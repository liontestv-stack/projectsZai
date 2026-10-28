# RESUMEN SIMPLE — Nivel 3: Eficiencia simple (flags, cache, colocación — sin descargar nada)

> **Qué es este archivo:** la misma información que `nivel-3-eficiencia-simple.md`, punto a punto y sección por sección (los números de § coinciden), pero explicada en términos simples y resumida.
> **La información completa (flags al carácter, issues, protocolos, auditoría punto a punto) está en el archivo completo.** Este resumen no añade nada nuevo.
>
> Etiquetas simplificadas: **[medido aquí]** = probado en este rig · **[verificado afuera]** = confirmado en fuente externa · **[estimación]** = cuenta propia.

---

## 0. Veredicto (§0 del completo)

- De **37 configs medidos [medido aquí], solo 3 movieron la aguja al alza**:
  - **ORO-UB1K** (`-ub 1024 -b 4096`): prefill **+26.5%**, decode intacto. Ya vive en el launcher.
  - **NCM37C4** (`-ncmoe 37 -c 4096 -ctk/ctv q4_0`): decode **+4.4%** (el mejor decode medido).
  - **FIT-A** (`-ngl auto -ncmoe 34 -fitt 256`): decode **+4.0%**.
- El gran pendiente no es decode sino **TTFT** (el tiempo hasta la primera palabra): configurar bien la cache de prompts evita re-pagar el prefill en cada turno de chat.
- Techo honesto del nivel: +5–9% decode + mejoras grandes de TTFT. La potencia está en los Niveles 1 y 2; este nivel es pulir.

## 1. Dónde se va el tiempo de un turno (§1)

- Turno típico: **~35% prefill + ~65% decode**. Con system prompt grande o conversación larga, el prefill domina. Creer que "solo importa el t/s" es el error clásico.

## 2. Los 37 configs, clasificados (§2) [medido aquí]

- **Ganan**: UB1K (prefill), NCM37C4 y FIT-A (decode +4%).
- **PÉSIMO (cerrado con datos)**: fijar afinidad de hilos a núcleos: −9% a −38%. El scheduler de Windows ya lo hace mejor.
- **Ruido**: prioridades, polling, KV q5_1, `-lm dio`.
- **Muertos**: spec por n-gramos (aceptación casi cero en este uso), FIT-C (desbordó y colapsó −38%), repack off (−5%), el override con la clave equivocada (renace como Nivel 1).
- Lección fina: en colocación, un margen de ±256 MiB decide entre +4% y −38%.

## 3. La joya pendiente: cache de prompts en un modelo híbrido (§3)

- **El problema**: este modelo mezcla 30 capas recurrentes + 10 de atención. El estado recurrente no se puede "cortar" por tokens, así que el server a veces **re-procesa TODO el prompt en cada turno** (línea de log "forcing full prompt re-processing", documentado como exclusivo de arquitecturas híbridas como la nuestra).
- **El arreglo (flags correctos)**:
  - `--cache-reuse 256` (recicla prefijos; hay que ponerlo explícito, el default es 0).
  - `--ctx-checkpoints N` (checkpoints para "rebobinar" el estado recurrente).
  - `--cache-ram 512` (el default 8192 MiB pelea con el modelo por la RAM).
  - Con la cache funcionando, terceros midieron **TTFT −93%** en prompts repetidos.
- **Cuidado**: si la plantilla de chat cambia el inicio del prompt (fechas, historial reescrito, `<think>` de turnos anteriores), la cache no acierta. Regla: lo inmutable arriba, lo volátil al final.
- **Validación**: repro curl de turnos crecientes midiendo el tiempo de primera respuesta. Sano = "restored context checkpoint" + TTFT plano; roto = "forcing full re-processing" + TTFT creciendo.

## 4. Paralelismo de slots (§4)

