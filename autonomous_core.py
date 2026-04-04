import time
import threading
import sys
import os
import queue
from collections import deque
from PIL import Image

# Fix import path
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
        self.active_provider = "auto" # Default to failover

        # 🧠 Internal Systems
        self.memory = MemoryManager(self.chat)
        self.goal_agent = GoalAgent(self.chat)
        self.planner_agent = PlannerAgent(self.chat)
        self.executor_agent = ExecutorAgent(self.run_skill) # Wraps our own run_skill
        self.monitor_agent = MonitorAgent(self.system_monitor)
        self.evaluator_agent = EvaluatorAgent(self.chat)
        
        # 🤖 Specialized Agents (New)
        self.researcher_agent = ResearcherAgent(self.chat)
        self.coder_agent = CoderAgent(self.chat)
        self.synthesis_engine = SkillSynthesisEngine(self.chat, self.executor_agent)

        # 👁️ Visual Awareness (Milestone 1)
        self.visual_observer = VisualObserver(self.chat, self.socketio, memory_obj=self.memory)
        self.visual_observer.start()

        # 🛡️ Proactive Autonomy (Milestone 3)
        self.proactive_event_queue = queue.Queue()
        self.sentinel = SystemSentinel(self.monitor_agent, safety_manager, self.proactive_event_queue)
        self.sentinel.start()

        # 🖐️ Gesture Mastery (Milestone 5)
        try:
            self.gesture_engine = GestureEngine(self.socketio)
        except Exception as e:
            self.log(f"Gesture Engine failed to initialize: {e}", "error")
            self.gesture_engine = None
        self.gesture_active = False
        
        # ⏱️ Quota Management (Milestone 7 Throttle)
        self.last_goal_check = time.time()
        self.goal_check_interval = 1800 # 30 minutes between autonomous goal checks
        self.cooldown_until = 0 # ⏱️ Rate-limit suppression

        # 🧩 State & Context Management
        self.task_queue: list[str] = []
        self.user_priority_queue: list[str] = []
        self.active_goal: str | None = None
        
        # Working memory: Stores the last 5 interactions for pronoun resolution
        self.context_buffer = deque(maxlen=5) 
        
        self.state = {
            "last_action": None,
            "system_status": "nominal",
            "is_busy": False,
            "current_focus": None # e.g., "Spotify" or "Project.py"
        }

        # --- Safety / confirmation gating ---
        # Note: ExecutorAgent now handles environment allowlists, but we keep UI-level gating here.
        allow_env = os.getenv("JARVIS_ALLOW_DANGEROUS", "").strip().lower()
        self.allow_dangerous = allow_env in {"1", "true", "yes", "y", "on"}
        
        # High-risk skills that always trigger a UI confirmation if not in high-trust mode.
        # Pull from Registry where risk == 1
        self.dangerous_skills = {name for name, data in SKILL_REGISTRY.items() if data.get("risk", 0) == 1}
        
        self.pending_confirmation: dict | None = None

        # --- CORE PROMPT SYSTEM ---
        self.CORE_SYSTEM_PROMPT = f"""
You are JARVIS, a highly advanced AI system. 
Recent Context: {{context_snapshot}}
Visual Awareness (Last Scan): {{v_ctx}}
Relevant Past Experiences:
{{past_memories}}

User said: "{{user_input}}"

Decide the next logical action. Respond ONLY as one single line in the following format:
ACTION: <skill_name>: <json_params>

Supported skills:
{get_skill_list_prompt()}

PROACTIVE STRATEGY:
1. Prefer direct skills (like 'email_sender' or 'web_search') over opening an app and waiting.
2. If the user's intent is clear (e.g. 'tell me the time' or 'send mail'), do it DIRECTLY. 
3. Only use 'open_app' if the user explicitly asks to 'open' something for them to use manually.
"""

    def run_skill(self, skill_name, params):
        """
        The orchestrator's skill router. 
        Handles built-in system skills and delegates others to the original run_skill_fn.
        """
        if skill_name == "research":
            topic = params.get("topic")
            context = params.get("context", str(self.active_goal))
            return self.researcher_agent.research(topic, context)
        
        if skill_name == "synthesize_skill":
            name = params.get("skill_name")
            desc = params.get("description")
            reqs = params.get("requirements")
            return self.synthesis_engine.synthesize_skill(name, desc, reqs)

        # Fallback to the original run_skill (which handles 'speak', etc.)
        return self.run_skill_callback(skill_name, params)

    def _set_busy(self, busy: bool) -> None:
        """Sync internal busy state to the browser HUD."""
        self.state["is_busy"] = busy
        if self.socketio:
            self.socketio.emit("state_change", "processing" if busy else "idle")

    def _set_action(self) -> None:
        """Emit 'action' state to HUD when executing a skill."""
        if self.socketio:
            self.socketio.emit("state_change", "action")

    def _emit_jarvis_message(self, text: str) -> None:
        safe_text = str(text).strip()
        if self.socketio and safe_text:
            self.socketio.emit("new_message", {"sender": "jarvis", "text": safe_text})

    def set_active_provider(self, provider: str):
        """Sets the manual override for the AI provider (Gemini, Groq, etc.)"""
        self.active_provider = provider

    def _inject_context(self, params: dict) -> dict:
        """Inject system context (Socket.IO, Memory) into tool params for background skills."""
        p = dict(params or {})
        if self.socketio:
            p["_socketio"] = self.socketio
        if self.memory:
            p["_memory"] = self.memory
        return p

    def log(self, message, type="info"):
        """Sends logs to terminal and the Web HUD."""
        prefix = f"[{type.upper()}]"
        print(f"{prefix} {message}")
        if self.socketio:
            self.socketio.emit('system_log', f"{prefix} {message}")

    def _emit_agent_update(self, agent_name: str, status: str) -> None:
        """Sync specific agent's internal thought state to the Web HUD."""
        if self.socketio:
            self.socketio.emit("agent_status", {"agent": agent_name, "status": status})

    def set_user_input(self, text: str):
        """High-priority injection of user intent."""
        if text.strip():
            self.log(f"Priority Interrupt: '{text}'", "user")
            self.user_priority_queue.append(text)
            # If we're already waiting for CONFIRM/CANCEL, don't wipe the plan.
            if self.pending_confirmation is None:
                self.task_queue = []
                self.active_goal = None

    def think(self):
        """The Decision Engine: Priority > Proactive > Monitoring > Background Goals."""
        if self.pending_confirmation is not None:
            if self.user_priority_queue:
                return {"type": "confirmation_response", "data": self.user_priority_queue.pop(0)}
            return {"type": "idle", "data": None}

        if self.user_priority_queue:
            peek_intent = self.user_priority_queue[0].lower()
            if any(w in peek_intent for w in ["stop", "cancel", "abort", "shut up"]):
                return {"type": "interrupt", "data": self.user_priority_queue.pop(0)}

        if time.time() < self.cooldown_until:
            return {"type": "idle", "data": None}

        if self.state.get("is_busy"):
            return {"type": "idle", "data": None}

        if self.user_priority_queue:
            return {"type": "user_intent", "data": self.user_priority_queue.pop(0)}

        # 🛡️ Milestone 3: Proactive Sentinel Interrupt
        try:
            event = self.proactive_event_queue.get_nowait()
            return {"type": "proactive_event", "data": event}
        except queue.Empty:
            pass

        status = self.monitor_agent.observe()
        self.state["system_status"] = status

        if not self.task_queue and self.active_goal:
            self.active_goal = None
        
        if self.task_queue:
            return {"type": "execute_task", "data": self.task_queue.pop(0)}

        if not self.active_goal and (time.time() - self.last_goal_check > self.goal_check_interval):
            if time.time() < self.cooldown_until:
                return {"type": "idle", "data": None}
            
            self.last_goal_check = time.time()
            memory_data = self.memory.load_memory()
            goal = self.goal_agent.generate_goal(status, memory_data)
            if goal and goal != "none":
                self.active_goal = goal
                self.log(f"New Autonomous Goal: {goal}", "brain")
                self._emit_agent_update("planner", f"New Goal: {goal}")
                v_ctx = self.visual_observer.get_context()
                self.task_queue = self.planner_agent.plan(goal, v_ctx, self.memory)
        
        return {"type": "idle", "data": None}

    def act(self, thought):
        t_type = thought["type"]
        t_data = thought["data"]

        if t_type == "idle":
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
            try:
                if t_type == "proactive_event":
                    # 🛡️ Milestone 3: Handle Sentinel Notifications
                    event_msg = t_data.get("message", "Unknown system event.")
                    priority = t_data.get("priority", "normal")
                
                    self.log(f"Proactive Event ({priority}): {event_msg}", "sentinel")
                    self._emit_agent_update("sentinel", f"Alert ({priority}): {event_msg}")
                    self._emit_jarvis_message(f"Attention: {event_msg}")
                
                    # If high priority, speak it and clear the task queue to focus on the issue.
                    if priority == "high":
                        self.executor_agent.execute_skill("speak", {"text": f"Sir, excuse the interruption. {event_msg}"})
                        self.task_queue = []
                        self.active_goal = f"Resolve: {event_msg}"
                        # Proactively plan a fix
                        self.task_queue = self.planner_agent.plan(self.active_goal, self.visual_observer.get_context(), self.memory)
                    return

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
                            action_text = pc.get("action_text", f"{skill_name}: {params}")
                            self._emit_jarvis_message(f"Confirmed. Executing: {action_text}")
                            self._set_busy(True)
                            self._set_action()
                            result = self.executor_agent.execute_skill(skill_name, self._inject_context(params))
                            if result is not None:
                                self._emit_jarvis_message(str(result))
                            self._set_busy(False)
                            self._post_action_evaluate(action_text, str(result))
                            return

                        if user_text in {"cancel", "no", "n", "stop", "abort"}:
                            self._emit_jarvis_message("Cancelled. No action was taken.")
                            self.pending_confirmation = None
                            self._set_busy(False)
                            return

                        self._emit_jarvis_message("Please reply with `CONFIRM` to run it, or `CANCEL` to abort.")
                    finally:
                        if self.state.get("is_busy"):
                            self._set_busy(False)
                    return

                if t_type == "user_intent":
                    # 🖐️ Milestone 5: Voice Toggle for Gesture Control
                    lower_intent = t_data.lower()
                    if "hand control" in lower_intent or "gesture mode" in lower_intent:
                        if "on" in lower_intent or "start" in lower_intent:
                            if self.gesture_engine:
                                self.gesture_active = True
                                self.gesture_engine.start()
                                self._emit_jarvis_message("Physical gesture control initiated. I'm watching your hands, Sir.")
                                self.executor_agent.execute_skill("speak", {"text": "Physical gesture control initiated."})
                            else:
                                self._emit_jarvis_message("Cannot start gesture control: Module not initialized.")
                                self.executor_agent.execute_skill("speak", {"text": "I'm sorry Sir, gesture control is currently unavailable."})
                        else:
                            self.gesture_active = False
                            if self.gesture_engine:
                                self.gesture_engine.stop()
                            self._emit_jarvis_message("Gesture control deactivated.")
                            self.executor_agent.execute_skill("speak", {"text": "Gesture control deactivated."})
                        return

                    self._set_busy(True)
            
                    # Dynamic Vision Context (Use last scan if recent, otherwise save quota)
                    v_ctx = self.visual_observer.get_context()
                    if "No visual data" in v_ctx:
                        v_ctx = "Visual context is currently empty. ONLY use the 'vision' skill if the user explicitly asks you to look at their screen or analyze something."
                
                    context_snapshot = "\n".join(list(self.context_buffer))
            
                    # 🧠 Semantic Recall & Persona Facts
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
                        # Pass the forced provider to the switchboard
                        is_uncensored = (self.active_provider == "uncensored")
                        response = self.chat.send_message(prompt, uncensored=is_uncensored, forced_provider=self.active_provider)
                        
                        if not response or not hasattr(response, 'text'):
                            self.log("Brain returned an empty or invalid response.", "error")
                            return

                        action_text = response.text.strip()
                        actions = []
                        for line in action_text.splitlines():
                            if "ACTION:" in line.upper():
                                actions.append(line.strip())
                
                        if not actions:
                            final_text = action_text
                            self._emit_jarvis_message(final_text)
                            self.executor_agent.execute_skill("speak", {"text": final_text})
                            self.context_buffer.append(f"User: {t_data} | JARVIS: {final_text}")
                            self._compress_memory_if_needed()
                            # 💡 Semantic Memory: Store the interaction
                            self.memory.store_semantic(f"User asked: {t_data}. JARVIS responded: {final_text}", {"type": "conversation"})
                            return

                        # Process all actions in sequence
                        self.context_buffer.append(f"User: {t_data} | JARVIS Actions: {', '.join(actions)}")
                        
                        for act in actions:
                            skill_name, params = self.executor_agent.parse_task(act)
                            if not skill_name or skill_name in {"none", "null", "idle"}:
                                continue
                    
                            self.state["last_action"] = {"skill": skill_name, "params": params}
                            
                            # UI Confirmation Gating
                            if (not self.allow_dangerous) and (skill_name in self.dangerous_skills):
                                self.pending_confirmation = {"skill_name": skill_name, "params": params, "action_text": act}
                                self._emit_jarvis_message(f"Security Alert: `{act}` requires confirmation.")
                                return

                            if skill_name == "vision":
                                self._set_action()
                                result = self.executor_agent.execute_skill("vision", self._inject_context(params))
                                if isinstance(result, str) and "SCREENSHOT_SAVED" in result:
                                    img_path = os.path.abspath(result.split(":", 1)[-1].strip())
                                    img = Image.open(img_path)
                                    is_uncensored = (self.active_provider == "uncensored")
                                    vision_res = self.chat.send_message([f"Analyze screen for: {t_data}", img], uncensored=is_uncensored, forced_provider=self.active_provider)
                                    if vision_res and hasattr(vision_res, 'text'):
                                        final_text = vision_res.text
                                        self._emit_jarvis_message(final_text)
                                        self.executor_agent.execute_skill("speak", {"text": final_text})
                                        self._post_action_evaluate(act, str(final_text))
                                continue

                            self._set_action()
                            result = self.executor_agent.execute_skill(skill_name, self._inject_context(params))
                            if result is not None:
                                self._emit_jarvis_message(f"[{skill_name}]: {result}")
                            
                            self._post_action_evaluate(act, str(result))
                        
                        self._compress_memory_if_needed()
                    
                    except QuotaExceededError as e:
                        self.log("CRITICAL: ALL API KEYS EXHAUSTED. Initiating 10-minute hibernation.", "brain")
                        self.cooldown_until = time.time() + 600 
                        self._emit_jarvis_message("Sir, my neural processors are exhausted. I need 10 minutes to cool down before we continue.")
                        self.executor_agent.execute_skill("speak", {"text": "Sir, my neural processors are exhausted. Initiating ten minute hibernation."})
                    except Exception as e:
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            self.log("Brain Overloaded (429). Cooling down for 5 minutes.", "brain")
                            self.cooldown_until = time.time() + 300
                        self.log(f"Reasoning Error: {e}", "error")
                    finally:
                        self._set_busy(False)

                elif t_type == "execute_task":
                    self._set_busy(True)
                    try:
                        self.log(f"Executing: {t_data}", "executor")
                        skill_name, params = self.executor_agent.parse_task(t_data)

                        if not skill_name or skill_name in {"none", "null", "idle"}:
                            return

                        if (not self.allow_dangerous) and (skill_name in self.dangerous_skills):
                            self.pending_confirmation = {"skill_name": skill_name, "params": params, "action_text": t_data}
                            self._emit_jarvis_message(f"Security Alert: `{t_data}` requires confirmation.")
                            return

                        # Vision autonomous logic
                        if skill_name == "vision":
                            result = self.executor_agent.execute_skill("vision", self._inject_context(params))
                            if isinstance(result, str) and "SCREENSHOT_SAVED" in result:
                                img_path = os.path.abspath(result.split(":", 1)[-1].strip())
                                img = Image.open(img_path)
                                is_uncensored = (self.active_provider == "uncensored")
                                vision_res = self.chat.send_message([f"Analyze screen for: {self.active_goal}", img], uncensored=is_uncensored, forced_provider=self.active_provider)
                                if not vision_res or not hasattr(vision_res, 'text'):
                                    err_msg = "Visual analysis failed."
                                    self._emit_jarvis_message(err_msg)
                                    self._post_action_evaluate(t_data, err_msg)
                                    return
                                self._emit_jarvis_message(vision_res.text)
                                self.executor_agent.execute_skill("speak", {"text": vision_res.text})
                                self._post_action_evaluate(t_data, str(vision_res.text))
                            else:
                                self._emit_jarvis_message(str(result))
                            return

                        result = self.executor_agent.execute_skill(skill_name, self._inject_context(params))
                        if result is not None:
                            self._emit_jarvis_message(str(result))
                        self._post_action_evaluate(t_data, str(result))
                    except Exception as e:
                        self.log(f"Execution Error: {e}", "error")
                    finally:
                        self._set_busy(False)


            finally:
                self._set_busy(False)
        threading.Thread(target=_async_act_worker, daemon=True).start()
    def _post_action_evaluate(self, last_action_text: str, result_text: str) -> None:
        if not self.active_goal: return
        
        # --- QUOTA SAVER ---
        # Don't evaluate simple 'speak' or 'none' actions during high-frequency conversation
        if "ACTION: speak" in last_action_text.upper() or "speak:" in last_action_text.lower():
            return

        def _eval_worker():
            try:
                status, suggestion = self.evaluator_agent.evaluate(self.active_goal, last_action_text, result_text)
                if (status or "").strip().lower() == "fail" and suggestion and suggestion.lower() != "none":
                    self.task_queue.insert(0, suggestion)
                    self.log(f"Recovery step queued: {suggestion}", "evaluator")
            except Exception as e:
                self.log(f"Evaluator Error: {e}", "error")
        threading.Thread(target=_eval_worker, daemon=True).start()

    def run_loop(self):
        self.log(f"Neural Core Synchronized. Environment: {safety_manager.env}.", "system")
        while self.active:
            try:
                thought = self.think()
                self.act(thought)
                time.sleep(0.2 if self.user_priority_queue else 1.2)
            except Exception as e:
                self.log(f"Core Loop Error: {e}", "error")
                time.sleep(5)

    def _compress_memory_if_needed(self):
        """Compresses the context buffer into a short summary to save tokens (Async)."""
        if len(self.context_buffer) >= 8: # Increased limit to 8 to reduce frequency
            history = "\n".join(self.context_buffer)
            self.context_buffer.clear() # Clear immediately to prevent double-calls
            
            def _compress_worker():
                self.log("Background memory compression initiated...", "system")
                try:
                    summary_res = self.chat.send_message(summary_prompt)
                    if summary_res and hasattr(summary_res, 'text'):
                        summary = summary_res.text
                        self.context_buffer.appendleft(f"[Past Context Summary]: {summary}")
                except Exception as e:
                    self.log(f"Memory Compression Error: {e}", "error")
            
            threading.Thread(target=_compress_worker, daemon=True).start()

def start_autonomous_core(run_skill_fn, system_monitor_fn, chat_obj, socketio_obj):
    core = AutonomousCore(run_skill_fn, system_monitor_fn, chat_obj, socketio_obj)
    thread = threading.Thread(target=core.run_loop, daemon=True)
    thread.start()
    return core