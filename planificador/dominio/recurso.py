"""Clase Recurso del dominio."""

from __future__ import annotations

from dataclasses import dataclass, field

from planificador.dominio.enums import EstadoRecurso, TipoRecurso
from planificador.dominio.excepciones import ValidacionError
from planificador.dominio.intervalo import Intervalo


@dataclass
class Recurso:
    """Recurso humano, de equipo o de unidad operativa asignable a actividades."""

    id: str
    nombre: str
    tipo: TipoRecurso
    capacidad: int
    costo_hora: float
    habilidades: frozenset[str]
    disponibilidad: tuple[Intervalo, ...]
    estado: EstadoRecurso = field(default=EstadoRecurso.ACTIVO)

    def __post_init__(self) -> None:
        if not isinstance(self.capacidad, int) or self.capacidad < 1:
            raise ValidacionError("capacidad", "debe ser un entero mayor o igual a 1")
        if self.costo_hora < 0:
            raise ValidacionError("costo_hora", "no puede ser negativo")
        if not self.habilidades:
            raise ValidacionError("habilidades", "no puede estar vacío")

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
