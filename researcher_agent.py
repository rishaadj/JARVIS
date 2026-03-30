class ResearcherAgent:
    def __init__(self, chat):
        self.chat = chat

    def research(self, topic: str, current_context: str):
        print(f"[RESEARCHER AGENT] Deep investigation: {topic}")

        prompt = f"""
        You are the Research Specialist for JARVIS. 
        Your goal is to gather detailed information to help the Planner solve a task.

        Topic: "{topic}"
        Context: "{current_context}"

        Instructions:
        1. Breakdown the topic into specific questions.
        2. Synthesize a "Research Report" that is concise but factually rich.
        3. Identify any risks or technical requirements related to this topic.

        Respond with ONLY the markdown-formatted report.
        """

        try:
            response = self.chat.send_message(prompt)
            report = response.text.strip()
            return report
        except Exception as e:
            print("[RESEARCHER AGENT ERROR]", e)
            return f"Researcher Error: {e}"
