"""Primer acto (planteamiento): etapas 1 a 5 del viaje del héroe."""

from .efectos import confianza, da, muere, no, pon, recuerdo, si, sombra, une, vigor
from .modelo import Escena, Opcion, P, res

ESCENAS = [

    # ------------------------------------------------------------------ 1
    Escena(
        id="mundo_ordinario", etapa=1,
        fuentes=(
            ("todorov", "el equilibrio inicial que la historia va a romper"),
            ("vogler", "el mundo ordinario, antes de la llamada"),
            ("propp", "la situación inicial"),
            ("mago_oz", "la vida gris en Kansas antes del viaje"),
        ),
        texto=[
            "{ambiente}",
            "Es un día como cualquier otro en {hogar}. Eres {heroe}, y todo el "
            "mundo sabe dos cosas de ti: que {rasgo}, y que {falla_txt}.",
            "{pueblo_hoy}",
            "Nada ha cambiado en años, y a veces tú también desearías que nada "
            "cambiase. Sin embargo, algo en el aire se siente a punto de romperse.",
            "{voz_inicio}",
            "¿En qué empleas el día?",
        ],
        opciones=[
            Opcion("Entrenar con {herramienta} hasta el agotamiento", "valor",
                   res("Cada golpe te recuerda para qué sirve la fuerza: para "
                       "proteger lo que quieres. Cuando terminas estás "
                       "agotad{heroe.o}, y por un momento en paz.")),
            Opcion("Pasar el día observando, escuchando y tomando nota de todo",
                   "ingenio",
                   res("Entre conversaciones a medias y miradas esquivas reúnes "
                       "más de lo que nadie sospecha. Una frase suelta sobre "
                       "{villano} se te queda grabada.", pon("oyo_rumores"),
                       recuerdo("curioso", 1))),
            Opcion("Ayudar a tus vecinos con lo que necesiten", "compasion",
                   res("Llevas cargas, escuchas penas, arreglas lo que se puede "
                       "arreglar. Al caer el día, media gente {hogar.de} sabe tu "
                       "nombre y te lo agradece.", pon("querido"),
                       recuerdo("ayudo", 2))),
        ],
    ),

    # ------------------------------------------------------------------ 2
    Escena(
        id="llamada_heraldo", etapa=2, participan=("heraldo",),
        fuentes=(
            ("campbell", "la llamada a la aventura"),
            ("propp", "la fechoría o carencia y el momento de conexión: "
                      "alguien pide ayuda al héroe"),
            ("star_wars", "el mensaje que llega a Luke y la oferta de Obi-Wan"),
        ),
        texto=[
            "{ambiente}",
            "Al terminar el día, {heraldo} llega {hogar.a} sin aliento y "
            "pregunta por ti.",
            "—Te buscaba —dice—. {problema}",
            "Todos los ojos se vuelven hacia ti. {heraldo.Cap} sabe que eres de "
            "los pocos que podrían {objetivo}.",
            P("Los vecinos asienten en silencio: confían en ti.", si("querido")),
            "¿Qué respondes?",
        ],
        opciones=[
            Opcion("Aceptar sin dudar: «Iré.»", "valor",
                   res("—Iré —dices, y la palabra pesa más de lo que esperabas. "
                       "{heraldo.Cap} suspira, aliviad{heraldo.o} y asustad"
                       "{heraldo.o} a la vez.",
                       pon("acepta"), confianza("heraldo", 1))),
            Opcion("Compartir lo que has oído sobre {villano} y aceptar",
                   "ingenio",
                   res("Cuentas lo que escuchaste: {villano} no es invencible, "
                       "y todo poder tiene un punto débil que alguien, alguna "
                       "vez, dejó escapar. —Iré —añades—, pero iré sabiendo "
                       "dónde mirar.", pon("acepta", "sabe_debilidad")),
                   visible=si("oyo_rumores")),
            Opcion("Prometer que nadie volverá a pasar miedo en {hogar}",
                   "compasion",
                   res("—Nadie volverá a pasar miedo aquí —prometes, y esta vez "
                       "no suena a consuelo, sino a juramento. A {heraldo.nombre} "
                       "se le humedecen los ojos.",
                       pon("acepta"), confianza("heraldo", 2))),
            Opcion("Aceptar, pero exigir una recompensa antes de partir",
                   "sombra",
                   res("—Iré —dices—, pero no será gratis. Se hace un silencio "
                       "incómodo. {heraldo.Cap} asiente de mala gana: el trato "
                       "está hecho.",
                       pon("acepta", "recompensa_pactada"), sombra(1),
                       confianza("heraldo", -1))),
            Opcion("Negarte: «No es asunto mío.»", None,
                   res("—No es asunto mío —dices, y cierras la puerta. "
                       "{heraldo.Cap} se queda un momento al otro lado. "
                       "—Entonces tendré que buscar a otro —murmura. Los dos "
                       "saben que no hay nadie más.", pon("rechaza"))),
        ],
    ),

    # ------------------------------------------------------------------ 3
    Escena(
        id="rechazo_consecuencias", etapa=3, critica=True, urgente=True, participan=("heraldo",),
        requiere=si("rechaza"),
        fuentes=(
            ("campbell", "el rechazo de la llamada y su coste"),
            ("star_wars", "Luke rechaza a Obi-Wan y, al volver, encuentra su "
                          "hogar destruido"),
        ),
        texto=[
            "{ambiente}",
            "Pasan unos días en los que intentas convencerte de que hiciste lo "
            "correcto. Después, {esbirros} llegan {hogar.a}.",
            "El caos estalla. {heraldo.Cap} está en medio, y te busca con la "
            "mirada.",
            "¿Qué haces?",
        ],
        opciones=[
            Opcion("Defender {hogar} con todo lo que tienes", "valor", dif=7,
                   ok=res("Peleas como nunca antes. Cuando todo termina, "
                          "{esbirros} se han retirado y {hogar} sigue en pie, "
                          "a costa de muchas heridas. {heraldo.Cap} sobrevive "
                          "gracias a ti. Ya no hay vuelta atrás: partes al "
                          "amanecer.",
                          vigor(-1), pon("acepta", "hogar_danado"),
                          confianza("heraldo", 2)),
                   mal=res("Peleas con todo lo que tienes, pero no basta. "
                           "Cuando el humo se disipa, {hogar} está en ruinas y "
                           "{heraldo} yace entre los escombros. Ya no queda "
                           "nada que te retenga: partes en cuanto puedes "
                           "caminar.",
                           vigor(-2), muere("heraldo"),
                           pon("acepta", "hogar_perdido"), sombra(1))),
            Opcion("Poner a salvo a los vecinos antes que pelear", "compasion",
                   dif=6,
                   ok=res("Guías a los vecinos hasta un lugar seguro, uno a "
                          "uno, sin soltar ninguna mano. {hogar.Cap} lo pierde "
                          "casi todo, pero nadie se queda atrás. {heraldo.Cap} "
                          "te mira con una gratitud que duele. Partes sabiendo "
                          "que lo que dejas merece ser salvado.",
                          pon("acepta", "hogar_danado"), confianza("heraldo", 1)),
                   mal=res("Intentas sacar a todos a tiempo, pero el miedo los "
                           "dispersa. Cuando el humo se disipa, {heraldo} ya no "
                           "respira. Su último gesto fue señalarte el camino que "
                           "ahora no tienes más remedio que tomar.",
                           vigor(-1), muere("heraldo"),
                           pon("acepta", "hogar_danado"))),
            Opcion("Esconderte y esperar a que pase", None,
                   res("Te encierras, te tapas los oídos y esperas. El ruido "
                       "tarda una eternidad en apagarse. Cuando por fin sales, "
                       "{hogar} es otra cosa, y {heraldo} no está entre los que "
                       "siguen en pie. Esta vez no hay excusa que valga: partes "
                       "antes de que amanezca.",
                       pon("acepta", "hogar_perdido", "culpa"),
                       muere("heraldo"), sombra(1))),
        ],
    ),

    Escena(
        id="ultimos_preparativos", etapa=3,
        requiere=no("rechaza"),
        fuentes=(
            ("vogler", "los preparativos antes de cruzar el umbral"),
            ("lotr_film", "la partida de Frodo, que deja su hogar sabiendo "
                          "que quizá no vuelva"),
        ),
        texto=[
            "{ambiente}",
            "Partes al amanecer. Durante la noche, mientras reúnes lo que "
            "podrías necesitar, no dejas de pensar en lo que se queda atrás.",
            "Tienes poco tiempo y ninguna certeza. ¿Qué te llevas?",
        ],
        opciones=[
            Opcion("Provisiones y {herramienta} en buen estado", "valor",
                   res("Revisas y empacas con el cuidado de quien sabe que de "
                       "ello depende su vida. Nada de lo que llevas es bonito, "
                       "pero todo es útil.", da("equipo"))),
            Opcion("Mapas, notas y todo lo que puedas saber del camino",
                   "ingenio",
                   res("Pasas la noche en vela repasando rutas, nombres y "
                       "rumores. Para cuando amanece, el camino ya no te es del "
                       "todo desconocido.", da("mapa"))),
            Opcion("Un recuerdo {hogar.de}, algo que te haga volver",
                   "compasion",
                   res("Eliges un objeto pequeño y gastado, sin valor para nadie "
                       "más. Pesa muy poco; lo notarás sobre todo en los peores "
                       "momentos.", da("recuerdo"))),
        ],
    ),

    # ------------------------------------------------------------------ 4
    Escena(
        id="mentor_don", etapa=4, presentes=("mentor",), menciona=("mentor",),
        fuentes=(
            ("propp", "la primera función del donante: el que prueba al héroe "
                      "y le entrega un objeto o un consejo"),
            ("vogler", "el arquetipo del mentor"),
            ("star_wars", "Obi-Wan entrega a Luke el sable de su padre"),
            ("karate_kid", "el señor Miyagi y su enseñanza"),
        ),
        texto=[
            "{ambiente}",
            "Sigues el rumbo que te marcó el instinto —o el destino— y acabas "
            "ante {refugio}. Dentro te espera {mentor}, que te mira como quien "
            "reconoce una vieja promesa.",
            "—Sé a qué vas —dice—. Y sé que aún no estás list{heroe.o}. Nadie "
            "lo está.",
            "Hay mucho que podría enseñarte, y muy poco tiempo. Te ofrece "
            "sentarte y escuchar.",
            "¿Cómo respondes?",
        ],
        opciones=[
            Opcion("Escuchar sus lecciones con humildad", "ingenio",
                   res("Pasas horas escuchando, preguntando, corrigiéndote. Al "
                       "despedirte, {mentor.nombre} te entrega {don}. —Te servirá "
                       "cuando yo ya no pueda —dice. Y lo dice como quien sabe "
                       "algo que tú todavía no.",
                       une("mentor"), da("don"), confianza("mentor", 2))),
            Opcion("Preguntarle por qué vive apartad{mentor.o} del mundo",
                   "compasion",
                   res([
                       "Algo en tu pregunta lo desarma. Se queda en silencio y "
                       "luego habla, más de lo que ha hablado en años.",
                       P("—{villano.Cap} fue mi discípulo —confiesa—. Le enseñé "
                         "todo lo que hoy usa contra nosotros.",
                         lambda w: w.vinculo == "discipulo"),
                       P("—{villano.Cap} lleva tu sangre —dice, y el suelo "
                         "parece moverse bajo tus pies—. Nadie en {hogar} quiso "
                         "decírtelo.", lambda w: w.vinculo == "familiar"),
                       P("—Lo conocí hace mucho. Nunca fue inocente, pero tampoco "
                         "nació monstruo —dice.",
                         lambda w: w.vinculo == "ninguno"),
                       "Al despedirte, te entrega {don}. —Para que no tengas que "
                       "cargar con mis errores.",
                   ], une("mentor"), da("don"), confianza("mentor", 3),
                       pon("sabe_vinculo"))),
            Opcion("Rechazar su ayuda: puedes arreglártelas sol{heroe.o}",
                   "sombra",
                   res("—Gracias, pero no —dices—. Prefiero ir por mi cuenta. "
                       "{mentor.Cap} no discute. Solo asiente, despacio, con la "
                       "tristeza de quien ya ha visto ese gesto antes. —Entonces "
                       "que te vaya bien —dice—. Lo vas a necesitar.",
                       sombra(1), confianza("mentor", -1))),
        ],
    ),

    Escena(
        id="mentor_rescate", etapa=4, urgente=True, presentes=("mentor",), menciona=("mentor",),
        fuentes=(
            ("propp", "el donante y el héroe: aquí el favor va al revés, es el "
                      "héroe quien debe ganarse al donante"),
            ("campbell", "la ayuda sobrenatural"),
            ("vogler", "el arquetipo del mentor"),
        ),
        texto=[
            "{ambiente}",
            "Poco antes de llegar {umbral.a}, ves a lo lejos una figura rodeada "
            "por {esbirros}. Se defiende como puede, que no es poco, pero está "
            "perdiendo.",
            "Al acercarte la reconoces: es {mentor}, de quien se dice que sabe "
            "más que nadie sobre {villano}.",
            "No hay tiempo para pensar. ¿Qué haces?",
        ],
        opciones=[
            Opcion("Cargar contra {esbirros} sin pensarlo", "valor", dif=6,
                   ok=res("Irrumpes gritando y {esbirros}, desconcertados, se "
                          "dispersan. {mentor.Cap} te mira, jadeante. —Valiente "
                          "y poco prudente —dice, y casi sonríe—. Me valdrás. "
                          "Antes de seguir, te da {don}.",
                          une("mentor"), da("don"), confianza("mentor", 2)),
                   mal=res("Te lanzas al combate y sales peor parado de lo "
                           "previsto, pero lo bastante rápido para que "
                           "{mentor.nombre} se libre. No sin heridas. A modo de "
                           "gracias, te da {don}.",
                           vigor(-1), une("mentor"), da("don"),
                           pon("mentor_herido"), confianza("mentor", 1))),
            Opcion("Crear una distracción para alejarlos", "ingenio", dif=6,
                   ok=res("Haces ruido donde no deben oírse y enciendes lo que "
                          "no debería encenderse. {esbirros.Cap} se vuelven hacia el "
                          "engaño y {mentor.nombre} aprovecha para escapar. "
                          "—Eso sí que no lo vi venir —dice, impresionad"
                          "{mentor.o}, y te regala {don}.",
                          une("mentor"), da("don"), confianza("mentor", 2)),
                   mal=res("La distracción sale a medias: {esbirros} se dividen y "
                           "{mentor.nombre} recibe un golpe antes de que logres "
                           "sacar{mentor.lo} de allí. Sigue con vida, pero herid{mentor.o}. "
                           "Aun así te entrega {don}.",
                           vigor(-1), une("mentor"), da("don"),
                           pon("mentor_herido"), confianza("mentor", 1))),
            Opcion("Esperar a que acaben y quedarte con lo que {mentor.nombre} "
                   "deje caer", "sombra",
                   res("Esperas, inmóvil, mientras la pelea se alarga. "
                       "{mentor.Cap} logra escapar, herid{mentor.o}, no sin "
                       "antes perder {don}. Lo recoges sin que nadie te vea. Te "
                       "dices que era lo único sensato. No lo crees del todo.",
                       da("don"), sombra(1), confianza("mentor", -3))),
        ],
    ),

    # ------------------------------------------------------------------ 5
    Escena(
        id="guardian_umbral", etapa=5, presentes=("guardian",),
        fuentes=(
            ("campbell", "el cruce del primer umbral y su guardián"),
            ("vogler", "el guardián del umbral, que prueba si el héroe merece "
                       "pasar"),
            ("chihiro", "el paso al mundo de los espíritus, donde cada puerta "
                        "tiene sus reglas"),
        ),
        texto=[
            "{ambiente}",
            "{umbral.Cap} se alza ante ti. Más allá, el mundo que conoces "
            "termina y empieza otro, más peligroso y más verdadero. "
            "Bloqueándote el paso, {guardian}.",
            "No es exactamente un enemigo. Solo decide quién pasa y quién no.",
            P("{mentor.Cap} se detiene a tu lado. —Este es el primer umbral "
              "—murmura—. Los demás serán peores.", lambda w: w.con("mentor")),
            "¿Cómo intentas cruzar?",
        ],
        opciones=[
            Opcion("Abrirte paso por la fuerza", "valor", dif=7,
                   ok=res("Aprietas los dientes y avanzas. Lo que podría haber "
                          "sido un combate largo se resuelve en un instante: "
                          "{guardian.ya} entiende que no te detendrás, y se "
                          "aparta."),
                   mal=res("Lo intentas por la fuerza, pero {guardian.ya} resiste "
                           "más de lo que parecía. Pasas, sí, con las costillas "
                           "doloridas y la certeza de que no todas las puertas "
                           "se abren a golpes.", vigor(-1))),
            Opcion("Engañar al guardián", "ingenio", dif=6,
                   ok=res("Inventas una historia tan convincente que {guardian.ya} "
                          "casi se disculpa por haberte retrasado. Cruzas sin "
                          "mirar atrás, con el corazón a mil."),
                   mal=res("Tu mentira se desmorona a media frase. "
                           "{guardian.ya.Cap} te mira en silencio y entiendes "
                           "que no se ha creído nada. Acabas cruzando de todos "
                           "modos, a trompicones y con un golpe en el costado.",
                           vigor(-1))),
            Opcion("Hablarle como a un igual y preguntarle por qué guarda el "
                   "paso", "compasion", dif=6,
                   ok=res("Te sientas, en lugar de amenazar, y preguntas. "
                          "{guardian.ya.Cap} duda y luego, despacio, empieza a "
                          "contar. Llevaba demasiado tiempo sin nadie con quien "
                          "hablar. Al final se aparta, y casi parece agradecerte "
                          "la compañía.", pon("guardian_amigo")),
                   mal=res("Lo intentas, pero {guardian.ya} no está para charlas. "
                           "Te deja pasar a su manera: con un empujón que te "
                           "recuerda que ha sido un mal día para hablar.",
                           vigor(-1))),
            Opcion("Dejar que {mentor.nombre} interceda", None, tag="Confianza",
                   visible=lambda w: (w.con("mentor")
                                      and w.reparto["mentor"].confianza >= 2),
                   ok=res("{mentor.Cap} se adelanta y dice unas palabras que no "
                          "alcanzas a oír. {guardian.ya.Cap} baja la cabeza, como "
                          "ante un viejo conocido, y se aparta.",
                          confianza("mentor", 1))),
        ],
    ),
]
