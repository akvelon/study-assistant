import sqlite3
from uuid import uuid4
from pydantic import BaseModel
import pickle
import numpy as np
class DocumentEntry(BaseModel):
    id: str
    url: str
    title: str
    type: str
    metadata: list
    image_metadata: list
    content: str
    summary: str
    embedding: None = None
    def __init__(self, id, url, title, type, metadata, image_metadata, content, summary, embedding=None):

        super().__init__(
            id=id,
            url=url,
            title=title,
            type=type,
            metadata=eval(metadata),
            image_metadata=eval(image_metadata),
            content=content,
            summary=summary,
        )
        self.embedding = np.array(pickle.loads(embedding))

    class Config:
        fields = {'embedding': {'exclude': True}}


class IndexDB:
    def __init__(self, path):
        self.path = path

        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.connection.close()

    def delete_database(self):
        """WARNING: Deletes the entire indexing database!"""
        self.cursor.execute("DROP TABLE IF EXISTS embeddings")
        self.cursor.execute("DROP TABLE IF EXISTS summaries")
        self.cursor.execute("DROP TABLE IF EXISTS documents")

    def create_database_if_not_exists(self):
        """Creates the indexing database, if it doesn't exist already."""
        sql_create_documents_table = """
        CREATE TABLE IF NOT EXISTS documents (
            id text PRIMARY KEY,
            url text,
            title text,
            type text,
            metadata text,
        	image_metadata text,
            content text
        );"""
        sql_create_summaries_table = """
        CREATE TABLE IF NOT EXISTS summaries (
            id text PRIMARY KEY,
            document_id text REFERENCES documents(id),
            summary text
        );"""
        sql_create_embedding_table = """
        CREATE TABLE IF NOT EXISTS embeddings (
            id text PRIMARY KEY,
            summary_id text REFERENCES summaries(id),
            type text,
            embedding blob
        );"""
        self.cursor.execute(sql_create_documents_table)
        self.cursor.execute(sql_create_summaries_table)
        self.cursor.execute(sql_create_embedding_table)

    def get_documents(self):
        self.cursor.execute("""
            SELECT
                documents.id,
                documents.url,
                documents.title,
                documents.type,
                documents.metadata,
                documents.image_metadata,
                documents.content,
                summaries.summary,
                embeddings.embedding
            FROM
                documents
            INNER JOIN
                summaries
            ON
                summaries.document_id = documents.id
            INNER JOIN
                embeddings 
            ON 
                embeddings.summary_id = summaries.id;
        """)
        rows = self.cursor.fetchall()
        documents = []
        for row in rows:
            document = DocumentEntry(*row)
            documents.append(document)
        return documents

    def insert_document(self, document):
        """Add document to indexing database, and return its ID."""
        document["id"] = str(uuid4())
        sql_insert_document = """
        INSERT INTO documents(id, url, title, type, metadata, image_metadata, content)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(
            sql_insert_document,
            (
                str(document["id"]),
                str(document["url"]),
                str(document["title"]),
                str(document["type"]),
                str(document["metadata"]),
                str(document["image_metadata"]),
                str(document["content"]),
            ),
        )
        self.connection.commit()
        return document["id"]

    def insert_summary(self, document_id, summary):
        """Add summary to indexing database, and return its ID."""
        sql_insert_summary = """
        INSERT INTO summaries(id, document_id, summary)
        VALUES(?, ?, ?)
        """
        summary_id = str(uuid4())
        self.cursor.execute(
            sql_insert_summary, (summary_id, str(document_id), str(summary))
        )
        self.connection.commit()
        return summary_id

    def insert_embedding(self, summary_id, type, embedding):
        """Add embedding to indexing database, and return its ID."""
        sql_insert_embedding = """
        INSERT INTO embeddings(id, summary_id, type, embedding)
        VALUES(?, ?, ?, ?)"""
        embedding_id = str(uuid4())
        self.cursor.execute(
            sql_insert_embedding, (embedding_id, str(summary_id), str(type), embedding)
        )
        self.connection.commit()
        return embedding_id

    def find_document_by_url(self, url):
        sql_find_document = """
        SELECT * FROM documents WHERE url = ?
        """
        self.cursor.execute(sql_find_document, (url,))
        return self.cursor.fetchone()

    def find_summary_by_document_id(self, document_id):
        sql_find_summary = """
        SELECT * FROM summaries WHERE document_id = ?"""
        self.cursor.execute(sql_find_summary, (document_id,))
        return self.cursor.fetchone()

    def find_embedding_by_summary_id(self, summary_id):
        sql_find_embedding = """
        SELECT * FROM embeddings WHERE summary_id = ?"""
        self.cursor.execute(sql_find_embedding, (summary_id,))
        return self.cursor.fetchone()
