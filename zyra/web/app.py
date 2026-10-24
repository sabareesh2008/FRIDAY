"""Flask Web Server & API for ZYRA Assistant Web Dashboard."""
import os
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

from zyra.ai_engine import ai_engine
from zyra.planner import planner
from zyra.safety import safety_guard
from zyra.media_finder import media_finder
from zyra.config import config
from zyra.startup import startup_manager
from zyra.windows_manager import windows_manager
from zyra.browser_manager import browser_manager

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = Flask(__name__, template_folder=str(TEMPLATE_DIR), static_folder=str(STATIC_DIR))
CORS(app)

# Ensure media indexing starts when web server boots
media_finder.start_indexing()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/command", methods=["POST"])
def execute_command():
    data = request.get_json(force=True, silent=True) or {}
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"success": False, "error": "Empty command"}), 400

    if planner.is_multi_step(command):
        response_text = planner.execute_plan(command, ai_engine.parse_and_execute)
    else:
        response_text = ai_engine.parse_and_execute(command)

    has_pending = safety_guard.has_pending
    pending_desc = safety_guard.get_pending_description() if has_pending else ""

    return jsonify({
        "success": True,
        "command": command,
        "response": response_text,
        "pending_confirmation": has_pending,
        "confirmation_description": pending_desc
    })

@app.route("/api/confirm", methods=["POST"])
def handle_confirmation():
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "").lower().strip()

    if action in {"yes", "confirm", "proceed", "y"}:
        res = safety_guard.confirm()
    elif action in {"no", "cancel", "abort", "n"}:
        res = safety_guard.cancel()
    else:
        return jsonify({"success": False, "error": "Invalid action. Use 'yes' or 'no'."}), 400

    return jsonify({
        "success": True,
        "response": res,
        "pending_confirmation": safety_guard.has_pending
    })

@app.route("/browser/bridge", methods=["POST", "OPTIONS"])
def browser_bridge():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    data = request.get_json(force=True, silent=True) or {}
    tabs = data.get("tabs", [])
    if tabs:
        browser_manager.update_extension_tabs(tabs)
    return jsonify({"status": "ok", "synced_count": len(tabs)})

@app.route("/api/status", methods=["GET"])
def get_status():
    indexed_count = len(media_finder._file_index)
    return jsonify({
        "assistant_name": config.get("assistant_name", "ZYRA"),
        "media_indexer_ready": media_finder._index_ready,
        "media_indexed_count": indexed_count,
        "pending_confirmation": safety_guard.has_pending,
        "pending_description": safety_guard.get_pending_description(),
        "tts_enabled": config.get("tts_enabled", True),
        "tts_rate": config.get("tts_rate", 175),
        "tts_volume": config.get("tts_volume", 1.0),
        "startup_enabled": startup_manager.is_startup_enabled(),
        "has_api_key": bool(config.get("api_key")),
        "llm_provider": config.get("llm_provider", "local_rules"),
    })

@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.get_json(force=True, silent=True) or {}
    if "api_key" in data:
        key = str(data["api_key"]).strip()
        if key:
            config.set("api_key", key)
            if key.startswith("AIza"):
                config.set("llm_provider", "gemini")
            elif key.startswith("sk-"):
                config.set("llm_provider", "openai")
    if "tts_enabled" in data:
        config.set("tts_enabled", bool(data["tts_enabled"]))
    if "tts_rate" in data:
        config.set("tts_rate", int(data["tts_rate"]))
    if "tts_volume" in data:
        config.set("tts_volume", float(data["tts_volume"]))
    if "startup_enabled" in data:
        enable = bool(data["startup_enabled"])
        if enable:
            startup_manager.enable_startup()
        else:
            startup_manager.disable_startup()

    return jsonify({"success": True, "config": config.data})

@app.route("/api/quick-actions", methods=["GET"])
def get_quick_actions():
    actions = [
        {
            "category": "Desktop & Windows",
            "items": [
                {"label": "Show Desktop", "cmd": "show desktop", "icon": "desktop"},
                {"label": "Switch Window", "cmd": "switch window", "icon": "clone"},
                {"label": "Maximize Window", "cmd": "maximize window", "icon": "window-maximize"},
                {"label": "Toggle Mute", "cmd": "mute", "icon": "volume-mute"},
            ]
        },
        {
            "category": "Browser & Tabs",
            "items": [
                {"label": "New Tab", "cmd": "new tab", "icon": "plus-circle"},
                {"label": "Close Tab", "cmd": "close tab", "icon": "times-circle"},
                {"label": "Reopen Tab", "cmd": "reopen tab", "icon": "undo"},
                {"label": "Open Gmail", "cmd": "open Gmail", "icon": "envelope"},
                {"label": "Open YouTube", "cmd": "go to youtube.com", "icon": "play-circle"},
            ]
        },
        {
            "category": "Vision & AI",
            "items": [
                {"label": "Analyze Screen", "cmd": "look at my screen and help with any error", "icon": "eye"},
                {"label": "Debug Code on Screen", "cmd": "look at my screen and debug the code", "icon": "bug"},
                {"label": "Check RAM & System", "cmd": "how much RAM do I have?", "icon": "microchip"},
                {"label": "Check Battery", "cmd": "check battery percentage", "icon": "battery-three-quarters"},
            ]
        },
        {
            "category": "Coding & Compilers",
            "items": [
                {"label": "Java Two Sum (VS Code)", "cmd": "create Java file TwoSum and open in VS Code", "icon": "code"},
                {"label": "Python Binary Search (Run)", "cmd": "write python code for binary search and run it", "icon": "terminal"},
                {"label": "Java Online Compiler", "cmd": "open online compiler for Java and write two sum", "icon": "globe"},
                {"label": "C++ Merge Sort (VS Code)", "cmd": "create cpp file MergeSort and open in VS Code", "icon": "laptop-code"},
            ]
        },
        {
            "category": "Files & System",
            "items": [
                {"label": "Organize Downloads", "cmd": "organize downloads", "icon": "folder"},
                {"label": "Lock PC", "cmd": "lock PC", "icon": "lock"},
                {"label": "Sleep PC", "cmd": "sleep PC", "icon": "moon", "risky": True},
            ]
        }
    ]
    return jsonify(actions)

def create_app():
    return app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
