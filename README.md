# Planificador de Recursos (SC-250)

Sistema de Planificación y Optimización de Recursos. Proyecto final grupal
del curso Paradigmas de Programación (Universidad Fidélitas).

## Requisitos

- Python 3.12 o superior

## Instalación

Con [uv](https://docs.astral.sh/uv/) (recomendado). Usa la versión de `.python-version` (3.14):

```powershell
uv sync
```

Con pip, en cualquier Python 3.12 o superior:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` se genera desde `uv.lock` con
`uv export --format requirements-txt --no-hashes --no-emit-project -o requirements.txt`.

## Pruebas

Todas las pruebas:

```powershell
uv run pytest                                   # o: python -m pytest
uv run --isolated --python 3.12 pytest          # comprobar compatibilidad con 3.12
uv run pytest -m "not lento"                    # omitir las pruebas de varios segundos
```

`tests/test_regresion.py` fija las cifras registradas en `Resultados.xlsx`. Si un
cambio las altera, debe ser intencional y quedar documentado.

Solo las del algoritmo inicial y el genético:

```powershell
python -m pytest tests/test_genetico.py -q
```

## Algoritmo inicial y genético

Ejecuta el algoritmo inicial (greedy) y el genético sobre un escenario generado,
y muestra la comparación y la evolución de la aptitud por generación:

```powershell
python -m planificador.algoritmos --tamano pequeno
python -m planificador.algoritmos --tamano mediano --poblacion 40 --generaciones 80 --semilla 2027
python -m planificador.algoritmos --tamano pequeno --detalle
python -m planificador.algoritmos --tamano pequeno --json
```

`--detalle` muestra las asignaciones y los motivos de las actividades pendientes.
`--json` imprime el resultado completo. Las demás opciones, la fórmula de aptitud
y el funcionamiento están en [docs/genetico.md](docs/genetico.md).

## Estructura

- `planificador/dominio`: entidades, enums y excepciones del dominio.
- `planificador/reglas`: motor de reglas de negocio.
- `planificador/algoritmos`: algoritmos greedy y genético.
- `planificador/funcional`: utilidades funcionales.
- `planificador/paralelo`: procesamiento paralelo.
- `planificador/escenarios`: gestión de escenarios de planificación.
- `planificador/persistencia`: guardado y carga de datos.
- `planificador/interfaz`: interfaz de consola.
- `tests/`: pruebas automatizadas.
- `docs/`: documentación del proyecto (contratos, decisiones).
- `datos/`: datos de ejemplo.

