"""Autonomous Computer-Using Agent & Screen Operator for FRIDAY.

Provides visual grounding, UI element discovery, mouse/keyboard manipulation,
browser navigation, download monitoring, and arbitrary custom task automation.
"""
import os
import re
import time
import json
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

try:
    import uiautomation as auto
except ImportError:
    auto = None

try:
    import mss
except ImportError:
    mss = None

from zyra.config import config
from zyra.tts_engine import tts_engine
from zyra.vision_manager import vision_manager

class ScreenOperator:
    def __init__(self):
        self.downloads_dir = Path.home() / "Downloads"
        self._last_download_file: Optional[Path] = None
        self._download_monitor_thread: Optional[threading.Thread] = None
        self._monitoring_downloads: bool = False
        self.start_download_watcher()

    # --- Mouse & Cursor Automation ---
    def get_screen_size(self) -> Tuple[int, int]:
        if pyautogui:
            return pyautogui.size()
        return (1920, 1080)

    def click(self, target: str) -> str:
        """Finds element on screen by text/description or coordinates, and clicks it."""
        user_title = config.get("user_title", "sir")
        if not pyautogui:
            return f"PyAutoGUI is not available to click, {user_title}."

        clean_target = target.strip()

        # 1. Check if coordinate format like "500, 300" or "500 300"
        coord_match = re.match(r"^(\d+)[,\s]+(\d+)$", clean_target)
        if coord_match:
            x, y = int(coord_match.group(1)), int(coord_match.group(2))
            pyautogui.moveTo(x, y, duration=0.25)
            pyautogui.click()
            return f"Clicked at coordinates ({x}, {y}), {user_title}."

        # 2. Try locating element via Windows UI Automation (Native, Fast, Exact)
        point = self._find_element_via_uia(clean_target)
        if point:
            x, y = point
            pyautogui.moveTo(x, y, duration=0.25)
            pyautogui.click()
            return f"Found and clicked '{clean_target}' at ({x}, {y}), {user_title}."

        # 3. Try locating element via Visual AI (Gemini Flash Multimodal Grounding)
        api_key = config.get("api_key", "").strip() or config.get("gemini_api_key", "").strip()
        if api_key:
            point = self._find_element_via_vision(clean_target, api_key)
            if point:
                x, y = point
                pyautogui.moveTo(x, y, duration=0.25)
                pyautogui.click()
                return f"Visually located and clicked '{clean_target}' at ({x}, {y}), {user_title}."

        # 4. Fallback: Browser In-Page Text Search and Click
        # If in a browser or document, jump to target text using Ctrl+F
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.15)
        pyautogui.write(clean_target, interval=0.02)
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.15)
        pyautogui.press("esc")  # Close find bar, focus matched element
        time.sleep(0.1)
        pyautogui.press("enter")  # Activate link/element if focused
        return f"Searched on-screen for '{clean_target}' and selected it, {user_title}."

    def double_click(self, target: Optional[str] = None) -> str:
        """Double clicks target element or current cursor location."""
        user_title = config.get("user_title", "sir")
        if not pyautogui:
            return f"PyAutoGUI is not available, {user_title}."

        if target and target.strip():
            self.click(target)
            pyautogui.doubleClick()
            return f"Double-clicked '{target}', {user_title}."
        pyautogui.doubleClick()
        return f"Double-clicked at current position, {user_title}."

    def right_click(self, target: Optional[str] = None) -> str:
        """Right clicks target element or current cursor location."""
        user_title = config.get("user_title", "sir")
        if not pyautogui:
            return f"PyAutoGUI is not available, {user_title}."

        if target and target.strip():
            point = self._find_element_via_uia(target) or (
                self._find_element_via_vision(target, config.get("api_key", "")) if config.get("api_key") else None
            )
            if point:
                pyautogui.moveTo(point[0], point[1], duration=0.25)
                pyautogui.rightClick()
                return f"Right-clicked '{target}' at ({point[0]}, {point[1]}), {user_title}."
        pyautogui.rightClick()
        return f"Right-clicked, {user_title}."

    # --- Keyboard & Text Automation ---
    def type_text(self, text: str, press_enter: bool = False) -> str:
        """Types specified text naturally, optionally pressing enter."""
        user_title = config.get("user_title", "sir")
        if not pyautogui:
            return f"PyAutoGUI is not available, {user_title}."

        # Strip outer quotes if passed as "hello world"
        clean = text.strip().strip("\"'")
        pyautogui.write(clean, interval=0.02)
        if press_enter:
            time.sleep(0.1)
            pyautogui.press("enter")
            return f"Typed '{clean}' and pressed Enter, {user_title}."
        return f"Typed '{clean}', {user_title}."

    def press_key(self, key_combo: str) -> str:
        """Presses single key, combination, or multi-step shortcut chord (e.g. 'ctrl+k ctrl+o')."""
        user_title = config.get("user_title", "sir")
        if not pyautogui:
            return f"PyAutoGUI is not available, {user_title}."

        clean = key_combo.lower().strip()

        # Normalize "ctrl k" -> "ctrl+k"
        normalized = re.sub(r"\bctrl\s+([a-z0-9])\b", r"ctrl+\1", clean)
        normalized = re.sub(r"\balt\s+([a-z0-9])\b", r"alt+\1", normalized)
        normalized = re.sub(r"\bshift\s+([a-z0-9])\b", r"shift+\1", normalized)

        # Split multiple chords (e.g. "ctrl+k ctrl+o" -> ["ctrl+k", "ctrl+o"])
        parts = [p.strip() for p in re.split(r"[\s,]+|\band\b", normalized) if p.strip()]

        if len(parts) > 1 and all("+" in p or len(p) <= 2 or p in ("enter", "esc", "tab", "space") for p in parts):
            executed = []
            for part in parts:
                if "+" in part:
                    keys = [k.strip() for k in part.split("+")]
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(part)
                executed.append(part.upper())
                time.sleep(0.18)
            return f"Executed shortcut chord: {' '.join(executed)}, {user_title}."

        # Single combination
        if "+" in clean:
            keys = [k.strip() for k in clean.split("+")]
            pyautogui.hotkey(*keys)
            return f"Pressed {' + '.join(keys).upper()}, {user_title}."

        pyautogui.press(clean)
        return f"Pressed {clean.upper()}, {user_title}."

    def scroll(self, direction: str = "down", amount: int = 5) -> str:
        """Scrolls active page or window up or down."""
        user_title = config.get("user_title", "sir")
        if not pyautogui:
            return f"PyAutoGUI is not available, {user_title}."

        clicks = -abs(amount) * 120 if direction.lower() in ("down", "bottom") else abs(amount) * 120
        pyautogui.scroll(clicks)
        return f"Scrolled {direction}, {user_title}."

    # --- Browser & Link Navigation ---
    def search_and_enter(self, query: str) -> str:
        """Focuses browser search bar (Ctrl+L or Ctrl+E), types query and searches."""
        user_title = config.get("user_title", "sir")
        if not pyautogui:
            return f"PyAutoGUI is not available, {user_title}."

        clean_query = query.strip()
        # Focus browser address/search bar
        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.15)
        pyautogui.write(clean_query, interval=0.02)
        time.sleep(0.1)
        pyautogui.press("enter")
        return f"Searching for '{clean_query}' in browser, {user_title}."

    def open_link_or_item(self, target: str) -> str:
        """Opens link or item by clicking it or jumping via in-page navigation."""
        user_title = config.get("user_title", "sir")
        clean = target.strip()
        # If it looks like a URL, open directly
        if clean.startswith(("http://", "https://", "www.")) or ("." in clean and " " not in clean):
            from zyra.browser_manager import browser_manager
            return browser_manager.open_url(clean)

        return self.click(clean)

    # --- Download Automation & Monitoring ---
    def trigger_download(self) -> str:
        """Finds download buttons/links on screen or triggers browser download shortcut."""
        user_title = config.get("user_title", "sir")
        # Try common download button names
        for label in ("download", "download file", "save file", "get file", "direct download"):
            point = self._find_element_via_uia(label)
            if point:
                pyautogui.moveTo(point[0], point[1], duration=0.25)
                pyautogui.click()
                return f"Found and clicked '{label}' button. Watching for download completion, {user_title}."

        # Fallback to saving or browser download page
        pyautogui.hotkey("ctrl", "s")
        time.sleep(0.5)
        pyautogui.press("enter")
        return f"Triggered download save dialog, {user_title}."

    def start_download_watcher(self):
        """Monitors user's Downloads folder in the background to alert when downloads finish."""
        if self._monitoring_downloads:
            return
        self._monitoring_downloads = True
        self._download_monitor_thread = threading.Thread(target=self._watch_downloads_loop, daemon=True)
        self._download_monitor_thread.start()

    def _watch_downloads_loop(self):
        seen_files = set()
        if self.downloads_dir.exists():
            try:
                seen_files = {f.name for f in self.downloads_dir.iterdir()}
            except Exception:
                seen_files = set()

        while self._monitoring_downloads:
            time.sleep(2.0)
            if not self.downloads_dir.exists():
                continue
            try:
                current_files = list(self.downloads_dir.iterdir())
                for f in current_files:
                    if f.name not in seen_files:
                        # Ignore partial temporary download extensions
                        if f.suffix.lower() in (".crdownload", ".tmp", ".part", ".downloading"):
                            continue
                        seen_files.add(f.name)
                        # Confirm file is not still growing
                        time.sleep(1.0)
                        user_title = config.get("user_title", "sir")
                        tts_engine.speak(f"Your download of {f.name} is complete, {user_title}.")
            except Exception:
                pass

    # --- Element Finding Engine ---
    def _find_element_via_uia(self, query: str) -> Optional[Tuple[int, int]]:
        """Scans Windows UI Automation tree to locate element matching query."""
        if not auto:
            return None
        q = query.lower().strip()
        root = auto.GetRootControl()

        # 1. Search Active / Focused Window First (fastest)
        try:
            focused = auto.GetFocusedControl()
            if focused:
                top_win = focused.GetTopLevelControl()
                point = self._search_control_tree(top_win, q)
                if point:
                    return point
        except Exception:
            pass

        # 2. Search Desktop Children
        try:
            for win in root.GetChildren():
                try:
                    if win.IsOffscreen:
                        continue
                    point = self._search_control_tree(win, q)
                    if point:
                        return point
                except Exception:
                    continue
        except Exception:
            pass

        return None

    def _search_control_tree(self, control, query: str, max_depth: int = 5) -> Optional[Tuple[int, int]]:
        """Recursively inspects control children for matching element."""
        if not control:
            return None

        # Check self
        try:
            name = (control.Name or "").strip().lower()
            auto_id = (control.AutomationId or "").strip().lower()
            if query in name or query in auto_id:
                rect = control.BoundingRectangle
                if rect.width() > 0 and rect.height() > 0:
                    cx = (rect.left + rect.right) // 2
                    cy = (rect.top + rect.bottom) // 2
                    return (cx, cy)
        except Exception:
            pass

        if max_depth <= 0:
            return None

        try:
            for child in control.GetChildren():
                try:
                    if child.IsOffscreen:
                        continue
                    res = self._search_control_tree(child, query, max_depth - 1)
                    if res:
                        return res
                except Exception:
                    continue
        except Exception:
            pass

        return None

    def _find_element_via_vision(self, query: str, api_key: str) -> Optional[Tuple[int, int]]:
        """Takes a screenshot and asks Gemini Flash Vision to return pixel coordinates."""
        try:
            img_path = vision_manager.capture_screenshot()
            if not img_path or not os.path.exists(img_path):
                return None

            screen_w, screen_h = self.get_screen_size()
            prompt = (
                f"You are a computer UI vision grounding system. Locate the UI element or text on the screen corresponding to: '{query}'. "
                f"The screen resolution is {screen_w}x{screen_h}. "
                "Respond ONLY with a JSON object in this exact format: {\"found\": true, \"x\": <integer_x>, \"y\": <integer_y>} "
                "or {\"found\": false} if the element is not visible. Do not write explanations or markdown code fences."
            )

            raw_resp = vision_manager._gemini_vision_query(img_path, prompt, api_key)
            if not raw_resp:
                return None

            # Clean JSON response
            cleaned = re.sub(r"^```(?:json)?", "", raw_resp.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
            data = json.loads(cleaned)
            if data.get("found") and "x" in data and "y" in data:
                return (int(data["x"]), int(data["y"]))
        except Exception:
            pass
        return None

screen_operator = ScreenOperator()
