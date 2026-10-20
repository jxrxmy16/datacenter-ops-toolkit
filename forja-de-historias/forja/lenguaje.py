"""Intérprete de texto libre en español, sin IA: léxico de raíces + reglas.

Dado "salir del bosque caminando con los ojos cerrados", averigua:

  * la INTENCIÓN dominante (valor, ingenio, compasión, ambición, duda, o una
    de las acciones de exploración: observar, hablar, descansar, moverse);
  * los MODIFICADORES de dificultad ("con los ojos cerrados" la sube,
    "con cuidado" la baja) y el fragmento exacto que escribió el jugador;
  * las ENTIDADES nombradas (el mentor, el guardián, el hogar...);
  * si encaja con alguna de las opciones de la escena (por intención y por
    palabras compartidas con su texto);
  * si la acción es IMPOSIBLE en este momento del relato (hablar con alguien
    que murió, ir a un sitio al que aún no se puede llegar).

No entiende el lenguaje: reconoce raíces de palabras. Por eso siempre muestra
al jugador cómo lo ha interpretado, y le deja corregirlo.
"""

import re
import unicodedata
from dataclasses import dataclass, field

CLASES_ACCION = ("valor", "ingenio", "compasion", "sombra", "duda")
CLASES_EXPLORACION = ("observar", "hablar", "descansar", "moverse")
CLASES = CLASES_ACCION + CLASES_EXPLORACION
# Orden de desempate: primero las acciones que deciden.
_ORDEN = {c: i for i, c in enumerate(CLASES)}

# Qué enfoque de las opciones corresponde a cada intención de acción.
ENFOQUE_DE = {"valor": "valor", "ingenio": "ingenio", "compasion": "compasion",
              "sombra": "sombra", "duda": None}

# Una acción de exploración se parece también a alguna acción de decisión.
AFINIDAD = {
    "hablar": {"compasion": 0.6, "ingenio": 0.4},
    "observar": {"ingenio": 0.7},
    "moverse": {"valor": 0.3, "duda": 0.2},
    "descansar": {"duda": 0.5},
}

MIN_LETRAS_CORRECCION = 8      # el corrector de erratas solo actúa en palabras largas
UMBRAL_CONFIANZA = 0.8        # por debajo, el intérprete pregunta en lugar de suponer
MAX_CARACTERES = 300          # una acción es una línea; más se recorta
_TOKEN = re.compile(r"[\wáéíóúüñÁÉÍÓÚÜÑ]+", re.UNICODE)


# --------------------------------------------------------------------------
# Normalización
# --------------------------------------------------------------------------
def quitar_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower()


def normalizar_token(token: str) -> str:
    t = quitar_tildes(token)
    return re.sub(r"(.)\1{2,}", r"\1", t)          # "ataaacooo" -> "ataco"


def tokenizar(texto: str):
    originales = _TOKEN.findall(texto)
    return originales, [normalizar_token(t) for t in originales]


# --------------------------------------------------------------------------
# Léxico
# --------------------------------------------------------------------------
_FORMAS = {
    "ar": ("ar o as a amos an e es emos en aba abas abamos aban are ara aremos aran "
           "aria arias ariamos arian ando ado ada ados adas aste aron").split(),
    "er": ("er o es e emos en a as amos an ia ias iamos ian ere era eremos eran "
           "eria erias eriamos erian iendo ido ida idos idas i imos iste io ieron").split(),
    "ir": ("ir o es e imos en a as amos an ia ias iamos ian ire ira iremos iran "
           "iria irias iriamos irian iendo ido ida idos idas i iste io ieron").split(),
}


def conjugar(raiz: str, tipo: str) -> set:
    """Formas regulares de un verbo (sin tildes), con cambios c/qu, g/gu, z/c."""
    formas = set()
    for f in _FORMAS[tipo]:
        r = raiz
        if f and f[0] in "eé" and tipo == "ar":
            if raiz.endswith("c"):
                r = raiz[:-1] + "qu"
            elif raiz.endswith("g"):
                r = raiz[:-1] + "gu"
            elif raiz.endswith("z"):
                r = raiz[:-1] + "c"
        formas.add(r + f)
    return formas


def _leer(texto: str):
    """Interpreta una cadena de léxico.

    raiz           prefijo de palabra          (atac -> atacar, ataco, atacando)
    raiz:0.5       idem con otro peso
    =palabra       palabra exacta              (=mato)
    +raiz *raiz ~raiz   verbo regular -ar / -er / -ir
    """
    prefijos, exactas = {}, {}
    for item in texto.split():
        peso = 1.0
        if ":" in item:
            item, p = item.rsplit(":", 1)
            peso = float(p)
        if item[0] in "+*~":
            tipo = {"+": "ar", "*": "er", "~": "ir"}[item[0]]
            for forma in conjugar(item[1:], tipo):
                exactas[forma] = peso
        elif item[0] == "=":
            exactas[item[1:]] = peso
        else:
            prefijos[item] = peso
    return prefijos, exactas


LEXICO_TEXTO = {
    "valor": """
        atac enfrent combat embist luch pele golpe destroz derrib aplast arremet desenvain
        blandi dispar forz empuj repel contraatac abalanz resist aguant defend derrot
        aniquil machac patad punet apunal acuchill estoc decapit carga cargu embest
        guantaz mampor paliz apunt:0.6 empun desenfund demol aporre zurr abofete hostig
        embrav acomet cabezaz embestid
        lanz:0.6 arroj:0.6 abat:0.5 sacud:0.5 valent:0.6 brav:0.6 audaz:0.6 empujon:0.8
        =cargo =herir =hiero =hieres =hiere =hirio =hiriendo =tortas =tumbo =tumbar:0.6
        +mat +pate +peg:0.8
    """,
    "ingenio": """
        engan minti mient finj fing disfraz distra trampa planific planea calcul
        deduc infer ingeni improvis aprovech astuc truc sorprend sabot manipul regate
        esquiv evad sigil camufl infiltr senuel cebo derrumb bloque desvi atajo
        terren ardid estratagem argucia maquin ocurr invent simul imit suplant
        pirat enred embauc camel furtiv disimul sutil subterfug pretext fals
        falsific despist provoc cortocircuit ganzu labia
        analiz:0.5 negoci:0.7 ocult:0.6 escond:0.5 excusa:0.8 hack:0.8 pens:0.4
        =planeo =plan =rodear =rodeo =rodeamos =rodeando =colar =colarme =colarse
        =colarnos =cuelo =cuela =idea =farol:0.5
    """,
    "compasion": """
        ayud auxili socorr sana consol calm tranquiliz abraz perdon disculp compart
        ofrec proteg salv rescat apoy acompan consuel empati reconcili cobij abrig
        aliment piedad compas amab gentil amistad sosten
        convenc:0.7 persuad:0.7 comprend:0.6 entend:0.3 escuch:0.3 entreg:0.4
        =curar =curo =curas =curamos =curan =curarle =curarla =curarlo =curalo
        =curala =curame =cuidar =cuido =cuidas =cuida =cuidamos =cuidan =cuidarle
        =cuidarla =cuidarlo =animar =animo =animas =animarle =vendar =vendo
        =vendarle =vendarla =vendarlo
    """,
    "sombra": """
        hurt saque amenaz intimid chantaj extors soborn traicion apropi domin tortur
        exig codici ambici despiadad cruel mezquin rapi coaccion chivat chiv delat
        denunci estaf desvalij mang birl afan chor
        asust:0.8 explot:0.6 abandon:0.8 ignor:0.5 aprovech:0.3 timo:0.6
        =cobrar =cobro =cobra =cobras =quemo =quemar =quemarle +rob:1.4 +vaci:0.4
    """,
    "duda": """
        escap fug retir retroced rechaz evit dud titube paraliz tembl rendici
        esper rend:0.8 escond:1.0 ignor:0.5 cobard:0.8
        =huir =huyo =huyes =huye =huimos =huyen =huyendo =huido =huyamos =huid
        =quedo =quedar =quedarme =quedarse =quedate =quedamos =quedas
        =negar =niego =niegas =niega =negarme =negarse =negamos =negativa
        =rendir =rendirme =rendirse =rindo =rendi =rinde =rindete
        =piro =pirarme =pirarse =pirate =pira +larg
    """,
    "observar": """
        mir observ examin invest inspeccion busc revis registr escuch huel explor
        vigil atisb otear rastre fij reconoc record recuerd contempl lectur
        estudi:0.6 pens:0.8 reflexion medit analiz:0.7 evalu sopes atent:0.5 ojear
        hojear curiose cotille espi
        =oler =ver =veo =ves =vemos =ven =viendo =visto =leer =leo =lee =leemos
        =leyendo +olfate
    """,
    "hablar": """
        habl conver platic pregunt contest respond salud suplic rog explic dialog
        confes interrog propon susurr comunic avis advert inform aconsej consej charl
        relat narr palique sonsac
        grit:0.6 cuent:0.6 present:0.3
        =decir =digo =dices =dice =decimos =dicen =dime =dile =diciendo =dijo =dijimos
        =pedir =pido =pides =pide =pedimos =piden =pidiendo =pidele =pidelo =pedi
        =pedia =pediria =pedire =pidio +llam +cont:0.8
    """,
    "descansar": """
        descans dorm duerm durm:1.3 siest cabezad repos recuper recost relaj respir
        acamp recobr reventad agotad cansad
        polvo:0.3
        =sentarme =sentarse =sientate =sentarnos =sentandome =tumbarme =tumbarse
        =tumbarnos =vendarme =vendarse =sueno =suenito =suenecito =comer:0.9
        =comerme:0.9 =comiendo:0.9 =beber:0.7 =comida:0.5 =pan:0.5 =queso:0.5
        =bocata:0.5 =bocadillo:0.5 =vendo:0.8
    """,
    "moverse": """
        camin avanz entr cruz baj regres acerc aleja viaj trep escal atraves recorr
        pase rumb dirig lleg volv vuelv adent descend ascend
        march:0.6 adelant:0.5 mov:0.6 muev:0.6 desplaz arrastr:0.5 repto atrav
        sendero:0.4 alante:0.8
        =ir =voy =vas =va =vamos =van =iba =fui =fue =vaya =yendo =ido =ire
        =subir =subo =subes =sube =subimos =suben =subiendo =sub
        =salir =salgo =sales =sale =salimos =salen =salga =salgamos =salio =saldre =sal
        =seguir =sigo =sigue =sigues =seguimos =siguen =siguiendo =siguio =seguire
        =pasar:0.5 =paso:0.5 =pasas:0.5 =pasa:0.5 =pasamos:0.5 =pasan:0.5 =pasando:0.5
        *corr:0.9
    """,
}

