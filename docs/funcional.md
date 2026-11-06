# Análisis funcional

Implementa RF-06 sobre las clases del dominio. Las operaciones no cambian las
colecciones ni los atributos de entrada y no dependen de variables globales mutables.
Filtrado y agrupación conservan referencias a las entidades: no son copias profundas.
Un llamador que luego edite una entidad seguirá editando el objeto del dominio.

## Ejecutar

```powershell
python -m planificador.funcional
python -m pytest tests/test_funcional.py -q
```

La demostración muestra tres equivalencias y el costo de una entrada parcial de
análisis. No presenta esa entrada como una planificación factible.

## Operaciones disponibles

- `filtrar_recursos_activos(recursos)`: devuelve una tupla mediante `filter`.
- `ordenar_actividades(actividades)`: prioridad descendente, fecha límite e ID.
- `agrupar_actividades_por_prioridad(actividades)`: usa `reduce` y construye
  un diccionario nuevo con tuplas por prioridad.
- `calcular_costo_total(plan, escenario)`: transforma las asignaciones mediante
  `map` y agrega los importes con `fsum`.
- `costos_por_recurso(plan, escenario)`: conserva también los recursos de costo cero.
- `tareas_retrasadas(plan, escenario)`: horas positivas por actividad; varios
  recursos de una tarea no multiplican el retraso.
- `utilizacion_por_recurso(plan, escenario, horizonte)`: horas asignadas divididas
  entre horas disponibles por capacidad. Las ventanas superpuestas se cuentan
  una vez y los intervalos se recortan al horizonte. Sin disponibilidad devuelve
  `None`, porque el denominador es cero. La razón no se limita a 1.
- `comparar_operaciones(plan, escenario)`: compara tres versiones funcionales
  con sus implementaciones imperativas independientes.

## Comparación de paradigmas

El filtrado imperativo utiliza un bucle y una lista local. El funcional expresa
la condición como predicado de `filter`. Ambos conservan el orden de entrada.
El costo imperativo acumula importes en una variable local; el funcional transforma
y agrega. Se usa tolerancia numérica al comparar resultados de punto flotante.
La agrupación imperativa añade a listas locales; la funcional devuelve un nuevo
acumulador en cada paso de `reduce`. Ninguna versión modifica las entradas.
Las asignaciones locales no son efectos secundarios sobre el escenario recibido.

## Integración

```python
from planificador.funcional import comparar_operaciones, calcular_costo_total

equivalencias = comparar_operaciones(planificacion, escenario)
costo = calcular_costo_total(planificacion, escenario)
```

El menú puede recibir un `Escenario` y una `Planificacion` de cualquier algoritmo.
Las métricas no sustituyen las reglas de negocio. Se rechazan referencias a
recursos o actividades inexistentes mediante `ReferenciaError`.
