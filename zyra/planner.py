"""Multi-step planner and sequential task execution for FRIDAY."""
import re
import time
from typing import List, Callable, Tuple, Any

SPLIT_PATTERN = re.compile(
    r"\s*(?:\.{2,}|(?:\b(?:and\s+then|then|after\s+that|and\s+also)\b)|[;,]|\band(?=\s+(?:open|show|close|maximize|minimize|switch|search|play|watch|lock|sleep|create|delete|organize|find|launch|run|go\s+to|click|double\s+click|right\s+click|type|write|press|scroll|download))\b)\s*",
    flags=re.IGNORECASE
)

class Planner:
    @staticmethod
    def is_multi_step(command: str) -> bool:
        # Don't split if it's a search query or a single path/URL
        lower = command.lower()
        if any(lower.startswith(p) for p in ("search google for", "search for", "google ")):
            return False
        parts = SPLIT_PATTERN.split(command.strip())
        parts = [p.strip().strip(".") for p in parts if p.strip().strip(".")]
        return len(parts) > 1

    @staticmethod
    def split_steps(command: str) -> List[str]:
        parts = SPLIT_PATTERN.split(command.strip())
        return [p.strip().strip(".") for p in parts if p.strip().strip(".")]

    def execute_plan(self, command: str, executor: Callable[[str], str]) -> str:
        """Executes a multi-step sequence with verification and cumulative reporting."""
        steps = self.split_steps(command)
        if len(steps) <= 1:
            return executor(command)

        results: List[str] = []
        for i, step in enumerate(steps, 1):
            res = executor(step)
            results.append(f"Step {i} ({step}): {res}")
            # If step explicitly required confirmation, halt sequential execution
            if "[CONFIRMATION REQUIRED]" in res:
                results.append("Multi-step execution paused waiting for your confirmation.")
                break
            # Stabilization delay between UI steps (e.g. after opening an app or clicking a link)
            time.sleep(0.5)

        return "\n".join(results)

planner = Planner()
