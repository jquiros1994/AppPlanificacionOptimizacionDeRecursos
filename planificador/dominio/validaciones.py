"""Validadores puros de campos del dominio.

Cada función recibe el nombre del campo y el valor, devuelve el valor normalizado
o lanza ValidacionError con el campo y el motivo. Se reutilizan al crear, editar
y cargar entidades, para que las tres vías apliquen exactamente las mismas reglas.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, TypeVar

from planificador.dominio.excepciones import ValidacionError

E = TypeVar("E", bound=Enum)


def texto(campo: str, valor: object) -> str:
    """Texto obligatorio, sin espacios sobrantes."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValidacionError(campo, "es obligatorio y debe ser texto no vacío")
    return valor.strip()


def entero_positivo(campo: str, valor: object) -> int:
    """Entero mayor o igual a 1. Rechaza bool, aunque en Python sea subclase de int."""
    if type(valor) is not int or valor < 1:
        raise ValidacionError(campo, "debe ser un entero mayor o igual a 1")
    return valor


def real_finito(campo: str, valor: object, minimo: float = 0.0, *, estricto: bool = False) -> float:
    """Número finito mayor o igual a minimo (mayor si estricto). Rechaza bool, NaN e infinito."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
        raise ValidacionError(campo, "debe ser un número finito")
    if valor < minimo or (estricto and valor == minimo):
        relacion = "mayor que" if estricto else "mayor o igual a"
        raise ValidacionError(campo, f"debe ser {relacion} {minimo:g}")
    return float(valor)


def enumerado(tipo: type[E], campo: str, valor: object) -> E:
    """Acepta el miembro, su valor ('humano', 2) o su nombre ('HUMANO', 'critica')."""
    if isinstance(valor, tipo):
        return valor
    if not isinstance(valor, bool):
        try:
            return tipo(valor)
        except ValueError:
            pass
        if isinstance(valor, str) and valor.strip().upper() in tipo.__members__:
            return tipo[valor.strip().upper()]
    permitidos = ", ".join(str(m.value) for m in tipo)
    raise ValidacionError(campo, f"valor no permitido {valor!r}; use {permitidos}")


def fecha_local(campo: str, valor: object) -> datetime:
    """Fecha y hora sin zona horaria, como el resto del dominio."""
    if not isinstance(valor, datetime):
        raise ValidacionError(campo, "debe ser una fecha y hora")
    if valor.tzinfo is not None:
        raise ValidacionError(campo, "debe ser local, sin zona horaria")
    return valor


def conjunto_textos(campo: str, valor: object, *, vacio: bool = True) -> frozenset[str]:
    """Colección de textos convertida en frozenset. Un str suelto no se acepta como conjunto."""
    if isinstance(valor, (str, bytes)) or not isinstance(valor, Iterable):
        raise ValidacionError(campo, "debe ser una colección de textos")
    resultado = frozenset(texto(campo, elemento) for elemento in valor)
    if not resultado and not vacio:
        raise ValidacionError(campo, "no puede estar vacío")
    return resultado


def tupla_de(tipo: type, campo: str, valor: object) -> tuple:
    if isinstance(valor, (str, bytes)) or not isinstance(valor, Iterable):
        raise ValidacionError(campo, f"debe ser una colección de {tipo.__name__}")
    resultado = tuple(valor)
    if not all(isinstance(elemento, tipo) for elemento in resultado):
        raise ValidacionError(campo, f"todos los elementos deben ser {tipo.__name__}")
    return resultado


class EntidadValidada:
    """Mantiene las invariantes también cuando se asigna un atributo después de crear la entidad.

    _normalizadores valida cada campo por separado. _validar_relaciones comprueba las
    reglas entre campos; si falla tras una asignación, el valor anterior se restaura.
    """

    _normalizadores: ClassVar[dict[str, Callable[[Any], Any]]] = {}

    def __setattr__(self, nombre: str, valor: object) -> None:
        normalizar = self._normalizadores.get(nombre)
        if normalizar is not None:
            valor = normalizar(valor)
        if not self.__dict__.get("_validada", False):
            object.__setattr__(self, nombre, valor)
            return
        anterior = getattr(self, nombre)
        object.__setattr__(self, nombre, valor)
        try:
            self._validar_relaciones()
        except ValidacionError:
            object.__setattr__(self, nombre, anterior)
            raise

    def _finalizar_validacion(self) -> None:
        self._validar_relaciones()
        object.__setattr__(self, "_validada", True)

    def _validar_relaciones(self) -> None:
        """Reglas entre campos. Las subclases la redefinen si las necesitan."""
