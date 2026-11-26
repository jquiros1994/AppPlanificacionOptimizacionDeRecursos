# SC-250 · Plan de trabajo para las correcciones

**Base:** `Correcciones_SC250.md`, enunciado del proyecto final y código del commit `e98b0e3`. Todo se verificó ejecutando el código en Windows 11 con Python 3.14.4.

**Cómo usar este documento:** la sección 1 resume qué está mal y por qué. La sección 2 fija las decisiones. Las secciones 3 a 5 son el plan: forma de trabajo, tareas por fase y reparto. La sección 6 es la lista final antes de entregar.

---

## 1. Estado actual verificado

### 1.1 Las correcciones son válidas

Reproduje cada afirmación de `Correcciones_SC250.md`. El enunciado confirma la principal: según RF-03, una actividad sin asignar **no** es una restricción dura, y hoy el motor declara *no factible* cualquier plan con pendientes.

| Cifra del documento | Resultado |
|---|---|
| 155 pruebas pasan | ✅ Con `python -m pytest`. Con `pytest` a secas fallan 12 módulos al importar (H12). |
| Pequeño: 18 asignadas, A010 y A020 pendientes, 73,25 h; genético *factible* y motor *no factible* | ✅ Exacto con los parámetros por defecto |
| Pequeño: −21 h de retraso con el mismo costo | ✅ 94,25 h → 73,25 h, ₡71.000 |
| Mediano: ahorro de ₡9.500 (2,14 %) y −25 h | ✅ Solo con población 40, 80 generaciones y semilla 2026. El README usa la semilla 2027, que da 0,96 %. En 13 de 40 configuraciones probadas el genético **sube** el costo. |
| Grande | Con los valores por defecto, el genético sube el costo 18,7 % para asignar 9 actividades más. Con 40×80, sube el costo 25,3 % para asignar 11 más. |

Matices:

- **`decodificador.py`:** ya acepta las dependencias completadas. El error está en el motor.
- **`algoritmo_base.py`:** ya ordena con el criterio de RF-04 y devuelve los motivos. Falta exponerlo en el menú y calcular costo y retraso por actividad.
- **Penalización por pendientes:** el documento recomienda mantenerla, pero está mal (H1).

### 1.2 Defectos que el documento no incluye

| # | Defecto | Evidencia | Requisito afectado |
|---|---|---|---|
| H1 | La penalización por pendiente no garantiza que asignar sea mejor: cubre el retraso de *esa* actividad, no el que causa a otras. | 31 actividades críticas: el greedy asigna 31 y el genético devuelve 30, con mejor aptitud. `docs/genetico.md` afirma lo contrario. | Nota de RF-05, rúbrica D "Fitness y factibilidad" |
| H2 | Un conflicto duro puede salir más barato que dejar actividades pendientes. | Cuatro críticas solapadas: aptitud 2.810, frente a 3.216 si quedan vacías. | RF-05 |
| H3 | `paralelo/simulacion.py` tiene un tercer veredicto de factibilidad, distinto. | `factible_segun_motor = not incidencias` | RF-07 |
| H4 | El motor no recibe el horizonte. `evaluar_genetico` se ejecuta sin horizonte. | Una asignación fuera del horizonte no produce incidencias. | RF-04 y RF-07 |
| H5 | Estados: una dependencia ASIGNADA bloquea a la sucesora y una actividad completada o cancelada se puede reasignar sin incidencias. | Reproducido | RF-03 y RF-04 |
| H6 | La caché del genético sobrevive entre ejecuciones y falsea los tiempos. | 0,31 s y luego 0,027 s sobre la misma instancia | RF-05 y RF-09 |
| H7 | La carga y la edición fallan con dependencias en orden arbitrario, con cadenas de más de 1.000 actividades y sin *rollback*. | `ReferenciaError` y `RecursionError` | RF-02, RF-08 y RF-10 |
| H8 | El orden de los IDs en las incidencias depende de `PYTHONHASHSEED`, distinto en cada proceso. | Tres semillas de hash dan tres órdenes distintos. | RF-07: equivalencia de resultados |
| H9 | Dos ventanas contiguas (8–12 y 12–14) no cubren 11–13. | `False` | RF-01 y RF-03 |
| H10 | El grande es lento: ~58 s con los valores por defecto y más de 10 min con 40×80. El 75 % del tiempo es decodificación. | `cProfile` | Experimentos |
| H11 | En Windows, `→` y `₡` rompen la salida en cp1252. `>` en PowerShell 5.1 escribe UTF-16. | Reproducido | RF-10 y RF-11 |
| H12 | `pytest` a secas no encuentra el paquete. | 12 errores al recolectar | Rúbrica F |

