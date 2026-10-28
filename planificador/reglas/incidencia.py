
"""Representa una incidencia detectada por una regla."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Incidencia:
    regla: str
    mensaje: str
    actividad_id: str | None = None
    recurso_id: str | None = None
