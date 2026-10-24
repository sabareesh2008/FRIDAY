# ZYRA / FRIDAY — Autonomous Windows Desktop AI Assistant

**ZYRA (FRIDAY)** is an intelligent, reliable, hands-free personal desktop AI assistant engineered specifically for Windows 10 and 11. It blends native Windows UI Automation, multimodal visual grounding, autonomous browser tab orchestration, safe file management with full Undo history, and hands-free voice control with a respectful British lady voice (*Microsoft Hazel*).

---

## 🌟 Key Capabilities

### 1. Hands-Free Voice Assistant (Lady Voice)
- **Natural Voice Persona**: Speaks with a clear, warm British female voice (*Microsoft Hazel* / *Zira*) and respectfully addresses you as **"sir"**.
- **Local Wake-Word**: Listens continuously for `"Hey Friday"`, `"Friday"`, or `"Hey Zyra"`.
- **Configurable Audio Devices**: Detects and switches microphones via `"list microphones"` and `"set microphone <index>"`.
- **Hands-Free Cancellation**: Speak *"stop"*, *"cancel"*, *"shut up"*, or *"nevermind"* at any time to immediately interrupt speech or abort actions.

### 2. Autonomous Screen Operator ("Eyes & Hands")
- **Computer-Using Agent**: Doesn't rely only on static commands; visually perceives elements on your monitor and clicks them automatically.
- **Visual Grounding**: Employs **Windows UI Automation (UIA)** first, backed by **Google Gemini Flash Vision** coordinate grounding for deep in-page elements.
- **Mouse & Keystroke Automation**:
  - `"click Sabareesh mail id"`
  - `"search machine learning and press enter"`
  - `"double click project file"`
  - `"scroll down"`
  - `"type hello sir and enter"`
- **Automatic Download Watcher**: Continuously monitors your `Downloads` directory in the background and announces aloud when a file finishes downloading (*"Your download of report.pdf is complete, sir."*).

### 3. Natural Language & Conversational Context
- **Chained Multi-Step Pipelines**: Chain custom commands with `..`, commas, or phrases:
  > *"open chrome.. click Sabareesh mail id.. search python tutorial.. open this link.. click download"*
- **Conversational Follow-ups & Pronoun Resolution**:
  - *"Open Chrome."*
  - *"Find the PDF I downloaded yesterday and put it in my project folder."*
  - *"Open that folder again."*
  - *"Actually, move it to Documents instead."*
  - *"Undo the last action if possible."*
- **Action History & Full Undo Stack**: Reverts file moves, renames, and creations with a single `"undo"` command.

### 4. Advanced Browser Orchestration
- **Specific Tab Control**:
  - *"Close the YouTube tab but leave my college portal open."*
  - *"List open tabs"* / *"Show tabs"*.
  - *"Switch to tab college portal"*.
- **Offline Browser History Search**: Directly queries local Chrome / Edge SQLite history databases (`"search browser history for python"`) even when the browser is closed.
- **Manifest V3 Extension**: Dedicated companion extension located in `browser_extension/` for 100% accurate tab synchronization.

### 5. Windows Desktop Control
- **App Launching**: Discovers installed software dynamically across registry, Start Menu shortcuts, and Windows UWP tools (`camera`, `photos`, `clock`, `settings`, etc.).
- **Virtual Desktops**:
  - *"create virtual desktop"* (`Win+Ctrl+D`)
  - *"close virtual desktop"* (`Win+Ctrl+F4`)
  - *"next desktop"* / *"previous desktop"* (`Win+Ctrl+Right/Left`)
- **System Controls**: Adjust volume, mute/unmute, lock screen (`Win+L`), sleep, restart, and shutdown.

### 6. 3-Tier Safety & Permissions
- **Low Risk** (Auto-executed): Open app, switch window, search files, read screen.
- **Medium Risk** (Logged & Reversible): Move/rename files, close tabs.
- **High Risk** (Explicit Confirmation Required): Delete files (safely sent to Recycle Bin via `send2trash`), system power actions.
- **Privacy Action Logging**: Appends sanitized action records to `~/.zyra/actions.log` without storing passwords, tokens, or credentials.

### 7. Remote Task Queue & Wake-on-LAN
- **Task Queue**: Schedule commands to execute automatically when the laptop wakes up (`"queue task organize downloads"`).
- **Wake-on-LAN**: Broadcasts UDP magic packets to wake supported PCs on the local network (`"wake on lan AA:BB:CC:DD:EE:FF"`).

---

## 🚀 Installation & Quick Start (Windows)

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10, 3.11, or 3.12 installed and added to your `PATH`

### Step 1: Install Dependencies
Open PowerShell or Command Prompt in the project folder and run:
```cmd
pip install -r requirements.txt
```

### Step 2: Configure Environment (Optional)
Copy `.env.example` to `.env`:
```cmd
copy .env.example .env
```
*(Optional: Add your free Google Gemini API key to enable visual vision and open-ended conversation. ZYRA runs 100% offline without it!)*

### Step 3: Run ZYRA / FRIDAY

You can run FRIDAY in three modes:

1. **Terminal & Voice Assistant Mode**:
   ```cmd
   run_friday.bat
   ```
   *(Or `python main.py`)*

2. **Web Dashboard & REST API Mode**:
   ```cmd
   run_friday_web.bat
   ```
   Open `http://127.0.0.1:5000` in your browser to access the visual HUD dashboard.

3. **Background Daemon Mode**:
   ```cmd
   run_friday_daemon.bat
   ```
   Runs as an always-on background listener that responds whenever you say *"Hey Friday"*.

---

## 🌐 Browser Extension Setup (Chrome / Edge / Brave)

1. Open your browser and go to `chrome://extensions` (or `edge://extensions`).
2. Turn ON **Developer mode** in the top-right corner.
3. Click **Load unpacked** (top-left).
4. Select the directory:
   ```
   C:\Sabareesh\ZYRA\browser_extension
   ```
5. The extension connects to ZYRA at `http://127.0.0.1:5005` to synchronize tabs in real time.

---

## 🧪 Automated Testing

Run the full automated test suite (all 68 unit & integration tests):
```cmd
python -m unittest discover -s tests -p "test_*.py"
```

### Test Coverage Summary:
- **`test_zyra_core.py`**: Core commands, app discovery, media isolation, safety confirmations, planner.
- **`test_master_upgrade.py`**: Undo stack, follow-ups, specific tab close, history search, virtual desktops, remote tasks, WOL, 3-tier risk logging, microphone listing.
- **`test_screen_operator.py`**: UI click, type, press key, scroll, chained pipeline execution, companion chit-chat.
- **`test_tts.py`**: Windows SAPI Hazel lady voice engine and respectful *"sir"* formatting.
- **`test_coding_system.py`**: Multi-language code generation, IDE manager, runner, and phonetic transcript normalizer.
- **`test_vision_daemon.py`**: Screen capture, vision diagnostics, and daemon listener.
- **`test_web_api.py`**: Flask Web API, command endpoint, and status reporting.

**Result: 68 tests passing (100% success rate).**

---

## 🛡️ License
Private project engineered for personal desktop productivity.
