#!/usr/bin/env python3
"""Forja de Historias: un narrador interactivo de consola, sin inteligencia artificial.

Uso:
    python jugar.py                 partida interactiva (continúa la última si la hay)
    python jugar.py --nueva         empieza de cero aunque haya una partida guardada
    python jugar.py --aleatorio     todos los parámetros al azar
    python jugar.py --demo          una partida entera que se juega sola
    python jugar.py --semilla 42    repite exactamente un mundo
    python jugar.py --notas         muestra de qué obra sale cada escena
    python jugar.py --opciones      enseña siempre la lista de opciones

Durante la partida escribes con tus palabras lo que quieres hacer («?» te da ideas).
Escribe /ayuda para ver los comandos (deshacer, guardar, reintentar...).
"""

import argparse
import random
import sys
from pathlib import Path

from forja.consola import Consola, Demo
from forja.generador import nombre_al_azar
from forja.lexico import ARQUETIPOS, FALLAS, GENEROS, TONOS, TRAMAS
from forja.modelo import Params
from forja.sesion import ErrorCarga, Salir, Sesion, leer_guardado

RAIZ = Path(__file__).resolve().parent
CARPETA_LIBROS = RAIZ / "historias"
CARPETA_PARTIDAS = RAIZ / "partidas"
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


def _partida_en_curso(ui, args):
    """Ofrece continuar la partida automática; devuelve el guardado o None."""
    if args.demo or args.nueva or args.aleatorio or args.semilla is not None:
        return None
    auto = leer_guardado(CARPETA_PARTIDAS / "auto.json")
    if not auto or auto.get("terminada"):
        return None
    pregunta = (f"Hay una partida en curso de {auto['heroe']} («{auto['titulo']}», "
                f"capítulo {auto['capitulo']}, {auto['hora']}). ¿Continuarla?")
    return auto if ui.si_no(pregunta) else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--semilla", type=int, help="repite un mundo concreto")
    ap.add_argument("--nueva", action="store_true",
                    help="empieza de cero aunque haya una partida guardada")
    ap.add_argument("--aleatorio", action="store_true",
                    help="elige todos los parámetros al azar")
    ap.add_argument("--demo", action="store_true",
                    help="juega sola una partida completa")
    ap.add_argument("--notas", action="store_true",
                    help="muestra las fuentes de cada escena")
    ap.add_argument("--opciones", action="store_true",
                    help="enseña siempre la lista de opciones (por defecto escribes tú)")
    ap.add_argument("--sin-color", action="store_true")
    ap.add_argument("--sin-pausas", action="store_true")
    ap.add_argument("--no-guardar", action="store_true",
                    help="no ofrece guardar el libro al terminar")
    args = ap.parse_args(argv)

    semilla_demo = args.semilla if args.semilla is not None else random.randrange(10**6)
    if args.demo:
        args.semilla = semilla_demo
        ui = Demo(semilla_demo, color=not args.sin_color, notas=args.notas)
    else:
        ui = Consola(color=not args.sin_color, notas=args.notas,
                     pausas=not args.sin_pausas,
                     modo="opciones" if args.opciones else "libre")

    ses = None
    try:
        auto = _partida_en_curso(ui, args)
        if auto:
            params, registros = Params(**auto["params"]), auto["registros"]
        else:
            params, registros = pedir_parametros(ui, args), []
        ses = Sesion(ui, params, CARPETA_PARTIDAS, CARPETA_LIBROS)
        ses.guardar_auto = not args.demo
        ses.reanudar(registros)
        try:
            final = ses.ejecutar()
        except ErrorCarga as exc:
            print()
            ui.parrafo(f"No pude retomar esa partida ({exc}). Empezamos una nueva.")
            ses = Sesion(ui, pedir_parametros(ui, args), CARPETA_PARTIDAS, CARPETA_LIBROS)
            final = ses.ejecutar()
        ui.bibliografia(ses.w)
        if not (args.no_guardar or args.demo):
            if ui.si_no("¿Guardar tu historia como libro (Markdown)?"):
                ui.parrafo(f"Guardado en: {ses.guardar_libro(final)}")
    except (Salir, KeyboardInterrupt, EOFError):
        print("\n")
        ui.parrafo("La historia queda en pausa"
                   + (" (guardada en «auto»: vuelve a ejecutar jugar.py para seguir)."
                      if ses is not None and ses.guardar_auto else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
