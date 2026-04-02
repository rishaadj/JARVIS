import os
import zipfile
import requests
import sys

def setup_small_vosk():
    target_dir = "vosk-model-small-en-in-0.4"
    if os.path.exists(target_dir):
        print(f"[SYSTEM] Model '{target_dir}' already exists.")
        return
        
    url = f"https://alphacephei.com/vosk/models/{target_dir}.zip"
    zip_path = f"{target_dir}.zip"
    
    print("="*40)
    print("--- JARVIS RESOURCE OPTIMIZATION ---")
    print(f"Downloading Light Indian English Model...")
    print(f"Size: ~12MB (Fast download)")
    print("="*40)
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("[SYSTEM] Download complete. Extracting...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        os.remove(zip_path)
        print(f"[SUCCESS] Light Model is now ready in '{target_dir}'.")
    except Exception as e:
        print(f"[ERROR] Setup failed: {e}")

if __name__ == "__main__":
    setup_small_vosk()
