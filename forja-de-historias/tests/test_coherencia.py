"""Pruebas de coherencia del intérprete y del relato (hallazgos de la revisión).

Cada una cubre un caso real que fallaba: bloqueos falsos por alias de entidad,
frases que elegían la opción contraria, personajes ausentes que se dejaban
tratar como presentes, y textos con la gramática o las plantillas rotas.
"""

import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_forja import nueva_sesion, parametros_aleatorios          # noqa: E402
from forja import lenguaje, libre                                    # noqa: E402
from forja.generador import crear_mundo                              # noqa: E402
from forja.lenguaje import analizar                                  # noqa: E402


def mundo(semilla, etapa):
    w = crear_mundo(parametros_aleatorios(semilla))
    w.etapa = etapa
    return w


def escena(**kw):
    base = dict(id="x", presentes=(), participan=(), urgente=False, critica=False)
    base.update(kw)
    return SimpleNamespace(**base)


def opcion(enfoque, tag=None):
    return SimpleNamespace(enfoque=enfoque, tag=tag)


class TestAliasDeEntidades(unittest.TestCase):
    def test_la_frase_estrella_nunca_se_bloquea(self):
        frase = "salir del bosque caminando con los ojos cerrados"
        bloqueados = [s for s in range(200)
                      if analizar(frase, mundo(s, 6), escena()).bloqueo]
        self.assertEqual(bloqueados, [])

    def test_los_modificadores_no_nombran_entidades(self):
        for s in range(60):
            r = analizar("caminar paso a paso por el pueblo", mundo(s, 1), escena())
            self.assertIsNone(r.bloqueo, s)
            r = analizar("seguir mi camino sin mirar atrás", mundo(s, 2), escena())
            self.assertIsNone(r.bloqueo, s)

    def test_camino_como_verbo_no_es_el_lugar(self):
        for s in range(30):
            r = analizar("camino hacia las afueras", mundo(s, 2), escena())
            self.assertNotIn("camino", r.entidades)

    def test_lo_descriptivo_de_un_nombre_no_identifica(self):
        # «ojos» está en «un troll de ojos vacíos» pero no es el guardián.
        for s in range(100):
            w = mundo(s, 6)
            self.assertNotIn("guardian", analizar("miro sus ojos", w, escena()).entidades)

    def test_el_sustantivo_y_los_nombres_propios_si_identifican(self):
        w = mundo(2, 6)
        alias = lenguaje._alias(w)
        self.assertEqual(alias["troll"], {"guardian"})
        self.assertEqual(alias["tomas"], {"mentor"})
        self.assertEqual(alias["valleclaro"], {"hogar"})
        self.assertEqual(alias["eclipse"], {"villano"})

    def test_lo_de_este_mundo_gana_a_la_lista_generica(self):
        # En ciencia ficción los esbirros son «los drones centinela»: «dron» no es el guardián.
        for s in range(60):
            w = mundo(s, 6)
            if "drones" in str(w.objetos["esbirros"]):
                self.assertEqual(lenguaje._alias(w)["drones"], {"esbirros"})
                r = analizar("atacar a los drones", w, escena(id="emboscada", urgente=True))
                self.assertIsNone(r.bloqueo)
                return
        self.fail("ningún mundo con drones")


class TestPresencia(unittest.TestCase):
    def test_el_villano_esta_lejos_salvo_en_su_escena(self):
        for s in range(20):
            w = mundo(s, 3)
            r = analizar(f"robarle a {w.reparto['villano'].nombre}", w, escena())
            self.assertIsNotNone(r.bloqueo, s)
            self.assertIn("lejos", r.bloqueo)
            r = analizar(f"robarle a {w.reparto['villano'].nombre}", w,
                         escena(presentes=("villano",)))
            self.assertIsNone(r.bloqueo, s)

    def test_hablar_de_un_ausente_con_quien_esta_no_se_bloquea(self):
        w = mundo(3, 4)
        mentor, villano = w.reparto["mentor"].nombre, w.reparto["villano"].nombre
        r = analizar(f"hablar con {mentor} sobre {villano}", w,
                     escena(presentes=("mentor",)))
        self.assertIsNone(r.bloqueo)

    def test_el_heraldo_no_esta_antes_de_la_llamada(self):
        w = mundo(3, 1)
        r = analizar(f"hablar con {w.reparto['heraldo'].nombre}", w, escena())
        self.assertIsNotNone(r.bloqueo)
        w.etapa = 2
        r = analizar(f"hablar con {w.reparto['heraldo'].nombre}", w, escena())
        self.assertIsNone(r.bloqueo)

    def test_el_mensaje_de_lugar_no_duplica_la_preposicion(self):
        visto = False
        for s in range(40):
            w = mundo(s, 5)
            lugar = str(w.lugares["hogar"]).split()[-1]
            r = analizar(f"volver a {lugar}", w, escena())
            if r.bloqueo and "Todavía no puedes ir" in r.bloqueo:
                visto = True
                self.assertNotRegex(r.bloqueo, r"\bir a a\b|\ba al\b|\ba a la\b|\ba a los\b")
        self.assertTrue(visto)

    def test_defender_al_compañero_no_es_alzar_la_mano_contra_el(self):
        w = mundo(3, 6)
        aliado = w.reparto["aliado"].nombre
        r = analizar(f"defender a {aliado} de los esbirros", w,
                     escena(presentes=("aliado",)))
        self.assertIsNone(r.bloqueo)

    def test_la_emergencia_no_deja_descansar(self):
        sesion = nueva_sesion(5, guion=[0, 0, 0, "descansar tranquilamente", 0, 0],
                              confirmaciones=["l"])
        sesion.ui.estrategia = "prudente"
        sesion.ejecutar()
        ints = [r for r in sesion.registros if r["k"] == "int"]
        self.assertFalse([r for r in ints if r["clase"] == "descansar"])


