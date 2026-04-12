import time
import os
from google import genai

class QuotaExceededError(Exception):
    """Raised when all provided API keys have hit their rate limits."""
    pass

class GeminiRotator:
    """Manages multiple Gemini API keys and automatically rotates on 429 Exhausted."""
    def __init__(self, api_keys_str: str, model: str):
        keys = []
        if api_keys_str:
            keys = [k.strip() for k in api_keys_str.replace(',', ' ').split() if k.strip()]
        self.api_keys = keys
        
        if not self.api_keys:
            raise ValueError("[API ROTATOR] No API keys provided to GeminiRotator.")
            
        self.model = model
        self.current_idx = 0
        self.client = genai.Client(api_key=self.api_keys[self.current_idx])
        print(f"[API ROTATOR] Initialized with {len(self.api_keys)} keys. Using Key 1.")

    def _rotate_key(self):
        self.current_idx = (self.current_idx + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_idx]
        print(f"[API ROTATOR] Rate limit hit. Rotating to API Key {self.current_idx + 1}/{len(self.api_keys)}")
        self.client = genai.Client(api_key=new_key)
        time.sleep(0.5)

    def send_message(self, contents, **kwargs):
        """
        Drop-in replacement for stateful chat `send_message`.
        Acts completely stateless to save input tokens, and rotates keys on failure.
        """
        attempts = 0
        while attempts < len(self.api_keys):
            try:
                response = self.client.models.generate_content(
                    model=self.model, 
                    contents=contents, 
                    **kwargs
                )
                return response
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print(f"[API ROTATOR] 429 Overload detected on Key {self.current_idx + 1}. ({e})")
                    self._rotate_key()
                    attempts += 1
                else:
                    raise e
        
        raise QuotaExceededError(f"[API ROTATOR] ALL {len(self.api_keys)} API keys evaluated as 429 RESOURCE_EXHAUSTED! Please add more or wait.")
