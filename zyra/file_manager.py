"""Advanced, reliable, and safe file management for ZYRA/FRIDAY."""
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import send2trash
from zyra.safety import safety_guard
from zyra.action_history import action_history

SYSTEM_CRITICAL_DIRS = {
    "c:\\windows",
    "c:\\program files",
    "c:\\program files (x86)",
    "c:\\system volume information",
    "c:\\recovery",
}

FILE_CATEGORIES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".ico"},
    "Documents": {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".csv", ".rtf", ".odt"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
    "Audio": {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"},
    "Executables": {".exe", ".msi", ".bat", ".cmd", ".ps1"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".cs", ".json", ".xml", ".yaml", ".yml", ".sql"},
}

class FileManager:
    @staticmethod
    def _resolve_path(raw_path: str) -> Path:
        clean = raw_path.strip().strip('"\'')
        expanded = os.path.expandvars(os.path.expanduser(clean))
        return Path(expanded).resolve()

    @staticmethod
    def _is_critical_path(path: Path) -> bool:
        norm = str(path).lower()
        return any(norm == crit or norm.startswith(crit + "\\") for crit in SYSTEM_CRITICAL_DIRS)

    def open_file_or_folder(self, raw_path: str) -> str:
        path = self._resolve_path(raw_path)
        if not path.exists():
            return f"I couldn't find path: {path}"
        try:
            os.startfile(str(path))
            return f"Opened {path.name or str(path)}."
        except Exception as exc:
            return f"Failed to open {path}: {exc}"

    def create_file(self, raw_path: str, content: str = "") -> str:
        path = self._resolve_path(raw_path)
        if path.exists():
            return f"File already exists: {path}"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                if content:
                    f.write(content)

            def _undo():
                if path.exists():
                    path.unlink()
                    return f"Removed created file {path.name}."
                return "File was already removed."

            action_history.push("create_file", f"Created file {path.name}", _undo, path=str(path))
            return f"Created file {path.name} at {path.parent}."
        except Exception as exc:
            return f"Failed to create file: {exc}"

    def create_folder(self, raw_path: str) -> str:
        path = self._resolve_path(raw_path)
        if path.exists():
            return f"Folder already exists: {path}"
        try:
            path.mkdir(parents=True, exist_ok=True)

            def _undo():
                if path.exists() and path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
                    return f"Removed empty folder {path.name}."
                return "Folder contains files or was already removed."

            action_history.push("create_folder", f"Created folder {path.name}", _undo, path=str(path))
            return f"Created directory: {path}"
        except Exception as exc:
            return f"Failed to create directory: {exc}"

    def rename_item(self, source_path: str, new_name: str) -> str:
        src = self._resolve_path(source_path)
        if not src.exists():
            return f"Source path does not exist: {src}"
        new_name_clean = Path(new_name.strip().strip('"\'')).name
        dest = src.parent / new_name_clean
        if dest.exists():
            return f"Target item already exists: {dest.name}"
        try:
            src.rename(dest)

            def _undo():
                if dest.exists() and not src.exists():
                    dest.rename(src)
                    return f"Restored original name '{src.name}'."
                return "Could not revert name."

            action_history.push("rename_file", f"Renamed {src.name} to {dest.name}", _undo, original=str(src), new=str(dest))
            return f"Renamed {src.name} to {dest.name}."
        except PermissionError:
            return f"Permission denied renaming {src.name}. The file may be in use by another program."
        except Exception as exc:
            return f"Failed to rename: {exc}"

    def move_item(self, source_path: str, dest_folder: str) -> str:
        src = self._resolve_path(source_path)
        dest = self._resolve_path(dest_folder)
        if not src.exists():
            return f"Source item does not exist: {src}"
        if not dest.exists():
            return f"Destination directory does not exist: {dest}"
        if not dest.is_dir():
            return f"Destination is not a directory: {dest}"
        target = dest / src.name
        if target.exists():
            return f"{src.name} already exists in destination folder."
        try:
            shutil.move(str(src), str(target))

            def _undo():
                if target.exists() and not src.exists():
                    shutil.move(str(target), str(src))
                    return f"Moved {src.name} back to {src.parent}."
                return "Could not revert move."

            action_history.push("move_file", f"Moved {src.name} to {dest.name}", _undo, source=str(src), destination=str(target))
            return f"Moved {src.name} to {dest}."
        except PermissionError:
            return f"Permission denied moving {src.name}. The file might be open or locked."
        except Exception as exc:
            return f"Failed to move {src.name}: {exc}"

    def copy_item(self, source_path: str, dest_folder: str) -> str:
        src = self._resolve_path(source_path)
        dest = self._resolve_path(dest_folder)
        if not src.exists():
            return f"Source does not exist: {src}"
        if not dest.exists() or not dest.is_dir():
            return f"Destination directory does not exist: {dest}"
        target = dest / src.name
        if target.exists():
            return f"{src.name} already exists in destination. Skipping copy."
        try:
            if src.is_dir():
                shutil.copytree(src, target)
            else:
                shutil.copy2(src, target)
            return f"Copied {src.name} to {dest}."
        except Exception as exc:
            return f"Failed to copy: {exc}"

    def delete_item(self, raw_path: str, require_confirm: bool = True) -> str:
        path = self._resolve_path(raw_path)
        if not path.exists():
            return f"Item does not exist: {path}"
        if self._is_critical_path(path):
            return f"Refused to delete system critical path: {path}"

        def do_delete():
            try:
                send2trash.send2trash(str(path))
                return f"Moved {path.name} to the Recycle Bin."
            except Exception as exc:
                return f"Failed to send to Recycle Bin: {exc}"

        if require_confirm:
            item_type = "directory" if path.is_dir() else "file"
            return safety_guard.request_confirmation(
                action_type="delete_file",
                description=f"delete the {item_type} '{path.name}' (moved safely to Recycle Bin)",
                callback=do_delete
            )
        return do_delete()

    def preview_organize(self, raw_path: str = "") -> str:
        """Previews planned file reorganization before applying changes."""
        target_dir = self._get_organize_target(raw_path)
        if not target_dir.exists() or not target_dir.is_dir():
            return f"Directory not found: {target_dir}"

        plan = {}
        for item in list(target_dir.iterdir()):
            if item.is_file() and not item.name.startswith("."):
                ext = item.suffix.lower()
                for category, extensions in FILE_CATEGORIES.items():
                    if ext in extensions:
                        plan[category] = plan.get(category, 0) + 1
                        break

        if not plan:
            return f"No unorganized files found in {target_dir.name}."

        details = ", ".join(f"{count} into {cat}" for cat, count in plan.items())
        total = sum(plan.values())
        return f"Preview: Organizing {target_dir.name} will move {total} file(s) ({details}). Reply 'confirm' or say 'yes' to proceed."

    def organize_directory(self, raw_path: str = "") -> str:
        """Organizes files in a folder into categorical subfolders."""
        target_dir = self._get_organize_target(raw_path)
        if not target_dir.exists() or not target_dir.is_dir():
            return f"Directory not found: {target_dir}"

        moved_count = 0
        try:
            for item in list(target_dir.iterdir()):
                if item.is_file() and not item.name.startswith("."):
                    ext = item.suffix.lower()
                    matched_category = None
                    for category, extensions in FILE_CATEGORIES.items():
                        if ext in extensions:
                            matched_category = category
                            break
                    if matched_category:
                        cat_dir = target_dir / matched_category
                        cat_dir.mkdir(exist_ok=True)
                        dest_file = cat_dir / item.name
                        if not dest_file.exists():
                            shutil.move(str(item), str(dest_file))
                            moved_count += 1
            return f"Organized {target_dir.name}: categorized {moved_count} file(s) into subfolders."
        except Exception as exc:
            return f"Error while organizing directory: {exc}"

    def _get_organize_target(self, raw_path: str) -> Path:
        clean = raw_path.lower().strip()
        if not clean or clean in {"downloads", "my downloads"}:
            return Path.home() / "Downloads"
        if clean in {"desktop", "my desktop"}:
            return Path.home() / "Desktop"
        return self._resolve_path(raw_path)

    def find_files(self, query: str, search_root: Optional[str] = None, max_results: int = 7) -> str:
        """Search files by keyword, extension, and date qualifiers."""
        query_clean = query.strip().lower()
        if not query_clean:
            return "Please specify a file or keyword to search for."

        # Parse date qualifiers if present
        date_cutoff: Optional[datetime] = None
        now = datetime.now()
        if "yesterday" in query_clean:
            date_cutoff = now - timedelta(days=2)
            query_clean = query_clean.replace("yesterday", "").strip()
        elif "today" in query_clean:
            date_cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query_clean = query_clean.replace("today", "").strip()
        elif "last week" in query_clean:
            date_cutoff = now - timedelta(days=7)
            query_clean = query_clean.replace("last week", "").strip()

        # Parse extension keywords
        target_ext = None
        for ext in (".pdf", ".docx", ".txt", ".png", ".jpg", ".zip", ".exe", ".cpp", ".py"):
            if ext in query_clean or ext[1:] in query_clean.split():
                target_ext = ext
                query_clean = query_clean.replace(ext, "").replace(ext[1:], "").strip()
                break

        roots = []
        if search_root:
            r = self._resolve_path(search_root)
            if r.exists():
                roots.append(r)
        if not roots:
            home = Path.home()
            roots = [home / "Desktop", home / "Downloads", home / "Documents", home / "Videos"]

        matches = []
        skip_dirs = {"node_modules", ".git", "__pycache__", "appdata", "temp"}
        for root in roots:
            if not root.exists():
                continue
            for current, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if d.lower() not in skip_dirs and not d.startswith(".")]
                for filename in files:
                    fn_lower = filename.lower()
                    if query_clean and query_clean not in fn_lower:
                        continue
                    p = Path(current) / filename
                    if target_ext and p.suffix.lower() != target_ext:
                        continue
                    if date_cutoff:
                        try:
                            mtime = datetime.fromtimestamp(p.stat().st_mtime)
                            if mtime < date_cutoff:
                                continue
                        except Exception:
                            continue
                    matches.append(p)
                    if len(matches) >= max_results:
                        break
                if len(matches) >= max_results:
                    break
            if len(matches) >= max_results:
                break

        if not matches:
            return f"No files matching '{query}' were found in common user folders."

        out = [f"Found {len(matches)} match(es) for '{query}':"]
        for i, m in enumerate(matches, 1):
            out.append(f"{i}. {m.name}  —  {m.parent}")
        return "\n".join(out)

file_manager = FileManager()
