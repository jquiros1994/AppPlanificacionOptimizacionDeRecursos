import argparse
from dataclasses import asdict
import json

from planificador.dominio import ValidacionError
from planificador.escenarios import ConfiguracionEscenario, generar_escenario
from planificador.paralelo import ConfiguracionParalela, comparar_ejecuciones
from planificador.paralelo.simulacion import evaluar_muestra


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara evaluaciones secuenciales y paralelas.")
    parser.add_argument("--tamano", choices=("pequeno", "mediano", "grande"), default="pequeno")
    parser.add_argument("--semilla", type=int, default=2026)
    parser.add_argument("--evaluaciones", type=int, default=4)
    parser.add_argument("--procesos", type=int, default=2)
    parser.add_argument("--detalle", action="store_true", help="Incluye resultados y fallos de cada evaluación")
    args = parser.parse_args()
    try:
        generado = generar_escenario(ConfiguracionEscenario(tamano=args.tamano, semilla=args.semilla))
        configuracion = ConfiguracionParalela(args.evaluaciones, args.procesos, args.semilla)
    except ValidacionError as error:
        parser.error(str(error))
    comparacion = comparar_ejecuciones(generado.escenario, configuracion, evaluar_muestra)
    salida = {"escenario": generado.resumen(), "comparacion": comparacion.resumen()}
    if args.detalle:
        salida["secuencial"] = asdict(comparacion.secuencial)
        salida["paralelo"] = asdict(comparacion.paralelo)
    print(json.dumps(salida, ensure_ascii=False, indent=2))
    if comparacion.aceleracion is None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
