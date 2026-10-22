"""Interfaz de consola (pensada para CMD de Windows, PowerShell, Termux y Unix).

Hay tres interfaces con la misma API, que la sesión usa sin saber cuál es:

  * Consola: interactiva, con menús, texto libre y color opcional.
  * Demo:    la misma salida, pero elige sola entre las opciones.
  * Muda:    sin salida y con guion o estrategia (para las pruebas).
"""

import os
import random
import re
import shutil
import sys
import textwrap

from .fuentes import FUENTES, agrupar, nota
from .modelo import ETIQUETAS

_COLORES = {
    "titulo": "1;33", "capitulo": "1;36", "etiqueta": "36", "nota": "2;37",
    "dado": "2;35", "final": "1;32", "aviso": "33", "elige": "1",
    "tuyo": "1;34",
}

# Menú de ayuda cuando el intérprete no sabe qué has querido decir.
MENU_INTENCIONES = [
    ("valor", "Atacar o actuar con fuerza"),
    ("ingenio", "Engañar o usar la astucia"),
    ("compasion", "Ayudar o cuidar a alguien"),
    ("sombra", "Aprovecharme o actuar sin escrúpulos"),
    ("duda", "Huir, evitar o esperar"),
    ("observar", "Observar o pensar"),
    ("hablar", "Hablar con alguien"),
    ("descansar", "Descansar, comer o dormir"),
    ("moverse", "Moverme o ir a otro sitio"),
]

# Palabras sueltas que se aceptan como comando sin la barra.
COMANDOS_SUELTOS = {"atras", "atrás", "deshacer", "ayuda", "historial", "estado",
                    "guardar", "cargar", "partidas", "reintentar", "otra"}


