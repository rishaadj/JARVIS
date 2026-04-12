import os

SKILLS_DIR = os.path.abspath("./skills")

def execute(params):
    skill_name = params.get("skill_name")
    code = params.get("code")
    plan = params.get("plan", "No explicit plan provided.")
    
    if not skill_name or not code:
        return "Sir, I require both a skill name and the code payload to synthesize a new capability."

    import ast
    try:
        ast.parse(code)
    except SyntaxError as e:
        return f"Sir, I've halted the synthesis. The provided code failed validation due to a syntax error: {e}"

    file_path = os.path.join(SKILLS_DIR, f"{skill_name}.py")
    log_path = os.path.join(SKILLS_DIR, "synthesis.log")
    
    from safety_manager import safety_manager
    try:
        with open(file_path, "w") as f:
            f.write(code)
        
        safety_manager.audit_log("SKILL_TOOL", "create_skill", {"skill": skill_name}, "SUCCESS", f"Manual creation via tool. Plan: {plan}")
            
        return f"Sir, the new skill '{skill_name}' has been successfully validated, logged, and integrated into my cognitive systems."
    except Exception as e:
        safety_manager.audit_log("SKILL_TOOL", "create_skill", {"skill": skill_name}, "FAILED", str(e))
        return f"Sir, I encountered a system error while integrating the new skill: {e}"