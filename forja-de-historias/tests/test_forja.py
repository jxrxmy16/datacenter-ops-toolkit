"""Pruebas de la Forja de Historias.

La más importante es `test_coherencia_en_partidas_aleatorias`: juega cientos de
historias con decisiones al azar y exige que ninguna rompa las reglas del
universo (nadie muerto actúa, nadie ausente acompaña, no quedan huecos en las
plantillas). Es la comprobación mecánica de que el relato "tiene lógica".
"""

import random
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from forja.consola import Muda                                   # noqa: E402
from forja.final import TITULOS                                  # noqa: E402
from forja.fuentes import FUENTES                                # noqa: E402
from forja.generador import crear_mundo, nombre_al_azar          # noqa: E402
from forja.gramatica import Nom                                  # noqa: E402
from forja.lexico import ARQUETIPOS, FALLAS, GENEROS, TONOS, TRAMAS  # noqa: E402
from forja.libro import a_markdown                               # noqa: E402
from forja.modelo import Params                                  # noqa: E402
from forja.motor import ESCENAS, PLAN, jugar                     # noqa: E402


def parametros_aleatorios(semilla):
    rng = random.Random(semilla)
    genero = rng.choice(list(GENEROS))
    pronombre = rng.choice(["f", "m", "n"])
    return Params(genero, rng.choice(list(TONOS)), rng.choice(list(TRAMAS)),
                  nombre_al_azar(genero, pronombre, rng), pronombre,
                  rng.choice(list(ARQUETIPOS)), rng.choice(list(FALLAS)),
                  semilla)


def jugar_partida(semilla, estrategia="azar"):
    w = crear_mundo(parametros_aleatorios(semilla))
    final = jugar(w, Muda(semilla, estrategia))
    return w, final


def texto_completo(w):
    partes = []
    for cap in w.cronica:
        for b in cap.bloques:
            partes += b.texto + [b.eleccion or ""] + b.resultado
    return "\n".join(partes)


# Una frase que empieza en minúscula casi siempre es un `.Cap` olvidado.
MINUSCULA_INICIAL = re.compile(r"(?m)(?:^|[.!?] )[a-záéíóúñ]")

# Errores típicos de plantilla: preposición duplicada o contracción mal hecha.
ERRORES_GRAMATICALES = re.compile(
    r"\b(?:a al|de del|de el|a el|al a|del de|en en|que que)\b|[{}]")


class TestGramatica(unittest.TestCase):
    def test_declinacion(self):
        n = Nom("el núcleo de datos")
        self.assertEqual(n.de, "del núcleo de datos")
        self.assertEqual(n.a, "al núcleo de datos")
        self.assertEqual(n.Cap, "El núcleo de datos")
        self.assertEqual(n.lo, "lo")
        m = Nom("la Corona de Ceniza")
        self.assertEqual(m.de, "de la Corona de Ceniza")
        self.assertEqual(m.a, "a la Corona de Ceniza")
        self.assertEqual((m.lo, m.el, m.o), ("la", "ella", "a"))

    def test_indefinido_a_definido(self):
        self.assertEqual(Nom("una daga rúnica").ya, "la daga rúnica")
        self.assertEqual(Nom("un amuleto de plata").ya, "el amuleto de plata")
        self.assertEqual(Nom("el dron").ya, "el dron")