def preparar_salida(color=True):
    """Activa UTF-8 y, en Windows, las secuencias ANSI. Devuelve si hay color."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if os.name == "nt":
        os.system("")   # truco clásico: activa ANSI en la consola de Windows 10+
    return bool(color and sys.stdout.isatty() and "NO_COLOR" not in os.environ)


def entero(texto):
    """Un entero pequeño escrito con cifras ASCII, o None.

    `str.isdigit()` da True para '²' o '①' y `int()` se niega con más de 4300
    cifras; ninguna de las dos cosas debe tumbar la partida.
    """
    t = str(texto).strip()
    return int(t) if t.isascii() and t.isdigit() and len(t) <= 6 else None


def analizar_linea(linea: str, n_opciones: int):
    """Clasifica lo que escribió el jugador: opción, comando o texto libre."""
    s = linea.strip()
    if not s:
        return ("vacio",)
    i = entero(s)
    if i is not None:
        return ("op", i - 1) if 1 <= i <= n_opciones else ("mal", s)
    if s.startswith("/"):
        nombre, _, arg = s[1:].partition(" ")
        return ("cmd", nombre.strip().lower(), arg.strip())
    low = s.lower()
    if low in ("?", "ideas", "opciones", "ver opciones"):
        return ("ideas",)
    if low == "n":
        return ("cmd", "notas", "")
    if low == "q":
        return ("cmd", "salir", "")
    primero, _, resto = low.partition(" ")
    if primero in COMANDOS_SUELTOS and not resto.strip():
        return ("cmd", primero, "")
    if primero in ("atras", "atrás", "volver") and entero(resto) is not None:
        return ("cmd", primero, resto.strip())
    return ("txt", s)


class Consola:
    def __init__(self, color=True, notas=False, pausas=True, modo="libre", dados=True):
        self.color = preparar_salida(color)
        self.notas = notas
        self.dados = dados            # enseñar la tirada de cada acción arriesgada
        self.pausas = pausas
        # "libre": se escribe con palabras propias y la lista de opciones solo
        # sale si se pide («?») o en los momentos críticos; "opciones": la
        # lista se enseña siempre.
        self.modo = modo if modo in ("libre", "opciones") else "libre"
        self._lista_pedida = False
        self._ejemplos_dados = False
        self._pista_dada = False

    # --- utilidades --------------------------------------------------------
    @property
    def ancho(self):
        return max(40, min(shutil.get_terminal_size((80, 24)).columns - 2, 92))

    def c(self, texto, estilo):
        if not self.color:
            return texto
        return f"\033[{_COLORES[estilo]}m{texto}\033[0m"

    def parrafo(self, texto, sangria="", estilo=None):
        out = textwrap.fill(texto, self.ancho, initial_indent=sangria,
                            subsequent_indent=sangria)
        print(self.c(out, estilo) if estilo else out)

    def _con_sangria(self, texto, sangria="  ", extra=None, estilo=None):
        """Imprime `texto` ajustado al ancho, con sangría francesa.

        Si no se indica `extra`, las líneas siguientes se alinean bajo el texto
        que sigue al número de una lista ("1) ...") o 2 espacios más adentro.
        """
        if extra is None:
            m = re.match(r"\d+\) ", texto)
            extra = m.end() if m else 2
        out = textwrap.fill(texto, self.ancho, initial_indent=sangria,
                            subsequent_indent=sangria + " " * extra,
                            break_long_words=False, break_on_hyphens=False)
        print(self.c(out, estilo) if estilo else out)

    def _leer_linea(self, prompt="> "):
        try:
            return input(prompt)
        except EOFError:
            raise KeyboardInterrupt

    def esperar(self, mensaje="Pulsa Enter para continuar..."):
        if self.pausas:
            self._leer_linea(self.c(f"\n  {mensaje}", "nota"))
        print()

    # --- preguntas previas a la partida ----------------------------------
    def menu(self, titulo, opciones, azar=True):
        """opciones: lista de (clave, nombre, descripcion). Devuelve la clave."""
        print(self.c(f"\n{titulo}", "elige"))
        for i, (_, nombre, desc) in enumerate(opciones, 1):
            self._con_sangria(f"{i}) {nombre}" + (f" - {desc}" if desc else ""), "  ")
        if azar:
            print("  0) Sorpréndeme (también vale pulsar Enter)")
        while True:
            r = self._leer_linea().strip()
            if r in ("", "0") and azar:
                return None
            n = entero(r)
            if n is not None and 1 <= n <= len(opciones):
                return opciones[n - 1][0]
            print(self.c("  Elige un número de la lista.", "aviso"))

    def multi(self, titulo, opciones):
        """Varias opciones a la vez: «1,3» o «1 3». Enter = ninguna. Devuelve las claves."""
        print(self.c(f"\n{titulo}", "elige"))
        for i, (_, nombre, desc) in enumerate(opciones, 1):
            self._con_sangria(f"{i}) {nombre}" + (f" - {desc}" if desc else ""), "  ")
        while True:
            r = self._leer_linea().strip()
            if not r or r.lower() in ("no", "n", "ninguno", "ninguna", "0"):
                return []
            numeros = re.split(r"[\s,;y]+", r.lower())
            elegidas = [entero(x) for x in numeros if x]
            if elegidas and all(n is not None and 1 <= n <= len(opciones) for n in elegidas):
                return list(dict.fromkeys(opciones[n - 1][0] for n in elegidas))
            print(self.c("  Escribe números de la lista separados por comas, o Enter para ninguno.",
                         "aviso"))

    def texto(self, pregunta, defecto=None):
        sufijo = f" [{defecto}]" if defecto else ""
        r = self._leer_linea(f"\n{pregunta}{sufijo}: ").strip()
        return r or defecto

    def si_no(self, pregunta, defecto=True):
        marca = "S/n" if defecto else "s/N"
        r = self._leer_linea(f"\n{pregunta} [{marca}] ").strip().lower()
        if not r:
            return defecto
        return r not in ("n", "no")

    # --- salida general ------------------------------------------------------
    def mensaje(self, texto):
        self.parrafo(texto, "  ", "aviso")

    def imprimir(self, lineas):
        """Líneas ya formadas (ayuda, listas...). Se ajustan al ancho de la
        pantalla conservando su sangría; las órdenes («/atras  deshace...»)
        continúan alineadas bajo su descripción."""
        print()
        for linea in lineas:
            if not linea.strip():
                print()
                continue
            lead = len(linea) - len(linea.lstrip())
            orden = re.match(r" */\S+(?: \S+)?? {2,}(?=\S)", linea)
            extra = orden.end() - lead if orden and orden.end() + 24 < self.ancho else 2
            self._con_sangria(linea.strip(), "  " + " " * lead, extra)
        print()

    def portada(self, titulo, subtitulo=""):
        linea = "=" * min(self.ancho, 60)
        print(self.c(f"\n{linea}\n  {titulo}\n{linea}", "titulo"))
        if subtitulo:
            self.parrafo(subtitulo, "  ", "nota")

    def inicio(self, w):
        self.portada(w.titulo().upper(),
                     f"Crónica de {w.heroe.nombre} · semilla {w.params.semilla}")
        print()
        if self.modo == "libre":
            self.parrafo("Escribe lo que quieras hacer, con tus palabras. «?» te "
                         "da ideas y «/ayuda» explica los comandos (deshacer, "
                         "guardar...).", "  ", "nota")
        else:
            self.parrafo("Elige un número o escribe lo que quieras hacer. «/ayuda» "
                         "explica los comandos (deshacer, guardar...).", "  ", "nota")

    def capitulo(self, etapa, titulo):
        print()
        self.parrafo(f"--- Capítulo {etapa} de 12: {titulo} ---", "", "capitulo")
        print()

    def mostrar_notas(self, fuentes):
        if fuentes:
            print()
            for clave, detalle in fuentes:
                self.parrafo(f"[Fuente] {nota(clave, detalle)}", "  ", "nota")

    def escena(self, parrafos, fuentes=(), critica=False):
        for p in parrafos:
            self.parrafo(p)
            print()
        self._fuentes = fuentes
        if self.notas:
            self.mostrar_notas(fuentes)
        self._pista_dada = False

    # --- lectura de acciones -------------------------------------------------
    def _listar(self, opciones, marcada=None, probs=None):
        """Imprime las opciones numeradas, con sangría francesa (y la probabilidad
        de acertar, si la opción tiene tirada)."""
        for i, (rotulo, etiqueta) in enumerate(opciones, 1):
            cab = ("> " if marcada == i - 1 else "  ") + f"{i}) "
            p = probs[i - 1] if probs and i - 1 < len(probs) else None
            extra = f"  (≈ {round(100 * p)} %)" if p is not None else ""
            cuerpo = textwrap.fill(f"[{rotulo}] {etiqueta}{extra}", self.ancho,
                                   initial_indent=cab,
                                   subsequent_indent=" " * len(cab))
            print(cuerpo.replace(f"[{rotulo}]", self.c(f"[{rotulo}]", "etiqueta"), 1))

    def pedir_lista(self):
        """La próxima lectura enseña las opciones aunque el modo sea libre."""
        self._lista_pedida = True

    def cambiar_modo(self, arg=""):
        """Alterna (o fija) el modo de lectura y devuelve el aviso para el jugador."""
        arg = arg.strip().lower()
        if arg in ("libre", "opciones"):
            self.modo = arg
        elif not arg:
            self.modo = "opciones" if self.modo == "libre" else "libre"
        else:
            return "Uso: /modo libre (escribes) o /modo opciones (siempre ves la lista)."
        self._ejemplos_dados = False
        if self.modo == "libre":
            return ("Modo libre: escribes lo que quieres hacer; con «?» ves ideas. "
                    "En los momentos críticos sigue habiendo opciones.")
        return "Modo opciones: verás la lista en cada escena (y aún puedes escribir)."

    def leer(self, opciones, libre_ok=True, critica=False):
        """Devuelve ('op', i) | ('txt', frase) | ('cmd', nombre, argumento)."""
        probs = getattr(self, "probs_actuales", None)
        listar = critica or self.modo == "opciones" or self._lista_pedida
        self._lista_pedida = False
        if listar:
            self._listar(opciones, probs=probs)
        if critica:
            self.parrafo("Momento crítico: elige una opción.", "  ", "aviso")
        elif not listar:
            if not self._ejemplos_dados:
                self.parrafo("Escribe con tus palabras lo que haces: «mirar a mi "
                             "alrededor», «hablar con el mentor», «avanzar con "
                             "cuidado»… Con «?» te enseño ideas; también vale un "
                             "número. «/ayuda» explica los comandos.", "  ", "nota")
                print()
                self._ejemplos_dados = True
        elif not self._pista_dada:
            self.parrafo("…o escribe lo que quieras hacer (y «/ayuda» para "
                         "deshacer, guardar, etc.).", "  ", "nota")
            self._pista_dada = True
        indicacion = "\n> " if listar else "¿Qué haces? (? = ideas) > "
        while True:
            e = analizar_linea(self._leer_linea(indicacion), len(opciones))
            if e[0] == "vacio":
                continue
            if e[0] == "ideas":
                print(self.c("\n  Ideas (o escribe otra cosa):", "nota"))
                self._listar(opciones, probs=probs)
                indicacion = "\n> "
                continue
            if e[0] == "mal":
                print(self.c("  Ese número no está en la lista.", "aviso"))
                continue
            print()
            return e

    def confirmar(self, interp, rotulo, etiqueta, permite_libre=False):
        """Muestra cómo se ha entendido la frase. Devuelve 's', 'n' o 'l'."""
        self._con_sangria(f"Lo entiendo así: [{rotulo}] {etiqueta}", "  ", 2, "tuyo")
        if interp.mods_desc:
            signo = "+" if interp.dd > 0 else ""
            self.parrafo(f"({', '.join(interp.mods_desc)}: dificultad "
                         f"{signo}{interp.dd})", "  ", "nota")
        extra = " · l = solo como acción libre" if permite_libre else ""
        self._con_sangria(f"¿Es eso? Enter = sí · n = no, otra cosa{extra}", "  ", 2, "nota")
        while True:
            r = self._leer_linea("  > ").strip().lower()
            if r in ("", "s", "si", "sí"):
                print()
                return "s"
            if r in ("n", "no"):
                print()
                return "n"
            if r == "l" and permite_libre:
                print()
                return "l"

    def preguntar_intencion(self, frase, sugerida=None):
        """Ayuda cuando el intérprete duda. Devuelve la intención elegida o None.

        Si trae una `sugerida`, primero se confirma; con «n» se ofrece el menú.
        """
        nombres = dict(MENU_INTENCIONES)
        if sugerida in nombres:
            self._con_sangria(f"Creo que «{frase}» es: {nombres[sugerida].lower()}. "
                              "¿Vale? Enter = sí · n = no, elegir", "  ", 2, "tuyo")
            r = self._leer_linea("  > ").strip().lower()
            if r in ("", "s", "si", "sí"):
                return sugerida
        else:
            self._con_sangria(f"No sé cómo interpretar «{frase}». ¿Qué intentas?",
                              "  ", 2, "tuyo")
        for i, (_, texto) in enumerate(MENU_INTENCIONES, 1):
            self._con_sangria(f"{i}) {texto}", "   ")
        print("   0) Ninguna: lo escribo de otra forma")
        while True:
            r = self._leer_linea(self.c("  > ", "nota")).strip()
            if r == "0":
                return None
            n = entero(r)
            if n is not None and 1 <= n <= len(MENU_INTENCIONES):
                print()
                return MENU_INTENCIONES[n - 1][0]

    def pedir_final(self):
        print()
        self._con_sangria("Fin. «/atras» para rectificar, «/libro» para guardar el "
                          "libro, Enter para terminar.", "  ", 2, "nota")
        r = self._leer_linea("  > ").strip()
        if not r:
            return ("fin",)
        e = analizar_linea(r, 0)
        return e if e[0] == "cmd" else ("cmd", "ayuda", "")

    # --- resultados ----------------------------------------------------------
    def interludio(self, frase, parrafos, tirada=None, enfoque=None):
        self.parrafo(f"▸ «{frase}»", "", "tuyo")
        for p in parrafos:
            self.parrafo(p)
        if self.dados and tirada is not None:
            self.parrafo(f"({tirada.describir(ETIQUETAS.get(enfoque, 'ingenio').lower())})",
                         "  ", "dado")
        print()

    def resultado(self, parrafos, tirada=None, enfoque=None):
        for p in parrafos:
            self.parrafo(p)
            print()
        if self.dados and tirada is not None:
            self.parrafo(f"({tirada.describir(ETIQUETAS.get(enfoque, 'ingenio').lower())})",
                         "  ", "dado")
        self.esperar()

    def final(self, final, w):
        linea = "=" * min(self.ancho, 60)
        print(self.c(f"\n{linea}\n  {final.titulo}\n{linea}\n", "final"))
        for p in final.parrafos:
            self.parrafo(p)
            print()
        if self.notas:
            self.mostrar_notas(final.fuentes)

    def bibliografia(self, w):
        print(self.c("\nFuentes de esta partida", "capitulo"))
        for titulo, claves in agrupar(w.fuentes_usadas).items():
            print(self.c(f"\n  {titulo}", "elige"))
            for clave in claves:
                texto = FUENTES[clave].cita.replace("*", "")
                print(textwrap.fill(texto, self.ancho, initial_indent="    · ",
                                    subsequent_indent="      "))


class Demo(Consola):
    """Igual que Consola, pero elige sola entre las opciones y no hace pausas."""

    def __init__(self, semilla, color=True, notas=False):
        super().__init__(color=color, notas=notas, pausas=False, modo="opciones")
        self._rng = random.Random(semilla * 7919 + 1)

    def leer(self, opciones, libre_ok=True, critica=False):
        probs = getattr(self, "probs_actuales", None)
        # Juega como una persona razonable: casi siempre evita la ambición y la
        # duda, pero no siempre (así también se ven los caminos oscuros).
        buenas = [k for k, (rotulo, _) in enumerate(opciones)
                  if rotulo not in ("Ambición", "Duda")]
        if buenas and self._rng.random() < 0.85:
            i = self._rng.choice(buenas)
        else:
            i = self._rng.randrange(len(opciones))
        self._listar(opciones, marcada=i, probs=probs)
        print()
        return ("op", i)

    def pedir_final(self):
        return ("fin",)


class Muda:
    """Interfaz sin salida para pruebas.

    `guion` es una lista de entradas que se sirven en orden:
      un entero  -> ('op', n)        "texto" -> ('txt', texto)
      "/cmd arg" -> ('cmd', cmd, arg)   ("confirmar", 'n') etc. para las respuestas
    Cuando se acaba el guion elige con la estrategia.
    """

    notas = False

    def __init__(self, semilla=0, estrategia="azar", guion=None, confirmaciones=None,
                 intenciones=None):
        import random as _r
        self._rng = _r.Random(semilla)
        self.estrategia = estrategia
        self.guion = list(guion or [])
        self.confirmaciones = list(confirmaciones or [])
        self.intenciones = list(intenciones or [])   # respuestas del menú de ayuda
        self.preguntas = []             # (frase, sugerida) que se han preguntado
        self.mensajes = []
        self.lineas = []
        self.interludios = []
        self.resultados = []
        self.escenas = []
        self.final_guion = []

    def inicio(self, w): pass
    def capitulo(self, etapa, titulo): pass
    def mostrar_notas(self, fuentes): pass
    def pedir_lista(self): self.listas_pedidas = getattr(self, "listas_pedidas", 0) + 1
    def cambiar_modo(self, arg=""): return "modo"

    def escena(self, parrafos, fuentes=(), critica=False):
        self.escenas.append((parrafos, critica))

    def interludio(self, frase, parrafos, tirada=None, enfoque=None):
        self.interludios.append((frase, parrafos))

    def resultado(self, parrafos, tirada=None, enfoque=None):
        self.resultados.append(parrafos)

    def final(self, final, w): self.ultimo_final = final
    def mensaje(self, texto): self.mensajes.append(texto)
    def imprimir(self, lineas): self.lineas.extend(lineas)

    def confirmar(self, interp, rotulo, etiqueta, permite_libre=False):
        return self.confirmaciones.pop(0) if self.confirmaciones else "s"

    def preguntar_intencion(self, frase, sugerida=None):
        self.preguntas.append((frase, sugerida))
        if self.intenciones:
            x = self.intenciones.pop(0)
            return None if x in (None, "ninguna") else x
        return sugerida

    def pedir_final(self):
        if self.final_guion:
            return analizar_linea(self.final_guion.pop(0), 0)
        return ("fin",)

    def leer(self, opciones, libre_ok=True, critica=False):
        self.ultimas_probs = getattr(self, "probs_actuales", None)
        if self.guion:
            e = self.guion.pop(0)
            if isinstance(e, int):
                return ("op", e)
            if isinstance(e, tuple):
                return e
            return analizar_linea(e, len(opciones))
        n = len(opciones)
        if self.estrategia == "primera":
            return ("op", 0)
        if self.estrategia == "ultima":
            return ("op", n - 1)
        if self.estrategia == "prudente":
            buenas = [i for i, (rotulo, _) in enumerate(opciones)
                      if rotulo not in ("Ambición", "Duda")]
            if buenas:
                return ("op", self._rng.choice(buenas))
        return ("op", self._rng.randrange(n))
