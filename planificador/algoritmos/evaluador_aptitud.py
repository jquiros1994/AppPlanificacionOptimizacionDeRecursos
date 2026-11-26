"""Cálculo de la aptitud de una planificación. Valores menores son mejores."""

from __future__ import annotations

from dataclasses import dataclass

from planificador.dominio.escenario import Escenario
from planificador.dominio.intervalo import Intervalo
from planificador.dominio.planificacion import Planificacion
from planificador.dominio.enums import Prioridad
from planificador.funcional import calcular_costo_total
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.motor_reglas import MotorReglas
from planificador.reglas.resultado_validacion import ResultadoValidacion


@dataclass(frozen=True)
class ResultadoAptitud:
    valor: float
    costo: float
    horas_retraso: float
    asignadas: int
    pendientes: int
    conflictos_duros: tuple[Incidencia, ...]
    validacion: ResultadoValidacion | None = None

    @property
    def factible(self) -> bool:
        """Lo decide el motor de reglas: cero conflictos duros."""
        return not self.conflictos_duros


class EvaluadorAptitud:
    """aptitud = costo + retraso ponderado + penalización por pendientes + penalización por conflictos.

    peso_retraso: costo de una hora de retraso, multiplicado por la prioridad de la actividad.

    penalizacion_pendiente (por unidad de prioridad) supera el costo más el retraso
    ponderado máximo de *todas* las actividades juntas. Así, cualquier plan con menos
    prioridad pendiente tiene mejor aptitud, aunque asignar una actividad retrase a
    otras o encarezca el plan. Dentro de la misma cobertura, decide costo + retraso.

    penalizacion_conflicto supera la penalización máxima posible por pendientes:
    un plan con un conflicto duro nunca es mejor que uno sin conflictos.
    """

    def __init__(self, escenario: Escenario, horizonte: Intervalo | None = None) -> None:
        self._escenario = escenario
        self._motor = MotorReglas(horizonte)
        self._cache: dict[tuple, ResultadoValidacion] = {}

        costo_hora_maximo = max((r.costo_hora for r in escenario.recursos.values()), default=0.0)
        self.peso_retraso = max(costo_hora_maximo, 1.0)
        actividades = escenario.actividades.values()
        costo_actividad_maximo = max(
            (costo_hora_maximo * a.duracion_horas * a.cantidad_recursos for a in actividades),
            default=0.0,
        )
        retraso_actividad_maximo = self.peso_retraso * max(Prioridad) * self._horas_retraso_maximas()
        cantidad = max(len(escenario.actividades), 1)
        self.penalizacion_pendiente = (costo_actividad_maximo + retraso_actividad_maximo) * cantidad + 1.0
        self.penalizacion_conflicto = self.penalizacion_pendiente * (max(Prioridad) * cantidad + 1)

    def evaluar(self, planificacion: Planificacion) -> ResultadoAptitud:
        validacion = self.validar(planificacion)
        actividades = self._escenario.actividades
        retraso_ponderado = sum(
            horas * actividades[aid].prioridad
            for aid, horas in validacion.retrasos_por_actividad.items()
        )
        pendientes = validacion.actividades_pendientes
        conflictos = validacion.conflictos_duros
        costo = self._costo(planificacion)
        valor = (
            costo
            + self.peso_retraso * retraso_ponderado
            + self.penalizacion_pendiente * sum(actividades[aid].prioridad for aid in pendientes)
            + self.penalizacion_conflicto * len(conflictos)
        )
        asignadas = len({a.actividad_id for a in planificacion.asignaciones if a.actividad_id in actividades})
        return ResultadoAptitud(
            valor, costo, validacion.horas_retraso, asignadas, len(pendientes), conflictos, validacion,
        )

    def validar(self, planificacion: Planificacion) -> ResultadoValidacion:
        clave = planificacion.asignaciones
        if clave not in self._cache:
            self._cache[clave] = self._motor.validar(planificacion, self._escenario)
        return self._cache[clave]

    def _costo(self, planificacion: Planificacion) -> float:
        """Ignora las asignaciones con referencias inexistentes: el motor ya las reporta como conflicto."""
        recursos = self._escenario.recursos
        validas = tuple(
            a for a in planificacion.asignaciones
            if a.actividad_id in self._escenario.actividades
            and all(rid in recursos for rid in a.recursos_ids)
        )
        return calcular_costo_total(Planificacion(validas, planificacion.algoritmo), self._escenario)

    def _horas_retraso_maximas(self) -> float:
        fines = [v.fin for r in self._escenario.recursos.values() for v in r.disponibilidad]
        limites = [a.fecha_limite for a in self._escenario.actividades.values()]
        if not fines or not limites:
            return 0.0
        return max(0.0, (max(fines) - min(limites)).total_seconds() / 3600)
