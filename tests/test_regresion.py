"""Regresión de las cifras registradas en Resultados.xlsx.

Si una corrección cambia estos valores, debe ser intencional y quedar documentada.
"""

import pytest

from planificador.algoritmos import AlgoritmoGenetico, ConfiguracionGenetica
from planificador.escenarios import ConfiguracionEscenario, generar_escenario
from planificador.reglas.motor_reglas import MotorReglas

CASOS = [
    pytest.param(
        "pequeno", {},
        (71_000.0, 94.25, 18), (71_000.0, 73.25, 18), {"A010", "A020"},
        id="pequeno-por-defecto",
    ),
    pytest.param(
        "mediano", {"poblacion": 40, "generaciones": 80, "semilla": 2026},
        (444_250.0, 550.75, 83), (434_750.0, 525.75, 83), None,
        id="mediano-40x80", marks=pytest.mark.lento,
    ),
]


@pytest.mark.parametrize("tamano, parametros, base, genetico, pendientes", CASOS)
def test_cifras_del_excel_se_mantienen(tamano, parametros, base, genetico, pendientes):
    generado = generar_escenario(ConfiguracionEscenario(tamano=tamano, semilla=2026))
    configuracion = ConfiguracionGenetica(**parametros)
    resultado = AlgoritmoGenetico(generado.escenario, configuracion, generado.horizonte).ejecutar()

    motor = MotorReglas(generado.horizonte)
    for ejecucion, esperado in ((resultado.base, base), (resultado, genetico)):
        aptitud = ejecucion.aptitud
        assert (aptitud.costo, aptitud.horas_retraso, aptitud.asignadas) == esperado
        # Veredicto único: algoritmo, evaluador y motor coinciden (T1.10).
        validacion = motor.validar(ejecucion.planificacion, generado.escenario)
        assert aptitud.factible and validacion.factible
        assert set(validacion.actividades_pendientes) == set(ejecucion.pendientes)
        assert validacion.horas_retraso == aptitud.horas_retraso
        if pendientes is not None:
            assert set(ejecucion.pendientes) == pendientes
