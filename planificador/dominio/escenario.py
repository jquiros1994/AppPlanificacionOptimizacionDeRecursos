"""Clase Escenario del dominio."""

from __future__ import annotations

from dataclasses import dataclass, field

from planificador.dominio.actividad import Actividad
from planificador.dominio.enums import EstadoActividad
from planificador.dominio.excepciones import (
    CicloDependenciaError,
    ReferenciaError,
    ValidacionError,
)
from planificador.dominio.recurso import Recurso


@dataclass
class Escenario:
    """Conjunto de recursos y actividades sobre el que se planifica."""

    recursos: dict[str, Recurso] = field(default_factory=dict)
    actividades: dict[str, Actividad] = field(default_factory=dict)

    def agregar_recurso(self, recurso: Recurso) -> None:
        """Registra un recurso nuevo. Rechaza IDs duplicados."""
        if recurso.id in self.recursos:
            raise ReferenciaError(f"{recurso.id} ya existe como recurso")
        self.recursos[recurso.id] = recurso

    def agregar_actividad(self, actividad: Actividad) -> None:
        """Registra una actividad nueva.

        Rechaza IDs duplicados, dependencias a actividades inexistentes y
        ciclos en el grafo de dependencias.
        """
        if actividad.id in self.actividades:
            raise ReferenciaError(f"{actividad.id} ya existe como actividad")
        for dependencia_id in actividad.dependencias:
            if dependencia_id not in self.actividades:
                raise ReferenciaError(
                    f"{actividad.id} depende de {dependencia_id}, que no existe"
                )
        self.actividades[actividad.id] = actividad
        self.verificar_sin_ciclos()

    def eliminar_actividad(self, actividad_id: str) -> None:
        """Elimina una actividad pendiente.

        Rechaza si no existe, si no está pendiente o si otra actividad
        depende de ella (para no dejar referencias huérfanas).
        """
        if actividad_id not in self.actividades:
            raise ReferenciaError(f"{actividad_id} no existe")

        actividad = self.actividades[actividad_id]
        if actividad.estado != EstadoActividad.PENDIENTE:
            raise ValidacionError("estado", "solo se puede eliminar una actividad pendiente")

        dependientes = sorted(
            otra.id
            for otra in self.actividades.values()
            if actividad_id in otra.dependencias
        )
        if dependientes:
            raise ReferenciaError(
                f"{actividad_id} no se puede eliminar: depende de ella "
                + ", ".join(dependientes)
            )

        del self.actividades[actividad_id]

    def desactivar_recurso(self, recurso_id: str) -> None:
        """Marca un recurso como inactivo sin borrar su historial."""
        if recurso_id not in self.recursos:
            raise ReferenciaError(f"{recurso_id} no existe")
        self.recursos[recurso_id].desactivar()

    def verificar_sin_ciclos(self) -> None:
        """Recorre todo el grafo de dependencias con DFS.

        Lanza CicloDependenciaError con la cadena completa (por ejemplo
        A002 → A005 → A002) si encuentra un ciclo.
        """
        visitados: set[str] = set()
        for actividad_id in self.actividades:
            if actividad_id not in visitados:
                self._dfs_detectar_ciclo(actividad_id, visitados, [])

    def _dfs_detectar_ciclo(
        self, actividad_id: str, visitados: set[str], pila: list[str]
    ) -> None:
        if actividad_id in pila:
            cadena = pila[pila.index(actividad_id) :] + [actividad_id]
            raise CicloDependenciaError(cadena)
        if actividad_id in visitados:
            return

        pila.append(actividad_id)
        actividad = self.actividades[actividad_id]
        for dependencia_id in actividad.dependencias:
            self._dfs_detectar_ciclo(dependencia_id, visitados, pila)
        pila.pop()
        visitados.add(actividad_id)