**Prototipo** (copia desechable): al corregir el veredicto y la penalización, solo falla `test_generar_reporte_no_factible`, que fija el error. Las cifras del pequeño y del mediano no cambian; las del grande sí. **Los experimentos del grande deben hacerse después de la Fase 1.**

### 1.3 Lo que el enunciado pide y todavía falta

| Requisito | Falta |
|---|---|
| RF-01 y RF-02 | Edición validada. Mensaje literal «ID duplicado». En la edición, mostrar la cadena del ciclo (A002 → A005 → A002). |
| RF-03 | Veredicto correcto. Contexto en las incidencias: el ejemplo pide A001 y A004 con solape en 10:00–12:00. Seleccionar una planificación guardada. |
| RF-04 | Tabla por actividad (recursos, inicio, fin, costo, retraso, estado), totales y elección del criterio en el menú. |
| RF-05 | Ahorro con porcentaje. Si no hay mejora, decirlo. Penalización corregida y explicada. |
| RF-06 y RF-07 | Ejecutarlos sobre el escenario o la ejecución seleccionados, desde el menú. |
| RF-08 | Cargar y guardar escenarios. |
| RF-09 | Comparación completa: recursos usados, utilización, violaciones por tipo, tiempo y aptitud. Indicar si cada métrica mejoró, empeoró o no cambió. |
| RF-10 | Historial con ID (E001), abrir sin recalcular, «Ejecutar de nuevo», exportar y eliminar con confirmación. Error controlado si el archivo está dañado. |
| RF-11 | Menú principal y la secuencia de demostración de 8 pasos. Mensajes como «Debe cargar o generar un escenario». Avisar en las operaciones largas. |
| Entregables | `datos/`, resultados experimentales, artículo de 8 a 12 páginas en formato IEEE. |

---

## 2. Decisiones

| # | Decisión | Estado | Base |
|---|---|---|---|
| D1 | *Factible* = 0 conflictos duros. Las pendientes y los retrasos se informan aparte. | ✅ Resuelta | RF-03 (lista de restricciones duras), RF-04 y RF-05 |
| D2 | Solo se planifican las actividades PENDIENTES. Si un plan incluye una actividad COMPLETADA o CANCELADA, es el error duro `ESTADO_NO_PLANIFICABLE`. Una ASIGNADA **sí** puede figurar en el plan, porque está asignada justamente en una planificación; fuera del plan no genera incidencias. Una dependencia ASIGNADA fuera del plan deja a la sucesora pendiente, porque no se conoce su hora de fin. | ✅ Implementada en F1. La primera parte la fija RF-04; el tratamiento de ASIGNADA se ajustó al implementar. | RF-04 paso 1 |
| D3 | Sin `fin_real`. Una dependencia COMPLETADA se da por cumplida. Una dependencia CANCELADA deja a la sucesora pendiente, con motivo. | ✅ Resuelta | Sección 4.2 y RF-03 «dependencias terminadas» |
| D4 | JSON UTF-8 con `version_esquema` y escritura atómica. Ejecuciones con ID `E001`, `E002`… y **copia** del escenario dentro de cada ejecución. | ✅ El formato lo elige el equipo y el contenido lo fija RF-10. | RF-10 y RF-01 (referencia histórica) |
| D5 | Unir las ventanas de disponibilidad contiguas o solapadas al crear el recurso. | ⚠️ Confirmar en el equipo | El enunciado no lo dice |
| D6 | Experimentos: población 30, 50 generaciones, paciencia 15, cinco semillas (2026–2030) por escenario y tamaño. Informar media y desviación. | ⚠️ Confirmar en el equipo | Rúbrica D y E: parámetros documentados, misma carga y semillas |
| D7 | Horizonte: lo respeta el algoritmo (RF-04). La regla `HORIZONTE` en el motor es opcional, como demostración de extensibilidad. | ✅ Resuelta | Las nueve reglas de RF-03 no lo incluyen |

