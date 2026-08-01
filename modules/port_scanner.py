"""Port-scanning functions for SentinelHome."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import nmap


COMMON_PORTS = (
    "20,21,22,23,25,53,67,68,80,110,123,135,137,138,139,"
    "143,161,389,443,445,465,514,587,631,993,995,1433,"
    "1900,3306,3389,5353,5357,5900,8000,8080,8443"
)


def scan_device_ports(
    ip_address: str,
) -> dict[str, Any]:
    """Scan common TCP ports on one device."""
    scanner = nmap.PortScanner()

    scanner.scan(
        hosts=ip_address,
        ports=COMMON_PORTS,
        arguments="-sT -sV --version-light",
    )

    scan_time = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    result: dict[str, Any] = {
        "ip": ip_address,
        "scanned_at": scan_time,
        "status": "Unknown",
        "open_ports": [],
    }

    if ip_address not in scanner.all_hosts():
        return result

    host_data = scanner[ip_address]
    result["status"] = host_data.state().title()

    open_ports: list[dict[str, Any]] = []

    if "tcp" in host_data:
        for port_number in sorted(host_data["tcp"]):
            port_data = host_data["tcp"][port_number]

            if port_data.get("state") != "open":
                continue

            open_ports.append(
                {
                    "port": port_number,
                    "protocol": "TCP",
                    "service": port_data.get("name") or "Unknown",
                    "product": port_data.get("product") or "Unknown",
                    "version": port_data.get("version") or "Unknown",
                }
            )

    result["open_ports"] = open_ports
    return result


def load_port_scan_results(
    file_path: Path,
) -> dict[str, dict[str, Any]]:
    """Load saved port-scan results."""
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


def save_port_scan_result(
    file_path: Path,
    scan_result: dict[str, Any],
) -> None:
    """Save the latest port scan for one IP address."""
    results = load_port_scan_results(file_path)

    ip_address = str(scan_result.get("ip", "")).strip()

    if not ip_address:
        return

    results[ip_address] = scan_result

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = file_path.with_suffix(".tmp")

    temporary_file.write_text(
        json.dumps(
            results,
            indent=4,
        ),
        encoding="utf-8",
    )

    temporary_file.replace(file_path)