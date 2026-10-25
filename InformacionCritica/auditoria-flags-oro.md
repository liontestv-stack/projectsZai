# Auditoria flag a flag del build b11856 — buscando oro para carga, decode y prefill

- **Fecha**: 25-oct-2026
- **Fuente de verdad**: `llama-flags-nuevo.txt` (dump UTF-16LE del `llama-server --help` del build b11856 del Director, 751 lineas decodificadas y leidas INTTEGRAS)
- **Metodo**: las ~190 flags del help, una a una, con tres lupas: CARGA (tiempo de arranque/carga del modelo), DECODE (t/s de generacion, campeon medido 21.50 con `-lm none`), PREFILL (velocidad de procesamiento del prompt, el frente que los barridos 25/30 apenas tocaron)
- **Reglas respetadas**: `aprendido.md` manda (lo medido no se prueba dos veces); no se repite nada de las 25 ni de las 30; nada entra sin fuente primaria; expectativas honestas separadas de hipotesis

---

## 0. Perfil del rig y estado de partida

- i3-10100F 4C/8T · GTX 1650 4 GB (~3.1 GB libres con escritorio cerrado) · 16 GB DDR4
- Modelo: APEX-I-MINI (Qwen3.6-35B-A3B, ~3.3 bpw) = 14.27 GB → expertos (~11 GB) en CPU leyendo DDR4
- Campeon: BASE + `-lm none` = **21.50 t/s decode** (barrido-25). Techo fisico declarado: 21.5-22 a $0
- En vuelo: barrido-30 (EXP override-kv, FIT, NCMOE, afinidad, prioridad, cierres)
- Cuello de botella fisico: ancho de banda DDR4 en decode; CPU+GPU en prefill

**La lupa nueva de esta auditoria**: los barridos anteriores optimizaban DECODE casi exclusivamente. El build tiene un **grupo completo de flags SEPARADAS para el procesamiento por lotes/prefill** que nunca se tocaron: `-tb`, `-Cb`, `-Crb`, `--cpu-strict-batch`, `--prio-batch`, `--poll-batch` (dump L9-24, verbatim). Eso abre un frente entero sin tocar al campeon.

---

## 1. EL ORO (rankeado por esperanza matematica x coste)

### G1 — El grupo PREFILL separado: `-tb` + `-Crb` + `-ub` (hipotesis: prefill +10-30%, decode intacto)

El dump dice verbatim:

```
-tb,  --threads-batch N    number of threads to use during batch and prompt processing
                           (default: same as --threads)
-Crb, --cpu-range-batch lo-hi    ranges of CPUs for affinity (BATCH threads)
--prio-batch N             set process/thread priority (batch) (default: 0)
--poll-batch <0|1>         use polling to wait for work (default: same as --poll)
```

- Hoy el launcher corre con `-t 4` y SIN `-tb` → **el prefill tambien usa 4 hilos**, cuando el rig tiene 8 logicos. El decode se queda con los 4 fisicos (campeon intacto); el prefill puede usar los 8: `-tb 8 -Crb 0-7`.
- **`-ub 256` en BASE_FLAGS es la MITAD del default del build (512)** (dump L31: `-ub, --ubatch-size N ... default: 512`). Nunca se eligio por medicion: vino heredado de la linea de comandos original. En prefill, ubatch mas grande = menos lanzamientos de kernels y mejores lecturas amortizadas (mecanismo confirmado por docs/speculative.md: "computar n tokens en batch es mas eficiente que computarlos secuencialmente").
- Candidatos: `-ub 512` (volver al default del build) y `-ub 1024` + `-b 4096` (escalada).
- **Riesgo honesto**: los buffers de computo crecen con ub; en 4 GB de VRAM puede haber desborde → el fit lo anotaria, o se baja ctx. Coste de probar: bajo.
- Las 30 descartaron `-b/-ub` mirando el DECODE (ahi el batch es 1 y no mueve nada); con la lupa en PREFILL vuelven legalmente.

### G2 — NGRAM speculative: `--spec-type ngram-simple` / `ngram-mod` (hipotesis: 0 a +15% decode, mas en contenido repetitivo; borrador GRATIS)

