import os
import fitz
from PIL import Image

def execute(params):
    input_file = params.get("filename")
    target_format = params.get("target_format", "jpg").lower().strip(".")
    
    if not input_file or not os.path.exists(input_file):
        print(f"JARVIS: I can't find the file '{input_file}', Sir.")
        return False

    base_name = os.path.splitext(input_file)[0]
    ext = os.path.splitext(input_file)[1].lower()

    try:
        if ext == ".pdf":
            doc = fitz.open(input_file)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                output_path = f"{base_name}_page_{page_num+1}.{target_format}"
                pix.save(output_path)
            doc.close()
            print(f"JARVIS: PDF converted. Created {len(doc)} {target_format} files.")

        elif ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"]:
            img = Image.open(input_file)
            if target_format in ["jpg", "jpeg"] and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            output_path = f"{base_name}.{target_format}"
            img.save(output_path)
            print(f"JARVIS: Image converted to {target_format} successfully.")

        else:
            print(f"JARVIS: I don't have a handler for {ext} files yet, Sir.")
            
    except Exception as e:
        print(f"JARVIS: The conversion failed. Error: {e}")
    
    return True