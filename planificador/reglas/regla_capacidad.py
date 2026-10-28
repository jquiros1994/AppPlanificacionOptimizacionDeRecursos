
"""Valida la capacidad simultánea de los recursos."""

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaCapacidad(Regla):

    def evaluar(
        self,
        planificacion: Planificacion,
        escenario: Escenario
    ) -> list[Incidencia]:

        incidencias = []

        for recurso_id, recurso in escenario.recursos.items():

            asignaciones = planificacion.asignaciones_de_recurso(
                recurso_id
            )

            eventos = []

            for asignacion in asignaciones:
                eventos.append((asignacion.intervalo.inicio, 1))
                eventos.append((asignacion.intervalo.fin, -1))

            # Procesar finales antes que inicios a la misma hora.
            eventos.sort(key=lambda evento: (evento[0], evento[1]))

            simultaneas = 0
            exceso_detectado = False

            for momento, cambio in eventos:
                simultaneas += cambio

                if simultaneas > recurso.capacidad:
                    if not exceso_detectado:
                        incidencias.append(
                            Incidencia(
                                regla="CAPACIDAD",
                                mensaje=(
                                    "El recurso supera su capacidad "
                                    "de actividades simultáneas"
                                ),
                                recurso_id=recurso_id
                            )
                        )
                        exceso_detectado = True

                else:
                    exceso_detectado = False

        return incidencias
