
"""Comprueba que las referencias de las asignaciones existan."""

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaReferencias(Regla):

    def evaluar(
        self,
        planificacion: Planificacion,
        escenario: Escenario
    ) -> list[Incidencia]:

        incidencias = []

        for asignacion in planificacion.asignaciones:

            if asignacion.actividad_id not in escenario.actividades:
                incidencias.append(
                    Incidencia(
                        regla="REFERENCIA_ACTIVIDAD",
                        mensaje="La actividad no existe en el escenario",
                        actividad_id=asignacion.actividad_id
                    )
                )

            for recurso_id in asignacion.recursos_ids:

                if recurso_id not in escenario.recursos:
                    incidencias.append(
                        Incidencia(
                            regla="REFERENCIA_RECURSO",
                            mensaje="El recurso no existe en el escenario",
                            actividad_id=asignacion.actividad_id,
                            recurso_id=recurso_id
                        )
                    )

        return incidencias
