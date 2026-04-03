import json
import os
import numpy as np
from datetime import datetime

class SemanticMemory:
    def __init__(self, chat_obj, index_file="semantic_index.json"):
        self.chat = chat_obj
        self.index_file = index_file
        self.memories = [] # List of tuples: (vector, metadata)
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r") as f:
                    data = json.load(f)
                    # Convert list-vectors back to numpy arrays
                    self.memories = [(np.array(m['vector']), m['metadata']) for m in data]
            except Exception as e:
                print(f"[SEMANTIC MEMORY] Load Error: {e}")
                self.memories = []

    def _save_index(self):
        try:
            # Convert numpy vectors to lists for JSON serialization
            data = [{'vector': m[0].tolist(), 'metadata': m[1]} for m in self.memories]
            with open(self.index_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SEMANTIC MEMORY] Save Error: {e}")

    def _get_embedding(self, text):
        """Fetches embedding vector from Gemini."""
        try:
            from google import genai
            import os
            # Using the first key from Rotator pool for basic embedding tasks
            keys = os.getenv("GEMINI_API_KEYS", "")
            first_key = [k.strip() for k in keys.replace(',', ' ').split() if k.strip()][0]
            
            client = genai.Client(api_key=first_key)
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text
            )
            # Extracted vector based on new SDK schema
            return np.array(result.embeddings[0].values)
        except Exception as e:
            if "text-embedding-004" in str(e):
                print(f"[SEMANTIC MEMORY] text-embedding-004 failed, trying fallback...")
                try:
                    result = client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=text
                    )
                    return np.array(result.embeddings[0].values)
                except Exception as e2:
                    print(f"[SEMANTIC MEMORY] Fallback Embedding Error: {e2}")
            else:
                print(f"[SEMANTIC MEMORY] Embedding Error: {e}")
            return None

    def store(self, text, metadata=None):
        """Embeds and saves a new concept/experience."""
        if not text or not text.strip():
            return
        
        vector = self._get_embedding(text)
        if vector is not None:
            metadata = metadata or {}
            metadata['text'] = text
            metadata['timestamp'] = datetime.now().isoformat()
            
            self.memories.append((vector, metadata))
            self._save_index()
            return True
        return False

    def search(self, query, top_k=3):
        """Semantic search for similar concepts."""
        if not self.memories:
            return []
            
        query_vector = self._get_embedding(query)
        if query_vector is None:
            return []
            
        results = []
        for vector, metadata in self.memories:
            # Cosine similarity: (A · B) / (||A|| * ||B||)
            # Since genai usually returns normalized embeddings, dot product is enough.
            similarity = np.dot(query_vector, vector)
            results.append((similarity, metadata))
            
        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

    def clear(self):
        self.memories = []
        self._save_index()
