"""Pruebas de la mezcla de géneros y de la premisa libre del mundo.

Garantizan que:
  * un mundo mezclado se juega entero, sin avisos de coherencia ni errores de
    gramática, para TODAS las combinaciones de géneros;
  * sin mezcla el mundo es idéntico al de antes (los guardados antiguos siguen);
  * la premisa del jugador se lee con prudencia (se enseña lo entendido) y los
    nombres que pone se usan, también en el libro.
"""

import contextlib
import io
import itertools
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_forja import (ERRORES_GRAMATICALES, MINUSCULA_INICIAL,       # noqa: E402
                        nueva_sesion, texto_completo)
from forja import contexto, lenguaje                                    # noqa: E402
from forja.consola import Consola                                       # noqa: E402
from forja.generador import _lugar_con_nombre, crear_mundo              # noqa: E402
from forja.lexico import (ARQUETIPOS, FALLAS, GENEROS, TONOS, TRAMAS,   # noqa: E402
                          mezclar_generos)
from forja.libro import a_markdown                                      # noqa: E402
from forja.modelo import Params                                         # noqa: E402
from forja.sesion import leer_guardado                                  # noqa: E402


def tearDownModule():
    lenguaje.fijar_personal(None)


def params(genero, semilla=1, mezcla=(), contexto_="", nombres=None, trama="monstruo"):
    rng = random.Random(semilla)
    return Params(genero, rng.choice(list(TONOS)), trama, "Ana", "f",
                  rng.choice(list(ARQUETIPOS)), rng.choice(list(FALLAS)), semilla,
                  list(mezcla), contexto_, dict(nombres or {}))


def jugar(p, estrategia="azar"):
    ses = nueva_sesion(p.semilla, estrategia, params=p)
    final = ses.ejecutar()
    return ses, final


class TestMezclarLexicos(unittest.TestCase):
    def test_sin_secundarios_es_el_mismo_lexico(self):
        self.assertIs(mezclar_generos("noir"), GENEROS["noir"])
        self.assertIs(mezclar_generos("noir", ["noir", "desconocido"]), GENEROS["noir"])

    def test_la_unión_conserva_todo_y_el_principal_domina(self):
        m = mezclar_generos("fantasia", ["ciencia_ficcion"])
        for clave, valor in GENEROS["fantasia"].items():
            if isinstance(valor, list):
                self.assertTrue(set(valor) | set(GENEROS["ciencia_ficcion"][clave]) <= set(m[clave]))
        propios = sum(1 for x in m["guarida"] if x in GENEROS["fantasia"]["guarida"])
        ajenos = len(m["guarida"]) - propios
        self.assertEqual(propios, 2 * ajenos)
        self.assertEqual(m["nombre"], "Fantasía épica + Ciencia ficción")
        self.assertEqual(m["problema"], GENEROS["fantasia"]["problema"])

    def test_el_original_no_se_modifica(self):
        antes = json.dumps(GENEROS, sort_keys=True)
        mezclar_generos("noir", ["terror", "fantasia"])
        self.assertEqual(json.dumps(GENEROS, sort_keys=True), antes)


