"""Puente hacia el Modulo 1 (Scala): lo ejecuta por subprocess con
scala-cli y traduce su salida de texto (catalogo, total del carrito y
hechos Prolog) a datos Python."""

import re
from pathlib import Path

from base import MotorExterno
from modelos import Cotizacion, LineaCarrito, Producto

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_RELATIVA_SCRIPT_SCALA = "scala/MotorRecomendacion.scala"

PATRON_PRODUCTO = re.compile(
    r"Producto\((\d+),\s*(\w+),\s*(\w+),\s*(\w+),\s*([\d.]+),\s*(\d+)\)"
)
PATRON_HECHO_ES_UN = re.compile(r"es_un\([^)]+\)\.")
PATRON_TOTAL = re.compile(r"TOTAL CARRITO:\s*\$?\s*([0-9]+(?:[.,][0-9]+)?)")
PATRON_PRECIO = re.compile(r"^PRECIO:(\d+):([\d.]+):([\d.]+)\s*$", re.MULTILINE)
PATRON_ITEM = re.compile(r"^ITEM:(\d+):(\d+):([\d.]+):([\d.]+)\s*$", re.MULTILINE)
PATRON_SUBTOTAL = re.compile(r"^SUBTOTAL:([\d.]+)\s*$", re.MULTILINE)


class MotorScala(MotorExterno):
    nombre_ejecutable = "scala-cli"
    rutas_conocidas = (
        r"C:\Program Files\scala-cli-x86_64-pc-win32\scala-cli.exe",
    )

    def ejecutar(self, *argumentos: str) -> str:
        ejecutable = self.localizar_ejecutable()
        comando = [ejecutable, "run", RUTA_RELATIVA_SCRIPT_SCALA]
        if argumentos:
            comando += ["--", *argumentos]
        return self._correr(comando, cwd=str(RAIZ_PROYECTO))

    def cotizar(self, tipo_cliente: str, nombre_cliente: str, carrito: dict) -> Cotizacion:
        """Pide a Scala los precios con descuento para tipo_cliente y el
        total de `carrito` ({id_producto: cantidad})."""
        items = [f"{id_}:{cant}" for id_, cant in carrito.items() if cant > 0]
        salida = self.ejecutar("cotizar", tipo_cliente, nombre_cliente or "cliente", *items)

        catalogo = self.extraer_catalogo(salida)
        por_id = {p.id: p for p in catalogo}
        for id_, descuento, final in PATRON_PRECIO.findall(salida):
            producto = por_id[int(id_)]
            producto.descuento = float(descuento)
            producto.precio_final = float(final)

        lineas = [
            LineaCarrito(por_id[int(id_)], int(cant), float(unit), float(sub))
            for id_, cant, unit, sub in PATRON_ITEM.findall(salida)
        ]
        subtotal = PATRON_SUBTOTAL.search(salida)
        return Cotizacion(
            catalogo=catalogo,
            lineas=lineas,
            subtotal=float(subtotal.group(1)) if subtotal else 0.0,
            total=self.extraer_total_carrito(salida),
            hechos_prolog=self.extraer_hechos_prolog(salida),
        )

    @staticmethod
    def extraer_catalogo(salida: str) -> list:
        # El catalogo completo se imprime una sola vez, antes del
        # encabezado del siguiente bloque ("PRODUCTOS ENTRE..."); de lo
        # contrario, los Producto(...) del bloque filtrado (un
        # subconjunto) se contarian dos veces.
        limite = salida.find("PRODUCTOS ENTRE")
        bloque_catalogo = salida[:limite] if limite != -1 else salida

        catalogo = []
        for id_, nombre, categoria, subtipo, precio, stock in PATRON_PRODUCTO.findall(bloque_catalogo):
            catalogo.append(
                Producto(
                    id=int(id_),
                    nombre=nombre,
                    categoria=categoria,
                    subtipo=subtipo,
                    precio=float(precio),
                    stock=int(stock),
                )
            )
        return catalogo

    @staticmethod
    def extraer_hechos_prolog(salida: str) -> list:
        marcador = salida.find("HECHOS PROLOG GENERADOS")
        bloque = salida[marcador:] if marcador != -1 else salida
        return PATRON_HECHO_ES_UN.findall(bloque)

    @staticmethod
    def extraer_total_carrito(salida: str) -> float:
        coincidencia = PATRON_TOTAL.search(salida)
        if not coincidencia:
            raise ValueError("No se encontro 'TOTAL CARRITO' en la salida de Scala")
        return float(coincidencia.group(1).replace(",", "."))
