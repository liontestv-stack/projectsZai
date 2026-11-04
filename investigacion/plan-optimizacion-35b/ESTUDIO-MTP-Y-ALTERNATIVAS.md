# Estudio MTP y alternativas de speculative decoding para Qwen3.6-35B-A3B APEX-I-MINI

**Fecha de corte:** 4 de noviembre de 2026  
**Estado:** investigación y preparación; NO autorizado para producción.  
**Perfil prioritario:** K=8, calidad/capacidad intactas.  
**Runtime local:** llama.cpp b11856, CUDA 12.4, Windows, GTX 1650 4 GB.  
**Modelo local:** Qwen3.6-35B-A3B Uncensored Heretic + MPOA, APEX-I-MINI GGUF, aproximadamente 14,27 GB.

---

## 1. Decisión ejecutiva

MTP merece una investigación específica porque el GGUF local se publicó como variante **Native-MTP-Preserved** y el código de llama.cpp b11856 contiene un camino MTP para `qwen35moe`. Sin embargo, **no debemos activar MTP en producción todavía**.

Hay tres bloqueos técnicos que obligan a preparar primero la comprobación:

1. Existe un reporte de `draft-mtp` que inicializa pero no llega a producir estadísticas ni tokens aceptados en una GTX 1650 SUPER de 4 GB (Turing, sm_75) con Qwen3.6-35B-A3B híbrido. No es el mismo Windows/build/GPU exacto del rig, por lo que es una señal de riesgo, no una prueba de que nuestro equipo falle.
2. A fecha de corte sigue abierto un informe de divergencia de salida en el camino de verificación por lotes de `qwen35moe`: afecta a DFlash/DSpark y el autor informa que un mecanismo MTP independiente también muestra la misma firma. La reproducción publicada usa Qwen3.5-35B-A3B y build más reciente que b11856, no nuestro GGUF; aun así, es suficientemente cercano para exigir una puerta de corrección antes de adoptar speculative decoding.
3. MTP se debe probar en una rama de **NP1**, no mezclarse con la receta de producción NP2. Los informes upstream también registran problemas de aceptación bajo múltiples slots y lotes con varias ubatches.

**Orden recomendado:** verificar metadata/tensores MTP del GGUF local → auditar el ejecutable b11856 y su CUDA/GPU → preparar benchmark aislado NP1 con línea base sin draft → probar activación y aceptación MTP n=2 → solo si supera las puertas técnicas, comparar sidecars DFlash y DSpark. K=8 se mantiene fijo.

La meta no es acelerar a costa de menos expertos ni de respuestas alteradas. Speculative decoding solo puede ser candidato ganador si demuestra mejora neta y conserva la distribución/calidad del modelo objetivo en las pruebas acordadas.

---

## 2. Equipo y restricciones reales

| Recurso | Dato confirmado | Implicación para la prueba |
|---|---|---|
| CPU | Intel Core i3-10100F, 4C/8T | Un draft ejecutado completamente en CPU podría competir por los mismos cuatro núcleos con el verificador. |
| RAM | 16 GB DDR4-2666 | El informe del 04-nov dejó 0,64 GB libres con Qwen cargado; vigilar commit, paginación y RAM libre durante todo el ensayo. |
| GPU | NVIDIA GTX 1650, 4 GB | El modelo utilizó 2.213 MiB de VRAM en reposo en la última captura; ese número no incluye la carga adicional de cada draft/contexto. |
| Disco | SSD 500 GB | Hay espacio para sidecars pequeños, pero no se debe descargar un modelo draft denso grande sin justificarlo. |
| Runtime | llama.cpp b11856, CUDA 12.4 | Las opciones del dump local y el comportamiento real de este ejecutable prevalecen sobre documentación de builds nuevos. |

La captura de reposo deja nominalmente alrededor de 1,8 GiB de VRAM libre, pero **no equivale a presupuesto utilizable garantizado**: los buffers de cómputo, KV, contexto especulativo y fragmentación pueden consumirlo. No se aprueba un draft por su tamaño de archivo solamente.

### Dato de hardware pendiente

Registrar el nombre completo que devuelve `nvidia-smi`, versión del driver y la salida de `llama-server.exe --list-devices`. Necesitamos distinguir GTX 1650, 1650 D6 y variantes de placa; el reporte de riesgo principal es de GTX 1650 SUPER, no exactamente el mismo SKU del rig.

