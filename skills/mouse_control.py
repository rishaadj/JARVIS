import pyautogui # type: ignore

def execute(params):
    action = params.get("action", "").lower() # move, click, drag, scroll
    x = params.get("x")
    y = params.get("y")
    clicks = params.get("clicks", 1)
    button = params.get("button", "left") # left, right, middle
    amount = params.get("amount", 0) # for scroll

    try:
        if action == "move":
            pyautogui.moveTo(x, y, duration=0.5)
            return f"Moved mouse to ({x}, {y})"
        elif action == "click":
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
                return f"Clicked {button} at ({x}, {y}) {clicks} times."
            else:
                pyautogui.click(clicks=clicks, button=button)
                return f"Clicked {button} {clicks} times at current position."
        elif action == "drag":
            pyautogui.dragTo(x, y, duration=0.5, button=button)
            return f"Dragged mouse to ({x}, {y})"
        elif action == "scroll":
            pyautogui.scroll(amount)
            return f"Sir, I have successfully completed the {action} operation."
        elif action == "position":
            pos = pyautogui.position()
            return f"Sir, mouse position: {pos.x}, {pos.y}"
        else:
            return "Sir, please specify action (move, click, drag, scroll, position)."
    except Exception as e:
        return f"Sir, there was an issue with the mouse control: {e}"
