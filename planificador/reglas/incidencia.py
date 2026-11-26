"""Representa una incidencia detectada por una regla."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Categoria(Enum):
    """DURA invalida la planificación. PENDIENTE solo informa una actividad sin asignar."""

    DURA = "dura"
    PENDIENTE = "pendiente"


@dataclass(frozen=True)
class Incidencia:
    """Resultado de una regla, con datos de contexto.

    actividad_id y recurso_id identifican el caso principal. actividades_ids y
    recursos_ids reúnen todos los involucrados; siempre están ordenados para que
    el reporte no dependa del orden de iteración de los conjuntos.
    inicio y fin, cuando existen, delimitan el intervalo del conflicto.
    """

    regla: str
    mensaje: str
    actividad_id: str | None = None
    recurso_id: str | None = None
    actividades_ids: tuple[str, ...] = ()
    recursos_ids: tuple[str, ...] = ()
    inicio: datetime | None = None
    fin: datetime | None = None
    categoria: Categoria = Categoria.DURA

    def __post_init__(self) -> None:
        object.__setattr__(self, "actividades_ids", _unir(self.actividad_id, self.actividades_ids))
        object.__setattr__(self, "recursos_ids", _unir(self.recurso_id, self.recursos_ids))

    @property
    def es_dura(self) -> bool:
        return self.categoria is Categoria.DURA

    def a_dict(self) -> dict[str, object]:
        """Datos serializables en JSON."""
        return {
            "regla": self.regla,
            "categoria": self.categoria.value,
            "mensaje": self.mensaje,
            "actividad_id": self.actividad_id,
            "recurso_id": self.recurso_id,
            "actividades_ids": list(self.actividades_ids),
            "recursos_ids": list(self.recursos_ids),
            "inicio": self.inicio.isoformat() if self.inicio else None,
            "fin": self.fin.isoformat() if self.fin else None,
        }


def _unir(principal: str | None, otros: tuple[str, ...]) -> tuple[str, ...]:
    ids = set(otros)
    if principal is not None:
        ids.add(principal)
    return tuple(sorted(ids))
