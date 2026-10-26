# INVESTIGACIÓN — Los 5 niveles de velocidad (Qwen3.6-35B-A3B en el rig)

Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB · Modelo actual: APEX-I-MINI (14.27 GB) · Plan de descarga: unsloth UD-IQ3_XXS (14.07 GB, con nextn dentro — nombre nuevo tras renombrado del repo, ver N2 §16)

Etiquetas usadas en todos los archivos: **[F]** = verificado en fuente externa · **[M]** = medido en ESTE rig (sweeps/barridos propios) · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy.

Cada nivel tiene anexos por rondas de investigación (ronda 1 = cuerpo principal, ronda 2-6 = ANEXOS al final del archivo). Estado de la ronda 6 (2026-10-26):

| # | Archivo | Tema | Hallazgo mayor de la ronda 6 |
|---|---------|------|------------------------------|
| 1 | [`nivel-1-recorte-expertos.md`](nivel-1-recorte-expertos.md) | Recorte de expertos en runtime (fase D EXP) | MEC con números de producción sobre nuestro modelo exacto (+36-40% con caches de 7-9 GiB en 5070Ti); **el cache CHICO puede REGRESAR** (600 MiB → −48% en un caso real) → dosis con control D-MEC-0 obligatorio; **sinergia MEC×MTP super-aditiva** (+28% → +51% en GLM); b11856 sin flag del batch-gate de spec |
| 2 | [`nivel-2-cuant-ligero.md`](nivel-2-cuant-ligero.md) | Cuant más ligero ya hecho (sin requant local) | **El repo MTP RENOMBRÓ sus archivos**: el objetivo ahora es `UD-IQ3_XXS.gguf` (mismos 14,069,266,720 bytes, SHA256 36f9ec0e… valida); TODA la escalera lleva nextn dentro; GSQ-RCO ya probado en familia Qwen (3.8-27B a 11.8 GB) — aún sin 3.6 |
| 3 | [`nivel-3-eficiencia-simple.md`](nivel-3-eficiencia-simple.md) | Eficiencia simple (flags, cache, TTFT) | **#21831 sigue sin fix y su workaround (`-cpent`) NO existe en b11856** → RUTA 0 o parche si el repro aparece; flags muertas `--no-mmap/--mlock` confirmadas por 2 fuentes (traducción: `-lm`); el MTP degrada el hit-rate del prefix cache 92→71% [F] → protocolo E mide TTFT |
| 4 | [`nivel-4-memoria-vram-ram.md`](nivel-4-memoria-vram-ram.md) | Presupuesto de memoria al límite (VRAM/RAM) | Presupuesto con datos de producción: L4 cabe Q4_K_XL full-GPU con `-ub 64 -b 512` (palanca presupuestaria real); MEC a escala usa 7-9 GiB (techo del nivel); el thrash del cache chico entra como riesgo presupuestario; fix upstream DRY (rig no expuesto [M]) |
| 5 | [`nivel-5-draft-externo-gpu.md`](nivel-5-draft-externo-gpu.md) | Draft externo en GPU (fase S especulativa) | **EXISTE sidecar DSpark para el 3.6-35B-A3B** (IQ4_XS 286 MB / Q4_K_M 307 MB) **con fix de hybrid-GDN state commit que DFlash NO tiene** → S2 = DSpark preferente; lección thc1006: nunca auto-convertir el draft (−44.6% → +26.3%); MTP en L4 = +45-57% (cuanto menos bandwidth, más paga) |

## Orden de lectura operativa

1. Empezar por el **veredicto ejecutivo** (§0) de cada archivo.
2. La línea de ejecución en el rig hoy: `-ctxcp 4` + `--moe-cache-mib 512` (con control D-MEC-0) sobre NCM37C4 → descargar UD-IQ3_XXS (14.07 GB, nombre nuevo) → fase E (MTP-n2) → fase S2 (DSpark Q4_K_M 307 MB n2/n3, fix GDN) y S2b (DFlash-n2 421 MB).
3. Reglas de medición (N3 §13): mediana de 3 corridas, baseline matcheado por corrida, no perseguir deltas <5pp.
4. Traducciones obligatorias de comandos de internet a b11856: `--no-mmap`→`-lm none`, `--mlock`→`-lm mmap+mlock`, `--draft-max`→`--spec-draft-n-max` (N3 §14, N5 §13).

**Regla del proyecto:** ninguna flag usada en comandos/configs puede salir de `InformacionCritica/llama-flags.txt` (dump b11856). Si una flag no está ahí, no existe.
