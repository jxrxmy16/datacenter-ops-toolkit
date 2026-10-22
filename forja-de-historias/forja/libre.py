"""Acciones libres: lo que ocurre cuando el jugador escribe en lugar de elegir.

Hay dos caminos, igual que en una mesa de rol:

  * DECISIÓN: la frase encaja con una de las opciones de la escena. Se resuelve
    esa opción (con sus efectos, que son los que mantienen la historia
    coherente), pero tu frase y tus modificadores ("con los ojos cerrados")
    cambian la dificultad y se cuentan en el relato.
  * INTERLUDIO: la frase es otra cosa (mirar, hablar con alguien, descansar,
    moverse, improvisar). Se resuelve en el momento, puede darte una pista,
    una ventaja o un coste, pero la escena sigue abierta.

Todo lo que se necesita para repetir una acción libre está en su registro, de
modo que deshacer y cargar partidas reproducen exactamente la misma historia.
"""

from .efectos import confianza, pon, sombra, vigor
from .lenguaje import ENFOQUE_DE
from .modelo import MAX_VIGOR

MAX_LIBRES = 3          # interludios por escena antes de tener que decidir

# --------------------------------------------------------------------------
# Textos
# --------------------------------------------------------------------------
CONSEJOS_MENTOR = {
    4: "—No temas pedir ayuda —dice—. Quien parte solo llega tarde, o no llega.",
    5: "—Un umbral no se cruza con la fuerza ni con la astucia, sino con la "
       "verdad de quien lo cruza —dice—. Elige cómo quieres ser visto.",
    6: "—El camino enseña más que cualquier maestro —dice—. Observa en quién "
       "confías, y por qué.",
    7: "—Antes de la batalla, calma —dice—. Todo lo que has aprendido sigue "
       "contigo.",
}
CONSEJO_GENERICO = ("—Sigue tu criterio —dice—, pero no olvides por qué "
                    "empezaste.")

# (con modificador, sin modificador)
MOVER_OK = [
    ("Avanzas {m} y el camino se deja recorrer: ni un tropiezo.",
     "Avanzas y el camino se deja recorrer: ni un tropiezo."),
    ("Te desplazas {m} con más suerte que cabeza, pero llegas.",
     "Te desplazas con más suerte que cabeza, pero llegas."),
    ("Cada paso {m} es una pequeña apuesta, y esta vez sales ganando.",
     "Cada paso es una pequeña apuesta, y esta vez sales ganando."),
]
MOVER_MAL = [
    ("Avanzas {m}, pero el terreno te traiciona y pierdes pie.",
     "Avanzas, pero el terreno te traiciona y pierdes pie."),
    ("Lo intentas {m}; tropiezas, te golpeas y tienes que rehacer el paso.",
     "Lo intentas; tropiezas, te golpeas y tienes que rehacer el paso."),
    ("Te mueves {m} y el mundo te lo cobra con un golpe.",
     "Te mueves y el mundo te lo cobra con un golpe."),
]
MOVER_FIN = [
    "Pero lo que te trajo hasta aquí sigue esperando.",
    "Aun así, el asunto que te ocupa no se ha movido de su sitio.",
    "Das unas vueltas, pero lo que tienes delante sigue ahí.",
    "Nada de eso cambia lo que hay que decidir.",
]

# La frase del jugador ya se enseña antes del párrafo («▸ «frase»» en pantalla,
# cursiva en el libro): las plantillas no la repiten.
IMPROV_OK = {
    "valor": ["Lo haces sin dudar, y el gesto no resuelve nada todavía, pero te "
              "deja el pulso firme y la certeza de ir por delante."],
    "ingenio": ["Piensas deprisa y actúas con cabeza: aún no decides nada, pero "
                "ahora ves el terreno con otros ojos."],
    "compasion": ["Un gesto amable cambia el ánimo de quienes te rodean, y tú "
                  "respiras mejor."],
    "sombra": ["Haces lo que te conviene, y funciona; algo en ti se endurece un "
               "poco."],
    "duda": ["Te echas atrás un instante y ganas un respiro para pensar."],
}
IMPROV_MAL = {
    "valor": ["Lo intentas con más ímpetu que acierto y sales magullad{o}."],
    "ingenio": ["La idea era buena, pero la ejecución falla y pierdes tiempo y "
                "fuerzas."],
    "compasion": ["Tu gesto no llega a donde querías y te deja un regusto "
                  "amargo."],
    "sombra": ["Te sale mal, y la culpa se te queda pegada a la piel."],
    "duda": ["Dudas demasiado y el momento se te escapa entre los dedos."],
}
VENTAJA_OBSERVAR = " Sientes que lo que has visto te dará ventaja en tu próxima jugada."
VENTAJA_ACTUAR = " Eso te deja un paso por delante en tu próxima jugada."
PREMIO_AUDACIA = "Tu audacia tiene premio: recuperas un poco de aliento."


