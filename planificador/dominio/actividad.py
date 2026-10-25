"""Clase Actividad del dominio."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from planificador.dominio.enums import EstadoActividad, Prioridad
from planificador.dominio.excepciones import ValidacionError


@dataclass
class Actividad:
    """Tarea que debe ejecutarse con recursos específicos dentro de una ventana temporal."""

    id: str
    descripcion: str
    duracion_horas: float
    prioridad: Prioridad
    inicio_permitido: datetime
    fecha_limite: datetime
    habilidades_requeridas: frozenset[str]
    cantidad_recursos: int
    dependencias: frozenset[str]
    estado: EstadoActividad = field(default=EstadoActividad.PENDIENTE)

    def __post_init__(self) -> None:
        if self.duracion_horas <= 0:
            raise ValidacionError("duracion_horas", "debe ser mayor a 0")
        if self.inicio_permitido >= self.fecha_limite:
            raise ValidacionError(
                "inicio_permitido", "debe ser anterior a fecha_limite"
            )
        if not isinstance(self.cantidad_recursos, int) or self.cantidad_recursos < 1:
            raise ValidacionError(
                "cantidad_recursos", "debe ser un entero mayor o igual a 1"
            )
        if self.id in self.dependencias:
            raise ValidacionError("dependencias", "una actividad no puede depender de sí misma")
