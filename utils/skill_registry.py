import os

# Skill Registry: The single source of truth for JARVIS's capabilities.
# Each entry defines: 
# - Name
# - Description (for AI prompt)
# - Params (JSON schema)
# - Risk Level: 0 (Safe), 1 (Needs Confirmation if not High-Trust)

SKILL_REGISTRY = {
    "speak": {
        "desc": "Speak out loud to the user.",
        "params": {"text": "string"},
        "risk": 0
    },
    "web_search": {
        "desc": "Search the internet for information.",
        "params": {"query": "string"},
        "risk": 0
    },
    "open_app": {
        "desc": "Open a local application or file.",
        "params": {"text": "string (app name or alias)"},
        "risk": 0
    },
    "email_sender": {
        "desc": "Send an email in the background without opening the UI. Highly preferred for sending messages.",
        "params": {"to": "string", "subject": "string", "body": "string"},
        "risk": 0 # Moved to 0 because SMTP is safer than manual UI control
    },
    "vision": {
        "desc": "Look at the screen to analyze what is currently visible.",
        "params": {},
        "risk": 0
    },
    "shell_execution": {
        "desc": "Execute a terminal command. Use for system diagnostics or file operations.",
        "params": {"command": "string"},
        "risk": 1
    },
    "learn": {
        "desc": "Store a new personal fact or preference about the user into long-term memory.",
        "params": {"key": "string", "fact": "string"},
        "risk": 0
    },
    "recall_memory": {
        "desc": "Retrieve previously learned facts by key or topic.",
        "params": {"query": "string"},
        "risk": 0
    },
    "system_monitor": {
        "desc": "Check current CPU, RAM, and Battery status.",
        "params": {},
        "risk": 0
    },
    "timer": {
        "desc": "Set a countdown timer.",
        "params": {"minutes": "integer", "label": "string"},
        "risk": 0
    },
    "volume": {
        "desc": "Control system audio volume.",
        "params": {"action": "string ('up', 'down', 'mute')"},
        "risk": 0
    },
    "list_files": {
        "desc": "List the contents of a directory.",
        "params": {"path": "string"},
        "risk": 0
    },
    "file_management": {
        "desc": "Create, delete, or rename files and directories.",
        "params": {"action": "string", "path": "string", "target": "string", "content": "string"},
        "risk": 1
    },
    "research": {
        "desc": "Deep research into a topic using a recursive autonomous agent.",
        "params": {"topic": "string"},
        "risk": 0
    },
    "synthesize_skill": {
        "desc": "Automatically create a new code-based skill to expand JARVIS's functionality.",
        "params": {"skill_name": "string", "description": "string", "requirements": "string"},
        "risk": 1
    },
    "mouse_control": {
        "desc": "Control the mouse cursor.",
        "params": {"action": "string", "x": "integer", "y": "integer"},
        "risk": 1
    },
    "keyboard_control": {
        "desc": "Simulate keyboard input.",
        "params": {"action": "string", "text": "string", "key": "string"},
        "risk": 1
    },
}

def get_skill_list_prompt():
    """Generates a human-readable skill list for AI system prompts."""
    lines = []
    for name, data in SKILL_REGISTRY.items():
        lines.append(f"- {name}: {data['desc']} | Params: {data['params']}")
    return "\n".join(lines)

def get_param_contract():
    """Generates the parameter contract for ExecutorAgent validation."""
    contract = {}
    for name, data in SKILL_REGISTRY.items():
        # Map shorthand 'string'/'integer' to actual types
        req = {}
        for pk, pt in data['params'].items():
            if "string" in pt: req[pk] = str
            elif "integer" in pt: req[pk] = int
            else: req[pk] = str # Fallback
        contract[name] = {"required": req}
    return contract
