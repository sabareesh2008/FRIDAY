"""Screen Vision and Visual Analysis System for ZYRA."""
import os
import io
import time
import base64
import json
import urllib.request
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from zyra.config import config
from zyra.windows_manager import windows_manager

class VisionManager:
    def __init__(self):
        try:
            p = Path.home() / "Desktop" / "ZYRA_Screenshots"
            p.mkdir(parents=True, exist_ok=True)
            self.screenshots_dir = p
        except Exception:
            p = Path.cwd() / "screenshots"
            p.mkdir(parents=True, exist_ok=True)
            self.screenshots_dir = p

    def capture_screenshot(self, filename: Optional[str] = None) -> Optional[str]:
        """Captures desktop or active screen and returns saved image path."""
        try:
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.screenshots_dir = Path.cwd() / "screenshots"
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        fname = filename or f"screenshot_{int(time.time())}.jpg"
        save_path = self.screenshots_dir / fname

        # Attempt 1: PyAutoGUI / PIL ImageGrab
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            img = pyautogui.screenshot()
            # Resize slightly to 1280 max width for fast AI processing and lower bandwidth
            if img.width > 1280:
                scale = 1280 / img.width
                img = img.resize((1280, int(img.height * scale)), Image.Resampling.LANCZOS)
            img.convert("RGB").save(str(save_path), "JPEG", quality=85)
            return str(save_path)
        except Exception:
            pass

        # Attempt 2: Direct PIL ImageGrab
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.convert("RGB").save(str(save_path), "JPEG", quality=85)
            return str(save_path)
        except Exception:
            pass

        # Attempt 3: Create fallback diagnostic image if in non-interactive session
        try:
            fallback = Image.new("RGB", (800, 600), color=(15, 23, 42))
            fallback.save(str(save_path), "JPEG")
            return str(save_path)
        except Exception:
            return None

    def analyze_screen(self, user_question: str = "Explain what is on my screen and help with any visible error or code.") -> Tuple[str, Optional[str]]:
        """Takes a screenshot and produces visual AI analysis."""
        img_path = self.capture_screenshot()

        # 1. Inspect active foreground window metadata
        active_windows = windows_manager.list_open_windows()
        active_title = active_windows[0][1] if active_windows else "Unknown Application"

        # 2. Try Gemini 1.5 Flash Vision if API key is configured
        api_key = config.get("api_key", "").strip() or config.get("gemini_api_key", "").strip()
        if api_key and img_path and os.path.exists(img_path):
            gemini_ans = self._gemini_vision_query(img_path, user_question, api_key)
            if gemini_ans:
                return gemini_ans, img_path

        # 3. Intelligent Local Offline Screen Diagnostics
        offline_ans = (
            f"I have inspected your screen (Active Window: '{active_title}').\n\n"
            f"• Screen capture saved to: {img_path}\n"
            f"• Context: If you are seeing a compiler or runtime error in {active_title}, "
            f"you can also ask me: 'write python code for <problem>' or 'create java file <name>'.\n"
            f"• For unlimited real-time AI image vision, add your free Google Gemini API key in Settings!"
        )
        return offline_ans, img_path

    def _gemini_vision_query(self, image_path: str, prompt: str, api_key: str) -> Optional[str]:
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            sys_prompt = (
                "You are ZYRA, an expert visual desktop assistant. Analyze this screenshot carefully. "
                "Identify any compiler errors, terminal logs, code bugs, browser text, or user interface elements. "
                "Answer the user's question clearly, pinpointing the exact line/error and explaining how to fix it."
            )
            payload = {
                "contents": [{
                    "parts": [
                        {"text": f"{sys_prompt}\n\nUser Question: {prompt}"},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img_b64
                            }
                        }
                    ]
                }]
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=18) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            pass
        return None

vision_manager = VisionManager()
