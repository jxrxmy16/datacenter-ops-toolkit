#!/usr/bin/env python3
"""Compila los vocabularios por intención (JSON) en forja/vocabulario.py.

    python tools/compilar_vocabulario.py vocab/valor.json vocab/ingenio.json ...

Normaliza (minúsculas, sin tildes), descarta lo inservible (raíces de menos de
4 letras, entradas con espacios, pesos fuera de rango), elimina duplicados y
escribe un módulo Python ordenado, para que los cambios se vean bien en git.
"""

import json
import pprint
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from forja.lenguaje import CLASES, quitar_tildes           # noqa: E402

SALIDA = RAIZ / "forja" / "vocabulario.py"
CABECERA = SALIDA.read_text(encoding="utf-8").split("VOCABULARIO = ")[0].rstrip() + "\n\n"


def _item(texto: str):
    """'palabra:0.5' -> (palabra normalizada, peso) o None si no vale."""
    palabra, _, p = quitar_tildes(str(texto)).strip().partition(":")
    palabra = palabra.strip()
    if not palabra or " " in palabra:
        return None
    try:
        peso = float(p) if p else 1.0
    except ValueError:
        return None
    return (palabra, round(peso, 2)) if 0 < peso <= 2 else None


def _unir(items, minimo=1, verbos=False):
    """Deduplica conservando el mayor peso; devuelve cadenas ordenadas."""
    mejor = {}
    for x in items:
        if verbos:                                  # "almorzar|almuerz:0.5"
            cuerpo, _, p = str(x).partition(":")
            partes = [quitar_tildes(t).strip() for t in cuerpo.split("|") if t.strip()]
            if not partes or " " in partes[0]:
                continue
            try:
                peso = float(p) if p else 1.0
            except ValueError:
                continue
            clave, valor = partes[0], ("|".join(partes), peso)
            if clave not in mejor or peso > mejor[clave][1]:
                mejor[clave] = valor
            continue
        r = _item(x)
        if r and len(r[0]) >= minimo and (r[0] not in mejor or r[1] > mejor[r[0]]):
            mejor[r[0]] = r[1]
    if verbos:
        return sorted(f"{c}:{p:g}" if p != 1.0 else c for c, p in mejor.values())
    return sorted(f"{w}:{p:g}" if p != 1.0 else w for w, p in mejor.items())


def compilar(rutas):
    salida = {}
    for ruta in rutas:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        for clase, d in datos.items():
            if clase not in CLASES:
                print(f"  (ignorada la clave desconocida «{clase}» de {ruta})")
                continue
            s = salida.setdefault(clase, {"verbos": [], "raices": [], "exactas": [], "frases": []})
            s["verbos"] += d.get("verbos", [])
            s["raices"] += d.get("raices", [])
            s["exactas"] += d.get("exactas", [])
            s["frases"] += d.get("frases", [])
    final = {}
    for clase in CLASES:
        if clase not in salida:
            continue
        s = salida[clase]
        frases, vistas = [], set()
        for entrada in s["frases"]:
            try:
                patron, peso = (entrada["patron"], entrada["peso"]) if isinstance(entrada, dict) else entrada
                patron = [t if ("*" in t or "|" in t or t == "@hacer") else quitar_tildes(t) for t in patron]
                clave = (tuple(patron), clase)
                if clave in vistas or not (0 < float(peso) <= 3) or not 1 <= len(patron) <= 4:
                    continue
                vistas.add(clave)
                frases.append([patron, round(float(peso), 2)])
            except (TypeError, ValueError, KeyError):
                continue
        final[clase] = {
            "verbos": _unir(s["verbos"], verbos=True),
            "raices": [r for r in _unir(s["raices"]) if len(r.partition(":")[0]) >= 4],
            "exactas": _unir(s["exactas"]),
            "frases": sorted(frases),
        }
    return final


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    final = compilar(sys.argv[1:])
    cuerpo = pprint.pformat(final, width=96, sort_dicts=False, compact=True)
    SALIDA.write_text(CABECERA + "VOCABULARIO = " + cuerpo + "\n", encoding="utf-8")
    for clase, d in final.items():
        print(f"{clase:10s} {len(d['verbos']):4d} verbos {len(d['raices']):4d} raíces "
              f"{len(d['exactas']):4d} exactas {len(d['frases']):3d} frases")
    print(f"escrito {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
