# PLAN DE LOS SIGUIENTES 10 PASOS — la ruta táctica de la campaña (ronda 33, 2026-10-28)

**Qué es este doc:** la capa táctica que vive ENTRE dos planos ya aprobados — el **ORDEN DE EJECUCIÓN APROBADO** (ronda 12: N1 → N3 → N2 → N4 → RUTA 0 + N5) y el **PLAN DE PRUEBAS POR NIVEL** (ronda 19: el método de los cocineros aplicado a toda la campaña). Aquellos dicen EL QUÉ y EL MÉTODO; este doc dice EL ORDEN FINO, EL COSTO y EL CRITERIO DE SALIDA de cada paso, con el estado real de hoy: **N3 cosechada (R32: 13/13 válidas, NP2 campeón +22.8% pendiente de confirmación, CMS1024 candidata Nº 2), N1 informal cerrado pero formal pendiente, N2 con SHA256 ya certificado.**

**Dónde estamos (foto R32):** receta diaria = FLAGS_BASE + GANADORAS (modo dual k=8 trabajo / k=4 charla), SIN `-np 2` todavía. Ancla del día lento 17.44 t/s (suelo histórico 17.36-17.80 [M]); techo de días buenos 21.5 — y NP2 lo rozó (21.49/21.41/21.32) en un solo día. RAM sana al 24-25% con apps cerradas (regla R28). Build 11856 pinned. C: al 6% libre (13/223 GB, pagefile en C:) — vigilancia activa.

**Reglas transversales que gobiernan TODOS los pasos** (no se repiten paso a paso, valen siempre): mediana de 3 corridas antes de proclamar (thc1006 v4: 9.4 pp entre corridas — una corrida no prueba nada); ancla + bookend por sesión (la GPU fría miente ~−15%); no perseguir deltas <5 pp; sanity con tool-calling SIEMPRE en cambio de cuant o draft; no apilar dosis sin medir la pila (NP2+CMS1024 juntas NO se midieron); cliff−1 en VRAM; medir antes de promover (lección R32: CRAM512 prometía −7.7 GB [M] y ganó +600 MiB — el traje se prueba antes de comprarlo); ninguna flag fuera del dump (`InformacionCritica/llama-flags.txt`); append-only en la investigación.

---

## PASO 1 — Mediana de 3 de NP2: confirmar al campeón (hoy, ~15 min del rig)

**QUÉ:** 2 corridas nuevas en carpetas NUEVAS (el resume salta las 13 ya-válidas; y `--quick` mide ids 1/5/9/10/13 y NO incluye NP2 = id 7 — verificado contra el script en R32):

```
py barrido-n3-eficiencia.py --logs D:\ZLia\faseN3-np2-b2 --solo ancla,slots,anclafin
py barrido-n3-eficiencia.py --logs D:\ZLia\faseN3-np2-b3 --solo ancla,slots,anclafin
```

(~6-8 min c/u: ANCLA + NP2 + bookend; cada corrida con su propia ancla de sesión, como exige el protocolo). Apps cerradas (regla R28) y en un bloque horario DISTINTO al del 28-10:27 — la variedad de días es información gratis.

**POR QUÉ AQUÍ:** es el único dato que bloquea la promoción y el más barato de conseguir. Regla de la casa: NP2 hizo UN partido estelar (+22.8% en día lento, tocando el techo 21.5) — antes de ficharlo para la receta diaria hay que verlo repetir en 3 partidos (b1 del 28 + b2 + b3).

**CRITERIO DE SALIDA:** mediana de NP2 contra su ancla por corrida → **GO promoción** si sostiene ≥ +15%; **NO-GO** si cae bajo 5 pp (no perseguir); zona 5-15% = decisión del Director con costo/beneficio en la mano. El t/s absoluto manda sobre el %: si las anclas de b2/b3 salen en día bueno (>19), el % baja pero NP2 ya demostró que roza el techo absoluto.

**RAMAS:** ancla de nuevo en el suelo 17.36-17.80 = comparación limpia con b1; ancla alta = igualmente válida (el bookend certifica la sesión). Si alguna corrida muere → el FATAL-inmediato de la v1.3 deja forense en el CSV y se repite esa corrida.

## PASO 2 — Cosecha de la mediana + la decisión CMS1024 (yo ~10 min + decisión del Director)

**QUÉ:** yo leo b2/b3, calculo la mediana de las 3 corridas, verifico anclas/bookends y registro todo (SS24 en N3 + espejo + README + Registro + commit/push = ronda 34). En la misma ronda, el Director decide con datos: **¿CMS1024 (+5.2%, RAM plana) merece su propia mediana** (2 corridas más, ~15 min)?

**POR QUÉ AQUÍ:** el N3 debe cerrarse con decisiones limpias ANTES de tocar config.txt — no se promociona y se sigue midiendo a la vez.

**RECOMENDACIÓN HONESTA:** si NP2 aguanta, CMS1024 es prescindible HOY (el objetivo t/s ya lo sirve NP2 con +22.8% vs +5.2%; y +5.2% roza el umbral de 5 pp). Su valor real es doble: (a) plan B si NP2 NO aguanta, (b) pieza para un futuro combo — pero **NP2+CMS1024 juntas NUNCA se apilan sin su propia mediana** (regla transversal).

**CRITERIO DE SALIDA:** CMS1024 promocionada / archivada como plan B / a mediana — cualquiera es un cierre válido; lo que no es válido es dejarla flotando sin decisión.

## PASO 3 — Promoción: `-np 2` entra en FLAGS_BASE (Director, 5 min, reversible)

**QUÉ:** UNA palabra añadida a FLAGS_BASE en config.txt. El repo lleva el historial → reversible en 5 segundos si algo falla.

**POR QUÉ AQUÍ:** es la ganancia certificada más grande disponible en toda la campaña (+22.8% en día lento; VRAM incluso bajó −142 MiB; prefill +48%; probe concurrente 20.8 tok/s agg +16.6% = SS4 certificada) y cuesta una palabra.

**LOS TRES MATICES que se aceptan conscientemente al escribir la línea:**
1. **Contexto por sesión baja a 8192** (con `-c 16384` y `-np 2` son 2 sesiones de 8192). Para el uso híbrido actual (~25 tok/turno, chat + tools) sobra [T]. Si algún día se pegan documentos enormes: o `-c 24576` (costo RAM/VRAM a medir, su propia mediana) o se acepta el recorte.
2. **WorkingSet SUBE ~+965 MiB** con NP2 (R32: el mecanismo NO es libera-RAM). Con apps cerradas (RAM 24-25%) cabe de sobra; la regla R28 sigue siendo obligatoria.
3. **SS11.4: MTP exige `-np 1`** — si en el paso 10 el spec gana el duelo, la receta cambia de manos. Anotado, no es problema hoy.

**CRITERIO DE SALIDA:** línea editada, server arranca, la auditoría de flags del diagnóstico sigue VERDE, primer chat manual se siente normal.

## PASO 4 — Sanity de 20 prompts: el juez humano → CIERRE DEL N3 (Director, ~20-30 min)

**QUÉ:** 20 prompts variados contra el server ya con `-np 2`: tool-calling (obligatorio), español, código, conversación larga multi-turno, alguna pregunta trampa. Yo preparo la lista exacta si el Director la quiere.

**POR QUÉ AQUÍ:** velocidad certificada ≠ calidad certificada. `-np 2` reparte el contexto en 2 sesiones y ningún número del barrido mide "se siente igual". El Director es el catador que prueba los platos antes de que el restaurante cambie el menú para siempre.

**CRITERIO DE SALIDA (cierra el N3 en AMBOS desenlaces):** 20/20 sin roturas → **N3 CERRADO con promoción aceptada** (SS de cierre + README). Cualquier fallo de calidad → revertir la línea (5 s), reportar qué falló, y el N3 se cierra "sin promoción" con la lección registrada. Lo único prohibido es dejar el nivel abierto sin veredicto.

## PASO 5 — Cierre formal del N1: la escalera de expertos con protocolo completo (~50-65 min)

**QUÉ:** BARRIDO-N1.bat v1.2.1 completo (k=8→6→5→4→3→2 + MEC 512/768/1024 + stacks combo, 18 configs) + su sanity.

**POR QUÉ AQUÍ (y por qué corre CON la receta ya promovida):** (a) el N1 informal ya midió k=4 +41% — el formal lo certifica con ancla+bookend+mediana y cierra el nivel base con evidencia completa; (b) al correr DESPUÉS de la promoción, sus números viven en el mundo final (`-np 2` incluido en la receta) y de paso re-certifican NP2 en otro bloque horario — dos pájaros, un tiro; (c) resuelve la **ramificación plan B de la ronda 12**: si el override con la clave correcta no aplica (log sin `n_expert_used`), RUTA 0 se adelanta inmediatamente (son solo 2 zips).

