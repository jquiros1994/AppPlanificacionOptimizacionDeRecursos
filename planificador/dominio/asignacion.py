"""Clase Asignacion del dominio."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from planificador.dominio.intervalo import Intervalo
from planificador.dominio.recurso import Recurso


@dataclass(frozen=True)
class Asignacion:
    """Vínculo entre una actividad, los recursos que la atienden y el intervalo de ejecución.

    No valida restricciones de negocio (disponibilidad, capacidad, dependencias):
    esa responsabilidad es del motor de reglas.
    """

    actividad_id: str
    recursos_ids: frozenset[str]
    intervalo: Intervalo

    def calcular_costo(self, recursos: Mapping[str, Recurso]) -> float:
        """Calcula el costo de la asignación: costo_hora de cada recurso por la duración."""
        duracion = self.intervalo.duracion_horas()
        return sum(
            recursos[recurso_id].costo_hora * duracion
            for recurso_id in self.recursos_ids
        )
