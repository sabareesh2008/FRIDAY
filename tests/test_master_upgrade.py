"""Comprehensive test suite for ZYRA Master Upgrade.

Validates:
- Action History and Undo stack (file creates, renames, moves).
- Follow-ups ("open that folder again", "actually move it to Documents instead").
- Specific browser tab controls ("close YouTube but keep college portal open", tab listing, history search).
- Virtual desktop commands.
- Remote task queue and Wake-on-LAN packet generation.
- 3-tier risk safety guardrails and action logging.
- Microphone listing and selection.
"""
import os
import shutil
import unittest
from pathlib import Path

from zyra.ai_engine import ai_engine
from zyra.action_history import action_history
from zyra.file_manager import file_manager
from zyra.browser_manager import browser_manager
from zyra.windows_manager import windows_manager
from zyra.safety import safety_guard, RiskLevel
from zyra.remote_tasks import remote_tasks
from zyra.voice_manager import VoiceManager

class TestMasterUpgrade(unittest.TestCase):

    def setUp(self):
        self.scratch = Path(__file__).resolve().parent / "test_scratch_master"
        self.scratch.mkdir(parents=True, exist_ok=True)
        safety_guard._pending_action = None

    def tearDown(self):
        safety_guard._pending_action = None
        if self.scratch.exists():
            shutil.rmtree(self.scratch, ignore_errors=True)

    # 1. Action History & Undo Stack
    def test_create_file_and_undo(self):
        f = self.scratch / "sample_undo.txt"
        file_manager.create_file(str(f), "Sample content")
        self.assertTrue(f.exists())

        res = action_history.undo_last()
        self.assertIn("Undid action", res)
        self.assertFalse(f.exists())

    def test_move_file_and_undo(self):
        src = self.scratch / "orig.txt"
        src.write_text("orig text")
        dest_folder = self.scratch / "dest_folder"
        dest_folder.mkdir()

        res_move = file_manager.move_item(str(src), str(dest_folder))
        self.assertIn("Moved", res_move)
        target = dest_folder / "orig.txt"
        self.assertTrue(target.exists())
        self.assertFalse(src.exists())

        res_undo = action_history.undo_last()
        self.assertIn("Undid action", res_undo)
        self.assertTrue(src.exists())
        self.assertFalse(target.exists())

    def test_rename_file_and_undo(self):
        f = self.scratch / "first_name.txt"
        f.write_text("content")

        res_rename = file_manager.rename_item(str(f), "second_name.txt")
        self.assertIn("Renamed", res_rename)
        renamed = self.scratch / "second_name.txt"
        self.assertTrue(renamed.exists())
        self.assertFalse(f.exists())

        res_undo = action_history.undo_last()
        self.assertIn("Undid action", res_undo)
        self.assertTrue(f.exists())
        self.assertFalse(renamed.exists())

    # 2. Conversational Follow-ups
    def test_open_folder_again_followup(self):
        test_dir = self.scratch / "project_folder"
        test_dir.mkdir()
        ai_engine.parse_and_execute(f"open {test_dir}")
        self.assertEqual(ai_engine.memory.last_folder, str(test_dir))

        res = ai_engine.parse_and_execute("open that folder again")
        self.assertIn("Opened project_folder", res)

    def test_actually_move_it_instead_followup(self):
        f = self.scratch / "paper.pdf"
        f.write_text("paper content")
        folder1 = self.scratch / "folder1"
        folder2 = self.scratch / "folder2"
        folder1.mkdir()
        folder2.mkdir()

        # Step 1: Move to folder1
        ai_engine.parse_and_execute(f"move {f} to {folder1}")
        moved_first = folder1 / "paper.pdf"
        self.assertTrue(moved_first.exists())

        # Step 2: "Actually, move it to folder2 instead"
        res2 = ai_engine.parse_and_execute(f"actually, move it to {folder2} instead")
        self.assertTrue("Moved" in res2 or "Adjusted destination" in res2)
        moved_second = folder2 / "paper.pdf"
        self.assertTrue(moved_second.exists())

    # 3. Advanced Browser Control
    def test_close_specific_tab_query_parsing(self):
        res = ai_engine.parse_and_execute("close the YouTube tab but leave my college portal open")
        self.assertTrue("Closed tab" in res or "Attempted tab action" in res)

    def test_tab_listing_command(self):
        res = ai_engine.parse_and_execute("list open tabs")
        self.assertTrue("open browser tab" in res or "No open browser tabs" in res)

    def test_history_search_offline(self):
        res = browser_manager.search_browser_history("python", max_results=3)
        self.assertTrue("browser history" in res.lower() or "no browser history" in res.lower())

    # 4. Virtual Desktops
    def test_virtual_desktop_commands(self):
        res1 = ai_engine.parse_and_execute("list virtual desktops")
        self.assertIn("Virtual Desktops", res1)

        res2 = ai_engine.parse_and_execute("create virtual desktop")
        self.assertTrue("virtual desktop" in res2.lower())

        res3 = ai_engine.parse_and_execute("next desktop")
        self.assertTrue("virtual desktop" in res3.lower())

        res4 = ai_engine.parse_and_execute("close virtual desktop")
        self.assertTrue("virtual desktop" in res4.lower())

    # 5. Remote Tasks and Wake-on-LAN
    def test_remote_task_queue(self):
        res = ai_engine.parse_and_execute("queue task open notepad")
        self.assertIn("Enqueued task", res)

        q = remote_tasks.list_queued_tasks()
        self.assertTrue(len(q) > 0)
        self.assertTrue(any("open notepad" in t["command"] for t in q))

        # Process pending tasks
        processed = remote_tasks.process_pending_tasks(lambda c: f"Executed {c}")
        self.assertTrue(len(processed) > 0)

    def test_wake_on_lan_packet(self):
        # Valid MAC address
        res_valid = remote_tasks.send_wake_on_lan("AA:BB:CC:DD:EE:FF")
        self.assertIn("Sent Wake-on-LAN magic packet", res_valid)

        # Invalid MAC address
        res_invalid = remote_tasks.send_wake_on_lan("INVALID_MAC")
        self.assertIn("Invalid MAC", res_invalid)

    # 6. Safety Guard 3-Tier Risk Logging
    def test_action_logging(self):
        safety_guard.log_action("test_action", "secret=my_secret_token", RiskLevel.LOW, "SUCCESS")
        log_file = Path.home() / ".zyra" / "actions.log"
        self.assertTrue(log_file.exists())
        content = log_file.read_text(encoding="utf-8")
        self.assertIn("[LOW] [test_action]", content)
        self.assertNotIn("my_secret_token", content)  # Sanitized to secret=***

    # 7. Microphone Controls
    def test_microphone_listing(self):
        res = ai_engine.parse_and_execute("list microphones")
        self.assertTrue("microphone" in res.lower() or "audio input" in res.lower())

    # 8. User Corrections & Enhanced Shortcuts
    def test_open_this_folder(self):
        test_dir = self.scratch / "test_folder_open"
        test_dir.mkdir()
        ai_engine.memory.update(last_folder=str(test_dir))

        res = ai_engine.parse_and_execute("open this folder")
        self.assertIn("Opened test_folder_open", res)

    def test_open_folder_by_name(self):
        test_dir = self.scratch / "custom_work"
        test_dir.mkdir()
        ai_engine.memory.update(last_folder=str(test_dir))

        res = ai_engine.parse_and_execute(f"open folder {test_dir}")
        self.assertIn("Opened custom_work", res)

    def test_chrome_profile_detection(self):
        prof_dir = browser_manager.get_chrome_profile_directory("Sabareesh")
        # On this system, Sabareesh is in Profile 42
        self.assertIsNotNone(prof_dir)
        self.assertIn("Profile", prof_dir)

    def test_chord_shortcut_execution(self):
        res = ai_engine.parse_and_execute("press ctrl+k ctrl+o")
        self.assertIn("CTRL+K CTRL+O", res.upper())

    def test_open_in_vscode_command(self):
        res = ai_engine.parse_and_execute("open suggested folder in vs code")
        self.assertTrue("VS Code" in res or "Code" in res)

if __name__ == "__main__":
    unittest.main()
