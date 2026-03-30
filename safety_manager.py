import os
import json
import logging
from datetime import datetime

class SafetyManager:
    # Environments
    RESTRICTED = "RESTRICTED"
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"

    def __init__(self):
        self.env = os.getenv("JARVIS_ENV", self.RESTRICTED).upper()
        self.audit_log_path = os.path.join(os.path.dirname(__file__), "audit.log")
        self._setup_audit_logger()
        self.latest_violation = None

        # Allowlists: (Skill -> Allowed Environments)
        # If a skill isn't here, it defaults to PRODUCTION only.
        self.allowlists = {
            "speak": [self.RESTRICTED, self.DEVELOPMENT, self.PRODUCTION],
            "timer": [self.RESTRICTED, self.DEVELOPMENT, self.PRODUCTION],
            "volume": [self.RESTRICTED, self.DEVELOPMENT, self.PRODUCTION],
            "list_files": [self.RESTRICTED, self.DEVELOPMENT, self.PRODUCTION],
            "recall_memory": [self.RESTRICTED, self.DEVELOPMENT, self.PRODUCTION],
            "web_search": [self.DEVELOPMENT, self.PRODUCTION],
            "vision": [self.DEVELOPMENT, self.PRODUCTION],
            "screen_capture": [self.DEVELOPMENT, self.PRODUCTION],
            "open_app": [self.DEVELOPMENT, self.PRODUCTION],
            "shell_execution": [self.PRODUCTION],
            "create_skill": [self.PRODUCTION],
            "file_management": [self.PRODUCTION],
            "mouse_control": [self.PRODUCTION],
            "keyboard_control": [self.PRODUCTION],
            "email_sender": [self.PRODUCTION],
            "send_whatsapp_message": [self.PRODUCTION],
        }

    def _setup_audit_logger(self):
        self.logger = logging.getLogger("JARVIS_AUDIT")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.audit_log_path)
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def is_skill_allowed(self, skill_name: str) -> bool:
        allowed_envs = self.allowlists.get(skill_name, [self.PRODUCTION])
        return self.env in allowed_envs

    def audit_log(self, agent_role: str, skill_name: str, params: dict, status: str, metadata: str = ""):
        if status == "DENIED":
            self.latest_violation = f"{agent_role} attempted {skill_name} but was DENIED in {self.env} environment."
        
        log_entry = {
            "agent": agent_role,
            "skill": skill_name,
            "params": params,
            "status": status,
            "metadata": metadata,
            "env": self.env
        }
        self.logger.info(json.dumps(log_entry))

    def get_latest_violation(self):
        v = self.latest_violation
        self.latest_violation = None
        return v

    def validate_path(self, path: str) -> bool:
        """Simple path guard: Don't allow access outside the project or sensitive dirs."""
        repo_root = os.path.dirname(os.path.abspath(__file__))
        abs_path = os.path.abspath(path)
        
        # Allow repo root
        if abs_path.startswith(repo_root):
            return True
            
        # Block common sensitive dirs on Windows
        sensitive_dirs = ["C:\\Windows", "C:\\Users", "C:\\Program Files"]
        for sd in sensitive_dirs:
            if abs_path.startswith(sd) and not abs_path.startswith(os.path.join("C:\\Users", os.getlogin(), "Desktop")):
                # Special allowance for Desktop/Downloads if needed, but for now be strict.
                return False
        
        return True

safety_manager = SafetyManager()
