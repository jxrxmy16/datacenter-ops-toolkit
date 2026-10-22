"""Datos del universo: vocabulario por género, arquetipos, fallas, tonos y tramas.

Todo son datos, sin lógica. Añadir un género nuevo es añadir un diccionario
a GENEROS con las mismas claves que los existentes.

Convenciones:
  * Los lugares y objetos llevan su artículo ("la aldea de Brumahonda").
  * `hogar`, `umbral`, `guarida` y `metas` son SIEMPRE singulares.
  * `esbirros` es SIEMPRE plural; `guardianes` y `dones` son singulares.
  * Los títulos de personajes son (título con artículo, género m/f).
  * Las frases de `ambiente` no mencionan la hora del día.
"""

GENEROS = {
    # ------------------------------------------------------------------
    "fantasia": {
        "nombre": "Fantasía épica",
        "desc": "reinos antiguos, magia y sombras que despiertan",
        "inspiracion": ["tolkien", "leguin", "lotr_film"],
        "hogar": ["la aldea de Brumahonda", "el pueblo de Valleclaro",
                  "la villa de Piedrasanta"],
        "umbral": ["el Paso de los Cuervos", "el Puente de Alderrón",
                   "la Puerta del Bosque Viejo"],
        "camino": ["los Páramos Grises", "el Bosque de las Mil Voces",
                   "las Marismas de Nevarra"],
        "guarida": ["la Fortaleza de Hierro Negro",
                    "la ciudadela en ruinas de Karn-Duhl",
                    "la Torre de los Vientos Muertos"],
        "metas": ["la Corona de Ceniza", "el Cáliz de la Aurora",
                  "la Piedra del Alba"],
        "dones": ["una daga rúnica", "un amuleto de plata",
                  "una capa tejida con viento"],
        "herramientas": ["tu espada", "tu arco", "tu bastón de roble"],
        "guardianes": ["un gigante de piedra", "un troll de ojos vacíos",
                       "una esfinge de basalto"],
        "esbirros": ["los lobos de ceniza", "los jinetes sin rostro",
                     "los huargos del Eclipse"],
        "refugios": ["una cabaña de piedra junto al camino",
                     "una torre medio derruida"],
        "ambiente": [
            "Huele a lluvia y a hierro viejo.",
            "Un viento frío mueve las ramas, como si el bosque susurrara.",
            "Las antorchas parpadean y alargan las sombras.",
            "Algún cuervo grazna a lo lejos.",
            "El cielo tiene el color de una herida a medio cerrar.",
            "Una campana distante suena una sola vez y no vuelve a sonar.",
            "El camino está lleno de huellas que nadie sabría decir de quién son.",
            "Hasta el silencio parece escuchar.",
        ],
        "mentores": [("la archimaga", "f"), ("el ermitaño", "m"),
                     ("el viejo caballero", "m")],
        "aliados": [("la ladrona", "f"), ("el bardo", "m"),
                    ("la cazadora", "f")],
        "heraldos": [("el mensajero", "m"), ("la niña", "f"),
                     ("el herrero", "m")],
        "villanos": [("el Rey Marchito", "m"), ("la Reina de Espinas", "f"),
                     ("el Hechicero del Eclipse", "m")],
        "nombres_f": ["Ilvane", "Tarsa", "Maeve", "Selene", "Orla", "Kaelis",
                      "Nyra", "Edda"],
        "nombres_m": ["Orsolo", "Bren", "Dorin", "Maeron", "Tomas", "Kael",
                      "Hobb", "Alderic"],
        "pueblo": {
            "oficios": [("la panadera", "f"), ("el herrero", "m"), ("la curandera", "f"),
                        ("el posadero", "m"), ("la tejedora", "f"), ("el molinero", "m"),
                        ("la pastora", "f"), ("el carpintero", "m"), ("la cervecera", "f"),
                        ("el cantero", "m")],
            "nombres": {"plaza": "la plaza del pueblo",
                        "adornos": "guirnaldas de hojas y cintas",
                        "musica": "un laúd y dos flautas",
                        "comida": "pan caliente y sidra",
                        "faena": "martillos y sierras",
                        "pueblo": "el pueblo", "danio": "la última tormenta",
                        "destrozos": "tejados abiertos, vallas caídas, barro por todas partes",
                        "arreglado": "tejados nuevos, vallas en pie y madera recién cortada por todas partes",
                        "por": "casa por casa"},
            "eventos": ["fiesta", "mercado", "cosecha", "reparaciones", "luto"],
        },
        "problema": {
            "monstruo": "{esbirros.Cap} rondan {hogar} cada noche. Dicen que "
                        "{villano} ha despertado en {guarida} y que, si nadie "
                        "lo detiene, no quedará nada en pie.",
            "busqueda": "{meta.Cap} ha desaparecido, y con {meta.el} se ha "
                        "ido la última esperanza {hogar.de}. Se dice que "
                        "{villano} {meta.lo} guarda en {guarida}.",
        },
    },
    # ------------------------------------------------------------------
    "ciencia_ficcion": {
        "nombre": "Ciencia ficción",
        "desc": "estaciones remotas, corporaciones y silencio espacial",
        "inspiracion": ["dick", "herbert", "blade_runner", "alien"],
        "hogar": ["la estación Horizonte-9", "la colonia de Nueva Esperanza",
                  "el hábitat minero de Cerro Rojo"],
        "umbral": ["la esclusa del Sector 9", "el puerto de salto de Kepler",
                   "la compuerta de cuarentena"],
        "camino": ["el cinturón de asteroides de Argos",
                   "las rutas muertas del Vacío Exterior",
                   "la nebulosa de Orfeo"],
        "guarida": ["la nave nodriza Behemot", "la base secreta de Ceres",
                    "el reactor abandonado de Titán"],
        "metas": ["el núcleo de datos Aurora", "la llave del Archivo Estelar",
                  "el reactor de fusión perdido"],
        "dones": ["un módulo de navegación antiguo", "un implante de reflejos",
                  "un escudo personal experimental"],
        "herramientas": ["tu pistola de pulsos", "tu multiherramienta"],
        "guardianes": ["un dron de seguridad", "un androide centinela",
                       "un oficial de aduanas implacable"],
        "esbirros": ["los drones centinela", "los mercenarios sin bandera",
                     "los cazarrecompensas"],
        "refugios": ["un taller de reparaciones abandonado",
                     "una cápsula de carga reconvertida en vivienda"],
        "ambiente": [
            "Los paneles de la pared zumban con un pulso irregular.",
            "La luz de emergencia lo tiñe todo de rojo.",
            "El aire reciclado sabe a metal y a sudor.",
            "Una alarma lejana se repite y nadie le hace caso.",
            "Tras un ojo de buey, las estrellas parecen más frías que nunca.",
            "Un sistema de ventilación suspira, cansado de funcionar.",
            "El suelo vibra con el rumor sordo de los motores.",
            "Un indicador parpadea en ámbar, a la espera de que alguien lo atienda.",
        ],
        "mentores": [("la capitana retirada", "f"),
                     ("el ingeniero veterano", "m"), ("la doctora", "f")],
        "aliados": [("el piloto", "m"), ("la hacker", "f"),
                    ("el mecánico", "m")],
        "heraldos": [("la operadora de comunicaciones", "f"),
                     ("el técnico", "m"), ("la mensajera", "f")],
        "villanos": [("la Corporación Helix", "f"), ("el Almirante Kross", "m"),
                     ("la inteligencia Leviatán", "f")],
        "nombres_f": ["Vega", "Nadia", "Zara", "Mara", "Ilsa", "Okoye", "Lena",
                      "Suri"],
        "nombres_m": ["Teo", "Kenji", "Ilya", "Dax", "Rafe", "Oriol", "Jonas",
                      "Amadi"],
        "pueblo": {
            "oficios": [("la hidrocultora", "f"), ("el mecánico de muelle", "m"),
                        ("la médica del módulo", "f"), ("el cocinero del comedor", "m"),
                        ("la operaria de reciclaje", "f"), ("el electricista", "m"),
                        ("la tendera de suministros", "f"), ("el vigilante de turno", "m"),
                        ("la maestra de sección", "f"), ("el barman del módulo", "m")],
            "nombres": {"plaza": "el atrio central",
                        "adornos": "tiras de luz y banderines de plástico",
                        "musica": "un sintetizador de segunda mano",
                        "comida": "barritas dulces y té sintético",
                        "faena": "soldadores y llaves de carraca",
                        "pueblo": "la colonia", "danio": "el último fallo de presión",
                        "destrozos": "mamparos abollados, luces apagadas y charcos de refrigerante por todas partes",
                        "arreglado": "mamparos nuevos, luces encendidas y olor a soldadura reciente por todas partes",
                        "por": "módulo por módulo"},
            "eventos": ["fiesta", "mercado", "reparaciones", "luto"],
        },
        "problema": {
            "monstruo": "{esbirros.Cap} han cortado los suministros "
                        "{hogar.de}. Se rumorea que {villano} controla ahora "
                        "{guarida} y que seremos los siguientes.",
            "busqueda": "{meta.Cap} ha desaparecido {hogar.de}, y sin "
                        "{meta.el} no resistiremos mucho. Todo apunta a que "
                        "{villano} {meta.lo} tiene en {guarida}.",
        },
    },
    # ------------------------------------------------------------------
    "noir": {
        "nombre": "Noir",
        "desc": "ciudad lluviosa, secretos viejos y favores que se cobran",
        "inspiracion": ["chandler", "hammett", "chinatown", "halcon_maltes"],
        "hogar": ["el distrito de Puerto Gris", "el barrio de las Tres Chimeneas",
                  "la ciudad de Villanegra"],
        "umbral": ["la puerta del club Medianoche", "el control del puerto",
                   "el vestíbulo del hotel Imperial"],
        "camino": ["los callejones del Muelle Viejo",
                   "las calles empapadas del centro",
                   "el distrito de los casinos"],
        "guarida": ["la mansión de la colina", "el ático del hotel Meridiano",
                    "la torre del Banco Atlántico"],
        "metas": ["el libro de cuentas", "la grabación de la noche del puerto",
                  "el expediente Sombra"],
        "dones": ["una placa vieja", "una llave sin etiqueta",
                  "una tarjeta con un nombre y una dirección"],
        "herramientas": ["tu revólver", "tu libreta y tu instinto"],
        "guardianes": ["un portero del tamaño de un armario",
                       "un policía que no mira a los ojos",
                       "un recepcionista demasiado amable"],
        "esbirros": ["los hombres del sindicato", "los matones del puerto",
                     "los policías comprados"],
        "refugios": ["un bar casi vacío",
                     "una oficina con las persianas echadas"],
        "ambiente": [
            "La lluvia golpea los cristales como si quisiera entrar.",
            "El humo de un cigarrillo se enrosca bajo la luz de una farola.",
            "Un saxofón triste se cuela por alguna ventana.",
            "Las calles huelen a asfalto mojado y a secretos.",
            "Un neón parpadea, medio rojo, medio roto.",
            "Un teléfono suena en algún sitio y nadie se atreve a contestar.",
            "Los charcos reflejan luces que no parecen de aquí.",
            "Se oye un reloj, y cada tic suena a plazo vencido.",
        ],
        "mentores": [("el inspector retirado", "m"),
                     ("la periodista veterana", "f"), ("el viejo abogado", "m")],
        "aliados": [("la cantante", "f"), ("el taxista", "m"),
                    ("el forense", "m")],
        "heraldos": [("la clienta", "f"), ("el chico del periódico", "m"),
                     ("el viejo camarero", "m")],
        "villanos": [("el magnate Orlov", "m"), ("la señora Valcárcel", "f"),
                     ("el comisario Salas", "m")],
        "nombres_f": ["Rita", "Vera", "Lola", "Nora", "Greta", "Irene", "Dalia",
                      "Celia"],
        "nombres_m": ["Dante", "Bruno", "Leo", "Hugo", "Nico", "Víctor",
                      "Marcos", "Elías"],
        "pueblo": {
            "oficios": [("la camarera", "f"), ("el barbero", "m"), ("la florista", "f"),
                        ("el sereno", "m"), ("la modista", "f"), ("el quiosquero", "m"),
                        ("la telefonista", "f"), ("el zapatero", "m"), ("la pensionista", "f"),
                        ("el taxista", "m")],
            "nombres": {"plaza": "la plaza del barrio",
                        "adornos": "farolillos de papel y serpentinas",
                        "musica": "una banda de jazz de tres músicos",
                        "comida": "bocadillos y whisky barato",
                        "faena": "martillos y brochas",
                        "pueblo": "el barrio", "danio": "el último temporal",
                        "destrozos": "escaparates rotos, toldos arrancados y charcos por todas partes",
                        "arreglado": "escaparates nuevos, toldos puestos y olor a pintura fresca por todas partes",
                        "por": "local por local"},
            "eventos": ["fiesta", "mercado", "reparaciones", "luto"],
        },
        "problema": {
            "monstruo": "{esbirros.Cap} cobran «protección» en {hogar}, "
                        "y quien se niega aparece flotando en el puerto. "
                        "Detrás de todo está {villano}, que maneja {guarida} "
                        "como si fuera suya.",
            "busqueda": "{meta.Cap} ha desaparecido, y la gente que sabía "
                        "dónde estaba empieza a morir. Todos los hilos "
                        "conducen {villano.a}, que {meta.lo} guarda en "
                        "{guarida}.",
        },
    },
    # ------------------------------------------------------------------
    "terror": {
        "nombre": "Terror gótico",
        "desc": "pueblos aislados, niebla y algo que no debería despertar",
        "inspiracion": ["lovecraft", "stoker", "jackson_hh", "resplandor"],
        "hogar": ["el pueblo de Valle Hondo", "la aldea de Cuervo Seco",
                  "el caserío de Santa Perpetua"],
        "umbral": ["la verja del cementerio", "el puente de la niebla",
                   "el portón de la abadía"],
        "camino": ["el bosque de los Ahorcados", "la carretera de las Ánimas",
                   "los pantanos de Mortecina"],
        "guarida": ["la abadía abandonada", "el sótano del viejo molino",
                    "la cripta bajo la iglesia"],
        "metas": ["el grimorio sin nombre", "la reliquia de San Aldrico",
                  "el cuaderno del padre Anselmo"],
        "dones": ["un crucifijo de hierro", "un farol que nunca se apaga",
                  "un frasco de agua bendita"],
        "herramientas": ["tu escopeta de caza", "tu hacha de leñador"],
        "guardianes": ["un enterrador taciturno",
                       "un perro negro de ojos blancos",
                       "una niebla que susurra nombres"],
        "esbirros": ["los poseídos", "las sombras sin rostro",
                     "los muertos del cementerio"],
        "refugios": ["una capilla en ruinas",
                     "una casa con todas las ventanas tapiadas"],
        "ambiente": [
            "La niebla se pega a la piel como una mano fría.",
            "Una puerta lejana se cierra sola, y nadie la tocó.",
            "Hay un silencio demasiado espeso para ser natural.",
            "Las velas se doblan hacia la oscuridad, como si algo respirara.",
            "Un cuervo observa desde una rama, sin parpadear.",
            "Algo cruje arriba, donde no debería haber nadie.",
            "El aire huele a tierra removida y a cera quemada.",
            "Un frío súbito te recorre la nuca sin que sople el viento.",
        ],
        "mentores": [("el párroco", "m"), ("la anciana curandera", "f"),
                     ("el erudito", "m")],
        "aliados": [("el cazador", "m"), ("la forastera", "f"),
                    ("el sacristán", "m")],
        "heraldos": [("la niña", "f"), ("el alguacil", "m"), ("la viuda", "f")],
        "villanos": [("la Dama Pálida", "f"), ("el Hombre de la Niebla", "m"),
                     ("la Madre Hiedra", "f")],
        "nombres_f": ["Agnes", "Elsbeth", "Marta", "Clara", "Edith", "Berta",
                      "Ottilie", "Wilhelmina"],
        "nombres_m": ["Anselmo", "Tobías", "Gaspar", "Ignacio", "Matías", "Eloy",
                      "Lázaro", "Silas"],
        "pueblo": {
            "oficios": [("la lechera", "f"), ("el enterrador", "m"), ("la tabernera", "f"),
                        ("el campanero", "m"), ("la costurera", "f"), ("el leñador", "m"),
                        ("la partera", "f"), ("el sacristán", "m"), ("la hilandera", "f"),
                        ("el cazador", "m")],
            "nombres": {"plaza": "la plaza mayor",
                        "adornos": "coronas de flores secas y velas",
                        "musica": "un acordeón desafinado",
                        "comida": "pan negro y vino caliente",
                        "faena": "mazos y clavos",
                        "pueblo": "el pueblo", "danio": "la última tormenta",
                        "destrozos": "tejados abiertos, vallas caídas, barro hasta las rodillas",
                        "arreglado": "tejados nuevos, vallas en pie y madera recién cortada por todas partes",
                        "por": "casa por casa"},
            "eventos": ["fiesta", "mercado", "cosecha", "reparaciones", "luto"],
        },
        "problema": {
            "monstruo": "Cada luna llena desaparece alguien en {hogar}. "
                        "{esbirros.Cap} han sido vistos cerca {guarida.de}, y "
                        "todos saben quién los manda: {villano}.",
            "busqueda": "{meta.Cap} ha sido robad{meta.o}, y desde entonces "
                        "{hogar} no duerme. Todos dicen que {villano} "
                        "{meta.lo} oculta en {guarida}.",
        },
    },
}

