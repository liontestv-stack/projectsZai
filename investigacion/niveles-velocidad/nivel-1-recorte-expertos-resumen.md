# RESUMEN SIMPLE — Nivel 1: Recorte de expertos en runtime (fase D EXP)

> **Qué es este archivo:** la misma información que `nivel-1-recorte-expertos.md`, punto a punto y sección por sección (los números de § coinciden), pero explicada en términos simples y resumida.
> **La información completa (fuentes exactas, URLs, tablas completas, auditoría punto a punto) está en el archivo completo.** Este resumen no añade nada nuevo.
>
> Etiquetas simplificadas: **[medido aquí]** = probado en este rig · **[verificado afuera]** = confirmado en fuente externa (ver archivo completo) · **[estimación]** = cuenta propia no medida todavía.

---

## 0. Veredicto (§0 del completo)

- La idea: decirle al modelo que use **menos expertos por token** (de 8 activados a 6, 4 o menos) con un solo flag. No hay que descargar nada, se puede revertir al instante y el archivo del modelo no se toca.
- Es la vía de aligerado más potente que existe para este modelo. La evidencia en modelos hermanos es fuerte: un paper académico midió **~95% de calidad conservada al doble de velocidad**, y Cerebras (REAP) retuvo **97.6% de capacidad de código** quitando la mitad de los expertos [verificado afuera].
- **PERO el barrido-30 de este rig midió todo plano** (no cambió nada) porque el script usó una clave equivocada: la dosis **nunca se aplicó**. No es que la idea falló — es que **aún no se ha probado de verdad**.
- Esperanza realista aquí: **+8–17% t/s con k=6..4, +22–28% con k=3..2** [estimación], con calidad que aguanta hasta k=4 según la evidencia.

## 1. Qué toca exactamente la dosis (§1)

- El modelo tiene 40 capas; cada capa MoE tiene **256 expertos** guardados y usa **8 por token** (+ 1 compartido que siempre se usa).
- Bajar k (= expertos usados) hace que **se lean menos datos de la RAM por token**. Eso es exactamente lo que este rig necesita (ver §2).
- Lo que NO cambia: la RAM ocupada (los 256 siguen cargados), la VRAM, el archivo descargado. Es un recorte "virtual": el modelo completo sigue en memoria, solo se lee menos.

## 2. Por qué esto es ganancia casi directa (§2)

- Este rig está **clavado en la velocidad de la RAM** (~32 GB/s efectivos, medido indirectamente con el ancla 21.53 t/s).
- Regla simple: **menos bytes leídos por token ≈ más t/s casi 1 a 1**. Todo lo demás medido en este rig se comporta como predice esa regla.

## 3. La evidencia profesional (§3)

- **MoE-Spec (paper)**: en el hermano 30B (mismo patrón de routing), bajar expertos mantiene ~95% de calidad a 2× de velocidad. Es el modelo más favorable de los evaluados. Los últimos expertos del top-8 casi no pesan en la respuesta.
- **REAP (Cerebras)**: podar la mitad de expertos retiene 97.6% de coding / 96.7% SWE-Bench agéntico.
- **Ojo con la cola larga**: borrar del archivo los expertos "raros" sí daña (llevan información única). Nuestro método NO borra nada — solo deja de leer los de menor probabilidad en cada token. Es la forma menos dañina de recortar.
- **Comunidad llama.cpp**: un usuario bajó de 10 a 7 expertos y pasó de 35 a 45 t/s (+29%) sin degradación visible.
- **Recortes ya hechos y descargables del 3.6**: el REAP-90% es un "meme" incoherente (NO-GO, dicho por su propio autor); el vocab-trim existe (ver N2); el REAP-50 coding es un experimento opcional.

## 4. Qué pasó en el barrido-30: el no-op (§4)

- Los datos [medido aquí]: EXP10/8/6/5/4 dieron todos ~21.3–21.5 t/s = idéntico al ancla. Plano total.
- Tres explicaciones posibles; las dos primeras quedan descartadas por matemática (un rig limitado por RAM no puede ser ciego a ±15% de bytes leídos).
- La correcta: **el override nunca se aplicó** — la clave usada era `qwen3moe.expert_used_count` pero la arquitectura real del 3.6 es `qwen3_5_moe`. La firma: incluso el control EXP10 (que debía FRENAAR) no se movió.
- **Lección operativa**: toda dosis debe autenticarse. El barrido-total v1.0 ya lo hace: lee el nombre real de la arquitectura del archivo GGUF y construye la clave correcta. Un run solo vale si el log muestra `n_expert_used = N` con el N dosificado.

