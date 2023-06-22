import os

from dotenv import load_dotenv
from pydantic import BaseSettings

class Settings(BaseSettings):
    # OpenAI API key
    openai_key: str
    # API root path
    root_path: str

    port: int = 8080

if os.path.exists(".env"):
    load_dotenv(".env")

settings = Settings()
