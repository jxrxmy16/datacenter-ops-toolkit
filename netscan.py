#!/usr/bin/env python3
"""
netscan.py – Network host discovery with port scanning
Usage:
    python netscan.py 192.168.1.0/24
    python netscan.py 192.168.1.0/24 --ports
    python netscan.py 192.168.1.0/24 --ports --output results.csv
"""

import argparse
import subprocess
import socket
import ipaddress
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn
from rich import box

console = Console()

COMMON_PORTS = {
    22:   "SSH",
    23:   "Telnet",
    25:   "SMTP",
    53:   "DNS",
    80:   "HTTP",
    161:  "SNMP",
    443:  "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    9100: "JetDirect",
}


def ping(ip: str, timeout: int = 1) -> tuple:
    try:
        cmd = ["ping", "-c", "1", "-W", str(timeout), str(ip)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "time=" in line:
                    ms = float(line.split("time=")[1].split()[0])
                    return True, ms
            return True, 0.0
        return False, -1.0
    except Exception:
        return False, -1.0


def resolve(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


def scan_ports(ip: str, timeout: float = 0.5) -> dict:
    open_ports = {}

    def try_port(port):
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                return port
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=30) as ex:
        for result in ex.map(try_port, COMMON_PORTS.keys()):
            if result:
                open_ports[result] = COMMON_PORTS[result]

    return open_ports


def scan(cidr: str, check_ports: bool, workers: int, output: str):
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except ValueError as e:
        console.print(f"[red]Error:[/] Rango inválido: {e}")
        sys.exit(1)

    hosts = [str(h) for h in network.hosts()]
    total  = len(hosts)
    results = []

    console.print()
    console.rule(f"[bold cyan]NOC TOOLKIT[/] · Network Scanner")
    console.print(f"  Rango : [cyan]{cidr}[/]   Hosts: [cyan]{total}[/]   Workers: [cyan]{workers}[/]\n")

    def probe(ip):
        alive, latency = ping(ip)
        hostname = resolve(ip) if alive else ""
        ports = scan_ports(ip) if (alive and check_ports) else {}
        return {
            "ip": ip, "alive": alive, "latency": latency,
            "hostname": hostname, "ports": ports,
            "scanned_at": datetime.now().isoformat(),
        }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"  Escaneando {cidr}...", total=total)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(probe, ip): ip for ip in hosts}
            for future in as_completed(futures):
                results.append(future.result())
                progress.advance(task)

    results.sort(key=lambda h: ipaddress.ip_address(h["ip"]))
    alive_hosts = [h for h in results if h["alive"]]

    # ── Tabla de resultados ────────────────────────────────────────────────────
    table = Table(box=box.SIMPLE_HEAD, border_style="dim", show_lines=False)
    table.add_column("IP",         style="cyan",  no_wrap=True, min_width=16)
    table.add_column("Estado",     justify="center", min_width=6)
    table.add_column("Latencia",   justify="right", min_width=10)
    table.add_column("Hostname",   style="dim",   min_width=20)
    table.add_column("Puertos",    min_width=30)

    for h in results:
        if h["alive"]:
            status  = "[bold green]UP[/]"
            lat     = f"{h['latency']:.1f} ms"
            ports_s = "  ".join(
                f"[green]{svc}[/]:[dim]{p}[/]"
                for p, svc in sorted(h["ports"].items())
            ) or "[dim]—[/]"
        else:
            status  = "[red]DOWN[/]"
            lat     = "[dim]—[/]"
            ports_s = "[dim]—[/]"

        table.add_row(
            h["ip"],
            status,
            lat,
            h["hostname"] or "[dim]—[/]",
            ports_s,
        )

    console.print(table)
    console.print(
        f"  Resumen: [green]{len(alive_hosts)} UP[/]  [red]{total - len(alive_hosts)} DOWN[/]  "
        f"[dim]{total} total[/]  ·  {datetime.now().strftime('%H:%M:%S')}\n"
    )

    if output:
        _export(results, output)


def _export(results, path):
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "json":
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
    else:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ip", "alive", "latency_ms", "hostname", "open_ports", "scanned_at"])
            for h in results:
                ports_s = ";".join(f"{p}/{s}" for p, s in h["ports"].items())
                w.writerow([h["ip"], h["alive"], h["latency"], h["hostname"], ports_s, h["scanned_at"]])
    console.print(f"  [dim]Exportado →[/] [cyan]{path}[/]\n")


def main():
    parser = argparse.ArgumentParser(
        description="Network host discovery and port scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python netscan.py 192.168.1.0/24
  python netscan.py 10.0.0.0/24 --ports
  python netscan.py 172.16.0.0/24 --ports --output hosts.csv --workers 100
        """,
    )
    parser.add_argument("range",            help="Rango CIDR (ej: 192.168.1.0/24)")
    parser.add_argument("--ports",          action="store_true", help="Escanear puertos comunes en hosts UP")
    parser.add_argument("--workers", "-w",  type=int, default=50, help="Hilos concurrentes (default: 50)")
    parser.add_argument("--output",  "-o",  help="Exportar resultados (.csv o .json)")
    args = parser.parse_args()

    scan(args.range, args.ports, args.workers, args.output)


if __name__ == "__main__":
    main()
