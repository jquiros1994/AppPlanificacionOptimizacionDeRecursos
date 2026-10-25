"""Enumeraciones del dominio."""

from enum import Enum, IntEnum


class TipoRecurso(Enum):
    """Tipo de recurso disponible para asignar a actividades."""

    HUMANO = "humano"
    EQUIPO = "equipo"
    UNIDAD_OPERATIVA = "unidad_operativa"


class Prioridad(IntEnum):
    """Prioridad de una actividad. Al ser IntEnum, es comparable y ordenable."""

    BAJA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4


class EstadoRecurso(Enum):
    """Estado de disponibilidad de un recurso."""

    ACTIVO = "activo"
    INACTIVO = "inactivo"


class EstadoActividad(Enum):
    """Estado de avance de una actividad."""

    PENDIENTE = "pendiente"
    ASIGNADA = "asignada"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
