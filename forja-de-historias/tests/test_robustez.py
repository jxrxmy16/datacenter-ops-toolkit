"""Pruebas de robustez: errores que una revisión adversarial encontró en el juego real.

Cada prueba reproduce un fallo concreto (cuelgues con la consola real, datos
perdidos al reproducir una partida, texto del jugador que rompe una expresión
regular...) para que no vuelva.
"""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_forja import nueva_sesion, parametros_aleatorios          # noqa: E402
from forja import lenguaje, libre                                    # noqa: E402
from forja.consola import Consola, analizar_linea, entero            # noqa: E402
from forja.libro import a_markdown, nombre_archivo, reemplazar_nombre   # noqa: E402
from forja.modelo import Tirada                                      # noqa: E402
from forja.sesion import Salir, Sesion, leer_guardado               # noqa: E402


def tearDownModule():
    lenguaje.fijar_personal(None)


def jugar(semilla, guion=None, final_guion=None, **kw):
    ses = nueva_sesion(semilla, guion=guion, **kw)
    ses.ui.estrategia = "prudente"
    ses.ui.final_guion = list(final_guion or [])
    final = ses.ejecutar()
    return ses, final


class TestNombresEnElLibro(unittest.TestCase):
    def test_la_barra_invertida_no_rompe_el_renombrado(self):
        for nuevo in ("Ana\\x", "\\1", "a\\", "C:\\Users\\yo", "\\g<0>"):
            texto = reemplazar_nombre("Hola, el Rey Marchito.", "el Rey Marchito", nuevo)
            self.assertEqual(texto, f"Hola, {nuevo}.")
            texto = reemplazar_nombre("Hola, Bruno.", "Bruno", nuevo)
            self.assertEqual(texto, f"Hola, {nuevo}.")

    def test_nombres_con_la_tambien_al_principio_de_frase(self):
        texto = "La Reina de Espinas ríe. Vi a la Reina de Espinas. —La Reina de Espinas—"
        nuevo = reemplazar_nombre(texto, "la Reina de Espinas", "Zarkon")
        self.assertNotIn("Reina", nuevo)
        self.assertTrue(nuevo.startswith("Zarkon ríe."))

    def test_el_nombre_del_archivo_conserva_las_letras_con_tilde(self):
        class W:                                      # lo mínimo que usa nombre_archivo
            params = mock.Mock(semilla=5020)

            def titulo(self):
                return "El cáliz de la señora Valcárcel"
        self.assertEqual(nombre_archivo(W()), "el-caliz-de-la-senora-valcarcel-5020.md")


class TestNumerosRaros(unittest.TestCase):
    def test_entero_solo_acepta_cifras_ascii_cortas(self):
        self.assertEqual(entero(" 12 "), 12)
        for malo in ("²", "①", "٣", "9" * 5000, "", "1.5", "-2", "x"):
            self.assertIsNone(entero(malo), malo)

    def test_analizar_linea_no_se_cae(self):
        for texto in ("²", "①", "9" * 5000, "atras ²", "volver ①"):
            analizar_linea(texto, 3)                  # basta con que no lance
        self.assertEqual(analizar_linea("²", 3), ("txt", "²"))


class TestConsolaConNotas(unittest.TestCase):
    def test_el_resultado_de_una_opcion_sin_enfoque_no_revienta(self):
        # Una decisión libre sobre una opción «Duda» con modificador tira un dado
        # sin enfoque propio; la consola con notas no debe caerse.
        c = Consola(color=False, notas=True, pausas=False)
        tirada = Tirada(dado=3, atributo=1, bono=0, total=4, dificultad=6, exito=False)
        with contextlib.redirect_stdout(io.StringIO()) as salida:
            c.resultado(["Algo ocurre."], tirada, None)
            c.interludio("huir a ciegas", ["Te echas atrás."], tirada, None)
        self.assertIn("dado 3 + ingenio 1", salida.getvalue())

    def test_partidas_completas_con_notas_en_la_consola_real(self):
        for semilla in range(12):
            ses = nueva_sesion(semilla)
            ses.ui = _ConsolaMuda(semilla)
            with contextlib.redirect_stdout(io.StringIO()):
                ses.ejecutar()


class _ConsolaMuda(Consola):
    """La consola real (con notas), pero eligiendo sola entre las opciones."""

    def __init__(self, semilla):
        super().__init__(color=False, notas=True, pausas=False)
        import random
        self._rng = random.Random(semilla)

    def leer(self, opciones, libre_ok=True, critica=False):
        # Prefiere las opciones «Duda» para recorrer el camino que fallaba.
        dudas = [i for i, (rotulo, _) in enumerate(opciones) if rotulo == "Duda"]
        pool = dudas if dudas and self._rng.random() < 0.7 else range(len(opciones))
        return ("op", self._rng.choice(list(pool)))

    def pedir_final(self):
        return ("fin",)