class TestContenido(unittest.TestCase):
    def test_el_plan_solo_cita_escenas_existentes(self):
        for etapa, pasos in PLAN.items():
            for _, ids in pasos:
                for i in ids:
                    self.assertIn(i, ESCENAS)
                    self.assertEqual(ESCENAS[i].etapa, etapa, i)

    def test_todas_las_fuentes_citadas_existen(self):
        for esc in ESCENAS.values():
            for clave, detalle in esc.fuentes:
                self.assertIn(clave, FUENTES, esc.id)
                self.assertTrue(detalle, esc.id)

    def test_toda_escena_tiene_fuentes_y_opciones(self):
        for esc in ESCENAS.values():
            self.assertTrue(esc.fuentes, f"{esc.id} no cita fuentes")
            self.assertTrue(esc.opciones, f"{esc.id} no tiene opciones")

    def test_los_lexicos_tienen_las_mismas_claves(self):
        claves = set(next(iter(GENEROS.values())))
        for nombre, lex in GENEROS.items():
            self.assertEqual(set(lex), claves, nombre)
            for f in lex["inspiracion"]:
                self.assertIn(f, FUENTES)
            for trama in TRAMAS:
                self.assertIn(trama, lex["problema"], nombre)


class TestMotor(unittest.TestCase):
    def test_misma_semilla_misma_historia(self):
        a, fa = jugar_partida(123)
        b, fb = jugar_partida(123)
        self.assertEqual(texto_completo(a), texto_completo(b))
        self.assertEqual(fa.clave, fb.clave)

    def test_semillas_distintas_historias_distintas(self):
        textos = {texto_completo(jugar_partida(s)[0]) for s in range(60)}
        self.assertEqual(len(textos), 60)

    def test_coherencia_en_partidas_aleatorias(self):
        for semilla in range(400):
            w, final = jugar_partida(semilla)
            contexto = f"semilla {semilla}"
            self.assertEqual(w.avisos, [], contexto)
            self.assertTrue(0 <= w.vigor <= 9, contexto)
            self.assertFalse(w.grupo - {"mentor", "aliado"}, contexto)
            for rol in w.grupo:
                self.assertTrue(w.vivo(rol), f"{contexto}: {rol} muerto en el grupo")
            self.assertIsNone(ERRORES_GRAMATICALES.search(texto_completo(w)),
                              f"{contexto}: {ERRORES_GRAMATICALES.search(texto_completo(w))}")
            self.assertIsNone(MINUSCULA_INICIAL.search(texto_completo(w)),
                              f"{contexto}: frase en minúscula")
            self.assertEqual(w.cronica[-1].etapa, 12, contexto)

    def test_estrategias_extremas_tambien_terminan(self):
        for estrategia in ("primera", "ultima"):
            for semilla in range(100):
                w, final = jugar_partida(semilla, estrategia)
                self.assertEqual(w.avisos, [], f"{estrategia} {semilla}")
                self.assertIn(final.clave, TITULOS)

    def test_hay_variedad_de_finales(self):
        finales = Counter(jugar_partida(s)[1].clave for s in range(400))
        self.assertGreaterEqual(len(finales), 5, finales)

    def test_quien_muere_no_vuelve_a_actuar(self):
        # El aviso del renderizador cubre esto; aquí se comprueba además que
        # los muertos nunca figuran entre quienes viajan con el héroe.
        for semilla in range(200):
            w, _ = jugar_partida(semilla)
            for rol, p in w.reparto.items():
                if not p.vivo:
                    self.assertNotIn(rol, w.grupo)

    def test_el_traidor_es_una_decision_del_mundo_no_del_azar_tardio(self):
        # Lo decide crear_mundo, antes de jugar: es siempre el mismo para una
        # misma semilla, juegue lo que juegue el jugador.
        p = parametros_aleatorios(5)
        self.assertEqual(crear_mundo(p).reparto["aliado"].traidor,
                         crear_mundo(p).reparto["aliado"].traidor)


class TestLibro(unittest.TestCase):
    def test_el_libro_incluye_capitulos_y_bibliografia(self):
        w, final = jugar_partida(11)
        md = a_markdown(w, final)
        self.assertTrue(md.startswith("# "))
        self.assertIn("## Capítulo 1.", md)
        self.assertIn("## Capítulo 12.", md)
        self.assertIn("## Notas y fuentes", md)
        self.assertIn(FUENTES[w.fuentes_usadas[0]].cita, md)


if __name__ == "__main__":
    unittest.main()
