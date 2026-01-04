import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Target Settings (Ollama)
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")

    # Judge Settings (Hugging Face)
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    # Priority List of Cloud Judges (Fallbacks)
    HF_JUDGE_CANDIDATES = [
        "google/gemma-2-9b-it",
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "microsoft/Phi-3-mini-4k-instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "Qwen/Qwen2.5-7B-Instruct",
        "NousResearch/Hermes-2-Pro-Llama-3-8B"
    ]
    
    
    # Local Fallback (Specific Model)
    LOCAL_JUDGE_MODEL = "qwen3:latest"
    
    # Load EVAL CONFIG
    EVAL_CONFIG = {}
    
    @classmethod
    def load_eval_config(cls):
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), "config", "eval_config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                cls.EVAL_CONFIG = yaml.safe_load(f)
        else:
            print(f"Warning: Config file not found at {config_path}")

    # Validation
    @classmethod
    def validate(cls):
        cls.load_eval_config()
        if not cls.HF_TOKEN:
            print("Warning: HF_TOKEN environment variable is not set. Judge capabilities will be limited to Local Judge.")