class TestMetaTrasElFinal(unittest.TestCase):
    def test_una_nota_tras_el_final_entra_en_el_libro_y_sobrevive_a_reproducir(self):
        ses, final = jugar(5, final_guion=["/nota Mi nota final"])
        self.assertIn("Mi nota final", a_markdown(ses.w, final))
        reproducida = Sesion(ses.ui.__class__(5, "prudente"), ses.params, tempfile.mkdtemp())
        reproducida.guardar_auto = False
        reproducida.reanudar(ses.registros)
        final2 = reproducida.ejecutar()
        self.assertEqual(a_markdown(reproducida.w, final2), a_markdown(ses.w, final))

    def test_un_renombrado_tras_el_final_sobrevive_a_reproducir(self):
        ses, final = jugar(5, final_guion=["/renombrar mentor Zarkon"])
        libro = a_markdown(ses.w, final)
        self.assertIn("Zarkon", libro)
        reproducida = Sesion(ses.ui.__class__(5, "prudente"), ses.params, tempfile.mkdtemp())
        reproducida.guardar_auto = False
        reproducida.reanudar(ses.registros)
        final2 = reproducida.ejecutar()
        self.assertEqual(a_markdown(reproducida.w, final2), libro)

    def test_renombrar_con_barra_invertida_no_tumba_el_libro(self):
        ses, final = jugar(5, final_guion=["/renombrar mentor Ana\\x", "/libro"])
        self.assertIn("Ana\\x", a_markdown(ses.w, final))

    def test_deshacer_no_pierde_notas_ni_renombrados(self):
        ses, final = jugar(5, guion=[0, 0, "/nota Se queda", "/renombrar aliado Maeron",
                                     "/atras"])
        self.assertTrue(any(r["k"] == "nota" for r in ses.registros))
        self.assertTrue(any(r["k"] == "renombrar" for r in ses.registros))
        libro = a_markdown(ses.w, final)
        self.assertIn("Se queda", libro)
        self.assertIn("Maeron", libro)


class TestAutoguardado(unittest.TestCase):
    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.carpeta, True)

    def _sesion(self, guion):
        ses = Sesion(__import__("forja.consola", fromlist=["Muda"]).Muda(
            5, "prudente", guion), parametros_aleatorios(5), self.carpeta)
        ses.guardar_auto = True
        return ses

    def test_el_autoguardado_refleja_lo_deshecho(self):
        ses = self._sesion([0, 0, 0, "/atras", "/salir"])
        with self.assertRaises(Salir):
            ses.ejecutar()
        datos = json.loads((self.carpeta / "auto.json").read_text(encoding="utf-8"))
        self.assertEqual(datos["acciones"], 2)
        self.assertEqual(len([r for r in datos["registros"] if r["k"] == "op"]), 2)


class TestGuardadosDañados(unittest.TestCase):
    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.carpeta, True)
        ses = nueva_sesion(5, guion=[0, 0])
        ses.carpeta = self.carpeta
        ses.guardar_auto = False
        try:
            ses.ui.estrategia = "primera"
            ses.ejecutar()
        except Exception:
            pass
        self.ruta = ses.guardar("bueno")
        self.datos = json.loads(self.ruta.read_text(encoding="utf-8"))

    def _con(self, cambio):
        d = json.loads(json.dumps(self.datos))
        cambio(d)
        ruta = self.carpeta / "x.json"
        ruta.write_text(json.dumps(d), encoding="utf-8")
        return leer_guardado(ruta)

    def test_el_guardado_bueno_se_lee(self):
        self.assertIsNotNone(leer_guardado(self.ruta))

    def test_se_rechaza_lo_que_no_se_puede_reproducir(self):
        malos = {
            "genero inexistente": lambda d: d["params"].update(genero="no-existe"),
            "registro sin k": lambda d: d["registros"].append({"i": 0}),
            "opcion no numerica": lambda d: d["registros"].append({"k": "op", "i": "a"}),
            "texto no es texto": lambda d: d["registros"].append({"k": "libre", "txt": 3, "i": 0}),
            "registro que no es dict": lambda d: d["registros"].append(7),
            "semilla no entera": lambda d: d["params"].update(semilla="x"),
            "sin acciones": lambda d: d.pop("acciones"),
        }
        for nombre, cambio in malos.items():
            self.assertIsNone(self._con(cambio), nombre)


