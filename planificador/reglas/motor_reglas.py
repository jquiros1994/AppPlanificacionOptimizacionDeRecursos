
"""Motor de reglas y restricciones."""

from planificador.reglas.regla_referencias import ReglaReferencias
from planificador.reglas.regla_habilidades import ReglaHabilidades
from planificador.reglas.regla_estado_recurso import ReglaEstadoRecurso
from planificador.reglas.regla_disponibilidad import ReglaDisponibilidad
from planificador.reglas.regla_capacidad import ReglaCapacidad
from planificador.reglas.regla_cantidad_recursos import ReglaCantidadRecursos
from planificador.reglas.regla_dependencias import ReglaDependencias
from planificador.reglas.regla_inicio_permitido import ReglaInicioPermitido
from planificador.reglas.regla_integridad import ReglaIntegridad

from planificador.reglas.penalizacion_retrasos import calcular_retrasos


class MotorReglas:

    def __init__(self):
        self.reglas = [
            ReglaReferencias(),
            ReglaHabilidades(),
            ReglaEstadoRecurso(),
            ReglaDisponibilidad(),
            ReglaCapacidad(),
            ReglaCantidadRecursos(),
            ReglaDependencias(),
            ReglaInicioPermitido(),
            ReglaIntegridad()
        ]

    def agregar_regla(self, regla):
        self.reglas.append(regla)

    def evaluar(self, planificacion, escenario):
        incidencias = []

        for regla in self.reglas:
            resultado = regla.evaluar(
                planificacion,
                escenario
            )

            incidencias.extend(resultado)

        return incidencias

    def generar_reporte(self, planificacion, escenario):
        incidencias = self.evaluar(
            planificacion,
            escenario
        )

        retrasos = calcular_retrasos(
            planificacion,
            escenario
        )

        return {
            "factible": len(incidencias) == 0,
            "incidencias": incidencias,
            "horas_retraso": retrasos.horas_totales,
            "retrasos_por_actividad": retrasos.retrasos_por_actividad
        }
