#!/usr/bin/env python3
"""Mide cuántas frases del corpus interpreta bien el intérprete de texto libre.

    python tools/evaluar_corpus.py                 resumen
    python tools/evaluar_corpus.py --fallos        lista las frases mal interpretadas
    python tools/evaluar_corpus.py --clase hablar  solo una clase
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
from forja.lenguaje import analizar                        # noqa: E402

CORPUS = RAIZ / "tests" / "datos" / "corpus_frases.json"


def evaluar(fichero=CORPUS, semillas=(3, 11, 20, 31)):
    corpus = json.loads(Path(fichero).read_text(encoding="utf-8"))
    mundos = []
    for s in semillas:
        w, _ = jugar_partida(s)
        w.etapa = 6
        mundos.append(w)
    filas = []
    for i, d in enumerate(corpus):
        w = mundos[i % len(mundos)]          # reparte las frases entre universos
        r = analizar(d["frase"], w)
        filas.append((d, r))
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fallos", action="store_true")
    ap.add_argument("--clase")
    ap.add_argument("--fichero", default=str(CORPUS))
    args = ap.parse_args()

    filas = evaluar(args.fichero)
    ok = Counter()
    total = Counter()
    confusion = defaultdict(Counter)
    mod_ok = mod_tot = 0
    fallos = []
    for d, r in filas:
        esperada = d["clase"]
        if args.clase and esperada != args.clase:
            continue
        total[esperada] += 1
        confusion[esperada][r.clase] += 1
        if r.clase == esperada:
            ok[esperada] += 1
        else:
            fallos.append((d, r))
        if d.get("modificador") in ("dificil", "facil"):
            mod_tot += 1
            if (d["modificador"] == "dificil" and r.dd > 0) or \
               (d["modificador"] == "facil" and r.dd < 0):
                mod_ok += 1
    n = sum(total.values())
    print(f"Intención: {sum(ok.values())}/{n} = {100*sum(ok.values())/n:.1f}%")
    for c in sorted(total):
        print(f"  {c:12s} {ok[c]:3d}/{total[c]:3d}  {100*ok[c]/total[c]:5.1f}%   "
              + ", ".join(f"{k}:{v}" for k, v in confusion[c].most_common(4) if k != c))
    if mod_tot:
        print(f"Modificadores de dificultad: {mod_ok}/{mod_tot} = {100*mod_ok/mod_tot:.1f}%")
    if args.fallos:
        print("\nFallos (esperada -> obtenida):")
        for d, r in fallos:
            print(f"  [{d['clase']:10s} -> {r.clase:11s}] {d['frase']}  {r.puntos}")


if __name__ == "__main__":
    main()