---

## 3. Forma de trabajo

### 3.1 Entorno con uv (Python 3.14, compatible con 3.12)

Lo prepara una persona y lo sube en un PR (tarea T0.1). Las demás solo ejecutan `uv sync`.

```powershell
uv python pin 3.14                 # crea .python-version
uv add --dev pytest                # declara pytest en pyproject.toml
uv sync                            # crea .venv e instala
uv run pytest                      # pruebas con 3.14
uv run --python 3.12 pytest        # pruebas con 3.12, obligatorio antes de cada PR a main
uv export --format requirements-txt --no-hashes -o requirements.txt   # para quien use pip
uv run python -m planificador      # menú, a partir de la Fase 5
```

Mantener `requires-python = ">=3.12"`. No usar funciones exclusivas de 3.13 o 3.14. Subir `uv.lock` y `.python-version` al repositorio.

### 3.2 Ramas y PR

- Una rama por tarea grande, con el formato que ya usa el repositorio: `feature/veredicto-unico`, `feature/validacion-dominio`, `feature/persistencia`, `feature/comparacion`, `feature/consola`, `docs/resultados-articulo`.
- PR a `main` con al menos una revisión de otra persona del equipo. La rúbrica G exige que todos entiendan la solución, así que conviene rotar quién revisa.
- No hacer `merge` con la suite en rojo en 3.12 o en 3.14.

### 3.3 Definición de terminado (para cada tarea)

1. El código y las pruebas nuevas pasan con `uv run pytest` y con `uv run --python 3.12 pytest`.
2. Las cifras de la línea base no cambian, salvo que la tarea diga lo contrario y se documente.
3. La documentación del módulo está actualizada.
4. Un compañero revisó el PR.

### 3.4 Línea base de regresión

Estas cifras deben mantenerse tras la Fase 1. Las del grande cambian y se regeneran en la Fase 6.

| Escenario (semilla 2026) | Parámetros | Greedy | Genético |
|---|---|---|---|
| Pequeño | por defecto | ₡71.000 · 94,25 h · 18/2 | ₡71.000 · 73,25 h · 18/2 (A010, A020) |
| Mediano | 40×80, semilla 2026 | ₡444.250 · 550,75 h · 83/17 | ₡434.750 · 525,75 h · 83/17 |

---

## 4. Tareas por fase

### Avance (rama `feature/veredicto-unico`)

| Fase | Estado |
|---|---|
| F0 | ✅ T0.1 y T0.3 listas. Falta T0.2: confirmar D5 y D6 y repartir responsables. |
| F1 | ✅ T1.1 a T1.10 listas. Hay 183 pruebas y pasan en 3.12 y 3.14. Las cifras del Excel se mantienen. `docs/genetico.md` y el README están actualizados. |
| Pendiente de F1 para F4 | `evaluar_genetico` todavía no recibe el horizonte (T4.3). |

Cifras nuevas del grande (semilla 2026, valores por defecto) con la penalización corregida: el greedy da ₡2.798.250 · 2.560,5 h · 353 asignadas, y el genético ₡3.495.000 · 2.885,25 h · 362 asignadas.

