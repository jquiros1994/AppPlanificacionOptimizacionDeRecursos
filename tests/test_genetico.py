from datetime import datetime
from random import Random

import pytest

from planificador.algoritmos import (
    AlgoritmoBase, AlgoritmoGenetico, ConfiguracionGenetica, Cromosoma,
    Decodificador, EvaluadorAptitud, Gen, OperadoresGeneticos, evaluar_genetico,
)
from planificador.dominio import (
    Actividad, Escenario, Intervalo, Planificacion, Prioridad, Recurso,
    TipoRecurso, ValidacionError,
)
from planificador.escenarios import ConfiguracionEscenario, generar_escenario
from planificador.reglas.motor_reglas import MotorReglas


def _hora(hora, minuto=0):
    return datetime(2026, 11, 2, hora, minuto)


def _recurso(rid, costo, capacidad=1, habilidades=("tecnico",), inicio=8, fin=12):
    return Recurso(
        id=rid, nombre=rid, tipo=TipoRecurso.HUMANO, capacidad=capacidad,
        costo_hora=costo, habilidades=frozenset(habilidades),
        disponibilidad=(Intervalo(_hora(inicio), _hora(fin)),),
    )


def _actividad(aid, duracion=2, dependencias=(), habilidades=("tecnico",), cantidad=1,
               prioridad=Prioridad.MEDIA, limite=12):
    return Actividad(
        id=aid, descripcion=aid, duracion_horas=duracion, prioridad=prioridad,
        inicio_permitido=_hora(8), fecha_limite=_hora(limite),
        habilidades_requeridas=frozenset(habilidades), cantidad_recursos=cantidad,
        dependencias=frozenset(dependencias),
    )


def _escenario(recursos, actividades):
    escenario = Escenario()
    for recurso in recursos:
        escenario.agregar_recurso(recurso)
    for actividad in actividades:
        escenario.agregar_actividad(actividad)
    return escenario


@pytest.fixture(scope="module")
def pequeno():
    return generar_escenario(ConfiguracionEscenario(tamano="pequeno", semilla=2026))


def _configuracion(**cambios):
    valores = {"poblacion": 10, "generaciones": 8, "semilla": 7, "paciencia": None}
    valores.update(cambios)
    return ConfiguracionGenetica(**valores)


@pytest.mark.parametrize("campo, valor", [
    ("poblacion", 1), ("poblacion", 2.5), ("generaciones", 0),
    ("prob_mutacion", -0.1), ("prob_mutacion", 1.5), ("prob_cruce", 2),
    ("prob_cruce", True), ("elitismo", 10), ("elitismo", -1), ("semilla", "x"),
    ("paciencia", 0), ("tamano_torneo", 1), ("tamano_torneo", 11),
])
def test_configuracion_rechaza_valores_fuera_de_rango(campo, valor):
    with pytest.raises(ValidacionError) as error:
        _configuracion(**{campo: valor})
    assert error.value.campo == campo


def test_configuracion_acepta_limites():
    configuracion = _configuracion(prob_mutacion=0, prob_cruce=1, elitismo=9, tamano_torneo=10)
    assert configuracion.elitismo == 9


def test_decodificador_usa_el_primer_horario_y_el_recurso_mas_barato():
    escenario = _escenario([_recurso("R1", 100), _recurso("R2", 50)], [_actividad("A1")])
    resultado = Decodificador(escenario).decodificar([("A1", 0)])
    asignacion = resultado.asignaciones[0]
    assert asignacion.recursos_ids == {"R2"}
    assert asignacion.intervalo == Intervalo(_hora(8), _hora(10))
    assert resultado.pendientes == {}


def test_decodificador_preferencia_elige_otro_recurso():
    escenario = _escenario([_recurso("R1", 100), _recurso("R2", 50)], [_actividad("A1")])
    resultado = Decodificador(escenario).decodificar([("A1", 1)])
    assert resultado.asignaciones[0].recursos_ids == {"R1"}


def test_decodificador_reprograma_si_el_recurso_esta_ocupado():
    escenario = _escenario([_recurso("R1", 100)], [_actividad("A1"), _actividad("A2")])
    resultado = Decodificador(escenario).decodificar([("A2", 0), ("A1", 0)])
    intervalos = {a.actividad_id: a.intervalo for a in resultado.asignaciones}
    assert intervalos["A2"] == Intervalo(_hora(8), _hora(10))
    assert intervalos["A1"] == Intervalo(_hora(10), _hora(12))


def test_decodificador_respeta_capacidad_mayor_a_uno():
    escenario = _escenario([_recurso("R1", 100, capacidad=2)],
                           [_actividad("A1"), _actividad("A2"), _actividad("A3")])
    resultado = Decodificador(escenario).decodificar([("A1", 0), ("A2", 0), ("A3", 0)])
    inicios = sorted(a.intervalo.inicio for a in resultado.asignaciones)
    assert inicios == [_hora(8), _hora(8), _hora(10)]


