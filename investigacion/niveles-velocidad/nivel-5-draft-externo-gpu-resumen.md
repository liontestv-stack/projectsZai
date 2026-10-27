# RESUMEN SIMPLE — Nivel 5: Draft externo en GPU (fase S especulativa — la vía al ×2)

> **Qué es este archivo:** la misma información que `nivel-5-draft-externo-gpu.md`, punto a punto y sección por sección (los números de § coinciden), pero explicada en términos simples y resumida.
> **La información completa (tablas del estudio, fichas técnicas, SHA256, auditoría punto a punto) está en el archivo completo.** Este resumen no añade nada nuevo.
>
> Etiquetas simplificadas: **[medido aquí]** = probado en este rig / leído del dump del build · **[verificado afuera]** = confirmado en fuente externa · **[estimación]** = cuenta propia.

---

## 1. Tesis (§1)

- **Idea simple de la decodificación especulativa**: un "draft" (borrador chiquito) adivina varios tokens de golpe y el modelo grande los verifica todos en un solo pase. Verificar k tokens cuesta ~lo mismo que verificar 1 → **cada token adivinado es velocidad casi gratis**.
- Además del MTP interno (fase E, la cabeza draft del propio modelo), existen **drafts sidecar** entrenados para nuestro modelo exacto que caben en la VRAM libre de la 1650.
- Este nivel convierte "MTP sí o sí" en una **decisión empírica**: se mide MTP vs sidecars y gana el mejor.

## 2. Inventario de drafts para nuestro modelo (§2)

| Draft | Tamaño | Aceptación publicada | Estado simple |
|---|---|---|---|
| **EAGLE-3 "Caption"** | 517 MB | 83% (¡pero medido en captions de imágenes en inglés!) | GGUF publicado |
| **DFlash** (z-lab oficial) | 421 MB | sin número; "mejor en prompts largos" | GGUF publicado |
| **DSpark** | 286-556 MB | aceptación plana (ver §13) | sidecar descubierto ronda 6 |
| Draft denso de la familia (0.8B-27B) | — | — | **NO-GO** (muere por coste, ver §12) |

- Corrección importante: el NO-GO viejo de DFlash quedaba ligado a otra configuración; con 421 MB medidos **cabe holgado** → pasa a dosis de barrido.
- **Advertencia de dominio (la más importante)**: el 83% de EAGLE3 se midió en su dominio de entrenamiento (captions EN). En chat ES la aceptación real será menor → por eso la fase S es un A/B medido, no una apuesta.

## 3. Mecánica en el build (§3)

- El build soporta varias familias especulativas y `--spec-type` acepta **listas compuestas** (p.ej. DFlash + ngram a la vez).
- Con `-hfd`, llama.cpp descarga el draft y deduce el tipo solo desde la metadata del GGUF. Para rutas locales: `-md` + tipo explícito (sin ambigüedad).
- Flags de draft: carga, dispositivo (`-ngld`), KV del draft (`-ctkd/-ctvd`), dosis (`--spec-draft-n-max/n-min/p-min`), prioridad. Y existe un **bench sintético** (`--spec-synth-*`) que mide el coste de la maquinaria especulativa sin draft real.

## 4. Presupuesto en el rig (§4)

- El draft vive **SIEMPRE en GPU** aquí: en CPU mataría la ganancia (leería ~0.5 GB/token extra).
- Su KV es de pocos MB (1-2 capas).
- Con spec: `-np 1` obligatorio y sin mmproj → **los slots del N3 y el spec no coexisten**: elegir por escenario (chat interactivo → spec).

## 5. Matemática de aceptación (§5) [estimación]

- Tabla simple: con aceptación p y n-max n, los tokens esperados por ciclo son E ≈ (1−p^(n+1))/(1−p). Ejemplos: p=0.83 y n=2 → 2.4; p=0.70 y n=2 → 2.0; p=0.50 y n=7 → 1.9.
- Referencia medida: MTP n2 = ×1.28. Un sidecar con p≈0.7-0.8 podría dar **×1.8-2.5** → el único nivel del proyecto cuyo techo llega al objetivo 43-45 t/s.

## 6. Matriz de decisión (§6)

- Se resuelve con el barrido, no con opiniones: MTP = ancla (ya inventariado con SHA256); EAGLE3 = riesgo de dominio; DFlash = bajo-medio; la ganadora = mejor t/s × calidad en spot-check.

## 7. Dosis fase S propuesta (§7)

Escalera S0-S5: ancla sin spec → MTP n2 → EAGLE3 (n3 y alrededor) → DFlash (n7/p-min 0.50, dosis de comunidad) → compuesta con ngram → sintético de overhead. Autenticadores por config: log del spec cargado + aceptación observada + t/s + **spot-check de calidad en ES** (obligatorio para EAGLE3) + nvidia-smi ≤ 3.7 GB.

