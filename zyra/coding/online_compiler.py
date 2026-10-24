"""Online compiler and web playground integration for ZYRA."""
import webbrowser
import pyperclip
from typing import Dict, Optional
from zyra.coding.languages import detect_language, LANGUAGES

ONLINE_COMPILERS: Dict[str, str] = {
    "java": "https://onecompiler.com/java",
    "python": "https://onecompiler.com/python",
    "cpp": "https://onecompiler.com/cpp",
    "c": "https://onecompiler.com/c",
    "javascript": "https://onecompiler.com/javascript",
    "typescript": "https://onecompiler.com/typescript",
    "go": "https://go.dev/play/",
    "rust": "https://play.rust-lang.org/",
    "csharp": "https://onecompiler.com/csharp",
    "html": "https://onecompiler.com/html",
    "sql": "https://onecompiler.com/mysql",
    "kotlin": "https://onecompiler.com/kotlin",
    "php": "https://onecompiler.com/php",
    "ruby": "https://onecompiler.com/ruby",
}

class OnlineCompilerManager:
    @staticmethod
    def get_compiler_url(lang_key: str) -> str:
        return ONLINE_COMPILERS.get(lang_key.lower(), "https://onecompiler.com/")

    def open_compiler(self, query: str, code_to_copy: str = "") -> str:
        lang_spec = detect_language(query)
        lang_key = lang_spec.name.lower() if lang_spec else "python"
        url = self.get_compiler_url(lang_key)

        clipboard_note = ""
        if code_to_copy:
            try:
                pyperclip.copy(code_to_copy)
                clipboard_note = " The generated code has been copied to your clipboard (press Ctrl+V to paste)."
            except Exception:
                pass

        try:
            webbrowser.open(url)
            lang_display = lang_spec.name if lang_spec else "Online"
            return f"Opened {lang_display} online compiler ({url}).{clipboard_note}"
        except Exception as exc:
            return f"Failed to open online compiler: {exc}"

online_compiler = OnlineCompilerManager()
