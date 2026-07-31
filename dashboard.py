"""Flask dashboard for SentinelHome."""

from pathlib import Path

from flask import Flask, redirect, render_template, url_for

from modules.dashboard_data import build_dashboard_data
from modules.trusted_manager import (
    approve_device,
    remove_trusted_device,
)

app = Flask(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
TRUSTED_FILE = PROJECT_DIR / "trusted_devices.json"


@app.route("/")
def home():
    """Display the SentinelHome dashboard."""
    dashboard_data = build_dashboard_data()

    return render_template(
        "dashboard.html",
        **dashboard_data,
    )


@app.route("/approve/<path:mac>")
def approve(mac):
    """Approve a device."""

    dashboard_data = build_dashboard_data()

    for device in dashboard_data["live_inventory"]:

        if device["mac"].upper() != mac.upper():
            continue

        approve_device(
            TRUSTED_FILE,
            device=device,
            name=device["name"],
            owner="Chris",
        )

        break

    return redirect(url_for("home"))


@app.route("/remove/<path:mac>")
def remove(mac):
    """Remove a trusted device."""

    remove_trusted_device(
        TRUSTED_FILE,
        mac,
    )

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )