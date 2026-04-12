import subprocess
import os

def execute(params):
    file_path = params.get("path")
    
    if not file_path or not os.path.exists(file_path):
        print(f"JARVIS: I cannot find the file at {file_path}, Sir.")
        return False

    print(f"JARVIS: Executing {os.path.basename(file_path)}...")
    try:
        result = subprocess.run(["python", file_path], capture_output=True, text=True)
        print("-" * 30)
        print(result.stdout)
        if result.stderr:
            print(f"Errors:\n{result.stderr}")
        print("-" * 30)
    except Exception as e:
        print(f"JARVIS: Failed to run the script. Error: {e}")
    
    return True