# --- índices: se construyen en `reconstruir()` (al final de esta sección) ------
_PREFIJOS = []            # (raiz, clase, peso)
_PREF_POR_INICIO = {}     # primeras 3 letras -> [(raiz, clase, peso)]
_EXACTAS = {}             # palabra -> [(clase, peso)]
FRASES = []
_VOCABULARIO = []
_VOCAB_POR_INICIO = {}

# Frases: todas las raíces deben aparecer cerca (en cualquier orden).
# Cada raíz: `abc*` prefijo, `a|b` alternativas, 4+ letras prefijo, 3 o menos exacta.
# "@hacer" se expande a hac*/hag*/hic*/hiz* (hacer, hago, haga, hice, hizo).
_FRASES_BASE = [
    (("tend*", "mano"), {"compasion": 2.0}),
    (("tiend*", "mano"), {"compasion": 2.0}),
    (("ech*", "mano"), {"compasion": 1.6}),
    (("ech*", "cable"), {"compasion": 1.6}),
    (("sosten*", "mano"), {"compasion": 1.6}),
    (("dar|doy|da|dale|dame|entreg*|ofrec*|pas*|compart*|comparto|sirvo|sirv*",
      "com*|beb*|raci*|pan|agua|trozo|bocata|bocadillo|aliment*|medicin*|pocion|venda*|"
      "manzana|fruta|sopa|caldo|leche|vino|bocado|mendrug*|migaja*|cena|desayuno|abrigo|manta"),
     {"compasion": 2.0}),
    (("plant*", "cara"), {"valor": 2.0}),
    (("abr*", "paso"), {"valor": 2.0}),
    (("@hacer", "frente"), {"valor": 2.0}),
    (("part*", "cara"), {"valor": 2.0}),
    (("cabeza", "contra"), {"valor": 1.5}),
    (("a", "golpes"), {"valor": 1.0}),
    (("dar|doy|da|dale|darle", "espald"), {"duda": 1.5}),
    (("dand*", "espald"), {"duda": 1.5}),
    (("no", "@hacer", "nada"), {"duda": 2.5}),
    (("sin", "@hacer", "nada"), {"duda": 2.5}),
    (("@hacer", "ruido"), {"ingenio": 1.0}),
    (("@hacer", "muert"), {"ingenio": 1.5, "duda": 0.8}),
    (("fing*", "muert"), {"ingenio": 1.5}),
    (("@hacer", "pas*", "por"), {"ingenio": 2.0}),
    (("@hacer", "tonto"), {"ingenio": 1.2}),
    (("@hacer", "farol"), {"ingenio": 2.0}),
    (("@hacer", "cre*"), {"ingenio": 1.5}),
    (("cuento", "chino"), {"ingenio": 1.5}),
    (("salir", "corr*"), {"duda": 2.0}),
    (("salgo", "corr*"), {"duda": 2.0}),
    (("ech*", "corr*"), {"duda": 2.0}),
    (("volv*", "atras"), {"duda": 1.5}),
    (("vuelv*", "atras"), {"duda": 1.5}),
    (("tir*", "toalla"), {"duda": 2.0}),
    (("abandon*", "misi*"), {"duda": 2.5}),
    (("ni", "cona"), {"duda": 2.0}),
    (("ni", "loco"), {"duda": 2.0}),
    (("ni", "hablar"), {"duda": 1.5}),
    (("de", "ninguna", "manera"), {"duda": 1.5}),
    (("pas*", "de", "todo"), {"duda": 2.5}),
    (("no", "me", "meto"), {"duda": 2.0}),
    (("@hacer", "lado"), {"duda": 1.5}),
    (("no", "abr*", "puerta"), {"duda": 1.5}),
    (("alz*|levant*", "manos"), {"duda": 1.0}),
    (("entreg*", "arma*"), {"duda": 1.5}),
    (("esper*", "ver"), {"duda": 1.5}),
    (("decidir", "nada"), {"duda": 1.5}),
    (("me", "asust*"), {"duda": 1.0}),
    (("de", "largo"), {"sombra": 1.2, "duda": 0.5}),
    (("sin", "piedad"), {"sombra": 1.5}),
    (("sin", "compas*"), {"sombra": 1.5}),
    (("sangre", "fria"), {"sombra": 1.5}),
    (("solo", "para", "mi"), {"sombra": 1.5}),
    (("no", "parte"), {"sombra": 1.5}),
    (("sin", "reparti*"), {"sombra": 1.5}),
    (("dej*", "tirad*"), {"sombra": 2.0}),
    (("aprovech*", "de"), {"sombra": 1.2}),
    (("aprovech*", "confianza"), {"sombra": 2.0}),
    (("sac*", "dinero|pasta|monedas"), {"sombra": 1.5}),
    (("tom*", "respiro"), {"descansar": 2.0}),
    (("tom*", "aire"), {"descansar": 1.5}),
    (("pas*", "noche"), {"descansar": 1.5}),
    (("qued*", "dormid*"), {"descansar": 1.5}),
    (("ech*", "dormir"), {"descansar": 1.2}),
    (("pill*", "sueno"), {"descansar": 1.5}),
    (("@hacer", "pausa"), {"descansar": 1.5}),
    (("@hacer", "alto"), {"descansar": 1.5}),
    (("mir*", "alrededor"), {"observar": 1.0}),
    (("recorr*", "mirada"), {"observar": 2.0}),
    (("ech*", "ojo"), {"observar": 1.5}),
    (("qued*", "mirando"), {"observar": 1.5}),
    (("pid*|ped*", "ayud*"), {"compasion": 0.5}),
    (("pid*|ped*", "perdon"), {"compasion": 1.0}),
    (("tir*", "lengua"), {"hablar": 1.5}),
    (("tir*", "tejos"), {"hablar": 1.0}),
    (("ve", "hasta"), {"moverse": 1.5}),
    (("plant*", "en"), {"moverse": 0.8}),
]


