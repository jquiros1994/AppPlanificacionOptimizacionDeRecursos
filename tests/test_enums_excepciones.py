import pytest

from planificador.dominio import (
    CicloDependenciaError,
    EstadoActividad,
    EstadoRecurso,
    PlanificadorError,
    Prioridad,
    ReferenciaError,
    TipoRecurso,
    ValidacionError,
)


def test_prioridades_se_pueden_ordenar():
    desordenadas = [Prioridad.BAJA, Prioridad.CRITICA, Prioridad.MEDIA]
    assert sorted(desordenadas, reverse=True) == [
        Prioridad.CRITICA,
        Prioridad.MEDIA,
        Prioridad.BAJA,
    ]


def test_tipo_recurso_se_crea_desde_texto():
    assert TipoRecurso("equipo") is TipoRecurso.EQUIPO


def test_tipo_recurso_invalido_lanza_error():
    with pytest.raises(ValueError):
        TipoRecurso("robot")


def test_estado_recurso_tiene_activo_e_inactivo():
    assert {e.value for e in EstadoRecurso} == {"activo", "inactivo"}


def test_estado_actividad_tiene_los_cuatro_valores():
    assert {e.value for e in EstadoActividad} == {
        "pendiente",
        "asignada",
        "completada",
        "cancelada",
    }


def test_validacion_error_guarda_campo_y_motivo():
    error = ValidacionError("capacidad", "debe ser >= 1")
    assert error.campo == "capacidad"
    assert str(error) == "capacidad: debe ser >= 1"


def test_referencia_error_se_puede_lanzar():
    with pytest.raises(ReferenciaError):
        raise ReferenciaError("A999 no existe en el escenario")


def test_ciclo_muestra_la_cadena():
    error = CicloDependenciaError(["A002", "A005", "A002"])
    assert "A002 → A005 → A002" in str(error)


def test_todas_heredan_de_planificador_error():
    with pytest.raises(PlanificadorError):
        raise ValidacionError("costo", "no puede ser negativo")

    with pytest.raises(PlanificadorError):
        raise ReferenciaError("A999 no existe")

    with pytest.raises(PlanificadorError):
        raise CicloDependenciaError(["A001", "A002", "A001"])
