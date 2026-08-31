import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    VECTOR_DB_COLLECTION_NAME = os.getenv("VECTOR_DB_COLLECTION_NAME", "ip_sakti_docs")
    CORPUS_MANIFEST_PATH = os.getenv("CORPUS_MANIFEST_PATH", "./corpus/manifest.json")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")


config = Config()
