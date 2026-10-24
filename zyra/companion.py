"""Conversational Companion Engine for FRIDAY.

Provides human-like, warm, empathetic dialogue, general Q&A, and intelligent
reasoning. Works both offline (knowledge heuristics) and online (free Gemini Flash).
Always speaks respectfully addressing the user as 'sir'.
"""
import os
import re
import json
import urllib.request
from typing import Optional, Dict, Any
from zyra.config import config

OFFLINE_CHIT_CHAT: Dict[str, str] = {
    "how are you": "I am functioning splendidly, sir. Thank you for asking. How are you feeling today?",
    "who are you": "I am FRIDAY, your personal AI desktop companion and autonomous operator, sir.",
    "what is your name": "My name is FRIDAY, sir.",
    "what can you do": "I can control your desktop, click elements on your screen, automate downloads, manage files, open apps and websites, and chat with you anytime, sir.",
    "thank you": "You are most welcome, sir. It is always my pleasure to assist you.",
    "thanks": "Anytime, sir. Happy to help.",
    "i am fine": "I am glad to hear that, sir! What are we working on today?",
    "i'm good": "Delighted to hear that, sir! Let me know what you'd like to do.",
    "i am tired": "Please make sure to take a short break and rest your eyes, sir. Your health comes first.",
    "tell me a joke": "Why do programmers prefer dark mode, sir? Because light attracts bugs!",
    "i love you": "That is very kind of you, sir! I am honored to be your loyal assistant.",
    "are you real": "I am as real as the code running in your system, sir — and always here at your side.",
}

class CompanionEngine:
    def __init__(self):
        self.history = []

    def respond(self, user_query: str) -> str:
        """Answers any user question or conversational remark."""
        user_title = config.get("user_title", "sir")
        clean = user_query.strip()
        lower = clean.lower().rstrip(".?!")

        # 1. Quick exact or fuzzy match in offline chit-chat
        for key, reply in OFFLINE_CHIT_CHAT.items():
            if key in lower:
                return reply

        # 2. Try Gemini API for unlimited human-like open Q&A if key is configured
        api_key = config.get("api_key", "").strip() or config.get("gemini_api_key", "").strip()
        if api_key:
            llm_reply = self._query_gemini(clean, api_key, user_title)
            if llm_reply:
                return llm_reply

        # 3. Intelligent Local Fallback Response
        if lower.startswith(("what is", "who is", "explain", "how does", "tell me about")):
            return (
                f"That is an interesting topic, {user_title}. To let me explain any topic in deep detail, "
                f"you can add a free Google Gemini API key in Settings, and I can answer all your questions!"
            )

        return f"I hear you, {user_title}. I am ready to help you with that or carry out any task on your screen."

    def _query_gemini(self, prompt: str, api_key: str, user_title: str) -> Optional[str]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            system_instruction = (
                f"You are FRIDAY, a warm, witty, highly intelligent, and loyal personal female AI assistant. "
                f"You speak like a helpful human friend. Always address the user respectfully as '{user_title}'. "
                f"Keep answers concise, engaging, and suitable for spoken text without unnecessary markdown asterisks."
            )
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"System: {system_instruction}\n\nUser: {prompt}"}]}
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 250
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            pass
        return None

companion_engine = CompanionEngine()
