import time
import threading
import importlib.util
import os # type: ignore

def background_timer(minutes, label, socketio=None):
    seconds = minutes * 60
    time.sleep(seconds)
    
    # Alert when finished
    alert_text = f"Sir, your {minutes} minute timer for {label} is complete."
    print(f"\n[ALARM] {alert_text}")

    # Notify HUD if the core injected Socket.IO (background timer runs outside the core).
    if socketio:
        try:
            socketio.emit("new_message", {"sender": "jarvis", "text": alert_text})
        except Exception:
            pass
    
    # Dynamically load and run the speak skill to avoid circular imports
    try:
        skills_dir = os.path.dirname(__file__)
        speak_path = os.path.join(skills_dir, "speak.py")
        spec = importlib.util.spec_from_file_location("speak", speak_path)
        if spec and spec.loader:
            speak_module = importlib.util.module_from_spec(spec) # type: ignore
            spec.loader.exec_module(speak_module) # type: ignore
            speak_module.execute({"text": alert_text})
    except Exception as e:
        print(f"Timer Alert Error: {e}")

def execute(params):
    minutes = int(params.get("minutes", 5))
    label = params.get("label", "study session")
    socketio = params.get("_socketio")
    
    # Start the timer in a separate thread
    timer_thread = threading.Thread(target=background_timer, args=(minutes, label, socketio))
    timer_thread.start()
    
    return f"Sir, I've set a timer for {minutes} minutes for your {label}."