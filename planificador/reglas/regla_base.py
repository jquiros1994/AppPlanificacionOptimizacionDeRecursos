
"""Contrato que deben implementar las reglas."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from planificador.reglas.incidencia import Incidencia

if TYPE_CHECKING:
    from planificador.dominio.planificacion import Planificacion
    from planificador.dominio.escenario import Escenario


class Regla(ABC):

    @abstractmethod
    def evaluar(
        self,
        planificacion: Planificacion,
        escenario: Escenario
    ) -> list[Incidencia]:
        pass
