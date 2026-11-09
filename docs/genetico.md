# Algoritmo inicial y algoritmo genético

Implementa RF-04 y RF-05 en `planificador/algoritmos`.

## Ejecutar

```powershell
python -m planificador.algoritmos --tamano pequeno
python -m planificador.algoritmos --tamano mediano --poblacion 40 --generaciones 80 --semilla 2027
python -m planificador.algoritmos --tamano pequeno --detalle
python -m planificador.algoritmos --tamano pequeno --json > resultado_genetico.json
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
2. Si una dependencia quedó pendiente, la actividad también queda pendiente.
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
- `penalizacion_pendiente`: costo máximo de una actividad + `peso_retraso` × 4 × horas
  máximas de retraso posibles + 1.
- `penalizacion_conflicto`: 10 × `penalizacion_pendiente`.
- Prioridad: BAJA = 1, MEDIA = 2, ALTA = 3, CRITICA = 4.

**Por qué no favorece dejar actividades sin asignar:** la penalización por una
actividad pendiente es mayor que el costo más el retraso máximo que esa actividad
podría generar al asignarse. Por eso asignar una actividad siempre baja la aptitud.

**Factibilidad:** una solución es factible cuando el motor de reglas no reporta
incidencias, excepto `ACTIVIDAD_SIN_ASIGNACION`. Las actividades sin asignar se
reportan aparte como pendientes, con su motivo. El valor de aptitud no reemplaza
esta validación. El resultado final es el mejor individuo factible encontrado.

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
