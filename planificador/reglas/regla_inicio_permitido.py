
"""Valida que las actividades no comiencen antes de lo permitido."""

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaInicioPermitido(Regla):

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

            if asignacion.intervalo.inicio < actividad.inicio_permitido:

                incidencias.append(
                    Incidencia(
                        regla="INICIO_PERMITIDO",
                        mensaje=(
                            f"La actividad {actividad.id} comienza "
                            "antes de su inicio permitido"
                        ),
                        actividad_id=actividad.id
                    )
                )

        return incidencias
