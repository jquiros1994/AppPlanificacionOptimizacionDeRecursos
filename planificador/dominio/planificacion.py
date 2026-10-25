"""Clase Planificacion del dominio."""

from __future__ import annotations

from dataclasses import dataclass

from planificador.dominio.asignacion import Asignacion


@dataclass(frozen=True)
class Planificacion:
    """Resultado de ejecutar un algoritmo: el conjunto de asignaciones que propone.

    No valida restricciones de negocio: esa responsabilidad es del motor de reglas.
    """

    asignaciones: tuple[Asignacion, ...]
    algoritmo: str
    semilla: int | None = None

    def asignaciones_de_actividad(self, actividad_id: str) -> tuple[Asignacion, ...]:
        """Devuelve las asignaciones correspondientes a una actividad."""
        return tuple(a for a in self.asignaciones if a.actividad_id == actividad_id)

    def asignaciones_de_recurso(self, recurso_id: str) -> tuple[Asignacion, ...]:
        """Devuelve las asignaciones en las que participa un recurso."""
        return tuple(a for a in self.asignaciones if recurso_id in a.recursos_ids)
