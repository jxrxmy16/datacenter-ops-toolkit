"""El pueblo vivo: un lugar que sigue pasando aunque el héroe no esté.

Idea (Dwarf Fortress, Stardew Valley, las rutinas de Ultima VII): el mundo no se
detiene cuando miras hacia otro lado. Pero tampoco se simula minuto a minuto
mientras nadie mira. Aquí el tiempo es una cuenta de DÍAS (`Mundo.dia`) que
avanza con lo que hace el jugador (viajar, descansar, resolver escenas), y el
estado del pueblo en cualquier día es una función pura de (semilla, día):

  * un ACONTECIMIENTO con fases de duración fija (fiesta -> limpieza -> calma);
  * unas NOTICIAS DE VIDA semana a semana (bodas, mudanzas, sueños cumplidos...)
    decididas con un azar propio, que no toca el del resto de la historia;
  * los RECUERDOS que los vecinos guardan del héroe (lo único que cambia con
    lo que el jugador hace).

Que sea una función del día es lo que permite «volver meses después y que esté
todo limpio»: no hay nada que simular para recuperar el tiempo perdido, solo
preguntar por el día de hoy. Y como todo sale de la semilla, deshacer, guardar y
cargar siguen siendo exactos.
"""

import random
from dataclasses import dataclass, field

from .gramatica import Nom

# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------
# Lo propio de cada género: oficios (título con artículo, género), y los sustantivos
# con los que se cuentan los acontecimientos. Los define lexico.GENEROS["...]["pueblo"].

RASGOS = [
    "que siempre tiene tiempo para escuchar",
    "que no se fía de los forasteros",
    "que cuenta cada historia dos veces",
    "que guarda un viejo rencor a un vecino",
    "que ríe antes de que acabe el chiste",
    "a quien todos piden consejo",
    "que habla poco y lo ve todo",
    "que presume de lo que no tiene",
    "que no ha salido del pueblo en su vida",
    "que se queja de todo y ayuda en todo",
    "que sabe más de lo que cuenta",
    "que se sabe todos los cuentos del lugar",
]

# (lo que desea, lo que cuenta la noticia cuando se cumple, ¿se marcha del pueblo?)
DESEOS = [
    ("sueña con abrir su propio negocio", "ha abierto por fin su propio negocio", False),
    ("quiere irse {del_pueblo}, aunque no lo diga", "se marchó {del_pueblo} una mañana, sin "
     "despedirse", True),
    ("espera noticias de un hijo que se fue", "ha recibido por fin noticias de su hijo", False),
    ("está ahorrando para una boda", "se ha casado, y medio pueblo estuvo en la celebración",
     False),
    ("quiere hacer las paces con un viejo amigo", "ha hecho las paces con un viejo amigo", False),
    ("desea que {pueblo} vuelva a ser lo que era", "ha empezado a organizar a los vecinos "
     "para arreglar lo que estaba estropeado", False),
    ("guarda un secreto desde hace años", "ha contado por fin su secreto, y ahora lo sabe "
     "todo el pueblo", False),
    ("teme que todo cambie", "ha descubierto que el cambio no era tan terrible", False),
]

