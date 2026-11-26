"""Motor de reglas y restricciones."""

from __future__ import annotations

from typing import TYPE_CHECKING

from planificador.reglas.penalizacion_retrasos import calcular_retrasos
from planificador.reglas.regla_cantidad_recursos import ReglaCantidadRecursos
from planificador.reglas.regla_capacidad import ReglaCapacidad
from planificador.reglas.regla_dependencias import ReglaDependencias
from planificador.reglas.regla_disponibilidad import ReglaDisponibilidad
from planificador.reglas.regla_estado_recurso import ReglaEstadoRecurso
from planificador.reglas.regla_habilidades import ReglaHabilidades
from planificador.reglas.regla_horizonte import ReglaHorizonte
from planificador.reglas.regla_inicio_permitido import ReglaInicioPermitido
from planificador.reglas.regla_integridad import ReglaIntegridad
from planificador.reglas.regla_referencias import ReglaReferencias
from planificador.reglas.resultado_validacion import ResultadoValidacion

if TYPE_CHECKING:
    from planificador.dominio.escenario import Escenario
    from planificador.dominio.intervalo import Intervalo
    from planificador.dominio.planificacion import Planificacion
    from planificador.reglas.incidencia import Incidencia
    from planificador.reglas.regla_base import Regla


class MotorReglas:
    """Aplica las reglas registradas y emite el veredicto de factibilidad.

    Con un horizonte, agrega la regla opcional de horizonte de planificación.
    """

    def __init__(self, horizonte: Intervalo | None = None) -> None:
        self.reglas: list[Regla] = [
            ReglaReferencias(),
            ReglaHabilidades(),
            ReglaEstadoRecurso(),
            ReglaDisponibilidad(),
            ReglaCapacidad(),
            ReglaCantidadRecursos(),
            ReglaDependencias(),
            ReglaInicioPermitido(),
            ReglaIntegridad(),
        ]
        if horizonte is not None:
            self.agregar_regla(ReglaHorizonte(horizonte))

    def agregar_regla(self, regla: Regla) -> None:
        self.reglas.append(regla)

    def evaluar(self, planificacion: Planificacion, escenario: Escenario) -> list[Incidencia]:
        """Todas las incidencias, duras y pendientes, en el orden de las reglas."""
        incidencias: list[Incidencia] = []
        for regla in self.reglas:
            incidencias.extend(regla.evaluar(planificacion, escenario))
        return incidencias

    def validar(self, planificacion: Planificacion, escenario: Escenario) -> ResultadoValidacion:
        """Veredicto único usado por los algoritmos, la comparación y la persistencia."""
        retrasos = calcular_retrasos(planificacion, escenario)
        return ResultadoValidacion(
            tuple(self.evaluar(planificacion, escenario)),
            retrasos.horas_totales,
            retrasos.retrasos_por_actividad,
        )

    def generar_reporte(self, planificacion: Planificacion, escenario: Escenario) -> dict[str, object]:
        """Reporte en diccionario, compatible con la versión anterior."""
        resultado = self.validar(planificacion, escenario)
        return {
            "factible": resultado.factible,
            "incidencias": list(resultado.incidencias),
            "conflictos_duros": list(resultado.conflictos_duros),
            "pendientes": list(resultado.actividades_pendientes),
            "horas_retraso": resultado.horas_retraso,
            "retrasos_por_actividad": resultado.retrasos_por_actividad,
        }