def _llaves(texto: str) -> str:
    """Protege las llaves del texto del jugador dentro de una plantilla."""
    return texto.replace("{", "{{").replace("}", "}}")


def _mods(reg) -> str:
    """Los modificadores que escribió el jugador, sin repetidos y bien unidos."""
    frag = []
    for m in reg.get("mods") or []:
        m = " ".join(str(m).split())
        if m:
            frag.append(m[:1].lower() + m[1:])
    # un fragmento que contiene a otro lo repetiría: se queda el más corto
    unicos = [m for m in dict.fromkeys(frag)
              if not any(o != m and o in m for o in frag)]
    if len(unicos) <= 1:
        return "".join(unicos)
    return ", ".join(unicos[:-1]) + " y " + unicos[-1]


def _premio(w, reg) -> list:
    """El premio de la audacia, si de verdad hay aliento que recuperar."""
    if reg.get("dd", 0) > 0 and w.vigor < MAX_VIGOR:
        vigor(+1)(w)
        return [PREMIO_AUDACIA]
    return []


# --------------------------------------------------------------------------
# Pistas que se pueden descubrir observando
# --------------------------------------------------------------------------
def _pistas(w, esc):
    """Lista de (clave, condición, texto, efectos); la primera aplicable gana."""
    return [
        ("traidor",
         lambda: (w.con("aliado") and w.reparto["aliado"].traidor
                  and not w.b("sospecha")),
         "Algo no encaja en {aliado.nombre}: evita tu mirada cada vez que sale "
         "el nombre {villano.de}. Lo guardas para ti.",
         [pon("sospecha")]),
        ("vinculo",
         lambda: (w.con("mentor") and w.vinculo != "ninguno"
                  and not w.b("sabe_vinculo") and not w.b("intuye_vinculo")),
         "{mentor.Cap} calla cada vez que alguien nombra {villano.a}. Ahí hay "
         "una historia que no te han contado.",
         [pon("intuye_vinculo")]),
        ("pueblo",
         lambda: esc is not None and esc.id == "mundo_ordinario",
         "Observas a la gente {hogar.de} con calma. {pueblo_detalle}",
         []),
        ("guardian",
         lambda: esc is not None and esc.id == "guardian_umbral",
         "{guardian.ya.Cap} no vigila el camino: vigila a quien llega. Quizá "
         "importe más cómo te acercas que cuánta fuerza llevas.",
         []),
    ]


# --------------------------------------------------------------------------
# Interludios
# --------------------------------------------------------------------------
def ejecutar(w, esc, reg):
    """Resuelve un interludio. Devuelve (párrafos, tirada, enfoque)."""
    w.libres_escena += 1
    clase = reg["clase"]
    if clase == "observar":
        return _observar(w, esc, reg)
    if clase == "hablar":
        return _hablar(w, esc, reg)
    if clase == "descansar":
        return _descansar(w, esc, reg)
    if clase == "moverse":
        return _moverse(w, esc, reg)
    return _improvisar(w, esc, reg)


def _dar_ventaja(w, texto=VENTAJA_OBSERVAR) -> str:
    if w.ventaja >= 1:
        return ""
    w.ventaja = 1
    return texto


def _observar(w, esc, reg):
    t = w.tirar("ingenio", 6, ajuste=reg.get("dd", 0))
    reg["azar"] = True
    if not t.exito:
        return (w.renderizar(["Miras y remiras, pero nada te llama la atención."],
                             ("mentor", "aliado", "villano")), t, "ingenio")
    for clave, cond, texto, efectos in _pistas(w, esc):
        if clave not in w.observados and cond():
            w.observados.add(clave)
            for e in efectos:
                e(w)
            ps = w.renderizar([texto + _dar_ventaja(w)],
                              ("mentor", "aliado", "villano"))
            return ps, t, "ingenio"
    ps = w.renderizar([f"Observas con calma. {w.nuevo_ambiente()}" + _dar_ventaja(w)])
    return ps, t, "ingenio"


def _objetivo_charla(w, esc, reg):
    for rol in ("mentor", "aliado", "heraldo", "villano"):
        if rol in reg.get("ent", ()):
            return rol
    if "guardian" in reg.get("ent", ()):
        return "guardian"
    return None


