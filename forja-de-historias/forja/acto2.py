"""Segundo acto (confrontación): etapas 6 a 9 del viaje del héroe."""

from .efectos import (alguien, amenaza, con, confianza, cuando, da, muere, pon,
                      sacrifica_acompanante, sale, si, sombra, une, vigor)
from .modelo import Escena, Opcion, P, res


def _traidor(w):
    return w.reparto["aliado"].traidor


ESCENAS = [

    # ------------------------------------------------------------------ 6
    Escena(
        id="aliado_inesperado", etapa=6, presentes=("aliado",), menciona=("aliado",),
        fuentes=(
            ("propp", "el auxiliar: quien acompaña y ayuda al héroe"),
            ("greimas", "el actante «ayudante» frente al «oponente»"),
            ("siete_samurais", "el héroe reúne compañeros antes del combate"),
            ("star_wars", "la cantina de Mos Eisley, donde el héroe conoce a "
                          "sus aliados"),
        ),
        texto=[
            "{ambiente}",
            "Al otro lado del umbral, el mundo cambia. En {camino}, el paisaje "
            "parece observarte.",
            "Allí te cruzas con {aliado}, que huye de {esbirros} y que, al "
            "verte, no pide ayuda: la exige con la mirada.",
            "—Tengo cuentas pendientes con {villano} —dice, casi sin aliento—. "
            "Déjame acompañarte.",
            "Podría ser verdad. O no. ¿Qué haces?",
        ],
        opciones=[
            Opcion("Confiar: tenderle la mano y compartir lo que tienes",
                   "compasion",
                   res("Compartes agua, pan y una mirada franca. Algo en su "
                       "expresión se relaja. —No lo olvidaré —dice. Y, por un "
                       "momento, parece que lo dice en serio.",
                       une("aliado"), confianza("aliado", 2))),
            Opcion("Poner{aliado.lo} a prueba con preguntas antes de aceptar{aliado.lo}",
                   "ingenio", dif=6,
                   ok=res([
                       "Preguntas por lugares, nombres y fechas, y escuchas más "
                       "lo que calla que lo que dice.",
                       P("Hay un detalle que no encaja: una contradicción "
                         "pequeña, casi invisible. Lo guardas para ti, sin "
                         "decir nada.", _traidor),
                       P("Todo encaja. Cuando por fin dices «de acuerdo», "
                         "{aliado.nombre} sonríe con un alivio genuino.",
                         lambda w: not _traidor(w)),
                   ], une("aliado"),
                       cuando(_traidor, pon("sospecha")),
                       cuando(lambda w: not _traidor(w),
                              confianza("aliado", 1))),
                   mal=res("Tus preguntas resultan torpes y {aliado.nombre} se "
                           "ofende. —Si no me quieres, dilo —gruñe. Al final lo "
                           "aceptas, pero algo entre vosotros se ha enfriado.",
                           une("aliado"), confianza("aliado", -1))),
            Opcion("Aceptar{aliado.lo} solo como herramienta: usar{aliado.lo} mientras sirva",
                   "sombra",
                   res("—Puedes venir —dices—, pero te mantienes a mi vista. "
                       "{aliado.Cap} acepta sin protestar. Si le molesta ser un "
                       "medio y no un fin, no lo demuestra.",
                       une("aliado"), sombra(1), confianza("aliado", -1))),
            Opcion("Rechazar{aliado.lo}: prefieres seguir sin compañía", None,
                   res("—Esto no es asunto tuyo —dices—. Sigue tu camino. "
                       "{aliado.Cap} te mira un instante, encoge los hombros y "
                       "se marcha por donde vino.", pon("sin_aliado"))),
        ],
    ),

    Escena(
        id="descanso", etapa=6,
        fuentes=(
            ("vogler", "pruebas, aliados y enemigos: el respiro donde se "
                       "afianzan los vínculos"),
            ("siete_samurais", "los momentos de calma entre combates, donde el "
                               "grupo se conoce"),
        ),
        texto=[
            "{ambiente}",
            "Tras varios días de marcha encuentras un lugar donde parar sin "
            "miedo a ser sorprendid{heroe.o}. Es la primera vez en mucho tiempo "
            "que nada te persigue.",
            P("{aliado.Cap} se sienta frente a ti, en silencio, con la mirada "
              "perdida.", con("aliado")),
            P("{mentor.Cap} se ocupa de sus heridas con la paciencia de quien "
              "ha aprendido a esperar.",
              lambda w: w.con("mentor") and w.b("mentor_herido")),
            "El descanso es breve. ¿Cómo lo aprovechas?",
        ],
        opciones=[
            Opcion("Conversar, escuchar y contar historias", "compasion",
                   res([
                       "Hablas de lo que dejaste atrás; el silencio cede y algo "
                       "parecido a la confianza ocupa su lugar.",
                       P("{aliado.Cap} te cuenta cosas que nunca había contado.",
                         con("aliado")),
                       P("{mentor.Cap} te cuenta, por primera vez, un recuerdo "
                         "que no tiene que ver con su oficio.", con("mentor")),
                   ], vigor(1),
                       cuando(con("aliado"), confianza("aliado", 1)),
                       cuando(con("mentor"), confianza("mentor", 1)))),
            Opcion("Vigilar por turnos y estudiar el terreno", "ingenio",
                   dif=7,
                   ok=res([
                       "Pasas la noche atento a cada ruido.",
                       P("A medianoche descubres a {aliado.nombre} haciendo una "
                         "señal a alguien que no está ahí… o que no deberías "
                         "ver.", lambda w: w.con("aliado") and _traidor(w)),
                       "Al amanecer conoces el terreno como la palma de tu mano.",
                   ], vigor(1),
                       cuando(lambda w: w.con("aliado") and _traidor(w),
                              pon("sospecha"))),
                   mal=res("Vigilas tanto que acabas durmiéndote de puro "
                           "cansancio. No pasa nada, pero tampoco aprendes "
                           "nada nuevo.", vigor(1))),
            Opcion("Entrenar con quien esté dispuesto", "valor",
                   res("Entrenas hasta que los músculos protestan y después "
                       "sigues un poco más. Dormir luego es un regalo.",
                       vigor(1))),
        ],
    ),

    Escena(
        id="emboscada", etapa=6, urgente=True,
        fuentes=(
            ("propp", "el combate con el agresor y las tareas difíciles"),
            ("vogler", "pruebas en el camino: el mundo especial pone a prueba "
                       "al héroe"),
        ),
        texto=[
            "{ambiente}",
            "El camino se estrecha. Demasiado tarde, notas que el silencio es "
            "el de quien espera. {esbirros.Cap} emergen por todos lados.",
            P("{aliado.Cap} se pone a tu lado, list{aliado.o} para pelear.",
              con("aliado")),
            "No hay tiempo para dudar. ¿Cómo respondes?",
        ],
        opciones=[
            Opcion("Plantar cara y combatir", "valor", dif=7,
                   ok=res("Peleas con la furia de quien no tiene otra opción. "
                          "Cuando por fin cesa el estruendo, los que quedan "
                          "huyen y tú sigues en pie.", amenaza(-1)),
                   mal=res("Peleas con todo, pero son demasiados. Logras abrirte "
                           "paso a costa de heridas que tardarán en cerrar.",
                           vigor(-2))),
            Opcion("Aprovechar el terreno para dividirlos", "ingenio", dif=6,
                   ok=res("Un desprendimiento aquí, una trampa allá… Para cuando "
                          "comprenden lo que ocurre, ya los has dispersado sin "
                          "gastar un golpe.", amenaza(-1)),
                   mal=res("Tu plan era bueno en teoría. En la práctica, te das "
                           "cuenta tarde de que tú también estabas en la "
                           "trampa.", vigor(-1))),
            Opcion("Cubrir a {aliado.nombre}, que ha quedado expuest{aliado.o}",
                   "compasion", dif=7, visible=con("aliado"),
                   ok=res("Te interpones sin pensar, y tu coraje sorprende "
                          "incluso a quienes te atacan. Nadie cae hoy.",
                          confianza("aliado", 2)),
                   mal=res("Protegiendo a {aliado.nombre} te descubres tú. "
                           "Sobrevivís los dos, pero a un precio.",
                           vigor(-2), confianza("aliado", 1))),
            Opcion("Cubrir a {mentor.nombre}, que ya no tiene edad para esto",
                   "compasion", dif=7, visible=con("mentor"),
                   ok=res("Te interpones sin pensar, y tu coraje sorprende "
                          "incluso a quienes te atacan. Nadie cae hoy.",
                          confianza("mentor", 2)),
                   mal=res("Protegiendo a {mentor.nombre} te descubres tú. "
                           "Sobrevivís los dos, pero a un precio.",
                           vigor(-2), confianza("mentor", 1))),
        ],
    ),

    Escena(
        id="dilema", etapa=6,
        fuentes=(
            ("polti", "la Súplica: alguien débil pide auxilio a quien tiene "
                      "poder para dárselo"),
            ("booker", "el héroe se define por su capacidad de salir de sí "
                       "mismo"),
        ),
        texto=[
            "{ambiente}",
            "Al borde del camino, un grupo de desconocidos te pide ayuda: han "
            "quedado atrapados y quienes los persiguen no tardarán en volver.",
            "Ayudarlos te costará tiempo, y {villano} no espera a nadie. Cada "
            "hora cuenta.",
            "¿Qué decides?",
        ],
        opciones=[
            Opcion("Ayudarlos, aunque cueste tiempo", "compasion",
                   res("Dedicas horas que no tienes a sacar a quienes no "
                       "conoces. Cuando por fin se ponen a salvo, no saben cómo "
                       "agradecértelo. Tú tampoco sabes por qué se te hace el "
                       "pecho más ligero.",
                       amenaza(1), pon("ayudo_extranos"))),
            Opcion("Ayudarlos deprisa, arriesgando más de lo prudente", "valor",
                   dif=7,
                   ok=res("Actúas rápido, sin pensar en tu propia seguridad. "
                          "Los pones a salvo y recuperas la ruta sin perder "
                          "apenas tiempo.", pon("ayudo_extranos")),
                   mal=res("Lo intentas deprisa y sale mal: los pones a salvo, "
                           "pero pierdes más tiempo del que ahorrabas y te "
                           "llevas un buen golpe.",
                           vigor(-1), amenaza(1), pon("ayudo_extranos"))),
            Opcion("Seguir de largo: no es tu problema", "sombra",
                   res("Aceleras el paso. Detrás, las voces se apagan una a "
                       "una. Te dices que no había alternativa. Es una de esas "
                       "frases que se repiten hasta que dejan de significar "
                       "algo.", sombra(1), pon("ignoro_extranos"))),
        ],
    ),

    # ------------------------------------------------------------------ 7
    Escena(
        id="vispera", etapa=7,
        fuentes=(
            ("vogler", "el acercamiento a la caverna más profunda: se prepara "
                       "la prueba definitiva"),
            ("campbell", "el vientre de la ballena: el umbral de la gran prueba"),
            ("siete_samurais", "la preparación de la defensa antes de la "
                               "batalla"),
            ("conrad", "el viaje hacia el corazón de la oscuridad"),
        ),
        texto=[
            "{ambiente}",
            "Por fin, {guarida} se recorta en el horizonte. Es más grande, más "
            "oscur{guarida.o} y más silencios{guarida.o} de lo que imaginabas.",
            P("{mentor.Cap} y {aliado.nombre} se colocan a tu lado. Nadie "
              "habla.", con("mentor", "aliado")),
            P("{mentor.Cap} se coloca a tu lado. Nadie habla.",
              lambda w: w.con("mentor") and not w.con("aliado")),
            P("{aliado.Cap} se coloca a tu lado. Nadie habla.",
              lambda w: w.con("aliado") and not w.con("mentor")),
            P("Estás sol{heroe.o}, y nunca lo habías sentido tanto.",
              lambda w: not w.con("aliado") and not w.con("mentor")),
            "Es hora de decidir cómo entrar.",
        ],
        opciones=[
            Opcion("Asalto frontal, por la puerta principal", "valor",
                   res("Decides entrar por donde nadie espera que se entre: por "
                       "la puerta grande. A veces la audacia es el mejor "
                       "disfraz.", pon("plan_frontal"))),
            Opcion("Infiltrarte por un acceso secundario", "ingenio",
                   res("Rodeas {guarida} hasta encontrar una entrada olvidada. "
                       "Es angosta y huele a abandono, pero nadie la vigila.",
                       pon("plan_sigilo"))),
            Opcion("Llegar hasta {villano} para hablarle, no para luchar",
                   "compasion",
                   res("Si queda algo humano en {villano}, solo despertará con "
                       "palabras. Es una apuesta arriesgada. La haces de todos "
                       "modos.", pon("plan_palabra")),
                   visible=lambda w: w.vinculo != "ninguno"),
            Opcion("Esperar un día más, por si ocurre algo", None,
                   res("Esperas, observas, dudas. Descansas, pero {villano} "
                       "también. Cuando amanece, la guarida parece aún más "
                       "grande.", vigor(1), amenaza(1))),
        ],
    ),

    Escena(
        id="traicion_prevista", etapa=7, critica=True, urgente=True, participan=("aliado",),
        requiere=lambda w: w.con("aliado") and _traidor(w) and w.b("sospecha"),
        fuentes=(
            ("vogler", "el cambiaformas: el aliado cuya lealtad es dudosa"),
            ("greimas", "el oponente disfrazado de ayudante"),
            ("propp", "el falso héroe y el castigo del traidor"),
            ("imperio", "la traición de Lando Calrissian"),
            ("la_cosa", "la desconfianza dentro del grupo"),
        ),
        texto=[
            "{ambiente}",
            "Mientras os acercáis, {aliado.nombre} se rezaga. Lo esperabas. "
            "Cuando por fin se aparta del grupo y hace una señal hacia "
            "{guarida}, ya estás detrás de {aliado.el}.",
            "—¿Desde cuándo? —preguntas.",
            "{aliado.Cap} se vuelve despacio. No intenta negarlo. —Desde antes "
            "de conocerte —dice—. Me prometieron lo que tú nunca podrás darme.",
            "¿Qué haces?",
        ],
        opciones=[
            Opcion("Perdonar{aliado.lo} y darle una última oportunidad", "compasion",
                   dif=7,
                   ok=res("No sabes de dónde sacas las palabras. Le dices que "
                          "todos merecen escoger dos veces. {aliado.Cap} baja la "
                          "mirada y algo se rompe en su expresión. —No sé si "
                          "merezco esto —susurra—. Pero lo intentaré.",
                          pon("aliado_redimido"), confianza("aliado", 3)),
                   mal=res("Le tiendes la mano, pero ya es tarde: {aliado.Cap} "
                           "da un paso atrás y echa a correr hacia {guarida}. Te "
                           "quedas con las manos vacías y con una certeza "
                           "amarga.", vigor(-1), sale("aliado"),
                           pon("aliado_enemigo"))),
            Opcion("Enfrentar{aliado.lo} y obligar{aliado.lo} a hablar", "valor", dif=6,
                   ok=res("Lo inmovilizas antes de que pueda reaccionar. Bajo "
                          "presión, {aliado.nombre} confiesa todo lo que sabe, "
                          "incluido el punto débil {villano.de}. Después {aliado.lo} "
                          "dejas marchar: ya no es una amenaza.",
                          sale("aliado"), pon("aliado_expulsado", "sabe_debilidad")),
                   mal=res("Es más rápido de lo que pensabas. Se zafa, te golpea "
                           "y huye con lo que sabe. Esta vez {villano} sabrá "
                           "que vas.", vigor(-1), amenaza(1), sale("aliado"),
                           pon("aliado_enemigo"))),
            Opcion("Castigar{aliado.lo} sin piedad", "sombra",
                   res("No hay juicio ni palabras. {aliado.Cap} no vuelve a "
                       "levantarse. Te dices que era necesario. El silencio que "
                       "queda no te lo discute.",
                       muere("aliado"), sombra(2), pon("castigo_cruel"))),
        ],
    ),

    Escena(
        id="traicion_sorpresa", etapa=7, critica=True, urgente=True, participan=("aliado",),
        requiere=lambda w: (w.con("aliado") and _traidor(w)
                            and not w.b("sospecha")),
        fuentes=(
            ("vogler", "el cambiaformas: el aliado cuya lealtad es dudosa"),
            ("aristoteles", "la peripecia: un giro de la fortuna que invierte "
                            "la situación"),
            ("imperio", "la traición de Lando Calrissian"),
            ("la_cosa", "la desconfianza dentro del grupo"),
        ),
        texto=[
            "{ambiente}",
            "Ocurre sin aviso. Un chasquido, una luz, un movimiento mal "
            "calculado: {esbirros} aparecen de entre las sombras y te rodean. "
            "Y {aliado.nombre} ya no te mira a los ojos.",
            "—Lo siento —dice, y no parece sentirlo—. Me prometieron lo que tú "
            "nunca podrás darme.",
            "Comprendes tarde lo que debiste ver antes. No hay tiempo para "
            "lamentarse. ¿Qué haces?",
        ],
        opciones=[
            Opcion("Abrirte paso a golpes", "valor", dif=8,
                   ok=res("Peleas con la rabia de quien se sabe traicionad"
                          "{heroe.o}. {aliado.Cap} huye antes de que lo "
                          "alcances, y {esbirros} aprenden que no eres presa "
                          "fácil.", vigor(-1), sale("aliado"),
                          pon("aliado_enemigo")),
                   mal=res("Peleas con todo, pero te han tendido bien la "
                           "trampa. Escapas con lo justo.", vigor(-2),
                           amenaza(1), sale("aliado"), pon("aliado_enemigo"))),
            Opcion("Huir por donde nadie espera", "ingenio", dif=7,
                   ok=res("Tu mirada encuentra un hueco, un resquicio, un "
                          "instante. Huyes sin mirar atrás, con la traición "
                          "clavada como una espina.", vigor(-1), sale("aliado"),
                          pon("aliado_enemigo")),
                   mal=res("Huyes, sí, pero no lo bastante rápido. Cuando "
                           "consigues despistarlos estás herid{heroe.o} y "
                           "sol{heroe.o}.", vigor(-2), amenaza(1),
                           sale("aliado"), pon("aliado_enemigo"))),
            Opcion("Apelar a lo que queda de bueno en {aliado.el}", "compasion",
                   dif=9,
                   ok=res("Con el peligro a un palmo de la garganta no hablas de "
                          "venganza, sino de lo que pudo ser. Algo se quiebra en "
                          "{aliado.nombre}. Se vuelve contra los suyos y, en el "
                          "desorden, logras escapar. Más tarde regresa a tu "
                          "lado, avergonzad{aliado.o}.",
                          vigor(-1), pon("aliado_redimido"),
                          confianza("aliado", 3)),
                   mal=res("Hablas, y {aliado.nombre} te escucha un instante, "
                           "pero no cambia nada. Escapas con lo justo, y con una "
                           "herida que no es solo del cuerpo.", vigor(-2),
                           sale("aliado"), pon("aliado_enemigo"))),
        ],
    ),

    Escena(
        id="sacrificio_mentor", etapa=7, critica=True, urgente=True, participan=("mentor",),
        requiere=con("mentor"),
        fuentes=(
            ("vogler", "el mentor cede el paso: el héroe debe sostenerse solo"),
            ("star_wars", "Obi-Wan se enfrenta a Vader para que los demás "
                          "puedan huir"),
            ("lotr_film", "Gandalf frente al Balrog en Khazad-dûm"),
            ("polti", "el Sacrificio por un ideal"),
        ),
        texto=[
            "{ambiente}",
            "Un estruendo a vuestras espaldas: {esbirros} han descubierto el "
            "avance. El paso se estrecha y está claro que alguien tendrá que "
            "quedarse atrás para cubrir la retirada.",
            "{mentor.Cap} da un paso al frente, y entonces comprendes que lo "
            "había decidido mucho antes.",
            P("Cojea, y aun así sonríe.", si("mentor_herido")),
            "—No hay otra manera —dice—. No discutas.",
            "¿Qué haces?",
        ],
        opciones=[
            Opcion("Aceptar su sacrificio y darle las gracias", "compasion",
                   res("—Gracias —dices, y es lo más difícil que has dicho "
                       "nunca. {mentor.Cap} asiente. —Recuerda lo que te "
                       "enseñé —es lo último que oyes de {mentor.el}. No miras "
                       "atrás. Nunca habías estado tan solo, ni tan "
                       "acompañad{heroe.o}.",
                       muere("mentor"), da("legado"), pon("mentor_cayo"))),
            Opcion("Quedarte a su lado y pelear juntos", "valor",
                   dif=lambda w: 8 if w.b("mentor_herido") else 7,
                   ok=res("—Esta vez no —dices—. Si caemos, caemos juntos. "
                          "Peleáis codo con codo hasta que {esbirros} "
                          "retroceden. {mentor.Cap} te mira, jadeante. —Eres más "
                          "terco de lo que pensaba —dice, casi con orgullo.",
                          vigor(-1), confianza("mentor", 2)),
                   mal=res("Os quedáis los dos, y no basta. Cuando por fin te "
                           "retiras, {mentor.nombre} ya no te acompaña. Cae "
                           "protegiéndote, y su último gesto es empujarte hacia "
                           "delante.", vigor(-2), muere("mentor"), da("legado"),
                           pon("mentor_cayo"))),
            Opcion("Improvisar algo para cerrar el paso a todos", "ingenio",
                   dif=7,
                   ok=res("Buscas, calculas, aprovechas. Un derrumbe oportuno "
                          "cierra el camino. {esbirros.Cap} quedan al otro lado, y "
                          "vosotros del vuestro. —Eso ha sido… inesperado "
                          "—dice {mentor.nombre}.", confianza("mentor", 2)),
                   mal=res("El derrumbe llega, pero tarde: {mentor.nombre} queda "
                           "al otro lado. No vuelves a ver{mentor.lo}.",
                           vigor(-1), muere("mentor"), da("legado"),
                           pon("mentor_cayo"))),
        ],
    ),

    # ------------------------------------------------------------------ 8
    Escena(
        id="prueba_suprema", etapa=8, critica=True, urgente=True, participan=("villano",),
        menciona=("mentor", "aliado"),
        fuentes=(
            ("campbell", "la reconciliación con el padre: el héroe se enfrenta "
                         "a la figura de poder"),
            ("vogler", "la prueba suprema: el héroe afronta la muerte o su "
                       "mayor miedo"),
            ("propp", "el combate con el agresor y la victoria"),
            ("aristoteles", "la anagnórisis: el reconocimiento súbito de un "
                            "vínculo que lo cambia todo"),
            ("imperio", "la revelación de «Yo soy tu padre»"),
            ("retorno_jedi", "Luke tiende la mano a Vader en lugar de matarlo"),
        ),
        texto=[
            "{ambiente}",
            "Por fin: el corazón {guarida.de}. {villano.Cap} te espera, y no "
            "parece sorprendid{villano.o}.",
            P("Entre quienes rodean {villano.a}, reconoces a {aliado.nombre}, "
              "que evita tu mirada.", si("aliado_enemigo")),
            P("Entre quienes rodean {villano.a}, reconoces a {aliado.nombre}, "
              "a quien rechazaste en el camino. Al menos ahora sabes por qué no te "
              "dio buena espina.",
              lambda w: w.b("sin_aliado") and _traidor(w)),
            P("Tu entrada de frente ha sido una declaración. No hay marcha "
              "atrás ni sorpresa posible.", si("plan_frontal")),
            P("Tu entrada silenciosa te ha dado ventaja: el primer movimiento "
              "es tuyo.", si("plan_sigilo")),
            P("No has venido a pelear. Eso, en sí mismo, es una forma de "
              "sorpresa.", si("plan_palabra")),
            P("—Reconozco ese estilo —dice—. Alguien te enseñó lo que yo "
              "aprendí antes que tú. Alguien que nunca te contó de dónde "
              "sacó sus lecciones.",
              lambda w: w.vinculo == "discipulo" and not w.b("sabe_vinculo")),
            P("—Reconozco ese estilo —dice—. {mentor.Cap} te lo habrá contado. "
              "A mí me enseñó lo mismo, y ya ves en qué me convirtió.",
              lambda w: w.vinculo == "discipulo" and w.b("sabe_vinculo")),
            P("—Tienes mis ojos —dice, y la sala entera parece contener el "
              "aliento—. ¿Nunca te preguntaste por qué nadie hablaba de tu "
              "familia en {hogar}?",
              lambda w: w.vinculo == "familiar" and not w.b("sabe_vinculo")),
            P("—Tienes mis ojos —dice—. Supongo que ya te lo habrán contado. "
              "Mejor así: ahorramos tiempo.",
              lambda w: w.vinculo == "familiar" and w.b("sabe_vinculo")),
            P("—Otro héroe más —dice—. He visto caer a muchos como tú.",
              lambda w: w.vinculo == "ninguno"),
            P("Recuerdas lo que descubriste sobre su punto débil. Es tu única "
              "ventaja, y es real.", si("sabe_debilidad")),
            "Es el momento de la verdad. ¿Qué haces?",
        ],
        opciones=[
            Opcion("Atacar de frente, con todo lo que tienes", "valor", dif=8,
                   amenaza=True,
                   ok=res("El combate es tan brutal que apenas lo recordarás "
                          "después. Cuando el estruendo se apaga, {villano} yace "
                          "vencid{villano.o} y tú sigues en pie, aunque no "
                          "sepas cómo.", vigor(-1), pon("villano_derrotado")),
                   mal=res("Todo tu valor no es suficiente. Un golpe que no ves "
                           "venir te arrebata el suelo, el aire, la luz. Lo "
                           "último que oyes es una risa que no es del todo "
                           "triunfal.", vigor(-2), pon("derrotado_en_prueba"))),
            Opcion("Buscar y explotar su punto débil", "ingenio",
                   dif=lambda w: 6 if w.b("sabe_debilidad") else 8,
                   amenaza=True,
                   ok=res("Un detalle, una grieta, un gesto mal medido: lo que "
                          "buscabas. Lo que sigue ocurre muy deprisa. "
                          "{villano.Cap} cae, y su caída tiene algo de justicia.",
                          vigor(-1), pon("villano_derrotado")),
                   mal=res("Tu plan era bueno, pero {villano} lo había previsto. "
                           "Te cae encima como una ola, y todo se vuelve negro.",
                           vigor(-2), pon("derrotado_en_prueba"))),
            Opcion("Tenderle la mano y hablarle de lo que fue", "compasion",
                   visible=lambda w: w.vinculo != "ninguno",
                   dif=lambda w: 6 if w.b("sabe_vinculo") else 8,
                   amenaza=True,
                   ok=res("Bajas la guardia y dices su nombre de antes, el que "
                          "nadie pronuncia. Algo en {villano} se resquebraja. "
                          "Durante un instante, solo un instante, parece "
                          "cansad{villano.o} y human{villano.o}. Después se aparta, deja "
                          "caer lo que sostenía y se pierde en las sombras para "
                          "no volver.", vigor(-1), pon("villano_redimido")),
                   mal=res("Tiendes la mano, y {villano} la mira con desprecio. "
                           "—Qué ingenuidad —dice, y el golpe llega antes que "
                           "la respuesta.", vigor(-2),
                           pon("derrotado_en_prueba"))),
            Opcion("Sacrificar a quien te acompaña para ganar tiempo", "sombra",
                   visible=alguien(),
                   ok=res([
                       "Es una decisión de un segundo y la tomas sin mirar. "
                       "Empujas a quien tienes más cerca hacia el peligro, y "
                       "ganas el instante que necesitabas.",
                       P("{aliado.Cap} cae sin comprender.", con("aliado")),
                       P("{mentor.Cap} cae sin comprender.",
                         lambda w: w.con("mentor") and not w.con("aliado")),
                       "{villano.Cap} se distrae lo justo. Ganas. Pero nunca "
                       "volverás a ser quien cruzó aquella puerta.",
                   ], sacrifica_acompanante(), sombra(3),
                       pon("villano_derrotado", "sacrificaste"))),
        ],
    ),

    # ------------------------------------------------------------------ 9
    Escena(
        id="recompensa", etapa=9, critica=True, urgente=True, menciona=("villano",),
        requiere=lambda w: w.villano_fuera(),
        fuentes=(
            ("vogler", "la recompensa: el héroe toma la espada"),
            ("campbell", "el don último, que transforma a quien lo recibe"),
            ("lotr_film", "la tentación del Anillo"),
            ("tolkien", "el poder que corrompe a quien lo empuña"),
        ),
        texto=[
            "{ambiente}",
            "El silencio que sigue al combate es casi incómodo. {villano.Cap} "
            "ya no es una amenaza, y ante ti, por fin, está {meta}.",
            "Nunca imaginaste que algo pudiera atraer y asustar tanto a la "
            "vez. Y entonces la voz de siempre regresa. {tentacion_meta}",
            "¿Qué haces con {meta.el}?",
        ],
        opciones=[
            Opcion("Quedarte con {meta}: nadie más sabrá usar{meta.lo}",
                   "sombra",
                   res("Tomas {meta}. Está tibi{meta.o}, como si latiera. "
                       "Sientes un poder que no tiene nada de metáfora. Te "
                       "dices que lo usarás bien. Casi te lo crees.",
                       sombra(2), pon("meta_obtenida", "meta_poder"))),
            Opcion("Llevar{meta.lo} de vuelta a quienes lo necesitan",
                   "compasion",
                   res("Guardas {meta} con cuidado. No {meta.lo} miras "
                       "demasiado: sabes lo que haría una mirada larga. Pesa "
                       "más de lo que parece, y no solo en las manos.",
                       pon("meta_obtenida"))),
            Opcion("Estudiar{meta.lo} antes de tocar{meta.lo}", "ingenio",
                   dif=7,
                   ok=res("Observas, comparas, recuerdas. Hay algo en {meta.el} "
                          "que responde a quien {meta.lo} mira: un hambre "
                          "antigua, paciente. Ahora sabes qué es, y eso, en sí "
                          "mismo, es una defensa.",
                          pon("meta_obtenida", "conoce_meta")),
                   mal=res("Estudias, dudas y, al final, {meta.lo} tocas sin "
                           "saber que no debías. Algo despierta. Algo, en ti, "
                           "se alegra demasiado.",
                           sombra(1), pon("meta_obtenida"))),
        ],
    ),

    Escena(
        id="rescate_derrota", etapa=9, presentes=("villano",), menciona=("mentor", "aliado"),
        requiere=si("derrotado_en_prueba"),
        fuentes=(
            ("vogler", "la muerte aparente del héroe, que renace para seguir"),
            ("campbell", "el auxilio exterior: el héroe es rescatado"),
            ("propp", "el socorro"),
        ),
        texto=[
            "{ambiente}",
            "Despiertas sin saber cuánto tiempo ha pasado. Todo duele.",
            P("{aliado.Cap} te arrastró hasta un lugar seguro, a pesar de todo. "
              "Está herid{aliado.o} y no se separa de ti.", con("aliado")),
            P("{mentor.Cap} te arrastró hasta un lugar seguro, a pesar de su "
              "edad. No se separa de ti.",
              lambda w: w.con("mentor") and not w.con("aliado")),
            P("Nadie vino por ti. Si sigues con vida, es por pura obstinación.",
              lambda w: not w.con("aliado") and not w.con("mentor")),
            "{villano.Cap} sigue ahí, y {meta} también, al alcance de quien se "
            "atreva. No será fácil.",
            "¿Qué haces?",
        ],
        opciones=[
            Opcion("Volver sigilosamente por {meta}, aprovechando la confusión",
                   "ingenio", dif=8,
                   ok=res("Esperas a que baje la guardia y, con la paciencia de "
                          "quien no tiene nada que perder, te deslizas dentro y "
                          "fuera. Cuando huyes, llevas {meta} contigo.",
                          vigor(-1), pon("meta_obtenida")),
                   mal=res("Te descubren a mitad del camino. Escapas por muy "
                           "poco y con las manos vacías.", vigor(-2))),
            Opcion("Ponerte en pie y terminar lo que empezaste", "valor",
                   dif=9, amenaza=True,
                   ok=res("Algo en ti se niega a rendirse. Te levantas y esta "
                          "vez el combate es otro: cada golpe tiene un porqué. "
                          "Cuando todo acaba, {villano} ya no es amenaza, y "
                          "{meta} es tuy{meta.o}.", vigor(-2),
                          pon("villano_derrotado", "meta_obtenida")),
                   mal=res("Te levantas, sí. Y vuelves a caer, más hondo esta "
                           "vez.", vigor(-2))),
            Opcion("Aceptar la derrota y salvar a quienes puedas", "compasion",
                   res("Retirarse no es rendirse, aunque se le parezca. Reúnes "
                       "lo que queda, ayudas a quien puedes y te marchas antes "
                       "de que el enemigo recupere el aliento.",
                       vigor(1), amenaza(1), pon("retirada"))),
        ],
    ),
]
