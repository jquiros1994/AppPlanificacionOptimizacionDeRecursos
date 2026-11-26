# Algoritmo inicial y algoritmo genético

Implementa RF-04 y RF-05 en `planificador/algoritmos`.

## Ejecutar

```powershell
python -m planificador.algoritmos --tamano pequeno
python -m planificador.algoritmos --tamano mediano --poblacion 40 --generaciones 80 --semilla 2027
python -m planificador.algoritmos --tamano pequeno --detalle
python -m planificador.algoritmos --tamano pequeno --salida resultado_genetico.json
python -m pytest tests/test_genetico.py -q
```

| Opción | Valor por defecto | Rango |
|---|---|---|
| `--poblacion` | 30 | entero >= 2 |
| `--generaciones` | 50 | entero >= 1 |
| `--prob-mutacion` | 0.02 | 0 a 1, por gen |
| `--prob-cruce` | 0.9 | 0 a 1 |
| `--elitismo` | 2 | 0 a poblacion - 1 |
| `--torneo` | 3 | 2 a poblacion |
| `--paciencia` | 15 | entero >= 1, o `no` |
| `--semilla` | 2026 | semilla del genético |
| `--semilla-escenario` | 2026 | semilla del escenario generado |

## Componentes

| Archivo | Clase | Responsabilidad |
|---|---|---|
| `configuracion_genetica.py` | `ConfiguracionGenetica` | Parámetros y validación de rangos |
| `decodificador.py` | `Decodificador` | Convierte un orden de actividades en asignaciones |
| `evaluador_aptitud.py` | `EvaluadorAptitud` | Costo, retraso, pendientes, conflictos y aptitud |
| `algoritmo_base.py` | `AlgoritmoBase` | Greedy determinista (RF-04) |
| `cromosoma.py` | `Gen`, `Cromosoma` | Representación de una solución |
| `operadores_geneticos.py` | `OperadoresGeneticos` | Torneo, cruce OX, mutación y élites |
| `algoritmo_genetico.py` | `AlgoritmoGenetico` | Ciclo evolutivo y resultado |

## Cromosoma

Un cromosoma es una permutación de las actividades pendientes. Cada gen tiene
`actividad_id` y `preferencia`. Ejemplo: `A007:1 A003:0 A010:2`.

- La posición indica el turno en que la actividad reserva recursos.
- La preferencia indica desde qué recurso compatible se empieza a elegir. Los
  candidatos se ordenan por costo por hora y luego por ID.

## Decodificación

Para cada actividad, en el orden del cromosoma:

1. Si una dependencia todavía no se procesó, la actividad se pospone hasta que se procese.
   Si hay un ciclo de dependencias, se lanza `CicloDependenciaError` con la cadena.
2. Si una dependencia quedó pendiente, fue cancelada o está asignada fuera del plan,
   la actividad también queda pendiente, con su motivo.
3. Se prueban instantes desde `max(inicio_permitido, fin de dependencias)`. Solo se
   prueban los instantes donde puede cambiar la factibilidad: inicios de ventanas
   de disponibilidad y fines de asignaciones ya hechas.
4. En el primer instante con suficientes recursos activos, con las habilidades, disponibles
   y sin exceder su capacidad, se asignan los recursos según la preferencia.
5. Si no existe ese instante dentro del horizonte, la actividad queda pendiente con su motivo.

El decodificador solo construye asignaciones que cumplen las restricciones duras.
Este es el paso de reparación: los hijos producidos por cruce y mutación siempre
se decodifican a una planificación válida. El motor de reglas vuelve a validar cada
individuo para que la factibilidad no dependa solo del decodificador.

El algoritmo inicial es el mismo decodificador aplicado al orden
prioridad descendente, fecha límite e ID, con preferencia 0 (recurso más barato).

## Aptitud

Se minimiza:

```
aptitud = costo
        + peso_retraso × Σ (horas_retraso × prioridad)
        + penalizacion_pendiente × Σ prioridad de las actividades pendientes
        + penalizacion_conflicto × cantidad de conflictos duros
```

