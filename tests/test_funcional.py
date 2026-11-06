from copy import deepcopy
from datetime import datetime
from math import isclose

import pytest

from planificador.dominio import (
    Actividad, Asignacion, Escenario, EstadoRecurso, Intervalo, Planificacion,
    Prioridad, Recurso, ReferenciaError, TipoRecurso,
)
from planificador.funcional import (
    agrupar_actividades_por_prioridad, calcular_costo_total, comparar_operaciones,
    costos_por_recurso, filtrar_recursos_activos, ordenar_actividades,
    tareas_retrasadas, utilizacion_por_recurso,
)


def _hora(hora):
    return datetime(2026, 11, 2, hora)


@pytest.fixture
def datos():
    escenario = Escenario()
    for rid, costo, capacidad, estado in (
        ("R001", 1000, 2, EstadoRecurso.ACTIVO),
        ("R002", 2000, 1, EstadoRecurso.ACTIVO),
        ("R003", 3000, 1, EstadoRecurso.INACTIVO),
    ):
        ventanas = (Intervalo(_hora(8), _hora(12)), Intervalo(_hora(9), _hora(11)))
        escenario.agregar_recurso(Recurso(
            rid, rid, TipoRecurso.HUMANO, capacidad, costo,
            frozenset({"instalacion"}), ventanas if rid != "R003" else (), estado,
        ))
    for aid, duracion, prioridad, limite in (
        ("A001", 2, Prioridad.MEDIA, 9), ("A002", 1, Prioridad.CRITICA, 11),
    ):
        escenario.agregar_actividad(Actividad(
            aid, aid, duracion, prioridad, _hora(8), _hora(limite),
            frozenset({"instalacion"}), 1, frozenset(),
        ))
    plan = Planificacion((
        Asignacion("A001", frozenset({"R001", "R002"}), Intervalo(_hora(8), _hora(10))),
        Asignacion("A002", frozenset({"R001"}), Intervalo(_hora(10), _hora(11))),
    ), "prueba", 2026)
    return escenario, plan


def test_filtrado_ordenamiento_y_grupos(datos):
    escenario, _ = datos
    assert tuple(r.id for r in filtrar_recursos_activos(escenario.recursos.values())) == ("R001", "R002")
    assert tuple(a.id for a in ordenar_actividades(escenario.actividades.values())) == ("A002", "A001")
    grupos = agrupar_actividades_por_prioridad(escenario.actividades.values())
    assert tuple(a.id for a in grupos[Prioridad.MEDIA]) == ("A001",)
    assert grupos[Prioridad.BAJA] == ()


def test_desempate_por_fecha_y_id():
    def actividad(aid, limite):
        return Actividad(aid, aid, 1, Prioridad.ALTA, _hora(8), _hora(limite), frozenset(), 1, frozenset())
    actividades = [actividad("A003", 12), actividad("A002", 10), actividad("A001", 10)]
    assert [a.id for a in ordenar_actividades(actividades)] == ["A001", "A002", "A003"]


def test_costos_multirrecurso_y_retraso_sin_duplicar(datos):
    escenario, plan = datos
    assert calcular_costo_total(plan, escenario) == 7000
    assert costos_por_recurso(plan, escenario) == {"R001": 3000, "R002": 4000, "R003": 0}
    assert tareas_retrasadas(plan, escenario) == {"A001": 1}
    assert all(comparar_operaciones(plan, escenario).values())


def test_utilizacion_considera_capacidad_union_y_horizonte(datos):
    escenario, plan = datos
    uso = utilizacion_por_recurso(plan, escenario, Intervalo(_hora(8), _hora(12)))
    assert isclose(uso["R001"], 3 / 8)
    assert isclose(uso["R002"], 2 / 4)
    assert uso["R003"] is None
    recortado = utilizacion_por_recurso(plan, escenario, Intervalo(_hora(10), _hora(12)))
    assert recortado["R001"] == 1 / 4
    assert recortado["R002"] == 0


def test_todas_las_metricas_son_repetibles_y_no_modifican_entradas(datos):
    escenario, plan = datos
    original = deepcopy(datos)
    operaciones = (
        lambda: filtrar_recursos_activos(escenario.recursos.values()),
        lambda: ordenar_actividades(escenario.actividades.values()),
        lambda: agrupar_actividades_por_prioridad(escenario.actividades.values()),
        lambda: calcular_costo_total(plan, escenario),
        lambda: costos_por_recurso(plan, escenario),
        lambda: tareas_retrasadas(plan, escenario),
        lambda: utilizacion_por_recurso(plan, escenario, Intervalo(_hora(8), _hora(12))),
        lambda: comparar_operaciones(plan, escenario),
    )
    for operacion in operaciones:
        assert operacion() == operacion()
        assert datos == original


@pytest.mark.parametrize("funcion", [calcular_costo_total, costos_por_recurso, tareas_retrasadas])
@pytest.mark.parametrize("aid,rid", [("A999", "R001"), ("A001", "R999")])
def test_referencias_invalidas_se_reportan(datos, funcion, aid, rid):
    escenario, _ = datos
    plan = Planificacion((Asignacion(aid, frozenset({rid}), Intervalo(_hora(8), _hora(9))),), "prueba")
    with pytest.raises(ReferenciaError):
        funcion(plan, escenario)


def test_entradas_vacias():
    escenario = Escenario()
    plan = Planificacion((), "vacio")
    assert calcular_costo_total(plan, escenario) == 0
    assert costos_por_recurso(plan, escenario) == {}
    assert tareas_retrasadas(plan, escenario) == {}
    assert filtrar_recursos_activos(()) == ()
    assert all(comparar_operaciones(plan, escenario).values())


def test_ejemplo_costos_del_enunciado():
    escenario = Escenario()
    asignaciones = []
    for i, costo in enumerate((1000, 2000, 3000), 1):
        rid, aid = f"R{i}", f"A{i}"
        escenario.agregar_recurso(Recurso(rid, rid, TipoRecurso.HUMANO, 1, costo,
            frozenset({"x"}), (Intervalo(_hora(8), _hora(12)),)))
        escenario.agregar_actividad(Actividad(aid, aid, 1, Prioridad.BAJA,
            _hora(8), _hora(12), frozenset({"x"}), 1, frozenset()))
        asignaciones.append(Asignacion(aid, frozenset({rid}), Intervalo(_hora(8), _hora(9))))
    plan = Planificacion(tuple(asignaciones), "ejemplo")
    assert calcular_costo_total(plan, escenario) == 6000
    assert comparar_operaciones(plan, escenario)["costo_total"]
