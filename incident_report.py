#!/usr/bin/env python3
"""
incident_report.py – NOC incident report generator (HTML)
Usage:
    python incident_report.py                               # modo interactivo
    python incident_report.py --from-log uptime.csv        # desde log de uptime_monitor
    python incident_report.py --json incident.json         # desde archivo JSON
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import box
from rich.table import Table

console = Console()

SEVERITY_COLOR = {
    "CRÍTICO":  "#dc2626",
    "ALTO":     "#ea580c",
    "MEDIO":    "#ca8a04",
    "BAJO":     "#16a34a",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Reporte de Incidente – {incident_id}</title>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#f8fafc; color:#1e293b; font-size:10pt; }}
    .header {{ background:#0f172a; color:#fff; padding:28px 40px; }}
    .header h1 {{ font-size:20pt; font-weight:700; margin-bottom:4px; }}
    .header .meta {{ color:#94a3b8; font-size:9pt; }}
    .severity {{ display:inline-block; padding:3px 12px; border-radius:4px; font-weight:700;
                 font-size:9pt; color:#fff; background:{severity_color}; margin-left:12px; }}
    .body {{ max-width:960px; margin:0 auto; padding:32px 40px; }}
    .section {{ margin-bottom:28px; }}
    h2 {{ font-size:11pt; font-weight:700; color:#0f172a; border-bottom:2px solid #e2e8f0;
          padding-bottom:6px; margin-bottom:14px; text-transform:uppercase; letter-spacing:0.5px; }}
    .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .card {{ background:#fff; border:1px solid #e2e8f0; border-radius:6px; padding:16px; }}
    .card label {{ font-size:7.5pt; font-weight:700; color:#94a3b8; text-transform:uppercase;
                   letter-spacing:0.8px; display:block; margin-bottom:4px; }}
    .card .value {{ font-size:10.5pt; color:#1e293b; font-weight:500; }}
    table {{ width:100%; border-collapse:collapse; font-size:9.5pt; }}
    th {{ background:#f1f5f9; padding:8px 12px; text-align:left; font-weight:700;
          font-size:8pt; text-transform:uppercase; letter-spacing:0.5px; color:#475569; }}
    td {{ padding:8px 12px; border-bottom:1px solid #f1f5f9; }}
    tr:last-child td {{ border-bottom:none; }}
    .badge-up   {{ color:#16a34a; font-weight:700; }}
    .badge-down {{ color:#dc2626; font-weight:700; }}
    .timeline {{ list-style:none; }}
    .timeline li {{ display:flex; gap:16px; padding:10px 0; border-bottom:1px solid #f1f5f9; }}
    .timeline .ts {{ color:#94a3b8; font-size:8.5pt; white-space:nowrap; min-width:80px; }}
    .timeline .event {{ font-size:9.5pt; }}
    .steps {{ counter-reset:step; }}
    .steps li {{ counter-increment:step; display:flex; gap:12px; margin-bottom:10px;
                 align-items:flex-start; font-size:9.5pt; line-height:1.5; }}
    .steps li::before {{ content:counter(step); background:#0f172a; color:#fff; border-radius:50%;
                         min-width:22px; height:22px; display:flex; align-items:center;
                         justify-content:center; font-size:8pt; font-weight:700; }}
    .footer {{ text-align:center; color:#94a3b8; font-size:8pt; padding:20px; border-top:1px solid #e2e8f0; }}
    pre {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:12px;
           font-size:8.5pt; white-space:pre-wrap; word-break:break-word; }}
    @media print {{
      body {{ background:#fff; }}
      .card, table {{ break-inside:avoid; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>
    Reporte de Incidente
    <span class="severity">{severity}</span>
  </h1>
  <div class="meta">
    ID: <strong>{incident_id}</strong> &nbsp;·&nbsp;
    Generado: {generated_at} &nbsp;·&nbsp;
    Operador: {operator}
  </div>
</div>

<div class="body">

  <div class="section">
    <h2>Resumen</h2>
    <div class="card">
      <label>Título</label>
      <div class="value">{title}</div>
    </div>
    <div class="grid-2" style="margin-top:12px;">
      <div class="card"><label>Inicio</label><div class="value">{start_time}</div></div>
      <div class="card"><label>Fin / Resolución</label><div class="value">{end_time}</div></div>
      <div class="card"><label>Duración</label><div class="value">{duration}</div></div>
      <div class="card"><label>Causa Raíz</label><div class="value">{root_cause}</div></div>
    </div>
  </div>

  <div class="section">
    <h2>Descripción</h2>
    <div class="card">
      <pre>{description}</pre>
    </div>
  </div>

  <div class="section">
    <h2>Hosts Afectados</h2>
    <table>
      <tr>
        <th>Host / IP</th>
        <th>Estado</th>
        <th>Tiempo Caído</th>
        <th>Última Latencia</th>
        <th>Notas</th>
      </tr>
      {hosts_rows}
    </table>
  </div>

  <div class="section">
    <h2>Timeline</h2>
    <ul class="timeline">
      {timeline_items}
    </ul>
  </div>

  <div class="section">
    <h2>Pasos de Resolución</h2>
    <ol class="steps">
      {steps_items}
    </ol>
  </div>

  <div class="section">
    <h2>Lecciones Aprendidas</h2>
    <div class="card">
      <pre>{lessons}</pre>
    </div>
  </div>

</div>

<div class="footer">
  Generado por <strong>datacenter-ops-toolkit · incident_report.py</strong> &nbsp;·&nbsp; {generated_at}
</div>

</body>
</html>
"""


