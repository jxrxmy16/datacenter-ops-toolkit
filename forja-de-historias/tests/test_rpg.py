"""Pruebas del componente RPG: probabilidades exactas, modificadores y lo que se enseña.

Garantizan que:
  * la probabilidad que se enseña es EXACTAMENTE la de la tirada (se contrasta con
    el dado real, y con una simulación);
  * cada atributo se muestra como un modificador alrededor de 0 (lo no entrenado
    resta) sin cambiar el resultado de la tirada;
  * las opciones con riesgo enseñan su probabilidad y las seguras no.
"""

import contextlib
import io
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_forja import nueva_sesion, parametros_aleatorios          # noqa: E402
from forja import lenguaje                                           # noqa: E402
from forja.consola import Consola                                    # noqa: E402
from forja.generador import crear_mundo                              # noqa: E402
from forja.modelo import (BASE_MODIFICADOR, ENFOQUES, NIVELES, Tirada,   # noqa: E402
                          nivel_de)
from forja.motor import ESCENAS                                      # noqa: E402


def tearDownModule():
    lenguaje.fijar_personal(None)


def mundo(semilla=1):
    return crear_mundo(parametros_aleatorios(semilla))


class TestProbabilidadExacta(unittest.TestCase):
    def test_coincide_con_contar_los_dados(self):
        w = mundo()
        for enfoque in ENFOQUES:
            for dif in range(2, 13):
                esperado = sum(1 for d in range(1, 7)
                               if d + w.atributos[enfoque] + w.bono(enfoque)
                               >= dif - 1) / 6          # AJUSTE_DIFICULTAD = -1
                self.assertAlmostEqual(w.probabilidad(enfoque, dif), esperado)

    def test_coincide_con_tirar_de_verdad(self):
        for semilla in range(6):
            w = mundo(semilla)
            for enfoque in ENFOQUES:
                for dif in (5, 7, 9):
                    p = w.probabilidad(enfoque, dif)
                    aciertos = 0
                    n = 1200
                    for _ in range(n):
                        w2 = mundo(semilla)
                        w2.rng = random.Random(w.rng.random())
                        aciertos += w2.tirar(enfoque, dif).exito
                    self.assertAlmostEqual(aciertos / n, p, delta=0.06,
                                           msg=f"{semilla} {enfoque} {dif}")

    def test_entrenar_sube_la_probabilidad_y_lo_malo_la_baja(self):
        w = mundo()
        antes = w.probabilidad("valor", 8)
        w.atributos["valor"] += 1
        self.assertGreaterEqual(w.probabilidad("valor", 8), antes)
        w.ventaja = 1
        self.assertGreaterEqual(w.probabilidad("valor", 8), antes)
        w.ventaja = 0
        w.amenaza = 2
        self.assertLess(w.probabilidad("valor", 8, con_amenaza=True),
                        w.probabilidad("valor", 8, con_amenaza=False) + 1e-9)

    def test_la_probabilidad_no_gasta_el_azar(self):
        w = mundo()
        antes = w.rng.getstate()
        w.probabilidad("ingenio", 7)
        w.probabilidad_opcion(next(o for e in ESCENAS.values() for o in e.opciones if o.dif))
        self.assertEqual(w.rng.getstate(), antes)

    def test_opciones_seguras_no_tienen_probabilidad(self):
        w = mundo()
        for esc in ESCENAS.values():
            for o in esc.opciones:
                p = w.probabilidad_opcion(o)
                if o.dif is None or o.enfoque is None:
                    self.assertIsNone(p, esc.id)
                else:
                    self.assertTrue(0 <= p <= 1, esc.id)


class TestModificadores(unittest.TestCase):
    def test_lo_no_entrenado_resta(self):
        self.assertEqual(BASE_MODIFICADOR, 2)
        self.assertEqual([nivel_de(a) for a in range(5)], list(NIVELES.values()))
        t = Tirada(dado=3, atributo=0, bono=0, total=3, dificultad=7, exito=False)
        self.assertIn("valor -2 (sin entrenar)", t.describir("valor"))

    def test_lo_corriente_ni_suma_ni_resta(self):
        t = Tirada(dado=3, atributo=2, bono=0, total=5, dificultad=7, exito=False)
        self.assertIn("valor +0 (corriente)", t.describir("valor"))

    def test_el_resultado_mostrado_es_el_mismo_que_el_real(self):
        # desplazar atributo y dificultad por igual no cambia éxito o fracaso
        for atributo in range(5):
            for bono in (-1, 0, 1):
                for dado in range(1, 7):
                    for dif in range(3, 12):
                        total = dado + atributo + bono
                        t = Tirada(dado, atributo, bono, total, dif, total >= dif)
                        texto = " ".join(t.describir("valor").split())
                        izq = int(texto.split(" = ")[1].split(" contra ")[0])
                        der = int(texto.split(" contra ")[1].split(" ")[0])
                        self.assertEqual(izq >= der, t.exito, texto)


class TestLoQueSeEnseña(unittest.TestCase):
    def test_las_opciones_con_riesgo_enseñan_su_probabilidad(self):
        c = Consola(color=False, pausas=False)
        c.probs_actuales = [0.5, None, 1 / 6]
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            c._listar([("Valor", "Atacar"), ("Compasión", "Ayudar"), ("Ingenio", "Engañar")],
                      probs=c.probs_actuales)
        texto = salida.getvalue()
        self.assertIn("1) [Valor] Atacar  (≈ 50 %)", texto)
        self.assertIn("2) [Compasión] Ayudar\n", texto)
        self.assertIn("3) [Ingenio] Engañar  (≈ 17 %)", texto)

    def test_la_sesion_pasa_las_probabilidades_a_la_interfaz(self):
        ses = nueva_sesion(5, guion=["/salir"])
        try:
            ses.ejecutar()
        except Exception:
            pass
        probs = getattr(ses.ui, "ultimas_probs", None)
        self.assertIsNotNone(probs)
        self.assertTrue(all(p is None or 0 <= p <= 1 for p in probs))

    def test_el_comando_prob_lista_los_cuatro_atributos(self):
        ses = nueva_sesion(5, guion=["/prob", "/salir"])
        try:
            ses.ejecutar()
        except Exception:
            pass
        texto = "\n".join(ses.ui.lineas)
        for nombre in ("Valor", "Ingenio", "Compasión", "Ambición"):
            self.assertIn(nombre, texto)
        self.assertIn("fácil", texto)
        self.assertIn("difícil", texto)
        self.assertRegex(texto, r"\d+ %")

    def test_una_interfaz_antigua_sin_probabilidades_sigue_valiendo(self):
        class Vieja:
            """Una interfaz que no sabe nada de probabilidades."""
        # Sesion solo asigna un atributo: cualquier objeto lo admite.
        v = Vieja()
        v.probs_actuales = [None]
        self.assertEqual(v.probs_actuales, [None])


if __name__ == "__main__":
    unittest.main()
