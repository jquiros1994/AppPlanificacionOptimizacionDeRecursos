"""Validación de entidades y edición del escenario (RF-01, RF-02, carga de RF-08)."""

import math
from datetime import datetime, timezone

import pytest

from planificador.dominio import (
    Actividad, CicloDependenciaError, Escenario, EstadoActividad, EstadoRecurso,
    Intervalo, Prioridad, Recurso, ReferenciaError, TipoRecurso, ValidacionError,
)
from planificador.dominio import validaciones as v


def _hora(hora: int) -> datetime:
    return datetime(2026, 1, 1, hora)


def _recurso(**cambios) -> Recurso:
    valores = dict(
        id="R001", nombre="Técnico", tipo=TipoRecurso.HUMANO, capacidad=1, costo_hora=5000,
        habilidades=frozenset({"instalacion"}), disponibilidad=(Intervalo(_hora(8), _hora(12)),),
    )
    valores.update(cambios)
    return Recurso(**valores)


def _actividad(id_="A001", dependencias=frozenset(), **cambios) -> Actividad:
    valores = dict(
        id=id_, descripcion=f"Actividad {id_}", duracion_horas=2, prioridad=Prioridad.ALTA,
        inicio_permitido=_hora(8), fecha_limite=_hora(17),
        habilidades_requeridas=frozenset({"instalacion"}), cantidad_recursos=1,
        dependencias=dependencias,
    )
    valores.update(cambios)
    return Actividad(**valores)


# --- Validadores -----------------------------------------------------------

def test_validadores_normalizan_y_rechazan():
    assert v.texto("id", " R1 ") == "R1"
    assert v.real_finito("costo", 3) == 3.0
    assert v.enumerado(Prioridad, "prioridad", "Critica") is Prioridad.CRITICA
    assert v.enumerado(TipoRecurso, "tipo", "unidad_operativa") is TipoRecurso.UNIDAD_OPERATIVA
    assert v.conjunto_textos("h", ["a", "b", "a"]) == frozenset({"a", "b"})
    with pytest.raises(ValidacionError, match="mayor que 0"):
        v.real_finito("d", 0, estricto=True)
    with pytest.raises(ValidacionError, match="no puede estar vacío"):
        v.conjunto_textos("h", [], vacio=False)


# --- Recurso (RF-01) -------------------------------------------------------

@pytest.mark.parametrize("campo, valor", [
    ("id", ""), ("id", "   "), ("id", None), ("nombre", ""),
    ("tipo", "nave"), ("tipo", 3), ("estado", "dormido"),
    ("capacidad", True), ("capacidad", 0), ("capacidad", "2"),
    ("costo_hora", math.nan), ("costo_hora", math.inf), ("costo_hora", True),
    ("costo_hora", "500"), ("costo_hora", -1),
    ("habilidades", "instalacion"), ("habilidades", {""}), ("habilidades", None),
    ("habilidades", frozenset()),
    ("disponibilidad", "08-12"), ("disponibilidad", (("08", "12"),)),
])
def test_recurso_rechaza_valores_invalidos_indicando_el_campo(campo, valor):
    with pytest.raises(ValidacionError) as error:
        _recurso(**{campo: valor})
    assert error.value.campo == campo


def test_recurso_normaliza_textos_enums_y_colecciones():
    recurso = _recurso(id=" R005 ", tipo="equipo", estado="INACTIVO",
                       habilidades=["soldadura", "instalacion"], costo_hora=0,
                       disponibilidad=[Intervalo(_hora(8), _hora(9))])
    assert recurso.id == "R005"
    assert recurso.tipo is TipoRecurso.EQUIPO
    assert recurso.estado is EstadoRecurso.INACTIVO
    assert recurso.habilidades == frozenset({"soldadura", "instalacion"})
    assert recurso.costo_hora == 0.0
    assert isinstance(recurso.disponibilidad, tuple)


def test_asignar_un_atributo_invalido_en_recurso_se_rechaza_y_conserva_el_valor():
    recurso = _recurso()
    with pytest.raises(ValidacionError):
        recurso.capacidad = 0
    with pytest.raises(ValidacionError):
        recurso.costo_hora = -1
    assert (recurso.capacidad, recurso.costo_hora) == (1, 5000)
    recurso.desactivar()
    assert not recurso.esta_activo


def test_intervalo_rechaza_fechas_con_zona_horaria_o_de_otro_tipo():
    with pytest.raises(ValidacionError):
        Intervalo(_hora(8).replace(tzinfo=timezone.utc), _hora(9).replace(tzinfo=timezone.utc))
    with pytest.raises(ValidacionError):
        Intervalo("08:00", "09:00")


# --- Actividad (RF-02) -----------------------------------------------------

@pytest.mark.parametrize("campo, valor", [
    ("id", ""), ("descripcion", "  "),
    ("prioridad", 99), ("prioridad", 0), ("prioridad", "urgente"), ("prioridad", True),
    ("estado", "terminada"),
    ("duracion_horas", math.nan), ("duracion_horas", math.inf), ("duracion_horas", 1e-11),
    ("duracion_horas", True), ("duracion_horas", 0), ("duracion_horas", -3),
    ("cantidad_recursos", True), ("cantidad_recursos", 2.0), ("cantidad_recursos", 0),
    ("habilidades_requeridas", "instalacion"), ("dependencias", "A002"),
    ("inicio_permitido", "2026-01-01 08:00"),
    ("fecha_limite", _hora(17).replace(tzinfo=timezone.utc)),
])
def test_actividad_rechaza_valores_invalidos_indicando_el_campo(campo, valor):
    with pytest.raises(ValidacionError) as error:
        _actividad(**{campo: valor})
    assert error.value.campo == campo


