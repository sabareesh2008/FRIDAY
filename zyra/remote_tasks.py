"""Secure Remote Task Queue and Wake-on-LAN Manager for ZYRA/FRIDAY."""
import os
import json
import time
import socket
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from zyra.config import config

class RemoteTaskManager:
    def __init__(self):
        self._queue_file = Path.home() / ".zyra" / "task_queue.json"
        self._queue_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_queue(self) -> List[Dict[str, Any]]:
        if not self._queue_file.exists():
            return []
        try:
            with open(self._queue_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_queue(self, queue: List[Dict[str, Any]]):
        try:
            with open(self._queue_file, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=2)
        except Exception:
            pass

    def queue_task(self, command: str, requires_local: bool = True) -> str:
        """Enqueues a task to run when the laptop/desktop is awake and connected."""
        user_title = config.get("user_title", "sir")
        queue = self._load_queue()
        task = {
            "id": f"task_{int(time.time())}_{len(queue)+1}",
            "command": command.strip(),
            "requires_local": requires_local,
            "created_at": time.time(),
            "status": "QUEUED"
        }
        queue.append(task)
        self._save_queue(queue)
        return f"Enqueued task: '{command}'. It will execute automatically when your laptop is active, {user_title}."

    def list_queued_tasks(self) -> List[Dict[str, Any]]:
        return self._load_queue()

    def process_pending_tasks(self, executor: Callable[[str], str]) -> List[str]:
        """Runs all queued tasks when the assistant reconnects."""
        queue = self._load_queue()
        if not queue:
            return []

        results = []
        remaining = []
        for task in queue:
            try:
                res = executor(task["command"])
                results.append(f"Completed queued task '{task['command']}': {res}")
            except Exception as exc:
                results.append(f"Failed queued task '{task['command']}': {exc}")

        # Clear executed tasks
        self._save_queue(remaining)
        return results

    @staticmethod
    def send_wake_on_lan(mac_address: str, broadcast_ip: str = "255.255.255.255", port: int = 9) -> str:
        """Sends a standard UDP Wake-on-LAN magic packet to wake supported hardware on LAN."""
        clean_mac = mac_address.replace(":", "").replace("-", "").strip()
        if len(clean_mac) != 12:
            return f"Invalid MAC address format: '{mac_address}'. Format should be XX:XX:XX:XX:XX:XX."

        try:
            mac_bytes = bytes.fromhex(clean_mac)
            # Magic packet: 6 bytes of 0xFF followed by 16 repetitions of MAC address
            magic_packet = b"\xff" * 6 + mac_bytes * 16

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(magic_packet, (broadcast_ip, port))

            return (
                f"Sent Wake-on-LAN magic packet to {mac_address} via {broadcast_ip}:{port}.\n"
                f"Note: Wake-on-LAN requires Motherboard BIOS/UEFI and Network Card WOL support to be enabled."
            )
        except Exception as exc:
            return f"Failed to send Wake-on-LAN packet: {exc}"

remote_tasks = RemoteTaskManager()
