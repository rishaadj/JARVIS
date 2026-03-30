class GoalAgent:
    def __init__(self, chat):
        self.chat = chat

    def generate_goal(self, system_status, memory):
        prompt = f"""
You are JARVIS.

System Status:
{system_status}

Memory:
{memory}

Decide:
- Should a goal be created?

Respond ONLY:

GOAL: <goal or none>
"""

        try:
            response = self.chat.send_message(prompt)
            text = response.text.strip()

            if "GOAL:" in text:
                goal = text.split("GOAL:")[1].strip().lower()
                return goal

        except Exception as e:
            print("[GOAL AGENT ERROR]", e)

        return "none"