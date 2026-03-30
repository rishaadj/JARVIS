class PlannerAgent:
    def __init__(self, chat):
        self.chat = chat

    def plan(self, goal: str, visual_context: str = "", memory=None):
        print(f"[PLANNER AGENT] Planning for: {goal}")
        
        # 🧠 Semantic Recall
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
        - open_app: {{"text":"<app name>"}}
        - vision: {{}}
        - speak: {{"text":"<what to say>"}}
        - web_search: {{"query":"<search query>"}}
        - research: {{"topic":"<topic>"}} # Use for deep investigation or complex info gathering.
        - synthesize_skill: {{"skill_name":"<name>", "description":"<desc>", "requirements":"<reqs>"}} # Use to expand your own capabilities when a requested action isn't possible with current skills.
        - shell_execution: {{"command":"<shell command>"}}
        - list_files: {{"path":"<path>"}}
        - screen_capture: {{"filename":"<optional filename>"}}
        - screen_analysis: {{"action":"ocr"|"capture"}}
        - learn: {{"key":"<key>","fact":"<fact text>"}}
        - recall_memory: {{"key":"<key>"}}
        - system_monitor: {{}}
        - timer: {{"minutes": <int>, "label":"<label>"}}
        - volume: {{"action":"up"|"down"|"mute"}}
        - scheduler: {{"action":"schedule","delay_seconds": <int>,"skill_name":"<skill>","params":{{}}, "recurring": false}}
        - file_management: {{"action":"create_file|delete_file|move_file|rename_file|create_dir","path":"<path>","target":"<target>","content":"<content>"}}
        - mouse_control: {{"action":"move|click|drag|scroll|position","x":<int>,"y":<int>,"clicks":<int>,"button":"left|right|middle","amount":<int>}}
        - keyboard_control: {{"action":"type|press|hotkey","text":"<text>","key":"<key>","hotkey":["ctrl","c"]}}

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
                # Allow accidental "ACTION:" prefix, strip it.
                if line.upper().startswith("ACTION:"):
                    line = line[len("ACTION:"):].strip()
                steps.append(line)
            return steps[:5]

        except Exception as e:
            print("[PLANNER AGENT ERROR]", e)
            return []