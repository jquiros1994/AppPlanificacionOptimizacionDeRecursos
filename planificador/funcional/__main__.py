import json

from planificador.dominio import Asignacion, Intervalo, Planificacion
from planificador.escenarios import generar_escenario
from planificador.funcional import calcular_costo_total, comparar_operaciones
from datetime import timedelta


def main() -> None:
    generado = generar_escenario()
    escenario = generado.escenario
    recurso = escenario.recursos["R001"]
    actividad = escenario.actividades["A001"]
    ventana = recurso.disponibilidad[0]
    # Esta asignación es una entrada de análisis; no representa un plan validado.
    asignacion = Asignacion(actividad.id, frozenset({recurso.id}), Intervalo(
        ventana.inicio, ventana.inicio + timedelta(hours=actividad.duracion_horas),
    ))
    plan = Planificacion((asignacion,), "demostracion", generado.configuracion.semilla)
    print(json.dumps({
        "equivalencias": comparar_operaciones(plan, escenario),
        "costo_total": calcular_costo_total(plan, escenario),
        "nota": "Entrada de análisis parcial; no es una planificación validada.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
