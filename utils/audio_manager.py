import threading

class AudioManager:
    def __init__(self):
        self.is_speaking = False
        self._stop_event = threading.Event()

    def start_speaking(self):
        self.is_speaking = True
        self._stop_event.clear()

    def stop_speaking(self):
        self._stop_event.set()
        self.is_speaking = False

    def should_stop(self):
        return self._stop_event.is_set()

# Global instance
audio_manager = AudioManager()
