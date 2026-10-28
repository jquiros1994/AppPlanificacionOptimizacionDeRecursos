
from datetime import datetime, timedelta

from planificador.dominio.asignacion import Asignacion
from planificador.dominio.escenario import Escenario
from planificador.dominio.intervalo import Intervalo
from planificador.dominio.planificacion import Planificacion
from planificador.reglas.motor_reglas import MotorReglas
from planificador.reglas.penalizacion_retrasos import calcular_retrasos


def test_detecta_referencias_inexistentes():
    inicio = datetime(2026, 10, 28, 8, 0)
    fin = inicio + timedelta(hours=2)

    asignacion = Asignacion(
        actividad_id="A001",
        recursos_ids=frozenset({"R999"}),
        intervalo=Intervalo(inicio, fin)
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    escenario = Escenario()

    motor = MotorReglas()
    incidencias = motor.evaluar(planificacion, escenario)

    codigos = {incidencia.regla for incidencia in incidencias}

    assert "REFERENCIA_ACTIVIDAD" in codigos
    assert "REFERENCIA_RECURSO" in codigos
    assert len(incidencias) == 2

from planificador.dominio.actividad import Actividad
from planificador.dominio.recurso import Recurso
from planificador.dominio.enums import (
    TipoRecurso,
    EstadoRecurso,
    EstadoActividad,
    Prioridad
)


def test_detecta_habilidades_faltantes():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)
    fin = inicio + timedelta(hours=2)

    intervalo = Intervalo(inicio, fin)

    recurso = Recurso(
        id="R001",
        nombre="Carlos",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=5000,
        habilidades=frozenset({"Mecanica"}),
        disponibilidad=(intervalo,),
        estado=EstadoRecurso.ACTIVO
    )

    actividad = Actividad(
        id="A001",
        descripcion="Reparar sistema electrico",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=fin + timedelta(hours=1),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset(),
        estado=EstadoActividad.PENDIENTE
    )

    escenario = Escenario(
        recursos={"R001": recurso},
        actividades={"A001": actividad}
    )

    asignacion = Asignacion(
        actividad_id="A001",
        recursos_ids=frozenset({"R001"}),
        intervalo=intervalo
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    motor = MotorReglas()
    incidencias = motor.evaluar(planificacion, escenario)

    assert any(
        incidencia.regla == "HABILIDADES"
        for incidencia in incidencias
    )



def test_detecta_recurso_inactivo():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)
    fin = inicio + timedelta(hours=2)

    intervalo = Intervalo(inicio, fin)

    recurso = Recurso(
        id="R002",
        nombre="Pedro",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=4000,
        habilidades=frozenset({"Electricidad"}),
        disponibilidad=(intervalo,),
        estado=EstadoRecurso.INACTIVO
    )

    actividad = Actividad(
        id="A002",
        descripcion="Instalación eléctrica",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=fin + timedelta(hours=1),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset(),
        estado=EstadoActividad.PENDIENTE
    )

    escenario = Escenario(
        recursos={"R002": recurso},
        actividades={"A002": actividad}
    )

    asignacion = Asignacion(
        actividad_id="A002",
        recursos_ids=frozenset({"R002"}),
        intervalo=intervalo
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    motor = MotorReglas()
    incidencias = motor.evaluar(planificacion, escenario)

    assert any(
        incidencia.regla == "RECURSO_INACTIVO"
        for incidencia in incidencias
    )

    
def test_detecta_recurso_fuera_de_disponibilidad():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)

    # El recurso solamente trabaja de 8:00 a 12:00
    horario_recurso = Intervalo(
        inicio,
        inicio + timedelta(hours=4)
    )

    # La actividad se programa de 11:00 a 14:00
    horario_asignacion = Intervalo(
        inicio + timedelta(hours=3),
        inicio + timedelta(hours=6)
    )

    recurso = Recurso(
        id="R003",
        nombre="Ana",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=6000,
        habilidades=frozenset({"Electricidad"}),
        disponibilidad=(horario_recurso,),
        estado=EstadoRecurso.ACTIVO
    )

    actividad = Actividad(
        id="A003",
        descripcion="Instalación eléctrica",
        duracion_horas=3,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=inicio + timedelta(hours=8),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset(),
        estado=EstadoActividad.PENDIENTE
    )

    escenario = Escenario(
        recursos={"R003": recurso},
        actividades={"A003": actividad}
    )

    asignacion = Asignacion(
        actividad_id="A003",
        recursos_ids=frozenset({"R003"}),
        intervalo=horario_asignacion
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(
        planificacion,
        escenario
    )

    assert any(
        incidencia.regla == "DISPONIBILIDAD"
        for incidencia in incidencias
    )


def test_detecta_exceso_de_capacidad():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)

    disponibilidad = Intervalo(
        inicio,
        inicio + timedelta(hours=8)
    )

    recurso = Recurso(
        id="R004",
        nombre="Carlos",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=5000,
        habilidades=frozenset({"Electricidad"}),
        disponibilidad=(disponibilidad,),
        estado=EstadoRecurso.ACTIVO
    )

    actividades = {}

    for numero in (1, 2):
        actividad_id = f"A{numero:03d}"

        actividades[actividad_id] = Actividad(
            id=actividad_id,
            descripcion=f"Actividad {numero}",
            duracion_horas=2,
            prioridad=Prioridad.MEDIA,
            inicio_permitido=inicio,
            fecha_limite=inicio + timedelta(hours=8),
            habilidades_requeridas=frozenset({"Electricidad"}),
            cantidad_recursos=1,
            dependencias=frozenset(),
            estado=EstadoActividad.PENDIENTE
        )

    asignacion_1 = Asignacion(
        actividad_id="A001",
        recursos_ids=frozenset({"R004"}),
        intervalo=Intervalo(
            inicio,
            inicio + timedelta(hours=2)
        )
    )

    asignacion_2 = Asignacion(
        actividad_id="A002",
        recursos_ids=frozenset({"R004"}),
        intervalo=Intervalo(
            inicio + timedelta(hours=1),
            inicio + timedelta(hours=3)
        )
    )

    escenario = Escenario(
        recursos={"R004": recurso},
        actividades=actividades
    )

    planificacion = Planificacion(
        asignaciones=(asignacion_1, asignacion_2),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(
        planificacion,
        escenario
    )

    assert any(
        incidencia.regla == "CAPACIDAD"
        for incidencia in incidencias
    )

def test_detecta_cantidad_recursos_insuficiente():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)
    fin = inicio + timedelta(hours=2)

    intervalo = Intervalo(inicio, fin)

    recurso = Recurso(
        id="R005",
        nombre="Luis",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=5000,
        habilidades=frozenset({"Electricidad"}),
        disponibilidad=(intervalo,),
        estado=EstadoRecurso.ACTIVO
    )

    actividad = Actividad(
        id="A005",
        descripcion="Instalación de equipo",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=fin + timedelta(hours=1),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=2,
        dependencias=frozenset(),
        estado=EstadoActividad.PENDIENTE
    )

    escenario = Escenario(
        recursos={"R005": recurso},
        actividades={"A005": actividad}
    )

    asignacion = Asignacion(
        actividad_id="A005",
        recursos_ids=frozenset({"R005"}),
        intervalo=intervalo
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(
        planificacion,
        escenario
    )

    assert any(
        incidencia.regla == "CANTIDAD_RECURSOS"
        for incidencia in incidencias
    )


def test_detecta_dependencia_no_finalizada():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)

    actividad_1 = Actividad(
        id="A001",
        descripcion="Instalar cableado",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=inicio + timedelta(hours=8),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset()
    )

    actividad_2 = Actividad(
        id="A002",
        descripcion="Probar instalacion",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=inicio + timedelta(hours=8),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset({"A001"})
    )

    recurso = Recurso(
        id="R001",
        nombre="Carlos",
        tipo=TipoRecurso.HUMANO,
        capacidad=2,
        costo_hora=5000,
        habilidades=frozenset({"Electricidad"}),
        disponibilidad=(
            Intervalo(inicio, inicio + timedelta(hours=8)),
        )
    )

    escenario = Escenario(
        recursos={"R001": recurso},
        actividades={
            "A001": actividad_1,
            "A002": actividad_2
        }
    )

    asignacion_1 = Asignacion(
        actividad_id="A001",
        recursos_ids=frozenset({"R001"}),
        intervalo=Intervalo(
            inicio,
            inicio + timedelta(hours=2)
        )
    )

    asignacion_2 = Asignacion(
        actividad_id="A002",
        recursos_ids=frozenset({"R001"}),
        intervalo=Intervalo(
            inicio + timedelta(hours=1),
            inicio + timedelta(hours=3)
        )
    )

    planificacion = Planificacion(
        asignaciones=(asignacion_1, asignacion_2),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(
        planificacion,
        escenario
    )

    assert any(
        incidencia.regla == "DEPENDENCIAS"
        for incidencia in incidencias
    )

def test_detecta_inicio_antes_de_lo_permitido():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)

    recurso = Recurso(
        id="R001",
        nombre="Carlos",
        tipo=TipoRecurso.HUMANO,
        capacidad=1,
        costo_hora=5000,
        habilidades=frozenset({"Electricidad"}),
        disponibilidad=(
            Intervalo(
                inicio,
                inicio + timedelta(hours=8)
            ),
        )
    )

    actividad = Actividad(
        id="A001",
        descripcion="Instalar equipo",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio + timedelta(hours=2),
        fecha_limite=inicio + timedelta(hours=8),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset()
    )

    escenario = Escenario(
        recursos={"R001": recurso},
        actividades={"A001": actividad}
    )

    asignacion = Asignacion(
        actividad_id="A001",
        recursos_ids=frozenset({"R001"}),
        intervalo=Intervalo(
            inicio,
            inicio + timedelta(hours=2)
        )
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(
        planificacion,
        escenario
    )

    assert any(
        incidencia.regla == "INICIO_PERMITIDO"
        for incidencia in incidencias
    )


def test_detecta_actividad_sin_asignacion():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)

    actividad = Actividad(
        id="A010",
        descripcion="Instalar equipo",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=inicio + timedelta(hours=8),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset()
    )

    escenario = Escenario(
        actividades={"A010": actividad}
    )

    planificacion = Planificacion(
        asignaciones=(),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(
        planificacion,
        escenario
    )

    assert any(
        incidencia.regla == "ACTIVIDAD_SIN_ASIGNACION"
        for incidencia in incidencias
    )


def test_calcula_retraso_de_actividad():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)

    actividad = Actividad(
        id="A020",
        descripcion="Actividad con retraso",
        duracion_horas=4,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=inicio + timedelta(hours=2),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset()
    )

    escenario = Escenario(
        actividades={"A020": actividad}
    )

    asignacion = Asignacion(
        actividad_id="A020",
        recursos_ids=frozenset({"R001"}),
        intervalo=Intervalo(
            inicio,
            inicio + timedelta(hours=4)
        )
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    resultado = calcular_retrasos(
        planificacion,
        escenario
    )

    assert resultado.horas_totales == 2.0
    assert resultado.retrasos_por_actividad["A020"] == 2.0


def test_generar_reporte_factible():
    escenario = Escenario()

    planificacion = Planificacion(
        asignaciones=(),
        algoritmo="prueba"
    )

    motor = MotorReglas()

    reporte = motor.generar_reporte(
        planificacion,
        escenario
    )

    assert reporte["factible"] is True
    assert reporte["incidencias"] == []
    assert reporte["horas_retraso"] == 0.0
    assert reporte["retrasos_por_actividad"] == {}


def test_generar_reporte_no_factible():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8, 0)

    actividad = Actividad(
        id="A030",
        descripcion="Instalar equipo",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=inicio + timedelta(hours=8),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset()
    )

    escenario = Escenario(
        actividades={"A030": actividad}
    )

    planificacion = Planificacion(
        asignaciones=(),
        algoritmo="prueba"
    )

    motor = MotorReglas()
    reporte = motor.generar_reporte(
        planificacion,
        escenario
    )

    assert reporte["factible"] is False

    assert any(
        incidencia.regla == "ACTIVIDAD_SIN_ASIGNACION"
        for incidencia in reporte["incidencias"]
    )

    assert reporte["horas_retraso"] == 0.0


