# Planificador de Recursos (SC-250)

Sistema de Planificación y Optimización de Recursos. Proyecto final grupal
del curso Paradigmas de Programación (Universidad Fidélitas).

## Requisitos

- Python 3.12 o superior

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Pruebas

Todas las pruebas:

```powershell
python -m pytest
```

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

