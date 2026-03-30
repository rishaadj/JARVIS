import os
import importlib.util

SKILLS_DIR = os.path.abspath("./skills")

def execute(params):
    skill_name = params.get("skill_name")
    test_params = params.get("test_params", {})
    
    if not skill_name:
        return "JARVIS: Please specify which skill to test."

    skill_path = os.path.join(SKILLS_DIR, f"{skill_name}.py")
    if not os.path.exists(skill_path):
        return f"JARVIS: Skill '{skill_name}' not found for testing."

    try:
        spec = importlib.util.spec_from_file_location(skill_name, skill_path)
        if spec is None or spec.loader is None:
            return f"Sir, I'm unable to load '{skill_name}' for testing. The module structure appears invalid."
        
        module = importlib.util.module_from_spec(spec) # type: ignore
        spec.loader.exec_module(module) # type: ignore
        
        # Run the execute function
        result = module.execute(test_params)
        
        # Log the test result
        log_path = os.path.join(SKILLS_DIR, "test_run.log")
        with open(log_path, "a") as log:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{timestamp}] Test: {skill_name} | Params: {test_params} | Result: {result}\n")
            
        return f"Sir, the test run for '{skill_name}' is complete. The result was: {result}"
    except Exception as e:
        # Log the failure
        log_path = os.path.join(SKILLS_DIR, "test_run.log")
        with open(log_path, "a") as log:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"[{timestamp}] Test FAILED: {skill_name} | Error: {e}\n")
        return f"Sir, the test run for '{skill_name}' failed. Error encountered: {e}"
