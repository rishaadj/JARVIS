import time
import threading
import os
import pyautogui
from PIL import Image
from datetime import datetime

class VisualObserver:
    def __init__(self, chat_obj, socketio_obj=None, scan_interval=600):
        self.chat = chat_obj
        self.socketio = socketio_obj
        self.scan_interval = scan_interval
        self.active = False
        self.visual_context = "System starting... No visual data yet."
        self.last_screenshot_path = None
        
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")

    def _emit_update(self, context, screenshot_path):
        if self.socketio:
            self.socketio.emit('visual_awareness', {
                'context': context,
                'image_path': screenshot_path,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })

    def observe_loop(self):
        print(f"[VISUAL_OBSERVER] Awareness loop started (Interval: {self.scan_interval}s).")
        while self.active:
            try:
                # 1. Capture Screen
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.abspath(f"screenshots/observer_{timestamp}.png")
                
                screenshot = pyautogui.screenshot()
                # Resize for faster API transmission if needed, but for now full size is OK.
                screenshot.save(filepath)
                self.last_screenshot_path = filepath
                
                # 2. Analyze with Gemini
                img = Image.open(filepath)
                prompt = """
                You are the 'Visual Cortex' of JARVIS. 
                Analyze this screen and provide a CONCISE description of what is happening.
                Focus on:
                1. Active applications.
                2. Visible progress (downloads, rendering, errors).
                3. Content the user is currently focused on.
                
                Respond in a structured format:
                AWARENESS: <context summary>
                EVENTS: <notable items>
                """
                
                # Use the chat object to send the message
                response = self.chat.send_message([prompt, img])
                self.visual_context = response.text.strip()
                
                # 3. Update UI
                self._emit_update(self.visual_context, f"/screenshots/{os.path.basename(filepath)}")
                
                # 4. Clean up old screenshots (keep only the last 5)
                self._cleanup_screenshots()
                
            except Exception as e:
                # 🛡️ 429 Rate Limit Mitigation
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"[VISUAL_OBSERVER] Brain Overloaded (429). Eye rest for 10 minutes...")
                    time.sleep(600) # Sleep longer if 429 occurs
                else:
                    print(f"[VISUAL_OBSERVER] Error: {e}")
            
            time.sleep(self.scan_interval)

    def _cleanup_screenshots(self):
        files = sorted([os.path.join("screenshots", f) for f in os.listdir("screenshots") if f.startswith("observer_")], 
                       key=os.path.getmtime)
        if len(files) > 5:
            for f in files[:-5]:
                try: os.remove(f)
                except: pass

    def start(self):
        if not self.active:
            self.active = True
            self.thread = threading.Thread(target=self.observe_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.active = False

    def get_context(self):
        return self.visual_context