class TestMundosMezclados(unittest.TestCase):
    def test_sin_mezcla_el_mundo_no_cambia(self):
        a = crear_mundo(params("noir", 9))
        b = crear_mundo(params("noir", 9, mezcla=[]))
        self.assertEqual(a.instantanea(), b.instantanea())

    def test_los_guardados_antiguos_siguen_valiendo(self):
        viejo = {"genero": "noir", "tono": "equilibrado", "trama": "monstruo",
                 "nombre": "Ana", "pronombre": "f", "arquetipo": list(ARQUETIPOS)[0],
                 "falla": list(FALLAS)[0], "semilla": 4}
        p = Params(**viejo)
        self.assertEqual((p.mezcla, p.contexto, p.nombres), ([], "", {}))
        crear_mundo(p)

    def test_todas_las_combinaciones_se_juegan_enteras(self):
        generos = list(GENEROS)
        combos = [(g, [s]) for g in generos for s in generos if s != g]
        combos += [(g, [a, b]) for g in generos
                   for a, b in itertools.combinations([s for s in generos if s != g], 2)]
        for genero, mezcla in combos:
            for semilla in (1, 2, 3):
                for trama in TRAMAS:
                    p = params(genero, semilla, mezcla, trama=trama)
                    ses, final = jugar(p)
                    w = ses.w
                    ctx = f"{genero}+{mezcla} semilla {semilla} {trama}"
                    self.assertEqual(w.avisos, [], ctx)
                    texto = texto_completo(w)
                    self.assertIsNone(ERRORES_GRAMATICALES.search(texto), ctx)
                    self.assertIsNone(MINUSCULA_INICIAL.search(texto), ctx)

    def test_aparecen_elementos_de_los_secundarios(self):
        vistos = set()
        for semilla in range(60):
            w = crear_mundo(params("fantasia", semilla, ["ciencia_ficcion"]))
            vistos.add("ciencia_ficcion" if str(w.objetos["guardian"]) in
                       GENEROS["ciencia_ficcion"]["guardianes"] else "fantasia")
        self.assertEqual(vistos, {"fantasia", "ciencia_ficcion"})

    def test_el_libro_dice_la_mezcla_y_la_premisa(self):
        p = params("noir", 5, ["fantasia"], "Una ciudad de canales con magia vieja.")
        ses, final = jugar(p)
        libro = a_markdown(ses.w, final)
        self.assertIn("Noir + Fantasía épica", libro)
        self.assertIn("Una ciudad de canales con magia vieja.", libro)

    def test_los_alias_del_interprete_siguen_las_palabras_del_mundo_mezclado(self):
        for semilla in range(80):
            w = crear_mundo(params("fantasia", semilla, ["ciencia_ficcion"]))
            if "androide" in str(w.objetos["guardian"]):
                self.assertIn("guardian", lenguaje._alias(w)["androide"])
                return
        self.fail("ningún mundo con androide")


class TestNombresPropios(unittest.TestCase):
    def test_se_aplican_a_los_personajes_y_al_lugar(self):
        p = params("fantasia", 3, nombres={"villano": "Zarkon", "mentor": "Sibila",
                                           "hogar": "el pueblo de Aguasmuertas"})
        w = crear_mundo(p)
        self.assertEqual(w.reparto["villano"].nombre, "Zarkon")
        self.assertEqual(w.reparto["mentor"].nombre, "Sibila")
        self.assertEqual(str(w.lugares["hogar"]), "el pueblo de Aguasmuertas")
        self.assertEqual(w.titulo(), "La sombra de Zarkon")

    def test_el_titulo_conserva_el_articulo_del_hogar_original(self):
        w = crear_mundo(params("fantasia", 3, nombres={"hogar": "Aguasmuertas"}))
        self.assertTrue(str(w.lugares["hogar"]).endswith(" Aguasmuertas"))
        self.assertNotEqual(str(w.lugares["hogar"]), "Aguasmuertas")

    def test_lugar_con_nombre(self):
        casos = [("la aldea de Brumahonda", "Aguasmuertas", "la aldea de Aguasmuertas"),
                 ("el barrio de las Tres Chimeneas", "Sur", "el barrio de Sur"),
                 ("la estación Horizonte-9", "Kepler", "la estación Kepler"),
                 ("la aldea de Brumahonda", "el pueblo de Ceniza", "el pueblo de Ceniza")]
        for actual, nuevo, esperado in casos:
            self.assertEqual(_lugar_con_nombre(actual, nuevo), esperado)

    def test_una_partida_con_nombres_se_juega_sin_avisos(self):
        for semilla in range(8):
            p = params("noir", semilla, ["terror"], "x",
                       {"villano": "Zarkon", "aliado": "Tano", "heraldo": "Lis",
                        "hogar": "la ciudad de Neblina"})
            ses, _ = jugar(p)
            self.assertEqual(ses.w.avisos, [], semilla)
            self.assertIsNone(ERRORES_GRAMATICALES.search(texto_completo(ses.w)), semilla)


