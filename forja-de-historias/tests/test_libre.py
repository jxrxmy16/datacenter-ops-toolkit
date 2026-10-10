"""Pruebas del texto libre, deshacer, reintentar, guardar/cargar y comandos.

Lo esencial que garantizan:

  * DESHACER es exacto: [a, b, /atras, c] deja el mundo idéntico a [a, c],
    hasta el último dado y la última palabra de la crónica.
  * CARGAR reproduce una partida guardada sin diferencias.
  * El texto libre no rompe la coherencia (nadie muerto actúa, etc.).
  * En los momentos críticos solo valen las opciones.
"""

import json
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_forja import (CARPETA_TEMPORAL, nueva_sesion,            # noqa: E402
                        parametros_aleatorios)
from forja.consola import Muda, analizar_linea                      # noqa: E402
from forja.lenguaje import analizar                                 # noqa: E402
from forja.libro import a_markdown, reemplazar_nombre              # noqa: E402
from forja.sesion import Salir, Sesion, leer_guardado   # noqa: E402

_RUTA_CORPUS = Path(__file__).parent / "datos" / "corpus_frases.json"
try:
    CORPUS = json.loads(_RUTA_CORPUS.read_text(encoding="utf-8"))
except (OSError, ValueError):             # sin el corpus, el fuzz usa unas pocas frases
    CORPUS = [{"frase": f, "clase": "valor"} for f in (
        "atacar al guardián", "mirar a mi alrededor", "hablar con el mentor",
        "descansar un rato", "salir del bosque con los ojos cerrados")]
FRASES_LIBRES = [d["frase"] for d in CORPUS if d["clase"] != "desconocida"]


def jugar_con_guion(semilla, guion, **kw):
    ses = nueva_sesion(semilla, guion=guion, **kw)
    ses.ui.estrategia = "prudente"
    final = ses.ejecutar()
    return ses, final


def foto(ses):
    return ses.w.instantanea()


class TestLineas(unittest.TestCase):
    def test_clasifica_lo_que_escribe_el_jugador(self):
        self.assertEqual(analizar_linea("2", 3), ("op", 1))
        self.assertEqual(analizar_linea("9", 3), ("mal", "9"))
        self.assertEqual(analizar_linea("/atras 2", 3), ("cmd", "atras", "2"))
        self.assertEqual(analizar_linea("/Guardar mi partida", 3),
                         ("cmd", "guardar", "mi partida"))
        self.assertEqual(analizar_linea("atras", 3), ("cmd", "atras", ""))
        self.assertEqual(analizar_linea("n", 3), ("cmd", "notas", ""))
        self.assertEqual(analizar_linea("q", 3), ("cmd", "salir", ""))
        self.assertEqual(analizar_linea("salir del bosque", 3),
                         ("txt", "salir del bosque"))
        self.assertEqual(analizar_linea("   ", 3), ("vacio",))


