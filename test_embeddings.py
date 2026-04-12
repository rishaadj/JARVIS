from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEYS", "").replace(',', ' ').split()[0]
client = genai.Client(api_key=key)

try:
    result = client.models.embed_content(
        model="text-embedding-004",
        contents="Hello world"
    )
    print(f"Success 004: {result.embeddings[0].values[:5]}...")
except Exception as e:
    print(f"Error 004: {e}")
    try:
        result = client.models.embed_content(
            model="embedding-001",
            contents="Hello world"
        )
        print(f"Success 001: {result.embeddings[0].values[:5]}...")
    except Exception as e2:
        print(f"Error 001: {e2}")
