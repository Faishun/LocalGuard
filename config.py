import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Target Settings (Ollama)
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")

    # Judge Settings (Hugging Face)
    HF_TOKEN = os.getenv("HF_TOKEN")
    # Using a model confirmed to work on free tier router
    HF_MODEL = os.getenv("HF_MODEL", "google/gemma-2-9b-it")
    
    # Validation
    @classmethod
    def validate(cls):
        if not cls.HF_TOKEN:
            print("Warning: HF_TOKEN environment variable is not set. Judge capabilities may be limited.")
