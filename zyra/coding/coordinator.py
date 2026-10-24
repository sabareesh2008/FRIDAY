"""Polyglot coding coordinator with smart folder discovery, context memory for 'this folder', and auto-naming."""
import os
import re
from pathlib import Path
from typing import Optional, Tuple
from zyra.coding.languages import detect_language, normalize_filename, LanguageSpec, LANGUAGES
from zyra.coding.coder_engine import coder_engine
from zyra.coding.ide_manager import ide_manager
from zyra.coding.online_compiler import online_compiler
from zyra.coding.runner import code_runner

class CodingCoordinator:
    _last_used_folder: Optional[Path] = None

    @staticmethod
    def is_coding_intent(command: str) -> bool:
        lower = command.lower()
        keywords = (
            "online compiler", "compiler for", "code for", "write code", "solve problem",
            "create java", "create python", "create cpp", "create c++", "create file", "new file",
            "write a program", "write a python", "write a java", "write a c++",
            "open vscode", "open vs code", "open in vscode", "run code", "compile and run",
            "open this folder", "on this folder", "in this folder", "open folder",
            "two sum", "binary search", "merge sort", "quick sort", "fibonacci", "factorial",
            "snake game", "flappy bird", "tic tac toe", "lru cache", "linked list",
            "calculator app", "todo app", "express server", "spring boot", "rest api"
        )
        return any(k in lower for k in keywords)

    def execute_coding_task(self, command: str) -> str:
        lower = command.lower()

        # 1. Online Compiler Request
        if "online compiler" in lower or "compiler for" in lower or "playground" in lower:
            lang = detect_language(command) or LANGUAGES["python"]
            code = coder_engine.generate_code(command, lang)
            return online_compiler.open_compiler(command, code_to_copy=code)

        # 2. Extract Language (Default to Java if mentions Java, or Python if unspecified)
        lang = detect_language(command) or LANGUAGES["python"]

        # 3. Resolve Target Folder (handles "this folder", named folders, or full paths)
        target_dir, filename = self.resolve_file_location(command, lang)
        target_dir.mkdir(parents=True, exist_ok=True)
        self._last_used_folder = target_dir
        file_path = target_dir / filename
        stem = file_path.stem

        # 4. Generate Code
        code = coder_engine.generate_code(command, lang, class_name=stem)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as exc:
            return f"Failed to write file {file_path}: {exc}"

        # 5. Check if execution was requested
        run_requested = any(w in lower for w in ("run it", "execute it", "compile and run", "test it", "launch it"))
        run_summary = ""
        if run_requested:
            res = code_runner.execute_file(str(file_path))
            if res.get("success"):
                run_summary = f"\n\n[Execution Output ({res.get('duration')}):\n{res.get('output')}]"
            else:
                run_summary = f"\n\n[Execution {res.get('phase', 'error').capitalize()} Error:\n{res.get('error')}]"

        # 6. Check if IDE opening was requested
        ide_requested = self._detect_target_ide(command)
        if ide_requested or any(w in lower for w in ("open", "vscode", "ide", "editor")):
            ide_name = ide_requested or "vscode"
            ide_msg = ide_manager.open_workspace(ide_name, file_path=str(file_path), folder_path=str(target_dir))
            return f"Opened folder '{target_dir.name}' in VS Code and created {lang.name} file '{filename}'.\n{ide_msg}{run_summary}"

        return f"Created {lang.name} file at {file_path}.{run_summary}"

    @classmethod
    def resolve_file_location(cls, command: str, lang: LanguageSpec) -> Tuple[Path, str]:
        """Smart folder resolver supporting 'this folder', folder names, or custom locations."""
        lower = command.lower()

        # Case A: Full absolute path with extension (e.g. C:\MyProjects\Main.java)
        match_full = re.search(r"([a-zA-Z]:[\\/][^,\"\';\n]+\.[a-zA-Z0-9]+)", command)
        if match_full:
            full_p = Path(match_full.group(1).strip())
            return full_p.parent, full_p.name

        # Case B: Absolute folder path (quoted or unquoted, stopping before conjunctions)
        match_quoted = re.search(r'["\']([a-zA-Z]:[\\/][^"\']+)["\']', command)
        match_abs = re.search(
            r'([a-zA-Z]:[\\/][^\s,\"\';\n]+(?:[ \t]+(?!(?:and|create|open|with|to|in)\b)[^\s,\"\';\n]+)*)',
            command
        )
        target_dir = None
        if match_quoted:
            target_dir = Path(match_quoted.group(1).strip().rstrip("\\/")).resolve()
        elif match_abs:
            target_dir = Path(match_abs.group(1).strip().rstrip("\\/")).resolve()
        elif any(phrase in lower for phrase in ("this folder", "current folder", "the folder", "same folder", "here")):
            # Case C: Context memory for "this folder"
            if cls._last_used_folder and cls._last_used_folder.exists():
                target_dir = cls._last_used_folder
            else:
                # Default to Desktop / MyProject if no previous folder active
                target_dir = Path.home() / "Desktop" / "MyProject"
        else:
            # Case D: Named folder without path (e.g. "open DSA folder" or "folder called LeetCode" or "in folder WebApp")
            named_match = re.search(
                r"(?:open|in|into|inside)\s+(?:the\s+|this\s+)?(?:folder\s+(?:called\s+|named\s+)?([a-zA-Z0-9_-]+)|([a-zA-Z0-9_-]+)\s+folder)",
                command,
                re.IGNORECASE
            )
            if named_match:
                folder_name = (named_match.group(1) or named_match.group(2)).strip()
                # Skip words like "vscode", "code", "this"
                if folder_name.lower() not in {"vscode", "code", "this", "new", "a"}:
                    target_dir = cls._find_or_create_named_folder(folder_name)

            if not target_dir:
                # Check standard locations
                home = Path.home()
                if "desktop" in lower:
                    target_dir = home / "Desktop"
                elif "download" in lower:
                    target_dir = home / "Downloads"
                elif "document" in lower:
                    target_dir = home / "Documents"
                elif "project" in lower:
                    target_dir = home / "Desktop" / "Projects"
                else:
                    target_dir = cls._last_used_folder or (home / "Desktop" / "MyProject")

        filename = cls._extract_filename(command, lang)
        return target_dir, filename

    @classmethod
    def _find_or_create_named_folder(cls, folder_name: str) -> Path:
        """Finds an existing folder across user paths or creates it conveniently on Desktop/Projects."""
        home = Path.home()
        candidates = [
            home / "Desktop",
            home / "Documents",
            home / "Downloads",
            Path.cwd(),
            home,
        ]
        # 1. Search if it already exists
        for base in candidates:
            try:
                if base.exists():
                    p = base / folder_name
                    if p.exists() and p.is_dir():
                        return p.resolve()
                    try:
                        for sub in base.iterdir():
                            if sub.is_dir() and sub.name.lower() == folder_name.lower():
                                return sub.resolve()
                    except Exception:
                        pass
            except (PermissionError, OSError):
                continue

        # 2. If it does not exist, create it on Desktop or local workspace
        try:
            new_dir = home / "Desktop" / folder_name
            new_dir.mkdir(parents=True, exist_ok=True)
            return new_dir.resolve()
        except Exception:
            new_dir = Path.cwd() / "zyra_workspace" / folder_name
            new_dir.mkdir(parents=True, exist_ok=True)
            return new_dir.resolve()

    @staticmethod
    def _extract_filename(command: str, lang: LanguageSpec) -> str:
        # Match pattern like `filename.ext`
        match = re.search(r"\b([a-zA-Z0-9_]+\.[a-zA-Z0-9]+)\b", command)
        if match:
            return normalize_filename(match.group(1), lang)

        # Match pattern like `create java file TwoSum` or `file called Main`
        match2 = re.search(r"(?:file|named|called)\s+([a-zA-Z0-9_]+)", command, re.IGNORECASE)
        if match2:
            candidate = match2.group(1).strip()
            if candidate.lower() not in {"new", "this", "code", "program", "in", "at", "for", "with", "on"}:
                return normalize_filename(candidate, lang)

        # Infer filename intelligently from problem statement if user says "create new file" or "create a file"
        lower = command.lower()
        if "two sum" in lower or "2 sum" in lower:
            return normalize_filename("TwoSum", lang)
        if "binary search" in lower:
            return normalize_filename("BinarySearch", lang)
        if "merge sort" in lower:
            return normalize_filename("MergeSort", lang)
        if "quick sort" in lower:
            return normalize_filename("QuickSort", lang)
        if "snake" in lower:
            return normalize_filename("SnakeGame", lang)
        if "lru" in lower:
            return normalize_filename("LRUCache", lang)
        if "calculator" in lower:
            return normalize_filename("Calculator", lang)
        if "todo" in lower:
            return normalize_filename("TodoApp", lang)

        return lang.default_filename

    @staticmethod
    def _detect_target_ide(command: str) -> Optional[str]:
        lower = command.lower()
        if "vscode" in lower or "vs code" in lower or "code" in lower:
            return "vscode"
        if "pycharm" in lower:
            return "pycharm"
        if "intellij" in lower or "idea" in lower:
            return "intellij"
        if "sublime" in lower:
            return "sublime"
        if "notepad++" in lower or "notepadplusplus" in lower:
            return "notepadplusplus"
        if "notepad" in lower:
            return "notepad"
        if "eclipse" in lower:
            return "eclipse"
        return None

coding_coordinator = CodingCoordinator()
