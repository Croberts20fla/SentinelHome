"""Manage SentinelHome trusted-device records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_trusted_devices(
    file_path: Path,
) -> dict[str, dict[str, str]]:
    """Load trusted devices from JSON."""
    if not file_path.exists():
        return {}

    try:
        data = json.loads(
            file_path.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def save_trusted_devices(
    file_path: Path,
    trusted_devices: dict[str, dict[str, str]],
) -> None:
    """Safely save trusted-device records to JSON."""
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = file_path.with_suffix(".tmp")

    temporary_file.write_text(
        json.dumps(
            trusted_devices,
            indent=4,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    temporary_file.replace(file_path)


def approve_device(
    file_path: Path,
    device: dict[str, Any],
    name: str | None = None,
    owner: str = "Unknown",
) -> bool:
    """Add a device to the trusted inventory."""
    mac = str(
        device.get("mac", "UNKNOWN")
    ).upper()

    if mac == "UNKNOWN":
        return False

    trusted_devices = load_trusted_devices(
        file_path
    )

    hostname = str(
        device.get("hostname", "Unknown Device")
    )

    vendor = str(
        device.get("vendor", "Unknown")
    )

    trusted_devices[mac] = {
        "name": name or hostname,
        "vendor": vendor,
        "owner": owner,
    }

    save_trusted_devices(
        file_path,
        trusted_devices,
    )

    return True

def rename_trusted_device(
    file_path: Path,
    mac: str,
    new_name: str,
) -> bool:
    """Rename a device in the trusted inventory."""
    normalized_mac = mac.upper()
    cleaned_name = new_name.strip()

    if not cleaned_name:
        return False

    trusted_devices = load_trusted_devices(file_path)

    if normalized_mac not in trusted_devices:
        return False

    trusted_devices[normalized_mac]["name"] = cleaned_name

    save_trusted_devices(
        file_path,
        trusted_devices,
    )

    return True


def remove_trusted_device(
    file_path: Path,
    mac: str,
) -> bool:
    """Remove a device from the trusted inventory."""
    normalized_mac = mac.upper()

    trusted_devices = load_trusted_devices(
        file_path
    )

    if normalized_mac not in trusted_devices:
        return False

    del trusted_devices[normalized_mac]

    save_trusted_devices(
        file_path,
        trusted_devices,
    )

    return True