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

**Módulo 3 — Python (Orquestador/Integrador, diseño para fase futura)**
Será el punto de entrada único del sistema. Su responsabilidad es
orquestar, no calcular: recibe la solicitud del usuario (ej. "quiero
recomendaciones para mi carrito"), invoca al módulo Scala para obtener
precios/descuentos y hechos Prolog, invoca al módulo Prolog para obtener
inferencias de compatibilidad, y combina ambas respuestas en el resultado
final que se muestra al usuario. En esta entrega **solo se diseña su lugar
en la arquitectura** (ver 8.4); su implementación se abordará en la
integración posterior.

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

**Plan de integración futura con Python:** Python actuará como
orquestador usando `subprocess` para invocar ambos ejecutables:

1. Ejecutar el `.jar`/script de Scala con `subprocess.run([...], capture_output=True)`
   y capturar por **stdout** tanto el total del carrito como los hechos
   Prolog generados.
2. Escribir esos hechos en un archivo temporal `catalogo_generado.pl` que se
   agrega a la base de conocimiento de `red_semantica.pl`.
3. Ejecutar GNU Prolog con `subprocess.run(["gprolog", "--consult-file", ...])`,
   capturando su salida estándar (los `write/1` + `nl/0` del predicado
   `main/0`).
4. Parsear esa salida de texto en Python y combinarla con el resultado de
   Scala para construir la respuesta final al usuario.

Este diseño (texto plano por `stdin`/`stdout`/archivos intermedios) se eligió
porque no requiere librerías externas ni frameworks de serialización
complejos, manteniéndose dentro del nivel introductorio pedido, y porque es
el mecanismo más simple de depurar: en cualquier punto se puede inspeccionar
el archivo de hechos intermedio para verificar qué se está comunicando.

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
