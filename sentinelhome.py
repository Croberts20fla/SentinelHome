"""SentinelHome live network monitor."""

from __future__ import annotations

import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from modules.database import (
    initialize_database,
    record_device_event,
    upsert_device,
)
from modules.event_logger import log_event
from modules.inventory import (
    device_key,
    is_trusted,
    load_trusted_devices,
)
from modules.live_inventory import save_live_inventory
from modules.notifier import notify_unknown_device
from modules.scanner import scan_network


NETWORK = "192.168.1.0/24"
SCAN_INTERVAL_SECONDS = 30

PROJECT_DIR = Path(__file__).resolve().parent

TRUSTED_FILE = PROJECT_DIR / "trusted_devices.json"
LOG_FILE = (
    PROJECT_DIR
    / "logs"
    / "sentinelhome_events.jsonl"
)
LIVE_INVENTORY_FILE = (
    PROJECT_DIR
    / "live_inventory.json"
)
DATABASE_FILE = (
    PROJECT_DIR
    / "data"
    / "sentinelhome.db"
)

console = Console()


def display_devices(
    devices: list[dict[str, str]],
    trusted_devices: dict,
) -> None:
    """Display the current network inventory."""
    table = Table(
        title="SentinelHome Live Device Inventory"
    )

    table.add_column("Status")
    table.add_column("Device Name")
    table.add_column("IP Address")
    table.add_column("Hostname")
    table.add_column("MAC Address")
    table.add_column("Vendor")

    for device in devices:
        mac = device["mac"]

        if is_trusted(device, trusted_devices):
            status = "[green]TRUSTED[/green]"

            trusted_record = trusted_devices.get(
                mac,
                {},
            )

            device_name = trusted_record.get(
                "name",
                device["hostname"],
            )
        else:
            status = "[bold red]UNKNOWN[/bold red]"
            device_name = "Unapproved"

        table.add_row(
            status,
            device_name,
            device["ip"],
            device["hostname"],
            mac,
            device["vendor"],
        )

    console.print(table)


def save_devices_to_database(
    devices: list[dict[str, str]],
    trusted_devices: dict,
) -> None:
    """Save the current scan into SQLite."""
    for device in devices:
        mac = device["mac"]

        trusted = is_trusted(
            device,
            trusted_devices,
        )

        trusted_record = trusted_devices.get(
            mac,
            {},
        )

        if trusted:
            device_name = trusted_record.get(
                "name",
                device["hostname"],
            )

            owner = trusted_record.get(
                "owner",
                "Unknown",
            )
        else:
            device_name = device["hostname"]
            owner = "Unknown"

        database_device = {
            **device,
            "status": "Online",
        }

        database_key, is_new_device = upsert_device(
            DATABASE_FILE,
            database_device,
            trusted=trusted,
            name=device_name,
            owner=owner,
        )

        if is_new_device:
            record_device_event(
                DATABASE_FILE,
                database_key,
                "device_discovered",
                {
                    "ip": device["ip"],
                    "hostname": device["hostname"],
                    "mac": device["mac"],
                    "vendor": device["vendor"],
                    "trusted": trusted,
                },
            )


def main() -> None:
    """Start SentinelHome network monitoring."""
    initialize_database(DATABASE_FILE)

    console.print(
        "[bold cyan]SentinelHome Live Monitor[/bold cyan]"
    )

    console.print(
        f"Scanning [bold]{NETWORK}[/bold] every "
        f"[bold]{SCAN_INTERVAL_SECONDS} seconds[/bold]."
    )

    console.print(
        "Press [bold]Ctrl + C[/bold] to stop.\n"
    )

    alerted_unknown_devices: set[str] = set()

    while True:
        try:
            devices = scan_network(NETWORK)

            trusted_devices = load_trusted_devices(
                TRUSTED_FILE
            )

            save_live_inventory(
                LIVE_INVENTORY_FILE,
                devices,
            )

            save_devices_to_database(
                devices,
                trusted_devices,
            )

            console.clear()

            display_devices(
                devices,
                trusted_devices,
            )

            current_unknown_keys: set[str] = set()

            for device in devices:
                if is_trusted(
                    device,
                    trusted_devices,
                ):
                    continue

                key = device_key(device)
                current_unknown_keys.add(key)

                if key in alerted_unknown_devices:
                    continue

                console.print(
                    "\n[bold red]"
                    "UNKNOWN DEVICE DETECTED"
                    "[/bold red]\n"
                    f"Hostname: {device['hostname']}\n"
                    f"IP: {device['ip']}\n"
                    f"MAC: {device['mac']}\n"
                    f"Vendor: {device['vendor']}\n"
                )

                notify_unknown_device(device)

                log_event(
                    LOG_FILE,
                    "unknown_device_detected",
                    device,
                )

                database_key, _ = upsert_device(
                    DATABASE_FILE,
                    {
                        **device,
                        "status": "Online",
                    },
                    trusted=False,
                    name=device["hostname"],
                    owner="Unknown",
                )

                record_device_event(
                    DATABASE_FILE,
                    database_key,
                    "unknown_device_detected",
                    {
                        "ip": device["ip"],
                        "hostname": device["hostname"],
                        "mac": device["mac"],
                        "vendor": device["vendor"],
                    },
                )

                alerted_unknown_devices.add(key)

            alerted_unknown_devices.intersection_update(
                current_unknown_keys
            )

            console.print(
                f"\nNext scan in "
                f"{SCAN_INTERVAL_SECONDS} seconds. "
                "Press Ctrl + C to stop."
            )

            time.sleep(SCAN_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            console.print(
                "\n[yellow]"
                "SentinelHome monitoring stopped."
                "[/yellow]"
            )
            break

        except Exception as error:
            console.print(
                "\n[bold red]Monitoring error:"
                f"[/bold red] {error}"
            )

            console.print(
                f"Retrying in "
                f"{SCAN_INTERVAL_SECONDS} seconds..."
            )

            time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()