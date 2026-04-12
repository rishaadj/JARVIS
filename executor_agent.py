import importlib.util
import json
import os
import sys
from typing import Any, Tuple

from utils.skill_registry import SKILL_REGISTRY, get_param_contract
from safety_manager import safety_manager

class ExecutorAgent:
    def __init__(self, run_skill_fn):
        self.run_skill = run_skill_fn
        self.skills_path = os.path.join(os.path.dirname(__file__), "skills")
        repo_root = os.path.dirname(os.path.abspath(__file__))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        self.skill_param_contract = get_param_contract()

    def _coerce_value(self, key: str, value: Any, target_type: type) -> Any:
        if value is None:
            return value
        if isinstance(value, target_type):
            return value
        if target_type is bool:
            s = str(value).strip().lower()
            if s in {"true", "1", "yes", "y", "on"}:
                return True
            if s in {"false", "0", "no", "n", "off"}:
                return False
            return value
        if target_type is int:
            try:
                return int(float(str(value).strip()))
            except Exception:
                return value
        return value

    def _validate_skill_params(self, skill_name: str, params: dict) -> Tuple[bool, str]:
        rules = self.skill_param_contract.get(skill_name)
        if not rules:
            return True, ""

        if skill_name in ["file_management", "run_script", "list_files"]:
            path = params.get("path") or params.get("target") or "."
            if not safety_manager.validate_path(path):
                return False, f"Access to path `{path}` is restricted by safety policy."

        required: dict[str, type] = rules.get("required", {})
        enum_rules: dict[str, set] = rules.get("enum", {})
        coerce_rules: dict[str, type] = rules.get("coerce", {})

        if coerce_rules:
            for k, t in coerce_rules.items():
                if k in params:
                    params[k] = self._coerce_value(k, params.get(k), t)

        for key, expected_type in required.items():
            if key not in params:
                return False, f"Missing required param `{key}`."
            val = params.get(key)
            if expected_type is str and not isinstance(val, str):
                return False, f"Param `{key}` must be a string."
            elif expected_type is int and not isinstance(val, int):
                return False, f"Param `{key}` must be an integer."
            elif expected_type not in (str, int) and not isinstance(val, expected_type):
                return False, f"Param `{key}` has invalid type."

        for key, allowed in enum_rules.items():
            if key in params:
                if str(params[key]).lower() not in allowed:
                    return False, f"Param `{key}` must be one of: {sorted(list(allowed))}."

        return True, ""

    def parse_params(self, params_str: str) -> dict:
        s = (params_str or "").strip()
        if not s:
            return {}
        if s.startswith("```"):
            try:
                s = s.strip("`")
                s = "\n".join(s.splitlines()[1:]) if "\n" in s else s
                s = s.strip()
            except Exception:
                pass
        if s.startswith("{") or s.startswith("["):
            try:
                loaded = json.loads(s)
                if isinstance(loaded, dict):
                    return {str(k).lower(): v for k, v in loaded.items()}
                return {"text": s}
            except Exception:
                pass
        params: dict[str, Any] = {}
        parts = [p.strip() for p in s.split(",") if p.strip()]
        parsed_any = False
        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                params[k.strip().strip("\"'").lower()] = v.strip().strip("\"'")
                parsed_any = True
            elif ":" in part:
                k, v = part.split(":", 1)
                params[k.strip().strip("\"'").lower()] = v.strip().strip("\"'")
                parsed_any = True
        if parsed_any:
            return params
        return {"text": s}

    def parse_task(self, task: str) -> Tuple[str, dict]:
        t = (task or "").strip()
        if not t:
            return "", {}
        if t.upper().startswith("ACTION:"):
            t = t[len("ACTION:"):].strip()
        if ":" in t:
            skill_name, params_str = t.split(":", 1)
            return skill_name.strip().lower(), self.parse_params(params_str)
        return t.strip().lower(), {}

    def execute_skill(self, skill_name: str, params: dict):
        skill_name = (skill_name or "").strip().lower()
        if not skill_name:
            return None

        if not safety_manager.is_skill_allowed(skill_name):
            error_msg = f"Skill `{skill_name}` is not allowed in the current environment ({safety_manager.env})."
            safety_manager.audit_log("EXECUTOR", skill_name, params, "BLOCKED", error_msg)
            return error_msg

        ok, err = self._validate_skill_params(skill_name, params or {})
        if not ok:
            safety_manager.audit_log("EXECUTOR", skill_name, params, "INVALID_PARAMS", err)
            return f"Parameter validation failed for `{skill_name}`: {err}"

        result = None
        try:
            skill_file = os.path.join(self.skills_path, f"{skill_name}.py")
            if os.path.exists(skill_file):
                spec = importlib.util.spec_from_file_location(skill_name, skill_file)
                module = importlib.util.module_from_spec(spec)
                assert spec and spec.loader
                spec.loader.exec_module(module)
                if hasattr(module, "execute"):
                    result = module.execute(params)
                else:
                    result = "Error: Skill module missing `execute` function."
            else:
                result = self.run_skill(skill_name, params)
            
            status = "SUCCESS" if "Error" not in str(result) else "FAILED"
            safety_manager.audit_log("EXECUTOR", skill_name, params, status, str(result)[:500])
            return result
        except Exception as e:
            safety_manager.audit_log("EXECUTOR", skill_name, params, "ERROR", str(e))
            return f"Execution Error in `{skill_name}`: {e}"

    def execute(self, task: str):
        try:
            skill_name, params = self.parse_task(task)
            return self.execute_skill(skill_name, params)
        except Exception as e:
            print(f"[EXECUTOR] Error: {e}")