- `-np 2` da ~+14% de throughput agregado [medido aquí] (el ctx se reparte entre slots). Para un solo usuario es el punto razonable. **PERO con MTP va `-np 1` obligatorio (§11.4)**.

## 5. Carga, arranque y RAM (§5)

- `--no-warmup` ahorra ~1.5 s de carga. `-lm dio` no cambia nada medible.
- **mlock: NO** con 14.27 GB de modelo en 16 GB de RAM (riesgo de ahogar al sistema).

## 6. Sistema operativo (§6)

- Plan de energía "Alto rendimiento" (perfil de Windows, no BIOS): candidato a medir.
- Excluir el server de Defender: **PROHIBIDO por decisión del Director**. No se propone.
- Afinidad de núcleos: cerrado con datos negativos.

## 7. Muertos definitivos — no reintentar (§7)

ngram como spec · afinidad/masks · FIT-C · repack off · KV q5_1 · override con clave `qwen3moe.*` · polling no-default.

## 8. Protocolo para cosechar lo que queda (§8)

1. Combo ganadores juntos: UB1K ⊕ NCM37C4 ⊕ (-np 2) ⊕ cache (reuse 256 + cache-ram 512 + checkpoints). Expectativa: decode ~22.5–23.5.
2. Si el ctx 4096 es poco: `-c 8192` con KV cuantizada (lo paga el IQ3_XXS del N2).
3. Validar la cache en chat real con el repro curl.
4. Registrar todo en el informe del barrido.

## 10. Anexo ronda 2: defaults del build y presupuesto de checkpoints (§10)