def test_actividad_acepta_prioridad_y_estado_como_texto_o_numero():
    actividad = _actividad(prioridad="critica", estado="asignada", dependencias=["A002"])
    assert actividad.prioridad is Prioridad.CRITICA
    assert actividad.estado is EstadoActividad.ASIGNADA
    assert actividad.dependencias == frozenset({"A002"})
    assert _actividad(prioridad=2).prioridad is Prioridad.MEDIA


def test_asignar_atributos_inconsistentes_en_actividad_se_rechaza_y_conserva_el_valor():
    actividad = _actividad()
    with pytest.raises(ValidacionError):
        actividad.fecha_limite = _hora(7)
    with pytest.raises(ValidacionError):
        actividad.dependencias = frozenset({"A001"})
    assert actividad.fecha_limite == _hora(17)
    assert actividad.dependencias == frozenset()


# --- Escenario: edición y carga -------------------------------------------

def _con_a002_a004_a005() -> Escenario:
    escenario = Escenario()
    escenario.agregar_actividad(_actividad("A002"))
    escenario.agregar_actividad(_actividad("A004"))
    escenario.agregar_actividad(_actividad("A005", frozenset({"A002", "A004"})))
    return escenario


def test_id_duplicado_se_informa_con_ese_mensaje():
    escenario = Escenario()
    escenario.agregar_recurso(_recurso())
    with pytest.raises(ReferenciaError, match="ID duplicado"):
        escenario.agregar_recurso(_recurso())
    escenario.agregar_actividad(_actividad())
    with pytest.raises(ReferenciaError, match="ID duplicado"):
        escenario.agregar_actividad(_actividad())


def test_rf02_editar_que_forma_un_ciclo_se_rechaza_con_la_cadena_sin_cambiar_nada():
    escenario = _con_a002_a004_a005()
    original = escenario.actividades["A002"]

    with pytest.raises(CicloDependenciaError) as info:
        escenario.editar_actividad("A002", dependencias=frozenset({"A005"}))

    assert info.value.cadena == ["A002", "A005", "A002"]
    assert "A002 → A005 → A002" in str(info.value)
    assert escenario.actividades["A002"] is original
    assert original.dependencias == frozenset()


def test_editar_actividad_valida_aplica_el_cambio():
    escenario = _con_a002_a004_a005()
    editada = escenario.editar_actividad("A005", duracion_horas=3, dependencias=frozenset({"A002"}))
    assert escenario.actividades["A005"] is editada
    assert (editada.duracion_horas, editada.dependencias) == (3.0, frozenset({"A002"}))


@pytest.mark.parametrize("cambios, error", [
    ({"dependencias": frozenset({"A999"})}, ReferenciaError),
    ({"duracion_horas": 0}, ValidacionError),
    ({"prioridad": 99}, ValidacionError),
    ({"id": "A777"}, ValidacionError),
    ({"color": "rojo"}, ValidacionError),
])
def test_editar_actividad_invalida_no_cambia_el_escenario(cambios, error):
    escenario = _con_a002_a004_a005()
    antes = dict(escenario.actividades)
    with pytest.raises(error):
        escenario.editar_actividad("A005", **cambios)
    assert escenario.actividades == antes
    assert all(escenario.actividades[k] is antes[k] for k in antes)


def test_editar_recurso_valida_y_conserva_el_id():
    escenario = Escenario()
    escenario.agregar_recurso(_recurso())
    editado = escenario.editar_recurso("R001", costo_hora=2500, nombre="Técnica")
    assert (editado.id, editado.costo_hora, editado.nombre) == ("R001", 2500.0, "Técnica")
    with pytest.raises(ValidacionError):
        escenario.editar_recurso("R001", capacidad=0)
    with pytest.raises(ReferenciaError):
        escenario.editar_recurso("R999", nombre="x")
    assert escenario.recursos["R001"] is editado


def test_desde_entidades_acepta_actividades_en_cualquier_orden():
    escenario = Escenario.desde_entidades(
        [_recurso()],
        [_actividad("A005", frozenset({"A002", "A004"})), _actividad("A004"), _actividad("A002")],
    )
    assert set(escenario.actividades) == {"A002", "A004", "A005"}


@pytest.mark.parametrize("actividades, error", [
    ([_actividad("A001"), _actividad("A001")], ReferenciaError),
    ([_actividad("A002", frozenset({"A999"}))], ReferenciaError),
    ([_actividad("A001", frozenset({"A002"})), _actividad("A002", frozenset({"A001"}))],
     CicloDependenciaError),
])
def test_desde_entidades_rechaza_datos_inconsistentes(actividades, error):
    with pytest.raises(error):
        Escenario.desde_entidades([], actividades)


def test_cadena_larga_de_dependencias_no_agota_la_recursion():
    cantidad = 3000
    actividades = [
        _actividad(f"A{i:04d}", frozenset({f"A{i + 1:04d}"}) if i < cantidad - 1 else frozenset())
        for i in range(cantidad)
    ]
    escenario = Escenario.desde_entidades([], actividades)
    escenario.verificar_sin_ciclos()
    assert len(escenario.actividades) == cantidad


def test_constructor_rechaza_claves_que_no_coinciden_con_el_id():
    with pytest.raises(ReferenciaError):
        Escenario(recursos={"R002": _recurso()})


def test_obtener_inexistente_lanza_referencia_error():
    with pytest.raises(ReferenciaError):
        Escenario().obtener_actividad("A001")
    with pytest.raises(ReferenciaError):
        Escenario().obtener_recurso("R001")
