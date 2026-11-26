"""Valida la capacidad simultánea de los recursos."""

from __future__ import annotations

from datetime import datetime

from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaCapacidad(Regla):
    """Reporta cada tramo en que un recurso supera su capacidad.

    La incidencia incluye las actividades que coinciden en ese tramo y el
    intervalo exacto del exceso. Los intervalos son semiabiertos: una tarea que
    termina a las 10:00 no choca con otra que empieza a las 10:00.
    """

    def evaluar(self, planificacion: Planificacion, escenario: Escenario) -> list[Incidencia]:
        incidencias = []
        for recurso_id, recurso in escenario.recursos.items():
            asignaciones = planificacion.asignaciones_de_recurso(recurso_id)
            eventos = []
            for indice, asignacion in enumerate(asignaciones):
                eventos.append((asignacion.intervalo.inicio, 1, indice))
                eventos.append((asignacion.intervalo.fin, -1, indice))
            # Los finales (-1) se procesan antes que los inicios a la misma hora.
            eventos.sort(key=lambda evento: (evento[0], evento[1]))

            activas: set[int] = set()
            involucradas: set[int] = set()
            inicio_exceso: datetime | None = None
            for momento, cambio, indice in eventos:
                if cambio > 0:
                    activas.add(indice)
                else:
                    activas.discard(indice)
                if len(activas) > recurso.capacidad:
                    if inicio_exceso is None:
                        inicio_exceso = momento
                    involucradas |= activas
                elif inicio_exceso is not None:
                    ids = sorted({asignaciones[i].actividad_id for i in involucradas})
                    incidencias.append(Incidencia(
                        regla="CAPACIDAD",
                        mensaje=(
                            f"El recurso {recurso_id} (capacidad {recurso.capacidad}) "
                            f"atiende {', '.join(ids)} a la vez entre "
                            f"{inicio_exceso:%Y-%m-%d %H:%M} y {momento:%H:%M}"
                        ),
                        recurso_id=recurso_id,
                        actividades_ids=tuple(ids),
                        inicio=inicio_exceso,
                        fin=momento,
                    ))
                    inicio_exceso = None
                    involucradas = set()
        return incidencias
