import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

try:
    print("Initiating JARVIS Core...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in .env")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
    response = model.generate_content("System check. Reply with: Online, Sir.")
    
    print("-" * 30)
    print(f"JARVIS: {response.text}")
    print("-" * 30)
    print("SUCCESS: Connection established.")

except Exception as e:
    print(f"Connection Failed: {e}")