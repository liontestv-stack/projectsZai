# Nivel 4 (PROPUESTA) — Presupuesto de memoria al límite: VRAM útil de la GTX 1650 + RAM sin pageouts

> Estado: PROPUESTA ronda 0 — pendiente de aprobación del Director para cablear la fase H en `barrido-total.py`.
> Etiquetas: [F] verificado en fuente/media, [M] leído del dump del build b11856 (`llama-flags-nuevo.txt`), [T] teórico/derivado, [N/D] sin datos.
> Convivencia: componible con N1 (dosis EXP), N2 (UD-IQ3_XXS / -MTP), N3 (ORO-UB1K, cache) y N5 (draft externo). Coste: 0 descargas, 0 riesgo de calidad.

## 1. Tesis

El rig gasta dos memorias y hoy solo administramos una. Los expertos ruteados viven en DDR4 (~26-28 GB/s efectivos, cuello de botella), la GTX 1650 tiene ~1.2-1.7 GB de VRAM libre con la config ancla, y la RAM física (16 GB) está tan justa que el build itself advierte sobre pageouts. Este nivel explota ambos frentes con flags que ya existen en b11856: `-ncmoe/-ot` (reparto fino de expertos en VRAM) y `-lm/--load-mode` (control de paginación). **Ganancia esperada: +3-5% por VRAM [T] + 0 a +15% por eliminación de pageouts [N/D → medible en 10 min]. Sin tocar calidad: es el mismo modelo, byte a byte.**

## 2. Mapa de memoria del Qwen3.6-35B-A3B con la config ancla (-ngl 99 -cmoe)

Arquitectura [F ficha oficial Qwen/Qwen3.6-35B-A3B]: 40 capas, layout `10 × (3 × (Gated DeltaNet → MoE) → 1 × (Gated Attention → MoE))` → **30 capas GDN + 10 capas GA**; MoE de **256 expertos, 8 ruteados + 1 compartido**, expert dim 512, hidden 2048; vocab 248320 (padded); GDN: 32 heads V / 16 QK, dim 128; GA: 16 Q / 2 KV, dim 256, RoPE 64.

| Tensor | Params | Bytes @3.26 bpw | Dispositivo con ancla | Tráfico por token emitido |
|---|---|---|---|---|
| Expertos ruteados (256/capa × 40) | 32.21 B | **13.13 GB** (92% del GGUF 14.27 [F]) | **CPU (DDR4)** por `-cmoe` | 8 exp × 1.28 MB × 40 capas = **410 MB/t** |
| Expertos por capa (unidad de reparto) | 805.3 M | **328.2 MB/capa** | — | 10.26 MB/t por capa |
| Expertos compartidos | 125.8 M | 51.3 MB | **GPU** (ver §3) | 5.1 MB/t (NO pasa por DDR4) |
| LM head (salida) | 508.6 M | 207 MB | GPU | 207 MB/t (NO pasa por DDR4) |
| Embeddings entrada | 508.6 M | 207 MB | GPU | 1 fila/t (despreciable) |
| Atención + GDN (40 capas) | ~0.94 B | ~383 MB | GPU | — |
| KV cache q8_0 @16k | — | **~171 MB** | GPU | 10.4 KB/t |
| Estados recurrentes GDN | — | ~50-100 MB | GPU | — |
| CUDA ctx + compute buffers (-ub 1024) | — | ~0.85-1.2 GB | GPU | — |

**Conclusiones del mapa [T derivado de datos F]:**
- Con la ancla, VRAM usada ≈ **2.4-2.9 GB de 4.0** → **libre ≈ 1.2-1.7 GB** → caben **3-5 capas ruteadas** (328 MB c/u) o un draft de ~0.5 GB + 2-3 capas.
- El contexto es BARATO en esta arquitectura: la KV entera @16k pesa menos que 1 capa de expertos. **Reducir `-c` NO es palanca de RAM → NO-GO** (además rompería cache-reuse de N3).
- El 92% del GGUF son expertos ruteados: cada 328 MB que suban a VRAM quitan 10.26 MB/t de tráfico DDR4.

## 3. Front VRAM-A: dosis `-ncmoe` (expertos de capas concretas a VRAM)

