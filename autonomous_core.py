import time
import threading
import sys
import os
import queue
import json
from collections import deque
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from planner_agent import PlannerAgent
from executor_agent import ExecutorAgent
from monitor_agent import MonitorAgent
from evaluator_agent import EvaluatorAgent
from memory_manager import MemoryManager
from goal_agent import GoalAgent
from researcher_agent import ResearcherAgent
from coder_agent import CoderAgent
from skill_synthesis_engine import SkillSynthesisEngine
from safety_manager import safety_manager
from visual_observer import VisualObserver
from system_sentinel import SystemSentinel
from gesture_engine import GestureEngine
from utils.gemini_rotator import QuotaExceededError
from utils.skill_registry import SKILL_REGISTRY, get_skill_list_prompt

class AutonomousCore:
    def __init__(self, run_skill_fn, system_monitor_fn, chat_obj, socketio_obj=None):
        self.active = True
        self.run_skill_callback = run_skill_fn
        self.system_monitor = system_monitor_fn
        self.chat = chat_obj
        self.socketio = socketio_obj
        self.active_provider = "auto"

        self.memory = MemoryManager(self.chat)
        self.goal_agent = GoalAgent(self.chat)
        self.planner_agent = PlannerAgent(self.chat)
        self.executor_agent = ExecutorAgent(self.run_skill)
        self.monitor_agent = MonitorAgent(self.system_monitor)
        self.evaluator_agent = EvaluatorAgent(self.chat)

        self.researcher_agent = ResearcherAgent(self.chat)
        self.coder_agent = CoderAgent(self.chat)
        self.synthesis_engine = SkillSynthesisEngine(self.chat, self.executor_agent)

        self.visual_observer = VisualObserver(self.chat, self.socketio, memory_obj=self.memory)
        self.visual_observer.start()

        # [AGENTIC UPGRADE]: Unified Event Bus instead of fragmented polling queues
        self.event_bus = queue.PriorityQueue()
        
        self.sentinel = SystemSentinel(self.monitor_agent, safety_manager, self.event_bus)
        self.sentinel.start()

        try:
            self.gesture_engine = GestureEngine(self.socketio)
        except Exception as e:
            self.log(f"Gesture Engine failed to initialize: {e}", "error")
            self.gesture_engine = None
        self.gesture_active = False

        self.last_goal_check = time.time()
        self.goal_check_interval = 1800
        self.cooldown_until = 0

        self.task_queue: list[str] = [] # Legacy support for Evaluator queueing
        self.active_goal: str | None = None

        self.context_buffer = deque(maxlen=5)

        self.state = {
            "last_action": None,
            "system_status": "nominal",
            "is_busy": False,
            "current_focus": None
        }

        allow_env = os.getenv("JARVIS_ALLOW_DANGEROUS", "").strip().lower()
        self.allow_dangerous = allow_env in {"1", "true", "yes", "y", "on"}

        self.dangerous_skills = {name for name, data in SKILL_REGISTRY.items() if data.get("risk", 0) == 1}

        self.pending_confirmation: dict | None = None

        # [AGENTIC UPGRADE]: Strict JSON Output enforcing for functional reliability
        self.CORE_SYSTEM_PROMPT = f"""
You are JARVIS, a highly advanced autonomous AI system.
Recent Context: {{context_snapshot}}
Visual Awareness (Last Scan): {{v_ctx}}
Relevant Past Experiences:
{{past_memories}}

User Input or Event: "{{user_input}}"

Analyze the input and decide the next logical actions.
You MUST respond with a pure JSON array containing the tools to execute.
Do NOT wrap it in markdown block quotes (no ```json). Output RAW JSON ONLY.
Format:
[
  {{"skill": "<skill_name>", "params": {{"key": "value"}} }}
]

Proactive Strategy:
1. Prefer direct background skills (email_sender, web_search, file_management) over opening UI apps.
2. If simply having a conversation, use the `speak` skill.
3. Only use 'vision' skill if explicitly asked to analyze the screen.
4. Try to satisfy the request fully in one response using multiple tools if necessary.

Supported skills schema to use in your JSON:
{get_skill_list_prompt()}
"""

    def run_skill(self, skill_name, params):
        if skill_name == "research":
            topic = params.get("topic")
            context = params.get("context", str(self.active_goal))
            return self.researcher_agent.research(topic, context)
        if skill_name == "synthesize_skill":
            name = params.get("skill_name")
            desc = params.get("description")
            reqs = params.get("requirements")
            return self.synthesis_engine.synthesize_skill(name, desc, reqs)
        return self.run_skill_callback(skill_name, params)

    def _set_busy(self, busy: bool) -> None:
        self.state["is_busy"] = busy
        if self.socketio:
            self.socketio.emit("state_change", "processing" if busy else "idle")

    def _set_action(self) -> None:
        if self.socketio:
            self.socketio.emit("state_change", "action")

    def _emit_jarvis_message(self, text: str) -> None:
        safe_text = str(text).strip()
        if self.socketio and safe_text:
            self.socketio.emit("new_message", {"sender": "jarvis", "text": safe_text})

    def set_active_provider(self, provider: str):
        self.active_provider = provider

    def _inject_context(self, params: dict) -> dict:
        p = dict(params or {})
        if self.socketio: p["_socketio"] = self.socketio
        if self.memory: p["_memory"] = self.memory
        return p

    def log(self, message, type="info"):
        prefix = f"[{type.upper()}]"
        print(f"{prefix} {message}")
        if self.socketio:
            self.socketio.emit('system_log', f"{prefix} {message}")

    def _emit_agent_update(self, agent_name: str, status: str) -> None:
        if self.socketio:
            self.socketio.emit("agent_status", {"agent": agent_name, "status": status})

    def set_user_input(self, text: str):
        """Web HUD / Voice interrupt injection point. Puts high priority event on bus."""
        if text.strip():
            self.log(f"Priority Interrupt: '{text}'", "user")
            if self.pending_confirmation is None:
                self.task_queue.clear()
            self.event_bus.put((1, time.time(), {"type": "user_intent", "data": text}))

    def extract_json(self, raw_text: str) -> list:
        # Helper to forcefully extract JSON from models that ignore formatting rules
        raw_text = raw_text.strip()
        if '```json' in raw_text:
            raw_text = raw_text.split('```json')[1].split('```')[0].strip()
        elif '```' in raw_text:
            raw_text = raw_text.split('```')[1].split('```')[0].strip()
            
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and "skill" in parsed:
                return [parsed]
            elif isinstance(parsed, list):
                return parsed
        except BaseException as e:
            self.log(f"Failed to parse JSON schema: {e}. Raw Text was: {raw_text}", "error")
        return []

    def act(self, event):
        t_type = event["type"]
        t_data = event["data"]

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
            try:
                # 1. Background System Sentinel Alerts
                if t_type in ["file_created", "scheduled_task", "critical_load", "security_alert"]:
                    event_msg = t_data if isinstance(t_data, str) else event.get("message", "Unknown event.")
                    priority = event.get("priority", "normal")
                    self.log(f"System Event ({priority}): {event_msg}", "sentinel")
                    
                    if priority == "high":
                        self.executor_agent.execute_skill("speak", {"text": f"Sir, excuse the interruption. {event_msg}"})
                        self._emit_jarvis_message(f"Security/System Alert: {event_msg}")
                        self.task_queue.clear()
                        # Direct injection to brain via self-event
                        self.event_bus.put((2, time.time(), {"type": "user_intent", "data": f"SYSTEM CRITICAL ALERT: {event_msg}. Resolve this immediately."}))
                    return

                # 2. Security Confirmation Handling
                if t_type == "confirmation_response":
                    user_text = (t_data or "").strip().lower()
                    try:
                        if not self.pending_confirmation:
                            return
                        if user_text in {"confirm", "yes", "y", "proceed", "do it", "go"}:
                            pc = self.pending_confirmation
                            self.pending_confirmation = None
                            skill_name = pc["skill_name"]
                            params = pc["params"]
                            self._emit_jarvis_message(f"Confirmed. Executing `{skill_name}`...")
                            self._set_busy(True)
                            self._set_action()
                            result = self.executor_agent.execute_skill(skill_name, self._inject_context(params))
                            if result is not None:
                                self._emit_jarvis_message(str(result))
                            self._post_action_evaluate(f"{skill_name}", str(result))
                            return
                        if user_text in {"cancel", "no", "n", "stop", "abort"}:
                            self._emit_jarvis_message("Action Cancelled.")
                            self.pending_confirmation = None
                            return
                        self._emit_jarvis_message("Please reply with `CONFIRM` to run it, or `CANCEL` to abort.")
                    finally:
                        self._set_busy(False)
                    return

                # 3. Main Reasoning Loop & JSON Tool Agent
                if t_type == "user_intent":
                    lower_intent = t_data.lower()
                    
                    if self.pending_confirmation:
                        # Reroute to confirmation parsing
                        self.event_bus.put((1, time.time(), {"type": "confirmation_response", "data": t_data}))
                        return
                    
                    if any(w in lower_intent for w in ["stop", "cancel", "abort", "shut up"]):
                        self.event_bus.put((0, time.time(), {"type": "interrupt", "data": t_data}))
                        return

                    if "hand control" in lower_intent or "gesture mode" in lower_intent:
                        if "on" in lower_intent or "start" in lower_intent:
                            if self.gesture_engine:
                                self.gesture_active = True
                                self.gesture_engine.start()
                                self._emit_jarvis_message("Physical gesture control initiated. I'm watching your hands, Sir.")
                            else:
                                self._emit_jarvis_message("Cannot start gesture control: Module not initialized.")
                        else:
                            self.gesture_active = False
                            if getattr(self, 'gesture_engine', None): self.gesture_engine.stop()
                            self._emit_jarvis_message("Gesture control deactivated.")
                        return

                    self._set_busy(True)
                    v_ctx = self.visual_observer.get_context()
                    context_snapshot = "\n".join(list(self.context_buffer))
                    
                    personal_context = self.memory.load_memory()
                    persona_facts = "\n".join([f"- {k}: {v}" for k, v in personal_context.items()])

                    past_memories = persona_facts
                    results = self.memory.search_semantic(t_data, top_k=2)
                    if results:
                        sem_memories = "\n".join([f"- {m['text']}" for _, m in results])
                        past_memories += "\n" + sem_memories

                    prompt = self.CORE_SYSTEM_PROMPT.format(
                        context_snapshot=context_snapshot,
                        v_ctx=v_ctx,
                        past_memories=past_memories if past_memories else "None",
                        user_input=t_data
                    )

                    try:
                        self._emit_agent_update("planner", "Analyzing request via Neural Array...")
                        is_uncensored = (self.active_provider == "uncensored")
                        response = self.chat.send_message(prompt, uncensored=is_uncensored, forced_provider=self.active_provider)

                        if not response or not hasattr(response, 'text'):
                            self.log("Brain returned an empty or invalid response.", "error")
                            return

                        actions = self.extract_json(response.text)
                        
                        if not actions:
                            # Fallback if the LLM completely failed to output JSON
                            final_text = response.text.replace("```json", "").replace("```", "").strip()
                            self._emit_jarvis_message(final_text)
                            self.executor_agent.execute_skill("speak", {"text": final_text})
                            self.context_buffer.append(f"User: {t_data} | JARVIS: {final_text}")
                            self._compress_memory_if_needed()
                            return

                        self.context_buffer.append(f"User: {t_data} | JARVIS Tool Calls: {json.dumps(actions)}")

                        for act in actions:
                            skill_name = act.get("skill", "").strip().lower()
                            params = act.get("params", {})
                            
                            if not skill_name or skill_name in {"none", "null", "idle"}:
                                continue

                            self.state["last_action"] = {"skill": skill_name, "params": params}

                            if (not self.allow_dangerous) and (skill_name in self.dangerous_skills):
                                self.pending_confirmation = {"skill_name": skill_name, "params": params}
                                self._emit_jarvis_message(f"Security Alert: `{skill_name}` with params `{params}` requires confirmation.")
                                return

                            if skill_name == "vision":
                                self._set_action()
                                result = self.executor_agent.execute_skill("vision", self._inject_context(params))
                                if isinstance(result, str) and "SCREENSHOT_SAVED" in result:
                                    img_path = os.path.abspath(result.split(":", 1)[-1].strip())
                                    img = Image.open(img_path)
                                    vision_res = self.chat.send_message([f"Analyze screencap for: {t_data}", img], uncensored=is_uncensored, forced_provider=self.active_provider)
                                    if vision_res and hasattr(vision_res, 'text'):
                                        self._emit_jarvis_message(vision_res.text)
                                        self.executor_agent.execute_skill("speak", {"text": vision_res.text})
                                continue

                            self._set_action()
                            result = self.executor_agent.execute_skill(skill_name, self._inject_context(params))
                            if result is not None:
                                self._emit_jarvis_message(f"[{skill_name}]: ✓ done")
                                
                            self._post_action_evaluate(skill_name, str(result))

                        self._compress_memory_if_needed()

                    except QuotaExceededError as e:
                        self.log("CRITICAL: API EXHAUSTED. Hibernating.", "brain")
                        self.cooldown_until = time.time() + 600
                        self.executor_agent.execute_skill("speak", {"text": "Sir, my neural processors are exhausted. Initiating cooldown."})
                    except Exception as e:
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            self.cooldown_until = time.time() + 300
                        self.log(f"Reasoning/JSON Error: {e}", "error")

            finally:
                self._set_busy(False)
        threading.Thread(target=_async_act_worker, daemon=True).start()

    def _post_action_evaluate(self, last_action_text: str, result_text: str) -> None:
        if not self.active_goal: return
        if "speak" in last_action_text.lower(): return

        def _eval_worker():
            try:
                status, suggestion = self.evaluator_agent.evaluate(self.active_goal, last_action_text, result_text)
                if (status or "").strip().lower() == "fail" and suggestion and suggestion.lower() != "none":
                    # Place evaluator feedback back onto the Event Bus dynamically
                    self.event_bus.put((2, time.time(), {"type": "user_intent", "data": suggestion}))
            except Exception as e:
                self.log(f"Evaluator Error: {e}", "error")
        threading.Thread(target=_eval_worker, daemon=True).start()

    def run_loop(self):
        """[AGENTIC UPGRADE] True Event-Driven Main Loop using blocking Queue."""
        self.log(f"Neural Core Event Bus Active. Environment: {safety_manager.env}.", "system")
        while self.active:
            try:
                if time.time() > self.last_goal_check + self.goal_check_interval and time.time() > self.cooldown_until:
                    # Self-inject a generic background goal thought if bored (Timer Event)
                    self.last_goal_check = time.time()
                    # self.event_bus.put((5, time.time(), {"type": "generate_goal", "data": None})) # Off for now to prevent spam
                
                # Fetch next event securely. Block=True means 0 CPU until interrupted natively.
                try:
                    priority, ts, event = self.event_bus.get(block=True, timeout=10)
                    if time.time() < self.cooldown_until: continue
                    self.act(event)
                except queue.Empty:
                    continue

                if self.task_queue:
                    # Process legacy evaluator queue items
                    task = self.task_queue.pop(0)
                    self.event_bus.put((3, time.time(), {"type": "user_intent", "data": task}))

            except Exception as e:
                self.log(f"Event Bus Error: {e}", "error")
                time.sleep(5)

    def _compress_memory_if_needed(self):
        if len(self.context_buffer) >= 8:
            history = "\n".join(self.context_buffer)
            self.context_buffer.clear()
            def _compress_worker():
                try:
                    res = self.chat.send_message(f"Summarize this interaction history contextually:\n{history}")
                    if res and hasattr(res, 'text'):
                        self.context_buffer.appendleft(f"[Past Summary]: {res.text}")
                except:
                    pass
            threading.Thread(target=_compress_worker, daemon=True).start()

def start_autonomous_core(run_skill_fn, system_monitor_fn, chat_obj, socketio_obj):
    core = AutonomousCore(run_skill_fn, system_monitor_fn, chat_obj, socketio_obj)
    thread = threading.Thread(target=core.run_loop, daemon=True)
    thread.start()
    return core