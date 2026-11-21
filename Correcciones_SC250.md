# SC-250 · Correcciones para finalizar el proyecto

**Sistema Inteligente de Planificación y Optimización de Recursos**  
**Base de revisión:** enunciado SC-250, ZIP del proyecto, informe técnico y `Resultados.xlsx`. Las rutas parten de la raíz del repositorio.

Las 155 pruebas de la revisión inicial pasaron en Linux. Las corridas en Windows desde Visual Studio Code confirmaron el funcionamiento del greedy y el genético en los escenarios pequeño y mediano. El genético redujo 21 horas de retraso en el pequeño con el mismo costo. En el mediano ahorró ₡9.500 (2,14 %) y redujo 25 horas de retraso con la misma cobertura. Las cifras corresponden a las configuraciones registradas en el Excel.

La prioridad es unificar la validación. Al reconstruir las 18 asignaciones del JSON del escenario pequeño y ejecutar el motor del ZIP, el genético informó **factible, 0 conflictos duros y 2 pendientes**. El motor informó **no factible** por A010 y A020, las únicas pendientes. Ambos calcularon **73,25 horas** de retraso.

## 1. Archivos existentes que se deben corregir

### Prioridad 1 · Reglas y factibilidad

| Archivo | Por qué | Recomendación |
|---|---|---|
| `planificador/reglas/motor_reglas.py` | El reporte declara no factible cualquier plan con una incidencia, incluso si solo faltan actividades por asignar. | Centralizar el veredicto en el motor. Separar restricciones duras, pendientes y retrasos. Usar ese resultado al validar, comparar y guardar una ejecución. |
| `planificador/reglas/regla_integridad.py` | Reporta ausencia de asignación incluso para actividades completadas o canceladas. | Registrar como pendientes las actividades elegibles que quedaron sin asignar. Conservar como errores de integridad la duración incorrecta y las asignaciones duplicadas. |
| `planificador/reglas/regla_dependencias.py` | Exige una asignación en el plan nuevo para una dependencia que ya figura como completada. | Reconocer una finalización previa. Si el modelo registra su hora, comprobar que sea anterior o igual al inicio de la sucesora. Una dependencia pendiente debe estar programada y terminar a tiempo. |
| `planificador/reglas/regla_capacidad.py` | Detecta el exceso, pero el ejemplo de aceptación devuelve solo el ID del recurso. | Reportar las actividades que exceden la capacidad y el intervalo de conflicto. Comprobar el ejemplo de R001 con A001 y A004 entre 10:00 y 12:00. |
| `planificador/reglas/incidencia.py` | El modelo permite un solo ID de actividad y carece de campos para el intervalo. | Admitir datos de contexto estructurados y serializables para varios IDs, inicio y fin. Mantener compatibilidad con las reglas que reportan una sola actividad. |
| `planificador/algoritmos/evaluador_aptitud.py` | Aplica por su cuenta un filtro de incidencias distinto del reporte del motor. | Consumir el veredicto y los conflictos duros del motor. Mantener la penalización ponderada por pendientes y el cálculo de aptitud. |
| `planificador/algoritmos/decodificador.py` | Acepta dependencias completadas con un criterio que el motor actual contradice. | Alinear la lógica de precedencia con el motor, incluida la hora histórica si existe. Seguir devolviendo motivos de no asignación por actividad. |

### Prioridad 2 · Gestión de datos

| Archivo | Por qué | Recomendación |
|---|---|---|
| `planificador/dominio/recurso.py` | Admite identificadores y nombres vacíos, tipos inválidos, capacidad booleana y costo NaN. | Validar campos obligatorios, tipo y estado, capacidad entera positiva, costo finito no negativo, habilidades y disponibilidad. Aplicar las mismas validaciones en registro, edición y carga. |
| `planificador/dominio/actividad.py` | Admite identificación vacía, prioridad 99, duración NaN y cantidad booleana. | Validar campos obligatorios, prioridad y estado, duración finita positiva, fechas y cantidad entera positiva. Si se decide registrar la finalización histórica, documentar y validar ese campo. |
| `planificador/dominio/escenario.py` | Hay alta, desactivación y borrado de pendientes, pero falta edición validada. | Validar una copia de los datos editados, comprobar dependencias y ciclos, y aplicar el cambio solo si todos los controles pasan. Mantener los IDs y proteger las referencias existentes. |