---

## 3. Qué sabemos del GGUF objetivo

El archivo local coincide por nombre y tamaño aproximado con el artefacto APEX-I-MINI del repositorio de SC117. La ficha del repositorio describe el modelo como Qwen3.6-35B-A3B, Heretic + MPOA, 256 expertos enrutados y 8 activos por token, y recomienda `--spec-type draft-mtp --spec-draft-n-max 2`. Es una recomendación del autor, no una garantía de rendimiento en una GTX 1650.

**Ambigüedad de metadata que debemos resolver localmente:** la misma ficha dice en una sección que se preservaron “20 MTP layers”, pero en su tabla de detalles describe “40 transformer layers + 1 MTP layer”. El código de llama.cpp b11856 para Qwen35MoE exige `n_layer_nextn > 0` y afirma que actualmente solo soporta un bloque MTP. Por tanto, no vamos a interpretar el texto “20 MTP layers” como veinte bloques especulativos: hay que leer el GGUF real.

La inspección local debe registrar, como mínimo:

- `general.architecture` (esperado: `qwen35moe`).
- `qwen35moe.nextn_predict_layers` o la metadata equivalente que exponga el GGUF.
- Existencia y nombres de los tensores `nextn.*` / cabeza MTP.
- Número, tipos y bytes de esos tensores.
- Resultado del cargador b11856 al construir el contexto MTP.

El parser de Fase 1 leyó la cabecera GGUF y detectó la arquitectura `qwen35moe`, 41 bloques y 753 tensores, pero el informe compartido no incluyó el detalle de `nextn.*`. Ese dato sigue pendiente; no inventarlo.

---

## 4. Qué soporta realmente llama.cpp b11856

No debemos repetir la conclusión antigua de que b11856 no reconoce MTP/DFlash/DSpark. La inspección del código exacto del tag b11856 y del dump de ayuda local confirma que el registro de tipos incluye:

- `draft-mtp`
- `draft-dflash`
- `draft-dspark`
- `draft-eagle3`
- `ngram-simple`, `ngram-map-k`, `ngram-map-k4v`, `ngram-mod`, `ngram-cache`

El archivo de ayuda local también muestra `--spec-type`, `--spec-draft-n-max`, `--spec-draft-n-min`, `--spec-draft-p-min`, `--spec-draft-device` y `--spec-draft-ngl`. En el dump b11856, `n-max` tiene default 3 y `p-min` default 0.00; la ficha APEX recomienda n-max 2. En nuestros ensayos fijaremos los valores explícitamente para no depender de defaults.

**Distinción importante:** que el parser reconozca un tipo no demuestra que el GGUF sidecar sea compatible, que el draft se active o que la generación sea correcta/rápida. Cada etapa tiene un autenticador independiente.

Fuentes de código:
- `common/speculative.cpp` en tag b11856: registro de tipos y creación del contexto especulativo.
- `src/models/qwen35moe.cpp` en tag b11856: graph MTP de Qwen35MoE; exige un bloque NextN.
- PR #22673 (MTP) fue integrado upstream el 16-may-2026.
- PR #26275 (soporte de checkpoints DSpark en formato Speculators) fue integrado el 17-ago-2026, antes de b11856. Algunas fichas de sidecars todavía muestran advertencias de compatibilidad que pueden haber quedado desactualizadas.

---

## 5. Riesgos técnicos que mandan el orden

### 5.1 Reporte Turing / MTP que no se activa

El issue llama.cpp #24670 describe Qwen3.6-35B-A3B híbrido en GTX 1650 SUPER 4 GB (Turing sm_75): el contexto `draft-mtp` se inicializaba, pero tras más de 800 tokens no aparecía `statistics draft-mtp`, no se observaba aceptación y el rendimiento era igual al modo sin MTP. El autor sospechó una diferencia de estado recurrente SSM entre el contexto principal y el contexto draft.

El issue se cerró como stale/not planned el 9-oct-2026, no como una corrección verificada. Nuestro runtime es más nuevo (b11856), Windows y CUDA 12.4, y nuestra GPU es GTX 1650 no confirmada como SUPER; por eso no asumimos el mismo resultado. Sí establecemos como condición obligatoria comprobar estadísticas reales de draft, no solo que el servidor diga “MTP initialized”.