def test_detecta_asignaciones_duplicadas():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8)
    fin = inicio + timedelta(hours=2)

    actividad = Actividad(
        id="A040",
        descripcion="Instalar equipo",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=fin + timedelta(hours=2),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset()
    )

    escenario = Escenario(actividades={"A040": actividad})

    asignacion = Asignacion(
        actividad_id="A040",
        recursos_ids=frozenset({"R001"}),
        intervalo=Intervalo(inicio, fin)
    )

    planificacion = Planificacion(
        asignaciones=(asignacion, asignacion),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(planificacion, escenario)

    assert any(
        i.regla == "ASIGNACION_DUPLICADA"
        for i in incidencias
    )


def test_detecta_duracion_incorrecta():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8)

    actividad = Actividad(
        id="A041",
        descripcion="Instalar equipo",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=inicio + timedelta(hours=5),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=1,
        dependencias=frozenset()
    )

    escenario = Escenario(actividades={"A041": actividad})

    asignacion = Asignacion(
        actividad_id="A041",
        recursos_ids=frozenset({"R001"}),
        intervalo=Intervalo(
            inicio,
            inicio + timedelta(hours=3)
        )
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(planificacion, escenario)

    assert any(
        i.regla == "DURACION_INCORRECTA"
        for i in incidencias
    )


def test_detecta_exceso_de_recursos():
    from datetime import datetime, timedelta

    inicio = datetime(2026, 10, 28, 8)
    fin = inicio + timedelta(hours=2)

    actividad = Actividad(
        id="A042",
        descripcion="Instalar equipo",
        duracion_horas=2,
        prioridad=Prioridad.MEDIA,
        inicio_permitido=inicio,
        fecha_limite=fin + timedelta(hours=2),
        habilidades_requeridas=frozenset({"Electricidad"}),
        cantidad_recursos=2,
        dependencias=frozenset()
    )

    escenario = Escenario(actividades={"A042": actividad})

    asignacion = Asignacion(
        actividad_id="A042",
        recursos_ids=frozenset({"R001", "R002", "R003"}),
        intervalo=Intervalo(inicio, fin)
    )

    planificacion = Planificacion(
        asignaciones=(asignacion,),
        algoritmo="prueba"
    )

    incidencias = MotorReglas().evaluar(planificacion, escenario)

    assert any(
        i.regla == "CANTIDAD_RECURSOS"
        for i in incidencias
    )
