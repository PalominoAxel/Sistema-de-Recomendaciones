# Tema 3: Motor de Recomendación para Tienda/E-commerce

## 8. DISEÑO DEL SISTEMA

### 8.1 Diseño de módulos

El sistema se organiza en **tres módulos**, cada uno resolviendo la parte del
problema para la que su paradigma es más natural:

**Módulo 1 — Scala (Funcional): Procesamiento de catálogo y descuentos**
Recibe el catálogo de productos y las órdenes de los clientes. Usando
funciones puras (`filter`, `map`, pattern matching) calcula qué productos
están disponibles, agrupa el catálogo por categoría y aplica reglas de
descuento según la categoría del producto y el tipo de cliente. Su salida
final no es solo el total del carrito: también **traduce cada producto del
catálogo a hechos Prolog** (`es_un/2`), dejando la base de conocimiento lista
para el siguiente módulo. Este módulo nunca modifica estado compartido: cada
función recibe datos y devuelve datos nuevos (inmutabilidad).

**Módulo 2 — Prolog (Lógico): Red Semántica de compatibilidades y categorías**
Recibe los hechos generados por Scala (jerarquía `es_un`) y los combina con
una base de conocimiento propia de propiedades (`propiedad/2`) y
compatibilidades (`compatible/2`). A partir de esto, por **resolución e
unificación**, infiere:
- a qué categorías pertenece un producto (herencia transitiva),
- qué propiedades hereda de su categoría,
- qué accesorios son recomendables para él.

Este módulo representa el "razonamiento" del motor de recomendación: no
calcula precios ni filtra listas, solo responde preguntas sobre relaciones
semánticas entre conceptos.

**Módulo 3 — Python (Orquestador/Integrador, implementado en `python/`)**
Es el punto de entrada único del sistema. Su responsabilidad es
orquestar, no calcular: invoca por `subprocess` al módulo Scala (con
`scala-cli`) para obtener el catálogo, el total del carrito de
demostración y los hechos Prolog; prepara con esos hechos la base de
conocimiento combinada que necesita el módulo lógico; invoca por
`subprocess` al módulo Prolog (con `swipl`) para obtener, para el
producto que el usuario elige en un menú interactivo, su herencia de
categorías, propiedades y accesorios recomendados; y combina ambas
respuestas en el resultado final que se muestra al usuario. Es también
el módulo donde se demuestra el paradigma orientado a objetos del
curso (clases, objetos y herencia — ver 10.3), como contraparte del
paradigma funcional de Scala y el lógico de Prolog. El mecanismo de
comunicación realmente implementado se describe en 8.4.

```
 ┌──────────────┐      hechos es_un/2       ┌──────────────┐
 │   MÓDULO     │ ────────────────────────▶ │   MÓDULO     │
 │   SCALA      │                           │   PROLOG     │
 │ (catálogo,   │                           │ (red         │
 │ descuentos)  │ ◀──────────────────────── │ semántica)   │
 └──────────────┘    accesorios inferidos   └──────────────┘
         ▲                                          ▲
         │                 invoca / combina         │
         └───────────────┬──────────────────────────┘
                          │
                 ┌──────────────┐
                 │   MÓDULO     │
                 │   PYTHON     │
                 │(orquestador) │
                 └──────────────┘
                          ▲
                          │
                      Usuario final
```

### 8.2 Flujo del sistema

1. **Entrada de datos**: se define el catálogo de productos (nombre,
   categoría, subtipo, precio, stock) y el carrito del cliente actual
   (productos deseados, cantidad, tipo de cliente).
2. **Filtrado (Scala)**: el módulo Scala filtra el catálogo según
   disponibilidad de stock y rango de precio solicitado (`filter`).
3. **Organización (Scala)**: el catálogo filtrado se agrupa por categoría
   (`Map[String, List[Producto]]`) para facilitar su análisis.
4. **Cálculo de precios (Scala)**: mediante *pattern matching* sobre
   `(categoria, tipoCliente)` se determina el descuento aplicable, y se
   calcula el precio final de cada ítem y el total del carrito.
