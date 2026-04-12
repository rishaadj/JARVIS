class MonitorAgent:
    def __init__(self, system_monitor):
        self.system_monitor = system_monitor

    def observe(self):
        """Observes system and returns status. Only alerts if critical."""
        status = self.system_monitor()
        
        cpu = status.get('cpu', 0)
        ram = status.get('ram', 0)
        battery = status.get('battery') 
        battery_pct = battery.get('percent', 100) if battery else 100

        if cpu > 90 or ram > 90:
            print(f"[MONITOR AGENT] CRITICAL STATE: CPU {cpu}% | RAM {ram}%")
            return status

        if battery_pct < 20 and not battery.get('power_plugged', True):
            print(f"[MONITOR AGENT] CRITICAL STATE: Low Battery {battery_pct}%")
            return status
        
        return status