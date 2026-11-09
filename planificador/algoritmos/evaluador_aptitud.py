"""Cálculo de la aptitud de una planificación. Valores menores son mejores."""

from __future__ import annotations

from dataclasses import dataclass

from planificador.dominio.enums import EstadoActividad, Prioridad
from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.funcional import calcular_costo_total
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.motor_reglas import MotorReglas

# Las actividades sin asignar se reportan como pendientes, no como conflicto duro.
REGLAS_DE_PENDIENTES = frozenset({"ACTIVIDAD_SIN_ASIGNACION"})


@dataclass(frozen=True)
class ResultadoAptitud:
    valor: float
    costo: float
    horas_retraso: float
    asignadas: int
    pendientes: int
    conflictos_duros: tuple[Incidencia, ...]

    @property
    def factible(self) -> bool:
        return not self.conflictos_duros


class EvaluadorAptitud:
    """aptitud = costo + retraso ponderado + penalización por pendientes + penalización por conflictos.

    peso_retraso: costo por hora de retraso, multiplicado por la prioridad de la actividad.
    penalizacion_pendiente: supera el costo más el retraso máximo de cualquier actividad,
    por lo que asignar una actividad siempre da mejor aptitud que dejarla pendiente.
    """

    def __init__(self, escenario: Escenario) -> None:
        self._escenario = escenario
        self._motor = MotorReglas()
        self._cache: dict[tuple, tuple[Incidencia, ...]] = {}

        costo_hora_maximo = max((r.costo_hora for r in escenario.recursos.values()), default=0.0)
        self.peso_retraso = max(costo_hora_maximo, 1.0)
        actividades = escenario.actividades.values()
        costo_actividad_maximo = max(
            (costo_hora_maximo * a.duracion_horas * a.cantidad_recursos for a in actividades),
            default=0.0,
        )
        retraso_actividad_maximo = self.peso_retraso * max(Prioridad) * self._horas_retraso_maximas()
        self.penalizacion_pendiente = costo_actividad_maximo + retraso_actividad_maximo + 1.0
        self.penalizacion_conflicto = self.penalizacion_pendiente * 10

    def evaluar(self, planificacion: Planificacion) -> ResultadoAptitud:
        actividades = self._escenario.actividades
        asignadas = {a.actividad_id for a in planificacion.asignaciones}
        costo = calcular_costo_total(planificacion, self._escenario)

        horas_retraso = 0.0
        retraso_ponderado = 0.0
        for asignacion in planificacion.asignaciones:
            actividad = actividades[asignacion.actividad_id]
            horas = max(0.0, (asignacion.intervalo.fin - actividad.fecha_limite).total_seconds() / 3600)
            horas_retraso += horas
            retraso_ponderado += horas * actividad.prioridad

        pendientes = [
            a for a in actividades.values()
            if a.estado == EstadoActividad.PENDIENTE and a.id not in asignadas
        ]
        conflictos = self._conflictos_duros(planificacion)
        valor = (
            costo
            + self.peso_retraso * retraso_ponderado
            + self.penalizacion_pendiente * sum(a.prioridad for a in pendientes)
            + self.penalizacion_conflicto * len(conflictos)
        )
        return ResultadoAptitud(valor, costo, horas_retraso, len(asignadas), len(pendientes), conflictos)

    def _conflictos_duros(self, planificacion: Planificacion) -> tuple[Incidencia, ...]:
        clave = planificacion.asignaciones
        if clave not in self._cache:
            incidencias = self._motor.evaluar(planificacion, self._escenario)
            self._cache[clave] = tuple(i for i in incidencias if i.regla not in REGLAS_DE_PENDIENTES)
        return self._cache[clave]

    def _horas_retraso_maximas(self) -> float:
        fines = [v.fin for r in self._escenario.recursos.values() for v in r.disponibilidad]
        limites = [a.fecha_limite for a in self._escenario.actividades.values()]
        if not fines or not limites:
            return 0.0
        return max(0.0, (max(fines) - min(limites)).total_seconds() / 3600)
