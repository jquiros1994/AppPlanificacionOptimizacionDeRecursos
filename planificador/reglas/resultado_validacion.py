"""Veredicto único del motor de reglas."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from planificador.reglas.incidencia import Incidencia


@dataclass(frozen=True)
class ResultadoValidacion:
    """FACTIBLE significa cero conflictos duros (RF-03).

    Las actividades pendientes sin asignar y los retrasos se informan aparte:
    no invalidan la planificación.
    """

    incidencias: tuple[Incidencia, ...]
    horas_retraso: float
    retrasos_por_actividad: dict[str, float] = field(default_factory=dict)

    @property
    def conflictos_duros(self) -> tuple[Incidencia, ...]:
        return tuple(i for i in self.incidencias if i.es_dura)

    @property
    def pendientes(self) -> tuple[Incidencia, ...]:
        return tuple(i for i in self.incidencias if not i.es_dura)

    @property
    def actividades_pendientes(self) -> tuple[str, ...]:
        return tuple(sorted({i.actividad_id for i in self.pendientes if i.actividad_id}))

    @property
    def factible(self) -> bool:
        return not self.conflictos_duros

    def por_regla(self, solo_duras: bool = False) -> dict[str, int]:
        """Cantidad de incidencias por código de regla, en orden alfabético."""
        conteo = Counter(i.regla for i in self.incidencias if i.es_dura or not solo_duras)
        return dict(sorted(conteo.items()))

    def a_dict(self) -> dict[str, object]:
        return {
            "factible": self.factible,
            "estado": "FACTIBLE" if self.factible else "NO FACTIBLE",
            "conflictos_duros": [i.a_dict() for i in self.conflictos_duros],
            "pendientes": list(self.actividades_pendientes),
            "violaciones_por_regla": self.por_regla(solo_duras=True),
            "horas_retraso": self.horas_retraso,
            "retrasos_por_actividad": dict(sorted(self.retrasos_por_actividad.items())),
        }
