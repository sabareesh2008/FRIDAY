"""AI Command Understanding, context memory, and intent parsing for ZYRA."""
import os
import re
import difflib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from zyra.config import config
from zyra.safety import safety_guard
from zyra.windows_manager import windows_manager
from zyra.browser_manager import browser_manager
from zyra.file_manager import file_manager
from zyra.media_finder import media_finder
from zyra.startup import startup_manager
from zyra.coding.coordinator import coding_coordinator
from zyra.system_agent import system_agent
from zyra.vision_manager import vision_manager
from zyra.screen_operator import screen_operator
from zyra.companion import companion_engine
from zyra.action_history import action_history
from zyra.remote_tasks import remote_tasks

POPULAR_SITES: Dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "you tube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "google mail": "https://mail.google.com",
    "github": "https://www.github.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://www.x.com",
    "x": "https://www.x.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "chatgpt": "https://chatgpt.com",
    "chat gpt": "https://chatgpt.com",
    "openai": "https://chatgpt.com",
    "amazon": "https://www.amazon.com",
    "wikipedia": "https://www.wikipedia.org",
    "linkedin": "https://www.linkedin.com",
    "twitch": "https://www.twitch.tv",
    "pinterest": "https://www.pinterest.com",
    "prime video": "https://www.primevideo.com",
    "hotstar": "https://www.hotstar.com",
    "disney": "https://www.disneyplus.com",
}

class ContextMemory:
    def __init__(self):
        self.last_app: Optional[str] = None
        self.last_window: Optional[str] = None
        self.last_file: Optional[str] = None
        self.last_folder: Optional[str] = None
        self.last_media: Optional[str] = None
        self.last_action: Optional[str] = None
        self.last_moved_file: Optional[str] = None
        self.last_destination: Optional[str] = None

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k) and v:
                setattr(self, k, v)

