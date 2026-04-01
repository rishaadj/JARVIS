import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

if not GEMINI_API_KEY:
    print("API Key not found in .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
try:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents="Hello, identify yourself."
    )
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)