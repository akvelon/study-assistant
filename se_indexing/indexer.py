import os
import pathlib
import sys
import pickle
import json
import glob

import openai
from db_engine.config import get_database


sys.path.append(os.path.abspath(pathlib.Path(__file__).parent.parent))
os.chdir(pathlib.Path(__file__).parent.parent)
from settings import settings


def get_documents():
    """Find all documents from the documents/ folder and return absolute path."""

    root_dir = os.getcwd()
    os.chdir("se_indexing/documents/")

    # Find all files in documents/ folder
    document_files = glob.glob("*.json", recursive=True)

    # Make all files absolute paths
    document_files = [
        os.path.join(os.getcwd(), document_file) for document_file in document_files
    ]

    return document_files


# TODO: Implement deleting a document when finished indexing
def delete_document(document):
    """When finished indexing, delete the document from the documents/ folder because it is no longer needed."""
    pass


def create_summary_for_content(content):
    max_tokens = 4097
    summary_word_count = 100  # words
    tokens_per_word = 100 / 75  # tokens per word
    summary_token_count = int(summary_word_count * tokens_per_word)  # words
    messages = [
        # Prepare ChatGPT for summarizing
        {
            "role": "system",
            "content": "You are an intelligent human summarizer.",
        },
        {
            "role": "user",
            "content": f"Summarize the document delimited by an XML tags in one paragraph of about {summary_word_count} words.\n<document>{content[:max_tokens-summary_token_count]}</document>",
        },
    ]

    gpt_response = openai.ChatCompletion.create(
        model=settings.chatgpt_model,
        messages=messages,
    )
    summary = gpt_response.choices[0].message.content

    return summary


def create_embedding_for_summary(summary):
    embedding_reply = openai.Embedding.create(
        model=settings.embedding_model,
        input=summary,
    )
    embedding_list = embedding_reply["data"][0]["embedding"]

    # Serialize embedding_list into a bytestream
    embedding = pickle.dumps(embedding_list, pickle.HIGHEST_PROTOCOL)

    return embedding


with get_database() as db:
    # db.delete_database()
    db.create_database_if_not_exists()

    openai.api_key = settings.openai_key

    for document_abspath in get_documents():
        document_filename = os.path.basename(document_abspath)
        print(f"Indexing {document_filename}")

        with open(document_abspath, "r") as document_file:
            document = json.load(document_file)
            document_content = document["content"]

            # Check if document is already in database
            if db.find_document_by_url(document["url"]) is None:
                document_summary = create_summary_for_content(document_content)
                document_embedding = create_embedding_for_summary(document_summary)

                document_id = db.insert_document(document)
                summary_id = db.insert_summary(document_id, document_summary)
                embedding_id = db.insert_embedding(
                    summary_id, settings.embedding_model, document_embedding
                )

        # TODO: Delete document from documents/ folder
        # delete_document(document_filename)
