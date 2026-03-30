import psutil # type: ignore

def execute(params):
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        
        status = f"Sir, here is the current system status:\n"
        status += f"- CPU Usage: {cpu_usage}%\n"
        status += f"- RAM Usage: {memory.percent}% ({memory.used // (1024**2)}MB used)\n"
        
        if battery:
            status += f"- Battery: {battery.percent}% ({'Charging' if battery.power_plugged else 'Discharging'})\n"
        else:
            status += "- Battery: Not detected (likely a desktop PC)\n"
            
        return status
    except Exception as e:
        return f"Sir, I encountered an error while monitoring the system: {e}"