_HACER = ("hacer|hace|haces|hacemos|hacen|haciendo|hago|haga|hagas|hagamos|hagan|"
          "hice|hizo|hicieron|hecho|haz")


def _expandir_frases(base):
    """«@hacer» -> las formas de hacer (sin «hacia», que empezaría igual)."""
    return [(tuple(_HACER if x == "@hacer" else x for x in patron), pesos)
            for patron, pesos in base]



# Modificadores de dificultad: (raíces cercanas, delta, descripción).
_MODIFICADORES_BASE = [
    (("ojos", "cerr"), +2, "a ciegas"),
    (("cerr", "ojos"), +2, "a ciegas"),
    (("ojos", "vend"), +2, "a ciegas"),
    (("ciegas",), +2, "a ciegas"),
    (("sin", "mirar"), +1, "sin mirar"),
    (("de", "^espaldas"), +1, "de espaldas"),
    (("cierr", "^los", "^ojos"), +2, "a ciegas"),
    (("descalz",), +1, "descalzo"),
    (("desarmad",), +1, "sin armas"),
    (("sin", "arma"), +1, "sin armas"),
    (("sin", "luz"), +1, "sin luz"),
    (("con", "^una", "^mano"), +1, "con una mano"),
    (("con", "^una", "^sola", "^mano"), +1, "con una mano"),
    (("atand*|atad*|atar", "una", "mano"), +1, "con una mano"),
    (("sin", "herramient"), +1, "sin herramientas"),
    (("sin", "usar", "manos"), +1, "sin usar las manos"),
    (("oscuras",), +1, "a oscuras"),
    (("despacit",), -1, "despacito"),
    (("despues", "planear"), -1, "tras planearlo"),
    (("un", "pie"), +1, "a la pata coja"),
    (("pata", "coja"), +1, "a la pata coja"),
    (("sin", "pensar"), +1, "sin pensar"),
    (("a", "lo", "loco"), +1, "a lo loco"),
    (("desesper",), +1, "a la desesperada"),
    (("imprudent",), +1, "con imprudencia"),
    (("temerari",), +1, "con temeridad"),
    (("borrach",), +1, "borracho"),
    (("sin", "ayuda"), +1, "sin ayuda"),
    (("con", "cuidado"), -1, "con cuidado"),
    (("cautel",), -1, "con cautela"),
    (("despacio",), -1, "despacio"),
    (("lentamente",), -1, "lentamente"),
    (("paso", "paso"), -1, "paso a paso"),
    (("con", "calma"), -1, "con calma"),
    (("tranquilamente",), -1, "con tranquilidad"),
    (("paciencia",), -1, "con paciencia"),
    (("en", "silencio"), -1, "en silencio"),
    (("silenciosamente",), -1, "en silencio"),
    (("sigilosamente",), -1, "con sigilo"),
    (("sin", "ruido"), -1, "sin ruido"),
    (("sin", "hacer", "ruido"), -1, "sin hacer ruido"),
    (("bien", "preparad"), -1, "bien preparado"),
    (("tras", "planear"), -1, "tras planearlo"),
    (("con", "astucia"), -1, "con astucia"),
]
MODIFICADORES = list(_MODIFICADORES_BASE)       # base + los que añade el vocabulario ampliado

# Fuera del mundo del juego: si aparecen y nada del mundo, no es una acción.
_FUERA_DE_MUNDO_BASE = {"telefono", "movil", "celular", "taxi", "pizza", "instagram",
                   "whatsapp", "internet", "google", "wifi", "email", "facebook",
                   "tiktok", "netflix", "futbol", "politica", "publico", "gasto",
                   "narrador", "juego", "ordenador", "app", "tokio", "equipo",
                   "fichar", "recortar", "videojuego", "youtube", "twitter"}
_FUERA_DE_MUNDO = set(_FUERA_DE_MUNDO_BASE)       # base + las que añade el vocabulario ampliado

NEGADORES = {"no", "nunca", "jamas", "ni", "tampoco", "sin"}
_IGNORADAS = {"apoyado", "apoyada", "apoyados", "apoyadas"}
NEGACION_INVERSA = {"valor": ("duda", 0.7), "duda": ("valor", 0.7)}

_RELLENO = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
            "a", "en", "con", "por", "para", "y", "o", "que", "se", "me", "te", "lo",
            "le", "les", "mi", "mis", "tu", "tus", "su", "sus", "es", "ya", "muy",
            "mas", "como", "si", "pero", "sin", "sobre", "hacia", "entre", "este",
            "esta", "ese", "esa", "eso", "esto", "bien", "tan", "e", "u", "nos"}

_CLITICOS = ("selo", "sela", "selos", "selas", "melo", "mela", "telo", "tela",
             "nos", "les", "los", "las", "lo", "la", "le", "me", "te", "se")


def _candidatas(token: str):
    """El token y sus variantes sin pronombres pegados (atacalo -> ataca)."""
    vistas = [token]
    for _ in range(2):
        nuevas = []
        for t in vistas:
            for c in _CLITICOS:
                if t.endswith(c) and len(t) - len(c) >= 3:
                    base = t[: -len(c)]
                    if base not in vistas and base not in nuevas:
                        nuevas.append(base)
        vistas += nuevas
    return vistas


def _variantes_ortograficas(token: str):
    """Formas alternativas de escribir lo mismo: [(variante, raíz mínima)].

    k->c/qu y la h inicial perdida (ataka, ablar) valen con cualquier raíz. Los
    cambios de letras que suenan igual (v/b, ll/y, s/c, g/j...) son más
    arriesgados ("hay" -> "hall..."), así que solo casan con raíces de 5 o más.
    """
    vs = [(token, 3)]
    if "k" in token:
        vs.append((re.sub(r"k([eiy])", r"qu\1", token).replace("k", "c"), 3))
    if token[:1] in "aeiou":
        vs.append(("h" + token, 3))
    if len(token) >= 5:
        for a, b in (("v", "b"), ("b", "v"), ("ll", "y"), ("y", "ll"), ("s", "c"),
                     ("c", "s"), ("z", "c"), ("s", "z"), ("g", "j"), ("j", "g")):
            if a in token:
                vs.append((token.replace(a, b, 1), 5))
    return vs


def coincidencias(token: str) -> dict:
    """{clase: peso} de un token (el mayor peso por clase)."""
    mejor = {}
    for variante, minimo in _variantes_ortograficas(token):
        _sumar(mejor, variante, minimo)
        if mejor:
            break
    return mejor


def _sumar(mejor: dict, token: str, minimo: int = 3) -> None:
    for cand in _candidatas(token):
        antes = len(mejor)
        for clase, peso in _EXACTAS.get(cand, ()):
            mejor[clase] = max(mejor.get(clase, 0.0), peso)
        if len(cand) >= 3:
            for raiz, clase, peso in _PREF_POR_INICIO.get(cand[:3], ()):
                if len(raiz) >= minimo and cand.startswith(raiz):
                    mejor[clase] = max(mejor.get(clase, 0.0), peso)
        if len(mejor) > antes:
            return                      # la forma original manda sobre la que pierde su clítico


