# FRIDAY — Intelligent Personal Desktop AI Assistant

FRIDAY is an advanced, multimodal (Voice + CLI) desktop operating assistant for Windows. It combines natural voice interaction, dynamic application launching, window & browser controls, safe file operations, multi-step sequential execution, and local movie/media search.

---

## 1. Quick Setup & Installation

Ensure you have **Python 3.11** or newer installed. Open PowerShell in the project directory and run:

```powershell
python -m pip install -r requirements.txt
```

> **Note on Audio:** If `PyAudio` is unavailable or your microphone fails, ZYRA automatically degrades to a smooth, fully featured text-only interface.

---

## 2. Running ZYRA

### Option A: Web Dashboard (Interactive AI Interface)
Launch the modern glassmorphism web dashboard in standalone app window:

```powershell
python web_main.py
```
Or double-click:
```text
run_zyra_web.bat
```
*(Runs at `http://127.0.0.1:5000` with animated visualizer orb, live chat, one-click quick actions, safety confirmation modal, and in-browser voice support).*

### Option B: Terminal CLI Interface
Launch in standard PowerShell/Command Prompt:

```powershell
python main.py
```
Or double-click:
```text
run_zyra.bat
```

---

## 3. Core Features & Command Guide

### 🤖 1. AI Command Understanding & Context
* Flexible natural language parsing with typo tolerance.
* Wake phrase removal (`"Hey Friday"`, `"Friday"`, `"Hey Zyra"`, `"Zyra"`).
* Pronoun resolution (`"open Notepad"` $\rightarrow$ `"maximize it"` $\rightarrow$ `"close it"`).
* Direct cancellation support: type or say `"stop"`, `"cancel"`, or `"nevermind"` to halt active speech or tasks.

### 🪟 2. Windows & Application Control
* **Dynamic Software Discovery:** Automatically scans the Windows Start Menu and Registry `App Paths` to launch any installed program:
  * `"open Notepad"`
  * `"launch Discord"`
  * `"open VS Code"`
  * `"open Spotify"`
* **Window Management:**
  * `"switch window"` (or `"focus Notepad"`)
  * `"maximize window"` / `"minimize window"`
  * `"close window"`
  * `"show desktop"` (or `"minimize all"`)
* **Volume Control:**
  * `"mute"`, `"unmute"`
  * `"increase volume"`, `"decrease volume"`
* **Power Management (Protected):**
  * `"lock PC"`
  * `"sleep PC"` *(requires confirmation)*
  * `"restart PC"` *(requires confirmation)*
  * `"shutdown PC"` *(requires confirmation)*

### 🌐 3. Browser & Tab Controls
* **Tab Controls:** `"new tab"`, `"close tab"`, `"reopen tab"`, `"next tab"`, `"previous tab"`.
* **In-Page Search:** `"search this page for scholarship"`.
* **Page Utilities:** `"refresh"`, `"history"`, `"downloads"`, `"bookmarks"`, `"zoom in"`, `"zoom out"`.
* **Web Search Engine Integration:**
  * `"search Google for Python DSA"`
  * `"search YouTube for lofi hip hop"`
  * `"search GitHub for machine learning"`
  * `"search Wikipedia for Quantum Physics"`
* **Direct Navigation:** `"go to youtube.com"`, `"open Gmail"` (or `"open Gmail for user@example.com"`).

### 📁 4. Safe File Management
* **Find Files:** `"find file report.docx"`, `"locate file project"`
* **Create Files & Folders:**
  * `"create folder ProjectAlpha"`
  * `"create file notes.txt with content Meeting at 10 AM"`
* **Organize Directory:**
  * `"organize downloads"` *(sorts files into Images, Documents, Videos, Audio, Archives, Executables, and Code)*
* **Safe Deletion:**
  * `"delete file old_draft.txt"` *(moves file to Windows Recycle Bin via `send2trash` with confirmation)*
* **Rename & Move:**
  * `"rename notes.txt to final_notes.txt"`
  * `"move file.txt to C:\Users\Username\Documents"`

### ⚡ 5. Multi-Step Sequential Planning
Chain multiple commands using `"and"`, `"then"`, `"after that"`, or semicolons:
* `"open Notepad and open Calculator and show desktop"`
* `"create folder Work and then organize downloads"`
* Verified execution: reports progress step-by-step and safely pauses if confirmation is required.

