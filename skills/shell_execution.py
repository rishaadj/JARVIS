import subprocess

def execute(params):
    command = params.get("command", "")
    if not command:
        return "Sir, please provide a command to execute."

    try:
        # Run command and capture output
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if result.returncode == 0:
            if not output:
                return "Command executed successfully, Sir. However, there was no output to report."
            return f"Execution successful, Sir. Here is the output:\n\n{output}"
        else:
            return f"Command failed with return code {result.returncode}.\nError Output:\n{error}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Shell execution error: {e}"
