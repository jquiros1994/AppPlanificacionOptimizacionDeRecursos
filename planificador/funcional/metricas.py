from __future__ import annotations

from collections.abc import Iterable
from functools import reduce
from math import fsum, isclose

from planificador.dominio import (
    Actividad, Escenario, Intervalo, Planificacion, Prioridad,
    Recurso, ReferenciaError,
)


def filtrar_recursos_activos(recursos: Iterable[Recurso]) -> tuple[Recurso, ...]:
    return tuple(filter(lambda recurso: recurso.esta_activo, recursos))


def ordenar_actividades(actividades: Iterable[Actividad]) -> tuple[Actividad, ...]:
    return tuple(sorted(actividades, key=lambda a: (-a.prioridad, a.fecha_limite, a.id)))


def agrupar_actividades_por_prioridad(
    actividades: Iterable[Actividad],
) -> dict[Prioridad, tuple[Actividad, ...]]:
    def agregar(grupos, actividad):
        return {**grupos, actividad.prioridad: grupos[actividad.prioridad] + (actividad,)}

    return reduce(agregar, actividades, {prioridad: () for prioridad in Prioridad})


def _validar_referencias(plan: Planificacion, escenario: Escenario) -> None:
    for asignacion in plan.asignaciones:
        if asignacion.actividad_id not in escenario.actividades:
            raise ReferenciaError(f"Actividad inexistente: {asignacion.actividad_id}")
        for recurso_id in sorted(asignacion.recursos_ids):
            if recurso_id not in escenario.recursos:
                raise ReferenciaError(f"Recurso inexistente: {recurso_id}")


def calcular_costo_total(plan: Planificacion, escenario: Escenario) -> float:
    _validar_referencias(plan, escenario)
    return fsum(map(
        lambda a: a.intervalo.duracion_horas() * fsum(
            escenario.recursos[rid].costo_hora for rid in sorted(a.recursos_ids)
        ), plan.asignaciones,
    ))


def costos_por_recurso(plan: Planificacion, escenario: Escenario) -> dict[str, float]:
    _validar_referencias(plan, escenario)
    return {
        rid: fsum(map(
            lambda a: a.intervalo.duracion_horas() * escenario.recursos[rid].costo_hora,
            filter(lambda a: rid in a.recursos_ids, plan.asignaciones),
        ))
        for rid in sorted(escenario.recursos)
    }


def tareas_retrasadas(plan: Planificacion, escenario: Escenario) -> dict[str, float]:
    """Retraso por actividad, contado una vez aunque tenga varios recursos."""
    _validar_referencias(plan, escenario)
    retrasos = {}
    for aid in sorted(escenario.actividades):
        asignaciones = plan.asignaciones_de_actividad(aid)
        if asignaciones:
            fin = max(map(lambda a: a.intervalo.fin, asignaciones))
            horas = (fin - escenario.actividades[aid].fecha_limite).total_seconds() / 3600
            if horas > 0:
                retrasos[aid] = horas
    return retrasos


def _horas_union(intervalos: Iterable[Intervalo]) -> float:
    """Evita contar dos veces ventanas de disponibilidad superpuestas."""
    ordenados = sorted(intervalos, key=lambda i: (i.inicio, i.fin))
    if not ordenados:
        return 0.0
    inicio, fin = ordenados[0].inicio, ordenados[0].fin
    segundos = 0.0
    for intervalo in ordenados[1:]:
        if intervalo.inicio <= fin:
            fin = max(fin, intervalo.fin)
        else:
            segundos += (fin - inicio).total_seconds()
            inicio, fin = intervalo.inicio, intervalo.fin
    return (segundos + (fin - inicio).total_seconds()) / 3600


def utilizacion_por_recurso(
    plan: Planificacion, escenario: Escenario, horizonte: Intervalo,
) -> dict[str, float | None]:
    """Razón entre horas asignadas y horas disponibles multiplicadas por capacidad.

    Se recorta al horizonte. No se limita a 1: una sobreasignación debe poder
    observarse. El motor de reglas determina la validez de los intervalos.
    """
    _validar_referencias(plan, escenario)
    resultado = {}
    for rid, recurso in sorted(escenario.recursos.items()):
        ventanas = tuple(filter(None, map(
            lambda i: i.interseccion(horizonte), recurso.disponibilidad,
        )))
        disponibles = _horas_union(ventanas) * recurso.capacidad
        ocupados = fsum(
            recorte.duracion_horas()
            for a in plan.asignaciones_de_recurso(rid)
            if (recorte := a.intervalo.interseccion(horizonte)) is not None
        )
        resultado[rid] = ocupados / disponibles if disponibles else None
    return resultado


def recursos_activos_imperativo(recursos: Iterable[Recurso]) -> tuple[Recurso, ...]:
    activos = []
    for recurso in recursos:
        if recurso.esta_activo:
            activos.append(recurso)
    return tuple(activos)


def costo_total_imperativo(plan: Planificacion, escenario: Escenario) -> float:
    _validar_referencias(plan, escenario)
    total = 0.0
    for asignacion in plan.asignaciones:
        for rid in sorted(asignacion.recursos_ids):
            total += escenario.recursos[rid].costo_hora * asignacion.intervalo.duracion_horas()
    return total


def agrupar_prioridad_imperativo(
    actividades: Iterable[Actividad],
) -> dict[Prioridad, tuple[Actividad, ...]]:
    grupos = {prioridad: [] for prioridad in Prioridad}
    for actividad in actividades:
        grupos[actividad.prioridad].append(actividad)
    return {prioridad: tuple(grupo) for prioridad, grupo in grupos.items()}


def comparar_operaciones(plan: Planificacion, escenario: Escenario) -> dict[str, bool]:
    recursos = tuple(escenario.recursos.values())
    actividades = tuple(escenario.actividades.values())
    return {
        "recursos_activos": filtrar_recursos_activos(recursos) == recursos_activos_imperativo(recursos),
        "costo_total": isclose(
            calcular_costo_total(plan, escenario), costo_total_imperativo(plan, escenario),
            rel_tol=1e-9, abs_tol=1e-9,
        ),
        "actividades_por_prioridad": (
            agrupar_actividades_por_prioridad(actividades) == agrupar_prioridad_imperativo(actividades)
        ),
    }
