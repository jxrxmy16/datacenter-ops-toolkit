"""Ayudas de gramática española para que los textos generados concuerden.

Los léxicos guardan los sustantivos con su artículo ("la Corona de Ceniza",
"un dron de seguridad"). `Nom` sabe declinarlos dentro de una plantilla:

    {meta}        la Corona de Ceniza
    {meta.Cap}    La Corona de Ceniza
    {meta.de}     de la Corona de Ceniza   (y "del núcleo" si es "el núcleo")
    {meta.a}      a la Corona de Ceniza    (y "al núcleo")
    {meta.ya}     la Corona de Ceniza      (convierte "una daga" en "la daga")
    {meta.el}     ella / él / ellas / ellos
    {meta.lo}     la / lo / las / los
    {meta.o}      a / o / as / os          (robad{meta.o})
"""

_INDEFINIDO = {"el": "un", "la": "una", "los": "unos", "las": "unas"}
_DEFINIDO = {v: k for k, v in _INDEFINIDO.items()}
_TERMINACION = {"el": "o", "la": "a", "los": "os", "las": "as",
                "un": "o", "una": "a", "unos": "os", "unas": "as"}
_CLITICO = {"el": "lo", "la": "la", "los": "los", "las": "las",
            "un": "lo", "una": "la", "unos": "los", "unas": "las"}
_PRONOMBRE = {"el": "él", "la": "ella", "los": "ellos", "las": "ellas",
              "un": "él", "una": "ella", "unos": "ellos", "unas": "ellas"}


class Nom(str):
    """Sintagma nominal con artículo que sabe declinarse."""

    def _partes(self):
        primera, _, resto = self.partition(" ")
        return primera.lower(), resto

    @property
    def de(self):
        art, resto = self._partes()
        return Nom("del " + resto) if art == "el" else Nom("de " + self)

    @property
    def a(self):
        art, resto = self._partes()
        return Nom("al " + resto) if art == "el" else Nom("a " + self)

    @property
    def Cap(self):
        return Nom(self[:1].upper() + self[1:])

    @property
    def ya(self):
        """Forma determinada: 'una daga rúnica' -> 'la daga rúnica'."""
        art, resto = self._partes()
        return Nom(_DEFINIDO[art] + " " + resto) if art in _DEFINIDO else self

    @property
    def o(self):
        return _TERMINACION.get(self._partes()[0], "o")

    @property
    def lo(self):
        return _CLITICO.get(self._partes()[0], "lo")

    @property
    def el(self):
        return _PRONOMBRE.get(self._partes()[0], "él")
