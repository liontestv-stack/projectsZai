# Nivel 5 (PROPUESTA) — Draft externo en GPU: EAGLE-3 / DFlash para 3.6-35B-A3B (la vía al ×2)

> Estado: PROPUESTA ronda 0 — pendiente de aprobación del Director para cablear la fase S en `barrido-total.py`.
> Etiquetas: [F] verificado en fuente/media, [M] leído del dump del build b11856 (`llama-flags-nuevo.txt`), [T] teórico/derivado, [N/D] sin datos.
> Relación con fase E (MTP): MTP sigue siendo el ancla especulativa planificada [F]. Este nivel la CONVIERTE EN DECISIÓN EMPÍRICA: hoy existen drafts sidecar entrenados para el 3.6-35B-A3B, con aceptación publicada de 83%, que caben en la VRAM libre de la 1650.

## 1. Tesis

La fase E apuesta todo a un único draft (la cabeza MTP del propio modelo). El build b11856 soporta **seis familias especulativas** [M] y el ecosistema ya publicó **dos drafts sidecar oficiales/de comunidad para exactamente nuestro modelo** [F]. El argumento físico es el mismo que justifica el MTP: verificar k tokens cuesta ~lo mismo que verificar 1 (los expertos leídos por ciclo son los mismos), así que cada token aceptado extra divide el tráfico DDR4 por token emitido [T]. Si un draft denso/head acepta más que el MTP de 1 capa, la brecha hasta 43-45 t/s se cierra sin tocar el modelo base.

## 2. Inventario de drafts para Qwen3.6-35B-A3B (verificado hoy)

| Draft | Archivo | Bytes | Aceptación publicada | Estado |
|---|---|---|---|---|
| **EAGLE-3 "Caption"** (EntityDeletr) | `Qwen3.6-35B-A3B-Caption-Eagle3DraftModel.gguf` (bf16-size) | **517,403,232 B** [F API HF] | **83% medio** [F card] | Jul-2026; entrenado sobre Microsoft COCO train2017 captions (100k) [F card] |
| **DFlash** (z-lab oficial, GGUF por lym00) | `Qwen3.6-35B-A3B-DFlash-q8_0.gguf` | **421 MB** (Q8_0); 783 MB (BF16) [F lym00] | N/D numérica; "mejor aceptación en prompts largos" [F lym00] | Feb-2026; GGUF marcado "Test" |
| DSpark | sidecar N/D para 3.6 | — | — | Tipo existe en b11856 [M]; el sidecar DSpark "lleva la cabeza Markov extra" y tiene prioridad de auto-descubrimiento sobre DFlash [F código arg.cpp]; vigilar HF |
| Densos pequeños de la familia | **NO EXISTEN** | — | — | Familia 3.6 en unsloth = 27B denso + 35B-A3B [F colección]; un 27B denso como draft es imposible en 4 GB → **draft-simple con modelo denso familiar: NO-GO** |

**Corrección de ronda anterior [F]:** el NO-GO "DFlash VRAM 6 GB" del ronda 3 quedaba ligado al PR #22105 en otra configuración. Con el GGUF Q8_0 de **421 MB medidos**, DFlash **cabe holgado en la VRAM libre del rig** → se deroga el NO-GO y pasa a dosis de barrido.

**Advertencia de dominio (la más importante del nivel) [T]:** el 83% del EAGLE-3 se midió en el dominio de entrenamiento (captions COCO, inglés, descripción visual). En chat en español y código la aceptación real será menor (N/D en el rig). Por eso la fase S es un A/B empírico, no una apuesta.

## 3. Mecánica en el build b11856 (lo que ya está cableado)

**Tipos especulativos [M dump]:** `none, draft-simple, draft-eagle3, draft-mtp, draft-dflash, draft-dspark, ngram-simple, ngram-map-k, ngram-map-k4v, ngram-mod, ngram-cache` — y `--spec-type` acepta **lista compuesta** [F código: `params.speculative.types` es un vector; ejemplo real de lym00: `--spec-type draft-dflash,ngram-mod,ngram-map-k4v`].

**Auto-descubrimiento de sidecars [F código arg.cpp]:** con `-hfd <repo-draft>` (o repo que incluya sidecar), llama.cpp descarga y **deduce el tipo desde la metadata del GGUF** (`common_speculative_types_from_gguf`); prioridad si el repo trae varios: mtp > dspark > dflash > eagle3. Para rutas locales usar `-md` + `--spec-type` explícito (sin ambigüedad).