- **No viola aprendido.md**: lo medido y sancionado fue la familia draft-MTP (10 configs, 16.6-18.9 t/s). El ngram NUNCA se midio en este rig y su fisica es DISTINTA.
- Por que MTP perdio aqui: cada token de borrador del MTP paga lecturas de expertos en DDR4 (el draft no es gratis en un rig bandwidth-bound). Por que el ngram puede ganar: **el borrador es un lookup de tabla, coste ~cero**, y la verificacion de N tokens va en UN solo ubatch — docs/speculative.md (fuente primaria, apertura): "computing n tokens in a batch is more efficient than computing n sequentially". Las lecturas de pesos se amortizan entre los N tokens verificados.
- Dato de comunidad (prueba honesta con 8 prompts distintos, RTX 5060 Ti, MoE 26B-A4B): +6.7% en codigo, ~0% en prosa diversa; otra fuente: "el ngram (prompt-lookup) casi nunca hace dano". En codigo/ plantillas/respuestas repetitivas espera mas.
- Flags verbatim del dump (L390-414) para este build — nombres NUEVOS (los viejos `--draft-max` etc. estan REMOVIDOS):
  - `--spec-type ngram-simple` con `--spec-ngram-simple-size-n 12 --spec-ngram-simple-size-m 48 --spec-ngram-simple-min-hits 1` (defaults)
  - `--spec-type ngram-mod` con `--spec-ngram-mod-n-min 48 --spec-ngram-mod-n-max 64 --spec-ngram-mod-n-match 24` (defaults; la comunidad lo recomienda para MoE)
  - `ngram-cache` (+ `-lcs/-lcd` lookup cache) existe; fase 2
- **ADVERTENCIA CRITICA DE MEDICION** (documentada con caso real: mismo prompt repetido = 88 → 419 t/s FAKE, x5 falso): con ngram activo, repetir el MISMO prompt infla el resultado porque el lookup clava el texto. **El protocolo de los barridos (mismo prompt x4 pasadas) NO SIRVE para ngram**: hay que medir con 4 prompts DIFERENTES de la misma familia y leer el acceptance rate del log del server.

### G3 — EAGLE3 draft (`--spec-type draft-eagle3`): la unica familia speculative cuya fisica ENCAJA aqui (fase 2, con prerrequisitos)

- docs/speculative.md (fuente primaria) lista drafts EAGLE3 para esta familia: `AngelSlim/Qwen3-a3B_eagle3` y `Tengyunw/qwen3_30b_moe_eagle3`; `draft-eagle3` esta verbatim en el spec-type del dump L390.
- Fisica: el draft EAGLE3 es un transformador de UNA capa (~0.3-0.9 GB) que lee los hidden states del modelo grande → **el borrador es casi gratis y cabe entero en la VRAM libre** — a diferencia del MTP cuyo draft pago DDR4 (por eso perdio). La verificacion batched amortiza lecturas igual que G2 pero con acceptance entrenado, mucho mayor que ngram en texto diverso.
- Prerrequisitos honestos: conseguir/convertir el GGUF del draft (`convert_hf_to_gguf.py --target-model-dir`), VRAM para el draft, y medir acceptance real. Complejidad media-alta → fase 2, no antes de agotar G1/G2.

### G4 — `--no-warmup` (CARGA): arranque mas rapido, verbatim en el dump (L463: "whether to perform warmup with an empty run, default: enabled")

- El server hace un run vacio de calentamiento al arrancar. `--no-warmup` lo salta → banner/health antes. Coste: la PRIMERA peticion paga el calentamiento. $0, reversible, ideal para quien abre y cierra el server seguido.
- Nota: NO cambia los t/s; cambia la espera hasta "listo".

### G5 — `-cram` / `--cache-ram`: el default 8192 MiB pelea contra tu RAM (verificado HOY; antes estaba descartada por "semantica no verificable" — la semantica quedo verificada)

