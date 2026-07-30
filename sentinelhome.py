from __future__ import annotations

import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from modules.event_logger import log_event
from modules.inventory import device_key, is_trusted, load_trusted_devices
from modules.live_inventory import save_live_inventory
from modules.notifier import notify_unknown_device
from modules.scanner import scan_network


NETWORK = "192.168.1.0/24"
SCAN_INTERVAL_SECONDS = 30

PROJECT_DIR = Path(__file__).resolve().parent
TRUSTED_FILE = PROJECT_DIR / "trusted_devices.json"
LOG_FILE = PROJECT_DIR / "logs" / "sentinelhome_events.jsonl"
LIVE_INVENTORY_FILE = PROJECT_DIR / "live_inventory.json"

console = Console()


def display_devices(
    devices: list[dict[str, str]],
    trusted: dict,
) -> None:
    """Display the current device inventory."""
    table = Table(title="SentinelHome Live Device Inventory")

    table.add_column("Status")
    table.add_column("Device Name")
    table.add_column("IP Address")
    table.add_column("Hostname")
    table.add_column("MAC Address")
    table.add_column("Vendor")

    for device in devices:
        mac = device["mac"]

        if is_trusted(device, trusted):
            status = "[green]TRUSTED[/green]"
            device_name = trusted[mac].get(
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


def main() -> None:
    """Run the continuous SentinelHome network monitor."""
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

    trusted_devices = load_trusted_devices(TRUSTED_FILE)

    # Prevents the same unknown device from triggering every 30 seconds.
    alerted_unknown_devices: set[str] = set()

    while True:
        try:
            devices = scan_network(NETWORK)

            # Reload trusted devices every scan so new approvals
            # take effect without restarting SentinelHome.
            trusted_devices = load_trusted_devices(
                TRUSTED_FILE
            )

            save_live_inventory(
                LIVE_INVENTORY_FILE,
                devices,
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

                if key not in alerted_unknown_devices:
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

                    alerted_unknown_devices.add(key)

            # If an unknown device disconnects, remove it from the
            # session alert set. A later reconnection triggers a new alert.
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
                "\n[bold red]"
                "Monitoring error:"
                f"[/bold red] {error}"
            )
            console.print(
                f"Retrying in "
                f"{SCAN_INTERVAL_SECONDS} seconds..."
            )
            time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()