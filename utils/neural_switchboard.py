import os
import base64
import time
import io
import json
from google import genai
from groq import Groq
import ollama
from PIL import Image

class NeuralSwitchboard:
    """The Multi-Provider Brain of JARVIS. Failover order: Gemini -> Groq -> Ollama."""

    def __init__(self, gemini_api_keys: str, gemini_model: str,
                 groq_api_key: str = None, groq_model: str = "llama-3.3-70b-versatile",
                 ollama_model: str = "llama3.2-vision",
                 ollama_uncensored_model: str = "dolphin-llama3"):

        self.gemini_keys = [k.strip() for k in gemini_api_keys.replace(',', ' ').split() if k.strip()]
        self.gemini_idx = 0
        self.gemini_model = gemini_model
        self.gemini_client = genai.Client(api_key=self.gemini_keys[0]) if self.gemini_keys else None

        self.groq_keys = [k.strip() for k in groq_api_key.replace(',', ' ').split() if k.strip()] if groq_api_key else []
        self.groq_idx = 0
        self.groq_model = groq_model
        self.groq_client = Groq(api_key=self.groq_keys[0]) if self.groq_keys else None

        self.ollama_model = ollama_model
        self.ollama_uncensored_model = ollama_uncensored_model

        print(f"[NEURAL SWITCHBOARD] Initialized. Gemini: {len(self.gemini_keys)} keys | Groq: {len(self.groq_keys)} keys | Ollama: {self.ollama_model} | Uncensored: {self.ollama_uncensored_model}")

    def _rotate_gemini(self):
        self.gemini_idx = (self.gemini_idx + 1) % len(self.gemini_keys)
        self.gemini_client = genai.Client(api_key=self.gemini_keys[self.gemini_idx])
        time.sleep(0.5)

    def _rotate_groq(self):
        if not self.groq_keys: return
        self.groq_idx = (self.groq_idx + 1) % len(self.groq_keys)
        self.groq_client = Groq(api_key=self.groq_keys[self.groq_idx])
        time.sleep(0.5)

    def _pil_to_base64(self, pil_img):
        buffered = io.BytesIO()
        pil_img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def _send_gemini(self, contents):
        """Internal helper for Gemini reasoning with auto-rotation."""
        if not self.gemini_client: return None

        attempts = 0
        while attempts < len(self.gemini_keys):
            try:
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model, contents=contents
                )
                return response
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"[SWITCHBOARD] Gemini Limit Hit. Rotating...")
                    self._rotate_gemini()
                    attempts += 1
                else:
                    print(f"[SWITCHBOARD] Gemini unknown error: {e}")
                    break
        return None

    def _send_groq(self, contents):
        """Internal helper for Groq reasoning with auto-rotation."""
        if not self.groq_client: return None

        has_image = False
        pil_image = None
        text_query = ""

        if isinstance(contents, list):
            for item in contents:
                if isinstance(item, Image.Image):
                    has_image = True
                    pil_image = item
                elif isinstance(item, str):
                    text_query += item + " "
        else:
            text_query = str(contents)

        attempts = 0
        while attempts < len(self.groq_keys):
            try:
                messages = []
                if has_image:
                    b64 = self._pil_to_base64(pil_image)
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text_query},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                        ]
                    })
                else:
                    messages.append({"role": "user", "content": text_query})

                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=messages,
                )

                class MockResponse:
                    def __init__(self, text): self.text = text
                return MockResponse(response.choices[0].message.content)
            except Exception as e:
                if "429" in str(e):
                    print(f"[SWITCHBOARD] Groq Limit Hit. Rotating...")
                    self._rotate_groq()
                    attempts += 1
                else:
                    print(f"[SWITCHBOARD] Groq failed: {e}")
                    break
        return None

    def send_message(self, contents, uncensored=False, forced_provider=None):
        if forced_provider and forced_provider != 'auto':
            if forced_provider == 'uncensored':
                res = self._try_ollama(contents, use_uncensored=True)
                if res: return res
            elif forced_provider == 'ollama':
                res = self._try_ollama(contents, use_uncensored=False)
                if res: return res
            elif forced_provider == 'groq':
                print(f"[SWITCHBOARD] Forced Provider: Groq")
                res = self._send_groq(contents)
                if res: return res
            elif forced_provider == 'gemini':
                print(f"[SWITCHBOARD] Forced Provider: Gemini")
                res = self._send_gemini(contents)
                if res: return res

        if uncensored:
            print(f"[SWITCHBOARD] 🔓 Uncensored Mode Engaged. Using {self.ollama_uncensored_model}")
            return self._try_ollama(contents, use_uncensored=True)

        res = self._send_gemini(contents)
        if res: return res

        print("[SWITCHBOARD] Gemini failed. Failing over to Groq...")
        res = self._send_groq(contents)
        if res: return res

        res = self._try_ollama(contents)
        if res: return res

        print("[SWITCHBOARD] 🏁 Final Resort: Attempting Uncensored Reasoning...")
        res = self._try_ollama(contents, use_uncensored=True)
        if res: return res


        return type("Err", (), {"text": "Sir, all neural systems (Online, Offline, and Uncensored) are currently unavailable."})()

    def _try_ollama(self, contents, use_uncensored=False):
        """Internal helper for Ollama reasoning."""
        has_image = False
        pil_image = None
        text_query = ""

        if isinstance(contents, list):
            for item in contents:
                if isinstance(item, Image.Image):
                    has_image = True
                    pil_image = item
                elif isinstance(item, str):
                    text_query += item + " "
        else:
            text_query = str(contents)

        model = self.ollama_uncensored_model if use_uncensored else self.ollama_model
        try:
            options = {
                "num_ctx": 8192
            }
            if has_image:
                options["images"] = [self._pil_to_base64(pil_image)]

            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': text_query}],
                options=options
            )

            class MockResponse:
                def __init__(self, text): self.text = text
            return MockResponse(response['message']['content'])
        except Exception as e:
            return None