## 5. Dosis esperadas y puerta de calidad (§5)

| Dosis (k) | decode esperado | vs ancla | Calidad esperada |
|---|---|---|---|
| 8 (ancla) | 21.5 t/s | = | 100% |
| 6 | ~23.3 | **+8%** | pérdida despreciable en chat |
| 4 | ~25.1 | **+17%** | ~95–98% (zona segura según paper) |
| 3 | ~26.4 | **+22%** | sacrificio real; math/código se notan |
| 2 | ~27.5 | **+28%** | cliff; solo si la calidad es sacrificable |

- La calidad NO se mide con t/s: puerta doble = re-ancla del barrido + **sanity manual de 20 prompts** (10 chat ES, 5 código, 5 tool-calling — tool-calling es lo más frágil del modelo).

## 6. Protocolo de ejecución (§6)

1. Correr `barrido-total.py` fase D (construye la clave correcta él solo).
2. Gate: si el log no muestra la dosis pedida → run inválido.
3. Escalera: EXP6 → EXP4 → EXP3 (solo si EXP4 pasa sanity) → EXP2 (curiosidad).
4. El ganador se apila con ORO-UB1K sin conflicto de flags.
5. Plan B si la clave correcta tampoco funcionara: actualizar build (no hay flag futuro — ver §12).

## 7. Riesgos y mitigaciones (§7)

- Degradación no uniforme: math/código/tool-calling primero, chat al final → sanity por categorías, k≥4 como default.
- A k agresivo la salida se "atenúa" (no hay re-escalado de pesos) → quedarse en k=4–6 donde eso importa poco.
- Con MTP (fase E) es **sinergia**, no conflicto.
- La RAM ocupada no baja (eso lo da el Nivel 2).
- Reversibilidad total: es un flag, se quita y listo.

## 8. Stack con los otros niveles (§8) [estimación]

Ancla 21.5 → +cuant IQ3_XXS ~23.2 → +EXP k=4 ~27.1 → +NCM/FIT ~28.2 → +MTP n2 **~36 t/s** (variante sacrificio k=2: ~40). El objetivo +50% queda dentro del compuesto; el ×2 exige todo el stack.

## 9. Pendientes (§9)

- No existe métrica KLD para recorte (es inferencia distinta, no cuant): la puerta es sanity + benchmarks de uso.
- Confirmar si el build renormaliza en silencio con k<8.
- Vigilar un flag dedicado upstream (aunque §12 lo da por muerto).

## 10. Referencias (§10)

Todas las URLs exactas (papers, issues, discusiones, repos HF) están en el archivo completo. Nada se repite aquí.

## 11. Anexo ronda 2: la clave exacta (§11)