- Verbatim dump (L446-449): `-cram, --cache-ram N` "set the maximum cache size in MiB (default: 8192...)" + `--cache-idle-slots` (default enabled, "requires cache-ram"): los estados de slots inactivos se guardan en la caché de prompts en RAM.
- PR #16391 (merge oct-2025) verificado via tutorial oficial de la comunidad + issue #22127 (el log "prompt cache is enabled, size limit: 8192 MiB" aparece al cargar) + PSA reddit: la cache se usa al cambiar de conversacion; el propio tutorial dice **"Don't use when: memory-constrained systems (<16GB RAM)"** — con 14.27 GB del modelo en RAM (`-lm none`) y 16 GB totales, dejar un tope de 8 GiB para cache de prompts es tierra de pageouts.
- Candidato: `-cram 512` (o `0` para desactivar) en el uso diario de chats largos/cambios de conversacion. Efecto esperado: estabilidad y TTFT de re-entrada, NO t/s decode. En el barrido de velocidad puro, ruido esperado (los sweeps no cambian de conversacion).

### G6 — Fuera del build: exclusion de Windows Defender (CARGA, $0, clasica)

- Cada arranque con `-lm none` lee 14.27 GB del SSD; Defender en tiempo real inspecciona lo que abre `llama-server.exe`/lee el GGUF. Excluir `D:\llama.cpp\build\bin` y la carpeta de modelos es el acelerador de carga clasico de Windows (efecto tipico documentado en guias de tuning: decenas de segundos ahorrados; aqui se MEDIRA con `load_s`, columna que el barrido-30 ya guarda).
- No es flag de llama.cpp: se declara como palanca del sistema, medible con el mismo protocolo.

### G7 — Retome en chats largos: `--context-shift` + `--cache-reuse 256` (verbatim L458-460 y L620-623)

- El server trae context-shift DESACTIVADO por default ("default: disabled" verbatim). Activarlo + `--cache-reuse 256` permite que chats que pasan de 16k reciclen KV por chunks en el shift, en vez de recorte brutal → re-entrada rapida.
- Nota honesta: shift = el modelo pierde el inicio mas viejo del contexto (calidad, no solo velocidad). Para chat diario largo es el mal menor frente a errores de corte.

---

## 2. AUDITORIA UNO A UNO (~190 flags del dump)

Veredictos: **ORO** (candidato a medir), UTIL (ya integrado o util puntual), RUIDO (sin efecto real en este rig), VENENO (danino o aprendido), PROBADO (ya medido en 25/30), N/A (no aplica al rig/caso), ANTI (activarlo EMPEORA; no usar).

### 2.1 common params — hilos, afinidad, batch

| Flag | Que hace (verbatim resumido) | Veredicto | Motivo |
|---|---|---|---|
| `-h/--help`, `--version`, `-cl`, `--completion-bash` | info/ayuda | N/A | sin efecto runtime |
| `-t N` | hilos de GENERACION (default -1=auto) | PROBADO | -t 4 campeon; 3/5 pierden (aprendido §4) |
| `-tb N` | hilos de BATCH/PROMPT processing (default = -t) | **ORO (G1)** | prefill hoy limitado a 4; probar 8 |
| `-C M` / `-Cr lo-hi` | afinidad CPU (decode) | PROBADO | CR03/CMASK55/STRICT/CR14 en barrido-30 |
| `--cpu-strict 0/1` | colocacion estricta (decode) | PROBADO | STRICT/STRICT55 en barrido-30 |
| `--prio N` | prioridad hilos generacion | PROBADO | 2 campeon; 0/3 en barrido-30 |
| `--poll 0..100` | nivel de polling espera de trabajo | PROBADO/EN VUELO | POLL0/100 medidos (21.33/21.42); POLL20/80 pendientes en el 30 |
| `-Cb M` / `-Crb lo-hi` | afinidad de hilos BATCH (separada!) | **ORO (G1)** | nunca tocada; permitiria -Crb 0-7 con -t 4 |
| `--cpu-strict-batch 0/1` | colocacion estricta batch | **ORO (G1)** | acompana a -Crb |
| `--prio-batch N` | prioridad hilos batch (default 0) | **ORO (G1)** | probar 2 con -tb 8 |
| `--poll-batch 0/1` | polling para batch (default = --poll) | ORO menor (G1) | probar 1 con -tb 8 |
| `-c N` | ctx size | PROBADO | 16384 base; 8192/4096 en NCM del 30 |
| `-n N` | tokens a predecir | N/A | por-request |
| `-b N` | batch logico (default 2048) | ORO menor (G1) | escalar a 4096 con ub alto |
| `-ub N` | ubatch fisico (default 512) | **ORO (G1)** | BASE va en 256 = mitad del default del build |
| `--keep N` | tokens iniciales conservados en shift | UTIL | acompana a G7 en chats largos |
| `--swa-full` | cache SWA tamano completo | N/A | verificar en banner si el modelo usa SWA (n_swa); si n_swa=0, irrelevante |