5. **Exportación a hechos (Scala → Prolog)**: cada producto del catálogo se
   traduce a hechos `es_un(instancia, subtipo).` y `es_un(subtipo,
   categoria).`, que constituyen la entrada de la Red Semántica.
6. **Carga de la base de conocimiento (Prolog)**: el módulo Prolog incorpora
   los hechos recibidos junto con sus propias reglas de `propiedad/2` y
   `compatible/2`.
7. **Inferencia (Prolog)**: por resolución, el motor lógico calcula para el
   producto consultado: (a) toda su cadena de categorías (herencia
   transitiva `es_un_transitivo/2`), (b) las propiedades heredadas
   (`tiene_propiedad/2`), y (c) los accesorios recomendados
   (`recomendar_accesorio/2`).
8. **Combinación de resultados (futuro Módulo Python)**: el orquestador
   junta el precio final calculado en Scala con las recomendaciones de
   accesorios inferidas en Prolog.
9. **Recomendación final**: se entrega al cliente el precio con descuento
   aplicado más la lista de accesorios compatibles sugeridos para su compra.

### 8.3 Modelo de datos

**En Scala** (estructuras inmutables, `case class`):

```scala
case class Producto(
    id: Int,
    nombre: String,     // átomo Prolog, ej: "laptop_hp"
    categoria: String,  // ej: "electronica"
    subtipo: String,    // ej: "laptop"
    precio: Double,
    stock: Int
)

case class ItemCarrito(producto: Producto, cantidad: Int)

case class Carrito(
    cliente: String,
    tipoCliente: String, // "regular" | "premium" | "nuevo"
    items: List[ItemCarrito]
)
```

**En Prolog** (hechos de la Red Semántica):

```prolog
% jerarquía / instancias
es_un(laptop_hp, laptop).
es_un(laptop, electronica).
es_un(electronica, producto).

% propiedades
propiedad(electronica, requiere_electricidad).

% compatibilidades
compatible(laptop, mouse).
```

Existe una correspondencia directa campo a campo: `Producto.nombre` se
convierte en el primer argumento de un hecho `es_un/2`, y
`Producto.subtipo`/`Producto.categoria` en el segundo argumento de los dos
niveles de jerarquía generados.

### 8.4 Comunicación entre lenguajes

**Mecanismo actual (esta entrega):** comunicación por **archivos de texto en
formato de hechos Prolog**. El módulo Scala imprime/escribe una lista de
líneas con la forma `es_un(X, Y).`, que son sintácticamente hechos Prolog
válidos. El módulo Prolog puede incorporar ese texto (por ejemplo,
concatenándolo a su propio archivo `.pl` o cargándolo con `consult/1`) antes
de ejecutar sus reglas de inferencia. Esto desacopla completamente ambos
módulos: Scala no necesita saber nada de resolución lógica, y Prolog no
necesita saber nada de precios o descuentos.

**Integración implementada con Python (`python/`):** Python actúa como
orquestador usando `subprocess` para invocar ambos ejecutables. El flujo
real, en `python/main.py` + `python/scala_bridge.py` +
`python/prolog_bridge.py`:

1. `MotorScala.cotizar(tipo, cliente, carrito)` corre
   `scala-cli run scala/MotorRecomendacion.scala -- cotizar <tipo> <cliente> <id:cant>...`
   con `subprocess.run([...], capture_output=True)`. En este modo, Scala
   recibe por **argumentos** el tipo de cliente elegido por el usuario y
   los productos de su carrito, y responde por **stdout** con el catálogo
   completo, una línea `PRECIO:id:descuento:precio_final` por producto
   (descuento obtenido por *pattern matching* para ese tipo de cliente),
   una línea `ITEM:id:cantidad:unitario:subtotal` por ítem del carrito,
   el `SUBTOTAL` sin descuento, el `TOTAL CARRITO` y los hechos `es_un/2`
   generados (todo extraído con expresiones regulares). Sin argumentos,
   Scala conserva su demo original.
