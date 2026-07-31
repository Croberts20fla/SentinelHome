"""Network discovery functions for SentinelHome."""

from __future__ import annotations

import re
import subprocess

import nmap


def load_arp_table() -> dict[str, str]:
    """Read the Windows ARP cache and return IP-to-MAC mappings."""
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
        mac_address = match.group(2).replace("-", ":").upper()

        arp_devices[ip_address] = mac_address

    return arp_devices


def scan_network(network: str) -> list[dict[str, str]]:
    """Discover active devices on the configured local network."""
    scanner = nmap.PortScanner()
    scanner.scan(
        hosts=network,
        arguments="-sn",
    )

    arp_table = load_arp_table()
    devices: list[dict[str, str]] = []

    for host in scanner.all_hosts():
        host_data = scanner[host]
        addresses = host_data.get("addresses", {})

        mac = addresses.get("mac", "UNKNOWN").upper()

        if mac == "UNKNOWN":
            mac = arp_table.get(host, "UNKNOWN")

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