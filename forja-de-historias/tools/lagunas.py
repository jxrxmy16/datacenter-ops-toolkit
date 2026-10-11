#!/usr/bin/env python3
"""Lista las palabras que el intérprete NO conoce, por intención, en un corpus.

    python tools/lagunas.py corpus.json                 resumen por intención
    python tools/lagunas.py corpus.json --clase duda    solo una intención
    python tools/lagunas.py corpus.json --json lagunas.json

Una «laguna» es una palabra de 4 o más letras que no casa con nada del léxico (ni
con una errata corregible), no es una palabra de relleno ni un modificador de
dificultad. Las frases en las que NO se reconoce ninguna palabra se cuentan aparte
(«sin_pista»): son las que el intérprete deja en «desconocida».

Sirve para saber qué vocabulario falta, no para copiarlo: el objetivo es ampliar
FAMILIAS (sinónimos, derivados) alrededor de lo que se echa en falta.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

from test_forja import jugar_partida                       # noqa: E402
from forja import lenguaje                                 # noqa: E402


def lagunas(frases, mundos):
    """Devuelve ({clase: Counter(palabra)}, {clase: [frases sin pista]}, aciertos)."""
    por_clase = defaultdict(Counter)
    sin_pista = defaultdict(list)
    for i, d in enumerate(frases):
        w = mundos[i % len(mundos)]
        _, norm = lenguaje.tokenizar(" ".join(d["frase"].split()))
        alias = lenguaje._alias(w)
        mods = set()
        for patron, _, _ in lenguaje.MODIFICADORES:
            ids = lenguaje._ventana(norm, patron)
            if ids is not None:
                mods.update(ids)
        conocidas = 0
        for j, t in enumerate(norm):
            if len(t) < 4 or t in lenguaje._RELLENO or t in alias or j in mods:
                continue
            if t in lenguaje._FUNCIONALES or t in lenguaje._AUXILIARES:
                continue
            if lenguaje.coincidencias(t) or lenguaje._corregir(t):
                conocidas += 1
                continue
            por_clase[d["clase"]][t] += 1
        r = lenguaje.analizar(d["frase"], w)
        if r.clase == "desconocida" and d["clase"] != "desconocida":
            sin_pista[d["clase"]].append(d["frase"])
    return por_clase, sin_pista


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("--clase")
    ap.add_argument("--top", type=int, default=60)
    ap.add_argument("--json")
    args = ap.parse_args()

    frases = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    mundos = []
    for s in (3, 11, 20, 31):
        w, _ = jugar_partida(s)
        w.etapa = 6
        mundos.append(w)
    por_clase, sin_pista = lagunas(frases, mundos)
    if args.json:
        Path(args.json).write_text(json.dumps(
            {c: {"palabras": dict(cnt.most_common()), "sin_pista": sin_pista.get(c, [])}
             for c, cnt in por_clase.items()}, ensure_ascii=False, indent=1), encoding="utf-8")
    for clase in sorted(por_clase):
        if args.clase and clase != args.clase:
            continue
        cnt = por_clase[clase]
        print(f"\n== {clase}: {sum(cnt.values())} apariciones de {len(cnt)} palabras "
              f"desconocidas; {len(sin_pista.get(clase, []))} frases sin pista")
        print("  " + ", ".join(f"{p}({n})" for p, n in cnt.most_common(args.top)))


if __name__ == "__main__":
    main()
