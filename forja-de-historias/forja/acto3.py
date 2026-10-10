"""Tercer acto (resolución): etapas 10 y 11 del viaje del héroe.

La etapa 12, el regreso, no es una escena con opciones sino un epílogo que se
compone a partir de todo lo ocurrido: véase `final.py`.
"""

from .efectos import con, confianza, cuando, pon, si, sombra, vigor
from .modelo import Escena, Opcion, P, res


def _tentado(w):
    """Cuánto cuesta resistir la voz: crece con la sombra acumulada."""
    return w.atributos["sombra"]


ESCENAS = [

    # ----------------------------------------------------------------- 10
    Escena(
        id="camino_de_vuelta", etapa=10, urgente=True, menciona=("aliado", "mentor"),
        fuentes=(
            ("propp", "la persecución y el socorro"),
            ("campbell", "la huida mágica y el auxilio exterior"),
            ("vogler", "el camino de vuelta: el mal todavía no ha terminado"),
            ("mad_max", "el regreso por el mismo camino por el que se huyó"),
        ),
        texto=[
            "{ambiente}",
            "Ya no hay nada que te retenga en {guarida}. El camino de vuelta es "
            "largo, y las cosas rara vez terminan cuando uno quiere.",
            P("{villano.Cap} no se ha rendido: su sombra te sigue, a una "
              "distancia que se acorta con cada paso.",
              lambda w: not w.villano_fuera()),
            P("{esbirros.Cap} se reagrupan y te cierran el paso. El lugar entero "
              "parece venirse abajo, como si la oscuridad no soportara perder.",
              lambda w: w.villano_fuera()),
            P("{aliado.Cap} te cubre la espalda, como si hubiera olvidado que "
              "alguna vez dudó.",
              lambda w: w.b("aliado_redimido") and w.con("aliado")),
            P("Recuerdas {guardian.ya.a}, junto {umbral.a}. Si logras llegar "
              "hasta allí, quizá no estés tan sol{heroe.o}.", si("guardian_amigo")),
            P("Una figura te hace señas a lo lejos: son algunos de los "
              "desconocidos a los que ayudaste. Han venido a buscarte.",
              si("ayudo_extranos")),
            "El tiempo se acaba. ¿Qué haces?",
        ],
        opciones=[
            Opcion("Seguir las señas de quienes ayudaste", None, tag="Gratitud",
                   visible=si("ayudo_extranos"),
                   ok=res("Te guían por un atajo que solo ellos conocen. "
                          "—Nos salvaste —dicen—. Déjanos devolverte el favor. "
                          "Para cuando termina la persecución, apenas estás "
                          "cansad{heroe.o}.", vigor(1))),
            Opcion("Pedir ayuda {guardian.ya.a}", None, tag="Gratitud",
                   visible=si("guardian_amigo"),
                   ok=res("{guardian.ya.Cap} te espera en {umbral}. Sin una "
                          "palabra, se interpone entre ti y quienes te siguen. "
                          "Cruzas sin mirar atrás. Algunas amistades, "
                          "comprendes, se hacen sin darse cuenta.", vigor(1))),
            Opcion("Abrirte paso sin mirar atrás", "valor", dif=7,
                   ok=res("Corres, golpeas, saltas. No hay estilo, pero sí "
                          "fuerza. Cuando por fin dejas de oír pasos, el "
                          "corazón sigue galopándote."),
                   mal=res("Corres y te alcanzan. El camino de vuelta te cuesta "
                           "más de lo que pensabas.", vigor(-2))),
            Opcion("Dejar trampas y falsas pistas a tu paso", "ingenio", dif=7,
                   ok=res("Cada paso tuyo es una mentira para quien te sigue. "
                          "Se pierden, se dividen, discuten. Cuando te alcanzan, "
                          "ya es demasiado tarde."),
                   mal=res("Tus trampas retrasan a quien te sigue, pero no lo "
                           "bastante. Llegas casi sin aliento.", vigor(-1))),
            Opcion("Cargar con quien no pueda seguir tu ritmo", "compasion",
                   dif=7, visible=lambda w: w.con("aliado") or w.con("mentor"),
                   ok=res("No dejas a nadie atrás. Pierdes tiempo, pero ganas "
                          "algo que no se mide en pasos: la certeza de no estar "
                          "solo.",
                          cuando(con("aliado"), confianza("aliado", 1)),
                          cuando(con("mentor"), confianza("mentor", 1))),
                   mal=res("Cargas con quien se queda atrás y pagas el precio: "
                           "os alcanzan, y solo sobrevivís porque nadie se "
                           "rindió.", vigor(-2))),
        ],
    ),

    # ----------------------------------------------------------------- 11
    Escena(
        id="ultimo_asalto", etapa=11, critica=True, urgente=True, participan=("villano",),
        requiere=lambda w: not w.villano_fuera(),
        menciona=("aliado", "mentor"),
        fuentes=(
            ("vogler", "la resurrección: la última prueba, de la que el héroe "
                       "sale transformado"),
            ("freytag", "el clímax del drama"),
            ("field", "el clímax del tercer acto"),
            ("tiburon", "el monstruo del que Booker hace el modelo de «Vencer "
                        "al monstruo»"),
        ),
        texto=[
            "{ambiente}",
            "Cuando ya ves {hogar} en el horizonte, comprendes que lo peor no ha "
            "terminado. {villano.Cap} te ha seguido hasta aquí, y esta vez no "
            "hay guarida ni sombras que lo protejan: solo vosotros dos, y todo "
            "lo que habéis sido.",
            P("Sientes el peso {meta.de} contigo. Sería tan fácil…",
              si("meta_obtenida")),
            P("{aliado.Cap} está a tu lado, y eso cambia las cosas.",
              con("aliado")),
            "Todo termina aquí. ¿Cómo lo afrontas?",
        ],
        opciones=[
            Opcion("Plantar cara con todo lo aprendido", "valor", dif=9,
                   amenaza=True,
                   ok=res("Cada golpe repite una lección: la del camino, la de "
                          "los errores, la de quienes te ayudaron. Cuando "
                          "{villano} cae, lo hace con la expresión de quien no "
                          "entiende cómo ha perdido.",
                          vigor(-1), pon("villano_derrotado")),
                   mal=res("Lo das todo. No alcanza. {villano.Cap} te derriba, y "
                           "por un instante todo se vuelve nítido y "
                           "absurdamente tranquilo.", vigor(-2))),
            Opcion("Usar el terreno y lo que sabes para vencerlo", "ingenio",
                   dif=lambda w: 7 if w.b("sabe_debilidad") else 9,
                   amenaza=True,
                   ok=res("Lo has pensado cien veces durante el camino, y ahora "
                          "cada pieza encaja. {villano.Cap} cae en una trampa "
                          "que lleva tu nombre.",
                          vigor(-1), pon("villano_derrotado")),
                   mal=res("Tu plan falla por un detalle que no habías "
                           "previsto, como suele ocurrir. {villano.Cap} no "
                           "desaprovecha el error.", vigor(-2))),
            Opcion("Apelar al vínculo que os une", "compasion", dif=8,
                   amenaza=True, visible=lambda w: w.vinculo != "ninguno",
                   ok=res("En medio del fragor dices lo que nadie le ha dicho "
                          "nunca. {villano.Cap} duda, y esa duda es su fin como "
                          "amenaza. Se aparta y esta vez no vuelve.",
                          vigor(-1), pon("villano_redimido")),
                   mal=res("Hablas, y {villano} no te escucha. Lo que sigue "
                           "duele.", vigor(-2))),
            Opcion("Usar {meta} contra {villano.el}", "sombra",
                   visible=si("meta_obtenida"),
                   ok=res("Liberas lo que {meta} guarda. El poder es enorme, y "
                          "por unos segundos sientes que no tiene límites. "
                          "{villano.Cap} desaparece como si nunca hubiera "
                          "existido. Tú, en cambio, tienes la sensación de que "
                          "algo ha ocupado un lugar nuevo dentro de ti.",
                          sombra(2), pon("villano_derrotado", "meta_poder"))),
        ],
    ),

    Escena(
        id="la_voz", etapa=11, critica=True, urgente=True, menciona=("mentor", "aliado", "villano"),
        fuentes=(
            ("vogler", "la resurrección: la purga final y el renacimiento del "
                       "héroe"),
            ("jung", "la sombra: aquello que el yo rechaza de sí mismo"),
            ("leguin", "Ged nombra a su sombra y deja de huir de ella"),
            ("stevenson", "Jekyll y Hyde: lo que ocurre al ceder a la sombra"),
            ("aristoteles", "la catarsis"),
        ),
        texto=[
            "{ambiente}",
            P("Por fin, el silencio. {hogar.Cap}, o lo que queda, está al "
              "alcance de la mano.", lambda w: w.villano_fuera()),
            P("{villano.Cap} se retira, o tú sobrevives a duras penas; sea como "
              "sea, el estruendo se apaga y {hogar} queda al alcance de la mano.",
              lambda w: not w.villano_fuera()),
            "Y entonces vuelve la voz de siempre, la que conoces desde el "
            "primer día.",
            "{voz_final}",
            P("Llevas {meta} contigo, y su peso es una pregunta que no deja de "
              "repetirse.", si("meta_obtenida")),
            P("El recuerdo de {mentor.nombre} te acompaña: «Recuerda lo que te "
              "enseñé».", lambda w: "legado" in w.inventario),
            P("Aprietas el objeto que trajiste de casa. Es poco, pero es tuyo, y "
              "viene de un lugar donde eras algo más que un héroe.",
              lambda w: "recuerdo" in w.inventario),
            "Es la última prueba, y no tiene que ver con nadie más: eres tú "
            "contra lo que siempre has sido. ¿Qué haces?",
        ],
        opciones=[
            Opcion("Resistir la voz y mirar hacia delante", "valor",
                   dif=lambda w: 5 + _tentado(w) + (
                       1 if w.params.falla == "codicia" else 0),
                   ok=res("Es la lucha más larga de tu vida, y la más "
                          "silenciosa. Cuando por fin cesa la voz, no sientes "
                          "triunfo, sino algo más extraño: paz.",
                          cuando(lambda w: _tentado(w) >= 3,
                                 pon("arco_redimido")),
                          cuando(lambda w: _tentado(w) < 3, pon("arco_firme"))),
                   mal=res("Resistes, y resistes, y por fin dejas de resistir. "
                           "Es una derrota sin estruendo.",
                           sombra(1), pon("arco_caido"))),
            Opcion("Contarlo en voz alta: no estás sol{heroe.o}", "compasion",
                   visible=lambda w: (w.con("aliado") or w.con("mentor")
                                      or "recuerdo" in w.inventario
                                      or w.b("querido")),
                   dif=lambda w: 4 + _tentado(w) - (
                       1 if (w.con("aliado") or w.con("mentor")) else 0),
                   ok=res("Dices en voz alta lo que la voz susurraba, y de "
                          "pronto pierde su poder. Descubres que hay cosas que "
                          "solo pesan cuando se cargan a solas.",
                          cuando(lambda w: _tentado(w) >= 3,
                                 pon("arco_redimido")),
                          cuando(lambda w: _tentado(w) < 3, pon("arco_firme"))),
                   mal=res("Intentas compartirlo, pero las palabras no salen. "
                           "La voz gana terreno.",
                           sombra(1), pon("arco_caido"))),
            Opcion("Ceder: la voz tiene razón", "sombra",
                   res("Es sorprendentemente fácil. Es lo que más te asusta "
                       "después: lo fácil que fue.",
                       sombra(2), pon("arco_caido"))),
        ],
    ),
]