### Prioridad 3 · Ejecución y comparación

| Archivo | Por qué | Recomendación |
|---|---|---|
| `planificador/algoritmos/algoritmo_base.py` | El greedy funciona, pero falta su ejecución independiente con detalle por actividad. | Exponer resultados reutilizables por el menú con asignaciones, costos, retrasos, pendientes, motivos y tiempo. Habilitar el criterio de ordenamiento requerido con desempate determinista. |
| `planificador/algoritmos/algoritmo_genetico.py` | El resultado visible mezcla el tiempo del cálculo inicial con el de la corrida genética y el JSON resume el diagnóstico como un conteo. | Conservar parámetros, evolución, motivos y diagnóstico completo en el resultado. Registrar y documentar qué incluye el tiempo de cada método. |
| `planificador/algoritmos/__main__.py` | Existe una comparación básica que funciona en Windows, pero omite métricas del RF-09. | Usar el comparador común para presentar recursos utilizados, utilización, violaciones por regla, tiempos y diferencias porcentuales. Indicar si un ahorro viene acompañado de más retrasos o pendientes. |

Para integrar los módulos funcional y paralelo, reutilizar `planificador/funcional/metricas.py` y `planificador/paralelo/evaluaciones.py` desde la consola nueva. Sus comandos independientes pueden seguir sirviendo como demostraciones.

### Prioridad 4 · Pruebas y documentación

| Archivo | Por qué | Recomendación |
|---|---|---|
| `tests/test_motor_reglas.py` | La suite anterior dejó pasar la diferencia entre un plan parcial y uno con conflictos. | Probar planes parciales, dependencias completadas, actividades canceladas y el diagnóstico con IDs e intervalo de solapamiento. |
| `tests/test_genetico.py` | Falta verificar que greedy, genético y motor emitan el mismo veredicto. | Usar como regresión el plan pequeño del Excel, con 18 asignadas, A010 y A020 pendientes, cero conflictos duros y 73,25 h de retraso. |
| `tests/test_recurso.py` | Los casos válidos existentes no cubren todos los valores inválidos detectados. | Probar nombres e IDs vacíos, enums inválidos, capacidad booleana y costos no finitos. |
| `tests/test_actividad.py` | Faltan casos de prioridad fuera del enum y datos numéricos inválidos. | Probar prioridad 99, duración NaN, cantidad booleana y campos obligatorios vacíos. |
| `tests/test_escenario.py` | La edición nueva necesita verificar la integridad del grafo. | Probar edición válida, rechazo de ciclos y referencias inexistentes, y conservación del escenario ante un error. |
| `README.md` | Documenta la instalación y los comandos de genética, y falta la secuencia integral. | Añadir inicio del menú, instalación, ejecución de pruebas y una demostración de generación, validación, comparación y reapertura. |
| `docs/escenarios.md` | Describe la generación y falta el contrato de los datos importados. | Documentar el esquema, las validaciones y cómo cargar y guardar. |
| `docs/genetico.md` | El diseño del algoritmo ya está documentado. Falta explicar el criterio de factibilidad unificado y el alcance de los tiempos. | Actualizar esas secciones y añadir un ejemplo que muestre cobertura, costo, retraso y aptitud. |
| `docs/funcional.md` | El ejemplo actual usa una muestra fija. | Documentar cómo seleccionar un escenario o ejecución y consultar sus métricas en el menú. |
| `docs/paralelo.md` | La ejecución independiente genera su propio escenario. | Documentar cómo comparar ambas modalidades sobre el escenario seleccionado, qué condiciones deben coincidir y cómo interpretar la aceleración. |

## 2. Archivos que faltan por agregar

Los nombres son una propuesta de organización. Los entregables y comportamientos vienen del enunciado.