**Semántica (CONFLICTO RESUELTO):**
- [M] Dump del propio build b11856: `-ncmoe N` = *"keep the MoE weights of the **first N layers** in the CPU"*. N alto = más en CPU; N bajo = las **últimas** capas suben a GPU.
- [F] shawnmayzes.com (Oct-2026) describe exactamente lo mismo: first N layers en RAM, "lower N means more experts on GPU".
- [F] Guía DocShotgun (HF blog) dice que cuenta "desde las capas más altas" — discrepancia de su nota; su tabla de `-ot` equivalente sigue siendo válida como control explícito.
- **Autoridad: el dump del build del rig.** Verificación en 30 s: comparar en el log `load_tensors: CUDA0 model buffer size = X MiB` con y sin `-ncmoe 38` → debe crecer ~2×328 = 656 MiB. Si no crece, la semántica es la inversa y se usa la vía `-ot` explícita (abajo).
- [F] Discusión #13154 (slaren): `-ot` se aplica AL FINAL sobre el reparto; múltiples `-ot` van como **comma-list** (repetir el flag está deprecado). [F] DocShotgun: `-ot "exps=CPU"` deja **atención + FFN densa + shared expert + KV** en GPU → el shared expert (5.1 MB/t) **ya está en VRAM con la ancla**, no se paga en DDR4.

**Dosis propuestas (sobre ancla ORO-UB1K + `-cmoe`):**

| Config | Flag | VRAM extra | Tráfico DDR4/t | Ganancia [T] |
|---|---|---|---|---|
| H1 (ancla) | `-cmoe` (= `-ncmoe 40`) | 0 | 410 MB + overhead | — |
| H2 | `-ncmoe 38` | +656 MB | −20.5 MB/t | +1.6% |
| H3 | `-ncmoe 37` | +984 MB | −30.8 MB/t | +2.5% |
| H4 | `-ncmoe 36` | +1313 MB | −41.0 MB/t | +3.3% |
| H5 | `-ncmoe 34` | +1969 MB | −61.6 MB/t | +5.2% (solo si libre ≥ 2.0 GB) |
| H6 (blindada) | `-ot "blk\.(3[6-9])\.ffn_.*_exps\.weight=CUDA0"` (capas 36-39 explícitas) | igual H4 | igual H4 | independiente de la semántica de `-ncmoe` |

