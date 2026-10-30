# PLAN COMPLETO DE N4 (P8) — la despensa VRAM/RAM: TODOS los experimentos posibles (ronda 61, 2026-10-31)

> **Qué es este doc:** el inventario COMPLETO de experimentos del N4, pedido por el Director ("hora de n4, planifica los pasos necesarios para no dejar nada de n4 fuera, todos los experimentos posibles"). Recoge TODO lo que el nivel 4 (`nivel-4-memoria-vram-ram.md` §1-§18 + resumen) tiene investigado y lo baja a **peldaños concretos, orden de corrida, autenticadores y criterios de salida**, sin dejar frente abierto y sin inventar nada fuera del dump.
> **El instrumento que ejecuta:** P8 de `InformacionCritica/scripts/CAMPANA-6A10.py` (byte-intacta, cliff-1 automático, certificado VRAM ≤ 3712 MB, mediana de 3 corridas por peldaño) + el archivo editable `campana-6a10-p8-escalera.txt` (el Director activa/inactiva cada peldaño; "edita y vuelve a correr p8"; lo ya medido se suma al CSV).
> **Etiquetas:** [F] verificado en fuente/media · [M] leído del dump del build (`InformacionCritica/configs/llama-flags-nuevo.txt`) · [T] teórico/derivado · [M-arit] aritmética verificada con código esta ronda.

---

## 0. Puertas y estado

- **N4 = P8** (confirmado por el Director, APÉNDICE R60): la petición "gestionar la RAM y balancear recursos para que no se realentice por falta de recursos" se mapea a los certificados ya existentes: **pageouts ≈ 0** (nada se derrama al swap), **nvidia-smi ≤ 3.7 GB**, **delta de buffer en el log**, **escalera ngl + MEC dosis fina + página (-lm)**, **regla cliff-1**.
- **Puerta de P8: P7 verde** (la olla la aplica sola: `p8 exige p7 verde`). Motivo de la casa: el lado RAM de dosis fina del N4 (CTXCP4, `-ctxcp 4`, libera 1.5-1.8 GB de RAM [T]) **vive en P7** — saltarla con `--fuerza` es posible (queda escrito) pero deja ese lado del N4 sin medir.
- **Lo que la olla ya automatiza** (leído del código, P8): ANCLA de la escalera SIEMPRE primero (receta tal cual, mediana de 3); peldaños activos EN ORDEN del archivo; **cliff-1 automático** (t/s < 70% del ancla o server muerto → la escalera SE DETIENE y la frontera queda UN peldaño antes); por cada corrida guarda **t/s del medidor, VRAM usada (nvidia-smi), contador de "pageout" del log, errores**; veredicto GO/DUDOSO + CSV + informe.

## 1. Preflight — higiene antes de subir a la escalera (~10 min, cada sesión)

| # | Check | Fuente/regla |
|---|---|---|
| H1 | Apps cerradas, RAM libre (regla R28: higiene transversal; la RAM del rig es el cuello de botella) | plan §7 transversales |
| H2 | **Sysmem Fallback OFF** verificado (driver 546.01+) — convierte el spill silencioso de Windows en error duro visible | N4 §3, ronda 3 |
| H3 | Plan de energía **Alto rendimiento** (GUID 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c) + pagefile en SSD + C: con espacio (higiene R52: 11/223 GB) | N4 §6, R52 |
| H4 | mmproj/imatrix fuera del disco de trabajo (ya cerrado ronda 5; verificar que no reaparecieron) | N4 §13 |
| H5 | Toda flag de la escalera existe en el dump vigente — verificado esta ronda [M]: `-ncmoe/--n-cpu-moe`, `-cmoe/--cpu-moe`, `--moe-cache-mib`, `-lm/--load-mode`, `-ot/--override-tensor`, `-ctxcp/--ctx-checkpoints`, `-ctkd/-ctvd`, `-cmoed/-ncmoed` | dump líneas 87/99/123/125/128/232/237/344/348/439 |
| H6 | Sin MTP/spec activo en P8 (el MTP exige `-np 1` [M SS11.4] y rompería el NP2 promovido) → el reparto con especulación se PLANEA aquí y se CORRE en P10 (§3.4) | plan R52/R60 |

## 2. El presupuesto que manda (mapa + aritmética verificada)

