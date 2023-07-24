"""Search endpoint"""
import math
import re
from collections import Counter
import numpy as np
import openai
from fastapi import APIRouter
from scipy import spatial
from pydantic import BaseModel
from settings import settings
from se_indexing.db_engine.db import DocumentEntry
from se_indexing.db_engine.config import get_database
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


class SearchEngine:
    """Search engine"""

    documents = []

    def __init__(self):
        openai.api_key = settings.openai_key
        self.documents = self.get_documents_from_index()

    def find_documents_by_text_similarity(self, messages) -> bool:
        """Function for comparing texts and check if it fit for requirements"""
        threshold = 0.25
        for document in self.documents:
            vector1 = generate_vectors(document.summary)
            vector2 = generate_vectors(messages[-1].content)
            cosine = cosine_similarity_for_attachments(vector1, vector2)
            if cosine > threshold:
                return True
        return False

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

    def search_document(self, embeddings):
        """Calculating cosine similarity,
        searching and sorting most similar and relevant documents"""
        similar_documents = []
        for embedding in embeddings:
            for document in self.documents:
                threshold = 0.82
                cosine_similarity = 1 - spatial.distance.cosine(
                    embedding.T, document.embedding.T
                )
                if cosine_similarity > threshold:
                    similar_documents.append(
                        SearchDocument(document=document, similarity=cosine_similarity)
                    )
            response = sorted(similar_documents, key=lambda x: x.similarity, reverse=True)
        return response

    async def search_text_vectors(self, request: MessagesRequest):
        """Function for call text comparing and search engine"""
        documents = self.find_documents_by_text_similarity(request.messages)
        if documents is True:
            embeddings = self.generate_embeddings(request)
            documents = self.search_document(embeddings)[:10]
            return []
        return documents

    def get_system_message(self, document):
        """Creates system message for chat"""
        system_message = {
            "role": "system",
            "content": f"Answer for User question Using this summary:"
            f"{document.document.summary}",
        }
        return system_message


search_engine = SearchEngine()
search_db = search_engine.documents


@search_router.post("/", response_model=None)
async def search_documents(query: SearchQuery) -> SearchResult:
    """POST request with 10 relevant documents"""
    embeddings = search_engine.generate_embeddings(query)
    similar_documents = search_engine.search_document(embeddings)[:10]
    return SearchResult(documents=similar_documents)
