# Evaluaciones secuenciales y paralelas

Implementa RF-07. El mismo conjunto de trabajos, cada uno con índice y semilla,
se ejecuta primero secuencialmente y después mediante `ProcessPoolExecutor`.
Los resultados conservan el orden de los trabajos, no el orden de finalización.

## Ejecutar

python -m planificador.paralelo --tamano pequeno --evaluaciones 4 --procesos 2 --semilla 2026
python -m planificador.paralelo --tamano mediano --evaluaciones 4 --procesos 2 --semilla 2026
python -m planificador.paralelo --tamano grande --evaluaciones 4 --procesos 2 --semilla 2026
python -m pytest tests/test_paralelo.py -q

`--detalle` incluye valores y fallos de cada evaluación. El JSON de salida se
puede guardar para registrar mediciones reales, por ejemplo en PowerShell:

```powershell
python -m planificador.paralelo --tamano mediano --detalle > resultado_mediano.json
```

La generación de datos queda fuera del tiempo medido. El tiempo de cada modalidad
incluye sus evaluaciones y copias; el paralelo incluye además el inicio y cierre
de los procesos y la transferencia de datos. Se usa `perf_counter`.
Para un experimento final se deben repetir mediciones, conservar el equipo,
versión del código, parámetros y entradas, e informar la variabilidad.

## Evaluador de muestra

`evaluar_muestra` construye una planificación aleatoria y calcula costos,
retrasos y violaciones utilizando el motor de reglas. Puede contener conflictos:
no es el algoritmo inicial ni el genético, y no se presenta como un optimizador.
Sirve para ejecutar una carga independiente real mientras se integran los otros
algoritmos. El resultado completo, incluidas asignaciones, se compara entre modos.

## Integrar otro evaluador

```python
from planificador.paralelo import ConfiguracionParalela, comparar_ejecuciones
from planificador.paralelo.simulacion import evaluar_muestra

def main():
    comparacion = comparar_ejecuciones(
        escenario,
        ConfiguracionParalela(evaluaciones=4, procesos=2, semilla=2026),
        evaluar_muestra,
    )
    print(comparacion.resumen())

if __name__ == "__main__":
    main()
```

El ejemplo asume un escenario cargado por el llamador. Para evaluar otra función,
definirla al nivel superior de un módulo con firma `(escenario, semilla)`.
No pasar lambdas ni funciones anidadas a los procesos. El retorno debe ser
serializable y comparable; excluir tiempos y otros datos no deterministas.
Usar el protector `if __name__ == "__main__"` en el punto de entrada es necesario
para `spawn`, especialmente en Windows. El módulo ya utiliza esa protección.

Cada evaluación recibe una copia de los datos. Los errores de evaluación o
transferencia se registran en lugar de anunciar éxito. Si hay fallos o resultados
diferentes, no se informa aceleración válida. En la CLI esto termina con código 1.
Dos resultados fallidos pueden coincidir, pero no constituyen un experimento exitoso.

La aceleración es `tiempo_secuencial / tiempo_paralelo`. Una razón menor que 1
indica desaceleración. El costo de crear procesos, copiar y transferir datos puede
superar el beneficio del paralelismo, especialmente en escenarios pequeños.
