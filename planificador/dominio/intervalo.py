"""Intervalo de tiempo del dominio."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from planificador.dominio.excepciones import ValidacionError


@dataclass(frozen=True)
class Intervalo:
    """Rango de tiempo con inicio y fin. No incluye el instante final (semiabierto)."""

    inicio: datetime
    fin: datetime

    def __post_init__(self) -> None:
        if self.inicio >= self.fin:
            raise ValidacionError("inicio", "debe ser anterior a fin")

    def duracion_horas(self) -> float:
        """Duración del intervalo en horas."""
        return (self.fin - self.inicio).total_seconds() / 3600

    def contiene(self, otro: Intervalo) -> bool:
        """Indica si este intervalo cubre completamente a otro."""
        return self.inicio <= otro.inicio and otro.fin <= self.fin

    def se_superpone(self, otro: Intervalo) -> bool:
        """Indica si comparte tiempo con otro. Dos intervalos que solo se tocan en un extremo no se superponen."""
        return self.inicio < otro.fin and otro.inicio < self.fin

    def interseccion(self, otro: Intervalo) -> Intervalo | None:
        """Devuelve el intervalo común con otro, o None si no se superponen."""
        if not self.se_superpone(otro):
            return None
        return Intervalo(max(self.inicio, otro.inicio), min(self.fin, otro.fin))
