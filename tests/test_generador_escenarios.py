"""RF-08: tamaños, datos válidos, dependencias y reproducibilidad."""

from copy import deepcopy
from datetime import datetime
import os
import random
import subprocess
import sys

import pytest

from planificador.dominio import EstadoActividad, Prioridad, TipoRecurso, ValidacionError
from planificador.escenarios import ConfiguracionEscenario, generar_escenario


@pytest.mark.parametrize("tamano,actividades,recursos", [
    ("pequeno", 20, 5), ("mediano", 100, 20), ("grande", 500, 50),
])
def test_tamanos_y_datos_del_dominio(tamano, actividades, recursos):
    generado = generar_escenario(ConfiguracionEscenario(tamano=tamano))
    escenario = generado.escenario
    assert len(escenario.actividades) == actividades
    assert len(escenario.recursos) == recursos
    assert set(r.tipo for r in escenario.recursos.values()) == set(TipoRecurso)
    assert set(a.prioridad for a in escenario.actividades.values()) == set(Prioridad)
    for recurso in escenario.recursos.values():
        assert recurso.id in escenario.recursos
        assert recurso.capacidad >= 1
        assert recurso.costo_hora >= 0
        assert recurso.habilidades
        assert len(recurso.disponibilidad) == generado.configuracion.dias
        for ventana in recurso.disponibilidad:
            assert generado.horizonte.contiene(ventana)
    for actividad in escenario.actividades.values():
        assert actividad.estado == EstadoActividad.PENDIENTE
        assert actividad.duracion_horas > 0
        assert actividad.cantidad_recursos >= 1
        assert generado.horizonte.inicio <= actividad.inicio_permitido < actividad.fecha_limite
        assert actividad.fecha_limite <= generado.horizonte.fin
        assert actividad.dependencias <= escenario.actividades.keys()
        assert all(int(dep[1:]) < int(actividad.id[1:]) for dep in actividad.dependencias)
    escenario.verificar_sin_ciclos()
    assert any(a.dependencias for a in escenario.actividades.values())


@pytest.mark.parametrize("tamano", ["pequeno", "mediano", "grande"])
def test_misma_configuracion_repite_todos_los_datos(tamano):
    configuracion = ConfiguracionEscenario(tamano=tamano)
    assert generar_escenario(configuracion) == generar_escenario(configuracion)


def test_otra_semilla_cambia_datos_sin_cambiar_cantidades():
    a = generar_escenario(ConfiguracionEscenario(semilla=2026))
    b = generar_escenario(ConfiguracionEscenario(semilla=2027))
    assert a.escenario != b.escenario
    assert len(a.escenario.actividades) == len(b.escenario.actividades)
    assert len(a.escenario.recursos) == len(b.escenario.recursos)


def test_generaciones_no_comparten_entidades_mutables():
    a, b = generar_escenario(), generar_escenario()
    original_b = deepcopy(b)
    a.escenario.recursos["R001"].desactivar()
    a.escenario.actividades["A001"].descripcion = "Editada"
    assert b == original_b


def test_generar_no_cambia_el_generador_aleatorio_global():
    estado = random.getstate()
    generar_escenario()
    assert random.getstate() == estado


def test_hay_compatibles_y_tareas_sin_habilidad_disponible():
    escenario = generar_escenario().escenario
    compatibles, incompatibles = 0, 0
    for actividad in escenario.actividades.values():
        candidatos = [r for r in escenario.recursos.values()
                      if r.esta_activo and r.tiene_habilidades(actividad.habilidades_requeridas)]
        if candidatos:
            compatibles += 1
            assert len(candidatos) >= actividad.cantidad_recursos
        else:
            incompatibles += 1
    assert (compatibles, incompatibles) == (18, 2)


def test_resumen_es_independiente_y_contiene_configuracion():
    generado = generar_escenario()
    anterior = deepcopy(generado)
    resumen = generado.resumen()
    assert resumen["semilla"] == 2026
    assert resumen["version_generador"] == "1"
    assert sum(resumen["actividades_por_prioridad"].values()) == 20
    assert sum(resumen["recursos_por_tipo"].values()) == 5
    assert 0 < resumen["recursos_activos"] < 5
    resumen["actividades_por_prioridad"].clear()
    assert generado == anterior
    assert len(generado.resumen()["actividades_por_prioridad"]) == 4


@pytest.mark.parametrize("campos", [
    {"tamano": "gigante"}, {"tamano": None}, {"semilla": True},
    {"semilla": 1.5}, {"dias": 0}, {"dias": True}, {"dias": 2.5},
    {"fecha_inicio": "2026-11-02"}, {"fecha_inicio": datetime(2026, 11, 2, 9)},
])
def test_configuracion_invalida_se_rechaza(campos):
    with pytest.raises(ValidacionError):
        ConfiguracionEscenario(**campos)


def test_rechaza_objeto_de_configuracion_incorrecto():
    with pytest.raises(ValidacionError):
        generar_escenario("pequeno")


def test_se_puede_cambiar_fecha_y_horizonte():
    configuracion = ConfiguracionEscenario(fecha_inicio=datetime(2027, 1, 4, 8), dias=1)
    generado = generar_escenario(configuracion)
    assert generado.horizonte.inicio == datetime(2027, 1, 4, 8)
    assert generado.horizonte.fin == datetime(2027, 1, 4, 17)
    assert all(len(r.disponibilidad) == 1 for r in generado.escenario.recursos.values())


def test_datos_no_dependen_del_orden_aleatorio_de_sets_entre_procesos():
    codigo = '''
import json
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from planificador.escenarios import generar_escenario
def convertir(valor):
    if isinstance(valor, (set, frozenset)): return sorted(valor)
    if isinstance(valor, datetime): return valor.isoformat()
    if isinstance(valor, Enum): return valor.value
    raise TypeError(type(valor).__name__)
print(json.dumps(asdict(generar_escenario()), default=convertir, sort_keys=True))
'''
    salidas = [subprocess.check_output(
        [sys.executable, "-c", codigo],
        env={**os.environ, "PYTHONHASHSEED": semilla}, text=True,
    ) for semilla in ("1", "2")]
    assert salidas[0] == salidas[1]


def test_demostracion_desde_consola():
    resultado = subprocess.run(
        [sys.executable, "-m", "planificador.escenarios", "--tamano", "mediano"],
        capture_output=True, text=True, check=True,
    )
    import json
    resumen = json.loads(resultado.stdout)
    assert resumen["actividades"] == 100
    assert resumen["recursos"] == 20


def test_consola_informa_errores_sin_exito_falso():
    resultado = subprocess.run(
        [sys.executable, "-m", "planificador.escenarios", "--dias", "0"],
        capture_output=True, text=True,
    )
    assert resultado.returncode != 0
    assert "dias" in resultado.stderr
    assert not resultado.stdout
