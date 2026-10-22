# Forja de Historias

Un narrador interactivo de consola, **sin inteligencia artificial**. Tú pones los
parámetros (universo, tono, protagonista, falla) y vas tomando decisiones; el
juego va armando una historia que cambia en cada partida y que **se mantiene
lógica dentro de su universo**. Al terminar puedes guardarla como un libro.

No usa redes neuronales, ni APIs, ni internet, ni dependencias: solo Python 3.8+
y su biblioteca estándar (probado en 3.11, 3.12 y 3.13). Los textos están escritos a mano; la variedad sale de
combinar reglas, léxicos y el estado del mundo.

## Jugar

```
python jugar.py                  # partida interactiva con menús
python jugar.py --aleatorio      # todos los parámetros al azar
python jugar.py --demo           # una partida entera que se juega sola
python jugar.py --semilla 42     # repite exactamente el mismo mundo
python jugar.py --notas          # muestra de qué obra sale cada escena
```

En Windows: `py jugar.py`. Durante la partida, `n` activa o desactiva las notas de
fuentes y `q` sale. Al final se ofrece guardar el libro en `historias/`.
Hay un libro ya jugado en [`ejemplos/`](ejemplos/el-expediente-sombra-1541.md).

## Jugar en Android

La forma más cómoda es **Termux**, una terminal para Android. Instálala desde
[F-Droid](https://f-droid.org/packages/com.termux/) (la versión de Google Play
está desactualizada). Luego, dentro de Termux:

```
pkg update && pkg install -y git python
git clone -b claude/peaceful-cori-nibpuy https://github.com/jxrxmy16/datacenter-ops-toolkit.git
cd datacenter-ops-toolkit/forja-de-historias
python jugar.py
```

O, con el script que instala Python si falta: `sh termux.sh`.

Para recibir las novedades más tarde: `git pull` dentro de la carpeta del repositorio. Tu partida guardada (`partidas/`) y tus libros (`historias/`) no se tocan.

- **Pantalla**: el texto se ajusta al ancho (mínimo 40 columnas). En vertical
  cabe; en horizontal queda más cómodo.
- **Teclado**: escribes frases con tus palabras. Para los comandos necesitas la
  tecla `/` (en la fila extra de Termux). Un número también vale como atajo.
- **Tu libro**: se guarda en `historias/`. Para sacarlo a la carpeta de
  Descargas: `termux-setup-storage` (una vez) y
  `cp historias/*.md ~/storage/downloads/`.
- **Sin Git**: descarga el ZIP del repositorio desde el navegador, descomprímelo
  y entra en la carpeta `forja-de-historias`.

Alternativa sin terminal: **Pydroid 3** (Play Store). Abre la carpeta
`forja-de-historias` completa (no solo `jugar.py`) y ejecuta `jugar.py`; el
color se desactiva solo.

> No he podido probarlo en un teléfono real: lo verifiqué simulando una pantalla
> de 42 columnas sin color y con Python 3.11-3.13. Si algo falla en tu móvil,
> dime el mensaje de error.

## Cómo es una partida

1. **Parámetros**: género (fantasía, ciencia ficción, noir, terror gótico), tono
   (luminoso, equilibrado, sombrío), trama (vencer al monstruo / la búsqueda),
   nombre y pronombres del protagonista, arquetipo y una *falla* que la historia
   pondrá a prueba. Además puedes **contar tu mundo** (ver abajo).
2. **Doce capítulos** (las etapas del viaje del héroe). En cada uno el motor
   elige, entre las escenas que el estado del mundo permite, una distinta, y te
   da 2-5 decisiones.
3. **Un final** que no está escrito de antemano: triunfo, victoria pírrica,
   renacimiento, tragedia, derrota o caída, según lo que le pasó a cada personaje
   y a quién se volvió el héroe.
4. **El libro**: capítulos, tus decisiones en cursiva y la bibliografía de lo que
   apareció.

## El pueblo vivo y el reloj del mundo

El mundo no se detiene cuando miras hacia otro lado. La historia lleva la cuenta
de los **días** (viajar, descansar y resolver escenas gastan tiempo) y el
pueblo de donde partes sigue viviendo:

- Al empezar, está en mitad de **un acontecimiento** (una fiesta que acaba en
  limpieza, un mercado que se desmonta, la cosecha, las reparaciones tras una
  tormenta, un velatorio), y tiene **ocho vecinos inventados** con oficio,
  carácter y un deseo (abrir un negocio, irse, casarse...).