def _a_distancia_1(a: str, b: str) -> bool:
    """¿Se diferencian en una sola letra (cambio, falta, sobra o intercambio)?"""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        d = [i for i in range(la) if a[i] != b[i]]
        if len(d) == 1:
            return True
        return (len(d) == 2 and d[1] == d[0] + 1
                and a[d[0]] == b[d[1]] and a[d[1]] == b[d[0]])
    if la > lb:
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


def _corregir(token: str):
    """Reconoce una errata leve de una palabra larga (enboscada -> emboscada).

    Solo palabras de 8 o más letras, a una letra de distancia, con el mismo
    comienzo (2 letras) y el mismo final (2 letras): con menos exigencia, palabras
    corrientes pasan a ser del léxico (mantas ~ matas, partido ~ partio).
    """
    if len(token) < MIN_LETRAS_CORRECCION or token in _RELLENO:
        return None
    for p in _VOCAB_POR_INICIO.get(token[:2], ()):
        if (abs(len(p) - len(token)) <= 1 and p[-2:] == token[-2:]
                and _a_distancia_1(token, p)):
            return p
    return None


# --------------------------------------------------------------------------
# Construcción de los índices (léxico base + vocabulario ampliado)
# --------------------------------------------------------------------------
def raices_de_verbo(spec: str):
    """De un infinitivo saca sus raíces: (prefijos, formas exactas, peso).

    "almorzar|almuerz"  raíz regular (almorz) y raíz irregular (almuerz)
    "tomar:0.6"         con peso
    Las raíces de menos de 4 letras son demasiado ambiguas para ser prefijo:
    se convierten en formas exactas conjugadas.
    """
    cuerpo, _, p = spec.partition(":")
    peso = float(p) if p else 1.0
    base, *irreg = [quitar_tildes(x).strip() for x in cuerpo.split("|")]
    if base.endswith("se"):
        base = base[:-2]
    tipo = base[-2:]
    if tipo not in _FORMAS or len(base) < 3:
        return set(), ({base} if base else set()), peso
    raiz = base[:-2]
    cand = {raiz} | {i for i in irreg if i}
    if base.endswith("car"):
        cand.add(raiz[:-1] + "qu")
    elif base.endswith("gar"):
        cand.add(raiz + "u")
    elif base.endswith("zar"):
        cand.add(raiz[:-1] + "c")
    elif base.endswith(("ger", "gir")):
        cand.add(raiz[:-1] + "j")
    prefijos, exactas = set(), {base}
    for c in cand:
        if len(c) >= 4:
            prefijos.add(c)
        elif c:
            exactas.update(conjugar(c, tipo))
    return prefijos, exactas, peso


def _extras_de_entorno():
    """Vocabularios adicionales: rutas JSON en FORJA_LEXICO_EXTRA (separadas por os.pathsep)."""
    import json
    import os
    fuentes = []
    for ruta in filter(None, os.environ.get("FORJA_LEXICO_EXTRA", "").split(os.pathsep)):
        try:
            with open(ruta, encoding="utf-8") as f:
                fuentes.append(json.load(f))
        except (OSError, ValueError):
            pass
    return fuentes


def _partir_peso(item: str):
    palabra, _, p = item.partition(":")
    try:
        return palabra, (float(p) if p else 1.0)
    except ValueError:
        return palabra, 1.0


# Palabras corrientes que no dicen nada de la intención: nunca se aprenden como raíz
# (si no, «mejor» o «ahora» acabarían puntuando para siempre en una intención).
_FUNCIONALES = set("""
    mejor peor ahora antes luego despues tambien siempre nunca jamas mucho mucha muchos
    muchas poco poca pocos pocas algo nada alguien nadie todo todos toda todas cada otro
    otra otros otras mismo misma mismos mismas tanto tanta tantos tantas aqui alli ahi alla
    aca donde cuando mientras aunque porque pues entonces solo sola solos solas solamente
    quiza quizas tal vez veces cosa cosas manera forma momento tiempo parte lado esto eso
    aquello aquel aquella aquellos aquellas estos estas esos esas quien quienes cual cuales
    cuanto cuanta hacia hasta desde entre sobre bajo tras ante segun contra durante
    mediante ademas incluso apenas casi bastante demasiado demasiada menos propio propia
    nuestro nuestra nuestros nuestras vuestro vuestra ellos ellas nosotros nosotras usted
    ustedes estoy estas estamos estan estaba estaban tengo tienes tiene tenemos tienen
    tenia hecho hecha hacer hice hizo haber habia habra seria sera somos eran eres fuera
    fuese tenga tengas poder queda quedan sino pero ademas bien mal asi casi igual mismo
    lugar sitio vamos vais dime dile dice dicen digo dijo hace hacen hacia otro unos unas
    segun luego ahora""".split())
_PERSONAL = {}               # {clase: {"raices": [...]}} lo que ha enseñado el jugador
_FRASES_PERSONALES = {}      # frase normalizada -> clase


def fijar_personal(datos) -> None:
    """Carga (o vacía, con None) el vocabulario que el jugador ha ido enseñando."""
    global _PERSONAL, _FRASES_PERSONALES
    datos = datos if isinstance(datos, dict) else {}
    raices = datos.get("raices")
    frases = datos.get("frases")
    raices = raices if isinstance(raices, dict) else {}
    frases = frases if isinstance(frases, dict) else {}
    _PERSONAL = {c: {"raices": [x for x in v if isinstance(x, str)]}
                 for c, v in raices.items() if c in CLASES and isinstance(v, list)}
    _FRASES_PERSONALES = {k: c for k, c in frases.items()
                          if isinstance(k, str) and c in CLASES}
    _indexar()


def personal_a_dict() -> dict:
    return {"raices": {c: sorted(set(d["raices"])) for c, d in _PERSONAL.items()},
            "frases": dict(_FRASES_PERSONALES)}


def aprender(texto: str, clase: str, w) -> list:
    """Anota que `texto` significa `clase`: aprende sus palabras desconocidas.

    Devuelve las raíces nuevas. Las palabras desconocidas se guardan como raíz
    (quitando la terminación, para que sirvan otras conjugaciones) y la frase
    entera se recuerda tal cual.
    """
    if clase not in CLASES:
        return []
    _, norm = tokenizar(" ".join(texto.split())[:MAX_CARACTERES])
    alias = _alias(w)
    modificadores = set()
    for patron, _, _ in MODIFICADORES:
        ids = _ventana(norm, patron)
        if ids is not None:
            modificadores.update(ids)
    nuevas = []
    for i, t in enumerate(norm):
        if len(t) < 4 or t in _RELLENO or t in alias or t in _IGNORADAS \
                or t in _FUNCIONALES or t in _AUXILIARES or t in NEGADORES \
                or i in modificadores or coincidencias(t):
            continue
        raiz = t[:-2] if len(t) >= 8 else (t[:-1] if len(t) >= 6 else t)
        if raiz not in nuevas:
            nuevas.append(raiz)
    for raiz in nuevas:
        _PERSONAL.setdefault(clase, {"raices": []})["raices"].append(raiz)
    if norm:
        _FRASES_PERSONALES[" ".join(norm)] = clase
    _indexar()
    return nuevas


