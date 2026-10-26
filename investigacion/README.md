# INVESTIGACIÓN — Los 5 niveles de velocidad (Qwen3.6-35B-A3B en el rig)

Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB · Modelo actual: APEX-I-MINI (14.27 GB) · Plan de descarga: unsloth UD-IQ3_XXS (14.07 GB, con nextn dentro — nombre nuevo tras renombrado del repo, ver N2 §16)

Etiquetas usadas en todos los archivos: **[F]** = verificado en fuente externa · **[M]** = medido en ESTE rig (sweeps/barridos propios) · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy.

Cada nivel tiene anexos por rondas de investigación (ronda 1 = cuerpo principal, ronda 2-10 = ANEXOS al final del archivo). Estado de la ronda 10 (2026-10-26, foco Director: auditoría de respaldo riguroso de los 5 niveles): 0 puntos refutados, ~50 re-verificados contra fuente primaria (40+ búsquedas frescas), dump b11856 respaldado 1:1 por la manpage Debian (segunda fuente), 5 matices anotados.

| # | Archivo | Tema | Respaldo riguroso de la ronda 10 (auditoría) |
|---|---------|------|------------------------------|
| 1 | [`nivel-1-recorte-expertos.md`](nivel-1-recorte-expertos.md) | Recorte de expertos en runtime (fase D EXP) | **AUDITORÍA §19**: MoE-Spec (95% @2.0×) y REAP (97.6/96.7, en el 480B-Coder) confirmados verbatim; #5114, #20757, #29887+#30112, v0.7.0 (~2.2x), ik #1699, #30426, Doctor-Shotgun y llmkube verbatim; `qwen4exp` como arch real de #30155; dosis fase D intacta |
| 2 | [`nivel-2-cuant-ligero.md`](nivel-2-cuant-ligero.md) | Cuant más ligero ya hecho (sin requant local) | **AUDITORÍA §20**: localbench (64 cuants/6 uploaders, unsloth 14/26, mudler nunca, tool-calling KL 0.177, IQ1_M 86.9%) verbatim; restricciones MTP (-np>1/mmproj) verbatim; headroom MTP ~1 GB respaldado por la guía específica del 3.6; CUDA 13.2 gibberish verbatim; GSQ-RCO sigue sin 3.6 |
| 3 | [`nivel-3-eficiencia-simple.md`](nivel-3-eficiencia-simple.md) | Eficiencia simple (flags, cache, TTFT) | **AUDITORÍA §18**: #21831 (híbridos-exclusivo + repro viciado) y particula.tech verbatim; #20574 (TTFT −93%), #25345, #23268, xhinker, vLLM #38182 y thc1006 verbatim; muerte de alias (-lm) y cliff 5090 verbatim en openclawdc; defaults b11856 ≠ master re-anclados; protocolo curl y mediana-de-3 intactos |
| 4 | [`nivel-4-memoria-vram-ram.md`](nivel-4-memoria-vram-ram.md) | Presupuesto de memoria al límite (VRAM/RAM) | **AUDITORÍA §18**: #23472/#26432 verbatim; **#26038 CERRADO not-planned 09-Oct** → no esperar fix, medir buffer del draft con el log; spill silencioso WDDM triple-fuente (#9964 + openclawdc + guías); suelo backbone (2.4 GB) y -lm none (98%→71%) verbatim; orden de dosis v5 intacto |
| 5 | [`nivel-5-draft-externo-gpu.md`](nivel-5-draft-externo-gpu.md) | Draft externo en GPU (fase S especulativa) | **AUDITORÍA §17**: mecánica DSpark (Markov in-graph) verbatim en docs master; card williamliao verbatim (DFlash-7 rey de código, accept sola no basta); forma n2>n3>n4 TRIPLE-fuente (v4 + MXFP4 + 27B); linaje 35B = DFlash+heads (#26230) y soporte vía PR #26275 → RUTA 0 sigue siendo el gate; dosis v6 intacta |

## Orden de lectura operativa

1. Empezar por el **veredicto ejecutivo** (§0) de cada archivo.
2. La línea de ejecución en el rig hoy: **RUTA 0 simplificada = descargar 2 zips de b11901** (binario CUDA 12.4 + cudart DLLs — sin compilar, N3 §16; sin el cudart la GPU queda dormida) → descargar UD-IQ3_XXS (14.07 GB, SHA256 `36f9ec0e…` cerrado, N2 §18) + DSpark Q4_K_M (307 MB, SHA256 `a3542c05…`, N5 §15) → fase E (MTP-n2) → fase S2 (DSpark n2/n3, conf-min como A/B) y S2b (DFlash-n2); paralelo sin RUTA 0: `-ctxcp 4` + `--moe-cache-mib 512` (con control D-MEC-0) sobre NCM37C4.
3. Reglas de medición (N3 §13): mediana de 3 corridas, baseline matcheado por corrida, no perseguir deltas <5pp.
4. Traducciones obligatorias de comandos de internet a b11856: `--no-mmap`→`-lm none`, `--mlock`→`-lm mmap+mlock`, `--draft-max`→`--spec-draft-n-max` (N3 §14, N5 §13); y fijar SIEMPRE `--spec-draft-n-max` + `--spec-draft-p-min` explícitos (defaults de b11856: 16 y 0.75 ≠ master 3 y 0.00 — N3 §15). Tras RUTA 0 (b11901) los alias `--no-mmap`/`--mlock` mueren en duro (PR #28334, 09-Sep-2026 — N3 §17): la traducción `-lm` pasa a obligatoria.

**Regla del proyecto:** ninguna flag usada en comandos/configs puede salir de `InformacionCritica/llama-flags.txt` (dump b11856). Si una flag no está ahí, no existe.
