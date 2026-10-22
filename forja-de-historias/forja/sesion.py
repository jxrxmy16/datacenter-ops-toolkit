"""Sesión de juego: grabación de acciones, deshacer, guardados y comandos.

La idea que lo hace todo posible: la partida es DETERMINISTA. Dada la misma
configuración (semilla incluida) y la misma lista de acciones, el motor produce
exactamente la misma historia, hasta el último dado. Así que "guardar" es
guardar esa lista, "deshacer" es quitar la última acción y reconstruir, y
"volver a otro punto" es truncar la lista. No hay copias del mundo que puedan
quedar desincronizadas.

Registros (uno por acción del jugador; los dos últimos son «meta»):
  {"k": "op",    "i": n}                         eligió la opción n
  {"k": "libre", "txt", "i", "dd", "mods"}       frase libre resuelta como la opción i
  {"k": "int",   "txt", "clase", "ent", "dd", "mods"}   interludio (la escena sigue)
  {"k": "renombrar", "rol", "nombre"}            /renombrar
  {"k": "nota", "txt"}                           /nota
Campos opcionales: "sal" (otra suerte), "azar" (hubo tiradas), "cap", "lbl".
"""

import json
import re
import time
from pathlib import Path

from . import lenguaje, libre, motor
from .consola import entero
from .generador import crear_mundo
from .lenguaje import analizar
from .libro import guardar as guardar_libro
from .lexico import ARQUETIPOS, FALLAS, GENEROS, TONOS, TRAMAS
from .modelo import BASE_MODIFICADOR, ENFOQUES, ETIQUETAS, Params, nivel_de

VERSION_GUARDADO = 1
ACCIONES = ("op", "libre", "int")
META = ("renombrar", "nota")
ROLES_RENOMBRABLES = {
    "mentor": "mentor", "maestro": "mentor", "maestra": "mentor",
    "aliado": "aliado", "aliada": "aliado",
    "heraldo": "heraldo", "mensajero": "heraldo",
    "villano": "villano", "villana": "villano", "enemigo": "villano",
    "heroe": "heroe", "héroe": "heroe", "yo": "heroe", "protagonista": "heroe",
}

AYUDA = """\
Escribe con tus palabras lo que quieres hacer; con «?» te enseño ideas (también vale el número de una opción). En los momentos críticos solo hay opciones, como en un RPG.
  Ejemplos: «atacar al guardián por sorpresa», «hablar con el mentor», «mirar a mi alrededor», «cruzar el puente con los ojos cerrados».
  Si lo que escribes encaja con una opción, te digo cómo lo he entendido y puedes corregirme. «Con cuidado» o «en silencio» facilitan; «a ciegas» o «sin armas» dificultan pero, si sale bien, te dan aliento.

Comandos (empiezan por /):
  /atras [n]          deshace tus últimas n acciones (por defecto 1)
  /historial          lista tus acciones, numeradas
  /volver N           vuelve a justo antes de la acción N
  /reintentar         repite la última acción con otra suerte
  /guardar [nombre]   guarda la partida
  /cargar [nombre]    la recupera
  /partidas           lista tus guardados (hay uno automático, «auto»)
  /corregir           si te malinterpreté tu última frase, me dices qué querías decir
  /olvidar            borra lo que me hayas ido enseñando de tu forma de escribir
  /renombrar X nombre cambia el nombre de mentor, aliado, heraldo, villano o héroe
  /nota texto         añade una nota tuya al libro
  /estado             atributos, vigor y compañía
  /libro              guarda ahora el libro de tu historia
  /notas              muestra u oculta las fuentes de cada escena
  /confirmar          activa o desactiva la confirmación de lo que entiendo
  /modo               alterna entre escribir libremente y ver siempre la lista de opciones
  /dados              enseña u oculta la tirada de dado de cada acción arriesgada
  /prob               tus probabilidades de éxito según lo que has entrenado
  /frases             lista las frases que no supe leer (para ayudarme a aprender)
  /salir              sale (la partida queda guardada en «auto»)"""

