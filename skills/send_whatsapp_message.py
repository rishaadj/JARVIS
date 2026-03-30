import webbrowser
import pyautogui
import time
import urllib.parse

def execute(params):
    phone = params.get("phone")
    message = params.get("message")
    
    if not phone or not message:
        return "Sir, I require both a destination number and a message body."

    # Remove any +, spaces, or dashes from the phone number
    clean_phone = "".join(filter(str.isdigit, str(phone)))

    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"
        
        webbrowser.open(url)
        
        # Give it a bit more time for the UI to settle
        time.sleep(15) 
        
        # Safety: Pressing Enter to send. 
        # Note: If the chat doesn't load, this will do nothing.
        pyautogui.press('enter')
        time.sleep(2)
        
        return f"Sir, the transmission to {clean_phone} has been initiated via the browser."
    except Exception as e:
        return f"WhatsApp Interface Error: {e}"