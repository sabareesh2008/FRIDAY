"""Unified computer operations interface for ZYRA (backward-compatible adapter)."""
from pathlib import Path
from typing import List, Optional
from zyra.windows_manager import windows_manager
from zyra.browser_manager import browser_manager
from zyra.file_manager import file_manager
from zyra.media_finder import media_finder

class Computer:
    def __init__(self):
        self._media_finder = media_finder

    @property
    def _file_index(self):
        return self._media_finder._file_index

    @property
    def _index_ready(self):
        return self._media_finder._index_ready

    @property
    def _index_lock(self):
        return self._media_finder._index_lock

    @property
    def _index_thread(self):
        return self._media_finder._index_thread

    def start_file_indexing(self):
        self._media_finder.start_indexing()

    def find_media(self, query: str) -> str:
        return self._media_finder.find_and_play(query)

    def chrome_action(self, action: str, value: str = '') -> str:
        act = action.lower().strip()
        if act == "search page":
            return browser_manager.search_page(value)
        if act == "search google":
            return browser_manager.web_search("google", value)
        if act == "open url":
            return browser_manager.open_url(value)
        return browser_manager.tab_action(act)

    def desktop_action(self, action: str) -> str:
        act = action.lower().strip()
        if act == "show desktop":
            return windows_manager.show_desktop()
        if act in ("minimize windows", "minimize window"):
            return windows_manager.minimize_window()
        if act in ("maximize windows", "maximize window"):
            return windows_manager.maximize_window()
        if act == "switch window":
            return windows_manager.switch_window()
        if act == "close window":
            return windows_manager.close_window()
        return "Unrecognized desktop action."

    def open_app(self, app_name: str) -> str:
        # First check dynamic apps
        res = windows_manager.launch_app(app_name)
        if not res.startswith("Could not find an installed application"):
            return res
        # Fallback to media search as in original behavior
        return self.find_media(app_name)

    def open_path(self, raw_path: str) -> str:
        return file_manager.open_file_or_folder(raw_path)

    def open_website(self, address: str) -> str:
        return browser_manager.open_url(address)

    def copy_file(self, source_text: str, destination_text: str) -> str:
        return file_manager.copy_item(source_text, destination_text)