- Cuando vuelves a casa, **ya han pasado semanas o meses**: la plaza está limpia
  porque terminaron de limpiar, y los vecinos te ponen al día de lo que les
  pasó mientras no estabas (se casaron, se marcharon, alguien mayor murió...).
- El pueblo **te recuerda**: si ayudaste a tus vecinos, alguien te lo recuerda
  con su nombre; si escuchaste a todos, también.

Cómo funciona sin simular cada día: el estado del pueblo es una *función pura*
del día y de la semilla (el acontecimiento tiene fases de duración fija y las
noticias se deciden por semanas con un azar propio), así que recuperar meses
perdidos es preguntar «¿cómo está hoy?». Por eso deshacer, guardar y cargar
siguen siendo exactos, y por eso crear el pueblo no cambia ningún otro dado de
la historia. Es una porción pequeña: un solo pueblo, el principio y el final del
viaje; el siguiente paso sería un mapa con más lugares y vecinos que se mudan.

## Dados y estadísticas (el componente de rol)

Toda acción con riesgo se resuelve con un dado de seis caras: **dado + tu
atributo + bonos contra una dificultad**. Se ve siempre, con su desglose:

```
(dado 4 + valor -1 (poco entrenado) +1 (equipo, ánimo, falla) = 4 contra 5 → fracaso)
```

- Los atributos (Valor, Ingenio, Compasión, Ambición) se muestran como
  **modificadores alrededor de 0**: «corriente» ni suma ni resta; «poco
  entrenado» (-1) y «sin entrenar» (-2) **restan**. Así, un personaje que ha
  crecido en Ingenio y se lanza a una acción de fuerza tiene un negativo real.
  Se entrena a base de éxitos con ese atributo.
- Las opciones con riesgo enseñan su **probabilidad exacta** (`≈ 50 %`) antes de
  elegir, y también cuando el narrador te enseña cómo ha entendido tu frase.
  `/prob` resume lo que puedes esperar con cada atributo. `/dados` oculta o
  muestra las tiradas.
- «Con cuidado», «en silencio» o «con ayuda» bajan la dificultad; «a ciegas»,
  «sin armas» o «herido» la suben. «Otra suerte» (`/reintentar`) repite la
  tirada con otro dado sin cambiar nada más.

## Cuenta tu mundo: mezclar géneros y poner nombres

Al crear la partida, tras elegir el género:

- **Mezcla de géneros.** Puedes mezclarlo con uno o varios más («1,3»). El
  género principal domina (pesa el doble) y los demás aportan lugares, villanos,
  guardianes, esbirros, objetos, nombres y ambiente. Un Noir con toques de
  Fantasía puede tener un detective retirado, un portero del tamaño de un
  armario y una torre de los vientos muertos, y el libro cita las obras de todos.
- **Premisa libre.** Una línea con tus palabras: «una ciudad de canales con
  magia vieja y detectives cansados; el pueblo se llama Aguasmuertas y el
  villano Zarkon; tono oscuro». No hay IA: el narrador solo reconoce tres
  cosas concretas, y **te enseña lo que ha entendido** para que lo confirmes:
  géneros por palabras clave (magia, nave, detective, fantasma...), un tono, y
  nombres propios tras «se llama / llamado» (pueblo, mentor, aliado, heraldo,
  villano). El resto de tu texto sale como *premisa* en el libro, pero no
  cambia las escenas: es mejor decirlo que fingir que lo ha entendido.
- Con `--aleatorio` hay una probabilidad de mezcla al azar.

## Escribir libremente, deshacer y guardar

**La partida se juega escribiendo.** En cada escena el libro te pregunta
«¿Qué haces?» y tú respondes con tus palabras, sin lista de opciones delante:

```
¿Qué haces? (? = ideas) > salir del bosque caminando con los ojos cerrados
¿Qué haces? (? = ideas) > hablar con el mentor
¿Qué haces? (? = ideas) > engañar al guardián diciendo que soy inspector
¿Qué haces? (? = ideas) > tender la mano al aliado
```

- Con **`?`** (o `ideas`) te enseño las opciones de la escena, por si no sabes
  qué probar; también salen solas cuando lo que escribes no se puede aplicar.
  Escribir su número sigue valiendo.
