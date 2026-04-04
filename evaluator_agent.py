class EvaluatorAgent:
    def __init__(self, chat):
        self.chat = chat

    def evaluate(self, goal, last_action, result=""):
        prompt = f"""
You are the EVALUATOR agent of JARVIS.

Goal:
{goal}

Last Action Attempted:
{last_action}

Result of Action:
{result}

Decide:
1. Was this successful? (Did it move us closer to the goal?)
2. If it FAILED (errors, app not found, etc.), what is the next logical step to fix it?
   - If an app is missing, suggest 'web_search' or 'research'.
   - If a file is missing, suggest 'list_files'.
   - If a command failed, suggest researching the error.

Respond ONLY:
STATUS: success / fail
SUGGESTION: <next action in the same format: "ACTION: <skill_name>: {{...}}" or "none">
"""

        try:
            response = self.chat.send_message(prompt)
            text = response.text.strip()

            status = "unknown"
            suggestion = "none"

            for line in text.split("\n"):
                if "STATUS:" in line:
                    status = line.split("STATUS:")[1].strip().lower()
                if "SUGGESTION:" in line:
                    # Important: do NOT lowercase suggestion; it may contain JSON or casing-sensitive values.
                    suggestion = line.split("SUGGESTION:")[1].strip()

            return status, suggestion

        except Exception as e:
            print("[EVALUATOR ERROR]", e)
            return "unknown", "none"