"""ZYRA Background Daemon Entry Point — Silent background boot with hands-free 'Hey ZYRA' wake-word."""
import sys
from zyra.daemon import daemon_instance

if __name__ == "__main__":
    try:
        daemon_instance.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