- **`/modo`** alterna entre escribir libremente y ver siempre la lista (como en
  un librojuego clásico). `python jugar.py --opciones` arranca así.
- En los **momentos críticos** la lista siempre está y solo valen las opciones.

No hay inteligencia artificial detrás: un intérprete de español por reglas
(`forja/lenguaje.py`) reconoce **raíces de palabras**, no significados. Por eso
trabaja **en modo asistido**:

- Si **no está seguro** o no conoce tu frase, te pregunta qué intentabas con un
  menú de nueve opciones (atacar, engañar, ayudar, aprovecharte, evitar,
  observar, hablar, descansar, moverte). Con tu respuesta sigue adelante.
- **Aprende de ti**: las palabras que no conocía las guarda en
  `partidas/vocabulario_personal.json`, y la próxima vez que las escribas (aunque
  cambie la conjugación) ya no pregunta. `/olvidar` lo borra.
- Si te malinterpretó **sin avisar**, `/corregir` vuelve a preguntarte por tu
  última frase; y `/atras` deshace cualquier acción.

- **Decisión.** Si lo que escribes encaja con una opción de la escena (por la
  intención o por palabras compartidas), se resuelve esa opción con sus efectos,
  pero tu frase cuenta en el relato y en la dificultad. Te pregunta antes
  («¿Es eso?»); con `/confirmar` puedes desactivar la pregunta.
- **Interludio.** Si es otra cosa (mirar, hablar con alguien, descansar,
  moverte, improvisar) se resuelve al momento y la escena sigue abierta. Puede
  darte una pista, una **ventaja** para tu próxima jugada o un coste. Hasta tres
  por escena.
- **Modificadores.** «Con cuidado», «en silencio» o «despacio» bajan la
  dificultad; «a ciegas», «sin armas» o «con una mano» la suben, pero si sale
  bien recuperas aliento.
- **Coherencia.** No puedes hablar con quien murió, ni ir a un lugar al que aún
  no se puede llegar, ni descansar en mitad de una emboscada. Las acciones
  contra tus compañeros se reservan para los momentos críticos.
- **Momentos críticos** (la traición, el sacrificio del mentor, la prueba
  suprema, el último asalto...): solo hay opciones, como en un RPG.

### Deshacer, rehacer y guardar

Todo es reversible porque la partida es **determinista**: la semilla más la
lista de tus acciones reconstruyen exactamente la misma historia, hasta el
último dado. No se guardan «copias» del mundo que puedan desincronizarse.

| Comando | Qué hace |
|---|---|
| `/atras [n]` | deshace tus últimas *n* acciones (también tras el final) |
| `/historial` · `/volver N` | lista tus acciones y vuelve a justo antes de la *N* |
| `/reintentar` | repite la última acción con otra suerte |
| `/corregir` · `/olvidar` | corrige cómo entendí tu última frase · borra lo que he aprendido de ti |
| `/frases` | enseña las frases que no supe leer y lo que querías decir (se guardan solo en tu equipo, en `partidas/frases_dudosas.jsonl`; si me las pegas, el vocabulario mejora con lo que escribes de verdad) |
| `/modo` · `/dados` | escribir libremente o ver siempre la lista · mostrar u ocultar las tiradas |
| `/prob` | tus probabilidades de éxito (fácil / normal / difícil) según lo que has entrenado |
| `/guardar [nombre]` · `/cargar [nombre]` · `/partidas` | guardados con nombre |
| `/renombrar mentor Zarkon` | cambia un nombre, también en el libro |
| `/nota texto` | añade una nota tuya al libro |
| `/estado` · `/libro` · `/notas` · `/confirmar` · `/ayuda` · `/salir` | consulta y ajustes |

La partida se guarda sola en `partidas/auto.json` tras cada acción. Al volver a
ejecutar `python jugar.py` te ofrece continuarla (`--nueva` empieza de cero).

### Cuánto entiende de verdad (cifras reales, provisionales)

El intérprete se mide con frases de jugador escritas por agentes que no vieron
el código (`tests/datos/`, `tools/evaluar_corpus.py`), separadas en corpus de
**desarrollo** (con los que se afina, en el repositorio) y de **prueba** (que
nunca se usan para afinar y viven fuera). Sobre los corpus de prueba:

