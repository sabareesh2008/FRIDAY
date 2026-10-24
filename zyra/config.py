"""Configuration management for ZYRA assistant."""
import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path(__file__).resolve().parent.parent / "zyra_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "assistant_name": "FRIDAY",
    "user_name": "Sabareesh",
    "user_title": "sir",
    "chrome_profile": "Sabareesh",
    "voice_gender": "female",
    "wake_words": ["hey friday", "friday", "hey zyra", "zyra"],
    "require_confirmation": True,
    "tts_enabled": True,
    "tts_rate": 175,
    "tts_volume": 1.0,
    "stt_language": "en-IN",
    "browser": "chrome",  # chrome, edge, default
    "llm_provider": "local_rules",  # "local_rules", "ollama", "gemini", "openai"
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.2:3b",
    "api_key": "",
    "gemini_api_key": "",
    "openai_api_key": "",
    "microphone_index": None,
    "browser_bridge_port": 5005,
    "custom_search_paths": [],
    "run_on_startup": False,
    "safe_mode": True,  # Protect system files from accidental deletion
}

class ZyraConfig:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.data: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    self.data.update(user_data)
            except Exception:
                pass
        else:
            self.save()

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

config = ZyraConfig()
