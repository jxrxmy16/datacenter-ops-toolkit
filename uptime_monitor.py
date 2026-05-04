#!/usr/bin/env python3
"""
uptime_monitor.py – Live uptime dashboard for NOC operations
Usage:
    python uptime_monitor.py 192.168.1.1 192.168.1.254 8.8.8.8
    python uptime_monitor.py --file hosts.txt --interval 30 --log uptime.csv
"""

import argparse
import subprocess
import csv
import sys
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich import box

console = Console()

MAX_HISTORY   = 20
SPARKLINE_UP  = "▇"
SPARKLINE_DOWN = "░"


def ping(ip: str, timeout: int = 2) -> tuple:
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


class HostState:
    def __init__(self, ip: str):
        self.ip       = ip
        self.alive    = None
        self.latency  = -1.0
        self.checks   = 0
        self.up_count = 0
        self.history  = deque(maxlen=MAX_HISTORY)  # True/False per check
        self.latencies= deque(maxlen=MAX_HISTORY)
        self.last_change: datetime = None
        self.last_down: str = "—"
        self.alerts   = 0

    @property
    def uptime_pct(self) -> float:
        return (self.up_count / self.checks * 100) if self.checks else 0.0

    @property
    def avg_latency(self) -> float:
        lats = [l for l in self.latencies if l > 0]
        return sum(lats) / len(lats) if lats else -1.0

    def update(self, alive: bool, latency: float):
        prev = self.alive
        self.alive   = alive
        self.latency = latency
        self.checks += 1
        self.history.append(alive)
        if alive:
            self.up_count += 1
            self.latencies.append(latency)
        else:
            self.latencies.append(-1.0)
        if prev is not None and prev != alive:
            self.last_change = datetime.now()
            if not alive:
                self.last_down = datetime.now().strftime("%H:%M:%S")
                self.alerts += 1

    def sparkline(self) -> Text:
        t = Text()
        for ok in self.history:
            if ok:
                t.append(SPARKLINE_UP, style="green")
            else:
                t.append(SPARKLINE_DOWN, style="red")
        return t

    def uptime_style(self) -> str:
        p = self.uptime_pct
        if p >= 99.9: return "bold green"
        if p >= 99.0: return "green"
        if p >= 95.0: return "yellow"
        return "red"

    def latency_style(self) -> str:
        if self.latency < 0:   return "dim"
        if self.latency < 10:  return "green"
        if self.latency < 50:  return "yellow"
        return "red"


def build_table(states: dict, interval: int, log_file: str) -> Table:
    ts    = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    title = f"[bold cyan]NOC UPTIME MONITOR[/]   [dim]{ts}   intervalo: {interval}s"
    if log_file:
        title += f"   log: [cyan]{log_file}[/]"

    table = Table(
        title=title,
        box=box.SIMPLE_HEAD,
        border_style="dim",
        show_lines=False,
        expand=True,
    )
    table.add_column("HOST",        style="cyan",  no_wrap=True, min_width=18)
    table.add_column("ESTADO",      justify="center", min_width=6)
    table.add_column("LATENCIA",    justify="right",  min_width=10)
    table.add_column("AVG LAT",     justify="right",  min_width=10)
    table.add_column("UPTIME",      justify="right",  min_width=8)
    table.add_column("CHECKS",      justify="right",  min_width=7)
    table.add_column("ALERTAS",     justify="center", min_width=7)
    table.add_column("ÚLT. CAÍDA",  min_width=10)
    table.add_column(f"HISTORIAL ({MAX_HISTORY})", min_width=MAX_HISTORY + 2)

    for ip, s in states.items():
        if s.alive is None:
            status = Text("—", style="dim")
        elif s.alive:
            status = Text("UP", style="bold green")
        else:
            status = Text("DOWN", style="bold red")

        lat_str = f"{s.latency:.1f} ms" if s.latency >= 0 else "—"
        avg_str = f"{s.avg_latency:.1f} ms" if s.avg_latency >= 0 else "—"

        table.add_row(
            ip,
            status,
            Text(lat_str, style=s.latency_style()),
            Text(avg_str),
            Text(f"{s.uptime_pct:.2f}%", style=s.uptime_style()),
            str(s.checks),
            Text(str(s.alerts), style="red bold" if s.alerts else "dim"),
            Text(s.last_down, style="red" if s.last_down != "—" else "dim"),
            s.sparkline(),
        )

    return table


