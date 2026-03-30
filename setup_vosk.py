import os
import zipfile
import requests # type: ignore

def setup_vosk_model():
    model_dir = "model"
    if os.path.exists(model_dir):
        print("Vosk model already exists.")
        return
        
    url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    zip_path = "vosk-model.zip"
    
    print("Downloading Vosk model (~40MB, this might take a minute)...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
    except Exception as e:
        print(f"Download failed: {e}")
        return
        
    print("Extracting model...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    os.rename("vosk-model-small-en-us-0.15", model_dir)
    os.remove(zip_path)
    print("Vosk model ready.")

if __name__ == "__main__":
    setup_vosk_model()
