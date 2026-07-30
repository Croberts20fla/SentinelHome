"""Flask dashboard for SentinelHome."""

from flask import Flask, render_template, redirect, url_for

from modules.dashboard_data import build_dashboard_data
from modules.trusted_manager import approve_device

from pathlib import Path

app = Flask(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
TRUSTED_FILE = PROJECT_DIR / "trusted_devices.json"


@app.route("/")
def home():
    """Display the SentinelHome security dashboard."""
    dashboard_data = build_dashboard_data()

    return render_template(
        "dashboard.html",
        **dashboard_data,
    )

@app.route("/approve/<mac>")
def approve(mac):
    """
    Approve a device from the dashboard.
    """

    dashboard_data = build_dashboard_data()

    for device in dashboard_data["live_inventory"]:
        if device["mac"] == mac:

            approve_device(
                TRUSTED_FILE,
                device,
                name=device["device_name"],
                owner="Chris",
            )

            break

    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )