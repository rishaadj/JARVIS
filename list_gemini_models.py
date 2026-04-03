from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEYS", "").replace(',', ' ').split()[0]
client = genai.Client(api_key=key)

try:
    print("Available Gemini Models:")
    models = list(client.models.list())
    if models:
        print(f"Attributes of first model ({models[0].name}):")
        print(dir(models[0]))
        for m in models:
             print(f" - {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