# Fases de cada acontecimiento: (nombre, duración en días; None = para siempre).
# Los textos son neutros en cuanto al género de mundo: llevan marcadores
# ({pueblo}, {plaza}, {adornos}, {musica}, {comida}, {faena}, {danio}, {destrozos},
# {arreglado}, {por}) que cada género rellena con sus palabras.
EVENTOS = {
    "fiesta": {
        "antes": "{pueblo} andaba de fiesta",
        "fases": [("preparativos", 2), ("fiesta", 1), ("limpieza", 3), ("calma", None)],
        "texto": {
            "preparativos": "Hay prisa y buen humor en {plaza}: cuelgan {adornos} y ensayan "
                            "con {musica}.",
            "fiesta": "{Plaza} rebosa de gente: se oye {musica}, circulan {comida} y nadie "
                      "se acuerda de las preocupaciones.",
            "limpieza": "{Plaza} amanece llen{o} de restos de la fiesta de anoche, y por turnos "
                        "se barre, se recogen {adornos} y se friegan las mesas.",
            "calma": "{Plaza} está limpi{o} y en orden; solo algún resto de {adornos} "
                     "enredado en un rincón recuerda la fiesta.",
        },
        "actos": {
            "preparativos": ["ata {adornos} a lo alto", "discute cómo colgar las luces",
                             "reparte tareas con voz de mando"],
            "fiesta": ["baila con quien se deja", "reparte {comida}", "canta sin afinar"],
            "limpieza": ["barre la puerta de su casa", "friega las mesas prestadas",
                         "devuelve las sillas a quien las prestó"],
            "calma": ["ha vuelto a su trabajo de siempre", "cuenta lo bien que salió la fiesta"],
        },
    },
    "mercado": {
        "antes": "{plaza} estaba patas arriba por el mercado",
        "fases": [("montaje", 1), ("mercado", 2), ("desmontaje", 1), ("calma", None)],
        "texto": {
            "montaje": "En {plaza} se montan los puestos entre voces y empujones.",
            "mercado": "{Plaza} bulle con el mercado: se regatea, circulan {comida} y se "
                       "cierran tratos a gritos.",
            "desmontaje": "Los comerciantes recogen sus puestos en {plaza} y se llevan lo que "
                          "no vendieron.",
            "calma": "{Plaza} ha recuperado su silencio de siempre; solo quedan las marcas de "
                     "los puestos en el suelo.",
        },
        "actos": {
            "montaje": ["monta su puesto el primero", "se queja de su sitio"],
            "mercado": ["regatea con una sonrisa", "pregona su mercancía"],
            "desmontaje": ["cuenta las monedas con cara de pocos amigos", "carga sus cajas"],
            "calma": ["ha vuelto a su trabajo de siempre"],
        },
    },
    "cosecha": {
        "antes": "todos andaban metidos en la cosecha",
        "fases": [("recogida", 6), ("trabajo", 3), ("almacenaje", 3), ("calma", None)],
        "texto": {
            "recogida": "Todo el que puede ayudar está fuera, recogiendo la cosecha antes de "
                        "que cambie el tiempo.",
            "trabajo": "En {plaza} se trabaja sin parar para dejar la cosecha lista.",
            "almacenaje": "Se acarrea y se guarda lo recogido; los almacenes huelen a "
                          "trabajo bien hecho.",
            "calma": "La cosecha ya está guardada y {pueblo} respira: por fin hay tiempo "
                     "para sentarse en {plaza}.",
        },
        "actos": {
            "recogida": ["trabaja desde el amanecer", "lleva agua a quien no puede parar"],
            "trabajo": ["clasifica lo recogido", "se queja de la espalda"],
            "almacenaje": ["cuenta los sacos una y otra vez", "carga sin quejarse"],
            "calma": ["descansa al fin", "reparte lo que sobró"],
        },
    },
    "reparaciones": {
        "antes": "{danio} lo había dejado todo patas arriba",
        "fases": [("destrozos", 2), ("reparacion", 9), ("calma", None)],
        "texto": {
            "destrozos": "{Pueblo} contempla los daños {danio_de}: {destrozos}.",
            "reparacion": "Resuenan {faena} por {todo_pueblo}: están arreglando los daños, "
                          "{por}.",
            "calma": "Casi no se nota que hubo daños: {arreglado}.",
        },
        "actos": {
            "destrozos": ["achica lo que puede", "cuenta lo que se ha perdido"],
            "reparacion": ["reparte herramientas y consejos", "se sube a ayudar donde hace falta"],
            "calma": ["presume de lo bien que ha quedado su parte",
                      "ofrece ayuda al que aún no ha terminado"],
        },
    },
    "luto": {
        "antes": "{pueblo} velaba a uno de los suyos",
        "fases": [("velatorio", 2), ("entierro", 1), ("calma", None)],
        "texto": {
            "velatorio": "{Pueblo} vela a uno de los suyos: puertas entornadas, voces bajas "
                         "y luces encendidas toda la noche.",
            "entierro": "{Todo_pueblo} acompaña el entierro, en silencio, hasta el último "
                        "momento.",
            "calma": "{Pueblo} ha vuelto poco a poco a su ritmo, aunque falta alguien en "
                     "{plaza} y todos lo saben.",
        },
        "actos": {
            "velatorio": ["se queda a velar toda la noche", "reparte pan y café a quien llega"],
            "entierro": ["lleva flores sin decir nada", "ayuda a cargar sin pedir permiso"],
            "calma": ["habla del difunto con cariño", "ha vuelto a su trabajo de siempre"],
        },
    },
}

