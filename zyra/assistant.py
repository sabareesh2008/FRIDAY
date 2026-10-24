"""ZYRA — Intelligent Personal Desktop Assistant with AI understanding, voice & multi-step execution."""
import os
import sys
import threading
from typing import Optional
from zyra.ai_engine import ai_engine
from zyra.planner import planner
from zyra.voice_manager import VoiceManager
from zyra.computer import Computer
from zyra.media_finder import media_finder
from zyra.config import config

class ZyraAssistant:
    def __init__(self):
        self.computer = Computer()
        self.running = True
        self.output_lock = threading.Lock()
        self.voice_manager = VoiceManager(
            on_command_callback=self.handle_command,
            on_say_callback=self.say
        )

    def say(self, message: str):
        if not message:
            return
        asst_name = config.get("assistant_name", "FRIDAY")
        with self.output_lock:
            print(f"\n{asst_name}: {message}")
        self.voice_manager.speak(message)

    def handle_command(self, raw_command: str) -> str:
        command = raw_command.strip()
        if not command:
            return ""

        # Check multi-step planning
        if planner.is_multi_step(command):
            res = planner.execute_plan(command, ai_engine.parse_and_execute)
        else:
            res = ai_engine.parse_and_execute(command)

        if res == "QUIT_SIGNAL":
            self.running = False
            return "Goodbye! Have a great day."

        return res

    def run(self):
        asst_name = config.get("assistant_name", "FRIDAY")
        print("=" * 60)
        print(f"   {asst_name} — Intelligent Personal Desktop AI Assistant")
        print("=" * 60)
        print(f" • Voice & Text: Speak ('Hey {asst_name} ...') or type commands below.")
        print(" • Preserved Media Search: 'play Interstellar', 'watch Avatar'")
        print(" • Dynamic App Launching: 'open Notepad', 'launch VS Code', 'open Spotify'")
        print(" • Window Controls: 'switch window', 'maximize/minimize window', 'show desktop'")
        print(" • Browser & Tabs: 'new tab', 'close tab', 'search Google for Java DSA'")
        print(" • Safe File Management: 'organize downloads', 'find file report', 'delete file'")
        print(" • Multi-Step Commands: 'open Notepad and open Calculator and show desktop'")
        print(" • System Power: 'lock PC', 'sleep PC', 'restart PC' (safely confirmed)")
        print(" • Autostart: 'enable startup' / 'disable startup'")
        print(" Type 'help' for full guide, or 'exit' to quit.")
        print("-" * 60)

        # Start background media indexing
        media_finder.start_indexing()

        # Start hands-free voice listener
        self.voice_manager.start_listening(notify_fn=lambda msg: print(f"\n{msg}\nYou: ", end="", flush=True))

        while self.running:
            try:
                raw = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                self.running = False
                print(f"\n{asst_name}: Goodbye!")
                break

            if not raw:
                continue

            # Immediate cancellation
            if raw.lower() in {"stop", "cancel", "shut up", "abort"}:
                self.voice_manager.stop_speaking()
                print(f"\n{asst_name}: Stopped active task/speech.")
                continue

            response = self.handle_command(raw)
            if response:
                self.say(response)

            if not self.running:
                break

        self.voice_manager.stop_listening()

if __name__ == "__main__":
    ZyraAssistant().run()
