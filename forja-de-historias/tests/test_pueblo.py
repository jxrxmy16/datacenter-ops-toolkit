"""Pruebas del pueblo vivo y del reloj del mundo.

Lo que garantizan:
  * el pueblo es una función pura de (semilla, día): pasar meses y preguntar «qué
    hay hoy» da lo mismo que ir día a día, y el acontecimiento acaba en calma;
  * crearlo no toca el azar de la historia (los mundos de antes no cambian);
  * nadie que se marchó o murió aparece después en una escena;
  * el regreso a casa cuenta el tiempo transcurrido, y el pueblo recuerda al héroe;
  * deshacer, guardar y cargar siguen siendo exactos con el reloj.
"""

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_forja import (ERRORES_GRAMATICALES, MINUSCULA_INICIAL,          # noqa: E402
                        jugar_partida, nueva_sesion, parametros_aleatorios)
from forja import lenguaje, pueblo                                          # noqa: E402
from forja.generador import crear_mundo                                     # noqa: E402
from forja.lexico import GENEROS                                            # noqa: E402
from forja.pueblo import DESEOS, EVENTOS, crear_pueblo                      # noqa: E402


def tearDownModule():
    lenguaje.fijar_personal(None)


def un_pueblo(semilla=3, genero="fantasia"):
    lex = GENEROS[genero]
    return crear_pueblo(semilla, lex["pueblo"], lex["nombres_f"], lex["nombres_m"])


class TestFases(unittest.TestCase):
    def test_el_dia_cero_cae_en_la_fase_pedida_y_todo_acaba_en_calma(self):
        for genero in GENEROS:
            for semilla in range(60):
                p = un_pueblo(semilla, genero)
                self.assertEqual(p.fase(0), p.fase_inicial, (genero, semilla))
                self.assertIn(p.evento, GENEROS[genero]["pueblo"]["eventos"])
                dias = [p.fase(d) for d in range(0, 80)]
                self.assertEqual(dias[-1], "calma")
                # una vez en calma, siempre en calma; y las fases van en orden
                orden = [f for f, _ in EVENTOS[p.evento]["fases"]]
                vistos = [orden.index(f) for f in dias]
                self.assertEqual(vistos, sorted(vistos), (genero, semilla))

    def test_el_pueblo_es_una_funcion_pura_del_dia(self):
        p = un_pueblo(5)
        a = [p.describir_fase(d) for d in (0, 3, 9, 40, 90)]
        for d in range(0, 91):                    # «vivir» todos los días no cambia nada
            p.describir_fase(d)
        b = [p.describir_fase(d) for d in (0, 3, 9, 40, 90)]
        self.assertEqual(a, b)

    def test_volver_meses_despues_esta_todo_limpio(self):
        visto = False
        for semilla in range(80):
            p = un_pueblo(semilla)
            if p.evento == "fiesta":
                visto = True
                self.assertIn("limpi", p.describir_fase(90).lower())
                self.assertNotIn("amanece", p.describir_fase(90))
        self.assertTrue(visto)

    def test_cada_texto_se_rellena_sin_marcadores_sueltos(self):
        for genero, lex in GENEROS.items():
            p = un_pueblo(1, genero)
            for ev in lex["pueblo"]["eventos"]:
                d = EVENTOS[ev]
                for fase, plantilla in d["texto"].items():
                    texto = p._formato(plantilla)
                    self.assertNotRegex(texto, r"[{}]", (genero, ev, fase))
                    self.assertNotRegex(texto, r"\b(de|a) el\b", texto)
                    self.assertNotRegex(texto, r"\btodo la\b|\bllena la\b", texto)
                self.assertNotRegex(p._formato(d["antes"]), r"[{}]")
                for fase, actos in d["actos"].items():
                    for acto in actos:
                        self.assertNotRegex(p._formato(acto), r"[{}]")


class TestIndependenciaDelAzar(unittest.TestCase):
    def test_crear_el_pueblo_no_toca_el_azar_de_la_historia(self):
        for semilla in range(5):
            p = parametros_aleatorios(semilla)
            con = crear_mundo(p)
            with mock.patch("forja.generador.crear_pueblo", return_value=None):
                sin = crear_mundo(p)
            self.assertEqual(con.rng.getstate(), sin.rng.getstate())
            self.assertEqual({r: str(x) for r, x in con.reparto.items()},
                             {r: str(x) for r, x in sin.reparto.items()})

    def test_recordar_tampoco(self):
        w = crear_mundo(parametros_aleatorios(4))
        antes = w.rng.getstate()
        w.pueblo.recordar("ayudo", 0, 2)
        self.assertEqual(w.rng.getstate(), antes)

    def test_misma_semilla_mismo_pueblo(self):
        self.assertEqual(un_pueblo(8).resumen(), un_pueblo(8).resumen())
        self.assertNotEqual(un_pueblo(8).resumen(), un_pueblo(9).resumen())