# Los acontecimientos que el pueblo puede tener en el día 0 y la fase en la que están.
INICIOS = [("fiesta", "limpieza"), ("fiesta", "fiesta"), ("fiesta", "preparativos"),
           ("mercado", "mercado"), ("mercado", "desmontaje"), ("cosecha", "recogida"),
           ("cosecha", "almacenaje"), ("reparaciones", "reparacion"), ("luto", "velatorio")]

# Días que tarda el héroe en llegar a cada etapa y días que pasan al resolver cada
# escena. El viaje de vuelta a casa (etapa 12) también cuenta.
DIAS_VIAJE = {2: 1, 3: 1, 4: 4, 5: 3, 6: 5, 7: 8, 8: 4, 9: 2, 10: 5, 11: 7, 12: 14}
DIAS_ESCENA = 1


# --------------------------------------------------------------------------
# Modelo
# --------------------------------------------------------------------------
@dataclass
class Vecino:
    nombre: str
    oficio: str                   # título con artículo: «la panadera»
    genero: str                   # m | f
    rasgo: str
    deseo: int                    # índice en DESEOS
    mayor: bool = False
    cumple_el: int = -1           # día en que se cumple su deseo (-1: nunca, en la partida)
    muere_el: int = -1            # día en que muere (-1: no)

    def __str__(self) -> str:
        return f"{self.oficio} {self.nombre}"


@dataclass
class Recuerdo:
    dia: int
    clave: str                    # ayudo | curioso | ...
    vecino: int                   # índice en Pueblo.vecinos


