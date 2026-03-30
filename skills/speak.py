import asyncio
import edge_tts
import pygame
import os
from speech_formatter import format_for_speech

# Initialize pygame mixer for audio playback
if not pygame.mixer.get_init():
    pygame.mixer.init()

async def generate_and_play(text, voice="en-GB-RyanNeural"):
    """Internal function to handle TTS generation and playback."""
    clean_text = format_for_speech(text)
    if not clean_text:
        return

    output_file = "speech_output.mp3"
    
    # Generate TTS
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(output_file)

    # Play TTS
    pygame.mixer.music.load(output_file)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    
    pygame.mixer.music.unload()
    try:
        os.remove(output_file)
    except:
        pass

def execute(params):
    """The entry point called by the ExecutorAgent."""
    text = params.get("text", "")
    if text:
        # Run the async function in a synchronous wrapper
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_and_play(text))
        loop.close()