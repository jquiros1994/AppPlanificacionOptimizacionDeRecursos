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

```powershell
pytest
```

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

Ver `CLAUDE.md` para las reglas y convenciones del proyecto.
