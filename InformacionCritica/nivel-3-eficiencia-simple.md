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
