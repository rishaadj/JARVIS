from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
keys = os.getenv("GROQ_API_KEY", "").replace(',', ' ').split()
client = Groq(api_key=keys[0])

try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(f"Success: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error: {e}")
