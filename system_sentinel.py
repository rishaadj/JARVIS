import time
import threading
from collections import deque
from datetime import datetime
from scheduler_system import TaskScheduler
from filesystem_watcher import FilesystemWatcher

class SystemSentinel:
    def __init__(self, monitor_agent, safety_manager, event_queue, interval=10):
        self.monitor = monitor_agent
        self.safety = safety_manager
        self.event_queue = event_queue
        self.interval = interval
        self.active = False
        
        self.scheduler = TaskScheduler(self._fire_event)
        self.watcher = FilesystemWatcher(self._fire_event)

        self.telemetry_history = deque(maxlen=6)
        self.last_proactive_ts = 0
        self.proactive_cooldown = 600
        
        self.event_history = {} 

        from datetime import timedelta
        briefing_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        if briefing_time < datetime.now():
            briefing_time += timedelta(days=1)
        
        self.scheduler.add_task("Daily Briefing", briefing_time, interval=timedelta(days=1))

    def monitor_loop(self):
        print(f"[SENTINEL] System Watchdog Active (Interval: {self.interval}s).")
        while self.active:
            try:
                try:
                    status = self.monitor.observe()
                    self.telemetry_history.append(status)
                    
                    if self._check_sustained_load():
                        self._fire_event("critical_load", f"Sustained high system load detected: CPU {status.get('cpu')}% | RAM {status.get('ram')}%", priority="high")

                    battery = status.get('battery')
                    if battery and battery.get('percent', 100) < 20 and not battery.get('power_plugged', True):
                        self._fire_event("low_battery", f"Critical battery level: {battery['percent']}%", priority="high")
                except Exception as e:
                    print(f"[SENTINEL] Telemetry Error: {e}")

                try:
                    if hasattr(self.safety, "get_latest_violation"):
                        violation = self.safety.get_latest_violation()
                        if violation:
                            self._fire_event("security_alert", f"Security violation detected: {violation}", priority="high")
                except Exception as e:
                    print(f"[SENTINEL] Security Check Error: {e}")

            except Exception as e:
                print(f"[SENTINEL] Loop Error: {e}")
            
            time.sleep(self.interval)

    def _check_sustained_load(self):
        if len(self.telemetry_history) < 3:
            return False
        return all(s.get('cpu', 0) > 90 for s in list(self.telemetry_history)[-3:])

    def _fire_event(self, event_type, message, priority="normal"):
        """
        Fires an event to the brain.
        Includes a debouncer and global proactivity cooldown.
        """
        now = time.time()
        
        last_time = self.event_history.get(event_type, 0)
        if priority != "high" and (now - last_time < self.proactive_cooldown):
            return

        if priority != "high" and (now - self.last_proactive_ts < self.proactive_cooldown):
            return

        event = {
            "type": event_type,
            "message": message,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        }
        
        self.event_queue.put(event)
        self.event_history[event_type] = now
        
        if priority == "high" or event_type in ["file_created", "scheduled_task"]:
            self.last_proactive_ts = now

    def start(self):
        if not self.active:
            self.active = True
            self.scheduler.start()
            self.watcher.start()
            self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.active = False
        self.scheduler.stop()
        self.watcher.stop()
