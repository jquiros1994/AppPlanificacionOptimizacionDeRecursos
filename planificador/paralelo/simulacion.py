"""Evaluador de muestra independiente de los algoritmos greedy y genético."""

from datetime import timedelta
from random import Random

from planificador.dominio import Asignacion, Escenario, Intervalo, Planificacion
from planificador.funcional import calcular_costo_total, tareas_retrasadas
from planificador.reglas.motor_reglas import MotorReglas


def evaluar_muestra(escenario: Escenario, semilla: int) -> dict[str, object]:
    """Construye una muestra aleatoria y evalúa sus restricciones y métricas.

    Puede tener conflictos: se registran sin presentar la muestra como solución
    factible. Sirve para medir la misma carga de CPU en ambas modalidades.
    """
    azar = Random(semilla)
    asignaciones = []
    for actividad in sorted(escenario.actividades.values(), key=lambda a: a.id):
        candidatos = sorted((r for r in escenario.recursos.values()
                             if r.esta_activo and r.tiene_habilidades(actividad.habilidades_requeridas)),
                            key=lambda r: r.id)
        azar.shuffle(candidatos)
        for referencia in candidatos:
            colocado = False
            for ventana in referencia.disponibilidad:
                inicio = max(actividad.inicio_permitido, ventana.inicio)
                fin = inicio + timedelta(hours=actividad.duracion_horas)
                if fin > ventana.fin:
                    continue
                margen = int((ventana.fin - fin).total_seconds() // 3600)
                inicio += timedelta(hours=azar.randint(0, margen))
                intervalo = Intervalo(inicio, inicio + timedelta(hours=actividad.duracion_horas))
                compatibles = [r for r in candidatos if r.esta_disponible(intervalo)]
                if len(compatibles) < actividad.cantidad_recursos:
                    continue
                elegidos = azar.sample(compatibles, actividad.cantidad_recursos)
                asignaciones.append(Asignacion(
                    actividad.id, frozenset(r.id for r in elegidos), intervalo,
                ))
                colocado = True
                break
            if colocado:
                break
    plan = Planificacion(tuple(asignaciones), "muestra_aleatoria", semilla)
    incidencias = MotorReglas().evaluar(plan, escenario)
    reglas = sorted({incidencia.regla for incidencia in incidencias})
    return {
        "asignadas": len(asignaciones),
        "pendientes": len(escenario.actividades) - len(asignaciones),
        "costo": calcular_costo_total(plan, escenario),
        "retraso_horas": sum(tareas_retrasadas(plan, escenario).values()),
        "factible_segun_motor": not incidencias,
        "incidencias_por_regla": {
            regla: sum(i.regla == regla for i in incidencias) for regla in reglas
        },
        "asignaciones": tuple((
            a.actividad_id, tuple(sorted(a.recursos_ids)),
            a.intervalo.inicio.isoformat(), a.intervalo.fin.isoformat(),
        ) for a in asignaciones),
    }