class TestReintentarInterludios(unittest.TestCase):
    FRASE = "avanzar a ciegas"
    PREAMBULO = [0, 0, 0, 0, 0]

    def _jugar(self, semilla, con_reintento):
        guion = self.PREAMBULO + [self.FRASE] + (["/reintentar"] if con_reintento else [])
        ses = nueva_sesion(semilla, guion=guion, confirmaciones=["l", "l"])
        ses.ui.estrategia = "prudente"
        ses.ejecutar()
        return ses

    def test_otra_suerte_cambia_el_resultado_de_un_interludio(self):
        distintas = 0
        for semilla in range(25):
            normal = self._jugar(semilla, False)
            ints = [r for r in normal.registros if r["k"] == "int"]
            if not ints or not ints[0].get("azar"):
                continue
            retry = self._jugar(semilla, True)
            if [r.get("sal") for r in retry.registros if r["k"] == "int"][:1] != [1]:
                continue
            if retry.ui.interludios[-1] != normal.ui.interludios[0] or \
                    retry.w.instantanea() != normal.w.instantanea():
                distintas += 1
        self.assertGreater(distintas, 0)

    def test_el_reintento_es_determinista(self):
        a = self._jugar(7, True)
        b = self._jugar(7, True)
        self.assertEqual(a.w.instantanea(), b.w.instantanea())


class TestVigorEnInterludios(unittest.TestCase):
    def test_quedarse_sin_vigor_en_un_interludio_termina_la_partida(self):
        def agotador(w, esc, reg):
            w.vigor = 0
            return ["Caes rendido."], None, "valor"
        ses = nueva_sesion(5, guion=["mirar a mi alrededor"], confirmaciones=["l"])
        ses.ui.estrategia = "primera"
        with mock.patch.object(libre, "ejecutar", agotador):
            ses.ejecutar()
        self.assertLessEqual(ses.w.vigor, 0)
        self.assertEqual(len([r for r in ses.registros if r["k"] == "op"]), 0)
        self.assertTrue(ses.terminada)


if __name__ == "__main__":
    unittest.main()


class TestFrasesDudosas(unittest.TestCase):
    def setUp(self):
        self.carpeta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.carpeta, True)

    def _sesion(self, guion, **kw):
        from forja.consola import Muda
        ses = Sesion(Muda(5, "prudente", guion, **kw), parametros_aleatorios(5), self.carpeta)
        ses.guardar_auto = True
        return ses

    def _lineas(self):
        ruta = self.carpeta / "frases_dudosas.jsonl"
        return [json.loads(x) for x in ruta.read_text(encoding="utf-8").splitlines()] \
            if ruta.exists() else []

    def test_se_anota_lo_que_no_se_entendio_y_lo_que_querias(self):
        ses = self._sesion([0, 0, 0, 0, 0, "glorfindar plácidamente", 0],
                           intenciones=["descansar"])
        ses.ejecutar()
        lineas = self._lineas()
        self.assertEqual(len(lineas), 1)
        self.assertEqual((lineas[0]["frase"], lineas[0]["elegido"], lineas[0]["motivo"]),
                         ("glorfindar plácidamente", "descansar", "dudaba"))
        lenguaje.fijar_personal(None)

    def test_responder_ninguna_tambien_se_anota(self):
        ses = self._sesion([0, 0, 0, 0, 0, "zzzquux plonk", 0], intenciones=["ninguna"])
        ses.ejecutar()
        self.assertEqual([x["elegido"] for x in self._lineas()], [None])
        lenguaje.fijar_personal(None)

    def test_no_se_escribe_nada_sin_guardado(self):
        ses = self._sesion([0, 0, 0, 0, 0, "zzzquux plonk", 0], intenciones=["ninguna"])
        ses.guardar_auto = False
        ses.ejecutar()
        self.assertEqual(self._lineas(), [])

    def test_el_comando_frases_las_enseña(self):
        ses = self._sesion([0, 0, 0, 0, 0, "zzzquux plonk", "/frases", 0],
                           intenciones=["valor"])
        ses.ejecutar()
        self.assertTrue(any("zzzquux plonk" in x and "valor" in x for x in ses.ui.lineas))
        lenguaje.fijar_personal(None)

    def test_sin_frases_el_comando_lo_dice(self):
        ses = self._sesion([0, "/frases", 0])
        ses.ejecutar()
        self.assertTrue(any("Todavía no hay frases" in m for m in ses.ui.mensajes))