**Flags de draft disponibles [M dump]:**
- Carga: `--spec-draft-model/-md`, `--spec-draft-hf/-hfd`
- Dispositivo: `--spec-draft-ngl/-ngld` (default auto), `--spec-draft-device/-devd` (default sigue `-dev`), `-cmoed/-ncmoed/-otd` para MoE del draft (relevante para nextn, no para EAGLE3/DFlash que no son MoE)
- KV del draft: `--spec-draft-type-k/-ctkd`, `--spec-draft-type-v/-ctvd` (default f16; q8_0 permitido)
- Dosis: `--spec-draft-n-max` (default 3), `--spec-draft-n-min` (default 0), `--spec-draft-n-ubatch` (ahorra VRAM del draft), `--spec-draft-p-min` (default 0.00), `--spec-draft-p-split` (default 0.10), `--spec-draft-sampling greedy|probabilistic` (default greedy)
- Hilos/prioridad del draft si va a CPU: `-td/-tbd/--prio-draft` (default 0)
- **Bench sintético [M]:** `--spec-synth-len` + `--spec-synth-rates P0,P1,...` → mide el OVERHEAD de la maquinaria especulativa con aceptación simulada, sin draft real. Aísla "cuánto cuesta el pipeline" de "cuánto da el draft".

## 4. Presupuesto en el rig

- Draft EAGLE3 517 MB / DFlash Q8_0 421 MB → VRAM con `-ngld 99 -devd CUDA0` [T sobre datos F]. Cabe junto a 2-3 capas ruteadas del N4 (§4 del nivel-4). Alternativa extrema: draft en CPU (`-devd none`) — con 4 hilos un head de ~0.5 GB lee ~0.5 GB/t extra → mataría la ganancia [T] → **draft SIEMPRE en GPU en este rig**.
- KV del draft: EAGLE3/DFlash son 1-2 capas → MB, cuantizable a q8_0 sin efecto [T].
- RAM: el draft vive entero en VRAM → coste RAM ≈ 0 (a diferencia del draft denso descartado).
- Restricciones heredadas [F ronda 3]: `-np 1` obligatorio y `--mmproj` no soportado con spec (válido por el mismo mecanismo para sidecars [T]) → 4 slots de N3 **no coexisten** con ninguna especulación: elegir por escenario (chat interactivo 1 usuario → spec siempre).

## 5. Matemática de aceptación (para fijar expectativas y dosis)

Esperanza de tokens aceptados por ciclo con aceptación por posición p y n-max n [T, modelo geométrico]: E ≈ (1−p^(n+1))/(1−p). El speedup real = E × amortización − overhead del pipeline; el verify de k tokens lee los MISMOS expertos que verify de 1 [T tesis DDR4], por lo que el techo es alto.

| p | n-max 2 | n-max 3 | n-max 4 | n-max 7 |
|---|---|---|---|---|
| 0.83 (EAGLE3 en captions [F]) | 2.4 | 3.1 | 3.6 | 4.6 |
| 0.70 | 2.0 | 2.4 | 2.6 | 2.9 |
| 0.60 | 1.7 | 1.9 | 2.0 | 2.1 |
| 0.50 (p-min DFlash) | 1.5 | 1.65 | 1.75 | 1.9 |

Referencia medida: MTP n2 = **×1.28 [F guía unsloth]** ≈ E 1.5-1.6. Con p≈0.7-0.8 y n-max 3-4, un sidecar podría dar **×1.8-2.5 [T]** → con el roadmap N2+N1+N3+N4 (~28-30 t/s sin spec [T]) eso sitúa el rango 43-45+ t/s. Con p≈0.5-0.6 (chat ES real), ×1.5-1.8 → 36-42 t/s. **Ningún otro nivel del proyecto tiene este techo.**

## 6. Matriz de decisión (se resuelve con el barrido, no con opiniones)

| Criterio | MTP (fase E) | EAGLE3-Caption | DFlash | Compuesta +ngram |
|---|---|---|---|---|
| Disponibilidad HOY | Requiere cuant -MTP (14.07 GB [F]) | GGUF ya publicado [F] | GGUF Q8_0 ya publicado [F] | misma base DFlash |
| VRAM extra | 858 MB (nextn) | ~517 MB | ~421 MB | +41 MB |
| Aceptación esperada chat/código | típica n2 [F ×1.28] | N/D (83% en captions [F]) | N/D | N/D |
| Riesgo calidad | bajo (head propia) | **dominio captions** → validar ES | bajo-medio (Test) | hereda DFlash |
| Download extra | 14.07 GB cuant | 0.52 GB | 0.42 GB | 0.42 GB |

Regla: **la fase E sigue siendo el ancla** (modelo -MTP ya inventariado con SHA256); la fase S corre el A/B sidecars sobre el mismo modelo base; gana la config con mejor t/s × calidad-en-spot-check.

## 7. Dosis fase S propuesta (sobre la mejor config sin spec)

