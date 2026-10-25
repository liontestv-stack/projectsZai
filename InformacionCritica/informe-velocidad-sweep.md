# INFORME DE VELOCIDAD — situación real, diagnóstico y 100 configuraciones

> LAIA · 2026-10-25 · Fuente primaria: los 5 logs del sweep subidos por el Director (sweep-logs.7z,
> corrido 2026-10-25 07:08) + dump `llama-flags-nuevo.txt` (b11856) + PR #22673 + release v0.7.0.
> Regla de oro aplicada: cada afirmación de flag lleva línea del dump; cada número de t/s sale
> de los logs reales del rig. Cero inventos.

---

## 0. Resumen ejecutivo (3 hallazgos + la ruta a 30 t/s)

1. **El barrido del 25-oct midió mal y a la vez midió la verdad.** El ganador `-cmoe` dio
   **9.33 t/s** (69 tokens, 1 sola pasada); `-ncmoe` fue empeorando (7.33 → 5.58). La medición
   no es comparable entre configs (una se midió con 256 tokens, las otras con 69) y no hay
   repeticiones. Aun así, el VEREDICTO DE FONDO es correcto: **en este rig, con 4 GB de VRAM,
   `-cmoe` (todos los expertos MoE en CPU) es la base correcta y `-ncmoe N` con `-ngl 99` fijo
   es veneno** (ver §2).
2. **Los logs revelan 3 palancas que nunca probamos**: (a) el loader avisa oficialmente
   *"tensor overrides to CPU are used with mmap enabled - consider using --load-mode none"* —
   existe `-lm none|mmap|dio` (dump L87-96); (b) el server arrancó con **4 slots automáticos**
   (`-np -1 = auto`, dump L468) cuando para 1 usuario basta 1; (c) `--moe-cache-mib N` (dump
   L128) — caché de expertos en GPU para expertos residentes en CPU, default 0 = sin usar.
3. **El 23 t/s que recuerda el Director encaja con draft-MTP activo, no con magia.** Base 9.33
   t/s × 2.4 ≈ 22.4 t/s, exactamente el ">2x speed-up with ~75% acceptance" declarado en el PR
   #22673 que introdujo `draft-mtp`. (La alternativa: confundir los ~21-22 t/s de PREFILL con
   la generación — el prefill sí marca 21.08 en el log.) El sweep nuevo lo separa y lo mide.

**La ruta a 30 t/s** (presupuesto honesto, §4): subir la base de 9.33 a ~12-13 t/s con las
palancas de fase A (`-np 1`, `-lm none`, `--moe-cache-mib`, `-t` óptimo, `--poll`) y multiplicar
por draft-MTP bien afinado (×2.2-2.6 medidos en el PR): 12.5 × 2.4 ≈ **30 t/s**. Sin MTP el
techo físico DDR4 está en ~20-23 t/s (§4): **no hay combinación de flags sola que dé 30 sin
draft-MTP**. Con MTP sí es alcanzable.

---

## 1. Los datos reales (fuente: los 5 logs subidos)

Sweep 20261025-070852, cada config = 1 pasada. Prompt de 12 tokens (demasiado chico), generación
de 69 tokens en 4 de 5 configs y de 256 en ncmoe-16 (comparación sesgada).

| Config | t/s generación | t/s prefill | tokens medidos |
|---|---|---|---|
| `-cmoe` | **9.33** | 21.08 | 69 |
| `-ncmoe 16` | 7.33 | 21.31 | **256** |
| `-ncmoe 24` | 5.90 | 22.68 | 69 |
| `-ncmoe 32` | 5.86 | 19.85 | 69 |
| `-ncmoe 40` | 5.58 | 19.80 | 69 |

Extras constantes en todos los logs: `n_threads = 4`, `n_slots = 4, n_ctx_slot = 16384,
kv_unified = 'true'`, reasoning-preserve ON por defecto, warmup interno (task 0) con 2.36-4.44 t/s.

## 2. Diagnóstico: por qué `-ncmoe` perdió y por qué la base es 9.33

