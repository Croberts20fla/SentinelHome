"""Risk-scoring functions for SentinelHome."""

from __future__ import annotations

from typing import Any


HIGH_RISK_PORTS = {
    21: "FTP",
    23: "Telnet",
    445: "SMB",
    3389: "Remote Desktop",
    5900: "VNC",
}

MEDIUM_RISK_PORTS = {
    135: "Windows RPC",
    139: "NetBIOS",
    1900: "UPnP",
    5357: "Windows Device Discovery",
}


def calculate_device_risk(
    device: dict[str, Any],
    port_scan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate a device risk score and supporting reasons."""
    score = 0
    reasons: list[dict[str, str]] = []

    trusted = bool(device.get("trusted", False))
    mac_address = str(device.get("mac", "UNKNOWN")).upper()
    vendor = str(device.get("vendor", "Unknown"))
    hostname = str(device.get("hostname", "Unknown"))

    if trusted:
        reasons.append(
            {
                "level": "positive",
                "message": "Device is approved as trusted.",
            }
        )
    else:
        score += 35
        reasons.append(
            {
                "level": "high",
                "message": "Device has not been approved.",
            }
        )

    if mac_address == "UNKNOWN":
        score += 20
        reasons.append(
            {
                "level": "high",
                "message": "MAC address could not be identified.",
            }
        )
    else:
        reasons.append(
            {
                "level": "positive",
                "message": "MAC address is known.",
            }
        )

    if vendor.lower() == "unknown":
        score += 10
        reasons.append(
            {
                "level": "medium",
                "message": "Device vendor is unknown.",
            }
        )

    if hostname.lower() == "unknown":
        score += 5
        reasons.append(
            {
                "level": "medium",
                "message": "Hostname is unavailable.",
            }
        )

    open_ports = []

    if port_scan:
        open_ports = port_scan.get("open_ports", [])

    if not port_scan:
        score += 5
        reasons.append(
            {
                "level": "info",
                "message": "No port scan has been completed.",
            }
        )
    elif not open_ports:
        reasons.append(
            {
                "level": "positive",
                "message": "No configured common TCP ports were open.",
            }
        )

    for port_record in open_ports:
        port_number = int(port_record.get("port", 0))

        if port_number in HIGH_RISK_PORTS:
            score += 15
            reasons.append(
                {
                    "level": "high",
                    "message": (
                        f"Port {port_number} "
                        f"({HIGH_RISK_PORTS[port_number]}) is open."
                    ),
                }
            )

        elif port_number in MEDIUM_RISK_PORTS:
            score += 7
            reasons.append(
                {
                    "level": "medium",
                    "message": (
                        f"Port {port_number} "
                        f"({MEDIUM_RISK_PORTS[port_number]}) is open."
                    ),
                }
            )

        else:
            score += 2
            reasons.append(
                {
                    "level": "info",
                    "message": f"Port {port_number} is open.",
                }
            )

    score = min(score, 100)

    if score <= 24:
        rating = "Low"
        css_class = "risk-low"
    elif score <= 49:
        rating = "Moderate"
        css_class = "risk-moderate"
    elif score <= 74:
        rating = "High"
        css_class = "risk-high"
    else:
        rating = "Critical"
        css_class = "risk-critical"

    return {
        "score": score,
        "rating": rating,
        "css_class": css_class,
        "reasons": reasons,
        "open_port_count": len(open_ports),
    }