import re

def format_for_speech(text: str) -> str:
    """Clean text for natural-sounding speech."""
    text = re.sub(r'\*.*?\*', '', text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r'```.*?```', '[code block]', text, flags=re.DOTALL)
    text = text.replace("CPU", "C.P.U.").replace("RAM", "ram")
    return text.strip()