| | prueba 1 (583 frases) | prueba 2 (1 594 frases, 8 registros) |
|---|---|---|
| intención acertada | **88,9 %** | **86,2 %** |
| matices de dificultad acertados («a ciegas», «con cuidado») | 97,9 % | 86,6 % |
| se entiende bien y se aplica sin preguntar | 79,4 % | 72,7 % |
| duda y te pregunta (basta con pulsar Enter) | 14,1 % | 18,7 % |
| se entiende mal **sin avisar** | 6,5 % | 8,6 % |

La prueba 2 mezcla órdenes cortas, primera persona, literario, jerga regional,
escritura de móvil, mezcla de géneros, matices y frases indirectas; es más
difícil que la primera (las frases indirectas y la jerga regional son lo más
flojo, y «la frase no es una acción del juego» sigue en ~78 %). En desarrollo
salen cifras más altas (~89–97 %), pero son optimistas porque ahí se afinó.
El narrador pregunta cuando la mejor y la segunda lectura están muy cerca: eso
cuesta una pulsación y evita errores en silencio. Si te malinterpreta,
`/corregir` y `/atras` lo arreglan. El vocabulario crece por rondas, midiendo
siempre con frases nuevas (de 79,0 a 86,2 % en la prueba 2 en un día).

## Por qué la historia tiene lógica

La idea viene de los planificadores narrativos clásicos: cada escena exige
**precondiciones** sobre el estado del mundo y, al resolverse, aplica
**efectos**.

- Quien muere sale del grupo y **no puede volver a aparecer**. Un aviso del
  renderizador salta si una plantilla nombra a un personaje ausente o muerto sin
  haberlo declarado como mención (un recuerdo, un epitafio).
- Quien no fue invitado no acompaña: si rechazas al mentor, no habrá sacrificio
  del mentor ni «voz del mentor» al final.
- **Los secretos se deciden al crear el mundo**, no cuando aparecen: quién es
  el traidor y qué une al villano con el héroe ya está fijado, así que las pistas
  que se siembran son verdaderas.
- **Siembra y cosecha** (la pistola de Chéjov): lo que haces antes se cobra
  después.

| Siembra | Cosecha |
|---|---|
| Escuchar rumores en el capítulo 1 | Una opción extra en la llamada: conoces su punto débil |
| Preguntarle al mentor por su pasado | La revelación del villano no te sorprende; hablarle cuesta menos |
| Rechazar a un aliado que era traidor | Lo reconoces junto al villano en la prueba suprema |
| Sospechar de un aliado (preguntas, guardias) | Si traiciona, ya estabas preparado y perdonarlo cuesta menos |
| Ayudar a unos desconocidos | Vuelven a rescatarte en el camino de vuelta |
| Ganarte al guardián del umbral hablando | Te abre paso al volver |
| Perder al mentor (por su sacrificio) | Su legado te da ventaja en la prueba final |
| Llevarte un recuerdo de casa | Ayuda a resistir la voz de tu falla |
| Negarte a partir | Tu hogar sufre, y puede que el heraldo no lo cuente |

Hay dados (un d6 más tus atributos y objetos) que deciden si un golpe sale bien,
pero el sentido moral del final lo decide la **Ambición** acumulada y si al
final resistes o cedes a la voz de tu falla (la *hamartia* de Aristóteles, la
«sombra» de Jung).

## Las fuentes: teoría y cine como estructura

El esqueleto no es inventado:

- **Doce etapas**: Vogler, *El viaje del escritor*, sobre Campbell, *El héroe de
  las mil caras*.
- **Funciones y personajes**: Propp (donante, auxiliar, agresor, falso héroe,
  persecución, socorro...) y el modelo actancial de Greimas (ayudante frente a
  oponente).
- **Equilibrio roto y restablecido**: Todorov.
- **Tramas**: Booker, *Las siete tramas básicas* (aquí, dos: vencer al monstruo y
  la búsqueda; la tragedia y el renacimiento emergen en los finales).
- **Reversión y reconocimiento**: Aristóteles, *Poética*.
- **Situaciones**: Polti, *Las 36 situaciones dramáticas*.

Cada escena cita las obras que recuerda (Star Wars, *El Señor de los Anillos*,
*Los siete samuráis*, *Mad Max*, Le Guin, Conrad...). Con `--notas` se ven junto a
la escena, y el libro final incluye «qué escena recuerda a qué». El catálogo
completo está en [`FUENTES.md`](FUENTES.md).

