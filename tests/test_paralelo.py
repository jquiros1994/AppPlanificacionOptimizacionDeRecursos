from copy import deepcopy
import json
import subprocess
import sys

import pytest

from planificador.dominio import ValidacionError
from planificador.escenarios import generar_escenario
from planificador.paralelo import (
    ComparacionEjecuciones, ConfiguracionParalela, ResultadoModalidad,
    comparar_ejecuciones, ejecutar_secuencial, preparar_trabajos,
)
from planificador.paralelo.simulacion import evaluar_muestra


def evaluar_carga(escenario, semilla):
    return {"recursos": len(escenario.recursos), "valor": sum((semilla + i) % 97 for i in range(5000))}


def evaluar_con_error(escenario, semilla):
    raise ValueError("evaluacion rechazada")


def evaluar_con_mutacion(escenario, semilla):
    cantidad = len(escenario.recursos)
    escenario.recursos.clear()
    return cantidad


def test_trabajos_se_reproducen_sin_compartir_semilla_de_todos():
    configuracion = ConfiguracionParalela(evaluaciones=4)
    trabajos = preparar_trabajos(configuracion)
    assert trabajos == preparar_trabajos(configuracion)
    assert len({t.semilla for t in trabajos}) == 4
    assert [t.indice for t in trabajos] == list(range(4))


@pytest.mark.parametrize("procesos", [1, 2])
def test_procesos_calculan_exactamente_los_mismos_resultados(procesos):
    escenario = generar_escenario().escenario
    original = deepcopy(escenario)
    configuracion = ConfiguracionParalela(evaluaciones=3, procesos=procesos)
    comparacion = comparar_ejecuciones(escenario, configuracion, evaluar_carga)
    assert comparacion.equivalentes
    assert comparacion.secuencial.fallos == comparacion.paralelo.fallos == 0
    assert comparacion.aceleracion > 0
    assert escenario == original


def test_cada_evaluacion_tiene_datos_independientes():
    escenario = generar_escenario().escenario
    comparacion = comparar_ejecuciones(escenario, ConfiguracionParalela(3, 2), evaluar_con_mutacion)
    assert comparacion.equivalentes
    assert [r.valor for r in comparacion.secuencial.resultados] == [5, 5, 5]
    assert len(escenario.recursos) == 5


def test_errores_se_registran_en_ambas_modalidades_y_no_se_afirman_mejoras():
    comparacion = comparar_ejecuciones(
        generar_escenario().escenario, ConfiguracionParalela(2, 2), evaluar_con_error,
    )
    assert comparacion.secuencial.fallos == comparacion.paralelo.fallos == 2
    assert comparacion.aceleracion is None
    assert all("ValueError" in r.error for r in comparacion.paralelo.resultados)
    assert "no válida" in comparacion.resumen()["observacion"]


def test_evaluador_no_serializable_informa_fallo():
    comparacion = comparar_ejecuciones(
        generar_escenario().escenario, ConfiguracionParalela(1, 1), lambda escenario, semilla: 1,
    )
    assert comparacion.secuencial.fallos == 0
    assert comparacion.paralelo.fallos == 1
    assert not comparacion.equivalentes
    assert comparacion.aceleracion is None


def test_simulacion_repite_plan_y_metricas_sin_modificar_entrada():
    escenario = generar_escenario().escenario
    original = deepcopy(escenario)
    resultado = evaluar_muestra(escenario, 2026)
    assert resultado == evaluar_muestra(escenario, 2026)
    assert escenario == original
    assert resultado["asignadas"] + resultado["pendientes"] == 20
    assert resultado["costo"] >= 0
    assert resultado["factible_segun_motor"] == (not resultado["incidencias_por_regla"])


@pytest.mark.parametrize("campos", [
    {"procesos": 0}, {"procesos": True}, {"evaluaciones": 0},
    {"evaluaciones": 1.5}, {"semilla": True},
])
def test_parametros_invalidos(campos):
    with pytest.raises(ValidacionError):
        ConfiguracionParalela(**campos)


def test_formula_e_interpretacion_sin_depender_de_velocidad_del_equipo():
    configuracion = ConfiguracionParalela()
    for tiempo, factor in ((5, 1.6), (10, 0.8)):
        comparacion = ComparacionEjecuciones(configuracion,
            ResultadoModalidad("secuencial", 8, ()), ResultadoModalidad("paralelo", tiempo, ()))
        assert comparacion.aceleracion == factor
        if factor < 1:
            assert "más lento" in comparacion.resumen()["observacion"]


def test_orden_no_cambia_con_la_ejecucion_secuencial():
    trabajos = preparar_trabajos(ConfiguracionParalela(3, 1))
    resultados = ejecutar_secuencial(generar_escenario().escenario, trabajos, evaluar_carga)
    assert tuple(r.trabajo for r in resultados.resultados) == trabajos


def test_consola_con_procesos_y_resultados_detallados():
    resultado = subprocess.run([sys.executable, "-m", "planificador.paralelo",
        "--evaluaciones", "2", "--procesos", "2", "--detalle"],
        capture_output=True, text=True, check=True)
    salida = json.loads(resultado.stdout)
    assert salida["comparacion"]["equivalentes"]
    assert salida["comparacion"]["fallos_paralelo"] == 0
    assert len(salida["paralelo"]["resultados"]) == 2