**CRITERIO DE SALIDA:** modo dual TRABAJO k=8 / CHARLA k=4 ratificado con mediana (o nueva dosis k ganadora, con su sorpresa correspondiente). Las dosis k son arquitectura (256 expertos guardados / 8 usados), no bytes → **SÍ transfieren al cuant nuevo** (se re-aplican en el paso 7 sin re-medir desde cero).

## PASO 6 — Pre-vuelo y descarga del N2: UD-IQ3_XXS, el cambio de baseline (descarga en horario libre + ~10 min de verificación)

**QUÉ:** (a) **PRE-VUELO DE DISCO, obligatorio**: C: va al 6% (13/223 GB) y el pagefile vive en C: — el caché temporal de HuggingFace va por defecto a C: aunque el destino sea D: → o se limpia C: (recomendado ≥25 GB libres) o se redirige `HF_HOME` a D:. El modelo destino ya está escrito: `D:\ZLia\models` (N2 §3). (b) Descarga: `hf download unsloth/Qwen3.6-35B-A3B-GGUF Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf --local-dir D:\ZLia\models` (13.2 GB). (c) Verificación doble: SHA256 `36f9ec0e…7150` + parser GGUF (arch, 256/8, **`nextn.*`** — si el módulo MTP viene dentro del GGUF, el draft de la fase E no cuesta descarga extra; si no, plan B draft separado ya documentado).

**POR QUÉ AQUÍ:** es la palanca estructural más grande que queda: modelo 14.27 → 13.2 GB = **~1.05 GB de RAM liberados**; bytes/token −7.5% → ~+8% t/s [T]; y probablemente MEJORA la calidad por byte (unsloth domina la frontera Pareto del 3.6, 14/26 posiciones; mudler/APEX —el uploader actual— nunca aparece en ella [F]). Todo lo medible en el cuant viejo ya quedó cosechado (N3 completa) — seguir midiendo en el viejo sería tirar el tiempo.

**CRITERIO DE SALIDA:** SHA256 clava, parser ve `nextn.*` (o plan B activado), re-ancla con el cuant nuevo medible. El cuant viejo NO se borra (fallback y referencia).

## PASO 7 — N2 dosis: re-aplicar lo que transfiere + sanity del cuant (2-3 sesiones de rig)

**QUÉ:** re-ancla con el cuant nuevo → re-aplicar las dosis certificadas que transfieren entre cuants: escalera k de N1 (arquitectura), cache de prompts, `-ctxcp 4` (ahora con margen real de RAM), UB1K **solo donde no estorbe** (lección R32: UB1K×NCM = −16.5% — en NCM va SIN UB1K), re-check rápido de NCM37C4 (lleva dosis de capas → única excepción que no transfiere limpia). **Sanity 20 prompts CON tool-calling — obligatorio en cambio de cuant** (y tool-calling es la categoría que peor cuantiza [F]: doble motivo).

**POR QUÉ AQUÍ:** el orden ronda 12 lo fija: N2 va después de N1/N3 porque "todo lo medible en el cuant viejo que SÍ transfiere ya quedó cosechado en los pasos 1-5".

**CRITERIO DE SALIDA (N2 §5):** ≥ +8% t/s con calidad intacta y ~+1 GB RAM libre. Si no llega → se registra, se decide con datos; el cuant viejo sigue siendo el fallback y nada se borra.

## PASO 8 — N4: la escalera de VRAM sobre el cuant NUEVO (2-3 sesiones cortas)

**QUÉ:** re-sweep completo de la frontera VRAM con el cuant final: ngl/límites en escalera ascendente + MEC dosis fina en MiB + página (`-lm`) + cliff con regla cliff−1.

**POR QUÉ AQUÍ y no antes:** las dosis VRAM **NO transfieren entre cuants** (el peso por capa cambia — N4 §17 dice que el offload "solo se re-optimiza si cambia cuant, ctx o entra MEC/draft"). Medirla en el cuant viejo habría sido medir dos veces; medirla aquí es medir una sola vez en el mundo que se queda.

**CERTIFICADOS:** nvidia-smi ≤ 3.7 GB, delta de buffer en log, pageouts ≈ 0.

**CRITERIO DE SALIDA:** frontera VRAM estable sin cliff; modo dual ratificado en el cuant nuevo. La VRAM queda cerrada → el hueco real para el draft del paso 10 será un dato, no una suposición.

## PASO 9 — RUTA 0: build b11901 y el despertar de las features muertas (1 sesión de taller + re-ancla)

**QUÉ:** 2 zips de b11901 (binario CUDA 12.4 + cudart DLLs — sin compilar, N3 §16; sin el cudart la GPU queda dormida) → re-auditoría completa de defaults del build nuevo → re-ancla → re-certificar overrides (¡la clave `qwen35moe.expert_used_count` puede cambiar de nombre en el build nuevo!) → probar si cache-reuse revive.

