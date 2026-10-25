from datetime import datetime

import pytest

from planificador.dominio import (
    Actividad,
    CicloDependenciaError,
    Escenario,
    EstadoActividad,
    Intervalo,
    Prioridad,
    Recurso,
    ReferenciaError,
    TipoRecurso,
    ValidacionError,
)


def _hora(hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 1, 1, hora, minuto)


def _recurso(id_: str = "R001") -> Recurso:
    return Recurso(
        id=id_,
        nombre=f"Recurso {id_}",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=1000,
        habilidades=frozenset({"instalacion"}),
        disponibilidad=(Intervalo(_hora(8), _hora(17)),),
    )


def _actividad(id_: str, dependencias: frozenset[str] = frozenset()) -> Actividad:
    return Actividad(
        id=id_,
        descripcion=f"Actividad {id_}",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=_hora(8),
        fecha_limite=_hora(17),
        habilidades_requeridas=frozenset({"instalacion"}),
        cantidad_recursos=1,
        dependencias=dependencias,
    )


def test_agregar_recurso_duplicado_lanza_referencia_error():
    escenario = Escenario()
    escenario.agregar_recurso(_recurso("R001"))

    with pytest.raises(ReferenciaError):
        escenario.agregar_recurso(_recurso("R001"))


def test_agregar_actividad_duplicada_lanza_referencia_error():
    escenario = Escenario()
    escenario.agregar_actividad(_actividad("A001"))

    with pytest.raises(ReferenciaError):
        escenario.agregar_actividad(_actividad("A001"))


def test_agregar_actividad_con_dependencia_inexistente_lanza_referencia_error():
    escenario = Escenario()

    with pytest.raises(ReferenciaError):
        escenario.agregar_actividad(_actividad("A005", dependencias=frozenset({"A002"})))


def test_agregar_actividad_con_dependencias_existentes_funciona():
    escenario = Escenario()
    escenario.agregar_actividad(_actividad("A002"))
    escenario.agregar_actividad(_actividad("A004"))
    escenario.agregar_actividad(_actividad("A005", dependencias=frozenset({"A002", "A004"})))

    assert set(escenario.actividades) == {"A002", "A004", "A005"}


def test_eliminar_actividad_inexistente_lanza_referencia_error():
    escenario = Escenario()

    with pytest.raises(ReferenciaError):
        escenario.eliminar_actividad("A999")


def test_eliminar_actividad_de_la_que_otras_dependen_lanza_referencia_error():
    escenario = Escenario()
    escenario.agregar_actividad(_actividad("A002"))
    escenario.agregar_actividad(_actividad("A005", dependencias=frozenset({"A002"})))

    with pytest.raises(ReferenciaError):
        escenario.eliminar_actividad("A002")


def test_eliminar_actividad_no_pendiente_lanza_validacion_error():
    escenario = Escenario()
    actividad = _actividad("A001")
    actividad.estado = EstadoActividad.COMPLETADA
    escenario.agregar_actividad(actividad)

    with pytest.raises(ValidacionError):
        escenario.eliminar_actividad("A001")


def test_eliminar_actividad_pendiente_sin_dependientes_funciona():
    escenario = Escenario()
    escenario.agregar_actividad(_actividad("A001"))

    escenario.eliminar_actividad("A001")

    assert "A001" not in escenario.actividades


def test_desactivar_recurso_inexistente_lanza_referencia_error():
    escenario = Escenario()

    with pytest.raises(ReferenciaError):
        escenario.desactivar_recurso("R999")


def test_desactivar_recurso_cambia_su_estado():
    escenario = Escenario()
    escenario.agregar_recurso(_recurso("R001"))

    escenario.desactivar_recurso("R001")

    assert not escenario.recursos["R001"].esta_activo


def test_ciclo_a002_a005_a002_se_detecta_y_muestra_la_cadena_completa():
    # A005 depende de A002 y A004 (ejemplo oficial del enunciado).
    escenario = Escenario()
    escenario.agregar_actividad(_actividad("A002"))
    escenario.agregar_actividad(_actividad("A004"))
    escenario.agregar_actividad(_actividad("A005", dependencias=frozenset({"A002", "A004"})))

    # Simula el intento de editar A002 para que dependa de A005: se forma un ciclo.
    escenario.actividades["A002"].dependencias = frozenset({"A005"})

    with pytest.raises(CicloDependenciaError) as info:
        escenario.verificar_sin_ciclos()

    cadena = info.value.cadena
    assert cadena[0] == cadena[-1]
    assert set(cadena) == {"A002", "A005"}
    assert " → ".join(cadena) in str(info.value)