En el código b11856, la creación del contexto MTP fija `n_rs_seq = 0`. El modelo implementa el bloque MTP como bloque denso de atención, de modo que no declaramos automáticamente que sea un bug; lo contrastaremos contra logs y comportamiento del rig.

### 5.2 Verificación por lotes / fidelidad del target

El issue llama.cpp #31472, abierto el 31-oct-2026 y aún abierto al corte, informa divergencias de salida en el camino speculative de `qwen35moe`: salidas distintas de autoregressive incluso cuando se aceptaron todos los tokens draft en su batería a temperatura 0. El autor acota el origen al forward de verificación por lotes y amplificación de pequeñas diferencias numéricas en el router MoE. Informa la misma firma con DFlash, DSpark y un mecanismo MTP independiente.

La reproducción publicada usa Qwen3.5-35B-A3B y un commit posterior a b11856; no prueba que nuestro APEX-Qwen3.6 falle. Sí significa que no aceptaremos una “ganancia” de t/s con una verificación de calidad superficial. Primero compararemos el modo autoregressive y el speculative en una batería congelada, incluida una comprobación determinista separada y tareas funcionales.

### 5.3 NP1 y concurrencia

La línea de investigación MTP se separa de producción NP2. En el issue #27572 se reportó que, bajo `-np N` y varias ubatches, la aceptación MTP podía caer a cero por una carrera en la transferencia del tensor de hidden state; el caso reproducido era AMD/HIP y un build posterior, así que no lo extrapolamos como fallo cierto de NVIDIA. El issue #24320 documenta también la carga de memoria recurrente asociada a slots múltiples.

Regla del estudio: **NP1 explícito para todos los brazos MTP y sus controles**, un solo cliente durante la medida. Si posteriormente se quisiera estudiar NP2+MTP, sería otro experimento de compatibilidad independiente y no parte de la primera fase.

### 5.4 Prefill y coste del draft

El PR de MTP upstream advierte que el prompt processing puede sufrir una penalización por transferencias de embeddings device-to-host. Por tanto, no mediremos solo decode t/s: también prefill, TTFT y tiempo total por turno. Un MTP que acelera el decode, pero empeora el tiempo total habitual, no gana.

---

## 6. Candidatos: orden de interés para este hardware

| Candidato | Requisito | Valor potencial | Riesgo / prioridad |
|---|---|---|---|
| **MTP nativo del GGUF** | Cabeza NextN embebida; `--spec-type draft-mtp` | Primera prueba por ser parte del mismo GGUF y no requerir sidecar descargado | **Primero en activación-smoke**, pero riesgo Turing/SSM y verify-path. NP1 explícito. |
| **DFlash** | GGUF draft externo + `draft-dflash` | Alternativa muy interesante si pasa la puerta de fidelidad. Un benchmark público sobre otro hardware/modelo reporta buen resultado en tareas previsibles | Requiere VRAM/compute adicional; el target exacto de ese benchmark no es nuestro fine-tune. Bloqueado hasta aclarar verify-path. |
| **DSpark Q4_K_M** | Sidecar GGUF ~307 MB + `draft-dspark` | Tamaño nominal pequeño; incluye cabeza de confianza/Markov y puede ser candidato para VRAM limitada | Se entrenó contra Qwen3.6 base, no nuestro Heretic/APEX. Bench público reporta resultados variables y negativos en agregado frente a no-spec. Bloqueado por el mismo riesgo de verify-path. |
| **EAGLE-3 Caption** | Sidecar GGUF ~517 MB + `draft-eagle3` | Existe un draft para esta familia | Entrenado para captions COCO en inglés; probable desajuste con chat ES/código. Fallback de baja prioridad. |
| **N-gram** | Sin sidecar; patrones repetidos | Menor memoria; útil en código/JSON/texto repetitivo | No es reemplazo universal de MTP; el histórico del proyecto lo considera flojo en chat libre. Solo workloads de baja entropía. |
| **Draft denso pequeño** | Modelo auxiliar completo | En teoría una cabeza auxiliar externa | El coste de un forward adicional puede comerse la ganancia; proyecto lo mantiene NO-GO tras resultados negativos externos. No priorizar. |

### Evidencia externa no transferible