**POR QUÉ AQUÍ:** acumula TRES motivos certificados: (1) defaults b11856 ≠ master (re-anclados, vigilar); (2) los alias `--no-mmap`/`--mlock` mueren en duro tras RUTA 0 (PR #28334) — la traducción `-lm` pasa a obligatoria; (3) **NUEVO y generalizado (R32): cache-reuse NO-SOPORTADO #24055 en AMBAS colocaciones** = es el build, no la receta. Si reuse revive en b11901, la familia ORO-SHIFT/reuse256 (21.39 [M]) vuelve a la mesa sin comprar nada.

**RIESGO conocido y aceptado:** build nuevo = mundo nuevo (todo se re-ancla; el informe del N3 queda como referencia histórica del 11856). Por eso va DESPUÉS de N4 — no ensucia mediciones a mitad de campaña.

**CRITERIO DE SALIDA:** reuse vivo en log ("restored context checkpoint") + overrides aplicados + defaults re-anclados. Si reuse sigue muerto → el motivo se cierra con certificado y se sigue: **el plan NO depende de reuse**.

## PASO 10 — N5: el duelo spec vs NP2 + receta final de campaña (la apuesta grande, al final)

**QUÉ:** fase E (MTP-n2 — el draft puede venir dentro del GGUF nuevo del paso 6) → fase S (S0 ancla sin spec → S1 MTP n2 → S2 DSpark Q4_K_M n2/n3 con A/B conf-min 0.5-0.7 → S2b DFlash-n2 → S3 EAGLE3 fallback → S5 sintético de overhead). Fijar SIEMPRE `--spec-draft-n-max` + `--spec-draft-p-min` explícitos (defaults b11856: 16 y 0.75 ≠ master 3 y 0.00).

**EL DUELO central:** MTP exige `-np 1` (SS11.4) y NP2 aporta +22.8% sin pedir nada. Se mide cara a cara: receta con NP2 sin spec vs receta con spec sin NP2 (y si el margen lo justifica, combinaciones intermedias — cada una con su propia mediana). Gana el mejor **t/s × calidad**. Ojo #25345 kv-unified: puede silenciar el draft → `--kv-unified off` si no engancha.

**CRITERIO DE SALIDA:** ≥ +25% [M] con spot-check ES limpio por config; presupuesto del draft medido con la VRAM ya cerrada por el paso 8 (un dato, no una suposición); referencia ajena: DFlash-n2 +26.3% > MTP-n2 +22.7%.

**CIERRE DE CAMPAÑA (mismo paso):** receta final certificada = FLAGS_BASE + todas las dosis ganadoras por nivel, escrita con backup; informe de campaña que cierra los 5 niveles; la RAM queda administrada (regla R28 + ~1 GB del cuant nuevo) — **el menú RAM agresivo ya no hace falta**: el problema del 97% se resolvió por higiene (R28), no por cirugía, y el barrido desmintió los certificados de CRAM512/CTXCP4 en el intento.

---

## Tabla resumen — los 10 pasos de un vistazo

| # | Paso | Quién | Costo | Criterio de salida | Desbloquea |
|---|------|-------|-------|--------------------|------------|
| 1 | Mediana de 3 de NP2 (b2/b3) | Director | ~15 min | mediana ≥ +15% = GO; <5pp = NO-GO | promoción |
| 2 | Cosecha mediana + decisión CMS1024 | LAIA + Director | ~10 min | decisión registrada (GO/plan B/archivada) | paso 3 |
| 3 | Promoción `-np 2` en config.txt | Director | 5 min | server arriba + auditoría VERDE | paso 4 |
| 4 | Sanity 20 prompts (el juez) | Director | ~20-30 min | 20/20 → N3 CERRADO (o revert + lección) | N3 cerrado |
| 5 | N1 formal (BARRIDO-N1.bat v1.2.1) | Director | ~50-65 min | modo dual ratificado con mediana | base certificada + plan B resuelto |
| 6 | Pre-vuelo disco + descarga UD-IQ3_XXS + parser | Director | descarga + ~10 min | SHA256 clava + `nextn.*` visto | N2 real |
| 7 | N2 dosis re-aplicadas + sanity cuant | Director + LAIA | 2-3 sesiones | ≥ +8% t/s + ~+1 GB RAM + calidad | baseline nuevo |
| 8 | N4 escalera VRAM (cuant nuevo) | Director + LAIA | 2-3 sesiones | frontera sin cliff + pageouts ≈ 0 | VRAM cerrada |
| 9 | RUTA 0 (b11901, 2 zips) + re-auditoría | LAIA + Director | 1 sesión + re-ancla | reuse vivo o motivo cerrado | features muertas despiertas |
| 10 | N5 duelo spec vs NP2 + receta final | Director + LAIA | fase E + S | ≥ +25% [M] o NP2 se queda | campaña cerrada |

## Riesgos y vigilancia transversal (viven durante TODA la ruta)

- **C: al 6% libre** (13/223 GB; pagefile en C:) — el pre-vuelo del paso 6 es OBLIGATORIO: o limpieza (≥25 GB libres) o `HF_HOME` a D:. Un disco C: lleno estrangula el swap (el "sótano") justo cuando el modelo nuevo llega.
- **WorkingSet de NP2 +965 MiB** — la regla R28 (apps cerradas antes de medir/trabajar pesado) sigue siendo ley.
- **Anomalía NOCACHE abierta (no bloqueante)** — leer `logs-config/12-NOCACHE.log` en el rig (2 min; se mete en cualquier sesión de rig, por ejemplo en el paso 5). El repro TTFT necesita re-calibración; el certificado fuerte de cache sigue siendo líneas de log + decode.
- **Días lentos/rápidos (17.4 vs 21.5)** — por eso ancla por sesión SIEMPRE; el techo ya se tocó una vez (R32) pero solo la mediana lo convierte en hecho.
- **No apilar sin medir** — NP2+CMS1024, y en general cualquier combo nuevo = su propia mediana antes de tocar la receta.
- **El cuant viejo y las carpetas de evidencia NUNCA se borran** — fallback y referencia histórica (append-only).

---

# REVISIÓN R34 — ORDEN MEJORADO DE LOS 10 PASOS (2026-10-28, pedido del Director: "mejora el orden")

**Naturaleza del cambio:** NO es barajar por gusto — es mover 3 piezas fuera de la ruta crítica, adelantar 2 higiene/verificación que hoy pagan intereses después, y estacionar 1 decisión que no bloquea nada. El método, los criterios de salida y la tesis RAM quedan intactos.

## Las 6 mejoras reales (ANTES → AHORA → POR QUÉ)

1. **La higiene de disco se ADELANTA a la mediana.** ANTES: limpiar C: era preparación del N2 (paso 6, días después). AHORA: primer movimiento de todos. POR QUÉ: el pagefile vive en C: y un C: al 6% puede contaminar con swap TODAS las mediciones que vienen (mediana, N1 formal) — es higiene de medición, no solo logística de descarga; además es el único prerequisito de la descarga.
2. **La descarga de 13.2 GB SALE DE LA RUTA CRÍTICA.** ANTES: bloqueaba el paso 7 y venía después del N1 formal. AHORA: se lanza apenas cierra el N3 y corre en TIEMPO DE RELOJ (noche / entre sesiones — nunca en paralelo con una corrida de medición, higiene R28). POR QUÉ: es el único ítem de horas de toda la ruta; serializado cuesta una tarde, en paralelo de reloj cuesta 0 minutos de rig. Cuando llegue el turno del N2, el modelo ya estará ahí.
3. **Verificación + humo del cuant ADELANTADA (fail-fast).** ANTES: SHA256 + parser venían amarrados al trabajo de dosis del N2. AHORA: en cuanto termina la descarga, 10-15 min de verificación (SHA256 `36f9ec0e…` + parser `nextn.*` + primer arranque). POR QUÉ: si el archivo vino roto o el parser no ve el MTP, se sabe HOY con tiempo de re-descargar — no una semana después con la campaña ya montada encima.
4. **Ruta crítica simplificada: mediana → promoción → sanity SIN escalas.** ANTES: el paso 2 (cosecha + decisión CMS1024) estaba EN la ruta crítica. AHORA: la cosecha es trabajo mío entre pasos (minutos, cero rig) y la decisión CMS1024 queda ESTACIONADA como plan B — solo se activa si NP2 NO-GO (o después de campaña, si sobran ganas). POR QUÉ: si NP2 aguanta (+22.8%), CMS1024 (+5.2%, roza el umbral) no bloquea nada y no merece un escalón propio.
5. **El log NOCACHE (2 min) se lee en la misma visita al rig de la mediana.** ANTES: pendiente flotante "para cualquier sesión". AHORA: tarea anclada al paso 1. POR QUÉ: cierra temprano el hilo abierto de la anomalía TTFT (recalibración del repro) con costo cero.
6. **El N1 formal mantiene su lugar lógico (tras la promoción) pero ahora LLENA LA VENTANA de espera de la descarga.** ANTES: N1 formal → luego pre-vuelo → luego descarga (todo serial). AHORA: N1 formal corre mientras el modelo baja en segundo plano de reloj. POR QUÉ: mismo certificado (receta final con -np 2 incluida), mejor calendario. El override ya demostró aplicar informalmente (escalera 17.80→35.12 t/s) → riesgo plan B bajo, no justifica adelantarlo.

## Lo que NO cambia (y por qué — la parte seria de "mejorar el orden" es saber qué no tocar)

- **N4 después de N2**: las dosis VRAM no transfieren entre cuants (N4 §17) — medirla antes es medir dos veces.
- **RUTA 0 antes de N5**: el presupuesto del draft se mide con la VRAM ya cerrada (un dato, no una suposición).
- **N1 formal tras la promoción**: su ancla es la receta final; adelantarlo mediría un mundo que ya cambió.
- **Sanity con tool-calling en cada cambio de cuant; mediana de 3; ancla por sesión; no apilar sin medir.**
- **La tesis RAM**: higiene (R28) + ~1.05 GB del cuant nuevo — sin cirugía.

## El orden mejorado (esta tabla REEMPLAZA a la de R33)

| # | Paso | Quién | Costo de rig | Cambio vs R33 | Criterio de salida |
|---|------|-------|--------------|---------------|--------------------|
| 1 | Higiene C: (≥25 GB libres) + mediana de 3 de NP2 (b2/b3) + leer 12-NOCACHE.log | Director | ~35-45 min | **ADELANTADO** (higiene era paso 6; NOCACHE flotaba) | mediana ≥+15% = GO; <5pp = NO-GO |
| 2 | Promoción `-np 2` en FLAGS_BASE | Director | 5 min | **DIRECTO** (ya sin escala CMS1024) | server arriba + auditoría VERDE |
| 3 | Sanity 20 prompts (el juez) → CIERRE del N3 | Director | ~20-30 min | igual | 20/20 o revert+lección |
| 4 | **Lanzar descarga UD-IQ3_XXS** (13.2 GB, entre sesiones/de noche) | Director (0 min activos) | horas de reloj | **SALE DE LA RUTA CRÍTICA** (era paso 6) | descarga completa |
| 5 | Verificación + humo del cuant nuevo (SHA256 + parser nextn.* + primer arranque) | Director | ~10-15 min | **NUEVO paso** (fail-fast; antes viajaba dentro del N2) | SHA clava + parser ve MTP (o plan B draft) |
| 6 | N1 formal (BARRIDO-N1.bat v1.2.1) | Director | ~50-65 min | mantiene lógica, llena la ventana de la descarga | modo dual ratificado con mediana |
| 7 | N2 dosis re-aplicadas + sanity del cuant | Director + LAIA | 2-3 sesiones | igual (ya sin carga de descarga/verificación) | ≥+8% t/s + ~+1 GB RAM |
| 8 | N4 escalera VRAM sobre cuant nuevo | Director + LAIA | 2-3 sesiones | igual | sin cliff + pageouts ≈0 |
| 9 | RUTA 0 (b11901, 2 zips) + re-auditoría + test cache-reuse | LAIA + Director | 1 sesión + re-ancla | igual (los 2 zips también pueden bajar en paralelo de reloj) | reuse vivo o motivo cerrado |
| 10 | N5 duelo spec vs NP2 + receta final con backup | Director + LAIA | fase E + S | igual | ≥+25% [M] o NP2 se queda |

**La ruta crítica queda en ~60-90 min de rig para tener el N3 cerrado y la descarga ya corriendo**: higiene+mediana → promoción → sanity → lanzar descarga. Todo lo demás hereda el tiempo libre.

**Regla nueva de calendario que introduce esta revisión:** las descargas (N2 hoy; zips de RUTA 0 cuando toque) corren cuando el rig NO mide; si una sesión de medición cae en medio de una descarga, la descarga se pausa — ninguna medición compite con el disco.

---

# SOLIDIFICACIÓN R35 — EL PLAN VIVE AHORA EN `campana-10-pasos.py v1.0` (2026-10-28)

Pedido del Director: "tengo mas espacio en D:, ahora planea esos 10 pasos solidificarlos bien en un .py que haga todo". El plan deja de ser solo papel: **`InformacionCritica/scripts/campana-10-pasos.py` v1.0** es el PILOTO de la campaña — no reemplaza a los instrumentos de cada nivel (regla de la casa: se generan "conforme se llegue, sin adelantar trabajo"), los maneja en orden con puertas, pre-vuelos, certificados y memoria.

**Comandos:** `estado` (foto de la campaña) · `p1` (higiene C:/D:/RAM + log 12-NOCACHE + mediana de 3 de NP2 via barrido v1.3 b2/b3 + veredicto GO ≥+15% / NO-GO <5pp / DUDOSO) · `p2` (promoción `-np 2` en config.txt: confirmación ESCRITA, backup con marca de tiempo, `--revert` byte-a-byte) · `p3` (sanity de 20 prompts al server vivo —ES, código, tool-calling, trampa— + `--veredicto OK|FALLA` que CIERRA el N3) · `p4` (descarga UD-IQ3_XXS 14,069,266,720 B con HF_HOME en D:, resumable, `--dry-run`) · `p5` (fail-fast: bytes exactos + SHA256 certificado `36f9ec0e…7150` + parser GGUF nextn.* + humo con la receta promovida, 1 prompt) · `p6` (lanza BARRIDO-N1.bat) · `p7-p10` (guiados: checklist del nivel + registro de la decisión).

**Reglas que el script hace cumplir:** PUERTAS (p2 exige p1=GO; p3 exige p2; p4 exige N3 cerrado; p5 exige archivo) con `--fuerza` que salta A PROPÓSITO y lo deja escrito; config.txt SOLO se toca en p2; informe `campana-INFORME.md` APPEND-ONLY; estado en `campana-estado.json`; FATAL nominado con forense; importa al barrido N3 real (mismo directorio) para reutilizar parser GGUF, SHA256 streaming, RAM y health.

**Batería:** `tests/test_campana_mock.py` — 38 checks TODO VERDE (U01-U22 piezas puras: autenticadores del hito PINADOS contra RUTAS.md L738, mediana con ancla por corrida, GGUF fabricado a bytes con/sin nextn, informe append-only; E01-E24 E2E: puertas, cirugía con backup+revert, cierre del N3, dry-run que no frena, humo con server falso en sus DOS mundos —levanta y responde / muere en carga con forense— y guardarrail de server ajeno). **Bugs que la batería cazó en el taller:** (1) la rama idempotente de p2 borraba la referencia al backup → revert ciego (arreglado + fallback al backup más reciente); (2) dry-run de p4 moría por disco chico del taller → ahora avisa sin frenar (en real sigue siendo FATAL); (3) verificar_gguf devolvía bool y paso5 hacía len() → devuelve la lista de claves. Regresión de la casa 5/5 VERDE (abrir 11/11, chatear E2E, barrido, diagnostico, barrido-n3).

**El Director solo necesita:** copiar `campana-10-pasos.py` a D:\ZLia (junto a barrido-n3-eficiencia.py) y correr `py campana-10-pasos.py estado`. La ruta crítica del R34 queda intacta: p1 → p2 → p3 → lanzar p4 de noche → p5 al amanecer.

---

## ANEXO R36 — REVISIÓN "NI UN SOLO BUG" DEL PILOTO (v1.0 → v1.1)

Pedido del Director (28-oct-2026): "yo hago doble click y hace todo automaticamente, dime que hace de forma simplificada, hazle una revision para que no tenga ni un solo bug". Auditoría línea a línea del piloto contra sus compañeros REALES (barrido-n3 v1.3, config.txt de la casa, abrir-qwen-apex.py, tests) — no una relectura: verificación de contratos. **13 hallazgos corregidos**, ninguno de gravedad crítica pero 3 habrían estorbado en el rig:

**Habrían estorbado en la campaña:**
1. **Puerta p3 bloqueada por un re-run inofensivo** — si el Director re-ejecutaba p2 (rama idempotente), el estado quedaba "YA-PROMOVIDA" y la puerta de p3 solo aceptaba "PROMOVIDA": bloqueo falso justo antes del juez. Fix: la puerta acepta PROMOVIDA/YA-PROMOVIDA.
2. **Humo con receta distinta a la diaria** — el humo de p5 no replicaba el lanzador de la casa: faltaba el override de expertos cuando EXPERTOS_TRABAJO != 8 (misma regla de abrir-qwen-apex.py), moría con KeyError crudo si faltaba RUTA_SERVER, y un `-m` colado dentro de las flags habría cargado OTRO modelo (el humo habría mentido). Fix: receta espejo del lanzador + limpieza de -m/--model + FATAL nominado.
3. **Forense del humo destruido** — campana-humo.log se abría en modo "w": el intento #2 borraba el forense del intento #1 (contra la regla de la casa: la evidencia nunca se pisa). Fix: acumulativo con cabecera por intento.

**El resto:**
4. p2 por substring: "-np 20" hacía pasar el chequeo "-np 2" y la promoción se apilaba si ya había un -np → ahora por tokens; -np distinto de 2 = no se toca nada y queda escrito en el informe.
5. Higiene p1: D: por debajo del mínimo salía VERDE (avisaba solo C:) → avisan ambos discos con su motivo.
6. DOBLE CLICK: la ventana se cerraba sola antes de poder leerse → arrancado SIN argumentos, el piloto espera un Enter al mostrar el estado (con argumentos no molesta). Nuevo launcher **CAMPANA.bat** (patrón de la casa: doble click = foto del estado; `CAMPANA.bat p1` = paso concreto).
7. Ctrl+C en la corrida del barrido (p1) o en el N1 formal (p6) mostraba traceback crudo → pausa limpia rc 130.
8. Paleta del estado: YA-PROMOVIDA / VERIFICADO-SIN-HUMO / NO-GO / REVERTIDA / INCOMPLETO pintados de rojo (alarma falsa) → verdes/amarillos correctos, rojo solo para FALLO-CERTIFICADO/FALLA.
9. Estado json viejo o roto (sin pasos/n3, o no-dict) reventaba después → lectura defensiva.
10. Un hf instalado como .bat/.cmd (shim de pip) no arrancaba en Windows → envuelto en cmd /c.
11. El veredicto OK/FALLA de p3 no actualizaba pasos["3"] (se quedaba "EN-ESPERA-DEL-JUEZ" para siempre) → actualizado; y re-corridas del mismo tag PISABAN el RESUMEN.md → el anterior se archiva con timestamp.
12. Cancelaciones (p2/p4/p6) sin rastro en el informe → la memoria append-only ahora también registra lo que el Director NO dejó hacer.
13. REPO_ALT (repo alternativo, mismo archivo y SHA) estaba muerto → documentado en la ayuda de --repo.

**Paperería cazada de paso:** la ronda 35 anunciaba "38 checks" y la batería ejecutaba en realidad 46 — conteo a la baja corregido (el contador ahora es dinámico).

**Batería:** test_campana_mock.py pasa de 46 a **65 checks ejecutados TODO VERDE** (N01-N14 nuevos: puerta tras YA-PROMOVIDA, -np 20 no engaña, cancelaciones escritas, higiene que avisa en ambos discos, json roto no revienta, helpers puros, paleta, veredicto que actualiza pasos["3"], pausa de doble click, Ctrl+C limpio, forense acumulativo con 4 intentos, RESUMEN archivado). Regresión de la casa 5/5 VERDE (abrir, chatear, barrido, diagnostico, barrido-n3). py_compile OK. test_faseD_n1 SIN TOCAR (el diff confirma: cero cambios fuera del campana, su test y el bat nuevo).

---

## Anexo R37 — Verificación de seguridad EN VIVO del objetivo N2 (2026-10-29)

Pedido del Director: "realiza una verificacion de seguridad del archivo". Cuatro candadas contra la API pública de HuggingFace + la cadena local del repo:

1. **El paquete es auténtico [F]:** la API pública publica HOY `Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf` en `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` con **14,069,266,720 bytes y SHA256 `36f9ec0e…7150` — idénticos a los pinados en el script desde r35** (comparados al carácter). El almacén es de la org oficial unsloth, no gated, sin banner de seguridad. Nadie cambió nada en el estante.
2. **REPO_ALT desautenticado [F — el único ROJO]:** `unsloth/Qwen3.6-35B-A3B-GGUF` sirve el MISMO nombre de archivo pero **SIN el módulo MTP**: 13,211,155,424 B (13.21 GB), SHA256 `9c964e65…88fbe`, y CERO variantes -MTP entre sus 23 GGUF. La nota de r35/r36 "mismo archivo, mismo SHA" era FALSA (el N2 lo tenía escrito: el sin-MTP pesa 858 MB menos = el módulo nextn). Haberlo usado habría costado una descarga nocturna de 13 GB que p5 rechaza por SHA. **Fix (campana v1.2):** p4 rechaza el repo ALT con FATAL nominado ANTES de descargar (--fuerza lo salta dejándolo escrito); el fallback real es re-ejecutar p4 contra el repo por defecto (hf retoma donde iba).
3. **Aclaración del "13 GB":** la cifra "13.2 GB" del PASO 6 es la foto vieja de la variante sin-MTP (ronda 33, antes de los inventarios al byte de las rondas 6-8). El objetivo del hito cerrado por SHA es el de **14.07 GB con nextn dentro**: RAM ≈ igual que hoy; la ganancia = calidad-por-byte (frontera Pareto: unsloth 14/26 posiciones, mudler/APEX ninguna [F]) + el draft de la fase E incluido sin segunda descarga.
4. **Cadena local intacta:** git status limpio; constantes del script == docs (comparación programática); batería 65 → **67 checks TODO VERDE** (E13b/E13c nuevos) + regresión de la casa 5/5 + py_compile OK; configs/barridos/bats SIN TOCAR.

---

## Anexo R40 — Llegó b3: el Director ejecutó P1 y la mediana de NP2 va 2/3 (2026-10-29)

**Qué llegó de campo** ("ten" + 4 archivos): la corrida completa de `D:\ZLia\faseN3-np2-b3` (consola, datos.json, INFORME.md, resultados.csv) del 2026-10-28 17:18-17:24, barrido-n3-eficiencia v1.3 con `--solo ancla,slots,anclafin` — la huella exacta de P1 (su 3ª corrida de la mediana). Preflight limpio: modelo APEX-I-MINI con bytes y SHA256 `e4eae0e2…` certificados, build 11856 OK, higiene OK (RAM 18% en uso al iniciar, comepanes chicos, plan Máximo rendimiento). Evidencia copiada al repo: `evidencia/faseN3-np2-b3-20261028/`.

**Números de b3 [M]** (4 pasadas × 256 tokens, temp 0, mediana de pasadas 2-4):

| config | decode t/s | vs ancla | dato clave |
|---|---|---|---|
| 1 N3-ANCLA (receta diaria) | 17.32 (dispers 1.6%) | — | TTFT repro 4.26→5.06 s PLANO; 5 líneas #21831 = repro multi-turno SIN cache-reuse (comportamiento de hoy, no modo ROTO) |
| 7 N3-NP2 (`-np 2 -cmoe`) | 21.37 (dispers 2.9%) | **+23.4%** | probe concurrente agg 20.73 vs 17.57 tok/s = **+18.0%** (la hipótesis SS4 prometía +14%); VRAM 2211/4096 |
| 13 N3-ANCLA-FIN | 17.60 | +1.6% | bookend ESTABLE (≤5%): la sesión no derivó; los deltas se leen limpios |

Sanity auto 3/3 en las tres configs (391 / Cervantes / Marte). El prefill también sube: 16.5 → 20.1 tok/s frío (+22%).

**El día estaba LENTO y aun así NP2 ganó [M]:** el ancla 17.32 aterrizó en el suelo histórico (17.36-17.80; −19.6% vs ORO-UB1K 21.53) con la firma de la ronda 28: RAM al 95-97% tras cargar (775/435/418 MiB libres) y pagefile con pico de 3389 MB. Regla anti-cruce de sesiones: el "21.37 de hoy ≈ 21.53 de ORO" es una coincidencia llamativa, NO una comparación válida (otro día). Lo único válido: los deltas DENTRO de cada sesión.

**Cruce con b1 (la otra corrida, ya en el repo — `evidencia/faseN3-20261028`, del 28-oct por la mañana):** ancla 17.44 → NP2 21.41 = **+22.8%** [M], bookend +1.7% ESTABLE, y el control NOCACHE midió +0.9% (ruido puro: el control se comporta como debe). Dos sesiones distintas (mañana y tarde) clavan el mismo delta ~+23% con dispersión interna ≤2.9%: **el efecto no es ruido de un día**.

**Estado de la mediana P1 (GO ≥+15% / NO-GO <+5% / DUDOSO entre medias):** 2 de 3 deltas: b1 +22.8% y b3 +23.4%. La mediana de tres con esos dos anclados **no puede bajar de +22.8% pase lo que pase en b2** → GO matemático pendiente de cosecha formal. Único modo de romperlo: que b2 no coseche (sin ancla o sin NP2 válidas → INCOMPLETO). Falta para sellar en el repo: el CSV de b2 (el rig ya lo tiene si P1 lo corrió antes de b3) o la línea "VEREDICTO P1" del campana-INFORME.md.

**Misterio registrado (observación, no hecho):** la hipótesis SS4 prometía la ganancia de slots SOLO con 2 sesiones a la vez; aquí el decode de UN stream también aceleró ~+23% (b1 y b3). Mecanismo no explicado: KV repartida 2×8192, VRAM −142 MiB sistemática en ambas sesiones (2238→2096 y 2353→2211), RAM de proceso +~0.9 GB (12101→13066 y 12260→13176). No proclamar mecanismo; lo que sí está certificado con su probe es la ganancia concurrente (+18% agregado).

**Coste conocido de NP2:** +~0.9 GB de RAM de proceso; en 16 GB ya saturados (95-97% con el modelo cargado) es el riesgo del día normal — exactamente por eso el protocolo exige la mediana completa antes de la cirugía p2.

**Siguiente paso del rig:** doble click en CAMPANA.bat → si P1 ya quedó cosechado, la foto muestra su veredicto y ofrece p2 (la ÚNICA cirugía: `-np 2` a FLAGS_BASE, con backup y `--revert`). Si P1 sigue PENDIENTE/INCOMPLETO: `py campana-10-pasos.py p1 --sin-corridas` cosecha lo ya medido; y si b2 no existe, una pasada de `py barrido-n3-eficiencia.py --logs D:\ZLia\faseN3-np2-b2 --solo ancla,slots,anclafin` y cosechar de nuevo. Después: p3 (el sanity de 20 prompts del Director) cierra el N3.

## Anexo R43 — DUELO PROFESIONAL DE CUANTS: cuant vigente (SC117 APEX-I-MINI heretic+MTP) vs unsloth UD-IQ3_XXS (2026-10-29, pedida por el Director: "analiza mas seriamente profesional ambos repos ... busca las diferencias y elige una")

**DESCUBRIMIENTO DE IDENTIDAD (verificado byte-a-byte via API de HF):** el modelo que el rig corre desde hace semanas NO es un APEX generico — es `SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf`, **14,273,277,376 bytes y SHA256 `e4eae0e2...118d4` exactos** a los documentados del rig (14.27 GB). Cadena de procedencia: Qwen/Qwen3.6-35B-A3B (oficial) -> llmfan46 heretic v1.3.0+MPOA (88% menos rechazos con **KL 0.0015**, es decir: el Director tenia razon, el heretic moderno pierde casi nada) -> SC117 lo re-cuantiza con **APEX-I** (apex-quant de mudler, codigo abierto: precision mixta por ROL de tensor — experto routado / experto compartido / atencion, gradiente por capa) dejando **las 20 capas MTP dentro del mismo GGUF**.

**Comparacion tecnica:**

| Dimension | Vigente: SC117 APEX-I-MINI | unsloth UD-IQ3_XXS |
|---|---|---|
| Peso | 13.29 GiB (14,273,277,376 B) | 13.10 GiB (14,069,266,720 B) |
| bpw aprox (33.1B params) | ~3.2 | ~3.2 |
| Esquema | APEX-I: MoE-aware por rol (mudler, open source; su card reclama PP mejor que Q8_0 a mitad de tamano) | UD dinamicos con imatrix calibrada (estandar de facto, 1.3M descargas) |
| Heretic/uncensored | SI (KL 0.0015, 88% menos rechazos) | NO (alineacion stock: vuelve el "soy un asistente...") |
| MTP dentro (nextn) | SI, 20 capas, flags `--spec-type draft-mtp --spec-draft-n-max 2` | SI, identico |
| -np 2 + MTP simultaneos | NO (MTP exige -np 1; card de unsloth) | NO (misma limitacion) |
| Evidencia N3 en el rig | TODA: b1 +22.8%, b3 +23.4%, bookends, firma R28 | NINGUNA |
| Verificacion anti-malware | SHA pinado aqui; corriendo en el rig hace semanas (validacion empirica) | SHA pinado desde r35; verificado vs API en r37 |
| Riesgo de procedencia | re-empaquetador unico (52k desc) pero archivo ya auditado en el rig | org verificada, changelogs publicos |

**DECISION (Puerta A, elegida por encargo del Director): NOS QUEDAMOS con el cuant vigente.** Razones: (a) heretic preservado — la propiedad que el Director valora explicitamente; (b) la UD NO compra turbo: el MTP es identico y en ambos el duelo spec-vs-NP2 de P10 decide; (c) cambiar de cuant tira TODA la evidencia N3 medida por un edge de cuantizacion no demostrado (~mismo bpw); (d) 0 GB de descarga, 0 superficie nueva de riesgo, RAM ya validada en dias lentos reales. Consecuencias: **P4-P5 quedan APARCADAS** (campana v1.6: `P4_APARCADA = True`, el AUTO salta 4/5 y lo deja escrito; el acceso manual `p4`/`p5` sigue vivo para un duelo explicito; la UD-IQ3_XXS queda PINADA como revivable). P6 (N1 formal) corre sobre la receta promovida con el vigente y HEREDA la puerta del juez (N3 cerrado antes de avanzar — hueco cazado por U17 en el taller). P7..P10 intactos: ahora el escalon MTP (P8) y el duelo (P10) se corren con el vigente, sin descargas. La personalidad de ZLia se cocina igual con system prompt (pendiente de pedido explicito).

---

## APENDICE R51 (2026-10-30): los instrumentos finos de los pasos 7-10 YA EXISTEN
Los pasos 7..10 de este plan ya NO son solo checklist guiadas: viven en `InformacionCritica/scripts/CAMPANA-6A10.py` (olla separada, mundo propio, puerta de entrada = la primera olla cerrada). Corresponde 1 a 1 con este plan: P7 = PASO 7 (re-ancla + dosis que transfieren + sanity tool-calling obligatorio), P8 = PASO 8 (escalera VRAM, certificados nvidia-smi/pageouts, cliff-1 automatico), P9 = PASO 9 (b11901, diff de defaults, override, sondeo cache-reuse, re-ancla), P10 = PASO 10 (duelo spec vs NP2 con mediana de medianas + spot ES + fallback kv-unified + receta final con backup y CIERRE DE CAMPAÑA). Las candidatas/peldanos se DERIVAN de la receta real de config.txt y quedan en archivos editables (campana-6a10-p7-candidatas.txt / campana-6a10-p8-escalera.txt): el Director activa o inactiva cada dosis. Bateria: 51/51 checks con taller falso (tests/test_campana6a10_mock.py).

## APENDICE R52 (2026-10-30): PASO 1 GO — la mediana de NP2 confirma al campeón
Corridas de campo b2/b3 (29-oct noche, 7z "Nueva carpeta") + b1 (cosecha R32) + bx (28-oct manana, ya en evidencia) = CUATRO sesiones independientes, ninguna contada doble. Trio canonico b1/b2/b3: mediana NP2 21.45 t/s, mediana de deltas +19.8% — GO (criterio >= +15%); la PEOR sesion (+18.8%) tambien pasa el corte; con las 4 sesiones la mediana es 21.43 t/s / +21.3% con dispersion ENTRE sesiones de 1.0% (contra los 9.4 pp de thc1006 v4). En dias lentos NP2 escribe al techo de dias buenos (mediana a -0.3% del 21.5 [M]). **PASO 1 CERRADO.** PASO 2 resuelto sin medir: CMS1024 APARCADA como plan B (criterio "prescindible si NP2 aguanta" — aguanta; NP2+CMS1024 siguen sin medirse juntas). La ruta critica queda reducida a lo que vive en el rig del Director: PASO 3 = UNA palabra (`-np 2` en FLAGS_BASE de config.txt, aprobacion del Director) -> PASO 4 = sanity 20 prompts -> CIERRE del N3; despues higiene C: (11/223 GB libres) antes de la descarga N2 de 13.2 GB (solo cuando el rig NO mide) y la ruta de r34 sigue intacta (N1 formal llena la ventana de descarga). Matiz RAM en vigilancia: el WorkingSet +965 MiB de R32 no se reprodujo en b2/b3 (NP2 quedo 500-600 MiB POR DEBAJO de su ancla). Anexo completo: N3 SS24 + espejo simple; aritmetica verificada con codigo.

## APENDICE R53 — PASO 3 ejecutado en el repo (2026-10-30)
El Director aprobo la promocion ("actualiza el abrir modelo del repo con las nuevas flags la nueva config") y el repo la materializa: FLAGS_BASE de configs/config.txt suma `-np 2` (ficha completa como comentario en el propio config), abrir-qwen-apex.py v3.1 lo documenta en su docstring (logica intacta) y el T06 del test de abrir fija la receta promovida. Idempotencia con el AUTO verificada: P2 de CAMPANA.py ante `-np 2` ya presente no toca nada (YA-PROMOVIDA). Tabla de pasos: PASO 3 LISTO EN REPO; PASO 4 (sanity 20 prompts en el rig con el config nuevo en D:\ZLia) sigue siendo la puerta del CIERRE del N3. CMS1024 sigue aparcada como plan B; las tres ollas byte-intactas (huellas re-verificadas).

## APENDICE R57 — Re-anclaje del mapa a pedido del Director (2026-10-31)
El Director corrige el mapa ("no, recuerda que estabamos en que corrimos los niveles 1 a 6, faltaban del 7 al 10, recuerda aparte que ibamos en etapa 2 de algo mas arriba"):

1. **PRIMERA OLLA (pasos 1..6) CORRIDA.** CAMPANA.py v1.7.2 + CAMPANA-v2.py v2.0 (p1 higiene+mediana NP2, p2 promocion -np 2, p3 sanity 20 prompts, p4 descarga UD-IQ3_XXS, p5 verificacion SHA256+parser+humo, p6 N1 formal con BARRIDO-N1.bat) quedan corridas segun la palabra del Director; el estado oficial vive en el rig (campana-estado.json). Reconciliacion de evidencia pendiente: cuando el Director pase los informes/7z de p3..p6, se preservan 1:1 en evidencia/ (como se hizo con b2/b3) y se registran los veredictos (CIERRE del N3 y N1 formal) en los docs.
2. **SEGUNDA OLLA (pasos 7..10) PENDIENTE — EL SIGUIENTE PASO ES P7.** CAMPANA-6A10.py v1.0 (olla separada, hornilla propia puerto 9932, mundo propio campana-6a10-*): P7 = re-ancla con el cuant nuevo + candidatas que transfieren (escalera k de N1, UB, ctxcp) + sanity CON tool-calling OBLIGATORIO en cambio de cuant (criterio >= +8% t/s con calidad intacta; si no llega, se REGISTRA y se decide con datos). Luego P8 (escalera VRAM/N4), P9 (b11901/RUTA 0) y P10 (duelo spec vs NP2 + receta final + CIERRE DE CAMPAÑA). Doble click = MODO AUTO (P7..P10 en orden, retoma donde quedo); puertas p8 exige p7, p9 exige p8, p10 exige p9; la puerta de entrada exige la primera olla cerrada (N3 veredicto OK y P6 verde en campana-estado.json) o --fuerza manual (queda escrito). La lista de sanity de la R56 (docs/sanity-n3-20-prompts.md) queda como ayuda manual del juez con los mismos 20 prompts.
3. **"ETAPA 2 DE ALGO MAS ARRIBA":** la palabra "etapa" NO existe en ningun doc del repo (busqueda hecha en todo el arbol) — es marco del Director de una estructura superior que no esta escrita aqui. Lectura coherente con el repo: en el ORDEN DE EJECUCION APROBADO (N1 -> N3 -> N2 -> N4 -> RUTA 0 + N5), con N1 y N3 cerrados, se ENTRA al tramo de N2 (el cuant nuevo UD-IQ3_XXS) — exactamente lo que cocinan P7 (dosis N2) y P8 (VRAM/N4). Queda registrado el marco del Director para que no se vuelva a perder: si el Director lo corrige, su palabra manda y este anexo se enmienda append-only.

## APENDICE R58 — Los niveles encontrados a pedido del Director (2026-10-31)
El Director pide ubicar la lista de niveles ("habian 4 o 5 niveles encuentralos, estabamos en el 2, (antiguo 3)"). La lista vive en `investigacion/niveles-velocidad/` (README + 5 docs completos con su par `-resumen`): **son 5 niveles numerados + RUTA 0 (6 piezas en total)**:

| # | Nivel | Tema | Doc | Estado HOY |
|---|---|---|---|---|
| 1 | N1 recorte de expertos | escalera k (fase D EXP) + modo dual | `nivel-1-recorte-expertos.md` | CERRADO (informal r16-18 + formal P6) |
| 2 | N3 eficiencia simple | flags, cache, TTFT, NP2 | `nivel-3-eficiencia-simple.md` | CERRADO (mediana NP2 GO +19.8%, promocion, sanity R56) |
| 3 | N2 cuant ligero | cambio de baseline (UD-IQ3_XXS) | `nivel-2-cuant-ligero.md` | ENTRANDO — ESTAMOS AQUI (P7) |
| 4 | N4 memoria VRAM/RAM | ngl, MEC, pagina, cliff | `nivel-4-memoria-vram-ram.md` | PENDIENTE (P8) |
| 5 | N5 draft externo GPU | fase S especulativa | `nivel-5-draft-externo-gpu.md` | PENDIENTE (P10) |
| — | RUTA 0 (sin numero) | build b11901, 2 zips | (vive en N3 §16 y el plan) | PENDIENTE (P9) |

**Reconciliacion con la memoria del Director:** en el ORDEN APROBADO (N1 -> N3 -> N2 -> N4 -> RUTA 0 + N5), la **posicion 2** la ocupa el **N3** — "el 2 (antiguo 3)": el segundo nivel que se ejecuta, el que lleva el 3 en el nombre. Ese acabamos de cerrarlo. El siguiente es la **posicion 3 = N2** ("el 2" del nombre): exactamente el cambio de nivel que el Director propuso en el turno anterior y que cocina P7. Matiz R43 que se mantiene: la mitad "descarga de cuant" del N2 queda APARCADA (el cuant vigente gano su duelo); el N2 que se corre es la mitad de dosis/sanity que vive en P7 (re-ancla + candidatas que transfieren + sanity tool-calling obligatorio, criterio >= +8% t/s).

## APENDICE R59 — El Director retira de la lista la pieza de "mejorar/cambiar modelos" (2026-10-31)
El Director decide ("no creo que podamos bajo nuestra propia cuenta mejorar los modelos que tenemos o que estan en huggingface, por lo tanto propongo quitarlo de la lista"). Materializacion:

1. **RETIRO DEFINITIVO de la lista de la campana: el cambio de cuant (descarga UD-IQ3_XXS).** Pasa de APARCADA/PINADA-revivable (R43) a RETIRADA: no hay turno que la cocine ni puerta que la revive. El PIN (14,069,266,720 B, SHA256 `36f9ec0e...7150`) queda en los docs SOLO como referencia historica.
2. **Regla generalizada y escrita: ningun trabajo de "mejorar modelos por cuenta propia"** (requant local, podas offline REAP, vocab-trim, fine-tuning). La casa ya la respetaba (N2 linea 8: "no requantizamos nada en este rig, decision del Director") y las vias candidatas ya estaban cerradas por sus propios datos: REAP-50 Q4_K_M = MAS lento en este rig (~1.6 GB/token vs ~1.45 del APEX actual, N2 §13.4); REAP-90 = meme incoherente NO-GO definitivo (N2 §19); vocab-trim real = 20.07 GB Q4_K_S (mas bytes/token, no es via de t/s); GSQ-RCO sin 3.6. Ahora la regla es del Director y vale para TODA la campana.
3. **Lo que NO se retira** (no es "mejorar el modelo"): (a) el P7 tal como esta cocinado — el script ya re-ancla "con el cuant vigente (receta tal cual)" (paso7 de CAMPANA-6A10.py) y las candidatas son DOSIS de flags, no bytes: el N2 sigue en la lista SOLO como su mitad de dosis/sanity, criterio >= +8% t/s intacto; (b) P8/P9/P10 intactos; (c) RUTA 0 (2 zips de b11901) = actualizar el MOTOR llama.cpp, no un modelo; (d) los drafts de la fase especulativa = piezas instrumentales de N5 (el MTP ya viene DENTRO del GGUF vigente via nextn.*; DSpark 307 MB queda como candidata opcional del duelo P10), no mejoras del modelo.
4. **Cambio practico en el rig: CERO.** P4/P5 ya estaban APARCADAS desde campana v1.6 (P4_APARCADA=True); CAMPANA-6A10.py no descarga nada; el re-ancla de P7 ya corre sobre el cuant vigente. La decision deja de tener un "quizas" colgando: **la lista de la campana queda sin pieza de modelo nuevo — todo lo que resta son dosis, VRAM, motor y el duelo final sobre el modelo que ya se queda.**

Tabla R58 enmendada por este anexo: la fila N2 se lee "dosis/sanity sobre el cuant vigente (pieza de cambio de baseline RETIRADA — R59)".

## APENDICE R60 — El Director confirma la ruta restante: N4 (memoria VRAM/RAM) y RUTA 0 + N5 (draft) (2026-10-31)
El Director fija el rumbo ("por lo tanto seguiremos con 4 y 5, memoria vram ram, analizar como gestionar la ram y balancear los recursos del modelo para que no se realentice por falta de recursos, y ruta 5 n draft"). Encaje con el plan (sin cambios de orden, su palabra CONFIRMA la ruta):

1. **N4 = P8 (escalera de recursos sobre el cuant vigente).** La peticion del Director — "gestionar la RAM y balancear recursos para que no se realentice por falta de recursos" — es exactamente lo que P8 certifica: (a) lado VRAM: escalera ngl + MEC dosis fina en MiB + pagina (-lm), con certificados nvidia-smi <= 3.7 GB y delta de buffer en log; (b) lado RAM/dispatch: **pageouts ~= 0** = el certificado literal de "no se realentiza por falta de recursos" (nada se derrama al swap); (c) regla cliff-1 (retroceder un peldano antes del acantilado). El lado RAM de dosis fina vive en P7 (CTXCP4 es candidata) con la leccion R32 vigente: las promesas de RAM se MIDEN, no se creen (CRAM512 prometia -7.7 GB y gano +600 MiB); la higiene R28 (apps cerradas) sigue siendo ley transversal.
2. **RUTA 0 + N5 = P9 + P10.** P9: build b11901 (2 zips, el MOTOR — no es modelo), re-auditoria de defaults, re-certificar la clave del override, sondeo cache-reuse ("restored context checkpoint") y re-ancla. P10: el duelo spec vs NP2 (MTP ya dentro del GGUF vigente via nextn.* — sin descarga; DSpark 307 MB candidata opcional), mediana de 3 por brazo, spot ES, fallback kv-unified #25345, criterio >= +25% [M]; el ganador escribe la RECETA FINAL (con backup) y cierra la campana.
3. **El orden no cambia:** P7 primero (puerta de P8), P8 antes de P9 (el presupuesto del draft se mide con la VRAM ya cerrada: un dato, no una suposicion). El "no se realentice por falta de recursos" queda como criterio de fondo de P8: sin cliff, pageouts ~= 0 y VRAM dentro de 4 GB.

## APENDICE R61 — PLAN COMPLETO DE N4: todos los experimentos posibles, nada fuera (2026-10-31, pedido del Director: "hora de n4, planifica los pasos necesarios para no dejar nada de n4 fuera, todos los experimentos posibles")
El inventario COMPLETO del N4/P8 queda materializado en doc propio: `plan-p8-n4-experimentos.md` (misma carpeta). Resumen del encaje (sin cambios de orden ni de criterios — el PASO 8 y el APENDICE R60 quedan INTACTOS):

1. **8 frentes, ~20 peldaños, cero improvisacion:** (F1) escalera -ncmoe ascendente NCM38/37/36/(35)/34 con autenticacion de semantica por delta de buffer (+656/985/1313/1969 MiB) y control -ot blindado (H6) + aislamiento del confound ctx como diagnostico (A7); (F2) MEC dosis fina --moe-cache-mib 512/768/1024 sobre el GANADOR con D-MEC-0 OBLIGATORIO (el cache chico puede ser NETO NEGATIVO: 600 MiB = -48% ajeno); (F3) RAM/pageouts: Get-Counter 10 min como CERTIFICADO literal del Director (pageouts ~= 0), -lm none YA vive en la receta (certificar, no repetir), -lm dio solo si hay pageouts, mmap+mlock prohibido salvo headroom, -lzm no aplica; CTXCP4 sigue en P7; (F4) VRAM-B con especulacion: se PLANEA aqui y se CORRE en P10 (el MTP exige -np 1) — P8 entrega el HUECO REAL como dato (NCM37 -> ~901 MB: el nextn de 858 cabe sin margen; NCM36 -> ~572: no cabe, -cmoed o bajar una capa); (F5) Vulkan shootout 1 min (NO-GO automatico si el arch GDN no carga); (F6) -ub 64 -b 512 como INTERCAMBIO presupuestario (U1, solo si la frontera queda corta para MEC — ORO-UB1K sigue mandando en velocidad); (F7) KV f16 solo diagnostico (feature de memoria, no de velocidad); (F8) ratificacion dual: el ganador re-medido en charla k=4 (D1).
2. **Aritmetica del presupuesto verificada con codigo esta ronda [M-arit, base 2211/4096 MB medidos R52]:** NCM38 est 2867 MB / NCM37 3196 / NCM36 3524 (bajo certificado 3712) / NCM35 3852 (pasa certificado, cabe en 4 GB) / NCM34 4180 = CLIFF esperado; NCM37+MEC512 = 3708 (al borde exacto del certificado); NCM36+MEC512 = 4036 (sobre cliff). La escalera + nvidia-smi deciden por peldano.
3. **Tres trampas cazadas al cruzar el codigo de la olla con los docs (van corregidas en la tabla editable):** (a) la derivacion automatica deja NGL-87/93 ACTIVAS ANTES de la subida NCM — bajar -ngl manda atencion+GDN a CPU (castigo mayor que mover expertos) y un cliff temprano DETENDRIA la escalera sin correr la subida NCM: la tabla recomendada pone los NCM PRIMERO y las NGL INACTIVAS (diagnostico del suelo del backbone, aparte al final); (b) el placeholder de MEC de la derivacion "--cmoe-cache" NO existe en el dump — la flag real es **--moe-cache-mib** [M dump linea 128]; (c) los peldanos de la olla NO son acumulativos (las acciones son autocontenidas) — las pilas del ganador (NCM+MEC, NCM+CHARLA4...) se escriben como peldanos combinados con acciones separadas por ';'.
4. **Dos vueltas de escalera:** vuelta 1 = subida pura NCM (la frontera y el cliff quedan como dato); vuelta 2 = la pila sobre el ganador (MEC, dio si R0 lo pide, U1, K1, D1) + bookend del ANCLA. Avulsos: A0 (30 s), R0 (10 min), V1 Vulkan (1-10 min). Coste total acorde a la estimacion del PASO 8 (2-3 sesiones cortas). Las dos tablas listas para pegar en campana-6a10-p8-escalera.txt viven en el doc (seccion 5).
5. **Criterios intactos:** promocion de dosis exige >= +5 pp sostenido (mediana de 3, no perseguir < 5 pp); con < +5 pp la receta no se toca y P8 cierra con frontera = ANCLA (resultado valido); salida del PASO 8 = frontera sin cliff + dual ratificado + hueco del draft registrado como dato + pageouts certificados. Sanity tool-calling NO obligatorio en P8 (mismo modelo byte a byte). El orden no cambia: P7 primero (puerta de P8), P8 antes de P9, P10 usa el hueco.

## APENDICE R62 — EL BOCETO: pseudocodigo de TODA la ronda + experimentos densificados en UN archivo (2026-10-31, pedido del Director: "en una nueva carpeta realiza pseudocodigo... sera casi un boceto, dejando un log final que te proporcionare")
Nace la carpeta `pseudocodigo/` en la raiz del repo con UN solo archivo: `boceto-ronda-completa-p7-p10.md`. No es ejecutable y no sustituye a nadie: es el PLANO para leer antes de tocar (si el boceto y el byte-intacto se pelean, manda el byte-intacto). Contenido en 8 secciones: (0) constantes de la casa leidas del codigo de la olla (9932, MED3, 8 prompts, KEEP_MIN_PP 5.0, N2_META_PP 8.0, CLIFF 0.70, certificado 3712 MB) + la receta real leida esta ronda de config.txt (FLAGS_BASE + FLAGS_GANADORAS, el ultimo valor gana: -ub 1024 -b 4096 manda sobre -b 2048 -ub 256); (1) ciclo de la ronda: guardian de huella (rc=3), main/AUTO con prevuelo, puertas rojas, DETENER_LIMPIO, regla "edita la tabla y vuelve a correr"; (2) P7 pseudocodigo completo (re-ancla, candidatas K-N1-PIN8/SIN-UB1K/CTXCP4, sanity 12 prompts tool-calling obligatorio, veredicto FALLA/GO >= +8pp/REGISTRADO); (3) P8 pseudocodigo completo con las 3 trampas R61 incrustadas como comentarios, dos vueltas de escalera, avulsos A0/R0/V1, aritmetica del presupuesto y criterios de salida; (4) P9 (version b11901, cudart, diff --help, override vivo, sondeo reuse #24055, re-ancla); (5) P10 (brazos A/B/C, fallback B < 90% de A, mediana de medianas + spot ES, receta final con backup + re-lectura, cierre de campana); (6) MATRIZ DENSIFICADA: 42 experimentos numerados E01-E42 con criterio/autenticador en una linea cada uno — P7 (6), P8 (E07-E30: 8 frentes + NGL aparte), P9 (E31-E36), P10 (E37-E42) + predeclarados; (7) ANTI-BUGS: las 10 trampas ya cazadas (T1-T10) para no repetirlas; (8) LOG FINAL: hueco RESERVADO al final del archivo, vacio, a la espera del log que el Director proporcionara (se pegara sin reescribir nada). Verificacion de huellas antes de escribir el boceto: CAMPANA-6A10.py CFEADBEA...D1947 (crudo), CAMPANA.py 65D33CBA...DA4B1, CAMPANA-v2.py 52996E67...B1E86 — las tres ollas BYTE-INTACTAS (el boceto vive en carpeta nueva y no toca ni una coma del codigo). Ningun criterio ni orden cambiado: el boceto ESPEJA el plan R61 tal cual.

## APENDICE R63 — AUDITORIA DEL BOCETO: 12 hallazgos corregidos + fortaleza (2026-10-31, pedido del Director: "encuentra inconsistencias incoherencias en el pseudocodigo, fortificalo hazlo mas eficiente")
El boceto `pseudocodigo/boceto-ronda-completa-p7-p10.md` fue contrastado funcion por funcion contra CAMPANA-6A10.py (P7-P10, hornilla, rutas, cirugia de flags, bloque final). Hallazgos corregidos (bitacora completa en la seccion 9 del boceto): (F1) veredicto P8 estaba incompleto — faltaba la rama cliff-sin-frontera -> DUDOSO rc=2 (cliff en el PRIMER peldano activo); (F2) P7 con --sin-sanity tiene el GO IMPOSIBLE (la rama GO exige sanity_ok True; techo REGISTRADO; P8 abre igual porque REGISTRADO es verde); (F3) la puerta de entrada quedo escrita EXACTA: (n3.cerrado O P3 verde_olla1) Y P6 verde_olla1 de campana-estado.json; (F4-F6) bloques nuevos de consulta rapida: MUNDO PROPIO (rutas, CSV de 9 columnas una fila por corrida, logs server-<ETIQUETA>-c<k>.log), TABLA DE RC del guardian (0/1/2/3/130) y CLI completo (estado|plan|pN|AUTO + flags por paso); (F7) el spot de P10 corre POR CORRIDA y el brazo exige spot limpio en TODAS sus corridas; (F8) avulsos A0/R0/V1 y bookend son MANUAL fuera de la olla, mientras el calentamiento "Calienta la plancha" se descarga POR CORRIDA dentro del codigo; (F9) la derivacion de candidatas P7 tiene DOS ramas (receta sin pin -> PIN EXPERTOS_TRABAJO=8 + vecinos 7/9; receta con pin -> re-aplica + pin-1); (F10) estado corrupto -> .corrupto-<sello> como evidencia, nunca silencio; (F11) COSMETICO DE LA OLLA CAZADO: el print del paso 6 de P9 dice "1 corrida" pero _lanza_corridas corre --corridas=3 — anotado en el boceto y aqui, la olla queda BYTE-INTACTA (el boceto describe la conducta: MED3); (F12) semantica exacta de la cirugia: add al final (ultimo valor gana), del/sub pisan TODAS las apariciones, delpair borra flag+valor, accion desconocida se ignora y queda en el informe. Trampas nuevas T11-T14 (techo sin sanity; fila de tabla con <3 celdas se ignora en silencio y celda no puede llevar "|"; VRAM = certificado blando que nunca frena; cirugia exacta). EFICIENCIA: runbook de una lectura (DOOR -> P7 -> P8 -> P9 -> P10 -> cierre) como primera linea del ciclo. NINGUN criterio del plan cambio: cliff-1, MED3, >= +5 pp, >= +8 pp, 3712 MB, fallback 90%, spot limpio — todo INTACTO. Huellas re-verificadas antes y despues: las tres ollas byte-intactas.

## APENDICE R64 — SEGUNDA RONDA DE REVISION DEL BOCETO: 12 hallazgos nuevos en hornilla/utilidades/docstring (2026-10-31, pedido del Director: "segunda ronda de revision del pseudocodigo")
La re-auditoria cubrio lo que la R63 no habia contrastado: hornilla fina (_arranca_server/_chat_uno/_auto_apaga/_cuenta_en_log), utilidades (mediana/health_ok/sin_tildes/gb_libres/sha256_archivo) y el docstring de cabecera de CAMPANA-6A10.py. Hallazgos F13-F24 (bitacora del boceto, seccion 9): (F13) la "mediana de medianas" es la mecanica de TODA la olla, no solo de P10 — cada corrida = mediana de los t/s de sus prompts, total = mediana de las 3 medianas; (F14) en P8 basta UNA corrida muerta (muertos>0) para declarar el cliff, la mediana se calcula con las vivas (2 → promedio); (F15) el sondeo cache-reuse de P9 tiene TRES salidas — VIVO / MUERTO / INDETERMINADO (server del sondeo no levanto → GO con reuse "?"); (F16) semantica exacta de mediana() (filtra no-numericos; 2 vivas → promedio; 0 → None); (F17) el sampling del medidor es FIJO (temp 1.0, top_k 20, top_p 0.95, max_tokens 220) y NUNCA debe cambiarse entre dosis — es lo que hace comparables las corridas; (F18) el reintento (1, 3 s) es SOLO para red/timeout/5xx, un 4xx no se repite (herencia r50); (F19) los logs de server van en APPEND y acumulan sesiones; (F20) la hornilla NUNCA levanta ni apaga servers ajenos, solo sus hijos; (F21) arranque: health poll cada 2 s, tope 7 min, sin health → auto-apaga + peldano como DATO; (F22) --m-prompts corta los PRIMEROS N de la lista fija de 8; (F23) el RESUMEN.md del sanity se ROTA con sello (no se borra); (F24) el sondeo reuse tambien calienta plancha. Trampas nuevas T15-T18 en el boceto. NINGUN criterio cambio; las tres ollas byte-intactas re-verificadas.
