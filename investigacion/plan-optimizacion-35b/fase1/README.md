# Fase 1 — Diagnóstico

Este directorio contiene un ejecutor único para recopilar la evidencia inicial antes de modificar el runtime o probar optimizaciones.

## Ejecutable

- FASE1-DIAGNOSTICO.py

Requisitos: Windows 10/11, Python 3.8 o superior y el runtime/modelo que se quiera inspeccionar. El script usa solo la biblioteca estándar de Python. No requiere pip ni paquetes externos.

## Ejecución recomendada

1. Actualiza o clona el repositorio en el PC donde está instalado Qwen.
2. Deja llama-server cargado pero sin conversaciones activas para obtener una captura real de memoria/VRAM.
3. Abre una consola en esta carpeta.
4. Ejecuta:

   py -3 FASE1-DIAGNOSTICO.py

La captura predeterminada dura aproximadamente 12 segundos para los contadores y la GPU. Puede tardar más por las consultas WMI/PowerShell y la lectura de ayuda del ejecutable.

El script busca config.txt en InformacionCritica/configs/config.txt y en D:\ZLia\config.txt. Busca también el dump de flags del repositorio y sus ubicaciones habituales en D:\ZLia.

## Qué hace en modo normal

- Lee config.txt sin modificarlo.
- Consulta llama-server --version y --help; estas opciones finalizan sin cargar el modelo.
- Compara flags de la configuración con el dump permitido y con la ayuda del ejecutable instalado.
- Lee solo la cabecera y los metadatos GGUF; no recorre tensores ni calcula un hash del modelo completo.
- Inspecciona el proceso llama-server y su línea de comandos; redacta argumentos que parezcan claves/tokens.
- Consulta por GET /health, /slots y /metrics en localhost. En /slots conserva solo estados/contadores, nunca prompts.
- Captura memoria física, contadores de paginación y muestras NVIDIA SMI cuando están disponibles.
- Crea un informe Markdown, un JSON estructurado, datos auxiliares y un ZIP.

No inicia, detiene ni reinicia el servidor. No cambia flags, configuración, slots ni propiedades.

## Prueba activa opcional de aislamiento de caché

Primero ejecuta el modo normal. Después, solo si el servidor está completamente desocupado y ningún cliente lo está usando, puedes ejecutar:

   py -3 FASE1-DIAGNOSTICO.py --probe-cache

El script solicitará escribir exactamente:

   PROBAR_CACHE_EN_SERVIDOR_QUIETO

La prueba envía dos solicitudes cortas y concurrentes por ronda, con identificadores aleatorios distintos. No la ejecutes si estás chateando, si hay otra persona conectada o si el servidor está atendiendo trabajo.

Interpretación:
- POTENTIAL_CONTAMINATION: se detectó el identificador de una petición dentro de la respuesta de la otra. Es una señal positiva que requiere conservar el ZIP e investigar.
- NO_CONTAMINATION_OBSERVED: no se vio contaminación en esas rondas; no demuestra que el problema sea imposible.
- copy_misses: el modelo no copió exactamente su propio marcador; es inconcluso, no una prueba de contaminación.

La prueba no es una auditoría formal del aislamiento de slots. No sustituye una reproducción determinista ni una revisión del código fuente de la build.

## Opciones

- --sample-seconds 0: no toma muestras temporales de contadores/GPU.
- --sample-seconds 30: extiende la captura (máximo 60 segundos).
- --sample-interval 1: intenta muestrear cada segundo.
- --host 127.0.0.1 --port 9931: cambia el destino local de los endpoints.
- --output RUTA: guarda los resultados en otra carpeta.
- --probe-rounds 5: hasta cinco rondas en la prueba activa.

## Archivos que debes compartir para el análisis

Comparte el ZIP FASE1_<fecha>.zip generado junto al informe. Antes de compartirlo, revisa que las rutas locales y los argumentos de proceso no contengan información privada. Las claves/tokens comunes se redactan automáticamente, pero ningún filtro puede garantizar que detecte toda información sensible.

## Limitaciones conocidas

- La telemetría de memoria y procesos está implementada para Windows.
- Los contadores Page Reads/sec y Pages Input/sec son globales del sistema, no exclusivos de llama-server.
- En Windows localizado, Get-Counter puede necesitar nombres de contadores traducidos; el error quedará registrado.
- La comparación de flags es textual y puede necesitar revisión si el formato de --help cambia.
- La cabecera GGUF informa metadatos, pero no valida el contenido de todos los tensores.
- El script no realiza benchmarks de tokens/s. Eso pertenece a las fases 2 y 3.