class TestTextoLibre(unittest.TestCase):
    def test_el_ejemplo_del_jugador(self):
        # Estación 6: se escribe «salir del bosque caminando con los ojos cerrados».
        frase = "salir del bosque caminando con los ojos cerrados"
        ses, _ = jugar_con_guion(5, [0, 0, 0, 0, 0, frase], confirmaciones=["l"])
        ints = [r for r in ses.registros if r["k"] == "int"]
        self.assertEqual(len(ints), 1)
        self.assertEqual(ints[0]["clase"], "moverse")
        self.assertEqual(ints[0]["dd"], 2)
        self.assertEqual(ints[0]["mods"], ["con los ojos cerrados"])
        self.assertTrue(any("ojos cerrados" in "".join(p)
                            for _, p in ses.ui.interludios))
        self.assertEqual(ses.w.avisos, [])

    def test_una_frase_que_encaja_resuelve_la_opcion(self):
        # Escena 1: «entrenar con la espada» encaja con la primera opción.
        ses, _ = jugar_con_guion(2, ["entrenar con mi espada hasta caer rendido"],
                                 confirmaciones=["s"])
        r = ses.registros[0]
        self.assertEqual(r["k"], "libre")
        self.assertEqual(r["i"], 0)

    def test_una_frase_incomprensible_se_rechaza_sin_gastar_nada(self):
        ses, _ = jugar_con_guion(2, ["asdf qwerty jajaja", 0])
        self.assertTrue(any("No he entendido" in m for m in ses.ui.mensajes))
        self.assertEqual(ses.registros[0]["k"], "op")

    def test_en_los_momentos_criticos_solo_hay_opciones(self):
        # Se busca una partida donde aparezca una escena crítica y se escribe texto.
        for semilla in range(60):
            ses = nueva_sesion(semilla, guion=[])
            ses.ui.estrategia = "prudente"
            ses.ejecutar()
            if any(c for _, c in ses.ui.escenas):
                break
        guion = []
        for ya, critica in ses.ui.escenas:
            guion.append("atacar con todas mis fuerzas" if critica else 0)
        # Re-juega: el texto en escenas críticas debe ser rechazado, no registrado.
        ses2 = nueva_sesion(semilla, guion=guion, confirmaciones=["s"] * 50)
        ses2.ui.estrategia = "prudente"
        try:
            ses2.ejecutar()
        except Exception:
            pass
        self.assertTrue(any("momento crítico" in m for m in ses2.ui.mensajes))

    def test_no_se_puede_hablar_con_los_muertos(self):
        for semilla in range(300):
            ses = nueva_sesion(semilla, estrategia="prudente")
            ses.ejecutar()
            w = ses.w
            muertos = [r for r in ("mentor", "aliado", "heraldo")
                       if not w.vivo(r)]
            if muertos:
                break
        else:
            self.skipTest("ninguna partida de prueba tuvo muertos")
        rol = muertos[0]
        w.etapa = 6
        nombre = w.reparto[rol].nombre
        r = analizar(f"hablar con {nombre}", w)
        self.assertIsNotNone(r.bloqueo)
        self.assertIn("ya no está", r.bloqueo)

    def test_las_llaves_del_jugador_no_rompen_las_plantillas(self):
        ses, _ = jugar_con_guion(
            4, [0, 0, 0, 0, 0, "mirar {mentor.nombre} {} {0} con calma", 0])
        self.assertEqual(ses.w.avisos, [])


class TestDeshacer(unittest.TestCase):
    def test_atras_equivale_a_no_haberlo_hecho(self):
        for semilla in (1, 7, 12, 30):
            a, _ = jugar_con_guion(semilla, [0, 1, "/atras", 2])
            b, _ = jugar_con_guion(semilla, [0, 2])
            self.assertEqual(foto(a), foto(b), f"semilla {semilla}")
            self.assertEqual([r["k"] for r in a.registros][:2],
                             [r["k"] for r in b.registros][:2])

    def test_atras_varias_acciones(self):
        a, _ = jugar_con_guion(9, [0, 1, 0, 1, "/atras 3", 0])
        b, _ = jugar_con_guion(9, [0, 0])
        self.assertEqual(foto(a), foto(b))

    def test_volver_a_una_accion(self):
        a, _ = jugar_con_guion(9, [0, 1, 0, 1, "/volver 2", 2])
        b, _ = jugar_con_guion(9, [0, 2])
        self.assertEqual(foto(a), foto(b))

    def test_deshacer_con_texto_libre_en_medio(self):
        guion = [0, 0, 0, 0, 0, "mirar a mi alrededor", "descansar un rato"]
        a, _ = jugar_con_guion(5, guion + ["/atras", 0], confirmaciones=["l", "l"])
        b, _ = jugar_con_guion(5, guion[:-1] + [0], confirmaciones=["l"])
        self.assertEqual(foto(a), foto(b))

    def test_sin_nada_que_deshacer(self):
        ses, _ = jugar_con_guion(3, ["/atras", 0])
        self.assertTrue(any("nada que deshacer" in m for m in ses.ui.mensajes))

    def test_atras_despues_del_final(self):
        # Se rectifica tras ver el final: la última acción se vuelve a decidir.
        ref = nueva_sesion(3, estrategia="primera")
        ref.ejecutar()
        n = len(ref.registros)
        ses = nueva_sesion(3, estrategia="primera")
        ses.ui.final_guion = ["/atras"]
        ses.ejecutar()
        self.assertEqual(len(ses.registros), n)           # la rehízo (misma opción)
        self.assertEqual(foto(ses), foto(ref))
        self.assertTrue(any("Vuelves atrás" in m for m in ses.ui.mensajes))


