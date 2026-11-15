"""Modelo de datos del orquestador, en Python orientado a objetos.

Es el tercer paradigma del proyecto junto al funcional de Scala
(case class + pattern matching) y al logico de Prolog (hechos +
resolucion): aqui se usan Clases, Objetos y Herencia.
"""

from dataclasses import dataclass, field


@dataclass
class Producto:
    id: int
    nombre: str
    categoria: str
    subtipo: str
    precio: float
    stock: int
    # Calculados por Scala segun el tipo de cliente (modo "cotizar").
    descuento: float = 0.0
    precio_final: float = None

    def __post_init__(self):
        if self.precio_final is None:
            self.precio_final = self.precio

    @property
    def nombre_legible(self) -> str:
        return self.nombre.replace("_", " ").title()


@dataclass
class LineaCarrito:
    producto: Producto
    cantidad: int
    precio_unitario: float
    subtotal: float


@dataclass
class Cotizacion:
    """Respuesta completa de Scala para un cliente y su carrito."""
    catalogo: list
    lineas: list
    subtotal: float
    total: float
    hechos_prolog: list

    @property
    def ahorro(self) -> float:
        return self.subtotal - self.total


@dataclass
class Recomendacion:
    producto: Producto
    categorias_heredadas: list = field(default_factory=list)
    propiedades: list = field(default_factory=list)
    accesorios: list = field(default_factory=list)

    def resumen(self) -> str:
        accesorios_texto = ", ".join(self.accesorios) if self.accesorios else "ninguno"
        return (
            f"{self.producto.nombre} ({self.producto.subtipo}/{self.producto.categoria}) "
            f"-> accesorios recomendados: {accesorios_texto}"
        )


class Cliente:
    """Clase base: todo cliente tiene nombre y sabe describirse.

    Las subclases (herencia) especializan el beneficio asociado a su
    tipo. El porcentaje de descuento en si mismo sigue siendo
    responsabilidad exclusiva del Modulo Scala (pattern matching
    sobre categoria/tipoCliente), para no duplicar la logica de
    precios en dos lenguajes distintos; esta jerarquia es la version
    Python, orientada a objetos, de "que tipos de cliente existen".
    """

    tipo = "regular"

    def __init__(self, nombre: str):
        self.nombre = nombre

    def beneficio(self) -> str:
        return "Descuento estandar segun categoria."

    def describir(self) -> str:
        return f"{self.nombre} (cliente {self.tipo}): {self.beneficio()}"


class ClienteRegular(Cliente):
    tipo = "regular"


class ClientePremium(Cliente):
    tipo = "premium"

    def beneficio(self) -> str:
        return "Mayor descuento por categoria + atencion prioritaria."


class ClienteNuevo(Cliente):
    tipo = "nuevo"

    def beneficio(self) -> str:
        return "Cupon de bienvenida: 5% de descuento en cualquier categoria."


CLIENTES_DISPONIBLES = {
    "1": ClienteRegular,
    "2": ClientePremium,
    "3": ClienteNuevo,
}