def monitor(hosts: list, interval: int, log_file: str):
    states = {ip: HostState(ip) for ip in hosts}

    if log_file:
        with open(log_file, "w", newline="") as f:
            csv.writer(f).writerow(["timestamp", "ip", "alive", "latency_ms"])

    def check_all():
        with ThreadPoolExecutor(max_workers=len(hosts)) as ex:
            futures = {ex.submit(ping, ip): ip for ip in hosts}
            for fut in as_completed(futures):
                ip = futures[fut]
                alive, lat = fut.result()
                states[ip].update(alive, lat)
                if log_file:
                    with open(log_file, "a", newline="") as f:
                        csv.writer(f).writerow([
                            datetime.now().isoformat(), ip, alive, lat
                        ])

    console.print(f"\n[bold cyan]NOC Uptime Monitor[/] arrancando con [cyan]{len(hosts)}[/] hosts...")
    console.print("[dim]Ctrl+C para detener y ver resumen final\n[/]")
    time.sleep(0.5)

    try:
        with Live(build_table(states, interval, log_file),
                  refresh_per_second=2, console=console) as live:
            while True:
                check_all()
                live.update(build_table(states, interval, log_file))
                time.sleep(interval)

    except KeyboardInterrupt:
        pass

    # Resumen final
    console.print("\n")
    console.rule("[bold]Resumen Final[/]")
    summary = Table(box=box.SIMPLE, border_style="dim")
    summary.add_column("HOST",   style="cyan")
    summary.add_column("UPTIME", justify="right")
    summary.add_column("CHECKS", justify="right")
    summary.add_column("AVG LAT", justify="right")
    summary.add_column("ALERTAS", justify="center")

    for ip, s in states.items():
        summary.add_row(
            ip,
            Text(f"{s.uptime_pct:.3f}%", style=s.uptime_style()),
            str(s.checks),
            f"{s.avg_latency:.1f} ms" if s.avg_latency >= 0 else "—",
            Text(str(s.alerts), style="red" if s.alerts else "dim"),
        )

    console.print(summary)
    if log_file:
        console.print(f"\n  Log guardado en [cyan]{log_file}[/]\n")


def load_hosts_file(path: str) -> list:
    hosts = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                hosts.append(line)
    return hosts


def main():
    parser = argparse.ArgumentParser(
        description="Live uptime monitor for NOC operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python uptime_monitor.py 192.168.1.1 8.8.8.8 1.1.1.1
  python uptime_monitor.py --file hosts.txt --interval 30
  python uptime_monitor.py 10.0.0.1 10.0.0.2 --interval 60 --log uptime.csv

Formato hosts.txt:
  # Comentarios con #
  192.168.1.1
  192.168.1.254
  8.8.8.8
        """,
    )
    parser.add_argument("hosts",            nargs="*",          help="IPs a monitorear")
    parser.add_argument("--file",    "-f",                      help="Archivo con lista de hosts")
    parser.add_argument("--interval","-i",  type=int, default=60, help="Intervalo en segundos (default: 60)")
    parser.add_argument("--log",     "-l",                      help="Guardar historial en CSV")
    args = parser.parse_args()

    hosts = list(args.hosts or [])
    if args.file:
        hosts += load_hosts_file(args.file)
    if not hosts:
        console.print("[red]Error:[/] Especifica al menos un host o usa --file")
        sys.exit(1)

    monitor(hosts, args.interval, args.log)


if __name__ == "__main__":
    main()
