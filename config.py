import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Target Settings (Ollama)
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")

    # Local Judge Settings (Fallback)
    LOCAL_JUDGE_PROVIDER = os.getenv("LOCAL_JUDGE_PROVIDER", "ollama")
    LOCAL_JUDGE_MODEL = os.getenv("LOCAL_JUDGE_MODEL", "qwen3:latest")

    # Cloud Provider Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    HF_TOKEN = os.getenv("HF_TOKEN") # Used for both Judge and Target if selected

    # Supported Providers
    PROVIDERS = {
        "Ollama (Local)": "ollama",
        "OpenAI (Cloud)": "openai",
        "Anthropic (Cloud)": "anthropic",
        "Google (Cloud)": "google",
        "Hugging Face (Cloud)": "huggingface",
        "vLLM (Local)": "vllm",
        "Custom / Other": "openai" # generic openai-compatible
    }

    # Judge Settings (Hugging Face)
    
    # Priority List of Cloud Judges (Fallbacks)
    HF_JUDGE_CANDIDATES = [
        "google/gemma-2-9b-it",
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "microsoft/Phi-3-mini-4k-instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "Qwen/Qwen2.5-7B-Instruct",
        "NousResearch/Hermes-2-Pro-Llama-3-8B"
    ]
    
    
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
            print("Note: HF_TOKEN not set. Cloud Judge capabilities limited.")