### Fase 0 · Preparación

| ID | Tarea | Archivos | Listo cuando |
|---|---|---|---|
| T0.1 | Entorno uv según 3.1, `pythonpath = ["."]` en `[tool.pytest.ini_options]` y salto de línea final en `requirements.txt`. | `pyproject.toml`, `requirements.txt`, `.python-version`, `uv.lock` | `uv run pytest` y `pytest` a secas pasan en 3.12 y 3.14. |
| T0.2 | Confirmar D5 y D6 en el equipo y repartir responsables (sección 5). | Este documento | Las decisiones quedan anotadas. |
| T0.3 | Prueba de regresión con la línea base de 3.4, todavía sin cambiar el código. | `tests/test_regresion.py` | La prueba pasa con el código actual. |

### Fase 1 · Veredicto único de factibilidad (RF-03, RF-05)

| ID | Tarea | Archivos | Listo cuando |
|---|---|---|---|
| T1.1 | `Incidencia` con contexto: `actividades_ids` y `recursos_ids` como tuplas **ordenadas**, `inicio`, `fin`, `categoria` (`DURA` o `PENDIENTE`) y `a_dict()`. Conservar `actividad_id` y `recurso_id` por compatibilidad. | `reglas/incidencia.py` | Sigue siendo inmutable y *hashable*. El orden no depende de `PYTHONHASHSEED` (H8). |
| T1.2 | Capacidad: reportar las actividades simultáneas y el intervalo exacto del exceso. | `reglas/regla_capacidad.py` | El ejemplo de RF-03 (R001 de capacidad 1, A001 08–12 y A004 10–13) da los IDs A001 y A004 y el intervalo 10:00–12:00. |
| T1.3 | Integridad. Una PENDIENTE sin asignar se registra como incidencia *pendiente*. Una COMPLETADA o CANCELADA sin asignar no genera nada. Una COMPLETADA, CANCELADA o ASIGNADA dentro del plan da el error duro `ESTADO_NO_PLANIFICABLE` (D2). | `reglas/regla_integridad.py` | Pruebas para los cuatro estados. |
| T1.4 | Dependencias. COMPLETADA se cumple. CANCELADA es un conflicto si la sucesora está en el plan. PENDIENTE debe estar asignada y terminar antes del inicio de la sucesora (D3). | `reglas/regla_dependencias.py` | Pruebas con dependencias completadas, canceladas, pendientes y con solape (A005 y A002 de RF-03). |
| T1.5 | El motor devuelve un `ResultadoValidacion` inmutable con `factible`, `conflictos_duros`, `pendientes`, `retrasos_por_actividad`, `horas_retraso` y `por_regla()`. `generar_reporte()` se mantiene como envoltorio. El retraso se calcula en un solo lugar. Indexar las asignaciones por actividad y por recurso para evitar las búsquedas O(N²). | `reglas/motor_reglas.py`, `reglas/penalizacion_retrasos.py` | Un plan parcial sin conflictos es FACTIBLE. Reescribir `test_generar_reporte_no_factible`. |
| T1.6 | Opcional (D7): `ReglaHorizonte`, que se registra con `agregar_regla`. Demuestra la extensibilidad. | `reglas/regla_horizonte.py` | Prueba positiva y negativa. |
| T1.7 | El evaluador usa `ResultadoValidacion`, valida las referencias antes de calcular el costo y aplica la penalización acotada: `pendiente = (costo_max + retraso_max) × N + 1` y `conflicto = pendiente × (4N + 1)`. | `algoritmos/evaluador_aptitud.py` | Los contraejemplos H1 y H2 pasan como pruebas. Un plan con referencias inválidas es *no factible* y no lanza excepción. |
| T1.8 | El decodificador sigue los mismos criterios que el motor. Una dependencia CANCELADA da el motivo «la dependencia X fue cancelada». Una dependencia ASIGNADA se trata según D2. Si el orden pierde actividades por un ciclo, se lanza un error. | `algoritmos/decodificador.py` | Pruebas con los estados de las dependencias. |
| T1.9 | La simulación paralela usa el veredicto del motor. | `paralelo/simulacion.py`, `tests/test_paralelo.py:87` | Hay un solo criterio de factibilidad en todo el código. |
| T1.10 | Regresión cruzada: greedy, genético, motor y simulación emiten el mismo veredicto para el mismo plan. | `tests/test_genetico.py` | La línea base de 3.4 se mantiene. |

