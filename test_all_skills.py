import os
import importlib.util
import sys

def test_skills():
    skills_dir = "skills"
    if not os.path.exists(skills_dir):
        print(f"FAILED: {skills_dir} directory not found.")
        return

    sys.path.insert(0, os.getcwd())

    files = [f for f in os.listdir(skills_dir) if f.endswith(".py") and not f.startswith("__")]
    
    print(f"--- ANALYZING {len(files)} SKILLS ---")
    
    success_count = 0
    fail_count = 0
    
    for f in files:
        skill_name = f[:-3]
        file_path = os.path.join(skills_dir, f)
        
        try:
            spec = importlib.util.spec_from_file_location(skill_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "execute"):
                print(f"OK: {skill_name}")
                success_count += 1
            else:
                print(f"MISSING_EXECUTE: {skill_name}")
                fail_count += 1
        except Exception as e:
            print(f"IMPORT_ERROR: {skill_name} - {e}")
            fail_count += 1
            
    print("---------------------------")
    print(f"TOTAL SKILLS: {len(files)}")
    print(f"SUCCESSFUL: {success_count}")
    print(f"FAILED: {fail_count}")

if __name__ == "__main__":
    test_skills()
