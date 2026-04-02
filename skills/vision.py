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
        import pygetwindow as gw
        window = gw.getActiveWindow()
        if window and window.width > 0 and window.height > 0:
            region = (window.left, window.top, window.width, window.height)
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
            
        screenshot.thumbnail((1280, 720))
        screenshot.save(filepath)
        
        # Return the path so the Core knows where to find the image
        return f"SCREENSHOT_SAVED: {filepath}"
    except Exception as e:
        return f"VISION_ERROR: {str(e)}"