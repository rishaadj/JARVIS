from dotenv import load_dotenv
load_dotenv()

import os
import sys
import json
import threading
import time
import queue
import sounddevice as sd
from flask import Flask, render_template
from flask_socketio import SocketIO
from vosk import Model, KaldiRecognizer

# --- UPDATED 2026 SDK IMPORT ---
# pip install google-genai
from google import genai

# Import the core and skills
from autonomous_core import start_autonomous_core
from utils.audio_manager import audio_manager
from topology_engine import TopologyEngine

from utils.neural_switchboard import NeuralSwitchboard

# --- CONFIGURATION ---
GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()
JARVIS_PIN = os.getenv("JARVIS_PIN", "0000").strip()

# --- INITIALIZE FLASK & SOCKETIO FIRST ---
# This MUST happen before any @socketio.on decorators are used.
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- REMOTE AUTHENTICATION ---
@socketio.on('verify_pin')
def on_verify_pin(data):
    pin = data.get('pin', '')
    if pin == JARVIS_PIN:
        socketio.emit('auth_success')
        print(f"[SECURITY] Authorized remote session.")
    else:
        socketio.emit('auth_failure')
        print(f"[SECURITY] Denied unauthorized access attempt.")

# --- NEURAL BRAIN SETUP (Multi-Provider Switchboard) ---
chat_session = None
if GEMINI_API_KEYS:
    GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
    O_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2-vision").strip()
    U_MODEL = os.getenv("OLLAMA_UNCENSORED_MODEL", "dolphin-llama3").strip()
    
    chat_session = NeuralSwitchboard(
        gemini_api_keys=GEMINI_API_KEYS, 
        gemini_model=GEMINI_MODEL,
        groq_api_key=GROQ_KEY if "YOUR_GROQ" not in GROQ_KEY else None,
        ollama_model=O_MODEL,
        ollama_uncensored_model=U_MODEL
    )
    print(f"[SYSTEM] Neural Brain Synchronized: {GEMINI_MODEL} (Switchboard Active)")
else:
    print("[ERROR] GEMINI_API_KEYS is not set. Core will run in UI-only mode.")

# Audio Queue for Vosk
audio_queue = queue.Queue()

# Global State
core = None
running = True

# --- VOSK SETUP ---
def load_vosk_model():
    # Priority: Large EN-IN (High Accuracy) > Small EN-IN (Fast) > Generic Model
    model_options = [
        "vosk-model-en-in-0.5",
        "vosk-model-small-en-in-0.4",
        "model"
    ]
    
    for m in model_options:
        if os.path.exists(m):
            try:
                print(f"[SYSTEM] Initializing Sensory Input with: {m}")
                return Model(m)
            except Exception as e:
                print(f"[WARNING] Failed to load model {m}: {e}")
    
    print("[ERROR] No Vosk models found. Please run 'setup_indian_vosk.py'.")
    return None

vosk_model = load_vosk_model()
rec = KaldiRecognizer(vosk_model, 16000) if vosk_model else None

# --- SKILL ENGINE ---
def run_skill(skill_name, params=None):
    """Executes Jarvis skills (like speech or system commands)."""
    print(f"[SKILL] Executing: {skill_name} with {params}")
    if skill_name == "speak":
        text = params.get("text", "")
        # Notify the UI that Jarvis is talking
        socketio.emit('jarvis_speaking', {'text': text})
        print(f"JARVIS: {text}")

def system_monitor():
    """Returns a dictionary of real-time hardware health."""
    import psutil
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    return {
        "cpu": cpu,
        "ram": ram,
        "battery": None if not battery else {
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
        },
    }

# --- NETWORKING & UI ROUTES ---
@app.route('/')
def index():
    from datetime import datetime
    date_str = datetime.now().strftime("%d %b %Y")
    return render_template('index.html', date_str=date_str)

@app.route('/lab')
def lab():
    return render_template('lab.html', os=os)

@app.route('/api/topology')
def api_topology():
    engine = TopologyEngine(os.getcwd())
    return engine.get_topology()

