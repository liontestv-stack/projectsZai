# NIVEL 3 — EFICIENCIA SIMPLE (flags, cache, colocación: sin descargar nada)

Proyecto APEX-I-MINI / Qwen3.6-35B-A3B | Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB
Fecha: 2026-10-26 | Investigación profesional profunda | Nivel 3 de 3 ("mejorar eficiencia sin complicar")

Etiquetas: **[F]** = verificado en fuente externa (URL abajo) · **[M]** = medido en ESTE rig (barrido-30, 37 configs) · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy

---

## 0. Veredicto ejecutivo

Lo simple está **casi cosechado**. De 37 configs medidos [M], solo 3 movieron la aguja al alza, y uno ya vive en el launcher:

| Ganador medido [M] | Flags | Efecto |
|---|---|---|
| **ORO-UB1K** (en launcher v2.1) | `-ub 1024 -b 4096` | prefill 45.5 → **57.56 t/s (+26.5%)**, decode intacto 21.55 |
| **NCM37C4** | `-ncmoe 37 -c 4096 -ctk q4_0 -ctv q4_0` | decode 21.53 → **22.49 (+4.4%)** (paga: ctx 4096 + KV q4_0) |
| **FIT-A** | `-ngl auto -ncmoe 34 -fitt 256` | decode **22.40 (+4.0%)** (el auto-fit decide cuántas capas de expertos suben a GPU) |

