import json
from pathlib import Path

import nmap
from rich.console import Console
from rich.table import Table

NETWORK = "192.168.1.0/24"
TRUSTED_FILE = Path(r"C:\SentinelHome\trusted_devices.json")

console = Console()


def load_trusted_devices() -> dict:
    if not TRUSTED_FILE.exists():
        return {}

    try:
        return json.loads(TRUSTED_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        console.print("[red]Trusted-device file could not be read. Starting empty.[/red]")
        return {}


def save_trusted_devices(devices: dict) -> None:
    TRUSTED_FILE.write_text(
        json.dumps(devices, indent=4),
        encoding="utf-8"
    )


def scan_network() -> list[dict]:
    scanner = nmap.PortScanner()
    scanner.scan(hosts=NETWORK, arguments="-sn")

    devices = []

    for host in scanner.all_hosts():
        addresses = scanner[host].get("addresses", {})
        mac = addresses.get("mac", "Unknown").upper()

        vendor_data = scanner[host].get("vendor", {})
        vendor = vendor_data.get(mac, "Unknown")

        devices.append(
            {
                "ip": host,
                "hostname": scanner[host].hostname() or "Unknown",
                "mac": mac,
                "vendor": vendor,
            }
        )

    return devices


def main() -> None:
    console.print("[bold cyan]SentinelHome[/bold cyan]")
    console.print("[+] Scanning your home network...\n")

    trusted = load_trusted_devices()
    discovered = scan_network()

    table = Table(title="SentinelHome Device Inventory")
    table.add_column("Status")
    table.add_column("Device Name")
    table.add_column("IP Address")
    table.add_column("Hostname")
    table.add_column("MAC Address")
    table.add_column("Vendor")

    unknown_devices = []

    for device in discovered:
        mac = device["mac"]

        if mac != "UNKNOWN" and mac in trusted:
            status = "[green]TRUSTED[/green]"
            name = trusted[mac]["name"]
        else:
            status = "[bold red]NEW[/bold red]"
            name = "Unapproved"
            unknown_devices.append(device)

        table.add_row(
            status,
            name,
            device["ip"],
            device["hostname"],
            mac,
            device["vendor"],
        )

    console.print(table)

    if not unknown_devices:
        console.print("\n[green]No unknown devices detected.[/green]")
        return

    console.print(
        f"\n[bold yellow]{len(unknown_devices)} new or unapproved device(s) detected.[/bold yellow]"
    )

    for device in unknown_devices:
        if device["mac"] == "UNKNOWN":
            console.print(
                f"\n[yellow]Cannot approve {device['ip']} because its MAC address was unavailable.[/yellow]"
            )
            continue

        console.print(
            f"\nIP: {device['ip']}\n"
            f"Hostname: {device['hostname']}\n"
            f"MAC: {device['mac']}\n"
            f"Vendor: {device['vendor']}"
        )

        approve = input("Approve this device? (y/n): ").strip().lower()

        if approve == "y":
            name = input("Enter a friendly name: ").strip()
            trusted[device["mac"]] = {
                "name": name or device["hostname"],
                "vendor": device["vendor"],
            }
            console.print("[green]Device approved.[/green]")

    save_trusted_devices(trusted)
    console.print(f"\n[cyan]Trusted inventory saved to {TRUSTED_FILE}[/cyan]")


if __name__ == "__main__":
    main()
