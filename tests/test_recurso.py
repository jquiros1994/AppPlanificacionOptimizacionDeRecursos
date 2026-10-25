from datetime import datetime

import pytest

from planificador.dominio import (
    EstadoRecurso,
    Intervalo,
    Recurso,
    TipoRecurso,
    ValidacionError,
)


def _hora(hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 1, 1, hora, minuto)


def _recurso(**overrides) -> Recurso:
    valores = dict(
        id="R002",
        nombre="Técnico de instalaciones",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=5000,
        habilidades=frozenset({"instalacion"}),
        disponibilidad=(Intervalo(_hora(8), _hora(12)),),
    )
    valores.update(overrides)
    return Recurso(**valores)


def test_recurso_valido_queda_activo_por_defecto():
    recurso = _recurso()

    assert recurso.estado == EstadoRecurso.ACTIVO
    assert recurso.esta_activo


def test_capacidad_menor_a_uno_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        _recurso(capacidad=0)


def test_capacidad_no_entera_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        _recurso(capacidad=1.5)


def test_costo_negativo_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        _recurso(costo_hora=-100)


def test_habilidades_vacias_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        _recurso(habilidades=frozenset())


def test_tiene_habilidades_cuando_cubre_todas_las_requeridas():
    recurso = _recurso(habilidades=frozenset({"instalacion", "soldadura"}))

    assert recurso.tiene_habilidades(frozenset({"instalacion"}))
    assert not recurso.tiene_habilidades(frozenset({"electricidad"}))


def test_r002_08_12_rechaza_tarea_11_14():
    recurso = _recurso(disponibilidad=(Intervalo(_hora(8), _hora(12)),))

    tarea = Intervalo(_hora(11), _hora(14))

    assert not recurso.esta_disponible(tarea)


def test_recurso_disponible_para_intervalo_contenido():
    recurso = _recurso(disponibilidad=(Intervalo(_hora(8), _hora(12)),))

    tarea = Intervalo(_hora(9), _hora(11))

    assert recurso.esta_disponible(tarea)


def test_recurso_disponible_considera_varias_ventanas():
    recurso = _recurso(
        disponibilidad=(
            Intervalo(_hora(8), _hora(12)),
            Intervalo(_hora(14), _hora(17)),
        )
    )

    assert recurso.esta_disponible(Intervalo(_hora(15), _hora(16)))
    assert not recurso.esta_disponible(Intervalo(_hora(12), _hora(14)))


def test_desactivar_cambia_estado_y_esta_activo():
    recurso = _recurso()

    recurso.desactivar()

    assert recurso.estado == EstadoRecurso.INACTIVO
    assert not recurso.esta_activo
