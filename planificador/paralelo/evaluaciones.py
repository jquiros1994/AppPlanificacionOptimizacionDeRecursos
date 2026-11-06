from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from multiprocessing import get_context
from random import Random
from time import perf_counter

from planificador.dominio import Escenario, ValidacionError

Evaluador = Callable[[Escenario, int], object]


@dataclass(frozen=True)
class ConfiguracionParalela:
    evaluaciones: int = 4
    procesos: int = 2
    semilla: int = 2026

    def __post_init__(self) -> None:
        for campo in ("evaluaciones", "procesos"):
            valor = getattr(self, campo)
            if type(valor) is not int or valor < 1:
                raise ValidacionError(campo, "debe ser un entero mayor o igual a 1")
        if type(self.semilla) is not int:
            raise ValidacionError("semilla", "debe ser un entero")


@dataclass(frozen=True)
class TrabajoEvaluacion:
    indice: int
    semilla: int


@dataclass(frozen=True)
class ResultadoEvaluacion:
    trabajo: TrabajoEvaluacion
    valor: object = None
    error: str | None = None


@dataclass(frozen=True)
class ResultadoModalidad:
    modalidad: str
    segundos: float
    resultados: tuple[ResultadoEvaluacion, ...]

    @property
    def fallos(self) -> int:
        return sum(r.error is not None for r in self.resultados)


@dataclass(frozen=True)
class ComparacionEjecuciones:
    configuracion: ConfiguracionParalela
    secuencial: ResultadoModalidad
    paralelo: ResultadoModalidad

    @property
    def equivalentes(self) -> bool:
        return self.secuencial.resultados == self.paralelo.resultados

    @property
    def aceleracion(self) -> float | None:
        if (not self.equivalentes or self.secuencial.fallos or self.paralelo.fallos
                or self.paralelo.segundos <= 0):
            return None
        return self.secuencial.segundos / self.paralelo.segundos

    def resumen(self) -> dict[str, object]:
        aceleracion = self.aceleracion
        if aceleracion is None:
            observacion = "Comparación no válida: hubo fallos o resultados diferentes."
        elif aceleracion > 1:
            observacion = "El modo paralelo fue más rápido en esta medición."
        elif aceleracion < 1:
            observacion = "El modo paralelo fue más lento; considerar la sobrecarga de procesos y copias."
        else:
            observacion = "Los tiempos fueron iguales en esta medición."
        return {
            "evaluaciones": self.configuracion.evaluaciones,
            "procesos": self.configuracion.procesos,
            "semilla": self.configuracion.semilla,
            "semillas_evaluaciones": [r.trabajo.semilla for r in self.secuencial.resultados],
            "segundos_secuencial": self.secuencial.segundos,
            "segundos_paralelo": self.paralelo.segundos,
            "fallos_secuencial": self.secuencial.fallos,
            "fallos_paralelo": self.paralelo.fallos,
            "equivalentes": self.equivalentes,
            "aceleracion": aceleracion,
            "observacion": observacion,
        }


def preparar_trabajos(configuracion: ConfiguracionParalela) -> tuple[TrabajoEvaluacion, ...]:
    azar = Random(configuracion.semilla)
    return tuple(TrabajoEvaluacion(i, azar.getrandbits(32))
                 for i in range(configuracion.evaluaciones))


def _evaluar(
    trabajo: TrabajoEvaluacion, escenario: Escenario, evaluador: Evaluador,
) -> ResultadoEvaluacion:
    try:
        # Cada evaluación recibe su propia copia también en la ejecución secuencial.
        valor = evaluador(deepcopy(escenario), trabajo.semilla)
        return ResultadoEvaluacion(trabajo, valor)
    except Exception as error:
        return ResultadoEvaluacion(trabajo, error=f"{type(error).__name__}: {error}")


def ejecutar_secuencial(
    escenario: Escenario, trabajos: tuple[TrabajoEvaluacion, ...], evaluador: Evaluador,
) -> ResultadoModalidad:
    inicio = perf_counter()
    resultados = tuple(_evaluar(trabajo, escenario, evaluador) for trabajo in trabajos)
    return ResultadoModalidad("secuencial", perf_counter() - inicio, resultados)


def ejecutar_paralelo(
    escenario: Escenario, trabajos: tuple[TrabajoEvaluacion, ...],
    evaluador: Evaluador, procesos: int,
) -> ResultadoModalidad:
    if type(procesos) is not int or procesos < 1:
        raise ValidacionError("procesos", "debe ser un entero mayor o igual a 1")
    inicio = perf_counter()
    resultados = []
    try:
        # spawn hace explícitas las condiciones que también exige Windows.
        with ProcessPoolExecutor(max_workers=procesos, mp_context=get_context("spawn")) as ejecutor:
            futuros = [ejecutor.submit(_evaluar, trabajo, escenario, evaluador) for trabajo in trabajos]
            for trabajo, futuro in zip(trabajos, futuros):
                try:
                    resultados.append(futuro.result())
                except Exception as error:
                    resultados.append(ResultadoEvaluacion(
                        trabajo, error=f"{type(error).__name__}: {error}",
                    ))
    except Exception as error:
        completados = {r.trabajo.indice for r in resultados}
        resultados.extend(ResultadoEvaluacion(t, error=f"{type(error).__name__}: {error}")
                          for t in trabajos if t.indice not in completados)
    return ResultadoModalidad("paralelo", perf_counter() - inicio, tuple(resultados))


def comparar_ejecuciones(
    escenario: Escenario, configuracion: ConfiguracionParalela, evaluador: Evaluador,
) -> ComparacionEjecuciones:
    """Usa los mismos trabajos, semillas y orden en ambas modalidades.

    El evaluador debe ser una función importable de un módulo, y devolver datos
    serializables y comparables (por ejemplo diccionarios, tuplas y números).
    No debe depender del reloj, de E/S ni de estado global mutable.
    """
    trabajos = preparar_trabajos(configuracion)
    secuencial = ejecutar_secuencial(escenario, trabajos, evaluador)
    paralelo = ejecutar_paralelo(escenario, trabajos, evaluador, configuracion.procesos)
    return ComparacionEjecuciones(configuracion, secuencial, paralelo)
