
"""Calcula los retrasos de una planificación."""

from dataclasses import dataclass

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion


@dataclass(frozen=True)
class ResultadoRetrasos:
    horas_totales: float
    retrasos_por_actividad: dict[str, float]


def calcular_retrasos(
    planificacion: Planificacion,
    escenario: Escenario
) -> ResultadoRetrasos:

    retrasos = {}

    for actividad in escenario.actividades.values():

        asignaciones = planificacion.asignaciones_de_actividad(
            actividad.id
        )

        if not asignaciones:
            continue

        fin_actividad = max(
            asignacion.intervalo.fin
            for asignacion in asignaciones
        )

        segundos_retraso = (
            fin_actividad - actividad.fecha_limite
        ).total_seconds()

        horas_retraso = max(
            0.0,
            segundos_retraso / 3600
        )

        retrasos[actividad.id] = horas_retraso

    return ResultadoRetrasos(
        horas_totales=sum(retrasos.values()),
        retrasos_por_actividad=retrasos
    )
