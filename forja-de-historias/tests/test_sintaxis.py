"""Pruebas de sintaxis del intérprete: perífrasis, negaciones y reglas con personajes.

Cada caso salió de la revisión adversarial o de una prueba a mano: frases corrientes
que el intérprete leía al revés («voy a esconderme» como un desplazamiento, «sin
armas ataco» como una evasiva, «protejo al aliado con mi escudo» como ambición).
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_forja import jugar_partida                                 # noqa: E402
from forja import lenguaje                                           # noqa: E402
from forja.lenguaje import analizar, conjugar                        # noqa: E402

_MUNDO = None


def mundo():
    global _MUNDO
    if _MUNDO is None:
        _MUNDO, _ = jugar_partida(3)
        _MUNDO.etapa = 6
    return _MUNDO


def clase(frase):
    return analizar(frase, mundo()).clase


def tearDownModule():
    lenguaje.fijar_personal(None)


class TestPerifrasis(unittest.TestCase):
    def test_el_auxiliar_no_lleva_la_intencion(self):
        for frase, esperada in (
                ("voy a esconderme", "duda"),
                ("voy a esconderme tras el barril", "duda"),
                ("voy a ayudarlo", "compasion"),
                ("pienso rendirme", "duda"),
                ("puedo esconderme aquí", "duda"),
                ("voy a atacar al guardián", "valor"),
                ("quiero descansar", "descansar")):
            self.assertEqual(clase(frase), esperada, frase)

    def test_sin_infinitivo_el_verbo_conserva_su_sentido(self):
        self.assertEqual(clase("voy a casa"), "moverse")
        self.assertEqual(clase("vuelvo a la aldea"), "moverse")
        self.assertEqual(clase("pienso en el mentor"), "observar")

    def test_los_infinitivos_con_pronombre_pegado_se_reconocen(self):
        for tok in ("esconderme", "ayudarlo", "atacarlos", "rendirse", "convencerlo"):
            self.assertTrue(lenguaje._es_infinitivo(tok), tok)
        for tok in ("casa", "guardian", "ayuda"):
            self.assertFalse(lenguaje._es_infinitivo(tok), tok)


class TestNegaciones(unittest.TestCase):
    def test_la_negacion_afecta_a_un_solo_verbo(self):
        self.assertEqual(clase("no ataco, hablo con él"), "hablar")
        self.assertEqual(clase("no me escondo, peleo"), "valor")
        self.assertEqual(clase("no robo nada, lo ayudo"), "compasion")

    def test_la_negacion_cruza_la_perifrasis(self):
        self.assertEqual(clase("no voy a huir"), "valor")
        self.assertEqual(clase("no pienso huir, me quedo y peleo"), "valor")

    def test_negaciones_enfaticas(self):
        self.assertEqual(clase("ni de broma me escondo, ataco"), "valor")

    def test_sin_armas_es_un_modificador_no_una_negacion(self):
        r = analizar("sin armas ataco", mundo())
        self.assertEqual(r.clase, "valor")
        self.assertGreater(r.dd, 0)
        r = analizar("sin ruido ataco al guardián", mundo())
        self.assertEqual(r.clase, "valor")
        self.assertLess(r.dd, 0)

    def test_sin_dudar_es_valor(self):
        self.assertEqual(clase("sin dudar me lanzo"), "valor")


class TestModificadoresOrdenados(unittest.TestCase):
    def test_tender_una_mano_no_es_con_una_mano(self):
        r = analizar("tiendo una mano al herido", mundo())
        self.assertEqual((r.clase, r.dd, r.mods_desc), ("compasion", 0, []))

    def test_con_una_mano_si(self):
        for frase in ("avanzo con una mano", "avanzo con una sola mano",
                      "pelear atándome una mano a la espalda"):
            self.assertGreater(analizar(frase, mundo()).dd, 0, frase)

    def test_cubrirse_las_espaldas_no_es_de_espaldas(self):
        self.assertEqual(analizar("me cubro las espaldas", mundo()).dd, 0)
        self.assertGreater(analizar("avanzo de espaldas", mundo()).dd, 0)

    def test_cerrar_los_ojos_es_ir_a_ciegas(self):
        self.assertEqual(analizar("cierro los ojos y avanzo", mundo()).dd, 2)
        self.assertEqual(analizar("avanzo con los ojos vendados", mundo()).dd, 2)

    def test_la_adyacencia_en_las_ventanas(self):
        norm = ["tiendo", "una", "mano", "al", "herido", "con", "calma"]
        self.assertIsNone(lenguaje._ventana(norm, ("con", "^una", "^mano")))
        norm = ["avanzo", "con", "una", "mano"]
        self.assertEqual(lenguaje._ventana(norm, ("con", "^una", "^mano")), [1, 2, 3])


class TestReglasConCompañeros(unittest.TestCase):
    def test_proteger_o_sacrificarse_no_es_ambicion(self):
        for frase in ("protejo al aliado con mi escudo",
                      "me sacrifico por el aliado",
                      "sacrificarme por ellos",
                      "uso mi escudo para cubrir al mentor",
                      "cambio de lugar con el aliado"):
            self.assertNotEqual(clase(frase), "sombra", frase)

    def test_usar_al_otro_de_escudo_si_lo_es(self):
        for frase in ("uso al aliado de escudo humano",
                      "sacrifico al aliado para ganar tiempo",
                      "ofrezco al heraldo como sacrificio pa salvarme yo"):
            self.assertEqual(clase(frase), "sombra", frase)


class TestAprendizajeSensato(unittest.TestCase):
    def setUp(self):
        lenguaje.fijar_personal(None)

    def tearDown(self):
        lenguaje.fijar_personal(None)

    def test_las_palabras_corrientes_no_se_aprenden(self):
        nuevas = lenguaje.aprender("quiero glorfindar ahora mejor siempre", "descansar",
                                   mundo())
        self.assertEqual(nuevas, ["glorfindar"[:-2]])
        self.assertEqual(clase("quiero ver el cielo ahora"), "observar")

    def test_un_fichero_personal_con_otra_forma_no_impide_arrancar(self):
        for basura in ([], "texto", 7, {"raices": []}, {"raices": {"valor": "x"}},
                       {"raices": {"valor": [1, None]}, "frases": []},
                       {"frases": {3: "valor"}}):
            lenguaje.fijar_personal(basura)             # no debe lanzar
            self.assertEqual(clase("atacar al guardián"), "valor")


class TestConjugacion(unittest.TestCase):
    def test_primera_persona_del_preterito(self):
        self.assertIn("bebi", conjugar("beb", "er"))
        self.assertIn("bebimos", conjugar("beb", "er"))
        self.assertIn("part" + "i", conjugar("part", "ir"))
        self.assertIn("ataque", conjugar("atac", "ar"))


if __name__ == "__main__":
    unittest.main()
