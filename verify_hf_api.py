import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

token = os.getenv("HF_TOKEN")
models_to_test = [
    "HuggingFaceH4/zephyr-7b-beta",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "google/gemma-2-9b-it",
    "meta-llama/Meta-Llama-3-8B-Instruct"
]

print(f"Testing HF API with Token: {token[:5]}...")

for m in models_to_test:
    # Testing router endpoint.
    # Note: OpenAI client usually requires base_url to end in /v1/
    url_router = "https://router.huggingface.co/v1/"
    print(f"\nTesting Model: {m} at {url_router}")
    try:
        client = OpenAI(base_url=url_router, api_key=token)
        # We must pass the model name in the create call
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10
        )
        print(f"SUCCESS with {m}!")
        print(resp.choices[0].message.content)
        break # Found one that works
    except Exception as e:
        print(f"Failed with {m}: {e}")
