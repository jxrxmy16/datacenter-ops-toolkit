"""Efectos y condiciones: el vocabulario con el que las escenas cambian el mundo.

Cada función devuelve un closure `f(mundo)`. Así las escenas se leen casi como
una descripción: `res("...", vigor(-1), pon("acepta"), muere("heraldo"))`.
"""

from .modelo import MAX_VIGOR


def vigor(n):
    def f(w):
        w.vigor = max(0, min(MAX_VIGOR, w.vigor + n))
    return f


def sombra(n):
    def f(w):
        w.atributos["sombra"] = max(0, min(6, w.atributos["sombra"] + n))
    return f


def amenaza(n):
    def f(w):
        w.amenaza = max(0, w.amenaza + n)
    return f


def pon(*banderas):
    def f(w):
        w.banderas.update(banderas)
    return f


def quita(*banderas):
    def f(w):
        w.banderas.difference_update(banderas)
    return f


def da(objeto):
    def f(w):
        w.inventario.add(objeto)
    return f


def confianza(rol, n):
    def f(w):
        p = w.reparto[rol]
        p.confianza = max(-3, min(5, p.confianza + n))
    return f


def une(rol):
    def f(w):
        w.grupo.add(rol)
    return f


def sale(rol):
    def f(w):
        w.grupo.discard(rol)
    return f


def muere(rol):
    def f(w):
        w.reparto[rol].vivo = False
        w.grupo.discard(rol)
    return f


def sacrifica_acompanante():
    """Quien acompaña al héroe (primero el aliado) cae para darle ventaja."""
    def f(w):
        rol = "aliado" if w.con("aliado") else "mentor"
        muere(rol)(w)
        w.banderas.add("sacrificado_" + rol)
    return f


def cuando(cond, *efectos):
    def f(w):
        if cond(w):
            for e in efectos:
                e(w)
    return f


# --- condiciones ----------------------------------------------------------
def si(*banderas):
    return lambda w: w.b(*banderas)


def no(*banderas):
    return lambda w: not any(x in w.banderas for x in banderas)


def con(*roles):
    return lambda w: all(w.con(r) for r in roles)


def alguien():
    return lambda w: w.con("aliado") or w.con("mentor")
