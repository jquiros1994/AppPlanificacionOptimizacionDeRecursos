"""Algoritmo genético de optimización (RF-05)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from random import Random
from statistics import fmean
from time import perf_counter

from planificador.algoritmos.algoritmo_base import AlgoritmoBase, ResultadoBase
from planificador.algoritmos.configuracion_genetica import ConfiguracionGenetica
from planificador.algoritmos.cromosoma import Cromosoma
from planificador.algoritmos.decodificador import Decodificador, ResultadoDecodificacion
from planificador.algoritmos.evaluador_aptitud import EvaluadorAptitud, ResultadoAptitud
from planificador.algoritmos.operadores_geneticos import OperadoresGeneticos
from planificador.dominio.escenario import Escenario
from planificador.dominio.intervalo import Intervalo
from planificador.dominio.planificacion import Planificacion


@dataclass(frozen=True)
class RegistroGeneracion:
    generacion: int
    mejor: float
    promedio: float
    peor: float
    factibles: int
    mejor_historico: float


@dataclass(frozen=True)
class ResultadoGenetico:
    planificacion: Planificacion
    cromosoma: Cromosoma
    pendientes: dict[str, str]
    aptitud: ResultadoAptitud
    base: ResultadoBase
    historial: tuple[RegistroGeneracion, ...]
    motivo_parada: str
    configuracion: ConfiguracionGenetica
    segundos: float

    @property
    def generaciones_ejecutadas(self) -> int:
        return len(self.historial)

    def ahorro(self) -> tuple[float, float | None]:
        """Diferencia de costo frente al algoritmo base y su porcentaje, si el costo base no es cero."""
        diferencia = self.base.aptitud.costo - self.aptitud.costo
        if self.base.aptitud.costo == 0:
            return diferencia, None
        return diferencia, diferencia / self.base.aptitud.costo * 100

    def resumen(self, incluir_tiempo: bool = True) -> dict[str, object]:
        diferencia, porcentaje = self.ahorro()
        resumen = {
            "parametros": asdict(self.configuracion),
            "factible": self.aptitud.factible,
            "aptitud": self.aptitud.valor,
            "costo": self.aptitud.costo,
            "horas_retraso": self.aptitud.horas_retraso,
            "asignadas": self.aptitud.asignadas,
            "pendientes": self.aptitud.pendientes,
            "conflictos_duros": len(self.aptitud.conflictos_duros),
            "generaciones_ejecutadas": self.generaciones_ejecutadas,
            "motivo_parada": self.motivo_parada,
            "base": {
                "aptitud": self.base.aptitud.valor,
                "costo": self.base.aptitud.costo,
                "horas_retraso": self.base.aptitud.horas_retraso,
                "asignadas": self.base.aptitud.asignadas,
                "pendientes": self.base.aptitud.pendientes,
            },
            "ahorro_costo": diferencia,
            "ahorro_porcentaje": porcentaje,
            "evolucion": [asdict(registro) for registro in self.historial],
            "asignaciones": [
                (a.actividad_id, sorted(a.recursos_ids), a.intervalo.inicio.isoformat(),
                 a.intervalo.fin.isoformat())
                for a in self.planificacion.asignaciones
            ],
        }
        if incluir_tiempo:
            resumen["segundos"] = self.segundos
        return resumen


class AlgoritmoGenetico:
    nombre = "genetico"

    def __init__(
        self, escenario: Escenario, configuracion: ConfiguracionGenetica,
        horizonte: Intervalo | None = None,
    ) -> None:
        self._escenario = escenario
        self._configuracion = configuracion
        self._base = AlgoritmoBase(escenario, horizonte)
        self._decodificador = Decodificador(escenario, horizonte)
        self._evaluador = EvaluadorAptitud(escenario)
        self._limites = {
            aid: self._decodificador.cantidad_candidatos(aid)
            for aid in self._decodificador.actividades_ids
        }
        self._cache: dict[Cromosoma, tuple[ResultadoDecodificacion, ResultadoAptitud]] = {}

    def ejecutar(self) -> ResultadoGenetico:
        inicio = perf_counter()
        configuracion = self._configuracion
        azar = Random(configuracion.semilla)
        operadores = OperadoresGeneticos(azar, self._limites, configuracion.tamano_torneo)
        base = self._base.ejecutar()

        poblacion = self._poblacion_inicial(azar)
        historial: list[RegistroGeneracion] = []
        mejor: Cromosoma | None = None
        mejor_factible: Cromosoma | None = None
        sin_mejora = 0
        motivo = "generaciones_maximas"

        for generacion in range(1, configuracion.generaciones + 1):
            evaluados = sorted(
                ((cromosoma, self._evaluar(cromosoma)[1].valor) for cromosoma in poblacion),
                key=lambda par: par[1],
            )
            if mejor is None or evaluados[0][1] < self._evaluar(mejor)[1].valor:
                mejor = evaluados[0][0]
                sin_mejora = 0
            else:
                sin_mejora += 1
            mejor_factible = self._actualizar_mejor_factible(mejor_factible, evaluados)
            historial.append(self._registrar(generacion, evaluados, mejor))

            if configuracion.paciencia is not None and sin_mejora >= configuracion.paciencia:
                motivo = "sin_mejora"
                break
            if generacion < configuracion.generaciones:
                poblacion = self._siguiente_generacion(evaluados, operadores, azar)

        elegido = mejor_factible if mejor_factible is not None else mejor
        decodificado, aptitud = self._evaluar(elegido)
        planificacion = Planificacion(decodificado.asignaciones, self.nombre, configuracion.semilla)
        return ResultadoGenetico(
            planificacion, elegido, decodificado.pendientes, aptitud, base,
            tuple(historial), motivo, configuracion, perf_counter() - inicio,
        )

    def _poblacion_inicial(self, azar: Random) -> list[Cromosoma]:
        """Incluye la solución greedy para que el resultado nunca sea peor que el algoritmo base."""
        poblacion = [Cromosoma.desde_orden(AlgoritmoBase.orden(self._escenario))]
        while len(poblacion) < self._configuracion.poblacion:
            poblacion.append(Cromosoma.aleatorio(self._limites, azar))
        return poblacion

    def _siguiente_generacion(
        self, evaluados: list[tuple[Cromosoma, float]], operadores: OperadoresGeneticos, azar: Random,
    ) -> list[Cromosoma]:
        configuracion = self._configuracion
        nueva = operadores.elites(evaluados, configuracion.elitismo)
        while len(nueva) < configuracion.poblacion:
            padre = operadores.seleccionar(evaluados)
            madre = operadores.seleccionar(evaluados)
            if azar.random() < configuracion.prob_cruce:
                hijos = operadores.cruzar(padre, madre)
            else:
                hijos = (padre, madre)
            for hijo in hijos:
                if len(nueva) < configuracion.poblacion:
                    nueva.append(operadores.mutar(hijo, configuracion.prob_mutacion))
        return nueva

    def _evaluar(self, cromosoma: Cromosoma) -> tuple[ResultadoDecodificacion, ResultadoAptitud]:
        if cromosoma not in self._cache:
            decodificado = self._decodificador.decodificar(cromosoma.como_pares())
            planificacion = Planificacion(decodificado.asignaciones, self.nombre)
            self._cache[cromosoma] = (decodificado, self._evaluador.evaluar(planificacion))
        return self._cache[cromosoma]

    def _actualizar_mejor_factible(
        self, actual: Cromosoma | None, evaluados: list[tuple[Cromosoma, float]],
    ) -> Cromosoma | None:
        for cromosoma, valor in evaluados:
            if self._evaluar(cromosoma)[1].factible:
                if actual is None or valor < self._evaluar(actual)[1].valor:
                    return cromosoma
                return actual
        return actual

    def _registrar(
        self, generacion: int, evaluados: list[tuple[Cromosoma, float]], mejor: Cromosoma,
    ) -> RegistroGeneracion:
        valores = [valor for _, valor in evaluados]
        factibles = sum(self._evaluar(cromosoma)[1].factible for cromosoma, _ in evaluados)
        return RegistroGeneracion(
            generacion, valores[0], fmean(valores), valores[-1], factibles, self._evaluar(mejor)[1].valor,
        )


def evaluar_genetico(escenario: Escenario, semilla: int) -> dict[str, object]:
    """Evaluador para comparar_ejecuciones (RF-07). Excluye el tiempo para que los resultados sean comparables."""
    configuracion = ConfiguracionGenetica(poblacion=20, generaciones=20, semilla=semilla)
    return AlgoritmoGenetico(escenario, configuracion).ejecutar().resumen(incluir_tiempo=False)
