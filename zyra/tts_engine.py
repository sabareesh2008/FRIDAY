"""Dedicated, ultra-reliable Lady Voice Speech Engine for FRIDAY with native Windows SAPI COM and 'sir' personalization."""
import queue
import threading
import time
import re
from typing import Optional
from zyra.config import config

class TTSEngine:
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.running = True
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def _speech_worker(self):
        """Worker thread dedicated to native Windows SAPI5 audio playback with COM apartment."""
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

        # 1. Primary: Native Windows SAPI.SpVoice (bulletproof on Windows)
        sapi_voice = None
        try:
            import win32com.client
            sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
            # Select Lady Voice (Hazel or Zira)
            for v in sapi_voice.GetVoices():
                desc = v.GetDescription().lower()
                if "hazel" in desc or "zira" in desc or "female" in desc:
                    sapi_voice.Voice = v
                    break
        except Exception:
            sapi_voice = None

        # 2. Fallback: pyttsx3
        pyttsx_engine = None
        if not sapi_voice:
            try:
                import pyttsx3
                pyttsx_engine = pyttsx3.init()
                voices = pyttsx_engine.getProperty("voices")
                lady = next((v for v in voices if "hazel" in v.name.lower() or "zira" in v.name.lower()), None)
                if lady:
                    pyttsx_engine.setProperty("voice", lady.id)
            except Exception:
                pyttsx_engine = None

        while self.running:
            try:
                item = self.speech_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if not item:
                continue

            text, user_title = item
            if not config.get("tts_enabled", True):
                continue

            spoken_text = self.format_speech_text(text, user_title)
            if not spoken_text:
                continue

            # Play using SAPI.SpVoice
            if sapi_voice:
                try:
                    sapi_voice.Volume = int(config.get("tts_volume", 1.0) * 100)
                    sapi_voice.Rate = 1  # 0 is normal, 1 is slightly faster
                    sapi_voice.Speak(spoken_text)
                    continue
                except Exception:
                    pass

            # Fallback to pyttsx3
            if pyttsx_engine:
                try:
                    pyttsx_engine.say(spoken_text)
                    pyttsx_engine.runAndWait()
                except Exception:
                    pass

    @staticmethod
    def format_speech_text(text: str, user_title: str = "sir") -> str:
        """Enriches responses naturally with respectful 'sir' addressing."""
        clean = text.strip()
        if not clean:
            return ""

        # Remove markdown fences or code blocks for speech clarity
        clean = re.sub(r"```[\s\S]*?```", f"Code generated for you, {user_title}.", clean)
        clean = re.sub(r"([a-zA-Z]:\\[^\s,]+)", "specified folder", clean)
        clean = re.sub(r"\n+", " ", clean).strip()

        lower = clean.lower()
        if lower in {"yes", "yes?", "listening", "yes, sir?", "yes, i'm listening", "yes, i'm listening."}:
            return f"Yes, {user_title}? How can I help you?"
        if lower in {"goodbye", "goodbye!"}:
            return f"Goodbye, {user_title}. Have a great day."

        # If already contains user title, keep it clean
        if re.search(rf"\b{user_title}\b", clean, re.IGNORECASE):
            return clean

        # Natural prefix/suffix for action confirmations
        if any(clean.startswith(w) for w in ("Opened", "Created", "Launched", "Playing", "Switched", "Maximized", "Minimized", "Closed", "Searched")):
            return f"{clean}, {user_title}."

        return clean

    def speak(self, text: str):
        user_title = config.get("user_title", "sir")
        self.speech_queue.put((text, user_title))

    def stop(self):
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break

tts_engine = TTSEngine()
