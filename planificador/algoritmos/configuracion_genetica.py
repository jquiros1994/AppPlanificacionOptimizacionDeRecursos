"""Parámetros del algoritmo genético."""

from __future__ import annotations

from dataclasses import dataclass

from planificador.dominio.excepciones import ValidacionError


def _es_entero(valor: object) -> bool:
    return type(valor) is int


def _es_probabilidad(valor: object) -> bool:
    return type(valor) in (int, float) and 0 <= valor <= 1


@dataclass(frozen=True)
class ConfiguracionGenetica:
    """Parámetros validados antes de iniciar la optimización.

    paciencia: generaciones seguidas sin mejora antes de detenerse. None la desactiva.
    prob_mutacion: probabilidad aplicada a cada gen del cromosoma.
    """

    poblacion: int = 30
    generaciones: int = 50
    prob_mutacion: float = 0.02
    prob_cruce: float = 0.9
    elitismo: int = 2
    semilla: int = 2026
    paciencia: int | None = 15
    tamano_torneo: int = 3

    def __post_init__(self) -> None:
        if not _es_entero(self.poblacion) or self.poblacion < 2:
            raise ValidacionError("poblacion", "debe ser un entero mayor o igual a 2")
        if not _es_entero(self.generaciones) or self.generaciones < 1:
            raise ValidacionError("generaciones", "debe ser un entero mayor o igual a 1")
        if not _es_probabilidad(self.prob_mutacion):
            raise ValidacionError("prob_mutacion", "debe estar entre 0 y 1")
        if not _es_probabilidad(self.prob_cruce):
            raise ValidacionError("prob_cruce", "debe estar entre 0 y 1")
        if not _es_entero(self.elitismo) or not 0 <= self.elitismo < self.poblacion:
            raise ValidacionError("elitismo", "debe ser un entero entre 0 y poblacion - 1")
        if not _es_entero(self.semilla):
            raise ValidacionError("semilla", "debe ser un entero")
        if self.paciencia is not None and (not _es_entero(self.paciencia) or self.paciencia < 1):
            raise ValidacionError("paciencia", "debe ser None o un entero mayor o igual a 1")
        if not _es_entero(self.tamano_torneo) or not 2 <= self.tamano_torneo <= self.poblacion:
            raise ValidacionError("tamano_torneo", "debe ser un entero entre 2 y poblacion")