Un benchmark público de Qwen3.6-35B-A3B con su propio hardware, target y prompts reporta DFlash n-max 7 como mejor agregado (+18% frente a su baseline), mientras DSpark n-max 2/3/5 queda por debajo de no-spec en agregado; recomiendan DSpark n-max 3 solo como preset general de esa prueba y desactivar speculative para traducción, escritura creativa y explicaciones largas. No se copiarán sus cifras a nuestro equipo ni adoptaremos n-max 7 sin medir: solo orientan qué candidatos merecen un A/B.

El sidecar DSpark Q4_K_M publicado tiene aproximadamente 307 MB, pero ese tamaño no incluye los buffers de runtime. El repositorio declara como target Qwen/Qwen3.6-35B-A3B vanilla; nuestra variante APEX es una derivación Heretic + MPOA y puede tener una aceptación distinta.

---

## 7. Preparación experimental segura

### Etapa 0 — Preflight sin iniciar ni tocar producción

1. Obtener `llama-server.exe --version`, SHA256 y `--help` real del equipo.
2. Guardar el nombre exacto de GPU, driver y `--list-devices`.
3. Inspeccionar la metadata GGUF completa relevante: `general.architecture`, `nextn_predict_layers`, tensores NextN y tipos/tamaños.
4. Confirmar la receta de producción intacta: K=8, NP2 y sus flags; guardar copia/hash del config.
5. No descargar sidecars hasta completar esta etapa.

**Salida:** informe preflight con evidencia suficiente para saber si el MTP nativo está efectivamente presente y qué dispositivo puede ejecutar el draft.

### Etapa 1 — Smoke de activación MTP

1. Apagar manualmente la instancia de producción antes del ensayo; no usar una rutina que mate procesos por nombre.
2. Usar puerto de laboratorio separado (por ejemplo 9932) y un único proceso llama-server.
3. Ejecutar el modelo objetivo con K=8, misma receta restante, **NP1 explícito** y `--spec-type draft-mtp --spec-draft-n-max 2`. Fijar `--spec-draft-p-min` explícitamente tras comprobar ayuda local.
4. Generar una salida suficientemente larga y comprobar en el log estadísticas MTP con intentos/aceptaciones no nulos.
5. Si no hay actividad de draft, clasificar `MTP_NOT_ACTIVATED`; no calcular speedup ni continuar con barridos de n-max.
6. Registrar RAM/VRAM antes, durante y después de prompt processing y decode.

**Salida:** PASS/FAIL de activación, no benchmark de ganador.

### Etapa 2 — Comparación controlada MTP vs no-spec

Solo si Etapa 1 activa el draft:
- Baseline NP1 sin speculative y MTP NP1, misma build, GGUF, flags, contexto, temperatura, prompt y cantidad de tokens.
- Usar el perfil sampling real (temperature 1.0 / top-k 20 / top-p 0.95) para la comparación principal. Añadir una batería determinista separada como diagnóstico de fidelidad, no como sustituto del perfil real.
- Mínimo tres repeticiones independientes por configuración, mismos prompts y orden equilibrado; medir prefill, decode, TTFT, coste total del turno, aceptación real, RAM y VRAM.
- No inferir aceptación desde t/s; leer las estadísticas del log del server.
- Calidad: chat ES, razonamiento, matemática verificable, código, instrucciones y tool-calling. Registrar fallos, respuestas incompletas y divergencias relevantes.
- Rechazar cualquier modo con aceptación N/D, estadísticas ausentes, corrupción, crashes, pérdida de capacidades o mejora solo de decode que no mejore el tiempo de turno.

### Etapa 3 — Sidecars (solo si el camino de verificación queda validado)

Orden inicial:
1. DFlash n-max 2 como primer sidecar A/B; estudiar n-max 3 solo si n=2 es correcto y positivo.
2. DSpark Q4_K_M n-max 2/3 como comparación secundaria.
3. EAGLE-3 solo si los anteriores fallan y hay una razón de dominio para probarlo.

Para cada sidecar:
- Verificar archivo, SHA256, metadata y tokenizer/vocab contra target.
- Mantener NP1; no combinar draft types en el primer A/B.
- Verificar que el sidecar se cargó y que hubo drafting/acceptance real.
- Medir VRAM total y picos de memoria, no solo el tamaño del GGUF.
- Repetir la batería de fidelidad y calidad.

### Etapa 4 — Decisión

