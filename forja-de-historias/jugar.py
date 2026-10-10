#!/usr/bin/env python3
"""Forja de Historias: un narrador interactivo de consola, sin inteligencia artificial.

Uso:
    python jugar.py                 partida interactiva con menús
    python jugar.py --aleatorio     todos los parámetros al azar
    python jugar.py --demo          una partida entera que se juega sola
    python jugar.py --semilla 42    repite exactamente un mundo
    python jugar.py --notas         muestra de qué obra sale cada escena
"""

import argparse
import random
import sys
from pathlib import Path

from forja.consola import Consola, Demo
from forja.generador import crear_mundo, nombre_al_azar
from forja.libro import guardar
from forja.lexico import ARQUETIPOS, FALLAS, GENEROS, TONOS, TRAMAS
from forja.modelo import Params
from forja.motor import jugar

CARPETA_LIBROS = Path(__file__).resolve().parent / "historias"
PRONOMBRES = [("f", "ella", ""), ("m", "él", ""), ("n", "elle", "")]


def _elegir(ui, titulo, datos, rng, descripcion, azar=True):
    """Menú sobre un diccionario de datos; si se pide azar, elige con `rng`."""
    opciones = [(k, v["nombre"], v.get(descripcion, "")) for k, v in datos.items()]
    clave = ui.menu(titulo, opciones, azar=azar)
    return clave if clave is not None else rng.choice(list(datos))


def pedir_parametros(ui, args):
    semilla = args.semilla if args.semilla is not None else random.randrange(10**6)
    rng = random.Random(semilla ^ 0xA5A5)

    if args.aleatorio or args.demo:
        genero = rng.choice(list(GENEROS))
        tono = rng.choice(list(TONOS))
        trama = rng.choice(list(TRAMAS))
        pronombre = rng.choice(["f", "m", "n"])
        arquetipo = rng.choice(list(ARQUETIPOS))
        falla = rng.choice(list(FALLAS))
        nombre = nombre_al_azar(genero, pronombre, rng)
        return Params(genero, tono, trama, nombre, pronombre, arquetipo, falla,
                      semilla)

    ui.portada("FORJA DE HISTORIAS",
               "Un narrador sin inteligencia artificial. Tú pones los "
               "parámetros y las decisiones; las reglas del viaje del héroe "
               "ponen la lógica. Cada partida es un libro distinto.")
    genero = _elegir(ui, "¿En qué universo transcurre la historia?", GENEROS,
                     rng, "desc")
    tono = _elegir(ui, "¿Qué tono tiene?", TONOS, rng, "desc")
    trama = _elegir(ui, "¿Qué tipo de historia es?", TRAMAS, rng, "desc")
    pronombre = ui.menu("¿Cómo se refiere la historia a tu protagonista?",
                        PRONOMBRES, azar=False)
    nombre = ui.texto("¿Cómo se llama tu protagonista? (Enter = al azar)")
    if not nombre:
        nombre = nombre_al_azar(genero, pronombre, rng)
    arquetipo = _elegir(ui, "¿Qué clase de persona es?", ARQUETIPOS, rng, "desc")
    falla = _elegir(ui, "¿Cuál es su falla? (la historia la pondrá a prueba)",
                    FALLAS, rng, "desc")
    return Params(genero, tono, trama, nombre, pronombre, arquetipo, falla,
                  semilla)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--semilla", type=int, help="repite un mundo concreto")
    ap.add_argument("--aleatorio", action="store_true",
                    help="elige todos los parámetros al azar")
    ap.add_argument("--demo", action="store_true",
                    help="juega sola una partida completa")
    ap.add_argument("--notas", action="store_true",
                    help="muestra las fuentes de cada escena")
    ap.add_argument("--sin-color", action="store_true")
    ap.add_argument("--sin-pausas", action="store_true")
    ap.add_argument("--no-guardar", action="store_true",
                    help="no ofrece guardar el libro al terminar")
    args = ap.parse_args(argv)

    semilla = args.semilla if args.semilla is not None else random.randrange(10**6)
    args.semilla = semilla
    if args.demo:
        ui = Demo(semilla, color=not args.sin_color, notas=args.notas)
    else:
        ui = Consola(color=not args.sin_color, notas=args.notas,
                     pausas=not args.sin_pausas)

    try:
        w = crear_mundo(pedir_parametros(ui, args))
        final = jugar(w, ui)
        ui.bibliografia(w)
        if args.no_guardar or args.demo:
            return 0
        r = input("\n¿Guardar tu historia como libro (Markdown)? [S/n] ").strip()
        if r.lower() not in ("n", "no"):
            ruta = guardar(w, final, CARPETA_LIBROS)
            print(f"Guardado en: {ruta}")
    except (KeyboardInterrupt, EOFError):
        print("\n\nLa historia queda en pausa. Hasta pronto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
