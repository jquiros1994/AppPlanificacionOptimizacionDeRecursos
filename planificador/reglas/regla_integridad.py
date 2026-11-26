"""Valida la integridad de las asignaciones."""

from math import isclose

from planificador.dominio.enums import EstadoActividad
from planificador.dominio.escenario import Escenario
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Categoria, Incidencia
from planificador.reglas.regla_base import Regla

# Una actividad completada o cancelada no puede recibir una asignación nueva.
ESTADOS_NO_PLANIFICABLES = frozenset({EstadoActividad.COMPLETADA, EstadoActividad.CANCELADA})


class ReglaIntegridad(Regla):
    """Duplicados, duración y estado son conflictos duros.

    Una actividad PENDIENTE sin asignar se informa como pendiente: no invalida el
    plan. Las actividades ASIGNADAS, COMPLETADAS o CANCELADAS que no figuran en
    el plan no generan incidencias.
    """

    def evaluar(self, planificacion: Planificacion, escenario: Escenario) -> list[Incidencia]:
        incidencias = []
        for actividad in escenario.actividades.values():
            asignaciones = planificacion.asignaciones_de_actividad(actividad.id)

            if not asignaciones:
                if actividad.estado == EstadoActividad.PENDIENTE:
                    incidencias.append(Incidencia(
                        regla="ACTIVIDAD_SIN_ASIGNACION",
                        mensaje="La actividad pendiente quedó sin asignación",
                        actividad_id=actividad.id,
                        categoria=Categoria.PENDIENTE,
                    ))
                continue

            if actividad.estado in ESTADOS_NO_PLANIFICABLES:
                incidencias.append(Incidencia(
                    regla="ESTADO_NO_PLANIFICABLE",
                    mensaje=(
                        f"La actividad está {actividad.estado.value} "
                        "y no puede recibir una asignación"
                    ),
                    actividad_id=actividad.id,
                ))

            if len(asignaciones) > 1:
                incidencias.append(Incidencia(
                    regla="ASIGNACION_DUPLICADA",
                    mensaje="La actividad tiene más de una asignación programada",
                    actividad_id=actividad.id,
                ))

            for asignacion in asignaciones:
                duracion = asignacion.intervalo.duracion_horas()
                if not isclose(duracion, actividad.duracion_horas, rel_tol=1e-9, abs_tol=1e-9):
                    incidencias.append(Incidencia(
                        regla="DURACION_INCORRECTA",
                        mensaje=(
                            f"La actividad requiere {actividad.duracion_horas} horas, "
                            f"pero se programaron {duracion} horas"
                        ),
                        actividad_id=actividad.id,
                        inicio=asignacion.intervalo.inicio,
                        fin=asignacion.intervalo.fin,
                    ))
        return incidencias
