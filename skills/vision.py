import pyautogui
import os
from datetime import datetime
from PIL import Image

def execute(params):
    """
    Skill: Vision / Screen Capture
    Analyzes the current screen state.
    """
    # Create a directory for screenshots if it doesn't exist
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"screenshots/scr_{timestamp}.png"

    try:
        # Take the screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        # Return the path so the Core knows where to find the image
        return f"SCREENSHOT_SAVED: {filepath}"
    except Exception as e:
        return f"VISION_ERROR: {str(e)}"