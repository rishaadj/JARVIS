import os
import subprocess
import platform

def execute(params):
    """
    Skill: Open Application
    Params: {'text': 'application name'}
    """
    app_name = params.get("text", "").lower().strip()
    if not app_name:
        return "No application name provided, Sir."

    system = platform.system()

    try:
        if system == "Windows":
            # `start` is a cmd.exe internal command; invoke cmd explicitly for reliability.
            # The empty string after `start` is the window title parameter.
            subprocess.Popen(["cmd", "/c", "start", "", app_name], shell=False)
            return f"Opening {app_name}."
            
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", app_name])
            return f"Launching {app_name} for you."
            
        elif system == "Linux":
            subprocess.Popen([app_name], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            return f"Starting {app_name}."

    except Exception as e:
        return f"I encountered an error trying to open {app_name}: {str(e)}"

# For testing independently
if __name__ == "__main__":
    print(execute({"text": "notepad"}))