from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def log_event(
    log_file: Path,
    event_type: str,
    device: dict[str, str],
) -> None:
    """Write one JSON event per line to the SentinelHome log."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "event_type": event_type,
        "device": device,
    }

    with log_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")