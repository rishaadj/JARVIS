import threading
import time
import importlib.util
import os

def background_task(delay, skill_name, params, recurring=False, socketio=None):
    while True:
        time.sleep(delay)
        # Execute skill
        try:
            skills_dir = os.path.dirname(__file__)
            skill_path = os.path.join(skills_dir, f"{skill_name}.py")
            spec = importlib.util.spec_from_file_location(skill_name, skill_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec) # type: ignore
                spec.loader.exec_module(module) # type: ignore
                result = module.execute(params)

                # Notify the HUD about tool results (background tasks run outside core).
                if socketio and result is not None:
                    try:
                        socketio.emit("new_message", {"sender": "jarvis", "text": str(result)})
                    except Exception:
                        pass
        except Exception as e:
            print(f"Scheduler Error in {skill_name}: {e}")
        
        if not recurring:
            break

def execute(params):
    action = params.get("action") # schedule
    delay_seconds = params.get("delay_seconds", 0)
    skill_to_run = params.get("skill_name")
    skill_params = params.get("params", {})
    recurring = params.get("recurring", False)
    socketio = params.get("_socketio")

    if action == "schedule":
        if not skill_to_run:
            return "Sir, I need a skill name to schedule."

        # Ensure scheduled skills also receive _socketio if they want it.
        if socketio:
            try:
                skill_params = dict(skill_params)
                skill_params["_socketio"] = socketio
            except Exception:
                pass
        
        threading.Thread(
            target=background_task,
            args=(delay_seconds, skill_to_run, skill_params, recurring, socketio),
            daemon=True,
        ).start()
        msg = f"I've scheduled '{skill_to_run}' to run in {delay_seconds} seconds"
        if recurring:
            msg += " on a recurring basis."
        else:
            msg += "."
        return msg
    else:
        return "Unknown scheduler action."
