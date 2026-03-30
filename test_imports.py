try:
    from autonomous_core import start_autonomous_core
    print("Success: start_autonomous_core imported")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
