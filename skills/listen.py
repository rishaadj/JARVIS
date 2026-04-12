import speech_recognition as sr

r = sr.Recognizer()
r.energy_threshold = 300
r.dynamic_energy_threshold = True

def execute(params=None):
    """Simple one-shot listen for when we already have his attention."""
    with sr.Microphone() as source:
        try:
            audio = r.listen(source, timeout=3, phrase_time_limit=5)
            return r.recognize_google(audio).lower()
        except:
            return None