- Defaults confirmados del build b11856 [medido en el dump]: checkpoints 32/slot, checkpoint-min-step 8192, cache-ram 8192 MiB, kv-unified ON, context-shift OFF, cache-reuse 0 (apagado).
- Cada checkpoint guarda el estado recurrente ≈ **63 MB** → el default (32) puede comer **~2 GB de RAM** → bajar (`-ctxcp` chico + `-cms 1024`).
- Bug conocido (#24055): el flag de checkpoints puede no crear checkpoints y forzar re-procesado; además la cache puede auto-apagarse según el contexto (línea "cache_reuse is not supported"). → **Protocolo de validación obligatorio** antes de dar por buena la cache.

## 11. Anexo ronda 3: Windows/GPU fino y defaults al 100% (§11)

- **"CUDA - Sysmem Fallback Policy"** (Panel NVIDIA): cuando la VRAM se llena, Windows puede aterrizar asignaciones en la RAM **en silencio** y todo se vuelve lento sin error. Cambiar a **"Prefer No Sysmem Fallback"**: si desborda, falla con error visible (exactamente lo que un barrido necesita para detectar malos fits al instante). Es setting de driver — no toca BIOS ni Defender.
- Plan de energía con GUID exacto: Alto rendimiento `8c5e7fda-…` (comando powercfg en el archivo completo).
- Auditoría completa de ~25 defaults del build (tabla en el archivo completo): lo que hay que cambiar explícito es cache-reuse 256, cache-ram 512, -cms 1024, context-shift ON, prio 2, fa on.
- **Conflicto resuelto: MTP exige `-np 1`** (restricción oficial del repo MTP) → la ganancia de slots solo aplica SIN MTP.
- "Speculative checkpointing" (PR #19493): dosis por n-gramos solo para sesiones de código; prioridad baja.
- Detalles finos confirmados a nivel de código: checkpoints exigen contexto FULL/RS/n_swa; el repro del issue #21831 estaba **viciado** (solo mandaba el mensaje nuevo); los `<think>` de turnos anteriores rompen el prefijo incluso con `-rea off`.
- Líneas finales recomendadas: una SIN MTP (combo ganadores + cache) y una CON MTP (`-np 1` + spec flags + cache-ram 256) — texto completo de ambos comandos en el archivo.

## 12. Anexo ronda 4: KV unificada silencia el spec, leaks y checkpoints (§12)

- **#25345**: con la KV unificada activa (default en este build), llama-server **puede IGNORAR el draft en silencio** → en toda config especulativa: grep del log + aceptación > 0; si no engancha, probar `--kv-unified off`.
- Leak de VRAM en prefill con MTP + KV cuantizada (#23635, cerrado upstream) y leak genérico ~3 MB/request (#27725, sin confirmar) → higiene: reiniciar server entre fases y vigilar RAM/VRAM en sesiones largas.
- Presupuesto de checkpoints: default ≈ 2 GB potenciales → dosis **`-ctxcp 4`** libera ~1.5-1.8 GB = candidato #1 a culpable de pageouts.

## 13. Anexo ronda 5: b11856 vs upstream y protocolo de medición (§13)

- El build del rig ya incluye 3 fixes útiles (FA races, cache updates, k-pool); NO incluye el fix de plantillas Jinja (b11869) — única razón funcional para actualizar, y solo si aparecen síntomas de tool-calling malformado.
- **Protocolo de medición** (de un estudio con 3002 corridas): el mismo config varía **9.4 puntos porcentuales** en un día → reglas: mediana de 3, baseline matcheado DENTRO de cada corrida, no perseguir deltas <5pp, mismo horario.
- op-offload: con expertos en CPU, batches grandes de prefill copian pesos a la GPU; el tamaño de `-ub` amortiza esas copias (terceros: 5.5× de prefill con `-ub 4096`) → A/B de `-ub` con protocolo TTFT; no copiar números sin medir en 4 GB.

## 14. Anexo ronda 6: #21831 sin fix, flags muertas y coste del MTP al cache (§14)

- El re-procesado completo en híbridos sigue **sin arreglo**: los workarounds con flag (`-cpent`) **NO existen en b11856** [medido en el dump] → si el bug aparece, opciones reales = build nuevo, parche, o aceptar el coste medido.
- **Muerte de las flags de carga**: `--no-mmap`/`--mlock`/`--direct-io` fueron plegadas en `-lm` (PR #20834) y luego **eliminadas por completo** (PR #28334) → en builds nuevos dan error duro. Traducción obligatoria: `--no-mmap` → `-lm none`, `--mlock` → `-lm mmap+mlock`.
- El MTP degrada el hit-rate del cache de prompts (92% → 71% medido en vLLM) → la fase E añade medición de TTFT y un A/B con cache off si el chat empeora.
- Regla de terceros ratificada: *"Do not copy a value. Sweep it"* (con `-ncmoe`) — exactamente la filosofía del barrido.

## 15. Anexo ronda 7: timeouts con spec, drift del MTP y defaults ≠ master (§15)

- **Timeouts intermitentes con spec** (#23268): <1% de llamadas pueden colgarse con la conexión viva → timeout de cliente 120-180 s + 1 retry; si aparecen cuelgues, primer sospechoso = el spec (A/B spec off).
- **Drift de salida del MTP medido**: con temp 0, solo 7/50 respuestas idénticas carácter a carácter; en corrección de tareas es ruido (34 vs 33 aciertos), no degradación → reglas: MTP ON para agentes, MTP OFF para evals/reproducibilidad, y para matching exacto usar greedy.
- **Defaults del build ≠ master**: en b11856 `--spec-draft-n-max` default es **16** (master: 3) y `--spec-draft-p-min` es **0.75** (master: 0.00) → fijar SIEMPRE ambos explícitos.
- v0.7.0 trae chat session API, restore de slots/prompt-cache mejorado, puerto nuevo 9931.
- Herramienta oficial de medición: **SPEED-Bench** en master.

## 16. Anexo ronda 8: RUTA 0 sin compilar (§16)

- **No hace falta compilar**: GitHub publica binarios Windows precompilados. Último release etiquetado: **b11901** (45 builds más nuevo que b11856; incluye TODO v0.7.0).
- Elección conservadora para la 1650 (Turing): la variante **CUDA 12.4** (el aviso de low-bit roto era de CUDA 13.2; el estado de 13.4 es desconocido).
- **GOTCHA crítico**: el zip del binario NO trae las DLL de CUDA → descargar TAMBIÉN `cudart-llama-bin-win-cuda-12.4-x64.zip` y extraerlo en la misma carpeta. Sin eso la GPU queda dormida (caso real: 26 t/s por Vulkan de emergencia). RUTA 0 = DOS zips.
- Config de producción ajena con nuestra familia exacta (UD-Q4_K_S + draft-mtp n4 + ctx 64k + KV q4_0): valida que la pila convive; nuestros n-max sigue siendo 2.
- Tras instalar: re-auditar defaults del build nuevo y registrar el dump nuevo como fuente de verdad #1 (sin borrar el viejo).

## 17. Anexo ronda 9: muerte con fecha de los alias y op-offload (§17)

- Calendario: los alias de carga murieron oficialmente (plegados 23-Jul, eliminados 09-Sep-2026) → tras RUTA 0, `--no-mmap`/`--mlock` dan **error duro sin warning**; la traducción `-lm` pasa de recomendada a **obligatoria**.
- `-ngl` default "auto" ya existe en b11856 [medido en el dump] — el consejo de internet "-ngl 99 siempre" es un workaround viejo; nuestras recetas fijan `-ngl` explícito.
- **Op-offload**: explica por qué `-ub` manda en el prefill híbrido (ver §13) — mecanismo confirmado por guía profesional + dato 5.5×.
- Fork ik descartado también para prefill (−2× PP) — se cierra toda la vía fork.
- Categorización 2026 de flags: **"solo `-fa` y `-ub` compran velocidad cuando el modelo ya cabe; el resto compra que quepa"** — coherente con todo nuestro CSV.

## 18. Anexo ronda 10: auditoría de respaldo riguroso (§18)

- Re-verificación punto a punto: **0 puntos refutados**; el bloque de cache híbrida (#21831 + repro viciado + protocolo curl) y los bugs de spec (#25345, #23268) quedaron confirmados verbatim contra fuente primaria; el dump respaldado por la manpage Debian.
- Benchmark ajeno con nuestro modelo exacto replica la forma n2 > n3 > n4 de la aceptación (independiente del estudio v4).
- Protocolos SIN cambios: combo ganadores + curl protocol + `-ctxcp 4` + traducción `-lm` tras RUTA 0.

## 19. Anexo ronda 11: el instrumento de la cosecha (§19)

- Nace `barrido-n3-eficiencia.py`: mide TODO lo que queda vivo de este nivel en UNA corrida (~35-45 min, o `--quick` ~18 min), con el método de la casa (escalera + control + certificado + informe).
- **La medida de referencia ya no es el laboratorio: es tu receta diaria.** El ancla de la sesión es lo que ABRIR-QWEN lanza hoy; si una dosis no le gana a eso, no entra en config.txt.
- La escalera (13 configs): RAM (cache-ram 512, ctxcp 4, cms 1024) · cache (reuse 256 solo y con shift — la joya) · 2 meseros (-np 2) · NCM37C4 apilada con UB1K (primer dato de ese combo) · 3 combos · 2 controles (sin cache y bookend).
- Cada dosis trae su testamento: la cache se certifica con **líneas del log** (restored vs forcing) + **TTFT plano en una conversación que crece**; la RAM con lo libre antes/después; los 2 meseros con dos pedidos a la vez.
- Control honesto incluido: una config **SIN cache que DEBE ir lenta** — si no va lenta, el medidor está roto, no la idea.
- Si la cache no se deja activar en este build (#24055), queda registrado como **motivo para RUTA 0** (build nuevo), no como fracaso.
- Las candidatas que certifiquen se promueven editando UNA línea de config.txt (eso ya se sabe pagar).

---

## Cheatsheet operativa del nivel 3

- **Ganadores medidos**: `-ub 1024 -b 4096` (prefill +26.5%) ⊕ NCM37C4 o FIT-A (decode +4.4%/+4.0%).
- **Cache híbrida**: `--cache-reuse 256 --cache-ram 512 -cms 1024 --ctx-checkpoints 16(8)` + validación curl obligatoria.
- **RAM gratis**: `-ctxcp 4` (libera ~1.5-1.8 GB).
- **Traducciones obligatorias**: `--no-mmap`→`-lm none`, `--mlock`→`-lm mmap+mlock`, `--draft-max`→`--spec-draft-n-max`; fijar siempre n-max y p-min explícitos.
- **RUTA 0** = 2 zips de b11901 (binario CUDA 12.4 + cudart DLLs).
- **Medición**: mediana de 3, baseline matcheado, no perseguir <5pp.
- 📄 Detalle completo, fuentes y auditoría: [`nivel-3-eficiencia-simple.md`](nivel-3-eficiencia-simple.md)

---

## El prevuelo completo: lo que el barrido sabe de ti antes de empezar (28-oct-2026, espejo simple del §20)

- **Pedido del Director**: "hazlo completo con todo lo que va a necesitar saber sobre mi pc, el modelo y todo sobre el nivel en el que estamos antes de comenzar". Ahora el informe abre con un **dossier completo** (sección 0) que se arma ANTES de medir la primera config.
- **0.1 Tu PC**: sistema operativo, CPU, RAM por módulo (¿son 2 palos a la misma velocidad? = dual channel), pagefile (el detector del riesgo de la ronda 28), espacio libre en los discos, GPU con su driver, plan de energía, cuánto tiempo lleva encendida la máquina y **los 4 programas que más RAM se están comiendo** (explica dónde se fue el 97% del 27-oct).
- **0.2 Tu modelo, certificado**: tamaño exacto + **huella SHA256** (como la firma del archivo: si mañana descargas otro cuant, la huella cambia y se nota) + los datos internos del GGUF leídos del archivo real (cuántos cocineros tiene de fábrica, contexto, bloques, si trae MTP) + la versión del server (build 11856).
- **0.3 Tu receta diaria**: el comando exacto que se va a medir, con la auditoría de flags en verde.
- **0.4 El nivel N3 entero, incrustado**: la campaña (N1 → N3 → N2 → N4 → RUTA 0 + N5 y dónde está cada una), los números de referencia del laboratorio (21.53 / 22.49 / 21.57 / 21.39 / k=4 28.85), el libro de muertos (lo que NO se vuelve a medir), lo que ESTA corrida viene a cosechar, y el protocolo de decisión (mediana de 3, bookend, promoción de UNA línea).
- **0.5 El día**: el recordatorio de la ronda 28 — si la RAM va al 97%, cierra apps antes; el barrido debe medir la receta, no el pagefile.
- **Sin miedo**: si una pieza no existe (p. ej. fuera de Windows), el dossier pone "no disponible" y sigue — nunca se cae. El hash añade ~1 min al inicio; `--sin-sha256` lo salta y `--sin-prevuelo` vuelve al comportamiento de la v1.0. Las dosis, la medición y el CSV NO cambian nada.

---

## El examen de campo del dossier: primer arranque real, un crash cazado y curado (28-oct-2026, espejo simple del §21)

- **Qué pasó**: al estrenar la v1.1 en tu PC, la auditoría de flags pasó en verde (13 configs, cero prohibidas), pero el dossier del PC se cayó al tropezar con... tus 2 palos de RAM. El barrido murió ANTES de tocar nada: no se midió nada, no hay nada que limpiar ni rescatar.
- **El bug en cristiano**: una frase del dossier estaba escrita a medias en dos líneas sin paréntesis — Python leyó la primera línea como una orden completa y la segunda como otra orden que recibía 3 datos para 0 huecos → error y fuera. En las pruebas de taller (Linux) esa pieza nunca se ejecutaba porque ahí no hay Windows; en tu PC sí, y con 2 palos justo.
- **El arreglo**: paréntesis alrededor de la frase completa. Nada más cambió: las 13 dosis, el protocolo y el dossier son idénticos a los de la v1.1.
- **La vacuna (lo importante)**: la batería trae ahora un **detector de esta familia entera de bugs** que revisa TODOS los scripts en cada corrida (11/11 limpios hoy), y por fin prueba la pieza Windows del dossier con datos falsos realistas (2 palos, 1 palo sin velocidad): 55 → **58 checks, todo verde**. Esta clase de bug no puede volver a colarse sin que la batería grite.
- **Honestidad**: durante la revisión se sospechó de una segunda pieza (la función math de PowerShell en los comepanes); verificada byte a byte, estaba BIEN — la sospecha era un espejismo del taller, descartado y registrado.
- **Para ti**: re-copiar `barrido-n3-eficiencia.py` (v1.2) a D:\ZLia y repetir el mismo comando de siempre.

---

## La segunda examen de campo: 11 de 13 medidas muertas por una palabra olvidada, cazado y curado (28-oct-2026, espejo simple del §22)

- **Qué pasó**: en la primera corrida completa de la v1.2 (27-oct noche), el inventario de tu PC y la auditoría de flags pasaron bien — y luego **11 de las 13 medidas murieron en ~2.5 segundos** al arrancar el server. Solo sobrevivieron las 2 medidas que llevaban su propio acomodo de expertos (NCM37C4 y COMBO-T). La ancla (tu receta diaria) murió también, y sin ancla no hay sesión que valga.
- **El bug en cristiano**: la lista de comandos del barrido se copió a mano en su día y **se olvidó una palabra de tu receta diaria: `-cmoe`** (la orden de "los expertos viven en la RAM"). Sin esa palabra, cada arranque intentaba meter el modelo entero de **14.27 GB dentro de la GPU de 4 GB** → muerte instantánea. Lo irónico: tu receta diaria la trae siempre — el error era solo del papel del barrido.
- **Por qué nadie lo vio**: los tres controles miraban cosas distintas — la auditoría revisa que cada palabra exista en el diccionario de flags (no que la receta esté COMPLETA), y el server de práctica del taller aceptaba cualquier comando. La lección ya estaba escrita en el cuaderno del barrido campeón del laboratorio ("cada medida lleva su propio acomodo") y no se consultó. Ahora esa regla está grabada a fuego.
- **El arreglo (v1.3)**: (1) la palabra está de vuelta — cada medida lleva su acomodo, como en el laboratorio; (2) **tres trampas nuevas**: si a la ancla le falta UNA pieza de tu receta, no se mide nada; si a cualquier medida le falta su acomodo, no se mide nada; y si la ancla muere, el barrido PARA en el minuto 0 en vez de quemar el día; (3) el CSV guarda ahora las últimas palabras del server (forense) para diagnosticar sin abrir archivos; (4) el server de práctica del taller **se niega a arrancar sin acomodo** — este fallo ya no puede colarse en las pruebas.
- **Lo que la corrida muerta sí dejó**: la huella digital del modelo certificada (SHA256 = el certificado del N2 adelantado), el **tercer motivo de RUTA 0** (la cache de prompts está DECLINADA por tu build en esa colocación — el warning #24055 salió en vivo), y el primer dato del stack UB1K×NCM (18.78 vs 22.49 histórico sin UB1K — sugiere que UB1K estorba ahí, provisional hasta mediana de 3).
- **Para ti**: re-copiar `barrido-n3-eficiencia.py` (v1.3) a D:\ZLia y **repetir el mismo comando en la misma carpeta**. Las 11 muertas se re-miden solas y las 2 vivas conservan sus números. Batería 58 → **63 checks, todo verde**.
