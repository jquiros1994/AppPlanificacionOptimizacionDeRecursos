import argparse
import json
from datetime import datetime

from planificador.dominio import ValidacionError
from planificador.escenarios import ConfiguracionEscenario, generar_escenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera y resume un escenario reproducible.")
    parser.add_argument("--tamano", choices=("pequeno", "mediano", "grande"), default="pequeno")
    parser.add_argument("--semilla", type=int, default=2026)
    parser.add_argument("--fecha", default="2026-11-02", help="Inicio YYYY-MM-DD, a las 08:00")
    parser.add_argument("--dias", type=int, default=5)
    argumentos = parser.parse_args()
    try:
        fecha = datetime.strptime(argumentos.fecha, "%Y-%m-%d").replace(hour=8)
        configuracion = ConfiguracionEscenario(
            tamano=argumentos.tamano, semilla=argumentos.semilla,
            fecha_inicio=fecha, dias=argumentos.dias,
        )
        resultado = generar_escenario(configuracion)
    except (ValueError, ValidacionError) as error:
        parser.error(str(error))
    print(json.dumps(resultado.resumen(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
