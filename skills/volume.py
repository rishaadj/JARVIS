import pyautogui # type: ignore

def execute(params):
    action = params.get("action", "").lower()
    
    if action == "up":
        for _ in range(5):
            pyautogui.press('volumeup')
        return f"Sir, I've successfully adjusted the volume {action}."
    elif action == "down":
        for _ in range(5):
            pyautogui.press('volumedown')
        return f"Sir, I've successfully adjusted the volume {action}."
    elif action == "mute":
        # Toggle mute
        pyautogui.press("volumemute")
        return "Sir, I have toggled the sound state."
    else:
        return "Sir, please specify volume up, down, or mute."
