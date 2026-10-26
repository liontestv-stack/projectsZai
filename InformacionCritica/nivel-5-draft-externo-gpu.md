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
