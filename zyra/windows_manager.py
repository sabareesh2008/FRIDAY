"""Windows system management, dynamic app discovery, window operations, and power actions."""
import os
import sys
import subprocess
import shutil
import difflib
import winreg
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import ctypes
from ctypes import wintypes
from zyra.safety import safety_guard

user32 = ctypes.windll.user32

class WindowsManager:
    def __init__(self):
        self._apps_cache: Dict[str, str] = {}
        self._refresh_apps_cache()

    def _refresh_apps_cache(self):
        """Scans registry and Start Menu shortcuts to dynamically discover all installed software."""
        discovered: Dict[str, str] = {}

        # 1. Standard Windows Utilities & UWP Apps
        builtin_tools = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "camera": "microsoft.windows.camera:",
            "webcam": "microsoft.windows.camera:",
            "cam": "microsoft.windows.camera:",
            "web camera": "microsoft.windows.camera:",
            "photos": "ms-photos:",
            "paint": "mspaint.exe",
            "clock": "ms-clock:",
            "alarm": "ms-clock:",
            "alarms": "ms-clock:",
            "file explorer": "explorer.exe",
            "explorer": "explorer.exe",
            "command prompt": "cmd.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "task manager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "control panel": "control.exe",
            "registry editor": "regedit.exe",
            "snipping tool": "snippingtool.exe",
            "settings": "ms-settings:",
            "store": "ms-windows-store:",
            "windows store": "ms-windows-store:",
            "weather": "bingweather:",
            "maps": "bingmaps:",
        }
        discovered.update(builtin_tools)

        # 2. Registry App Paths
        for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(root_key, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths") as key:
                    count, _, _ = winreg.QueryInfoKey(key)
                    for i in range(count):
                        name = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, name) as subkey:
                                exe_path, _ = winreg.QueryValueEx(subkey, "")
                                if exe_path and os.path.exists(exe_path):
                                    stem = Path(name).stem.lower()
                                    discovered[stem] = exe_path
                                    discovered[name.lower()] = exe_path
                        except OSError:
                            pass
            except OSError:
                pass

        # 3. Start Menu Shortcuts (.lnk)
        for env_var in ("ProgramData", "APPDATA"):
            base = os.environ.get(env_var, "")
            if not base:
                continue
            sm = Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            if sm.exists():
                for root, _, files in os.walk(sm):
                    for f in files:
                        if f.lower().endswith(".lnk"):
                            stem = Path(f).stem.lower()
                            full_path = str(Path(root) / f)
                            discovered[stem] = full_path

        self._apps_cache = discovered

    def find_app_path(self, app_name: str) -> Optional[str]:
        """Finds application path using exact or fuzzy matching."""
        clean = app_name.lower().strip()
        if clean in self._apps_cache:
            return self._apps_cache[clean]

        # Aliases
        aliases = {
            "chrome": ["google chrome", "chrome.exe"],
            "vs code": ["visual studio code", "code"],
            "vscode": ["visual studio code", "code"],
            "word": ["microsoft word", "winword"],
            "excel": ["microsoft excel", "excel"],
            "powerpoint": ["microsoft powerpoint", "powerpnt"],
            "browser": ["google chrome", "brave", "msedge"],
            "edge": ["microsoft edge", "msedge"],
        }
        for alias_key, targets in aliases.items():
            if clean == alias_key:
                for target in targets:
                    if target in self._apps_cache:
                        return self._apps_cache[target]

        # Fuzzy match
        keys = list(self._apps_cache.keys())
        matches = difflib.get_close_matches(clean, keys, n=1, cutoff=0.6)
        if matches:
            return self._apps_cache[matches[0]]

        # Substring search
        for key, path in self._apps_cache.items():
            if clean in key or key in clean:
                return path

        return None

    def launch_app(self, app_name: str) -> str:
        """Launches an application by name or path."""
        target = self.find_app_path(app_name)
        if not target:
            # Refresh cache once in case new app was installed
            self._refresh_apps_cache()
            target = self.find_app_path(app_name)

        if target:
            try:
                # Handle Windows URI schemes (e.g. microsoft.windows.camera:, ms-settings:, ms-photos:)
                if ":" in target and not (len(target) > 2 and target[1] == ":" and target[2] in "\\/"):
                    os.startfile(target)
                elif target.lower().endswith(".lnk"):
                    os.startfile(target)
                else:
                    subprocess.Popen([target], shell=False)
                return f"Launching {app_name}."
            except Exception as exc:
                return f"Failed to launch {app_name}: {exc}"

        return f"Could not find an installed application matching '{app_name}'."

    # --- Window Management ---
    def list_open_windows(self) -> List[Tuple[int, str]]:
        """Returns list of visible window (hwnd, title) pairs."""
        results = []
        def enum_cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.strip()
                    if title and title not in ("Program Manager", "Settings", "Default IME"):
                        results.append((hwnd, title))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return results

    def find_window_by_title(self, query: str) -> Optional[int]:
        query_clean = query.lower().strip()
        windows = self.list_open_windows()
        for hwnd, title in windows:
            if query_clean in title.lower():
                return hwnd
        # Fuzzy match
        titles = [t for _, t in windows]
        matches = difflib.get_close_matches(query_clean, [t.lower() for t in titles], n=1, cutoff=0.5)
        if matches:
            for hwnd, title in windows:
                if title.lower() == matches[0]:
                    return hwnd
        return None

    def focus_window(self, query: str) -> str:
        hwnd = self.find_window_by_title(query)
        if not hwnd:
            return f"I couldn't find an open window matching '{query}'."
        try:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            return f"Brought window '{query}' to the front."
        except Exception as exc:
            return f"Could not focus window: {exc}"

    def close_window(self, query: str = "") -> str:
        if query:
            hwnd = self.find_window_by_title(query)
            if not hwnd:
                return f"No open window matching '{query}' found to close."
            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            return f"Closed window matching '{query}'."
        else:
            # Close active window via Alt+F4
            return self.send_shortcut("alt", "f4", message="Closed the active window.")

    def maximize_window(self, query: str = "") -> str:
        if query:
            hwnd = self.find_window_by_title(query)
            if hwnd:
                user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                return f"Maximized '{query}'."
            return f"Could not find window matching '{query}'."
        return self.send_shortcut("win", "up", message="Maximized the active window.")

    def minimize_window(self, query: str = "") -> str:
        if query:
            hwnd = self.find_window_by_title(query)
            if hwnd:
                user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                return f"Minimized '{query}'."
            return f"Could not find window matching '{query}'."
        return self.send_shortcut("win", "down", message="Minimized the active window.")

    def show_desktop(self) -> str:
        return self.send_shortcut("win", "d", message="Showing desktop.")

    def switch_window(self) -> str:
        return self.send_shortcut("alt", "tab", message="Switched to next window.")

    @staticmethod
    def send_shortcut(*keys: str, message: str = "Action completed.") -> str:
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.hotkey(*keys)
            return message
        except Exception as exc:
            return f"Failed to send keyboard shortcut: {exc}"

    # --- Volume Control ---
    @staticmethod
    def volume_control(action: str) -> str:
        try:
            import pyautogui
            act = action.lower().strip()
            if act in ("mute", "unmute", "toggle mute"):
                pyautogui.press("volumemute")
                return "Toggled volume mute."
            elif act in ("up", "volume up", "louder"):
                for _ in range(5):
                    pyautogui.press("volumeup")
                return "Increased volume."
            elif act in ("down", "volume down", "quieter"):
                for _ in range(5):
                    pyautogui.press("volumedown")
                return "Decreased volume."
        except Exception as exc:
            return f"Could not adjust volume: {exc}"
        return "Unknown volume command."

    # --- Power Actions (Guarded) ---
    def lock_workstation(self) -> str:
        try:
            user32.LockWorkStation()
            return "Locked your workstation."
        except Exception as exc:
            return f"Failed to lock workstation: {exc}"

    def sleep_pc(self) -> str:
        def do_sleep():
            try:
                subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], shell=False)
                return "Putting PC to sleep."
            except Exception as exc:
                return f"Failed to put PC to sleep: {exc}"

        return safety_guard.request_confirmation(
            action_type="sleep_pc",
            description="put the computer to sleep",
            callback=do_sleep
        )

    def restart_pc(self) -> str:
        def do_restart():
            try:
                subprocess.Popen(["shutdown", "/r", "/t", "5"], shell=False)
                return "Restarting computer in 5 seconds."
            except Exception as exc:
                return f"Failed to initiate restart: {exc}"

        return safety_guard.request_confirmation(
            action_type="restart_pc",
            description="restart the computer",
            callback=do_restart
        )

    def shutdown_pc(self) -> str:
        def do_shutdown():
            try:
                subprocess.Popen(["shutdown", "/s", "/t", "5"], shell=False)
                return "Shutting down computer in 5 seconds."
            except Exception as exc:
                return f"Failed to initiate shutdown: {exc}"

        return safety_guard.request_confirmation(
            action_type="shutdown_pc",
            description="shut down the computer",
            callback=do_shutdown
        )

    # --- Virtual Desktops ---
    def create_virtual_desktop(self) -> str:
        try:
            import pyautogui
            pyautogui.hotkey("win", "ctrl", "d")
            return "Created a new virtual desktop."
        except Exception as exc:
            return f"Failed to create virtual desktop: {exc}"

    def close_virtual_desktop(self) -> str:
        try:
            import pyautogui
            pyautogui.hotkey("win", "ctrl", "f4")
            return "Closed current virtual desktop."
        except Exception as exc:
            return f"Failed to close virtual desktop: {exc}"

    def switch_virtual_desktop(self, direction: str = "next") -> str:
        try:
            import pyautogui
            key = "right" if direction.lower() in ("next", "right") else "left"
            pyautogui.hotkey("win", "ctrl", key)
            return f"Switched to {direction} virtual desktop."
        except Exception as exc:
            return f"Failed to switch virtual desktop: {exc}"

    def list_virtual_desktops(self) -> str:
        return (
            "Windows Virtual Desktops:\n"
            "• Create: 'create virtual desktop'\n"
            "• Close: 'close virtual desktop'\n"
            "• Switch: 'next desktop' or 'previous desktop'\n"
            "• Overview: Press Win+Tab for Task View."
        )

windows_manager = WindowsManager()
