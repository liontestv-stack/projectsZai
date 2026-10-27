# APRENDIDO — lo que NO funciona en este rig (lista de no-repetir)

> LAIA · 2026-10-25 · Fuente: barrido real 25/25 (`sweep-resultados.csv`,
> corrida completa del BARRIDO-QWEN.bat) + logs del sweep manual del mismo día.
> Cada línea lleva su número medido. **Regla de uso: antes de probar cualquier
> flag nueva, mirar aquí — lo que está en esta lista ya se probó y perdió.**
> No repetir experimentos que ya tienen veredicto.

---

## 1. draft-MTP — el ×2 prometido NO existe en este rig

- Las **10 configuraciones MTP** del barrido miden **16.6-18.9 t/s**: TODAS por
  debajo de la BASE (20.85). Castigo: **-2.0 a -4.2 t/s**.
- La mejor variante (MTPTD2, 18.53) sigue perdiendo 2.3 t/s. La peor
  (`--spec-draft-n-max 3`, 16.62) pierde 4.2: más fichas propuestas = más
  trabajo tirado cuando el borrador falla.
- Por qué: el ×2.4 del PR #22673 se midió en otro hardware. Aquí el draft
  (capa nextn, blk.40) corre sobre la MISMA DDR4 que frena todo — el coste
  del borrador + verificación supera lo que ahorra.
- **Consecuencia: la ruta a 30 t/s vía MTP está CERRADA en este hardware.**
  No re-probar variantes MTP sin un cambio físico (RAM más rápida).

## 2. `--moe-cache-mib` — veneno con 4 GB de VRAM

- 256 MiB → **13.51 t/s (-7.34)**. 512 MiB → **17.22 t/s (-3.63)**.
- Por qué: la caché de expertos roba VRAM a los pesos densos; con ~3.1 GB
  libres el driver desborda a RAM compartida por PCIe y todo se hunde.
  La de 256 es peor que la de 512 (probable thrashing: caché tan chica que
  evicta constantemente).
- **No usar nunca en esta GPU.** Solo volvería a considerarse con más VRAM.

## 3. `-ncmoe N` con `-ngl 99` fijo — desborda la VRAM

- Sweep manual (logs 07:08): `-ncmoe 16/24/32/40` = 7.33 / 5.90 / 5.86 / 5.58.
  Cuantos más expertos a GPU, PEOR.
- Prueba del crimen en los logs: `failed to fit params to free device memory:
  n_gpu_layers already set by user to 99, abort` — el auto-fit de VRAM no
  puede actuar y el driver mete las capas a GPU por la fuerza (VMM → RAM
  compartida).
- Si algún día se re-intenta: solo con el fit libre (`-ngl auto`) o VRAM
  liberada de verdad (KV q4_0 + `-c 8192`) — el barrido no lo llegó a limpiar
  porque la familia entera perdió antes.

## 4. Hilos: `-t 3` y `-t 5` pierden — `-t 4` es el punto dulce

- `-t 3` → 18.29 (**-2.56**): deja un núcleo sin uso, menos ancho de banda
  en vuelo.
- `-t 5` → 18.75 (**-2.10**): hyperthreading = dos hilos peleándose por el
  mismo núcleo físico. En inferencia limitada por RAM el HT solo estorba.
- 4 hilos = 4 núcleos físicos del i3-10100F. Cerrado.

## 5. Ajustes "liberadores" que NO liberan nada

- `-c 8192` (menos contexto) → 20.38 (**-0.47**).
- `-ctk q4_0 -ctv q4_0` (KV mínima) → 20.21 (**-0.64**) — y regala riesgo de
  calidad a cambio de nada.
- `--no-op-offload` → 20.48 (**-0.37**).
- **Moraleja: el cuello de botella NO es la VRAM ni los slots — es el ancho
  de banda de la DDR4.** Todo lo que no reduzca bytes-leídos-por-token es
  ruido o pérdida.

## 6. Las palancas ganadoras NO se suman entre sí

- COMBO-A (np1 + poll100 + lmnone) = 21.33 — **menos** que LMNONE solo
  (21.50). Combinar lo mejor de cada variable no acumula: rozan la misma
  fricción y el máximo lo captura `-lm none` solo.
- No perseguir mega-comandos: el ganador simple ya es el techo práctico.

## 7. Cosas prohibidas de siempre (re-confirmado)

- `--mlock`: PROHIBIDO en este rig — 14.27 GB de modelo / 16 GB de RAM; no
  hay margen para fijar el modelo entero en memoria. (En b11856 además la
  flag vive bajo `-lm mlock`, mismo veneno.)
- Flags muertas del build viejo: `--no-mmap`/`-dio` (sustituidas por
  `-lm auto|none|mmap|dio|mlock`), `-dt/--defrag-thold` (DEPRECATED),
  `--jinja` (ya viene ON por defecto en b11856).
- `--spec-type mtp`, `-nkvo`, `--draft-max`: nombres que no existen o están
  muertos — ver `flags-verificadas-LAIA.txt` antes de escribir cualquier
  comando a mano.

## 8. Lección de MEDICIÓN (la más cara: nos costó un falso 9.33)

- El sweep manual de la mañana midió **9.33 t/s** para la misma BASE que en
  el barrido da **20.85**. La diferencia era el MÉTODO, no el rig:
  - 69 tokens por pasada (demasiado corto: el calentamiento pesa dentro),
  - 1 sola pasada SIN descartar la de calentamiento,
  - configs comparadas con nº de tokens distinto (69 vs 256).
- **Protocolo que sí vale** (el del barrido): 4 pasadas × 256 tokens con
  `cache_prompt`, temp 0, se descarta la 1ª, se promedia 2-4, pausas
  térmicas, CSV reanudable, ruido declarado ±0.3-0.5.
- Regla: **ningún número de t/s se reporta sin protocolo** — un dato mal
  medido mandó a todo el equipo a buscar un "techo 9.33" que nunca existió.

---

## Lo que SÍ funciona (contraste rápido)

| Qué | Dato |
|---|---|
| `-lm none` | 21.50 t/s (+3.1%) — GANADOR, ya pegado en abrir-qwen-apex.py |
| `-t 4` (BASE) | 20.85 t/s |
| `-cmoe` como base | correcto en este rig (los expertos en CPU) |
| preset think en sampling | calidad sin coste de velocidad (no afecta al t/s) |

**Techo del rig a $0: ~21.5-22 t/s.** Único margen $0 restante: XMP
DDR4-3200 en BIOS (hipótesis ~23-25, sin medir). 30 t/s exige hardware
nuevo (más VRAM o RAM más rápida).