# Lo que cada trama pide del objetivo. `{objetivo}` se usa tras "podrían ...".
OBJETIVOS = {
    "monstruo": "poner fin al poder {villano.de}",
    "busqueda": "recuperar {meta}",
}

TRAMAS = {
    "monstruo": {
        "nombre": "Vencer al monstruo",
        "desc": "una amenaza se cierne sobre los tuyos y hay que acabar con ella",
        "fuente": "booker",
    },
    "busqueda": {
        "nombre": "La búsqueda",
        "desc": "algo esencial se ha perdido y hay que traerlo de vuelta",
        "fuente": "booker",
    },
}

# bono_tono se suma a las tiradas; p_traidor es la probabilidad de que el
# aliado oculte una lealtad distinta.
TONOS = {
    "luminoso": {"nombre": "Luminoso", "bono": 1, "p_traidor": 0.20,
                 "desc": "la esperanza ayuda; los traidores son raros"},
    "equilibrado": {"nombre": "Equilibrado", "bono": 0, "p_traidor": 0.50,
                    "desc": "luces y sombras a partes iguales"},
    "sombrio": {"nombre": "Sombrío", "bono": -1, "p_traidor": 0.75,
                "desc": "el mundo no perdona y casi nadie es lo que parece"},
}

# stats: bonificación inicial a los atributos.
ARQUETIPOS = {
    "guerrero": {
        "nombre": "Guerrero", "desc": "fuerte y decidido (+Valor)",
        "stats": {"valor": 1},
        "rasgo": "eres de los primeros en dar un paso al frente cuando hay peligro",
    },
    "erudito": {
        "nombre": "Erudito", "desc": "observador y astuto (+Ingenio)",
        "stats": {"ingenio": 1},
        "rasgo": "lees más rápido de lo que otros hablan y casi nada se te escapa",
    },
    "sanador": {
        "nombre": "Sanador", "desc": "empático y paciente (+Compasión)",
        "stats": {"compasion": 1},
        "rasgo": "nadie se ha marchado nunca de tu lado sin sentirse un poco mejor",
    },
    "picaro": {
        "nombre": "Pícaro", "desc": "escurridizo y ambicioso (+Ingenio, +Ambición)",
        "stats": {"ingenio": 1, "sombra": 1},
        "rasgo": "sabes salir de cualquier aprieto y no siempre preguntas el precio",
    },
}

