"""Unit tests for FRIDAY Autonomous Screen Operator & Custom Commands."""
import unittest
from zyra.ai_engine import ai_engine
from zyra.planner import planner
from zyra.screen_operator import screen_operator
from zyra.companion import companion_engine

class TestScreenOperator(unittest.TestCase):

    def test_multi_step_double_dot_splitting(self):
        cmd = "open chrome.. click sabareesh mail id.. search this.. open this link.. click this"
        self.assertTrue(planner.is_multi_step(cmd))
        steps = planner.split_steps(cmd)
        self.assertEqual(len(steps), 5)
        self.assertEqual(steps[0], "open chrome")
        self.assertEqual(steps[1], "click sabareesh mail id")
        self.assertEqual(steps[2], "search this")
        self.assertEqual(steps[3], "open this link")
        self.assertEqual(steps[4], "click this")

    def test_click_command_parsing(self):
        res = ai_engine.parse_and_execute("click 100, 200")
        self.assertIn("Clicked at coordinates (100, 200)", res)

    def test_type_command_parsing(self):
        res = ai_engine.parse_and_execute("type hello world and enter")
        self.assertIn("Typed 'hello world' and pressed Enter", res)

        res2 = ai_engine.parse_and_execute("write test text")
        self.assertIn("Typed 'test text'", res2)

    def test_press_key_command(self):
        res = ai_engine.parse_and_execute("press enter")
        self.assertIn("Pressed ENTER", res)

        res2 = ai_engine.parse_and_execute("hit ctrl+t")
        self.assertIn("Pressed CTRL + T", res2)

    def test_scroll_command(self):
        res = ai_engine.parse_and_execute("scroll down")
        self.assertIn("Scrolled down", res)

    def test_download_intent(self):
        res = ai_engine.parse_and_execute("download the file")
        self.assertTrue("download" in res.lower() or "save" in res.lower())

    def test_companion_chit_chat(self):
        res = ai_engine.parse_and_execute("how are you")
        self.assertIn("sir", res.lower())

        res2 = ai_engine.parse_and_execute("who are you")
        self.assertIn("friday", res2.lower())
        self.assertIn("sir", res2.lower())

if __name__ == "__main__":
    unittest.main()
