"""Hands-free voice recognition, wake word detection, audio sensitivity, and TTS for ZYRA."""
import re
import threading
import time
from typing import Callable, Optional, List
from zyra.config import config
from zyra.tts_engine import tts_engine

# Phonetic and slang normalization dictionary for noisy/misheard speech recognition
SPEECH_REPLACEMENTS = [
    # Wake word variants
    (r"\b(?:hey\s+)?(?:friday|fryday|frieday|frida)\b", "friday"),
    (r"\b(?:hey\s+)?(?:zira|zara|zeera|sara|syra|xira|jyra)\b", "friday"),
    (r"\b(?:hey\s+)?zyra\b", "friday"),
    # User name normalization
    (r"\b(?:sabarish|sabreesh|shabareesh|sabrees|subareesh|sapareesh)\b", "sabareesh"),
    (r"\b(?:sabareesh\s+mail\s+id|sabareesh\s+email|sabareesh\s+account)\b", "sabareesh profile"),
    # Shortcut chords
    (r"\b(?:control|cntrl)\b", "ctrl"),
    (r"\b(?:ctrl\s+k\s+(?:and\s+)?(?:ctrl\s+)?o)\b", "ctrl+k ctrl+o"),
    # IDEs & Tools
    (r"\b(?:v\s+s\s+code|we\s+s\s+code|v\.s\.\s*code|visual\s+studio\s+code)\b", "vscode"),
    (r"\b(?:pi\s*charm|pie\s*charm)\b", "pycharm"),
    (r"\b(?:sub\s*lime)\b", "sublime"),
    (r"\b(?:notepad\s+plus\s+plus|notepad\s*\+\+)\b", "notepadplusplus"),
    # Languages
    (r"\b(?:c\s*plus\s*plus|c\s*\+\+)\b", "cpp"),
    (r"\b(?:c\s*sharp|c\s*#)\b", "csharp"),
    (r"\b(?:java\s*script)\b", "javascript"),
    (r"\b(?:type\s*script)\b", "typescript"),
    (r"\b(?:go\s*lang)\b", "go"),
    (r"\b(?:dot\s*net)\b", "dotnet"),
    # Common algorithmic phrases often misheard
    (r"\b(?:to\s+sum|too\s+sum|two\s+some|to\s+some)\b", "two sum"),
    (r"\b(?:merge\s+short)\b", "merge sort"),
    (r"\b(?:quick\s+short)\b", "quick sort"),
    (r"\b(?:binary\s+short)\b", "binary search"),
    # Polite filler words
    (r"^\s*(?:could\s+you\s+(?:please\s+)?|can\s+you\s+(?:please\s+)?|please\s+|friday\s+please\s+|zyra\s+please\s+)", ""),
]

def normalize_voice_transcript(raw_text: str) -> str:
    """Normalizes noisy transcripts, misheard technical terms, and filler words."""
    cleaned = raw_text.strip()
    for pattern, replacement in SPEECH_REPLACEMENTS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

class VoiceManager:
    def __init__(self, on_command_callback: Callable[[str], str], on_say_callback: Optional[Callable[[str], None]] = None):
        self.on_command = on_command_callback
        self.on_say = on_say_callback
        self.running = False
        self.tts_lock = threading.Lock()
        self.speaker = None
        self._init_tts()

    def _init_tts(self):
        try:
            import pyttsx3
            self.speaker = pyttsx3.init()
            rate = config.get("tts_rate", 175)
            volume = config.get("tts_volume", 1.0)
            self.speaker.setProperty("rate", rate)
            self.speaker.setProperty("volume", volume)
        except Exception:
            self.speaker = None

    def speak(self, text: str):
        tts_engine.speak(text)

    def stop_speaking(self):
        tts_engine.stop()

    def start_listening(self, notify_fn: Callable[[str], None]):
        self.running = True
        threading.Thread(target=self._listener_loop, args=(notify_fn,), daemon=True).start()

    def stop_listening(self):
        self.running = False
        self.stop_speaking()

    def list_microphones(self) -> List[str]:
        """Returns list of all audio input devices detected on the system."""
        try:
            import speech_recognition as sr
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []

    def set_microphone(self, index: int) -> str:
        """Sets the active microphone device index in config."""
        mics = self.list_microphones()
        if 0 <= index < len(mics):
            config.set("microphone_index", index)
            return f"Microphone set to [{index}]: {mics[index]}."
        return f"Invalid microphone index: {index}. Available indices: 0 to {len(mics)-1}."

    def _listener_loop(self, notify_fn: Callable[[str], None]):
        try:
            import speech_recognition as sr
        except ImportError:
            notify_fn("Voice packages (SpeechRecognition / PyAudio) are missing. Running in text-only mode.")
            return

        recognizer = sr.Recognizer()
        # Enhanced audio sensitivity and threshold parameters
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 300
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.25
        recognizer.non_speaking_duration = 0.4

        try:
            mic_idx = config.get("microphone_index", None)
            microphone = sr.Microphone(device_index=mic_idx)
        except Exception as exc:
            notify_fn(f"Microphone could not be accessed ({exc}). Running in text-only mode.")
            return

        with microphone as source:
            notify_fn("Hands-free voice listening is active (calibrating microphone)...")
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
            except Exception:
                pass
            asst_name = config.get("assistant_name", "FRIDAY")
            notify_fn(f"Microphone calibrated. Speak naturally (e.g. 'Hey {asst_name}, open VS Code').")

            lang = config.get("stt_language", "en-IN")
            while self.running:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    continue
                except Exception:
                    continue

                try:
                    raw_spoken = recognizer.recognize_google(audio, language=lang)
                    spoken = normalize_voice_transcript(raw_spoken)
                    spoken_lower = spoken.lower().strip()

                    # Immediate cancellation command
                    if spoken_lower in {"stop", "cancel", "shut up", "be quiet", "nevermind", "abort"}:
                        self.stop_speaking()
                        notify_fn("Stopped active speech/action.")
                        continue

                    notify_fn(f"🎤 Heard: \"{spoken}\"")
                    result = self.on_command(spoken)
                    if result:
                        notify_fn(f"{asst_name}: {result}")
                        self.speak(result)

                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    notify_fn("Speech recognition service is unreachable. Text commands are still active.")
                    time.sleep(2)
                    continue