# Una falla (Aristóteles: hamartia) que la historia pondrá a prueba.
# penaliza: enfoque en el que la falla estorba (-1 a sus tiradas).
FALLAS = {
    "orgullo": {
        "nombre": "Orgullo", "desc": "te cuesta pedir ayuda (-1 a Compasión)",
        "penaliza": "compasion", "sombra": 0,
        "texto": "te cuesta una barbaridad pedir ayuda",
        "voz_inicio": "Una voz te susurra que no necesitas a nadie, que ir sin "
                      "compañía sería más fácil.",
        "tentacion_meta": "Piensas que nadie más sabría usarla bien. Tú sí.",
        "voz_final": "«Nadie te ayudó a llegar hasta aquí —susurra la voz de "
                     "siempre—. ¿Para qué compartir lo que solo tú has ganado?»",
        "leccion_ok": "Aprendiste que pedir ayuda no te hace más pequeño.",
        "leccion_mal": "Nunca llegaste a aprender que se puede ser fuerte sin "
                       "estar solo.",
    },
    "miedo": {
        "nombre": "Miedo", "desc": "te paralizas ante el peligro (-1 a Valor)",
        "penaliza": "valor", "sombra": 0,
        "texto": "el miedo te paraliza cuando todo se pone difícil",
        "voz_inicio": "Una voz te susurra que aún estás a tiempo de quedarte, "
                      "de cerrar la puerta y fingir que nada ha pasado.",
        "tentacion_meta": "Piensas que con ella nunca más volverías a tener miedo.",
        "voz_final": "«Aún puedes huir —susurra la voz de siempre—. Nadie te "
                     "culparía.»",
        "leccion_ok": "Aprendiste que el valor no es la ausencia de miedo, sino "
                      "caminar con él al lado.",
        "leccion_mal": "El miedo, al final, siguió mandando en ti.",
    },
    "rencor": {
        "nombre": "Rencor", "desc": "no olvidas una ofensa (-1 a Ingenio)",
        "penaliza": "ingenio", "sombra": 0,
        "texto": "no olvidas jamás una ofensa",
        "voz_inicio": "Una rabia fría te empuja hacia adelante: piensas en todo "
                      "lo que te han quitado.",
        "tentacion_meta": "Piensas en todo lo que podrías hacer pagar con ella.",
        "voz_final": "«Que paguen —susurra la voz de siempre—. Todos ellos. Te "
                     "lo debes.»",
        "leccion_ok": "Aprendiste que soltar el rencor pesa menos que cargarlo.",
        "leccion_mal": "El rencor ocupó, al final, el lugar que antes tenían "
                       "tus sueños.",
    },
    "codicia": {
        "nombre": "Codicia", "desc": "nunca te basta (+1 Ambición inicial)",
        "penaliza": None, "sombra": 1,
        "texto": "nunca te basta con lo que tienes",
        "voz_inicio": "Piensas en lo que podrías ganar, y se te acelera el pulso.",
        "tentacion_meta": "Piensas en lo que sería tenerla solo para ti.",
        "voz_final": "«Es tuya —susurra la voz de siempre—. Siempre pudo serlo. "
                     "¿Cuánto más vas a esperar?»",
        "leccion_ok": "Aprendiste que hay cosas que se pierden al intentar "
                      "poseerlas.",
        "leccion_mal": "Tenías todo lo que hacía falta, y aun así querías más.",
    },
}


