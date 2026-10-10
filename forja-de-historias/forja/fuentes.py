"""Catálogo de fuentes: teoría narrativa, literatura, cine y técnica.

Cada escena del juego cita claves de este catálogo. Al final de la partida se
imprime (y se guarda en el libro) la bibliografía de lo que realmente se usó.

Las películas y novelas figuran como INSPIRACIÓN: se cita el patrón narrativo
que la escena recuerda, no se copia texto ni argumento.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuente:
    clave: str
    tipo: str      # teoría | literatura | cine | juego | investigación
    corta: str     # cómo se muestra en una anotación
    cita: str      # referencia completa


def _f(clave, tipo, corta, cita):
    return clave, Fuente(clave, tipo, corta, cita)


FUENTES = dict([
    # --- Teoría narrativa -------------------------------------------------
    _f("propp", "teoría", "Propp (1928)",
       "Vladímir Propp, *Morfología del cuento* (1928)."),
    _f("campbell", "teoría", "Campbell (1949)",
       "Joseph Campbell, *El héroe de las mil caras* (1949)."),
    _f("vogler", "teoría", "Vogler (1992)",
       "Christopher Vogler, *El viaje del escritor* (1992)."),
    _f("booker", "teoría", "Booker (2004)",
       "Christopher Booker, *Las siete tramas básicas* (2004)."),
    _f("aristoteles", "teoría", "Aristóteles",
       "Aristóteles, *Poética* (c. 335 a. C.)."),
    _f("freytag", "teoría", "Freytag (1863)",
       "Gustav Freytag, *La técnica del drama* (1863)."),
    _f("field", "teoría", "Field (1979)",
       "Syd Field, *El libro del guión* (1979)."),
    _f("todorov", "teoría", "Todorov (1969)",
       "Tzvetan Todorov, *Gramática del Decamerón* (1969)."),
    _f("greimas", "teoría", "Greimas (1966)",
       "Algirdas J. Greimas, *Semántica estructural* (1966)."),
    _f("polti", "teoría", "Polti (1895)",
       "Georges Polti, *Las 36 situaciones dramáticas* (1895)."),
    _f("jung", "teoría", "Jung",
       "Carl G. Jung, *Los arquetipos y lo inconsciente colectivo* "
       "(ensayos de 1934-1954)."),
    _f("tolkien_cuentos", "teoría", "Tolkien (1947)",
       "J. R. R. Tolkien, «Sobre los cuentos de hadas» (1947)."),

    # --- Literatura -------------------------------------------------------
    _f("tolkien", "literatura", "Tolkien (1954-55)",
       "J. R. R. Tolkien, *El Señor de los Anillos* (1954-1955)."),
    _f("leguin", "literatura", "Le Guin (1968)",
       "Ursula K. Le Guin, *Un mago de Terramar* (1968)."),
    _f("stevenson", "literatura", "Stevenson (1886)",
       "Robert L. Stevenson, *El extraño caso del doctor Jekyll y "
       "míster Hyde* (1886)."),
    _f("dickens", "literatura", "Dickens (1843)",
       "Charles Dickens, *Canción de Navidad* (1843)."),
    _f("macbeth", "literatura", "Shakespeare (c. 1606)",
       "William Shakespeare, *Macbeth* (c. 1606)."),
    _f("sofocles", "literatura", "Sófocles",
       "Sófocles, *Edipo rey* (c. 429 a. C.)."),
    _f("conrad", "literatura", "Conrad (1899)",
       "Joseph Conrad, *El corazón de las tinieblas* (1899)."),
    _f("lovecraft", "literatura", "Lovecraft (1928)",
       "H. P. Lovecraft, «La llamada de Cthulhu» (1928)."),
    _f("stoker", "literatura", "Stoker (1897)",
       "Bram Stoker, *Drácula* (1897)."),
    _f("jackson_hh", "literatura", "S. Jackson (1959)",
       "Shirley Jackson, *La maldición de Hill House* (1959)."),
    _f("chandler", "literatura", "Chandler (1939)",
       "Raymond Chandler, *El sueño eterno* (1939)."),
    _f("hammett", "literatura", "Hammett (1930)",
       "Dashiell Hammett, *El halcón maltés* (1930)."),
    _f("dick", "literatura", "P. K. Dick (1968)",
       "Philip K. Dick, *¿Sueñan los androides con ovejas eléctricas?* (1968)."),
    _f("herbert", "literatura", "Herbert (1965)",
       "Frank Herbert, *Dune* (1965)."),

    # --- Cine -------------------------------------------------------------
    _f("star_wars", "cine", "«La guerra de las galaxias» (1977)",
       "*La guerra de las galaxias* (Star Wars), dir. George Lucas (1977)."),
    _f("imperio", "cine", "«El Imperio contraataca» (1980)",
       "*El Imperio contraataca*, dir. Irvin Kershner (1980)."),
    _f("retorno_jedi", "cine", "«El retorno del Jedi» (1983)",
       "*El retorno del Jedi*, dir. Richard Marquand (1983)."),
    _f("lotr_film", "cine", "«La Comunidad del Anillo» (2001)",
       "*El Señor de los Anillos: La Comunidad del Anillo*, "
       "dir. Peter Jackson (2001)."),
    _f("siete_samurais", "cine", "«Los siete samuráis» (1954)",
       "*Los siete samuráis*, dir. Akira Kurosawa (1954)."),
    _f("chihiro", "cine", "«El viaje de Chihiro» (2001)",
       "*El viaje de Chihiro*, dir. Hayao Miyazaki (2001)."),
    _f("karate_kid", "cine", "«Karate Kid» (1984)",
       "*Karate Kid*, dir. John G. Avildsen (1984)."),
    _f("mago_oz", "cine", "«El mago de Oz» (1939)",
       "*El mago de Oz*, dir. Victor Fleming (1939)."),
    _f("mad_max", "cine", "«Mad Max: Furia en la carretera» (2015)",
       "*Mad Max: Furia en la carretera*, dir. George Miller (2015)."),
    _f("la_cosa", "cine", "«La cosa» (1982)",
       "*La cosa*, dir. John Carpenter (1982)."),
    _f("alien", "cine", "«Alien, el octavo pasajero» (1979)",
       "*Alien, el octavo pasajero*, dir. Ridley Scott (1979)."),
    _f("blade_runner", "cine", "«Blade Runner» (1982)",
       "*Blade Runner*, dir. Ridley Scott (1982)."),
    _f("chinatown", "cine", "«Chinatown» (1974)",
       "*Chinatown*, dir. Roman Polanski (1974)."),
    _f("halcon_maltes", "cine", "«El halcón maltés» (1941)",
       "*El halcón maltés*, dir. John Huston (1941)."),
    _f("casablanca", "cine", "«Casablanca» (1942)",
       "*Casablanca*, dir. Michael Curtiz (1942)."),
    _f("padrino", "cine", "«El padrino» (1972)",
       "*El padrino*, dir. Francis Ford Coppola (1972)."),
    _f("tiburon", "cine", "«Tiburón» (1975)",
       "*Tiburón*, dir. Steven Spielberg (1975)."),
    _f("resplandor", "cine", "«El resplandor» (1980)",
       "*El resplandor*, dir. Stanley Kubrick (1980)."),

    # --- Formato: librojuegos y ficción interactiva ------------------------
    _f("packard", "juego", "Packard (1979)",
       "Edward Packard, *The Cave of Time* (1979), serie *Choose Your Own "
       "Adventure*."),
    _f("jackson_livingstone", "juego", "Jackson y Livingstone (1982)",
       "Steve Jackson e Ian Livingstone, *The Warlock of Firetop Mountain* "
       "(1982)."),
    _f("crowther_woods", "juego", "Crowther y Woods (1976-77)",
       "William Crowther y Don Woods, *Colossal Cave Adventure* (1976-1977)."),

    # --- Generación narrativa por ordenador sin redes neuronales -----------
    _f("meehan", "investigación", "Meehan (1977)",
       "James R. Meehan, «TALE-SPIN, an interactive program that writes "
       "stories», *IJCAI-77* (1977)."),
    _f("turner", "investigación", "Turner (1994)",
       "Scott R. Turner, *The Creative Process: A Computer Model of "
       "Storytelling and Creativity* (1994)."),
    _f("gervas", "investigación", "Gervás (2013)",
       "Pablo Gervás, «Propp's Morphology of the Folk Tale as a Grammar for "
       "Generation», *Workshop on Computational Models of Narrative* (2013)."),
    _f("riedl_young", "investigación", "Riedl y Young (2010)",
       "Mark O. Riedl y R. Michael Young, «Narrative Planning: Balancing "
       "Plot and Character», *Journal of Artificial Intelligence Research* "
       "39 (2010)."),
])


TITULOS_TIPO = {
    "teoría": "Teoría narrativa",
    "literatura": "Literatura",
    "cine": "Cine",
    "juego": "Librojuegos y ficción interactiva",
    "investigación": "Generación narrativa por ordenador",
}


def agrupar(claves):
    """Agrupa claves de fuentes por tipo, en el orden del catálogo."""
    salida = {}
    for tipo in TITULOS_TIPO:
        grupo = [c for c in FUENTES if FUENTES[c].tipo == tipo and c in claves]
        if grupo:
            salida[TITULOS_TIPO[tipo]] = grupo
    return salida


def nota(clave, detalle):
    """Texto de anotación para una (fuente, detalle)."""
    return f"{FUENTES[clave].corta}: {detalle}"


def a_markdown():
    """Genera el contenido de FUENTES.md a partir del catálogo."""
    lineas = [
        "# Fuentes",
        "",
        "Catálogo de referencias que usa la Forja de Historias. Las escenas citan "
        "estas claves y el juego imprime, al terminar, la bibliografía de lo "
        "que de verdad apareció en tu partida.",
        "",
        "Las obras de ficción se citan como **inspiración**: se señala el patrón "
        "narrativo que una escena recuerda, no se copia texto ni argumento.",
        "",
        "> Las citas dan autor, título y año de la obra original; no incluyen "
        "editorial ni edición. Verifica los datos en tu edición antes de usarlos "
        "en un trabajo académico.",
        "",
    ]
    for tipo, titulo in TITULOS_TIPO.items():
        lineas += [f"## {titulo}", ""]
        lineas += [f"- {f.cita}" for f in FUENTES.values() if f.tipo == tipo]
        lineas.append("")
    return "\n".join(lineas)


if __name__ == "__main__":
    print(a_markdown())