def reconstruir(extra=None) -> None:
    """(Re)construye los índices. `extra` es un vocabulario adicional opcional."""
    global _BASE, MODIFICADORES, _FUERA_DE_MUNDO
    from . import vocabulario
    base = vocabulario.VOCABULARIO
    fuentes = [base] + _extras_de_entorno() + ([extra] if extra else [])

    # Matices de dificultad y palabras de fuera del mundo: listas aparte del léxico.
    matices = list(_MODIFICADORES_BASE)
    fuera = set(_FUERA_DE_MUNDO_BASE)
    for origen in (getattr(vocabulario, "MATICES", ()),
                   *(f.get("matices", ()) for f in fuentes[1:] if isinstance(f, dict))):
        for entrada in origen or ():
            try:
                patron, delta, desc = entrada
                matices.append((tuple(x if ("*" in x or "|" in x or x.startswith("^"))
                                      else quitar_tildes(x) for x in patron),
                                int(delta), str(desc)))
            except (TypeError, ValueError):
                pass
    for origen in (getattr(vocabulario, "FUERA_DE_MUNDO", ()),
                   *(f.get("fuera_de_mundo", ()) for f in fuentes[1:] if isinstance(f, dict))):
        fuera.update(quitar_tildes(str(p)).strip() for p in origen or () if str(p).strip())
    MODIFICADORES = matices
    _FUERA_DE_MUNDO = fuera

    prefijos = {}                       # (raiz, clase) -> peso
    exactas = {}                        # (palabra, clase) -> peso
    frases = list(_FRASES_BASE)
    vocab = set()

    def poner_prefijo(raiz, clase, peso):
        if len(raiz) >= 3:
            k = (raiz, clase)
            prefijos[k] = max(prefijos.get(k, 0.0), peso)

    def poner_exacta(palabra, clase, peso):
        if palabra:
            k = (palabra, clase)
            exactas[k] = max(exactas.get(k, 0.0), peso)

    prefijos_base = set()
    for clase, txt in LEXICO_TEXTO.items():
        pref, exac = _leer(txt)
        for r, pw in pref.items():
            poner_prefijo(r, clase, pw)
            prefijos_base.add(r)
        for w_, pw in exac.items():
            poner_exacta(w_, clase, pw)

    for fuente in fuentes:
        for clase, datos in (fuente or {}).items():
            if clase not in CLASES or not isinstance(datos, dict):
                continue
            for spec in datos.get("verbos", ()):
                pref, exac, pw = raices_de_verbo(spec)
                for r in pref:
                    poner_prefijo(r, clase, pw)
                for e in exac:
                    poner_exacta(e, clase, pw)
                vocab.update(e for e in exac if len(e) >= 5)
            for item in datos.get("raices", ()):
                r, pw = _partir_peso(quitar_tildes(item).strip())
                if len(r) >= 4 and " " not in r:      # menos de 4 letras: demasiado ambiguo
                    poner_prefijo(r, clase, pw)
            for item in datos.get("exactas", ()):
                e, pw = _partir_peso(quitar_tildes(item).strip())
                if e and " " not in e:
                    poner_exacta(e, clase, pw)
            for entrada in datos.get("frases", ()):
                try:
                    patron, peso = entrada
                    patron = tuple(x if ("*" in x or "|" in x or x == "@hacer")
                                   else quitar_tildes(x) for x in patron)
                    frases.append((patron, {clase: float(peso)}))
                except (TypeError, ValueError):
                    pass

    for r in prefijos_base:                      # solo el léxico base: son raíces verbales
        if len(r) >= 4:
            vocab.update({r + "ar", r + "o", r + "a", r + "ando"})
    _BASE = {"prefijos": prefijos, "exactas": exactas, "frases": frases, "vocab": vocab}
    _indexar()


_BASE = {"prefijos": {}, "exactas": {}, "frases": [], "vocab": set()}


def _indexar() -> None:
    """Índices de búsqueda = base ya construida + lo que ha enseñado el jugador.

    Es barato (milisegundos), a diferencia de reconstruir(); por eso aprender una
    palabra no obliga a rehacer el vocabulario entero.
    """
    global _PREFIJOS, _PREF_POR_INICIO, _EXACTAS, FRASES, _VOCABULARIO, _VOCAB_POR_INICIO
    prefijos = dict(_BASE["prefijos"])
    vocab = set(_BASE["vocab"])
    for clase, datos in _PERSONAL.items():
        for raiz in datos.get("raices", ()):
            raiz = quitar_tildes(str(raiz)).strip()
            if len(raiz) >= 4 and " " not in raiz:
                k = (raiz, clase)
                prefijos[k] = max(prefijos.get(k, 0.0), 1.0)
    _PREFIJOS = sorted(((r, c, pw) for (r, c), pw in prefijos.items()),
                       key=lambda t: -len(t[0]))
    _PREF_POR_INICIO = {}
    for r, c, pw in _PREFIJOS:
        _PREF_POR_INICIO.setdefault(r[:3], []).append((r, c, pw))
    _EXACTAS = {}
    for (w_, c), pw in _BASE["exactas"].items():
        _EXACTAS.setdefault(w_, []).append((c, pw))
    FRASES = _expandir_frases(_BASE["frases"])
    vocab.update(w_ for w_ in _EXACTAS if len(w_) >= 5)
    _VOCABULARIO = sorted(w_ for w_ in vocab if len(w_) >= 5)
    _VOCAB_POR_INICIO = {}
    for w_ in _VOCABULARIO:
        _VOCAB_POR_INICIO.setdefault(w_[:2], []).append(w_)
reconstruir()


# --------------------------------------------------------------------------
# Entidades: personajes, lugares y objetos del mundo actual
# --------------------------------------------------------------------------
PALABRAS_ENTIDAD = {
    "mentor": "mentor maestro maestra guia tutor",
    "aliado": "aliado aliada companero companera amigo amiga acompanante colega",
    "heraldo": "heraldo mensajero",
    "villano": "villano villana malvado malvada antagonista jefe enemigo enemiga archienemigo",
    "hogar": "casa hogar aldea pueblo villa ciudad barrio distrito colonia estacion habitat caserio",
    "umbral": "umbral puerta puente paso esclusa compuerta verja porton control vestibulo",
    "camino": "camino bosque paramos marismas cinturon rutas nebulosa callejones calles carretera pantanos senda sendero",
    "guarida": "guarida fortaleza torre nave base reactor mansion atico abadia sotano cripta ciudadela castillo",
    "guardian": "guardian portero centinela vigilante cancerbero dron androide recepcionista enterrador",
    "esbirros": "esbirros secuaces enemigos soldados matones lobos drones poseidos sombras muertos jinetes huargos mercenarios cazarrecompensas policias",
    "meta": "tesoro reliquia objetivo artefacto",
    "don": "don regalo amuleto daga farol crucifijo escudo implante modulo capa placa llave tarjeta frasco",
    "herramienta": "arma espada arco baston pistola revolver hacha escopeta libreta multiherramienta",
}
PERSONAJES = ("mentor", "aliado", "heraldo", "villano")
LUGARES = ("hogar", "umbral", "camino", "guarida")


def _raiz(token: str) -> str:
    return token


def _variantes_numero(token: str):
    if token.endswith("s") and len(token) > 4:
        return [token, token[:-1]]
    return [token, token + "s"]


_DETERMINANTES = {"el", "la", "los", "las", "un", "una", "unos", "unas", "tu", "tus",
                  "su", "sus", "mi", "mis", "del", "al"}
_PREPOSICIONES = {"de", "del", "en", "con", "sin", "bajo", "junto", "sobre"}
_ADJETIVOS_PREVIOS = {"viejo", "vieja", "anciano", "anciana", "joven", "gran", "buen",
                      "buena", "antiguo", "antigua"}
# Palabras de un nombre que pasarían por identificarlo y que son demasiado comunes.
_GENERICAS_DE_NOMBRE = {"inteligencia", "senora", "corporacion", "mil", "nueva", "nuevo"}
# Sustantivos que también son formas verbales («camino», «paso»...): solo cuentan
# como entidad si van precedidos de un determinante o una preposición.
_AMBIGUAS_VERBO = {"camino", "paso", "control", "base", "casa"}
_ANTES_DE_SUSTANTIVO = {"el", "la", "los", "las", "un", "una", "al", "del", "mi", "tu",
                        "su", "este", "esta", "ese", "esa", "aquel", "aquella", "por",
                        "hacia", "en", "de", "a", "para", "desde", "hasta", "tras"}


