"""Veredicto único de factibilidad (RF-03) y su uso en los algoritmos (RF-04, RF-05)."""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

import pytest

from planificador.algoritmos import AlgoritmoBase, Decodificador, EvaluadorAptitud
from planificador.dominio import (
    Actividad, Asignacion, CicloDependenciaError, Escenario, EstadoActividad,
    Intervalo, Planificacion, Prioridad, Recurso, TipoRecurso,
)
from planificador.reglas.incidencia import Categoria, Incidencia
from planificador.reglas.motor_reglas import MotorReglas
from planificador.reglas.regla_horizonte import ReglaHorizonte


def _h(hora: float) -> datetime:
    return datetime(2026, 11, 2) + timedelta(hours=hora)


def _recurso(rid="R001", capacidad=1, costo=100.0, ventanas=((8, 17),), habilidades=("x",)):
    return Recurso(
        id=rid, nombre=rid, tipo=TipoRecurso.HUMANO, capacidad=capacidad, costo_hora=costo,
        habilidades=frozenset(habilidades),
        disponibilidad=tuple(Intervalo(_h(i), _h(f)) for i, f in ventanas),
    )


def _actividad(aid, duracion=2.0, dependencias=(), estado=EstadoActividad.PENDIENTE,
               prioridad=Prioridad.MEDIA, limite=17.0, cantidad=1):
    return Actividad(
        id=aid, descripcion=aid, duracion_horas=duracion, prioridad=prioridad,
        inicio_permitido=_h(8), fecha_limite=_h(limite),
        habilidades_requeridas=frozenset({"x"}), cantidad_recursos=cantidad,
        dependencias=frozenset(dependencias), estado=estado,
    )


def _escenario(recursos, actividades):
    return Escenario({r.id: r for r in recursos}, {a.id: a for a in actividades})


def _asignacion(aid, inicio, fin, *recursos):
    return Asignacion(aid, frozenset(recursos or ("R001",)), Intervalo(_h(inicio), _h(fin)))


def _validar(escenario, *asignaciones, horizonte=None):
    return MotorReglas(horizonte).validar(Planificacion(asignaciones, "prueba"), escenario)


def _reglas(resultado):
    return sorted(i.regla for i in resultado.incidencias)


# --- Veredicto -------------------------------------------------------------

def test_plan_parcial_sin_conflictos_es_factible_y_reporta_pendientes():
    escenario = _escenario([_recurso()], [_actividad("A001"), _actividad("A002")])
    resultado = _validar(escenario, _asignacion("A001", 8, 10))
    assert resultado.factible
    assert resultado.actividades_pendientes == ("A002",)
    assert resultado.conflictos_duros == ()
    assert resultado.a_dict()["estado"] == "FACTIBLE"


def test_un_conflicto_duro_hace_no_factible_el_plan():
    escenario = _escenario([_recurso()], [_actividad("A001"), _actividad("A002")])
    resultado = _validar(escenario, _asignacion("A001", 8, 10), _asignacion("A002", 9, 11))
    assert not resultado.factible
    assert resultado.por_regla(solo_duras=True) == {"CAPACIDAD": 1}
    assert resultado.a_dict()["estado"] == "NO FACTIBLE"


def test_resultado_validacion_es_serializable():
    escenario = _escenario([_recurso()], [_actividad("A001", limite=9), _actividad("A002")])
    resultado = _validar(escenario, _asignacion("A001", 8, 10), _asignacion("A002", 9, 11))
    datos = json.loads(json.dumps(resultado.a_dict()))
    assert datos["retrasos_por_actividad"]["A001"] == 1.0
    assert datos["conflictos_duros"][0]["actividades_ids"] == ["A001", "A002"]


# --- Ejemplos literales de RF-03 ------------------------------------------

