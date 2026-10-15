// ============================================================
// MOTOR DE RECOMENDACIÓN PARA E-COMMERCE
// MÓDULO FUNCIONAL (SCALA)
// ------------------------------------------------------------
// Responsabilidad de este módulo: procesar el catálogo de
// productos, filtrar/organizar datos, calcular descuentos y
// totales de carrito, y finalmente EXPORTAR el catálogo como
// hechos Prolog (es_un/2) para que el Módulo Lógico construya
// sobre ellos su Red Semántica (jerarquía, propiedades y
// compatibilidades).
//
// Paradigma: puramente funcional. Solo se usan:
//   - case class (datos inmutables)
//   - funciones declarativas y anónimas
//   - List, Map
//   - filter, map
//   - pattern matching
// No se usan: Monads, Implicits, Future, Akka, Typeclasses, var.
//
// Compatible con Scastie (https://scastie.scala-lang.org/)
// ============================================================

// ---------- 1. MODELO DE DATOS (case class) ----------

// Representa un producto del catálogo.
// `subtipo` es el nodo de la Red Semántica al que pertenece
// (ej: "laptop"), y `categoria` es el nodo padre (ej: "electronica").
case class Producto(
    id: Int,
    nombre: String, // identificador simbólico -> será un átomo Prolog, ej: "laptop_hp"
    categoria: String, // categoría general, ej: "electronica"
    subtipo: String, // subtipo semántico, ej: "laptop"
    precio: Double,
    stock: Int
)

// Un ítem dentro del carrito: un producto más la cantidad pedida.
case class ItemCarrito(producto: Producto, cantidad: Int)

// Representa el carrito/orden de un cliente.
case class Carrito(
    cliente: String,
    tipoCliente: String, // "regular", "premium" o "nuevo"
    items: List[ItemCarrito]
)

object Main {

  // ---------- 2. CATÁLOGO DE EJEMPLO (List[Producto]) ----------

  val catalogo: List[Producto] = List(
    // --- electronica: laptop ---
    Producto(1, "laptop_hp", "electronica", "laptop", 1200.0, 8),
    Producto(2, "laptop_asus", "electronica", "laptop", 950.0, 0),
    Producto(3, "laptop_dell", "electronica", "laptop", 1100.0, 5),
    // --- electronica: smartphone ---
    Producto(4, "smartphone_sams", "electronica", "smartphone", 700.0, 15),
    Producto(5, "smartphone_xiaomi", "electronica", "smartphone", 300.0, 20),
    Producto(6, "smartphone_motorola", "electronica", "smartphone", 450.0, 12),
    // --- electronica: tablet ---
    Producto(7, "tablet_ipad", "electronica", "tablet", 900.0, 10),
    Producto(8, "tablet_samsung", "electronica", "tablet", 650.0, 0),
    // --- electronica: television ---
    Producto(9, "tv_lg", "electronica", "television", 1300.0, 6),
    Producto(10, "tv_sony", "electronica", "television", 1500.0, 4),
    // --- ropa: camisa ---
    Producto(11, "camisa_polo", "ropa", "camisa", 25.0, 50),
    Producto(12, "camisa_formal", "ropa", "camisa", 35.0, 25),
    // --- ropa: pantalon ---
    Producto(13, "pantalon_jean", "ropa", "pantalon", 40.0, 30),
    Producto(14, "pantalon_cargo", "ropa", "pantalon", 45.0, 18),
    // --- ropa: chaqueta ---
    Producto(15, "chaqueta_cuero", "ropa", "chaqueta", 120.0, 7),
    Producto(16, "chaqueta_jean", "ropa", "chaqueta", 60.0, 0),
    // --- ropa: zapatos ---
    Producto(17, "zapatos_deportivos", "ropa", "zapatos", 55.0, 40),
    Producto(18, "zapatos_formales", "ropa", "zapatos", 70.0, 22),
    // --- hogar: silla / mesa / lampara ---
    Producto(19, "silla_oficina", "hogar", "silla", 150.0, 9),
    Producto(20, "mesa_comedor", "hogar", "mesa", 300.0, 3),
    Producto(21, "lampara_led", "hogar", "lampara", 20.0, 60)
  )

  // ---------- 3. FUNCIONES DE FILTRADO (filter) ----------

  // Función declarativa: filtra productos dentro de un rango de precio.
  def filtrarPorPrecio(productos: List[Producto], min: Double, max: Double): List[Producto] =
    productos.filter(p => p.precio >= min && p.precio <= max)

  // Función que usa una función anónima (_) para quedarse solo con
  // productos que tienen stock disponible.
  def filtrarConStock(productos: List[Producto]): List[Producto] =
    productos.filter(_.stock > 0)