class TestEleccionDeOpcion(unittest.TestCase):
    def _elegir(self, frase, w, ops, etiquetas):
        r = analizar(frase, w, escena(), etiquetas, ops)
        return r.opcion

    def test_coincidir_solo_en_un_nombre_no_basta(self):
        w = mundo(3, 4)
        m = w.reparto["mentor"].nombre
        ops = [opcion("sombra"), opcion("valor")]
        etiquetas = [("Ambición", f"Esperar a que acaben y quedarte con lo que {m} deje caer"),
                     ("Valor", "Cargar contra los lobos sin pensarlo")]
        self.assertIsNone(self._elegir(f"ayudar a {m}", w, ops, etiquetas))

    def test_con_la_intencion_correcta_y_el_nombre_si_elige(self):
        w = mundo(3, 4)
        m = w.reparto["mentor"].nombre
        ops = [opcion("sombra"), opcion("compasion")]
        etiquetas = [("Ambición", f"Esperar a que acaben y quedarte con lo que {m} deje caer"),
                     ("Compasión", f"Cubrir a {m} mientras se repone")]
        self.assertEqual(self._elegir(f"ayudar a {m}", w, ops, etiquetas), 1)

    def test_una_evasiva_no_elige_confianza_ni_gratitud(self):
        w = mundo(3, 5)
        ops = [opcion(None, tag="confianza"), opcion("valor")]
        etiquetas = [("Confianza", "Dejar que Jonas interceda"),
                     ("Valor", "Forzar el paso por la fuerza")]
        for frase in ("huir", "rendirme, no cruzo", "negarme a cruzar"):
            self.assertIsNone(self._elegir(frase, w, ops, etiquetas), frase)


class TestTextosDelRelato(unittest.TestCase):
    ERRORES = re.compile(r"\b(?:de|a) el\b(?! \w+ de)", re.IGNORECASE)

    def test_las_pistas_respetan_las_contracciones(self):
        vistos = 0
        for s in range(80):
            w = mundo(s, 6)
            w.reparto["aliado"].traidor = True
            for clave, _, texto, _ in libre._pistas(w, None):
                render = w.renderizar([texto], ("mentor", "aliado", "villano"))[0]
                self.assertNotRegex(render, r"\b(de|a) el\b", f"{s}: {render}")
                vistos += 1
        self.assertGreater(vistos, 100)

    def test_los_modificadores_se_unen_sin_repetirse(self):
        m = libre._mods({"mods": ["Sin armas", "sin armas y sin luz"]})
        self.assertEqual(m, "sin armas")
        m = libre._mods({"mods": ["a ciegas", "descalza", "sin armas"]})
        self.assertEqual(m, "a ciegas, descalza y sin armas")
        self.assertEqual(libre._mods({"mods": []}), "")
        self.assertEqual(libre._mods({}), "")

    def test_los_interludios_de_movimiento_no_tartamudean(self):
        repetida = re.compile(r"\b(\w+) \1\b", re.IGNORECASE)
        for mods in ([], ["paso a paso"], ["con cuidado", "en silencio"], ["con paso firme"]):
            for s in range(30):
                w = mundo(s, 6)
                reg = {"clase": "moverse", "dd": 1, "mods": mods, "txt": "avanzar"}
                ps, _, _ = libre._moverse(w, None, reg)
                texto = " ".join(ps)
                self.assertNotRegex(texto, repetida, texto)
                self.assertNotIn("la historia te reclama", texto)

    def test_el_aliento_no_se_regala_con_el_vigor_al_maximo(self):
        for s in range(40):
            w = mundo(s, 6)
            w.vigor = 9
            reg = {"clase": "valor", "dd": 2, "mods": ["a ciegas"], "txt": "me lanzo"}
            for _ in range(5):
                ps, _, _ = libre._improvisar(w, None, reg)
                self.assertNotIn("aliento", " ".join(ps))
                w.vigor = 9

    def test_la_frase_del_jugador_no_se_repite_en_el_interludio(self):
        w = mundo(4, 6)
        reg = {"clase": "duda", "dd": 0, "mods": [], "txt": "¿Y si me escondo?"}
        for _ in range(20):
            ps, _, _ = libre._improvisar(w, None, reg)
            self.assertNotIn("escondo", " ".join(ps))
            self.assertNotIn("«", " ".join(ps))


if __name__ == "__main__":
    unittest.main()