```
S0  ancla sin especulación                          -> referencia
S1  MTP n-max 2 (fase E existente)                  -> ancla especulativa
S2  EAGLE3:  --spec-type draft-eagle3  -md <eagle3.gguf> -ngld 99 --spec-draft-n-max 3
S2b EAGLE3 n-max 2 / 4 y p-min 0.3                  -> dosis alrededor del pico
S3  DFlash:  --spec-type draft-dflash  -md <dflash-q8_0.gguf> -ngld 99
            --spec-draft-n-max 7 --spec-draft-p-min 0.50 --spec-draft-prio 2   (dosis lym00 [F])
S3b DFlash n-max 4 / p-min 0.3                      -> dosis alternativa
S4  compuesta: --spec-type draft-dflash,ngram-mod,ngram-map-k4v
            --spec-ngram-mod-n-min 48 --spec-ngram-mod-n-max 64 --spec-ngram-mod-n-match 24
            --spec-ngram-map-k4v-size-n 8 --spec-ngram-map-k4v-size-m 24 --spec-ngram-map-k4v-min-hits 2   ([F] config lym00)
S5  sintético: --spec-type draft-eagle3 -md <gguf> --spec-synth-len 2.5 --spec-synth-rates 0.6,0.6,0.6
            -> overhead puro del pipeline sin depender del draft real [M]
```

**Autenticadores por config:** (1) el log imprime el tipo especulativo activo y el draft cargado; (2) aceptación media observada en el log del server (anotarla por config: es el dato que calibra p); (3) t/s del medidor estándar; (4) **spot-check de calidad en ES + 1 tarea de código por config ganadora** (obligatorio para EAGLE3-caption: si la aceptación es alta pero degrada el español, la config muere). (5) `nvidia-smi` con draft en VRAM ≤ 3.7 GB.

## 8. Riesgos y NO-GO predeclarados

- **Dominio del draft**: EAGLE3-Caption entrenado en captions EN → aceptación en chat ES/código N/D; si p < 0.45 en el rig, la vía sidecar muere y MTP queda como único spec.
- **`--spec-draft-sampling greedy` + `p-min 0` [M default]**: el draft propone argmax y el target verifica → distribución del target se preserva (estándar); al subir `p-min` se descartan propuestas (menos accept, más seguro) — solo tocar en dosis S2b/S3b.
- **Overhead por ciclo CPU↔GPU**: cada ciclo spec sincroniza draft (GPU) y verify (CPU); con 4 hilos el draft en GPU es asíncrono pero no gratis [T]. S5 lo mide antes de conclusions.
- **Multi-slot muerto con spec** [F ronda 3] y `-np 1` obligatorio — no re-testear.
- **VRAM overshoot** → cliff ×10 [F, ver nivel-4 §3]: el draft + capas ruteadas se dosis-escalan juntos.
- ngram sobre chat general ya medido muerto en el rig (accept 0.00-0.16 [F barrido-30]) → las ramas ngram de S4 solo pueden ayudar en tareas repetitivas/código; si S4 ≈ S3, cerrar ngram definitivamente.
- No descargar el `model.safetensors` (1.43 GB) ni `model.gguf` del repo EAGLE3: solo el `.gguf` de 517 MB [F API].

## 9. Líneas finales por escenario (rig, rutas reales)

```
:: Descargas (una vez) — luego offline:
::  hfd EntityDeletr/Qwen3.6-35B-A3B-Caption-Eagle3DraftModel-GGUF  (517 MB)
::  lym00/Qwen3.6-35B-A3B-DFlash-GGUF-Test:Q8_0                      (421 MB)

:: S2 EAGLE3 sobre la mejor config base (ejemplo con ancla ORO-UB1K + ncmoe 38)
D:\llama.cpp\llama-server.exe -m D:\ZLia\models\APEX-I-MINI.gguf -ngl 99 -cmoe -ncmoe 38 -c 16384 -fa on -ctk q8_0 -ctv q8_0 -t 4 --prio 2 -ub 1024 -b 4096 --spec-type draft-eagle3 --spec-draft-model D:\ZLia\models\Qwen3.6-35B-A3B-Caption-Eagle3DraftModel.gguf --spec-draft-ngl 99 --spec-draft-n-max 3

:: S3 DFlash (dosis lym00)
... --spec-type draft-dflash --spec-draft-model D:\ZLia\models\Qwen3.6-35B-A3B-DFlash-q8_0.gguf --spec-draft-ngl 99 --spec-draft-n-max 7 --spec-draft-p-min 0.50 --spec-draft-prio 2
```

## 10. Referencias

- EntityDeletr/Qwen3.6-35B-A3B-Caption-Eagle3DraftModel-GGUF (card: EAGLE3, COCO 100k, accept 83%; API: GGUF 517,403,232 B) — [F]
- lym00/Qwen3.6-35B-A3B-DFlash-GGUF-Test (Q8_0 421 MB / BF16 783 MB; config real spec-type compuesto + dosis n-max 7 p-min 0.50) — [F]
- z-lab/Qwen3.6-35B-A3B-DFlash (draft oficial, Feb-2026) — [F]
- Dump b11856 (`llama-flags-nuevo.txt`): enum spec completo, todos los flags `--spec-*`, `--spec-synth-*`, defaults (n-max 3, p-min 0, p-split 0.10, greedy) — [M]
- Código `common/arg.cpp` (master): vector de tipos, auto-descubrimiento de sidecars y prioridad mtp>dspark>dflash>eagle3 — [F]
- Guía unsloth MTP 3.6 (n-max 2, ×1.28 medido, -np 1) — [F, repo ronda 2]
- Colección unsloth Qwen3.6 (familia: solo 27B denso y 35B-A3B → no hay draft denso familiar viable) — [F]
- Este repo: nivel-4 (presupuesto VRAM con draft), nivel-3 (conflicto slots-spec), barrido-30 (ngram muerto en chat) — [F/M]

