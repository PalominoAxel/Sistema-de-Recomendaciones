"""Puente hacia el Modulo 2 (Prolog): combina los hechos es_un/2 que
genero Scala con el resto de la base de conocimiento de
red_semantica.pl (propiedades, compatibilidades, reglas de inferencia)
y consulta swipl por subprocess para un producto puntual."""

import re
from pathlib import Path

from base import MotorExterno

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
ARCHIVO_RED_SEMANTICA = RAIZ_PROYECTO / "prolog" / "red_semantica.pl"
ARCHIVO_GENERADO = RAIZ_PROYECTO / "prolog" / "catalogo_generado.pl"
RUTA_RELATIVA_ARCHIVO_GENERADO = "prolog/catalogo_generado.pl"

# Linea de HECHO es_un(atomo, atomo). con sus dos argumentos
# capturados. Se exige que no tenga sangria y que los argumentos
# empiecen con minuscula (atomos) para no confundirla con el uso de
# es_un(X, Y) dentro del cuerpo de una regla (variables, en mayuscula
# y siempre sangrado en este archivo).
PATRON_ES_UN = re.compile(r"^es_un\(\s*[a-z]\w*\s*,\s*([a-z]\w*)\s*\)\.\s*$")


class MotorPrologo(MotorExterno):
    nombre_ejecutable = "swipl"
    rutas_conocidas = (
        r"C:\Program Files\swipl\bin\swipl.exe",
    )

    def construir_base_conocimiento(self, hechos_es_un: list) -> Path:
        """Escribe prolog/catalogo_generado.pl: los hechos es_un/2 de
        Scala (instancia->subtipo y subtipo->categoria) mas el resto de
        red_semantica.pl (propiedad/2, compatible/2, reglas, consultar/1,
        entrada/0). Se descartan de red_semantica.pl los hechos es_un/2
        que Scala ya volvio a generar, para no duplicarlos; se conservan
        los 3 hechos de nivel superior categoria->producto (electronica,
        ropa, hogar), que Scala no genera.
        """
        texto_original = ARCHIVO_RED_SEMANTICA.read_text(encoding="utf-8")
        lineas_conservadas = []
        for linea in texto_original.splitlines():
            coincidencia = PATRON_ES_UN.match(linea)
            si_la_regenera_scala = coincidencia and coincidencia.group(1) != "producto"
            if si_la_regenera_scala:
                continue
            lineas_conservadas.append(linea)

        encabezado = "% === Hechos es_un/2 generados por el Modulo Scala ==="
        separador = "% === Resto de la base de conocimiento (red_semantica.pl) ==="
        contenido_generado = "\n".join(
            [encabezado, *hechos_es_un, separador, *lineas_conservadas]
        )
        ARCHIVO_GENERADO.write_text(contenido_generado, encoding="utf-8")
        return ARCHIVO_GENERADO

    def consultar_producto(self, producto: str) -> dict:
        ejecutable = self.localizar_ejecutable()
        comando = [ejecutable, "-q", RUTA_RELATIVA_ARCHIVO_GENERADO, "--", producto]
        salida = self._correr(comando, cwd=str(RAIZ_PROYECTO))
        return self._parsear_salida(salida)

    def exportar_red(self) -> dict:
        """Pide a Prolog todos los arcos de la red semantica
        (es_un, propiedad, compatible) como listas de pares."""
        ejecutable = self.localizar_ejecutable()
        comando = [ejecutable, "-q", RUTA_RELATIVA_ARCHIVO_GENERADO, "--", "__red__"]
        salida = self._correr(comando, cwd=str(RAIZ_PROYECTO))
        red = {"ES_UN": [], "PROPIEDAD": [], "COMPATIBLE": []}
        for linea in salida.splitlines():
            partes = linea.strip().split(":")
            if len(partes) == 3 and partes[0] in red:
                red[partes[0]].append((partes[1], partes[2]))
        return red

    @staticmethod
    def _parsear_salida(salida: str) -> dict:
        resultado = {"producto": None, "categorias": [], "propiedades": [], "accesorios": []}
        for linea in salida.splitlines():
            if ":" not in linea:
                continue
            etiqueta, _, valor = linea.partition(":")
            valor = valor.strip()
            if etiqueta == "PRODUCTO":
                resultado["producto"] = valor
            elif etiqueta == "CATEGORIA":
                resultado["categorias"].append(valor)
            elif etiqueta == "PROPIEDAD":
                resultado["propiedades"].append(valor)
            elif etiqueta == "ACCESORIO":
                resultado["accesorios"].append(valor)
        return resultado
