"""Autonomous System Query Agent for ZYRA: Dynamic hardware, battery, RAM, CPU, and network answers."""
import subprocess
import shutil
import re
from typing import Optional

class SystemQueryAgent:
    @staticmethod
    def is_system_query(command: str) -> bool:
        lower = command.lower()
        triggers = (
            "battery", "ram usage", "free ram", "total ram", "how much ram",
            "cpu usage", "what cpu", "processor", "disk space", "free space",
            "ip address", "my ip", "windows version", "os version", "running processes"
        )
        return any(t in lower for t in triggers)

    def execute_query(self, command: str) -> str:
        lower = command.lower()

        # 1. RAM / Memory
        if "ram" in lower or "memory" in lower:
            ps_cmd = 'Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ConvertTo-Json'
            data = self._run_ps_json(ps_cmd)
            if data:
                total_gb = round(data.get("TotalVisibleMemorySize", 0) / (1024 * 1024), 2)
                free_gb = round(data.get("FreePhysicalMemory", 0) / (1024 * 1024), 2)
                used_gb = round(total_gb - free_gb, 2)
                pct_used = round((used_gb / max(total_gb, 1)) * 100, 1)
                return f"Memory Status: You have {total_gb} GB total RAM. Currently {used_gb} GB used ({pct_used}%), with {free_gb} GB free."

        # 2. Battery
        if "battery" in lower or "charge" in lower:
            ps_cmd = 'Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus | ConvertTo-Json'
            data = self._run_ps_json(ps_cmd)
            if data and "EstimatedChargeRemaining" in data:
                pct = data["EstimatedChargeRemaining"]
                return f"Battery Status: Your PC is currently at {pct}% battery charge."
            return "Battery Status: No active battery detected (system may be a desktop running on AC power)."

        # 3. CPU
        if "cpu" in lower or "processor" in lower:
            ps_cmd = 'Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | ConvertTo-Json'
            data = self._run_ps_json(ps_cmd)
            if data:
                name = data.get("Name", "Unknown CPU").strip()
                cores = data.get("NumberOfCores", 0)
                threads = data.get("NumberOfLogicalProcessors", 0)
                return f"CPU: {name} with {cores} cores and {threads} logical threads."

        # 4. Disk Space
        if "disk" in lower or "storage" in lower or "space" in lower:
            ps_cmd = 'Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | Select-Object DeviceID, Size, FreeSpace | ConvertTo-Json'
            res = self._run_ps(ps_cmd)
            try:
                import json
                items = json.loads(res)
                if isinstance(items, dict): items = [items]
                summaries = []
                for d in items:
                    drive = d.get("DeviceID", "Drive")
                    size_gb = round(d.get("Size", 0) / (1024**3), 1)
                    free_gb = round(d.get("FreeSpace", 0) / (1024**3), 1)
                    summaries.append(f"{drive} has {free_gb} GB free out of {size_gb} GB")
                return "Storage Status: " + ", ".join(summaries) + "."
            except Exception:
                pass

        # 5. IP Address
        if "ip" in lower or "network" in lower:
            ps_cmd = "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike '169.254*' }).IPAddress"
            ip = self._run_ps(ps_cmd).strip().splitlines()
            if ip:
                return f"Your local IP address is: {ip[0].strip()}."
            return "Could not determine local IP address."

        # 6. Windows Version
        if "windows" in lower or "os" in lower or "version" in lower:
            ps_cmd = "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').DisplayVersion"
            ver = self._run_ps(ps_cmd).strip()
            ps_build = "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').CurrentBuild"
            build = self._run_ps(ps_build).strip()
            return f"Windows Version: Windows 11/10 version {ver or 'release'} (Build {build})."

        return "I could not retrieve that system metric right now."

    @staticmethod
    def _run_ps(cmd: str) -> str:
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=5
            )
            return res.stdout.strip()
        except Exception:
            return ""

    @classmethod
    def _run_ps_json(cls, cmd: str) -> Optional[dict]:
        output = cls._run_ps(cmd)
        if not output:
            return None
        try:
            import json
            data = json.loads(output)
            return data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else None)
        except Exception:
            return None

system_agent = SystemQueryAgent()