## 8. Riesgos y NO-GO predeclarados (§8)

- Dominio del draft: si la aceptación en ES cae bajo 0.45, la vía sidecar muere y MTP queda como único spec.
- Defaults: greedy + p-min 0 preservan la distribución del target; subir p-min solo en dosis alternativas.
- Overhead CPU↔GPU por ciclo → el sintético (S5) lo mide antes de concluir.
- Multi-slot muerto con spec; VRAM overshoot → cliff ×10 (N4); ngram sobre chat general ya está muerto [medido aquí].
- Descargar SOLO los GGUF de los drafts (no los safetensors grandes).

## 11. Anexo ronda 4: números oficiales de DFlash y el régimen (§11)

- **DFlash (card oficial z-lab)**: draft de difusión por bloques de 0.4B; en GPU grande mide **×2.96-3.61** según tarea. Sus números no son transferibles, pero en un rig limitado por RAM el verify de bloque cuesta ≈ 1 pasada → el techo relativo aquí es MAYOR [estimación].
- Regla oficial: `--spec-draft-n-max` se CLAMPA al block size entrenado del draft.
- Anti-dato de la época (luego corregido en §12): en full-GPU todos los modos spec "perdían" — dato de una v1 rota; no refuta nuestra tesis.
- Qwen3.5-0.8B tiene el mismo vocabulario que el target (dosis S6 con draft-simple) — luego muere formal (§12).
- Calibración MTP: en GPU-bound el MoE paga poco (×1.17); rango realista aquí: ×1.2-1.8.
- #25345: con KV unificada el server puede ignorar el draft en silencio → autenticador obligatorio (log + aceptación > 0).

## 12. Anexo ronda 5: estudio controlado v4 en 3090 — EL dato duro (§12)

Existe un estudio público y riguroso **sobre nuestro modelo exacto** (3.002 corridas, checker anti-drift, errata propio que se retracta de su v1 negativa):

| Modo | Δ vs baseline | Lectura simple |
|---|---|---|
| **DFlash-n2** | **+26.3%** | el ganador |
| MTP-n2 | +22.7% | segundo |
| DFlash-n4 | +19.2% | n4 ya pierde vs n2 |
| ngram-* | −0.3% a −19% | muerto fuera de coding |
| **draft externo denso 0.8B** | **−73% / −75%** | MUERTO (el coste de sus forwards come todo) |

- **Orden oficial**: DFlash-n2 > MTP-n2 > DFlash-n4 >> ngram >>> draft externo denso. **La dosis n2 domina** porque la aceptación cae con la profundidad más rápido de lo que crece el ciclo.
- **S6 (draft-simple) = NO-GO formal**: pierde −73% incluso en GPU.
- Lecciones de medición para el rig: no fiarse del accept rate del log como métrica única (la v1 midió "100%" falso); el draft auto-convertido fue la causa del falso desastre inicial; mediana de 3 corridas.
- Dosis fase S actualizada: S1 = MTP n2 → S2 = DFlash n2 (la dosis vieja n7 queda como techo de exploración) → EAGLE3 solo fallback.

## 13. Anexo ronda 6: EXISTE un sidecar DSpark (con un fix que DFlash no tiene) (§13)

- **Descubrimiento**: `williamliao/Qwen3.6-35B-A3B-DSPARK-GGUF` — sidecar DSpark para nuestro modelo exacto, con cuants de **286 MB (IQ4_XS) a 556 MB (Q8_0)** — más chicos que el DFlash.
- **Por qué importa**: está re-entrenado desde el backbone DFlash e **"incluye un fix para hybrid-GDN state commit NO presente en el DFlash original"** — y nuestro target es justo un híbrido GDN → **S2 pasa a DSpark (Q4_K_M, 307 MB) y DFlash queda como comparación**.
- Ficha: vocab idéntico al target (cero problemas de vocab), aceptación por posición **PLANA** (~0.76-0.82, sin el colapso de DFlash n2→n4), regla de aceptación lossless (calidad idéntica al target).
- Datos del autor: DFlash sigue siendo el rey de código; DSpark es el generalista.
- **La lección del draft auto-convertido**: el mismo autor midió DFlash = −44.6% con un draft auto-convertido y n-max 8; en v4 con el sidecar oficial y n2 = +26.3% → reglas: **solo GGUF sidecar oficiales** y **n-max ∈ {2,3}**.
- **MTP paga más cuanto más pobre es la banda**: L4 (300 GB/s) +45-57% vs 3090 (936 GB/s) +22.7% → para nuestro rig el caso optimista sube (≥+25% plausible).
- Mecanismo de fondo unificado: los drafts densos pierden SIEMPRE porque el verify carga la unión de expertos; los drafts de hidden-states (MTP/DSpark/DFlash) eluden el problema. Explica todos los datos.
- Dosis fase S FINAL v6: S1 = MTP n2 → **S2 = DSpark Q4_K_M n2/n3** (+A/B conf-min) → S2b = DFlash n2 → S3 = EAGLE3 solo fallback.

