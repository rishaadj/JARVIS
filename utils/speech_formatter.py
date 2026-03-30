import re

def format_for_speech(text: str) -> str:
    """Clean text for natural-sounding speech."""
    # Remove Asterisks (actions like *nods*)
    text = re.sub(r'\*.*?\*', '', text)
    # Remove Markdown bold/italic
    text = text.replace("**", "").replace("__", "")
    # Remove code blocks
    text = re.sub(r'```.*?```', '[code block]', text, flags=re.DOTALL)
    # Convert abbreviations to spoken word if needed
    text = text.replace("CPU", "C.P.U.").replace("RAM", "ram")
    return text.strip()