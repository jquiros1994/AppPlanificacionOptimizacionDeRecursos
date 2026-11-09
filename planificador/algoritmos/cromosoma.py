"""Representación de una planificación como cromosoma."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class Gen:
    """actividad_id: actividad a programar. preferencia: desde qué recurso compatible, ordenado por costo, se elige."""

    actividad_id: str
    preferencia: int


@dataclass(frozen=True)
class Cromosoma:
    """Secuencia de genes. La posición de cada gen es el turno de la actividad en el decodificador."""

    genes: tuple[Gen, ...]

    @classmethod
    def desde_orden(cls, orden: Sequence[str]) -> Cromosoma:
        return cls(tuple(Gen(actividad_id, 0) for actividad_id in orden))

    @classmethod
    def aleatorio(cls, limites: Mapping[str, int], azar: Random) -> Cromosoma:
        """limites indica cuántos recursos candidatos tiene cada actividad."""
        orden = sorted(limites)
        azar.shuffle(orden)
        return cls(tuple(Gen(aid, azar.randrange(max(limites[aid], 1))) for aid in orden))

    def como_pares(self) -> list[tuple[str, int]]:
        return [(gen.actividad_id, gen.preferencia) for gen in self.genes]

    def describir(self) -> str:
        return " ".join(f"{gen.actividad_id}:{gen.preferencia}" for gen in self.genes)

    def __len__(self) -> int:
        return len(self.genes)
