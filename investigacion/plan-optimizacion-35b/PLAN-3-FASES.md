# Plan maestro — Optimización de Qwen 3.6-35B-A3B en hardware limitado

**Estado:** Fase 1 ejecutada con salvedades documentadas; Fase 2 preparada y pendiente de capturar la línea base controlada del perfil NP2 actual.  
**Fecha de creación:** 2026-11-03  
**Hardware de referencia:** Intel Core i3-10100F (4C/8T), 16 GB DDR4-2666, NVIDIA GTX 1650 4 GB, SSD 500 GB.  
**Runtime de referencia documentado:** llama.cpp b11856, CUDA 12.4, puerto 9931.  
**Modelo de referencia:** Qwen 3.6-35B-A3B APEX-I-MINI GGUF, aproximadamente 14,27 GB.  
**Objetivo:** máxima inteligencia útil por unidad de tiempo y memoria, aumentando tokens/s solo cuando la calidad se mantiene.

---

## Principios de la campaña

1. **La integridad precede a la velocidad.** Una respuesta contaminada por otra sesión invalida cualquier benchmark.
2. **La build instalada es la autoridad de compatibilidad.** El archivo de flags permitidas del repositorio sirve como referencia; la ayuda y versión del ejecutable local determinan qué acepta realmente el runtime.
3. **Una variable por experimento.** No combinar flags antes de saber qué efecto individual tiene cada una.
4. **No confundir prefill con decode.** La velocidad de generación se toma de timings del servidor, no de fragmentos SSE ni de banners de carga.
5. **Calidad como condición de aceptación.** Una configuración más rápida que falle más tareas no es una ganadora.
6. **Reproducibilidad.** Guardar comando exacto, versión, modelo, parámetros, métricas, logs y resultado de cada prueba.
7. **No tocar producción automáticamente.** Los experimentos no editan config.txt ni reemplazan el perfil estable sin aprobación.
8. **Separar perfiles.** La configuración NP2 de producción y cualquier perfil experimental NP1 (por ejemplo, especulación) son líneas distintas; no mezclar resultados.

## Estado inicial conocido

- La configuración central documentada utiliza -ngl 99, -cmoe, contexto 16384, KV Q8/Q8, -t 4, -lm none y -np 2; además aplica -ub 1024 y -b 4096 como flags ganadoras.
- NP2 fue promovido a producción después de sesiones independientes con mediana aproximada de 21,45 tokens/s.
- El barrido anterior registró 21,50 tokens/s para -lm none.
- La caché MoE de 256 y 512 MiB fue claramente negativa en el rig (13,51 y 17,22 tokens/s frente a 20,85 de la base de aquel barrido).
- KV Q4/Q4 también fue algo más lenta que Q8/Q8 en la prueba anterior; no se debe extrapolar ese resultado a combinaciones asimétricas K/V.
- MTP del perfil probado fue más lento que la base. No se repetirá el barrido completo de MTP hasta que exista una hipótesis técnica nueva.
- Estos números son referencias históricas del repositorio, no sustituyen una nueva línea base tomada el día de la campaña.

---

# Fase 1 — Diagnóstico, integridad y huella del sistema

**Objetivo:** saber exactamente qué hardware, modelo, build, flags y distribución de memoria estamos usando antes de cambiar nada.

### 1.1 Inventario del sistema
- Capturar versión de Windows, arquitectura, CPU, núcleos/hilos y módulos de RAM.
- Capturar RAM física disponible, memoria comprometida y margen de memoria virtual.
- Capturar GPU, driver, VRAM total/usada/libre, utilización, reloj y consumo si NVIDIA SMI está disponible.
- Identificar proceso llama-server, PID, ruta, línea de comandos y working set. Redactar cualquier argumento que parezca token o clave.

### 1.2 Huella del runtime y compatibilidad
- Capturar llama-server --version y --help desde el ejecutable configurado.
- Comparar flags de FLAGS_BASE, SAMPLING y FLAGS_GANADORAS con:
  1. InformacionCritica/configs/llama-flags-nuevo.txt.
  2. La ayuda del ejecutable instalado en el PC.
