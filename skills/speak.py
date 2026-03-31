import asyncio
import edge_tts
import pygame
import numpy as np
import os
import time
import threading
from speech_formatter import format_for_speech
from utils.audio_manager import audio_manager

# Initialize pygame mixer for audio playback
if not pygame.mixer.get_init():
    pygame.mixer.init(frequency=24000) # Edge-TTS usually defaults to 24kHz

def get_rms(audio_data):
    """Calculate Root Mean Square (volume level) of audio data."""
    if len(audio_data) == 0:
        return 0
    # Convert to float to avoid overflow
    return np.sqrt(np.mean(audio_data.astype(float)**2))

async def generate_and_play(text, socketio=None, voice="en-GB-RyanNeural"):
    """Handle TTS generation, level analysis, and synchronized playback."""
    clean_text = format_for_speech(text)
    if not clean_text:
        return

    output_file = "speech_output.mp3"
    
    # 1. Generate TTS
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(output_file)

    if not os.path.exists(output_file):
        return

    try:
        # 2. Load Sound
        # Note: pygame.mixer.Sound can load MP3 if SDL_mixer has the codec
        sound = pygame.mixer.Sound(output_file)
        
        # 3. Get Raw Data for Analysis
        # We use sndarray to get the PCM bytes as a numpy array
        try:
            samples = pygame.sndarray.array(sound)
        except Exception as e:
            print(f"[SPEECH] Could not extract samples for pulse: {e}")
            samples = None

        # 4. Play
        audio_manager.start_speaking()
        channel = sound.play()
        
        start_time = time.time()
        duration = sound.get_length()

        # 5. Dynamic Sync Loop (Levels for HUD)
        if samples is not None and socketio:
            num_samples = len(samples)
            # Calculate how many samples per 50ms chunk
            chunk_size = int(num_samples * (0.05 / duration)) 
            
            for i in range(0, num_samples, chunk_size):
                if audio_manager.should_stop() or not channel.get_busy():
                    break
                
                # Calculate level for this chunk
                chunk = samples[i : i + chunk_size]
                level = get_rms(chunk)
                
                # Normalize level (0 to 100 approx)
                # Max value for 16-bit PCM is 32767
                norm_level = min(100, (level / 1500) * 100) 
                
                socketio.emit('voice_level', {'level': norm_level})
                
                # Small sleep to match playback tempo
                await asyncio.sleep(0.05)
        else:
            # Fallback if analysis fails
            while channel.get_busy() and not audio_manager.should_stop():
                await asyncio.sleep(0.1)

        # 6. Cleanup
        if audio_manager.should_stop():
            pygame.mixer.stop()
            if socketio:
                socketio.emit('voice_level', {'level': 0})
        
        audio_manager.stop_speaking()
        sound = None # Free memory

    except Exception as e:
        print(f"[SPEECH] Playback error: {e}")
    finally:
        try:
            if os.path.exists(output_file):
                os.remove(output_file)
        except:
            pass

def execute(params):
    """The entry point called by the ExecutorAgent."""
    text = params.get("text", "")
    socketio = params.get("_socketio") # Injected by AutonomousCore
    
    if text:
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(generate_and_play(text, socketio))
        finally:
            loop.close()
    return f"Speaking: {text}"