# --------------------------------------------------------------------------
# Mezcla de géneros
# --------------------------------------------------------------------------
_PESO_PRINCIPAL = 2     # el género principal pesa el doble que cada secundario


def mezclar_generos(principal: str, secundarios=()) -> dict:
    """El léxico de un mundo que mezcla géneros.

    Cada lista (lugares, villanos, guardianes, nombres, ambiente...) es la unión
    de las del género principal y los secundarios, con el principal repetido
    para que domine. Lo que no es una lista (la plantilla del problema) se toma
    del principal. Sin secundarios devuelve el léxico del género tal cual.
    """
    base = GENEROS[principal]
    otros = [g for g in dict.fromkeys(secundarios) if g in GENEROS and g != principal]
    if not otros:
        return base
    mezcla = {}
    for clave, valor in base.items():
        if isinstance(valor, list):
            union = list(valor) * _PESO_PRINCIPAL
            for g in otros:
                union += GENEROS[g][clave]
            # sin duplicados consecutivos pero conservando el peso de cada entrada
            mezcla[clave] = union
        else:
            mezcla[clave] = valor
    mezcla["nombre"] = " + ".join([base["nombre"]] + [GENEROS[g]["nombre"] for g in otros])
    mezcla["inspiracion"] = list(dict.fromkeys(
        base["inspiracion"] + [f for g in otros for f in GENEROS[g]["inspiracion"]]))
    return mezcla