2. `MotorPrologo.construir_base_conocimiento(...)` escribe esos hechos en
   un archivo `prolog/catalogo_generado.pl` (generado, no versionado) que
   combina los hechos recibidos de Scala con el resto de la base de
   conocimiento de `red_semantica.pl` — descartando de este último los
   hechos `es_un/2` que Scala ya vuelve a generar, para no duplicarlos, y
   conservando únicamente los 3 hechos de nivel superior
   (`categoría -> producto`) que Scala no genera.
3. `MotorPrologo.consultar_producto(nombre)` ejecuta
   `swipl -q prolog/catalogo_generado.pl -- <producto>`, capturando su
   salida estándar. Para esto, `red_semantica.pl` incorpora dos
   predicados nuevos (no se modificó `main/0`): `consultar/1`, que
   imprime con `write/1` + `nl/0` líneas `ETIQUETA:valor` (categorías
   heredadas, propiedades, accesorios) para un solo producto; y
   `entrada/0`, el punto de entrada real del archivo
   (`:- initialization(entrada, main).`), que llama a `consultar/1` si
   recibe un producto como argumento de línea de comandos, o conserva el
   comportamiento original (`main/0`, la demo fija) si se ejecuta sin
   argumentos — así el módulo Prolog sigue funcionando de forma
   independiente, igual que en la entrega anterior.
   Además, `exportar_red/0` (invocado con el argumento especial
   `__red__`) imprime todos los arcos de la red (`ES_UN:x:y`,
   `PROPIEDAD:x:p`, `COMPATIBLE:x:a`), que la interfaz web usa para
   dibujar el grafo de la red semántica.
4. Python parsea esa salida de texto (`str.partition(':')`) y la combina
   con los precios y el total obtenidos de Scala para construir la
   respuesta final al usuario, ya sea en el menú de consola
   (`main.py`) o en la interfaz web (`app.py`).

Este diseño (texto plano por `stdout`/archivos intermedios) se eligió
porque no requiere librerías externas ni frameworks de serialización
complejos, manteniéndose dentro del nivel introductorio pedido, y porque es
el mecanismo más simple de depurar: en cualquier punto se puede inspeccionar
el archivo de hechos intermedio (`prolog/catalogo_generado.pl`) para
verificar qué se está comunicando. El ejecutable usado para el módulo
lógico es **SWI-Prolog** (`swipl`), que es el disponible en el entorno de
desarrollo; `red_semantica.pl` sigue siendo compatible con GNU
Prolog/OneCompiler para su uso independiente (`main/0`).

---

## 9. IMPLEMENTACIÓN EN SCALA

