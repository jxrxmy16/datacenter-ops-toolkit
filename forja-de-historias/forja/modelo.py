"""Modelo del mundo narrativo: personajes, estado, escenas y opciones.

La coherencia del relato descansa en una idea simple (la misma de los
planificadores narrativos clásicos): cada escena exige PRECONDICIONES sobre el
estado del mundo y, al resolverse, aplica EFECTOS sobre él. Quien ha muerto no
puede hablar, quien no fue invitado no acompaña y lo que no se aprendió no se
puede usar.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from typing import Callable, Optional, Union

from .gramatica import Nom
from .lexico import ARQUETIPOS, FALLAS, OBJETIVOS, TONOS

ENFOQUES = ("valor", "ingenio", "compasion", "sombra")
ETIQUETAS = {"valor": "Valor", "ingenio": "Ingenio",
             "compasion": "Compasión", "sombra": "Ambición"}
CRECEN = ("valor", "ingenio", "compasion")   # suben al tener éxito con ellos
TOPE_ATRIBUTO = 4
MAX_VIGOR = 9
VIGOR_INICIAL = 8
# Ajuste global de equilibrio: se suma a la dificultad de cada tirada.
AJUSTE_DIFICULTAD = -1

# Objetos del inventario y los enfoques a los que dan +1.
BONOS_OBJETO = {
    "equipo": ("valor",),
    "mapa": ("ingenio",),
    "recuerdo": ("compasion",),
    "don": ("valor", "ingenio"),
    "legado": ("valor", "ingenio", "compasion"),
}

_SUFIJO = {"m": "o", "f": "a", "n": "e"}
_PRONOMBRE = {"m": "él", "f": "ella", "n": "elle"}
_CLITICO = {"m": "lo", "f": "la", "n": "le"}

Condicion = Callable[["Mundo"], bool]
Efecto = Callable[["Mundo"], None]


# --------------------------------------------------------------------------
# Personajes
# --------------------------------------------------------------------------
@dataclass
class Personaje:
    rol: str                  # heroe | heraldo | mentor | aliado | villano
    nombre: str
    titulo: str = ""
    genero: str = "n"         # m | f | n
    vivo: bool = True
    confianza: int = 0
    traidor: bool = False     # solo tiene sentido para el aliado

    def __str__(self) -> str:
        return f"{self.titulo} {self.nombre}".strip()

    # Concordancia: cansad{x.o}, {x.el}, ver{x.lo}
    @property
    def o(self) -> str:
        return _SUFIJO[self.genero]

    @property
    def el(self) -> str:
        return _PRONOMBRE[self.genero]

    @property
    def El(self) -> str:
        return self.el.capitalize()

    @property
    def lo(self) -> str:
        return _CLITICO[self.genero]

    @property
    def de(self) -> Nom:
        return Nom(str(self)).de

    @property
    def a(self) -> Nom:
        return Nom(str(self)).a

    @property
    def Cap(self) -> Nom:
        return Nom(str(self)).Cap


# --------------------------------------------------------------------------
# Escenas
# --------------------------------------------------------------------------
@dataclass
class P:
    """Párrafo condicional: sólo se muestra si `si(mundo)` es verdadero."""
    texto: str
    si: Optional[Condicion] = None


@dataclass
class Resultado:
    parrafos: list
    efectos: list = field(default_factory=list)


def res(parrafos, *efectos) -> Resultado:
    if isinstance(parrafos, (str, P)):
        parrafos = [parrafos]
    return Resultado(list(parrafos), list(efectos))


@dataclass
class Opcion:
    etiqueta: str
    enfoque: Optional[str]                    # None = una duda, no un enfoque
    ok: Resultado
    mal: Optional[Resultado] = None
    dif: Union[int, Callable[["Mundo"], int], None] = None   # None = sin tirada
    amenaza: bool = False                     # la amenaza endurece la tirada
    visible: Optional[Condicion] = None
    tag: Optional[str] = None

    def rotulo(self) -> str:
        if self.tag:
            return self.tag
        return ETIQUETAS[self.enfoque] if self.enfoque else "Duda"


@dataclass
class Escena:
    id: str
    etapa: int
    texto: list
    opciones: list
    participan: tuple = ()     # roles que deben estar disponibles
    menciona: tuple = ()       # roles que se pueden nombrar aunque no lo estén
    requiere: Optional[Condicion] = None
    peso: int = 1
    fuentes: tuple = ()        # ((clave_fuente, detalle), ...)


@dataclass
class Tirada:
    dado: int
    atributo: int
    bono: int
    total: int
    dificultad: int
    exito: bool

    def describir(self, enfoque: str) -> str:
        veredicto = "éxito" if self.exito else "fracaso"
        return (f"tirada: d6={self.dado} + {enfoque} {self.atributo} + "
                f"bonos {self.bono:+d} = {self.total} contra {self.dificultad}"
                f" -> {veredicto}")


@dataclass
class Bloque:
    escena: str
    texto: list
    eleccion: Optional[str]
    resultado: list
    fuentes: tuple = ()


@dataclass
class Capitulo:
    etapa: int
    titulo: str
    bloques: list = field(default_factory=list)


@dataclass
class Params:
    genero: str
    tono: str
    trama: str
    nombre: str
    pronombre: str      # m | f | n
    arquetipo: str
    falla: str
    semilla: int


class _Registro(string.Formatter):
    """Formateador que anota qué claves de la plantilla se usaron."""

    def __init__(self):
        super().__init__()
        self.usados = set()

    def get_value(self, key, args, kwargs):
        self.usados.add(key)
        return kwargs[key]


# --------------------------------------------------------------------------
# El mundo
# --------------------------------------------------------------------------
@dataclass
class Mundo:
    params: Params
    rng: random.Random
    lex: dict
    reparto: dict
    lugares: dict
    objetos: dict
    vinculo: str                       # ninguno | discipulo | familiar
    atributos: dict
    vigor: int = VIGOR_INICIAL
    etapa: int = 0
    amenaza: int = 0
    banderas: set = field(default_factory=set)
    inventario: set = field(default_factory=set)
    grupo: set = field(default_factory=set)
    cronica: list = field(default_factory=list)
    fuentes_usadas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    ambiente: str = ""
    _ambientes_vistos: set = field(default_factory=set)

    # --- consultas ---------------------------------------------------------
    @property
    def heroe(self) -> Personaje:
        return self.reparto["heroe"]

    def b(self, *banderas) -> bool:
        return all(x in self.banderas for x in banderas)

    def vivo(self, rol: str) -> bool:
        return self.reparto[rol].vivo

    def con(self, rol: str) -> bool:
        """El personaje viaja con el héroe y sigue vivo."""
        return rol in self.grupo and self.reparto[rol].vivo

    def villano_fuera(self) -> bool:
        return self.b("villano_derrotado") or self.b("villano_redimido")

    def disponible(self, rol: str) -> bool:
        """¿Puede este personaje aparecer activamente en la escena actual?"""
        if rol == "heroe":
            return True
        personaje = self.reparto[rol]
        if not personaje.vivo:
            return False
        if rol in ("mentor", "aliado"):
            return rol in self.grupo
        if rol == "heraldo":                 # se queda en casa
            return self.etapa <= 3 or self.etapa >= 12
        return True                          # el villano, mientras viva

    def bono(self, enfoque: str) -> int:
        n = sum(1 for obj in self.inventario
                if enfoque in BONOS_OBJETO.get(obj, ()))
        n += TONOS[self.params.tono]["bono"]
        if FALLAS[self.params.falla]["penaliza"] == enfoque:
            n -= 1
        return n

    # --- cambios de estado -------------------------------------------------
    def tirar(self, enfoque, dificultad, con_amenaza=False) -> Tirada:
        dif = dificultad(self) if callable(dificultad) else dificultad
        dif += AJUSTE_DIFICULTAD
        if con_amenaza:
            dif += min(2, self.amenaza)
        dado = self.rng.randint(1, 6)
        atributo = self.atributos[enfoque]
        bono = self.bono(enfoque)
        total = dado + atributo + bono
        return Tirada(dado, atributo, bono, total, dif, total >= dif)

    def crecer(self, enfoque: str) -> None:
        if enfoque in CRECEN:
            self.atributos[enfoque] = min(TOPE_ATRIBUTO,
                                          self.atributos[enfoque] + 1)

    def nuevo_ambiente(self) -> str:
        frases = [f for f in self.lex["ambiente"]
                  if f not in self._ambientes_vistos]
        if not frases:
            self._ambientes_vistos.clear()
            frases = list(self.lex["ambiente"])
        frase = self.rng.choice(frases)
        self._ambientes_vistos.add(frase)
        return frase

    # --- texto -------------------------------------------------------------
    def contexto(self) -> dict:
        falla = FALLAS[self.params.falla]
        base = dict(self.reparto)
        base.update(self.lugares)
        base.update(self.objetos)
        ctx = dict(base)
        ctx["problema"] = self.lex["problema"][self.params.trama].format(**base)
        ctx["objetivo"] = OBJETIVOS[self.params.trama].format(**base)
        ctx["ambiente"] = self.ambiente
        ctx["rasgo"] = ARQUETIPOS[self.params.arquetipo]["rasgo"]
        ctx["falla_txt"] = falla["texto"]
        ctx["voz_inicio"] = falla["voz_inicio"]
        ctx["voz_final"] = falla["voz_final"]
        ctx["tentacion_meta"] = falla["tentacion_meta"]
        return ctx

    def renderizar(self, parrafos, menciona=()) -> list:
        """Rellena las plantillas y anota incoherencias de personajes.

        Si el texto nombra a alguien que no está disponible (muerto, ausente)
        y la escena no lo declaró en `menciona`, se registra un aviso. Los
        tests exigen que no haya ninguno.
        """
        ctx = self.contexto()
        fmt = _Registro()
        salida = []
        for p in parrafos:
            texto, cond = (p, None) if isinstance(p, str) else (p.texto, p.si)
            if cond is not None and not cond(self):
                continue
            salida.append(fmt.vformat(texto, (), ctx))
        for rol in fmt.usados:
            if (rol in self.reparto and rol not in menciona
                    and not self.disponible(rol)):
                self.avisos.append(
                    f"etapa {self.etapa}: se nombra a '{rol}' sin que esté "
                    f"disponible: {salida[0][:50] if salida else ''}")
        return salida

    def titulo(self) -> str:
        if self.params.trama == "monstruo":
            return f"La sombra {self.reparto['villano'].de}"
        return str(self.objetos["meta"].Cap)

    def usar_fuentes(self, fuentes) -> None:
        for clave, _ in fuentes:
            if clave not in self.fuentes_usadas:
                self.fuentes_usadas.append(clave)
