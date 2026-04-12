import json
import os
from semantic_memory import SemanticMemory

MEMORY_FILE = "jarvis_memory.json"

class MemoryManager:
    def __init__(self, chat_obj=None):
        self._ensure_file_exists()
        self.semantic = None
        if chat_obj:
            self.semantic = SemanticMemory(chat_obj)

    def _ensure_file_exists(self):
        if not os.path.exists(MEMORY_FILE) or os.stat(MEMORY_FILE).st_size == 0:
            with open(MEMORY_FILE, "w") as f:
                json.dump({}, f)

    def load_memory(self):
        self._ensure_file_exists()
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def save_memory(self, data):
        try:
            temp_file = f"{MEMORY_FILE}.tmp"
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, MEMORY_FILE)
        except Exception as e:
            print(f"Memory Save Error: {e}")

    def remember(self, key, value):
        data = self.load_memory()
        data[key] = value
        self.save_memory(data)

    def recall(self, key):
        data = self.load_memory()
        return data.get(key, "")

    def search_semantic(self, query, top_k=3):
        if self.semantic:
            return self.semantic.search(query, top_k)
        return []

    def store_semantic(self, text, metadata=None):
        if self.semantic:
            return self.semantic.store(text, metadata)
        return False