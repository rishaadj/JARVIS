import re


def format_for_speech(text: str, max_len: int = 1200) -> str:
    """
    Minimal text normalization for TTS.
    - trims whitespace
    - collapses repeated whitespace/newlines
    - strips characters that can cause TTS failures in some engines
    """
    if text is None:
        return ""

    s = str(text).strip()
    if not s:
        return ""

    # Collapse whitespace/newlines.
    s = re.sub(r"\s+", " ", s)

    # Remove some uncommon control characters.
    s = s.replace("\u200b", "")

    # Hard cap to keep TTS generation from exploding.
    if len(s) > max_len:
        s = s[:max_len].rstrip()

    return s