### 🛡️ 6. Safety & Confirmation Guardrails
Destructive or irreversible actions (PC shutdown, reboot, sleep, file deletion) are held in a pending state until you verify:
* Reply `"yes"` / `"confirm"` to execute.
* Reply `"no"` / `"cancel"` to abort.

### 🎬 7. Preserved Local Movie & Media Search
ZYRA maintains its fast background indexing and fuzzy media matching across user directories (`Desktop`, `Downloads`, `Videos`, `Movies`, `Documents`, and external drives `D:`, `E:`):
* `"play Interstellar"`
* `"watch Avatar"`
* `"open movie Inception"`
* Strips release tags (`1080p`, `BluRay`, `x264`, `webrip`) and provides disambiguation lists if multiple files match.

### 🚀 8. Windows Startup Autostart
* Turn on auto-launch when Windows boots:
  * `"enable startup"`
* Remove from Windows boot:
  * `"disable startup"`

### 💻 9. Autonomous AI Coding Assistant (Natural Folders & Any Language)
ZYRA can write, open, compile, and run code in any programming language, **without requiring you to type or know exact system paths**:
* **Natural Folder Phrasing:** You can simply say:
  * `"open this folder on vscode create new file on this folder"` $\rightarrow$ uses your active project folder or conveniently creates one on your Desktop.
  * `"open DSA folder on vscode and create a java file for two sum"` $\rightarrow$ automatically finds or creates a `DSA` folder and names the file `TwoSum.java`.
  * `"open LeetCode folder and create new file"` $\rightarrow$ finds `LeetCode` folder across your PC or creates it.
* **Context Memory:** Remembers your active folder across sequential voice commands (e.g. *"create new file on this folder"*).
* **Automatic File Naming:** If you just say *"create new file for two sum"*, ZYRA automatically names the file appropriately (`TwoSum.java` or `two_sum.py`).
* **Supported Languages:** Java, Python, C++, C, JavaScript, TypeScript, Go, Rust, C#, Kotlin, Swift, PHP, Ruby, HTML/CSS, SQL.
* **Supported IDEs & Editors:** VS Code, IntelliJ IDEA, PyCharm, Eclipse, Sublime Text, Notepad++, and system editors.
* **Online Compilers & Playgrounds:** OneCompiler, OnlineGDB, Programiz, Go Playground, Rust Playground.
* **Example Commands:**
  * `"open this folder on vscode create new file on this folder and write two sum"`
  * `"open DSA folder on vscode create new file on this folder and write binary search"`
  * `"create python file SnakeGame on my desktop and run it"`
  * `"open online compiler for Java and write two sum"` *(opens online compiler and copies code to clipboard)*

### 👁️ 11. Screen Vision & Visual Diagnostics
ZYRA can look at your active screen and answer questions both aloud and visually:
* **Audio & Visual Answers:** Speaks the diagnostic summary aloud through TTS and provides detailed logs and saved screenshots.
* **Multimodal AI Vision:** When connected to Gemini API, reads on-screen code, terminal stack traces, dialogs, and browser windows.
* **Example Commands:**
  * `"look at my screen and tell me what is the error"`
  * `"look at my screen and debug the code"`
  * `"what is on my screen?"`
  * `"take a screenshot and analyze it"`

### 🌙 12. Background Standby Daemon ("Hey FRIDAY" Auto-Boot)
FRIDAY can run 24/7 silently in the background without needing a terminal or web browser open:
* **Lady Voice (British Hazel / Zira):** Configured with an authentic female assistant voice, addressing you respectfully as **"sir"**.
* **Auto-Boot on Windows Startup:** Greets you aloud when Windows logs in (*"Good morning, sir! FRIDAY is online and at your service. Say 'Hey FRIDAY' whenever you need me."*).
* **Wake-Up Response:** Saying **`"Hey FRIDAY"`** immediately prompts her spoken reply: *"Yes, sir? What can I do for you?"*
* **Launch Daemon Manually:**
  * Double-click `run_zyra_daemon.bat` or run `pythonw daemon_main.py`.
* **Enable at Windows Boot:**
  * Say or type `"enable startup"` to register the background daemon.

---

## 4. Configuration (`zyra_config.json`)

Settings are stored in `zyra_config.json` at the root of the project:
* `wake_words`: customizable wake triggers.
* `require_confirmation`: toggle confirmation prompts on risky actions.
* `tts_enabled`, `tts_rate`, `tts_volume`: voice output preferences.
* `stt_language`: language code for speech recognition (default: `en-IN`).
* `browser`: preferred default browser target.
