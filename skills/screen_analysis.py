import cv2
import numpy as np
import pyautogui
import pytesseract
import os
from datetime import datetime


def execute(params):
    action = params.get("action", "ocr")
    
    try:
        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        if action == "ocr":
            text = pytesseract.image_to_string(img)
            if not text.strip():
                return "Sir, I scanned the screen but couldn't detect any legible text."
            return f"Sir, I've analyzed the screen. Here is the text I found:\n\n{text}"
            
        elif action == "capture":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vision_capture_{timestamp}.png"
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            path = os.path.join("screenshots", filename)
            cv2.imwrite(path, img)
            return f"Sir, I've captured a vision-processed screenshot and saved it to: {os.path.abspath(path)}"
            
        return "Sir, please specify a valid vision action (ocr, capture)."
        
    except Exception as e:
        return f"Sir, the vision system encountered an error: {e}. (Ensure Tesseract-OCR is installed and in your PATH)"
