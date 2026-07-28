# 🛡️ SentinelHome

A Python-based home network security monitoring application that discovers devices on a local network, identifies trusted and unknown devices, generates desktop alerts, logs security events, and provides a web dashboard for monitoring.

---

## Overview

SentinelHome was built as part of my cybersecurity portfolio while pursuing a Bachelor of Science in Information Technologies and a Master of Science in Cybersecurity Risk Management.

The goal of this project is to simulate the type of endpoint and network visibility used by security operations teams while demonstrating practical Python development, networking, and cybersecurity concepts.

---

## Features

- Live network device discovery using Nmap
- Trusted device inventory
- Detection of unknown devices
- Desktop notifications for new devices
- Event logging
- Flask web dashboard
- Modular Python architecture
- Git version control
- GitHub portfolio project

---

## Technologies

- Python 3
- Flask
- Nmap
- PowerShell
- Git
- GitHub
- JSON
- Windows
- VS Code

---

## Project Structure

```
SentinelHome/
│
├── docs/
├── logs/
├── modules/
│   ├── config.py
│   ├── event_logger.py
│   ├── inventory.py
│   ├── notifier.py
│   ├── scanner.py
│   └── utils.py
│
├── screenshots/
├── tests/
│
├── dashboard.py
├── sentinelhome.py
├── requirements.txt
├── trusted_devices.json
└── README.md
```

---

## Current Capabilities

- Discovers devices connected to the local network
- Maintains a trusted device inventory
- Detects new or unknown devices
- Displays live monitoring information
- Generates desktop notifications
- Logs security events for future analysis

---

## Planned Features

- Live dashboard updates
- Device history and timelines
- Risk scoring
- Email notifications
- Mobile notifications
- Device approval directly from the dashboard
- Port scanning of newly discovered devices
- Vendor logo support
- AI-assisted device analysis
- Wazuh SIEM integration
- Docker deployment

---

## Screenshots

### SentinelHome Dashboard

> *(Add a screenshot here once available.)*

### Live Device Inventory

> *(Add a screenshot of the console inventory here.)*

---

## Installation

Clone the repository

```bash
git clone https://github.com/Croberts20fla/SentinelHome.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run SentinelHome

```bash
python sentinelhome.py
```

Launch the dashboard

```bash
python dashboard.py
```

Open:

```
http://127.0.0.1:5000
```

---

## Why I Built This

I built SentinelHome to strengthen my practical cybersecurity and software development skills through a real-world project.

This project demonstrates:

- Python programming
- Network discovery
- JSON data management
- Modular software architecture
- Flask web development
- Git and GitHub workflows
- Security monitoring concepts

---

## About Me

I am an IT professional and cybersecurity graduate student at Indiana University, building practical security solutions through hands-on projects focused on network monitoring, automation, and defensive security.

My interests include:

- Blue Team Operations
- Security Engineering
- Python Automation
- Threat Detection
- Cloud Security
- SIEM Engineering

GitHub:

https://github.com/Croberts20fla

LinkedIn:

www.linkedin.com/in/christopher-roberts-324b3b219

---

## License

This project is licensed under the MIT License.