def test_decodificador_procesa_dependencias_antes_aunque_el_orden_diga_lo_contrario():
    escenario = _escenario([_recurso("R1", 100)], [_actividad("A1"), _actividad("A2", dependencias={"A1"})])
    resultado = Decodificador(escenario).decodificar([("A2", 0), ("A1", 0)])
    intervalos = {a.actividad_id: a.intervalo for a in resultado.asignaciones}
    assert intervalos["A2"].inicio >= intervalos["A1"].fin


def test_decodificador_deja_pendiente_con_motivo_y_propaga_a_dependientes():
    escenario = _escenario(
        [_recurso("R1", 100)],
        [_actividad("A1", habilidades=("soldador",)), _actividad("A2", dependencias={"A1"})],
    )
    resultado = Decodificador(escenario).decodificar([("A1", 0), ("A2", 0)])
    assert resultado.asignaciones == ()
    assert "habilidades" in resultado.pendientes["A1"]
    assert "A1" in resultado.pendientes["A2"]


def test_decodificador_no_inventa_disponibilidad_ni_sale_del_horizonte():
    escenario = _escenario([_recurso("R1", 100)], [_actividad("A1", duracion=5)])
    assert "A1" in Decodificador(escenario).decodificar([("A1", 0)]).pendientes

    escenario = _escenario([_recurso("R1", 100)], [_actividad("A1")])
    horizonte = Intervalo(_hora(8), _hora(9))
    assert "A1" in Decodificador(escenario, horizonte).decodificar([("A1", 0)]).pendientes


def test_decodificador_rechaza_genes_incompletos_o_repetidos():
    escenario = _escenario([_recurso("R1", 100)], [_actividad("A1"), _actividad("A2")])
    decodificador = Decodificador(escenario)
    with pytest.raises(ValueError):
        decodificador.decodificar([("A1", 0)])
    with pytest.raises(ValueError):
        decodificador.decodificar([("A1", 0), ("A1", 0), ("A2", 0)])


@pytest.mark.parametrize("tamano", ["pequeno", "mediano"])
def test_decodificador_nunca_produce_conflictos_duros(tamano):
    generado = generar_escenario(ConfiguracionEscenario(tamano=tamano, semilla=2026))
    decodificador = Decodificador(generado.escenario, generado.horizonte)
    limites = {aid: decodificador.cantidad_candidatos(aid) for aid in decodificador.actividades_ids}
    azar = Random(1)
    for _ in range(5):
        resultado = decodificador.decodificar(Cromosoma.aleatorio(limites, azar).como_pares())
        incidencias = MotorReglas().evaluar(Planificacion(resultado.asignaciones, "prueba"), generado.escenario)
        assert {i.regla for i in incidencias} <= {"ACTIVIDAD_SIN_ASIGNACION"}


def test_aptitud_siempre_prefiere_asignar_a_dejar_pendiente():
    escenario = _escenario([_recurso("R1", 10_000)], [_actividad("A1", limite=9)])
    evaluador = EvaluadorAptitud(escenario)
    asignada = Planificacion(Decodificador(escenario).decodificar([("A1", 0)]).asignaciones, "x")
    vacia = Planificacion((), "x")
    assert evaluador.evaluar(asignada).valor < evaluador.evaluar(vacia).valor


def test_aptitud_distingue_conflictos_duros_de_pendientes():
    escenario = _escenario([_recurso("R1", 100)], [_actividad("A1"), _actividad("A2")])
    evaluador = EvaluadorAptitud(escenario)
    asignacion = Decodificador(escenario).decodificar([("A1", 0), ("A2", 0)]).asignaciones[0]
    solo_una = evaluador.evaluar(Planificacion((asignacion,), "x"))
    assert solo_una.factible and solo_una.pendientes == 1

    choque = asignacion.__class__("A2", asignacion.recursos_ids, asignacion.intervalo)
    con_conflicto = evaluador.evaluar(Planificacion((asignacion, choque), "x"))
    assert not con_conflicto.factible
    assert "CAPACIDAD" in {i.regla for i in con_conflicto.conflictos_duros}
    assert con_conflicto.valor > solo_una.valor


def test_aptitud_penaliza_retraso_por_prioridad():
    actividades = [_actividad("A1", limite=9, prioridad=Prioridad.BAJA)]
    escenario = _escenario([_recurso("R1", 100)], actividades)
    plan = Planificacion(Decodificador(escenario).decodificar([("A1", 0)]).asignaciones, "x")
    resultado = EvaluadorAptitud(escenario).evaluar(plan)
    assert resultado.horas_retraso == 1
    assert resultado.valor == resultado.costo + EvaluadorAptitud(escenario).peso_retraso * 1