- Distinguir flag reconocida, no encontrada y no verificable. No inferir que una opción produce mejoras solo porque la build la acepta.
- Registrar SHA-256 del ejecutable cuando sea razonable; no hashear el GGUF completo.

### 1.3 Huella del modelo
- Leer solo la cabecera y metadatos GGUF, sin cargar tensores ni recorrer el archivo completo.
- Extraer arquitectura, cantidad de capas, expertos, expertos usados por token, tipo de archivo y tamaño.
- Registrar el tamaño, fecha de modificación y ruta del modelo.

### 1.4 Estado del servidor y de las sesiones
- Consultar por GET /health, /slots y /metrics en localhost.
- En /slots guardar solo estado y contadores; nunca guardar prompts ni texto de conversaciones.
- Capturar proceso y comando real. Contrastar la configuración deseada con la instancia que está abierta.

### 1.5 Presión de memoria y paginación
- Tomar una muestra de RAM y VRAM durante el servidor cargado y sin solicitudes de chat.
- Capturar los contadores Windows Memory\Page Reads/sec y Memory\Pages Input/sec si el sistema los expone.
- Registrar que estos contadores son del sistema completo, no exclusivos de llama-server.
- Comparar contadores con memoria disponible, Working Set del proceso y telemetría GPU. No diagnosticar paginación a partir de la palabra pageout de un log.

### 1.6 Aislamiento de caché
- La ejecución normal no envía prompts.
- Como prueba separada y optativa, enviar pares de canarios aleatorios concurrentes para detectar si la respuesta de una petición contiene el identificador privado de la otra.
- Ejecutar solo con el servidor desocupado, sin otros clientes conectados y con confirmación interactiva.
- Cualquier marcador ajeno es una señal que exige investigación; no observar contaminación no demuestra ausencia total del problema.
- Repetir después con políticas de caché seguras. No cambiar la configuración del servidor desde el script de diagnóstico.

### Entregables
- phase1_report.md: resumen legible.
- phase1_report.json: datos estructurados.
- runtime_help.txt y runtime_version.txt: evidencia del ejecutable instalado.
- server_endpoints.json, processes.json, memory_counters.json y gpu_samples.csv.
- cache_probe.json cuando se solicita la prueba activa.
- ZIP con todos los resultados para compartir y analizar.

### Criterio de salida / puerta a Fase 2
No avanzar a experimentos de velocidad hasta:
- Identificar el ejecutable y su versión real.
- Confirmar qué flags de la configuración reconoce la build local.
- Identificar el GGUF y su arquitectura.
- Saber si hay una instancia activa y qué argumentos utiliza.
- Obtener una captura de RAM/VRAM y contadores de paginación, o documentar por qué no están disponibles.
- Revisar cualquier señal de contaminación de caché. Si aparece un marcador ajeno, la prioridad pasa a reproducir y aislar el problema, no a acelerar.

**Ejecutor preparado:** investigacion/plan-optimizacion-35b/fase1/FASE1-DIAGNOSTICO.py (v1.1.0). Para el PC, copiar únicamente este archivo como `D:\\ZLia\\FASE1-DIAGNOSTICO.py` y hacer doble clic; no requiere módulos ni archivos `.py` auxiliares. Lee primero `D:\\ZLia\\config.txt` y guarda resultados en `D:\\ZLia\\salidas\\`. Es de solo lectura por defecto; la prueba activa requiere `--probe-cache`, confirmación exacta y slots verificados como libres.

---

# Fase 2 — Descubrimiento controlado (OFAT)

**Objetivo:** medir el efecto individual de la mayoría de las técnicas candidatas con el mínimo de variables confundidas.

