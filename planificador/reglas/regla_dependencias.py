
"""Valida las dependencias entre actividades."""

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaDependencias(Regla):

    def evaluar(
        self,
        planificacion: Planificacion,
        escenario: Escenario
    ) -> list[Incidencia]:

        incidencias = []

        for actividad in escenario.actividades.values():

            asignaciones = planificacion.asignaciones_de_actividad(
                actividad.id
            )

            if not asignaciones:
                continue

            for dependencia_id in actividad.dependencias:

                asignaciones_dependencia = (
                    planificacion.asignaciones_de_actividad(
                        dependencia_id
                    )
                )

                if not asignaciones_dependencia:
                    incidencias.append(
                        Incidencia(
                            regla="DEPENDENCIA_SIN_ASIGNACION",
                            mensaje=(
                                f"La dependencia {dependencia_id} "
                                "no tiene una asignación programada"
                            ),
                            actividad_id=actividad.id
                        )
                    )
                    continue

                fin_dependencia = max(
                    asignacion.intervalo.fin
                    for asignacion in asignaciones_dependencia
                )

                for asignacion in asignaciones:

                    if asignacion.intervalo.inicio < fin_dependencia:
                        incidencias.append(
                            Incidencia(
                                regla="DEPENDENCIAS",
                                mensaje=(
                                    f"La actividad {actividad.id} "
                                    f"comienza antes de finalizar "
                                    f"su dependencia {dependencia_id}"
                                ),
                                actividad_id=actividad.id
                            )
                        )

        return incidencias
