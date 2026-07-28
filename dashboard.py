from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="30">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>SentinelHome Dashboard</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111827;
            color: white;
            margin: 0;
            padding: 30px;
        }

        h1 {
            color: #60a5fa;
        }

        .card {
            background: #1f2937;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
        }

        .status {
            color: #34d399;
            font-size: 24px;
            font-weight: bold;
        }

        .muted {
            color: #9ca3af;
        }
    </style>
</head>

<body>
    <h1>SentinelHome</h1>

    <div class="card">
        <div class="status">Network Status: Monitoring</div>
        <p class="muted">This dashboard refreshes every 30 seconds.</p>
    </div>

    <div class="card">
        <h2>Current Monitoring</h2>
        <p>Trusted devices are being monitored.</p>
        <p>Unknown devices trigger desktop alerts.</p>
        <p>Event logging is enabled.</p>
    </div>

    <div class="card">
        <h2>Planned Features</h2>
        <p>Live device inventory</p>
        <p>Approve or deny unknown devices</p>
        <p>Email and phone notifications</p>
        <p>Wazuh integration</p>
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)