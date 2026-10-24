"""Three-tier safety guardrails, permission management, and secure action logging for ZYRA/FRIDAY."""
import os
import re
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Dict, Any

class RiskLevel(Enum):
    LOW = "LOW"        # open app, switch window, search files, read screen
    MEDIUM = "MEDIUM"  # move/rename files, close selected tab (reversible via undo)
    HIGH = "HIGH"      # permanently delete files, shutdown, restart, sleep, send messages

class SafetyGuard:
    def __init__(self):
        self._pending_action: Optional[Dict[str, Any]] = None
        try:
            d = Path.home() / ".zyra"
            d.mkdir(parents=True, exist_ok=True)
            self._log_dir = d
            self._log_file = d / "actions.log"
            # Test access
            with open(self._log_file, "a", encoding="utf-8") as f:
                pass
        except Exception:
            d = Path.cwd() / ".zyra"
            d.mkdir(parents=True, exist_ok=True)
            self._log_dir = d
            self._log_file = d / "actions.log"

    def _init_log(self):
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def log_action(self, action_type: str, details: str, risk: RiskLevel, status: str = "SUCCESS"):
        """Logs action safely without storing passwords, tokens, or private secrets."""
        sanitized = re.sub(r"(?i)(password|token|key|secret)=([^\s]+)", r"\1=***", details)
        entry = f"[{datetime.now().isoformat()}] [{risk.value}] [{action_type}] {sanitized} -> {status}\n"
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def request_confirmation(self, action_type: str, description: str, callback: Callable[[], str], risk: RiskLevel = RiskLevel.HIGH) -> str:
        """Stage an action that requires user confirmation."""
        self._pending_action = {
            "type": action_type,
            "description": description,
            "callback": callback,
            "risk": risk,
            "timestamp": time.time()
        }
        self.log_action(action_type, description, risk, status="WAITING_CONFIRMATION")
        return f"[CONFIRMATION REQUIRED] Are you sure you want to {description}? Please reply with 'yes' or 'confirm' to proceed, or 'no' / 'cancel' to abort."

    @property
    def has_pending(self) -> bool:
        return self._pending_action is not None

    def get_pending_description(self) -> str:
        if self._pending_action:
            return self._pending_action.get("description", "pending action")
        return ""

    def confirm(self) -> str:
        """Execute the confirmed action."""
        if not self._pending_action:
            return "There are no pending actions requiring confirmation."
        action = self._pending_action
        self._pending_action = None
        try:
            res = action["callback"]()
            self.log_action(action["type"], action["description"], action["risk"], status="CONFIRMED_SUCCESS")
            return res
        except Exception as exc:
            self.log_action(action["type"], action["description"], action["risk"], status=f"CONFIRMED_FAILED: {exc}")
            return f"Action failed during execution: {exc}"

    def cancel(self) -> str:
        """Abort the staged action."""
        if not self._pending_action:
            return "No action was waiting for confirmation."
        desc = self._pending_action.get("description", "action")
        act_type = self._pending_action.get("type", "unknown")
        risk = self._pending_action.get("risk", RiskLevel.HIGH)
        self._pending_action = None
        self.log_action(act_type, desc, risk, status="CANCELLED_BY_USER")
        return f"Cancelled '{desc}'. No changes were made."

safety_guard = SafetyGuard()