class AIEngine:
    def __init__(self):
        self.memory = ContextMemory()

    @staticmethod
    def strip_wake_words(command: str) -> str:
        wake_words = config.get("wake_words", ["hey zyra", "zyra"])
        cleaned = command.strip()
        for w in wake_words:
            # Strip leading wake word (e.g., "Hey Zyra open notepad")
            cleaned = re.sub(rf"^\s*(?:{re.escape(w)})[\s,.:!-]*", "", cleaned, flags=re.IGNORECASE).strip()
            # Strip trailing wake word (e.g., "goodbye zyra", "open notepad zyra")
            cleaned = re.sub(rf"[\s,.:!-]+(?:{re.escape(w)})\s*$", "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned

    def parse_and_execute(self, raw_input: str) -> str:
        cmd = self.strip_wake_words(raw_input).strip().strip(".")
        user_title = config.get("user_title", "sir")
        if not cmd:
            return f"Yes, {user_title}? How can I help you?"

        lower = cmd.lower()
        if lower in {"hello", "hi", "hey", "friday", "hey friday", "are you there"}:
            return f"Yes, {user_title}! FRIDAY is online and at your service."

        # 1. Safety Guard Confirmations
        if safety_guard.has_pending:
            if lower in {"yes", "confirm", "proceed", "yep", "sure", "ok", "do it", "y"}:
                return safety_guard.confirm()
            if lower in {"no", "cancel", "abort", "stop", "nevermind", "n", "don't"}:
                return safety_guard.cancel()
            return f"Action pending confirmation. {safety_guard.get_pending_description()}. Reply 'yes' to proceed, or 'no' to cancel."

        # 2. General / Help / Exit
        if lower in {"exit", "quit", "goodbye", "bye", "stop zyra", "close zyra"}:
            return "QUIT_SIGNAL"

        # Undo last action
        if lower in {"undo", "undo that", "undo last action", "undo the last action", "undo if possible", "revert", "revert last action"}:
            return action_history.undo_last()

        # Follow-up: "open that folder again" / "open this folder"
        if lower in {"open that folder again", "open that folder", "open the folder again", "open folder again", "open this folder", "open the folder"}:
            target_f = self.memory.last_folder or "C:\\Sabareesh"
            return file_manager.open_file_or_folder(target_f)

        # Open specific folder: "open folder <name>"
        open_folder_match = re.match(r"^open\s+(?:the\s+)?folder\s+(.+)$", cmd, re.IGNORECASE)
        if open_folder_match:
            fname = open_folder_match.group(1).strip()
            if fname.lower() in ("this", "this folder", "that", "that folder", "current folder"):
                target_f = self.memory.last_folder or "C:\\Sabareesh"
                return file_manager.open_file_or_folder(target_f)
            if fname.lower() == "sabareesh":
                self.memory.update(last_folder="C:\\Sabareesh")
                return file_manager.open_file_or_folder("C:\\Sabareesh")
            if fname.lower() in ("downloads", "my downloads"):
                p = str(Path.home() / "Downloads")
                self.memory.update(last_folder=p)
                return file_manager.open_file_or_folder(p)
            if fname.lower() in ("desktop", "my desktop"):
                p = str(Path.home() / "Desktop")
                self.memory.update(last_folder=p)
                return file_manager.open_file_or_folder(p)
            if fname.lower() in ("documents", "my documents"):
                p = str(Path.home() / "Documents")
                self.memory.update(last_folder=p)
                return file_manager.open_file_or_folder(p)
            for root_dir in [Path("C:/Sabareesh"), Path.home() / "Desktop", Path.home() / "Documents", Path.home() / "Downloads"]:
                cand = root_dir / fname
                if cand.exists() and cand.is_dir():
                    self.memory.update(last_folder=str(cand))
                    return file_manager.open_file_or_folder(str(cand))
            return file_manager.open_file_or_folder(fname)

        # Open in VS Code (folder or suggested folder)
        open_vscode_match = re.match(r"^(?:open|launch)\s+(?:the\s+)?(?:folder\s+)?(.+?)\s+in\s+(?:vs\s*code|visual\s+studio\s+code|code)$", cmd, re.IGNORECASE)
        if open_vscode_match or lower in {"open suggested folder in vs code", "open in vs code", "open folder in vs code"}:
            folder_target = open_vscode_match.group(1).strip() if open_vscode_match else (self.memory.last_folder or "C:\\Sabareesh")
            if folder_target.lower() in ("suggested folder", "suggested", "this folder", "current folder"):
                folder_target = self.memory.last_folder or "C:\\Sabareesh"
            if folder_target.lower() == "sabareesh":
                folder_target = "C:\\Sabareesh"
            import shutil, subprocess
            code_bin = shutil.which("code")
            if code_bin:
                subprocess.Popen([code_bin, folder_target], shell=True)
                return f"Opened folder '{folder_target}' in VS Code, {user_title}."
            windows_manager.focus_window("Visual Studio Code")
            time.sleep(0.3)
            screen_operator.press_key("ctrl+k ctrl+o")
            return f"Triggered Open Folder in VS Code for '{folder_target}', {user_title}."

        # Follow-up: "actually, move it to <dest> instead"
        actually_move_match = re.match(r"^(?:actually,?\s+)?move\s+(?:it|that|the\s+file)\s+to\s+(.+?)(?:\s+instead)?$", cmd, re.IGNORECASE)
        if actually_move_match:
            dest_folder = actually_move_match.group(1).strip()
            target_file = self.memory.last_moved_file or self.memory.last_file
            if target_file and os.path.exists(target_file):
                res = file_manager.move_item(target_file, dest_folder)
                self.memory.update(last_file=target_file, last_destination=dest_folder)
                return res
            last_file_action = action_history.get_last_file_action()
            if last_file_action and "destination" in last_file_action.details:
                src_dest = last_file_action.details["destination"]
                if os.path.exists(src_dest):
                    res = file_manager.move_item(src_dest, dest_folder)
                    return f"Adjusted destination: {res}"
            return f"I am not sure which file you'd like to move, {user_title}. Please specify the filename."

        # Advanced Browser Specific Tab: "close the X tab but leave Y open"
        close_tab_but_match = re.match(
            r"^close\s+(?:the\s+)?(.+?)(?:\s+tab)?\s+but\s+(?:leave|keep)\s+(?:my\s+)?(.+?)(?:\s+tab)?\s+open$",
            cmd,
            re.IGNORECASE
        )
        if close_tab_but_match:
            to_close = close_tab_but_match.group(1).strip()
            to_keep = close_tab_but_match.group(2).strip()
            return browser_manager.close_specific_tab(to_close, keep_target=to_keep)

        # Tab listing
        if lower in {"list tabs", "list open tabs", "show tabs", "show open tabs", "what tabs are open", "get open tabs"}:
            return browser_manager.get_open_tabs_report()

        # Switch to tab
        switch_tab_match = re.match(r"^(?:switch\s+to\s+tab|go\s+to\s+tab)\s+(.+)$", cmd, re.IGNORECASE)
        if switch_tab_match:
            return browser_manager.switch_to_tab(switch_tab_match.group(1).strip())

        # Search browser history
        hist_match = re.match(r"^(?:search\s+browser\s+history\s+for|search\s+history\s+for)\s+(.+)$", cmd, re.IGNORECASE)
        if hist_match:
            return browser_manager.search_browser_history(hist_match.group(1).strip())

        # Virtual Desktops
        if lower in {"create virtual desktop", "new virtual desktop", "add virtual desktop"}:
            return windows_manager.create_virtual_desktop()
        if lower in {"close virtual desktop", "remove virtual desktop"}:
            return windows_manager.close_virtual_desktop()
        if lower in {"next desktop", "next virtual desktop", "switch to next desktop"}:
            return windows_manager.switch_virtual_desktop("next")
        if lower in {"previous desktop", "prev desktop", "previous virtual desktop", "switch to previous desktop"}:
            return windows_manager.switch_virtual_desktop("previous")
        if lower in {"list virtual desktops", "virtual desktops", "show virtual desktops"}:
            return windows_manager.list_virtual_desktops()

        # Remote Tasks & Wake-on-LAN
        queue_match = re.match(r"^(?:queue\s+task|enqueue\s+task|run\s+when\s+laptop\s+is\s+awake)\s+(.+)$", cmd, re.IGNORECASE)
        if queue_match:
            return remote_tasks.queue_task(queue_match.group(1))

        if lower in {"list queued tasks", "show queued tasks", "queued tasks"}:
            q = remote_tasks.list_queued_tasks()
            if not q:
                return f"No queued tasks pending, {user_title}."
            return f"Found {len(q)} queued task(s):\n" + "\n".join(f"• {t['id']}: {t['command']} ({t['status']})" for t in q)

        wol_match = re.match(r"^(?:wake\s+on\s+lan|send\s+wol\s+to|wol)\s+([a-fA-F0-9:-]+)$", cmd, re.IGNORECASE)
        if wol_match:
            return remote_tasks.send_wake_on_lan(wol_match.group(1))

        # Microphone Management
        if lower in {"list microphones", "show microphones", "microphones"}:
            from zyra.voice_manager import VoiceManager
            dummy = VoiceManager(lambda c: "")
            mics = dummy.list_microphones()
            if not mics:
                return "No audio input devices detected or speech packages not installed."
            lines = [f"Detected {len(mics)} microphone(s):"]
            for i, m in enumerate(mics):
                lines.append(f"[{i}] {m}")
            return "\n".join(lines)

        set_mic_match = re.match(r"^(?:set\s+microphone|change\s+microphone\s+to)\s+(\d+)$", cmd, re.IGNORECASE)
        if set_mic_match:
            from zyra.voice_manager import VoiceManager
            dummy = VoiceManager(lambda c: "")
            return dummy.set_microphone(int(set_mic_match.group(1)))

        # Preview Organize
        if lower in {"preview organize", "preview organize downloads"}:
            return file_manager.preview_organize("downloads")

        if lower in {"help", "what can you do", "commands", "menu"}:
            return (
                "Here is what I can do:\n"
                "• Apps: 'open Notepad', 'launch Discord', 'open VS Code'\n"
                "• Windows: 'switch window', 'maximize/minimize window', 'close window', 'show desktop'\n"
                "• Media: 'play Interstellar', 'watch Avatar', 'open movie Inception'\n"
                "• Browser: 'new tab', 'close tab', 'reopen tab', 'next tab', 'search Google for Python'\n"
                "• Web: 'open youtube.com', 'open Gmail', 'search this page for keyword'\n"
                "• Files: 'find file resume', 'organize downloads', 'delete file test.txt', 'create folder Work'\n"
                "• System: 'mute volume', 'increase volume', 'lock PC', 'sleep PC', 'restart PC'\n"
                "• Coding: 'create Java file TwoSum and open in VS Code', 'open online compiler for Python'\n"
                "• Multi-step: 'open Notepad and open Calculator and show desktop'\n"
                "• Startup: 'enable startup', 'disable startup'"
            )

        # Coding and Software Development Tasks
        if coding_coordinator.is_coding_intent(cmd):
            return coding_coordinator.execute_coding_task(cmd)

        # Autonomous Hardware & System Queries
        if system_agent.is_system_query(cmd):
            return system_agent.execute_query(cmd)

        # Screen Vision & Visual Analysis
        if any(w in lower for w in ("look at my screen", "what is on my screen", "error on my screen", "debug my screen", "help with my screen", "analyze my screen", "take a screenshot")):
            ans, _ = vision_manager.analyze_screen(cmd)
            return ans

        # 3. Startup Configuration
        if lower in {"enable startup", "turn on startup", "run on boot", "start with windows"}:
            return startup_manager.enable_startup()
        if lower in {"disable startup", "turn off startup", "remove from startup"}:
            return startup_manager.disable_startup()

        # 4. Volume Control
        if any(lower.startswith(v) for v in ("volume ", "mute", "unmute", "louder", "quieter")):
            return windows_manager.volume_control(lower)

        # 5. Windows Management / Desktop Controls
        if lower in {"show desktop", "go to desktop", "minimize all", "minimize all windows"}:
            return windows_manager.show_desktop()
        if lower in {"switch window", "next window", "switch app"}:
            return windows_manager.switch_window()
        if lower in {"lock pc", "lock computer", "lock screen", "lock workstation"}:
            return windows_manager.lock_workstation()
        if lower in {"sleep", "sleep pc", "put computer to sleep", "suspend pc"}:
            return windows_manager.sleep_pc()
        if lower in {"restart", "restart pc", "restart computer", "reboot pc"}:
            return windows_manager.restart_pc()
        if lower in {"shutdown", "shut down", "shutdown pc", "power off computer", "turn off pc"}:
            return windows_manager.shutdown_pc()

        # Window state on active or specific window
        match = re.match(r"^(?:maximize|max)\s+(?:window\s+)?(.+)?$", cmd, re.IGNORECASE)
        if match:
            target = match.group(1) or ""
            target = self.resolve_pronouns(target)
            return windows_manager.maximize_window(target)

        match = re.match(r"^(?:minimize|min)\s+(?:window\s+)?(.+)?$", cmd, re.IGNORECASE)
        if match:
            target = match.group(1) or ""
            target = self.resolve_pronouns(target)
            return windows_manager.minimize_window(target)

        match = re.match(r"^(?:close)\s+(?:the\s+)?(?:window\s+)?(.+)?$", cmd, re.IGNORECASE)
        if match:
            target = match.group(1) or ""
            if target.lower() in {"it", "this", "window", "active window", "the window", ""}:
                return windows_manager.close_window("")
            if target.lower() in {"tab", "this tab", "current tab", "chrome tab"}:
                return browser_manager.tab_action("close tab")
            if target.lower() in {"chrome", "browser"}:
                return browser_manager.tab_action("close browser")
            return windows_manager.close_window(target)

        # Focus window
        match = re.match(r"^(?:switch to|focus|bring up)\s+(?:window\s+)?(.+)$", cmd, re.IGNORECASE)
        if match:
            target = self.resolve_pronouns(match.group(1).strip())
            return windows_manager.focus_window(target)

        # 6. Browser & Tabs
        tab_commands = {
            "new tab": "new tab", "open new tab": "new tab", "create new tab": "new tab",
            "close tab": "close tab", "close this tab": "close tab", "close current tab": "close tab",
            "reopen tab": "reopen tab", "restore tab": "reopen tab", "restore closed tab": "reopen tab",
            "next tab": "next tab", "switch to next tab": "next tab",
            "previous tab": "previous tab", "last tab": "previous tab",
            "refresh page": "refresh", "reload page": "refresh", "refresh": "refresh",
            "history": "history", "downloads": "downloads", "bookmarks": "bookmarks",
            "zoom in": "zoom in", "zoom out": "zoom out", "reset zoom": "zoom reset"
        }
        if lower in tab_commands:
            return browser_manager.tab_action(tab_commands[lower])

        # Browser in-page search
        match = re.match(r"^(?:search|find)\s+(?:this page|on this page|page)\s+(?:for\s+)?(.+)$", cmd, re.IGNORECASE)
        if match:
            return browser_manager.search_page(match.group(1))

        # Web Searches
        match = re.match(r"^(?:search google for|google)\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return browser_manager.web_search("google", match.group(1))
        match = re.match(r"^(?:search youtube for|youtube)\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return browser_manager.web_search("youtube", match.group(1))
        match = re.match(r"^(?:search github for|github)\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return browser_manager.web_search("github", match.group(1))
        match = re.match(r"^(?:search wikipedia for|wikipedia)\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return browser_manager.web_search("wikipedia", match.group(1))
        match = re.match(r"^(?:search the web for)\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return browser_manager.web_search("google", match.group(1))

        # Gmail
        match = re.match(r"^(?:open|go to|visit)\s+(?:gmail|my mail|email)\s+(?:for|with)\s+([^\s]+@[^\s]+)$", cmd, re.IGNORECASE)
        if match:
            return browser_manager.open_gmail(match.group(1))
        if lower in {"open gmail", "go to gmail", "my email", "open email", "check mail"}:
            return browser_manager.open_gmail()

        # 7. File Operations
        # Organize
        match = re.match(r"^(?:organize|sort|clean up)\s+(?:my\s+)?(.+)?$", cmd, re.IGNORECASE)
        if match:
            folder_target = match.group(1) or "downloads"
            return file_manager.organize_directory(folder_target)

        # Delete File/Folder
        match = re.match(r"^(?:delete|remove)\s+(?:file|folder|path)?\s*(.+)$", cmd, re.IGNORECASE)
        if match:
            target = self.resolve_pronouns(match.group(1).strip())
            return file_manager.delete_item(target)

        # Create File/Folder
        match = re.match(r"^(?:create|make)\s+(?:a\s+)?folder\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return file_manager.create_folder(match.group(1).strip())

        match = re.match(r"^(?:create|make)\s+(?:a\s+)?file\s+(.+?)(?:\s+with content\s+(.+))?$", cmd, re.IGNORECASE)
        if match:
            path_part = match.group(1).strip()
            content_part = match.group(2) or ""
            return file_manager.create_file(path_part, content_part)

        # Rename File
        match = re.match(r"^rename\s+(.+?)\s+to\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return file_manager.rename_item(match.group(1), match.group(2))

        # Move File
        match = re.match(r"^move\s+(.+?)\s+to\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            src = self.resolve_pronouns(match.group(1).strip())
            dst = match.group(2).strip()
            res = file_manager.move_item(src, dst)
            self.memory.update(last_file=src, last_moved_file=src, last_destination=dst)
            return res

        # Copy File
        match = re.match(r"^copy\s+(.+?)\s+to\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return file_manager.copy_item(match.group(1), match.group(2))

        # Find File
        match = re.match(r"^(?:find file|search file|locate file)\s+(.+)$", cmd, re.IGNORECASE)
        if match:
            return file_manager.find_files(match.group(1))

        # 8. Media / Movie Playback (Preserved full backward compatibility)
        media_match = re.match(r"^(?:play|watch|stream|open movie)\s+(?:the\s+)?(.+?)\s*$", cmd, re.IGNORECASE)
        if media_match:
            movie_title = media_match.group(1).strip()
            self.memory.update(last_media=movie_title)
            return media_finder.find_and_play(movie_title)

        # 9. Open / Launch Generic
        match = re.match(r"^(?:open|launch|start|run|go to)\s+(?:the\s+)?(.+?)(?:\s+in a new tab)?$", cmd, re.IGNORECASE)
        if match:
            target = match.group(1).strip()
            target_lower = target.lower().rstrip("./")

            # 0. Google Chrome Explicit Launch under Sabareesh Profile
            if target_lower in ("chrome", "google chrome", "chrome browser", "my chrome", "chrome as sabareesh"):
                self.memory.update(last_app="Chrome")
                return browser_manager.launch_chrome(profile="Sabareesh")

            # 1. Popular websites / web applications (e.g. "open youtube", "open you tube", "open instagram")
            if target_lower in POPULAR_SITES:
                return browser_manager.open_url(POPULAR_SITES[target_lower])

            # 2. URL or Website domain
            if target_lower.startswith(("http://", "https://", "www.")) or ("." in target and " " not in target and not target.endswith(".exe")):
                return browser_manager.open_url(target)

            # 3. Direct file/directory path
            if re.match(r"^[a-zA-Z]:[\\/]", target) or target.startswith(("%userprofile%", "~\\", "\\")):
                resolved_p = file_manager._resolve_path(target)
                if resolved_p.is_dir():
                    self.memory.update(last_folder=str(resolved_p), last_file=str(resolved_p))
                else:
                    self.memory.update(last_file=str(resolved_p), last_folder=str(resolved_p.parent))
                return file_manager.open_file_or_folder(target)

            # 4. Try Launching Application (Camera, Photos, Notepad, VS Code, Calculator, etc.)
            app_result = windows_manager.launch_app(target)
            if not app_result.startswith("Could not find an installed application"):
                self.memory.update(last_app=target)
                return app_result

            # 5. Media check ONLY if explicit media intent/words are present
            is_media_explicit = any(w in cmd.lower() for w in ("movie", "film", "video", "song", "episode", "season", "series", "audio", "track", "mp4", "mkv", "mp3"))
            if is_media_explicit:
                clean_target = re.sub(r"\b(movie|film|video|song|episode|series)\b", "", target, flags=re.IGNORECASE).strip()
                media_result = media_finder.find_and_play(clean_target or target)
                if not media_result.startswith("I could not find a movie") and not media_result.startswith("I am scanning"):
                    self.memory.update(last_media=clean_target or target)
                    return media_result
                return media_result

            return f"I couldn't find an application or file named '{target}', {user_title}. Type 'help' for examples."

        # 10. Autonomous Screen Operator Actions
        # Click / Double Click / Right Click
        double_click_match = re.match(r"^(?:double\s+click|double-click)(?:\s+(?:on|the)?\s+(.+))?$", cmd, re.IGNORECASE)
        if double_click_match:
            return screen_operator.double_click(double_click_match.group(1))

        right_click_match = re.match(r"^(?:right\s+click|right-click)(?:\s+(?:on|the)?\s+(.+))?$", cmd, re.IGNORECASE)
        if right_click_match:
            return screen_operator.right_click(right_click_match.group(1))

        click_match = re.match(r"^(?:click|click\s+on|tap|tap\s+on|select)\s+(?:the\s+)?(.+)$", cmd, re.IGNORECASE)
        if click_match:
            target = click_match.group(1).strip()
            # If user asks to select / click Sabareesh mail / profile
            if target.lower() in ("sabareesh", "sabareesh profile", "sabareesh mail id", "sabareesh mail", "sabareesh email"):
                pt = screen_operator._find_element_via_uia("Sabareesh")
                if pt:
                    return screen_operator.click("Sabareesh")
                return browser_manager.launch_chrome(profile="Sabareesh")
            return screen_operator.click(target)

        # Type text & press enter
        type_match = re.match(r"^(?:type|write|input)\s+(.+?)(?:\s+and\s+(?:press\s+)?enter)?$", cmd, re.IGNORECASE)
        if type_match:
            text_to_type = type_match.group(1).strip()
            has_enter = bool(re.search(r"\band\s+(?:press\s+)?enter\b", cmd, re.IGNORECASE))
            return screen_operator.type_text(text_to_type, press_enter=has_enter)

        # Press Key / Keystroke
        press_match = re.match(r"^(?:press|hit|send\s+key)\s+(?:key\s+)?(.+)$", cmd, re.IGNORECASE)
        if press_match:
            key_name = press_match.group(1).strip()
            return screen_operator.press_key(key_name)

        # Scroll Page / Window
        scroll_match = re.match(r"^(?:scroll\s+(down|up)|scroll)$", cmd, re.IGNORECASE)
        if scroll_match:
            direction = scroll_match.group(1) or "down"
            return screen_operator.scroll(direction)

        # Download Automation
        if lower in {"download", "download this", "download file", "download the file", "click download", "start download", "auto download", "automatic download", "automatic downloads"}:
            return screen_operator.trigger_download()

        # In-Browser / Screen Search & Enter
        search_this_match = re.match(r"^(?:search\s+this|search)\s+(.+?)(?:\s+and\s+(?:press\s+)?enter)?$", cmd, re.IGNORECASE)
        if search_this_match:
            search_query = search_this_match.group(1).strip()
            return screen_operator.search_and_enter(search_query)

        # Open Link / Link Access
        open_link_match = re.match(r"^(?:open\s+(?:the\s+|this\s+)?link|click\s+(?:the\s+|this\s+)?link)\s*(.*)$", cmd, re.IGNORECASE)
        if open_link_match:
            link_target = open_link_match.group(1).strip() or "link"
            return screen_operator.open_link_or_item(link_target)

        # 11. Autonomous Visual Element Fallback or Conversational Companion
        # Check if user mentioned an element currently on screen (e.g. "sabareesh mail id")
        try:
            uia_point = screen_operator._find_element_via_uia(cmd)
            if uia_point:
                return screen_operator.click(cmd)
        except Exception:
            pass

        # Conversational Companion Engine
        return companion_engine.respond(cmd)

    def resolve_pronouns(self, text: str) -> str:
        t = text.strip()
        lower = t.lower()
        if lower in {"it", "that", "this"}:
            if self.memory.last_window:
                return self.memory.last_window
            if self.memory.last_app:
                return self.memory.last_app
            if self.memory.last_file:
                return self.memory.last_file
        if lower in {"the file", "that file"}:
            if self.memory.last_file:
                return self.memory.last_file
        if lower in {"that folder", "the folder", "that directory"}:
            if self.memory.last_folder:
                return self.memory.last_folder
        return t

ai_engine = AIEngine()
