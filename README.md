# datacenter-ops-toolkit

A collection of Python CLI tools for **NOC and Data Center operations** — network discovery, uptime monitoring, NetBox integration, incident reporting, and device configuration backup.

Built from real operational experience in 24x7 Data Center environments.

---

## Tools

| Tool | Description |
|------|-------------|
| [`netscan.py`](#netscanpy) | ICMP host discovery + port scanning for IP ranges |
| [`uptime_monitor.py`](#uptime_monitorpy) | Live terminal uptime dashboard with history and alerting |
| [`netbox_sync.py`](#netbox_syncpy) | NetBox API integration — inventory listing, ping check, status update |
| [`incident_report.py`](#incident_reportpy) | HTML incident report generator (interactive or from log) |
| [`config_backup.py`](#config_backuppy) | SSH configuration backup for Cisco, Arista, Huawei, Linux, and more |

---

## Installation

```bash
git clone https://github.com/YOUR_USER/datacenter-ops-toolkit.git
cd datacenter-ops-toolkit
pip install -r requirements.txt
```

**Requirements:** Python 3.9+ · `rich` · `requests` · `paramiko`

---

## netscan.py

Discovers live hosts in an IP range using concurrent ICMP pings. Optionally checks common infrastructure ports on alive hosts.

```bash
# Basic scan
python netscan.py 192.168.1.0/24

# Scan with port check
python netscan.py 192.168.1.0/24 --ports

# Export to CSV
python netscan.py 10.0.0.0/24 --ports --output results.csv --workers 100
```

**Output:** Rich table with IP, status, latency, hostname, and open ports (SSH, SNMP, RDP, HTTP, etc.)

**Ports checked:** SSH (22), Telnet (23), SMTP (25), DNS (53), HTTP (80), SNMP (161), HTTPS (443), MySQL (3306), RDP (3389), PostgreSQL (5432), HTTP-Alt (8080), JetDirect (9100)

---

## uptime_monitor.py

Live NOC-style terminal dashboard that monitors host availability in real time. Tracks uptime percentage, latency history, and alerts on state changes.

```bash
# Monitor specific hosts
python uptime_monitor.py 192.168.1.1 192.168.1.254 8.8.8.8

# Monitor from file, every 30 seconds, log to CSV
python uptime_monitor.py --file hosts.txt --interval 30 --log uptime.csv
```

**`hosts.txt` format:**
```
# Gateway
192.168.1.1
# DNS servers
8.8.8.8
1.1.1.1
```

**Features:**
- Auto-refreshing Rich Live table
- Uptime % per host (color-coded: green ≥99.9% / yellow ≥99% / red <99%)
- Latency sparkline showing last 20 checks
- Alert counter per host
- Last downtime timestamp
- Summary report on exit (Ctrl+C)
- CSV logging compatible with `incident_report.py`

---

## netbox_sync.py

Integrates with the NetBox DCIM API to list devices, verify reachability, and optionally update device status.

```bash
# List all devices
python netbox_sync.py --url http://192.168.1.100:8000 --token YOUR_TOKEN

# Ping each device and show results
python netbox_sync.py --url http://netbox:8000 --token TOKEN --ping

# Update device status in NetBox based on ping result
python netbox_sync.py --url http://netbox:8000 --token TOKEN --ping --update-status

# Filter by site or role
python netbox_sync.py --url http://netbox:8000 --token TOKEN --site datacenter --role server

# Export inventory to CSV
python netbox_sync.py --url http://netbox:8000 --token TOKEN --export inventory.csv
```

**Features:**
- Reads primary IP from NetBox and pings each device
- Shows device name, role, site, rack position, IP, and NetBox status
- Can update NetBox device status (`active` / `failed`) automatically
- Exports to CSV or JSON

---

## incident_report.py

Generates professional HTML incident reports for NOC documentation and post-mortem analysis.

```bash
# Interactive mode — fill in details via CLI prompts
python incident_report.py

# Generate from uptime_monitor CSV log
python incident_report.py --from-log uptime.csv

# Load from JSON template
python incident_report.py --json incident.json --output INC-2025-001.html
```

**Report includes:**
- Incident ID, severity badge (BAJO / MEDIO / ALTO / CRÍTICO), operator
- Start time, end time, duration, root cause
- Affected hosts table with status and downtime
- Event timeline
- Resolution steps
- Lessons learned

Output is a self-contained HTML file — open in any browser, print to PDF with Ctrl+P.

---

## config_backup.py

Connects to network devices and servers via SSH, runs configuration commands, and saves the output locally. Detects changes between backups and generates diff files.

```bash
# Backup a single Cisco device
python config_backup.py 192.168.1.1 --user admin --type cisco

# Backup a Linux server using SSH key
python config_backup.py 10.0.0.5 --user root --type linux --key ~/.ssh/id_rsa

# Backup multiple devices from CSV
python config_backup.py --hosts devices.csv --output ./backups --workers 5
```

**`devices.csv` format:**
```csv
ip,user,type,port
192.168.1.1,admin,cisco,22
192.168.1.2,root,linux,22
10.0.0.1,admin,arista,22
10.0.0.2,admin,huawei,22
```

**Supported device types:**

| Type | Commands |
|------|----------|
| `cisco` | `show running-config` |
| `cisco-nx` | `show running-config` |
| `arista` | `show running-config` |
| `huawei` | `display current-configuration` |
| `linux` | `ip addr`, `ip route`, `iptables -L`, network interfaces |
| `fortinet` | `show full-configuration` |
| `mikrotik` | `/export` |

**Features:**
- Concurrent backups (configurable workers)
- Change detection — generates `.diff` file when config changes between runs
- Organized backup files: `IP_type_YYYYMMDD_HHMMSS.txt`
- Summary table with per-device status

---

## Workflow Example

```bash
# 1. Discover what's on the network
python netscan.py 192.168.1.0/24 --ports --output hosts.csv

# 2. Monitor critical hosts
python uptime_monitor.py 192.168.1.1 192.168.1.254 8.8.8.8 --log uptime.csv

# 3. After an incident, generate the report
python incident_report.py --from-log uptime.csv --output INC-20250815.html

# 4. Backup device configs
python config_backup.py --hosts hosts.csv --output ./backups
```

---

## Author

**Jeremy Inostrosa** — Network & Datacenter Operations Engineer  
[LinkedIn](https://linkedin.com/in/jeremyinostrosa)
