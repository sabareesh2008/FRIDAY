"""IDE and Code Editor integration for ZYRA (VS Code, JetBrains, Eclipse, Sublime, Notepad++, etc.)."""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IDE_EXECUTABLES: Dict[str, List[str]] = {
    "vscode": ["code.cmd", "code.exe", "code"],
    "pycharm": ["pycharm64.exe", "pycharm.exe", "pycharm"],
    "intellij": ["idea64.exe", "idea.exe", "idea"],
    "sublime": ["subl.exe", "sublime_text.exe", "subl"],
    "notepadplusplus": ["notepad++.exe", "notepad++"],
    "eclipse": ["eclipse.exe", "eclipse"],
    "visualstudio": ["devenv.exe"],
    "androidstudio": ["studio64.exe", "studio.exe"],
    "cursor": ["cursor.exe", "cursor"],
    "devcpp": ["devcpp.exe"],
    "codeblocks": ["codeblocks.exe"],
    "notepad": ["notepad.exe"],
}

class IDEManager:
    def __init__(self):
        self._cached_paths: Dict[str, str] = {}
        self._scan_ides()

    def _scan_ides(self):
        # 1. Search PATH
        for ide_key, binaries in IDE_EXECUTABLES.items():
            for b in binaries:
                found = shutil.which(b)
                if found:
                    self._cached_paths[ide_key] = found
                    break

        # 2. Search common Windows locations
        home = Path.home()
        extra_checks = {
            "vscode": [
                home / "AppData/Local/Programs/Microsoft VS Code/bin/code.cmd",
                home / "AppData/Local/Programs/Microsoft VS Code/Code.exe",
                Path("C:/Program Files/Microsoft VS Code/bin/code.cmd"),
                Path("C:/Program Files/Microsoft VS Code/Code.exe"),
            ],
            "notepadplusplus": [
                Path("C:/Program Files/Notepad++/notepad++.exe"),
                Path("C:/Program Files (x86)/Notepad++/notepad++.exe"),
            ],
            "sublime": [
                Path("C:/Program Files/Sublime Text/sublime_text.exe"),
                Path("C:/Program Files/Sublime Text 3/sublime_text.exe"),
            ],
            "pycharm": [
                home / "AppData/Local/Programs/JetBrains/PyCharm/bin/pycharm64.exe",
                Path("C:/Program Files/JetBrains/PyCharm/bin/pycharm64.exe"),
            ],
            "intellij": [
                home / "AppData/Local/Programs/JetBrains/IntelliJ IDEA/bin/idea64.exe",
                Path("C:/Program Files/JetBrains/IntelliJ IDEA/bin/idea64.exe"),
            ],
        }

        for ide_key, paths in extra_checks.items():
            if ide_key not in self._cached_paths:
                for p in paths:
                    if p.exists():
                        self._cached_paths[ide_key] = str(p)
                        break

    def get_ide_path(self, ide_name: str) -> Optional[str]:
        clean = ide_name.lower().replace(" ", "").replace("-", "")
        if clean in self._cached_paths:
            return self._cached_paths[clean]
        aliases = {
            "code": "vscode", "vs": "vscode", "visualstudiocode": "vscode",
            "charm": "pycharm", "py": "pycharm",
            "idea": "intellij",
            "subl": "sublime", "sublimetext": "sublime",
            "npp": "notepadplusplus", "notepad++": "notepadplusplus",
        }
        mapped = aliases.get(clean)
        if mapped and mapped in self._cached_paths:
            return self._cached_paths[mapped]

        # General search in cache
        for k, v in self._cached_paths.items():
            if clean in k or k in clean:
                return v

        return None

    def open_workspace(self, ide_name: str, file_path: Optional[str] = None, folder_path: Optional[str] = None) -> str:
        """Launches IDE with the folder and/or specific file opened."""
        target_ide = self.get_ide_path(ide_name) or self.get_ide_path("vscode") or self.get_ide_path("notepad")
        if not target_ide:
            # Fallback to system default association
            if file_path and os.path.exists(file_path):
                os.startfile(file_path)
                return f"Opened {Path(file_path).name} in default application."
            return f"No editor found for '{ide_name}'."

        args = [target_ide]
        clean_file = str(Path(file_path).resolve()) if file_path else ""
        clean_folder = str(Path(folder_path).resolve()) if folder_path else ""

        # VS Code handles `code <folder> <file>` or `code -r <file>`
        is_vscode = "code" in target_ide.lower()
        if is_vscode:
            if clean_folder and clean_file:
                args.extend([clean_folder, clean_file])
            elif clean_folder:
                args.append(clean_folder)
            elif clean_file:
                args.append(clean_file)
        else:
            if clean_file:
                args.append(clean_file)
            elif clean_folder:
                args.append(clean_folder)

        try:
            subprocess.Popen(args, shell=False)
            display_name = Path(target_ide).stem.capitalize()
            target_desc = f"file '{Path(clean_file).name}'" if clean_file else f"folder '{clean_folder}'"
            return f"Opened {target_desc} in {display_name}."
        except Exception as exc:
            return f"Failed to launch editor {target_ide}: {exc}"

ide_manager = IDEManager()