def test_algoritmo_base_es_determinista_y_rechaza_escenarios_vacios(pequeno):
    primero = AlgoritmoBase(pequeno.escenario, pequeno.horizonte).ejecutar()
    segundo = AlgoritmoBase(pequeno.escenario, pequeno.horizonte).ejecutar()
    assert primero.planificacion == segundo.planificacion
    assert primero.planificacion.algoritmo == "greedy"
    with pytest.raises(ValidacionError):
        AlgoritmoBase(Escenario())


def test_cromosoma_aleatorio_es_permutacion_con_preferencias_validas():
    limites = {"A1": 3, "A2": 1, "A3": 0}
    cromosoma = Cromosoma.aleatorio(limites, Random(3))
    assert sorted(g.actividad_id for g in cromosoma.genes) == ["A1", "A2", "A3"]
    assert all(0 <= g.preferencia < max(limites[g.actividad_id], 1) for g in cromosoma.genes)
    assert Cromosoma.desde_orden(["A2", "A1"]).describir() == "A2:0 A1:0"


def test_cruce_ox_conserva_permutacion_y_preferencias():
    padre = Cromosoma(tuple(Gen(f"A{i}", 1) for i in range(8)))
    madre = Cromosoma(tuple(Gen(f"A{i}", 2) for i in reversed(range(8))))
    operadores = OperadoresGeneticos(Random(5), {f"A{i}": 3 for i in range(8)}, 2)
    for _ in range(20):
        for hijo in operadores.cruzar(padre, madre):
            assert sorted(g.actividad_id for g in hijo.genes) == sorted(g.actividad_id for g in padre.genes)
            assert {g.preferencia for g in hijo.genes} <= {1, 2}


def test_mutacion_conserva_actividades_y_respeta_probabilidad_cero():
    cromosoma = Cromosoma(tuple(Gen(f"A{i}", 0) for i in range(10)))
    operadores = OperadoresGeneticos(Random(9), {f"A{i}": 4 for i in range(10)}, 2)
    assert operadores.mutar(cromosoma, 0) == cromosoma
    mutado = operadores.mutar(cromosoma, 1)
    assert mutado != cromosoma
    assert sorted(g.actividad_id for g in mutado.genes) == sorted(g.actividad_id for g in cromosoma.genes)
    assert all(0 <= g.preferencia < 4 for g in mutado.genes)


def test_seleccion_por_torneo_y_elitismo():
    individuos = [Cromosoma.desde_orden([f"A{i}"]) for i in range(5)]
    evaluados = [(c, float(v)) for c, v in zip(individuos, [5, 1, 4, 2, 3])]
    operadores = OperadoresGeneticos(Random(1), {}, 5)
    assert operadores.seleccionar(evaluados) == individuos[1]
    ordenados = sorted(evaluados, key=lambda par: par[1])
    assert operadores.elites(ordenados, 2) == [individuos[1], individuos[3]]


def test_genetico_es_reproducible_con_la_misma_semilla(pequeno):
    primero = AlgoritmoGenetico(pequeno.escenario, _configuracion(), pequeno.horizonte).ejecutar()
    segundo = AlgoritmoGenetico(pequeno.escenario, _configuracion(), pequeno.horizonte).ejecutar()
    assert primero.resumen(incluir_tiempo=False) == segundo.resumen(incluir_tiempo=False)
    assert primero.planificacion.semilla == 7
    assert primero.planificacion.algoritmo == "genetico"


def test_genetico_nunca_es_peor_que_el_base_y_es_factible(pequeno):
    resultado = AlgoritmoGenetico(pequeno.escenario, _configuracion(), pequeno.horizonte).ejecutar()
    assert resultado.aptitud.valor <= resultado.base.aptitud.valor
    assert resultado.aptitud.factible
    incidencias = MotorReglas().evaluar(resultado.planificacion, pequeno.escenario)
    assert {i.regla for i in incidencias} <= {"ACTIVIDAD_SIN_ASIGNACION"}


def test_genetico_registra_evolucion_sin_empeorar(pequeno):
    resultado = AlgoritmoGenetico(pequeno.escenario, _configuracion(), pequeno.horizonte).ejecutar()
    assert resultado.generaciones_ejecutadas == 8
    assert resultado.motivo_parada == "generaciones_maximas"
    historicos = [registro.mejor_historico for registro in resultado.historial]
    assert historicos == sorted(historicos, reverse=True)
    assert all(r.mejor <= r.promedio <= r.peor for r in resultado.historial)


def test_genetico_se_detiene_por_paciencia(pequeno):
    configuracion = _configuracion(generaciones=200, paciencia=3)
    resultado = AlgoritmoGenetico(pequeno.escenario, configuracion, pequeno.horizonte).ejecutar()
    assert resultado.motivo_parada == "sin_mejora"
    assert resultado.generaciones_ejecutadas < 200


def test_evaluar_genetico_devuelve_datos_serializables(pequeno):
    resultado = evaluar_genetico(pequeno.escenario, 11)
    assert resultado == evaluar_genetico(pequeno.escenario, 11)
    assert "segundos" not in resultado
    assert resultado["generaciones_ejecutadas"] == len(resultado["evolucion"])
