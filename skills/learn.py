import json
import os

MEMORY_FILE = "jarvis_memory.json"

def execute(params):
    fact = params.get("fact")
    key = params.get("key")
    
    if not key or not fact:
        return "I need both a key and a fact to learn something, Sir."

    memory = {}
    if os.path.exists(MEMORY_FILE) and os.stat(MEMORY_FILE).st_size > 0:
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
        except json.JSONDecodeError:
            memory = {}
    
    memory[key] = fact
    
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=4)
    
    memory_manager = params.get("_memory")
    if memory_manager:
        memory_manager.store_semantic(f"Learned fact about {key}: {fact}", {"type": "user_fact", "key": key})
    
    return f"Sir, I have committed that to memory under '{key}'."