### 2.2 common params — atencion, KV, carga, memoria

| Flag | Que hace | Veredicto | Motivo |
|---|---|---|---|
| `-fa on/off/auto` | flash attention | UTIL | ON en BASE; habilita KV cuantizada y acelera prefill |
| `--perf/--no-perf` | timings internos | RUIDO | default off; encender solo para diagnosticar |
| `-e escape` | procesar secuencias \n etc. | RUIDO | sin efecto en t/s |
| `--rope-*` (4), `--yarn-*` (5) | escalado de contexto | ANTI | alterar rompe el modelo; solo si se excede ctx entrenado |
| `-kvo / -nkvo` | KV offload a GPU (default on) | RUIDO/ANTI-off | apagarlo manda el KV a RAM: atencion techa ~16 t/s (aritmetica del estudio 30) |
| `--repack/-nr` | repack de pesos (default on) | PROBADO | REPACKOFF en barrido-30 |
| `--no-host` | bypass host buffer | PROBADO | NOHOST en barrido-30 |
| `-ctk/-ctv TYPE` | tipo KV (9 valores) | PROBADO | q8_0 campeon; q4_0 perdio; q5_1 cierra en el 30; tipos verbatim: f32/f16/bf16/q8_0/q4_0/q4_1/iq4_nl/q5_0/q5_1 |
| `-dt` | defrag KV | VENENO | DEPRECATED verbatim (aprendido §7) |
| `--rpc` | cluster RPC | N/A | un solo equipo |
| `-lm MODE` | modo de carga (auto/none/mmap/mlock/dio) | PROBADO+ORO menor | none campeon 21.50; dio mide load_s en el 30 (LMDIO); mlock prohibido (RAM) |
| `-lzm MODE` | lectura bajo demanda de tensores (requiere mmap) | DESCARTADA con motivo | bajo campeon (-lm none) no aplica; bajo mmap convertiria decode en lecturas de SSD |
| `--numa` | optimizaciones NUMA | N/A | un socket (aprendido) |
| `-dev/--list-devices` | eleccion de GPU | N/A | una sola GPU |
| `-ot pattern=buf` | override de buffer por tensor | UTIL | es el mecanismo general bajo -cmoe/-ncmoe; granularidad extra solo si EXP/FIT fracasan |
| `-cmoe` | TODOS los expertos en CPU | PROBADO | campeon base |
| `-ncmoe N` | expertos de primeras N capas en CPU | PROBADO | barrido-30 NCM con VRAM liberada (condiciones nuevas) |
| `--moe-cache-mib N` | cache GPU de expertos en CPU | VENENO | 13.51 vs 20.85 medido (aprendido §2); el video de YouTube describe esta familia: no aplica a 4 GB |
| `-ncffn N` | FFN densa en CPU | N/A | modelo MoE (para densos) |
| `-ngl N/auto/all` | capas a GPU | PROBADO | 99 fijo; auto en FIT del 30 |
| `-sm none/layer/row/tensor` | split multi-GPU | N/A | una GPU (tensor = EXPERIMENTAL) |
| `-ts`, `-mg` | split/proporciones multi-GPU | N/A | una GPU |
| `-fit on/off` | auto-ajuste a VRAM (default on) | PROBADO | FIT-A/B/C del 30 lo usan |
| `-fitt MiB` | margen del fit (default 1024) | PROBADO | 256/384 en FIT del 30 |
| `-fitc N` | ctx minimo que el fit puede imponer (default 4096) | UTIL | proteger ctx si FIT baja ctx; acompanar FIT |
| `--check-tensors` | validar datos del GGUF al cargar | ANTI | ralentiza la CARGA; no usar en produccion |
| `--override-kv` | override de metadata (via de EXP) | PROBADO | EXP4-10 del barrido-30 |
| `--op-offload / --no-op-offload` | offload de ops host a device (default on) | RUIDO | hermano de --no-host; probar solo si NOHOST movio algo |
| `--lora*` (3), `--control-vector*` (3) | adaptadores/vectores | ANTI | anaden computo por token |
| `-m/-mu/-dr/-hf/-hff/-hft` | fuentes del modelo | N/A | ruta local ya fija |
| `--log-*` (7), `-v`, `-lv` | logging | RUIDO | verbosidad alta ralentiza consola Windows; default OK |
| `--offline` | fuerza cache, bloquea red | RUIDO | con ruta local no hay red en arranque |
| `-ctkd/-ctvd` | KV del draft | N/A | sin draft (MTP sancionado) |