def _nucleo(texto: str, complemento: bool = False, titulo: bool = False):
    """Lo que de verdad identifica a algo dentro de su descripción.

    «un troll de ojos vacíos» -> troll; «el Puente de Alderrón» -> Puente, Alderrón.
    El resto (ojos, vacíos, piedra...) describe, no nombra, y como alias daría
    falsos positivos: «con los ojos cerrados» no se refiere al guardián.
    Con `complemento` entra también el primer sustantivo tras «de» («la verja del
    cementerio» -> verja, cementerio); con `titulo` se saltan los adjetivos
    previos («el viejo caballero» -> caballero).
    """
    tokens = _TOKEN.findall(texto)
    nucleo, cabeza, tras_de = [], False, False
    for i, t in enumerate(tokens):
        bajo = t.lower()
        if bajo in _DETERMINANTES:
            continue
        if bajo in _PREPOSICIONES:
            tras_de = complemento and cabeza
            continue
        if t[:1].isupper() and (i > 0 or not cabeza):
            nucleo.append(t)
            cabeza = True
            tras_de = False
            continue
        if not cabeza:
            if titulo and bajo in _ADJETIVOS_PREVIOS:
                continue
            nucleo.append(t)
            cabeza = True
        elif tras_de:
            nucleo.append(t)
            tras_de = False
    return nucleo


def _alias(w) -> dict:
    """token normalizado -> conjunto de entidades que lo usan."""
    estaticos = {}
    for ent, palabras in PALABRAS_ENTIDAD.items():
        for p in palabras.split():
            if len(p) >= 3 and p not in _RELLENO:
                estaticos.setdefault(p, set()).add(ent)

    # Lo propio de ESTE mundo: el sustantivo principal y los nombres propios.
    propios = {}                                  # token -> entidades de este mundo

    def poner(token, ent):
        if len(token) >= 3 and token not in _RELLENO and token not in _GENERICAS_DE_NOMBRE:
            propios.setdefault(token, set()).add(ent)

    for rol in PERSONAJES:
        p = w.reparto[rol]
        for t in _nucleo(p.titulo, titulo=True) + _nucleo(p.nombre, titulo=True):
            poner(normalizar_token(t), rol)
    for ent in LUGARES:
        for t in _nucleo(str(w.lugares[ent]), complemento=True):
            poner(normalizar_token(t), ent)
    for ent in ("meta", "don", "herramienta", "guardian", "esbirros"):
        for t in _nucleo(str(w.objetos[ent])):
            poner(normalizar_token(t), ent)

    alias = {t: set(e) for t, e in estaticos.items()}
    for token, ents in propios.items():
        if len(ents) == 1:
            alias[token] = set(ents)              # lo de este mundo manda sobre lo genérico
        elif token not in estaticos:
            alias.pop(token, None)                # ambiguo dentro del mundo: no identifica
        else:
            alias[token] = estaticos[token] & ents or estaticos[token]
    # singular/plural de lo derivado de nombres, sin pisar palabras ya asignadas
    for token, ents in propios.items():
        if len(ents) != 1:
            continue
        for v in _variantes_numero(token):
            if v not in alias:
                alias[v] = set(ents)
    return alias


# --------------------------------------------------------------------------
# Resultado del análisis
# --------------------------------------------------------------------------
@dataclass
class Interpretacion:
    frase: str
    clase: str = "desconocida"
    puntos: dict = field(default_factory=dict)
    entidades: list = field(default_factory=list)
    dd: int = 0                                  # ajuste de dificultad
    mods: list = field(default_factory=list)     # fragmentos escritos por el jugador
    mods_desc: list = field(default_factory=list)
    opcion: object = None                        # índice entre las opciones visibles
    puntaje_opcion: float = 0.0
    bloqueo: object = None                       # texto si la acción es imposible
    top: float = 0.0                             # puntuación de la intención ganadora
    margen: float = 0.0                          # ventaja sobre la segunda

    @property
    def insegura(self) -> bool:
        """¿Conviene preguntar al jugador qué quiso decir?"""
        return self.clase == "desconocida" or self.top < UMBRAL_CONFIANZA

    def a_registro(self) -> dict:
        return {"txt": self.frase, "clase": self.clase, "ent": list(self.entidades),
                "dd": self.dd, "mods": list(self.mods)}

    @property
    def es_exploracion(self) -> bool:
        return self.clase in CLASES_EXPLORACION


def _item_ok(item: str, cands) -> bool:
    """Una raíz de patrón: `abc*` prefijo; 4+ letras prefijo; 3 o menos exacta."""
    if "|" in item:
        return any(_item_ok(alt, cands) for alt in item.split("|"))
    if item.endswith("*"):
        pref = item[:-1]
        return any(c.startswith(pref) for c in cands)
    if len(item) >= 4:
        return any(c.startswith(item) for c in cands)
    return item in cands


def _precomputar(norm):
    """Variantes de cada palabra y conjuntos para descartar patrones imposibles."""
    cands = [_candidatas(t) for t in norm]
    planas = {c for cs in cands for c in cs}
    prefijos = {c[:k] for c in planas for k in range(1, len(c) + 1)}
    return cands, planas, prefijos


def _posible(item: str, planas, prefijos) -> bool:
    """¿Podría esta raíz casar con alguna palabra de la frase? (filtro barato)"""
    item = item.lstrip("^")
    if "|" in item:
        return any(_posible(a, planas, prefijos) for a in item.split("|"))
    if item.endswith("*"):
        return item[:-1] in prefijos
    if len(item) >= 4:
        return item in prefijos
    return item in planas


def _ventana(norm, patron, pre=None):
    """Índices donde aparecen todas las raíces del patrón en una ventana corta."""
    cands, planas, prefijos = pre if pre is not None else _precomputar(norm)
    if not all(_posible(item, planas, prefijos) for item in patron):
        return None
    ancho = len(patron) + 3
    for ini in range(len(norm)):
        ids, usados = [], set()
        for item in patron:
            hallado = None
            pegado = item.startswith("^")           # «^x»: justo detrás de la anterior
            if pegado:
                item = item[1:]
            for j in range(ini, min(len(norm), ini + ancho)):
                if pegado and ids and j != ids[-1] + 1:
                    continue
                if j not in usados and _item_ok(item, cands[j]):
                    hallado = j
                    break
            if hallado is None:
                break
            usados.add(hallado)
            ids.append(hallado)
        else:
            return ids
    return None


def _fragmento(orig, ids):
    """Texto original que cubre los tokens `ids`, con su preposición delante."""
    ini, fin = min(ids), max(ids)
    previas = {"con", "los", "las", "el", "la", "a", "de", "sin", "en", "muy", "bien", "tan"}
    quitar = 0
    while ini > 0 and quitar < 2 and normalizar_token(orig[ini - 1]) in previas:
        ini -= 1
        quitar += 1
    return " ".join(orig[ini:fin + 1])


def _mult_pos(i: int) -> float:
    return max(0.6, 1.0 - 0.04 * i)


_DETERMINANTES = {"el", "la", "los", "las", "un", "una", "unos", "unas", "del", "al",
                  "su", "sus", "tu", "tus", "mi", "mis", "este", "esta", "ese", "esa"}
# Palabras que, tras un determinante, son sustantivo y no verbo ("el camino").
_NOMBRES_AMBIGUOS = {"camino", "paso", "carga", "cargo", "marcha", "vuelta", "sueno",
                     "corte", "mira", "rastro", "lleg", "salto"}
