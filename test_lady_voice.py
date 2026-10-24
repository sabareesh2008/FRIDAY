"""Quick test script to hear FRIDAY's lady voice speak aloud immediately."""
import time
from zyra.tts_engine import tts_engine

if __name__ == "__main__":
    print("Testing FRIDAY lady voice speech...")
    tts_engine.speak("Good evening, sir! FRIDAY is online and my voice engine is working perfectly.")
    time.sleep(4)
    print("Done!")
