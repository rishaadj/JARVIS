import asyncio
import edge_tts
import os
import time
import threading
from speech_formatter import format_for_speech
from utils.audio_manager import audio_manager

# --- Global Lock for Thread-Safe Speech (pyttsx3) ---
speech_lock = threading.Lock()


# --- Dependency Check & Optional Imports ---
HAS_PYGAME = False
try:
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=24000)
    import numpy as np
    HAS_PYGAME = True
except ImportError:
    print("[SPEECH] Pygame not found. HUD Pulse mapping disabled. Using pyttsx3 fallback.")

def get_rms(audio_data):
    """Calculate Root Mean Square (volume level) of audio data."""
    if not HAS_PYGAME or len(audio_data) == 0:
        return 0
    return np.sqrt(np.mean(audio_data.astype(float)**2))

async def generate_and_play(text, socketio=None, voice="en-GB-RyanNeural"):
    """Handle TTS generation, level analysis, and synchronized playback."""
    clean_text = format_for_speech(text)
    if not clean_text:
        return

    # --- STRATEGY A: High-Quality Edge-TTS (Requires Pygame + MP3 support) ---
    if HAS_PYGAME:
        output_file = "speech_output.mp3"
        try:
            communicate = edge_tts.Communicate(clean_text, voice)
            await communicate.save(output_file)

            if os.path.exists(output_file):
                sound = pygame.mixer.Sound(output_file)
                samples = None
                try:
                    samples = pygame.sndarray.array(sound)
                except:
                    pass

                audio_manager.start_speaking()
                channel = sound.play()
                duration = sound.get_length()

                if samples is not None and socketio:
                    num_samples = len(samples)
                    chunk_size = int(num_samples * (0.05 / duration)) 
                    for i in range(0, num_samples, chunk_size):
                        if audio_manager.should_stop() or not channel.get_busy():
                            break
                        chunk = samples[i : i + chunk_size]
                        level = get_rms(chunk)
                        norm_level = min(100, (level / 1500) * 100) 
                        socketio.emit('voice_level', {'level': norm_level})
                        await asyncio.sleep(0.05)
                else:
                    while channel.get_busy() and not audio_manager.should_stop():
                        await asyncio.sleep(0.1)

                if audio_manager.should_stop():
                    pygame.mixer.stop()
                
                audio_manager.stop_speaking()
                return # SUCCESS
        except Exception as e:
            print(f"[SPEECH] Online TTS failed: {e}. Switching to offline fallback...")
        finally:
            if os.path.exists(output_file):
                try: os.remove(output_file)
                except: pass

    # --- STRATEGY B: Offline Robust Fallback (pyttsx3) ---
    try:
        def run_offline():
            with speech_lock:
                audio_manager.start_speaking()
                engine = pyttsx3.init()
                # Slightly Stark-like voice profile (clear, measured)
                engine.setProperty('rate', 175)
                engine.setProperty('volume', 1.0)
                engine.say(clean_text)
                engine.runAndWait()
                audio_manager.stop_speaking()

        threading.Thread(target=run_offline, daemon=True).start()
    except Exception as e:
        print(f"[SPEECH] Offline Fallback failed: {e}")
        audio_manager.stop_speaking()

def execute(params):
    """The entry point called by the ExecutorAgent."""
    text = params.get("text", "")
    socketio = params.get("_socketio")
    
    if text:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(generate_and_play(text, socketio))
        finally:
            loop.close()
    return f"Speaking: {text}"