# Verbos auxiliares: seguidos de un infinitivo («voy a esconderme», «pienso
# rendirme», «vuelvo a intentarlo») no llevan la intención; la lleva el infinitivo.
# forma -> True si el infinitivo va tras «a»/«de» (False: va directo).
_AUXILIARES = {}
for _formas, _enlace in (
        ("voy vas va vamos van iba ibas ibamos iban ire iras ira iremos iran vaya vayas "
         "vayamos vayan", "a"),
        ("vuelvo vuelves vuelve volvemos vuelven volvi volvio volvieron volvia volvere "
         "volvera", "a"),
        ("empiezo empiezas empieza empezamos empiezan empece empezo comienzo comienza "
         "comenzamos comienzan comence comenzo", "a"),
        ("trato trata tratamos tratan trate", "de"),
        ("acabo acaba acabamos acaban", "de"),
        ("quiero quieres quiere queremos quieren queria queriamos", ""),
        ("pienso piensa pensamos piensan pensaba pensabamos", ""),
        ("puedo puedes puede podemos pueden podia podria podriamos", ""),
        ("debo debes debe debemos deben debia", ""),
        ("decido decide decidimos deciden decidi decidio", ""),
        ("intento intenta intentamos intentan intente intento", ""),
        ("procuro procura procuramos", ""),
        ("necesito necesita necesitamos necesitan", ""),
        ("prefiero prefiere preferimos prefieren", ""),
        ("pretendo pretende pretendemos", ""),
        ("suelo sueles suele solemos suelen", ""),
        ("logro logra logramos", ""),
        ("sigo sigues sigue seguimos", "")):
    for _f in _formas.split():
        _AUXILIARES.setdefault(_f, _enlace)
# Negaciones enfáticas: «ni de broma me escondo» = nunca me escondería.
_NEGACIONES_ENFATICAS = [("ni", "de", "broma"), ("ni", "de", "chiste"), ("ni", "por", "asomo"),
                         ("ni", "loco"), ("ni", "muerto"), ("ni", "en", "suenos"),
                         ("jamas", "de", "los", "jamases"), ("ni", "de", "coña")]
_BOTIN = {"todo", "botin", "oro", "dinero", "monedas", "recompensa", "tesoro",
          "joya", "joyas", "cofre", "pasta", "premio", "parte", "ganancias"}
_APROVECHADOS = {"senuelo", "cebo", "escudo", "carnada", "sacrificio"}
_COMO_USO = {"de", "como", "para"}       # «de escudo», «como cebo»: se usa a alguien
COMPANEROS = ("aliado", "mentor", "heraldo")
# Lo que viene después de estas marcas manda ("miro y LUEGO ataco"). Lo que sigue
# a «para» NO se rebaja: casi siempre nombra la intención ("suelto los caballos
# para distraer"); se comprobó con los corpus.
_SECUENCIA = {"luego", "despues", "entonces", "finalmente", "seguidamente"}


def _pesos_de_clausula(norm) -> list:
    """Multiplicador por palabra: tras «luego/después» manda lo que sigue."""
    m = [1.0] * len(norm)
    seq = next((i for i, t in enumerate(norm) if t in _SECUENCIA), None)
    if seq is not None:
        for j in range(len(norm)):
            m[j] *= 0.8 if j < seq else (1.5 if j > seq else 1.0)
    return m


def _es_infinitivo(tok: str) -> bool:
    """«esconderme», «ayudarlo», «atacar»: infinitivos, con o sin pronombre pegado."""
    return any(len(c) > 3 and c.endswith(("ar", "er", "ir"))
               for c in _candidatas(tok))


def _es_auxiliar(norm, i: int) -> bool:
    """¿Es norm[i] un auxiliar de un infinitivo que viene justo detrás?"""
    enlace = _AUXILIARES.get(norm[i])
    if enlace is None:
        return False
    j = i + 1
    if enlace:
        if norm[j:j + 1] != [enlace]:
            return False
        j += 1
    return j < len(norm) and _es_infinitivo(norm[j])


def analizar(texto: str, w, esc=None, etiquetas=None, visibles=None,
             forzar=None) -> Interpretacion:
    """Interpreta `texto` en el contexto del mundo `w` y de la escena `esc`.

    `forzar` es una intención elegida por el propio jugador (menú de ayuda):
    manda sobre lo que deduzca el intérprete.
    """
    texto = " ".join(texto.split())[:MAX_CARACTERES]
    orig, norm = tokenizar(texto)
    r = Interpretacion(frase=texto)
    puntos = {c: 0.0 for c in CLASES}
    alias = _alias(w)
    pre = _precomputar(norm)

    # 1) Modificadores de dificultad. Sus palabras ("con calma", "sin mirar") no
    #    cuentan después como intención.
    enmascarados = set()
    for patron, delta, desc in MODIFICADORES:
        ids = _ventana(norm, patron, pre)
        if ids is not None and desc not in r.mods_desc:
            r.dd += delta
            r.mods_desc.append(desc)
            r.mods.append(_fragmento(orig, ids))
            enmascarados.update(ids)
    r.dd = max(-2, min(3, r.dd))

    # 2) Palabras sueltas, con negaciones y desambiguaciones sencillas.
    clausula = _pesos_de_clausula(norm)
    saltar = set()                                     # palabras de una negación enfática
    neg_hasta = -1                                     # la negación vigente alcanza hasta aquí
    neg_enfatica = False                               # la negación vigente es «ni de broma...»
    enfatica_invierte = False                          # y ya ha invertido un verbo
    for i, tok in enumerate(norm):
        if i in enmascarados or tok in _IGNORADAS or i in saltar:
            continue
        if tok in NEGADORES:
            # «sin armas» ya es un modificador: no niega al verbo que viene después.
            neg_hasta = i + 2
            for enf in _NEGACIONES_ENFATICAS:
                if tuple(norm[i:i + len(enf)]) == enf:
                    saltar.update(range(i, i + len(enf)))
                    neg_hasta = i + len(enf) + 3
                    neg_enfatica = True
                    break
            else:
                neg_enfatica = False
            continue
        if tok in _RELLENO and tok not in _EXACTAS:
            continue
        previo = norm[i - 1] if i else ""
        if tok in _NOMBRES_AMBIGUOS and previo in _DETERMINANTES:
            continue                                   # "el camino": sustantivo
        if _es_auxiliar(norm, i):
            if neg_hasta >= i:                         # «no voy a huir»: la negación
                neg_hasta += 2 if _AUXILIARES[tok] else 1   # llega hasta el infinitivo
            continue                                   # "voy a dormir", "pienso rendirme"
        if tok.startswith("sacrific") and (tok.endswith("me") or previo == "me"):
            puntos["compasion"] += 1.5                 # sacrificarse por otros no es ambición
            continue
        if tok.startswith("qued") and i + 1 < len(norm) and \
                norm[i + 1].endswith(("ando", "iendo")):
            continue                                   # "me quedo mirando"
        m = coincidencias(tok)
        if not m and tok not in alias:
            corregido = _corregir(tok)
            if corregido:
                m = coincidencias(corregido)
        if not m:
            continue
        negada = i <= neg_hasta
        if negada:
            neg_hasta = -1                             # la negación afecta a un solo verbo
        for clase, peso in m.items():
            if negada:
                inv = NEGACION_INVERSA.get(clase)
                if inv:
                    puntos[inv[0]] += inv[1] * _mult_pos(i)
                    enfatica_invierte = enfatica_invierte or neg_enfatica
                continue
            puntos[clase] += peso * _mult_pos(i) * clausula[i]

    # 3) Frases hechas (no cuentan si las precede una negación, salvo que la lleven).
    se_sacrifica = any(t.startswith("sacrific") and (t.endswith("me") or (k and norm[k - 1] == "me"))
                       for k, t in enumerate(norm))
    for patron, pesos in FRASES:
        if se_sacrifica and patron[0] == "sacrific*":
            continue                       # «me sacrifico por X»: no se sacrifica a X
        if enfatica_invierte and patron[0] == "ni":
            continue                       # «ni de broma me escondo»: ya se negó el verbo
        ids = _ventana(norm, patron, pre)
        if ids is None:
            continue
        lleva_negador = any(x in NEGADORES for x in patron)
        if not lleva_negador and min(ids) > 0 and norm[min(ids) - 1] in NEGADORES:
            continue
        for clase, peso in pesos.items():
            puntos[clase] += peso

    # 4) Entidades nombradas.
    vistas = []
    for i, tok in enumerate(norm):
        if i in enmascarados:
            continue                       # «con los ojos cerrados», «paso a paso»...
        if tok in _AMBIGUAS_VERBO and (i == 0 or norm[i - 1] not in _ANTES_DE_SUSTANTIVO):
            continue                       # «camino por el bosque» es un verbo
        if tok == "camino" and i > 0 and norm[i - 1] in ("mi", "tu", "su", "nuestro"):
            continue                       # «seguir mi camino» es figurado
        for ent in sorted(alias.get(tok, ())):
            if ent not in vistas:
                vistas.append(ent)
    r.entidades = vistas

    # 5) Reglas que combinan intención y entidad.
    quedarse = _ventana(norm, ("qued*",), pre) is not None
    if quedarse and (_BOTIN & set(norm) or "meta" in vistas or "don" in vistas):
        puntos["sombra"] += 2.0                  # quedarse con el botín: ambición
        puntos["duda"] = 0.0
    de_escudo = any(t in _APROVECHADOS and k > 0 and norm[k - 1] in _COMO_USO
                    for k, t in enumerate(norm))
    sacrifica_a_otro = any(
        t.startswith("sacrific") and not t.endswith("me")
        and not (k > 0 and norm[k - 1] == "me") for k, t in enumerate(norm))
    if any(c in vistas for c in COMPANEROS) and (de_escudo or sacrifica_a_otro):
        puntos["sombra"] += 2.0                  # usar a un compañero de escudo o cebo
        puntos["ingenio"] = max(0.0, puntos["ingenio"] - 1.0)
        puntos["compasion"] = max(0.0, puntos["compasion"] - 2.0)
    if _FUERA_DE_MUNDO & set(norm) and not any(e in vistas for e in
                                                PERSONAJES + ("hogar", "guardian", "esbirros")):
        puntos = {c: 0.0 for c in CLASES}

    # 5b) Lo que el jugador ya enseñó o acaba de elegir.
    personal = _FRASES_PERSONALES.get(" ".join(norm))
    if personal in CLASES:
        puntos[personal] += 3.0
    if forzar in CLASES:
        puntos[forzar] += 3.0

    # 6) Intención dominante.
    r.puntos = {c: round(v, 3) for c, v in puntos.items() if v > 0}
    if r.puntos:
        r.clase = max(r.puntos, key=lambda c: (r.puntos[c], -_ORDEN[c]))
        if r.puntos[r.clase] < 0.5:
            r.clase = "desconocida"
        valores = sorted(r.puntos.values(), reverse=True)
        r.top = valores[0]
        r.margen = valores[0] - (valores[1] if len(valores) > 1 else 0.0)

    # 7) Encaje con las opciones de la escena.
    if esc is not None and visibles is not None and etiquetas is not None:
        _elegir_opcion(r, norm, visibles, etiquetas, w)

    # 8) Coherencia con el estado del mundo.
    r.bloqueo = bloqueo(r, w, esc)
    return r


