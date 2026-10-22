"""Lee la premisa que el jugador escribe al crear su mundo (sin inteligencia artificial).

El jugador puede contar su mundo con palabras propias: «una ciudad de canales con
magia vieja y detectives cansados; el pueblo se llama Aguasmuertas y el villano
Zarkon». Un narrador de reglas no entiende el significado, pero sí puede sacar
tres cosas concretas, que luego se enseñan al jugador para que las confirme:

  * géneros que mezclar (por palabras: «magia», «nave», «detective», «fantasma»);
  * un tono, si lo deja claro («sombrío», «luminoso»);
  * nombres propios para el pueblo, el villano, el mentor... («se llama X»).

Todo lo demás se conserva como premisa y aparece en el libro, pero no cambia las
escenas: es mejor decirlo así que fingir que se ha entendido.
"""

import re
import unicodedata

# Palabras (o prefijos, si terminan en «*») que delatan un género. Sin tildes.
PALABRAS_GENERO = {
    "fantasia": (
        "magia magico magica mago maga hechizo hechizos hechicero hechicera brujo bruja "
        "dragon dragones elfo elfa elfos enano enanos orco orcos troll trolls reino reinos "
        "rey reina castillo castillos espada espadas caballero caballeros medieval hada "
        "hadas ogro grimorio varita varitas bardo paladin elfica gnomo gnomos nigromante "
        "profecia profecias"),
    "ciencia_ficcion": (
        "nave naves espacio espacial estelar planeta planetas galaxia galaxias robot robots "
        "androide androides laser alien aliens extraterrestre extraterrestres cyber* ciber* "
        "futurista futuro hacker hackers colonia colonias asteroide asteroides orbital "
        "cosmos clon clones implante implantes neon holograma hologramas astronauta "
        "inteligencia_artificial teletransporte pulsos"),
    "noir": (
        "detective detectives crimen crimenes asesino asesinato asesinatos lluvia mafia "
        "policia policias comisario comisaria corrupto corrupta corrupcion gangster gangsters "
        "sospechoso sospechosos chantaje periodista callejon callejones sindicato puerto "
        "casino cigarrillo cigarro whisky femme_fatale"),
    "terror": (
        "fantasma fantasmas vampiro vampiros maldicion maldiciones maldito maldita cementerio "
        "cementerios niebla poseido poseida exorcismo exorcista demonio demonios embrujado "
        "embrujada gotico gotica zombi zombis cadaver cadaveres sepulcro sepulcros aquelarre "
        "pesadilla pesadillas ritual rituales espectro espectros hombre_lobo licantropo"),
}

TONOS_PALABRAS = {
    "sombrio": ("oscuro oscura oscuros sombrio sombria crudo cruda cruel brutal desesperanza "
                "desesperanzado tragico tragica sangre miseria desolado desolada implacable "
                "opresivo opresiva"),
    "luminoso": ("esperanza esperanzador luminoso luminosa alegre calido calida optimista "
                 "comedia humor ligero ligera tierno tierna amable"),
}

# Palabras que anuncian a qué se refiere un nombre propio.
ROLES = {
    "hogar": ("pueblo aldea ciudad villa barrio caserio estacion colonia habitat distrito "
              "puerto capital"),
    "mentor": "mentor maestro maestra sabio sabia anciano anciana viejo vieja guia",
    "villano": ("villano villana enemigo enemiga malvado malvada antagonista tirano tirana "
                "jefe nemesis"),
    "aliado": "aliado aliada companero companera amigo amiga acompanante",
    "heraldo": "heraldo mensajero mensajera emisario emisaria",
}
_FEMENINOS_HOGAR = {"aldea", "ciudad", "villa", "estacion", "colonia", "capital"}

_NOMBRE = (r"([A-ZÁÉÍÓÚÑ][\wáéíóúüñ'’-]*(?:\s+(?:de|del|la|las|los|el)?\s*"
           r"[A-ZÁÉÍÓÚÑ][\wáéíóúüñ'’-]*){0,2})")
