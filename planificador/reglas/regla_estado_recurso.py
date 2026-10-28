
"""Valida que los recursos asignados estén activos."""

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaEstadoRecurso(Regla):

    def evaluar(
        self,
        planificacion: Planificacion,
        escenario: Escenario
    ) -> list[Incidencia]:

        incidencias = []

        for asignacion in planificacion.asignaciones:

            for recurso_id in asignacion.recursos_ids:

                recurso = escenario.recursos.get(recurso_id)

                if recurso is None:
                    continue

                if not recurso.esta_activo:
                    incidencias.append(
                        Incidencia(
                            regla="RECURSO_INACTIVO",
                            mensaje="El recurso asignado está inactivo",
                            actividad_id=asignacion.actividad_id,
                            recurso_id=recurso_id
                        )
                    )

        return incidencias
