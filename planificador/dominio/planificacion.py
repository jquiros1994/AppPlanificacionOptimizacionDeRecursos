"""Clase Planificacion del dominio."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

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
        return self._por_actividad.get(actividad_id, ())

    def asignaciones_de_recurso(self, recurso_id: str) -> tuple[Asignacion, ...]:
        """Devuelve las asignaciones en las que participa un recurso."""
        return self._por_recurso.get(recurso_id, ())

    # Índices calculados una sola vez. No son campos: no afectan la igualdad ni el hash.
    @cached_property
    def _por_actividad(self) -> dict[str, tuple[Asignacion, ...]]:
        indice: dict[str, list[Asignacion]] = {}
        for asignacion in self.asignaciones:
            indice.setdefault(asignacion.actividad_id, []).append(asignacion)
        return {clave: tuple(valor) for clave, valor in indice.items()}

    @cached_property
    def _por_recurso(self) -> dict[str, tuple[Asignacion, ...]]:
        indice: dict[str, list[Asignacion]] = {}
        for asignacion in self.asignaciones:
            for recurso_id in asignacion.recursos_ids:
                indice.setdefault(recurso_id, []).append(asignacion)
        return {clave: tuple(valor) for clave, valor in indice.items()}