def test_rf03_capacidad_reporta_ambas_actividades_y_el_solape():
    escenario = _escenario([_recurso()], [_actividad("A001", 4), _actividad("A004", 3)])
    resultado = _validar(escenario, _asignacion("A001", 8, 12), _asignacion("A004", 10, 13))
    [conflicto] = resultado.conflictos_duros
    assert conflicto.regla == "CAPACIDAD"
    assert conflicto.recurso_id == "R001"
    assert conflicto.actividades_ids == ("A001", "A004")
    assert (conflicto.inicio, conflicto.fin) == (_h(10), _h(12))
    assert "10:00" in conflicto.mensaje and "12:00" in conflicto.mensaje


def test_rf03_dependencia_incumplida_indica_ambas_actividades():
    escenario = _escenario(
        [_recurso(capacidad=2)], [_actividad("A002"), _actividad("A005", dependencias={"A002"})],
    )
    resultado = _validar(escenario, _asignacion("A002", 8, 10), _asignacion("A005", 9, 11))
    [conflicto] = resultado.conflictos_duros
    assert conflicto.regla == "DEPENDENCIAS"
    assert conflicto.actividad_id == "A005"
    assert conflicto.actividades_ids == ("A002", "A005")
    assert (conflicto.inicio, conflicto.fin) == (_h(9), _h(10))


def test_capacidad_separa_tramos_y_acepta_intervalos_que_se_tocan():
    escenario = _escenario([_recurso()], [_actividad(f"A00{i}") for i in range(1, 5)])
    resultado = _validar(
        escenario,
        _asignacion("A001", 8, 10), _asignacion("A002", 9, 11),
        _asignacion("A003", 13, 15), _asignacion("A004", 14, 16),
    )
    tramos = [(c.actividades_ids, c.inicio, c.fin) for c in resultado.conflictos_duros]
    assert tramos == [(("A001", "A002"), _h(9), _h(10)), (("A003", "A004"), _h(14), _h(15))]

    contiguas = _validar(escenario, _asignacion("A001", 8, 10), _asignacion("A002", 10, 12))
    assert "CAPACIDAD" not in _reglas(contiguas)


def test_capacidad_dos_admite_dos_simultaneas_y_reporta_la_tercera():
    escenario = _escenario([_recurso(capacidad=2)], [_actividad(f"A00{i}") for i in range(1, 4)])
    dos = _validar(escenario, _asignacion("A001", 8, 10), _asignacion("A002", 8, 10))
    assert "CAPACIDAD" not in _reglas(dos)
    tres = _validar(
        escenario, _asignacion("A001", 8, 10), _asignacion("A002", 8, 10), _asignacion("A003", 9, 11),
    )
    [conflicto] = tres.conflictos_duros
    assert conflicto.actividades_ids == ("A001", "A002", "A003")
    assert (conflicto.inicio, conflicto.fin) == (_h(9), _h(10))


# --- Estados de las actividades -------------------------------------------

@pytest.mark.parametrize("estado", [
    EstadoActividad.ASIGNADA, EstadoActividad.COMPLETADA, EstadoActividad.CANCELADA,
])
def test_actividad_no_pendiente_fuera_del_plan_no_genera_incidencias(estado):
    escenario = _escenario([_recurso()], [_actividad("A001", estado=estado)])
    resultado = _validar(escenario)
    assert resultado.incidencias == ()
    assert resultado.factible


@pytest.mark.parametrize("estado", [EstadoActividad.COMPLETADA, EstadoActividad.CANCELADA])
def test_actividad_completada_o_cancelada_no_puede_asignarse(estado):
    escenario = _escenario([_recurso()], [_actividad("A001", estado=estado)])
    resultado = _validar(escenario, _asignacion("A001", 8, 10))
    assert _reglas(resultado) == ["ESTADO_NO_PLANIFICABLE"]
    assert not resultado.factible


def test_dependencia_completada_se_cumple_sin_estar_en_el_plan():
    escenario = _escenario([_recurso()], [
        _actividad("A001", estado=EstadoActividad.COMPLETADA),
        _actividad("A002", dependencias={"A001"}),
    ])
    resultado = _validar(escenario, _asignacion("A002", 8, 10))
    assert resultado.factible
    assert resultado.incidencias == ()


