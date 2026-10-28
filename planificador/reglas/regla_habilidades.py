
"""Valida las habilidades de los recursos asignados."""

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaHabilidades(Regla):

    def evaluar(
        self,
        planificacion: Planificacion,
        escenario: Escenario
    ) -> list[Incidencia]:

        incidencias = []

        for asignacion in planificacion.asignaciones:

            actividad = escenario.actividades.get(
                asignacion.actividad_id
            )

            if actividad is None:
                continue

            for recurso_id in asignacion.recursos_ids:

                recurso = escenario.recursos.get(recurso_id)

                if recurso is None:
                    continue

                if not recurso.tiene_habilidades(
                    actividad.habilidades_requeridas
                ):
                    incidencias.append(
                        Incidencia(
                            regla="HABILIDADES",
                            mensaje=(
                                "El recurso no tiene las "
                                "habilidades requeridas"
                            ),
                            actividad_id=actividad.id,
                            recurso_id=recurso_id
                        )
                    )

        return incidencias
