import argparse
import json

from planificador.algoritmos import AlgoritmoGenetico, ConfiguracionGenetica, ResultadoGenetico
from planificador.dominio import ValidacionError
from planificador.escenarios import ConfiguracionEscenario, generar_escenario


def _paciencia(valor: str) -> int | None:
    return None if valor.lower() == "no" else int(valor)


def _imprimir(resultado: ResultadoGenetico, detalle: bool) -> None:
    base = resultado.base.aptitud
    genetico = resultado.aptitud
    print("Parámetros:", json.dumps(resultado.resumen()["parametros"], ensure_ascii=False))
    print(f"Generaciones ejecutadas: {resultado.generaciones_ejecutadas} ({resultado.motivo_parada})")
    print(f"Tiempo: {resultado.segundos:.3f} s")
    print()
    print(f"{'Métrica':<16}{'Inicial':>20}{'Genético':>20}{'Diferencia':>20}")
    filas = (
        ("Asignadas", base.asignadas, genetico.asignadas),
        ("Pendientes", base.pendientes, genetico.pendientes),
        ("Costo", base.costo, genetico.costo),
        ("Horas retraso", base.horas_retraso, genetico.horas_retraso),
        ("Aptitud", base.valor, genetico.valor),
    )
    for nombre, inicial, final in filas:
        print(f"{nombre:<16}{inicial:>20,.2f}{final:>20,.2f}{final - inicial:>20,.2f}")
    print(f"{'Factible':<16}{str(base.factible):>20}{str(genetico.factible):>20}")
    print()

    diferencia, porcentaje = resultado.ahorro()
    texto = f" ({abs(porcentaje):.2f} %)" if porcentaje is not None else ""
    if diferencia > 0:
        print(f"Ahorro de costo frente al inicial: {diferencia:,.2f}{texto}")
    elif diferencia < 0:
        print(f"El costo aumentó {-diferencia:,.2f}{texto} frente al inicial.")
    else:
        print("El costo no cambió frente al inicial.")
    if genetico.asignadas > base.asignadas:
        print(f"El genético asigna {genetico.asignadas - base.asignadas} actividades más.")
    elif genetico.asignadas < base.asignadas:
        print("Advertencia: el genético asigna menos actividades que el inicial.")
    if genetico.valor < base.valor:
        print("La aptitud mejoró frente al inicial.")
    else:
        print("El genético no mejoró la aptitud de la solución inicial.")
    print()

    print(f"{'Gen.':>5}{'Mejor':>20}{'Promedio':>20}{'Peor':>20}{'Factibles':>11}")
    for registro in resultado.historial:
        print(f"{registro.generacion:>5}{registro.mejor:>20,.2f}{registro.promedio:>20,.2f}"
              f"{registro.peor:>20,.2f}{registro.factibles:>11}")

    if detalle:
        print()
        print(f"{'Actividad':<11}{'Recursos':<20}{'Inicio':<18}{'Fin':<18}")
        for asignacion in resultado.planificacion.asignaciones:
            recursos = ",".join(sorted(asignacion.recursos_ids))
            print(f"{asignacion.actividad_id:<11}{recursos:<20}"
                  f"{asignacion.intervalo.inicio:%Y-%m-%d %H:%M}  {asignacion.intervalo.fin:%Y-%m-%d %H:%M}")
        print()
        print("Pendientes:")
        for actividad_id, motivo in sorted(resultado.pendientes.items()):
            print(f"  {actividad_id}: {motivo}")
        for incidencia in resultado.aptitud.conflictos_duros:
            print(f"  Conflicto {incidencia.regla}: {incidencia.mensaje}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta el algoritmo inicial y el genético sobre un escenario.")
    parser.add_argument("--tamano", choices=("pequeno", "mediano", "grande"), default="pequeno")
    parser.add_argument("--semilla-escenario", type=int, default=2026)
    parser.add_argument("--semilla", type=int, default=2026, help="Semilla del algoritmo genético")
    parser.add_argument("--poblacion", type=int, default=30)
    parser.add_argument("--generaciones", type=int, default=50)
    parser.add_argument("--prob-mutacion", type=float, default=0.02)
    parser.add_argument("--prob-cruce", type=float, default=0.9)
    parser.add_argument("--elitismo", type=int, default=2)
    parser.add_argument("--torneo", type=int, default=3)
    parser.add_argument("--paciencia", type=_paciencia, default=15, help="Entero o 'no' para desactivarla")
    parser.add_argument("--detalle", action="store_true", help="Muestra asignaciones y pendientes")
    parser.add_argument("--json", action="store_true", help="Imprime el resultado completo en JSON")
    args = parser.parse_args()
    try:
        generado = generar_escenario(ConfiguracionEscenario(tamano=args.tamano, semilla=args.semilla_escenario))
        configuracion = ConfiguracionGenetica(
            poblacion=args.poblacion, generaciones=args.generaciones,
            prob_mutacion=args.prob_mutacion, prob_cruce=args.prob_cruce,
            elitismo=args.elitismo, semilla=args.semilla,
            paciencia=args.paciencia, tamano_torneo=args.torneo,
        )
        resultado = AlgoritmoGenetico(generado.escenario, configuracion, generado.horizonte).ejecutar()
    except ValidacionError as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(resultado.resumen(), ensure_ascii=False, indent=2))
    else:
        _imprimir(resultado, args.detalle)


if __name__ == "__main__":
    main()