### Protocolo común
- Tomar una nueva línea base con el mismo modelo, runtime, prompt suite y condiciones térmicas.
- Cada variante cambia una sola variable o una sola familia estrechamente relacionada.
- Mantener constantes sampling, contexto, prompt, output tokens y cliente de benchmark.
- Usar el mismo servidor y reiniciar entre configuraciones cuando una opción solo se aplica al cargar el modelo.
- Mínimo tres repeticiones válidas por variante; descartar calentamiento y registrar fallos de carga.
- Registrar prompt processing t/s, decode t/s, TTFT, memoria RAM/VRAM, contadores de paginación y calidad.
- Guardar comando exacto, versión, logs del servidor y resultados crudos. No sobrescribir resultados anteriores.
- Rechazar combinaciones incompatibles o no reconocidas por la build local.

### Orden de investigación individual
1. Distribución parcial de expertos: -ncmoe sin -cmoe, escalera elegida según capas y VRAM observadas.
2. Distribución selectiva de tensores: -ot, solo después de identificar nombres reales de tensores y tipos de buffer admitidos.
3. Ubicación de KV: -kvo frente a -nkvo.
4. Auto-fit y capas: -ngl auto, -fit y -fit-target, documentando todos los argumentos que el runtime modifica.
5. Cuantización asimétrica K/V: combinaciones Q8/Q8, Q4/Q8, Q8/Q4, IQ4/Q8, Q8/IQ4 y Q5/Q5 si la build las admite.
6. N-gram mod: parámetros n-min, n-max y n-match.
7. N-gram simple y variantes map-k/map-k4v; cada tipo en pruebas independientes.
8. Caché y reutilización de prompt: --cache-reuse, --cache-ram y --cache-idle-slots, solo después de resolver el criterio de integridad.
9. KV unificada y contexto por slot: -kvu / --no-kv-unified y --kv-unified-per-slot.
10. Caché de búsqueda: -lcs y -lcd, con dataset repetitivo y dataset de conversación general.
11. Repack y host buffers: --repack/-nr y --no-host.
12. Checkpoints y memoria SWA: -ctxcp, -cms y --swa-full; baja prioridad y solo con margen de RAM suficiente.
13. Lazy mode: -lzm on/off, condicionado a que el GGUF y los tensores relevantes tengan sentido para esta función.
14. Revisión posterior de caché MoE: únicamente presupuestos pequeños o diferentes ubicaciones después de liberar VRAM; no repetir 256/512 MiB como candidatos ganadores.
15. Opciones del modelo borrador: solo si una variante especulativa demuestra aceptación y mejora neta; mantener NP1 separado del perfil NP2.

### Criterio de promoción de una variante
- La mejora supera el ruido observado en la línea base.
- La mediana de al menos tres ejecuciones mejora, no solo una ejecución aislada.
- No provoca presión de memoria, paging o errores nuevos.
- La calidad queda dentro del umbral acordado.
- La mejora puede repetirse con el comando exacto documentado.

---

# Fase 3 — Combinaciones, validación y promoción

**Objetivo:** descubrir interacciones entre las mejores variantes y confirmar un ganador real.

### Método
- Solo combinar opciones que hayan sido positivas o claramente neutras en Fase 2.
- Crear combinaciones por pares primero; después tríos si hay fundamento.
- No apilar opciones que controlan el mismo recurso sin evidencia (por ejemplo, dos mecanismos de caché que compitan por VRAM).
- Mantener perfiles separados para NP2 producción y cualquier ruta NP1 especulativa.
- Ejecutar al menos cinco repeticiones válidas de cada finalista, idealmente en más de una sesión.
- Comparar mediana, dispersión, peor caso y estabilidad térmica.

### Batería de calidad
- Matemáticas y aritmética verificable.
- Razonamiento multi-paso.
- Programación y depuración.
- Seguimiento de instrucciones.
- Conversación general y escritura.
- Contextos largos y recuperación de datos previos.
- Pruebas de aislamiento entre sesiones para cualquier cambio de caché/slots.

### Métrica de decisión
La métrica principal no será solo tokens/s. Se evaluará:
- Calidad y porcentaje de tareas resueltas correctamente.
- Decode tokens/s y prompt processing tokens/s.
- TTFT y tiempo total por tarea.
- RAM máxima, Working Set y presión de paginación.
- VRAM máxima y estabilidad del proceso.
- Repetibilidad entre ejecuciones.

