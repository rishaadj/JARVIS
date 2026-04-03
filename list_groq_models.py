from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
keys = os.getenv("GROQ_API_KEY", "").replace(',', ' ').split()
for i, key in enumerate(keys):
    try:
        client = Groq(api_key=key)
        models = client.models.list()
        print(f"Key {i} works! Models:")
        for model in models.data:
            print(f" - {model.id}")
        break
    except Exception as e:
        print(f"Key {i} failed: {e}")
