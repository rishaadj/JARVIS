import json
import os

MEMORY_FILE = "jarvis_memory.json"

def execute(params):
    fact = params.get("fact")
    key = params.get("key")
    
    if not key or not fact:
        return "I need both a key and a fact to learn something, Sir."

    # Load existing memory safely
    memory = {}
    if os.path.exists(MEMORY_FILE) and os.stat(MEMORY_FILE).st_size > 0:
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
        except json.JSONDecodeError:
            memory = {}
    
    # Update
    memory[key] = fact
    
    # Save safely
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=4)
    
    return f"Sir, I have committed that to memory under '{key}'."