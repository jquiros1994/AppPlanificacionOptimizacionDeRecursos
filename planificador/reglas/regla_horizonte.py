"""Regla opcional: las asignaciones deben quedar dentro del horizonte de planificación.

No forma parte de las nueve restricciones de RF-03. Se agrega con
MotorReglas(horizonte=...) o agregar_regla(), sin modificar el motor.
"""

from planificador.dominio.escenario import Escenario
from planificador.dominio.intervalo import Intervalo
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.incidencia import Incidencia
from planificador.reglas.regla_base import Regla


class ReglaHorizonte(Regla):

    def __init__(self, horizonte: Intervalo) -> None:
        self.horizonte = horizonte

    def evaluar(self, planificacion: Planificacion, escenario: Escenario) -> list[Incidencia]:
        return [
            Incidencia(
                regla="FUERA_DE_HORIZONTE",
                mensaje=(
                    "La asignación sale del horizonte de planificación "
                    f"{self.horizonte.inicio:%Y-%m-%d %H:%M} - {self.horizonte.fin:%Y-%m-%d %H:%M}"
                ),
                actividad_id=asignacion.actividad_id,
                recursos_ids=tuple(asignacion.recursos_ids),
                inicio=asignacion.intervalo.inicio,
                fin=asignacion.intervalo.fin,
            )
            for asignacion in planificacion.asignaciones
            if not self.horizonte.contiene(asignacion.intervalo)
        ]