### Promoción
- El ganador se documenta con configuración completa, build, modelo, métricas y logs.
- No se modifica la configuración central de producción automáticamente.
- Se requiere aprobación antes de sustituir NP2 o flags ganadoras.
- Los resultados negativos se conservan como conocimiento experimental y no se repiten sin una hipótesis nueva.

---

## Ranking de oportunidades que guía la campaña

Orden de interés para este hardware, no garantía de mejora:

| Orden | Técnica | Motivo principal |
|---:|---|---|
| 1 | -ncmoe | Cambia dónde se ejecuta el trabajo MoE |
| 2 | -ot / override-tensor | Distribución selectiva de tensores |
| 3 | -nkvo | Puede liberar VRAM para pesos |
| 4 | -ngl auto / -fit-target | Descubre una colocación viable |
| 5 | KV asimétrica -ctk/-ctv | Reduce memoria con menor compresión selectiva |
| 6 | ngram-mod | Especulación sin un borrador grande |
| 7 | -kvu / --no-kv-unified | Organización del pool KV entre slots |
| 8 | --kv-unified-per-slot | Presupuesto explícito de contexto |
| 9 | --cache-ram / --no-cache-idle-slots | Integridad y control de RAM |
| 10 | --cache-reuse | Evita reprocesar prefijos comunes |
| 11 | ngram-simple | Especulación por patrones repetidos |
| 12 | ngram-map-k / ngram-map-k4v | Otras estructuras de búsqueda especulativa |
| 13 | -lcs / -lcd | Caché de búsqueda |
| 14 | --repack / -nr | Reorganización de pesos |
| 15 | --no-host | Explorar buffers alternativos |
| 16 | --moe-cache-mib | Ya dio resultados negativos; solo reabrir con VRAM liberada |
| 17 | Ajustes de draft | Solo si especulación vuelve a ser rentable |
| 18 | -ctxcp / -cms | Checkpoints de contexto |
| 19 | --swa-full | Potencial coste alto de memoria |
| 20 | -lzm | Condicionado a tensores y comportamiento del GGUF |

## Referencias internas del proyecto
- Configuración central: InformacionCritica/configs/config.txt
- Dump de flags permitidas: InformacionCritica/configs/llama-flags-nuevo.txt
- Informe del barrido: InformacionCritica/docs/informe-velocidad-sweep.md
- Script de diagnóstico: InformacionCritica/scripts/diagnostico-velocidad.py
- Plan de Niveles: investigacion/niveles-velocidad/


---

# Bitácora de ejecución — 3 de noviembre de 2026

## Cierre de Fase 1

Se recibieron dos paquetes del equipo local:

1. Primera captura: el servidor no estaba iniciado. Sirvió para verificar rutas, modelo, metadatos GGUF y build sin cargar el modelo.
2. Segunda captura: el servidor estaba cargado y saludable. Esta es la línea base de estado del sistema, no todavía una medición de velocidad.

### Estado real observado en la segunda captura

- Windows 11, Python 3.14.4.
- llama.cpp: build 11856, commit 3642238cc.
- Modelo: GGUF Qwen 3.6-35B-A3B APEX-I-MINI, 14.273.277.376 bytes; arquitectura GGUF `qwen35moe`, 41 bloques, 256 expertos y 8 expertos usados por token.
- Proceso vivo: `D:\\llama.cpp\\llama-server.exe`, PID 15036.
- Perfil en ejecución: `-ngl 99 -cmoe -c 16384 -np 2 -ctk q8_0 -ctv q8_0 -t 4 -lm none`, con `-ub 1024 -b 4096` al final (last-wins).
- `/health`: HTTP 200. `/slots`: dos slots de 8.192 tokens, ambos libres.
- `/metrics`: HTTP 501 (endpoint no implementado en esta build).
- RAM física disponible: 0,453 GiB; carga informada: 97%; Working Set de llama-server: 11.136.299.008 bytes (~10,37 GiB).
- GTX 1650: 2.149 MiB VRAM usados de 4.096 MiB durante reposo.

