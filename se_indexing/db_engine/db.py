"""Search Index database wrapper"""

import os
import pathlib
import sys

import sqlite3
from uuid import uuid4
import json
import pickle
from contextlib import closing
from pydantic import BaseModel
import numpy as np


sys.path.append(os.path.abspath(pathlib.Path(__file__).parent.parent.parent))
os.chdir(pathlib.Path(__file__).parent.parent.parent)
# pylint: disable=wrong-import-position)
from api.db.schools import schools_db


def get_schools():
    """Function to get all schools id's"""
    schools = []
    for row in schools_db.get_schools():
        schools.append({"id": row[0], "url": row[3]})
    return schools


class DocumentEntry(BaseModel):
    """Document Entry class"""

    id: str
    url: str
    title: str
    type: str
    school_id: int = None
    metadata: list
    image_metadata: list
    content: str
    summary: str
    embedding: None = None

    def __init__(
        self,
        document_id,
        url,
        title,
        type,
        school_id,
        metadata,
        image_metadata,
        content,
        summary,
        embedding=None,
    ):
        """init"""
        super().__init__(
            id=document_id,
            url=url,
            title=title,
            type=type,
            school_id=school_id,
            metadata=json.loads(metadata),
            image_metadata=json.loads(image_metadata),
            content=content,
            summary=summary,
        )
        self.embedding = np.array(pickle.loads(embedding))

    class Config:
        "Config"
        fields = {"embedding": {"exclude": True}}


class IndexDB:
    """DataBase Index"""

    schools = get_schools()

    def __init__(self, path):
        self.path = path

        self.connection = sqlite3.connect(path)

    def __del__(self):
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()

    def delete_database(self):
        """WARNING: Deletes the entire indexing database!"""
        with closing(self.connection.cursor()) as cursor:
            cursor.execute("DROP TABLE IF EXISTS embeddings")
            cursor.execute("DROP TABLE IF EXISTS summaries")
            cursor.execute("DROP TABLE IF EXISTS documents")

        self.connection.commit()

    def create_database_if_not_exists(self):
        """Creates the indexing database, if it doesn't exist already."""
        sql_create_documents_table = """
        CREATE TABLE IF NOT EXISTS documents (
            id text PRIMARY KEY,
            url text,
            title text,
            school_id text,
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
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql_create_documents_table)
            cursor.execute(sql_create_summaries_table)
            cursor.execute(sql_create_embedding_table)

        self.connection.commit()

    def get_documents(self):
        """Function for load documents into Search engine"""
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT
                    documents.id,
                    documents.url,
                    documents.title,
                    documents.type,
                    documents.school_id,
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
            """
            )
            rows = cursor.fetchall()
            documents = []
            for row in rows:
                document = DocumentEntry(*row)
                documents.append(document)
            return documents

    def insert_document(self, document):
        """Add document to indexing database, and return its ID."""
        document["id"] = str(uuid4())
        school_id = self.get_school_by_url(document["url"])
        if school_id is None:
            document["type"] = "general"
        if len(document["content"]) == 0:
            return None

        sql_insert_document = """
        INSERT INTO documents(id, url, title, school_id, type, metadata, image_metadata, content)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                sql_insert_document,
                (
                    document["id"],
                    document["url"],
                    document["title"],
                    school_id,
                    document["type"],
                    json.dumps(document["metadata"]),
                    json.dumps(document["image_metadata"]),
                    document["content"],
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
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql_insert_summary, (summary_id, document_id, summary))
        self.connection.commit()
        return summary_id

    def insert_embedding(self, summary_id, type, embedding):
        """Add embedding to indexing database, and return its ID."""
        sql_insert_embedding = """
        INSERT INTO embeddings(id, summary_id, type, embedding)
        VALUES(?, ?, ?, ?)"""
        embedding_id = str(uuid4())
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                sql_insert_embedding,
                (embedding_id, summary_id, type, embedding),
            )
        self.connection.commit()
        return embedding_id

    def find_document_by_url(self, url):
        """Finds document in DB by URL"""
        sql_find_document = """
        SELECT * FROM documents WHERE url = ?
        """
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql_find_document, (url,))
            return cursor.fetchone()

    def find_summary_by_document_id(self, document_id):
        """Finds summary in DB bu document id"""
        sql_find_summary = """
        SELECT * FROM summaries WHERE document_id = ?"""
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql_find_summary, (document_id,))
            return cursor.fetchone()

    def find_embedding_by_summary_id(self, summary_id):
        """Finds embedding in DB by summary"""
        sql_find_embedding = """
        SELECT * FROM embeddings WHERE summary_id = ?"""
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql_find_embedding, (summary_id,))
            return cursor.fetchone()

    def get_school_by_url(self, url):
        """Get school id by url"""
        for school in self.schools:
            if url.startswith(school["url"]):
                return school["id"]
        return None
