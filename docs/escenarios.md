# Generador de escenarios

Implementa la generación y el resumen de RF-08. Usa las entidades existentes
de `planificador.dominio`; no modifica el dominio ni el motor de reglas.

## Ejecutar desde la carpeta del proyecto

```powershell
python -m planificador.escenarios --tamano pequeno --semilla 2026
python -m planificador.escenarios --tamano mediano --semilla 2026
python -m planificador.escenarios --tamano grande --semilla 2026
python -m pytest tests/test_generador_escenarios.py -q
```

Los tamaños son 20 actividades/5 recursos, 100/20 y 500/50. En el argumento
se escribe `pequeno` sin ñ. Se puede cambiar `--fecha 2027-01-04` y `--dias 5`.
La demostración muestra un resumen; no guarda ni carga archivos.

## Integración con los demás módulos

```python
from planificador.escenarios import ConfiguracionEscenario, generar_escenario

configuracion = ConfiguracionEscenario(tamano="mediano", semilla=2026)
generado = generar_escenario(configuracion)
escenario = generado.escenario
horizonte = generado.horizonte
metadatos = generado.resumen()
```

`escenario` es la clase `Escenario` del equipo, no un diccionario alternativo.
El algoritmo inicial y el genético deben recibir este mismo escenario y
usar el horizonte suministrado (el día inicial a las 08:00 hasta el último
día a las 17:00). No deben intentar buscar un horario fuera de ese intervalo.
Los intervalos respetan la convención semiabierta del dominio.

Para repetir la generación, conservar tamaño, semilla, fecha inicial, días,
versión del generador y versión del código. El resumen contiene los parámetros;
guardar los datos completos y cargarlos es responsabilidad de persistencia.

## Decisiones de generación

- Se usa una instancia local de `Random`; no se altera el azar global.
- La fecha predeterminada es fija. No se usa la fecha de la computadora.
- Se generan tipos humano, equipo y unidad operativa, capacidades de 1 a 3,
  costos no negativos y habilidades de un catálogo común. El modelo actual
  exige habilidades, pero no expresa un tipo de recurso requerido por actividad.
- Hay recursos inactivos y ventanas de 4, 6 u 8 horas por jornada.
- Las prioridades recorren los cuatro niveles para asegurar variedad.
- Cada tarea puede depender únicamente de alguna de las diez anteriores.
  Por construcción no puede haber autorreferencias, ciclos ni IDs inexistentes.
- Las tareas ordinarias tienen suficientes candidatos activos por habilidades
  e individualmente una ventana que puede cubrir su duración. No se garantiza
  que todos los candidatos coincidan en horario o estén libres simultáneamente.
- Una tarea de cada diez exige `especialidad_no_disponible`. Es un dato válido,
  pero no tiene recurso compatible: debe quedar pendiente con explicación.
  Las tareas que dependan de ella también pueden quedar pendientes.
- Algunos plazos son ajustados. Superar la fecha límite genera penalización;
  no invalida por sí solo una asignación, conforme al enunciado.
- No se garantiza que todas las actividades sean planificables. Ambos
  algoritmos deben reportar los pendientes y validar las asignaciones reales.

## Alcance de esta entrega

Incluye generación, metadatos, resumen, demostración por consola y pruebas.
La carga/guardado, el menú integrado, el módulo funcional y el paralelismo
todavía deben integrarse en sus respectivas etapas. El generador no sustituye
la validación de planes del motor de reglas.
