# IDEAS PARA AUMENTAR LOS t/s — estudio profesional + barrido-30

> LAIA · 2026-10-25 · Para el Director.
> Regla de oro del proyecto: **cero afirmaciones sin verificar**. Cada idea de
> este documento cita su fuente (dump del build = fuente última; web = fuente
> secundaria con URL). Los números de velocidad citados son MEDIDOS en este
> rig (barrido-25, 4 pasadas × 256 tok) o van marcados como hipótesis.
> Complementos: `aprendido.md` (lo que NO repetir) · `informe-velocidad-sweep.md`
> §11 (ranking del 25) · `llama-flags-nuevo.txt` (flags que TU build acepta).

---

## 0. Contexto recuperado (el estado real del rig)

| Componente | Dato verificado |
|---|---|
| CPU | Intel i3-10100F — 4 núcleos / 8 hilos (HT), Comet Lake, solo AVX2 |
| RAM | 16 GB DDR4 (canal dual asumido; el barrido-25 no la verificó — ver idea 8) |
| GPU | 4 GB VRAM — desborde probado con `failed to fit` (aprendido §3) |
| Modelo | Qwen3.6-35B-A3B heretic APEX-I-MINI.gguf — 14,273,277,376 B (~3.3 bits/param) |
| Build | llama-server b11856 (0.7.0-dev, commit 3642238cc) en `D:\llama.cpp\` |
| Puerto | 9931 (default del build) |
| Campeón medido | `-lm none` = **21.50 t/s** (base sin eso: 20.85) — en abrir-qwen-apex.py |
| Techo $0 declarado | 21.5-22 t/s (solo con flags); 30 t/s exigía hardware nuevo |

Lo ya probado y cerrado (aprendido.md, cada punto con su número): draft-MTP
negativo en este rig (10 configs, 16.6-18.9 t/s), `--moe-cache-mib` veneno con
4 GB de VRAM (13.51/17.22), `-ncmoe N` con `-ngl 99` fijo desborda (fit aborta),
`-t 3`/`-t 5` pierden ~2 t/s, liberar VRAM sin más no ayuda, los combos no suman
sobre el ganador solo, `--mlock` prohibido (14.27 GB de modelo / 16 GB de RAM),
y la lección de medición: el 9.33 fantasma era protocolo malo, no el rig.

---

## 1. La física del problema (por qué cuesta lo que cuesta)

La generación de un token en un MoE con los expertos en CPU se reduce a esto:
`t/s ≈ ancho_de_banda_efectivo / bytes_leídos_por_token`. En este rig los
expertos viven en la DDR4 (`-cmoe`) y el resto (atención, densos, KV) en la
GPU de 4 GB. Con ~14.27 GB de modelo y una fracción pequeña de pesos densos,
los tensores de expertos dominan lo que se lee de RAM por cada token: si el
modelo activa 8 expertos por capa y hay ~11 GB de expertos repartidos en las
capas MoE, cada token obliga a leer del orden de 1.0-1.4 GB desde la DDR4.
Con un ancho de banda efectivo típico de DDR4-2666 dual (~28-33 GB/s reales
sobre 42.6 teóricos), eso da 21-26 t/s teóricos — y medimos 21.50. La cuenta
cierra: **el cuello es exactamente ese, no hay misterio residual**.

La consecuencia operativa es dura pero útil: de todo el universo de flags,
solo tres familias mueven la aguja real. (a) **Leer menos bytes por token**:
menos expertos activos, pesos más cuantizados, o parte de los expertos en
VRAM. (b) **Más ancho de banda**: XMP en BIOS o RAM mejor. (c) **Mover
lecturas a memoria más rápida**: más VRAM (no hay) o streaming inteligente
(lo que el barrido-25 ya refutó con `--moe-cache-mib`). Todo lo demás —
hilos, polling, prioridades, batch, KV — solo pelea por las sobras: por eso
el barrido-25 terminó con una sola ganancia real (+3.1% de `-lm none`) y un
techo tan plano.

---

## 2. La pregunta pendiente: ¿bajar la cantidad de expertos ayuda?

**Respuesta corta: SÍ — y hay vía runtime sin tocar el GGUF.** Quedó abierta
en la sesión anterior ("bajar un poco la cantidad de expertos del modelo
ayudara?") porque faltaba verificar si b11856 exponía algún control. Lo verificado hoy:

1. **El dump del build lo permite** (`llama-flags-nuevo.txt` L162-165, verbatim):
   `--override-kv KEY=TYPE:VALUE,...` — "advanced option to override model
   metadata by key", con tipos `int, float, bool, str`.
2. **La clave correcta está documentada en la comunidad**: para la familia
   Qwen3-MoE la clave del GGUF es `qwen3moe.expert_used_count` y se usa
   exactamente así: `--override-kv qwen3moe.expert_used_count=int:N`
   (hilo público "Decreasing Qwen3-30B-A3B sparsity" en r/LocalLLaMA; la misma
   técnica en la guía de DavidAU para activar/desactivar expertos).
3. **La mecánica es segura estructuralmente**: el enrutador produce una
   distribución sobre todos los expertos y el modelo toma los N más probables;
   bajar N de 8 a 6 no rompe ningún tensor, solo ejecuta menos FFN por token.
   El costo es **calidad**, no estabilidad.

La cuantificación honesta, con la aritmética de §1: los expertos dominan los
bytes por token, así que bajar de 8 a 6 expertos activos recorta ~25% las
lecturas de RAM por token → **t/s esperado ~25-27 (hipótesis ±2)**; con 4
expertos el recorte es ~50% → **~28-33 (hipótesis, techo por cómputo)**. No
lineal perfecto no será (la CPU también tiene su piso de cómputo), pero es la
única palanca a $0 con magnitud suficiente para acercarse a 30 t/s.

El riesgo real es la calidad, y las fuentes apuntan en ambas direcciones:
más expertos activos claramente mejora (el experimento comunitario
"Qwen3-30B-A6B-16" con 16 expertos en vez de 8 se describe como "mucho más
listo"), y menos expertos degrada de forma no uniforme — el paper LExI
(arXiv 2509.02753) muestra incluso que el pruning por capas ayuda poco a la
velocidad real si el cuello no es la memoria. Por eso el barrido-30 mide la
curva COMPLETA con controles: EXP10 (10 expertos: si el mecanismo aplica,
debe medir MENOS que el campeón — es la prueba de que el override tomó),
EXP8 (debe clavar con la ancla si el modelo ya usa 8), y la escalera 6/5/4.
Además el script lee `n_expert_used` del log de carga y anota en el CSV si el
override se aplicó de verdad (nada se asume: si el arch del GGUF no fuera
`qwen3moe`, el control EXP10 lo delata de inmediato).

Y si EXP funciona pero la calidad no aguanta: la vía siguiente es **congelar
la reducción en el GGUF con cirugía estilo heretic** (re-entrenar el router o
podar expertos y re-cuantizar) — proyecto aparte, $0, con mejor calidad que
el corte en frío por top-k. Eso queda documentado como paso 2, no como
experimento del barrido.

---

## 3. Todas las ideas, ordenadas por (impacto × probabilidad ÷ coste)

### Idea 1 — EXP: menos expertos activos vía `--override-kv` (la apuesta grande)
La desarrollada en §2. Impacto: **+15-50% teórico**. Probabilidad de que el
mecanismo aplique: alta (flag en el dump + técnica pública); probabilidad de
que la calidad aguante: desconocida hasta chatear. Coste: cero. Es la familia
5/30 del barrido-30 con controles de mecanismo incluidos.

### Idea 2 — XMP en BIOS: el +20% de ancho de banda que está apagado (hipótesis)
Las DDR4 que soportan 3200 MT/s suelen arrancar a 2666 si nadie toca la BIOS
(PSA clásico de r/LocalLLaMA: "make sure your RAM is set to 3200"). Con la
aritmética de §1, pasar de 2666 a 3200 es +20% de ancho de banda teórico →
**~23-26 t/s hipotéticos** sobre el campeón actual. Es $0, toma 10 minutos de
BIOS, y es la segunda palanca más grande después de EXP. No es un flag: no
entra al barrido (no se puede automatizar desde Python), pero es la acción
recomendada al Director si EXP no rinde. OJO: el i3-10100F oficialmente
soporta DDR4-2666; 3200 funciona como overclock de memoria y en algunas
placas requiere activar XMP manualmente. Verificar con CPU-Z (pestaña Memory:
debe decir 1600 MHz = 3200 MT/s... si dice 1333 MHz = 2666 MT/s, hay margen).

### Idea 3 — FIT/NCMOE: meter las últimas capas de expertos en la 4 GB de VRAM
Con `-cmoe` TODOS los expertos viven en RAM. Cada capa de expertos que quepa
en VRAM son ~275 MB que dejan de cruzar la DDR4 por token. La VRAM libre es
mínima, pero se puede comprar espacio bajando contexto (`-c 8192`/`-c 4096`)
y cuantizando KV (`-ctk q4_0 -ctv q4_0`) — exactamente las condiciones que
aprendido.md §3 marcó como las ÚNICAS bajo las cuales reintentar la familia
ncmoe (la vez anterior desbordó porque `-ngl 99` fijo impedía el auto-fit).
El barrido-30 prueba ambas rutas: `--fit` libre con margen `-fitt` (el fit
decide cuántas capas caben) y `-ncmoe` explícito con VRAM liberada. Ganancia
esperada: **+2-7%** (cada capa movida es ~2.5% de los bytes de expertos).
Riesgo conocido y anotado: si el fit no cabe, el log trae `failed to fit` y
el script marca el dato como INVÁLIDO para comparar.

### Idea 4 — Afinidad de CPU: `-Cr/-C/--cpu-strict`
b11856 trae control de afinidad completo (dump L11-22). En un CPU uniforme
4C/8T como el i3-10100F (sin P/E cores), el PSA de hilos +80% no aplica
directo (es para híbridos Intel), pero quedan dos efectos reales: fijar los
4 hilos a los 4 núcleos físicos (evitar que el scheduler los ponga en pares
HT) y esquivar el núcleo lógico 0 (interrupciones/DPC). El oficial
`token_generation_performance_tips.md` de llama.cpp confirma la regla base:
hilos = núcleos físicos (ya la aplicamos con `-t 4`). Ganancia esperada:
**0 a +3%**. Cinco configs baratas lo cierran para siempre.

### Idea 5 — Actualizar el build o probar el fork ik_llama.cpp ($0, binario nuevo)
El build está congelado en b11856 por decisión operativa, pero quedan dos
palancas de software fuera del barrido: (a) **llama.cpp más nuevo**: los
zips oficiales con CUDA ya están validados como método de actualización sin
compilar (RUTAS §3-A), y mainline sigue ganando velocidad MoE ("LLaMA gotta
go fast!", r/LocalLLaMA, mejoras tanto en ik como en mainline); (b)
**ik_llama.cpp**, el fork de ikawrakow especializado en inferencia MoE
híbrida CPU+GPU: reporta mejoras grandes en exactamente este patrón de uso
(usuarios citan hasta 5x sobre CPU-puro; flags propias como `--merge-qkv`
y graph reuse). Regla aplicable: tras cualquier cambio de binario,
**re-auditar el dump de flags** (el procedimiento ya está en
flags-verificadas-LAIA.txt) y re-medir con el protocolo del barrido — el 9.33
fantasma se prohibió precisamente para no comparar builds sin protocolo.

### Idea 6 — Menos bytes por token por modelo: re-quant o modelo menor
El APEX-I-MINI ya está a ~3.3 bits/param (14.27 GB para 35B); un re-quant a
menos bits degradaría más de lo que acelera. La versión honesta de esta idea
es otra: si EXP6/EXP4 valida bien, **el mismo modelo con menos expertos por
token YA es un modelo menor** sin re-quantizar. Y en la retina queda el
escalón siguiente: un hipotético Qwen3.6 de clase 20B-A3B correría ~1.7x más
rápido por pura física. Coste real: descargar/verificar otro GGUF.

### Idea 7 — Cirugía permanente de expertos (solo si EXP valida)
Si EXP6/EXP4 da velocidad y la calidad aguanta en el uso real, se puede
consolidar: editar el GGUF (bajar `expert_used_count` en los metadatos con
gguf-py, o poda heretic de expertos + re-quant) para no depender del flag.
La comunidad ya tiene precedentes (poda de Qwen3-16B-A3B a 64→menos expertos
por kalomaze; heretic hace ablación de expertos como parte de su pipeline).
Prioridad BAJA hasta tener los datos del barrido-30.

### Idea 8 — Verificar que la RAM es dual-channel (2 minutos, puede ser el hallazgo del año)
Si una sola pestaña de RAM estuviera instalada (single-channel), el rig
estaría corriendo a ~21 GB/s teóricos y los 21.50 medidos serían ya el 100%
de la física — PERO con dual-channel real habría ~2x de margen escondido.
CPU-Z (modo Memory) o el Administrador de tareas lo dicen al instante.
El barrido-25 nunca verificó esto: es la verificación pendiente más barata
del rig antes de comprar cualquier cosa.

### Idea 9 — Higiene de sistema (ya aplicada, mantener)
Plan de energía Alto rendimiento, cerrar Firefox/Wallpaper Engine/Copilot al
medir (roban ~963 MiB de VRAM+RAM según los logs del sweep manual), no tocar
el PC durante mediciones. No suma t/s al campeón: evita que las medidas
mientan. Ya está integrado en los checklists de los dos barridos.

### Descartadas con motivo (no se prueban, no se discuten dos veces)
- **`--moe-cache-mib`**: veneno medido (-7.3 t/s con 256 MiB); solo con más VRAM.
- **draft-MTP en todas sus variantes**: negativo medido (10 configs); el draft
  paga la misma DDR4. Ruta a 30 vía MTP cerrada en este hardware.
- **`-nkvo` (KV en RAM para liberar VRAM)**: la aritmética lo mata — la
  atención pasaría a CPU y a 8K de contexto cuesta ~0.7 GFLOP/token extra en
  un i3 de ~30 GFLOPS útiles: techo ~16 t/s. Peor que el campeón.
- **`-lzm on` (lazy-mode)**: lee filas de tensores desde DISCO bajo demanda;
  si toca por token, el disco pierde contra la RAM siempre.
- **`-cram`**: semántica no verificable con fuentes públicas (PR #16391 sin
  detalle accesible desde aquí) — regla del proyecto: flag no entendida, no
  se pasa. Documentada para cuando el build traiga manpage completa.
- **NUMA (`--numa distribute/isolate`)**: single-socket, no hay nodos NUMA.
- **`-b`/`-ub` variables**: solo afectan prefill, no la generación (con 1 slot
  cada token es 1 ubatch); UB512 ya midió ruido (20.77).
- **KV f16/bf16/q5_0**: familia cerrada como ruido (q4_0 midió -0.64; solo
  queda q5_1 como cierre en el barrido-30).
- **Env vars no verificadas** (`GGML_OP_OFFLOAD_MIN_BATCH`, etc.): fuera del
  protocolo hasta que exista fuente que las documente en b11856.

---

## 4. El barrido-30: qué corre exactamente

`barrido-qwen-30.py` (doble click en `BARRIDO-QWEN-30.bat`) — 30 configs que
NO repiten ninguna de las 25 ya medidas, con anclas de reproducibilidad,
protocolo idéntico al 25 (4 pasadas × 256 tok, descarta calentamiento, pausas
térmicas, CSV reanudable) y 3 mejoras documentadas: `ignore_eos` (todas las
pasadas generan exactamente 256 tokens), columna `load_s` (tiempo de carga
por config), y columna `hparams` (arch + n_expert + n_expert_used leídos del
log: prueba objetiva del override de expertos). CSV y logs separados del 25
(`sweep-resultados-30.csv`, `sweep-logs-30\`).

| # | Nombre | Familia | Flags (diff sobre campeón) | Hipótesis |
|---|---|---|---|---|
| 1 | ANCHOR-B | ANCLA | `-cmoe` | reproducir 21.50 en esta corrida |
| 2 | ANCHOR-VJ | ANCLA | `-cmoe -lm mmap` | reproducir 20.85 (base vieja) |
| 3 | EXP10 | EXP | `-cmoe --override-kv …=int:10` | CONTROL: más expertos ⇒ más lento |
| 4 | EXP8 | EXP | `…=int:8` | SANITY: ≈ ancla si el modelo usa 8 |
| 5 | EXP6 | EXP | `…=int:6` | +15-25% t/s (calidad por validar) |
| 6 | EXP5 | EXP | `…=int:5` | punto medio |
| 7 | EXP4 | EXP | `…=int:4` | ruta a ~30 (calidad MUY en riesgo) |
| 8 | FIT-A | FIT | `-ngl auto -ncmoe 34 -fitt 256` | fit empaca expertos de cola a GPU |
| 9 | FIT-B | FIT | `-ngl auto -ncmoe 36 -fitt 256` | más candidatas, fit decide |
| 10 | FIT-C | FIT | `-ngl auto -ncmoe 32 -fitt 384` | margen conservador |
| 11 | NCM38 | NCM | `-ncmoe 38 -c 8192 -ctk q4_0 -ctv q4_0` | 2 capas a GPU |
| 12 | NCM39 | NCM | `-ncmoe 39 -c 8192 -ctk q4_0 -ctv q4_0` | 1 capa, margen holgado |
| 13 | NCM39Q8 | NCM | `-ncmoe 39 -c 8192` | igual pero KV q8 (mejor calidad) |
| 14 | NCM37C4 | NCM | `-ncmoe 37 -c 4096 -ctk q4_0 -ctv q4_0` | 3 capas: agresivo |
| 15 | CR03 | AFF | `-cmoe -Cr 0-3` | 4 núcleos físicos fijados |
| 16 | CMASK55 | AFF | `-cmoe -C 55` | máscara 0x55 (lógicos pares) |
| 17 | STRICT | AFF | `-cmoe -Cr 0-3 --cpu-strict 1` | sin migración de hilos |
| 18 | STRICT55 | AFF | `-cmoe -C 55 --cpu-strict 1` | pares + estricto |
| 19 | CR14 | AFF | `-cmoe -Cr 1-4` | esquivar núcleo 0 (DPC) |
| 20 | PRIO3 | PRI | `-cmoe --prio 3` | realtime sobre high |
| 21 | PRIO0 | PRI | `-cmoe --prio 0` | cierre de curva (normal) |
| 22 | POLL80 | PRI | `-cmoe --poll 80` | afinar entre 50 y 100 |
| 23 | POLL20 | PRI | `-cmoe --poll 20` | punto bajo de la curva |
| 24 | NOHOST | BUF | `-cmoe --no-host` | bypass del host buffer |
| 25 | REPACKOFF | BUF | `-cmoe -nr` | repack de pesos OFF |
| 26 | KVQ51 | BUF | `-cmoe -ctk q5_1 -ctv q5_1` | cierre familia KV |
| 27 | LMDIO | BUF | `-cmoe -lm dio` | cierre load-mode (dato: load_s) |
| 28 | COMBO-TOP | COMBO | dinámico | fusión de los 2 mejores medidos |
| 29 | COMBO-EXP | COMBO | dinámico | mejor EXP × mejor no-EXP |
| 30 | COMBO-X3 | COMBO | dinámico | fusión de los 3 mejores |

(Dif sobre BASE_FLAGS = el comando campeón con `-lm none`; la colocación de
expertos va POR config para que `-ncmoe` no quede anulado por un `-cmoe`
general. El script valida al arranque que toda config traiga `-cmoe` o
`-ncmoe`, y que ninguna use mlock.)

### Cómo interpretar los resultados (está impreso en el ranking también)
- **Anclas primero**: si ANCHOR-B no cae cerca de 21.50 (±0.5), la corrida
  está contaminada (termals, apps abiertas) y TODA comparación es inválida.
- **EXP10 manda sobre EXP6/5/4**: si EXP10 no mide MENOS que la ancla, el
  override no aplicó (arch distinto de `qwen3moe`) y la familia EXP se
  interpreta como "mecanismo no disponible en runtime" — la nota del CSV lo
  dice explícito (`override NO aplico` vs `override APLICADO`).
- **Ganador EXP\***: validar CALIDAD con CHATEAR-QWEN.bat ANTES de adoptar
  (menos expertos puede cortar razonamiento largo; probar con trabajo real).
- **Ganador con `-ncmoe`/`-ngl auto`**: NO pegar tal cual en el launcher —
  su BASE_FLAGS tiene `-cmoe` y `-ngl 99` que lo anulan; el ranking imprime
  la advertencia y hay que quitarlos a mano.
- **`fit-abortado` en notas**: dato INVÁLIDO para comparar (desborde VRAM).

### Verificación realizada antes de entregar (la "verificación si hace falta cambiar")
1. **Auditoría de flags**: los 25 tokens de flag distintos de las 30 configs
   + BASE_FLAGS existen VERBATIM en el dump b11856 (`llama-flags-nuevo.txt`,
   decodificado UTF-16); valores críticos (`auto`, `q8_0`, `q5_1`, `q4_0`,
   `none`, `mmap`, `dio`) también. Test automático incluido.
2. **Contra aprendido.md**: cero `--mlock`/mlock, cero `--moe-cache-mib`,
   cero `--spec-*`, cero `-dt`, cero `--numa`, cero `-t 3`/`-t 5`/`-ub 512`;
   las únicas configs `-ncmoe` cumplen las condiciones sancionadas (fit libre
   con `-ngl auto`, o VRAM liberada con `-c 8192`/`4096` + KV q4_0).
3. **No repetición**: ninguna config coincide con las 25 ya medidas
   (comparación automática contra `barrido-qwen-25.py`).
4. **Test funcional**: 47 checks verdes (py_compile, validación de arranque,
   fusión de combos sin duplicados, diagnóstico EXP aplicado/no-aplicado,
   ranking con empate exacto sin TypeError — el bug v1.1 del 25, CSV
   roundtrip, resume, avisos del ranking, protocolo).
5. **Cambios de última hora aplicados tras la verificación**: ninguno
   pendiente — las 30 configs pasaron el filtro completo tal como están.

---

## 5. Fuentes (verificadas 2026-10-25)

- Dump del build b11856 (`llama-flags-nuevo.txt`, UTF-16LE, 122,440 B) —
  fuente de verdad #1: `--override-kv` L162-165, `-fitt` L155-158, `-fitc`
  L159, `--cpu-strict` L14, `-C/-Cr` L11-13, `--poll` L17, `--prio` L15-16,
  `-lm` L87-98, `-cmoe/-ncmoe` L123-127, `-ngl auto|all` L135-137, `--no-host`
  L73, `--repack/-nr` L71-72, `-ctk/-ctv` L75-78 (sin tipos "turbo" en este
  build), `-kvo/--kv-offload` L68-70, `-lzm` L99-103, `-cram` L446-448.
- r/LocalLLaMA "Decreasing Qwen3-30B-A3B sparsity" — sintaxis
  `--override-kv qwen3moe.expert_used_count=int:N`, default 8.
- r/LocalLLaMA "Qwen3-30B-A6B-16-Extreme is fantastic" — 16 expertos > 8 en
  calidad (dirección contraria de la misma palanca).
- LExI: Layer-Adaptive Active Experts (arXiv 2509.02753) — pruning MoE mejora
  footprint más que velocidad; matiz honesto para §2.
- llama.cpp docs/development/token_generation_performance_tips.md — hilos =
  núcleos físicos; offload de capas.
- HF blog Doctor-Shotgun "Performant local MoE CPU inference" (ene 2026) —
  patrón `-ngl 999` + `-ot exps=CPU` / `--n-cpu-moe`, presupuesto de VRAM.
- Blog mdda "Running ~30B MoE models on an old GTX 1080" — `-ncmoe 30` real
  con 24.9 t/s (modelo Q4_K_M, 8 GB VRAM: más VRAM que este rig).
- ik_llama.cpp (github ikawrakow) + r/LocalLLaMA "LLaMA gotta go fast" — fork
  MoE híbrido más rápido; re-auditar flags si se cambia de binario.
- r/LocalLLaMA PSA "make sure your RAM is set to 3200" — XMP/DDR4 arranca a
  2666 por defecto.
- issue ggml-org/llama.cpp #27501 (ago 2026) — `--fit` NO ajusta `-ncmoe`
  (por eso el barrido fija `-ncmoe` a mano y deja que el fit mueva `-ngl`).
- issue #19528 "expert-override flag" (cerrada como not-planned) — no existe
  flag dedicada; `--override-kv` es la vía soportada.
