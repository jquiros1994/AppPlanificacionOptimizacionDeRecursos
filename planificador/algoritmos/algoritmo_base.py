"""Algoritmo inicial greedy (RF-04)."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from planificador.algoritmos.decodificador import Decodificador
from planificador.algoritmos.evaluador_aptitud import EvaluadorAptitud, ResultadoAptitud
from planificador.dominio.enums import EstadoActividad
from planificador.dominio.escenario import Escenario
from planificador.dominio.excepciones import ValidacionError
from planificador.dominio.intervalo import Intervalo
from planificador.dominio.planificacion import Planificacion
from planificador.funcional import filtrar_recursos_activos, ordenar_actividades


@dataclass(frozen=True)
class ResultadoBase:
    planificacion: Planificacion
    pendientes: dict[str, str]
    aptitud: ResultadoAptitud
    segundos: float


class AlgoritmoBase:
    """Asigna las actividades por prioridad descendente, fecha límite e ID, usando los recursos más baratos."""

    nombre = "greedy"

    def __init__(self, escenario: Escenario, horizonte: Intervalo | None = None) -> None:
        if not filtrar_recursos_activos(escenario.recursos.values()):
            raise ValidacionError("escenario", "no hay recursos activos")
        if not any(a.estado == EstadoActividad.PENDIENTE for a in escenario.actividades.values()):
            raise ValidacionError("escenario", "no hay actividades pendientes")
        self._escenario = escenario
        self._decodificador = Decodificador(escenario, horizonte)
        self._evaluador = EvaluadorAptitud(escenario)

    @staticmethod
    def orden(escenario: Escenario) -> tuple[str, ...]:
        pendientes = (a for a in escenario.actividades.values() if a.estado == EstadoActividad.PENDIENTE)
        return tuple(a.id for a in ordenar_actividades(pendientes))

    def ejecutar(self) -> ResultadoBase:
        inicio = perf_counter()
        genes = [(actividad_id, 0) for actividad_id in self.orden(self._escenario)]
        decodificado = self._decodificador.decodificar(genes)
        planificacion = Planificacion(decodificado.asignaciones, self.nombre)
        aptitud = self._evaluador.evaluar(planificacion)
        return ResultadoBase(planificacion, decodificado.pendientes, aptitud, perf_counter() - inicio)
