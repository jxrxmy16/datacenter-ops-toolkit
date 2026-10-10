"""Exporta la partida como un libro en Markdown.

Cada partida deja un librojuego ya leído: capítulos con las doce etapas del
viaje, la decisión tomada en cada escena (en cursiva), el final y las notas
bibliográficas de lo que realmente apareció.
"""

import re
from pathlib import Path

from .fuentes import FUENTES, agrupar, nota
from .lexico import ARQUETIPOS, FALLAS, GENEROS, TONOS, TRAMAS


def a_markdown(w, final) -> str:
    p = w.params
    lineas = [
        f"# {w.titulo()}",
        "",
        f"*Crónica de {w.heroe.nombre}* — {GENEROS[p.genero]['nombre']} · "
        f"{TRAMAS[p.trama]['nombre']} · tono {TONOS[p.tono]['nombre'].lower()} · "
        f"{ARQUETIPOS[p.arquetipo]['nombre'].lower()} con "
        f"{FALLAS[p.falla]['nombre'].lower()} · semilla `{p.semilla}`",
        "",
    ]
    for cap in w.cronica:
        lineas += [f"## Capítulo {cap.etapa}. {cap.titulo}", ""]
        for bloque in cap.bloques:
            for parrafo in bloque.texto:
                lineas += [parrafo, ""]
            if bloque.eleccion:
                lineas += [f"> *{bloque.eleccion}*", ""]
            for parrafo in bloque.resultado:
                lineas += [parrafo, ""]
    lineas += ["---", "", f"### {final.titulo}", ""]

    lineas += ["## Notas y fuentes", "",
               "Esta historia se generó sin inteligencia artificial, con reglas "
               "inspiradas en estas obras:", ""]
    for titulo, claves in agrupar(w.fuentes_usadas).items():
        lineas += [f"**{titulo}**", ""]
        lineas += [f"- {FUENTES[c].cita}" for c in claves]
        lineas.append("")
    lineas += ["", "### Qué escena recuerda a qué", ""]
    vistas = set()
    for cap in w.cronica:
        for bloque in cap.bloques:
            for clave, detalle in bloque.fuentes:
                par = (cap.etapa, clave, detalle)
                if par not in vistas:
                    vistas.add(par)
                    lineas.append(f"- Cap. {cap.etapa} — {nota(clave, detalle)}")
    return "\n".join(lineas) + "\n"


def nombre_archivo(w) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", w.titulo().lower()).strip("-")
    return f"{base}-{w.params.semilla}.md"


def guardar(w, final, carpeta) -> Path:
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre_archivo(w)
    ruta.write_text(a_markdown(w, final), encoding="utf-8")
    return ruta
