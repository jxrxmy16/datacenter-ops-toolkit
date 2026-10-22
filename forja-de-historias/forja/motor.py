"""Motor: recorre las doce etapas del viaje del héroe y resuelve cada escena.

En cada etapa el motor no sigue un guion fijo: filtra las escenas cuyas
precondiciones cumple el mundo actual y elige una al azar (con la semilla de la
partida). Por eso la misma etapa cuenta cosas distintas según quién viva,
quién viaje con el héroe y qué haya decidido el jugador antes.
"""

from . import acto1, acto2, acto3, libre
from .efectos import vigor
from .final import epilogo
from .modelo import Bloque, Capitulo, CRECEN
from .pueblo import DIAS_ESCENA, DIAS_VIAJE

# Vogler, *El viaje del escritor*: las doce etapas.
ETAPAS = {
    1: "El mundo ordinario",
    2: "La llamada a la aventura",
    3: "Dudas y preparativos",
    4: "El encuentro con el mentor",
    5: "El cruce del umbral",
    6: "Pruebas, aliados y enemigos",
    7: "El acercamiento a la caverna más profunda",
    8: "La prueba suprema",
    9: "La recompensa",
    10: "El camino de vuelta",
    11: "La resurrección",
    12: "El regreso con el elixir",
}

ESCENAS = {e.id: e for e in acto1.ESCENAS + acto2.ESCENAS + acto3.ESCENAS}

# Cada paso es (modo, [ids]). "uno": elige una escena elegible (obligatorio).
# "opcional": igual, pero si ninguna es elegible se salta el paso.
PLAN = {
    1: [("uno", ["mundo_ordinario"])],
    2: [("uno", ["llamada_heraldo"])],
    3: [("uno", ["rechazo_consecuencias", "ultimos_preparativos"])],
    4: [("uno", ["mentor_don", "mentor_rescate"])],
    5: [("uno", ["guardian_umbral"])],
    6: [("uno", ["aliado_inesperado"]),
        ("uno", ["descanso", "emboscada", "dilema"])],
    7: [("uno", ["vispera"]),
        ("opcional", ["traicion_prevista", "traicion_sorpresa"]),
        ("opcional", ["sacrificio_mentor"])],
    8: [("uno", ["prueba_suprema"])],
    9: [("uno", ["recompensa", "rescate_derrota"])],
    10: [("uno", ["camino_de_vuelta"])],
    11: [("opcional", ["ultimo_asalto"]), ("uno", ["la_voz"])],
}


def elegibles(w, ids):
    """Escenas de `ids` cuyas precondiciones cumple el mundo ahora mismo."""
    salida = []
    for i in ids:
        esc = ESCENAS[i]
        if esc.requiere is not None and not esc.requiere(w):
            continue
        if not all(w.disponible(rol) for rol in esc.participan):
            continue
        salida.append(esc)
    return salida


def elegir_escena(w, modo, ids):
    candidatas = elegibles(w, ids)
    if not candidatas:
        if modo == "opcional":
            return None
        raise RuntimeError(f"Ninguna escena elegible entre {ids} (etapa {w.etapa})")
    return w.rng.choices(candidatas, [e.peso for e in candidatas])[0]


