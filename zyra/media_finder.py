"""Preserved and enhanced local movie and media fuzzy search for ZYRA."""
import os
import re
import difflib
import threading
from pathlib import Path
from typing import List, Tuple, Set

VIDEO_EXTENSIONS: Set[str] = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.webm', '.mpeg', '.mpg', '.ts'}
AUDIO_EXTENSIONS: Set[str] = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}

class MediaFinder:
    def __init__(self):
        self._file_index: List[Path] = []
        self._index_ready: bool = False
        self._index_lock = threading.Lock()
        self._index_thread: threading.Thread | None = None

    def start_indexing(self):
        """Index user media folders in the background."""
        if self._index_thread and self._index_thread.is_alive():
            return
        self._index_thread = threading.Thread(target=self._build_index, daemon=True)
        self._index_thread.start()

    def _search_roots(self) -> List[Path]:
        home = Path.home()
        candidates = [
            home / 'Desktop', home / 'Downloads', home / 'Videos', home / 'Movies',
            home / 'Documents', home / 'OneDrive' / 'Desktop', home / 'OneDrive' / 'Documents',
            home / 'OneDrive' / 'Videos', home / 'OneDrive' / 'Downloads'
        ]
        for drive in (Path('D:/'), Path('E:/')):
            if drive.exists():
                candidates.extend([drive / 'Movies', drive / 'Videos', drive / 'Downloads'])
        seen, roots = set(), []
        for p in candidates:
            try:
                resolved = str(p.resolve()).lower()
                if p.is_dir() and resolved not in seen:
                    seen.add(resolved)
                    roots.append(p)
            except OSError:
                pass
        return roots

    def _build_index(self):
        found = []
        skip_dirs = {'$recycle.bin', 'system volume information', 'node_modules', '.git', '__pycache__'}
        for root in self._search_roots():
            for current, dirs, files in os.walk(root, onerror=lambda _e: None):
                dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith('.')]
                for filename in files:
                    p = Path(current) / filename
                    if p.suffix.lower() in VIDEO_EXTENSIONS | AUDIO_EXTENSIONS:
                        found.append(p)
        with self._index_lock:
            self._file_index = found
            self._index_ready = True

    @staticmethod
    def _clean_name(value: str) -> str:
        value = Path(value).stem.lower()
        value = re.sub(r'\b(1080p|720p|2160p|4k|bluray|blu-ray|web-dl|webrip|hdtv|x264|x265|hevc|aac)\b', ' ', value)
        return re.sub(r'[^a-z0-9]+', ' ', value).strip()

    def find_and_play(self, query: str, min_confidence: float = 0.70) -> str:
        """Finds the best matching movie/media file and opens it in default player."""
        query = query.strip().strip('"\'')
        if not query:
            return 'Tell me the movie or media name.'

        direct = Path(os.path.expandvars(os.path.expanduser(query)))
        if direct.exists():
            try:
                os.startfile(str(direct))
                return f"Playing {direct.name}."
            except Exception as exc:
                return f"Could not open media: {exc}"

        if not self._index_ready:
            self.start_indexing()
            if self._index_thread:
                self._index_thread.join(timeout=0.2)

        with self._index_lock:
            files = list(self._file_index)
            ready = self._index_ready

        if not files:
            if not ready:
                return ('I am scanning your Desktop, Downloads, Videos, Movies, and Documents folders. '
                        'Please try that movie name again in a few moments.')
            return 'I could not find any video or audio files in your media directories.'

        q = self._clean_name(query)
        if not q or len(q) < 2:
            return 'Please provide a clearer movie or media title.'

        q_words = set(q.split())
        scored: List[Tuple[float, Path]] = []
        for p in files:
            name = self._clean_name(p.name)
            folder = self._clean_name(p.parent.name)
            if not name:
                continue
            words = set(name.split())
            if q == name:
                score = 1.0
            elif q in name:
                score = 0.93 + min(0.05, len(q) / max(len(name), 1) * 0.05)
            else:
                overlap = len(q_words & words) / max(len(q_words), 1)
                ratio = difflib.SequenceMatcher(None, q, name).ratio()
                partial = max((difflib.SequenceMatcher(None, q, ' '.join(name.split()[i:i+len(q_words)])).ratio()
                               for i in range(max(1, len(words)))), default=0)
                score = max(ratio, partial * 0.92, overlap * 0.86)
                if q in folder:
                    score += 0.04
            if score >= min_confidence:
                scored.append((score, p))

        scored.sort(key=lambda item: (-item[0], len(item[1].name)))
        if not scored:
            return f"I could not find a movie matching “{query}” in your local folders."

        best_score = scored[0][0]
        close = [p for score, p in scored if score >= max(0.53, best_score - 0.08)][:5]
        if len(close) > 1 and scored[0][0] < 0.94:
            options = '\n'.join(f'{i}. {p.name}  —  {p.parent}' for i, p in enumerate(close, 1))
            return 'I found a few possible matches. Specify the title more clearly:\n' + options

        target_file = scored[0][1]
        try:
            os.startfile(str(target_file))
            return f"Opening {target_file.name} in your default player."
        except Exception as exc:
            return f"Failed to play {target_file.name}: {exc}"

media_finder = MediaFinder()
