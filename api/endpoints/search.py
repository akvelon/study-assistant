"""Search endpoint"""
import math
import re
from collections import Counter
import numpy as np
import openai
from fastapi import APIRouter, Depends
from typing_extensions import Annotated
from scipy import spatial
from pydantic import BaseModel
from settings import settings

# Index
from se_indexing.db_engine.config import get_database
from se_indexing.db_engine.db import DocumentEntry

# API
from api.endpoints.user import get_current_user_optional
from api.endpoints.schemas import SearchQuery, MessagesRequest


search_router = APIRouter(prefix="/search", tags=[""])


class SearchDocument(BaseModel):
    """Class for search engine response. Contains document and cosine similarity of it"""

    document: DocumentEntry
    similarity: float


class SearchResult(BaseModel):
    """List of search documents"""

    documents: list[SearchDocument]


WORD = re.compile(r"\w+")


def generate_vectors(text: str):
    """Generate vectors for summary and GPT response"""
    words = WORD.findall(text)
    return Counter(words)


def cosine_similarity_for_attachments(vec1, vec2):
    """Calculates cosine similarity for attachments"""
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[x] * vec2[x] for x in intersection)

    sum1 = sum(vec1[x] ** 2 for x in vec1.keys())
    sum2 = sum(vec2[x] ** 2 for x in vec2.keys())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    return float(numerator) / denominator


default_school_id = 1


class SearchEngine:
    """Search engine"""

    documents = []

    def __init__(self):
        openai.api_key = settings.openai_key
        self.documents = self.get_documents_from_index()

    def should_search_docs(self, messages, school_id=default_school_id) -> bool:
        """Function for comparing texts and check if it fit for requirements"""
        threshold = 0.155
        message_content = messages[-1].content
        msg_vector = generate_vectors(message_content)
        max_cosine = 0
        for document in self.documents:
            if document.school_id == school_id or document.type == "general":
                doc_vector = generate_vectors(document.summary)
                cosine = cosine_similarity_for_attachments(doc_vector, msg_vector)
                max_cosine = max(cosine, max_cosine)
        print("text similarity:", max_cosine, 'for "' + message_content + '"')
        return max_cosine > threshold

    def get_documents_from_index(self):
        """Get documents from database for Searching"""
        database = get_database()
        documents = database.get_documents()
        return documents

    def generate_embeddings(self, query: SearchQuery):
        """Generating embeddings for message content"""
        vectors = []
        for message in query.messages:
            response = openai.Embedding.create(
                input=[message.content], model="text-embedding-ada-002"
            )
            vector = response["data"][0]["embedding"]
            vectors.append(np.array(vector))
        return vectors

    def search_documents(self, embeddings, school_id=default_school_id):
        """Calculating cosine similarity,
        searching and sorting most similar and relevant documents"""
        similar_documents = []
        max_cosine = 0
        for embedding in embeddings:
            for document in self.documents:
                if document.school_id == school_id or document.type == "general":
                    threshold = 0.815
                    cosine_similarity = 1 - spatial.distance.cosine(
                        embedding.T, document.embedding.T
                    )
                    max_cosine = max(cosine_similarity, max_cosine)
                    if cosine_similarity > threshold:
                        similar_documents.append(
                            SearchDocument(
                                document=document, similarity=cosine_similarity
                            )
                        )
                else:
                    pass
            response = sorted(similar_documents, key=lambda x: x.similarity, reverse=True)
        print("      embedding:", max_cosine)
        return response

    async def search_text_vectors(
        self,
        request: MessagesRequest,
        school_id=default_school_id,
    ) -> list[DocumentEntry]:
        """Function for call text comparing and search engine"""
        if self.should_search_docs(request.messages, school_id):
            embeddings = self.generate_embeddings(request)
            return self.search_documents(embeddings, school_id)
        return []

    def get_system_message(self, document):
        """Creates system message for chat"""
        system_message = {
            "role": "system",
            "content": f"Answer for User question Using this summary:"
            f"{document.document.summary}",
        }
        return system_message


search_engine = SearchEngine()


@search_router.post("/", response_model=None)
async def search_documents(
    query: SearchQuery, current_user: Annotated[str, Depends(get_current_user_optional)]
) -> SearchResult:
    """POST request with 10 relevant documents"""
    school_id = current_user.schoolId if current_user and current_user.schoolId else None
    embeddings = search_engine.generate_embeddings(query)
    print('Searching for "' + query.messages[-1].content + '"')
    similar_documents = search_engine.search_documents(embeddings, school_id)[:10]
    return SearchResult(documents=similar_documents)
