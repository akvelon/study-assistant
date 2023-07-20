"""Search endpoint"""
import numpy as np
import openai
from fastapi import APIRouter
from scipy import spatial
from pydantic import BaseModel
from settings import settings
from se_indexing.db_engine.db import DocumentEntry
from se_indexing.db_engine.config import get_database
from .schemas import SearchQuery


search_router = APIRouter(prefix="/search", tags=[""])

class SearchDocument(BaseModel):
    document: DocumentEntry
    similarity: float

class SearchResult(BaseModel):
    documents: list[SearchDocument]


class SearchEngine:
    documents = []

    def __init__(self):
        openai.api_key = settings.openai_key
        self.documents = self.get_documents_from_index()

    def get_documents_from_index(self):
        '''Get documents from database for Searching'''
        db = get_database()
        documents = db.get_documents()
        return documents

    def generate_embeddings(self, query: SearchQuery):
        '''Generating embeddings for message content'''
        vectors = []
        for message in query.messages:
            response = openai.Embedding.create(input=[message.content], model="text-embedding-ada-002")
            vector = response["data"][0]["embedding"]
            vectors.append(np.array(vector))
        return vectors

    def search_document(self, embeddings):
        '''Calculating cosine similarity,
        searching and sorting most similar and relevant documents'''
        similar_documents = []
        for embedding in embeddings:
            for document in self.documents:
                threshold = 0.8
                cosine_similarity = 1 - spatial.distance.cosine(embedding.T, document.embedding.T)
                if cosine_similarity > threshold:
                    similar_documents.append(SearchDocument(document=document, similarity=cosine_similarity))
            response = sorted(similar_documents, key=lambda x: x.similarity, reverse=True)
        return response


search_engine = SearchEngine()

@search_router.post("/", response_model=None)
async def search_documents(query: SearchQuery) -> SearchResult:
    '''POST request with 10 relevant documents'''
    embeddings = search_engine.generate_embeddings(query)
    similar_documents = search_engine.search_document(embeddings)[:10]
    return SearchResult(documents=similar_documents)