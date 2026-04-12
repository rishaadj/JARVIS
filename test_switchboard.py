import os
import sys
from dotenv import load_dotenv
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from utils.neural_switchboard import NeuralSwitchboard

def test_switchboard():
    keys = os.getenv("GEMINI_API_KEYS", "")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    groq_key = os.getenv("GROQ_API_KEY", "")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    print("--- TESTING NEURAL SWITCHBOARD ---")
    brain = NeuralSwitchboard(keys, model, groq_key, ollama_model=ollama_model)

    print("\n[TEST 1] Text Reasoning...")
    res = brain.send_message("Who are you?")
    print(f"Response: {res.text[:100]}...")

    print("\n[TEST 2] Visual Awareness...")
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    res = brain.send_message(["What is in this image?", img])
    print(f"Response: {res.text[:100]}...")

if __name__ == "__main__":
    test_switchboard()
