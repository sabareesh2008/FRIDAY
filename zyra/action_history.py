"""Action history and undo stack for ZYRA/FRIDAY."""
import os
import shutil
from typing import Callable, Optional, Dict, Any, List
from pathlib import Path
from zyra.config import config

class ActionRecord:
    def __init__(self, action_type: str, description: str, undo_fn: Callable[[], str], details: Dict[str, Any]):
        self.action_type = action_type
        self.description = description
        self.undo_fn = undo_fn
        self.details = details

class ActionHistory:
    def __init__(self, max_history: int = 50):
        self._history: List[ActionRecord] = []
        self._max_history = max_history

    def push(self, action_type: str, description: str, undo_fn: Callable[[], str], **details):
        record = ActionRecord(action_type, description, undo_fn, details)
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def undo_last(self) -> str:
        """Undoes the last reversible action on the stack."""
        user_title = config.get("user_title", "sir")
        if not self._history:
            return f"There are no previous actions to undo, {user_title}."

        last_action = self._history.pop()
        try:
            result = last_action.undo_fn()
            return f"Undid action: {last_action.description}. {result}"
        except Exception as exc:
            return f"Failed to undo '{last_action.description}': {exc}"

    def get_last_action(self) -> Optional[ActionRecord]:
        return self._history[-1] if self._history else None

    def get_last_file_action(self) -> Optional[ActionRecord]:
        for rec in reversed(self._history):
            if rec.action_type in ("move_file", "rename_file", "create_file", "organize"):
                return rec
        return None

action_history = ActionHistory()