### Fase 2 · Validación del dominio y edición (RF-01, RF-02)

Puede avanzar en paralelo con la Fase 1.

| ID | Tarea | Archivos | Listo cuando |
|---|---|---|---|
| T2.1 | Validadores puros: texto obligatorio, entero positivo (rechaza `bool`), real finito no negativo, enum, fecha sin zona horaria y conjunto de textos (convertido a `frozenset`). | `dominio/validaciones.py` | Pruebas unitarias de cada validador. |
| T2.2 | Validar `Recurso`. Normalizar la disponibilidad como tupla de `Intervalo` unidos (D5). | `dominio/recurso.py` | Se rechaza cada caso de `Correcciones_SC250.md` (ID vacío, `capacidad=True`, costo NaN o ∞, tipo inválido…). |
| T2.3 | Validar `Actividad`. Duración finita con un mínimo de 1 minuto. Prioridad y estado dentro del enum. | `dominio/actividad.py` | Prioridad 99, duración NaN, ∞ o 1e-11 y cantidad `True` se rechazan. |
| T2.4 | `Escenario`: `editar_recurso` y `editar_actividad`, que validan sobre una copia y aplican el cambio solo si todo pasa, sin cambiar el ID. `desde_entidades()` para cargas en cualquier orden. DFS iterativo. *Rollback* en `agregar_actividad`. Mensaje «ID duplicado». | `dominio/escenario.py`, `dominio/excepciones.py` | El ejemplo de RF-02 (añadir que A002 depende de A005) se rechaza con la cadena y el escenario queda intacto. Una cadena de 1.100 actividades no rompe. |
| T2.5 | Comprobar que el generador produce exactamente los mismos datos. | `tests/test_generador_escenarios.py` | La línea base se mantiene. |

### Fase 3 · Persistencia (RF-08, RF-10)

Depende de T2.4.

| ID | Tarea | Archivos | Listo cuando |
|---|---|---|---|
| T3.1 | Serialización determinista: ISO 8601, enums por valor, conjuntos como listas ordenadas y `version_esquema`. | `persistencia/serializacion.py` | Guardar y cargar da los mismos datos. |
| T3.2 | Escenarios: `guardar` atómico (temporal y `os.replace`) en UTF-8 y `cargar`. Un error lanza `PersistenciaError` con el campo y la ruta, sin sustituir el escenario activo. | `persistencia/escenarios.py` | Un archivo truncado o una referencia rota dan un error controlado. |
| T3.3 | Ejecuciones: `RegistroEjecucion` con E001…, fecha, copia del escenario y su hash, algoritmo, parámetros, semillas, asignaciones, métricas, diagnóstico completo, pendientes con motivo, evolución y tiempos. Operaciones `guardar`, `listar`, `abrir` (sin recalcular), `exportar` y `eliminar`. | `persistencia/ejecuciones.py` | El ejemplo de RF-10 se cumple: guardar E001, cerrar, reabrir y obtener lo mismo. |
| T3.4 | Datos de ejemplo e ignorar las ejecuciones locales. | `datos/escenario_ejemplo.json`, `.gitignore` | El ejemplo se puede cargar. |
| T3.5 | Pruebas. | `tests/test_persistencia.py` (con `tmp_path`) | Cubren la ida y vuelta, archivos dañados, versiones desconocidas y que un fallo al guardar no corrompe el archivo anterior. |

