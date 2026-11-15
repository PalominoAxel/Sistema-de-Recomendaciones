"""Modulo 3 - Orquestador (Python) del Motor de Recomendacion.

Punto de entrada unico del sistema: invoca al Modulo Scala (precios y
catalogo), invoca al Modulo Prolog (red semantica de recomendaciones)
y combina ambas respuestas en un menu interactivo para el usuario.
"""

from array import array

from modelos import CLIENTES_DISPONIBLES, Recomendacion
from prolog_bridge import MotorPrologo
from scala_bridge import MotorScala


def preparar_pipeline(cliente):
    """Ejecuta Scala con el tipo de cliente elegido (precios con
    descuento), y deja lista la base de conocimiento combinada para
    Prolog. Devuelve (catalogo, motor_prolog)."""
    print(f"Ejecutando Modulo Scala (scala-cli) para cliente {cliente.tipo}...")
    cotizacion = MotorScala().cotizar(cliente.tipo, cliente.nombre, {})

    print(f"  -> catalogo recibido: {len(cotizacion.catalogo)} productos")
    print(f"  -> hechos es_un/2 recibidos: {len(cotizacion.hechos_prolog)}")

    print("Preparando base de conocimiento para el Modulo Prolog...")
    motor_prolog = MotorPrologo()
    motor_prolog.construir_base_conocimiento(cotizacion.hechos_prolog)

    return cotizacion.catalogo, motor_prolog


def resumen_precios(catalogo) -> str:
    # "Arreglos": a diferencia de una lista generica, array.array
    # guarda solo numeros de un tipo fijo ("d" = double), igual que
    # los arreglos de precios de un lenguaje tipado.
    precios = array("d", [producto.precio for producto in catalogo])
    if not precios:
        return "catalogo vacio"
    return (
        f"min=${min(precios):.2f}  "
        f"max=${max(precios):.2f}  "
        f"promedio=${sum(precios) / len(precios):.2f}"
    )


def mostrar_catalogo(catalogo) -> None:
    print("\n=== CATALOGO (recibido desde Scala) ===")
    for indice, producto in enumerate(catalogo, start=1):
        disponibilidad = "en stock" if producto.stock > 0 else "agotado"
        descuento = f"-{producto.descuento:.0%}" if producto.descuento else ""
        print(
            f" {indice:2d}. {producto.nombre:<22} {producto.categoria:<12} "
            f"${producto.precio:>8.2f} -> ${producto.precio_final:>8.2f} {descuento:>4}  "
            f"({disponibilidad})"
        )
    print(f" Resumen de precios: {resumen_precios(catalogo)}")


def elegir_cliente():
    nombre = input("Tu nombre: ").strip() or "Invitado"
    print("\n=== TIPO DE CLIENTE ===")
    for clave, clase in CLIENTES_DISPONIBLES.items():
        print(f" {clave}. {clase.tipo}")
    while True:
        opcion = input("Elige un tipo de cliente (1-3): ").strip()
        clase_cliente = CLIENTES_DISPONIBLES.get(opcion)
        if clase_cliente is not None:
            return clase_cliente(nombre)
        print("Opcion invalida, intenta de nuevo.")


def consultar_recomendacion(motor_prolog: MotorPrologo, producto) -> Recomendacion:
    datos = motor_prolog.consultar_producto(producto.nombre)
    return Recomendacion(
        producto=producto,
        categorias_heredadas=datos["categorias"],
        propiedades=datos["propiedades"],
        accesorios=datos["accesorios"],
    )


def mostrar_total(cliente, carrito: dict) -> None:
    if not carrito:
        print("El carrito esta vacio.")
        return
    print("\nScala esta calculando el total del carrito...")
    cotizacion = MotorScala().cotizar(cliente.tipo, cliente.nombre, carrito)
    print(f"\n=== CARRITO DE {cliente.nombre} (cliente {cliente.tipo}) ===")
    for linea in cotizacion.lineas:
        print(f" {linea.producto.nombre:<22} x{linea.cantidad:<3} "
              f"${linea.precio_unitario:>8.2f} c/u = ${linea.subtotal:>9.2f}")
    print(f" Subtotal sin descuento: ${cotizacion.subtotal:>9.2f}")
    print(f" Ahorro:                 ${cotizacion.ahorro:>9.2f}")
    print(f" TOTAL (Scala):          ${cotizacion.total:>9.2f}")


def menu_recomendaciones(catalogo, motor_prolog: MotorPrologo, cliente) -> None:
    indice_por_numero = {str(i): p for i, p in enumerate(catalogo, start=1)}
    carrito = {}  # {id_producto: cantidad}
    while True:
        print("\nOpciones:  <numero> ver recomendacion  |  a <numero> agregar al carrito")
        entrada_usuario = input("           carrito  |  catalogo  |  salir\n> ").strip().lower()

        if entrada_usuario == "salir":
            break
        if entrada_usuario == "carrito":
            mostrar_total(cliente, carrito)
            continue
        if entrada_usuario == "catalogo":
            mostrar_catalogo(catalogo)
            continue

        agregar = entrada_usuario.startswith("a ")
        numero = entrada_usuario[2:].strip() if agregar else entrada_usuario
        if numero not in indice_por_numero:
            print("Entrada invalida: escribe un numero del catalogo o una opcion.")
            continue

        producto = indice_por_numero[numero]
        if agregar:
            if carrito.get(producto.id, 0) >= producto.stock:
                print(f"No hay stock suficiente de {producto.nombre}.")
                continue
            carrito[producto.id] = carrito.get(producto.id, 0) + 1
            print(f"Agregado {producto.nombre} (x{carrito[producto.id]}).")

        print(f"\nConsultando Modulo Prolog para '{producto.nombre}'...")
        recomendacion = consultar_recomendacion(motor_prolog, producto)
        if agregar:
            print(f" Prolog sugiere acompanarlo con: {', '.join(recomendacion.accesorios) or 'nada'}")
            continue
        print(f" Herencia: {' -> '.join(recomendacion.categorias_heredadas)}")
        print(f" Propiedades: {', '.join(recomendacion.propiedades)}")
        print(f" {recomendacion.resumen()}")


def main() -> None:
    print("=== MOTOR DE RECOMENDACION: ORQUESTADOR PYTHON ===")
    cliente = elegir_cliente()
    print(cliente.describir())

    catalogo, motor_prolog = preparar_pipeline(cliente)
    mostrar_catalogo(catalogo)

    menu_recomendaciones(catalogo, motor_prolog, cliente)
    print(f"\nHasta luego, {cliente.nombre}.")


if __name__ == "__main__":
    main()