def _hablar(w, esc, reg):
    rol = _objetivo_charla(w, esc, reg)
    menc = ("mentor", "aliado", "heraldo", "villano")
    if rol is None:
        return ["Hablas en voz alta y solo te responde el eco."], None, None
    if rol == "guardian":
        return (w.renderizar(["{guardian.ya.Cap} te mira sin responder. Algo te "
                              "dice que no basta con hablarle: hay que "
                              "escucharle de verdad."], menc), None, None)
    if rol == "villano":
        if esc is not None and "villano" in esc.presentes:
            return (w.renderizar(["{villano.Cap} te escucha sin moverse, y no "
                                  "responde: no es hora de palabras."], menc),
                    None, None)
        return (w.renderizar(["Tus palabras se pierden en la distancia: "
                              "{villano} no está aquí para oírlas."], menc),
                None, None)
    clave = (rol, w.etapa)
    primera = clave not in w.charlas
    w.charlas.add(clave)
    if rol == "mentor":
        texto = ("{mentor.Cap} te escucha con atención. "
                 + CONSEJOS_MENTOR.get(w.etapa, CONSEJO_GENERICO))
    elif rol == "heraldo":
        texto = ("{heraldo.Cap} te repite lo que sabe, y no añade nada que no "
                 "supieras: {problema}")
    else:
        texto = ("—Si salimos de esta, te invito a lo que quieras —bromea "
                 "{aliado.nombre}, y por un momento todo parece más llevadero.")
    ps = [texto]
    t = None
    if primera:
        confianza(rol, 1)(w)
    if rol == "aliado" and w.reparto["aliado"].traidor and not w.b("sospecha"):
        t = w.tirar("ingenio", 8, ajuste=reg.get("dd", 0))
        reg["azar"] = True
        if t.exito:
            pon("sospecha")(w)
            ps.append("Pero hay una frase que suena demasiado ensayada, y la "
                       "guardas para ti.")
    return w.renderizar(ps, menc), t, ("ingenio" if t else None)


def _descansar(w, esc, reg):
    if w.etapa in w.descansos:
        return (["Ya has descansado todo lo que el tiempo permite en esta parte "
                 "del camino."], None, None)
    w.descansos.add(w.etapa)
    w.avanzar(1)                                         # un día de reposo
    antes = w.vigor
    vigor(+1)(w)
    w.amenaza += 1
    ganado = w.vigor - antes
    texto = ("Te permites un respiro" + (", y recuperas un poco de fuerza"
                                          if ganado else "") +
             ". Pero el tiempo corre también para {villano}: la amenaza crece.")
    return w.renderizar([texto], ("villano",)), None, None


def _moverse(w, esc, reg):
    enfoque = "ingenio" if w.atributos["ingenio"] > w.atributos["valor"] else "valor"
    dd = reg.get("dd", 0)
    t = w.tirar(enfoque, 5, ajuste=dd)
    reg["azar"] = True
    w.avanzar(1)                                         # caminar también cuesta un día
    m = _mods(reg)
    pool = MOVER_OK if t.exito else MOVER_MAL
    con, sin = w.rng.choice(pool)
    if not m or ("paso" in m and con.startswith("Cada paso")):
        ps = [sin]                 # sin matiz, o que no choque con «paso a paso»
    else:
        ps = [con.format(m=m)]
    if t.exito:
        ps += _premio(w, reg)
    else:
        vigor(-1)(w)
    ps.append(MOVER_FIN[w.libres_escena % len(MOVER_FIN)])
    return ps, t, enfoque


def _improvisar(w, esc, reg):
    clase = reg["clase"]
    enfoque = ENFOQUE_DE.get(clase) or "ingenio"
    t = w.tirar(enfoque, 6, ajuste=reg.get("dd", 0))
    reg["azar"] = True
    if t.exito:
        txt = w.rng.choice(IMPROV_OK[clase])
        extra = _dar_ventaja(w, VENTAJA_ACTUAR)
        if clase == "sombra":
            sombra(+1)(w)
        premio = _premio(w, reg)
        if premio:
            extra += " " + premio[0]
        return w.renderizar([txt + extra]), t, enfoque
    vigor(-1)(w)
    txt = w.rng.choice(IMPROV_MAL[clase]).replace("{o}", "{heroe.o}")
    return w.renderizar([txt]), t, enfoque


# --------------------------------------------------------------------------
# Decisiones escritas a mano
# --------------------------------------------------------------------------
def envoltura(reg, exito) -> list:
    """Frase que enlaza lo que escribió el jugador con el resultado de la opción."""
    m = _llaves(_mods(reg))
    if exito:
        txt = (f"A tu manera —{m}— lo consigues." if m
               else "Lo haces a tu manera, y funciona.")
    else:
        txt = (f"Lo intentas a tu manera —{m}—, pero no sale como esperabas."
               if m else "Lo intentas a tu manera, pero no sale como esperabas.")
    return [txt]


def tirada_de_decision(w, opcion, reg):
    """Tirada de una decisión libre: puede imponerla aunque la opción no tuviera.

    Devuelve (tirada | None, éxito, castigo_sin_mal).
    """
    dd = reg.get("dd", 0)
    if opcion.dif is not None:
        t = w.tirar(opcion.enfoque or "ingenio", opcion.dif, opcion.amenaza, dd)
        return t, t.exito, False
    if dd > 0:                      # se impuso un obstáculo a una opción segura
        t = w.tirar(opcion.enfoque or "ingenio", 5, False, dd)
        return t, t.exito, not t.exito
    return None, True, False


def hazana(w, reg, exito) -> list:
    return _premio(w, reg) if exito else []