Y el gran pendiente de este nivel no es decode sino **TTFT en uso real**: en arquitecturas híbridas como la de este modelo (30 capas recurrentes Gated DeltaNet + 10 de atención), la reutilización de prompts tiene un comportamiento especial documentado en llama.cpp (#21831: el re-procesado completo de prompts es "exclusivo de arquitecturas híbridas qwen35moe/gemma4moe") [F]. Configurarlo bien evita re-pagar el prefill en cada turno de chat.

**Techo honesto del Nivel 3**: +5–9% decode (combinando ganadores) + TTFT/prefill mucho mayores en chat real [M+T]. La potencia está en los Niveles 1 y 2; este nivel es pulir.

---

## 1. Presupuesto de tiempo de un turno (dónde se va el tiempo) [M]

Del ancla ANCHOR-B [M]: carga 34.3 s (una vez por sesión) · prefill cold 293 tokens a 45.5 t/s (6.4 s) · prefill medio (con overheads) 28.7 t/s · decode 256 tokens a 21.53 t/s (11.9 s).

Un turno típico de chat corto ≈ 18–20 s: **~35% prefill + ~65% decode**. Con un system prompt grande o conversación larga, el prefill domina — y ahí es donde UB1K (+26.5%) y la cache de prompts (§3) juegan. Concluir que "solo importa el t/s de decode" es el error clásico: en uso real, TTFT es la mitad de la experiencia [T].

## 2. Los 37 configs, clasificados (para no volver a pisar lo mismo) [M]

| Familia | Configs | Resultado | Lectura |
|---|---|---|---|
| ANCLA | ANCHOR-B / ANCHOR-VJ | 21.53 / 21.43 | base estable (VJ: primera sesión fría, −5% por warm-up del SO) |
| EXP (recorte) | EXP10/8/6/5/4 | 21.3–21.5 (plano) | **no-op**: clave override equivocada (`qwen3moe.*` vs arch real `qwen3_5_moe`) → renace como Nivel 1 |
| FIT/NCM (colocación) | FIT-A 22.40 · FIT-B 21.98 · FIT-C 13.25 · NCM38 21.67 · NCM39 21.30 · NCM39Q8 21.61 · **NCM37C4 22.49** | FIT-A y NCM37C4 ganan; FIT-C colapsa (el fit se pasó de margen y desbordó a RAM lenta) | la colocación de las últimas capas de MoE en GPU es real pero fina: margen de ±256 MiB decide entre +4% y −38% |
| AFINIDAD CPU | CR03 14.51 · CMASK55 19.48 · STRICT 13.37 · STRICT55 19.36 · CR14 16.37 | **PÉSIMO: −9% a −38%** | fijar hilos a núcleos en Windows 10 DAÑA (el scheduler ya lo hace mejor; el pinning impide migrar fuera de interrupciones) — cerrado con datos |
| PRIORIDAD/POLL | PRIO3 21.41 · PRIO0 21.47 · POLL80 20.69 · POLL20 21.32 | ruido | `--prio 2` (high) ya era el óptimo; el polling default está bien |
| BUFFERS/KV | KVQ51 21.43 · REPACKOFF 20.41 · NOHOST 21.41 · LMDIO 21.38 | KV q5_1 = 0% vs q8_0; repack off −5% | repack de pesos AVX2 sí ayuda: no tocar; `-lm dio` no cambia load_s medible |
| ORO | **UB1K 57.56 prefill** · CRAM512 21.57 · SHIFT 21.39 · NOWARM load 32.8s · NGRAMS 18.09 · NGRAMM 20.70 | UB1K campeón prefill; CRAM512 seguro (libera 7.7 GB de cache-RAM default sin tocar decode); ngram spec MUERTO (acceptance 0.00–0.16) | el draft por n-gramos no funciona en este modelo/uso: no reintentar |

## 3. La joya pendiente: cache de prompts en un modelo HÍBRIDO (GDN) [F]

### 3.1 El problema específico de este modelo

Qwen3.6-35B-A3B = 30 capas recurrentes (Gated DeltaNet) + 10 de atención. El estado recurrente **no se puede truncar arbitrariamente**: no hay "historial por token" que cortar, hay un estado que se reescribe [F particula.tech/llama.cpp source]. Consecuencia documentada: el server puede lanzar **"forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory)"** y re-pagar TODO el prompt [F issue #21831 — "exclusivo de arquitecturas híbridas (qwen35moe, gemma4moe)"; también #20225].

### 3.2 Cómo se arregla (flags correctos) [F]

- **`--cache-reuse 256`**: recicla KV/prefijos por chunks de 256 (tip del propio ggerganov). Ya saneado en el rig: ORO-SHIFT corrió `--context-shift --cache-reuse 256` a decode 21.39 = sin coste [M]. El default del server es 0 (apagado) en muchos builds — hay que ponerlo explícito.
- **`--ctx-checkpoints N`**: checkpoints de estado para poder rebobinar secuencias recurrentes (bounded por `n_rs_seq`). Sin ellos, cada turno puede resetear a cero [F].
- **`--cache-ram N`** (MiB de cache de prompts en RAM del host): el default (8192 MiB en el build del Director [M ORO-CRAM512]) **pelea con el modelo por la RAM** (14.27 GB en 16). CRAM512 midió decode intacto y liberó 7.7 GB [M] → recomendado **`--cache-ram 512`** (o 1024 con el GGUF IQ3_XXS del Nivel 2, que libera 1.05 GB).
- **Tutoriales del feature** [F discusión #20574]: con cache activa, TTFT 4.2 s → **0.3 s (−93%)** en prompts repetidos, +6% TBT de regalo. Referencia del feature: PR #16391 "host-memory prompt caching".
- **Cuidado con la plantilla de chat** [F]: si el harness mete fecha/hora o muta el inicio del prompt, el prefijo compartido se rompe y la cache no acierta (mantenedores: "no puedes cachear algo que cambia"; los `<think>` de turnos anteriores que la plantilla elimina también rompen el prefijo). Regla práctica: lo inmutable arriba del prompt, lo volátil al final.

### 3.3 Cómo validar que la cache funciona en ESTE rig [F]

Repro curl del issue/blog: conversación que crece turno a turno midiendo `time_starttransfer` con `stream:true` y el server en `-lv 4`:
- **Sano**: línea `restored context checkpoint (...)` y TTFT plano entre turnos.
- **Roto**: línea `forcing full prompt re-processing` y TTFT creciendo linealmente para siempre.
Si el repro curl es sano pero el uso real no, muta el prefijo el cliente (fechas, historial reescrito): `--log-prompts-dir` y diff [F].

## 4. Paralelismo de slots: +14% de throughput agregado [M]

Con `-np 4` (4 slots), el throughput agregado del server sube ~14% [M, medido pre-barrido] porque los ubatches de varios slots llenan mejor la banda. Coste: la latencia individual empeora si hay concurrencia real, y `-c 16384` se REPARTE entre slots (16384/4 = 4096 por slot). Para uso personal de 1 usuario: `-np 2` es el punto razonable (margen + throughput con poco reparto); `-np 4` solo si se usan varias sesiones a la vez [T].

## 5. Carga, arranque y RAM

- `--no-warmup`: load 34.3 → 32.8 s [M] (la pasada 1 paga el warm-up; ya se descarta en el protocolo). Ganancia pequeña pero gratis en sesiones cortas.
- `-lm dio` (DirectIO): sin efecto medible en load_s [M] — indiferente.
- **mlock: NO** [T]: con 14.27 GB de modelo en 16 GB de RAM, `--mlock` arriesga OOM del proceso o del SO; el mmap actual ya evita page-faults costosos tras el warm-up. Re-evaluar solo con el GGUF de 13.2 GB (Nivel 2) — y aun así con margen mínimo.
- Disco: modelo y pagefile en el SSD D: [M rutas].

## 6. Sistema operativo (sin tocar BIOS ni Defender — reglas del Director)

- **Plan de energía "Alto rendimiento"** (panel de control, software puro): evita que el governor baje frecuencia entre tokens [T, ganancia N/D en este rig]. No es BIOS: es un perfil de Windows.
- `start /high` al lanzar el server: redundante con `--prio 2` [M: prio 0/2/3 = ruido] — opcional.
- **Excluir el server de Defender: PROHIBIDO por decisión del Director** (registrado en worklog). No se propone; solo se documenta que existía como vía y queda cerrada.
- Afinidad de núcleos: **cerrado con datos negativos** (−9..−38%) [M].

## 7. Muertos definitivos (no reintentar) [M]

| Vía | Evidencia |
|---|---|
| ngram-simple / ngram-mod como spec | acceptance 0.00–0.16; decode medio −3..−16% |
| Afinidad/masks/strict | −9..−38% decode |
| FIT-C (margen 384) | −38% (desborde a RAM) |
| repack off (−nr) | −5% |
| KV q5_1 | 0% (y q4_0 solo vale como precio dentro de NCM37C4) |
| override-kv con clave `qwen3moe.*` | no-op → reemplazado por parser en barrido-total fase D |
| POLL distinto de default | ruido/−4% |

## 8. Protocolo: cómo cosechar lo que queda

1. **Combo ganadores** (pendiente de medir juntos): `ORO-UB1K ⊕ NCM37C4 ⊕ (-np 2) ⊕ (--cache-reuse 256 --cache-ram 512 --ctx-checkpoints 8)` — fase C del barrido-total. Expectativa: decode ~22.5–23.5 y prefill ~57+ [T].
2. **Si el ctx 4096 de NCM37C4 es poco** para el uso del Director: probar `-ncmoe 37 -c 8192 -ctk q4_0` (mitad delKV): la VRAM que libera el IQ3_XXS (Nivel 2) es la que paga ese contexto [T].
3. **Validar cache en chat real** con el repro curl (§3.3) + 5 turnos con LAIA mirando el log (`restored checkpoint` vs `forcing full re-processing`).
4. **Registrarse todo** en el informe JSON/MD del barrido (ya cableado) y en aprendido.md si algo sorprende.

## 9. Referencias

- Tutorial cache de prompts host-memory (PR #16391; TTFT −93%): https://github.com/ggml-org/llama.cpp/discussions/20574
- Issue híbridos: "exclusivo de qwen35moe/gemma4moe": https://github.com/ggml-org/llama.cpp/issues/21831 · bug 3.5: https://github.com/ggml-org/llama.cpp/issues/20225
- Mecánica de checkpoints/SWA/recurrentes (fuente server-context.cpp): https://particula.tech/blog/prompt-reprocessing-swa-hybrid-models-kv-cache
- Caso real de evicción de cache (—cache-ram demasiado chico): https://www.reddit.com/r/LocalLLaMA/comments/1td9stc/
- Tip ggerganov --cache-reuse 256: https://x.com/ggerganov/status/1909657397964292209
- Guía MoE CPU+GPU (colocación -ot/--cpu-moe, auto-fit): https://huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide
- Datos propios [M]: barrido-30-resultados.csv (37 configs), barrido-qwen-30.py (flags exactos), lanzador v2.1 ORO-UB1K, aprendido.md

---

## 10. ANEXO — Segunda ronda: flags exactos del build b11856 (2026-10-26)

### 10.1 Defaults confirmados en el dump del Director [M]

Del dump `llama-flags-nuevo.txt` (help del build b11856):

| Flag | Default del build | Nota |
|---|---|---|
| `--ctx-checkpoints N` (-ctxcp) | **32 por slot** | PR #15293 |
| `--checkpoint-min-step N` (-cms) | **8192** (0 = sin mínimo) | con chats de 16K caben ≤2 checkpoints: bajar a 1024–2048 para chat continuo |
| `--cache-ram N` (-cram) | **8192 MiB** (0 = off, −1 = sin límite) | con 14.27 GB de modelo en 16 GB RAM, el default PELEA con el modelo → 512–1024 |
| `--kv-unified` (-kvu) | ON si slots=auto | un solo buffer KV compartido; el log del issue #24055 muestra `kv_unified = true` con auto |
| `--cache-idle-slots` | ON (requiere cache-ram) | guarda slots idle en la cache de prompts: gratis para nosotros |
| `--context-shift` | **OFF** | ORO-SHIFT ya midió ON + reuse 256 sin coste [M] |
| `--cache-reuse N` | (L620 del dump) | usar 256 explícito |
| `--threads-batch N` (-tb) | existe | candidato de test: `-tb 4` explícito para prefill |

### 10.2 Presupuesto RAM de los checkpoints [T]

Cada checkpoint guarda el **estado recurrente GDN**: 30 capas × 32 heads × matriz 128×128 × 4 B ≈ **63 MB**. El default 32 checkpoints ≈ **2 GB** — exactamente el tipo de RAM que este rig no tiene. `--cache-ram` los cap: con 512 MiB caben ~8 checkpoints (suficiente para chat continuo de contexto moderado).

### 10.3 Bug conocido en la familia de checkpoints [F]

Issue #24055: en builds recientes (flag renombrado de `--checkpoint-every-n-tokens` a `--checkpoint-min-step`), el nuevo flag puede **no crear checkpoints y forzar re-procesado completo** (first bad commit e98cb51). El log del issue muestra además un warning real en un híbrido de la misma familia: **"cache_reuse is not supported by this context, it will be disabled"** — o sea, la cache puede auto-apagarse según el contexto/colocación.

Protocolo de validación en el rig (obligatorio antes de dar por buena la cache):
1. Arrancar con `-lv 4 --cache-reuse 256 --cache-ram 512 -cms 1024 --ctx-checkpoints 16`.
2. Buscar en el arranque: `cache_reuse is not supported by this context` (si sale → la vía cache-reuse queda condicionada a build/colocación).
3. Repro curl de 5 turnos (§3.3): sano si aparece `restored context checkpoint` y TTFT plano; roto si `forcing full prompt re-processing`.
4. Si el flag está roto en b11856: probar `-cms 0`, y si persiste, queda apuntado como motivo de actualización de build (junto con `--moe-topk` del Nivel 1).

### 10.4 Stack de referencia de un híbrido hermano [F]

Config de issue #24055 (Qwen3.6-27B-MTP en 2×P100): `--ctx-checkpoints 64 --checkpoint-min-step 512 --cache-reuse 256 --cache-ram 2048 --kv-unified --cont-batching --flash-attn on` — coincide línea por línea con lo que este documento recomienda; las diferencias (cache-ram 2048, checkpoints 64) son de un rig con más RAM libre.

### 10.5 Actualización del techo del Nivel 3 [T]

Con los defaults corregidos (cache-ram 512–1024, cms 1024, reuse 256, shift ON), el combo ganador queda: `-ub 1024 -b 4096 -np 2 --cache-reuse 256 --cache-ram 512 -cms 1024 --context-shift` ⊕ (NCM37C4 o FIT-A). El IQ3_XXS del Nivel 2 libera la RAM que hace viable este combo sin pelea de memoria.

---

## 11. ANEXO — Tercera ronda: Windows/GPU fino, defaults auditados al 100% y el conflicto MTP×slots (2026-10-26)

### 11.1 NUEVO — "CUDA - Sysmem Fallback Policy" en el Panel NVIDIA: la válvula oculta de WDDM [F]

- NVIDIA añadió el setting en driver **546.01 (Oct-2023)** [F KB oficial a_id/5490]: Panel de Control NVIDIA → Administrar configuración 3D → **"CUDA - Sysmem Fallback Policy"** → cambiar de "Driver Default" a **"Prefer No Sysmem Fallback"**.
- Mecánica confirmada por ingeniería de NVIDIA [F foro developer, respuesta de Robert Crovella]: bajo WDDM (todo Windows de escritorio), `cudaMalloc` NO garantiza VRAM — el gestor de memoria de Windows puede aterrizar la asignación en la "memoria compartida" (RAM) **silenciosamente**, y paginar datos GPU↔RAM cuando le conviene. Ni el driver ni la app lo reportan.
- **Por qué esto importa AQUÍ** [T compatible con lo medido]: el colapso FIT-C (−38%, §2) es exactamente el síntoma de un desborde de VRAM paginado en silencio por WDDM. Con "Prefer No Sysmem Fallback", el desborde falla RUIDOSO (error OOM inmediato) en vez de degradar a velocidad de RAM — que es exactamente lo que un barrido necesita para detectar malos fits al instante.
- Cumple las reglas del Director: es un setting de driver/gráficos, NO es BIOS ni Defender.
- Riesgo asumido: con fallback OFF, si algo pide más de los 4 GB → error visible en vez de lentitud. Mitigación: `-fit on` (default del build, §11.3) ya reserva margen de 1024 MiB; el setting es el detector, no el causante.

### 11.2 Plan de energía: GUID exacto y comandos [F]

- **Alto rendimiento = `8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c`** [F MS KB + práctica documentada]:
  ```
  powercfg /list
  powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
  ```
- Balanced (para volver atrás) = `381b4222-f694-41f0-9685-ff5bb260df2e` [F MS KB].
- Si "Alto rendimiento" no aparece en el panel (pasa en desktops con Modern Standby): `powercfg /duplicatescheme 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c` y luego activar el GUID nuevo que imprime [F windowscentral].
- Ultimate Performance = `e9a42b02-d5df-448d-aa00-03f14749eb61` (mismo método con /duplicatescheme) [T GUID documentado por Microsoft; no verificado en las fuentes de esta ronda].
- Ganancia en ESTE rig: [N/D] — candidato a 1 run del barrido (fase C) con etiqueta propia.

### 11.3 Defaults del build b11856: auditoría COMPLETA (ronda 2 + 3) [F dump]

Tabla definitiva — todo lo que el launcher hereda si no se pasa el flag:

| Flag | Default b11856 | Acción nuestra |
|---|---|---|
| `-t` | -1 (auto) | explícito 4 en launcher ✓ |
| `-tb` | = `-t` | candidato `-tb 4` (idéntico en la práctica) |
| `--prio` | **0** | launcher usa 2 ✓ (3 = realtime: ruido medido [M]) |
| `--poll` | 50 | no tocar [M] |
| `-ngl` | **auto** (acepta exacto/'auto'/'all') | launcher usa 99 ✓ |
| `-fit` | **ON** | FIT-A tunó esto con `-fitt 256` [M] |
| `-fitt` | **1024 MiB** margen por dispositivo | FIT-A lo baja a 256 (agresivo, medido +4%) |
| `-fitc` | 4096 (piso de ctx que el fit puede elegir) | verlo si un fit sorprende con ctx chico |
| `--cpu-strict` | 0 | no tocar [M: afinidad muerta] |
| `-fa` | **auto** | launcher usa `on` explícito ✓ |
| `--cache-prompt` | **ON** | bien (lo que falta activar es reuse) |
| `--cache-reuse` | **0** (OFF) | pasar 256 explícito |
| `-ctxcp` | 32/slot | bajar a 16 (RAM) |
| `-cms` | 8192 | bajar a 1024 para chat continuo |
| `-cram` | **8192 MiB** | bajar a 512 (rig actual) / 1024 con IQ3_XXS |
| `-kvu` | ON si slots=auto | OK |
| `--cache-idle-slots` | ON (requiere cache-ram) | gratis |
| `--context-shift` | **OFF** | ON en el combo (medido sin coste [M]) |
| `--metrics` | OFF | ON opcional para graficar |
| `--slots` | ON | endpoint de monitoreo gratis |
| `--log-prompts-dir` | OFF | ON solo para debug de cache (§3.3) |
| `--sleep-idle-seconds` | -1 (OFF) | [N/D] qué libera al dormir; no usar por ahora |
| `--threads-http` | -1 (→8 hilos) | irrelevante en uso mono-usuario |
| `--spec-draft-n-max` | **3** | T2 usa 2 explícito ✓ |
| `--spec-draft-prio` | **0** | **subir a 2 en fase E** (el draft heredaría prioridad normal) |
| `--slot-save-path` | OFF | legacy KV-a-disco; no usar en híbridos [T] |

Novedad del dump (no vista antes): **`--kv-unified-per-slot N`** [F dump L435–437]: con `-kvu` y SIN `-c`, el pool KV compartido se dimensiona como `n_parallel × N`. Forma limpia de fijar "-np 2 × 8192/slot" sin calcular `-c` global.

### 11.4 CONFLICTO resuelto: MTP exige `-np 1` (deroga parte de §4) [F]

El README oficial del repo MTP de unsloth para ESTE modelo declara: **`-np > 1` no soportado aún con draft-mtp** (y `--mmproj` tampoco). Consecuencia para el combo final:

- Config SIN MTP (fases B/C/D): `-np 2` permitido, +14% agregado [M §4] con `-kv-unified-per-slot 8192` si se quiere ctx fijo por slot.
- Config CON MTP (fase E): **`-np 1` obligatorio** — la ganancia MTP (×1.28+ [F]) absorbe y supera lo que los slots aportaban.
- Con MTP añadir también `--spec-draft-prio 2` (default 0 dejaría el draft en prioridad normal, §11.3).

### 11.5 "Speculative checkpointing" (PR #19493, fusionado Abr-2026): matiz con nuestro muerto ngram [F]

Se fusionó una técnica que reutiliza checkpoints de estado para especulación por n-gramos. La dosis de comunidad que reporta 0–50% en CODING: `--spec-type ngram-mod --spec-ngram-size-n 24 --draft-min 48 --draft-max 64`. Nuestros NGRAMS/NGRAMM muertos [M] usaron dosificación corta distinta — técnicamente queda una re-apertura opcional para sesiones de código, con dosis exacta de arriba y expectativa baja (nuestro uso principal es chat ES) [T]. Prioridad: baja. Y confirmado aparte: **DFlash (PR #22105) NO-GO en VRAM de 4–6 GB** [F reporte con el propio 3.6-35B] (ver Nivel 1 §12.8).

### 11.6 Detalles finos de la cache, confirmados a nivel de código [F]

- La creación de checkpoints exige que el contexto sea `FULL`, `RS`, o `n_swa > 0` [F particula.tech citando el source del server]. En el híbrido GDN, el contexto es RS (rollback limitado por `n_rs_seq`) → SÍ aplica, pero con el TODO del source admitiendo que el cálculo de rango está mal para SWA — o sea, el feature es joven: el repro de validación (§3.3) es obligatorio, no opcional.
- El repro del issue #21831 estaba VICIADO [F análisis particula]: mandaba solo el mensaje nuevo a un endpoint stateless; la respuesta "no sé tu nombre" no prueba nada. **La evidencia válida son las líneas de log** (`restored context checkpoint` vs `forcing full prompt re-processing`) y el TTFT plano — SIEMPRE enviando el historial completo en cada curl.
- Causas típicas de rotura de prefijo, según mantenedores [F]: `<think>` de turnos anteriores que la plantilla emite y luego strippea (**incluso con `-rea off`** se emiten dos tokens `<think></think>` que se strippean al turno siguiente), tool definitions regeneradas en otro orden, historial reescrito en sitio. `--log-prompts-dir` + diff consecutivo = método endosado para cazar al culpable [F dump L730: "auto-created if not present"].
- El log de arranque imprime `system_info: ... USE_GRAPHS = 1 | REPACK = 1` [F log #24055]: grep gratis para autenticar que el build activo tiene CUDA graphs y repack AVX2 (repack ON es +5% medido [M §2]).

### 11.7 Líneas finales recomendadas (actualizan §8.1) [T sobre M+F]

**Sin MTP** (fases B/C/D — combo ganadores):
```
-ub 1024 -b 4096 -np 2 --kv-unified-per-slot 8192 \
--cache-reuse 256 --cache-ram 512 -cms 1024 --ctx-checkpoints 16 \
--context-shift -fa on -t 4 --prio 2 \
[⊕ NCM37C4 o FIT-A] [⊕ --override-kv <arch>.expert_used_count=int:K en fase D]
```

**Con MTP** (fase E):
```
-ub 1024 -b 4096 -np 1 \
--spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-prio 2 \
--cache-reuse 256 --cache-ram 256 -cms 1024 --ctx-checkpoints 8 \
--context-shift -fa on -t 4 --prio 2 -c 8192
```
(RAM más apretada con el GGUF-MTP de 14.07 GB — presupuesto en Nivel 2 §13.6; cache-ram 256 y ctx-checkpoints 8 son la reducción de la factura de RAM del Nivel 3 al servicio de la fase E.)

**Referencias nuevas de esta ronda**: KB NVIDIA Sysmem Fallback (driver 546.01+): https://nvidia.custhelp.com/app/answers/detail/a_id/5490 · mecánica WDDM/cudaMalloc (R. Crovella, NVIDIA): https://forums.developer.nvidia.com/t/cudamalloc-with-sysmem-fallback/347791 · powercfg setactive GUID High Perf: https://learn.microsoft.com (KB 0e95387e) + https://blog.rmilne.ca/2023/10/06/using-powercfg-to-set-server-power-plan-from-command-line + https://www.windowscentral.com/how-use-powercfg-control-power-settings-windows-10 · mecánica checkpoints FULL/RS/SWA + repro viciado #21831 + `<think>` rompe-prefijo: https://particula.tech/blog/prompt-reprocessing-swa-hybrid-models-kv-cache · issue #24055 (log completo: kv_unified auto, cache_reuse warning, system_info): https://github.com/ggml-org/llama.cpp/issues/24055 · speculative checkpointing #19493: https://github.com/ggml-org/llama.cpp/pull/19493 (+ hilo r/LocalLLaMA 1sprdm8) · DFlash #22105: https://github.com/ggml-org/llama.cpp/pull/22105 · restricción -np>1 con MTP: https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF · dump local b11856 (líneas 7–17, 135–160, 435–459, 618–632, 728–731) [M].

## 12. ANEXO — Cuarta ronda: KV unificada silencia el spec, leaks del server y el presupuesto de checkpoints (2026-10-26)

- **[F #25345] llama-server IGNORA `-md` en silencio (el especulativo nunca se activa) cuando la KV unificada está activa.** El build del rig arranca con `--kv-unified ON` auto con slots [M ronda 3] → RIESGO DIRECTO de que las fases E/S midan un "spec" que nunca enganchó. Autenticador obligatorio en TODA config especulativa: (1) grep del log por el tipo/draft cargado, (2) métrica de aceptación > 0, (3) si no engancha: probar `--kv-unified off` y re-medir.
- **[F #23635] Leak de VRAM (`ggml_cuda_pool_vmm`) en PREFILL con MTP + KV cuantizada** — exactamente el combo del rig (MTP + ctk/ctv q8_0). Cerrado upstream → tras RUTA 0 verificar fecha del build; monitorear VRAM en prefill largo; diagnóstico temporal: KV f16. Con Sysmem Fallback OFF [F ronda 3] el leak se vuelve fallo visible y no silencioso.
- **[F xhinker Medium May-2026] MTP en uso real: a las ~3 h, RAM al 95% + swap + timeouts** (dual 3090; workaround de 2 flags tras paywall, flags N/D). Coherente con #23635 → el monitoreo de RAM/VRAM pasa a ser parte del PROTOCOLO MTP del rig, no opcional.
- **[F #27725] Leak genérico reportado ~3 MB/request en llama-server** (unconfirmed, Ago-2026): en jornadas largas del rig de 16 GB = gigas perdidos → higiene: reiniciar el server entre fases del barrido (ya es práctica) y vigilar RSS en sesiones largas.
- **Presupuesto de checkpoints [T sobre componentes F]:** `--ctx-checkpoints` default 32/slot [M] × ~63 MB por checkpoint GDN [F ronda 2] ≈ **2.0 GB de RAM potenciales** → dosis nueva **`-ctxcp 4`** (o 8) libera ~1.5-1.8 GB → candidato #1 a culpable de pageouts (N4 §12) y palanca de RAM gratis. Verificación en rig: RAM del proceso con sesión larga, `-ctxcp 32` vs `-ctxcp 4`.
- **Cierres con el CSV barrido-30 [F rig]:** ORO-TB8 (`-tb 8`) 21.45 t/s → threads-batch 8 MUERTO (no reintentar); ORO-CRAM512 21.57 → `--cache-ram 512` neutro en decode y seguro (prefill algo menor); ORO-SHIFT 21.39 → context-shift OFF se mantiene.

## 13. ANEXO — Quinta ronda: auditoría b11856 vs upstream, protocolo de medición con varianza 9.4pp (2026-10-26)

- **El build del rig posicionado en la línea temporal [F historial de releases]:** b11856 (~22-23 Oct) **YA incluye** tres fixes que nos benefician: b11747 (19 Oct) "Fixes CUDA flash-attention race conditions" — relevante porque usamos `-fa auto`; b11552 (10 Oct) fix de server donde "busy slots ran prompt cache updates before deferring" — relevante para la caché de prompts; b11456 (6 Oct) fix de k-pool scatter data race en secuencias compartidas. **NO incluye** b11869 (24 Oct) "fixed Jinja template select and selectattr filter argument handling" — el único cambio funcional posterior pertinente (plantillas de chat con filtros Jinja = tool-calling). b11888 (25 Oct) = limpieza CUDA sin cambio funcional. Etiquetas semánticas: 0.6.0 (5 Oct, habilita MTP speculative + Metal FA) y 0.7.0 (15 Oct).
- **Decisión de build derivada [T sobre datos F]:** NO urge actualizar por velocidad. RAZÓN ÚNICA para RUTA 0 ahora: si aparecen síntomas de plantilla (tool-calls mal formateados, mensajes con filtros select/selectattr raros). Si se actualiza, ir a b11869+ para llevar el fix Jinja; b11888 no aporta nada funcional. Esto convierte la RUTA 0 de "obligatoria" (ronda 1) a "condicional" — el driver original (draft-mtp x2) ya no aplica porque UD-IQ3_XXS-MTP trae el nextn dentro y b11856 YA soporta spec (la fase E corre en el build actual).
- **#24055 con log completo a mano [F]:** el compose de referencia de la comunidad para este problema combina `--swa-full --kv-unified --kv-offload --op-offload --repack --no-mmap --fit off --ctx-checkpoints 64 --checkpoint-min-step 512 --cache-reuse 256 --cache-ram 2048` en un híbrido — y el log muestra la línea clave que ya documentamos: *"srv load_model: cache_reuse is not supported by this context, it will be disabled"* con `n_parallel auto → kv_unified true`. First bad commit e98cb51. Nuestro autenticador (grep de esa línea + fallback `--kv-unified off`) queda ratificado por un caso tercero.
- **El repro de #21831 estaba VICIADO [F particula.tech]:** la segunda llamada curl solo enviaba el mensaje nuevo (`prompt_tokens: 18`) — `/v1/chat/completions` es stateless y el modelo no podía saber el nombre aunque la caché funcionara. **El protocolo correcto** (ya en §11, ahora con guion probado): enviar el HISTORIAL COMPLETO cada turno, medir `time_starttransfer` de curl con `stream: true` (proxy de TTFT), 8 turnos crecientes; sano = línea "restored context checkpoint" + TTFT plano; roto = "forcing full prompt re-processing" + TTFT que crece linealmente. Si el curl está sano pero el harness re-procesa: `--log-prompts-dir` y diff de dumps consecutivos (método mantenedor); culpables típicos: reasoning stripped de turnos previos, tool definitions regeneradas en otro orden, harness que reescribe el historial.
- **Tercera razón para `-ctxcp 4` [F reporte semanal]:** en Gemma 4 los checkpoints consumen RAM anormal hasta OOM en RTX 3090 (CUDA y Vulkan), workaround = reducir/desactivar checkpoints. Se suma al presupuesto de 2 GB por defaults (§12) y al bug de invalidación #24055 → el cachete de checkpoints acumula 3 evidencias de riesgo RAM; la dosis `-ctxcp 4` (libera ~1.5-1.8 GB) queda como la más defendible del Nivel 3.
- **PROTOCOLO DE MEDICIÓN del rig actualizado [F estudio thc1006 v4, 3002 arm-runs]:** el mismo config medido 12 veces en un día abarca **9.4 pp** (DFlash-n2: +17.3% a +26.7%, clusterizado por corrida — "solo un brazo se mueve entre clusters"); la aceptación real y el decode correlacionan r=+0.998. → Reglas para el barrido-total y para cualquier A/B futuro: (1) mediana de 3 corridas por celda clave, (2) baseline matcheado DENTRO de cada corrida (nunca comparar contra el ancla de otra sesión), (3) no perseguir deltas <5pp, (4) mismo bloque horario. Esto explica de paso por qué el CSV barrido-30 (1 corrida/celda) tiene que leerse con margen.
- **op-offload y batch [F blog Doctor-Shotgun]:** el pp por GPU de pesos CPU se dispara con batches ≥32 tokens (default llama.cpp); ik_llama.cpp usa umbral 32×256/8 = 1024. Para el rig: los `-b/-ub` del launcher (2048/512) ya superan el umbral; subirlos a 4096/4096 mejoraría prefill híbrido a costa de VRAM del buffer — dose solo si la fase H deja VRAM libre después del MEC (N1 §14).
- **Estado de cosecha del Nivel 3:** quedan por correr en el rig: (1) combo ganadores (ORO-UB1K + NCM37C4 + FIT-A margen), (2) `--cache-reuse 256` + `-ctxcp 4` + validación de checkpoints con el curl protocol, (3) NOW: dosis MEC 512/768/1024 (ver N1 §14 — es palanca del N3 también porque reduce el tiempo PCIe por token). El resto del N3 está cosechado o refutado con evidencia.
