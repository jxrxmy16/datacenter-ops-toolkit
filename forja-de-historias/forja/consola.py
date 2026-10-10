"""Interfaz de consola (pensada para CMD de Windows, PowerShell y terminales Unix).

Hay tres interfaces con la misma API, que el motor usa sin saber cuál es:

  * Consola: interactiva, con menús y color opcional.
  * Demo:    la misma salida, pero elige sola (para ver una partida entera).
  * Muda:    sin salida, elige con una estrategia (para las pruebas).
"""

import os
import random
import shutil
import sys
import textwrap

from .fuentes import FUENTES, agrupar, nota
from .modelo import ETIQUETAS

_COLORES = {
    "titulo": "1;33", "capitulo": "1;36", "etiqueta": "36", "nota": "2;37",
    "dado": "2;35", "final": "1;32", "aviso": "33", "elige": "1",
}


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


class Consola:
    def __init__(self, color=True, notas=False, pausas=True):
        self.color = preparar_salida(color)
        self.notas = notas
        self.pausas = pausas

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

    def esperar(self, mensaje="Pulsa Enter para continuar..."):
        if self.pausas:
            try:
                input(self.c(f"\n  {mensaje}", "nota"))
            except EOFError:
                raise KeyboardInterrupt
        print()

    # --- preguntas previas a la partida ----------------------------------
    def menu(self, titulo, opciones, azar=True):
        """opciones: lista de (clave, nombre, descripcion). Devuelve la clave."""
        print(self.c(f"\n{titulo}", "elige"))
        for i, (_, nombre, desc) in enumerate(opciones, 1):
            print(f"  {i}) {nombre}" + (f" - {desc}" if desc else ""))
        if azar:
            print("  0) Sorpréndeme (también vale pulsar Enter)")
        while True:
            try:
                r = input("> ").strip()
            except EOFError:
                raise KeyboardInterrupt
            if r in ("", "0") and azar:
                return None
            if r.isdigit() and 1 <= int(r) <= len(opciones):
                return opciones[int(r) - 1][0]
            print(self.c("  Elige un número de la lista.", "aviso"))

    def texto(self, pregunta, defecto=None):
        sufijo = f" [{defecto}]" if defecto else ""
        try:
            r = input(f"\n{pregunta}{sufijo}: ").strip()
        except EOFError:
            raise KeyboardInterrupt
        return r or defecto

    # --- API del motor -------------------------------------------------------
    def portada(self, titulo, subtitulo=""):
        linea = "=" * min(self.ancho, 60)
        print(self.c(f"\n{linea}\n  {titulo}\n{linea}", "titulo"))
        if subtitulo:
            self.parrafo(subtitulo, "  ", "nota")

    def inicio(self, w):
        self.portada(w.titulo().upper(),
                     f"Crónica de {w.heroe.nombre} · semilla {w.params.semilla}")
        print()
        self.parrafo("Escribe el número de tu elección. En cualquier momento: "
                     "«n» activa o desactiva las notas de fuentes, «q» sale.",
                     "  ", "nota")

    def capitulo(self, etapa, titulo):
        print(self.c(f"\n--- Capítulo {etapa} de 12: {titulo} ---", "capitulo"))
        print()

    def _notas(self, fuentes):
        if self.notas and fuentes:
            print()
            for clave, detalle in fuentes:
                self.parrafo(f"[Fuente] {nota(clave, detalle)}", "  ", "nota")

    def escena(self, parrafos, fuentes=()):
        for p in parrafos:
            self.parrafo(p)
            print()
        self._fuentes_pendientes = fuentes
        self._notas(fuentes)

    def _listar(self, opciones, marcada=None):
        """Imprime las opciones numeradas, con sangría francesa."""
        for i, (rotulo, etiqueta) in enumerate(opciones, 1):
            cab = ("> " if marcada == i - 1 else "  ") + f"{i}) "
            cuerpo = textwrap.fill(f"[{rotulo}] {etiqueta}", self.ancho,
                                   initial_indent=cab,
                                   subsequent_indent=" " * len(cab))
            print(cuerpo.replace(f"[{rotulo}]", self.c(f"[{rotulo}]", "etiqueta"), 1))

    def elegir(self, opciones):
        """opciones: lista de (rotulo, etiqueta). Devuelve el índice elegido."""
        self._listar(opciones)
        while True:
            try:
                r = input("\n> ").strip().lower()
            except EOFError:
                raise KeyboardInterrupt
            if r == "q":
                raise KeyboardInterrupt
            if r == "n":
                self.notas = not self.notas
                estado = "activadas" if self.notas else "desactivadas"
                print(self.c(f"  Notas de fuentes {estado}.", "aviso"))
                self._notas(getattr(self, "_fuentes_pendientes", ()))
                continue
            if r.isdigit() and 1 <= int(r) <= len(opciones):
                print()
                return int(r) - 1
            print(self.c("  Elige un número de la lista.", "aviso"))

    def resultado(self, parrafos, tirada=None, enfoque=None):
        for p in parrafos:
            self.parrafo(p)
            print()
        if self.notas and tirada is not None:
            self.parrafo(f"({tirada.describir(ETIQUETAS[enfoque].lower())})",
                         "  ", "dado")
        self.esperar()

    def final(self, final, w):
        linea = "=" * min(self.ancho, 60)
        print(self.c(f"\n{linea}\n  {final.titulo}\n{linea}\n", "final"))
        for p in final.parrafos:
            self.parrafo(p)
            print()
        self._notas(final.fuentes)

    def bibliografia(self, w):
        print(self.c("\nFuentes de esta partida", "capitulo"))
        for titulo, claves in agrupar(w.fuentes_usadas).items():
            print(self.c(f"\n  {titulo}", "elige"))
            for clave in claves:
                texto = FUENTES[clave].cita.replace("*", "")
                print(textwrap.fill(texto, self.ancho, initial_indent="    · ",
                                    subsequent_indent="      "))


class Demo(Consola):
    """Igual que Consola, pero elige sola y no hace pausas."""

    def __init__(self, semilla, color=True, notas=False):
        super().__init__(color=color, notas=notas, pausas=False)
        self._rng = random.Random(semilla * 7919 + 1)

    def elegir(self, opciones):
        # Juega como una persona razonable: casi siempre evita la ambición y la
        # duda, pero no siempre (así también se ven los caminos oscuros).
        buenas = [k for k, (rotulo, _) in enumerate(opciones)
                  if rotulo not in ("Ambición", "Duda")]
        if buenas and self._rng.random() < 0.85:
            i = self._rng.choice(buenas)
        else:
            i = self._rng.randrange(len(opciones))
        self._listar(opciones, marcada=i)
        print()
        return i


class Muda:
    """Interfaz sin salida para pruebas: elige con una estrategia."""

    notas = False

    def __init__(self, semilla=0, estrategia="azar"):
        self._rng = random.Random(semilla)
        self.estrategia = estrategia

    def inicio(self, w): pass
    def capitulo(self, etapa, titulo): pass
    def escena(self, parrafos, fuentes=()): pass
    def resultado(self, parrafos, tirada=None, enfoque=None): pass
    def final(self, final, w): pass

    def elegir(self, opciones):
        if self.estrategia == "primera":
            return 0
        if self.estrategia == "ultima":
            return len(opciones) - 1
        if self.estrategia == "prudente":
            # Un jugador sensato: evita la ambición y la duda si puede.
            buenas = [i for i, (rotulo, _) in enumerate(opciones)
                      if rotulo not in ("Ambición", "Duda")]
            if buenas:
                return self._rng.choice(buenas)
        return self._rng.randrange(len(opciones))
