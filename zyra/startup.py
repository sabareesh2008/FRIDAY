"""Windows startup integration for ZYRA assistant."""
import os
import sys
import winreg
from pathlib import Path

REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "ZYRA_Assistant"

class StartupManager:
    @staticmethod
    def get_run_command() -> str:
        project_root = Path(__file__).resolve().parent.parent
        bat_file = project_root / "run_zyra_daemon.bat"
        if bat_file.exists():
            return f'"{bat_file}"'
        daemon_py = project_root / "daemon_main.py"
        pythonw = Path(sys.executable).parent / "pythonw.exe"
        exe = pythonw if pythonw.exists() else sys.executable
        return f'"{exe}" "{daemon_py}"'

    def is_startup_enabled(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except OSError:
            return False

    def enable_startup(self) -> str:
        cmd = self.get_run_command()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            return "ZYRA will now start automatically when Windows boots."
        except Exception as exc:
            return f"Failed to enable startup: {exc}"

    def disable_startup(self) -> str:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, APP_NAME)
            return "ZYRA has been removed from Windows startup."
        except OSError:
            return "ZYRA was not configured to run on startup."
        except Exception as exc:
            return f"Failed to disable startup: {exc}"

startup_manager = StartupManager()
