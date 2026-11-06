from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from random import Random

from planificador.dominio import (
    Actividad, Escenario, EstadoRecurso, Intervalo, Prioridad,
    Recurso, TipoRecurso, ValidacionError,
)


_TAMANOS = {"pequeno": (20, 5), "mediano": (100, 20), "grande": (500, 50)}
_HABILIDADES = (
    "instalacion", "diagnostico", "inspeccion",
    "mantenimiento", "calibracion", "logistica",
)


@dataclass(frozen=True)
class ConfiguracionEscenario:
    """Parámetros que deben conservarse para repetir un experimento.

    Se usa una fecha fija, no datetime.now(), para no depender del día de ejecución.
    Las fechas son locales sin zona horaria, como en las pruebas del dominio.
    """

    tamano: str = "pequeno"
    semilla: int = 2026
    fecha_inicio: datetime = datetime(2026, 11, 2, 8)
    dias: int = 5

    def __post_init__(self) -> None:
        if not isinstance(self.tamano, str) or self.tamano not in _TAMANOS:
            raise ValidacionError("tamano", "use pequeno, mediano o grande")
        if type(self.semilla) is not int:
            raise ValidacionError("semilla", "debe ser un entero")
        if type(self.dias) is not int or self.dias < 1:
            raise ValidacionError("dias", "debe ser un entero mayor o igual a 1")
        if not isinstance(self.fecha_inicio, datetime):
            raise ValidacionError("fecha_inicio", "debe ser datetime")
        if self.fecha_inicio.tzinfo is not None:
            raise ValidacionError("fecha_inicio", "use fecha local sin zona horaria")
        if (self.fecha_inicio.hour, self.fecha_inicio.minute,
                self.fecha_inicio.second, self.fecha_inicio.microsecond) != (8, 0, 0, 0):
            raise ValidacionError("fecha_inicio", "la jornada debe comenzar a las 08:00")

    @property
    def cantidades(self) -> tuple[int, int]:
        """Devuelve (actividades, recursos)."""
        return _TAMANOS[self.tamano]


@dataclass(frozen=True)
class EscenarioGenerado:
    """Agrupa el escenario y los metadatos, sin modificar las clases del dominio.

    El envoltorio es inmutable; el Escenario contenido conserva la mutabilidad
    de las entidades del dominio. Cada generación construye entidades nuevas.
    """

    escenario: Escenario
    configuracion: ConfiguracionEscenario
    horizonte: Intervalo
    version_generador: str = "1"

    def resumen(self) -> dict[str, object]:
        """Devuelve datos nuevos aptos para mostrar o registrar por persistencia."""
        recursos = self.escenario.recursos.values()
        actividades = self.escenario.actividades.values()
        return {
            "version_generador": self.version_generador,
            "tamano": self.configuracion.tamano,
            "semilla": self.configuracion.semilla,
            "dias": self.configuracion.dias,
            "inicio": self.horizonte.inicio.isoformat(),
            "fin": self.horizonte.fin.isoformat(),
            "recursos": len(self.escenario.recursos),
            "recursos_activos": sum(r.esta_activo for r in recursos),
            "recursos_por_tipo": {
                tipo.value: sum(r.tipo == tipo for r in recursos)
                for tipo in TipoRecurso
            },
            "actividades": len(self.escenario.actividades),
            "actividades_por_prioridad": {
                prioridad.name: sum(a.prioridad == prioridad for a in actividades)
                for prioridad in Prioridad
            },
            "actividades_con_dependencias": sum(bool(a.dependencias) for a in actividades),
            "dependencias": sum(len(a.dependencias) for a in actividades),
        }


def generar_escenario(
    configuracion: ConfiguracionEscenario | None = None,
) -> EscenarioGenerado:
    """Crea datos válidos, sin garantizar que todas las tareas sean planificables.

    Una de cada diez tareas exige una habilidad que no está en el catálogo.
    Las demás tienen al menos un recurso activo compatible individualmente;
    capacidad, competencia y dependencias pueden impedir asignarlas todas.
    """
    if configuracion is None:
        configuracion = ConfiguracionEscenario()
    if not isinstance(configuracion, ConfiguracionEscenario):
        raise ValidacionError("configuracion", "use ConfiguracionEscenario")

    azar = Random(configuracion.semilla)
    escenario = Escenario()
    cantidad_actividades, cantidad_recursos = configuracion.cantidades
    tipos = tuple(TipoRecurso)
    prioridades = tuple(Prioridad)

    for numero in range(1, cantidad_recursos + 1):
        ventanas = []
        for dia in range(configuracion.dias):
            inicio = configuracion.fecha_inicio + timedelta(days=dia, hours=azar.randrange(2))
            ventanas.append(Intervalo(inicio, inicio + timedelta(hours=azar.choice((4, 6, 8)))))
        habilidades = frozenset(azar.sample(_HABILIDADES, azar.randint(1, 3)))
        escenario.agregar_recurso(Recurso(
            id=f"R{numero:03d}", nombre=f"Recurso {numero:03d}",
            tipo=tipos[(numero - 1) % len(tipos)],
            capacidad=1 + (numero - 1) % 3,
            costo_hora=float(azar.randrange(0, 21) * 500),
            habilidades=habilidades, disponibilidad=tuple(ventanas),
            estado=(EstadoRecurso.INACTIVO if numero % 10 == 0 or numero == cantidad_recursos
                    else EstadoRecurso.ACTIVO),
        ))

    activos = [r for r in escenario.recursos.values() if r.esta_activo]
    for numero in range(1, cantidad_actividades + 1):
        referencia = azar.choice(activos)
        ventana = azar.choice(referencia.disponibilidad)
        duracion = azar.choice((0.5, 1.0, 2.0, 3.0))
        margen = int(ventana.duracion_horas() - duracion)
        inicio = ventana.inicio + timedelta(hours=azar.randint(0, margen))
        # El plazo puede ser ajustado: un retraso es penalización, no dato inválido.
        plazo = azar.choice((duracion / 2, duracion, duracion + 2))
        horizonte_fin = configuracion.fecha_inicio + timedelta(days=configuracion.dias - 1, hours=9)
        limite = min(inicio + timedelta(hours=plazo), horizonte_fin)
        compatibles = [r for r in activos if r.tiene_habilidades(referencia.habilidades)]
        cantidad = azar.randint(1, min(2, len(compatibles)))
        habilidades = referencia.habilidades
        if numero % 10 == 0:
            habilidades = frozenset({"especialidad_no_disponible"})

        anteriores = list(escenario.actividades)[-10:]
        dependencias = frozenset()
        if anteriores and (numero == 2 or azar.random() < 0.35):
            dependencias = frozenset(azar.sample(anteriores, azar.randint(1, min(2, len(anteriores)))))
        escenario.agregar_actividad(Actividad(
            id=f"A{numero:03d}", descripcion=f"Servicio {numero:03d}",
            duracion_horas=duracion,
            prioridad=prioridades[(numero - 1) % len(prioridades)],
            inicio_permitido=inicio, fecha_limite=limite,
            habilidades_requeridas=habilidades, cantidad_recursos=cantidad,
            dependencias=dependencias,
        ))

    horizonte = Intervalo(
        configuracion.fecha_inicio,
        configuracion.fecha_inicio + timedelta(days=configuracion.dias - 1, hours=9),
    )
    return EscenarioGenerado(escenario, configuracion, horizonte)
