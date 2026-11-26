# Planificador de Recursos (SC-250)

Sistema Inteligente de Planificación y Optimización de Recursos. Proyecto final grupal
del curso Paradigmas de Programación (Universidad Fidélitas).

El sistema administra recursos y actividades, valida restricciones con un motor de
reglas, construye planes con un algoritmo greedy, los optimiza con un algoritmo genético
propio y compara la ejecución secuencial con la paralela. Integra programación
imperativa, orientada a objetos, funcional, declarativa (motor de reglas) y paralela.

## Estado del proyecto

| Requisito | Estado | Dónde |
|---|---|---|
| Modelo de dominio y validaciones (RF-01, RF-02) | ✅ Entidades validadas, edición atómica, ciclos detectados | `planificador/dominio` |
| Motor de reglas (RF-03) | ✅ Veredicto FACTIBLE / NO FACTIBLE, diagnóstico con IDs e intervalos | `planificador/reglas` |
| Algoritmo inicial (RF-04) | ✅ Greedy determinista | `planificador/algoritmos` |
| Algoritmo genético (RF-05) | ✅ | `planificador/algoritmos` |
| Análisis funcional (RF-06) | ✅ | `planificador/funcional` |
| Secuencial frente a paralelo (RF-07) | ✅ | `planificador/paralelo` |
| Generación de escenarios (RF-08) | ✅ Generar. ⏳ Cargar y guardar | `planificador/escenarios` |
| Comparación de algoritmos (RF-09) | ⏳ Comparación básica en la CLI | — |
| Persistencia (RF-10) | ⏳ Pendiente | `planificador/persistencia` |
| Menú integrado (RF-11) | ⏳ Pendiente | `planificador/interfaz` |

El detalle de lo que falta, las decisiones tomadas y el orden de trabajo están en
[Plan_Correcciones_SC250.md](Plan_Correcciones_SC250.md). Mientras no exista el menú,
cada módulo tiene su propio comando de demostración (ver [Uso](#uso)).

## Requisitos

- Python 3.12 o superior. El equipo desarrolla con 3.14 (`.python-version`).
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip.

## Instalación

Con uv:

```powershell
uv sync
```

Con pip:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` se genera desde `uv.lock`. Si cambian las dependencias, regenerarlo con:

```powershell
uv export --format requirements-txt --no-hashes --no-emit-project -o requirements.txt
```

## Pruebas

```powershell
uv run pytest                              # todas (con pip: python -m pytest, o pytest)
uv run pytest -m "not lento"               # omite las de varios segundos
uv run --isolated --python 3.12 pytest     # compatibilidad con Python 3.12
uv run pytest tests/test_validacion.py     # un archivo
```

| Archivo | Qué cubre |
|---|---|
| `test_validacion_dominio.py`, `test_recurso.py`, `test_actividad.py`, `test_escenario.py`, `test_intervalo.py` | Entidades, valores inválidos, edición y ciclos |
| `test_motor_reglas.py`, `test_validacion.py` | Reglas, veredicto único y ejemplos del enunciado |
| `test_genetico.py` | Decodificador, aptitud, operadores y ciclo evolutivo |
| `test_regresion.py` | Cifras de `Resultados.xlsx`: deben mantenerse salvo cambio intencional |
| `test_funcional.py`, `test_paralelo.py`, `test_generador_escenarios.py` | RF-06, RF-07 y RF-08 |

## Uso

Todos los comandos se ejecutan desde la raíz del repositorio. Con pip, cambie
`uv run python` por `python`. En el tamaño se escribe `pequeno`, sin ñ.

### Escenarios (RF-08)

```powershell
uv run python -m planificador.escenarios --tamano mediano --semilla 2026
```

Genera 20/5, 100/20 o 500/50 actividades y recursos, de forma reproducible por semilla.
Detalles en [docs/escenarios.md](docs/escenarios.md).

### Algoritmo inicial y genético (RF-04, RF-05)

```powershell
uv run python -m planificador.algoritmos --tamano pequeno --detalle
uv run python -m planificador.algoritmos --tamano mediano --poblacion 40 --generaciones 80 --semilla 2026
uv run python -m planificador.algoritmos --tamano pequeno --json
```

Muestra el plan inicial y el genético lado a lado, su factibilidad, la evolución de la
aptitud y, con `--detalle`, las asignaciones y los motivos de cada pendiente. Parámetros,
fórmula de aptitud y criterio de factibilidad en [docs/genetico.md](docs/genetico.md).

### Análisis funcional (RF-06)

```powershell
uv run python -m planificador.funcional
```

Ver [docs/funcional.md](docs/funcional.md).

### Secuencial frente a paralelo (RF-07)

```powershell
uv run python -m planificador.paralelo --tamano mediano --evaluaciones 4 --procesos 2
```

Ver [docs/paralelo.md](docs/paralelo.md). En escenarios pequeños, el paralelo suele ser más
lento por el costo de crear procesos: el resultado lo informa como desaceleración.

### Guardar la salida en un archivo

Use `--salida`, que escribe JSON en UTF-8:

```powershell
uv run python -m planificador.algoritmos --tamano mediano --salida resultado_genetico.json
uv run python -m planificador.paralelo --tamano mediano --detalle --salida resultado_paralelo.json
```

No redirija con `>`: en Windows PowerShell 5.1 el archivo queda en UTF-16, y con
`Out-File -Encoding utf8` queda con BOM. En ambos casos, otros programas pueden no leerlo.

## Criterios principales

- **Factibilidad:** un plan es FACTIBLE cuando no tiene conflictos duros (RF-03). Las
  actividades pendientes sin asignar y los retrasos se informan aparte y no lo invalidan.
  El motor de reglas emite el veredicto, y todos los algoritmos usan ese mismo resultado.
- **Restricciones duras:** referencias existentes, habilidades, recurso activo,
  disponibilidad completa, capacidad simultánea, cantidad de recursos, dependencias
  terminadas, inicio permitido e integridad (sin duplicados, con la duración exacta, sin
  reasignar actividades completadas o canceladas). La regla de horizonte es opcional.
- **Aptitud del genético:** costo + retraso ponderado por prioridad + penalizaciones.
  Asignar una actividad más siempre mejora la aptitud, y un plan con conflictos nunca
  supera a uno válido (ver [docs/genetico.md](docs/genetico.md)).
- **Validación de datos:** las entidades rechazan los valores inválidos al crearse y al
  modificarse. Editar a través de `Escenario` valida sobre una copia y no deja cambios
  parciales.

## Estructura

```
planificador/
  dominio/       entidades, enums, excepciones y validadores
  reglas/        motor de reglas, una clase por restricción
  algoritmos/    greedy, genético, decodificador y aptitud
  funcional/     métricas con funciones puras y comparación imperativa
  paralelo/      evaluaciones secuenciales y paralelas
  escenarios/    generador reproducible
  persistencia/  (pendiente) guardado y carga
  interfaz/      (pendiente) menú de consola
tests/           pruebas automatizadas (pytest)
docs/            documentación por módulo
```

## Flujo de trabajo del equipo

- Una rama por tarea (`feature/...`, `docs/...`) y un PR a `main` con al menos una revisión.
- Antes de pedir revisión: `uv run pytest` y `uv run --isolated --python 3.12 pytest`.
- Si cambia una cifra de `tests/test_regresion.py`, explicarlo en el PR.
