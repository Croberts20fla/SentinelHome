"""Flask dashboard for SentinelHome."""

from pathlib import Path

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)

from modules.dashboard_data import build_dashboard_data
from modules.database import (
    find_device_key,
    get_device_timeline,
    initialize_database,
    record_device_event,
    save_port_scan_to_database,
    update_device_management,
)
from modules.port_scanner import (
    load_port_scan_results,
    save_port_scan_result,
    scan_device_ports,
)
from modules.trusted_manager import (
    approve_device,
    remove_trusted_device,
    rename_trusted_device,
)
from modules.risk_engine import calculate_device_risk
   

app = Flask(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
TRUSTED_FILE = PROJECT_DIR / "trusted_devices.json"
PORT_SCAN_FILE = PROJECT_DIR / "logs" / "port_scan_results.json"
DATABASE_FILE = PROJECT_DIR / "data" / "sentinelhome.db"

initialize_database(DATABASE_FILE)


@app.route("/")
def home():
    """Display the SentinelHome dashboard."""
    dashboard_data = build_dashboard_data()

    return render_template(
        "dashboard.html",
        **dashboard_data,
    )


@app.route("/device/<path:ip_address>")
def device_details(ip_address):
    """Display details for one device."""
    dashboard_data = build_dashboard_data()

    selected_device = next(
        (
            device
            for device in dashboard_data["live_inventory"]
            if device["ip"] == ip_address
        ),
        None,
    )

    if selected_device is None:
        abort(404)

    device_key = find_device_key(
        DATABASE_FILE,
        mac_address=selected_device["mac"],
        ip_address=ip_address,
    )

    if device_key:
        related_events = get_device_timeline(
            DATABASE_FILE,
            device_key,
        )
    else:
        related_events = []

    saved_scans = load_port_scan_results(
        PORT_SCAN_FILE
    )

    port_scan = saved_scans.get(ip_address)

    risk_assessment = calculate_device_risk(
        selected_device,
        port_scan,
    )

    return render_template(
        "device_details.html",
        device=selected_device,
        related_events=related_events,
        port_scan=port_scan,
        risk_assessment=risk_assessment,
    )

@app.route(
    "/device/<path:ip_address>/scan-ports",
    methods=["POST"],
)
def scan_ports(ip_address):
    """Run and save a port scan for one device."""
    dashboard_data = build_dashboard_data()

    selected_device = next(
        (
            device
            for device in dashboard_data["live_inventory"]
            if device["ip"] == ip_address
        ),
        None,
    )

    if selected_device is None:
        abort(404)

    scan_result = scan_device_ports(ip_address)

    save_port_scan_result(
        PORT_SCAN_FILE,
        scan_result,
    )

    device_key = find_device_key(
        DATABASE_FILE,
        mac_address=selected_device["mac"],
        ip_address=ip_address,
    )

    if device_key:
        save_port_scan_to_database(
            DATABASE_FILE,
            device_key,
            scan_result,
        )

        record_device_event(
            DATABASE_FILE,
            device_key,
            "port_scan_completed",
            {
                "ip": selected_device["ip"],
                "hostname": selected_device["hostname"],
                "mac": selected_device["mac"],
                "open_port_count": len(
                    scan_result.get("open_ports", [])
                ),
            },
        )

    return redirect(
        url_for(
            "device_details",
            ip_address=ip_address,
        )
    )


@app.route("/approve/<path:mac>")
def approve(mac):
    """Approve a device."""
    dashboard_data = build_dashboard_data()

    selected_device = next(
        (
            device
            for device in dashboard_data["live_inventory"]
            if device["mac"].upper() == mac.upper()
        ),
        None,
    )

    if selected_device is not None:
        approved = approve_device(
            TRUSTED_FILE,
            device=selected_device,
            name=selected_device["name"],
            owner="Chris",
        )

        if approved:
            device_key = find_device_key(
                DATABASE_FILE,
                mac_address=mac,
                ip_address=selected_device["ip"],
            )

            if device_key:
                update_device_management(
                    DATABASE_FILE,
                    device_key,
                    trusted=True,
                    name=selected_device["name"],
                    owner="Chris",
                )

                record_device_event(
                    DATABASE_FILE,
                    device_key,
                    "device_approved",
                    {
                        "ip": selected_device["ip"],
                        "hostname": selected_device["hostname"],
                        "mac": selected_device["mac"],
                        "owner": "Chris",
                    },
                )

    return redirect(url_for("home"))


@app.route("/remove/<path:mac>")
def remove(mac):
    """Remove a trusted device."""
    dashboard_data = build_dashboard_data()

    selected_device = next(
        (
            device
            for device in dashboard_data["live_inventory"]
            if device["mac"].upper() == mac.upper()
        ),
        None,
    )

    removed = remove_trusted_device(
        TRUSTED_FILE,
        mac,
    )

    if removed:
        device_key = find_device_key(
            DATABASE_FILE,
            mac_address=mac,
            ip_address=(
                selected_device["ip"]
                if selected_device
                else None
            ),
        )

        if device_key:
            update_device_management(
                DATABASE_FILE,
                device_key,
                trusted=False,
                owner="Unknown",
            )

            record_device_event(
                DATABASE_FILE,
                device_key,
                "trust_removed",
                {
                    "ip": (
                        selected_device["ip"]
                        if selected_device
                        else "Unknown"
                    ),
                    "hostname": (
                        selected_device["hostname"]
                        if selected_device
                        else "Unknown"
                    ),
                    "mac": mac.upper(),
                },
            )

    return redirect(url_for("home"))


@app.route("/rename/<path:mac>", methods=["POST"])
def rename(mac):
    """Rename a trusted device."""
    new_name = request.form.get(
        "new_name",
        "",
    ).strip()

    renamed = rename_trusted_device(
        TRUSTED_FILE,
        mac,
        new_name,
    )

    if renamed:
        dashboard_data = build_dashboard_data()

        selected_device = next(
            (
                device
                for device in dashboard_data["live_inventory"]
                if device["mac"].upper() == mac.upper()
            ),
            None,
        )

        device_key = find_device_key(
            DATABASE_FILE,
            mac_address=mac,
            ip_address=(
                selected_device["ip"]
                if selected_device
                else None
            ),
        )

        if device_key:
            update_device_management(
                DATABASE_FILE,
                device_key,
                name=new_name,
            )

            record_device_event(
                DATABASE_FILE,
                device_key,
                "device_renamed",
                {
                    "ip": (
                        selected_device["ip"]
                        if selected_device
                        else "Unknown"
                    ),
                    "hostname": (
                        selected_device["hostname"]
                        if selected_device
                        else "Unknown"
                    ),
                    "mac": mac.upper(),
                    "new_name": new_name,
                },
            )

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )