import os

def execute(params):
    # Get the path from params, default to current directory if not provided
    path = params.get("path", ".")
    
    # Clean up the path (handling cases where Gemini might send 'C users risha')
    if path != "." and ":" not in path:
        # Simple fix for 'C users risha' -> 'C:/users/risha'
        path = path.replace(" ", "/")
        if not path.startswith("C:"):
             path = "C:/" + path

    try:
        # Expand user path (handles things like ~/Desktop)
        full_path = os.path.abspath(os.path.expanduser(path))
        
        if not os.path.exists(full_path):
            return f"Sir, the directory at {path} does not exist."

        files = os.listdir(full_path)
        if not files:
            return f"Sir, the directory '{full_path}' is empty."
        else:
            file_list = [f" - {f}" for f in files]
            return f"Sir, I've retrieved the contents of {path}:\n" + "\n".join(file_list)
    except Exception as e:
        return f"Sir, I encountered an error while accessing the directory: {e}"