Un candidato solo puede promocionarse si:
- el draft está activado y las métricas de aceptación son válidas;
- la mediana de al menos tres corridas mejora el tiempo total de turno, no solo decode;
- no hay señales de divergencia/corrupción ni regresión de calidad;
- RAM/VRAM y estabilidad tienen margen;
- el resultado se reproduce en otra sesión.

La producción NP2 K=8 permanece intacta mientras tanto. La rama de speculative es un perfil experimental alternativo NP1.

---

## 8. Auditoría del instrumento MTP existente

El archivo actual `InformacionCritica/scripts/tester-mtp.py` v1.1 **no debe ejecutarse todavía como protocolo de laboratorio** sin una revisión previa:

- Su `BASE_FLAGS_LAUNCHER` no fija `-np 1`; debe añadirse explícitamente en una versión de prueba nueva y ambos brazos (no-spec y MTP) deben compartirlo.
- La batería compacta usa temperatura 0 para parte de sus pruebas, mientras que la receta de producción del usuario usa temperature 1.0. Se necesitan brazos separados: sampling de producción para rendimiento y una batería determinista independiente para diagnóstico.
- La opción `--si` cierra un servidor vivo antes de medir. No se usará con la instancia de producción. La nueva herramienta debe negarse a terminar procesos ajenos y trabajar solo con un puerto/perfil de laboratorio declarado.
- No basta con una línea de “MTP context created”; el informe debe demostrar actividad efectiva y aceptación distinta de cero, además del tiempo total.
- Los resultados históricos del proyecto anotan 16,6–18,9 t/s en pruebas MTP frente a ~21 t/s de la base K=8, pero antes de reabrir la conclusión hay que re-auditar sus logs para confirmar si el draft realmente se activó y que las comparaciones usaron el mismo protocolo.

**No ejecutar ahora** `tester-mtp.py --protocolo --si`. Primero preparar la versión aislada con NP1 explícito y no destructiva.

---

## 9. Qué NO haremos

- No añadir flags speculative a `D:\ZLia\config.txt` de producción.
- No cambiar NP2 de producción para “probar suerte”.
- No reducir K de 8 como vía principal.
- No descargar todos los drafts ni ocupar VRAM antes del preflight.
- No asumir que 20–50% de speedup anunciado en una model card aplica a GTX 1650 + i3-10100F + 16 GB RAM.
- No aceptar estadísticas de aceptación por sí solas como prueba de fidelidad.
- No iniciar un benchmark largo si el smoke test muestra que el draft no se activa.

---

## 10. Referencias consultadas

### Fuente del modelo local
- [SC117 APEX MTP GGUF — README del modelo](https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF/blob/main/README.md)
- [Archivo APEX-I-MINI en el repositorio](https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF/tree/main)

### llama.cpp
- [Release/tag b11856](https://github.com/ggml-org/llama.cpp/releases/tag/b11856)
- [MTP support PR #22673](https://github.com/ggml-org/llama.cpp/pull/22673)
- [DSpark Speculators-format support PR #26275](https://github.com/ggml-org/llama.cpp/pull/26275)
- [Issue #24670 — MTP no activa en GTX 1650 SUPER / Qwen3.6 híbrido](https://github.com/ggml-org/llama.cpp/issues/24670)
- [Issue #27572 — aceptación MTP con -np N y múltiples ubatches](https://github.com/ggml-org/llama.cpp/issues/27572)
- [Issue #24320 — coste de n_rs_seq y slots múltiples](https://github.com/ggml-org/llama.cpp/issues/24320)
- [Issue #31472 — divergencia speculative en el verify por lotes de qwen35moe](https://github.com/ggml-org/llama.cpp/issues/31472)

### Sidecars
- [Qwen3.6-35B-A3B DSpark GGUF y benchmark público](https://huggingface.co/williamliao/Qwen3.6-35B-A3B-DSPARK-GGUF)
- [DFlash oficial z-lab](https://github.com/z-lab/dflash)

---

## 11. Próxima acción concreta

Preparar un **preflight local de MTP** que lea el GGUF sin cargar todos sus tensores, capture la GPU/driver y audite `llama-server --version/--help`. Entregar JSON + Markdown y no iniciar el servidor, no matar procesos, no modificar config ni descargar sidecars.

Cuando ese preflight confirme los datos, crear el ejecutor de smoke test NP1 con puerto de laboratorio y protecciones no destructivas. La primera decisión será simplemente: ¿MTP se activa de verdad en esta GTX 1650 con b11856?
