"""Convierte un orden de actividades en asignaciones que cumplen las restricciones duras."""

from __future__ import annotations

import heapq
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from planificador.dominio.asignacion import Asignacion
from planificador.dominio.enums import EstadoActividad
from planificador.dominio.escenario import Escenario
from planificador.dominio.intervalo import Intervalo
from planificador.dominio.recurso import Recurso


@dataclass(frozen=True)
class ResultadoDecodificacion:
    asignaciones: tuple[Asignacion, ...]
    pendientes: dict[str, str]


class Decodificador:
    """Programa cada actividad en el primer instante con recursos suficientes.

    Recibe pares (actividad_id, preferencia). El orden define quién reserva recursos
    primero y la preferencia elige qué recursos compatibles se usan, empezando por
    el más barato. Una actividad nunca se procesa antes que sus dependencias.
    """

    def __init__(self, escenario: Escenario, horizonte: Intervalo | None = None) -> None:
        self._escenario = escenario
        self._horizonte = horizonte
        self._pendientes_ids = tuple(sorted(
            actividad.id for actividad in escenario.actividades.values()
            if actividad.estado == EstadoActividad.PENDIENTE
        ))
        self._candidatos = {
            actividad_id: self._buscar_candidatos(actividad_id)
            for actividad_id in self._pendientes_ids
        }

    @property
    def actividades_ids(self) -> tuple[str, ...]:
        return self._pendientes_ids

    def cantidad_candidatos(self, actividad_id: str) -> int:
        return len(self._candidatos[actividad_id])

    def decodificar(self, genes: Sequence[tuple[str, int]]) -> ResultadoDecodificacion:
        preferencias = dict(genes)
        if sorted(preferencias) != list(self._pendientes_ids) or len(genes) != len(preferencias):
            raise ValueError("los genes deben contener cada actividad pendiente una sola vez")

        ocupacion: dict[str, list[Intervalo]] = {rid: [] for rid in self._escenario.recursos}
        fines: dict[str, datetime] = {}
        pendientes: dict[str, str] = {}
        asignaciones: list[Asignacion] = []

        for actividad_id in self._orden_respetando_dependencias([gen[0] for gen in genes]):
            motivo = self._motivo_por_dependencias(actividad_id, fines, pendientes)
            if motivo is None:
                asignacion = self._programar(actividad_id, preferencias[actividad_id], ocupacion, fines)
                if asignacion is None:
                    motivo = self._motivo_sin_horario(actividad_id)
                else:
                    asignaciones.append(asignacion)
                    fines[actividad_id] = asignacion.intervalo.fin
                    for recurso_id in asignacion.recursos_ids:
                        ocupacion[recurso_id].append(asignacion.intervalo)
            if motivo is not None:
                pendientes[actividad_id] = motivo

        asignaciones.sort(key=lambda a: a.actividad_id)
        return ResultadoDecodificacion(tuple(asignaciones), pendientes)

    def _buscar_candidatos(self, actividad_id: str) -> tuple[Recurso, ...]:
        actividad = self._escenario.actividades[actividad_id]
        compatibles = (
            recurso for recurso in self._escenario.recursos.values()
            if recurso.esta_activo and recurso.tiene_habilidades(actividad.habilidades_requeridas)
        )
        return tuple(sorted(compatibles, key=lambda r: (r.costo_hora, r.id)))

    def _orden_respetando_dependencias(self, orden: list[str]) -> list[str]:
        """Recorre el orden dado, pero pospone cada actividad hasta procesar sus dependencias."""
        posicion = {actividad_id: indice for indice, actividad_id in enumerate(orden)}
        faltantes = {}
        dependientes: dict[str, list[str]] = {actividad_id: [] for actividad_id in orden}
        for actividad_id in orden:
            internas = [d for d in self._escenario.actividades[actividad_id].dependencias if d in posicion]
            faltantes[actividad_id] = len(internas)
            for dependencia_id in internas:
                dependientes[dependencia_id].append(actividad_id)

        listas = [(posicion[aid], aid) for aid in orden if faltantes[aid] == 0]
        heapq.heapify(listas)
        resultado = []
        while listas:
            _, actividad_id = heapq.heappop(listas)
            resultado.append(actividad_id)
            for dependiente_id in dependientes[actividad_id]:
                faltantes[dependiente_id] -= 1
                if faltantes[dependiente_id] == 0:
                    heapq.heappush(listas, (posicion[dependiente_id], dependiente_id))
        return resultado

    def _motivo_por_dependencias(
        self, actividad_id: str, fines: dict[str, datetime], pendientes: dict[str, str],
    ) -> str | None:
        for dependencia_id in sorted(self._escenario.actividades[actividad_id].dependencias):
            if dependencia_id in fines:
                continue
            dependencia = self._escenario.actividades[dependencia_id]
            if dependencia_id in pendientes or dependencia.estado != EstadoActividad.COMPLETADA:
                return f"la dependencia {dependencia_id} no tiene asignación"
        return None

    def _motivo_sin_horario(self, actividad_id: str) -> str:
        actividad = self._escenario.actividades[actividad_id]
        candidatos = self._candidatos[actividad_id]
        if not candidatos:
            return "no hay recursos activos con las habilidades requeridas"
        if len(candidatos) < actividad.cantidad_recursos:
            return (f"requiere {actividad.cantidad_recursos} recursos compatibles "
                    f"y solo existen {len(candidatos)}")
        return "no hay horario con recursos suficientes dentro del horizonte"

    def _programar(
        self, actividad_id: str, preferencia: int,
        ocupacion: dict[str, list[Intervalo]], fines: dict[str, datetime],
    ) -> Asignacion | None:
        actividad = self._escenario.actividades[actividad_id]
        candidatos = self._candidatos[actividad_id]
        if len(candidatos) < actividad.cantidad_recursos:
            return None

        duracion = timedelta(hours=actividad.duracion_horas)
        dependencias = [fines[d] for d in actividad.dependencias if d in fines]
        minimo = max([actividad.inicio_permitido, *dependencias])
        if self._horizonte is not None:
            minimo = max(minimo, self._horizonte.inicio)

        for inicio in self._instantes_candidatos(minimo, candidatos, ocupacion):
            intervalo = Intervalo(inicio, inicio + duracion)
            if self._horizonte is not None and intervalo.fin > self._horizonte.fin:
                break
            compatibles = [
                recurso for recurso in candidatos
                if recurso.esta_disponible(intervalo)
                and _ocupacion_maxima(ocupacion[recurso.id], intervalo) < recurso.capacidad
            ]
            if len(compatibles) >= actividad.cantidad_recursos:
                desde = preferencia % len(compatibles)
                elegidos = (compatibles[desde:] + compatibles[:desde])[:actividad.cantidad_recursos]
                return Asignacion(actividad_id, frozenset(r.id for r in elegidos), intervalo)
        return None

    @staticmethod
    def _instantes_candidatos(
        minimo: datetime, candidatos: Sequence[Recurso], ocupacion: dict[str, list[Intervalo]],
    ) -> list[datetime]:
        """Instantes donde puede cambiar la factibilidad: inicios de ventana y fines de ocupación."""
        instantes = {minimo}
        for recurso in candidatos:
            instantes.update(v.inicio for v in recurso.disponibilidad if v.inicio > minimo)
            instantes.update(i.fin for i in ocupacion[recurso.id] if i.fin > minimo)
        return sorted(instantes)


def _ocupacion_maxima(ocupados: list[Intervalo], intervalo: Intervalo) -> int:
    """Máximo de asignaciones simultáneas de un recurso dentro del intervalo."""
    eventos = []
    for otro in ocupados:
        comun = otro.interseccion(intervalo)
        if comun is not None:
            eventos.append((comun.inicio, 1))
            eventos.append((comun.fin, -1))
    eventos.sort()
    actual = maximo = 0
    for _, cambio in eventos:
        actual += cambio
        maximo = max(maximo, actual)
    return maximo
