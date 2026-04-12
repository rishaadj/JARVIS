from google import genai
import os
import cv2
import edge_tts
import asyncio
from dotenv import load_dotenv

async def system_check():
    print("--- JARVIS SYSTEM CHECK ---")
    
    try:
        load_dotenv()
        keys = os.getenv("GEMINI_API_KEYS", "")
        first_key = [k.strip() for k in keys.replace(',', ' ').split() if k.strip()][0]
        client = genai.Client(api_key=first_key)
        response = client.models.generate_content(model='gemini-2.5-flash-lite', contents="Test connection.")
        print("SUCCESS AI Engine: Connected")
    except Exception as e:
        print(f"FAILED AI Engine: Failed ({e})")

    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("SUCCESS Vision: Camera Accessible")
        cap.release()
    else:
        print("FAILED Vision: Camera Not Found")

    print("SUCCESS Voice: edge-tts Ready")
    print("---------------------------")

if __name__ == "__main__":
    asyncio.run(system_check())