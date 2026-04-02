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

        # 1. Coder Generates Code
        code = self.coder.generate_skill_code(skill_name, description, requirements)
        if code.startswith("# Coder Error:"):
            return f"Synthesis Failed: {code}"

        # 2. Basic Validation (Done in CoderAgent already, but just in case)
        ok, err = self.coder.validate_code(code)
        if not ok:
            return f"Validation Failed: {err}"

        # 3. Save as temporary skill for testing
        test_file = os.path.join(self.skills_dir, f"test_{skill_name}.py")
        with open(test_file, "w") as f:
            f.write(code)

        # 4. Auto-Test Loop
        print(f"[SYNTHESIS ENGINE] Running auto-test for: {skill_name}")
        # Try to run it with empty/default params or sample params.
        test_result = self.executor.execute_skill(f"test_{skill_name}", {})
        
        # 5. Review & Self-Correction Loop
        retries = 2
        while retries > 0:
            if "Error" not in f"{test_result}":
                break
                
            print(f"[SYNTHESIS ENGINE] Test Failed: {test_result}. Attempting self-correction ({retries} left).")
            # Feed back the error to the coder
            code = self.coder.generate_skill_code(skill_name, description, requirements, previous_error=str(test_result))
            
            if not code.startswith("# Coder Error:"):
                with open(test_file, "w") as f:
                    f.write(code)
                # Re-test
                test_result = self.executor.execute_skill(f"test_{skill_name}", {})
            
            retries -= 1

        if "Error" in f"{test_result}":
            os.remove(test_file)
            return f"Synthesis failed after multiple attempts. Last error: {test_result}"

        # 6. Final Registration (Save to permanent file)
        final_file = os.path.join(self.skills_dir, f"{skill_name}.py")
        with open(final_file, "w") as f:
            f.write(code)
        
        # Cleanup test file
        os.remove(test_file)

        # 7. Audit Logging
        safety_manager.audit_log("SYNTESIS_ENGINE", "create_skill", {"skill": skill_name}, "SUCCESS", "Autonomously synthesized.")

        return f"Sir, the new capability '{skill_name}' has been successfully synthesized and integrated."
