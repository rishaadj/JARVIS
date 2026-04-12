import pyautogui

def execute(params):
    action = params.get("action", "").lower()
    text = params.get("text", "")
    key = params.get("key", "")
    hotkey = params.get("hotkey", [])

    try:
        if action == "type":
            pyautogui.write(text, interval=0.05)
            return f"Typed: {text}"
        elif action == "press":
            pyautogui.press(key)
            return f"Pressed {key}"
        elif action == "hotkey":
            pyautogui.hotkey(*hotkey)
            return f"Executed hotkey: {' + '.join(hotkey)}"
        else:
            return f"Sir, I have successfully executed the {action} action."
    except Exception as e:
        return f"Sir, I encountered an error during input control: {e}"
