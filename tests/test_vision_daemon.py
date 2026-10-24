"""Unit tests for ZYRA Screen Vision and Background Daemon."""
import unittest
import os
import shutil
from pathlib import Path

from zyra.vision_manager import vision_manager
from zyra.daemon import ZyraDaemon, re_strip_wake
from zyra.ai_engine import ai_engine

class TestVisionAndDaemon(unittest.TestCase):
    def setUp(self):
        self.daemon = ZyraDaemon()

    def test_daemon_greeting(self):
        greeting = self.daemon.get_greeting()
        self.assertIn("FRIDAY", greeting)
        self.assertIn("sir", greeting)
        self.assertTrue(any(t in greeting for t in ("Good morning", "Good afternoon", "Good evening")))

    def test_strip_wake_phrase(self):
        self.assertEqual(re_strip_wake("Hey Friday open Notepad"), "open Notepad")
        self.assertEqual(re_strip_wake("friday, what is my ram"), "what is my ram")
        self.assertEqual(re_strip_wake("Hey Zyra open Notepad"), "open Notepad")
        self.assertEqual(re_strip_wake("open VS Code"), "open VS Code")

    def test_capture_screenshot(self):
        img_path = vision_manager.capture_screenshot("test_screen.jpg")
        self.assertIsNotNone(img_path)
        self.assertTrue(os.path.exists(img_path))
        # Clean up test screenshot
        try:
            os.remove(img_path)
        except Exception:
            pass

    def test_analyze_screen(self):
        ans, path = vision_manager.analyze_screen("look at my screen")
        self.assertIn("inspected your screen", ans)
        self.assertIsNotNone(path)

    def test_ai_engine_vision_routing(self):
        res = ai_engine.parse_and_execute("look at my screen and tell me what is the error")
        self.assertIn("inspected your screen", res)

if __name__ == "__main__":
    unittest.main()
