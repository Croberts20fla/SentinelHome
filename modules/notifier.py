from __future__ import annotations

from plyer import notification


def notify_unknown_device(device: dict[str, str]) -> None:
    """Display a Windows notification for an unknown network device."""
    message = (
        f"Hostname: {device['hostname']}\n"
        f"IP: {device['ip']}\n"
        f"MAC: {device['mac']}\n"
        f"Vendor: {device['vendor']}"
    )

    try:
        notification.notify(
            title="SentinelHome: Unknown Device",
            message=message,
            app_name="SentinelHome",
            timeout=15,
        )
    except Exception as error:
        print(f"[!] Desktop notification failed: {error}")