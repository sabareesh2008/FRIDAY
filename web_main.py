"""Launch ZYRA Web Interface & App Window."""
import sys
import time
import shutil
import subprocess
import webbrowser
from pathlib import Path
from zyra.web.app import app

def launch_browser(url: str = "http://127.0.0.1:5000"):
    time.sleep(1.2)
    # Check if Chrome or Edge can be opened in clean borderless App Mode
    chrome_candidates = [
        shutil.which("chrome"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"),
        shutil.which("msedge"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for exe in chrome_candidates:
        if exe and Path(exe).exists():
            try:
                subprocess.Popen([exe, f"--app={url}"], shell=False)
                return
            except Exception:
                pass
    # Fallback to default browser
    webbrowser.open(url)

if __name__ == "__main__":
    import threading
    print("=" * 60)
    print("   FRIDAY — Web Dashboard & Assistant Server")
    print("=" * 60)
    print(" Starting local server at http://127.0.0.1:5000 ...")
    print(" Opening browser dashboard in standalone app window...")
    print(" Press Ctrl+C in this window to stop the server.")
    print("-" * 60)

    # Launch browser automatically
    threading.Thread(target=launch_browser, daemon=True).start()

    # Run Flask server
    app.run(host="127.0.0.1", port=5000, debug=False)
