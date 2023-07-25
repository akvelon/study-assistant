"""service settings and dotenv"""
import os
from dotenv import load_dotenv
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Service settings"""

    # OpenAI API key
    openai_key: str

    # API root path
    root_path: str

    # ChatGPT model
    chatgpt_model: str = "gpt-3.5-turbo"
    # OpenAI text embedding model
    embedding_model: str = "text-embedding-ada-002"

    # API database
    db_path: str = "data/db/api_data.sqlite"

    port: int = 8080


if os.path.exists(".env"):
    load_dotenv(".env")

settings = Settings()
