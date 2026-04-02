import re

with open('e:/Projects/JARVIS/autonomous_core.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace act()
act_start = code.find('    def act(self, thought):')
act_end = code.find('    def _post_action_evaluate(self')

act_body = code[act_start:act_end]

new_idle_check = '''        if t_type == "idle":
            return

        if t_type == "interrupt":
            self.log(f"Interrupt Received: {t_data}", "system")
            if "gesture" in str(t_data).lower() or "hand" in str(t_data).lower():
                self.gesture_active = False
                if getattr(self, 'gesture_engine', None):
                    self.gesture_engine.stop()
                self._emit_jarvis_message("Physical gesture control deactivated.")
            self.task_queue.clear()
            self.active_goal = None
            return

        self._set_busy(True)

        def _async_act_worker():
            try:'''

original_idle_check = '''        if t_type == "idle":
            return'''

if original_idle_check in act_body:
    act_body_modified = act_body.replace(original_idle_check, new_idle_check)

    lines = act_body_modified.split('\n')
    worker_passed = False
    final_lines = []
    for line in lines:
        if 'def _async_act_worker():' in line:
            final_lines.append(line)
            worker_passed = True
        elif worker_passed:
            if line.strip() != '':
                final_lines.append('    ' + line)
            else:
                final_lines.append(line)
        else:
            final_lines.append(line)

    final_lines.append('            finally:')
    final_lines.append('                self._set_busy(False)')
    final_lines.append('        threading.Thread(target=_async_act_worker, daemon=True).start()')
    final_lines.append('')
    
    new_act_body = '\n'.join(final_lines)
    code = code.replace(act_body, new_act_body)

# Replace _post_action_evaluate
old_eval = '''    def _post_action_evaluate(self, last_action_text: str, result_text: str) -> None:
        if not self.active_goal: return
        try:
            status, suggestion = self.evaluator_agent.evaluate(self.active_goal, last_action_text, result_text)
            if (status or "").strip().lower() == "fail" and suggestion and suggestion.lower() != "none":
                self.task_queue.insert(0, suggestion)
                self.log(f"Recovery step queued: {suggestion}", "evaluator")
        except Exception as e:
            self.log(f"Evaluator Error: {e}", "error")'''

new_eval = '''    def _post_action_evaluate(self, last_action_text: str, result_text: str) -> None:
        if not self.active_goal: return
        def _eval_worker():
            try:
                status, suggestion = self.evaluator_agent.evaluate(self.active_goal, last_action_text, result_text)
                if (status or "").strip().lower() == "fail" and suggestion and suggestion.lower() != "none":
                    self.task_queue.insert(0, suggestion)
                    self.log(f"Recovery step queued: {suggestion}", "evaluator")
            except Exception as e:
                self.log(f"Evaluator Error: {e}", "error")
        threading.Thread(target=_eval_worker, daemon=True).start()'''

code = code.replace(old_eval, new_eval)

with open('e:/Projects/JARVIS/autonomous_core.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Done.")
