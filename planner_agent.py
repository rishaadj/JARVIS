from utils.skill_registry import get_skill_list_prompt

class PlannerAgent:
    def __init__(self, chat):
        self.chat = chat

    def plan(self, goal: str, visual_context: str = "", memory=None):
        print(f"[PLANNER AGENT] Planning for: {goal}")
        
        past_memories = ""
        if memory:
            results = memory.search_semantic(goal, top_k=3)
            if results:
                past_memories = "\n".join([f"- {m['text']}" for _, m in results])

        prompt = f"""
        You are JARVIS.

        Relevant Past Experiences:
        {past_memories if past_memories else "None"}

        Current Visual Context (Last scan):
        {visual_context}

        Goal:
        {goal}

        Break this goal into at most 5 executable skill invocations.

        Output format:
        - Return ONLY lines.
        - Each line MUST be exactly:
          <skill_name>: <json_params>
        - json_params must be a JSON object.

        Supported skills and their params:
        {get_skill_list_prompt()}

        Strategies:
        1. If a goal requires info you don't have, use `research` first.
        2. If a goal requires a new tool (e.g. "Control Spotify"), use `synthesize_skill` to create it.
        3. Break complex goals into clear, logical steps.

        Notes:
        - If you need to talk to the user, use speak with params like {{"text":"..."}}.
        - Keep actions safe and minimal.

        """

        try:
            response = self.chat.send_message(prompt)
            plan_text = response.text.strip()

            steps: list[str] = []
            for line in plan_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.upper().startswith("ACTION:"):
                    line = line[len("ACTION:"):].strip()
                steps.append(line)
            return steps[:5]

        except Exception as e:
            print("[PLANNER AGENT ERROR]", e)
            return []