### 2.3 sampling params (no mueven t/s; afectan calidad/comportamiento)

| Flag | Veredicto | Motivo |
|---|---|---|
| `--samplers/--sampler-seq`, `-s` | RUIDO | costo por token despreciable |
| `--temp/--top-k/--top-p/--min-p/--top-nsigma/--xtc-*/--typical/--repeat-*/--presence/--frequency/--dry-*/--adaptive-*/--dynatemp-*/--mirostat*` | RUIDO | sampling ya fijado por preset oficial (config-sampling-qwen36.md); por-request en el cliente |
| `--ignore-eos` | UTIL | ya integrado al protocolo del barrido-30 (256 tokens exactos) |
| `-l logit-bias` | RUIDO | caso puntual |
| `--grammar/--grammar-file/-j/-jf` | ANTI | gramatica cuesta CPU por token y frena decode; evitar si velocidad manda |
| `-bs backend-sampling` | RUIDO | experimental; micro-coste |

### 2.4 speculative params

| Flag | Veredicto | Motivo |
|---|---|---|
| `--spec-type draft-mtp/...` (familia draft) | VENENO | medido 16.6-18.9 vs 20.85 (aprendido §1) |
| `--spec-type ngram-simple` + sus 3 params | **ORO (G2)** | nunca medido; borrador gratis; verificacion batched |
| `--spec-type ngram-mod` + sus 3 params | **ORO (G2)** | variante recomendada por la comunidad para MoE |
| `--spec-type ngram-cache` + `-lcs/-lcd` | ORO fase 2 | lookup cache persistente; despues de simple/mod |
| `--spec-type draft-eagle3` | ORO fase 2 (G3) | draft 1-capa casi gratis; requiere GGUF del draft |
| `--spec-type draft-dflash/draft-dspark` | N/A fase 2 | requieren draft externo entrenado; menos maduro que eagle3 |
| `--spec-synth-len/rates` | N/A | "benchmarking only" verbatim; no es decode real |
| `--spec-draft-n-max/n-min/p-split/p-min/sampling/backend-sampling` | PROBADO/N-A | params del draft: solo con draft vivo (MTP sancionado; eagle3 fase 2 los usara) |
| `--spec-draft-threads/-tbd/-Cd/-Crd/-Cbd/...` (afinidad del draft, 8 flags) | N/A | idem; en eagle3 fase 2: draft a 1-2 hilos para no robar nucleos |
| `--spec-draft-n-ubatch` | N/A | spare VRAM del draft; fase 2 |
| `-cmoed/-ncmoed/-otd/-devd/-ngld/-ctkd/-ctvd` | N/A | colocacion del draft; fase 2 |
| `--spec-draft-hf/-md` | N/A | sin draft descargado |
| `--draft/--draft-min/--spec-ngram-size-*` (viejos) | N/A | REMOVIDOS verbatim ("the argument has been removed") |
| `--spec-default` | RUIDO | config por defecto del proyecto; preferimos control explicito |

