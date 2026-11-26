"""Valida las dependencias entre actividades."""

from planificador.dominio.enums import EstadoActividad
from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaDependencias(Regla):
    """Una actividad del plan solo puede empezar cuando sus dependencias terminaron.

    - COMPLETADA: la dependencia ya terminó; se cumple.
    - CANCELADA: nunca terminará; la sucesora no puede programarse.
    - Cualquier otro estado: la dependencia debe estar en el mismo plan y
      terminar antes o en el instante en que empieza la sucesora.
    """

    def evaluar(self, planificacion: Planificacion, escenario: Escenario) -> list[Incidencia]:
        incidencias = []
        for actividad in escenario.actividades.values():
            asignaciones = planificacion.asignaciones_de_actividad(actividad.id)
            if not asignaciones:
                continue

            for dependencia_id in sorted(actividad.dependencias):
                dependencia = escenario.actividades.get(dependencia_id)
                if dependencia is not None and dependencia.estado == EstadoActividad.COMPLETADA:
                    continue
                if dependencia is not None and dependencia.estado == EstadoActividad.CANCELADA:
                    incidencias.append(Incidencia(
                        regla="DEPENDENCIA_CANCELADA",
                        mensaje=f"La dependencia {dependencia_id} fue cancelada y no terminará",
                        actividad_id=actividad.id,
                        actividades_ids=(dependencia_id,),
                    ))
                    continue

                asignaciones_dependencia = planificacion.asignaciones_de_actividad(dependencia_id)
                if not asignaciones_dependencia:
                    incidencias.append(Incidencia(
                        regla="DEPENDENCIA_SIN_ASIGNACION",
                        mensaje=f"La dependencia {dependencia_id} no tiene una asignación programada",
                        actividad_id=actividad.id,
                        actividades_ids=(dependencia_id,),
                    ))
                    continue

                fin_dependencia = max(a.intervalo.fin for a in asignaciones_dependencia)
                for asignacion in asignaciones:
                    if asignacion.intervalo.inicio < fin_dependencia:
                        incidencias.append(Incidencia(
                            regla="DEPENDENCIAS",
                            mensaje=(
                                f"La actividad {actividad.id} comienza a las "
                                f"{asignacion.intervalo.inicio:%H:%M}, antes de que termine "
                                f"su dependencia {dependencia_id} a las {fin_dependencia:%H:%M}"
                            ),
                            actividad_id=actividad.id,
                            actividades_ids=(dependencia_id,),
                            inicio=asignacion.intervalo.inicio,
                            fin=fin_dependencia,
                        ))
        return incidencias