@socketio.on('ui_command')
def on_ui_command(data):
    """Entry point for commands sent from the browser HUD."""
    text = data.get("text", "") if isinstance(data, dict) else str(data)
    if text.strip():
        if core is None:
            socketio.emit("new_message", {"sender": "jarvis", "text": "Core unavailable. Check API Key."})
            return
        process_intent(text.strip())

@socketio.on('update_brain_provider')
def on_update_brain(data):
    """Updates the active AI provider in the Autonomous Core."""
    provider = data.get("provider", "auto")
    if core:
        core.set_active_provider(provider)
        print(f"[SYSTEM] HUD update: Active Brain set to {provider.upper()}")

def run_web_server():
    # Use allow_unsafe_werkzeug to permit running inside the JARVIS environment
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

# --- SENSORY INPUT (VOICE) ---
INTERRUPT_ALLOWLIST = {"stop", "jarvis", "wait", "cancel", "shut up", "hush", "stark"}

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

def listen_loop():
    """Main voice recognition loop with Smart Barge-In & Noise Filtering."""
    print("[SYSTEM] Voice Recognition Active...")
    try:
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                channels=1, callback=audio_callback):
            while running:
                try:
                    data = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # 1. Smart Barge-In (The Filter)
                if audio_manager.is_speaking:
                    partial_str = rec.PartialResult()
                    if partial_str:
                        partial_data = json.loads(partial_str)
                        partial_text = partial_data.get("partial", "").strip().lower()
                        
                        # Only allow high-priority interrupts while JARVIS is speaking
                        if any(cmd in partial_text for cmd in INTERRUPT_ALLOWLIST):
                            print(f"[SYSTEM] Priority Interrupt Detected: '{partial_text}'")
                            audio_manager.stop_speaking()
                        else:
                            # Silence the "self-listening" noise
                            continue

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    user_text = result.get("text", "").strip()
                    
                    if not user_text:
                        continue

                    # 2. Heuristic Nonsense Filter
                    # Ignore 1-word or 2-letter fragments unless they are in allowlist (e.g. "fellow man", "selling imagine")
                    words = user_text.split()
                    is_interrupt = any(cmd in user_text.lower() for cmd in INTERRUPT_ALLOWLIST)
                    
                    if len(words) < 2 and not is_interrupt:
                        # print(f"[DEBUG] Noise Ignored: '{user_text}'")
                        continue
                    
                    # 3. Only process if not currently speaking (Echo Guard)
                    if not audio_manager.is_speaking or is_interrupt:
                        process_intent(user_text)
                    
    except Exception as e:
        print(f"[ERROR] listen_loop error: {e}")
    except Exception as e:
        print(f"[ERROR] listen_loop error: {e}")

def process_intent(user_input: str) -> None:
    """Updates UI and hands the intent to the autonomous core."""
    socketio.emit('new_message', {'sender': 'user', 'text': user_input})
    print(f"USER: {user_input}")
    if core:
        core.set_user_input(user_input)

def system_log_loop():
    """Continuously sends system health updates to the UI."""
    while running:
        status = system_monitor()
        socketio.emit('system_status', {'status': status})
        time.sleep(10)


# --- MAIN ENTRY ---
if __name__ == "__main__":
    print("\n" + "="*30)
    print("--- JARVIS SYSTEM ONLINE ---")
    print("="*30 + "\n")

    try:
        # 1. Initialize the Core (The Brain)
        if chat_session is not None:
            # We pass the chat_session (stateful) instead of just the client
            core = start_autonomous_core(run_skill, system_monitor, chat_session, socketio)
        
        # 2. Start Services
        threading.Thread(target=run_web_server, daemon=True).start()
        threading.Thread(target=system_log_loop, daemon=True).start()

        # 3. Start Voice (Blocking Main Thread)
        if vosk_model:
            listen_loop()
        else:
            print("[ERROR] Voice system failed. JARVIS will only respond to UI text input.")
            while running:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SYSTEM] Administrator initiated shutdown. Gracefully safely exiting JARVIS...")
    finally:
        running = False
        if core:
            core.active = False
        print("[SYSTEM] System Offline. Goodbye.")