def jugar_escena(w, esc, ses, capitulo):
    """Muestra una escena y la resuelve con las acciones del jugador.

    El jugador puede encadenar interludios (mirar, hablar, descansar...) y
    termina la escena con una decisión: una opción, o una frase suya que encaja
    con una opción.
    """
    w.ambiente = w.nuevo_ambiente()
    w.usar_fuentes(esc.fuentes)
    w.ventaja = 0
    w.libres_escena = 0
    texto = w.renderizar(esc.texto, esc.menciona)
    visibles = [o for o in esc.opciones if o.visible is None or o.visible(w)]
    etiquetas = [(o.rotulo(), w.renderizar([o.etiqueta], esc.menciona)[0])
                 for o in visibles]

    ses.escena(texto, esc.fuentes, esc.critica)
    bloque = Bloque(esc.id, texto, None, [], esc.fuentes)
    capitulo.bloques.append(bloque)

    while True:
        reg = ses.obtener(esc, visibles, etiquetas)
        if reg["k"] != "int":
            break
        if reg.get("sal"):                 # «otra suerte» también vale para un interludio
            w.rng.seed(f"{w.params.semilla}:{ses.indice_actual}:{reg['sal']}")
        parrafos, tirada, enfoque = libre.ejecutar(w, esc, reg)
        bloque.libres.append((reg["txt"], parrafos))
        ses.interludio(reg["txt"], parrafos, tirada, enfoque)
        if w.vigor <= 0:                   # el esfuerzo te deja sin fuerzas: se acabó
            bloque.eleccion = reg.get("lbl")
            bloque.notas = list(w.notas_pendientes)
            w.notas_pendientes.clear()
            return

    es_libre = reg["k"] == "libre"
    opcion = visibles[reg["i"]]
    if reg.get("sal"):                     # «otra suerte»: el dado cambia, el resto no
        w.rng.seed(f"{w.params.semilla}:{ses.indice_actual}:{reg['sal']}")

    if es_libre:
        tirada, exito, castigo = libre.tirada_de_decision(w, opcion, reg)
    else:
        tirada, exito, castigo = None, True, False
        if opcion.dif is not None:
            tirada = w.tirar(opcion.enfoque, opcion.dif, opcion.amenaza)
            exito = tirada.exito
    if tirada is not None:
        reg["azar"] = True
    resultado = opcion.ok if (exito or opcion.mal is None) else opcion.mal

    parrafos = list(resultado.parrafos)
    if es_libre:
        parrafos = libre.envoltura(reg, exito) + parrafos
    # Se renderiza ANTES de aplicar los efectos: el texto de una muerte todavía
    # puede nombrar a quien muere.
    desenlace = w.renderizar(parrafos, esc.menciona)
    for efecto in resultado.efectos:
        efecto(w)
    if castigo:
        vigor(-1)(w)
        desenlace.append("Hacerlo así te costó más de lo previsto.")
    if es_libre:
        desenlace += libre.hazana(w, reg, exito)
    if exito and opcion.enfoque in CRECEN:
        w.crecer(opcion.enfoque)
    w.avanzar(DIAS_ESCENA)                              # una escena es, al menos, un día

    ses.resultado(desenlace, tirada, opcion.enfoque or "ingenio")
    bloque.eleccion = reg.get("lbl") or etiquetas[reg["i"]][1]
    bloque.resultado = desenlace
    bloque.notas = list(w.notas_pendientes)
    w.notas_pendientes.clear()


def jugar(w, ses):
    """Juega la historia completa y devuelve el `Final`.

    `ses` es la sesión (o cualquier objeto con su misma interfaz): le pide las
    acciones del jugador y le cuenta lo que ocurre.
    """
    ses.inicio(w)
    for etapa in range(1, 12):
        w.etapa = etapa
        w.avanzar(DIAS_VIAJE.get(etapa, 0))            # el camino hasta aquí
        capitulo = Capitulo(etapa, ETAPAS[etapa])
        ses.capitulo(etapa, ETAPAS[etapa])
        for modo, ids in PLAN[etapa]:
            esc = elegir_escena(w, modo, ids)
            if esc is None:
                continue
            jugar_escena(w, esc, ses, capitulo)
            if w.vigor <= 0:
                break
        w.cronica.append(capitulo)
        if w.vigor <= 0:
            break

    final = epilogo(w)
    capitulo = Capitulo(12, ETAPAS[12])
    capitulo.bloques.append(Bloque("epilogo", final.parrafos, None, [],
                                   final.fuentes, notas=list(w.notas_pendientes)))
    w.notas_pendientes.clear()
    w.cronica.append(capitulo)
    w.usar_fuentes(final.fuentes)
    ses.final(final, w)
    return final