- El código fuente de llama.cpp confirma el formato: `<arch>.expert_used_count`. El nombre real de la arquitectura lo decide el campo `general.architecture` **del GGUF concreto** (lo imprime el log de carga) — no el tag de HF.
- Comunidad confirma que el override funciona cuando la clave es correcta (Reddit con el 235B; el +29% de la discusión #30155).
- Refuerzo de la puerta de calidad: REAP-50 (más agresivo que nuestro k=4 y borrando de verdad) retiene 96.7% agéntico → margen amplio.
- Test de coherencia del rig: si k=4 se aplica de verdad, el t/s DEBE subir ~15–17%. Si no sube con la dosis correcta en el log → revisar colocación antes de seguir.

## 12. Anexo ronda 3: mecánica hasta el último detalle (§12)

- Sintaxis confirmada al carácter (dump del build): `--override-kv CLAVE=TIPO:VALOR`, tipos `int/float/bool/str`, varios overrides separados por comas.
- La firma de autenticación es literal: grep `llm_load_print_meta: n_expert_used = N` (validado en producción desde 2024 en la discusión #5114).
- El issue que pedía un flag dedicado (`--moe-topk`) está **cerrado como "not planned"**: el mantenedor respondió que ya existe el override-kv → **no esperar flag nuevo**.
- **Lista NO-TOCAR**: las otras claves `expert_*` (count, ffl, shared, scale, gating) NO se tocan — cambiarlas rompe o corrompe.
- Por capa NO se puede: la dosis es global para todo el modelo.
- Bonus inesperado: bajar k también libera un poco de VRAM (el buffer de cómputo MoE se encoge) — verificar gratis comparando la línea de buffer del log.
- El draft MTP hereda la dosis (se construye del mismo GGUF) y tiene flags de colocación propios (`-ncmoed`, etc.) por si aprieta la VRAM.
- DFlash/DSpark existen como tipos en el build, pero DFlash es NO-GO en 4 GB ("not enough vram" reportado incluso en una 6 GB).

## 13. Anexo ronda 4: granularidad y sinergia (§13)

- Con 256 expertos (el doble que el hermano 30B) hay más redundancia → recortar debería costar menos calidad.
- La cabeza nextn del draft **también es MoE** → la dosis k abarata también el draft (doble ahorro) y puede bajar un poco su aceptación (a medir).
- Gate de calidad barato propuesto: perplexity sobre snippet ES fijo + sanity con temp 0 y semillas fijas + comparar k=8/6/4 en la misma sesión.
- Los sidecars (EAGLE3/DFlash) se entrenaron contra el modelo completo: anotar la aceptación por dosis k.

## 14. Anexo ronda 5: el cache de expertos calientes YA está en el build (§14)

- Descubrimiento [medido en el dump]: el build b11856 trae `--moe-cache-mib N` — un **cache en VRAM de los expertos que viven en CPU** — y viene **apagado (default 0)**. Por eso nadie lo había visto antes en las auditorías de defaults.
- Idea simple: en vez de mover más expertos a VRAM de forma permanente, se guarda una "lista de favoritos" en VRAM y los hits se sirven sin cruzar a la RAM.
- Números de comunidad: +60% en una 4050 de 6 GB, +34% en una 3080 (¡con nuestro modelo exacto!).
- Colisión de nombre a vigilar: en b11856 `-cmoe` es otra cosa (todo el MoE a CPU); el cache SOLO se controla con `--moe-cache-mib N`.
- Dosis nuevas de fase D: D-MEC-512 / D-MEC-768 / D-MEC-1024 sobre NCM37C4 (la VRAM del cache sale del mismo presupuesto que KV/buffers).
- Regla confirmada por terceros: `-ncmoe` cuenta capas desde la más alta; atención SIEMPRE en GPU; "encuentra el cliff y retrocede un paso".

## 15. Anexo ronda 6: números de producción, el riesgo del cache chico y MEC×MTP (§15)

- Producción real en 5070Ti con nuestro modelo: +36–40% con caches de **7–9 GiB**. Ojo: eso NO es transferible — nuestra 1650 solo tiene 1.2–1.7 GB libres; el rango honesto aquí es desconocido y lo mide la fase D.
- **Riesgo nuevo**: un cache DEMASIADO chico puede EMPEORAR las cosas (reporte: 600 MiB → −48% t/s, porque cada token expulsa lo que el siguiente necesita). → Regla: toda dosis MEC se compara A/B contra el control **D-MEC-0** (=sin cache) en la misma sesión; si pierde, se descarta.
- **Sinergia MEC×MTP super-aditiva** (dato de un fork no fusionado en GLM): MTP solo +28%; MTP con cache +51%. El verify releee los mismos expertos k+1 veces — con cache, esas relecturas salen de VRAM.
- Advertencia de build: existe un gate que puede excluir los batches chicos de verificación del cache; en b11856 no hay flag para eso → si el combo no rinde, primera hipótesis = ese gate; mitigación = build nuevo.
- Dosis fase D final: D-MEC-0 (control) → 512 → 1024 → 768.

## 16. Anexo ronda 7: MEC oficializada en v0.7.0 (§16)

- Las notas de la versión estable v0.7.0 (15-Oct-2026) oficializan el cache: `--moe-cache-mib`, "hasta ~2.2× de speedup cuando los expertos están offloadeados", cache compartible entre GPUs y parámetro API nuevo. Dirección upstream confirmada.
- La verificación especulativa (fase E) puede activar expertos extra en un MoE — con k-bajo + MEC ese coste extra baja → hipótesis de sinergia a medir tras el build nuevo.
- Enumeración real del build: b11856 solo tiene tipos de spec **sin draft** (ngram); los drafts llegan con el build nuevo (RUTA 0).

## 17. Anexo ronda 8: terceros con nuestra familia (§17)

- Una guía de producción con NUESTRO modelo exacto (UD-Q4_K_S) usa `--n-cpu-moe 31` + draft-mtp n4 + ctx 64k + KV q4_0 sin conflicto → valida que el knob convive con MTP en producción. Su número exacto no es transferible (su GPU no es una 1650).

## 18. Anexo ronda 9: -ot al detalle, la regla del offload y cierres (§18)

- `-ot/--override-tensor` EXISTE en b11856 [medido en el dump]: mueve tensores por regex. `-ot "exps=CPU"` manda todos los expertos ruteados a CPU y deja **el experto compartido, la atención, la KV y los buffers en GPU automáticamente** (el patrón "exps" no matchea "shexp").
- La primera regla que matchea gana; el formato oficial es una sola flag con comas.
- Contradicción resuelta: el dump dice "first N layers" y otra guía dice "highest" — para el 3.6 (40/40 capas MoE) da igual el orden; run autenticador cruzado barato para validar la comprensión.
- **La regla de oro del offload**: solo paga cuando modelo+ctx DESBORDA. Dato duro: en una máquina donde el modelo cabe, `-cmoe` global perdió **5×** (107.8 vs 21.7 t/s). En la 1650 el desborde es permanente → offload sí, pero **el mínimo necesario** (sweep del cliff, nunca global).
- Confirmado por 3 vías: auto-fit conservador cuesta (hasta +28% con dosis explícita en L4), fork ik_llama.cpp NO-GO con números (−1.5× TG / −2× PP con el 3.6), y el suelo VRAM del backbone (~2.4 GB con visión en una 1060 de 6 GB) es consistente con nuestra estimación.
- Piso físico de formato: **IQ1_S 1.66 GB es el mínimo GGUF posible** del 3.6 (el embedding de 248k y la lm_head untied no bajan de ~2 bits).
- Dosis fase D: SIN cambios.

## 19. Anexo ronda 10: auditoría de respaldo riguroso (§19)

- Re-verificación independiente punto a punto: **0 puntos refutados**; ~20 confirmados verbatim contra fuente primaria; el dump del build respaldado 1:1 por la manpage Debian (segunda fuente).
- Matices de precisión anotados: las cifras de REAP son del 480B-Coder; la discusión #30155 usa el arch `qwen4exp`.
- Dosis fase D intacta: NCM37C4 + D-MEC-0/512/1024 + escalera EXP6→4→3.

---

## 23. La primera corrida real completa (anexo §23 del completo): funcionó — y el doble de velocidad

- **La prueba salió bien de punta a punta**: 15 pruebas seguidas, 22 minutos, cero crashes. El error "HTTP 400" de antes quedó enterrado.
- **LA GRAN NOTICIA: el truco de usar menos expertos FUNCIONA.** Con 8 expertos ~18 t/s; bajando a 6, 5, 4, 3 y 2 la velocidad subió escalón por escalón hasta **35 t/s con k=2 (el doble)**. Si el truco no se hubiera aplicado, todo habría salido plano (como en el barrido-30 con la clave equivocada). La escalera ordenada ES la prueba.
- **¿Por qué el informe marcó casi todo "NO"?** Ninguna trampa es del modelo: (1) el programa pide un "certificado" en el log (la línea que dice cuántos expertos se usaron) y TU build nunca lo imprime — el portero pedía un papel que la oficina no emite; con `-lv 4` debería salir, y ahora además la dosis se autentica por 4 vías; (2) la GPU arrancó fría: el ancla (la referencia) midió 17.80 cuando el "8 expertos real" andaba en ~21 (cuatro pruebas lo confirman: EXP8 +15%, la recta de las filas estables da 21.7, el histórico da 21.53, y EXP10 sí frena contra la referencia sana). Por eso los "vs ancla" de esa corrida estaban inflados: corregidos son ~+41% (k=4), ~+55% (k=3), ~+71% (k=2).
- **Falsa alarma del "fit abortado"**: era el aviso benigno de "no auto-ajusto porque fijaste las capas a mano"; el server midió normal detrás. Corregido.
- **Calidad**: k=4 perfecto (3/3); k=6/5 se pone verboso y el examen se quedaba sin palabras (fallo del examen, no del modelo — ahora 128 tokens y distingue "se cortó" de "respondió mal"); k=3 ya falla cuentas (17×23 → 431); k=2 sopa de letras. **k=4 es la dosis competitiva con calidad intacta; k=2 muerto.**
- **Preliminares prometedores**: la cache de expertos (MEC) ganó en sesión (+38% con 1024 MiB, +31% con 768, contra su control) y el knob `-ot` clavó el método original (+0.9%) — dos caminos independientes al mismo número. Ojo: 1024 MiB de cache deja la VRAM al borde (3784/4096).
- **Siguiente paso humano**: copiar la v1.2.1 a `D:\ZLia\` y correr `BARRIDO-N1.bat` otra vez (~50-65 min, ahora 18 pruebas incluidos 2 stacks GANADOR+GANADOR); después, sanity manual de 20 prompts para fijar el k operativo.

---

## Cheatsheet operativa del nivel 1

- **Dosis**: `--override-kv <arch_real>.expert_used_count=int:K` (K = 6→4→3→2) + `--moe-cache-mib 512/1024` con control D-MEC-0.
- **Autenticador obligatorio**: línea de log `llm_load_print_meta: n_expert_used = N`.
- **Reglas**: k≥4 como zona segura; tool-calling en el sanity siempre; cache MEC nunca sin su control D-MEC-0; offload mínimo, nunca global.
- 📄 Detalle completo, fuentes y auditoría: [`nivel-1-recorte-expertos.md`](nivel-1-recorte-expertos.md)

---

## Idea del Director: modo dual de expertos (27-oct-2026, espejo simple del §25)

- **La idea**: dos perfiles de arranque — **TRABAJO** (programar: el equipo completo de 8 cocineros, es decir, no tocar nada) y **CHARLA** (4 cocineros: ~+41% de velocidad ya medida con el examen perfecto 3/3).
- **¿Por qué funciona? (el restaurante)**: el modelo tiene 256 cocineros y por cada palabra solo consulta a 8 (elegidos por el maître). Pedirle que consulte 4 = mitad de cocina por palabra = platos más rápido. Los 256 siguen en la cocina (RAM/VRAM casi no cambian — lo que se ahorra es trabajo, no memoria). El modelo aprendió a pensar con 8 opiniones: las cuentas y el código lo notan primero, la charla casi nunca — por eso charla=4 y programar=8.
- **¿Es un éxito si aguanta? SÍ** — es literalmente el objetivo del nivel 1 (velocidad arriba con calidad intacta). Ya casi lo tenemos: k=4 sacó 3/3 en el examen automático; falta la re-corrida v1.2.1 (~50-65 min) y el sanity manual de 20 prompts, que ahora hace de test del modo dual (chat y herramientas en k=4; código también en k=4, para decidir si aguanta o exige 8).
- **Cómo se cambia de perfil**: este build fija los expertos AL ARRANCAR (no se puede cambiar por mensaje). Opción recomendada: dos .bat (uno con override k=4, otro sin él) — cambiar de tarea = cerrar y reabrir (~1 min). Después, si apetece, llama-swap para automatizarlo (ya investigado, overhead <1%). Un parche para cambiarlo "en caliente" queda registrado como idea futura, fuera de la campaña.

---

## Los dos botones negros (27-oct-2026, espejo simple del §26)

- **Los dos .bat abren el MISMO restaurante**: mismo modelo, mismos 256 cocineros, mismas flags. Solo se diferencian en UNA palabra que le pasan al abridor: `trabajo` o `charla`.
- **CHARLA pega una nota en la puerta de la cocina**: "hoy, 4 cocineros por plato" (`--override-kv ...=int:4`). TRABAJO no pega nada: 8 es lo que ya dice el manual de fábrica — no se ordena lo que ya viene ordenado.
- **La nota se lee UNA sola vez al abrir la cocina**, no por mensaje. Por eso cambiar de modo = cerrar la ventana y abrir el otro .bat (~1 min).
- **El número vive en config.txt**: ¿quieres charla con 5 cocineros mañana? Editas UNA línea (`EXPERTOS_CHARLA = 5`) y los dos botones obedecen igual — jamás tienes que tocar los .bat.

---

## Juega con la escalera tú mismo (27-oct-2026, espejo simple del §27)

- **Ya lo tenías**: bajo cada respuesta, el chat de la casa imprime una línea con **tok/s** — ese es el número del experimento (la velocidad a la que ESCRIBE, no el "1er tok" que es el arranque).
- **Nuevo**: el **t/s en vivo en el título de la ventana** mientras escribe, y el comando **/modo 8** o **/modo 4** para etiquetar qué botón abriste — /stats te compara los modos lado a lado ("modo 4: 33.9 tok/s medio") y /guardar lo deja todo en el transcript.
- **Juego limpio (5 reglas)**: misma pregunta · respuestas de 200 palabras · descarta la primera (GPU fría) · compara solo el "tok/s" de escritura · etiqueta con /modo y /guardar al cerrar cada sesión.
- **Para bajar a 6, 5 o 3 expertos**: edita `EXPERTOS_CHARLA = K` en config.txt y abre CHARLA. Lo ya medido: k=4 (+41%) es la dosis buena; k=3 ya falla cuentas y k=2 es sopa de letras.
- **Honestidad**: esto es tu medición informal; el barrido formal (BARRIDO-N1.bat, ~50-65 min) sigue siendo el juez de N1.

---

## El velocímetro y el día a día: ¿15 t/s significa receta rota? (27-oct-2026, espejo simple del §28)

- **La pregunta**: "la receta completa de trabajo me va a 15 t/s, ¿hay algo mal? ¿Usaste la original, la de las pruebas?"
- **Respuesta corta: la receta ES la original.** Se auditaron las piezas una por una contra el comando REAL que midió el laboratorio: todas las flags de velocidad idénticas (`-ngl 99`, `-cmoe`, `-c 16384`, `-fa`, KV q8_0, `-t 4`, `--prio 2`, `-lm none`) y el único extra (`-ub 1024 -b 4096`) también es campeón medido (ORO-UB1K). Además un test automático (T06) re-comprueba en cada versión que el comando es exactamente el probado — nada se cuela.
- **¿Y por qué 15 entonces? Mismo restaurante, otro día.** En el laboratorio la MISMA receta con 8 cocineros marcó entre 17.4 y 21.5 según la sesión. En casa el velocímetro del chat es un cronómetro que cuenta TODAS las pausas: navegador abierto, RAM al límite (el modelo ocupa 14.3 de los 16 GB — si Windows empieza a mover trozos al pagefile, todo se traba: mira la memoria en el Administrador de tareas), GPU caliente, plan de energía "Equilibrado".
- **La prueba que decide (mejor que cualquier número suelto): el RATIO.** Misma pregunta, misma sesión: TRABAJO → /modo 8 → anota su tok/s → cierra todo → CHARLA → /modo 4 → misma pregunta → anota. **Sano = charla ~1.5-1.6 veces más rápido que trabajo.** Si charla no se separa de trabajo, eso sí es raro: avisa (y mira el banner del server, que dice qué perfil y qué config.txt usó).
- **Para chatear rápido: CHARLA.** TRABAJO (8 cocineros) es para código y tareas finas. Ver trabajo a ~15 y charla a ~24 es exactamente el comportamiento esperado de la receta original en un día normal — no hay nada que reparar.

---

## El mecánico: DIAGNOSTICO-VELOCIDAD.bat (27-oct-2026, espejo simple del §29)

- **¿Para qué?** Tu pregunta era "¿debería ir a más t/s con la receta completa?". Este botón nuevo responde con evidencia en ~1 minuto, así: abre el modelo con su .bat de siempre → doble click en **DIAGNOSTICO-VELOCIDAD.bat** → **no chatees ese minuto** → lee el veredicto (queda guardado en un informe).
- **Las 4 estaciones del taller**: **(1) revisa la orden de trabajo VIVA** — lee el comando real que tiene abierto el server y lo compara pieza por pieza con la receta original de config.txt; de paso te dice con cuántos cocineros arrancó (si editaste config.txt después de abrir, te avisa). **(2) mide con el MISMO cronómetro del laboratorio** — las mismas 4 preguntas, el mismo método: un número comparable con 17.4-21.5 (8 cocineros) y 24-30 (4 cocineros). **(3) mira el día** — RAM libre, GPU caliente, relojes bajos, plan de energía Equilibrado. **(4) el veredicto**: **NORMAL** (la receta va como debe; para más t/s → CHARLA) · **BAJO** (algo del día frena: te señala el culpable) · **GRIS** (haz el test del ratio) · **HUELE-A-4** (¿abriste charla?).
- **La respuesta corta a tu pregunta**: con 8 cocineros NO debería ir a más — ese es el techo físico del rig, medido. Para MÁS t/s está el modo dual (CHARLA, 4 cocineros: banda 24-30).
- **Lo que NO hace**: no toca el server, no cambia configs, no usa flags raras. Solo mira, mide y opina con los números del laboratorio. Si algún día sale BAJO sin culpables, se anota en el repo — ese dato alimenta el barrido formal.