_LLAMADO = re.compile(
    r"\b(?:llamad[oa]s?|se\s+llama[n]?|de\s+nombre|apodad[oa]s?|conocid[oa]s?\s+como)\s+"
    r"(?:(?:el|la|los|las)\s+)?" + _NOMBRE)
_SEPARADOR = re.compile(r"[.;]")


def quitar_tildes(texto: str) -> str:
    n = unicodedata.normalize("NFD", texto)
    return "".join(c for c in n if not unicodedata.combining(c))


def _tokens(texto: str):
    return re.findall(r"[a-zñ]+", quitar_tildes(texto.lower()))


def _casa(token: str, patron: str) -> bool:
    if patron.endswith("*"):
        return token.startswith(patron[:-1])
    return token == patron or token == patron + "s" or token == patron + "es"


def generos_en(texto: str) -> list:
    """Géneros que aparecen en el texto, del más al menos mencionado."""
    toks = _tokens(texto)
    cuentas = {}
    for genero, palabras in PALABRAS_GENERO.items():
        patrones = [p for p in palabras.split() if "_" not in p]
        n = sum(1 for t in toks for p in patrones if _casa(t, p))
        compuestas = [p.replace("_", " ") for p in palabras.split() if "_" in p]
        plano = " ".join(toks)
        n += sum(1 for c in compuestas if c in plano)
        if n:
            cuentas[genero] = n
    return sorted(cuentas, key=lambda g: -cuentas[g])


def tono_en(texto: str):
    """«sombrio» o «luminoso» si el texto se inclina claramente por uno."""
    toks = _tokens(texto)
    puntos = {t: sum(1 for x in toks for p in pal.split() if x == p)
              for t, pal in TONOS_PALABRAS.items()}
    mejor = max(puntos, key=puntos.get)
    if puntos[mejor] and sorted(puntos.values())[-1] > sorted(puntos.values())[0]:
        return mejor
    return None


def _rol_de(texto_previo: str):
    """El rol al que se refiere un nombre, según las palabras justo antes de él."""
    toks = _tokens(texto_previo)[-6:]
    for t in reversed(toks):
        for rol, palabras in ROLES.items():
            if t in palabras.split():
                return rol, t
    return None, None


def nombres_en(texto: str) -> dict:
    """{rol: nombre} para lo que el jugador nombra («el pueblo se llama Aguasmuertas»)."""
    encontrados = {}
    for m in _LLAMADO.finditer(texto):
        previo = texto[max(0, m.start() - 60):m.start()]
        previo = _SEPARADOR.split(previo)[-1]       # solo la oración en curso
        rol, palabra = _rol_de(previo)
        if rol is None or rol in encontrados:
            continue
        nombre = m.group(1).strip()
        if rol == "hogar":
            art = "la" if palabra in _FEMENINOS_HOGAR else "el"
            nombre = f"{art} {palabra} de {nombre}"
        encontrados[rol] = nombre
    return encontrados


def leer_premisa(texto: str, principal: str = None) -> dict:
    """Todo lo que se puede deducir de la premisa: géneros, tono y nombres."""
    texto = " ".join((texto or "").split())[:600]
    return {
        "mezcla": [g for g in generos_en(texto) if g != principal][:2],
        "tono": tono_en(texto),
        "nombres": nombres_en(texto),
    }


def describir(lectura: dict, nombres_generos: dict, nombres_tonos: dict) -> list:
    """Frases cortas para enseñar al jugador lo que se ha entendido."""
    cosas = []
    if lectura["mezcla"]:
        cosas.append("mezcla con " + " y ".join(nombres_generos[g] for g in lectura["mezcla"]))
    if lectura["tono"]:
        cosas.append("tono " + nombres_tonos[lectura["tono"]].lower())
    et = {"hogar": "el lugar de partida", "mentor": "el mentor", "villano": "el villano",
          "aliado": "el aliado", "heraldo": "el heraldo"}
    for rol, nombre in lectura["nombres"].items():
        cosas.append(f"{et[rol]}: {nombre}")
    return cosas