El código completo está en [`scala/MotorRecomendacion.scala`](../scala/MotorRecomendacion.scala)
(copiar y pegar directamente en [Scastie](https://scastie.scala-lang.org/)).

### Explicación paso a paso

1. **Modelo de datos (`case class`)** — `Producto`, `ItemCarrito` y
   `Carrito` son estructuras de datos inmutables. Una vez creada una
   instancia, sus campos no cambian; cualquier "modificación" se hace
   creando una nueva instancia. Esto es el pilar de la inmutabilidad
   funcional.

2. **Catálogo (`List[Producto]`)** — `catalogo` es una lista literal de
   seis productos de ejemplo, cubriendo dos categorías (`electronica`,
   `ropa`) y cuatro subtipos (`laptop`, `smartphone`, `camisa`, `pantalon`).

3. **Filtrado (`filter`)** — `filtrarPorPrecio` usa una función anónima
   `p => p.precio >= min && p.precio <= max` pasada a `filter`; devuelve una
   **nueva** lista sin modificar la original. `filtrarConStock` hace lo
   mismo con la sintaxis abreviada `_.stock > 0`.

4. **Organización (`Map`)** — `agruparPorCategoria` usa `groupBy`, que
   convierte la `List[Producto]` en un `Map[String, List[Producto]]`
   indexado por categoría, útil para mostrar el catálogo organizado.

5. **Pattern Matching (descuentos)** — `calcularDescuento` recibe una tupla
   `(categoria, tipoCliente)` y la compara contra varios patrones literales
   (`("electronica", "premium")`, etc.), incluyendo un comodín `(_, "nuevo")`
   para clientes nuevos sin importar la categoría, y un caso por defecto
   `_` que no aplica descuento. Es el ejemplo central de *pattern matching*
   pedido por la rúbrica.

6. **Cálculo del carrito (`map` + `sum`)** — `calcularTotalCarrito` recorre
   los ítems del carrito, calcula el precio con descuento de cada uno
   (`map`) y los suma (`sum`), sin usar ningún bucle imperativo ni variable
   mutable.

7. **Generación de hechos Prolog** — `generarHechosProlog` es la función que
   materializa la comunicación entre módulos (ver 8.4): por cada producto
   construye el string `es_un(nombre, subtipo).` y, usando `distinct`, un
   único hecho `es_un(subtipo, categoria).` por cada subtipo presente en el
   catálogo (evitando duplicados si hay varios productos del mismo subtipo).

8. **`main`** — ejecuta, en orden, cada una de las funciones anteriores e
   imprime sus resultados por consola, incluyendo al final la lista de
   hechos Prolog generados, lista para copiarse en el módulo lógico.

---

## RED SEMÁNTICA E IMPLEMENTACIÓN EN PROLOG

El código completo está en [`prolog/red_semantica.pl`](../prolog/red_semantica.pl)
(compatible con GNU Prolog / OneCompiler; ejecuta `main/0` vía
`:- initialization(main).`).

### 1. Red Semántica (diagrama)

```
                              producto
                             /        \
                     electronica       ropa
                    /           \      /    \
               laptop      smartphone camisa  pantalon
               /    \         /    \      \        \
      laptop_hp  laptop_asus  smartphone_sams  camisa_polo  pantalon_jean
                               smartphone_xiaomi

Propiedades (heredadas hacia abajo por la jerarquía es_un):
  producto    --propiedad--> tiene_precio
  electronica --propiedad--> requiere_electricidad
  laptop      --propiedad--> portatil
  smartphone  --propiedad--> portatil
  ropa        --propiedad--> textil

Compatibilidades (enlaces NO jerárquicos, accesorio recomendado):
  laptop     --compatible--> mouse, funda_laptop, audifonos
  smartphone --compatible--> funda_smartphone, cargador_rapido, audifonos
  camisa     --compatible--> corbata
  pantalon   --compatible--> cinturon
```

Las flechas `es_un` forman la jerarquía (herencia); las flechas
`propiedad` cuelgan de cada nodo una característica heredable; las flechas
`compatible` son relaciones asociativas (no jerárquicas) usadas para
recomendar accesorios.

### 2. Explicación paso a paso del código Prolog

1. **Hechos `es_un/2`** — Representan los arcos de la jerarquía de la red
   semántica. Se dividen en dos niveles: arcos de *jerarquía de concepto*
   (`laptop -> electronica -> producto`) y arcos de *instancia*
   (`laptop_hp -> laptop`), estos últimos equivalentes a los hechos que
   genera el módulo Scala.

2. **Hechos `propiedad/2`** — Asocian una característica a un nodo de la
   jerarquía. No se repiten en cada instancia: por ejemplo
   `smartphone_sams` no tiene su propia entrada en `propiedad/2`, la hereda
   de `smartphone` mediante la regla `tiene_propiedad/2`.

3. **Hechos `compatible/2`** — Asocian un subtipo con los accesorios que le
   son compatibles. Se definen a nivel de subtipo (`laptop`), no de
   instancia, para que todas las laptops del catálogo reciban las mismas
   recomendaciones sin tener que repetir el hecho por cada producto.

4. **Regla `es_un_transitivo/2`** — Implementa la **herencia transitiva**
   de la red: el caso base cubre la relación directa (`es_un(X, Y)`), y el
   caso recursivo busca un nodo intermedio `Z` (`es_un(X, Z)`) y resuelve
   recursivamente `es_un_transitivo(Z, Y)`. Así, `laptop_hp` se reconoce
   como `laptop`, `electronica` y `producto` con una sola llamada.

5. **Regla `tiene_propiedad/2`** — Usa la misma idea: si el nodo no tiene la
   propiedad directamente, sube un nivel en la jerarquía (`es_un(X, Y)`) y
   pregunta recursivamente si `Y` la tiene. Esto implementa la **herencia
   de propiedades** mencionada en la rúbrica.

6. **Regla `recomendar_accesorio/2`** — Primero intenta compatibilidad
   directa; si no la encuentra (o además de encontrarla), sube por la
   jerarquía con `es_un_transitivo/2` hasta encontrar un nodo que sí tenga
   accesorios compatibles definidos. Esto permite que `laptop_hp` reciba las
   recomendaciones definidas a nivel de `laptop`, sin tener que duplicarlas
   por cada producto concreto.

7. **Predicado `main/0`** — Usa `forall/2` para recorrer **todas** las
   soluciones de una consulta e imprimir una línea por cada una con
   `write/1` y `nl/0` (sin usar `format/2` ni librerías externas). Se
   consulta la herencia transitiva, las propiedades heredadas y las
   recomendaciones de accesorios, primero para `laptop_hp` y luego para
   `smartphone_xiaomi`, demostrando que las mismas reglas generalizan a
   cualquier instancia del catálogo.

8. **Directiva `:- initialization(main).`** — Es el punto de entrada
   requerido por la ejecución por lotes en GNU Prolog/OneCompiler: al
   cargar el archivo, el intérprete ejecuta automáticamente `main/0` y
   termina, imprimiendo todo el resultado por salida estándar.

9. **Predicado `consultar/1` y punto de entrada `entrada/0`** — Se
   agregaron para la integración con Python (ver 8.4 y sección 10), sin
   modificar nada de lo anterior. `consultar/1` repite el mismo tipo de
   consultas que `main/0` (herencia transitiva, propiedades, accesorios)
   pero para un solo producto recibido como argumento, imprimiendo cada
   dato con una etiqueta (`CATEGORIA:`, `PROPIEDAD:`, `ACCESORIO:`) fácil
   de parsear línea por línea. `entrada/0` decide, leyendo
   `current_prolog_flag(argv, Argv)`, si se recibió un producto por línea
   de comandos (llama a `consultar/1`) o no (llama a `main/0`, el
   comportamiento original). La directiva final del archivo pasó de
   `:- initialization(main).` a `:- initialization(entrada, main).`: la
   forma de dos argumentos con `main` es el modismo de SWI-Prolog para
   declarar el punto de entrada cuando el archivo se ejecuta como script
   (`swipl red_semantica.pl -- argumento`).

---

## 10. IMPLEMENTACIÓN EN PYTHON (Módulo 3 — Orquestador)

El código completo está en [`python/`](../python/): `base.py`,
`scala_bridge.py`, `prolog_bridge.py`, `modelos.py`, `main.py` y `app.py`.
Hay dos puntos de entrada, ejecutados desde la raíz del proyecto:

- **Interfaz web:** `python -m streamlit run python/app.py` (requiere
  `pip install -r python/requirements.txt`).
- **Consola:** `python python/main.py`.

### 10.1 Rol del módulo

A diferencia de Scala (funcional) y Prolog (lógico), que resuelven una
parte concreta del problema, Python no calcula precios ni infiere
compatibilidades: **orquesta**. Ejecuta los otros dos módulos como
procesos externos, traduce su salida de texto a datos Python, y conduce
la interacción con el usuario. El mecanismo de comunicación entre los
tres módulos ya se explicó en la sección 8.4; esta sección se enfoca en
cómo el código Python demuestra, de paso, los temas del curso
(características multiparadigma, tipos de datos, control de flujo,
estructuras de datos, funciones, módulos, clases y herencia).

### 10.2 Explicación paso a paso del código

1. **`base.py` — clase `MotorExterno`** — Concentra lo que Scala y
   Prolog necesitan por igual: localizar su ejecutable (primero en
   rutas conocidas de instalación, luego en el `PATH`) y ejecutarlo con
   `subprocess.run(..., capture_output=True, text=True)`. Se invoca con
   **rutas relativas** y `cwd` fijo en la raíz del proyecto, en vez de
   rutas absolutas, porque la carpeta del proyecto tiene una tilde
   ("Recomendación") que algunos lanzadores nativos de Windows no
   decodifican bien si llega como argumento de línea de comandos.

2. **`scala_bridge.py` — clase `MotorScala(MotorExterno)`** (herencia) —
   `cotizar` corre Scala en modo `cotizar` pasándole el tipo de cliente
   y el carrito como argumentos y, con expresiones regulares (**cadenas
   de texto**), extrae del *stdout*: la lista de `Producto(...)`, el
   descuento y precio final de cada uno (`PRECIO:`), las líneas del
   carrito (`ITEM:`), el subtotal, el total y los hechos `es_un(...)`.
   Todo se devuelve en un objeto `Cotizacion`.

3. **`prolog_bridge.py` — clase `MotorPrologo(MotorExterno)`** (herencia)
   — `construir_base_conocimiento` combina los hechos de Scala con el
   resto de `red_semantica.pl` (ver 8.4) escribiendo
   `prolog/catalogo_generado.pl`. `consultar_producto` corre
   `swipl -q prolog/catalogo_generado.pl -- <producto>` y parsea cada
   línea `ETIQUETA:valor` de la salida con `str.partition(':')`,
   acumulando los valores en un **diccionario** de **listas**.
   `exportar_red` obtiene todos los arcos de la red como **tuplas**.

4. **`modelos.py` — paradigma orientado a objetos** — `Producto`,
   `LineaCarrito`, `Cotizacion` y `Recomendacion` son `@dataclass` (equivalente Python de las
   `case class` de Scala). `Cliente` es la clase base de una jerarquía
   con **herencia**: `ClienteRegular`, `ClientePremium` y `ClienteNuevo`
   heredan de `Cliente` y sobrescriben (polimorfismo) el método
   `beneficio()`. A propósito, esta jerarquía **no** recalcula el
   porcentaje de descuento (eso sigue siendo responsabilidad exclusiva
   del *pattern matching* de Scala, para no duplicar la lógica de
   precios en dos lenguajes); solo modela, de forma orientada a
   objetos, los distintos tipos de cliente y su beneficio asociado.
   `CLIENTES_DISPONIBLES` es un **diccionario** que mapea la opción de
   menú a la clase (**objeto** tipo `type`) correspondiente.

5. **`main.py` — orquestación e interacción con el usuario** — Importa
   (**módulos**) `base`, `scala_bridge`, `prolog_bridge`, `modelos` y
   `array` de la librería estándar. `resumen_precios` usa
   `array.array("d", ...)` — un **arreglo** de tipo fijo (double), a
   diferencia de una lista genérica — para calcular mínimo, máximo y
   promedio de precios con `min()`, `max()` y `sum()`. `mostrar_catalogo`
   recorre la **lista** de productos con un bucle `for` e
   `enumerate` (**instrucción repetitiva**), formateando cada línea con
   f-strings (**cadenas de texto**). `elegir_cliente` usa un bucle
   `while True` con `input()` (**ingreso de datos por teclado**) para
   pedir el nombre y validar la opción antes de instanciar la subclase
   de `Cliente` elegida; el `tipo` de ese objeto se envía a Scala, de
   modo que los precios mostrados ya incluyen el descuento que le
   corresponde. `menu_recomendaciones` es el ciclo principal: un número
   muestra la recomendación de Prolog; `a <número>` agrega el producto a
   un carrito (**diccionario** `{id: cantidad}`) y muestra los
   accesorios que Prolog sugiere; `carrito` pide a Scala el total con
   descuento (`mostrar_total`). El flujo de `main()` en sí —elegir
   cliente, correr el pipeline, mostrar catálogo, correr el menú,
   despedirse— es una secuencia de **instrucciones de control
   secuenciales** con **funciones** que dividen cada responsabilidad.

6. **`app.py` — interfaz web con Streamlit** — Es solo una capa visual
   sobre los mismos puentes: no calcula precios ni infiere nada. Tiene
   cuatro pestañas:
   - **Catálogo:** tarjetas con precio original tachado y precio final
     calculado por Scala, filtros por categoría, precio y stock, y un
     botón que abre la recomendación de Prolog (herencia, propiedades,
     accesorios y un mini-grafo del producto).
   - **Carrito:** al agregar un producto, Prolog sugiere accesorios; el
     total oficial lo calcula Scala (`calcularTotalCarrito`) con un botón.
   - **Red semántica:** grafo completo exportado por Prolog
     (`exportar_red/0`), filtrable por categoría y con el camino
     `es_un` del producto elegido resaltado.
   - **Cómo funciona:** diagrama de la arquitectura y los hechos que
     Scala envía a Prolog.

   Como cada llamada a Scala o Prolog es un proceso externo que tarda
   unos segundos, las respuestas se guardan en caché (`st.cache_data`):
   la misma entrada siempre produce la misma salida.

### 10.3 Correspondencia con los temas del curso

| Tema del curso | Dónde se demuestra |
|---|---|
| Características del lenguaje multiparadigma | Python se usa aquí como orquestador imperativo, con objetos (`modelos.py`) y con listas/funciones de estilo funcional (`enumerate`, comprensiones en `resumen_precios`), a diferencia de Scala (funcional puro) y Prolog (lógico) |
| Tipos de datos, variables y operadores | Atributos `int`/`str`/`float`/`list` de `Producto`/`Recomendacion`; operadores aritméticos en `resumen_precios` |
| `print()` | En todo `main.py` para mostrar catálogo, menús y resultados |
| Ingreso de datos por teclado | `input()` en `elegir_cliente` y `menu_recomendaciones` |
| Instrucciones de control secuenciales | Flujo de `main()`: pipeline → catálogo → cliente → menú → despedida |
| Cadenas de texto | Expresiones regulares en `scala_bridge.py`, `str.partition`/`str.isdigit` en `prolog_bridge.py`/`main.py`, f-strings en todo el módulo |
| Instrucciones condicionales | Validaciones de opción en `elegir_cliente` y `menu_recomendaciones`; filtro de hechos en `prolog_bridge.py` |
| Instrucciones repetitivas | Bucles `for`/`while` en `mostrar_catalogo`, `elegir_cliente`, `menu_recomendaciones` |
| Arreglos | `array.array("d", ...)` en `resumen_precios` |
| Listas, tuplas y diccionarios | Catálogo como lista de `Producto`; `indice_por_numero` y `CLIENTES_DISPONIBLES` como diccionarios; resultado de `_parsear_salida` como diccionario de listas |
| Funciones | Cada responsabilidad (`preparar_pipeline`, `mostrar_catalogo`, `elegir_cliente`, `consultar_recomendacion`, `menu_recomendaciones`) es una función con una sola tarea |
| Módulos | `main.py` importa `base`, `scala_bridge`, `prolog_bridge`, `modelos` y la librería estándar (`array`); `app.py` además usa la librería externa `streamlit` |
| Clases y objetos | `Producto`, `Recomendacion`, `Cliente` y las clases `MotorExterno`/`MotorScala`/`MotorPrologo` |
| Herencia | `MotorScala`/`MotorPrologo` heredan de `MotorExterno`; `ClienteRegular`/`ClientePremium`/`ClienteNuevo` heredan de `Cliente` y sobrescriben `beneficio()` (polimorfismo) |
