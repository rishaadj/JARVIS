import os
import shutil

def execute(params):
    action = params.get("action") # create_file, delete_file, move_file, rename_file, create_dir
    path = params.get("path")
    target = params.get("target") # for move/rename
    content = params.get("content", "") # for create_file

    if not action or not path:
        return "Sir, I need an action and a path to manage files."

    try:
        if action == "create_file":
            with open(path, 'w') as f:
                f.write(content)
            return f"Sir, I have successfully created the file at: {path}"
        elif action == "delete_file":
            if os.path.isfile(path):
                os.remove(path)
                return f"Sir, the file at {path} has been deleted."
            elif os.path.isdir(path):
                shutil.rmtree(path)
                return f"Sir, the directory at {path} has been completely removed."
            else:
                return f"Path {path} does not exist."
        elif action == "move_file":
            shutil.move(path, target)
            return f"Sir, I've moved the item from {path} to {target}."
        elif action == "rename_file":
            os.rename(path, target)
            return f"Sir, the file has been renamed to {target}."
        elif action == "create_dir":
            os.makedirs(path, exist_ok=True)
            return f"Sir, the new directory has been established at: {path}"
        else:
            return f"Unknown action: {action}"
    except Exception as e:
        return f"File management error: {e}"
