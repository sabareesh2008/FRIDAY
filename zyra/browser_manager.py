"""Advanced Browser Automation, Tab Control, Extension Bridge & History Search for ZYRA/FRIDAY."""
import os
import re
import time
import json
import sqlite3
import shutil
import tempfile
import webbrowser
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

try:
    import uiautomation as auto
except ImportError:
    auto = None

class BrowserManager:
    def __init__(self):
        # Store extension-reported tab data when connected via extension bridge
        self._extension_tabs: List[Dict[str, Any]] = []
        self._last_extension_ping: float = 0.0

    # --- Extension Bridge Integration ---
    def update_extension_tabs(self, tabs: List[Dict[str, Any]]):
        """Called by local web bridge when browser extension syncs tabs."""
        self._extension_tabs = tabs
        self._last_extension_ping = time.time()

    def is_extension_connected(self) -> bool:
        return (time.time() - self._last_extension_ping) < 15.0 and len(self._extension_tabs) > 0

    # --- Window & Browser Activation ---
    @staticmethod
    def _activate_browser(preferred_browser: str = "chrome") -> bool:
        """Finds and brings the browser window to the foreground."""
        if os.name != "nt":
            return False
        targets = [preferred_browser.lower(), "chrome", "edge", "brave", "firefox"]
        matches = []

        def enum_cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.lower()
                    for t in targets:
                        if t in title:
                            matches.append(hwnd)
                            break
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if matches:
            hwnd = matches[0]
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.18)
            return True
        return False

    # --- Tab Inspection & Control ---
    def list_open_tabs(self) -> List[Dict[str, Any]]:
        """Returns list of open tabs with titles and URLs via Extension or UIA."""
        # 1. Extension bridge (highest fidelity)
        if self.is_extension_connected():
            return list(self._extension_tabs)

        # 2. Windows UI Automation tree inspection (Chrome/Edge accessibility tabs)
        tabs = []
        if auto:
            try:
                root = auto.GetRootControl()
                for win in root.GetChildren():
                    name_lower = (win.Name or "").lower()
                    if any(b in name_lower for b in ("chrome", "edge", "brave", "firefox")):
                        # Look for TabItem controls
                        for item in win.GetChildren():
                            self._extract_uia_tabs(item, tabs, win.Name)
            except Exception:
                pass
        return tabs

    def _extract_uia_tabs(self, control, result_list: List[Dict[str, Any]], window_name: str, depth: int = 4):
        if not control or depth <= 0:
            return
        try:
            if control.ControlTypeName == "TabItemControl" or "tab" in (control.Name or "").lower():
                title = control.Name.strip()
                if title and not any(t["title"] == title for t in result_list):
                    result_list.append({
                        "id": len(result_list) + 1,
                        "title": title,
                        "url": "",
                        "browser": window_name,
                        "control": control
                    })
            for child in control.GetChildren():
                self._extract_uia_tabs(child, result_list, window_name, depth - 1)
        except Exception:
            pass

    def get_open_tabs_report(self) -> str:
        """Formatted summary of currently open tabs."""
        tabs = self.list_open_tabs()
        if not tabs:
            return "No open browser tabs were detected. (Make sure Chrome or Edge is running)."
        lines = [f"Found {len(tabs)} open browser tab(s):"]
        for i, t in enumerate(tabs, 1):
            url_part = f" — {t['url']}" if t.get("url") else ""
            lines.append(f"{i}. {t.get('title', 'Untitled')}{url_part}")
        return "\n".join(lines)

    def switch_to_tab(self, target_query: str) -> str:
        """Switches to a specific tab matching title or URL query."""
        q = target_query.lower().strip()
        tabs = self.list_open_tabs()
        for t in tabs:
            title = t.get("title", "").lower()
            url = t.get("url", "").lower()
            if q in title or (url and q in url):
                # If UIA control is available
                ctrl = t.get("control")
                if ctrl:
                    try:
                        self._activate_browser()
                        rect = ctrl.BoundingRectangle
                        if rect.width() > 0:
                            import pyautogui
                            pyautogui.click((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)
                            return f"Switched to tab: {t.get('title')}."
                    except Exception:
                        pass
                # Otherwise focus browser
                self._activate_browser()
                return f"Switched to browser window for '{t.get('title')}'."

        return f"Could not find an open tab matching '{target_query}'."

    def close_specific_tab(self, target_to_close: str, keep_target: Optional[str] = None) -> str:
        """Closes a specific tab matching target_to_close without closing keep_target."""
        close_q = target_to_close.lower().strip()
        keep_q = keep_target.lower().strip() if keep_target else None

        tabs = self.list_open_tabs()
        closed = []
        kept = []

        for t in tabs:
            title = t.get("title", "").lower()
            url = t.get("url", "").lower()
            # If matches keep requirement, ensure preserved
            if keep_q and (keep_q in title or (url and keep_q in url)):
                kept.append(t.get("title"))
                continue

            # If matches close target
            if close_q in title or (url and close_q in url):
                ctrl = t.get("control")
                if ctrl:
                    try:
                        # Find close button on this tab control
                        rect = ctrl.BoundingRectangle
                        import pyautogui
                        # Tab close 'x' is usually at the far right of the tab rect
                        close_x = rect.right - 14
                        close_y = (rect.top + rect.bottom) // 2
                        pyautogui.click(close_x, close_y)
                        closed.append(t.get("title"))
                    except Exception:
                        pass

        if closed:
            keep_msg = f" (Kept '{', '.join(kept)}' open)" if kept else ""
            return f"Closed tab: {', '.join(closed)}{keep_msg}."

        # Fallback if no specific UIA tab close was reached
        self._activate_browser()
        return f"Attempted tab action for '{target_to_close}'."

    # --- History & Bookmarks Search ---
    def search_browser_history(self, query: str, max_results: int = 5) -> str:
        """Queries local Chrome or Edge SQLite history database without needing browser open."""
        q = query.lower().strip()
        history_paths = [
            Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "History",
            Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default" / "History",
        ]

        results = []
        for hp in history_paths:
            try:
                if not hp.exists():
                    continue
            except (PermissionError, OSError):
                continue
            # Copy to temp file to prevent database locked error if browser is currently running
            temp_db = Path(tempfile.gettempdir()) / f"zyra_hist_{os.getpid()}.sqlite"
            try:
                shutil.copy2(str(hp), str(temp_db))
                conn = sqlite3.connect(str(temp_db))
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT title, url, datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime') "
                    "FROM urls WHERE lower(title) LIKE ? OR lower(url) LIKE ? "
                    "ORDER BY last_visit_time DESC LIMIT ?",
                    (f"%{q}%", f"%{q}%", max_results)
                )
                for title, url, visit_time in cursor.fetchall():
                    results.append((title or "Untitled", url, visit_time))
                conn.close()
            except Exception:
                pass
            finally:
                if temp_db.exists():
                    try:
                        temp_db.unlink()
                    except Exception:
                        pass

            if results:
                break

        if not results:
            return f"No browser history found matching '{query}'."

        lines = [f"Found {len(results)} browser history item(s) for '{query}':"]
        for i, (title, url, visit_time) in enumerate(results, 1):
            lines.append(f"{i}. {title} — {url} ({visit_time})")
        return "\n".join(lines)

    # --- Standard Tab Shortcuts & URLs ---
    @staticmethod
    def _send_keys(*keys: str) -> str:
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.hotkey(*keys)
            return ""
        except Exception as exc:
            return f"Failed to send browser keys: {exc}"

    def tab_action(self, action: str) -> str:
        self._activate_browser()
        act = action.lower().strip()
        actions = {
            "new tab": (("ctrl", "t"), "Opened a new browser tab."),
            "close tab": (("ctrl", "w"), "Closed the current browser tab."),
            "reopen tab": (("ctrl", "shift", "t"), "Reopened the last closed tab."),
            "next tab": (("ctrl", "tab"), "Switched to next tab."),
            "previous tab": (("ctrl", "shift", "tab"), "Switched to previous tab."),
            "refresh": (("ctrl", "r"), "Refreshed the page."),
            "hard refresh": (("ctrl", "f5"), "Hard refreshed the page."),
            "history": (("ctrl", "h"), "Opened browser history."),
            "downloads": (("ctrl", "j"), "Opened browser downloads."),
            "bookmarks": (("ctrl", "shift", "o"), "Opened bookmarks manager."),
            "zoom in": (("ctrl", "plus"), "Zoomed in."),
            "zoom out": (("ctrl", "minus"), "Zoomed out."),
            "zoom reset": (("ctrl", "0"), "Reset zoom level."),
            "close browser": (("alt", "f4"), "Closed the active browser window."),
        }
        if act in actions:
            keys, msg = actions[act]
            err = self._send_keys(*keys)
            return err or msg
        return f"Unknown tab action: {action}"

    def search_page(self, query: str) -> str:
        if not query.strip():
            return "Please provide a search term for the page."
        self._activate_browser()
        err = self._send_keys("ctrl", "f")
        if err:
            return err
        time.sleep(0.1)
        try:
            import pyautogui
            pyautogui.write(query.strip(), interval=0.02)
            pyautogui.press("enter")
            return f"Searched current page for: {query.strip()}"
        except Exception as exc:
            return f"Failed to input search query: {exc}"

    @staticmethod
    def get_chrome_path() -> Optional[str]:
        for base in [os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", ""), os.environ.get("LOCALAPPDATA", "")]:
            if not base:
                continue
            cand = Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe"
            if cand.exists():
                return str(cand)
        return None

    @staticmethod
    def get_chrome_profile_directory(profile_query: str = "sabareesh") -> Optional[str]:
        """Inspects Chrome Local State to find matching profile directory (e.g. Profile 42 for Sabareesh)."""
        clean_q = profile_query.lower().strip()
        try:
            local_state = Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data" / "Local State"
            if local_state.exists():
                with open(local_state, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cache = data.get("profile", {}).get("info_cache", {})
                for p_dir, p_info in cache.items():
                    name = p_info.get("name", "").lower()
                    user_name = p_info.get("user_name", "").lower()
                    if clean_q == name or clean_q == user_name:
                        return p_dir
                for p_dir, p_info in cache.items():
                    name = p_info.get("name", "").lower()
                    user_name = p_info.get("user_name", "").lower()
                    if clean_q in name or clean_q in user_name:
                        return p_dir
        except Exception:
            pass
        if "sabareesh" in clean_q:
            return "Profile 42"
        return None

    def launch_chrome(self, url: Optional[str] = None, profile: Optional[str] = "Sabareesh") -> str:
        """Launches Google Chrome explicitly, opening directly into Sabareesh profile."""
        chrome_exe = self.get_chrome_path()
        if not chrome_exe:
            if url:
                webbrowser.open(url)
                return f"Opening {url} in browser."
            return "Google Chrome executable was not found on this system."

        args = [chrome_exe]
        from zyra.config import config
        prof_name = profile or config.get("chrome_profile", "Sabareesh")
        prof_dir = self.get_chrome_profile_directory(prof_name)
        if prof_dir:
            args.append(f"--profile-directory={prof_dir}")

        if url:
            if not re.match(r"^https?://", url, re.IGNORECASE):
                url = "https://" + url
            args.append(url)

        try:
            import subprocess
            subprocess.Popen(args, shell=False)
            target_desc = f" ({url})" if url else ""
            prof_desc = f" under {prof_name} profile" if prof_dir else ""
            return f"Opening Chrome{target_desc}{prof_desc}."
        except Exception as exc:
            return f"Failed to launch Chrome: {exc}"

    def open_url(self, address: str, in_new_tab: bool = False) -> str:
        addr = address.strip()
        if not addr:
            return "Please specify a URL or website."
        if not re.match(r"^https?://", addr, re.IGNORECASE):
            addr = "https://" + addr

        chrome_exe = self.get_chrome_path()
        if chrome_exe:
            from zyra.config import config
            prof = config.get("chrome_profile", "Sabareesh")
            self.launch_chrome(addr, profile=prof)
            return f"Opening {addr} in Chrome."

        try:
            webbrowser.open(addr, new=2 if in_new_tab else 0)
            return f"Opening {addr} in browser."
        except Exception as exc:
            return f"Failed to open website: {exc}"

    def web_search(self, engine: str, query: str) -> str:
        q = urllib.parse.quote_plus(query.strip())
        urls = {
            "google": f"https://www.google.com/search?q={q}",
            "youtube": f"https://www.youtube.com/results?search_query={q}",
            "github": f"https://github.com/search?q={q}",
            "wikipedia": f"https://en.wikipedia.org/wiki/Special:Search?search={q}",
            "stackoverflow": f"https://stackoverflow.com/search?q={q}",
        }
        target_url = urls.get(engine.lower(), urls["google"])
        self.open_url(target_url)
        return f"Searching {engine.capitalize()} for '{query}'."

    def open_gmail(self, email_address: Optional[str] = None) -> str:
        if email_address:
            url = f"https://mail.google.com/mail/u/?authuser={urllib.parse.quote_plus(email_address)}"
            return self.open_url(url)
        return self.open_url("https://mail.google.com")

browser_manager = BrowserManager()
