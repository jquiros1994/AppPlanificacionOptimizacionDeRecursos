
"""Valida la integridad de las asignaciones."""

from math import isclose

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaIntegridad(Regla):

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
                incidencias.append(
                    Incidencia(
                        regla="ACTIVIDAD_SIN_ASIGNACION",
                        mensaje=(
                            "La actividad no tiene una "
                            "asignación programada"
                        ),
                        actividad_id=actividad.id
                    )
                )
                continue

            if len(asignaciones) > 1:
                incidencias.append(
                    Incidencia(
                        regla="ASIGNACION_DUPLICADA",
                        mensaje=(
                            "La actividad tiene más de "
                            "una asignación programada"
                        ),
                        actividad_id=actividad.id
                    )
                )

            for asignacion in asignaciones:

                duracion = asignacion.intervalo.duracion_horas()

                if not isclose(
                    duracion,
                    actividad.duracion_horas,
                    rel_tol=1e-9,
                    abs_tol=1e-9
                ):
                    incidencias.append(
                        Incidencia(
                            regla="DURACION_INCORRECTA",
                            mensaje=(
                                f"La actividad requiere "
                                f"{actividad.duracion_horas} horas, "
                                f"pero se programaron {duracion} horas"
                            ),
                            actividad_id=actividad.id
                        )
                    )

        return incidencias