## 11. ANEXO — Cuarta ronda: números oficiales de DFlash, el régimen en que spec paga y el flag que lo silencia todo (2026-10-26)

- **[F card z-lab oficial] DFlash:** draft block-diffusion de **0.4B** que inyecta hidden states del target y emite el bloque entero en un pase; **speedups medidos concurrency 1: math500 ×3.61, humaneval ×3.29, mbpp ×2.97, gsm8k ×2.96** (×2.5-2.9 @conc32); entrenado a seq 40k con sliding-window (long-ctx); block size recomendado 16 (conc-1) / 8 (conc alta). Sus números son de rig GPU grande, pero en nuestro régimen DDR4-bound el verify de un bloque cuesta ≈ 1 pasada [T] → el techo relativo aquí es MAYOR [T]. La fase S decide.
- **[F docs/speculative.md] Clamps y comandos oficiales:** `--spec-draft-n-max` se CLAMPA al block size entrenado del draft (lym00 usó 7 → su GGUF test es block ~8); ejemplo oficial DFlash usa `-fa on --jinja`. DSpark = DFlash + cabeza Markov semi-autorregresiva [F docs].
- **[F docs/speculative.md] EAGLE-3:** draft de 1 capa que lee hidden states del target; comparte tokenizer; vocab reducido opcional con su propio lm_head + tabla `d2t`; formatos SpecForge (`LlamaForCausalLMEagle3`) y AngelSlim/vLLM (`Eagle3LlamaForCausalLM`) soportados; `eagle3.cpp` trae el scatter d2t [F #25187].
- **[F hackmd @thc1006 — RTX 3090 full-GPU, UD-Q4_K_XL, baseline 135.7 t/s]:** TODOS los modos spec PIERDEN en full-GPU: ngram-mod −1.5%; draft Qwen3.5-0.8B −11.6%; draft default (n-max 8-32) −60%; ngram-cache −12.2%. → Con verify compute-bound el spec NO paga. Nuestro rig es bandwidth-bound: verificar k tokens ≈ 1 pasada DDR4 → **es exactamente el régimen donde spec SÍ paga [T]**. Este anti-dato full-GPU refuerza la tesis híbrida; no la refuta.
- **[F hackmd] Qwen3.5-0.8B existe con vocab 248320 = el del target** (el 0.6B de vocab 151936 falla: "failed to create draft context") → dosis nueva **S6: `--spec-type draft-simple` con Qwen3.5-0.8B Q4 (~0.5 GB) en GPU**. Aceptación esperada menor que sidecars (draft genérico 0.8B) [T]; inventariar el GGUF exacto al descargar [N/D bytes].
- **[F #25345] llama-server ignora `-md` EN SILENCIO con la KV unificada activa** → autenticador obligatorio de la fase S: log del spec cargado + accept > 0; si no engancha, `--kv-unified off` y re-medir (protocolo completo en N3 §12).
- **Calibración MTP [F]:** jarvislabs (RTX PRO 6000, Q8_0): MoE 35B-A3B solo **×1.17** (193.36→225.48) vs dense 27B ×1.73 → en GPU-bound el MoE paga poco; unsloth guía ×1.28 [F]; mer.vin: n-max 2 es el favorito comunitario en MoE; reddit reporta 80%+ accept con el GGUF-MTP en otro setup. Rango realista para el rig DDR4-bound: ×1.2-1.8 — la fase E/S lo mide.
- **Riesgo operativo MTP [F #23635 + xhinker]:** leak VRAM en prefill con KV cuantizada (cerrado upstream; verificar build tras RUTA 0) y reporte de RAM→swap a las ~3 h → monitoreo RAM/VRAM obligatorio en fase E (protocolo N3 §12).
- **Descargas exactas de la fase S (solo los GGUF):** EAGLE3 `Qwen3.6-35B-A3B-Caption-Eagle3DraftModel.gguf` = 517,403,232 B [F API]; DFlash `Qwen3.6-35B-A3B-DFlash-q8_0.gguf` = 421 MB [F]; NO descargar `model.safetensors` (1.43 GB) ni `model.gguf` (1.44 GB) del repo EAGLE3.

## 12. ANEXO — Quinta ronda: estudio controlado v4 en RTX 3090 — DFlash-n2 gana, el draft externo denso MUERE (2026-10-26)

Existe ahora un estudio público y riguroso SOBRE NUESTRO MODELO EXACTO: repo `thc1006/qwen3.6-speculative-decoding-rtx3090` — Qwen3.6-35B-A3B **UD-Q4_K_XL**, RTX 3090, ctx 8192, commit llama.cpp 3737e4137, con **ERRATA propio que se retracta de sus resultados v1 negativos**. Metodología v4 [F]: 3.002 arm-runs en 74 directorios (25 Ago–31 Ago 2026), baseline matcheado DENTRO de cada corrida, supresión de thinking verificada por request, texto+token-ids completos por request, telemetría GPU continua, cifras re-derivadas de los datos por un checker que falla ante drift.

- **TABLA OFICIAL v4 [F] (baseline sin spec 115.7 t/s en 3090 — comparar SOLO los %, no los t/s absolutos):**

| Modo | t/s | Δ vs baseline | Accept | tok/ciclo |
|---|---|---|---|---|
| **spec-dflash-n2** | **146.2** | **+26.3%** | 72.3% | 0.81 |
| spec-mtp-n2 | 141.9 | +22.7% | 78.4% | 0.77 |
| spec-dflash-n4 | 137.9 | +19.2% | 55.2% | 1.24 |
| ngram-map-k4v-m8 | 115.4 | −0.3% | 50.0% | 0.01 |
| ngram-mod-n24 | 103.1 | −10.9% | 5.0% | 0.19 |
| ngram-cache | 93.7 | −19.0% | 5.2% | 0.17 |
| **spec-draft-n8 (0.8B ext.)** | **30.9** | **−73.3%** | 29.5% | 1.86 |
| spec-draft-n1 (0.8B ext.) | 29.2 | −74.8% | 69.7% | 0.50 |

- **ORDEN OFICIAL de métodos para el 3.6-35B-A3B [F]:** DFlash-n2 > MTP-n2 > DFlash-n4 >> ngram (muerto fuera de coding) >>> draft externo denso. La dosis n2 (2 tokens de draft) domina a n4 porque la aceptación cae con la profundidad (72→55%) más rápido de lo que crece el ciclo.
- **S6 (draft-simple con Qwen3.5-0.8B) = NO-GO FORMAL [F]:** la ronda 4 lo propuso como dosis; el estudio lo midió: **−73% incluso con el draft en GPU** — y la conclusión literal del autor: *"with external draft model, speculation loses badly and batching widens the gap"*. Con accept 69.7% a n1 AÚN pierde −74.8%: el coste de los forwards del draft supera cualquier ganancia. → S6 se elimina de la fase S; las únicas vías spec del proyecto son MTP (nextn interno) y los sidecars DFlash/DSpark.
- **ERRATA del estudio [F] — lecciones de medición para el rig:** (1) el "100% acceptance" de la v1 era un ARTEFACTO de cómo llama.cpp cuenta la aceptación en esta clase de modelo → **no fiarse del accept rate del log como métrica única** (usar t/s y spot-check de texto); (2) el draft de la v1 nunca fue vocabulary-compatible (lo que produjo el falso "todos pierden"); (3) 3/4 de los requests v1 devolvían thinking truncado en vez de respuestas; (4) llama-server+draft abortaba en commit bcb5eeb64 (b11856 es posterior — riesgo bajo, pero si la fase S aborta al arrancar, recordar este precedento).
- **Varianza → dosis de repetición [F]:** mismo config 12 veces en un día = 9.4 pp de rango; DFlash-n2 osciló +17.3%…+26.7% clusterizado por corrida. → La fase S mide S0 (ancla), S1 (MTP-n2) y S2 (DFlash-n2) con **mediana de 3 corridas** y baseline matcheado por corrida; deltas <5pp no son conclusión (protocolo ya adoptado en N3 §13).
- **Aceptación y cuant [F reddit 27B]:** "acceptance is quant-independent at matched depth; DFlash is the fastest algo overall; EAGLE3 is dominated by both, useful only as a fallback" — coherente con la tabla; permite usar estos accepts como prior para nuestro UD-IQ3_XXS-MTP [T]. EAGLE3 queda relegado a S3-fallback (su sidecar 517 MB sigue inventariado); referencia de familia: PRISM-EAGLE3 en el 3.6-27B mejora accept length 2.2→2.4 (hasta ~3.35 en PRO) [F Ex0bit] — el techo EAGLE3 sin training propio es modesto.
- **ngram ratificado como muerto en chat [F]:** ngram-map-k4v con accept 50% pero **0.01 tokens/ciclo** = el mecanismo existe pero no entrega tokens en texto general (coherente con el barrido-30: accept 0.00-0.16); la dosis #19493 (ngram-mod 24/48/64) queda exclusivamente para sesiones de coding.
- **Dosis fase S ACTUALIZADA (sustituye §7):** S1 = `-spec-type mtp --spec-draft-n-max 2` (o `--spec-draft-*` según autenticador #25345) sobre la mejor config H; S2 = DFlash sidecar 421 MB con `n-max 2` (LA config compuesta de z-lab usa n-max 7/p-min 0.50 — el estudio dice n2; probar 2 y 3); S3 = EAGLE3 solo si S2 falla el spot-check ES; S6 ELIMINADA. Expectativa para el rig [T]: ≥ ×1.2 sobre el mejor H — el 3090 es compute-bound (verify caro) y aun así gana +26%; el rig es bandwidth-bound (verify ≈ 1 pasada DDR4 compartida con el draft) que es el régimen donde el spec paga MÁS [T §11, reforzada por el dato de que en full-GPU el draft interno también ganó en v4].
- **Nota de consistencia interna:** la ronda 4 citaba el hackmd del mismo autor ("todos pierden en full-GPU, baseline 135.7") como anti-dato; el ERRATA del repo muestra que esa v1 estaba rota (draft sin vocab, thinking truncado). El anti-dato full-GPU queda SUSTITUIDO por el dato v4: con draft INTERNO (MTP/DFlash) el spec gana también en full-GPU (+22-26%); lo que pierde siempre es el draft EXTERNO denso.

## 13. ANEXO — Sexta ronda: EXISTE un sidecar DSpark para nuestro modelo exacto (con un fix GDN que DFlash NO tiene), la lección del draft auto-convertido y MTP en L4 +45% (2026-10-26)

- **DESCUBRIMIENTO [F HF]:** `williamliao/Qwen3.6-35B-A3B-DSPARK-GGUF` — sidecar DSpark para el 3.6-35B-A3B que la ronda 4/5 daba por inexistente. Base: `Koopah/Qwen3.6-35B-A3B-NVFP4-DSPARK`. Cuants del sidecar: **IQ4_XS 286 MB · Q4_K_M 307 MB · Q5_K_M 368 MB · Q6_K 432 MB · Q8_0 556 MB** (el IQ4_XS/Q4_K_M son aún más chicos que el DFlash Q8_0 421 MB). Uso mínimo documentado: `llama serve -hf williamliao/Qwen3.6-35B-A3B-DSPARK-GGUF:Q4_K_M` (con el target cargado, el sidecar se pasa `-md`/`--spec-type draft-dspark` — tipo PRESENTE en el enum de b11856 [M §ronda 3]).
- **POR QUÉ IMPORTA — el fix GDN [F card Koopah]:** el DSpark está warm-started del backbone z-lab DFlash, re-entrenado bajo el objetivo DSpark (cabeza Markov low-rank de rango 256 + confidence head) e **"incluye un fix para hybrid-GDN state commit NO presente en el DFlash original"**. Nuestro target ES híbrido GDN (10 capas GDN [F ficha]) → el sidecar DFlash podría arrastrar un defecto de commit de estado recurrente en nuestro arquetipo; el DSpark lo corrige de fábrica. **Esto REORDENA las dosis S: S2 = DSpark (Q4_K_M, 307 MB) pasa a preferente y S2b = DFlash (Q8_0, 421 MB) queda como comparación** — ambas con spot-check ES obligatorio (el fix es del lado draft, pero la confianza se mide).
- **Ficha técnica DSpark [F card Koopah]:** block size 8 (knob de runtime: puede servirse en bloques menores); ctx entrenado 32,768 (cubre nuestro `-c 4096-16k`); vocab 248,320 padded = idéntico al target (cero problemas de vocab — la trampa de la v1 del estudio thc1006 no existe aquí); regla de aceptación **min(1, q/p) LOSSLESS** → calidad idéntica al target solo, a cualquier temperatura. Aceptación por posición @0..@7: **0.812 / 0.784 / 0.780 / 0.792 / 0.824 / 0.757 / 0.780 / 0.766** — PLANA (sin el colapso 72→55% del DFlash n2→n4): tokens/ciclo esperables mayores; mean accepted length ~4.1-4.24 a k=8. En vLLM solo: 568 t/s; Spec-Bench macro 3.98 @temp0.
- **Comparativa del propio autor [F card williamliao]:** DFlash max 7 = **+18% vs sin spec** y **+31% vs DSpark max 5**; aceptaciones DFlash: 94.3% code_completion / 97.1% repeat_pattern / 73.7% json_output; default DSpark `n-max 3`. Lectura para el rig [T]: DFlash sigue siendo el rey de código (coherente con v4: +26.3% en 3090), pero DSpark es el candidato generalista con fix GDN y aceptación plana → la fase S mide AMBOS: dosis S-DSpark-n2 y S-DSpark-n3 (el n-max de DSpark puede subir hasta el block 8 legalmente [F docs/speculative.md clamp], pero el estudio v4 enseña que n2-n3 es donde vive la ganancia en cards de consumo).
- **La lección del draft auto-convertido [F unsloth discussion #14 — cronología completa del estudio thc1006]:** el 8-May-2026 el mismo autor midió DFlash = **−44.6%** (77.0 vs 138.9) usando un draft **auto-convertido BF16→GGUF con un convertidor modificado del PR #22105** y `draft-max 8`; en v4 (Ago) con el sidecar oficial y n2 = **+26.3%**. Dos causas de la voltereta: (1) **NUNCA auto-convertir el draft** — usar el GGUF oficial (williamliao para DSpark, z-lab/lym00 para DFlash); (2) **n-max domina** (8 → catástrofe; 2 → óptimo). Se fija como regla de fase S: solo GGUF sidecar oficiales, y n-max ∈ {2,3}.
- **Flags [M dump]:** b11856 eliminó `--draft/--draft-n/--draft-max` ("the argument has been removed. use --spec-draft-n-max") → **todos los comandos de internet con `--draft-max` (incluida media documentación DFlash/DSpark) se traducen a `--spec-draft-n-max`** en el rig. El enum `draft-dspark` está confirmado en b11856 → la dosis S-DSpark es ejecutable HOY sin RUTA 0.
- **MTP en una GPU bandwidth-pobre paga MUCHO más [F repo hanxiao L4]:** L4 24 GB (Ada, ~300 GB/s) full-GPU: sin MTP 63 t/s → **con MTP n2: 91-99 t/s (+45-57%)** con `-ub 64 -b 512 -np 1 --spec-type draft-mtp --spec-draft-n-max 2`. La escala de ganancia MTP sigue el hambre de bandwidth de la GPU (3090 936 GB/s: +22.7% [F v4] → L4 300 GB/s: +45-57% [F]) → para el rig DDR4-bound [T]: el caso optimista de fase E sube; **≥+25% es plausible y el techo ≥×1.45 no es descabellado**. Nota práctica de su config: `-ub 64 -b 512` es lo que le hace caber todo en VRAM — misma palanca presupuestaria de N4 §14.
- **El prefix-cache y el spec [F vLLM #38182 vía thc1006 v3]:** con MTP activo el hit-rate del prompt cache cayó 92→71%; con cache desactivado y flags matcheadas, MTP k=1 en vLLM (2×3090 PCIe) dio **TPOT −21.6% / TTFT −31.4% / total +31.7%**. → Protocolo fase E/S (coherente con N3 §14): medir con `--cache-prompt` ON; si el decode gana pero el TTFT empeora, A/B con cache OFF para separar efectos antes de la dosis final.
- **Mecanismo de fondo unificado [F MoESD arXiv 2505.19645 + Utility-Driven SD arXiv 2506.20675, vía #14]:** con sparsity 0.031 (A3B), el umbral de saturación de expertos T_thres ≈ 94 ≫ cualquier K de draft denso: el verify de k tokens carga la UNIÓN de expertos de k posiciones sin amortización → por eso el draft EXTERNO denso pierde SIEMPRE (incluso con accept 100%), mientras los drafts de hidden-states (MTP/DSpark/DFlash) eluden el problema compartiendo el forward del target. Unifica todos los signos medidos hasta hoy (v2 negativo, v4 positivo, L4 muy positivo).
- **Dosis fase S FINAL v6 (sustituye §12):** S1 = MTP n2 (repo renombrado: el GGUF objetivo ya trae nextn, nombre nuevo en N2 §16); **S2 = DSpark Q4_K_M 307 MB con `--spec-type draft-dspark --spec-draft-n-max 2` y n3**; S2b = DFlash Q8_0 421 MB n2 (comparación, mismo protocolo); S3 = EAGLE3 solo fallback. Autenticadores: log del spec cargado + accept > 0 (ojo artefacto de conteo [F ERRATA v1]) + spot-check ES + medición de TTFT del cache. Regla de oro: mediana de 3, baseline matcheado por corrida, no perseguir <5pp.

*Referencias nuevas: huggingface.co/williamliao/Qwen3.6-35B-A3B-DSPARK-GGUF y Koopah/Qwen3.6-35B-A3B-NVFP4-DSPARK (ficha técnica completa); huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/discussions/14 (cronología v1→v4 del estudio thc1006: −44.6% del 8-May con draft auto-convertido, correcciones y datos vLLM v3); github hanxiao/Qwen3.6-35B-A3B-MTP-L4 (MTP n2 en L4: 63→91-99 t/s).*


## 14. ANEXO — Séptima ronda: DSpark OFICIAL de RedHatAI para nuestro modelo exacto, LiliCorr fusionada, MTP adaptativo aún no, y b11856 sin NINGÚN draft aprendido (2026-10-26)

- **DSpark OFICIAL para el 3.6-35B-A3B [F API HF]:** `RedHatAI/Qwen3.6-35B-A3B-speculator.dspark` existe (creado 19-Jul-2026, última modificación 5-Ago-2026): safetensors BF16 con 949,973,761 parámetros (~0.95B), vocab 248,320 ✓ (coincide con ronda 4), `val_metrics.json` y `train_command.txt` públicos. Los GGUF de williamliao (286-556 MB, ronda 6) son cuants comunitarios de esta familia → **S2 queda anclada a un sidecar con upstream oficial**, no solo comunitario.
- **Mecanismo DSpark documentado en master [F, PR #25173]:** DFlash backbone + cabeza Markov semi-autorregresiva — los logits de cada posición del bloque se sesgan con un término low-rank keyed en el token PREVIO, encadenado in-graph a través del bloque → recupera la señal left-to-right que la difusión de bloque pura pierde, manteniendo 1 decode por bloque. **Flag nueva: `--spec-draft-conf-min P`** — trunca el bloque en la primera posición cuya aceptación predicha (confidence head) cae bajo P (default 0 = off) → dosis candidata A/B: conf-min 0.5-0.7 tras fijar n-max. Restricción: solo backbone Qwen3 soportado hoy (Gemma4 planeado) → nuestro 3.6 ✓. Ejemplo master: checkpoint block7 → `--spec-draft-n-max 7`.
- **Guía de dosis n-max del ecosistema [F Jetson AI Lab]:** DFlash block-16 → arrancar en 15 y bajar; "un valor menor puede ganar cuando la acceptance es baja, el target es compute-bound, o la verificación paralela activa expertos extra en un MoE" → nuestro arrastre en 2-3 (dosis v6 de §13) sigue siendo el punto de partida correcto para un MoE DDR4-bound; 15 queda como techo de exploración SOLO si acceptance >0.8 estable.
- **LiliCorr FUSIONADA a master el 15-Oct (#30506, danbev) [F]:** mejora de DFlash, NO un spec-type nuevo — usa el MISMO `--spec-type draft-dflash` con un draft GGUF convertido LiliCorr (`-md lilicorr.gguf`). Mecanismo: un pequeño transformer calcula vectores `in`/`out` para los top-k candidatos por posición; se elige el candidato cuyo vector `in` maximiza la similitud coseno con el vector `out` del token elegido en la posición anterior (`LiliCorrDraftModel` hereda de `DFlashDraftModel`). Sin cifras de speedup en el PR ("AL similar a la implementación de vLLM en una 5090") → vía S2b con draft LiliCorr-convertido como A/B contra DFlash crudo cuando exista conversión GGUF publicada.
- **MTP adaptativo, PR #27210 [F]: NO fusionado** (no aparece en la enumeración de `--spec-type` de master a hoy). Propuesta: `--spec-type draft-mtp-adaptive --spec-draft-n-max 12` (floor 3 con `--spec-draft-n-min-adaptive`); máquina de estados tipo contador: subir es difícil pasado 3-4 (protección contra rachas de suerte en prose), la presión de bajada escala con la profundidad. Números del autor: coding +10-15% vs MTP fijo n3; recall de código desde thinking >50%; recall de prose +20-30%; prose difícil −3%. Vigilancia activa: si se fusiona, añade dosis E-adaptativa.
- **EAGLE3 para nuestra clase [F master docs]:** `AngelSlim/Qwen3-a3B_eagle3` está en la lista OFICIAL de drafts EAGLE-3 soportados (formatos SpecForge y vLLM/AngelSlim `Eagle3LlamaForCausalLM` ambos convertibles con `convert_hf_to_gguf.py --target-model-dir`) → S3 deja de ser hipotética.
- **Auditoría b11856 [M dump — confirmación dura]:** cero ocurrencias de dflash, dspark, eagle3 y mtp en el dump completo; la enumeración de `--spec-type` solo lista tipos sin draft (`none|ngram-cache|ngram-simple|ngram-map-k|ngram-map-k4v|ngram-mod`) y con `-md` el build va por draft-simple implícito. `-hfd/--spec-draft-hf` (descarga directa del draft desde HF) SÍ existe, igual que `-ctkd/-ctvd` y `-cd`. **Conclusión: TODA la fase S/E con drafts aprendidos (S1 MTP, S2 DSpark, S2b DFlash, S3 EAGLE3) exige RUTA 0 (git pull + recompilar) — no es solo el draft-mtp: NINGÚN draft aprendido opera en b11856.** La dosis S v6 (§13) queda definida como dosis POST-RUTA-0; el hito de ejecución del Director arranca con el recompile, no con los sidecars.
- **Bench comparativo externo [F paywalled, Kaitchup 2-Jun]:** Qwen3.6 27B y 35B-A3B con vLLM y llama.cpp, MTP vs DFlash por tarea (coding/chat/math): "up to 4x" bien configurado; y la advertencia clave: **mal configurado puede ser MÁS LENTO silenciosamente** — coherente con la lección thc1006 (n-max domina, §13) y con nuestra regla de mediana de 3.

*Referencias nuevas: huggingface.co/api/models/RedHatAI/Qwen3.6-35B-A3B-speculator.dspark (ficha y safetensors, 2026-10-26); docs/speculative.md master (sección DSpark #25173, flag --spec-draft-conf-min, lista EAGLE3 con AngelSlim/Qwen3-a3B_eagle3, -hfd); github PR #30506 (LiliCorr, merge 15-Oct-2026, mecanismo in/out coseno); github PR #27210 (draft-mtp-adaptive, abierto); jetson-ai-lab.com/tutorials/speculative-decoding (guía DFlash/DSpark, dosis n-max, advertencia MoE); release v0.7.0 (LiliCorr en notas); kaitchup.substack.com (bench Qwen3.6 MTP vs DFlash, 2-Jun); dump b11856 del Director (sin dflash/dspark/eagle3/mtp; -hfd, -ctkd/-ctvd, -cd presentes) [M].*
