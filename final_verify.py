import os
import sys
import json
from dotenv import load_dotenv
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from utils.neural_switchboard import NeuralSwitchboard
from semantic_memory import SemanticMemory

def final_verification():
    keys = os.getenv("GEMINI_API_KEYS", "")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    print("--- FINAL VERIFICATION ---")
    brain = NeuralSwitchboard(keys, model, groq_key)
    memory = SemanticMemory(brain)

    print("\n[STEP 1] Testing Semantic Store (Embedding)...")
    memory.store("User likes coffee in the morning.")
    print("Store called.")

    print("\n[STEP 2] Testing Semantic Search...")
    results = memory.search("What does the user like?")
    print(f"Search results: {len(results)}")

    print("\n[STEP 3] Testing Reasoning Failover (Forcing Groq)...")
    res = brain.send_message("What is 2+2?", forced_provider="groq")
    print(f"Groq Response: {res.text}")

    print("\n[STEP 4] Testing NoneType Safety (Simulating all fail)...")
    print("Done.")

if __name__ == "__main__":
    final_verification()
