"""Background Windows Standby Daemon: Auto-boot, startup greeting, and hands-free 'Hey ZYRA' wake-word activation."""
import os
import sys
import time
import datetime
import threading
from typing import Optional

from zyra.config import config
from zyra.ai_engine import ai_engine
from zyra.media_finder import media_finder
from zyra.voice_manager import normalize_voice_transcript
from zyra.tts_engine import tts_engine

class ZyraDaemon:
    def __init__(self):
        self.running = True

    def speak(self, text: str):
        tts_engine.speak(text)

    def get_greeting(self) -> str:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            time_greeting = "Good morning"
        elif 12 <= hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        asst_name = config.get("assistant_name", "FRIDAY")
        user_title = config.get("user_title", "sir")
        return f"{time_greeting}, {user_title}! {asst_name} is online and at your service. Say 'Hey {asst_name}' whenever you need me."

    def start(self):
        asst_name = config.get("assistant_name", "FRIDAY")
        # Start background media indexing
        media_finder.start_indexing()

        # Speak startup greeting aloud
        greeting = self.get_greeting()
        print(f"\n[{asst_name} DAEMON] {greeting}")
        self.speak(greeting)

        # Start continuous hands-free wake-word loop
        self.listen_for_wake_word()

    def listen_for_wake_word(self):
        asst_name = config.get("assistant_name", "FRIDAY")
        try:
            import speech_recognition as sr
        except ImportError:
            print(f"[{asst_name} DAEMON] speech_recognition not available.")
            return

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 300
        recognizer.pause_threshold = 0.8

        try:
            microphone = sr.Microphone()
        except Exception as exc:
            print(f"[{asst_name} DAEMON] Microphone error: {exc}")
            return

        with microphone as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
            except Exception:
                pass

            lang = config.get("stt_language", "en-IN")
            print(f"[{asst_name} DAEMON] Passive listening for 'Hey {asst_name}'...")

            while self.running:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    continue
                except Exception:
                    continue

                try:
                    raw = recognizer.recognize_google(audio, language=lang)
                    normalized = normalize_voice_transcript(raw)
                    lower = normalized.lower().strip()

                    wake_words = tuple(config.get("wake_words", ["hey friday", "friday", "hey zyra", "zyra"]))
                    has_wake = any(w in lower for w in wake_words)

                    if has_wake:
                        print(f"\n[{asst_name} WAKE] Detected wake phrase: '{raw}'")
                        # If user gave a full command directly e.g. "Hey Friday open VS Code"
                        cleaned_cmd = re_strip_wake(normalized)
                        if cleaned_cmd:
                            self.execute_and_speak(cleaned_cmd)
                        else:
                            # Prompt user with respectful voice
                            user_title = config.get("user_title", "sir")
                            self.speak(f"Yes, {user_title}? What can I do for you?")
                            try:
                                cmd_audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                                cmd_raw = recognizer.recognize_google(cmd_audio, language=lang)
                                cmd_norm = normalize_voice_transcript(cmd_raw)
                                print(f"[{asst_name} COMMAND] Heard: '{cmd_norm}'")
                                self.execute_and_speak(cmd_norm)
                            except Exception:
                                pass
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    time.sleep(2)
                    continue

    def execute_and_speak(self, command: str):
        if not command.strip():
            return
        asst_name = config.get("assistant_name", "FRIDAY")
        result = ai_engine.parse_and_execute(command)
        if result == "QUIT_SIGNAL":
            self.speak(f"{asst_name} is going to sleep. Goodbye!")
            self.running = False
            return
        if result:
            print(f"\n{asst_name}: {result}")
            # Summarize long result for speech (first 2 sentences or 200 chars)
            speech_text = result.split("\n\n")[0]
            if len(speech_text) > 250:
                speech_text = speech_text[:250] + "..."
            self.speak(speech_text)

def re_strip_wake(cmd: str) -> str:
    import re
    return re.sub(r"^\s*(?:hey\s+)?(?:friday|zyra)[\s,.:!-]*", "", cmd, flags=re.IGNORECASE).strip()

daemon_instance = ZyraDaemon()
