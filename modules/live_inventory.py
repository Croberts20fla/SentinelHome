"""Functions for saving the latest SentinelHome network inventory."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def save_live_inventory(
    file_path: Path,
    devices: list[dict[str, str]],
) -> None:
    """Safely save the latest network scan as JSON."""
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    inventory: list[dict[str, Any]] = []

    for device in devices:
        inventory.append(
            {
                "ip": device.get("ip", "Unknown"),
                "hostname": device.get("hostname", "Unknown"),
                "mac": device.get("mac", "UNKNOWN").upper(),
                "vendor": device.get("vendor", "Unknown"),
                "status": "Online",
                "last_seen": timestamp,
            }
        )

    file_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = file_path.with_suffix(".tmp")

    temporary_file.write_text(
        json.dumps(inventory, indent=4),
        encoding="utf-8",
    )

    temporary_file.replace(file_path)