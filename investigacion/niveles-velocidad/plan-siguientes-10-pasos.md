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