- `costo`: Σ costo_hora × duración de cada recurso asignado.
- `peso_retraso`: costo por hora del recurso más caro (mínimo 1).
- `penalizacion_pendiente`: N × (costo máximo de una actividad + `peso_retraso` × 4 ×
  horas máximas de retraso posibles) + 1, donde N es la cantidad de actividades.
- `penalizacion_conflicto`: `penalizacion_pendiente` × (4 × N + 1).
- Prioridad: BAJA = 1, MEDIA = 2, ALTA = 3, CRITICA = 4.

**Por qué no favorece dejar actividades sin asignar:** cada unidad de prioridad
pendiente cuesta más que el costo y el retraso ponderado de *todas* las actividades
juntas. Por eso la aptitud ordena las soluciones primero por la prioridad que queda
pendiente y, a igual cobertura, por costo + retraso. Asignar una actividad más
siempre mejora la aptitud, aunque retrase a otras o encarezca el plan.

Una versión anterior acotaba la penalización con el costo y el retraso de una sola
actividad. No bastaba: con 10 recursos, una tarea BAJA que necesita los 10 retrasaba
a 10 tareas CRÍTICAS, y dejarla pendiente obtenía mejor aptitud. Ese caso está en
`tests/test_validacion.py::test_asignar_mas_siempre_mejora_aunque_retrase_a_otras`.

Por la misma razón, un solo conflicto duro pesa más que dejar todas las actividades
pendientes: un plan inválido nunca supera a uno válido.

Consecuencia práctica: el genético puede subir el costo para asignar más
actividades. En el escenario grande, con los parámetros por defecto, asigna 9
actividades más que el inicial con un costo mayor. La comparación lo informa como
un intercambio, no como un ahorro.

**Factibilidad:** el veredicto lo emite solo el motor de reglas
(`MotorReglas.validar`, que devuelve un `ResultadoValidacion`). Una solución es
FACTIBLE cuando no tiene conflictos duros (RF-03). Las actividades pendientes sin
asignar y los retrasos se informan aparte y no la invalidan. El algoritmo inicial, el
genético, la simulación paralela y la validación usan ese mismo veredicto. El valor
de aptitud no reemplaza esta validación. El resultado final es el mejor individuo
factible encontrado.

**Estados de las dependencias:** una dependencia COMPLETADA se da por cumplida. Una
CANCELADA nunca termina, así que la sucesora queda pendiente con ese motivo. Una
ASIGNADA fuera del plan tampoco permite programar la sucesora, porque no se conoce
su hora de fin.

## Ciclo evolutivo

1. Población inicial: la solución greedy y el resto de cromosomas aleatorios.
2. Se decodifica y evalúa cada individuo. Los resultados se guardan en caché por cromosoma.
3. Se ordena la población de menor a mayor aptitud y se registra la generación.
4. Élites: los `elitismo` mejores pasan sin cambios.
5. Selección por torneo de `tamano_torneo` individuos.
6. Cruce OX con probabilidad `prob_cruce`. Cada gen conserva su preferencia.
7. Mutación por gen con probabilidad `prob_mutacion`: intercambio de posición y
   cambio de preferencia.
8. Se repite hasta `generaciones` o hasta `paciencia` generaciones sin mejora.

Como la solución greedy está en la población inicial y el elitismo conserva al mejor,
el genético nunca devuelve una aptitud peor que la del algoritmo inicial. Esto no
garantiza que baje el costo: puede subirlo si asigna más actividades o reduce retrasos.

## Evolución registrada

Cada `RegistroGeneracion` guarda `generacion`, `mejor`, `promedio`, `peor`,
`factibles` y `mejor_historico`.

## Integración

```python
from planificador.algoritmos import AlgoritmoGenetico, ConfiguracionGenetica

configuracion = ConfiguracionGenetica(poblacion=30, generaciones=50, semilla=2026)
resultado = AlgoritmoGenetico(escenario, configuracion, horizonte).ejecutar()
resultado.planificacion
resultado.resumen()
```

Para RF-07 se puede usar `evaluar_genetico` con `comparar_ejecuciones`:

```python
from planificador.algoritmos import evaluar_genetico
from planificador.paralelo import ConfiguracionParalela, comparar_ejecuciones

comparacion = comparar_ejecuciones(escenario, ConfiguracionParalela(), evaluar_genetico)
```
