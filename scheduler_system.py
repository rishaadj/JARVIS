import time
import threading
from datetime import datetime, timedelta

class TaskScheduler:
    def __init__(self, on_event_callback):
        self.on_event_callback = on_event_callback
        self.tasks = []
        self.active = False

    def add_task(self, name, task_time, interval=None, priority="normal"):
        """
        Adds a task to the scheduler.
        :param task_time: datetime object
        :param interval: timedelta object (optional) for recurring tasks
        """
        self.tasks.append({
            "name": name,
            "next_run": task_time,
            "interval": interval,
            "priority": priority
        })

    def run_loop(self):
        print("[SCHEDULER] Background Task Engine Active.")
        while self.active:
            now = datetime.now()
            for task in self.tasks:
                if now >= task["next_run"]:
                    self._fire_task(task)
                    if task["interval"]:
                        task["next_run"] += task["interval"]
                    else:
                        self.tasks.remove(task)
            time.sleep(30)

    def _fire_task(self, task):
        self.on_event_callback(
            event_type="scheduled_task",
            message=f"Scheduled task triggered: {task['name']}",
            priority=task["priority"]
        )

    def start(self):
        if not self.active:
            self.active = True
            self.thread = threading.Thread(target=self.run_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.active = False