def _contenido(tokens):
    return {t[:5] for t in tokens if len(t) >= 4 and t not in _RELLENO}


def _nombres_propios(w) -> set:
    """Prefijos de 5 letras de los nombres de pila de los personajes de este mundo."""
    nombres = set()
    for rol in PERSONAJES:
        for t in _TOKEN.findall(w.reparto[rol].nombre):
            if t[:1].isupper():
                nombres.add(normalizar_token(t)[:5])
    return nombres


def _elegir_opcion(r: Interpretacion, norm, visibles, etiquetas, w) -> None:
    """Busca la opción de la escena que mejor encaja con la frase."""
    if r.clase == "desconocida":
        return
    vec = {c: r.puntos.get(c, 0.0) for c in CLASES_ACCION}
    for expl in CLASES_EXPLORACION:
        for c, a in AFINIDAD.get(expl, {}).items():
            vec[c] += a * r.puntos.get(expl, 0.0)
    cima = max(vec.values()) if vec else 0.0
    texto_tokens = _contenido(norm)
    nombres = _nombres_propios(w)
    mejor, mejor_p = None, 0.0
    for i, op in enumerate(visibles):
        clase_op = next((c for c, e in ENFOQUE_DE.items() if e == op.enfoque), None)
        if op.enfoque is None and op.tag:
            clase_op = None      # confianza o gratitud: no es una evasiva
        s_int = (vec.get(clase_op, 0.0) / cima) if cima > 0 and clase_op else 0.0
        _, etiqueta = etiquetas[i]
        comunes = texto_tokens & _contenido(tokenizar(etiqueta)[1])
        solape = len(comunes)
        if r.es_exploracion and solape == 0:
            continue             # mirar, hablar, ir... solo decide si nombra la opción
        if r.es_exploracion:
            puntaje = s_int + 0.8 * min(solape, 3)
        else:
            # Coincidir solo en el nombre de un personaje no basta: «ayudar a Ignacio»
            # no debe elegir «quedarte con lo que Ignacio deje caer».
            solo_nombres = len(comunes & nombres)
            puntaje = (s_int + 0.8 * min(solape - solo_nombres, 3)
                       + 0.3 * min(solo_nombres, 1))
        if puntaje > mejor_p:
            mejor, mejor_p = i, puntaje
    if mejor is not None and mejor_p >= 0.8:
        r.opcion, r.puntaje_opcion = mejor, round(mejor_p, 2)


# --------------------------------------------------------------------------
# Coherencia: ¿se puede hacer esto ahora, en esta historia?
# --------------------------------------------------------------------------
def presente(w, esc, rol: str) -> bool:
    """¿Está el personaje (u objeto) a mano en la escena actual?"""
    if rol == "guardian":
        return esc is not None and ("guardian" in esc.presentes
                                    or (esc.id == "camino_de_vuelta"
                                        and w.b("guardian_amigo")))
    if rol == "villano":                   # solo está donde la escena lo pone
        return esc is not None and ("villano" in esc.presentes
                                    or "villano" in esc.participan)
    if rol in PERSONAJES:
        return w.disponible(rol) or (esc is not None and rol in esc.presentes)
    return True


def _lugar_alcanzable(w, ent: str) -> bool:
    e = w.etapa
    if ent == "hogar":
        return e <= 3 or e >= 11
    if ent == "umbral":
        return 4 <= e <= 10
    if ent == "camino":
        return e >= 5
    if ent == "guarida":
        return e >= 7
    return True


def bloqueo(r: Interpretacion, w, esc):
    """Devuelve un texto si la acción es imposible ahora, o None."""
    # Al hablar, quien no está solo es el tema de la charla si hay con quién hablar.
    hay_interlocutor = r.clase == "hablar" and any(
        rol in PERSONAJES and presente(w, esc, rol) for rol in r.entidades)
    contra_enemigos = any(e in r.entidades for e in ("esbirros", "guardian", "villano"))
    for rol in r.entidades:
        if rol not in PERSONAJES:
            continue
        p = w.reparto[rol]
        if r.clase in ("observar", "desconocida"):
            continue                       # pensar o recordar a alguien siempre se puede
        if r.clase in ("valor", "sombra") and rol in ("mentor", "aliado", "heraldo"):
            if presente(w, esc, rol) and not contra_enemigos:
                return (f"Eso afectaría a {p.nombre}, y una decisión así pesa "
                        f"demasiado para tomarla a la ligera. Cuando llegue el "
                        f"momento, tendrás que elegir de verdad.")
        if hay_interlocutor:
            continue
        if not presente(w, esc, rol):
            if not p.vivo:
                return f"{p.nombre} ya no está para eso: murió, y lo sabes."
            if rol == "villano":
                return (f"{w.reparto['villano'].Cap} está lejos de aquí. Ahora tu "
                        f"enemigo es lo que tienes delante.")
            return f"{p.nombre} no está aquí en este momento."
    if "guardian" in r.entidades and r.clase not in ("observar", "desconocida"):
        if not presente(w, esc, "guardian"):
            return "Aquí no hay ningún guardián con quien tratar."
    if r.clase == "moverse":
        for ent in r.entidades:
            if ent in LUGARES and not _lugar_alcanzable(w, ent):
                return (f"Todavía no puedes ir {w.lugares[ent].a}: "
                        f"el camino hasta allí aún no ha llegado.")
    return None
