"""Clase Escenario del dominio."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace

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
    """Conjunto de recursos y actividades sobre el que se planifica.

    Garantiza IDs únicos, dependencias existentes y ausencia de ciclos. Todas las
    operaciones validan sobre una copia y aplican el cambio solo si todo es correcto:
    un error nunca deja el escenario a medio modificar.
    """

    recursos: dict[str, Recurso] = field(default_factory=dict)
    actividades: dict[str, Actividad] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validar_claves(self.recursos, Recurso, "recurso")
        _validar_claves(self.actividades, Actividad, "actividad")
        _validar_dependencias(self.actividades)

    @classmethod
    def desde_entidades(
        cls, recursos: Iterable[Recurso], actividades: Iterable[Actividad],
    ) -> Escenario:
        """Construye un escenario completo; las actividades pueden venir en cualquier orden.

        Pensado para cargar datos guardados: las dependencias se comprueban al final.
        """
        return cls(_indexar(recursos, "recurso"), _indexar(actividades, "actividad"))

    # --- Recursos (RF-01) --------------------------------------------------

    def agregar_recurso(self, recurso: Recurso) -> None:
        """Registra un recurso nuevo. Rechaza IDs duplicados."""
        if recurso.id in self.recursos:
            raise ReferenciaError(f"ID duplicado: {recurso.id} ya existe como recurso")
        self.recursos[recurso.id] = recurso

    def obtener_recurso(self, recurso_id: str) -> Recurso:
        if recurso_id not in self.recursos:
            raise ReferenciaError(f"{recurso_id} no existe")
        return self.recursos[recurso_id]

    def editar_recurso(self, recurso_id: str, **cambios: object) -> Recurso:
        """Valida de nuevo todos los campos y reemplaza el recurso solo si son correctos.

        El ID no se puede cambiar: las planificaciones guardadas lo referencian.
        """
        nuevo = _editar(self.obtener_recurso(recurso_id), cambios)
        self.recursos[recurso_id] = nuevo
        return nuevo

    def desactivar_recurso(self, recurso_id: str) -> None:
        """Marca un recurso como inactivo sin borrar su historial."""
        self.obtener_recurso(recurso_id).desactivar()

    # --- Actividades (RF-02) -----------------------------------------------

    def agregar_actividad(self, actividad: Actividad) -> None:
        """Registra una actividad nueva.

        Rechaza IDs duplicados, dependencias a actividades inexistentes y
        ciclos en el grafo de dependencias.
        """
        if actividad.id in self.actividades:
            raise ReferenciaError(f"ID duplicado: {actividad.id} ya existe como actividad")
        self._aplicar_actividad(actividad)

    def obtener_actividad(self, actividad_id: str) -> Actividad:
        if actividad_id not in self.actividades:
            raise ReferenciaError(f"{actividad_id} no existe")
        return self.actividades[actividad_id]

    def editar_actividad(self, actividad_id: str, **cambios: object) -> Actividad:
        """Valida los campos, las dependencias y los ciclos antes de aplicar el cambio.

        Ejemplo de RF-02: si A005 depende de A002, editar A002 para que dependa de
        A005 lanza CicloDependenciaError con la cadena A002 → A005 → A002.
        """
        nuevo = _editar(self.obtener_actividad(actividad_id), cambios)
        self._aplicar_actividad(nuevo)
        return nuevo

    def eliminar_actividad(self, actividad_id: str) -> None:
        """Elimina una actividad pendiente.

        Rechaza si no existe, si no está pendiente o si otra actividad
        depende de ella (para no dejar referencias huérfanas).
        """
        actividad = self.obtener_actividad(actividad_id)
        if actividad.estado != EstadoActividad.PENDIENTE:
            raise ValidacionError("estado", "solo se puede eliminar una actividad pendiente")

        dependientes = sorted(
            otra.id for otra in self.actividades.values() if actividad_id in otra.dependencias
        )
        if dependientes:
            raise ReferenciaError(
                f"{actividad_id} no se puede eliminar: depende de ella " + ", ".join(dependientes)
            )
        del self.actividades[actividad_id]

    def verificar_sin_ciclos(self) -> None:
        """Lanza CicloDependenciaError con la cadena completa (por ejemplo
        A002 → A005 → A002) si el grafo de dependencias tiene un ciclo."""
        ciclo = buscar_ciclo(self.actividades)
        if ciclo is not None:
            raise CicloDependenciaError(ciclo)

    def _aplicar_actividad(self, actividad: Actividad) -> None:
        candidato = {**self.actividades, actividad.id: actividad}
        _validar_dependencias(candidato)
        self.actividades[actividad.id] = actividad


def buscar_ciclo(actividades: Mapping[str, Actividad]) -> list[str] | None:
    """Recorrido en profundidad iterativo: no depende del límite de recursión.

    Devuelve la cadena del primer ciclo encontrado, cerrada con el nodo inicial,
    o None. Recorre las dependencias en orden alfabético para que el resultado sea
    reproducible. Las dependencias inexistentes se ignoran aquí.
    """
    terminados: set[str] = set()
    for raiz in actividades:
        if raiz in terminados:
            continue
        camino: list[str] = [raiz]
        en_camino = {raiz}
        pila = [iter(sorted(actividades[raiz].dependencias))]
        while pila:
            siguiente = next(pila[-1], None)
            if siguiente is None:
                pila.pop()
                terminado = camino.pop()
                en_camino.discard(terminado)
                terminados.add(terminado)
            elif siguiente in en_camino:
                return camino[camino.index(siguiente):] + [siguiente]
            elif siguiente in actividades and siguiente not in terminados:
                camino.append(siguiente)
                en_camino.add(siguiente)
                pila.append(iter(sorted(actividades[siguiente].dependencias)))
    return None


def _validar_dependencias(actividades: Mapping[str, Actividad]) -> None:
    for actividad in actividades.values():
        for dependencia_id in sorted(actividad.dependencias):
            if dependencia_id not in actividades:
                raise ReferenciaError(f"{actividad.id} depende de {dependencia_id}, que no existe")
    ciclo = buscar_ciclo(actividades)
    if ciclo is not None:
        raise CicloDependenciaError(ciclo)


def _validar_claves(entidades: Mapping[str, object], tipo: type, nombre: str) -> None:
    for clave, entidad in entidades.items():
        if not isinstance(entidad, tipo):
            raise ValidacionError(nombre, f"{clave} no es un {tipo.__name__}")
        if entidad.id != clave:
            raise ReferenciaError(f"La clave {clave} no coincide con el ID {entidad.id}")


def _indexar(entidades: Iterable, nombre: str) -> dict:
    resultado = {}
    for entidad in entidades:
        if entidad.id in resultado:
            raise ReferenciaError(f"ID duplicado: {entidad.id} aparece dos veces como {nombre}")
        resultado[entidad.id] = entidad
    return resultado


def _editar(entidad, cambios: Mapping[str, object]):
    if "id" in cambios and cambios["id"] != entidad.id:
        raise ValidacionError("id", "no se puede modificar")
    try:
        return replace(entidad, **cambios)
    except TypeError as error:
        raise ValidacionError("campos", f"campo desconocido: {error}") from None