def interactive_mode() -> dict:
    console.print()
    console.rule("[bold cyan]NOC TOOLKIT[/] · Generador de Reportes de Incidentes")
    console.print("[dim]  Completa los datos del incidente. Ctrl+C para cancelar.\n[/]")

    severities = ["BAJO", "MEDIO", "ALTO", "CRÍTICO"]

    data = {}
    data["incident_id"] = Prompt.ask("  ID del incidente", default=f"INC-{datetime.now().strftime('%Y%m%d-%H%M')}")
    data["title"]       = Prompt.ask("  Título del incidente")
    data["operator"]    = Prompt.ask("  Operador responsable")
    data["severity"]    = Prompt.ask("  Severidad", choices=severities, default="MEDIO")
    data["start_time"]  = Prompt.ask("  Inicio del incidente (ej: 2025-08-15 02:30)")
    data["end_time"]    = Prompt.ask("  Fin / Resolución (dejar vacío si sigue activo)", default="En curso")
    data["root_cause"]  = Prompt.ask("  Causa raíz")
    data["description"] = Prompt.ask("  Descripción del incidente")

    console.print("\n  [dim]Hosts afectados (ingresa IPs separadas por coma):[/]")
    hosts_raw = Prompt.ask("  Hosts")
    data["hosts"] = [{"ip": h.strip(), "status": "Afectado", "down_time": "—", "latency": "—", "notes": ""} for h in hosts_raw.split(",") if h.strip()]

    console.print("\n  [dim]Timeline (un evento por línea, formato: HH:MM - descripción):[/]")
    console.print("  [dim]Ingresa una línea vacía para terminar.[/]")
    timeline = []
    while True:
        line = Prompt.ask("  ")
        if not line:
            break
        timeline.append(line)
    data["timeline"] = timeline

    console.print("\n  [dim]Pasos de resolución (uno por línea, vacío para terminar):[/]")
    steps = []
    while True:
        line = Prompt.ask("  ")
        if not line:
            break
        steps.append(line)
    data["steps"] = steps

    data["lessons"] = Prompt.ask("\n  Lecciones aprendidas", default="—")
    return data