## 14. Anexo ronda 7: DSpark OFICIAL de RedHatAI y el gate RUTA 0 (§14)

- **DSpark oficial**: `RedHatAI/Qwen3.6-35B-A3B-speculator.dspark` existe (0.95B parámetros, vocab correcto, métricas públicas) → los GGUF de williamliao son cuants comunitarios de una familia con upstream oficial.
- Mecánica DSpark documentada en master: DFlash + **cabeza Markov** (cada posición del bloque se sesga con el token previo) + flag nueva `--spec-draft-conf-min P` (corta el bloque cuando la confianza cae bajo P; A/B 0.5-0.7).
- LiliCorr fusionada a master (15-Oct): mejora de DFlash (selección por similitud coseno) — mismo `--spec-type draft-dflash` con otro draft GGUF; cuando exista conversión publicada, A/B contra DFlash crudo.
- MTP adaptativo (PR #27210): **NO fusionado** — vigilancia.
- EAGLE3: `AngelSlim/Qwen3-a3B_eagle3` está en la lista oficial de drafts soportados → S3 deja de ser hipotética.
- **AUDITORÍA DURA [medido en el dump]**: b11856 NO tiene NINGÚN draft aprendido (ni mtp, ni dflash, ni dspark, ni eagle3) → **TODA la fase S/E exige RUTA 0 (build nuevo b11901)**. La dosis v6 es post-RUTA-0.
- Bench externo: "hasta 4×" bien configurado; **mal configurado puede ser MÁS LENTO silenciosamente** → coherente con la regla n-max y la mediana de 3.

## 15. Anexo ronda 8: sidecar al byte y blanco de RUTA 0 (§15)

- **Descarga del sidecar S2 con autenticador completo**: DSpark Q4_K_M = **307,213,088 B, SHA256 `a3542c05…8cab`** (todos los cuants con su hash en el archivo completo).
- RUTA 0 con blanco concreto: **b11901** (binario precompilado + cudart zip) desbloquea toda la fase S/E — no hace falta compilar.
- El dato "4 GB/Turing con spec" sigue [sin datos] → será dato propio del barrido post-RUTA-0.

## 16. Anexo ronda 9: MTP en producción ajena (§16)

- Escalera completa `-ncmoe` CON MTP activo (L4): auto-fit 63.3 → dosis explícita 80.9 t/s (+28%) → **con MTP n2: 90.6-98.8 t/s (~+45%)**. Lecturas: MTP convive con offload sin conflicto; dosis explícita > auto-fit SIEMPRE; la ganancia MTP se mide sobre el mejor baseline.
- Acceptance **80%+ estable** en producción 12 GB a ctx 128K → nuestro rango esperado se queda corto por abajo.
- Con nextn en los pesos, offload parcial sigue ganando a full (3090) → nuestro plan va en la dirección correcta.
- El fork ik queda cerrado también para drafts → RUTA 0 a mainline se mantiene.

## 17. Anexo ronda 10: auditoría de respaldo riguroso (§17)

- Re-verificación punto a punto: **0 puntos refutados**; la mecánica DSpark y las tablas del estudio v4 quedaron triple-fuente.
- **Matiz de linaje** (discusión #26230): el sidecar DSpark del 35B es el draft DFlash de z-lab **con cabezas Markov/confidence "bolted-on"** (warm-start), no entrenado desde cero — exactamente como describía §13; el spot-check ES sigue siendo el árbitro.
- Soporte de DSpark en llama.cpp vía PR #26275 → refuerza que S2 exige build nuevo (RUTA 0 es el gate).
- Dosis v6 SIN cambios; regla de oro intacta: solo sidecar oficiales, n-max ∈ {2,3}, mediana de 3, spot-check ES.

---

## Cheatsheet operativa del nivel 5

- **Dosis fase S v6** (tras RUTA 0): S1 = MTP n2 → **S2 = DSpark Q4_K_M (307 MB, SHA256 `a3542c05…`) n2/n3** (+A/B `--spec-draft-conf-min` 0.5-0.7) → S2b = DFlash Q8_0 (421 MB) n2 → S3 = EAGLE3 solo fallback.
- **Reglas de oro**: draft SIEMPRE en GPU; solo GGUF sidecar oficiales (nunca auto-convertir); n-max ∈ {2,3}; autenticador de spec vivo (log + aceptación > 0, ojo al artefacto de conteo); spot-check ES obligatorio; mediana de 3.
- **Gate**: b11856 no tiene NINGÚN draft aprendido → RUTA 0 (b11901, 2 zips) antes de tocar la fase S/E.
- 📄 Detalle completo, fuentes y auditoría: [`nivel-5-draft-externo-gpu.md`](nivel-5-draft-externo-gpu.md)