**El cliff que manda la dosis [F #13154, dpmm99]:** en Qwen3-30B-A3B-Q6_K, desbordar 4 capas de más activó la "shared GPU memory" de WDDM y el caudal fue **12.70 → 1.28 t/s (×10 colapso)**. El undershoot cuesta 5%; el overshoot cuesta 900%. Por eso: dosis ascendente, `nvidia-smi --query-gpu=memory.used --format=csv` tras cada arranque, y **Sysmem Fallback OFF ya fijado (ronda 3)** convierte el spill silencioso en error duro visible.

## 4. Front VRAM-B: reparto cuando hay especulación (interacción con fase E / N5)

- **nextn (MTP) = 858,111,296 B medidos [F API, por diferencia de bytes del repo MTP].** Con `-ngld 99` sube a VRAM (draft casi gratis, MTP rinde ×1.28 [F guía unsloth]); con `-cmoed` se queda en CPU y lee ~11 MB/t extra [T] (penaliza ~1% del gain MTP) pero **libera 858 MB ≈ 2.6 capas ruteadas (+2.2%)**. Casi neutro → dosis empírica: E-nextn-GPU vs E-nextn-CPU+2capas.
- **Draft EAGLE3/DFlash (N5): 421-517 MB [F]** → cabe junto a 2-3 capas ruteadas. Ver `nivel-5-draft-externo-gpu.md`.
- Regla de composición VRAM: nextn/draft (obligatorio para su función) > capas ruteadas (optimización lineal). Nunca caben ambos a tope.

## 5. Front VRAM-C: shootout CUDA vs Vulkan [N/D]

- El backend Vulkan viene en los releases precompilados; probar es gratis: mismo comando con el binario `vulkan`. Riesgo: soporte del arch `qwen3_5_moe` con GDN (gated deltanet) en Vulkan **N/D** → test de arranque 1 min (si el arch falla, NO-GO y se cierra la línea).
- Ganancia esperada ~0 o negativa (los kernels CUDA de Turing ya son buenos); se testea porque es la única variable de runtime sin coste y porque el fallback sysmem se comporta distinto por driver.
- NO aplicar `-ngl` distinto entre backends en la misma dosis: comparar con todo lo demás idéntico.

## 6. Front RAM-A: pageouts (el riesgo silencioso del rig)

**Por qué amenaza [T con números F]:** 16 GB físicos − Windows ~3.5-4 GB = ~12-12.5 GB útiles; modelo 14.27 (APEX) o 14.07 (UD-IQ3_XXS-MTP) + KV 0.17 + estados + buffers + staging del host ≈ **15.3-16 GB de huella**. El margen es ~cero: cualquier presión (navegador, índice de búsqueda) recorta el working set del mmap y el decode lee del SSD. [M] El propio build avisa: mmap *"may reduce pageouts if not using mlock"*.

**Protocolo de detección (10 min, PowerShell):**
```powershell
Get-Counter '\Memory\Page Reads/sec','\Memory\Pages Input/sec' -SampleInterval 1
# correrlo durante decode estable del server; anotar el pico sostenido
```
- Page Reads/sec ≈ 0 durante el decode → RAM limpia, este front rinde 0 y se cierra.
- >0 sostenido → cada unidad es un hard-fault = lectura de página del modelo desde SSD = stall de milisegundos dentro del crítico → hay t/s regalado.

**Dosis `-lm/--load-mode` [M dump: `auto | none | mmap | mlock | mmap+mlock | dio`, default auto]:**
| Config | Flag | Mecánica | Riesgo |
|---|---|---|---|
| H-RAM1 (ancla) | (default auto) | mmap + page cache de Windows | pageouts si hay presión |
| H-RAM2 | `-lm dio` | DirectIO: salta la page cache del GGUF → libera hasta ~1-2 GB de standby y evita la doble residency | carga inicial algo más lenta [T] |
| H-RAM3 | `-lm mmap+mlock` | VirtualLock de ~14.3 GB → **cero pageouts garantizados** si el SO acepta el lock | si la RAM no alcanza, el lock falla o ahoga a otros procesos → dosis última, probar primero con el cuant 13.2 GB de N2 |

- Ganancia: **0% si ya está limpio; 5-15% [T] si estaba paginando** (proporcional a los faults eliminados). Coste: 0 descargas.
- **`-lzm/--lazy-mode` [M]:** `auto` = carga bajo demanda solo tensores >4 GiB; en este GGUF el mayor tensor individual es la capa ruteada (328 MB) → **no aplica; dejar en auto** (documentado para no re-testear).
- Complementarios ya cerrados en ronda 3: plan de energía Alto rendimiento (GUID 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c) y pagefile en SSD (verificar en RUTAS.md).

## 7. Vigilancia (no accionar hoy)

- **Expert streaming desde disco**: ~5 implementaciones comunitarias sin fusionar; el router permite precargar los expertos de la capa siguiente mientras se computa la actual → **~2× teórico por overlap I/O** [F shawnmayzes Oct-2026]. Si se fusiona con soporte GDN, re-evaluar TODO el plan de RAM (el modelo podría ni caber completo en RAM y aun así volar). Revisar mensualmente junto con MoQ/GSQ de N2.
- #29964 (Oct-2026): pipeline parallelism con expertos en host RAM — solo multi-GPU, N/A al rig [F].

## 8. Integración con el barrido (fase H propuesta)

Correr DESPUÉS de B (ancla) y en paralelo con D/E (no dependen entre sí). Autenticadores por config: (1) delta de `model buffer size` del log igual al esperado de la tabla, (2) `Pages Input/sec ≈ 0` durante el medidor, (3) `nvidia-smi` ≤ 3.7 GB siempre, (4) t/s del medidor estándar del barrido.

```
H1  ancla ORO-UB1K (-cmoe, -lm auto)                    -> referencia
H2  + -ncmoe 38                                          -> autentica semántica (buffer +656 MB)
H3  + -ncmoe 37                                          -> dosis media
H4  + -ncmoe 36                                          -> dosis máxima conservadora
H5  + -ot explicito capas 36-39 (=H4 blindado)           -> solo si H2 no autentica
H6  mejor ncmoe + -lm dio                                -> RAM front
H7  mejor ncmoe + -lm mmap+mlock                         -> RAM front agresivo
H8  (si fase E activa) mejor VRAM split: nextn GPU vs nextn CPU + 2 capas
```

## 9. Riesgos y NO-GO predeclarados

- **Overshoot VRAM = cliff ×10 [F]**: dosis ascendente + monitor; jamás saltar a H5 sin medir H4.
- **mlock con RAM justa**: si el arranque con `-lm mmap+mlock` degrada el sistema o falla el lock → revertir a `dio` y cerrar la dosis.
- **Vulkan sin GDN**: NO-GO automático si el arch no carga; no perder >10 min.
- **Intacto**: nada de BIOS, nada de Defender, sin requant local — este nivel solo usa flags del build existente.
- Reducir `-c` para "ahorrar RAM": **NO-GO** (KV = 171 MB; el ahorro es ruido y mata cache-reuse de N3).

## 10. Líneas finales por escenario (rig, rutas reales)

```
:: H4 (sin especulación) — ancla + 4 capas ruteadas en VRAM
D:\llama.cpp\llama-server.exe -m D:\ZLia\models\APEX-I-MINI.gguf -ngl 99 -cmoe -ncmoe 36 -c 16384 -fa on -ctk q8_0 -ctv q8_0 -t 4 --prio 2 -ub 1024 -b 4096

:: H4 + RAM limpia (si Page Reads/sec > 0 en el diagnóstico)
... (lo anterior) -lm dio

:: H4 + MTP con nextn en CPU para liberar VRAM (variante E-H combinada)
... -ncmoe 38 -lm dio --spec-type draft-mtp --spec-draft-n-max 2 -cmoed
```

## 11. Referencias

- Dump del build b11856 del rig (`llama-flags-nuevo.txt`): `-ncmoe` (semántica), `-lm` modos, `-lzm`, `-ot`, `-otd/-cmoed/-ncmoed` — [M]
- Ficha oficial https://huggingface.co/Qwen/Qwen3.6-35B-A3B (40 capas, layout GDN/GA, 256 exp, 8+1, dims, vocab, MTP multi-step) — [F]
- Guía MoE offload DocShotgun: https://huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide (shared expert en GPU con exps=CPU; -ot comma-list; op-offload y -b/-ub) — [F]
- Discusión #13154 (slaren: -ot aplicado al final; dpmm99: colapso ×10 por shared GPU memory con 4 capas de overshoot) — [F]
- shawnmayzes.com Oct-2026 (`--n-cpu-moe` = first N en RAM; expert streaming ~2× sin fusionar) — [F]
- API HF: bytes de UD-IQ3_XXS (13,211,155,424 B), UD-IQ3_XXS-MTP (14,069,266,720 B), nextn (858,111,296 B) — [F]
- Ronda 3 de este repo: Sysmem Fallback OFF (driver 546.01+), powercfg GUIDs, RAM por escenario — [F]

## 12. ANEXO — Cuarta ronda: corrección KV, semillas ya medidas en el rig y leak VRAM del prefill (2026-10-26)

- **CORRECCIÓN a §2 [T]:** la KV se ALMACENA chica pero se LEE completa en cada token por las 10 capas GA: lecturas ≈ posición × 10.9 KB/t → @16k ≈ 179 MB/t desde VRAM (~1.4 ms/t ≈ 3% del turno de 46.5 ms a 21.5 t/s); GDN sigue siendo O(1) ✓. → **Reducir `-c` SÍ es palanca pequeña de decode en posiciones largas** (no de RAM: la KV vive en VRAM). En el barrido-30 (posiciones ~550) el efecto era ≈ 0; en chats largos reales cuenta.
- **SEMILLAS YA MEDIDAS EN EL RIG [F CSV barrido-30]:** NCM38 (`-ncmoe 38 -c 8192` KV q4) 21.67; NCM39 21.30; NCM39Q8 21.61; **NCM37C4 (`-ncmoe 37 -c 4096` KV q4) 22.49 = +4.4%, el mejor decode del barrido**; FIT-A (`-ngl auto -ncmoe 34 -fitt 256`) 22.40 = +4.0%. → La fase H NO parte de cero: semillas FIT-A y NCM37C4. Dosis nueva de aislamiento: NCM37@-c16384 vs NCM37@-c8192 vs NCM37C4 (separa el efecto de capas-GPU del confound ctx-4k). NCM39 ≈ ancla sugiere que con <2-3 capas el overhead de reparto no se paga.
- **Semántica `--fit` confirmada [M dump]:** ajusta solo argumentos NO fijados para caber en VRAM (margen `-fitt` 1024 MiB default, `-fitc` ctx mínimo 4096) → en la fase H fijar SIEMPRE `-c` y `-ngl` explícitos para que fit no mute las dosis en silencio; leer del log cualquier ajuste que fit haya hecho.
- **[F #23635] Leak VRAM en prefill con MTP + KV cuantizada** (detalle y protocolo en N3 §12): en combos H×E, `nvidia-smi` durante prefill; si crece sin parar → KV f16 de diagnóstico y revisar build.
- **Calibración externa [F]:** aminrj.com (24 GB: 3.6 @65k ctx — KV+overhead coherente con la KV chica del 3.6); mychen76 (6 GB VRAM + 32 GB RAM: ~30 t/s híbrido — su CPU/RAM superan al rig, no comparable directo); r/LocalLLaMA 80 t/s @12 GB con MTP (offload completo, no híbrido).
- **Techo N4 sin cambios:** +3-5% por VRAM [T] + 0-15% por pageouts [N/D]; con `-ctxcp 4` (N3 §12) el frente RAM probablemente se resuelva casi solo [T] — el presupuesto de checkpoints puede ser el pageout driver #1 del rig.

## 13. ANEXO — Quinta ronda: `--moe-cache-mib` entra al presupuesto VRAM, mmproj fuera del disco, RAM por `-lm none` con número (2026-10-26)

- **El descubrimiento del N1 cambia el presupuesto VRAM [M dump + F reddit]:** `--moe-cache-mib N` existe en b11856 (default 0) y consume la MISMA VRAM libre que administra este nivel: el pool LRU de expertos CPU vive en VRAM. → El presupuesto de la fase H pasa a tener 3 competidores por los ~1.2-1.7 GB libres [T §8]: (1) más capas de expertos en GPU (bajar `-ncmoe`), (2) pool MEC (512/768/1024 MiB), (3) KV f16 en vez de q4/q8. Los datos comunitarios favorecen al MEC [F: +60% en 4050 6GB con este mismo modelo]: un MiB de cache LRU rinde más que un MiB de expertos permanentes porque el routing es skew (44% de overlap entre tokens consecutivos, hit-rate 47→67% [F #20757]) — **dosis recomendada: MEC 512 primero, subir solo si sobra VRAM y no aparece el cliff.**
- **f16 KV vs KV cuantizada — regla definitiva [F openclawdc, coherente con el rig]:** "f16 KV es más rápido que q8_0 cuando cabe" (cuantizar la KV añade conversión por token; es feature de MEMORIA, no de velocidad). Nuestro KVQ51 midió 0% [F CSV] → en el presupuesto: KV cuantizada SOLO si liberar sus ~90-140 MB permite bajar `-ncmoe` una capa o meter MEC; nunca como apuesta de decode por sí sola.
- **`-lm none` con número comunitario [F openclawdc]:** un reporte midió **RAM del 98% → 71% a la misma velocidad** al añadir lo que antes se llamaba `--no-mmap` (hoy `-lm none`; el build tiene `-lm dio/mmap/mlock/mmap+mlock/dio` [M]). Es la primera medición externa que cuantifica la dosis RAM del N4: con la huella del rig a ~15.5/16 GB, el modo de carga explícito + `mlock` selectivo sigue siendo la palanca #1 de pageouts junto a `-ctxcp 4` [T, ahora con apoyo F].
- **mmproj e imatrix: NO entrar al disco [F tree API]:** el repo MTP trae `mmproj-BF16` 902.8 MB, `mmproj-F16` 899.3 MB, `mmproj-F32` 1.79 GB, `imatrix_unsloth.gguf_file` 192.2 MB → el rig es texto-only y `--mmproj` no está soportado con spec [F ronda 3] → descartarlos ahorra hasta 1.8 GB de disco y elimina el riesgo de que una config futura los cargue por accidente (se comerían 0.9-1.8 MB de VRAM/RAM y fallarían con spec).
- **El cliff silencioso tiene dato de forma [F openclawdc]:** sweep de un 5090 con ncmoe: 20→54, 16→64.5, 12→69.4 t/s y un paso menos → 27.5 t/s (spill de VRAM a RAM SIN error del driver; en Windows el cudaMalloc cae a sysmem en silencio — mecanismo ya documentado con el Sysmem Fallback [F ronda 3]). → Regla operativa del N4 para la fase H: el paso óptimo es "cliff menos uno"; cualquier dosis nueva (MEC incluida) se sube DE a 256 MiB con `nvidia-smi` abierto y el autenticador de buffer-size.
- **Vigilancia streaming [F Strix Halo, build custom]:** un usuario corre Qwen3.8-Flash-Next con el tensor PLE/Engram en **Q8_0 desde NVMe** a 120K+ de contexto (~40 t/s en código) — el streaming de expertos desde disco ya funciona en la práctica (no upstream). Si upstream lo fusiona, el límite de 16 GB RAM del rig deja de ser techo para cuants grandes [N/D fecha]. Seguimos con el plan actual: no esperar.
- **Resumen de dosis N4 v5 (orden de corrida en el rig):** 1) `-ctxcp 4` (libera 1.5-1.8 GB RAM, sin coste) + Sysmem Fallback OFF + plan Alto rendimiento; 2) `-lm dio` (o mmap+mlock) según pageouts medidos; 3) `--moe-cache-mib 512` sobre NCM37C4; 4) si VRAM sobra: MEC 768/1024 o bajar `-ncmoe` a 36; 5) KV f16 solo como diagnóstico del leak #23635. Todo con mediana de 3 corridas [F thc1006, varianza 9.4pp] y baseline matcheado por corrida.
