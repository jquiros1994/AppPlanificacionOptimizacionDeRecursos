"""Clase Actividad del dominio."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from functools import partial

from planificador.dominio import validaciones as v
from planificador.dominio.enums import EstadoActividad, Prioridad
from planificador.dominio.excepciones import ValidacionError

# Una duración menor no se puede representar de forma útil en el calendario.
DURACION_MINIMA_HORAS = 1 / 60


@dataclass
class Actividad(v.EntidadValidada):
    """Tarea que debe ejecutarse con recursos específicos dentro de una ventana temporal (RF-02).

    Las validaciones se aplican al crear la instancia y en cada asignación posterior
    de un atributo. Las referencias y los ciclos entre actividades los valida Escenario.
    """

    id: str
    descripcion: str
    duracion_horas: float
    prioridad: Prioridad
    inicio_permitido: datetime
    fecha_limite: datetime
    habilidades_requeridas: frozenset[str]
    cantidad_recursos: int
    dependencias: frozenset[str]
    estado: EstadoActividad = field(default=EstadoActividad.PENDIENTE)

    _normalizadores = {
        "id": partial(v.texto, "id"),
        "descripcion": partial(v.texto, "descripcion"),
        "duracion_horas": partial(v.real_finito, "duracion_horas", minimo=DURACION_MINIMA_HORAS),
        "prioridad": partial(v.enumerado, Prioridad, "prioridad"),
        "inicio_permitido": partial(v.fecha_local, "inicio_permitido"),
        "fecha_limite": partial(v.fecha_local, "fecha_limite"),
        "habilidades_requeridas": partial(v.conjunto_textos, "habilidades_requeridas"),
        "cantidad_recursos": partial(v.entero_positivo, "cantidad_recursos"),
        "dependencias": partial(v.conjunto_textos, "dependencias"),
        "estado": partial(v.enumerado, EstadoActividad, "estado"),
    }

    def __post_init__(self) -> None:
        self._finalizar_validacion()

    def _validar_relaciones(self) -> None:
        if self.inicio_permitido >= self.fecha_limite:
            raise ValidacionError("inicio_permitido", "debe ser anterior a fecha_limite")
        if self.id in self.dependencias:
            raise ValidacionError("dependencias", "una actividad no puede depender de sí misma")
