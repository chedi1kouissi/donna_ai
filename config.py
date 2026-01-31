import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    DATA_MODE = os.getenv("DATA_MODE", "fake")
    FAKE_DATA_PATH = os.getenv("FAKE_DATA_PATH", "./data/fake_clients")
    PRODUCT_CATALOG_PATH = os.getenv("PRODUCT_CATALOG_PATH", "./data/product_catalog.json")
    A2A_HOST = os.getenv("A2A_HOST", "0.0.0.0")
    A2A_PORT = int(os.getenv("A2A_PORT", 8000))

    @staticmethod
    def check_api_key():
        if not Config.GEMINI_API_KEY:
             raise ValueError("GEMINI_API_KEY is not set in .env file.")
