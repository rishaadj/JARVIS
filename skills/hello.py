import datetime

def execute(params):
    name = params.get("name", "Sir")
    
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    print(f"JARVIS: {greeting}, {name}. The environment is ready.")
    return True