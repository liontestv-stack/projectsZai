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

## 14. ANEXO — Sexta ronda: #21831 sigue sin arreglar (y su workaround NO existe en b11856), las flags muertas confirmadas y el coste de cache del MTP (2026-10-26)

- **#21831 (full prompt re-processing en qwen35moe) permanece ABIERTO en la práctica [F]:** cerrado "as not planned", con el problema confirmado por usuarios hasta el 29-Abr-2026 y sin commit de fix identificado. Los workarounds que circulaban quedan ahora documentados con nombre exacto: (1) `--checkpoint-every-n-tokens 1024` (alias `-cpent`; antes `--checkpoint-every-nb`) + `--ctx-checkpoints 256`; (2) parche de código: comentar `do_checkpoint = do_checkpoint && !has_mtmd;` en `tools/server/server-context.cpp`; (3) en harness tipo AiderDesk, desactivar Task Tools; (4) migrar a arquitectura pura-transformer (no aplica al proyecto).
- **CRÍTICO para el rig [M dump b11856]:** la flag del workaround **NO existe en b11856** — el dump solo tiene `-ctxcp/--ctx-checkpoints` (default 32) y `-cms/--checkpoint-min-step` (default 8192); cero ocurrencias de `checkpoint-every` / `cpent`. → **La mitigación (1) NO es ejecutable hoy**: exige RUTA 0 (build ≥ el que introdujo cpent) o el parche (2). Mientras tanto, si el curl protocol (§11/§13) muestra "forcing full prompt re-processing" persistente, las opciones reales son: RUTA 0, parche, o aceptar el coste (TTFT crece con el historial — medir y decidir con datos).
- **Confirmación de flags muertas desde fuente independiente [F openclawdc "Flags Explained 2026" + M dump]:** `--no-mmap`, `--mlock` y `--direct-io` fueron plegadas en `-lm/--load-mode` (PR #20834, 23-Jul-2026) como alias deprecados y **eliminadas por completo en PR #28334 (9-Sep-2026)** — builds posteriores responden `error: invalid argument`. El dump b11856 no las lista [M] → **cualquier comando de internet con `--no-mmap` (p.ej. el repo de referencia hanxiao/L4) FALLA en el rig**: traducción obligatoria `-lm none`; `--mlock` → `-lm mmap+mlock`. La guía también ratifica: `-ngl` default `auto` (la recomendación vieja "-ngl 99" ya no es un fix), y *"only -fa and -ub reliably buy you speed on a machine that already fits the model"* — consistente con todo nuestro CSV.
- **"Sweep, no copies" [F openclawdc]:** la guía profesional de 2026 dice literalmente de `--n-cpu-moe`: *"Do not copy a value. Sweep it."* — es exactamente la filosofía de la fase D del barrido (con el autenticador n_expert_used); external validation del diseño del barrido-total.
- **El MTP degrada el cache de prompts [F vLLM #38182, vía estudio thc1006 v3]:** con MTP activo el hit-rate del prefix cache cayó **92% → 71%** en la misma clase de modelo — tanto que en vLLM el MTP parecía NEGATIVO hasta que se midió con prefix-cache desactivado y flags matcheadas (entonces: **TPOT −21.6%, TTFT −31.4%, total +31.7%**). Para el rig: la fase E corre con `--cache-prompt` ON (nuestro chat); **el protocolo E añade medición de TTFT/hit-rate del cache**, y si el decode gana pero el TTFT del chat empeora, se corre un A/B con `--cache-prompt off` para separar los dos efectos antes de declarar la dosis final.
- **Fix upstream menor [F release b11888 25-Oct]:** límite de profundidad recursiva en grammar; tokens de 256+ caracteres bajo GBNF ya no se rechazan siempre; mejora sampling con gramática en Qwen3.6. Solo relevante si el Director usa salidas con GBNF; no afecta al barrido.
- **Estado de las rondas:** el Nivel 3 conserva su veredicto (combo ganadores + cache híbrida + -ctxcp 4 + MEC), con DOS actualizaciones operativas: (1) la validación de checkpoints puede requerir RUTA 0 si el repro del bug aparece (cpent no existe aquí); (2) la fase E ahora lleva el A/B de cache-prompt dentro de su protocolo.

*Referencias nuevas: github ggml-org/llama.cpp issue #21831 (estado y workarounds con nombres de flag exactos); openclawdc.com/blog/llama-cpp-flags-explained (2026, PRs #20834 y #28334); datos vLLM #38182 citados en unsloth discussion #14 (estudio thc1006 v3); release b11888.*


## 15. ANEXO — Séptima ronda: timeouts intermitentes con spec (#23268), el drift de salida del MTP medido y defaults de b11856 ≠ master (2026-10-26)

- **Timeouts intermitentes con spec, #23268 [F] (CERRADO sin fix claro documentado):** con `draft-mtp` O con `ngram-mod`, el streaming puede colgarse de forma intermitente (<1% de llamadas) con la conexión viva y sin end-of-stream → el cliente cuelga hasta su timeout (reporte: llama-swap con 300 s). Reproducido en Vulkan/AMD-395 con NUESTRO modelo (UD-Q8_K_XL del 3.6-35B-A3B) en build de Mayo. **Protocolo E/S actualizado:** (1) timeout de cliente 120-180 s + 1 retry automático; (2) si aparecen cuelgues, primer A/B = spec OFF (sospechoso estadístico, no el cache); (3) dato de aceptación ngram anotado: picos ~140 t/s en tokens repetidos.
- **El drift de salida del MTP, medido [F]** (mauriziofonte.it, 14-Oct-2026; Qwen3.8-27B GSQ-RCO-IQ3_S-mtp, temp 0): teoría — la verificación en lote NO es el mismo cómputo que decodificar 1 a 1; la suma flotante no es asociativa y el orden sigue la forma del lote; near-ties cambian de argmax y de ahí diverge todo. Datos: solo 7/50 respuestas idénticas carácter a carácter; 34/50 resueltos CON cabeza MTP vs 33/50 sin (5 solo-con, 4 solo-sin) = **ruido, no degradación sistemática**. Reglas operativas: MTP ON para agentes/interactivo (1.94x; texto estructurado y repetitivo se predice bien); MTP OFF para evals/regresión/reproducibilidad; misma config spec en ambos lados de TODA comparación; y de los docs oficiales master: "use greedy sampling when exact output matching is required".
- **Defaults de b11856 ≠ master [M dump]** (corrige el apunte de defaults de la ronda 3, que aquí queda sin borrar): `--spec-draft-n-max` default **16** en b11856 (master: 3) y `--spec-draft-p-min` default **0.75** en b11856 (master: 0.00) → con draft clásico y `-md`, el build del Director drafta hasta 16 tokens con umbral greedy 0.75 si no se fijan flags. Añadido a traducciones obligatorias: **fijar SIEMPRE `--spec-draft-n-max` y `--spec-draft-p-min` explícitos**. Además: `-cd/--ctx-size-draft` existe en b11856 (en master ya no figura en docs) y `--adaptive-target/--adaptive-decay` son del SAMPLER adaptive-p (#17927), NO del "MTP adaptativo" de redes sociales.
- **v0.7.0 (15-Oct) para el server, tras RUTA 0 [F]:** chat session API refactorizada (`common_chat_session`, salida part-based), restauración de slots y prompt-cache "mucho mejor", puerto default nuevo (9931), el MTP maneja entradas mtmd (visión) + fix de manejo mtmd en graphs MTP. `--backend-sampling` (sampling del draft/target en backend, con fallback a CPU) ya existe en b11856 [M].
- **Herramienta oficial de medición [F]:** SPEED-Bench client en master (`tools/server/bench/speed-bench`) — corre contra un llama-server vivo y compara baseline vs spec (throughput, latencia, draft acceptance) → candidata a reforzar el protocolo de mediana de 3 tras RUTA 0.

*Referencias nuevas: github ggml-org/llama.cpp issue #23268 (timeouts intermitentes con spec, cerrado); mauriziofonte.it/blog/post/mtp-speculative-decoding-llama-cpp-speedup-output-drift-qwen3-8-27b.html (drift de salida medido, 14-Oct-2026); docs/speculative.md master (defaults, backend-sampling, greedy para matching exacto, SPEED-Bench); release v0.7.0 (server: chat session, slots, puerto 9931, mtmd en MTP); dump b11856 del Director (defaults n-max/p-min, -cd, adaptive-p) [M].*


## 16. ANEXO — Octava ronda: RUTA 0 SIN COMPILAR — binarios precompilados de b11901, el gotcha de las DLL y config de producción de nuestra familia (2026-10-26)

- **RUTA 0 simplificada [F]:** no hace falta git pull + compilar. Los releases de GitHub publican binarios Windows precompilados: **"Windows x64 (CUDA 12) — DLLs CUDA 12.4"** y **"Windows x64 (CUDA 13) — DLLs CUDA 13.4"**. El último release etiquetado a hoy es **b11901** (atom feed, 26-Oct; nuestro build es b11856 → 45 builds de diferencia, incluye TODO el contenido de v0.7.0: draft-dspark, LiliCorr, MEC multi-GPU, nuevo restore de prompt-cache). La 1650 es Turing pre-Blackwell → ambas variantes le sirven; **la de CUDA 12.4 es la elección conservadora** (el aviso de low-bit roto era de CUDA 13.2, ronda 2; el estado de 13.4 con low-bit es [N/D]).
- **GOTCHA crítico del pack precompilado [F, discussion #17812]:** el zip del binario NO trae las DLL de CUDA — hay que descargar TAMBIÉN el zip `cudart-llama-bin-win-cuda-12.4-x64.zip` y extraerlo en la MISMA carpeta del exe. Sin eso el server "no ve" la GPU (reporte real: 26 t/s por Vulkan de emergencia vs CPU 36 t/s, GPU dormida). RUTA 0 = descargar DOS zips, no uno.
- **Config de producción con nuestra familia exacta [F lautenbacher.io 8-Jul]:** `UD-Q4_K_S` + `--spec-type draft-mtp --spec-draft-n-max 4` + `-c 64000` + KV `q4_0/q4_0` + `-ngl 99 --n-cpu-moe 31` + `-b 512 -ub 512` + `-lv 4`. Validaciones que aporta: (1) draft-mtp convive con KV doble-cuantizada en producción; (2) `-lv 4` existe como nivel de log para diagnóstico; (3) n-max 4 como punto de partida ajeno (nuestra dosis E sigue siendo n2, ronda 6). Nombres de flags de la guía verificados contra docs master [F] — todos existen en builds nuevos; en b11856 los operativos ya están en el dump.
- **Recordatorio del protocolo tras RUTA 0:** re-auditar defaults del build nuevo (los 25 de la ronda 3 fueron del b11856; b11901 puede traer cambios — el master ya difiere en n-max 3 vs 16 y p-min 0.00 vs 0.75, ronda 7) y registrar el dump nuevo como FUENTE DE VERDAD #1 en paralelo al actual, sin borrar el viejo.

*Referencias nuevas: github.com/ggml-org/llama.cpp/releases (variantes CUDA 12.4/13.4 para Windows) y releases.atom (b11901 último etiquetado, 26-Oct-2026); github discussion #17812 (cudart zip separado o GPU dormida); lautenbacher.io (config producción Qwen3.6-35B-A3B con draft-mtp, 8-Jul-2026).*


## 17. ANEXO — Novena ronda: la muerte con fecha de --no-mmap/--mlock, el op-offload del prefill híbrido y -ngl 'auto' ya en b11856 (2026-10-26)

- **Calendario de defunción de los alias de carga [F openclawdc flags-explained 15-Sep-2026]:** PR #20834 (23-Jul-2026) dobla `--no-mmap`/`--mlock`/`--direct-io` dentro de `-lm/--load-mode` (quedan como aliases deprecados); PR #28334 (09-Sep-2026) los **elimina por completo** → los builds posteriores los rechazan con `error: invalid argument`. b11901 (Oct-2026) es posterior al 09-Sep → **tras RUTA 0, el muscle-memory del Director (`--no-mmap`, `--mlock`) muere en duro, sin warning**. La traducción `-lm none` / `-lm mmap+mlock` de §14 pasa de "recomendada" a **obligatoria** para el build nuevo. (b11856 aún los acepta como aliases [M dump].)
- **`-ngl` default 'auto' YA en b11856 [M dump L116-117]:** *"max. number of layers to store in VRAM, either an exact number, 'auto', or 'all' (default: auto)"* — el consejo genérico de internet "-ngl 99 siempre" es un workaround de un default que ya no existe; nuestras recetas fijan `-ngl` explícito en todos los lanzamientos → sin drift posible.
- **Op-offload: por qué `-ub` manda en el prefill híbrido [F Doctor-Shotgun + reddit 1tany5t]:** con expertos residentes en CPU, si el batch de prompt supera ~32 tokens (default), llama.cpp procesa el prompt **copiando los pesos asignados a CPU hacia la GPU** ("op offload") en vez de ejecutarlos en CPU — y el tamaño de `-ub` amortiza esas copias: en modelos parcialmente offloadeados, `-ub 4096` vs el default 512 = **380 → 2091 t/s de prefill (5.5x)**. En el rig: subir `-ub` agranda el compute buffer (VRAM, N4) → el A/B de `-ub` para TTFT con el protocolo existente es el árbitro; NO copiar `-ub 4096` sin medir en 4GB. (Nota ik: su umbral de op-offload es 32 × total/activos expertos — para el 3.6 ≈ 910 tokens [F].)
- **ik_llama.cpp descartado también para prefill [F issue #1699]:** con el 3.6 (IQ4_XS, ctx 131k, -cmoe, 1660S 6GB): PP 118.8 vs 239.8 t/s de mainline (**−2x**) — el fork no mejora ni el PP ni el TG en el arch híbrido; se cierra toda la vía fork para el rig.
- **Categorización 2026 de flags [F openclawdc flags-explained]:** "solo `-fa` y `-ub` compran velocidad en una máquina donde el modelo ya cabe; el resto compra que quepa" — coherente con nuestra separación memoria/velocidad de §13: `-fa` (auto ya en build [M]) y `-ub` (ORO-UB1K) son las palancas de velocidad; el resto del inventario es presupuesto.
- **Sin cambios de dosis:** el protocolo de mediana de 3, el baseline matcheado y las traducciones §14 se mantienen; esta ronda añade la fecha de defunción de los alias (obligatoria tras RUTA 0) y el mecanismo op-offload que explica nuestros números de TTFT híbridos.

*Referencias nuevas: openclawdc.com/blog/llama-cpp-flags-explained (15-Sep-2026, PR #20834 y #28334 con fechas); huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide (op-offload, umbral 32 tokens); reddit r/LocalLLaMA 1tany5t (-ub 4096: 380→2091 t/s); github ikawrakow/ik_llama.cpp issue #1699 (PP -2x); dump b11856 del Director (-ngl auto por defecto) [M].*


---

## 18. ANEXO — Décima ronda: AUDITORÍA DE RESPALDO RIGUROSO punto a punto (2026-10-26)

Auditoría del Director aplicada a este nivel: re-verificación independiente de cada punto [F] hoy (lecturas directas de issues/discusiones/blogs citados) + re-chequeo del dump contra la manpage Debian. **Resultado: 0 puntos refutados; el bloque cache/prompt-híbrida y el bug de timeouts quedan confirmados verbatim; 2 matices de estado (cierre de #26038, fecha exacta de muerte de alias); protocolos SIN cambios.**

### 18.1 Cache de prompts en híbridos (el bloque más delicado del nivel)

| Punto (§) | Veredicto | Respaldo re-verificado hoy |
|---|---|---|
| Línea literal "forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory)" y su exclusividad en qwen35moe/gemma4moe (§3.1, §0) | ✔ VERBATIM | Issue #21831 leído hoy: la línea de log exacta, el repro con 18 tokens, y el análisis de asg-3d (14-Abr-2026): *"The 'forcing full prompt re-processing' error is exclusive to hybrid architectures (e.g., qwen35moe, gemma4moe) that utilize recurrent layers... Pure Transformer models (e.g., qwen2) are unaffected"* con tabla A/B qwen35moe vs qwen2 |
| El repro original de #21831 estaba VICIADO (18 tokens = solo el mensaje nuevo; stateless) (§11.6, §13) | ✔ VERBATIM | particula.tech leído hoy: *"The second logged prompt_tokens: 18, so the body carried only the new message, and /v1/chat/completions is stateless... The answer text is not [evidence]. Send the full history every turn"* — el texto coincide palabra a palabra con nuestro registro |
| Checkpoints exigen contexto FULL/RS/n_swa>0; TODO del source admite rango mal calculado para SWA (§11.6) | ✔ VERBATIM | particula.tech: *"the context must be FULL, be RS, or the model must have n_swa > 0"* + cita del TODO literal *"here we incorrectly deterimne that the saved checkpoint data covers the [pos_min, pos_max] range / this is not true for SWA models"* |
| Protocolo curl (time_starttransfer, stream:true, 8 turnos, sano = "restored context checkpoint" + TTFT plano) (§3.3, §13) | ✔ VERBATIM | El script bash del propio blog particula.tech coincide con el protocolo registrado (mismo endpoint, misma métrica, mismos veredictos sano/roto) |
| Culpables de rotura de prefijo: reasoning strippado, tools en otro orden, historial reescrito; `<think>` rompe incluso con `-rea off` (§3.2, §11.6) | ✔ VERBATIM | particula.tech: *"reasoning traces stripped from earlier turns, tool definitions regenerated in a different order, and harnesses that rewrite history in place"* + *"even -rea off still trashes context, because the assistant turn emits two <think></think> tokens that get stripped next turn"*; fixes comunitarios en #20225 (mensaje user vacío tras tool_call, fix de plantilla jinja con reasoning_content) |
| #20574: TTFT 4.2 s → 0.3 s (−93%) y +6% TBT con cache host-memory; PR #16391 (§3.2) | ✔ VERBATIM | Tutorial leído hoy (15-Mar-2026): tabla antes/después idéntica (4.2→0.3 s, 32→34 tok/s, +2 GB RAM); *"PR server : host-memory prompt caching #16391 merged October 2025"*; guía `--cram` 64/256/512/0 |
| #21831 sigue activo en la práctica con qwen3.6 (§14) | ✔ EXISTE | Reddit reciente: *"Still an issue for me with qwen3.6"*; workaround `--ctx-checkpoints 69` "reduce, not fix" |
| Workaround `-cpent` NO existe en b11856; fix real exige RUTA 0 o parche (§14) | ◻ + ✔ | El dump [M] (cero ocurrencias checkpoint-every) se mantiene; #21831 confirma que el flag hermano `--checkpoint-every-nb` (PR #20087) era *"currently non-functional in both release binaries and self-compiled builds"* — coherente con nuestra decisión de no contar con él |

### 18.2 Especulación: silencios, timeouts, drift y presupuesto

| Punto (§) | Veredicto | Respaldo re-verificado hoy |
|---|---|---|
| #25345: llama-server IGNORA `-md` en silencio con KV unificada activa (§12) | ✔ VERBATIM | Título exacto del issue leído hoy: *"Misc. bug: llama-server silently ignores -md (speculative decoding never engages) when the unified KV cache is active"* (bug-unconfirmed, closed) |
| #23268: streaming colgado intermitente (<1%) con draft-mtp Y ngram-mod; conexión viva sin EOS; llama-swap 300 s; Vulkan AMD-395 con nuestro modelo UD-Q8_K_XL (§15) | ✔ VERBATIM | Issue leído hoy: todo coincide (comando con `--spec-draft-n-max 6`, ngram-mod 24/48, *"probability of less than 1%"*, *"tasks that exceeded 300 seconds"*); cerrado sin fix documentado |
| MTP en uso real: RAM 95% + swap + timeouts a las ~3 h, dual 3090 (§12) | ✔ VERBATIM | xhinker Medium (21-May-2026): *"Then three hours later, your server RAM is at 95%, swap is churning, and your agent is timing out on every tool call"* |
| vLLM #38182: hit-rate del prefix cache cae 92→71% con MTP; con cache off: TPOT −21.6%, TTFT −31.4% (§14, N5 §13) | ✔ VERBATIM | Issue vivo hoy (25-Mar-2026): *"prefix-cache hit rate for Qwen3.5 drops significantly if mtp is enabled... only speculative decoding methods based on hidden states tend to yield lower prefix cache hit rates"* (cifras exactas registradas en ronda 6 vía estudio thc1006 v3) |
| Aceptación cae con la profundidad: n2 óptimo, n4 ya pierde (§15, coherencia con N5 v4) | ✔ VERBATIM (nueva fuente) | Benchmark ajeno con nuestro modelo exacto (MXFP4, 24 GB): sin MTP 91.4 → n2 111.1 t/s (+22%, accept 76.1%) → n3 98.8 (+8%, 58.5%) → **n4 87.6 (−4%, 44.4%)** — replica de forma independiente la forma de la tabla v4 de thc1006 (MTP-n2 +22.7%, accept 78.4%) |
| PR #19493 speculative checkpointing fusionado (§11.5) | ✔ EXISTE | Reddit "llama.cpp speculative checkpointing was merged" (1sprdm8) vivo; dosis ngram-mod de la lectura de ronda 3 |
| Drift de salida MTP: 7/50 idénticas, 34 vs 33 = ruido; greedy para matching exacto (§15) | ◻ | Fuente mauriziofonte.it no re-abierta hoy; el principio (verificación en lote ≠ decodificación 1-a-1; no esperarlo bit a bit) lo corrobora la docs oficial ("use greedy sampling when exact output matching is required", registrada ronda 7) y la ausencia total de contradicciones |
| Defaults b11856 ≠ master (n-max 16 vs 3; p-min 0.75 vs 0.00) [M] (§15) | ◻ + ✔ | Seguimos fijando ambos flags explícitos; la discusión #25198 (p-min 0.8 + n-max 8-16 en coding: 47→163-225 t/s en 27B) confirma que el knob p-min existe y es potente en builds nuevos |

### 18.3 Alias de carga, sistema y tooling

| Punto (§) | Veredicto | Respaldo re-verificado hoy |
|---|---|---|
| Muerte de `--no-mmap`/`--mlock`: plegados en `-lm` y luego eliminados → `error: invalid argument` (§14, §17) | ✔ VERBATIM | openclawdc actualizado 15-Sep-2026: *"--no-mmap and --mlock no longer exist. llama.cpp merged them into -lm, --load-mode and then removed the old spellings, so older command lines now fail with error: invalid argument"*; manpage Debian lista `-lm auto|none|mmap|mlock|mmap+mlock|dio` (mismos modos que el dump [M]) |
| `-lzm` lazy auto = solo tensores >4 GiB; no aplica al 3.6 (N4 §6) | ✔ VERBATIM | Manpage Debian: *"auto: on, but only for tensors larger than 4 GiB"* — coincidente con el dump |
| `-ngl` default 'auto' ya en b11856 (§17) | ✔ VERBATIM | Manpage: *"-ngl... either an exact number, 'auto', or 'all' (default: auto)"* |
| op-offload: umbral 32 tokens default; `-ub` amortiza copias; ik usa 32×total/activos (§17, §13) | ✔ VERBATIM | Doctor-Shotgun: *"the default required batch size to trigger this operation is 32 tokens, while in ik_llama.cpp, this threshold is 32 * total_experts / active_experts tokens"*; recomienda `-b 4096 -ub 4096` (nuestra regla: NO copiar sin medir en 4 GB queda en pie) |
| "Solo -fa y -ub compran velocidad cuando el modelo cabe" (§14, §17) | ✔ VERBATIM | openclawdc (en ambas guías) y coherencia total con el CSV propio [M] |
| Cliff silencioso 5090: 54/64.5/69.4/27.5 (N4 §13, citado aquí) | ✔ VERBATIM | openclawdc leído hoy con los 4 números exactos y la causa *"the allocation silently falls back to system memory"* |
| Sysmem Fallback Policy (driver 546.01, Oct-2023) y mecánica WDDM (§11.1) | ✔ EXISTE (mecanismo) | La mecánica del spill silencioso WDDM queda hoy triple-fuente: issue #9964 (*"pushed to shared GPU memory... incredibly slow due to memory speed"*), openclawdc y guías dedicadas; la KB a_id/5490 y el foro Crovella quedan de las lecturas de ronda 3 |
| GUIDs powercfg 8c5e7fda/381b4222/e9a42b02 (§11.2) | ◻ | Documentación MS de ronda 3; sin cambios |
| v0.7.0: chat session API, restore de slots/prompt-cache "mucho mejor", puerto 9931, mtmd en MTP (§15) | ✔ VERBATIM | Notas oficiales leídas hoy: *"The server gets a refactored chat session API (common_chat_session, part-based formatted output), much better slot and prompt-cache restore behavior... a new default port (9931)"* |
| SPEED-Bench en master (§15) | ◻ | Registrado ronda 7; no re-buscado hoy |
| Timeline b11747/b11552/b11456/b11869/b11888 (§13) | ◻ | De release history ronda 5; coherente con las fechas 0.6.0=05-Oct y 0.7.0=15-Oct re-confirmadas hoy |
| thc1006 v4: 3002 arm-runs, varianza 9.4 pp, checker anti-drift, commit 3737e4137 (§13) | ✔ VERBATIM | Repo leído hoy: *"llama.cpp speculative decoding measured on one RTX 3090, Qwen3.6-35B-A3B UD-Q4_K_XL, commit 3737e4137. Published figures are re-derived from the committed data by a checker that fails on drift"*; discusión #14 de unsloth muestra las líneas "skipping speculative decoding" y el cross-check en master bcb5eeb64 |

### 18.4 Estado [M]/[T] y protocolo

- **[M dump b11856]**: defaults (32/slot, 8192, cache-ram 8192, prio 0, poll 50, fit ON/fitt 1024, cache-reuse 0, shift OFF, n-max 16, p-min 0.75, -cd/-ctkd/-ctvd presentes) — respaldados por la doble lectura dump+manpage donde el flag existe en ambas; los defaults específicos del build siguen siendo autoridad local (la manpage es de master).
- **[M CSV]**: ORO-UB1K +26.5% prefill, CRAM512/SHIFT neutros, afinidad −9..−38% — datos propios, intocados; la regla "mediana de 3, baseline matcheado, no perseguir <5pp" queda respaldada por el estudio v4 (varianza 9.4 pp) y por el benchmark ajeno MXFP4 (misma forma n2>n3>n4).
- **Protocolo SIN cambios**: combo ganadores + curl protocol + `-ctxcp 4` + traducción `-lm` obligatoria tras RUTA 0.

*Referencias de esta auditoría: github issues #21831 (con análisis asg-3d), #20225, #25345, #23268, #9964, #24055; github discussion #20574; particula.tech (blog completo); reddit 1qzitx1, 1sprdm8; xhinker Medium (MTP bug); vLLM issue #38182; thc1006/qwen3.6-speculative-decoding-rtx3090 y unsloth discussion #14; benchmark MXFP4 24GB (comentario público); openclawdc flags-explained y moe-offload-flags; Doctor-Shotgun HF blog; manpages.debian.org llama-server.1; notas oficiales v0.7.0; discusión #25198.*

---

## 19. ANEXO — Undécima ronda: el instrumento de la cosecha materializado (2026-10-28)

Contexto: el Director aparca el diagnóstico de velocidad de las rondas 25-26 ("dejemos de lado el diagnostico, que hacemos") y LAIA pasa al siguiente paso del orden aprobado (Ronda 12: N1 → N3 → N2 → N4): materializar el instrumento que cosecha lo que ESTE documento declara pendiente desde SS8.1 y SS13 ("estado de las rondas": (1) combo ganadores juntos, (2) `--cache-reuse 256` + `-ctxcp 4` + validación de checkpoints con el curl protocol). El diagnóstico NO se borra: queda listo en el repo para cuando se quiera correr.

### 19.1 El instrumento y su decisión de diseño más importante

- NUEVO `InformacionCritica/scripts/barrido-n3-eficiencia.py` v1.0 (proto `faseN3-v1`): **13 configs**, cada una = RECETA DIARIA (config.txt `FLAGS_BASE` + `FLAGS_GANADORAS` = ORO-UB1K, auditoría R24) + `-lv 4` (para que el log deje los certificados de cache) + diff propio. Mismo esqueleto del barrido N1 (SS8 verbatim, CSV reanudable, informe automático), con los instrumentos nuevos de certificado del N3.
- **La ancla de esta sesión ES la receta diaria.** No se compara contra el ancla de laboratorio (barrido-30, base sin UB1K): si una dosis no le gana a lo que el Director USA HOY, no entra en config.txt. Es la aplicación directa de la regla thc1006 (SS13: "baseline matcheado DENTRO de cada corrida, nunca contra el ancla de otra sesión").

### 19.2 La escalera (13 configs, traducción ejecutable de §8.1/§11.7/§13)

| id | config | diff | Qué cosecha / certificado |
|---|---|---|---|
| 1 | N3-ANCLA | — | control de sesión = vida real del Director; sin reuse el híbrido puede mostrar "forcing full re-processing" (#21831): comportamiento de HOY, no fallo del barrido |
| 2 | N3-CRAM512 | `--cache-ram 512` | la dosis medida segura [M ORO-CRAM512 21.57, −7.7 GB]; certificado = RAM libre/proceso sube |
| 3 | N3-CTXCP4 | `-ctxcp 4` | checkpoints 32→4, ~63 MB/checkpoint GDN → libera ~1.5-1.8 GB [T §10.2/§12]; certificado = WorkingSet del proceso |
| 4 | N3-CMS1024 | `-cms 1024` | cadencia de checkpoints para chat continuo (default 8192, §10.1) |
| 5 | N3-REUSE | `--cache-reuse 256` | LA JOYA (§3): certificado triple = warning de arranque (#24055) + líneas de log + TTFT plano del repro |
| 6 | N3-SHIFT | `--context-shift --cache-reuse 256` | familia ORO-SHIFT verbatim [M 21.39 sin coste]; para conversaciones largas |
| 7 | N3-NP2 | `-np 2` | +14% agregado [M §4] con concurrencia; ctx 16384 → 8192/slot; SOLO sin spec (§11.4) |
| 8 | N3-NCM37C4-UB | `-ncmoe 37 -c 4096 -ctk q4_0 -ctv q4_0` | colocación campeona [M 22.49 SIN UB1K] APILADA con la receta diaria: PRIMER dato del stack UB1K×NCM (pendiente SS13-1) |
| 9 | N3-COMBO-R | cram512 ⊕ ctxcp4 ⊕ cms1024 ⊕ reuse ⊕ shift | combo RAM seguro sobre la vida real, sin tocar colocación: la candidata natural a config.txt |
| 10 | N3-COMBO-T | NCM37C4 ⊕ cram512 ⊕ ctxcp8 ⊕ cms1024 ⊕ reuse ⊕ shift | combo ganadores SS8.1/§11.7 completo (expectativa decode ~22.5-23.5 [T]); control de sesión = id 8 |
| 11 | N3-NP2-C | np2 ⊕ cram512 ⊕ ctxcp8 ⊕ cms1024 ⊕ reuse ⊕ shift | combo slots §11.7 sin NCM (8192 ctx/slot); para 2 sesiones a la vez |
| 12 | N3-NOCACHE | `--no-cache-prompt` | control del A/B cache (§14): DEBE crecer el TTFT; separa el efecto cache del efecto decode |
| 13 | N3-ANCLA-FIN | — | bookend (lección v1.2.1 del N1): deriva de sesión ±5% |

Bloques CLI: `--solo ancla,ram,cache,slots,ncm,combo,ctrl,anclafin`; `--quick` = ids 1,5,9,10,13 (~18 min); corrida completa ~35-45 min.

### 19.3 Los instrumentos nuevos (cada dosis con su testamento)

- **Repro TTFT (el curl protocol materializado, §3.3/§13):** conversación de 6 turnos crecientes con prefijo ESTABLE (lo inmutable arriba, regla §3.2), `stream:true`, TTFT = tiempo al primer chunk (proxy del `time_starttransfer`). Criterio honesto: crecimiento t2→tfin ≤ +50% = PLANO; ≥ +100% = CRECE; entre medias GRIS; el turno 1 (frío) se descarta. `N3-NOCACHE` es el control que DEBE crecer — si no crece, el medidor está roto.
- **Certificado de cache por líneas de log (§3.3/§10.3/§14):** `"cache_reuse is not supported"` en el arranque → NO-SOPORTADO (#24055, la vía queda condicionada a build/colocación); `"restored context checkpoint"` sin forcing → SANO; `"forcing full prompt re-processing"` sin restored → ROTO (#21831, el híbrido re-paga); ambos → MIXTO. Nada de fe: el log manda.
- **RAM (los certificados de CRAM512 y CTXCP4):** RAM libre del sistema vía GlobalMemoryStatusEx + WorkingSet del proceso vía Get-CimInstance, antes/después de la medición. Piezas se saltan solas fuera de Windows (nunca mueren; en la batería se registran las columnas igual).
- **Probe de concurrencia:** 2 POST simultáneos (hilos) → tokens agregados/s. El +14% [M §4] de `-np 2` SOLO existe con concurrencia real: sin este probe el knob sería fe.
- **Grep gratis del arranque:** `system_info:` con `USE_GRAPHS = 1 | REPACK = 1` (§11.6) — autentica que el build activo tiene CUDA graphs y repack (+5% medido [M]).
- **Lo que NO se re-mide:** el libro de muertos de §7/§12/§17 (ngram spec acceptance 0.00-0.16, afinidad −9..−38%, FIT-C −38%, repack off −5%, KV q5_1 0%, POLL ruido, TB8 muerto). Re-medir muertos es perder tiempo de GPU.

### 19.4 Protocolo, auditoría y promoción

- SS8 verbatim (4 pasadas × 256 tok, descarta la 1ª, temp 0, seed 424242, pausas térmicas 60 s cada 8, CSV reanudable, ruido ±0.3-0.5) + regla thc1006 v4 (9.4 pp): las celdas que GANEN se confirman con mediana de 3 antes de proclamar la ganancia; deltas <5pp no se persiguen.
- Auditoría de flags verbatim contra el dump ANTES de arrancar (FATAL si falta uno) — `DUMP_REQUERIDOS` ampliado con los 12 tokens N3 (`--cache-reuse`, `-cram,`, `--cache-ram`, `-ctxcp,`, `--ctx-checkpoints`, `-cms,`, `--checkpoint-min-step`, `--context-shift`, `-np,`, `--parallel`, `--cache-prompt`, `--no-cache-prompt`, `-kvu,`, `--kv-unified`), todos verificados verbatim en `llama-flags-nuevo.txt` (dump b11856) el 28-oct-2026. Valores legales nuevos: `-ctxcp/-cms/--cache-ram/--cache-reuse/-np` con entero. PROHIBIDAS intactas (aquí NO hay spec).
- Guardarrails heredados del N1: puerto ocupado = FATAL (`--si` lo mata), identidad del server por log (nunca un fantasma), fit abortado vs declinado (lección v1.2.1), VRAM >3700 MiB = aviso sysmem, sanity auto de 3 pares (humo-detector).
- **PROMOCIÓN con certificado:** el informe (`faseN3-INFORME.md`) emite las candidatas a config.txt con su evidencia (el protocolo de decisión automático evalúa bookend, familia RAM, familia cache, slots, NCM apilada y combos). La promoción formal = el Director edita UNA línea de `FLAGS_BASE` (pago del config central, ronda 20). Si la cache sale NO-SOPORTADO o ROTO en b11856: queda registrado como **MOTIVO DE RUTA 0** (build nuevo con cpent/fix), no como fracaso de la idea.

### 19.5 Verificación (batería de la casa)

- NUEVO `tests/test_barrido_n3_mock.py` — **40 checks TODO VERDE** (13 unitarios + 27 E2E). El fake llama-server (ThreadingHTTPServer, mismo patrón test_barrido_mock) reproduce los DOS mundos del híbrido: con `--cache-reuse` imprime "restored context checkpoint" y TTFT plano; sin cache imprime "forcing full prompt re-processing" y TTFT crece; `--no-cache-prompt` calla y TTFT crece. Cubre: corrida completa 13/13 válida, certificados por config (SANO solo en 5/6/9/10/11), forcing contado en el ancla, sanity 3/3, repro/agg/RAM en CSV+JSON, informe con bookend estable / joya certificada / COMBO-R candidata #1 / control NOCACHE crece, resume 2ª corrida salta las 13, `--solo ram` = 3, `--quick` = 5, `--sin-ttft` vacío, warning #24055 → NO-SOPORTADO + "RUTA 0 gana un motivo" en el informe, puerto ocupado FATAL, server inexistente FATAL, dump podrido FATAL.
- Regresión: `py_compile` OK en todos los .py de scripts/ y tests/; test_abrir_mock 11/11, test_chatear_mock E2E, test_barrido_mock, test_diagnostico_mock TODO VERDE; test_faseD_n1 SIN TOCAR (batería lenta, verde en ronda 23). Cero cambios en configs/config.txt, .bat, lanzador, cliente, barrido N1 o diagnóstico.

### 19.6 Para el rig (uso)

- Copiar `barrido-n3-eficiencia.py` a `D:\ZLia\`, cerrar el server, `py barrido-n3-eficiencia.py` (~35-45 min) o `--quick` (~18 min); NO chatear durante la corrida. Al final: pasar `faseN3-INFORME.md` + `faseN3-resultados.csv` (+ `logs-config/` si se pide) al análisis.
- Duración estimada por config ~2.5-3 min (carga ~35 s + medición SS8 + sanity + repro de 6 turnos + probe). Con `--sin-ttft` se recorta el repro si algún día solo interesa decode.

*Referencias de esta ronda: todo el bloque cache de este documento (§3, §10, §11.6-11.7, §12, §13, §14, §18); config.txt ronda 20; auditoría R24 de la receta diaria; thc1006 v4 (varianza 9.4 pp); issues #21831/#24055/#25345; discusión #20574; particula.tech (protocolo curl).*

## 20. ANEXO SS20 — PREVUELO COMPLETO: `barrido-n3-eficiencia.py` v1.0 → v1.1, TODO LO QUE HAY QUE SABER DEL PC, DEL MODELO Y DEL NIVEL ANTES DE MEDIR (ronda 29, 28-oct-2026)

> Pedido del Director: *"añadele mas cosas al barrido eficiencia, hazlo completo con todo lo que va a necesitar saber sobre mi pc el modelo y todo sobre el nivel en el que estamos antes de comenzar"*. Decisión de diseño: el informe deja de empezar con un pre-vuelo de 6 líneas y pasa a abrir con un **DOSSIER completo (sección 0)** que se construye ANTES de medir la primera config — para que cualquier resultado de esta corrida se pueda leer con el contexto completo a la vista, sin depender del repo ni de la memoria. Cero cambios en las 13 dosis, el protocolo de medición, el CSV ni el proto (`faseN3-v1` intacto → el resume sigue funcionando). Todo el dossier es NO-FATAL: si una pieza no existe (fuera de Windows, sin nvidia-smi), queda la nota "no disponible" y el barrido sigue.

**1. Estación 0.1 — el PC (hardware y estado del día).** Vía `Get-CimInstance` (PowerShell, stdlib-only): SO (Caption/arquitectura/build), CPU (nombre, núcleos/hilos, MHz máx), **RAM por módulo** (n sticks, GB cada uno, MT/s configurados — verifica el dual channel), **pagefile** (reservado/en uso/pico — el indicador directo del riesgo detectado en la ronda 28), **discos** (libre/total por unidad — el modelo, los logs y los checkpoints viven en D:), GPU extendida (nombre, driver, MiB, °C vía nvidia-smi), plan de energía (powercfg), RAM del momento + **los 4 comepanes de RAM** (top procesos por WorkingSet — explica DÓNDE se fue la RAM del 97% del 27-oct) y **uptime de la máquina** (encendido ≥12 h → nota de día largo). Consola: ~8 líneas; informe: detalle completo.

**2. Estación 0.2 — el modelo (identidad certificada).** Tres capas: (a) **bytes** contra los esperados de RutasArchivos (ya existía, ahora vive aquí); (b) **SHA256 en streaming** del archivo completo (~1 min en el rig; certifica EL archivo exacto y cierra la cadena de descarga — el mismo certificado que el N2 exige, disponible desde el N3 sin trabajo extra; `--sin-sha256` lo salta); (c) **parser GGUF propio** (cabecera only, cero tensores, buffer 1 MiB lección ronda 14): lee los kvs de interés — `general.architecture/name/size_label/file_type`, `expert_count`, `expert_used_count` (de FÁBRICA, con nota recordando que el barrido mide k=8 de fábrica y CHARLA usa override a 4 en el arranque diario), `context_length`, `block_count`, head_count KV, **claves nextn** (MTP preserved visible en el informe) — y SALTA sin materializar los arrays enormes (tokenizer = decenas de miles de strings) ni los strings >64 KiB (chat_template). Más el **pin del server** (`--version`, build esperado 11856). Si el archivo no es GGUF legible → nota limpia, nunca crash.

**3. Estación 0.3 — la receta viva + auditoría.** El pre-vuelo minimal de la v1.0 (server, pin, auditoría VERDE, comando base) vive dentro de esta sección del dossier. Sin cambios de comportamiento.

**4. Estación 0.4 — el nivel N3 (dónde estamos y qué cosecha esta corrida).** Constantes incrustadas en el script (el rig corre SIN el repo): **campaña** (orden aprobado ronda 12: N1 → N3 → N2 → N4 → RUTA 0 + N5, con el estado de cada nivel); **referencias [M]** (ORO-UB1K 21.53 receta diaria · NCM37C4 22.49 · ORO-CRAM512 21.57 · ORO-SHIFT 21.39 · k=4 28.85/29.13 · suelo k=8 17.36/17.80 · techo familia 21.50 · ruido ±0.3-0.5 y 9.4 pp thc1006); **libro de muertos** (ngram, afinidad, FIT-C, repack, q5_1, POLL/TB8 — NO se re-mide); **pendientes que esta corrida cosecha** (stack UB1K×NCM = id 8, combos = ids 9/10/11, cache con certificados = ids 5/6 + repro TTFT, control NOCACHE = id 12); **protocolo de decisión** (bookend ±5%, mediana de 3, <5pp no se persigue, promoción = UNA línea de FLAGS_BASE aprobada por el Director, cache NO-SOPORTADO/ROTO = motivo RUTA 0, sanity 20 prompts = juez de calidad); y las **13 configs del día** listadas con familia.

**5. Estación 0.5 — el día (recordatorio R28).** El hallazgo de la ronda 28 viaja dentro del informe: 17.29 t/s = día lento dentro del lab, RAM al 97% (0.40 GB libres) = culpable confirmado; antes de medir, cerrar apps — si no, el barrido mide el pagefile, no la receta.

**6. Batería: 40 → 55 checks TODO VERDE.** 8 unitarios nuevos (U14 parser GGUF sintético construido byte a byte en el test — kvs escalares + string de 70 KB que se salta + array de strings del tokenizer + clave nextn; U15 chat_template fuera de los metadatos; U16 no-GGUF → error limpio; U17 sha256 == hashlib; U18 dossier_nivel completo; U19 _ps_json nunca fatal; U20 dossier_modelo certifica bytes+sha+gguf+build; U21 md_prevuelo pinta las 5 secciones con "no disponible" graceful) + 7 E2E nuevos (E28 informe con las 5 secciones, E29 sha256 de 64 hex en el informe, E30 cabecera GGUF no-leible como nota, E31 nivel completo en el informe, E32 consola anuncia el prevuelo, E33 `--sin-prevuelo` = comportamiento v1.0 exacto, E34 `--sin-sha256` = prevuelo sin hash). Regresión: test_abrir 11/11, test_chatear E2E, test_barrido_mock, test_diagnostico_mock TODO VERDE; py_compile OK en scripts y tests; test_faseD_n1 sin tocar.

**7. Para el rig (cambia poco):** mismo uso que la v1.0 — el prevuelo añade ~1-2 min al inicio (sha256 del modelo de 14.27 GB). `py barrido-n3-eficiencia.py` / `--quick` / `--solo ...` igual que siempre; `--sin-prevuelo` recupera el comportamiento exacto v1.0; `--sin-sha256` solo quita el hash. Cero cambios en configs, .bat, lanzador, cliente, barrido N1 o diagnóstico.

## 21. ANEXO SS21 — HOTFIX DE CAMPO v1.1 → v1.2: LA PRIMERA CORRIDA REAL DEL PREVUELO CAZA UN CRASH EN EL DOSSIER (ronda 30, 28-oct-2026)

> El Director estrenó la v1.1 en el rig (D:\ZLia, puerto 9931). FASE 0, auditoría de flags: **VERDE** (13 configs, todos los tokens verbatim en el dump b11856, cero prohibidas — la auditoría pasa su primer examen en campo). En la FASE 0.5, dentro de `dossier_pc`, crash limpio: `TypeError: not all arguments converted during string formatting` en la línea 920. El barrido murió ANTES de arrancar el primer server: cero configs medidos, cero toques al sistema, nada que rescatar ni limpiar (el CSV ni llegó a crearse). Es el precedente del N1 repetido: **la primera corrida real es el examen final** — y otra vez el examen encontró lo que el mock no podía ver.

**1. Causa raíz (clase nueva de bug: literal partido en dos statements).** El literal se escribió partido en dos líneas SIN paréntesis:
```python
d["ram_hardware"] = "%d modulos x %s GB a %s MT/s (dual channel si "
"son 2)" % (len(palos), ...)
```
La primera línea es un statement COMPLETO (asigna un string con 3 placeholders que nadie formatea); la segunda queda como statement huérfano `"son 2)" % (3 args)` — 0 placeholders vs 3 argumentos → TypeError en cuanto la rama se ejecuta. Sin paréntesis que abarquen las dos líneas, Python no concatena los literales. El gatillo exacto: el rig del Director tiene **2 palos de RAM** (la rama de `Win32_PhysicalMemory`), y los tests en Linux no podían ejecutar esa rama JAMÁS porque `_ps_json` real devuelve None fuera de Windows → **la rama Windows del dossier era territorio sin testear**. Fix: paréntesis alrededor de (literal + % args), con comentario en el código.

**2. Falso positivo descartado (honestidad de registro).** Durante la auditoría se sospechó de la consulta de los comepanes (la función math de PowerShell dentro del CalculatedProperty). Verificación byte a byte EN PROCESO (conteos con strings construidos carácter a carácter, inmunes a la capa de visualización): la v1.1 ya traía esa línea BIEN — la apariencia de bug era un espejismo del taller (su capa de salida se come los pares corchete-m), no del archivo. Cero cambios en esa línea; un comentario de hotfix insertado por error se retiró en la misma ronda (el código queda limpio, el descarte queda registrado aquí y en el worklog).

**3. La vacuna: el detector permanente de la clase entera.** La batería incorpora una **auditoría AST de cadenas de formato** que recorre TODOS los scripts de `InformacionCritica/scripts/` (hoy 11) en cada corrida y caza: (a) statements `"..." % (...)` huérfanos cuyo resultado se tira (el crash de esta ronda); (b) literales sueltos como statement sin ser docstring (la misma clase en su forma pura); (c) aridad placeholders vs args (tupla literal; soporta `%%`, anchura/precisión con `*` y mapping `%(x)s`; salta lo no verificable: variables, `tuple(...)`, `dict(...)`). Verificado hoy: **11/11 scripts LIMPIOS**. La clase del crash no puede volver a colarse en ninguna ronda futura sin que la batería la grite.

**4. La rama Windows por fin ejecutada en test (U22/U23).** Nueva `_ps_falsa_ram` que inyecta en `_ps_json` datos REALISTAS del rig y ejecuta `dossier_pc` de verdad: 2 palos de 8 GB @ 3200 → `2 modulos x 16.0 GB a 3200 MT/s (dual channel si son 2)` SIN crash (la línea exacta del crash de campo, ejecutada y validada); 1 palo sin MT/s → `1 modulos x 8.0 GB a ? MT/s` (degradación elegante con "?"). U24 congela además la consulta de comepanes (que siga con su función math de fábrica) y exige 0 hallazgos del auditor AST.

**5. Batería 55 → 58 TODO VERDE + regresión.** U22 (2 palos rig real), U23 (1 palo sin velocidad), U24 (auditoría AST = 0 hallazgos en los 11 scripts). Regresión completa: test_abrir_mock 11/11, test_chatear_mock E2E, test_barrido_mock, test_diagnostico_mock TODO VERDE; py_compile OK en 17 archivos; test_faseD_n1 SIN TOCAR. VERSION v1.1 → v1.2 (y título del docstring); proto faseN3-v1 y CSV intactos — el resume ni entra en juego: la v1.1 murió antes de crear nada.

**6. Para el rig.** Re-copiar `barrido-n3-eficiencia.py` v1.2 a `D:\ZLia\` y repetir el mismo comando. Nada más cambió: las 13 dosis, el protocolo, el dossier y los flags son EXACTAMENTE los de la v1.1 (solo la línea de RAM se re-ensambló y la batería creció).

## 22. ANEXO SS22 — HOTFIX DE CAMPO v1.2 → v1.3: LA PRIMERA CORRIDA COMPLETA DEL BARRIDO MATA 11 DE 13 CONFIGS (ronda 31, 28-oct-2026)

**Lo que pasó en el campo (27-oct 20:26–20:32, D:\ZLia, puerto 9931).** La primera corrida COMPLETA de la v1.2 en el rig: el PREVUELO entero funcionó perfecto (dossier del PC con RAM al 24% — la regla R28 de cerrar apps APLICADA y certificada en el propio informe; dual channel confirmado; pagefile sano; modelo con bytes exactos + SHA256 `e4eae0e2…18d4` = **el certificado del N2 obtenido gratis desde el N3**; build 11856 pin OK), la FASE 0 auditoría de flags VERDE por segundo día consecutivo… y luego **11 de las 13 configs murieron durante la carga en ~2.5 s** (exit 1, "carga fallida: el server murio durante la carga (fit abortado: VRAM insuficiente para esta config)"). Solo sobrevivieron **id 8 (NCM37C4-UB: 18.78 t/s)** e **id 10 (COMBO-T: 19.72 t/s)**. La ANCLA (id 1 = la receta diaria que funciona TODOS los días) murió también, y con ella el bookend (id 13): **sin ancla de sesión, todo el protocolo de decisión quedó sin pata** (deltas N/D en todo el informe).

**Causa raíz (verificada contra el repo, no contra la memoria).** `BASE_FLAGS_FIJAS` (línea 153 de la v1.2) decía en su comentario ser "config.txt FLAGS_BASE materializada (auditoría R24: comando idéntico al que lanzan los .bat)"… pero al transcribirla en la R27 **se cayó el token `-cmoe`**. config.txt línea 26: `-ngl 99 -cmoe -c 16384 …`. La v1.2 lanzaba: `-ngl 99 -c 16384 …` SIN colocación → el comando pedía poner los 256 expertos (14.27 GB de modelo) EN la GPU de 4 GB → muerte instantánea en la reserva de VRAM. Los únicos sobrevivientes fueron los únicos que llevaban su propia colocación (`-ncmoe 37` = 37 capas de expertos en CPU RAM → huella 3128 MiB → cabe). La clasificación "fit abortado: VRAM insuficiente" del barrido era TÉCNICAMENTE CIERTA — lo que nadie sabía era que la receta estaba coja.

**Por qué pasó tres controles (lección de sistema, no de descuido).** (1) La auditoría de flags verifica que cada token del comando EXISTA en el dump b11856 — no que el comando contenga LA RECETA COMPLETA: un comando al que le falta una palabra pasa VERDE igual. (2) El server falso de la batería aceptaba cualquier comando: la receta coja corría 13/13 en el taller. (3) La lección del laboratorio YA ESTABA ESCRITA y no se consultó: barrido-qwen-30.py líneas 128-146: *"el -cmoe/-ncmoe va POR CONFIG (así FIT/NCM pueden probar -ncmoe sin que el -cmoe general lo anule: en b11856 ambos flags juntos = gana el general)"* + *"TODA config estática debe traer -cmoe o -ncmoe"*. La v1.3 materializa exactamente esa regla.

**Los cuatro arreglos de la v1.3.** (1) **COLOCACIÓN POR CONFIG**: `add()` de `construir_configs()` inyecta `-cmoe` en toda config que no traiga `-ncmoe` (11 configs: ANCLA, bookend, RAM×3, CACHE×2, NP2, COMBO-R, NP2-C, NOCACHE); NCM37C4 y COMBO-T conservan `-ncmoe 37` verbatim del barrido-30 (jamás llevarán `-cmoe` general: lo anularía). (2) **CERTIFICADO DE RECETA** (`verificar_receta` + `CERTIFICADO_RECETA`): el comando final del ANCLA DEBE contener los 12 items exactos de la receta diaria (config.txt FLAGS_BASE + FLAGS_GANADORAS con -ub 1024/-b 4096 pisados) o **FATAL antes de medir nada** — la auditoría de tokens y el certificado de receta ahora son capas distintas y complementarias. (3) **Regla barrido-30 materializada** (`verificar_colocacion`): todo comando final necesita `-cmoe` o `-ncmoe` o **FATAL** (nombra las configs malas). (4) **ANCLA MUERTA = FATAL inmediato**: si el id 1 no carga, el barrido se detiene al minuto 0 con la cola del log en pantalla (seguir midiendo sin baseline es tirar el día; en el campo la v1.2 gastó 6 configs muertas después de que el destino de la sesión ya estaba sellado) — la fila queda en el CSV y el resume la re-mide sola. Además: **forense en el CSV** — la nota de una carga fallida arrastra ahora las últimas líneas del log del server (`| log: …`), porque en el campo hizo falta abrir el log a mano para diagnosticar.

**Recuperación del campo ya certificada (E36).** `csv_cargar_hechos` solo cuenta filas `valido=SI` (estaba así de fábrica): **re-copiar la v1.3 y repetir el MISMO comando en la MISMA carpeta re-mide solas las 11 configs muertas y conserva los ids 8/10**. E35/E36 lo certifican en el taller: 1 fila inválida → re-run → 13 filas válidas + la muerta como historia (14 filas), rc=0.

**Lo que la corrida muerta DEJÓ (honestidad de cosecha — nada se tira).** (1) Certificado del modelo (SHA256 + bytes) = el certificado del N2 adelantado. (2) **MOTIVO DE RUTA 0 Nº 3 certificado en el campo**: `--cache-reuse` es **NO-SOPORTADO** en el colocación NCM con b11856 (id 10: warning #24055 + forcing×5 + restored×0; el TTFT PLANO 4.23→5.01 s queda invalidado como certificado porque sin cache activa el repro no mide nada — el criterio NO-SOPORTADO manda). (3) **Primer dato del stack UB1K × NCM37C4** (pendiente SS13-1): 18.78 t/s [S] (dispersión 1.026) vs el 22.49 [M] histórico SIN UB1K = **−16.5%** — sugerente de que UB1K estorba en esa colocación, pero PROVISIONAL: sin ancla de sesión y con la regla thc1006 v4 (mediana de 3) sin cumplir. (4) COMBO-T 19.72 t/s (+0.94 sobre NCM37C4-UB de la misma sesión = +5.0%, justo en el borde de los 5pp): **candidata provisional**, con matiz — sus flags de cache están muertos en este build, así que su identidad efectiva es NCM37C4-UB + ctxcp8/cram512/cms1024. (5) El dossier del PC completo del día 27-oct noche.

**Cosmética corregida de paso.** La línea de RAM del dossier decía "2 modulos x 16.0 GB a 2666 MT/s" — se lee como 2×16=32 GB cuando la suma es 16.0 GB TOTAL (2 palos de 8). Ahora: "**2 modulos, 16.0 GB en total a 2666 MT/s** (dual channel si son 2)" (U22/U23 actualizados a la nueva redacción; el dato de campo confirma 2666 MT/s configurados, normal para el i3-10100F).

**Batería 58 → 63 TODO VERDE.** U25 (certificado de receta VERDE en el ancla + una base rota devuelve exactamente los 11 faltantes), U26 (la base de la v1.2 de campo — sin `-cmoe` — es cazada por el certificado), U27 (colocación por config en 13/13 + una config sin ella se nombra), **E35** (ancla muerta → FATAL inmediato, 1 fila inválida, forense "failed to allocate" en la nota), **E36** (recuperación por resume en la misma carpeta). Y la vacuna estructural: **el server falso ahora SE NIEGA a arrancar sin colocación** (sin `-cmoe`/`-ncmoe` imprime "failed to allocate CUDA0 buffer" + "CUDA error: out of memory" y exit 1 = el rig de 4 GB materializado en el taller) — la clase entera del fallo de campo (receta coja) ya NO puede pasar la batería. Regresión: abrir 11/11, chatear E2E, barrido_mock, diagnostico_mock TODO VERDE; py_compile OK; test_faseD_n1 SIN TOCAR. VERSION v1.2 → v1.3 (docstring con la lección completa). Proto faseN3-v1 y columnas del CSV SIN CAMBIOS (el forense viaja dentro de la columna `nota`).

**Para el rig.** Re-copiar `barrido-n3-eficiencia.py` v1.3 a `D:\ZLia\`, cerrar apps (regla R28) y **repetir el MISMO comando en la MISMA carpeta de logs**: las 11 muertas se re-miden solas (~35-45 min), ids 8/10 conservan sus números de la noche del 27, y esta vez el ANCLA carga y el protocolo de decisión queda con pata completa (bookend incluido). La FASE 0 y el certificado de receta se re-ejecutan solos al inicio.

## 23. ANEXO SS23 — COSECHA COMPLETA DEL N3: 13/13 CONFIGS VÁLIDAS, NP2 CAMPEÓN (+22.8% EN UN DÍA LENTO), LOS CERTIFICADOS RAM DE LOS [M] NO SE CUMPLIERON Y EL CONTROL NOCACHE DEJA UNA ANOMALÍA ABIERTA (ronda 32, 28-oct-2026)

**La sesión.** 28-oct 10:27–10:52, `barrido-n3-eficiencia.py` v1.3, puerto 9931, carpeta de logs la MISMA (D:\ZLia\faseD-logs). La recuperación por resume prometida en E36 se cumplió EN EL CAMPO tal cual el taller la certificó: la consola abrió con "resume: 2 ya medidas, 11 pendientes", ids 8/10 conservaron sus números de la noche del 27 ("ya medida (válida), salto") y las 11 muertas se re-midieron solas. **13/13 configs válidas, sanity 3/3 en todas, dispersión ≤1.048 en todas** (bajo el umbral de la casa). El Director entregó los 4 artefactos de campo ("finalizado"), preservados en el repo en `investigacion/niveles-velocidad/evidencia/faseN3-20261028/` (INFORME + CSV de 24 filas con la historia completa de las dos noches + datos.json + consola.log).

**El día (el contexto que manda).** ANCLA (la receta diaria) midió **17.44 t/s** = día LENTO certificado: −19% contra el 21.53 [M] del barrido-30, pero clavado en el suelo histórico de la misma receta (17.36/17.80 [M]) → día dentro de lo esperado, NO un problema nuevo. RAM del día SANA (12.3–13.8 GB libres, 24-25% en uso: la regla R28 de cerrar apps aplicada de nuevo; comepanes normales de Windows ≤318 MB; pagefile pico 3389 MB = hubo pasada por el sótano en algún momento). Bookend **17.44 → 17.74 (+1.7%, dentro del ±5%) = SESIÓN ESTABLE**: los deltas se leen limpios, contra la ancla de HOY (regla de la casa: jamás contra el ancla de otra sesión). El dossier volvió a certificar el modelo (SHA256 `e4eae0e2…` íntegro, bytes exactos, build 11856 pin OK). Observación menor del dossier para el futuro: **C: tiene 13/223 GB libres (6%)** — el pagefile vive en C:; no afectó hoy, pero conviene no dejar que se llene más.

**La tabla de la cosecha (decode t/s, mediana de 3 pasadas, vs ANCLA de hoy 17.44; ruido declarado ±0.3-0.5):**

| # | config | familia | decode | vs ancla | RAM proc vs ancla | VRAM | cache | lectura |
|---|--------|---------|--------|----------|-------------------|------|-------|---------|
| 7 | **NP2** (`-np 2`) | SLOTS | **21.41** | **+22.8%** | +965 MiB | **2096** (−142) | — | **CAMPEONA: día lento → techo de día bueno** |
| 11 | NP2-C (`-np 2` + familia cache) | COMBO | 20.53 | +17.7% | +758 MiB | 2096 | NO-SOP. | el combo ESTORBA −0.88 vs NP2 sola |
| 10 | COMBO-T (NCM + cache) | COMBO | 19.72 | +13.1% | −148 MiB | 3128 | NO-SOP. | stack SS8.1 certifica (+0.94 sobre NCM-UB) |
| 8 | NCM37C4-UB | NCM | 18.78 | +7.7% | +233 MiB | 3128 | — | 18.78 vs 22.49 SIN UB1K = UB1K estorba en NCM (−16.5%, ahora CON ancla) |
| 4 | **CMS1024** (`-cms 1024`) | RAM | **18.34** | **+5.2%** | −80 MiB (plana) | 2238 | — | **GANA con costo cero — candidata barata** |
| 6 | SHIFT (+reuse) | CACHE | 18.26 | +4.7% | +668 MiB | 2238 | NO-SOP. | decode bien; su joya (cache) muerta en b11856 |
| 9 | COMBO-R | COMBO | 18.17 | +4.2% | +868 MiB | 2238 | NO-SOP. | no se promociona tal cual (informe: separar dosis) |
| 2 | CRAM512 | RAM | 17.94 | +2.9% | **+600 MiB** | 2238 | — | **certificado RAM FALLIDO** (empata en decode) |
| 5 | REUSE | CACHE | 17.89 | +2.6% | +164 MiB | 2238 | NO-SOP. | igual que SHIFT: vía condicionada a RUTA 0 |
| 3 | CTXCP4 | RAM | 17.84 | +2.3% | **+308 MiB** | 2238 | — | **certificado RAM FALLIDO** (empata en decode) |
| 12 | NOCACHE (control) | CTRL | 17.60 | +0.9% | +1133 MiB | 2242 | — | decode igual al ancla (esperado); **TTFT PLANO inesperado** ⚠ |
| 1/13 | ANCLA → ANCLA-FIN | ANCLA | 17.44 → 17.74 | bookend +1.7% | — | 2238→2242 | — | sesión estable, deltas limpios |

Prefill de la sesión: ANCLA 17.3 → **NP2 25.6 (+48%)**, NP2-C 23.9, SHIFT 23.2, COMBO-T 24.8 — la familia slots/NCM digiere prompts mucho más rápido (menos KV por slot / menos capas de expertos en GPU). Probe concurrente NP2: 2 pedidos simultáneos = **20.8 tok/s agregados vs 17.8 del ancla (+16.6%)** — la concurrencia de SS4 queda certificada en el campo.

**HALLAZGO 1 — NP2 es el plato fuerte de la cosecha.** Solo `-np 2` (dos mesas en vez de una, el contexto se reparte 8192+8192) llevó el decode a **21.41 t/s en un día que sin eso medía 17.44** — o sea: **el día lento alcanzó el TECHO de los días buenos (21.5)**. Tres pasadas casi clavadas (21.49/21.41/21.32, dispersión 1.008, la más limpia de la sesión), VRAM más BAJA que la ancla (2096 vs 2238 MiB — menos KV por slot), prefill +48%, concurrencia certificada. Mecanismo exacto [H] sin confirmar: NO es "libera RAM" (el WorkingSet SUBE +965 MiB); lo plausible es que el reparto del contexto alivia la presión del híbrido — lo que importa es el número, la mediana de 3 lo confirmará. **CANDIDATA Nº 1 a config.txt** (una palabra: `-np 2` en FLAGS_BASE), con dos matizes registrados: (a) SS11.4 — solo vale SIN spec (MTP exige `-np 1`; hoy no hay spec en la receta, pero RUTA 0/N5 deberán re-auditarlo); (b) cada sesión queda con 8192 de contexto (sobra para chat, no para documentos gigantes).

**HALLAZGO 2 — el stack SS8.1 certifica, pero hoy pierde contra NP2.** COMBO-T (19.72) GANA +0.94 sobre NCM37C4-UB (18.78) en la misma sesión = el apilamiento de la SS8.1 funciona (+5.0%, justo en el borde de los 5pp). Y con ancla por fin limpia, el dato de la R31 se consolida: **NCM37C4-UB 18.78 vs el 22.49 histórico SIN UB1K = UB1K estorba en la colocación NCM (−16.5%)** — si algún día se quiere la vía NCM, va SIN UB1K (mediana pendiente). Hoy, con NP2 a 21.41, ni COMBO-T ni NCM son candidatas: ceden −1.7 y −2.6 t/s respectivamente y pagan VRAM (3128 MiB).

**HALLAZGO 3 — los certificados RAM de los [M] NO se cumplieron: el barrido hizo exactamente su trabajo.** Las dos promesas grandes de la familia RAM venían de estimaciones: CRAM512 "[M] −7.7 GB" y CTXCP4 "[T] −1.5-1.8 GB". Medido en el rig con la dosis del barrido: CRAM512 **+600 MiB** de proceso (no −7.7 GB) y CTXCP4 **+308 MiB** (no −1.5-1.8) — y el decode de ambas EMPATA con la ancla (+2.9%/+2.3%, dentro del ruido). Conclusión: a estas dosis, ninguna de las dos toca el hambre estructural del modelo (14.27 GB); el certificado que traían escrito no resistió el probador. **NO se promocionan** — y esta es la lección bonita del día: se probó el traje ANTES de comprarlo (si se hubieran aplicado por los [M], hoy habría dos knobs muertos en config.txt). La RAM del 97% de la R28 se combate cerrando apps (regla R28, aplicada y funcionando: día al 24%) y, si hiciera falta más, la palanca real es NP2/NCM (reparto de contexto), no estas dosis.

**HALLAZGO 4 — CMS1024: la única de la familia RAM que gana.** +5.2% con RAM plana (−80 MiB) y cero riesgo aparente (checkpoints de contexto más seguidos en chat continuo). **CANDIDATA Nº 2** — barata, pero pasa por la misma mediana de 3 antes de proclamarse.

**HALLAZGO 5 — el NO-SOPORTADO del cache se GENERALIZA: es el build, no la colocación.** El warning #24055 (declinación de `--cache-reuse`) salió en **5 configs: ids 5/6/9/11 con la colocación `-cmoe` general Y id 10 con `-ncmoe 37`** — en la R31 solo se había visto en NCM. Conclusión registrada: la declinación NO depende de la colocación; es del build b11856 en este contexto. **RUTA 0 acumula motivo Nº 3 (ahora generalizado)**: el build nuevo es la vía para que la joya SS3 (TTFT −93% en prompts repetidos) exista aquí. Nada que decidir hoy: la vía queda condicionada y documentada.

**HALLAZGO 6 (ANOMALÍA ABIERTA) — el control que debía crecer no creció.** NOCACHE (`--no-cache-prompt`: sin cache de prompts TODO turno re-paga el prompt) debía mostrar TTFT CRECIENTE en el repro de 6 turnos; midió **4.33→5.13 s PLANO, idéntico al resto de la sesión**. Dos hipótesis [H], sin decidir: (a) `--no-cache-prompt` es no-op en b11856 (el flag no apagó de verdad); (b) el repro es demasiado chico para diferenciar: cada turno añade ~25 tokens y re-procesar 25 tokens extra no se nota en el TTFT. **Consecuencia honesta para TODA la sesión**: los veredictos TTFT "PLANO" de hoy (REUSE/SHIFT/COMBO-R/COMBO-T/NP2-C) quedan como *no-empeoran* — el certificado fuerte de esta sesión es el de líneas de log (NO-SOPORTADO) y el decode; el repro TTFT necesita re-calibración (turnos más grandes o más turnos) antes de volver a usarse como juez de cache. Pendiente no bloqueante: leer `logs-config/12-N3-NOCACHE.log` en el rig para ver si el server aceptó el flag. El decode del control sí hizo su trabajo: sin cache de prompts el decode es igual al ancla (el cache vive en el prefill, no en la escritura) — coherente con el modelo mental.

**Veredicto de la cosecha (pendiente SIEMPRE de mediana de 3 + aprobación del Director).** Promueven a examen: **NP2 (+22.8%)** y **CMS1024 (+5.2%)** — por separado y eventualmente juntas (NP2+CMS1024 NO se midió hoy: no apilar knobs sin medirlo, lección SS8.1). Quedan en el cajón: NCM/COMBO-T (certificadas, superadas por NP2 hoy), CRAM512/CTXCP4 (certificados fallidos), familia reuse (condicionada a RUTA 0). **Siguiente paso del protocolo**: mediana de 3 de NP2 (con NP2-C de contraste y ANCLA por corrida) en otro bloque horario → si el número aguanta, el Director promociona editando UNA línea de FLAGS_BASE en config.txt (añadir `-np 2`) + el sanity manual de 20 prompts como juez de calidad. Cola intacta: N1 formal (BARRIDO-N1.bat v1.2.1 + sanity 20 prompts), luego N2 → N4 → RUTA 0 + N5 con el orden aprobado de la ronda 12. La evidencia completa de las dos noches vive en `evidencia/faseN3-20261028/` (CSV de 24 filas: la historia del fallo, el resume y la cosecha, en un solo archivo).