**2.1 — El fit abortado (la prueba del crimen).** En los 3 logs de ncmoe-16/24/32 aparece:

```
W common_fit_params: failed to fit params to free device memory:
n_gpu_layers already set by user to 99, abort
```

El build b11856 trae auto-ajuste de VRAM (`-fit, --fit [on|off]`, dump L152: *"whether to adjust
unset arguments to fit in device memory"*). Nuestro lanzador fija `-ngl 99` SIEMPRE, así que el
fit no puede tocar nada: el server mete 16-40 capas de expertos en una GPU de ~3.1 GB libres, el
driver (VMM yes, visto en nvidia-smi del 22-oct) desborda a memoria compartida por PCIe, y el
rendimiento se hunde. **Consecuencia: `-ncmoe` solo tiene una oportunidad si se deja que el fit
trabaje (`-ngl auto` o sin `-ngl`) o si se libera VRAM antes (KV q4_0, `-c 8192`).** En fase C
del espacio de 100 hay 5 configs que lo prueban limpio; si ni así gana, se descarta para siempre.

**2.2 — El warning del loader (palanca gratis).** En TODOS los logs:

```
W llama_model_loader: tensor overrides to CPU are used with mmap enabled
  - consider using --load-mode none for better performance
```

Es el propio build sugiriendo `-lm none` cuando se usan overrides a CPU (`-cmoe`/`-ncmoe` son
overrides). No promete nada, pero es la única recomendación de tuning que el software nos da
gratis y nunca la probamos. Valores verificados (dump L87-96): `auto` (default, actual) |
`none` | `mmap` | `mlock` (PROHIBIDO en este rig: 14.27 GB de modelo / 16 GB de RAM, ya
documentado) | `dio`.

**2.3 — 4 slots automáticos.** El server arrancó con `n_slots = 4` porque el default de `-np`
es `-1 = auto` (dump L468). Para chat de 1 usuario, `-np 1` elimina el overhead de pool KV
dividido y de gestión multi-slot (LCP similarity, checkpoints). Riesgo: cero. Ganancia: por ver.

**2.4 — Por qué la base es 9.33 y no 20.** El modelo activa ~3B de parámetros por token (A3B);
con los expertos en DDR4, cada token generado exige leerlos de RAM. Con DDR4-2666 dual channel
(~42.6 GB/s teóricos, ~30-36 efectivos) y ~1.8-2.0 GB/token efectivos, el techo de ancho de
banda da ~17-20 t/s; el cómputo de los 4 núcleos del i3-10100F y los pageouts (14.27 GB de
modelo / 16 GB de RAM + escritorio) explican quedar en 9.33. **Esta es la razón física por la
que la fase A busca reducir bytes leídos y pageouts (moe-cache, load-mode, apps cerradas) y NO
empujar más capas a la VRAM.**

## 3. El misterio del 23 t/s — hipótesis y cómo la cerramos

- **H1 (la más probable): draft-MTP activo.** El menú [3] del lanzador v1.3 lanza
  `--spec-type draft-mtp --spec-draft-n-max 2`. Con aceptación ~75-85% el speedup medido
  upstream es >2x (PR #22673). 9.33 × 2.4 ≈ 22.4 ≈ 23. La capa nextn (blk.40 en los logs) ya
  está cargada en disco/VRAM aunque no se use sin MTP — los "unused tensor blk.40.*" son eso.
- **H2: prefill confundido con generación.** El prefill marca 21.08-22.68 t/s en los logs; muy
  cerca de 23. Si el número se leyó de un banner/log de prefill, no era generación.
- **Verificación propuesta:** el sweep nuevo mide SIEMPRE la generación con protocolo fijo
  (§8) y, en configs MTP, intenta leer la tasa de aceptación del log del server (best-effort,
  documentado; si el log no la imprime, el t/s final manda). Así el 23 deja de ser un recuerdo
  y pasa a ser un dato reproducible.

## 4. Presupuesto de velocidad hacia 30 t/s

```
base (-cmoe, hoy)                      9.33 t/s
+ np 1, -lm none, moe-cache, -t/poll   +20-50% (por medir, hipótesis de fase A)
base objetivo                          12-15 t/s
× draft-MTP (PR #22673, ~75% accept)   ×2.2-2.6
resultado esperado                     26-39 t/s  → META 30 EN RANGO
```

Sin draft-MTP: techo físico DDR4 ~17-23 t/s (§2.4). **El 30 exige MTP.** La única palanca
además de flags: activar XMP/DDR4-3200 en BIOS si los módulos lo permiten (gratis, +10-20% de
ancho de banda = +10-20% de base). Decisión de hardware del Director, fuera de este documento.

## 5. Palancas verificadas (todas con línea del dump b11856)

| Palanca | Dump | Efecto esperado | Riesgo |
|---|---|---|---|
| `-lm none\|mmap\|dio` | L87-96 | menos pageouts con overrides a CPU | bajo |
| `--moe-cache-mib N` | L128-130 | caché de expertos en GPU (default 0) | VRAM limitada: 128-512 |
| `-np 1` | L468 | 1 slot, pool KV limpio | ninguno para 1 usuario |
| `-t N` (default -1 = auto) | L7 | 3 puede dejar core al OS; 5-8 NO ayudan sin HT real... i3-10100F SÍ tiene HT (4C/8T): probar 5/6/8 | bajo |
| `-tb N` threads-batch | L9-10 | prefill más rápido | bajo |
| `--poll 0..100` (default 50) | L17 | 0 = menos busy-wait (CPU respira); 100 = menos latencia | bajo |
| `--prio-batch 0..3` | L22 | prioridad del prefill | bajo |
| `--no-op-offload` | L166 | ops de host sin offload a GPU | bajo |
| `-ub 128/512/1024` | L31 | buffers de cómputo VRAM vs prefill | medio (VRAM) |
| `-c 8192` | L25 | libera VRAM KV (~1 GB) | menos contexto |
| `-ctk/-ctv q4_0\|f16` | (verificado antes, §A flags) | KV más chico/más grande | calidad mínima |
| `-fit/-fit-target` | L152-159 | el build reparte VRAM solo | con -ngl fijo no actúa |
| `-ngl auto` | L135-136 | deja decidir al fit | puede poner menos capas |
| `--spec-draft-n-max 1/2/3` (default 3) | L352 | más drafts = más techo, más coste por rechazo | medio |
| `--spec-draft-p-min P` (default 0.00) | L369 | filtra drafts débiles | puede bajar aceptación |
| `--spec-draft-p-split P` (default 0.10) | L366-367 | probabilístico vs greedy | bajo |
| `--spec-draft-sampling greedy\|probabilistic` | L374-377 | modo de muestreo del draft | bajo |
| `-cmoed/-ncmoed N` | L344-350 | MoE del DRAFT en CPU/GPU | VRAM del draft |
| `--spec-draft-threads N` | L315 | hilos del draft | bajo |
| `--spec-draft-n-ubatch N` | L357 | VRAM del draft ubatch | bajo |
| `--spec-synth-len/rates` | L360-364 | MTP SINTÉTICO "benchmarking only" | solo diagnóstico de techo |
| `--cache-reuse N` | L620 | KV-shift entre prompts | no cambia t/s de gen |
| `-cram/--cache-ram N` (default 8192) | L446-448 | límite de RAM del prompt cache | 0-256 libera presión |
| `--warmup/--no-warmup` | L463 | mantener warmup ON (compila graphs) | - |

Descartadas y por qué: `--mlock` (RAM justa, ya prohibido), `-dt/--defrag-thold` (L83:
DEPRECATED), `--numa` (monosocket), `-sm/-ts` (1 sola GPU), `--kv-unified-per-slot` (L435,
semántica nueva sin doc de tuning), `-lzm/--lazy-mode` (L99-105: solo tensors >4 GiB, no es
nuestro caso).

## 6. Las 100 configuraciones

Notación: DIFF sobre BASE. BASE = `-m <modelo> -ngl 99 -cmoe -c 16384 -b 2048 -ub 256 -fa on
-ctk q8_0 -ctv q8_0 -t 4 --prio 2 --no-mmproj --host 127.0.0.1 --port 9931` (réplica exacta del
comando V1 del lanzador; el [1] del menú v1.3). Prioridad: A = barrer una variable (OFAT),
B = draft-MTP, C = combinaciones. "SweeP#N" = incluida en el .py de las 25 (§7).

**Fase A — una variable a la vez sobre BASE (50):**

| # | Config (DIFF) | Hipótesis |
|---|---|---|
| A01 | `-t 2` | menos contención con OS |
| A02 | `-t 3` | deja 1 core libre al OS/driver — SweeP#3 |
| A03 | `-t 5` | HT: 1 hyperthread extra — SweeP#4 |
| A04 | `-t 6` | HT x2 |
| A05 | `-t 8` | HT x4 (saturación) |
| A06 | `-tb 8` | prefill con más hilos |
| A07 | `-tb 2` | prefill ligero |
| A08 | `--poll 0` | sin busy-wait, CPU respira — SweeP#5 |
| A09 | `--poll 10` | intermedio |
| A10 | `--poll 25` | intermedio |
| A11 | `--poll 75` | casi máximo |
| A12 | `--poll 100` | latencia mínima — SweeP#6 |
| A13 | `--prio 1` | menos agresivo |
| A14 | `--prio 0` | normal |
| A15 | `--prio -1` | low |
| A16 | `--prio-batch 0` | prefill normal |
| A17 | `--prio-batch 3` | prefill realtime |
| A18 | `-lm none` | warning oficial del loader — SweeP#7 |
| A19 | `-lm mmap` | mmap puro sin auto |
| A20 | `-lm dio` | DirectIO (solo afecta carga, control) |
| A21 | `--moe-cache-mib 128` | caché de expertos chica — |
| A22 | `--moe-cache-mib 256` | — SweeP#8 |
| A23 | `--moe-cache-mib 512` | — SweeP#9 |
| A24 | `--moe-cache-mib 1024` | agresiva (VRAM) |
| A25 | `-np 1` | 1 slot, pool limpio — SweeP#2 |
| A26 | `-np 2` | mitades |
| A27 | `--no-op-offload` | ops host sin GPU |
| A28 | `-ub 128` | buffers chicos |
| A29 | `-ub 512` | default del build (vs 256 nuestro) — SweeP#11 |
| A30 | `-ub 1024` | prefill agresivo |
| A31 | `-b 512` | batch lógico chico |
| A32 | `-b 1024` | batch lógico medio |
| A33 | `-c 8192` | libera ~1 GB VRAM KV — SweeP#12 |
| A34 | `-c 24576` | más contexto (control de coste) |
| A35 | `-ctk f16 -ctv f16` | KV sin cuantizar (control) |
| A36 | `-ctk q4_0 -ctv q4_0` | KV mínimo — SweeP#12b |
| A37 | `--no-kv-unified` | pool por secuencia |
| A38 | `-cram 0` | sin prompt cache en RAM |
| A39 | `-cram 256` | cache RAM limitada |
| A40 | `-lzm off` | lazy mode off |
| A41 | `-ngl auto` | el fit decide capas |
| A42 | `-ngl auto -fit-target 512` | fit con margen menor |
| A43 | A02+A08 (t3+poll0) | combo CPU |
| A44 | A02+A18 (t3+lmnone) | combo load |
| A45 | A02+A22 (t3+moecache256) | combo caché |
| A46 | A08+A18 (poll0+lmnone) | combo load |
| A47 | A25+A02 (np1+t3) | combo slots |
| A48 | A25+A18 (np1+lmnone) | combo slots+load |
| A49 | A25+A23 (np1+moecache512) | combo slots+caché |
| A50 | A29+A06 (ub512+tb8) | combo prefill |

**Fase B — draft-MTP sobre la mejor base plausible `-np 1` (30):**
`MTP-BASE = BASE + -np 1 + --spec-type draft-mtp`

| # | Config (DIFF sobre MTP-BASE) | Hipótesis |
|---|---|---|
| B01 | (std: `-spec-draft-n-max 2`) | el estándar del PR #22673 — SweeP#14 |
| B02 | `-spec-draft-n-max 1` | techo ×2, coste por paso mínimo — SweeP#18 |
| B03 | `-spec-draft-n-max 3` | techo ×4, más rechazos |
| B04 | `-spec-draft-p-min 0.05` | corta drafts muy débiles |
| B05 | `-spec-draft-p-min 0.10` | — SweeP#16 |
| B06 | `-spec-draft-p-min 0.20` | filtro medio |
| B07 | `-spec-draft-p-min 0.30` | filtro duro |
| B08 | `-spec-draft-p-split 0.05` | casi greedy |
| B09 | `-spec-draft-p-split 0.20` | más probabilístico — SweeP#19 |
| B10 | `-spec-draft-sampling probabilistic` | verificación por rechazo — SweeP#20 |
| B11 | `--no-spec-draft-backend-sampling` | sampling del draft en CPU |
| B12 | `-cmoed` | MoE del draft en CPU |
| B13 | `-ncmoed 4` | 4 capas del draft en CPU |
| B14 | `-spec-draft-n-ubatch 64` | VRAM draft mínima |
| B15 | `-spec-draft-n-ubatch 128` | intermedio |
| B16 | `-spec-draft-threads 1` | 1 hilo para el draft |
| B17 | `-spec-draft-threads 2` | 2 hilos — SweeP#21 |
| B18 | `--spec-draft-prio 0` | draft prioridad normal |
| B19 | `--spec-draft-prio 2` | draft prioridad alta |
| B20 | `--spec-draft-poll 0` | draft sin busy-wait |
| B21 | B01+B05 (nmax2+pmin0.10) | combo canónico |
| B22 | B01+B06 (nmax2+pmin0.20) | combo |
| B23 | B03+B06 (nmax3+pmin0.20) | techo alto con filtro |
| B24 | B01+B08 (nmax2+psplit0.05) | combo |
| B25 | B01+B10 (nmax2+prob) | combo |
| B26 | B21+A08 (…+poll0) | combo CPU |
| B27 | B21+A02 (…+t3) | combo CPU |
| B28 | B21+A18 (…+lmnone) | combo load |
| B29 | B21+A22 (…+moecache256) | combo caché |
| B30 | B21+A29 (…+ub512) | combo prefill |

**Fase C — combinaciones globales y exploración de VRAM (20):**

| # | Config | Hipótesis |
|---|---|---|
| C01 | `-ngl auto -ncmoe 4` | fit decide con 4 capas MoE pedidas |
| C02 | `-ngl auto -ncmoe 8` | idem x8 |
| C03 | `-ngl 96 -ncmoe 4 -c 8192` | VRAM liberada + MoE parcial |
| C04 | `-ncmoe 2 -ctk q4_0 -ctv q4_0 -c 8192` | mínima VRAM + MoE parcial |
| C05 | `-ncmoe 4 -ctk q4_0 -ctv q4_0 -c 8192` | idem x4 |
| C06 | mejor(t) + mejor(poll) de fase A | combo medido |
| C07 | mejor(t) + mejor(-lm) | combo |
| C08 | mejor(t) + mejor(moe-cache) | combo |
| C09 | mejor(poll) + mejor(-lm) | combo |
| C10 | mejor(t)+mejor(poll)+mejor(lm) | triple |
| C11 | C10 + mejor(moe-cache) | cuádruple |
| C12 | C10 + np1 | cuádruple |
| C13 | C10 + draft-mtp nmax2 | LA COMBINACIÓN FINAL A |
| C14 | C13 + mejor(nmax) de fase B | afinado |
| C15 | C13 + mejor(p-min) | afinado |
| C16 | C13 + probabilistic | afinado |
| C17 | C13 + mejor(ub) | afinado |
| C18 | C13 + cram 0 | presión RAM mínima |
| C19 | C13 + mejor(tdraft) | afinado |
| C20 | re-validación del ganador global (5 runs) | confirmación final |

## 7. Las 25 seleccionadas para `barrido-qwen-25.py`

Criterio: cubrir TODAS las palancas de alto valor con el mínimo tiempo de carga (~2 min/config),
OFAT primero para poder COMBINAR después. #23-25 se CONSTRUYEN en runtime con los ganadores
medidos del CSV (combinación real, no pre-fijada). Orden de ejecución = orden de la tabla.

| SweeP# | Nombre | Flags (DIFF sobre BASE) | Qué aísla |
|---|---|---|---|
| 1 | BASE | (nada — réplica del ganador 25-oct) | referencia directa con 9.33 |
| 2 | NP1 | `-np 1` | slots |
| 3 | T3 | `-t 3` | hilos ↓ |
| 4 | T5 | `-t 5` | hilos ↑ (HT) |
| 5 | POLL0 | `--poll 0` | busy-wait off |
| 6 | POLL100 | `--poll 100` | busy-wait max |
| 7 | LMNONE | `-lm none` | warning del loader |
| 8 | MOECACHE256 | `--moe-cache-mib 256` | caché expertos |
| 9 | MOECACHE512 | `--moe-cache-mib 512` | caché expertos ↑ |
| 10 | NOOPOFF | `--no-op-offload` | offload ops |
| 11 | UB512 | `-ub 512` | buffers prefill |
| 12 | KVQ4 | `-ctk q4_0 -ctv q4_0` | VRAM KV |
| 13 | C8192 | `-c 8192` | ctx menor |
| 14 | MTPSTD | `--spec-type draft-mtp --spec-draft-n-max 2` | MTP sobre BASE |
| 15 | MTPNP1 | #14 + `-np 1` | MTP + slots |
| 16 | MTPPMIN10 | #15 + `--spec-draft-p-min 0.10` | filtro drafts |
| 17 | MTPNMAX3 | #15 + `--spec-draft-n-max 3` | techo alto |
| 18 | MTPNMAX1 | #15 + `--spec-draft-n-max 1` | techo bajo/estable |
| 19 | MTPPSPLIT05 | #15 + `--spec-draft-p-split 0.05` | split prob |
| 20 | MTPPROB | #15 + `--spec-draft-sampling probabilistic` | muestreo draft |
| 21 | MTPTD2 | #15 + `--spec-draft-threads 2` | hilos del draft |
| 22 | MTPCMOED | #15 + `--spec-draft-cpu-moe` | MoE del draft en CPU |
| 23 | COMBO-A | mejor(t/poll/lm/moecache/np) medidos | combinación real |
| 24 | COMBO-MTP | #23 + draft-mtp nmax2 | combinación final |
| 25 | COMBO-MTP-PLUS | #24 + mejor(pmin/nmax/sampling) | afinado final |

## 8. Protocolo de medición (lo que el barrido hace SIEMPRE)

1. **Un solo cambio por config** (OFAT) — si dos cambian a la vez, no se sabe quién ganó.
2. **Prompt fijo** de ~230 tokens de texto real (mismo para todas, hardcodeado).
3. **4 peticiones por config con `cache_prompt: true`, temp 0 (greedy SOLO para bench — excepción
   documentada al no-greedy de chat), n_predict 256.** Se descarta la 1ª (calentamiento) y se
   promedia 2ª-4ª. Fuente del dato: `timings.predicted_per_second` del JSON de `/completion`
   (misma fuente que los logs del server que ya usa el Director, pero vía API, sin parsear texto).
4. **Pausa de enfriamiento 60 s cada 8 configs** (4 núcleos al 100% durante ~2 h; el stock cooler
   del i3-10100F puede throttlear y envenenar la comparación).
5. **Resumen en CSV append** (`sweep-resultados.csv`): si una config ya tiene t/s válido, se
   SALTA → el barrido puede interrumpirse y reanudarse sin perder nada.
6. **Log del server por config** en `sweep-logs\NOMBRE.log` (mismo formato que los del Director,
   auditable después). Se registra además el warning "failed to fit" si aparece.
7. **Anti-contaminación**: si `/health` ya responde al arrancar, ABORTA pidiendo cerrar el
   server abierto (medir con otro server corriendo falsea TODO). Firefox/Wallpaper Engine/
   Copilot cerrados (los ~963 MiB de VRAM/RAM del escritorio, medidos el 22-oct).
8. **VRAM usada** se intenta registrar por config vía `nvidia-smi` (best-effort; si falla, vacío).

## 9. Cómo usar

1. Cerrar Firefox/Wallpaper Engine/Copilot (y cualquier llama-server abierto).
2. Doble click `BARRIDO-QWEN.bat` → Enter para empezar. ~2 h completas; Ctrl+C corta limpio y
   al relanzar continúa donde iba (CSV).
3. Al terminar: ranking en pantalla + `sweep-resultados.csv` + ganador con su COMANDO EXACTO.
4. Pegar las `FLAGS_GANADORAS` del ganador en `abrir-qwen-apex.py` (v2.0, 5 líneas arriba) —
   el abrir-simple queda alineado al ganador sin editar nada más.

## 10. Respuesta directa: ¿hay mejor forma de medir y de buscar?

**Medir.** Tres niveles, en orden de rigor:
- **Nuestro método (server + `/completion` + timings JSON)**: es el ÚNICO que mide draft-MTP
  real (el MTP vive en el server/llama-cli, no en el bench) y es el mismo dato que el Director
  ya veía en logs. Con protocolo fijo (§8) es comparable y reproducible. ES el correcto aquí.
- **`llama-bench.exe`** (viene en el zip b11856, junto a llama-server): estándar de oro para
  pp/tg sin server, con repeticiones integradas. LÍMITE verificado: no lanza draft-MTP ni el
  stack server. Útil solo para A/B de la BASE (fase A); para fase B no sirve. Nota: su
  existencia en el bin del Director queda por confirmar (`dir D:\llama.cpp\llama-bench.exe`).
- **`--spec-synth-len L` / `--spec-synth-rates P0,P1,...`** (dump L360-364, "benchmarking only"):
  MTP sintético — mide el TECHO teórico del bucle MTP con aceptación simulada, sin depender de
  la aceptación real del modelo. Herramienta de diagnóstico: si el techo sintético con 75% da
  ~2.4x pero el real da 1.5x, el problema es la aceptación, no el setup.

**Buscar.** El grid completo (todas las variables × todos los valores) es imposible: >10^9
combinaciones. La forma profesional es exactamente la del plan: **OFAT** (una variable a la vez,
fase A/B) para encontrar los gradientes, y luego **escalada de combos** con los ganadores medidos
(fase C, que el .py construye solo). Con 25 configs bien elegidas se cubre el 80% del valor de
las 100; las otras 75 quedan documentadas en §6 para profundizar donde el ganador indique.

## 11. Fuentes

- Logs del sweep del Director (sweep-logs.7z, 2026-10-25 07:08): todas las cifras de §1-§3.
- Dump `llama-flags-nuevo.txt` (b11856): L7-31 (threads/batch), L15-24 (prio/poll), L83-105
  (defrag/load-mode/lazy), L123-132 (cmoe/ncmoe/moe-cache), L135-159 (ngl/fit), L166
  (op-offload), L232-390 (spec-*), L433-472 (kv/warmup/parallel), L620 (cache-reuse).
- PR #22673 "llama + spec: MTP Support" (mergado 2026-05-16): ">2x speed-up with ~75%
  acceptance" — verificado en tasks 2/3.
- Release v0.7.0 (2026-10-15): puerto 9931, caché MoE host — verificada en task 3-b.
- nvidia-smi del Director (22-oct): GTX 1650 4095 MiB, ~963 MiB de escritorio → ~3.1 GB libres.
