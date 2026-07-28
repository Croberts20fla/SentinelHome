from __future__ import annotations

import json
from pathlib import Path


def load_trusted_devices(file_path: Path) -> dict:
    """Load the trusted-device inventory from JSON."""
    if not file_path.exists():
        return {}

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        print(f"[!] Could not read trusted-device inventory: {error}")
        return {}


def device_key(device: dict[str, str]) -> str:
    """
    Use the MAC address as the primary identity.

    If Nmap cannot retrieve a MAC address, use the IP address as a
    temporary fallback for the current monitoring session.
    """
    mac = device["mac"]

    if mac != "UNKNOWN":
        return mac

    return f"IP:{device['ip']}"


def is_trusted(device: dict[str, str], trusted_devices: dict) -> bool:
    """Return True when the device MAC is in the trusted inventory."""
    mac = device["mac"]
    return mac != "UNKNOWN" and mac in trusted_devices