def test_dependencia_cancelada_impide_programar_la_sucesora():
    escenario = _escenario([_recurso()], [
        _actividad("A001", estado=EstadoActividad.CANCELADA),
        _actividad("A002", dependencias={"A001"}),
    ])
    resultado = _validar(escenario, _asignacion("A002", 8, 10))
    assert _reglas(resultado) == ["DEPENDENCIA_CANCELADA"]


def test_dependencia_pendiente_sin_programar_es_conflicto():
    escenario = _escenario([_recurso()], [_actividad("A001"), _actividad("A002", dependencias={"A001"})])
    resultado = _validar(escenario, _asignacion("A002", 8, 10))
    assert _reglas(resultado) == ["ACTIVIDAD_SIN_ASIGNACION", "DEPENDENCIA_SIN_ASIGNACION"]
    assert not resultado.factible
    assert resultado.actividades_pendientes == ("A001",)


# --- Regla opcional de horizonte y extensibilidad --------------------------

def test_horizonte_es_regla_opcional():
    escenario = _escenario([_recurso()], [_actividad("A001")])
    horizonte = Intervalo(_h(8), _h(12))
    assert _validar(escenario, _asignacion("A001", 14, 16)).factible
    fuera = _validar(escenario, _asignacion("A001", 14, 16), horizonte=horizonte)
    assert _reglas(fuera) == ["FUERA_DE_HORIZONTE"]
    assert _validar(escenario, _asignacion("A001", 10, 12), horizonte=horizonte).factible

    motor = MotorReglas()
    motor.agregar_regla(ReglaHorizonte(horizonte))
    plan = Planificacion((_asignacion("A001", 14, 16),), "prueba")
    assert not motor.validar(plan, escenario).factible


# --- Incidencia ------------------------------------------------------------

def test_incidencia_conserva_compatibilidad_y_ordena_ids():
    incidencia = Incidencia("X", "m", actividad_id="A2", recurso_id="R9",
                            actividades_ids=("A3", "A1"), recursos_ids=("R1",))
    assert incidencia.actividades_ids == ("A1", "A2", "A3")
    assert incidencia.recursos_ids == ("R1", "R9")
    assert incidencia.es_dura and incidencia.categoria is Categoria.DURA
    assert hash(incidencia) == hash(Incidencia("X", "m", actividad_id="A2", recurso_id="R9",
                                               actividades_ids=("A1", "A3"), recursos_ids=("R1",)))
    assert json.loads(json.dumps(incidencia.a_dict()))["recursos_ids"] == ["R1", "R9"]


_GUION_ORDEN = """
from datetime import datetime
from planificador.dominio import *
from planificador.reglas.motor_reglas import MotorReglas
h = lambda x: datetime(2026, 11, 2, x)
ids = [f"R{i}" for i in range(6)]
recursos = {i: Recurso(i, i, TipoRecurso.HUMANO, 1, 1.0, frozenset("y"), (Intervalo(h(8), h(9)),)) for i in ids}
actividad = Actividad("A1", "a", 2, Prioridad.MEDIA, h(8), h(17), frozenset("x"), 6, frozenset())
plan = Planificacion((Asignacion("A1", frozenset(ids), Intervalo(h(8), h(10))),), "x")
print([(i.regla, i.recurso_id) for i in MotorReglas().evaluar(plan, Escenario(recursos, {"A1": actividad}))])
"""


def test_orden_de_incidencias_no_depende_de_la_semilla_de_hash():
    """Con spawn, cada proceso tiene otra PYTHONHASHSEED; el diagnóstico debe coincidir (RF-07)."""
    salidas = {
        subprocess.run(
            [sys.executable, "-c", _GUION_ORDEN], capture_output=True, text=True, check=True,
            env={**os.environ, "PYTHONHASHSEED": semilla},
        ).stdout
        for semilla in ("1", "2", "3")
    }
    assert len(salidas) == 1


# --- Decodificador alineado con el motor ----------------------------------

@pytest.mark.parametrize("estado, motivo", [
    (EstadoActividad.CANCELADA, "cancelada"),
    (EstadoActividad.ASIGNADA, "fuera de esta planificación"),
])
def test_decodificador_explica_dependencias_no_programables(estado, motivo):
    escenario = _escenario([_recurso()], [_actividad("A001", estado=estado), _actividad("A002", dependencias={"A001"})])
    resultado = Decodificador(escenario).decodificar([("A002", 0)])
    assert resultado.asignaciones == ()
    assert motivo in resultado.pendientes["A002"]


