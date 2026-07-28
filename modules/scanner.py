from __future__ import annotations

import nmap


def scan_network(network: str) -> list[dict[str, str]]:
    """Discover active devices on the configured local network."""
    scanner = nmap.PortScanner()
    scanner.scan(hosts=network, arguments="-sn")

    devices: list[dict[str, str]] = []

    for host in scanner.all_hosts():
        host_data = scanner[host]
        addresses = host_data.get("addresses", {})

        mac = addresses.get("mac", "UNKNOWN").upper()
        hostname = host_data.hostname() or "Unknown"
        vendor = host_data.get("vendor", {}).get(mac, "Unknown")

        devices.append(
            {
                "ip": host,
                "hostname": hostname,
                "mac": mac,
                "vendor": vendor,
            }
        )

    return devices