NOMBRE_CLASE = {
    "valor": "un acto de valor", "ingenio": "un acto de ingenio",
    "compasion": "un gesto de compasión", "sombra": "un acto de ambición",
    "duda": "una evasiva", "observar": "una observación",
    "hablar": "una conversación", "descansar": "un descanso",
    "moverse": "un desplazamiento",
}
NO_ENTENDIDO = ("No he entendido eso. Prueba con un verbo de acción (atacar, "
                "ayudar, engañar, observar, hablar con…, descansar, ir…) o elige "
                "un número. «/ayuda» te da ejemplos.")
MOMENTO_CRITICO = "Es un momento crítico: aquí hay que elegir una opción de la lista."
SIN_TIEMPO = "No hay tiempo para eso: ¡el peligro está encima!"
DEMASIADO = ("Ya has probado bastantes cosas aquí. El momento exige que decidas: "
             "elige una opción.")


class Retroceso(Exception):
    """Rehacer la partida quitando las últimas `n` acciones."""

    def __init__(self, n=1, resaltar=None):
        super().__init__(n)
        self.n = n
        self.resaltar = resaltar


class Cargar(Exception):
    def __init__(self, datos):
        super().__init__("cargar")
        self.datos = datos


class Salir(Exception):
    pass


class ErrorCarga(Exception):
    """Un guardado no se pudo reproducir (versión distinta o archivo dañado)."""


def _limpiar_nombre(nombre: str) -> str:
    nombre = re.sub(r"[^\w\-]+", "_", nombre.strip(), flags=re.UNICODE)[:30]
    return nombre or "manual"