### Fase 4 · Resultados y comparación (RF-04, RF-05, RF-07, RF-09)

Depende de la Fase 1.

| ID | Tarea | Archivos | Listo cuando |
|---|---|---|---|
| T4.1 | `ResultadoEjecucion` común con filas por actividad (recursos, inicio, fin, costo, retraso, estado), totales, `ResultadoValidacion`, pendientes con motivo, parámetros, semillas, tiempos separados y `a_dict()`. | `algoritmos/resultado.py` | Greedy y genético devuelven el mismo tipo de resultado. |
| T4.2 | Greedy: devolver `ResultadoEjecucion` y exponer el criterio de orden (prioridad, luego fecha límite o ID). | `algoritmos/algoritmo_base.py` | Se cumple el ejemplo de RF-04: A001 de 4 h en 08–12. |
| T4.3 | Genético: caché local a cada ejecución (H6), tiempos del greedy y de la evolución por separado y resumen completo. `evaluar_genetico(escenario, semilla, horizonte, configuracion)` se pasa a los procesos con `functools.partial`. | `algoritmos/algoritmo_genetico.py` | Dos ejecuciones dan el mismo resultado en tiempos comparables. Secuencial y paralelo son equivalentes. |
| T4.4 | Comparador: comprueba el hash del escenario y el horizonte y advierte si difieren. Calcula diferencias absolutas y porcentuales (`None` si la base es 0) y reutiliza `funcional`. Para cada métrica dice si mejoró, empeoró o no cambió, y clasifica el resultado como *dominante*, *intercambio* o *peor*. | `algoritmos/comparacion.py` | Se cumplen los ejemplos de RF-09 (₡100.000 → ₡90.000 = −10 %; con 90 frente a 70 asignadas no se declara mejor). |
| T4.5 | Rendimiento (H10): evaluar la población en paralelo, como opción. | `algoritmos/algoritmo_genetico.py` | Mismos resultados que en secuencial. El grande con los parámetros de D6 tarda un tiempo razonable. |
| T4.6 | La CLI usa el comparador y acepta `--escenario archivo.json` y `--salida archivo.json` (H11). | `algoritmos/__main__.py` | Funciona en PowerShell 5.1. |
| T4.7 | Pruebas. | `tests/test_comparacion.py` | Cubren la base cero, escenarios distintos y el intercambio de costo por cobertura. |

### Fase 5 · Consola integrada (RF-11, más el acceso a RF-01 a RF-10)

Depende de las fases 3 y 4.

| ID | Tarea | Archivos | Listo cuando |
|---|---|---|---|
| T5.1 | Punto de entrada con `if __name__ == "__main__"` y `stdout` en UTF-8 (H11). | `planificador/__main__.py` | `uv run python -m planificador` abre el menú y se puede salir. |
| T5.2 | Lógica de la consola separada de la E/S (entrada y salida inyectables). | `interfaz/consola.py` | Se puede probar sin teclado. |
| T5.3 | Menús: Recursos, Actividades, Escenarios, Validar, Algoritmo inicial, Algoritmo genético, Análisis funcional, Procesamiento paralelo, Comparación e Historial. Incluir «Ejecutar de nuevo». | `interfaz/consola.py` (puede dividirse en `interfaz/menus/`) | Cada operación informa el inicio, el fin y los errores, y avisa en las operaciones largas. «Debe cargar o generar un escenario» aparece donde corresponde. |
| T5.4 | Prueba de la secuencia de demostración de RF-11 (8 pasos), más entradas inválidas y la cancelación de un borrado. | `tests/test_consola.py` | Pasa con un guion de entradas. |

### Fase 6 · Experimentos, documentación y entrega

Depende de todas las fases anteriores.

