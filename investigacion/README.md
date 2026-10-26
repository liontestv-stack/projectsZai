# INVESTIGACIÓN — Los 5 niveles de velocidad (Qwen3.6-35B-A3B en el rig)

Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB · Modelo actual: APEX-I-MINI (14.27 GB) · Plan de descarga: unsloth UD-IQ3_XXS (14.07 GB, con nextn dentro — nombre nuevo tras renombrado del repo, ver N2 §16)

Etiquetas usadas en todos los archivos: **[F]** = verificado en fuente externa · **[M]** = medido en ESTE rig (sweeps/barridos propios) · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy.

Cada nivel tiene anexos por rondas de investigación (ronda 1 = cuerpo principal, ronda 2-7 = ANEXOS al final del archivo). Estado de la ronda 7 (2026-10-26):

| # | Archivo | Tema | Hallazgo mayor de la ronda 7 |
|---|---------|------|------------------------------|
| 1 | [`nivel-1-recorte-expertos.md`](nivel-1-recorte-expertos.md) | Recorte de expertos en runtime (fase D EXP) | MEC OFICIALIZADA en v0.7.0 (15-Oct): notas de release con "~2.2x" (#29887), cache multi-GPU (#30112); coste MoE de la verificación especulativa (activa expertos extra → sinergia k-bajo × spec a medir); b11856 solo tiene spec sin draft (ngram-*) |
| 2 | [`nivel-2-cuant-ligero.md`](nivel-2-cuant-ligero.md) | Cuant más ligero ya hecho (sin requant local) | **Árbol del repo MTP verificado byte a byte hoy**: UD-IQ3_XXS.gguf = 14,069,266,720 B ✓ (SHA256 36f9ec0e… valida); UD-IQ3_S de este repo = 15.35 GB (lleva nextn; el 13.68 GB de ronda 5 era del 3.5 sin nextn); GSQ-RCO sigue sin 3.6 |
| 3 | [`nivel-3-eficiencia-simple.md`](nivel-3-eficiencia-simple.md) | Eficiencia simple (flags, cache, TTFT) | **Timeouts intermitentes con spec #23268** (<1%, streaming colgado con conexión viva → timeout cliente + retry, primer A/B = spec off); **drift de salida del MTP medido** (7/50 idénticas, 34 vs 33 resueltos = ruido → MTP ON agentes, OFF evals); defaults b11856 ≠ master: n-max 16 y p-min 0.75 [M] |
| 4 | [`nivel-4-memoria-vram-ram.md`](nivel-4-memoria-vram-ram.md) | Presupuesto de memoria al límite (VRAM/RAM) | **El draft abre un SEGUNDO presupuesto**: #23472 (draft ctx default al n_ctx nativo → 990 GB) y #26038 (sobre-reserva ~800 MiB, ctx usable /2); dosis defensivas: `-cd` y `-ctkd/-ctvd` existen YA en b11856 [M]; fallback silencioso upstream #26432 = análogo de nuestro Sysmem Fallback |
| 5 | [`nivel-5-draft-externo-gpu.md`](nivel-5-draft-externo-gpu.md) | Draft externo en GPU (fase S especulativa) | **DSpark OFICIAL de RedHatAI para el 3.6-35B-A3B** (safetensors 0.95B, 19-Jul) → S2 con upstream oficial; **LiliCorr fusionada** (#30506, mejora DFlash mismo spec-type); MTP adaptativo #27210 aún NO fusionado; **b11856 no tiene NINGÚN draft aprendido [M] → RUTA 0 es el GATE de toda la fase S/E** |

## Orden de lectura operativa

1. Empezar por el **veredicto ejecutivo** (§0) de cada archivo.
2. La línea de ejecución en el rig hoy: **RUTA 0 (git pull + recompilar) es el GATE de toda la fase E/S** — b11856 no tiene eagle3/dflash/dspark/mtp [M dump ronda 7] → descargar UD-IQ3_XXS (14.07 GB, nombre nuevo) → fase E (MTP-n2) → fase S2 (DSpark Q4_K_M 307 MB n2/n3, conf-min como A/B) y S2b (DFlash-n2 421 MB); paralelo sin RUTA 0: `-ctxcp 4` + `--moe-cache-mib 512` (con control D-MEC-0) sobre NCM37C4.
3. Reglas de medición (N3 §13): mediana de 3 corridas, baseline matcheado por corrida, no perseguir deltas <5pp.
4. Traducciones obligatorias de comandos de internet a b11856: `--no-mmap`→`-lm none`, `--mlock`→`-lm mmap+mlock`, `--draft-max`→`--spec-draft-n-max` (N3 §14, N5 §13); y fijar SIEMPRE `--spec-draft-n-max` + `--spec-draft-p-min` explícitos (defaults de b11856: 16 y 0.75 ≠ master 3 y 0.00 — N3 §15).

**Regla del proyecto:** ninguna flag usada en comandos/configs puede salir de `InformacionCritica/llama-flags.txt` (dump b11856). Si una flag no está ahí, no existe.