class Sesion:
    """Interfaz entre el motor y el jugador: graba, repite y comanda."""

    def __init__(self, ui, params, carpeta_partidas, carpeta_libros=None):
        self.ui = ui
        self.params = params
        self.carpeta = Path(carpeta_partidas)
        self.carpeta_libros = Path(carpeta_libros) if carpeta_libros else None
        self.registros = []
        self.w = None
        self.confirmar_activo = True
        self.guardar_auto = True
        self.pos = 0
        self.n_replay = 0
        self.indice_actual = -1
        self._resaltar = None
        self._cargando = False
        self._ultimo_bueno = None      # (params, registros) que sabemos reproducibles
        self._inicio_hecho = False
        self._cap = None
        self._escena = None
        self._mostrado = True
        self.terminada = False
        self.aprendizaje = True        # recuerda lo que le explicas al intérprete
        self._reinterpretar = None     # frase a re-preguntar tras /corregir
        self._sucio = False            # hay que volver a autoguardar (tras deshacer o cargar)

    def reanudar(self, registros):
        """Prepara la sesión para retomar una partida a partir de sus acciones."""
        self.registros = [dict(r) for r in registros]
        self._cargando = bool(registros)

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------
    def ejecutar(self):
        """Juega la historia entera, atendiendo deshacer y cargar."""
        self._cargar_personal()
        while True:
            try:
                self.w = crear_mundo(self.params)
                self.pos, self.n_replay, self.indice_actual = 0, len(self.registros), -1
                self._inicio_hecho = False
                self._mostrado = True
                self.terminada = False
                final = motor.jugar(self.w, self)
                self.terminada = True
                self._cargando = False
                self._aplicar_meta_pendiente()
                self._autoguardar()
                self._post_final(final)
                return final
            except Retroceso as r:
                self._retroceder(r.n)
                self._resaltar = r.resaltar
                self._cargando = False
                self._sucio = True
                self.ui.mensaje("↩ Vuelves atrás." if r.n else "↻ El destino da otra vuelta.")
            except Cargar as c:
                self.params = Params(**c.datos["params"])
                self.registros = list(c.datos["registros"])
                self._resaltar = None
                self._cargando = True
                self._sucio = True
            except (Salir, KeyboardInterrupt):
                raise
            except Exception as exc:
                if not self._cargando:
                    raise
                self._cargando = False
                if self._ultimo_bueno is None:
                    raise ErrorCarga(f"{type(exc).__name__}: {exc}") from exc
                self.params, self.registros = self._ultimo_bueno
                self.ui.mensaje(f"No se pudo restaurar esa partida "
                                f"({type(exc).__name__}: {exc}). Sigues donde estabas.")

    # ------------------------------------------------------------------
    # API que usa el motor (hace de «interfaz» y silencia las repeticiones)
    # ------------------------------------------------------------------
    @property
    def reproduciendo(self) -> bool:
        return self.pos < self.n_replay

    def _muestra(self) -> bool:
        i = self.indice_actual
        return i >= self.n_replay or i == self._resaltar

    def inicio(self, w):
        if self.n_replay == 0 and not self._inicio_hecho:
            self.ui.inicio(w)
        self._inicio_hecho = True

    def capitulo(self, etapa, titulo):
        self._cap = (etapa, titulo)
        if not self.reproduciendo:
            self.ui.capitulo(etapa, titulo)

    def escena(self, parrafos, fuentes, critica):
        self._escena = (parrafos, fuentes, critica)
        self._mostrado = not self.reproduciendo
        if self._mostrado:
            self.ui.escena(parrafos, fuentes, critica)

    def interludio(self, frase, parrafos, tirada, enfoque):
        if self._muestra():
            self.ui.interludio(frase, parrafos, tirada, enfoque)

    def resultado(self, parrafos, tirada, enfoque):
        if self._muestra():
            self.ui.resultado(parrafos, tirada, enfoque)

    def final(self, final, w):
        self.ui.final(final, w)

    def _mostrar_pendiente(self):
        if self._cargando:
            self._cargando = False
            self.ui.mensaje(f"Retomas la historia de {self.w.heroe.nombre}.")
        if not self._mostrado and self._escena:
            if self._cap:
                self.ui.capitulo(*self._cap)
            self.ui.escena(*self._escena)
            self._mostrado = True

    # ------------------------------------------------------------------
    # Obtener la siguiente acción: de la grabación o del jugador
    # ------------------------------------------------------------------
    def obtener(self, esc, visibles, etiquetas):
        while self.pos < len(self.registros):
            reg = self.registros[self.pos]
            self.pos += 1
            if reg["k"] in META:
                self._aplicar_meta(reg)
                continue
            self.indice_actual = self.pos - 1
            return reg
        self._mostrar_pendiente()
        if self._sucio:
            self._sucio = False
            self._autoguardar()
        return self._en_vivo(esc, visibles, etiquetas)

    def _registrar(self, reg):
        reg["cap"] = self.w.etapa
        self.registros.append(reg)
        self.pos = len(self.registros)
        self.indice_actual = self.pos - 1
        self._autoguardar()
        return reg

    def _en_vivo(self, esc, visibles, etiquetas):
        while True:
            if self._reinterpretar is not None:        # tras /corregir
                texto, self._reinterpretar = self._reinterpretar, None
                reg = self._interpretar(texto, esc, visibles, etiquetas, preguntar=True)
                if reg is not None:
                    return self._registrar(reg)
                continue
            # La probabilidad de cada opción viaja aparte, para no cambiar la interfaz
            # de `leer` (cualquier interfaz de usuario sigue valiendo).
            self.ui.probs_actuales = [self.w.probabilidad_opcion(o) for o in visibles]
            entrada = self.ui.leer(etiquetas, libre_ok=not esc.critica,
                                   critica=esc.critica)
            tipo = entrada[0]
            if tipo == "op":
                i = entrada[1]
                return self._registrar({"k": "op", "i": i, "lbl": etiquetas[i][1]})
            if tipo == "cmd":
                self._comando(entrada[1], entrada[2], esc)
                continue
            reg = self._interpretar(entrada[1], esc, visibles, etiquetas)
            if reg is not None:
                return self._registrar(reg)

    def _sin_resolver(self, aviso):
        """Avisa de que no se pudo aplicar lo escrito y, en modo libre, enseña
        las opciones para que el jugador no se quede sin salida."""
        self.ui.mensaje(aviso)
        self.ui.pedir_lista()

    def _interpretar(self, texto, esc, visibles, etiquetas, preguntar=False):
        """Texto libre -> registro (o None si hay que volver a preguntar).

        Si el intérprete no está seguro (o el jugador pide corregir), pregunta
        qué intentaba y aprende de la respuesta.
        """
        w = self.w
        if esc.critica:
            self.ui.mensaje(MOMENTO_CRITICO)
            return None
        r = analizar(texto, w, esc, etiquetas, visibles)
        if r.bloqueo:
            self._sin_resolver(r.bloqueo)
            return None
        if r.opcion is None and (r.insegura or preguntar):
            clase = self.ui.preguntar_intencion(
                r.frase, None if r.clase == "desconocida" else r.clase)
            self._anotar_duda(r.frase, None if r.clase == "desconocida" else r.clase,
                              clase, "correccion" if preguntar else "dudaba")
            if clase is None:
                self._sin_resolver(NO_ENTENDIDO)
                return None
            if self.aprendizaje:
                lenguaje.aprender(r.frase, clase, w)
                self._guardar_personal()
            r = analizar(texto, w, esc, etiquetas, visibles, forzar=clase)
            if r.bloqueo:
                self._sin_resolver(r.bloqueo)
                return None
        elif preguntar and r.opcion is not None:
            pass                                       # ya se confirma con la opción
        if r.clase == "desconocida":
            self._sin_resolver(NO_ENTENDIDO)
            return None
        if esc.urgente and r.clase in ("descansar", "hablar") and r.opcion is None:
            self._sin_resolver(SIN_TIEMPO)
            return None
        if r.opcion is not None:
            eleccion = "s"
            if self.confirmar_activo or r.es_exploracion:
                rotulo, etiqueta = etiquetas[r.opcion]
                p = w.probabilidad_opcion(visibles[r.opcion])
                if p is not None:
                    etiqueta += f"  (≈ {round(100 * p)} %)"
                libre_ok = r.es_exploracion and not (
                    esc.urgente and r.clase in ("descansar", "hablar"))
                eleccion = self.ui.confirmar(r, rotulo, etiqueta, libre_ok)
            if eleccion == "n":
                self._anotar_duda(r.frase, r.clase, None, "rechazada")
            if eleccion == "s":
                return {"k": "libre", "txt": r.frase, "i": r.opcion, "dd": r.dd,
                        "mods": r.mods, "lbl": f"«{r.frase}»"}
            if eleccion == "n" or not r.es_exploracion:
                return None
            # eleccion == "l": hacerlo como acción libre, sin decidir la escena
        if w.libres_escena >= libre.MAX_LIBRES:
            self._sin_resolver(DEMASIADO)
            return None
        reg = r.a_registro()
        reg.update({"k": "int", "lbl": f"«{r.frase}»"})
        quien = NOMBRE_CLASE.get(r.clase, r.clase)
        if r.es_exploracion:
            self.ui.mensaje(f"Lo tomo como {quien}. (La escena sigue abierta; "
                            f"si no era eso, «/atras».)")
        else:
            self.ui.mensaje(f"Lo tomo como {quien} a tu manera: no resuelve la "
                            f"escena, pero cuenta. (Si no era eso, «/atras».)")
        return reg

    def _aplicar_meta(self, reg):
        if reg["k"] == "renombrar":
            self.w.renombrar(reg["rol"], reg["nombre"])
        elif reg["k"] == "nota":
            if self.terminada and self.w.cronica and self.w.cronica[-1].bloques:
                # el epílogo ya se escribió: la nota entra en su bloque
                self.w.cronica[-1].bloques[-1].notas.append(reg["txt"])
            else:
                self.w.notas_pendientes.append(reg["txt"])

    def _aplicar_meta_pendiente(self):
        """Tras el final, aplica las notas y renombrados que quedaron al final."""
        while self.pos < len(self.registros):
            reg = self.registros[self.pos]
            self.pos += 1
            if reg["k"] in META:
                self._aplicar_meta(reg)

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------
    def _acciones(self):
        return [i for i, r in enumerate(self.registros) if r["k"] in ACCIONES]

    def _retroceder(self, n):
        acc = self._acciones()
        n = max(0, min(n, len(acc)))
        if n:
            inicio = acc[-n]
            meta = [r for r in self.registros[inicio:] if r["k"] in META]
            del self.registros[inicio:]
            self.registros.extend(meta)     # tus notas y renombrados no se pierden

    def _comando(self, nombre, arg, esc=None, final=None):
        ui = self.ui
        nombre = nombre.lower().replace("á", "a").replace("é", "e")
        if nombre in ("atras", "deshacer"):
            n = entero(arg) or 1
            if not self._acciones():
                ui.mensaje("No hay nada que deshacer todavía.")
            else:
                raise Retroceso(n)
        elif nombre in ("historial", "acciones"):
            ui.imprimir(self._lineas_historial())
        elif nombre == "volver":
            acc = self._acciones()
            n = entero(arg)
            if n is None or not (1 <= n <= len(acc)):
                ui.mensaje(f"Uso: /volver N, con N entre 1 y {len(acc)} (mira /historial).")
            else:
                raise Retroceso(len(acc) - n + 1)
        elif nombre in ("reintentar", "otra"):
            self._reintentar()
        elif nombre == "guardar":
            try:
                ruta = self.guardar(arg)
                ui.mensaje(f"Guardado en «{ruta.stem}».")
            except OSError as exc:
                ui.mensaje(f"No pude guardar la partida ({exc.strerror or exc}).")
        elif nombre == "cargar":
            self._cargar(arg)
        elif nombre == "partidas":
            ui.imprimir(self._lineas_partidas())
        elif nombre == "renombrar":
            self._renombrar(arg)
        elif nombre == "nota":
            if not arg.strip():
                ui.mensaje("Uso: /nota texto")
            else:
                reg = {"k": "nota", "txt": arg.strip()}
                self.registros.append(reg)
                self.pos = len(self.registros)
                self._aplicar_meta(reg)
                self._autoguardar()
                ui.mensaje("Nota añadida al libro.")
        elif nombre == "corregir":
            self._corregir()
        elif nombre == "olvidar":
            lenguaje.fijar_personal(None)
            self._guardar_personal()
            ui.mensaje("He olvidado todo lo que me habías enseñado.")
        elif nombre == "estado":
            ui.imprimir(self._lineas_estado())
        elif nombre == "libro":
            try:
                ruta = self.guardar_libro(final)
            except OSError as exc:
                ui.mensaje(f"No pude guardar el libro ({exc.strerror or exc}).")
                ruta = None
            else:
                ui.mensaje(f"Libro guardado en: {ruta}" if ruta else
                           "No hay carpeta de libros configurada.")
        elif nombre == "notas":
            ui.notas = not ui.notas
            ui.mensaje("Notas de fuentes " + ("activadas." if ui.notas else "desactivadas."))
            if ui.notas and self._escena:
                ui.mostrar_notas(self._escena[1])
        elif nombre == "confirmar":
            self.confirmar_activo = not self.confirmar_activo
            ui.mensaje("Confirmación " + ("activada." if self.confirmar_activo
                                          else "desactivada (solo pregunto si dudo)."))
        elif nombre in ("prob", "probabilidad", "probabilidades", "stats"):
            ui.imprimir(self._lineas_probabilidades())
        elif nombre in ("frases", "exportar"):
            lineas = self._lineas_dudosas()
            if lineas:
                ui.imprimir(["Frases que no supe leer y lo que querías decir (más recientes al "
                             "final). Si quieres ayudarme a mejorar el vocabulario, "
                             "copia estas líneas y pégamelas:", ""] + lineas)
            else:
                ui.mensaje("Todavía no hay frases dudosas guardadas: aparecen aquí cuando el "
                           "narrador no te entiende y tú le explicas qué querías.")
        elif nombre == "modo":
            ui.mensaje(ui.cambiar_modo(arg))
        elif nombre == "dados":
            ui.dados = not getattr(ui, "dados", True)
            ui.mensaje("Verás la tirada de cada acción arriesgada." if ui.dados
                       else "Las tiradas quedan ocultas (el dado se sigue tirando).")
        elif nombre in ("ideas", "opciones"):
            ui.pedir_lista()
        elif nombre in ("ayuda", "help"):
            ui.imprimir(AYUDA.splitlines())
        elif nombre in ("salir", "q", "quit"):
            raise Salir()
        else:
            ui.mensaje(f"No conozco el comando «/{nombre}». Prueba /ayuda.")

    def _corregir(self):
        acc = self._acciones()
        if not acc or self.registros[acc[-1]]["k"] not in ("libre", "int"):
            self.ui.mensaje("Solo puedo corregir una frase libre que acabes de escribir. "
                            "Si fue una opción, usa /atras.")
            return
        self._reinterpretar = self.registros[acc[-1]]["txt"]
        raise Retroceso(1)

    def _reintentar(self):
        acc = self._acciones()
        if not acc:
            self.ui.mensaje("Aún no hay ninguna acción que repetir.")
            return
        ultimo = acc[-1]
        reg = self.registros[ultimo]
        if not reg.get("azar"):
            self.ui.mensaje("Esa acción no dependió del azar. Para cambiar el "
                            "resultado, vuelve atrás con /atras y decide otra cosa.")
            return
        reg["sal"] = reg.get("sal", 0) + 1
        raise Retroceso(0, resaltar=ultimo)

    def _renombrar(self, arg):
        partes = arg.strip().split(None, 1)
        if len(partes) < 2:
            self.ui.mensaje("Uso: /renombrar mentor|aliado|heraldo|villano|héroe NuevoNombre")
            return
        rol = ROLES_RENOMBRABLES.get(partes[0].lower())
        if rol is None:
            self.ui.mensaje(f"No sé a quién te refieres con «{partes[0]}». "
                            f"Puedes cambiar: mentor, aliado, heraldo, villano, héroe.")
            return
        nuevo = partes[1].strip()[:40]
        reg = {"k": "renombrar", "rol": rol, "nombre": nuevo}
        self.registros.append(reg)
        self.pos = len(self.registros)
        viejo = self.w.reparto[rol].nombre
        self._aplicar_meta(reg)
        self._autoguardar()
        self.ui.mensaje(f"{viejo[:1].upper() + viejo[1:]} se llamará {nuevo} a partir de "
                        "ahora (y en el libro).")

    # ------------------------------------------------------------------
    # Listados
    # ------------------------------------------------------------------
    def _lineas_historial(self):
        acc = self._acciones()
        if not acc:
            return ["Aún no has hecho nada."]
        return [f"{n:3d}. [cap. {self.registros[i].get('cap', '?')}] "
                f"{self.registros[i].get('lbl', '')}"
                + (" ↻" if self.registros[i].get("sal") else "")
                for n, i in enumerate(acc, 1)]

    def _lineas_probabilidades(self):
        w = self.w
        lineas = ["Tus probabilidades de éxito ahora (nivel, equipo, ánimo y falla):",
                  "                              fácil normal difícil"]
        for enfoque in ENFOQUES:
            mod = w.atributos[enfoque] - BASE_MODIFICADOR
            p = [round(100 * w.probabilidad(enfoque, dif)) for dif in (6, 7, 8)]
            nivel = nivel_de(w.atributos[enfoque])
            lineas.append(f"{ETIQUETAS[enfoque]:9s} {mod:+d} {nivel:<14s} "
                          f"{p[0]:4d} % {p[1]:4d} % {p[2]:4d} %")
        if w.ventaja:
            lineas.append("Tienes una ventaja para tu próxima tirada: ya está contada.")
        lineas.append("Lo que no has entrenado resta: te cuesta más.")
        return lineas

    def _lineas_estado(self):
        w = self.w
        a = w.atributos
        lineas = [
            f"{w.heroe.nombre}: vigor {w.vigor}/9 · valor {a['valor']} · ingenio "
            f"{a['ingenio']} · compasión {a['compasion']} · ambición {a['sombra']} "
            f"· amenaza {w.amenaza}",
        ]
        comp = []
        for rol in ("mentor", "aliado"):
            p = w.reparto[rol]
            if w.con(rol):
                comp.append(f"{p} (confianza {p.confianza})")
            elif not p.vivo:
                comp.append(f"{p.nombre} (ha muerto)")
        lineas.append("Te acompaña: " + (", ".join(comp) if comp else "nadie"))
        objetos = []
        if "don" in w.inventario:
            objetos.append(str(w.objetos["don"].ya))
        for k, nombre in (("equipo", "equipo de viaje"), ("mapa", "mapas y notas"),
                          ("recuerdo", "un recuerdo de casa"),
                          ("legado", "el legado del mentor")):
            if k in w.inventario:
                objetos.append(nombre)
        lineas.append("Llevas: " + (", ".join(objetos) if objetos else "poca cosa"))
        if w.ventaja:
            lineas.append("Tienes ventaja en tu próxima jugada.")
        return lineas

    # ------------------------------------------------------------------
    # Guardados
    # ------------------------------------------------------------------
    def _datos(self):
        w = self.w
        return {
            "version": VERSION_GUARDADO,
            "params": self.params.__dict__,
            "registros": self.registros,
            "titulo": w.titulo() if w else "",
            "heroe": w.heroe.nombre if w else self.params.nombre,
            "capitulo": w.etapa if w else 0,
            "acciones": len(self._acciones()),
            "terminada": self.terminada,
            "hora": time.strftime("%Y-%m-%d %H:%M"),
        }

    def _ruta(self, nombre):
        return self.carpeta / f"{_limpiar_nombre(nombre)}.json"

    def _escribir(self, ruta):
        self.carpeta.mkdir(parents=True, exist_ok=True)
        tmp = ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._datos(), ensure_ascii=False), encoding="utf-8")
        tmp.replace(ruta)

    def _ruta_personal(self):
        return self.carpeta / "vocabulario_personal.json"

    def _ruta_dudosas(self):
        return self.carpeta / "frases_dudosas.jsonl"

    def _anotar_duda(self, frase, entendido, elegido, motivo):
        """Guarda (solo en tu equipo) una frase que el intérprete no supo leer.

        Es la mejor materia prima para ampliar el vocabulario: lo que escribes de
        verdad y lo que querías decir. Nunca sale de tu carpeta `partidas/`;
        puedes enseñármelo con /frases.
        """
        if not self.guardar_auto:
            return
        try:
            self.carpeta.mkdir(parents=True, exist_ok=True)
            linea = json.dumps({"frase": frase, "entendido": entendido, "elegido": elegido,
                                "motivo": motivo, "hora": time.strftime("%Y-%m-%d %H:%M")},
                               ensure_ascii=False)
            with self._ruta_dudosas().open("a", encoding="utf-8") as f:
                f.write(linea + "\n")
        except (OSError, UnicodeError):
            pass

    def _lineas_dudosas(self, maximo=40):
        try:
            lineas = self._ruta_dudosas().read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            return []
        out = []
        for ln in lineas[-maximo:]:
            try:
                d = json.loads(ln)
                out.append(f"{d['frase']}  →  {d.get('elegido') or 'ninguna'}"
                           + (f" (entendí: {d['entendido']})" if d.get("entendido") else ""))
            except (ValueError, KeyError, TypeError):
                continue
        return out

    def _cargar_personal(self):
        try:
            datos = json.loads(self._ruta_personal().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            datos = None
        lenguaje.fijar_personal(datos if isinstance(datos, dict) else None)

    def _guardar_personal(self):
        if not self.guardar_auto:
            return
        try:
            self.carpeta.mkdir(parents=True, exist_ok=True)
            tmp = self._ruta_personal().with_suffix(".tmp")
            tmp.write_text(json.dumps(lenguaje.personal_a_dict(), ensure_ascii=False),
                           encoding="utf-8")
            tmp.replace(self._ruta_personal())
        except (OSError, UnicodeError):
            pass

    def _autoguardar(self):
        if self.guardar_auto and self.w is not None:
            try:
                self._escribir(self._ruta("auto"))
            except (OSError, UnicodeError):
                self.guardar_auto = False      # disco de solo lectura: seguimos sin guardar

    def guardar(self, nombre):
        ruta = self._ruta(nombre or "manual")
        self._escribir(ruta)
        return ruta

    def _cargar(self, nombre):
        if not nombre.strip():
            self.ui.imprimir(self._lineas_partidas())
            self.ui.mensaje("Usa /cargar nombre.")
            return
        datos = leer_guardado(self._ruta(nombre))
        if datos is None:
            self.ui.mensaje(f"No encuentro la partida «{nombre}». Mira /partidas.")
            return
        self._ultimo_bueno = (self.params, [dict(r) for r in self.registros])
        raise Cargar(datos)

    def _lineas_partidas(self):
        lineas = []
        for ruta in sorted(self.carpeta.glob("*.json")) if self.carpeta.exists() else []:
            d = leer_guardado(ruta)
            if d:
                lineas.append(f"{ruta.stem:16s} {d['heroe']} · «{d['titulo']}» · "
                              f"{d['acciones']} acciones · {d['hora']}"
                              + (" · terminada" if d.get("terminada") else ""))
        return lineas or ["No hay partidas guardadas."]

    def guardar_libro(self, final=None):
        if self.carpeta_libros is None:
            return None
        return guardar_libro(self.w, final, self.carpeta_libros)

    # ------------------------------------------------------------------
    def _post_final(self, final):
        """Tras el final se puede rectificar (/atras) o guardar el libro."""
        while True:
            entrada = self.ui.pedir_final()
            if entrada[0] == "fin":
                return
            self._comando(entrada[1], entrada[2], None, final)


def leer_guardado(ruta):
    """Lee y valida un guardado; None si no existe o está dañado."""
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        params = Params(**datos["params"])
        assert datos.get("version") == VERSION_GUARDADO
        assert params.genero in GENEROS and params.tono in TONOS
        assert params.trama in TRAMAS and params.arquetipo in ARQUETIPOS
        assert params.falla in FALLAS and isinstance(params.semilla, int)
        assert isinstance(params.mezcla, list) and all(g in GENEROS for g in params.mezcla)
        assert isinstance(params.contexto, str) and isinstance(params.nombres, dict)
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in params.nombres.items())
        assert isinstance(datos["registros"], list)
        for reg in datos["registros"]:
            assert isinstance(reg, dict) and reg.get("k") in ACCIONES + META
            if reg["k"] in ("op", "libre"):
                assert isinstance(reg.get("i"), int) and reg["i"] >= 0
            if reg["k"] in ("libre", "int", "nota"):
                assert isinstance(reg.get("txt"), str)
            if reg["k"] == "renombrar":
                assert isinstance(reg.get("rol"), str) and isinstance(reg.get("nombre"), str)
        for clave in ("heroe", "titulo", "hora"):
            assert isinstance(datos.get(clave), str)
        assert isinstance(datos.get("acciones"), int)
        return datos
    except (OSError, ValueError, KeyError, TypeError, AssertionError):
        return None