### Salvedades y correcciones

- El contador de Windows `Page Reads/sec` / `Pages Input/sec` no estuvo disponible: PowerShell devolvió que el objeto no existe. No se interpreta como cero paginación; queda como limitación de telemetría del sistema.
- El dump `llama-flags-nuevo.txt` es UTF-16. El lector anterior lo interpretó como UTF-8 y produjo un falso cero en el conteo del dump. El ejecutor se corrigió a v1.1.1 para detectar UTF-8/UTF-16. Independientemente de ese fallo de lectura, la ayuda local de b11856 reconoció las 18 flags configuradas y no encontró ninguna ausente.
- La prueba activa de canarios de caché no se ejecutó. La revisión de configuración sigue marcada como pendiente de aislamiento; no hay evidencia de contaminación en estas capturas, pero tampoco una prueba que la descarte.
- La RAM libre observada es demasiado baja para benchmarks fiables. No iniciar pruebas de variantes con menos de 1,5 GiB disponibles.

**Criterio de salida:** Fase 1 queda **completada con salvedades**. La build, el modelo, las flags activas, el servidor y el estado de slots están identificados. La telemetría de paginación está documentada como no disponible y la prueba de caché se mantiene diferida. No cambiar la configuración de producción.

## Entrada a Fase 2 — línea base controlada

Primer ejecutor: `InformacionCritica/scripts/diagnostico-velocidad.py` v1.2.

- Mantiene el servidor vivo; no reinicia procesos ni cambia `config.txt`.
- Certifica la receta activa a partir de la línea de comandos del proceso.
- Envía cuatro solicitudes secuenciales al endpoint `/completion`, 256 tokens cada una, temperatura 0 y seed fija; registra prefill de la primera y media decode de las pasadas 2–4.
- Comprueba `/slots` antes de cada solicitud y aborta si no puede verificar que todos estén libres.
- En Windows exige al menos 1,5 GiB de RAM física disponible antes de enviar prompts.
- Instrucción operativa: cerrar aplicaciones de alto consumo, mantener Qwen cargado, dejar el chat sin actividad durante la medición y no iniciar otra aplicación cliente.

Salida: `RUTA_LOGS\diagnostico-AAAAMMDD-HHMMSS.md`, normalmente bajo `D:\\ZLia\\faseD-logs\\`.

La captura actual (0,453 GiB libres) no pasa el umbral. La siguiente medición solo será válida cuando el preflight confirme ≥1,5 GiB y ambos slots estén libres.

## Reutilización de evidencia histórica

Antes de repetir experimentos, se deben tener presentes los datos documentados en `InformacionCritica/docs/informe-velocidad-sweep.md` y `investigacion/niveles-velocidad/nivel-1-recorte-expertos-resumen.md`:

- `-lm none`, `-t 4`, MTP y `--moe-cache-mib` ya tienen resultados históricos en el equipo. No repetir sin hipótesis nueva.
- El barrido histórico reportó 21,50 t/s con `-lm none`, 20,85 t/s para su BASE, pérdidas con las dosis MoE-cache de 256/512 MiB, y MTP por debajo de la base en aquel perfil.
- La campaña Nivel 1 documenta experimentos de `expert_used_count`, `-ncmoe` y `-ot`, pero se deben conservar sus límites de comparabilidad frente al perfil NP2 actualmente abierto y no mezclar medias entre protocolos distintos.
- La Fase 2 de esta campaña debe priorizar variables todavía no resueltas y perfiles comparables con NP2; cada variante debe cambiar una sola variable, tener al menos tres repeticiones válidas y conservar logs/resultados crudos.

**Siguiente puerta:** línea base NP2 nueva y limpia. Solo después de revisarla se selecciona el primer experimento OFAT; no se lanzará un barrido amplio a ciegas.