class TestVecinos(unittest.TestCase):
    def test_los_vecinos_son_distintos_y_no_repiten_nombre_con_el_reparto(self):
        for semilla in range(60):
            w = crear_mundo(parametros_aleatorios(semilla))
            nombres = [v.nombre for v in w.pueblo.vecinos]
            reparto = {x.nombre for x in w.reparto.values()}
            self.assertEqual(len(nombres), 8, semilla)
            self.assertEqual(len(set(nombres)), len(nombres), semilla)
            self.assertFalse(set(nombres) & reparto, semilla)

    def test_quien_se_va_o_muere_deja_de_estar(self):
        hubo = 0
        for semilla in range(120):
            p = un_pueblo(semilla)
            for v in p.vecinos:
                if v.muere_el >= 0:
                    self.assertTrue(v.mayor)
                    self.assertTrue(p.presente(v, v.muere_el - 1))
                    self.assertFalse(p.presente(v, v.muere_el))
                    hubo += 1
                if v.cumple_el >= 0 and DESEOS[v.deseo][2]:
                    self.assertFalse(p.presente(v, v.cumple_el))
        self.assertGreater(hubo, 0)

    def test_las_noticias_son_ordenadas_y_unicas_por_vecino(self):
        for semilla in range(60):
            p = un_pueblo(semilla)
            noticias = p.noticias(0, 120)
            self.assertEqual(noticias, sorted(noticias))
            textos = [t for _, t in noticias]
            self.assertEqual(len(textos), len(set(textos)))
            # lo que pasó entre dos fechas no se repite al sumar los tramos
            self.assertEqual(p.noticias(0, 40) + p.noticias(40, 120), noticias)

    def test_nunca_se_describe_a_un_ausente(self):
        for semilla in range(80):
            p = un_pueblo(semilla)
            for dia in range(0, 120, 3):
                texto = p.describir_fase(dia)
                for v in p.vecinos:
                    if not p.presente(v, dia):
                        self.assertIsNone(re.search(rf"\b{re.escape(v.nombre)}\b", texto),
                                          (semilla, dia))


class TestMemoria(unittest.TestCase):
    def test_los_vecinos_recuerdan_lo_que_hiciste(self):
        p = un_pueblo(2)
        nombres = p.recordar("ayudo", 0, 2)
        self.assertEqual(len(nombres), 2)
        v = p.quien_recuerda("ayudo", 5)
        self.assertIn(v.nombre, nombres)
        self.assertIsNone(p.quien_recuerda("robo", 5))

    def test_quien_recuerda_no_es_alguien_que_ya_no_esta(self):
        p = un_pueblo(2)
        p.recordar("ayudo", 0, 8)
        for v in p.vecinos:
            v.muere_el = 10
        self.assertIsNone(p.quien_recuerda("ayudo", 20))
        self.assertIsNotNone(p.quien_recuerda("ayudo", 5))

    def test_es_determinista(self):
        a, b = un_pueblo(6), un_pueblo(6)
        self.assertEqual(a.recordar("ayudo", 0, 3), b.recordar("ayudo", 0, 3))


class TestRelojEnLaHistoria(unittest.TestCase):
    def test_el_tiempo_pasa_de_forma_razonable(self):
        dias = []
        for semilla in range(120):
            w, final = jugar_partida(semilla)
            dias.append(w.dia)
        self.assertTrue(all(25 <= d <= 130 for d in dias), (min(dias), max(dias)))

    def test_descansar_y_caminar_cuestan_un_dia(self):
        base = nueva_sesion(5, guion=[0, 0, 0, 0, 0, "descansar un rato"],
                            confirmaciones=["l"])
        base.ui.estrategia = "prudente"
        base.ejecutar()
        otra = nueva_sesion(5, guion=[0, 0, 0, 0, 0], confirmaciones=["l"])
        otra.ui.estrategia = "prudente"
        otra.ejecutar()
        if any(r["k"] == "int" and r["clase"] == "descansar" for r in base.registros):
            self.assertEqual(base.w.dia, otra.w.dia + 1)

    def test_deshacer_devuelve_el_reloj(self):
        a = nueva_sesion(5, guion=[0, 0, 0, "avanzar a ciegas", "/atras", 0],
                         confirmaciones=["l", "l"])
        a.ui.estrategia = "prudente"
        a.ejecutar()
        b = nueva_sesion(5, guion=[0, 0, 0, 0], confirmaciones=["l"])
        b.ui.estrategia = "prudente"
        b.ejecutar()
        self.assertEqual(a.w.dia, b.w.dia)
        self.assertEqual(a.w.pueblo.resumen(), b.w.pueblo.resumen())

    def test_la_instantanea_incluye_el_reloj_y_el_pueblo(self):
        w, _ = jugar_partida(5)
        snap = w.instantanea()
        self.assertEqual(snap["dia"], w.dia)
        self.assertEqual(snap["pueblo"], w.pueblo.resumen())


