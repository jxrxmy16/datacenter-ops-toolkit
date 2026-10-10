"""Desenlace: elige el final según el estado del mundo y compone el epílogo.

No hay un "final bueno" escrito de antemano: cada final es una función de lo
que le ocurrió a cada personaje y de cómo cambió (o no) el héroe. Es el
equivalente narrativo de los tres estados de Todorov: el equilibrio roto al
principio se restablece, no se restablece, o se restablece a un precio.
"""

from dataclasses import dataclass

from .efectos import si
from .lexico import FALLAS
from .modelo import P

TODOS = ("heroe", "mentor", "aliado", "heraldo", "villano")

TITULOS = {
    "triunfo": "Final: Triunfo",
    "victoria_pirrica": "Final: Victoria pírrica",
    "renacimiento": "Final: Renacimiento",
    "tragedia": "Final: Tragedia",
    "derrota": "Final: La sombra persiste",
    "caida": "Final: Caída",
}

FUENTES_FINAL = {
    "triunfo": (
        ("vogler", "el regreso con el elixir: el héroe devuelve algo al mundo"),
        ("campbell", "el amo de los dos mundos"),
        ("todorov", "el nuevo equilibrio, distinto del inicial"),
        ("tolkien_cuentos", "la eucatástrofe: el giro feliz e inesperado"),
    ),
    "victoria_pirrica": (
        ("casablanca", "el triunfo que exige renunciar a algo querido"),
        ("polti", "el Sacrificio por un ideal"),
        ("todorov", "el nuevo equilibrio, pagado a un precio"),
    ),
    "renacimiento": (
        ("booker", "el Renacimiento: quien estuvo atrapado en su sombra se "
                   "libera"),
        ("dickens", "la redención de Scrooge"),
        ("retorno_jedi", "Anakin vuelve de la oscuridad"),
        ("aristoteles", "la catarsis y el reconocimiento"),
    ),
    "tragedia": (
        ("booker", "la Tragedia: el héroe cede a su sombra y se convierte en "
                   "lo que combatía"),
        ("macbeth", "la ambición que corrompe a quien la alimenta"),
        ("padrino", "el ascenso de Michael Corleone"),
        ("stevenson", "Jekyll y Hyde"),
    ),
    "derrota": (
        ("imperio", "el héroe sobrevive, pero el mal sigue en pie"),
        ("todorov", "el equilibrio no se restablece"),
    ),
    "caida": (
        ("aristoteles", "la caída del héroe y la compasión del público"),
        ("freytag", "la catástrofe, en el drama de cinco actos"),
    ),
}


@dataclass
class Final:
    clave: str
    titulo: str
    parrafos: list
    fuentes: tuple


def evaluar(w) -> str:
    """Decide el final a partir del estado del mundo."""
    if w.vigor <= 0:
        return "caida"
    if w.b("arco_caido"):
        return "tragedia"
    if not w.villano_fuera():
        return "derrota"
    if w.b("arco_redimido"):
        return "renacimiento"
    perdidas = sum([
        not w.vivo("mentor"),
        not w.vivo("aliado"),
        not w.vivo("heraldo"),
        w.b("hogar_perdido"),
        w.b("aliado_enemigo"),
    ])
    return "victoria_pirrica" if perdidas >= 2 else "triunfo"


_APERTURAS = {
    "triunfo": [
        "Cuando por fin ves {hogar} en el horizonte, comprendes que quien se "
        "marchó y quien vuelve ya no son la misma persona.",
        "El regreso es lento y silencioso. Cada paso hacia {hogar} te devuelve "
        "un poco de quien eras y te quita un poco de quien ya no podrás ser.",
    ],
    "victoria_pirrica": [
        "Has ganado. Lo repites por el camino como un conjuro, porque cuesta "
        "creerlo. La victoria tiene un precio, y lo has pagado entero.",
        "Regresas {hogar.a} con las manos vacías y el corazón lleno de nombres "
        "que ya no están. Ganaste, sí. Pero esta no es la clase de victoria que "
        "se celebra a gritos.",
    ],
    "renacimiento": [
        "Hubo un momento en que estuviste a punto de perderte para siempre. Que "
        "no ocurriera fue decisión tuya, y es lo único de lo que puedes sentirte "
        "orgullos{heroe.o}.",
        "Regresas {hogar.a} distint{heroe.o} a como te fuiste: más "
        "cansad{heroe.o}, sí, pero más entero. Has mirado de frente lo peor de ti "
        "y aun así sigues aquí.",
    ],
    "tragedia": [
        "Regresas {hogar.a} con la cabeza alta y el corazón oscuro. Nadie lo "
        "nota todavía. Con el tiempo, lo notarán todos.",
        "Has ganado cuanto querías, y al hacerlo has perdido a quien lo quería. "
        "{hogar.Cap} te recibe con aplausos que suenan, a tus oídos, lejanos.",
    ],
    "derrota": [
        "{villano.Cap} sigue ahí, y tú también. Regresas {hogar.a} sabiendo "
        "que esto no ha terminado, solo se ha aplazado.",
        "No lo lograste. No del todo. Pero sigues en pie, y eso, en una historia "
        "como esta, también cuenta.",
    ],
}

