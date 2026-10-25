import ast
import inspect
from datetime import datetime

from planificador.dominio import (
    Asignacion,
    EstadoRecurso,
    Intervalo,
    Planificacion,
    Recurso,
    TipoRecurso,
)
from planificador.dominio import planificacion as modulo_planificacion


def _hora(hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 1, 1, hora, minuto)


def _recurso(id_: str, costo_hora: float) -> Recurso:
    return Recurso(
        id=id_,
        nombre=f"Recurso {id_}",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=costo_hora,
        habilidades=frozenset({"instalacion"}),
        disponibilidad=(Intervalo(_hora(8), _hora(17)),),
        estado=EstadoRecurso.ACTIVO,
    )


def test_calcular_costo_suma_costo_hora_por_duracion_de_cada_recurso():
    asignacion = Asignacion(
        actividad_id="A001",
        recursos_ids=frozenset({"R001", "R002"}),
        intervalo=Intervalo(_hora(8), _hora(12)),
    )
    recursos = {
        "R001": _recurso("R001", costo_hora=1000),
        "R002": _recurso("R002", costo_hora=2000),
    }

    # 4 horas * (1000 + 2000) = 12000
    assert asignacion.calcular_costo(recursos) == 12000


def test_planificacion_consulta_por_actividad():
    asignacion_a001 = Asignacion("A001", frozenset({"R001"}), Intervalo(_hora(8), _hora(12)))
    asignacion_a002 = Asignacion("A002", frozenset({"R002"}), Intervalo(_hora(9), _hora(11)))
    planificacion = Planificacion(
        asignaciones=(asignacion_a001, asignacion_a002),
        algoritmo="greedy",
        semilla=2026,
    )

    assert planificacion.asignaciones_de_actividad("A001") == (asignacion_a001,)
    assert planificacion.asignaciones_de_actividad("A999") == ()


def test_planificacion_consulta_por_recurso():
    asignacion_a001 = Asignacion(
        "A001", frozenset({"R001", "R002"}), Intervalo(_hora(8), _hora(12))
    )
    asignacion_a002 = Asignacion("A002", frozenset({"R002"}), Intervalo(_hora(9), _hora(11)))
    planificacion = Planificacion(
        asignaciones=(asignacion_a001, asignacion_a002), algoritmo="greedy"
    )

    assert planificacion.asignaciones_de_recurso("R001") == (asignacion_a001,)
    assert planificacion.asignaciones_de_recurso("R002") == (
        asignacion_a001,
        asignacion_a002,
    )


def test_planificacion_no_importa_nada_de_reglas():
    codigo_fuente = inspect.getsource(modulo_planificacion)
    arbol = ast.parse(codigo_fuente)

    modulos_importados = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos_importados.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos_importados.append(nodo.module)

    assert not any("reglas" in modulo for modulo in modulos_importados)
