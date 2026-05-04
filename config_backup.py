#!/usr/bin/env python3
"""
config_backup.py – SSH configuration backup for network devices and Linux servers
Usage:
    python config_backup.py 192.168.1.1 --user admin --type cisco
    python config_backup.py 192.168.1.1 --user root --type linux
    python config_backup.py --hosts devices.csv --output ./backups
"""

import argparse
import csv
import difflib
import sys
import os
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import paramiko
except ImportError:
    print("Instala paramiko: pip install paramiko")
    sys.exit(1)

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt
from rich import box

console = Console()

# Comandos por tipo de dispositivo
DEVICE_COMMANDS = {
    "cisco":      ["show running-config"],
    "cisco-nx":   ["show running-config"],
    "arista":     ["show running-config"],
    "huawei":     ["display current-configuration"],
    "linux":      ["cat /etc/network/interfaces", "ip addr show", "ip route show", "iptables -L -n"],
    "mikrotik":   ["/export"],
    "fortinet":   ["show full-configuration"],
}

SUPPORTED_TYPES = list(DEVICE_COMMANDS.keys())


class BackupResult:
    def __init__(self, ip: str, hostname: str, device_type: str):
        self.ip          = ip
        self.hostname    = hostname
        self.device_type = device_type
        self.success     = False
        self.error       = ""
        self.config      = ""
        self.backup_path = ""
        self.changed     = False
        self.diff_lines  = 0


def ssh_connect(ip: str, user: str, password: str = None,
                key_path: str = None, port: int = 22, timeout: int = 15) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = dict(hostname=ip, username=user, port=port, timeout=timeout)
    if key_path:
        kwargs["key_filename"] = key_path
    elif password:
        kwargs["password"] = password
    else:
        raise ValueError("Se requiere contraseña o clave SSH")
    client.connect(**kwargs)
    return client


def run_commands(client: paramiko.SSHClient, commands: list) -> str:
    output_parts = []
    for cmd in commands:
        _, stdout, stderr = client.exec_command(cmd, timeout=30)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        if out.strip():
            output_parts.append(f"# {cmd}\n{out}")
        if err.strip():
            output_parts.append(f"# STDERR: {err}")
    return "\n".join(output_parts)


def backup_device(ip: str, user: str, password: str, key_path: str,
                  device_type: str, port: int, output_dir: Path) -> BackupResult:
    result = BackupResult(ip=ip, hostname=ip, device_type=device_type)
    commands = DEVICE_COMMANDS.get(device_type, DEVICE_COMMANDS["linux"])

    try:
        client = ssh_connect(ip, user, password, key_path, port)

        # Intentar resolver hostname real
        try:
            _, out, _ = client.exec_command("hostname", timeout=5)
            result.hostname = out.read().decode().strip() or ip
        except Exception:
            pass

        result.config = run_commands(client, commands)
        client.close()

        # Guardar backup
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_ip  = ip.replace(".", "_")
        filename = f"{safe_ip}_{device_type}_{ts}.txt"
        filepath = output_dir / filename
        filepath.write_text(result.config, encoding="utf-8")
        result.backup_path = str(filepath)

        # Detectar cambios vs backup anterior
        prev = _find_previous_backup(output_dir, safe_ip, device_type, filename)
        if prev:
            old_text = prev.read_text(encoding="utf-8")
            diff = list(difflib.unified_diff(
                old_text.splitlines(), result.config.splitlines(),
                lineterm=""
            ))
            if diff:
                result.changed    = True
                result.diff_lines = len(diff)
                diff_path = output_dir / f"{safe_ip}_{device_type}_{ts}.diff"
                diff_path.write_text("\n".join(diff), encoding="utf-8")

        result.success = True

    except Exception as e:
        result.error = str(e)

    return result


def _find_previous_backup(output_dir: Path, safe_ip: str, device_type: str,
                          current: str) -> Path:
    pattern = f"{safe_ip}_{device_type}_*.txt"
    backups = sorted(output_dir.glob(pattern))
    # Excluir el que acabamos de crear
    others = [b for b in backups if b.name != current]
    return others[-1] if others else None