_CIERRES = {
    "triunfo": "Así termina la historia de {heroe}. O quizá solo el primer "
               "capítulo de la siguiente.",
    "victoria_pirrica": "Algunas historias se cuentan para recordar lo que "
                        "costaron.",
    "renacimiento": "Dicen que quien vuelve del borde ve el mundo con otros "
                    "ojos. {heroe} lo comprobó.",
    "tragedia": "Y así, lo que empezó como una historia de héroes terminó "
                "siendo una advertencia.",
    "derrota": "Pero eso, como suele decirse, es otra historia.",
}


def _destinos(w) -> list:
    """Un párrafo por personaje y por lugar, según lo que les ocurrió."""
    return [
        # villano
        P("{villano.Cap} ya no volverá a amenazar a nadie.",
          lambda w: w.b("villano_derrotado") and not w.b("villano_redimido")),
        P("{villano.Cap} desapareció una noche, dejando atrás su poder y su "
          "nombre. Dicen que, en algún lugar lejano, intenta enmendar lo que "
          "hizo.", lambda w: w.b("villano_redimido")),
        # mentor
        P("Nadie en {hogar} sabe cuánto debes a {mentor.nombre}; tú sí, y su "
          "recuerdo sigue vivo en cada cosa que haces.",
          lambda w: not w.vivo("mentor") and not w.b("sacrificado_mentor")),
        P("Cargas con el recuerdo de {mentor.nombre}: lo que hiciste con "
          "{mentor.el} no se lo puedes contar a nadie.",
          si("sacrificado_mentor")),
        P("{mentor.Cap} se despide de ti con una sonrisa cansada: ya no le "
          "queda nada más que enseñarte.",
          lambda w: w.con("mentor")),
        P("No volviste a ver a {mentor.nombre}. A veces te preguntas qué habría "
          "pasado si lo hubieras escuchado.",
          lambda w: w.vivo("mentor") and "mentor" not in w.grupo),
        # aliado
        P("Cargas con el recuerdo de {aliado.nombre}: lo que hiciste con "
          "{aliado.el} no se lo puedes contar a nadie.",
          lambda w: w.b("castigo_cruel") or w.b("sacrificado_aliado")),
        P("De {aliado.nombre} no volviste a saber. Quizá siga sirviendo a quien "
          "no lo merece; quizá, en algún lugar, se pregunte si eligió bien.",
          lambda w: w.b("aliado_enemigo") and w.vivo("aliado")),
        P("{aliado.Cap} caminó a tu lado hasta el final: una traición perdonada "
          "pesa más que mil lealtades fáciles.",
          lambda w: w.b("aliado_redimido") and w.con("aliado")),
        P("{aliado.Cap} sigue a tu lado, y es la persona en quien más confías.",
          lambda w: w.con("aliado") and not w.b("aliado_redimido")),
        # heraldo
        P("{heraldo.Cap} no vivió para ver el final. Fue por sus palabras por lo "
          "que todo comenzó.", lambda w: not w.vivo("heraldo")),
        P("{heraldo.Cap} te abraza al verte llegar. No dice nada: no hace "
          "falta.", lambda w: w.vivo("heraldo")),
        # hogar
        P("{hogar.Cap} ya no es lo que era: hay que reconstruirlo paso a paso. "
          "Pero ahora hay manos para hacerlo.", si_perdido),
        P("Los vecinos salen a recibirte: nadie olvida a quien se jugó la vida "
          "por ellos.",
          lambda w: w.b("querido") and not w.b("hogar_perdido")),
        # la meta
        P("{meta.Cap} late en tu poder, y a veces crees oír que te llama por tu "
          "nombre.", lambda w: w.b("meta_obtenida") and w.b("arco_caido")),
        P("{meta.Cap} volvió a manos de quienes {meta.lo} necesitaban, y tú "
          "volviste a tener las manos libres.",
          lambda w: w.b("meta_obtenida") and not w.b("arco_caido")),
        P("{meta.Cap} quedó fuera de tu alcance, y quizá fuera lo mejor.",
          lambda w: not w.b("meta_obtenida")),
        P("La recompensa que pactaste llega puntual, aunque ya no sepas bien "
          "qué esperabas comprar con ella.", si_recompensa),
    ]


def si_perdido(w):
    return w.b("hogar_perdido") or w.b("hogar_danado")


def si_recompensa(w):
    return w.b("recompensa_pactada")


def epilogo(w) -> Final:
    """Compone el final y su epílogo a partir del estado del mundo."""
    clave = evaluar(w)
    w.etapa = 12
    w.ambiente = w.nuevo_ambiente()

    if clave == "caida":
        parrafos = [
            "Tus fuerzas te abandonan. No hay épica en este momento, solo un "
            "cansancio inmenso y una certeza tranquila.",
            "Lo último que piensas es en {hogar}.",
            P("{villano.Cap} sigue ahí cuando todo se apaga.",
              lambda w: not w.villano_fuera()),
            "Más tarde, la noticia llega {hogar.a}: {heroe} no volvió. Alguien "
            "guarda silencio; alguien más, por primera vez en mucho tiempo, "
            "empieza a contar esta historia.",
            "Quizá otra persona, otro día, tome el camino que dejaste a medias.",
        ]
    else:
        falla = FALLAS[w.params.falla]
        leccion = (falla["leccion_mal"] if w.b("arco_caido")
                   else falla["leccion_ok"])
        parrafos = ["{ambiente}", w.rng.choice(_APERTURAS[clave])]
        parrafos += _destinos(w)
        parrafos += [leccion, _CIERRES[clave]]

    textos = w.renderizar(parrafos, TODOS)
    return Final(clave, TITULOS[clave], textos, FUENTES_FINAL[clave])
