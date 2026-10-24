"""Unit tests for FRIDAY Lady Voice TTS Engine."""
import unittest
from zyra.tts_engine import tts_engine, TTSEngine

class TestTTSEngine(unittest.TestCase):
    def test_format_speech_text_adds_sir(self):
        # Confirmation statement
        res = TTSEngine.format_speech_text("Opened VS Code for you", "sir")
        self.assertEqual(res, "Opened VS Code for you, sir.")

        # Wake query response
        res2 = TTSEngine.format_speech_text("yes?", "sir")
        self.assertEqual(res2, "Yes, sir? How can I help you?")

        # Goodbye response
        res3 = TTSEngine.format_speech_text("goodbye!", "sir")
        self.assertEqual(res3, "Goodbye, sir. Have a great day.")

        # Statement that already includes "sir"
        res4 = TTSEngine.format_speech_text("Good evening, sir! Ready.", "sir")
        self.assertEqual(res4, "Good evening, sir! Ready.")

    def test_speech_queue_put(self):
        tts_engine.speak("Test speech item")
        self.assertFalse(tts_engine.speech_queue.empty())
        tts_engine.stop()

if __name__ == "__main__":
    unittest.main()
