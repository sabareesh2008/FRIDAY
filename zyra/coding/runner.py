"""Local code compilation, execution, and error verification for ZYRA."""
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from zyra.coding.languages import detect_language, LanguageSpec

class CodeRunner:
    @staticmethod
    def execute_file(file_path: str, timeout: int = 10) -> Dict[str, Any]:
        path = Path(file_path).resolve()
        if not path.exists():
            return {"success": False, "error": f"File does not exist: {path}"}

        lang = detect_language(path.suffix)
        if not lang:
            return {"success": False, "error": f"Unsupported language extension: {path.suffix}"}

        work_dir = str(path.parent)
        stem = path.stem
        filename = path.name

        # 1. Compilation step (if required by language)
        if lang.compile_cmd:
            compile_cmd = lang.compile_cmd.format(file=filename, stem=stem)
            try:
                proc = subprocess.run(
                    compile_cmd,
                    shell=True,
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                if proc.returncode != 0:
                    return {
                        "success": False,
                        "phase": "compilation",
                        "error": proc.stderr or proc.stdout,
                        "returncode": proc.returncode
                    }
            except subprocess.TimeoutExpired:
                return {"success": False, "phase": "compilation", "error": "Compilation timed out."}
            except Exception as exc:
                return {"success": False, "phase": "compilation", "error": f"Compilation failed: {exc}"}

        # 2. Execution step
        if not lang.run_cmd:
            return {"success": True, "output": "File saved (no execution command configured)."}

        run_cmd = lang.run_cmd.format(file=filename, stem=stem)
        start_time = time.time()
        try:
            proc = subprocess.run(
                run_cmd,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = round(time.time() - start_time, 3)
            if proc.returncode == 0:
                output = proc.stdout.strip() or "(Program completed with no console output)"
                return {
                    "success": True,
                    "phase": "execution",
                    "output": output,
                    "duration": f"{duration}s",
                    "returncode": 0
                }
            else:
                return {
                    "success": False,
                    "phase": "execution",
                    "error": proc.stderr or proc.stdout,
                    "duration": f"{duration}s",
                    "returncode": proc.returncode
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "phase": "execution", "error": f"Execution timed out (> {timeout}s)."}
        except Exception as exc:
            return {"success": False, "phase": "execution", "error": f"Execution error: {exc}"}

code_runner = CodeRunner()
