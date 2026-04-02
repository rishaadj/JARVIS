import os
import zipfile
import requests
import sys

def setup_indian_vosk():
    target_dir = "vosk-model-en-in-0.5"
    if os.path.exists(target_dir):
        print(f"[SYSTEM] Model '{target_dir}' already exists.")
        return
        
    url = "https://alphacephei.com/vosk/models/vosk-model-en-in-0.5.zip"
    zip_path = "vosk-model-en-in.zip"
    
    print("="*40)
    print("--- JARVIS SENSORY UPGRADE ---")
    print(f"Downloading High-Accuracy Indian English Model...")
    print(f"Size: ~1GB (This depends on your connection speed)")
    print("="*40)
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): 
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        done = int(50 * downloaded / total_size)
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded//(1024*1024)}MB / {total_size//(1024*1024)}MB")
                        sys.stdout.flush()
        print("\n\n[SYSTEM] Download complete. Extracting...")
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        return
        
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Cleanup
        os.remove(zip_path)
        print(f"[SUCCESS] High-Accuracy Indian English Model is now ready in '{target_dir}'.")
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")

if __name__ == "__main__":
    setup_indian_vosk()
