"""Clase base para los "motores" externos que el orquestador invoca.

Scala y Prolog comparten el mismo problema practico: hay que encontrar
su ejecutable (puede no estar en el PATH de la sesion actual) y correrlo
como subproceso capturando su salida de texto. MotorExterno concentra
esa parte comun; MotorScala y MotorPrologo (herencia) solo agregan como
armar la linea de comandos propia de cada lenguaje.
"""

import shutil
import subprocess
from pathlib import Path


class MotorExterno:
    nombre_ejecutable = ""
    rutas_conocidas = ()

    def localizar_ejecutable(self) -> str:
        # Se prueban primero las rutas conocidas (binario .exe real):
        # en Windows, los shims .BAT que algunos instaladores agregan
        # al PATH (p. ej. Coursier para scala-cli) corrompen argumentos
        # con tildes al pasar por cmd.exe, mientras que invocar el
        # .exe real directamente evita ese problema.
        for ruta in self.rutas_conocidas:
            if Path(ruta).exists():
                return ruta
        encontrado = shutil.which(self.nombre_ejecutable)
        if encontrado:
            return encontrado
        raise FileNotFoundError(
            f"No se encontro '{self.nombre_ejecutable}' ni en el PATH ni en "
            f"las rutas conocidas {self.rutas_conocidas}."
        )

    def ejecutar(self, *_args: str) -> str:
        raise NotImplementedError("Cada motor debe implementar su propia ejecucion")

    def _correr(self, comando: list, cwd: str = None) -> str:
        # Se pasan rutas relativas + cwd (en vez de rutas absolutas) a
        # los ejecutables externos: la carpeta del proyecto tiene una
        # tilde ("Recomendación") que algunos lanzadores nativos de
        # Windows no decodifican bien si llega como argumento de linea
        # de comandos; como cwd si se maneja de forma nativa, se evita
        # el problema por completo.
        resultado = subprocess.run(
            comando,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if resultado.returncode != 0:
            raise RuntimeError(
                f"{comando[0]} termino con codigo {resultado.returncode}:\n{resultado.stderr}"
            )
        return resultado.stdout