### 2.5 example/server params

| Flag | Veredicto | Motivo |
|---|---|---|
| `-lcs/-lcd` | ORO fase 2 | lookup caches de ngram-cache |
| `--kv-unified-per-slot` | RUIDO | con slots auto y KV unificado no cambia el caso un usuario |
| `-ctxcp N` (checkpoints, default 32) | RUIDO menor | snapshots de contexto para rollback de slots; uso monousuario simple; si el banner muestra coste, bajar |
| `-cms N` | RUIDO menor | espaciado de checkpoints; idem |
| `-cram N` | **ORO (G5)** | default 8192 MiB pelea la RAM del rig; 512/0 |
| `-kvu / -no-kvu` | RUIDO | unificado default con slots auto; correcto aqui |
| `--cache-idle-slots / --no-...` | UTIL (G5) | acompana a -cram; si -cram 0, queda inerte |
| `--context-shift / --no-...` | ORO (G7) | default disabled; activar para chats >16k con cache-reuse |
| `-r reverse-prompt`, `-sp` | N/A | modo interactivo CLI |
| `--warmup / --no-warmup` | **ORO (G4)** | carga mas rapida; primera peticion paga |
| `--spm-infill`, `--pooling`, `--embd-normalize` | N/A | embeddings/infill |
| `-np N` | PROBADO | NP1 20.92 < campeon; slots auto (4) no estorban al un usuario |
| `-cb / -nocb` | RUIDO | continuous batching default on; con 1 request el overhead es minimo; probar solo si sobran slots del sweep |
| `-mm/-mmu/--mmproj-auto/--mmproj-offload/-mmdev` | N/A | mmproj ya fuera con --no-mmproj (0.90 GB ahorrados) |
| `--image-*/--mtmd-*/--video-*` | N/A | multimodal desactivado |
| `-a/--tags` | RUIDO | metadata API |
| `--host/--port/--reuse-port/--path/--cors-*/--api-prefix/--ssl-*/--api-key*` | RUIDO | red; sin efecto en t/s |
| `--ui-config*/--ui-mcp-proxy/--tools*/--mcp-*/-ag/--connect*` | RUIDO | WebUI/agentes; no tocar |
| `--ui/--no-webui` | RUIDO | apagar la WebUI no mueve t/s medibles (1 request, sin UI abierta) |
| `--embedding/--rerank` | N/A | restringen a otros casos de uso |
| `-to/--sse-ping-interval/--threads-http` | RUIDO | infra HTTP |
| `--cache-prompt/--no-cache-prompt` | UTIL | ON por default = base del "retome" (ya activo en chatear) |
| `--cache-reuse N` | ORO (G7) | default 0; 256 tras el barrido |
| `--metrics/--props/--slots` | RUIDO | endpoints de observacion |
| `--slot-save-path` | UTIL | retome entre reinicios (ofrecido al Director en el analisis de KV) |
| `--media-path/--models-dir/--models-preset/--models-max/--models-autoload` | N/A | router/multimodal |
| `--jinja` | UTIL | ya ON (necesario para el template de Qwen3.6) |
| `--reasoning-format/-rea/--reasoning-effort/--reasoning-budget*/--reasoning-preserve` | UTIL | ya integrados al launcher v1.3 (presupuesto de thinking = respuestas mas cortas = tiempo total menor, no t/s) |
| `--chat-template/-file/--skip-chat-parsing/--prefill-assistant` | RUIDO | template del modelo correcto tal cual |
| `-sps` | RUIDO | seleccion de slot por similitud; un usuario |
| `--lora-init-without-apply` | N/A | sin LoRA |
| `--sleep-idle-seconds` | N/A | default -1 (off); dormir el server no ahorra decode |
| `--log-prompts-dir` | UTIL diagnostic | para cazar mutaciones de prefijo si el retome falla |
| `--embd-gemma-default/--fim-*/--gpt-oss-*/--vision-gemma-*` | N/A/ANTI | presets que DESCARGAN modelos; nunca en este rig |
| `--spec-default` | RUIDO | ver 2.4 |

