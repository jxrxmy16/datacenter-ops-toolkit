"""Pruebas del modo de lectura: escribir libremente frente a ver la lista.

Lo que garantizan:

  * Por defecto el jugador escribe: en las escenas normales no se enseña la
    lista de opciones, solo se le pregunta «¿Qué haces?».
  * «?» enseña las ideas cuando se piden, y también salen solas cuando lo
    escrito no se pudo aplicar (así nadie se queda sin salida).
  * En los momentos críticos la lista siempre está.
  * `/modo` alterna y `--opciones` arranca con la lista de siempre.
"""

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_forja import nueva_sesion                                 # noqa: E402
from forja.consola import Consola, analizar_linea                   # noqa: E402
from forja import lenguaje                                          # noqa: E402

OPCIONES = [("Valor", "Plantar cara al guardián"),
            ("Ingenio", "Buscar otro camino"),
            ("Compasión", "Ayudar al herido")]


def tearDownModule():
    lenguaje.fijar_personal(None)


def leer_con(consola, entradas, **kw):
    """Llama a `Consola.leer` con respuestas fijas y devuelve (resultado, salida)."""
    pendientes = list(entradas)
    prompts = []

    def falso(prompt="> "):
        prompts.append(prompt)
        return pendientes.pop(0)

    salida = io.StringIO()
    with mock.patch.object(Consola, "_leer_linea", side_effect=falso), \
            contextlib.redirect_stdout(salida):
        r = consola.leer(OPCIONES, **kw)
    return r, salida.getvalue(), prompts


def consola(**kw):
    return Consola(color=False, pausas=False, **kw)


class TestModoLibre(unittest.TestCase):
    def test_por_defecto_no_se_enseña_la_lista(self):
        r, salida, prompts = leer_con(consola(), ["atacar al guardián"])
        self.assertEqual(r, ("txt", "atacar al guardián"))
        self.assertNotIn("Plantar cara", salida)
        self.assertNotIn("1)", salida)
        self.assertIn("¿Qué haces?", prompts[0])

    def test_la_primera_vez_da_ejemplos_y_luego_no(self):
        c = consola()
        _, primera, _ = leer_con(c, ["mirar"])
        _, segunda, _ = leer_con(c, ["mirar"])
        self.assertIn("Escribe con tus palabras", primera)
        self.assertNotIn("Escribe con tus palabras", segunda)

    def test_el_numero_sigue_valiendo_aunque_no_se_vea(self):
        r, _, _ = leer_con(consola(), ["2"])
        self.assertEqual(r, ("op", 1))

    def test_interrogacion_enseña_las_ideas_y_sigue_esperando(self):
        r, salida, prompts = leer_con(consola(), ["?", "3"])
        self.assertEqual(r, ("op", 2))
        self.assertIn("Plantar cara al guardián", salida)
        self.assertIn("Ayudar al herido", salida)
        self.assertEqual(len(prompts), 2)

    def test_otras_formas_de_pedir_ideas(self):
        for texto in ("?", "ideas", "Opciones", "ver opciones"):
            self.assertEqual(analizar_linea(texto, 3), ("ideas",), texto)
        # …pero una frase que solo contiene la palabra sigue siendo una frase
        self.assertEqual(analizar_linea("ver opciones de huida", 3)[0], "txt")

    def test_pedir_lista_la_enseña_en_la_siguiente_lectura_solo(self):
        c = consola()
        c.pedir_lista()
        _, con, _ = leer_con(c, ["1"])
        _, sin, _ = leer_con(c, ["1"])
        self.assertIn("Buscar otro camino", con)
        self.assertNotIn("Buscar otro camino", sin)

    def test_los_momentos_criticos_siempre_enseñan_la_lista(self):
        r, salida, _ = leer_con(consola(), ["1"], libre_ok=False, critica=True)
        self.assertEqual(r, ("op", 0))
        self.assertIn("Plantar cara al guardián", salida)
        self.assertIn("Momento crítico", salida)

    def test_modo_opciones_enseña_siempre_la_lista(self):
        c = consola(modo="opciones")
        for _ in range(2):
            _, salida, prompts = leer_con(c, ["1"])
            self.assertIn("Plantar cara al guardián", salida)
            self.assertNotIn("¿Qué haces?", prompts[0])

    def test_un_modo_desconocido_cae_en_libre(self):
        self.assertEqual(consola(modo="otro").modo, "libre")

    def test_cambiar_modo(self):
        c = consola()
        self.assertIn("opciones", c.cambiar_modo("").lower())
        self.assertEqual(c.modo, "opciones")
        c.cambiar_modo("libre")
        self.assertEqual(c.modo, "libre")
        self.assertIn("Uso", c.cambiar_modo("quién sabe"))
        self.assertEqual(c.modo, "libre")


class TestModoEnLaSesion(unittest.TestCase):
    def test_lo_que_no_se_entiende_enseña_las_ideas(self):
        ses = nueva_sesion(5, guion=["xyzzyplugh qwerty", "/salir"])
        try:
            ses.ejecutar()
        except Exception:
            pass
        self.assertGreaterEqual(getattr(ses.ui, "listas_pedidas", 0), 1)

    def test_el_comando_modo_responde(self):
        ses = nueva_sesion(5, guion=["/modo", "/salir"])
        try:
            ses.ejecutar()
        except Exception:
            pass
        self.assertIn("modo", ses.ui.mensajes)

    def test_el_comando_ideas_pide_la_lista(self):
        ses = nueva_sesion(5, guion=["/ideas", "/salir"])
        try:
            ses.ejecutar()
        except Exception:
            pass
        self.assertGreaterEqual(getattr(ses.ui, "listas_pedidas", 0), 1)


if __name__ == "__main__":
    unittest.main()
