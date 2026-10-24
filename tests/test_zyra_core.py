"""Comprehensive unit and integration test suite for ZYRA upgrade."""
import unittest
import os
import shutil
from pathlib import Path

from zyra.config import config
from zyra.safety import safety_guard
from zyra.windows_manager import windows_manager
from zyra.browser_manager import browser_manager
from zyra.file_manager import file_manager
from zyra.media_finder import media_finder, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS
from zyra.planner import planner
from zyra.ai_engine import ai_engine
from zyra.startup import startup_manager

class TestZyraUpgrade(unittest.TestCase):

    def setUp(self):
        # Clean safety guard state
        safety_guard._pending_action = None
        self.test_dir = Path(__file__).resolve().parent / "test_scratch"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        safety_guard._pending_action = None
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. AI Command Understanding & Context
    def test_wake_word_stripping(self):
        self.assertEqual(ai_engine.strip_wake_words("Hey Friday open Notepad"), "open Notepad")
        self.assertEqual(ai_engine.strip_wake_words("friday, close window"), "close window")
        self.assertEqual(ai_engine.strip_wake_words("Hey Zyra open Notepad"), "open Notepad")
        self.assertEqual(ai_engine.strip_wake_words("open Notepad"), "open Notepad")

    def test_pronoun_resolution(self):
        ai_engine.memory.update(last_app="Notepad", last_window="Notepad")
        resolved = ai_engine.resolve_pronouns("it")
        self.assertEqual(resolved, "Notepad")

    # 2. Windows Control & App Discovery
    def test_app_discovery_cache(self):
        self.assertIn("notepad", windows_manager._apps_cache)
        self.assertIn("calc", windows_manager._apps_cache)
        path = windows_manager.find_app_path("notepad")
        self.assertIsNotNone(path)

    # 3. Browser Control
    def test_browser_tab_actions(self):
        res = browser_manager.tab_action("new tab")
        self.assertIn("tab", res.lower())

    def test_web_search_urls(self):
        res = browser_manager.web_search("google", "python coding")
        self.assertIn("Searching Google", res)

    # 4. File Management
    def test_file_create_and_delete(self):
        test_file = self.test_dir / "sample.txt"
        create_res = file_manager.create_file(str(test_file), "Hello ZYRA")
        self.assertTrue(test_file.exists())
        self.assertIn("Created file", create_res)

        # Safe delete with confirmation staged
        del_prompt = file_manager.delete_item(str(test_file), require_confirm=True)
        self.assertIn("[CONFIRMATION REQUIRED]", del_prompt)
        self.assertTrue(safety_guard.has_pending)

        # Confirm deletion
        confirm_res = safety_guard.confirm()
        self.assertFalse(test_file.exists())
        self.assertIn("Recycle Bin", confirm_res)

    def test_file_organize(self):
        (self.test_dir / "pic.png").write_text("fake image")
        (self.test_dir / "doc.pdf").write_text("fake pdf")
        res = file_manager.organize_directory(str(self.test_dir))
        self.assertIn("categorized 2 file(s)", res)
        self.assertTrue((self.test_dir / "Images" / "pic.png").exists())
        self.assertTrue((self.test_dir / "Documents" / "doc.pdf").exists())

    # 5. Multi-step Planning
    def test_multi_step_splitting(self):
        cmd = "open Notepad and then open Calculator and show desktop"
        self.assertTrue(planner.is_multi_step(cmd))
        steps = planner.split_steps(cmd)
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0], "open Notepad")
        self.assertEqual(steps[1], "open Calculator")
        self.assertEqual(steps[2], "show desktop")

    # 6. Safety & Confirmation Guardrails
    def test_safety_guard_cancel(self):
        safety_guard.request_confirmation("test_action", "test destructive action", lambda: "Executed")
        self.assertTrue(safety_guard.has_pending)
        cancel_res = ai_engine.parse_and_execute("cancel")
        self.assertIn("Cancelled", cancel_res)
        self.assertFalse(safety_guard.has_pending)

    def test_power_action_protection(self):
        res = windows_manager.shutdown_pc()
        self.assertIn("[CONFIRMATION REQUIRED]", res)
        self.assertTrue(safety_guard.has_pending)
        # Abort it immediately
        safety_guard.cancel()

    # 7. Preserved Media Finder
    def test_media_extensions(self):
        self.assertIn(".mp4", VIDEO_EXTENSIONS)
        self.assertIn(".mkv", VIDEO_EXTENSIONS)
        self.assertIn(".mp3", AUDIO_EXTENSIONS)

    def test_media_name_cleaning(self):
        raw = "Avatar.2009.1080p.BluRay.x264.mp4"
        cleaned = media_finder._clean_name(raw)
        self.assertEqual(cleaned, "avatar 2009")

    # 8. Startup Manager
    def test_startup_command(self):
        cmd = startup_manager.get_run_command()
        self.assertTrue(len(cmd) > 0)

    # 9. Additional Intent & Edge Cases
    def test_quit_signal(self):
        self.assertEqual(ai_engine.parse_and_execute("exit"), "QUIT_SIGNAL")
        self.assertEqual(ai_engine.parse_and_execute("quit"), "QUIT_SIGNAL")
        self.assertEqual(ai_engine.parse_and_execute("goodbye zyra"), "QUIT_SIGNAL")

    def test_critical_path_protection(self):
        res = file_manager.delete_item("C:\\Windows\\System32")
        self.assertIn("Refused to delete system critical path", res)

    def test_file_rename_and_move(self):
        f1 = self.test_dir / "orig.txt"
        f1.write_text("orig content")
        file_manager.rename_item(str(f1), "renamed.txt")
        self.assertFalse(f1.exists())
        renamed = self.test_dir / "renamed.txt"
        self.assertTrue(renamed.exists())

        sub = self.test_dir / "subfolder"
        sub.mkdir()
        file_manager.move_item(str(renamed), str(sub))
        self.assertFalse(renamed.exists())
        self.assertTrue((sub / "renamed.txt").exists())

    def test_web_search_providers(self):
        yt_res = browser_manager.web_search("youtube", "lofi beats")
        self.assertIn("Searching Youtube", yt_res)
        gh_res = browser_manager.web_search("github", "python")
        self.assertIn("Searching Github", gh_res)

    def test_open_camera_no_movie(self):
        # "open camera" must target the camera app, never media finder
        res = ai_engine.parse_and_execute("open camera")
        self.assertTrue("camera" in res.lower() or "launching" in res.lower())
        self.assertNotIn("Opening", res)  # Media finder uses "Opening <file> in your default player"
        self.assertNotIn("movie", res.lower())

    def test_open_youtube_no_movie(self):
        # "open you tube" and "open youtube" must open the website, never media finder
        res1 = ai_engine.parse_and_execute("open you tube")
        self.assertIn("youtube.com", res1.lower())
        self.assertNotIn("movie", res1.lower())

        res2 = ai_engine.parse_and_execute("open youtube")
        self.assertIn("youtube.com", res2.lower())
        self.assertNotIn("movie", res2.lower())

    def test_generic_open_never_falls_back_to_movie(self):
        # Opening an unknown app should say it couldn't find the app, NOT search or play a movie
        res = ai_engine.parse_and_execute("open completely_unknown_software_999")
        self.assertIn("couldn't find", res.lower())
        self.assertNotIn("default player", res.lower())

    def test_multi_step_planner_execution(self):
        # A plan with two safe non-destructive steps
        cmd = "create folder " + str(self.test_dir / "step1") + " and then create folder " + str(self.test_dir / "step2")
        res = planner.execute_plan(cmd, ai_engine.parse_and_execute)
        self.assertIn("Step 1", res)
        self.assertIn("Step 2", res)
        self.assertTrue((self.test_dir / "step1").exists())
        self.assertTrue((self.test_dir / "step2").exists())

if __name__ == "__main__":
    unittest.main()
