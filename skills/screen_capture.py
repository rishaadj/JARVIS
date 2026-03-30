import pyautogui # type: ignore
import os
from datetime import datetime

def execute(params):
    filename = params.get("filename")
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
    
    # Save to static folder if it exists, otherwise current dir
    save_path = os.path.join("screenshots", filename)
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        abs_path = os.path.abspath(save_path)
        return f"Sir, I've captured the screen. The image has been saved to: {abs_path}"
    except Exception as e:
        return f"Failed to capture screen: {e}"
