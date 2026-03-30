import ast

class CoderAgent:
    def __init__(self, chat):
        self.chat = chat

    def generate_skill_code(self, skill_name: str, description: str, requirements: str, previous_error: str = ""):
        print(f"[CODER AGENT] Generating code for skill: {skill_name}")

        error_feedback = ""
        if previous_error:
            error_feedback = f"""
            
            PREVIOUS ATTEMPT FAILED: {previous_error}
            Please analyze the error and fix it.
            """

        prompt = f"""
        You are the Head Coder for JARVIS. 
        Your task is to write a single Python file for a "Skill" that satisfies the following:

        Skill Name: "{skill_name}"
        Description: "{description}"
        Requirements: "{requirements}"
        {error_feedback}

        CONTRACT:
        - The file MUST HAVE an `execute(params: dict)` function.
        - Parameters are passed via the `params` dictionary.
        - The `execute` function MUST return a string (the result/feedback).
        - Use shared JARVIS helpers if needed: `from speech_formatter import format_speech`.
        - All imports must be standard libraries or already part of the project (pyautogui, requests, etc.).
        - If you need external libraries, mention it in a comment at the top.

        Format:
        Return ONLY the Python code. DO NOT wrap it in Markdown triple backticks unless you are 100% sure the parser handles it. Ideally just the raw code.
        """

        try:
            response = self.chat.send_message(prompt)
            code = response.text.strip()
            # Basic validation
            ast.parse(code)
            return code
        except SyntaxError as e:
            return self.generate_skill_code(skill_name, description, requirements, f"Syntax Error: {e}")
        except Exception as e:
            print("[CODER AGENT ERROR]", e)
            return f"# Coder Error: {e}"

    def validate_code(self, code: str):
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)
