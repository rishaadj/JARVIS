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

    def scan_now(self, prompt_context=""):
        """Event-Driven On-Demand Capture of Active Window."""
        print(f"[VISUAL_OBSERVER] Taking on-demand vision scan...")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.abspath(f"screenshots/observer_{timestamp}.png")
            
            import pygetwindow as gw
            window = gw.getActiveWindow()
            if window and window.width > 0 and window.height > 0:
                region = (window.left, window.top, window.width, window.height)
                screenshot = pyautogui.screenshot(region=region)
                w_title = window.title
            else:
                screenshot = pyautogui.screenshot()
                w_title = "Desktop"
                
            # Downscale resolution to max 720p equivalent to save Tokens
            screenshot.thumbnail((1280, 720))
            screenshot.save(filepath)
            self.last_screenshot_path = filepath
            
            img = Image.open(filepath)
            prompt = f"""
            You are the 'Visual Cortex' of JARVIS. 
            User Context: {prompt_context}
            Active Window Title: {w_title}
            
            Analyze this screen and provide a CONCISE description of what is happening.
            Focus on:
            1. Visible progress (downloads, errors, code).
            2. Content the user is currently focused on.
            
            Respond in a structured format:
            AWARENESS: <context summary>
            EVENTS: <notable items>
            """
            
            response = self.chat.send_message([prompt, img])
            self.visual_context = response.text.strip()
            
            self._emit_update(self.visual_context, f"/screenshots/{os.path.basename(filepath)}")
            self._cleanup_screenshots()
            
            return self.visual_context
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                err = "[VISUAL_OBSERVER] Brain Overloaded (429)."
            else:
                err = f"[VISUAL_OBSERVER] Vision Error: {e}"
            print(err)
            return err

    def _cleanup_screenshots(self):
        files = sorted([os.path.join("screenshots", f) for f in os.listdir("screenshots") if f.startswith("observer_")], 
                       key=os.path.getmtime)
        if len(files) > 5:
            for f in files[:-5]:
                try: os.remove(f)
                except: pass

    def start(self):
        # Background polling disabled. Eye operates strictly on demand now.
        print("[VISUAL_OBSERVER] Neural Optics loaded. (Event-Driven Mode)")
        self.active = True

    def stop(self):
        self.active = False

    def get_context(self):
        return self.visual_context