| Archivo propuesto | Qué debe incluir | Cómo comprobarlo |
|---|---|---|
| `planificador/__main__.py` | Punto de entrada protegido con `if __name__ == "__main__"` para abrir el menú y convivir con el arranque de procesos en Windows. | `python -m planificador` abre el menú y permite salir correctamente. |
| `planificador/interfaz/consola.py` | Menú para gestión de datos, escenario seleccionado, ejecución independiente de ambos algoritmos, validación, análisis funcional, paralelismo, comparación e historial. | Se puede completar la demostración desde el menú. Las operaciones largas tienen un aviso y los errores de entrada permiten continuar. |
| `planificador/persistencia/escenarios.py` | Carga y guardado en el formato elegido, con configuración, semilla, horizonte, recursos y actividades. | Guardar y recargar conserva los datos. Un archivo inválido no reemplaza el escenario activo. |
| `planificador/persistencia/ejecuciones.py` | Historial con ID, fecha, referencia o copia del escenario, algoritmo, parámetros, semillas, asignaciones, métricas y diagnóstico. Implementar consulta, reapertura, exportación y borrado confirmado desde el menú. | Cerrar y reabrir conserva la ejecución sin recalcular. Guardar evita resultados parciales y los archivos dañados reciben un error controlado. |
| `planificador/algoritmos/comparacion.py` | Comparar ejecuciones equivalentes y calcular diferencias. Reutilizar las métricas existentes para costos, retrasos y utilización. | Advierte si cambian los datos o el horizonte. Maneja bases cero en los porcentajes y explica los intercambios entre cobertura, costo y retraso. |
| `tests/test_persistencia.py` | Pruebas de guardado, reapertura, datos corruptos y referencias inválidas. | Los datos recuperados coinciden con los guardados. |
| `tests/test_comparacion.py` | Pruebas de métricas, coherencia de entradas y porcentajes. | Una reducción de costo con menor cobertura queda reflejada como un intercambio. |
| `tests/test_consola.py` | Pruebas del menú, entradas inválidas y selección de escenarios y ejecuciones. | El flujo llega desde la carga hasta la consulta de resultados guardados. |
| `datos/escenario_ejemplo.json` | Un escenario de ejemplo en el formato que implemente la carga. | Se puede abrir desde el menú y usar con ambos algoritmos. |
| `docs/resultados_experimentales.md` | Comandos, equipo y entorno, versión del código, semillas, parámetros y resultados. Incorporar los datos de `Resultados.xlsx` y registrar las corridas faltantes. | Otra persona puede reproducir las comparaciones. Si se estudia el efecto del tamaño, usar parámetros comunes en los tres escenarios. |
| `docs/articulo_cientifico.pdf` | Artículo con metodología, resultados reales, discusión, conclusiones y referencias. El enunciado recomienda 8–12 páginas en IEEE o formato equivalente. | Las tablas y conclusiones se pueden rastrear hasta los resultados experimentales. |

## 3. Resumen de lo que falta para finalizar el proyecto

1. **Corregir y comprobar la factibilidad.** El motor y ambos algoritmos deben dar el mismo veredicto para el mismo plan, mostrar pendientes aparte y explicar los conflictos reales. Repetir la comprobación con el escenario pequeño del Excel.
2. **Completar gestión y persistencia.** Agregar la edición validada, la carga y guardado de escenarios y un historial que permita recuperar la ejecución después de cerrar la aplicación.
3. **Integrar el flujo y completar la comparación.** Desde un solo menú se debe poder elegir un escenario, consultar y editar datos, correr los algoritmos por separado, validar y comparar, analizar métricas, medir el paralelismo y consultar el historial.
4. **Verificar el proyecto en Windows.** Mantener la suite existente pasando, sumar las regresiones y ejecutar el escenario grande, `pytest`, la comparación secuencial/paralela y el flujo de reapertura. El Excel ya acredita los escenarios pequeño y mediano.
5. **Cerrar los entregables académicos.** Incluir código y dependencias, documentación técnica, datos de ejemplo, resultados experimentales, artículo científico y acceso al repositorio para el docente. Ensayar la demostración completa con un escenario nuevo.