def _cap(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


@dataclass
class Pueblo:
    vecinos: list
    evento: str
    fase_inicial: str
    inicio: int                   # día (puede ser negativo) en que empezó el acontecimiento
    nombres: dict                 # plaza, adornos, musica, comida, faena
    semilla: int
    recuerdos: list = field(default_factory=list)
    _contador: int = 0

    # --- fases ------------------------------------------------------------
    def fase(self, dia: int) -> str:
        """La fase del acontecimiento en `dia` (función pura del día)."""
        t = dia - self.inicio
        fases = EVENTOS[self.evento]["fases"]
        acumulado = 0
        for nombre, dur in fases:
            if dur is None or t < acumulado + dur:
                return nombre
            acumulado += dur
        return fases[-1][0]

    def en_calma(self, dia: int) -> bool:
        return self.fase(dia) == "calma"

    def dia_de_calma(self) -> int:
        """El primer día en que el acontecimiento ya ha terminado."""
        total = sum(d for _, d in EVENTOS[self.evento]["fases"] if d is not None)
        return self.inicio + total

    # --- vecinos a una fecha ----------------------------------------------
    def presente(self, v: Vecino, dia: int) -> bool:
        """¿Sigue en el pueblo? (los que se marchan o mueren dejan de estar)"""
        if 0 <= v.muere_el <= dia:
            return False
        if v.cumple_el >= 0 and v.cumple_el <= dia and DESEOS[v.deseo][2]:
            return False
        return True

    def vecinos_en(self, dia: int) -> list:
        return [v for v in self.vecinos if self.presente(v, dia)]

    # --- texto --------------------------------------------------------------
    def _formato(self, plantilla: str) -> str:
        n = self.nombres
        o = "o" if n["plaza"].split()[0].lower() in ("el", "los") else "a"
        art = n["pueblo"].split()[0].lower()
        todo_pueblo = ("todo " if art in ("el", "los") else "toda ") + n["pueblo"]
        return plantilla.format(
            plaza=n["plaza"], Plaza=_cap(n["plaza"]), adornos=n["adornos"], musica=n["musica"],
            comida=n["comida"], faena=n["faena"], o=o, pueblo=n["pueblo"],
            Pueblo=_cap(n["pueblo"]), danio=n["danio"], destrozos=n["destrozos"],
            arreglado=n["arreglado"], por=n["por"], danio_de=Nom(n["danio"]).de,
            todo_pueblo=todo_pueblo, Todo_pueblo=_cap(todo_pueblo),
            del_pueblo=Nom(n["pueblo"]).de)

    def _elegir(self, opciones: list, dia: int, extra: str = "") -> str:
        r = random.Random(f"{self.semilla}:{dia}:{extra}")
        return r.choice(opciones)

    def describir_fase(self, dia: int) -> str:
        """Una o dos frases sobre cómo está el pueblo ese día."""
        ev = EVENTOS[self.evento]
        fase = self.fase(dia)
        frase = self._formato(ev["texto"][fase])
        vivos = self.vecinos_en(dia)
        if vivos:
            v = vivos[self._indice(dia, fase, len(vivos))]
            acto = self._formato(self._elegir(ev["actos"][fase], dia, fase))
            frase += f" {_cap(str(v))} {acto}."
        return frase

    def _indice(self, dia: int, extra: str, n: int) -> int:
        return random.Random(f"{self.semilla}:{extra}:v").randrange(n)

    def estado_hoy(self, dia: int) -> str:
        """El pueblo tal como está ahora (para la primera escena)."""
        return self.describir_fase(dia)

    # --- noticias de vida ----------------------------------------------------
    def noticias(self, desde: int, hasta: int) -> list:
        """Lo que pasó entre `desde` y `hasta` (días): [(día, texto)] ordenado."""
        out = []
        for v in self.vecinos:
            if v.muere_el >= 0 and desde < v.muere_el <= hasta:
                out.append((v.muere_el, f"{_cap(str(v))} murió mientras estabas fuera; el "
                                        "pueblo lo despidió como se merecía."))
            elif v.cumple_el >= 0 and desde < v.cumple_el <= hasta:
                if v.muere_el < 0 or v.cumple_el < v.muere_el:
                    out.append((v.cumple_el, self._formato(
                        f"{_cap(str(v))} {DESEOS[v.deseo][1]}.")))
        return sorted(out)

    # --- memoria del héroe ----------------------------------------------------
    def recordar(self, clave: str, dia: int, cuantos: int = 1) -> list:
        """Anota que `cuantos` vecinos recuerdan algo del héroe. Devuelve sus nombres.

        Los elegidos salen de un azar propio (semilla y número de recuerdo), así que
        no alteran los dados de la historia ni dependen de ellos.
        """
        r = random.Random(f"{self.semilla}:recuerdo:{self._contador}")
        self._contador += 1
        vivos = [i for i, v in enumerate(self.vecinos) if self.presente(v, dia)]
        r.shuffle(vivos)
        elegidos = vivos[:cuantos]
        for i in elegidos:
            self.recuerdos.append(Recuerdo(dia, clave, i))
        return [self.vecinos[i].nombre for i in elegidos]

    def quien_recuerda(self, clave: str, dia: int):
        """Un vecino presente que recuerde `clave` (o None)."""
        for rec in self.recuerdos:
            if rec.clave == clave and self.presente(self.vecinos[rec.vecino], dia):
                return self.vecinos[rec.vecino]
        return None

    def resumen(self) -> dict:
        """Estado comparable (para pruebas)."""
        return {"evento": self.evento, "inicio": self.inicio,
                "vecinos": [(str(v), v.cumple_el, v.muere_el) for v in self.vecinos],
                "recuerdos": [(r.dia, r.clave, r.vecino) for r in self.recuerdos]}


# --------------------------------------------------------------------------
# Creación
# --------------------------------------------------------------------------
def crear_pueblo(semilla: int, datos: dict, nombres_f, nombres_m, prohibidos=(), n=8,
                 horizonte=120) -> Pueblo:
    """El pueblo de esta semilla. `datos` es lex["pueblo"] del género del mundo.

    Usa un azar propio derivado de la semilla: crear un pueblo no cambia ninguna
    otra cosa del mundo.
    """
    rng = random.Random(f"pueblo:{semilla}")
    f = [x for x in nombres_f if x not in prohibidos]
    m = [x for x in nombres_m if x not in prohibidos]
    rng.shuffle(f)
    rng.shuffle(m)
    oficios = list(datos["oficios"])
    rng.shuffle(oficios)
    vecinos = []
    for oficio, genero in oficios:
        if len(vecinos) == n:
            break
        pool = f if genero == "f" else m
        if not pool:
            continue                  # sin más nombres de ese sexo: pasa al siguiente oficio
        vecinos.append(Vecino(pool.pop(), oficio, genero, rng.choice(RASGOS),
                              rng.randrange(len(DESEOS)), mayor=rng.random() < 0.3))

    permitidos = datos.get("eventos") or list(EVENTOS)
    evento, fase = rng.choice([x for x in INICIOS if x[0] in permitidos])
    # El acontecimiento empezó de modo que el día 0 caiga en la mitad de esa fase.
    fases = EVENTOS[evento]["fases"]
    antes = 0
    for nombre, dur in fases:
        if nombre == fase:
            inicio = -(antes + max(0, (dur or 1) - 1) // 2)
            break
        antes += dur or 0

    # Noticias de vida: cada semana, un pequeño azar por vecino.
    ultimo_muerto = -99
    for semana in range(2, horizonte // 7 + 1):
        dia = semana * 7
        for v in vecinos:
            if v.cumple_el >= 0 or v.muere_el >= 0:
                continue
            tirada = rng.random()
            if tirada < 0.05:
                v.cumple_el = dia + rng.randrange(7)
            elif v.mayor and tirada > 0.985 and dia - ultimo_muerto > 21:
                v.muere_el = dia + rng.randrange(7)
                ultimo_muerto = dia
    return Pueblo(vecinos, evento, fase, inicio, dict(datos["nombres"]), semilla)


# --------------------------------------------------------------------------
# Lo que se cuenta
# --------------------------------------------------------------------------
def detalle_de_un_vecino(p: Pueblo, dia: int) -> str:
    """Una pincelada sobre alguien del pueblo (para quien se fija en la gente)."""
    vivos = p.vecinos_en(dia)
    if not vivos:
        return ""
    v = vivos[random.Random(f"{p.semilla}:detalle").randrange(len(vivos))]
    return p._formato(f"{_cap(str(v))}, {v.rasgo}, {DESEOS[v.deseo][0]}.")


def _tiempo(dias: int) -> str:
    if dias < 14:
        return f"unos {max(dias, 2)} días"
    if dias < 60:
        return f"unas {round(dias / 7)} semanas"
    return f"casi {max(2, round(dias / 30))} meses"


def regreso(w) -> list:
    """Los párrafos del regreso a casa: el pueblo tal como está ahora.

    Recupera el tiempo perdido sin simular nada: pregunta por el día de hoy.
    """
    p = w.pueblo
    if p is None:
        return []
    dia = w.dia
    ev = EVENTOS[p.evento]
    antes = p._formato(ev["antes"])
    tiempo = _tiempo(dia)
    if w.b("hogar_perdido"):
        v = next(iter(p.vecinos_en(dia)), None)
        resto = (f" {_cap(str(v))} ya retira piedras con quien quiere ayudar." if v else "")
        return [f"Han pasado {tiempo} desde que te marchaste; entonces {antes}. "
                f"{_cap(p.nombres['plaza'])} ya no existe como era: queda el hueco entre los "
                f"escombros.{resto}"]
    parrafos = [f"Han pasado {tiempo} desde que te marchaste; entonces {antes}. "
                f"{p.describir_fase(dia)}"]
    noticias = p.noticias(0, dia)
    if noticias:
        parrafos.append("Te ponen al día en cuanto llegas. " +
                        " ".join(t for _, t in noticias[:2]))
    else:
        parrafos.append("Te cuentan que todo ha seguido su curso, sin grandes sobresaltos.")
    v = p.quien_recuerda("ayudo", dia)
    if v is not None:
        parrafos.append(f"{_cap(str(v))} aún recuerda que le echaste una mano antes de "
                        "partir, y se lo cuenta a quien quiere oírlo.")
    else:
        v = p.quien_recuerda("curioso", dia)
        if v is not None:
            parrafos.append(f"{_cap(str(v))} te recuerda como quien lo escuchaba todo con "
                            "atención, y te pregunta qué has aprendido por ahí.")
    return parrafos
