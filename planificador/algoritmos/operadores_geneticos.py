"""Selección, cruzamiento, mutación y elitismo."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from random import Random

from planificador.algoritmos.cromosoma import Cromosoma, Gen


class OperadoresGeneticos:
    """Todos los operadores usan el mismo generador aleatorio para que la ejecución sea reproducible."""

    def __init__(self, azar: Random, limites: Mapping[str, int], tamano_torneo: int) -> None:
        self._azar = azar
        self._limites = limites
        self._tamano_torneo = tamano_torneo

    def seleccionar(self, evaluados: Sequence[tuple[Cromosoma, float]]) -> Cromosoma:
        """Torneo: toma individuos al azar y gana el de menor aptitud."""
        participantes = self._azar.sample(range(len(evaluados)), self._tamano_torneo)
        ganador = min(participantes, key=lambda indice: (evaluados[indice][1], indice))
        return evaluados[ganador][0]

    def cruzar(self, padre: Cromosoma, madre: Cromosoma) -> tuple[Cromosoma, Cromosoma]:
        """Cruce de orden (OX): cada gen viaja con su preferencia y el hijo sigue siendo una permutación."""
        tamano = len(padre)
        if tamano < 2:
            return padre, madre
        inicio, fin = sorted(self._azar.sample(range(tamano + 1), 2))
        return self._hijo_ox(padre, madre, inicio, fin), self._hijo_ox(madre, padre, inicio, fin)

    def mutar(self, cromosoma: Cromosoma, probabilidad: float) -> Cromosoma:
        """Por cada gen: con la probabilidad dada se intercambia de posición y se cambia su preferencia."""
        genes = list(cromosoma.genes)
        tamano = len(genes)
        for indice in range(tamano):
            if tamano > 1 and self._azar.random() < probabilidad:
                otro = self._azar.randrange(tamano)
                genes[indice], genes[otro] = genes[otro], genes[indice]
            if self._azar.random() < probabilidad:
                gen = genes[indice]
                limite = max(self._limites[gen.actividad_id], 1)
                genes[indice] = Gen(gen.actividad_id, self._azar.randrange(limite))
        return Cromosoma(tuple(genes))

    @staticmethod
    def elites(evaluados: Sequence[tuple[Cromosoma, float]], cantidad: int) -> list[Cromosoma]:
        """Recibe la población ordenada de mejor a peor."""
        return [cromosoma for cromosoma, _ in evaluados[:cantidad]]

    @staticmethod
    def _hijo_ox(base: Cromosoma, relleno: Cromosoma, inicio: int, fin: int) -> Cromosoma:
        segmento = base.genes[inicio:fin]
        usados = {gen.actividad_id for gen in segmento}
        resto = [gen for gen in relleno.genes if gen.actividad_id not in usados]
        return Cromosoma(tuple(resto[:inicio]) + segmento + tuple(resto[inicio:]))
