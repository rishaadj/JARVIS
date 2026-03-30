import time
import os
from watchdog.observers import Observer # type: ignore
from watchdog.events import FileSystemEventHandler # type: ignore

_observers = []

class JarvisHandler(FileSystemEventHandler):
    def __init__(self, socketio=None):
        super().__init__()
        self.socketio = socketio

    def on_created(self, event):
        if not event.is_directory:
            msg = f"Sir, I've noticed a new file was created: {os.path.basename(event.src_path)}"
            print(f"JARVIS: {msg}")
            if self.socketio:
                try:
                    self.socketio.emit("new_message", {"sender": "jarvis", "text": msg})
                except Exception:
                    pass

def execute(params):
    path_to_watch = params.get("path")
    if not path_to_watch:
        # Default to Downloads if on Windows
        path_to_watch = os.path.join(os.path.expanduser("~"), "Downloads")

    socketio = params.get("_socketio")
    
    if not os.path.exists(path_to_watch):
        return f"Sir, the path {path_to_watch} does not exist."

    try:
        event_handler = JarvisHandler(socketio=socketio)
        observer = Observer()
        observer.schedule(event_handler, path_to_watch, recursive=False)
        observer.start()
        _observers.append(observer)
        
        # In a real tool use, this would run in a separate thread.
        # For this skill, we'll just confirm it started.
        return f"Sir, I am now monitoring the directory: {path_to_watch}. I will notify you of any new additions."
    except Exception as e:
        return f"Sir, I failed to initialize the file watcher: {e}"