class TestReintentar(unittest.TestCase):
    def _con_azar(self):
        for semilla in range(100):
            ses, _ = jugar_con_guion(semilla, [])
            if any(r.get("azar") for r in ses.registros):
                return semilla
        self.fail("no hay partidas con tiradas")

    def test_reintentar_cambia_la_suerte_pero_es_determinista(self):
        semilla = self._con_azar()
        ses, _ = jugar_con_guion(semilla, [])
        # Primera acción con azar: se repite justo después con /reintentar.
        pasos = []
        for r in ses.registros:
            pasos.append(r.get("i", 0))
            if r.get("azar"):
                break
        guion = pasos + ["/reintentar"]
        a, _ = jugar_con_guion(semilla, guion)
        b, _ = jugar_con_guion(semilla, guion)
        self.assertEqual(foto(a), foto(b))
        self.assertTrue(any(r.get("sal") == 1 for r in a.registros))

    def test_otra_suerte_cambia_de_verdad_los_dados(self):
        distintos = 0
        probadas = 0
        for semilla in range(40):
            ses, _ = jugar_con_guion(semilla, [])
            pasos = []
            for r in ses.registros:
                pasos.append(r.get("i", 0))
                if r.get("azar"):
                    break
            else:
                continue
            probadas += 1
            base, _ = jugar_con_guion(semilla, pasos)
            otra, _ = jugar_con_guion(semilla, pasos + ["/reintentar"])
            if foto(base) != foto(otra):
                distintos += 1
        self.assertGreater(probadas, 10)
        self.assertGreater(distintos, probadas // 4)

    def test_reintentar_sin_azar_avisa(self):
        ses, _ = jugar_con_guion(2, [0, "/reintentar", 0])
        self.assertTrue(any("no dependió del azar" in m for m in ses.ui.mensajes))


class TestGuardados(unittest.TestCase):
    def test_guardar_y_cargar_reproduce_la_partida(self):
        guion = [0, 0, 0, 0, 0, "mirar a mi alrededor", 0]
        ses = nueva_sesion(6, guion=list(guion), confirmaciones=["l"])
        ses.ui.estrategia = "prudente"
        ses.ejecutar()
        ruta = ses.guardar("prueba")
        datos = leer_guardado(ruta)
        self.assertIsNotNone(datos)

        ses2 = nueva_sesion(6, guion=[])
        ses2.ui.estrategia = "prudente"
        ses2.params = type(ses.params)(**datos["params"])
        ses2.reanudar(datos["registros"])
        # El guardado ya contiene la partida entera: se reproduce y termina.
        ses2.ejecutar()
        self.assertEqual(foto(ses), foto(ses2))

    def test_un_guardado_danado_no_se_traga(self):
        ruta = CARPETA_TEMPORAL / "roto.json"
        ruta.write_text("{esto no es json", encoding="utf-8")
        self.assertIsNone(leer_guardado(ruta))
        self.assertIsNone(leer_guardado(CARPETA_TEMPORAL / "no_existe.json"))

    def test_cargar_a_mitad_de_partida(self):
        # Guarda tras 3 acciones, sigue jugando, carga y comprueba el retroceso.
        ses = nueva_sesion(8, guion=[0, 0, 0, "/guardar mitad", 1, 1, 1, "/cargar mitad", 2])
        ses.ui.estrategia = "prudente"
        ses.ejecutar()
        self.assertTrue(any("Guardado" in m for m in ses.ui.mensajes))
        ref = nueva_sesion(8, guion=[0, 0, 0, 2])
        ref.ui.estrategia = "prudente"
        ref.ejecutar()
        self.assertEqual(foto(ses), foto(ref))

    def test_cargar_una_partida_que_no_existe(self):
        ses = nueva_sesion(8, guion=["/cargar fantasma", 0])
        ses.ui.estrategia = "prudente"
        ses.ejecutar()
        self.assertTrue(any("No encuentro" in m for m in ses.ui.mensajes))


class TestRetoques(unittest.TestCase):
    def test_renombrar_cambia_el_nombre_en_adelante_y_en_el_libro(self):
        ses, final = jugar_con_guion(
            4, [0, 0, 0, 0, 0, "/renombrar mentor Zarkon", 0])
        w = ses.w
        self.assertEqual(w.reparto["mentor"].nombre, "Zarkon")
        libro = a_markdown(w, final)
        viejo = next(iter(w.renombres))
        self.assertNotIn(viejo, libro.replace("Zarkon", ""))
        self.assertIn("Zarkon", libro)

    def test_renombrar_respeta_articulos_y_contracciones(self):
        t = "Vence al Rey Marchito. El Rey Marchito cae. La sombra del Rey Marchito."
        out = reemplazar_nombre(t, "el Rey Marchito", "Zarkon")
        self.assertEqual(out, "Vence a Zarkon. Zarkon cae. La sombra de Zarkon.")

    def test_renombrar_sobrevive_a_deshacer(self):
        ses, _ = jugar_con_guion(
            4, [0, 0, "/renombrar aliado Bruno", 0, 0, "/atras", 1])
        self.assertEqual(ses.w.reparto["aliado"].nombre, "Bruno")

    def test_nota_aparece_en_el_libro(self):
        ses, final = jugar_con_guion(4, ["/nota esto me gusta", 0])
        self.assertIn("Nota del autor: esto me gusta", a_markdown(ses.w, final))

    def test_comandos_de_consulta(self):
        ses, _ = jugar_con_guion(
            4, [0, "/historial", "/estado", "/ayuda", "/partidas", "/confirmar",
                "/notas", "/zzz", 0])
        self.assertTrue(any("Vigor" in l or "vigor" in l for l in ses.ui.lineas))
        self.assertTrue(any("/atras" in l for l in ses.ui.lineas))
        self.assertTrue(any("No conozco el comando" in m for m in ses.ui.mensajes))

    def test_salir_lanza_salir(self):
        ses = nueva_sesion(4, guion=["/salir"])
        with self.assertRaises(Salir):
            ses.ejecutar()


class TestPartidasAlAzar(unittest.TestCase):
    """Fuzz: mezcla opciones, frases del corpus y comandos."""

    class UIAzar(Muda):
        def __init__(self, semilla):
            super().__init__(semilla)
            self.r = random.Random(semilla * 31 + 7)
            self.deshacer_restantes = 3
            self.pasos = 0

        def confirmar(self, interp, rotulo, etiqueta, permite_libre=False):
            return self.r.choice(["s", "s", "n", "l" if permite_libre else "s"])

        def leer(self, opciones, libre_ok=True, critica=False):
            self.pasos += 1
            if self.pasos > 400:
                return ("op", 0)
            x = self.r.random()
            if x < 0.30 and libre_ok:
                return ("txt", self.r.choice(FRASES_LIBRES))
            if x < 0.34 and self.deshacer_restantes > 0:
                self.deshacer_restantes -= 1
                return ("cmd", "atras", "")
            if x < 0.37:
                return ("cmd", "reintentar", "")
            if x < 0.39:
                return ("cmd", self.r.choice(["estado", "historial", "ayuda"]), "")
            if x < 0.40:
                return ("cmd", "nota", "una nota")
            return ("op", self.r.randrange(len(opciones)))

    def test_cien_partidas_mezclando_todo(self):
        for semilla in range(100):
            ui = self.UIAzar(semilla)
            ses = Sesion(ui, parametros_aleatorios(semilla), CARPETA_TEMPORAL)
            ses.guardar_auto = False
            final = ses.ejecutar()
            ctx = f"semilla {semilla}"
            self.assertEqual(ses.w.avisos, [], ctx)
            self.assertTrue(0 <= ses.w.vigor <= 9, ctx)
            for rol in ses.w.grupo:
                self.assertTrue(ses.w.vivo(rol), ctx)
            self.assertIsNotNone(final, ctx)

    def test_reproducir_las_acciones_da_el_mismo_mundo(self):
        for semilla in range(40):
            ui = self.UIAzar(semilla)
            ses = Sesion(ui, parametros_aleatorios(semilla), CARPETA_TEMPORAL)
            ses.guardar_auto = False
            ses.ejecutar()
            copia = Sesion(Muda(0), parametros_aleatorios(semilla), CARPETA_TEMPORAL)
            copia.guardar_auto = False
            copia.reanudar([dict(r) for r in ses.registros])
            copia.ejecutar()
            self.assertEqual(foto(ses), foto(copia), f"semilla {semilla}")


if __name__ == "__main__":
    unittest.main()
