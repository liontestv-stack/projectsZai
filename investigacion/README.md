# INVESTIGACIÓN — Los 5 niveles de velocidad (Qwen3.6-35B-A3B en el rig)

Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB · Modelo actual: APEX-I-MINI (14.27 GB) · Plan de descarga: unsloth UD-IQ3_XXS (14.07 GB, con nextn dentro — nombre nuevo tras renombrado del repo, ver N2 §16)

Etiquetas usadas en todos los archivos: **[F]** = verificado en fuente externa · **[M]** = medido en ESTE rig (sweeps/barridos propios) · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy.

Cada nivel tiene anexos por rondas de investigación (ronda 1 = cuerpo principal, ronda 2-9 = ANEXOS al final del archivo). Estado de la ronda 9 (2026-10-26, foco Director: nivel 1):

| # | Archivo | Tema | Hallazgo mayor de la ronda 9 |
|---|---------|------|------------------------------|
| 1 | [`nivel-1-recorte-expertos.md`](nivel-1-recorte-expertos.md) | Recorte de expertos en runtime (fase D EXP) | **`-ot/--override-tensor` al detalle** (existe en b11856 [M]; `exps=CPU` no matchea `shexp` → shared queda en GPU; comas oficiales); **regla del offload**: `-cmoe` REGRESA 5x si el modelo cabe (107.8 vs 21.7 t/s) → offload mínimo, nunca full; fork ik_llama NO-GO (−1.5x TG vs mainline con el 3.6); run autenticador cruzado `-ot` ≡ NCM37C4 propuesto |
| 2 | [`nivel-2-cuant-ligero.md`](nivel-2-cuant-ligero.md) | Cuant más ligero ya hecho (sin requant local) | **Piso físico de formato del 3.6**: IQ1_S 1.66 GB es el mínimo GGUF posible (embedding 248k + lm_head untied forzan ≥2-bit); REAP-90 NO-GO re-confirmado por su propio autor ("meme", "mostly incoherent"); UD-IQ3_XXS sigue siendo el objetivo (SHA256 `36f9ec0e…` cerrado) |
| 3 | [`nivel-3-eficiencia-simple.md`](nivel-3-eficiencia-simple.md) | Eficiencia simple (flags, cache, TTFT) | **Muerte con fecha de los alias**: PR #28334 (09-Sep-2026) elimina `--no-mmap`/`--mlock` → b11901 los rechaza en duro; traducción `-lm` pasa a OBLIGATORIA tras RUTA 0 (b11901 binario + cudart sigue vigente); **op-offload** explica el prefill híbrido: `-ub` grande amortiza copias CPU→GPU (380→2091 t/s) |
| 4 | [`nivel-4-memoria-vram-ram.md`](nivel-4-memoria-vram-ram.md) | Presupuesto de memoria al límite (VRAM/RAM) | **Suelo VRAM del backbone validado por terceros** (Omni-30B en 1060 6GB: ~2.4 GB con visión ≈ 1.5 GB sin, consistente con §8); regla del desborde permanente en 4GB (el offload no se "gradúa"); soporte externo a `-lm none` (RAM 98%→71%) |
| 5 | [`nivel-5-draft-externo-gpu.md`](nivel-5-draft-externo-gpu.md) | Draft externo en GPU (fase S especulativa) | **MTP en producción ajena con la escalera -ncmoe completa**: L4 24GB auto-fit 63.3 → `-ncmoe 0` 80.9 t/s → 90.6-98.8 con MTP n2 (+~45%); acceptance 80%+ estable en 12GB; fork ik cerrado también para draft; sidecars SHA256 de ronda 8 intactos |

## Orden de lectura operativa

1. Empezar por el **veredicto ejecutivo** (§0) de cada archivo.
2. La línea de ejecución en el rig hoy: **RUTA 0 simplificada = descargar 2 zips de b11901** (binario CUDA 12.4 + cudart DLLs — sin compilar, N3 §16; sin el cudart la GPU queda dormida) → descargar UD-IQ3_XXS (14.07 GB, SHA256 `36f9ec0e…` cerrado, N2 §18) + DSpark Q4_K_M (307 MB, SHA256 `a3542c05…`, N5 §15) → fase E (MTP-n2) → fase S2 (DSpark n2/n3, conf-min como A/B) y S2b (DFlash-n2); paralelo sin RUTA 0: `-ctxcp 4` + `--moe-cache-mib 512` (con control D-MEC-0) sobre NCM37C4.
3. Reglas de medición (N3 §13): mediana de 3 corridas, baseline matcheado por corrida, no perseguir deltas <5pp.
4. Traducciones obligatorias de comandos de internet a b11856: `--no-mmap`→`-lm none`, `--mlock`→`-lm mmap+mlock`, `--draft-max`→`--spec-draft-n-max` (N3 §14, N5 §13); y fijar SIEMPRE `--spec-draft-n-max` + `--spec-draft-p-min` explícitos (defaults de b11856: 16 y 0.75 ≠ master 3 y 0.00 — N3 §15). Tras RUTA 0 (b11901) los alias `--no-mmap`/`--mlock` mueren en duro (PR #28334, 09-Sep-2026 — N3 §17): la traducción `-lm` pasa a obligatoria.

**Regla del proyecto:** ninguna flag usada en comandos/configs puede salir de `InformacionCritica/llama-flags.txt` (dump b11856). Si una flag no está ahí, no existe.