class TestLeerPremisa(unittest.TestCase):
    TEXTO = ("Una ciudad de canales con magia vieja y detectives cansados bajo la lluvia. "
             "El pueblo se llama Aguasmuertas y el villano se llama Zarkon. Tono oscuro.")

    def test_saca_generos_tono_y_nombres(self):
        r = contexto.leer_premisa(self.TEXTO, "noir")
        self.assertEqual(r["mezcla"], ["fantasia"])
        self.assertEqual(r["tono"], "sombrio")
        self.assertEqual(r["nombres"], {"hogar": "el pueblo de Aguasmuertas",
                                        "villano": "Zarkon"})

    def test_el_genero_principal_no_se_mezcla_consigo_mismo(self):
        r = contexto.leer_premisa("magia, dragones y un reino antiguo", "fantasia")
        self.assertEqual(r["mezcla"], [])

    def test_como_mucho_dos_secundarios_los_mas_mencionados(self):
        r = contexto.leer_premisa("una nave con un robot y un androide, un fantasma, "
                                  "un detective", "fantasia")
        self.assertEqual(r["mezcla"][0], "ciencia_ficcion")
        self.assertEqual(len(r["mezcla"]), 2)

    def test_no_inventa_nada_de_un_texto_sin_pistas(self):
        r = contexto.leer_premisa("Quiero algo tranquilo con mucha amistad.", "noir")
        self.assertEqual((r["mezcla"], r["tono"], r["nombres"]), ([], None, {}))
        self.assertEqual(contexto.leer_premisa("", "noir"),
                         {"mezcla": [], "tono": None, "nombres": {}})

    def test_los_nombres_necesitan_decir_a_quien_nombran(self):
        self.assertEqual(contexto.nombres_en("Alguien llamado Pepe vive allí"), {})
        self.assertEqual(contexto.nombres_en("Mi mentor, una vieja maga llamada Sibila"),
                         {"mentor": "Sibila"})
        self.assertEqual(contexto.nombres_en("la aldea llamada Piedra Gris"),
                         {"hogar": "la aldea de Piedra Gris"})

    def test_las_palabras_no_se_confunden_por_el_prefijo(self):
        # «navegante» no es «nave»; «cyberpunk» sí empieza por «cyber».
        self.assertEqual(contexto.generos_en("un navegante en el mar"), [])
        self.assertEqual(contexto.generos_en("un barrio cyberpunk"), ["ciencia_ficcion"])

    def test_texto_enorme_o_raro_no_rompe(self):
        contexto.leer_premisa("a" * 100000)
        contexto.leer_premisa("¿¿¿ llamado " * 2000)
        contexto.leer_premisa(None)


class TestGuardadosConMezcla(unittest.TestCase):
    def test_se_guardan_y_se_leen(self):
        carpeta = Path(tempfile.mkdtemp())
        p = params("noir", 5, ["fantasia"], "premisa", {"villano": "Zarkon"})
        ses = nueva_sesion(5, params=p)
        ses.carpeta = carpeta
        ses.guardar_auto = False
        ses.ui.estrategia = "primera"
        ses.ejecutar()
        ruta = ses.guardar("mezcla")
        datos = leer_guardado(ruta)
        self.assertIsNotNone(datos)
        self.assertEqual(datos["params"]["mezcla"], ["fantasia"])
        self.assertEqual(Params(**datos["params"]).nombres, {"villano": "Zarkon"})

    def test_un_guardado_con_mezcla_invalida_se_rechaza(self):
        carpeta = Path(tempfile.mkdtemp())
        ses = nueva_sesion(5, params=params("noir", 5, ["fantasia"]))
        ses.carpeta = carpeta
        ses.guardar_auto = False
        ses.ui.estrategia = "primera"
        ses.ejecutar()
        datos = json.loads(ses.guardar("x").read_text(encoding="utf-8"))
        for mal in (["no-existe"], "fantasia", [3]):
            datos["params"]["mezcla"] = mal
            ruta = carpeta / "mal.json"
            ruta.write_text(json.dumps(datos), encoding="utf-8")
            self.assertIsNone(leer_guardado(ruta), mal)


class TestMenuMultiple(unittest.TestCase):
    OPCIONES = [("a", "Uno", ""), ("b", "Dos", ""), ("c", "Tres", "")]

    def _multi(self, *entradas):
        pend = list(entradas)
        c = Consola(color=False, pausas=False)
        with mock.patch.object(Consola, "_leer_linea", side_effect=lambda p="> ": pend.pop(0)), \
                contextlib.redirect_stdout(io.StringIO()):
            return c.multi("¿Cuáles?", self.OPCIONES)

    def test_formas_de_responder(self):
        self.assertEqual(self._multi(""), [])
        self.assertEqual(self._multi("no"), [])
        self.assertEqual(self._multi("1,3"), ["a", "c"])
        self.assertEqual(self._multi("2 3"), ["b", "c"])
        self.assertEqual(self._multi("1 y 2"), ["a", "b"])
        self.assertEqual(self._multi("3,3,1"), ["c", "a"])

    def test_pide_de_nuevo_si_no_vale(self):
        self.assertEqual(self._multi("9", "x", "²", "2"), ["b"])


if __name__ == "__main__":
    unittest.main()
