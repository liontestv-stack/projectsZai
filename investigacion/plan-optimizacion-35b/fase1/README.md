# Fase 1 — Diagnóstico de projectsZai

## Un solo archivo para ejecutar desde D:\ZLia

El ejecutor es **FASE1-DIAGNOSTICO.py**. Es autónomo: no necesita otros .py, módulos propios, paquetes pip ni un archivo .bat.

1. Descarga [FASE1-DIAGNOSTICO.py](https://raw.githubusercontent.com/liontestv-stack/projectsZai/main/investigacion/plan-optimizacion-35b/fase1/FASE1-DIAGNOSTICO.py).
2. Guárdalo directamente en **D:\ZLia\FASE1-DIAGNOSTICO.py**.
3. Haz doble clic en ese archivo.
4. Al finalizar, lee la ruta del ZIP y pulsa ENTER para cerrar la ventana.

Requisitos: Windows 10/11 y Python 3.8+ instalado y asociado a archivos .py. Usa únicamente la biblioteca estándar de Python.

## Dónde busca archivos

- Configuración principal: D:\ZLia\config.txt.
- Ejecutable: valor de RUTA_SERVER en config.txt.
- Modelo GGUF: valor de RUTA_MODELO en config.txt.
- Dump permitido de flags, si está disponible: D:\ZLia\InformacionCritica\configs\llama-flags-nuevo.txt o D:\ZLia\llama-flags-nuevo.txt.

El dump de flags es una referencia opcional. Aunque no esté presente, el script puede comparar las flags configuradas con la ayuda del ejecutable local.

## Salida

Al ejecutarlo desde D:\ZLia, crea:

D:\ZLia\salidas\FASE1_<fecha_hora>\
- phase1_report.md
- phase1_report.json
- runtime_version.txt
- runtime_help.txt
- allowed_flags_dump.txt (si se encontró el dump)
- processes.json y processes_after_sample.json
- server_endpoints.json y slot_activity.json
- memory_counters.json
- gpu_samples.csv
- cache_probe.json

También crea **D:\ZLia\salidas\FASE1_<fecha_hora>.zip**. Ese ZIP es el paquete que debes compartir para el análisis.

## Qué hace en modo normal

Es solo lectura:
- Lee config.txt, pero no lo modifica.
- Ejecuta llama-server --version y --help (no carga el modelo).
- Compara flags configuradas con la ayuda de la build instalada y con el dump de flags, si existe.
- Lee únicamente cabecera y metadatos del GGUF. No carga ni recorre los tensores.
- Inspecciona procesos llama-server y redacta argumentos habituales de claves/tokens.
- Consulta GET /health, /slots y /metrics en localhost. No conserva prompts ni texto de slots.
- Captura RAM, memoria comprometida, contadores de paginación y VRAM/actividad GPU cuando el sistema lo permite.
- Contrasta el número de slots y flags configuradas con el proceso actualmente abierto.

No inicia, detiene ni reinicia el servidor. No modifica flags, config.txt, propiedades ni slots.

**Recomendación:** deja Qwen cargado y sin peticiones activas mientras haces la captura. Si hay una conversación generándose, los datos de VRAM y paginación reflejarán esa carga y se marcarán los estados de slots que la API permita detectar.

## Prueba activa opcional de aislamiento de caché

El modo normal no envía prompts. Existe una prueba separada que manda canarios aleatorios en parejas concurrentes para buscar marcadores cruzados:

```powershell
cd D:\ZLia
py -3 FASE1-DIAGNOSTICO.py --probe-cache
```

Solo ejecútala cuando:
- llama-server esté saludable;
- todos los slots estén libres;
- hayas cerrado CHATEAR-QWEN y cualquier otro cliente;
- nadie más esté usando el servidor.

El programa exige escribir exactamente:

```text
PROBAR_CACHE_EN_SERVIDOR_QUIETO
```

Además, comprueba /slots antes de empezar y antes de cada pareja. Si no puede verificar que todos los slots están libres o detecta uno ocupado, se niega a enviar peticiones. Esta comprobación reduce el riesgo, pero no puede impedir que otra aplicación empiece a usar el servidor justo después de la comprobación.

Interpretación:
- POTENTIAL_CONTAMINATION: apareció el marcador privado de una petición en la respuesta de la otra; señal positiva que requiere investigación.
- NO_CONTAMINATION_OBSERVED: no apareció un marcador ajeno y las respuestas permitieron evaluar el canario; no demuestra ausencia total del problema.
- INCONCLUSIVE: el modelo no devolvió suficientes marcadores propios para evaluar el resultado.
- INCONCLUSIVE_STOPPED_BUSY_OR_UNKNOWN: la prueba se detuvo por actividad o estado no verificable de slots.

La prueba es heurística, no una auditoría formal del aislamiento de slots.

## Parámetros opcionales desde consola

El doble clic ejecuta el modo seguro predeterminado. Para un muestreo más largo:

```powershell
py -3 FASE1-DIAGNOSTICO.py --sample-seconds 30 --sample-interval 1
```

Otras opciones: --sample-seconds 0, --host, --port, --output, --probe-rounds y --no-pause.

## Privacidad

Antes de compartir el ZIP, revisa las rutas locales y argumentos registrados. Se redactan API keys, HF tokens y opciones MCP habituales, pero ningún filtro puede garantizar detectar todo secreto posible. El script nunca guarda prompts del endpoint /slots.

## Limitaciones

- La telemetría detallada de procesos, RAM y contadores está pensada para Windows.
- Page Reads/sec y Pages Input/sec son contadores globales del sistema, no exclusivos de llama-server.
- Windows localizado puede usar nombres traducidos de contadores; el error queda registrado.
- La comparación de flags es textual; puede haber falsos negativos por aliases o cambios de formato de --help.
- GGUF se inspecciona solo hasta el final de los metadatos; no se valida el contenido de todos los tensores.
- La prueba activa no altera la configuración del servidor y no realiza benchmarks de velocidad.
- No se ha ejecutado contra tu PC desde GitHub; la primera ejecución real debe confirmar rutas, permisos, endpoints y disponibilidad de contadores.
