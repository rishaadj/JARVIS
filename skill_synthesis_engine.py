import os
import importlib.util
from coder_agent import CoderAgent
from safety_manager import safety_manager

class SkillSynthesisEngine:
    def __init__(self, chat, executor):
        self.coder = CoderAgent(chat)
        self.executor = executor
        self.skills_dir = os.path.join(os.path.dirname(__file__), "skills")

    def synthesize_skill(self, skill_name: str, description: str, requirements: str):
        print(f"[SYNTHESIS ENGINE] Synthesizing new capability: {skill_name}")

        code = self.coder.generate_skill_code(skill_name, description, requirements)
        if code.startswith("# Coder Error:"):
            return f"Synthesis Failed: {code}"

        ok, err = self.coder.validate_code(code)
        if not ok:
            return f"Validation Failed: {err}"

        test_file = os.path.join(self.skills_dir, f"test_{skill_name}.py")
        with open(test_file, "w") as f:
            f.write(code)

        print(f"[SYNTHESIS ENGINE] Running auto-test for: {skill_name}")
        test_result = self.executor.execute_skill(f"test_{skill_name}", {})
        
        retries = 2
        while retries > 0:
            if "Error" not in f"{test_result}":
                break
                
            print(f"[SYNTHESIS ENGINE] Test Failed: {test_result}. Attempting self-correction ({retries} left).")
            code = self.coder.generate_skill_code(skill_name, description, requirements, previous_error=str(test_result))
            
            if not code.startswith("# Coder Error:"):
                with open(test_file, "w") as f:
                    f.write(code)
                test_result = self.executor.execute_skill(f"test_{skill_name}", {})
            
            retries -= 1

        if "Error" in f"{test_result}":
            os.remove(test_file)
            return f"Synthesis failed after multiple attempts. Last error: {test_result}"

        final_file = os.path.join(self.skills_dir, f"{skill_name}.py")
        with open(final_file, "w") as f:
            f.write(code)
        
        os.remove(test_file)

        safety_manager.audit_log("SYNTESIS_ENGINE", "create_skill", {"skill": skill_name}, "SUCCESS", "Autonomously synthesized.")

        return f"Sir, the new capability '{skill_name}' has been successfully synthesized and integrated."
