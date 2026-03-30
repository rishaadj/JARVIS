import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from datetime import datetime

class JARVISEventHandler(FileSystemEventHandler):
    def __init__(self, on_event_callback):
        self.on_event_callback = on_event_callback
        self.last_fired = {} # Path -> Time

    def on_created(self, event):
        if event.is_directory:
            return
        
        filename = os.path.basename(event.src_path)
        # Prevent noise (temp files, pyc, etc.)
        if filename.startswith(".") or filename.endswith((".tmp", ".pyc")):
            return

        # Simple debounce: 2s
        if filename in self.last_fired and time.time() - self.last_fired[filename] < 2:
            return
        
        self.last_fired[filename] = time.time()
        
        # Dispatch event to Sentinel (instead of direct queue access)
        self.on_event_callback(
            event_type="file_created",
            message=f"New file detected: {filename}",
            priority="normal"
        )

class FilesystemWatcher:
    def __init__(self, on_event_callback, path_to_watch="."):
        self.on_event_callback = on_event_callback
        self.path = os.path.abspath(path_to_watch)
        self.observer = Observer()
        self.handler = JARVISEventHandler(self.on_event_callback)

    def start(self):
        print(f"[WATCHER] Monitoring started on: {self.path}")
        self.observer.schedule(self.handler, self.path, recursive=False)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
