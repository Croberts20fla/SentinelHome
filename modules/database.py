"""SQLite database functions for SentinelHome."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


def get_connection(database_file: Path) -> sqlite3.Connection:
    """Open a configured SQLite connection."""
    database_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(database_file)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database(database_file: Path) -> None:
    """Create SentinelHome database tables."""
    with get_connection(database_file) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS devices (
                device_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                hostname TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                mac_address TEXT NOT NULL,
                vendor TEXT NOT NULL,
                owner TEXT NOT NULL DEFAULT 'Unknown',
                trusted INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Unknown',
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS device_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_key TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_details TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (device_key)
                    REFERENCES devices(device_key)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS port_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_key TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                status TEXT NOT NULL,
                open_port_count INTEGER NOT NULL DEFAULT 0,
                scan_results TEXT NOT NULL DEFAULT '{}',
                scanned_at TEXT NOT NULL,
                FOREIGN KEY (device_key)
                    REFERENCES devices(device_key)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_devices_ip
                ON devices(ip_address);

            CREATE INDEX IF NOT EXISTS idx_events_device
                ON device_events(device_key);

            CREATE INDEX IF NOT EXISTS idx_events_created
                ON device_events(created_at);

            CREATE INDEX IF NOT EXISTS idx_port_scans_device
                ON port_scans(device_key);
            """
        )


def build_device_key(device: dict[str, Any]) -> str:
    """Return a stable identifier using MAC, with IP as fallback."""
    mac_address = str(
        device.get("mac", "UNKNOWN")
    ).strip().upper()

    if mac_address and mac_address != "UNKNOWN":
        return mac_address

    ip_address = str(
        device.get("ip", "UNKNOWN")
    ).strip()

    return f"IP:{ip_address}"

def upsert_device(
    database_file: Path,
    device: dict[str, Any],
    *,
    trusted: bool = False,
    name: str | None = None,
    owner: str = "Unknown",
) -> tuple[str, bool]:
    """
    Insert or update one device.

    Returns:
        A tuple containing the device key and whether this was
        the device's first database record.
    """
    now = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    device_key = build_device_key(device)

    hostname = str(
        device.get("hostname", "Unknown")
    )

    ip_address = str(
        device.get("ip", "Unknown")
    )

    mac_address = str(
        device.get("mac", "UNKNOWN")
    ).upper()

    vendor = str(
        device.get("vendor", "Unknown")
    )

    status = str(
        device.get("status", "Online")
    )

    device_name = (
        name
        or str(device.get("name", "")).strip()
        or hostname
    )

    with get_connection(database_file) as connection:
        existing_device = connection.execute(
            """
            SELECT device_key
            FROM devices
            WHERE device_key = ?
            """,
            (device_key,),
        ).fetchone()

        is_new_device = existing_device is None

        connection.execute(
            """
            INSERT INTO devices (
                device_key,
                name,
                hostname,
                ip_address,
                mac_address,
                vendor,
                owner,
                trusted,
                status,
                first_seen,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(device_key) DO UPDATE SET
                name = excluded.name,
                hostname = excluded.hostname,
                ip_address = excluded.ip_address,
                mac_address = excluded.mac_address,
                vendor = excluded.vendor,
                owner = excluded.owner,
                trusted = excluded.trusted,
                status = excluded.status,
                last_seen = excluded.last_seen
            """,
            (
                device_key,
                device_name,
                hostname,
                ip_address,
                mac_address,
                vendor,
                owner,
                int(trusted),
                status,
                now,
                now,
            ),
        )

    return device_key, is_new_device


    

def record_device_event(
    database_file: Path,
    device_key: str,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Record one device-history event."""
    created_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    event_details = json.dumps(
        details or {},
        ensure_ascii=False,
    )

    with get_connection(database_file) as connection:
        connection.execute(
            """
            INSERT INTO device_events (
                device_key,
                event_type,
                event_details,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                device_key,
                event_type,
                event_details,
                created_at,
            ),
        )


