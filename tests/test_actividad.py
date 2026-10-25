from datetime import datetime

import pytest

from planificador.dominio import Actividad, EstadoActividad, Prioridad, ValidacionError


def _hora(hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 1, 1, hora, minuto)


def _actividad(**overrides) -> Actividad:
    valores = dict(
        id="A001",
        descripcion="Instalación especializada",
        duracion_horas=6,
        prioridad=Prioridad.ALTA,
        inicio_permitido=_hora(8),
        fecha_limite=_hora(17),
        habilidades_requeridas=frozenset({"instalacion"}),
        cantidad_recursos=1,
        dependencias=frozenset(),
    )
    valores.update(overrides)
    return Actividad(**valores)


def test_actividad_valida_queda_pendiente_por_defecto():
    actividad = _actividad()

    assert actividad.estado == EstadoActividad.PENDIENTE


def test_duracion_cero_o_negativa_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        _actividad(duracion_horas=0)

    with pytest.raises(ValidacionError):
        _actividad(duracion_horas=-3)


def test_inicio_permitido_mayor_o_igual_a_fecha_limite_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        _actividad(inicio_permitido=_hora(17), fecha_limite=_hora(8))

    with pytest.raises(ValidacionError):
        _actividad(inicio_permitido=_hora(8), fecha_limite=_hora(8))


def test_cantidad_recursos_menor_a_uno_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        _actividad(cantidad_recursos=0)


def test_cantidad_recursos_no_entera_lanza_validacion_error():
    with pytest.raises(ValidacionError):
        _actividad(cantidad_recursos=1.5)


def test_a001_que_depende_de_a001_lanza_error():
    with pytest.raises(ValidacionError):
        _actividad(id="A001", dependencias=frozenset({"A001"}))


def test_actividad_puede_depender_de_otras_actividades():
    actividad = _actividad(id="A005", dependencias=frozenset({"A002", "A004"}))

    assert actividad.dependencias == frozenset({"A002", "A004"})
