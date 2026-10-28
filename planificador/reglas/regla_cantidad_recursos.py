
"""Valida la cantidad de recursos requeridos por actividad."""

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaCantidadRecursos(Regla):

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

            cantidad_asignada = len(asignacion.recursos_ids)
            cantidad_requerida = actividad.cantidad_recursos

            if cantidad_asignada != cantidad_requerida:
                incidencias.append(
                    Incidencia(
                        regla="CANTIDAD_RECURSOS",
                        mensaje=(
                            f"La actividad requiere "
                            f"{cantidad_requerida} recursos, "
                            f"pero tiene {cantidad_asignada} asignados"
                        ),
                        actividad_id=actividad.id
                    )
                )

        return incidencias