Receta vigente (config.txt promovido): `-ngl 99 -cmoe -c 16384 -fa on -ctk q8_0 -ctv q8_0 -t 4 --prio 2 --no-mmproj -lm none -np 2 -ub 1024 -b 4096`. VRAM medida con NP2: **2211/4096 MB** [M R52] (dispersión entre sesiones 2211-2353). Libre ANCLA ≈ **1885 MB**.

**La cuenta gruesa [M-arit, base 2211 MB; la escalera + nvidia-smi deciden por peldaño]:**

| Peldaño | Carga extra | Estimado VRAM | Veredicto esperado |
|---|---|---|---|
| NCM38 (+2 capas) | +656 MiB | 2867 MB | OK y bajo certificado |
| NCM37 (+3 capas) | +985 MiB | 3196 MB | OK y bajo certificado |
| NCM36 (+4 capas) | +1313 MiB | 3524 MB | OK, justo bajo certificado (3712) |
| NCM35 (+5 capas) | +1641 MiB | 3852 MB | pasa el certificado, cabe en 4 GB — zona de cliff |
| NCM34 (+6 capas) | +1969 MiB | 4180 MB | **CLIFF esperado** (> 4096) |
| NCM37+MEC512 | +985+512 | 3708 MB | al borde exacto del certificado |
| NCM36+MEC512 | +1313+512 | 4036 MB | sobre el cliff/certificado |

Unidad de reparto: capa de expertos = **328.2 MB** [F]; cada capa que sube quita ~10.26 MB/t de tráfico DDR4 [F §2]. El KV @16k q8_0 pesa ~171 MB [F] — **el KV no es el enemigo, los expertos sí** [F §17].

## 3. La matriz completa — 8 frentes, todos los experimentos posibles

### 3.1 FRENTE VRAM-A — la escalera de expertos a VRAM (`-ncmoe`, el corazón del N4)