def from_log(log_path: str) -> dict:
    records = []
    with open(log_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    if not records:
        console.print("[red]Error:[/] El log está vacío.")
        sys.exit(1)

    # Analizar hosts con caídas
    host_data = {}
    for r in records:
        ip = r["ip"]
        if ip not in host_data:
            host_data[ip] = {"up": 0, "down": 0, "down_start": None, "down_total": 0}
        if r["alive"] in ("True", "true", "1"):
            host_data[ip]["up"] += 1
        else:
            host_data[ip]["down"] += 1

    hosts = []
    for ip, d in host_data.items():
        total  = d["up"] + d["down"]
        uptime = d["up"] / total * 100 if total else 0
        hosts.append({
            "ip": ip,
            "status": "Recuperado" if d["down"] > 0 else "Operativo",
            "down_time": f"{d['down']} checks caídos ({100-uptime:.1f}%)",
            "latency": "—",
            "notes": f"Total checks: {total}"
        })

    start = records[0]["timestamp"][:16].replace("T", " ")
    end   = records[-1]["timestamp"][:16].replace("T", " ")

    return {
        "incident_id": f"INC-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "title":       f"Incidente detectado en {len(host_data)} hosts",
        "operator":    "NOC",
        "severity":    "MEDIO",
        "start_time":  start,
        "end_time":    end,
        "root_cause":  "Pendiente análisis",
        "description": f"Incidente generado automáticamente desde log: {log_path}",
        "hosts":       hosts,
        "timeline":    [f"{start} - Inicio de monitoreo", f"{end} - Fin del período analizado"],
        "steps":       ["Revisar logs de sistema", "Identificar causa raíz", "Documentar solución"],
        "lessons":     "Pendiente revisión post-incidente.",
    }


def render_html(data: dict, output: str):
    sev_color = SEVERITY_COLOR.get(data.get("severity", "MEDIO"), "#ca8a04")

    # Calcular duración
    try:
        start = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M")
        end   = datetime.strptime(data["end_time"],   "%Y-%m-%d %H:%M")
        delta = end - start
        h, r  = divmod(int(delta.total_seconds()), 3600)
        m     = r // 60
        duration = f"{h}h {m:02}m"
    except Exception:
        duration = "—"

    hosts_rows = ""
    for h in data.get("hosts", []):
        badge = "badge-up" if h.get("status") in ("Operativo", "Recuperado") else "badge-down"
        hosts_rows += f"""
      <tr>
        <td>{h.get('ip','—')}</td>
        <td><span class="{badge}">{h.get('status','—')}</span></td>
        <td>{h.get('down_time','—')}</td>
        <td>{h.get('latency','—')}</td>
        <td>{h.get('notes','')}</td>
      </tr>"""

    timeline_items = ""
    for event in data.get("timeline", []):
        parts = event.split(" - ", 1)
        ts    = parts[0] if len(parts) > 1 else ""
        desc  = parts[1] if len(parts) > 1 else parts[0]
        timeline_items += f'<li><span class="ts">{ts}</span><span class="event">{desc}</span></li>\n'

    steps_items = "\n".join(
        f"<li>{step}</li>" for step in data.get("steps", [])
    )

    html = HTML_TEMPLATE.format(
        incident_id   = data.get("incident_id", "—"),
        title         = data.get("title", "—"),
        severity      = data.get("severity", "MEDIO"),
        severity_color= sev_color,
        operator      = data.get("operator", "—"),
        start_time    = data.get("start_time", "—"),
        end_time      = data.get("end_time", "—"),
        duration      = duration,
        root_cause    = data.get("root_cause", "—"),
        description   = data.get("description", "—"),
        hosts_rows    = hosts_rows,
        timeline_items= timeline_items,
        steps_items   = steps_items,
        lessons       = data.get("lessons", "—"),
        generated_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    Path(output).write_text(html, encoding="utf-8")
    console.print(f"\n  [green]Reporte generado:[/] [cyan]{output}[/]")
    console.print(f"  [dim]Abre el archivo HTML en tu navegador para verlo.[/]\n")


def main():
    parser = argparse.ArgumentParser(
        description="NOC incident report generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python incident_report.py                               # modo interactivo
  python incident_report.py --from-log uptime.csv        # desde log de uptime_monitor
  python incident_report.py --json incident.json         # desde archivo JSON
        """,
    )
    parser.add_argument("--from-log", help="Generar reporte desde CSV de uptime_monitor")
    parser.add_argument("--json",     help="Cargar datos desde archivo JSON")
    parser.add_argument("--output", "-o", default="", help="Archivo de salida (default: INC-YYYYMMDD.html)")
    args = parser.parse_args()

    if args.from_log:
        data = from_log(args.from_log)
    elif args.json:
        with open(args.json) as f:
            data = json.load(f)
    else:
        data = interactive_mode()

    output = args.output or f"{data.get('incident_id', 'incident')}.html"
    render_html(data, output)


if __name__ == "__main__":
    main()
