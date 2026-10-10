"""Creación del mundo: reparto, lugares, objetos y secretos, a partir de una semilla.

Los secretos se deciden AL CREAR el mundo (quién es el traidor, qué une al
villano con el héroe), no cuando aparecen. Así las pistas que se siembran a lo
largo del relato son verdaderas y el desenlace es una consecuencia, no un
capricho: es la regla de "la pistola de Chéjov" hecha código.
"""

import random

from .gramatica import Nom
from .lexico import ARQUETIPOS, FALLAS, GENEROS, TONOS
from .modelo import Mundo, Params, Personaje


def nombre_al_azar(genero, pronombre, rng):
    lex = GENEROS[genero]
    if pronombre == "f":
        pool = lex["nombres_f"]
    elif pronombre == "m":
        pool = lex["nombres_m"]
    else:
        pool = lex["nombres_f"] + lex["nombres_m"]
    return rng.choice(pool)


def crear_mundo(p: Params) -> Mundo:
    rng = random.Random(p.semilla)
    lex = GENEROS[p.genero]

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

    atributos = {"valor": 1, "ingenio": 1, "compasion": 1, "sombra": 0}
    for k, v in ARQUETIPOS[p.arquetipo]["stats"].items():
        atributos[k] += v
    atributos["sombra"] += FALLAS[p.falla]["sombra"]

    return Mundo(params=p, rng=rng, lex=lex, reparto=reparto, lugares=lugares,
                 objetos=objetos, vinculo=vinculo, atributos=atributos)