def get_database_counts(
    database_file: Path,
) -> dict[str, int]:
    """Return basic database record counts."""
    with get_connection(database_file) as connection:
        device_count = connection.execute(
            "SELECT COUNT(*) FROM devices"
        ).fetchone()[0]

        event_count = connection.execute(
            "SELECT COUNT(*) FROM device_events"
        ).fetchone()[0]

        port_scan_count = connection.execute(
            "SELECT COUNT(*) FROM port_scans"
        ).fetchone()[0]

    return {
        "devices": device_count,
        "events": event_count,
        "port_scans": port_scan_count,
    }
def find_device_key(
    database_file: Path,
    *,
    mac_address: str | None = None,
    ip_address: str | None = None,
) -> str | None:
    """Find a database device key by MAC or IP address."""
    normalized_mac = (
        mac_address.strip().upper()
        if mac_address
        else None
    )

    with get_connection(database_file) as connection:
        if normalized_mac and normalized_mac != "UNKNOWN":
            row = connection.execute(
                """
                SELECT device_key
                FROM devices
                WHERE mac_address = ?
                """,
                (normalized_mac,),
            ).fetchone()

            if row:
                return str(row["device_key"])

        if ip_address:
            row = connection.execute(
                """
                SELECT device_key
                FROM devices
                WHERE ip_address = ?
                """,
                (ip_address,),
            ).fetchone()

            if row:
                return str(row["device_key"])

    return None


def update_device_management(
    database_file: Path,
    device_key: str,
    *,
    trusted: bool | None = None,
    name: str | None = None,
    owner: str | None = None,
) -> bool:
    """Update a device's trust, name, or owner fields."""
    updates: list[str] = []
    values: list[Any] = []

    if trusted is not None:
        updates.append("trusted = ?")
        values.append(int(trusted))

    if name is not None and name.strip():
        updates.append("name = ?")
        values.append(name.strip())

    if owner is not None and owner.strip():
        updates.append("owner = ?")
        values.append(owner.strip())

    if not updates:
        return False

    values.append(device_key)

    with get_connection(database_file) as connection:
        cursor = connection.execute(
            f"""
            UPDATE devices
            SET {", ".join(updates)}
            WHERE device_key = ?
            """,
            values,
        )

    return cursor.rowcount > 0


def save_port_scan_to_database(
    database_file: Path,
    device_key: str,
    scan_result: dict[str, Any],
) -> None:
    """Save a completed port scan in SQLite."""
    open_ports = scan_result.get("open_ports", [])

    with get_connection(database_file) as connection:
        connection.execute(
            """
            INSERT INTO port_scans (
                device_key,
                ip_address,
                status,
                open_port_count,
                scan_results,
                scanned_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                device_key,
                str(scan_result.get("ip", "Unknown")),
                str(scan_result.get("status", "Unknown")),
                len(open_ports),
                json.dumps(scan_result),
                str(scan_result.get("scanned_at", "")),
            ),
        )


def get_device_timeline(
    database_file: Path,
    device_key: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Return recent events for one device."""
    with get_connection(database_file) as connection:
        rows = connection.execute(
            """
            SELECT
                event_type,
                event_details,
                created_at
            FROM device_events
            WHERE device_key = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (
                device_key,
                limit,
            ),
        ).fetchall()

    events: list[dict[str, Any]] = []

    for row in rows:
        try:
            details = json.loads(row["event_details"])
        except json.JSONDecodeError:
            details = {}

        created_at = str(row["created_at"])

        try:
            display_time = datetime.fromisoformat(
                created_at
            ).strftime("%b %d, %Y %I:%M:%S %p")
        except ValueError:
            display_time = created_at

        events.append(
            {
                "event_type": str(row["event_type"])
                .replace("_", " ")
                .title(),
                "display_time": display_time,
                "hostname": details.get(
                    "hostname",
                    "Unknown",
                ),
                "ip": details.get(
                    "ip",
                    "Unknown",
                ),
                "mac": details.get(
                    "mac",
                    "UNKNOWN",
                ),
                "details": details,
            }
        )

    return events