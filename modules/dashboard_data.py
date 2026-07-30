"""Data-loading and formatting functions for the SentinelHome dashboard."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
TRUSTED_DEVICES_FILE = BASE_DIR / "trusted_devices.json"
EVENT_LOG_FILE = BASE_DIR / "logs" / "sentinelhome_events.jsonl"
LIVE_INVENTORY_FILE = BASE_DIR / "live_inventory.json"


def load_json_file(
    file_path: Path,
    default: Any,
) -> Any:
    """Load a JSON file and return a safe default if it cannot be read."""
    if not file_path.exists():
        return default

    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def load_trusted_devices() -> dict[str, dict[str, str]]:
    """Load the trusted-device inventory."""
    data = load_json_file(TRUSTED_DEVICES_FILE, {})

    if not isinstance(data, dict):
        return {}

    return data


def load_live_inventory() -> list[dict[str, Any]]:
    """Load the latest live network inventory."""
    data = load_json_file(LIVE_INVENTORY_FILE, [])

    if not isinstance(data, list):
        return []

    return data


def load_events() -> list[dict[str, Any]]:
    """Load valid JSON records from the SentinelHome JSONL event log."""
    if not EVENT_LOG_FILE.exists():
        return []

    events: list[dict[str, Any]] = []

    try:
        with EVENT_LOG_FILE.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if isinstance(event, dict):
                    events.append(event)

    except OSError:
        return []

    return events


def format_timestamp(timestamp: str) -> str:
    """Convert an ISO timestamp into a readable local time."""
    if not timestamp:
        return "No activity"

    try:
        parsed_time = datetime.fromisoformat(timestamp)
        return parsed_time.strftime("%b %d, %Y %I:%M:%S %p")
    except ValueError:
        return timestamp


def prepare_recent_events(
    events: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, str]]:
    """Prepare recent event records for display in the dashboard."""
    prepared_events: list[dict[str, str]] = []

    for event in reversed(events[-limit:]):
        device = event.get("device", {})

        if not isinstance(device, dict):
            device = {}

        prepared_events.append(
            {
                "display_time": format_timestamp(
                    str(event.get("timestamp", ""))
                ),
                "event_type": str(
                    event.get("event_type", "unknown_event")
                )
                .replace("_", " ")
                .title(),
                "hostname": str(device.get("hostname", "Unknown")),
                "ip": str(device.get("ip", "Unknown")),
                "mac": str(device.get("mac", "Unknown")),
            }
        )

    return prepared_events


def prepare_inventory(
    inventory: list[dict[str, Any]],
    trusted_devices: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    """Prepare live inventory records for dashboard display."""
    prepared_inventory: list[dict[str, Any]] = []

    for device in inventory:
        mac = str(device.get("mac", "UNKNOWN")).upper()
        trusted_record = trusted_devices.get(mac, {})
        trusted = mac != "UNKNOWN" and mac in trusted_devices

        prepared_inventory.append(
            {
                "name": trusted_record.get(
                    "name",
                    device.get("hostname", "Unknown Device"),
                ),
                "hostname": str(device.get("hostname", "Unknown")),
                "ip": str(device.get("ip", "Unknown")),
                "mac": mac,
                "vendor": trusted_record.get(
                    "vendor",
                    device.get("vendor", "Unknown"),
                ),
                "trusted": trusted,
                "status": str(device.get("status", "Online")),
                "last_seen": format_timestamp(
                    str(device.get("last_seen", ""))
                ),
            }
        )

    return prepared_inventory


def build_dashboard_data() -> dict[str, Any]:
    """Build the complete data package used by the Flask dashboard."""
    trusted_devices = load_trusted_devices()
    events = load_events()
    live_inventory = load_live_inventory()

    unknown_events = [
        event
        for event in events
        if event.get("event_type") == "unknown_device_detected"
    ]

    prepared_inventory = prepare_inventory(
        live_inventory,
        trusted_devices,
    )

    online_devices = [
        device
        for device in prepared_inventory
        if device["status"].lower() == "online"
    ]

    trusted_online = [
        device
        for device in online_devices
        if device["trusted"]
    ]

    unknown_online = [
        device
        for device in online_devices
        if not device["trusted"]
    ]

    last_activity = (
        format_timestamp(str(events[-1].get("timestamp", "")))
        if events
        else "No activity"
    )

    latest_unknown = (
        prepare_recent_events(unknown_events, limit=1)[0]
        if unknown_events
        else None
    )

    return {
        "monitoring_status": "Monitoring",
        "trusted_count": len(trusted_devices),
        "devices_online": len(online_devices),
        "trusted_online": len(trusted_online),
        "unknown_online": len(unknown_online),
        "unknown_alert_count": len(unknown_events),
        "total_events": len(events),
        "last_activity": last_activity,
        "latest_unknown": latest_unknown,
        "recent_events": prepare_recent_events(events),
        "live_inventory": prepared_inventory,
    }