| ID | Tarea | Archivos | Listo cuando |
|---|---|---|---|
| T6.1 | Experimentos con los parámetros de D6 en los tres tamaños, más la comparación secuencial/paralela con `evaluar_genetico`. Registrar equipo, Python, commit, comandos y semillas. | `docs/resultados_experimentales.md`, `datos/resultados/` | Otra persona puede reproducirlos. Incluye las cifras del Excel con su configuración exacta. |
| T6.2 | README: instalación con uv y con pip, menú, pruebas y demostración. | `README.md` | Alguien sin contexto puede instalar y ejecutar el proyecto. |
| T6.3 | Docs: esquema JSON (escenarios), veredicto unificado, penalización nueva con su justificación y alcance de los tiempos (genético), y uso desde el menú (funcional y paralelo). Corregir los comandos con `>`. | `docs/*.md` | Sin contradicciones con el código. |
| T6.4 | Artículo de 8 a 12 páginas en formato IEEE, con las secciones de la sección 8 del enunciado. | `docs/articulo_cientifico.pdf` | Cada tabla enlaza con T6.1. |
| T6.5 | Ensayo de la defensa en Windows, con un entorno limpio y un escenario nuevo (semilla distinta). Cada integrante explica una parte que no programó. | — | Sin fallos críticos. |

---

## 5. Orden y reparto

```
F0 ──► F1 (veredicto) ──────────────┬──► F4 (resultados) ──► F5 (consola) ──► F6 (experimentos y entrega)
   └─► F2 (dominio) ──► F3 (persistencia) ┘
```

Propuesta para tres personas. Ajustar al tamaño real del equipo:

| Persona | Bloque | Fases |
|---|---|---|
| A | Reglas y algoritmos | F1 y luego F4 |
| B | Dominio y datos | F2, F3 y luego T6.1 |
| C | Integración y documentación | F0, pruebas de regresión, F5 y luego T6.2–T6.4 |

**Puntos de integración:**

1. **Fin de F1 y F2:** el contrato de `ResultadoValidacion` y de las entidades queda fijo. F3, F4 y F5 dependen de él, así que conviene revisarlo en equipo.
2. **Fin de F3 y F4:** se prueba la secuencia de RF-11 de punta a punta antes de pulir la consola.
3. **Antes de F6:** congelar el código y etiquetar el commit (`git tag v1.0-experimentos`). Los resultados y el artículo citan ese commit.

---

## 6. Lista de comprobación antes de entregar (rúbrica)

- [ ] **A:** las entidades rechazan los datos inválidos y la edición es atómica (F2).
- [ ] **B:** nueve reglas duras, el retraso aparte, un diagnóstico con IDs e intervalos, y pruebas positivas y negativas (F1).
- [ ] **C:** tres equivalencias funcional/imperativa, accesibles desde el menú (ya existen; F5).
- [ ] **D:** la penalización no favorece las pendientes y está documentada. Parámetros y semilla visibles. Comparación con el greedy en varias semillas (F1, F4, F6).
- [ ] **E:** secuencial y paralelo equivalentes sobre el escenario seleccionado, con aceleración y sobrecarga explicadas (F4, F6).
- [ ] **F:** demostración de 8 pasos, tres tamaños, carga y guardado, al menos 30 pruebas en verde en 3.12 y 3.14, e instalación documentada (F3, F5, F6).
- [ ] **G:** ensayo de la defensa con los cambios de parámetros que pueda pedir el docente (T6.5).
- [ ] **H:** el artículo usa resultados reales del commit etiquetado (T6.4).
- [ ] Acceso del docente al repositorio.

**Riesgos:**

- Las cifras del grande cambian tras F1: no redactar el artículo antes.
- Hay que mantener las interfaces antiguas (`generar_reporte()` e `Incidencia(actividad_id=…)`), que se usan en unas 23 líneas de las pruebas.
- El grande es lento: reservar tiempo para T4.5 o reducir los parámetros (documentándolo).