---

## 3. Como medir el oro (protocolo)

1. **Decode**: igual que los barridos (4 pasadas x 256 tok, descarta la 1a, promedia 2-4, temp 0, `cache_prompt`).
2. **PREFILL (nuevo)**: leer del log del server la linea `prompt eval time ... prompt processing speed` de cada pasada, o `/completion timings` (field prompt tokens/s). Sin esto, G1 es invisible: el CSV del 30 solo guarda tps decode.
3. **CARGA**: columna `load_s` (ya existe en el barrido-30) + hora hasta `/health` OK. G4/G6 se miden ahi.
4. **NGRAM (G2) — REGLA NUEVA**: NUNCA repetir el mismo prompt con spec activo (inflado fake x5 documentado). Usar 4 prompts DIFERENTES de la misma familia y anotar el acceptance rate que imprime el log. Si acceptance < ~20%, el ngram no sirve para ese tipo de contenido y se apaga.
5. Un cambio a la vez; anclas de reproducibilidad (ANCHOR-B/-VJ) en cada corrida.

## 4. Propuesta concreta: BARRIDO-ORO (fase 2, ~12 configs)

Pre-fase (manual, 10 min): exclusión Defender (G6) — se mide sola comparando load_s ANTES/DESPUES.

| # | Nombre | Diferencia sobre BASE+campeon | Frente | Hipotesis |
|---|---|---|---|---|
| 1 | ANCLA-B | (repro campeon) | control | ~21.50 |
| 2 | TB8 | `-tb 8` | prefill | +hilos de prefill, decode intacto |
| 3 | TB8-CRB | `-tb 8 -Crb 0-7 --prio-batch 2` | prefill | prefill a 8 logicos con prioridad |
| 4 | UB512 | `-ub 512` | prefill | default del build vs 256 heredado |
| 5 | UB1K-B4K | `-ub 1024 -b 4096` | prefill | escalada; vigilar fit/VRAM |
| 6 | FULLPRE | TB8-CRB + UB512 | prefill | fusion de ganadores prefill |
| 7 | NGRAM-S | `--spec-type ngram-simple` | decode | 4 prompts distintos; acceptance del log |
| 8 | NGRAM-M | `--spec-type ngram-mod` | decode | variante MoE de la comunidad |
| 9 | NGRAM-M55 | ngram-mod con `--spec-ngram-mod-n-max 32` | decode | borradores mas cortos = menos union de expertos |
| 10 | CRAM512 | `-cram 512` | carga/estab. | protege RAM (chats con cambios de conversacion) |
| 11 | NOWARMUP | `--no-warmup` | carga | arranque mas rapido; medir hasta /health |
| 12 | COMBO-ORO | fusion de los ganadores medidos | final | dinamico como en el 30 |

Fuera del sweep: G3 (eagle3) queda como fase 3 con prerrequisitos; G7 (context-shift + cache-reuse) se activa en el uso diario tras validar el ganador.

## 5. Fuentes

- Dump b11856 del Director (`llama-flags-nuevo.txt`, UTF-16LE, 751 lineas) — fuente de verdad #1, leida integra
- docs/speculative.md oficial (mecanismo batch-vs-secuencial; lista EAGLE3 `AngelSlim/Qwen3-a3B_eagle3`, `Tengyunw/qwen3_30b_moe_eagle3`) — https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md
- PR #16391 host-memory prompt caching (verificado via discussion #20574 tutorial + issue #22127 "size limit: 8192 MiB" + PSA r/LocalLLaMA sobre -cram)
- Prueba honesta ngram (misma-prompt inflation x5; 8 prompts diversos: +6.7% codigo / ~0% prosa) — dev.to "I tested speculative decoding on my home GPU cluster"
- "N-gram speculation is a safe default... almost never hurts" — inventivehq consumer-GPU speculative guide (jun-2026)
- datos de rig y mediciones previas: `aprendido.md`, `informe-velocidad-sweep.md` §11, `ideas-velocidad-30.md`
