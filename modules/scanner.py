"""Network discovery functions for SentinelHome."""

from __future__ import annotations

import re
import subprocess

import nmap


def normalize_mac(mac_address: str) -> str:
    """Convert a MAC address to uppercase colon-separated format."""
    return mac_address.strip().replace("-", ":").upper()


def load_arp_table() -> dict[str, str]:
    """Return IP-to-MAC mappings from the Windows ARP cache."""
    arp_devices: dict[str, str] = {}

    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return arp_devices

    arp_pattern = re.compile(
        r"^\s*(\d{1,3}(?:\.\d{1,3}){3})\s+"
        r"([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})\s+"
        r"(?:dynamic|static)\s*$"
    )

    for line in result.stdout.splitlines():
        match = arp_pattern.match(line)

        if not match:
            continue

        ip_address = match.group(1)
        mac_address = normalize_mac(match.group(2))

        arp_devices[ip_address] = mac_address

    return arp_devices


def load_local_interfaces() -> dict[str, str]:
    """Return local Windows IPv4-to-MAC mappings."""
    interfaces: dict[str, str] = {}

    powershell_command = """
    Get-NetIPConfiguration |
    Where-Object {
        $_.IPv4Address -ne $null -and
        $_.NetAdapter.Status -eq 'Up'
    } |
    ForEach-Object {
        "$($_.IPv4Address.IPAddress)|$($_.NetAdapter.MacAddress)"
    }
    """

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                powershell_command,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return interfaces

    for line in result.stdout.splitlines():
        cleaned_line = line.strip()

        if "|" not in cleaned_line:
            continue

        ip_address, mac_address = cleaned_line.split("|", maxsplit=1)

        ip_address = ip_address.strip()
        mac_address = normalize_mac(mac_address)

        if ip_address and mac_address:
            interfaces[ip_address] = mac_address

    return interfaces


def scan_network(network: str) -> list[dict[str, str]]:
    """Discover active devices on the configured local network."""
    scanner = nmap.PortScanner()
    scanner.scan(
        hosts=network,
        arguments="-sn",
    )

    arp_table = load_arp_table()
    local_interfaces = load_local_interfaces()

    devices: list[dict[str, str]] = []

    for host in scanner.all_hosts():
        host_data = scanner[host]
        addresses = host_data.get("addresses", {})

        mac = normalize_mac(
            addresses.get("mac", "UNKNOWN")
        )

        if mac == "UNKNOWN":
            mac = arp_table.get(host, "UNKNOWN")

        if mac == "UNKNOWN":
            mac = local_interfaces.get(host, "UNKNOWN")

        hostname = host_data.hostname() or "Unknown"

        vendor_data = host_data.get("vendor", {})
        vendor = vendor_data.get(mac, "Unknown")

        devices.append(
            {
                "ip": host,
                "hostname": hostname,
                "mac": mac,
                "vendor": vendor,
            }
        )

    return devices