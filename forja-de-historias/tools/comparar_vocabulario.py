#!/usr/bin/env python3
"""Mide qué gana y qué rompe un vocabulario adicional, frase a frase.

    python tools/comparar_vocabulario.py extra.json [corpus.json ...]

Sin corpus, usa los dos de desarrollo (tests/datos). Compara el intérprete tal
cual contra el intérprete con el vocabulario adicional y enseña:
  * aciertos y fallos antes/después, por intención;
  * las frases que ANTES acertaba y AHORA fallan (regresiones), con la palabra
    que las provoca;
  * cuántas frases nuevas se aciertan.

Formato de `extra.json` (todas las claves opcionales, por intención):
  {"valor": {"verbos": ["acometer", "almorzar|almuerz"],
             "raices": ["guantaz", "mendrug:0.5"],
             "exactas": ["tentempie"],
             "frases": [[["tom*", "aire"], 1.5]]}, ...}
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

from test_forja import jugar_partida                       # noqa: E402
from forja import lenguaje                                 # noqa: E402

DESARROLLO = [RAIZ / "tests" / "datos" / "corpus_frases.json",
              RAIZ / "tests" / "datos" / "corpus_validacion.json"]


def mundos():
    ws = []
    for s in (3, 11, 20, 31):
        w, _ = jugar_partida(s)
        w.etapa = 6
        ws.append(w)
    return ws


def predecir(frases, ws):
    return [lenguaje.analizar(f["frase"], ws[i % len(ws)]) for i, f in enumerate(frases)]


def aciertos(frases, preds):
    return [p.clase == f["clase"] for f, p in zip(frases, preds)]


def culpables(frase, w, antes):
    """Palabras cuya lectura cambió con el vocabulario nuevo."""
    orig, norm = lenguaje.tokenizar(frase)
    return [(o, lenguaje.coincidencias(n)) for o, n in zip(orig, norm)
            if lenguaje.coincidencias(n) != antes.get(n)]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    extra = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rutas = [Path(p) for p in sys.argv[2:]] or DESARROLLO
    ws = mundos()
    total_antes = total_despues = n_total = 0
    regresiones, ganancias = [], 0
    for ruta in rutas:
        frases = json.loads(ruta.read_text(encoding="utf-8"))
        lenguaje.reconstruir(None)
        antes_p = predecir(frases, ws)
        base_tokens = {}
        for f in frases:
            for n in lenguaje.tokenizar(f["frase"])[1]:
                base_tokens[n] = lenguaje.coincidencias(n)
        lenguaje.reconstruir(extra)
        despues_p = predecir(frases, ws)
        a, d = aciertos(frases, antes_p), aciertos(frases, despues_p)
        n_total += len(frases)
        total_antes += sum(a)
        total_despues += sum(d)
        por_clase = defaultdict(lambda: [0, 0, 0])
        for f, x, y in zip(frases, a, d):
            por_clase[f["clase"]][0] += 1
            por_clase[f["clase"]][1] += x
            por_clase[f["clase"]][2] += y
        print(f"\n{ruta.name}: {sum(a)}/{len(frases)} -> {sum(d)}/{len(frases)} "
              f"({100*sum(a)/len(frases):.1f}% -> {100*sum(d)/len(frases):.1f}%)")
        for c in sorted(por_clase):
            n, x, y = por_clase[c]
            print(f"   {c:12s} {x:3d} -> {y:3d} / {n}")
        for i, (f, x, y) in enumerate(zip(frases, a, d)):
            if x and not y:
                regresiones.append((f, despues_p[i].clase, culpables(f["frase"], ws[0], base_tokens)))
            elif y and not x:
                ganancias += 1
    print(f"\nTOTAL: {total_antes}/{n_total} -> {total_despues}/{n_total} "
          f"({100*total_antes/n_total:.1f}% -> {100*total_despues/n_total:.1f}%)   "
          f"ganancias {ganancias}, regresiones {len(regresiones)}")
    if regresiones:
        print("\nREGRESIONES (acertaba antes, falla ahora):")
        for f, nueva, culp in regresiones[:60]:
            palabras = "; ".join(f"{o}->{sorted(m)}" for o, m in culp) or "(sin palabra clara)"
            print(f"  [{f['clase']} -> {nueva}] {f['frase']}   <- {palabras}")
    lenguaje.reconstruir(None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