def run(args):
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Recopilar dispositivos
    devices = []
    if args.hosts:
        with open(args.hosts, newline="") as f:
            for row in csv.DictReader(f):
                devices.append(row)
    else:
        devices.append({
            "ip": args.ip,
            "user": args.user or "",
            "type": args.type or "linux",
            "port": str(args.port or 22),
        })

    # Pedir contraseña si no hay clave
    password = None
    if not args.key:
        password = Prompt.ask(
            f"  Contraseña SSH para [cyan]{args.user or 'usuario'}[/]",
            password=True
        ) if not args.password else args.password

    console.print()
    console.rule("[bold cyan]NOC TOOLKIT[/] · Config Backup")
    console.print(f"  Dispositivos : [cyan]{len(devices)}[/]")
    console.print(f"  Destino      : [cyan]{output_dir.resolve()}[/]\n")

    results: list[BackupResult] = []

    def do_backup(dev):
        return backup_device(
            ip          = dev["ip"],
            user        = dev.get("user", args.user or ""),
            password    = password,
            key_path    = args.key,
            device_type = dev.get("type", args.type or "linux"),
            port        = int(dev.get("port", args.port or 22)),
            output_dir  = output_dir,
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("  Realizando backups...", total=len(devices))
        workers = min(args.workers, len(devices))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(do_backup, dev): dev for dev in devices}
            for fut in as_completed(futures):
                results.append(fut.result())
                progress.advance(task)

    # Tabla de resultados
    table = Table(box=box.SIMPLE_HEAD, border_style="dim", expand=True)
    table.add_column("HOST",     style="cyan",  min_width=16)
    table.add_column("TIPO",     style="dim",   min_width=10)
    table.add_column("ESTADO",   justify="center", min_width=8)
    table.add_column("CAMBIOS",  justify="center", min_width=8)
    table.add_column("ARCHIVO",  style="dim")
    table.add_column("ERROR",    style="red dim")

    ok_count = sum(1 for r in results if r.success)

    for r in sorted(results, key=lambda x: x.ip):
        status  = "[green]OK[/]"    if r.success else "[red]FAIL[/]"
        changed = "[yellow]SÍ[/]"   if r.changed else "[dim]No[/]"
        fname   = Path(r.backup_path).name if r.backup_path else "—"
        if r.changed:
            changed = f"[yellow]SÍ[/] [dim](+{r.diff_lines} líneas)[/]"
        table.add_row(
            r.hostname,
            r.device_type,
            status,
            changed if r.success else "[dim]—[/]",
            fname,
            r.error[:60] if r.error else "",
        )

    console.print(table)
    console.print(
        f"  Resultado: [green]{ok_count} exitosos[/]  [red]{len(results)-ok_count} fallidos[/]  "
        f"·  Backups en [cyan]{output_dir.resolve()}[/]\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="SSH config backup for network devices and Linux servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Tipos soportados: {', '.join(SUPPORTED_TYPES)}

Ejemplos:
  python config_backup.py 192.168.1.1 --user admin --type cisco
  python config_backup.py 192.168.1.1 --user root --type linux --key ~/.ssh/id_rsa
  python config_backup.py --hosts devices.csv --output ./backups --workers 5

Formato devices.csv:
  ip,user,type,port
  192.168.1.1,admin,cisco,22
  192.168.1.2,root,linux,22
  10.0.0.1,admin,arista,22
        """,
    )
    parser.add_argument("ip",                 nargs="?",              help="IP del dispositivo")
    parser.add_argument("--user",     "-u",                           help="Usuario SSH")
    parser.add_argument("--password", "-p",                           help="Contraseña SSH")
    parser.add_argument("--key",      "-k",                           help="Ruta a clave privada SSH")
    parser.add_argument("--type",     "-t",   choices=SUPPORTED_TYPES, default="linux", help="Tipo de dispositivo")
    parser.add_argument("--port",             type=int, default=22,   help="Puerto SSH (default: 22)")
    parser.add_argument("--hosts",            help="CSV con lista de dispositivos")
    parser.add_argument("--output",   "-o",   default="./backups",    help="Directorio de destino (default: ./backups)")
    parser.add_argument("--workers",  "-w",   type=int, default=5,    help="Backups en paralelo (default: 5)")
    args = parser.parse_args()

    if not args.hosts and not args.ip:
        parser.print_help()
        sys.exit(1)

    run(args)


if __name__ == "__main__":
    main()