def test_decodificador_acepta_dependencia_completada_y_el_motor_coincide():
    escenario = _escenario([_recurso()], [
        _actividad("A001", estado=EstadoActividad.COMPLETADA),
        _actividad("A002", dependencias={"A001"}),
    ])
    resultado = AlgoritmoBase(escenario).ejecutar()
    assert [a.actividad_id for a in resultado.planificacion.asignaciones] == ["A002"]
    assert resultado.aptitud.factible
    assert MotorReglas().validar(resultado.planificacion, escenario).factible


def test_decodificador_no_pierde_actividades_de_un_ciclo():
    escenario = _escenario([_recurso()], [
        _actividad("A001", dependencias={"A002"}), _actividad("A002", dependencias={"A001"}),
    ])
    with pytest.raises(CicloDependenciaError):
        Decodificador(escenario).decodificar([("A001", 0), ("A002", 0)])


# --- Aptitud ---------------------------------------------------------------

def test_asignar_mas_siempre_mejora_aunque_retrase_a_otras():
    """Contraejemplo H1: con la penalización anterior, dejar L pendiente salía mejor."""
    recursos = [_recurso(f"R{i:02}", ventanas=((8, 10), (10, 11))) for i in range(10)]
    criticas = [_actividad(f"C{i:02}", 1, prioridad=Prioridad.CRITICA, limite=9) for i in range(10)]
    larga = _actividad("L", 2, prioridad=Prioridad.BAJA, limite=11, cantidad=10)
    escenario = _escenario(recursos, [*criticas, larga])
    evaluador, decodificador = EvaluadorAptitud(escenario), Decodificador(escenario)

    def aptitud(orden):
        plan = Planificacion(decodificador.decodificar([(aid, 0) for aid in orden]).asignaciones, "x")
        return evaluador.evaluar(plan)

    todas = aptitud(["L", *(c.id for c in criticas)])
    sin_l = aptitud([*(c.id for c in criticas), "L"])
    assert (todas.asignadas, sin_l.asignadas) == (11, 10)
    assert todas.horas_retraso > sin_l.horas_retraso
    assert todas.valor < sin_l.valor


def test_un_conflicto_nunca_es_mejor_que_dejar_pendientes():
    """Contraejemplo H2: cuatro críticas solapadas salían mejor que el plan vacío."""
    escenario = _escenario([_recurso()], [_actividad(f"A{i}", prioridad=Prioridad.CRITICA) for i in range(4)])
    evaluador = EvaluadorAptitud(escenario)
    solapadas = evaluador.evaluar(Planificacion(tuple(_asignacion(f"A{i}", 8, 10) for i in range(4)), "x"))
    vacio = evaluador.evaluar(Planificacion((), "x"))
    assert not solapadas.factible and vacio.factible
    assert vacio.valor < solapadas.valor


def test_aptitud_con_referencias_inexistentes_no_lanza_excepcion():
    escenario = _escenario([_recurso()], [_actividad("A001")])
    resultado = EvaluadorAptitud(escenario).evaluar(
        Planificacion((_asignacion("NO", 8, 10), _asignacion("A001", 8, 10, "R999")), "x"),
    )
    assert not resultado.factible
    assert {"REFERENCIA_ACTIVIDAD", "REFERENCIA_RECURSO"} <= {i.regla for i in resultado.conflictos_duros}
    assert resultado.costo == 0


def test_retraso_de_aptitud_coincide_con_el_motor_con_asignaciones_duplicadas():
    escenario = _escenario([_recurso(capacidad=2)], [_actividad("A001", limite=9)])
    plan = Planificacion((_asignacion("A001", 8, 10), _asignacion("A001", 9, 11)), "x")
    assert EvaluadorAptitud(escenario).evaluar(plan).horas_retraso == MotorReglas().validar(plan, escenario).horas_retraso == 2