  // ---------- 4. ORGANIZACIÓN DEL CATÁLOGO (Map) ----------

  // Agrupa el catálogo por categoría: Map[String, List[Producto]]
  def agruparPorCategoria(productos: List[Producto]): Map[String, List[Producto]] =
    productos.groupBy(p => p.categoria)

  // ---------- 5. DESCUENTOS (Pattern Matching) ----------

  // Calcula el porcentaje de descuento según la categoría del producto
  // y el tipo de cliente. Este es el caso de uso principal de
  // pattern matching del módulo.
  def calcularDescuento(categoria: String, tipoCliente: String): Double =
    (categoria, tipoCliente) match {
      case ("electronica", "premium") => 0.15
      case ("electronica", "regular") => 0.05
      case ("ropa", "premium")        => 0.20
      case ("ropa", "regular")        => 0.10
      case ("hogar", "premium")       => 0.10
      case ("hogar", "regular")       => 0.03
      case (_, "nuevo")               => 0.05 // descuento de bienvenida, aplica a cualquier categoría
      case _                          => 0.0
    }

  // Aplica el descuento calculado al precio base de un producto.
  def precioConDescuento(producto: Producto, tipoCliente: String): Double = {
    val descuento = calcularDescuento(producto.categoria, tipoCliente)
    producto.precio * (1 - descuento)
  }

  // ---------- 6. CÁLCULO DEL CARRITO (map + sum) ----------

  // Calcula el total del carrito aplicando el descuento a cada ítem.
  def calcularTotalCarrito(carrito: Carrito): Double =
    carrito.items
      .map(item => precioConDescuento(item.producto, carrito.tipoCliente) * item.cantidad)
      .sum

  // ---------- 7. GENERACIÓN DE HECHOS PROLOG ----------
  // Esta es la "frontera" de comunicación entre el Módulo Scala y el
  // Módulo Prolog: convertimos cada producto en hechos es_un/2 con el
  // mismo formato que espera la base de conocimiento en Prolog.

  // Hecho de instancia: es_un(nombre_producto, subtipo).
  def productoAHechoEsUn(p: Producto): String =
    s"es_un(${p.nombre}, ${p.subtipo})."

  // Hecho de jerarquía: es_un(subtipo, categoria).
  def subtipoAHechoEsUn(p: Producto): String =
    s"es_un(${p.subtipo}, ${p.categoria})."

  // Genera la lista completa de hechos Prolog a partir del catálogo.
  // `distinct` evita repetir la relación subtipo->categoria por cada
  // producto que comparte subtipo (ej: dos laptops).
  def generarHechosProlog(productos: List[Producto]): List[String] = {
    val hechosInstancia = productos.map(productoAHechoEsUn)
    val hechosJerarquia  = productos.map(subtipoAHechoEsUn).distinct
    hechosInstancia ++ hechosJerarquia
  }

  // ---------- 8. PUNTO DE ENTRADA ----------

  def main(args: Array[String]): Unit = {

    println("=== CATÁLOGO COMPLETO ===")
    catalogo.foreach(println)

    println("\n=== PRODUCTOS ENTRE 500 Y 1500 CON STOCK (filter) ===")
    val disponibles = filtrarConStock(filtrarPorPrecio(catalogo, 500, 1500))
    disponibles.foreach(println)

    println("\n=== CATÁLOGO AGRUPADO POR CATEGORÍA (Map) ===")
    agruparPorCategoria(catalogo).foreach { case (categoria, productos) =>
      println(s"$categoria -> ${productos.map(_.nombre).mkString(", ")}")
    }

    println("\n=== SIMULACIÓN DE CARRITO (pattern matching en descuentos) ===")
    val carrito = Carrito(
      cliente = "Axel",
      tipoCliente = "premium",
      items = List(
        ItemCarrito(catalogo(0), 1), // laptop_hp x1
        ItemCarrito(catalogo(4), 2)  // camisa_polo x2
      )
    )
    println(s"Cliente: ${carrito.cliente} (${carrito.tipoCliente})")
    carrito.items.foreach { item =>
      val precioFinal = precioConDescuento(item.producto, carrito.tipoCliente)
      println(f"  ${item.producto.nombre}%-20s x${item.cantidad} -> $$${precioFinal}%.2f c/u")
    }
    println(f"TOTAL CARRITO: $$${calcularTotalCarrito(carrito)}%.2f")

    println("\n=== HECHOS PROLOG GENERADOS (salida para el Módulo Lógico) ===")
    generarHechosProlog(catalogo).foreach(println)
  }
}
