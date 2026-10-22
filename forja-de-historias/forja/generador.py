"""Creación del mundo: reparto, lugares, objetos y secretos, a partir de una semilla.

Los secretos se deciden AL CREAR el mundo (quién es el traidor, qué une al
villano con el héroe), no cuando aparecen. Así las pistas que se siembran a lo
largo del relato son verdaderas y el desenlace es una consecuencia, no un
capricho: es la regla de "la pistola de Chéjov" hecha código.
"""

import random

from .gramatica import Nom
from .lexico import ARQUETIPOS, FALLAS, TONOS, mezclar_generos
from .modelo import Mundo, Params, Personaje
from .pueblo import crear_pueblo


def nombre_al_azar(genero, pronombre, rng, mezcla=()):
    lex = mezclar_generos(genero, mezcla)
    if pronombre == "f":
        pool = lex["nombres_f"]
    elif pronombre == "m":
        pool = lex["nombres_m"]
    else:
        pool = lex["nombres_f"] + lex["nombres_m"]
    return rng.choice(pool)


_ARTICULOS = ("el", "la", "los", "las")


def _lugar_con_nombre(actual: str, nuevo: str) -> str:
    """«la aldea de Brumahonda» + «Aguasmuertas» -> «la aldea de Aguasmuertas».

    Si `nuevo` ya trae su propio sintagma («el pueblo de X»), manda ese.
    """
    if nuevo.split(" ", 1)[0].lower() in _ARTICULOS and " " in nuevo:
        return nuevo
    palabras = actual.split()
    for i, w in enumerate(palabras):
        if i and w[:1].isupper():
            prefijo = palabras[:i]
            while len(prefijo) > 1 and prefijo[-1].lower() in _ARTICULOS:
                prefijo.pop()               # «el barrio de las Tres Chimeneas» -> «el barrio de»
            return " ".join(prefijo + [nuevo])
    return " ".join(palabras[:-1] + [nuevo])


def crear_mundo(p: Params) -> Mundo:
    rng = random.Random(p.semilla)
    lex = mezclar_generos(p.genero, p.mezcla)

    # Nombres sin repetir (ni con el del héroe).
    mujeres = [n for n in lex["nombres_f"] if n != p.nombre]
    hombres = [n for n in lex["nombres_m"] if n != p.nombre]
    rng.shuffle(mujeres)
    rng.shuffle(hombres)

    def personaje(rol, opciones):
        titulo, genero = rng.choice(opciones)
        nombre = (mujeres if genero == "f" else hombres).pop()
        return Personaje(rol, nombre, titulo, genero)

    reparto = {
        "heroe": Personaje("heroe", p.nombre, "", p.pronombre),
        "mentor": personaje("mentor", lex["mentores"]),
        "aliado": personaje("aliado", lex["aliados"]),
        "heraldo": personaje("heraldo", lex["heraldos"]),
    }
    nombre_villano, genero_villano = rng.choice(lex["villanos"])
    reparto["villano"] = Personaje("villano", nombre_villano, "", genero_villano)

    # Secretos del mundo.
    reparto["aliado"].traidor = rng.random() < TONOS[p.tono]["p_traidor"]
    vinculo = rng.choices(["ninguno", "discipulo", "familiar"], [4, 3, 3])[0]

    lugares = {k: Nom(rng.choice(lex[k]))
               for k in ("hogar", "umbral", "camino", "guarida")}
    objetos = {
        "meta": Nom(rng.choice(lex["metas"])),
        "don": Nom(rng.choice(lex["dones"])),
        "herramienta": Nom(rng.choice(lex["herramientas"])),
        "guardian": Nom(rng.choice(lex["guardianes"])),
        "esbirros": Nom(rng.choice(lex["esbirros"])),
        "refugio": Nom(rng.choice(lex["refugios"])),
    }

    # Nombres propios que eligió el jugador al contar su mundo.
    for rol, nombre in (p.nombres or {}).items():
        nombre = " ".join(str(nombre).split())[:40]
        if not nombre:
            continue
        if rol == "hogar":
            lugares["hogar"] = Nom(_lugar_con_nombre(str(lugares["hogar"]), nombre))
        elif rol in reparto and rol != "heroe":
            reparto[rol].nombre = nombre

    atributos = {"valor": 1, "ingenio": 1, "compasion": 1, "sombra": 0}
    for k, v in ARQUETIPOS[p.arquetipo]["stats"].items():
        atributos[k] += v
    atributos["sombra"] += FALLAS[p.falla]["sombra"]

    # El pueblo tiene su propio azar: crearlo no cambia nada más del mundo.
    usados = {p.nombre} | {x.nombre for x in reparto.values()}
    pueblo = crear_pueblo(p.semilla, lex["pueblo"], lex["nombres_f"], lex["nombres_m"], usados)

    return Mundo(params=p, rng=rng, lex=lex, reparto=reparto, lugares=lugares,
                 objetos=objetos, vinculo=vinculo, atributos=atributos, pueblo=pueblo)