> Las obras de ficción son **inspiración**: se cita el patrón, no se copia texto.
> Las referencias dan autor, título y año, sin editorial: verifícalas antes de
> usarlas en un trabajo académico.

## Estructura del código

```
jugar.py            punto de entrada, menús y reanudar la partida automática
forja/
  lexico.py         vocabulario por género, arquetipos, fallas, tonos (solo datos)
  gramatica.py      concordancia en español: {meta.de}, {hogar.a}, cansad{heroe.o}
  modelo.py         Personaje, Mundo, Escena, Opcion; renderizador con avisos
  generador.py      crea el mundo y decide los secretos a partir de la semilla
  efectos.py        vigor(-1), pon("flag"), muere("mentor")... el vocabulario de las escenas
  acto1/2/3.py      las 21 escenas, agrupadas por acto
  final.py          elige el final y compone el epílogo
  motor.py          recorre las 12 etapas y resuelve cada escena (y sus interludios)
  sesion.py         graba las acciones; deshacer, reintentar, guardar/cargar, comandos
  lenguaje.py       intérprete del texto libre (raíces, frases, modificadores, bloqueos)
  vocabulario.py    vocabulario ampliado del intérprete (generado)
  libre.py          interludios (mirar, hablar, descansar, moverse) y decisiones escritas
  consola.py        interfaz: interactiva, demo y muda (para pruebas)
  libro.py          exporta la partida a Markdown (con acciones libres, notas y renombrados)
  fuentes.py        catálogo de referencias
tests/test_forja.py, tests/test_libre.py, tests/datos/ (corpus de frases)
tools/              evaluar_corpus, comparar_vocabulario, compilar_vocabulario
```

### Añadir una escena

```python
Escena(
    id="puente_roto", etapa=6,
    requiere=lambda w: w.con("aliado"),        # precondición sobre el mundo
    fuentes=(("propp", "las tareas difíciles"),),
    texto=["{ambiente}", "{aliado.Cap} mira el puente roto. «Tú primero», dice."],
    opciones=[
        Opcion("Cruzar por la cuerda", "valor", dif=7,
               ok=res("Llegas al otro lado.", confianza("aliado", 1)),
               mal=res("Resbalas.", vigor(-2))),
    ],
)
```

Añádela a la lista de su acto y al paso correspondiente de `PLAN` en `motor.py`.
Las plantillas usan `{meta.de}`, `{hogar.a}`, `{aliado.nombre}`, `{heroe.o}`,
`{villano.Cap}`... para que el género y el número concuerden en cualquier
universo.

## Pruebas

```
python -m unittest discover -s tests
```

La prueba clave juega **400 partidas con decisiones al azar** y exige que ninguna
rompa las reglas del universo: ningún muerto actúa, nadie ausente acompaña, no
quedan huecos en las plantillas, no hay preposiciones duplicadas ni frases en
minúscula, y todas terminan en un final. Otras pruebas comprueban que la misma
semilla repite la historia y que semillas distintas dan historias distintas.

`tests/test_libre.py` comprueba lo que hace seguro el deshacer: `[a, b, /atras, c]`
deja el mundo **idéntico** (hasta el último dado y la crónica) a `[a, c]`; cargar
un guardado reproduce la partida sin diferencias; y 100 partidas aleatorias que
mezclan opciones, frases libres y comandos no rompen la coherencia.

## Límites (es un prototipo)

- 21 escenas y 4 géneros: la variedad es real pero finita; a la tercera o cuarta
  partida con el mismo género empiezas a reconocer las piezas. (Es un
  límite que algunos críticos señalan también en *Wildermyth*.)
- El texto es de plantilla: coherente, pero no tan fluido como el de un humano
  o un modelo de lenguaje.
- Solo dos tramas de Booker; faltan comedia, viaje y regreso, etc.
- El texto libre reconoce raíces de palabras, no significados (véanse las cifras
  de arriba). Solo español.
- Las acciones libres afectan al estado (ventaja, vigor, pistas, confianza) pero no
  inventan escenas nuevas: lo que cambia la trama sigue pasando por las opciones.

Ideas para seguir: más escenas por etapa, más géneros (western, histórico),
más tramas, un «mundo persistente» entre partidas, o un editor para que
cualquiera añada escenas sin tocar Python.
