#!/usr/bin/env python3
"""
netbox_sync.py – NetBox API integration for DC inventory management
Usage:
    python netbox_sync.py --url http://netbox:8000 --token TOKEN
    python netbox_sync.py --url http://netbox:8000 --token TOKEN --ping
    python netbox_sync.py --url http://netbox:8000 --token TOKEN --export inventory.csv
    python netbox_sync.py --url http://netbox:8000 --token TOKEN --ping --update-status
"""

import argparse
import subprocess
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

try:
    import requests
except ImportError:
    print("Instala requests: pip install requests")
    sys.exit(1)

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

console = Console()


class NetBoxClient:
    def __init__(self, url: str, token: str):
        self.base = url.rstrip("/") + "/api"
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get(self, endpoint: str, params: dict = None) -> dict:
        resp = requests.get(f"{self.base}{endpoint}", headers=self.headers,
                            params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def patch(self, endpoint: str, data: dict) -> dict:
        resp = requests.patch(f"{self.base}{endpoint}", headers=self.headers,
                              json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def test_connection(self) -> bool:
        try:
            self.get("/")
            return True
        except Exception:
            return False

    def get_devices(self, site: str = None, role: str = None) -> list:
        params = {"limit": 1000}
        if site: params["site"] = site
        if role: params["role"] = role
        data = self.get("/dcim/devices/", params=params)
        return data.get("results", [])

    def get_racks(self) -> list:
        data = self.get("/dcim/racks/", {"limit": 1000})
        return data.get("results", [])

    def update_device_status(self, device_id: int, status: str) -> bool:
        try:
            self.patch(f"/dcim/devices/{device_id}/", {"status": status})
            return True
        except Exception:
            return False


def ping(ip: str, timeout: int = 1) -> tuple:
    if not ip:
        return False, -1.0
    try:
        cmd = ["ping", "-c", "1", "-W", str(timeout), str(ip)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                if "time=" in line:
                    ms = float(line.split("time=")[1].split()[0])
                    return True, ms
            return True, 0.0
        return False, -1.0
    except Exception:
        return False, -1.0


def get_primary_ip(device: dict) -> str:
    primary = device.get("primary_ip") or device.get("primary_ip4")
    if primary:
        addr = primary.get("address", "")
        return addr.split("/")[0]
    return ""


def run(args):
    nb = NetBoxClient(args.url, args.token)

    console.print()
    console.rule("[bold cyan]NOC TOOLKIT[/] · NetBox Sync")
    console.print(f"  URL   : [cyan]{args.url}[/]")

    with console.status("  Conectando a NetBox..."):
        if not nb.test_connection():
            console.print("  [red]Error:[/] No se pudo conectar. Verifica URL y token.")
            sys.exit(1)
    console.print("  Estado: [green]Conectado ✓[/]\n")

    # Obtener dispositivos
    with console.status("  Obteniendo inventario..."):
        devices = nb.get_devices(site=args.site, role=args.role)
        racks    = {r["id"]: r["name"] for r in nb.get_racks()}

    console.print(f"  Dispositivos encontrados: [cyan]{len(devices)}[/]\n")

    # Ping opcional
    ping_results = {}
    if args.ping and devices:
        ips = {d["id"]: get_primary_ip(d) for d in devices}
        ips_with_addr = {k: v for k, v in ips.items() if v}

        console.print(f"  Verificando conectividad de [cyan]{len(ips_with_addr)}[/] hosts...\n")

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("  Pinging hosts...", total=len(ips_with_addr))

            def check(item):
                dev_id, ip = item
                alive, lat = ping(ip)
                return dev_id, alive, lat

            with ThreadPoolExecutor(max_workers=30) as ex:
                futures = {ex.submit(check, item): item for item in ips_with_addr.items()}
                for fut in as_completed(futures):
                    dev_id, alive, lat = fut.result()
                    ping_results[dev_id] = (alive, lat)
                    progress.advance(task)

        # Actualizar estado en NetBox
        if args.update_status:
            console.print("\n  Actualizando estados en NetBox...")
            updated = 0
            for dev_id, (alive, _) in ping_results.items():
                status = "active" if alive else "failed"
                if nb.update_device_status(dev_id, status):
                    updated += 1
            console.print(f"  [green]{updated}[/] dispositivos actualizados\n")

    # Tabla de resultados
    table = Table(box=box.SIMPLE_HEAD, border_style="dim", expand=True)
    table.add_column("DISPOSITIVO",  style="cyan",  min_width=20)
    table.add_column("ROL",          style="dim",   min_width=15)
    table.add_column("SITE",         min_width=12)
    table.add_column("RACK / U",     min_width=12)
    table.add_column("IP PRIMARIA",  min_width=16)
    table.add_column("ESTADO NB",    justify="center", min_width=10)
    if args.ping:
        table.add_column("PING",     justify="center", min_width=8)
        table.add_column("LATENCIA", justify="right",  min_width=10)

    for d in devices:
        ip      = get_primary_ip(d)
        role    = d.get("role", {}) or {}
        site    = d.get("site", {}) or {}
        rack    = d.get("rack", {}) or {}
        status  = d.get("status", {}) or {}
        pos     = d.get("position")

        rack_str = f"{rack.get('name','—')} / U{pos}" if rack and pos else rack.get("name","—") if rack else "—"

        nb_status = status.get("label", "—")
        nb_color  = {"Active": "green", "Planned": "yellow", "Failed": "red"}.get(nb_status, "dim")

        row = [
            d.get("name", "—"),
            role.get("name", "—"),
            site.get("name", "—"),
            rack_str,
            ip or "[dim]—[/]",
            f"[{nb_color}]{nb_status}[/]",
        ]

        if args.ping:
            if d["id"] in ping_results:
                alive, lat = ping_results[d["id"]]
                row.append("[green]UP[/]" if alive else "[red]DOWN[/]")
                row.append(f"{lat:.1f} ms" if alive else "[dim]—[/]")
            else:
                row += ["[dim]—[/]", "[dim]—[/]"]

        table.add_row(*row)

    console.print(table)

    # Resumen
    if args.ping and ping_results:
        up   = sum(1 for a, _ in ping_results.values() if a)
        down = len(ping_results) - up
        console.print(f"  Ping: [green]{up} UP[/]  [red]{down} DOWN[/]  [dim]{len(ping_results)} verificados[/]")

    console.print(f"  Total: [cyan]{len(devices)}[/] dispositivos  ·  {datetime.now().strftime('%H:%M:%S')}\n")

    if args.export:
        _export(devices, ping_results, args.export)


def _export(devices: list, ping_results: dict, path: str):
    ext = path.rsplit(".", 1)[-1].lower()

    if ext == "json":
        data = []
        for d in devices:
            entry = {
                "id": d["id"], "name": d.get("name"),
                "role": (d.get("role") or {}).get("name"),
                "site": (d.get("site") or {}).get("name"),
                "ip":   get_primary_ip(d),
                "status": (d.get("status") or {}).get("label"),
            }
            if d["id"] in ping_results:
                alive, lat = ping_results[d["id"]]
                entry["ping_alive"] = alive
                entry["ping_latency_ms"] = lat
            data.append(entry)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    else:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            headers = ["id", "name", "role", "site", "rack", "position", "ip", "nb_status"]
            if ping_results:
                headers += ["ping_alive", "ping_latency_ms"]
            w.writerow(headers)
            for d in devices:
                row = [
                    d["id"], d.get("name"),
                    (d.get("role") or {}).get("name"),
                    (d.get("site") or {}).get("name"),
                    (d.get("rack") or {}).get("name"),
                    d.get("position"),
                    get_primary_ip(d),
                    (d.get("status") or {}).get("label"),
                ]
                if ping_results:
                    if d["id"] in ping_results:
                        alive, lat = ping_results[d["id"]]
                        row += [alive, lat]
                    else:
                        row += ["", ""]
                w.writerow(row)

    console.print(f"  [dim]Exportado →[/] [cyan]{path}[/]\n")


def main():
    parser = argparse.ArgumentParser(
        description="NetBox inventory sync and reachability checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python netbox_sync.py --url http://192.168.1.100:8000 --token abc123
  python netbox_sync.py --url http://netbox:8000 --token abc123 --ping
  python netbox_sync.py --url http://netbox:8000 --token abc123 --ping --update-status
  python netbox_sync.py --url http://netbox:8000 --token abc123 --export inventory.csv
  python netbox_sync.py --url http://netbox:8000 --token abc123 --site datacenter --role server
        """,
    )
    parser.add_argument("--url",           required=True, help="URL de NetBox (ej: http://netbox:8000)")
    parser.add_argument("--token",         required=True, help="Token de API de NetBox")
    parser.add_argument("--ping",          action="store_true", help="Verificar conectividad de cada dispositivo")
    parser.add_argument("--update-status", action="store_true", help="Actualizar estado en NetBox según ping")
    parser.add_argument("--site",                         help="Filtrar por site")
    parser.add_argument("--role",                         help="Filtrar por rol de dispositivo")
    parser.add_argument("--export", "-o",                 help="Exportar inventario (.csv o .json)")
    args = parser.parse_args()

    run(args)


if __name__ == "__main__":
    main()
