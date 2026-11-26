"""Clase Recurso del dominio."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial

from planificador.dominio import validaciones as v
from planificador.dominio.enums import EstadoRecurso, TipoRecurso
from planificador.dominio.intervalo import Intervalo


@dataclass
class Recurso(v.EntidadValidada):
    """Recurso humano, de equipo o de unidad operativa asignable a actividades (RF-01).

    Las validaciones se aplican al crear la instancia y en cada asignación posterior
    de un atributo. Los tipos y estados aceptan el miembro del enum o su texto.
    """

    id: str
    nombre: str
    tipo: TipoRecurso
    capacidad: int
    costo_hora: float
    habilidades: frozenset[str]
    disponibilidad: tuple[Intervalo, ...]
    estado: EstadoRecurso = field(default=EstadoRecurso.ACTIVO)

    _normalizadores = {
        "id": partial(v.texto, "id"),
        "nombre": partial(v.texto, "nombre"),
        "tipo": partial(v.enumerado, TipoRecurso, "tipo"),
        "capacidad": partial(v.entero_positivo, "capacidad"),
        "costo_hora": partial(v.real_finito, "costo_hora"),
        "habilidades": partial(v.conjunto_textos, "habilidades", vacio=False),
        "disponibilidad": partial(v.tupla_de, Intervalo, "disponibilidad"),
        "estado": partial(v.enumerado, EstadoRecurso, "estado"),
    }

    def __post_init__(self) -> None:
        self._finalizar_validacion()

    def tiene_habilidades(self, requeridas: frozenset[str]) -> bool:
        """Indica si el recurso posee todas las habilidades requeridas."""
        return requeridas.issubset(self.habilidades)

    def esta_disponible(self, intervalo: Intervalo) -> bool:
        """Indica si alguna ventana de disponibilidad cubre completamente el intervalo."""
        return any(ventana.contiene(intervalo) for ventana in self.disponibilidad)

    def desactivar(self) -> None:
        """Cambia el estado del recurso a inactivo, sin borrar su historial."""
        self.estado = EstadoRecurso.INACTIVO

    @property
    def esta_activo(self) -> bool:
        """Indica si el recurso puede elegirse para nuevas asignaciones."""
        return self.estado == EstadoRecurso.ACTIVO