class TestElRegreso(unittest.TestCase):
    def test_el_regreso_cuenta_el_tiempo_y_el_estado_del_pueblo(self):
        regresos = 0
        for semilla in range(150):
            w, final = jugar_partida(semilla)
            texto = "\n".join(final.parrafos)
            self.assertIsNone(ERRORES_GRAMATICALES.search(texto), semilla)
            self.assertIsNone(MINUSCULA_INICIAL.search(texto), semilla)
            self.assertEqual(w.avisos, [], semilla)
            if final.clave == "caida":
                self.assertNotIn("Han pasado", texto)
                continue
            self.assertRegex(texto, r"Han pasado (unos|unas|casi) ", semilla)
            regresos += 1
            if not w.b("hogar_perdido"):
                ev = EVENTOS[w.pueblo.evento]
                calma = w.pueblo._formato(ev["texto"]["calma"]).split(":")[0].split(";")[0]
                self.assertIn(calma, texto, semilla)
        self.assertGreater(regresos, 100)

    def test_si_el_hogar_se_pierde_se_cuenta_aparte(self):
        w, _ = jugar_partida(5)
        w.banderas.add("hogar_perdido")
        textos = pueblo.regreso(w)
        self.assertEqual(len(textos), 1)
        self.assertIn("escombros", textos[0])

    def test_ayudar_a_los_vecinos_deja_huella(self):
        ayudas = 0
        contados = 0
        for semilla in range(60):
            ses = nueva_sesion(semilla, guion=[2])      # «Ayudar a tus vecinos»
            ses.ui.estrategia = "prudente"
            final = ses.ejecutar()
            w = ses.w
            if final.clave == "caida" or w.b("hogar_perdido"):
                continue
            contados += 1
            recuerda = w.pueblo.quien_recuerda("ayudo", w.dia)
            texto = "\n".join(final.parrafos)
            if recuerda is not None:
                ayudas += 1
                self.assertIn("aún recuerda que le echaste una mano", texto, semilla)
                self.assertIn(recuerda.nombre, texto, semilla)
            else:
                self.assertNotIn("aún recuerda que le echaste una mano", texto, semilla)
        self.assertGreater(contados, 30)
        self.assertGreater(ayudas, contados // 2)

    def test_la_primera_escena_enseña_el_pueblo(self):
        for genero in GENEROS:
            for semilla in range(30):
                w = crear_mundo(parametros_aleatorios(semilla))
                if w.params.genero != genero:
                    continue
                w.etapa = 1
                texto = " ".join(w.renderizar(["{pueblo_hoy}"]))
                self.assertEqual(texto, w.pueblo.describir_fase(0))
                self.assertGreater(len(texto), 40)

    def test_mirar_a_la_gente_da_una_pincelada(self):
        ses = nueva_sesion(5, guion=["observar con calma"], confirmaciones=["l"])
        ses.ui.estrategia = "prudente"
        for semilla in range(40):
            ses = nueva_sesion(semilla, guion=["mirar a la gente con calma"],
                               confirmaciones=["l"])
            ses.ui.estrategia = "prudente"
            ses.ejecutar()
            if any("Observas a la gente" in " ".join(p) for _, p in ses.ui.interludios):
                return
        self.fail("ninguna observación mostró al pueblo")


class TestMezclaYPueblo(unittest.TestCase):
    def test_un_mundo_mezclado_tiene_el_pueblo_del_genero_principal(self):
        p = parametros_aleatorios(3)
        p.genero, p.mezcla = "ciencia_ficcion", ["fantasia"]
        w = crear_mundo(p)
        self.assertIn(w.pueblo.evento, GENEROS["ciencia_ficcion"]["pueblo"]["eventos"])
        self.assertNotIn("cosecha", [w.pueblo.evento])


if __name__ == "__main__":
    unittest.main()