| Exp | Peldaño | Acción | Autenticador | Nota |
|---|---|---|---|---|
| A0 | Verificación de semántica (30 s) | correr NCM38 y comparar `load_tensors: CUDA0 model buffer size` del log vs ANCLA | debe crecer **~+656 MiB** (=2×328.2) | si no crece, la semántica es la inversa → vía `-ot` blindada (A5) y se anota |
| A1 | NCM38 | `add:-ncmoe,38` | buffer +656 MiB; nvidia-smi | dosis H2 [T +1.6%] |
| A2 | NCM37 | `add:-ncmoe,37` | buffer +985 MiB | dosis H3; semilla del barrido-30: NCM37C4 22.49 t/s (+4.4%) fue el mejor decode **en el mundo viejo** — aquí se re-mide sobre la receta vigente (dosis NO transfiere entre cuants/configs, N4 §17) |
| A3 | NCM36 | `add:-ncmoe,36` | buffer +1313 MiB | dosis H4, máxima conservadora |
| A4 | NCM35 (fino, opcional) | `add:-ncmoe,35` | — | peldaño intermedio si la frontera queda entre 36 y 37 |
| A5 | NCM34 | `add:-ncmoe,34` | — | dosis H5, SOLO si A3 deja VRAM; **cliff esperado** [M-arit] |
| A6 | Blindado `-ot` (H6) | `add:-ncmoe,37;add:-ot,blk\.(3[7-9])\.ffn_.*_exps\.weight=CUDA0` | buffer igual que NCM37 | control de semántica independiente; `-ot` va comma-list en UN solo flag (repetirlo está deprecado [F #13154]); el patrón no lleva `\|` ni `,` (formato de la tabla) |
| A7 | Aislamiento del confound ctx (diagnóstico) | NCM37 con `-c 16384` (receta) vs `-c 8192` vs `-c 4096` | — | separa el efecto capas-GPU del efecto ctx-4k (lección §12: NCM37C4 mezclaba ambos); **reducir `-c` sigue siendo NO-GO como promoción** (mata cache-reuse N3) — estos peldaños son diagnóstico de decode, no receta |

Reglas de la subida: **ascendente estricta** (A1→A2→A3→A5, jamás saltar peldaño [F cliff ×10: 12.70→1.28 t/s]); el paso óptimo es **cliff-1** (la olla lo aplica sola); dosis nuevas suben de a 256 MiB / 1 capa con nvidia-smi abierto [F §13]. El shared expert, LM head y atención ya viven en GPU con la ancla [F §2] — no se tocan.

### 3.2 FRENTE MEC — el pool LRU de expertos en VRAM (`--moe-cache-mib`, dosis fina en MiB)

| Exp | Peldaño | Acción | Nota |
|---|---|---|---|
| M0 | **D-MEC-0 (control OBLIGATORIO)** | el peldaño ganador SIN MEC (ya medido en la vuelta 1) vs con MEC | el cache chico puede ser **NETO NEGATIVO**: 600 MiB → −48% en setup ajeno [F #29887]; si el pool es menor que el hot set (~1.0 GB del routed activo [T]) el LRU entra en churn (copia+expulsión por token, PCIe doble) |
| M1 | MEC-512 sobre el GANADOR | `add:-ncmoe,37;add:--moe-cache-mib,512` (sustituir 37 por el ganador real) | los datos favorecen al MEC sobre capas permanentes (routing skew: 44% overlap consecutivo, hit-rate 47→67% [F #20757; +60% en 4050 con este modelo]) |
| M2 | MEC-768 / MEC-1024 | `add:...;add:--moe-cache-mib,768` / `,1024` | escalar solo si sobra VRAM y no aparece cliff; de a 256 MiB con nvidia-smi abierto |
| M3 | Techo registrado | — | en producción ajena el MEC escala a 7-9 GiB (+36-40%) [F §14]; nuestro 512-1024 es fracción del working set → ganancia esperable menor; dato para el día que el rig suba de VRAM |

**AVISO de nombre real [M dump línea 128]:** la flag es **`--moe-cache-mib`** — la derivación automática de la olla escribe el placeholder `--cmoe-cache` con nota "verifica el nombre en el dump de TU build": en la tabla editable va el nombre real. Autenticador: delta de buffer en el log (+512/768/1024 MiB) + certificado nvidia-smi.

### 3.3 FRENTE RAM-A — pageouts, el certificado literal de "no se realentice por falta de recursos"

| Exp | Peldaño | Protocolo | Nota |
|---|---|---|---|
| R0 | Diagnóstico de pageouts (10 min) | PowerShell `Get-Counter '\Memory\Page Reads/sec','\Memory\Pages Input/sec' -SampleInterval 1` durante decode estable del medidor; anotar el pico sostenido | ≈0 → **frente cerrado con certificado** (pageouts ≈ 0, la línea RAM del informe de P8); >0 sostenido → cada unidad es un hard-fault al SSD = hay t/s regalado → activar R2 |
| R1 | La palanca principal YA está en la receta | `-lm none` ya vive en FLAGS_BASE | el modo que el reporte ajeno midió **RAM 98%→71% a igual velocidad** [F §13/§17] — el frente parte con la dosis aplicada; lo que falta es CERTIFICAR (R0) |
| R2 | `-lm dio` | `sub:none>dio` | DirectIO: salta la page cache, evita doble residencia, libera hasta 1-2 GB de standby [T]; carga inicial algo más lenta. Solo si R0 detecta pageouts |
| R3 | `-lm mmap+mlock` | `sub:none>mmap+mlock` | **dosis ÚLTIMA, prohibida en este rig salvo headroom demostrado** (14.27 GB de pesos / 16 GB RAM, prohibición ronda 1 + [F §17] "falla o estrella al resto"); solo si CTXCP4 u otra dosis deja headroom real medido; revertir a dio si degrada |
| R4 | `-lzm` lazy | **NO se corre** | no aplica a este GGUF: el mayor tensor individual es la capa ruteada 328 MB < 4 GiB [M §6] — documentado para no re-testear |
| R5 | CTXCP4 (`-ctxcp 4`) | vive en **P7** (candidata) | libera 1.5-1.8 GB de RAM [T], probable pageout-driver #1 del rig (§12); si se salta la puerta con --fuerza, queda registrado como pendiente de P7 |

Complementos ya cerrados (solo verificar en preflight): Sysmem Fallback OFF, Alto rendimiento, pagefile en SSD.

### 3.4 FRENTE VRAM-B — reparto con especulación: se PLANEA aquí, se CORRE en P10

- El nextn (MTP) pesa **858 MB** [F] y ya vive dentro del GGUF vigente; activarlo exige `-np 1` → rompería el NP2 promovido → **no se corre en P8**.
- **Lo que P8 SÍ entrega a P10 (criterio de salida del PASO 8):** el **hueco real de VRAM** como dato, no suposición: hueco = 4096 − VRAM del peldaño ganador [M-arit: si la frontera es NCM37 → hueco ~901 MB (el nextn cabe sin margen); si es NCM36 → ~572 MB (no cabe → `-cmoed` o bajar una capa)].
- Dosis defensivas del draft ya documentadas para P10: KV del draft cuantizada `-ctkd/-ctvd q8_0` [M dump 232/237], ctx del draft chico, y la señal de alarma del fallback silencioso (#26432: aceptación normal + t/s desplomado = driver, no draft); #26038 (sobre-reserva ~800 MiB) cerrado **not planned** → el buffer del draft se mide con el log desde el primer run.
- El duelo **nextn-GPU vs nextn-CPU+2capas** (`-cmoed`) se corre en P10 dentro del duelo spec vs NP2 (criterio ≥ +25%).

### 3.5 FRENTE VRAM-C — shootout CUDA vs Vulkan (la variable gratis)

- V1: test de arranque (1 min) con el binario `vulkan` del release, mismo comando. Si el arch con GDN no carga → **NO-GO automático** y la línea se cierra (no perder >10 min) [§5/§9].
- Si carga: UNA mediana de 3 en el peldaño ganador, **todo lo demás idéntico** (sin cambiar `-ngl` entre backends). Ganancia esperada ~0 o negativa (kernels CUDA de Turing ya buenos); se corre por completitud — es la única variable de runtime sin coste.

### 3.6 FRENTE BUFFERS — `-ub/-b` chicos como intercambio presupuestario

- U1: `-ub 64 -b 512` (la combinación de producción L4 [F §14]) — el micro-batch chico encoge los compute buffers y **libera VRAM para MEC/capas**. Autenticador: delta del compute buffer en el log.
- Es un **intercambio contra lo certificado**: N3 midió ORO-UB1K (`-ub 1024 -b 4096`) como ganador de velocidad → U1 se corre SOLO si la frontera queda corta para MEC (peldaño de segunda vuelta), nunca como promoción directa de velocidad.

### 3.7 DIAGNÓSTICO KV f16 — solo diagnóstico, nunca apuesta de velocidad

- K1: `-ctk f16 -ctv f16` en el peldaño ganador. Regla definitiva [F §13]: **KV cuantizada es feature de MEMORIA, no de velocidad** (f16 es más rápido cuando cabe; KVQ51 ya midió 0% aquí). Se corre solo si: (a) sospecha de leak de prefill #23635 (nvidia-smi creciendo sin parar con MTP+KVQ — aplicará en P10), o (b) para medir cuánta VRAM liberaría des-cuantizar (~90-140 MB) y decidir si compra una capa o MEC.

### 3.8 RATIFICACIÓN dual — el peldaño ganador en modo charla

- D1: ganador + `add:--override-kv,qwen35moe.expert_used_count=4` — la escalera corre con la receta (k de fábrica = 8 = modo TRABAJO); el criterio de salida del PASO 8 exige **modo dual ratificado**: el peldaño ganador también se mide en modo CHARLA k=4 (una mediana de 3) y ambas rectas quedan escritas.

## 4. Las dos vueltas de la escalera (sesiones y orden)

- **Vuelta 1 (sesión 1, ~45-60 min):** preflight → `p8` con la tabla de subida pura (ANCLA + NCM38→NCM34). La escalera sola encuentra la frontera VRAM del cuant y el cliff. (La olla re-mide el ANCLA en cada arranque: eso es también el ancla de sesión; la GPU fría miente ~−15%.)
- **Vuelta 2 (sesión 2, ~60-75 min):** preflight → `p8` con la tabla combinada (GANADOR + MEC0/512/768, DIO si R0 lo pide, U1, K1, D1) + **bookend** (re-corrida del ANCLA al cerrar; debe devolver ≈ ancla).
- **Avulsos (10-15 min, cualquier sesión):** R0 (Get-Counter), V1 (Vulkan), A0 (autenticación de semántica — de hecho, primer peldaño).
- **AVISO de orden (trampa cazada esta ronda):** la derivación automática deja **NGL-87/NGL-93 ACTIVAS ANTES** que cualquier peldaño NCM. Bajar `-ngl` manda capas enteras de atención+GDN a CPU (castigo muy mayor que mover expertos) → probable cliff temprano que **detendría la escalera antes de la subida NCM** y la dejaría sin correr. Corrección en la tabla editable: peldaños NCM PRIMERO; NGL-87/93 INACTIVAS (la escalera descendente de ngl es el diagnóstico del suelo del backbone, va al final y aparte, si se quiere).

## 5. La tabla lista para pegar en `campana-6a10-p8-escalera.txt`

**Vuelta 1 — la subida pura (buscar la frontera):**

```
# ESCALERA P8 vuelta 1 — subida NCM (la despensa). Orden = orden del archivo.
# ANCLA SIEMPRE primero. cliff-1 automatico (t/s < 70% del ancla o server muerto
# = la escalera se detiene y la frontera queda un peldano antes).
ANCLA | | ancla | la receta diaria tal cual (NP2, -lm none, UB1K)
NCM38 | add:-ncmoe,38 | activa | +2 capas a VRAM (+656 MiB); autentica semantica: buffer +656 MB (A0)
NCM37 | add:-ncmoe,37 | activa | +3 capas (+985 MiB); semilla barrido-30 22.49 t/s en el mundo viejo
NCM36 | add:-ncmoe,36 | activa | +4 capas (+1313 MiB); maxima conservadora, justo bajo certificado 3712
NCM35 | add:-ncmoe,35 | activa | +5 capas (+1641 MiB); zona de cliff, la regla cliff-1 decide
NCM34 | add:-ncmoe,34 | activa | +6 capas (+1969 MiB); CLIFF esperado (>4096): la escalera debe parar aqui
NGL-87 | sub:99>87 | inactiva | diagnostico del suelo del backbone (GDN/aten a CPU): va aparte al final
NGL-93 | sub:99>93 | inactiva | idem
BLIND-OT37 | add:-ncmoe,37;add:-ot,blk\.(3[7-9])\.ffn_.*_exps\.weight=CUDA0 | inactiva | control -ot (H6): activar si A0 no autentica la semantica
```

**Vuelta 2 — la pila sobre el ganador (sustituir NCM37 por el ganador real de la vuelta 1):**

```
ANCLA | | ancla | re-ancla de sesion (y bookend al final re-corriendo solo esto)
WIN | add:-ncmoe,37 | activa | el ganador de la vuelta 1 (peldano de referencia de esta vuelta)
WIN+MEC512 | add:-ncmoe,37;add:--moe-cache-mib,512 | activa | MEC 512 sobre el ganador (flag REAL del dump: --moe-cache-mib)
WIN+MEC768 | add:-ncmoe,37;add:--moe-cache-mib,768 | inactiva | escalar solo si 512 no toca el certificado
WIN+DIO | add:-ncmoe,37;sub:none>dio | inactiva | variante RAM: activar SOLO si el Get-Counter (R0) detecto pageouts
WIN+UBCHICO | add:-ncmoe,37;add:-ub,64;add:-b,512 | inactiva | intercambio presupuestario L4 (U1): menos buffer, mas VRAM para MEC/capa
WIN+KVF16 | add:-ncmoe,37;sub:q8_0>f16 | inactiva | diagnostico KV (K1): un solo sub pisa AMBOS -ctk y -ctv (la cirugia sustituye TODAS las apariciones); verificar en el log que la KV quedo f16
WIN+CHARLA4 | add:-ncmoe,37;add:--override-kv,qwen35moe.expert_used_count=4 | activa | ratificacion dual (D1): el ganador en modo charla k=4
```

**Nota WIN+KVF16:** `sub:q8_0>f16` reemplaza las DOS apariciones (`-ctk q8_0` y `-ctv q8_0`) en un solo verbo — no hace falta encadenar dos `sub`; igualmente no estorba si se encadena.

## 6. Autenticadores y certificados por peldaño (los 5 de la casa)

1. **Delta de buffer** en el log (`load_tensors: CUDA0 model buffer size`) igual al esperado de la tabla (capas×328.2 MiB; MEC suma sus MiB) [F §8].
2. **Pages Input/sec ≈ 0** durante el medidor (Get-Counter, R0) — el certificado literal del Director.
3. **nvidia-smi ≤ 3712 MB** (la olla lo mide por corrida y avisa sola si se pasa: `VRAM_CERTIFICADO_MB`).
4. **t/s del medidor estándar**, mediana de 3 corridas; cliff si < 70% del ancla o server muerto (la olla para sola — regla cliff-1).
5. **Contador de "pageout" en el log del server** (la olla lo suma por corrida; el build avisa de pageouts en la carga).

## 7. Cliff y NO-GO predeclarados (nada nuevo se improvisa)

- **Overshoot VRAM = cliff ×10** [F: 12.70→1.28 t/s; 5090: 69.4→27.5] → dosis ascendente, jamás saltar peldaño, el óptimo es cliff-1.
- **mlock sin headroom = prohibido** (dosis última, §3.3 R3).
- **Reducir `-c` para "ahorrar RAM" = NO-GO** (KV 171 MB; mata cache-reuse N3) — los peldaños A7 son diagnóstico, no receta.
- **Vulkan sin GDN = NO-GO automático**, máx 10 min.
- **MEC chico sin control = riesgo −48%** → M0 obligatorio.
- **Nada de BIOS, Defender, requant**; ninguna flag fuera del dump; NP2+CMS1024 siguen sin medirse juntas (CMS1024 sigue aparcada).
- **Sanity con tool-calling:** no obligatorio en P8 (no cambia cuant ni draft — el modelo es el mismo byte a byte); el spot de anclas de la olla queda disponible si el Director lo pide.

## 8. Criterios de decisión y salida de P8

- **Promoción de dosis:** el peldaño ganador debe superar al ANCLA por **≥ +5 pp sostenido** (mediana de 3; regla transversal: no perseguir deltas < 5 pp). Con < +5 pp la receta diaria NO se toca y P8 cierra con frontera = ANCLA (resultado válido: la despensa ya está bien repartida — el techo del nivel era +3-5% por VRAM [T] + 0-15% por pageouts).
- **Criterio de salida del PASO 8 (intacto):** frontera VRAM estable sin cliff + modo dual ratificado (D1) + hueco real para el draft registrado como dato + pageouts certificados (R0). La VRAM queda **cerrada**.
- **El orden no cambia:** P7 primero (puerta de P8, lado RAM de dosis fina), P8 antes de P9 (el presupuesto del draft se mide con la VRAM ya cerrada), P10 usa el hueco y el duelo spec vs NP2.

## 9. Registro y cierre (protocolo de la casa)

La olla escribe estado (`campana-6a10-p8` + CSV + informe). Cosecha append-only en `plan-siguientes-10-pasos.md` (mediana de medianas del peldaño ganador, frontera, cliff, certificados), estado de ronda en el README de niveles-velocidad, commit en español + push a origin/main, Worklog: Task ID, y las tres ollas re-verificadas por huella. En P9 (b11901) el mundo nuevo se re-ancla y el peldaño ganador se re-certifica (build nuevo = mundo nuevo); en P10 el hueco medido alimenta el presupuesto del draft.

---

## Cheatsheet operativa del N4 (P8)

- **Orden de dosis:** preflight H1-H6 → A0 semántica → escalera NCM ascendente (cliff-1 automático) → D-MEC-0 → MEC 512 sobre el ganador → escalar de a 256 MiB → R0 pageouts (certificado o dio) → U1/K1 solo si hacen falta → D1 charla k=4 → bookend.
- **Autenticadores:** delta de buffer en el log, Pages Input/sec ≈ 0, nvidia-smi ≤ 3712 MB, mediana de 3, contador pageout del log.
- **Reglas de oro:** cliff−1; el MEC y las capas compiten por los mismos ~1885 MB libres [M-arit]; draft (P10) con prioridad sobre capas cuando entre; `-lm none` ya vive en la receta — certificar, no repetir; `--moe-cache-mib` es el nombre real de la flag; NGL descendente va al final y aparte.
- 📄 Fuentes completas y auditoría: [`nivel-4-memoria-vram-ram.md`](nivel-4-memoria-vram-ram.md) (§1-§18) · `plan-siguientes-10-pasos.md` PASO 8 + APÉNDICE R60/R61.
