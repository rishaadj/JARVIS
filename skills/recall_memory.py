import json
import os

MEMORY_FILE = "jarvis_memory.json"

def execute(params):
    key = params.get("key")
    
    if not os.path.exists(MEMORY_FILE):
        return "Sir, I don't have anything in my memory yet."
    
    with open(MEMORY_FILE, 'r') as f:
        memory = json.load(f)
    
    if key:
        query = key.lower()
        matches = []
        
        if key in memory:
            return f"Sir, under '{key}', I remember: {memory[key]}"
        
        for k, v in memory.items():
            if query in k.lower() or query in str(v).lower():
                matches.append(f"'{k}': {v}")
        
        if matches:
            results = "\n".join(matches)
            memory_manager = params.get("_memory")
            if memory_manager:
                sem_results = memory_manager.search_semantic(query, top_k=2)
                if sem_results:
                    sem_text = "\n".join([f"- {m['text']}" for _, m in sem_results])
                    results += f"\n\nSemantic Matches:\n{sem_text}"
            
            return f"Sir, I found {len(matches)} relevant record(s) and semantic matches:\n\n{results}"
        
        return f"Sir, I couldn't find anything specifically about '{key}'."
    else:
        if not memory:
            return "Sir, my memory is currently empty."
        all_keys = ", ".join(memory.keys())
        return f"Sir, I remember facts about: {all_keys}. Which one would you like to recall?"
