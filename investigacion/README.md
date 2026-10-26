# INVESTIGACIÓN — Los 5 niveles de velocidad (Qwen3.6-35B-A3B en el rig)

Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB · Modelo actual: APEX-I-MINI (14.27 GB) · Plan de descarga: unsloth UD-IQ3_XXS (14.07 GB, con nextn dentro — nombre nuevo tras renombrado del repo, ver N2 §16)

Etiquetas usadas en todos los archivos: **[F]** = verificado en fuente externa · **[M]** = medido en ESTE rig (sweeps/barridos propios) · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy.

Cada nivel tiene anexos por rondas de investigación (ronda 1 = cuerpo principal, ronda 2-8 = ANEXOS al final del archivo). Estado de la ronda 8 (2026-10-26):

| # | Archivo | Tema | Hallazgo mayor de la ronda 8 |
|---|---------|------|------------------------------|
| 1 | [`nivel-1-recorte-expertos.md`](nivel-1-recorte-expertos.md) | Recorte de expertos en runtime (fase D EXP) | Punto de datos de producción de terceros: `--n-cpu-moe 31` con NUESTRA familia exacta (UD-Q4_K_S) convive con draft-mtp + KV q4_0 sin conflicto (no transferible a 4GB, [N/D] su VRAM) |
| 2 | [`nivel-2-cuant-ligero.md`](nivel-2-cuant-ligero.md) | Cuant más ligero ya hecho (sin requant local) | **SHA256 de descarga AUTORITATIVO y cerrado**: UD-IQ3_XXS.gguf = 14,069,266,720 B, SHA256 `36f9ec0e4c77…7150` verificado hoy contra `lfs.oid` de la API HF; gotcha documentado: `blobId` de la API es SHA-1, autenticar SIEMPRE con `lfs.oid` |
| 3 | [`nivel-3-eficiencia-simple.md`](nivel-3-eficiencia-simple.md) | Eficiencia simple (flags, cache, TTFT) | **RUTA 0 SIN COMPILAR**: binarios precompilados hasta **b11901** (45 builds sobre b11856, trae todo v0.7.0); GOTCHA: descargar TAMBIÉN `cudart-*.zip` o la GPU queda dormida (#17812); config de producción de la familia verificada (draft-mtp n4 + ctx 64k + KV q4_0) |
| 4 | [`nivel-4-memoria-vram-ram.md`](nivel-4-memoria-vram-ram.md) | Presupuesto de memoria al límite (VRAM/RAM) | Referencia de producción de la pila completa (KV cuant + ctx acotado + draft + MoE parcial CPU coexisten estables); plan de medición 1650 consolidado con las 3 rondas previas |
| 5 | [`nivel-5-draft-externo-gpu.md`](nivel-5-draft-externo-gpu.md) | Draft externo en GPU (fase S especulativa) | **Sidecar S2 al byte con SHA256**: DSpark Q4_K_M = 307,213,088 B, `a3542c05…8cab`; RUTA 0 con blanco concreto = **b11901**; dato 4GB/Turing+spec: [N/D] — la 1650 será dato propio del barrido |

## Orden de lectura operativa

1. Empezar por el **veredicto ejecutivo** (§0) de cada archivo.
2. La línea de ejecución en el rig hoy: **RUTA 0 simplificada = descargar 2 zips de b11901** (binario CUDA 12.4 + cudart DLLs — sin compilar, N3 §16; sin el cudart la GPU queda dormida) → descargar UD-IQ3_XXS (14.07 GB, SHA256 `36f9ec0e…` cerrado, N2 §18) + DSpark Q4_K_M (307 MB, SHA256 `a3542c05…`, N5 §15) → fase E (MTP-n2) → fase S2 (DSpark n2/n3, conf-min como A/B) y S2b (DFlash-n2); paralelo sin RUTA 0: `-ctxcp 4` + `--moe-cache-mib 512` (con control D-MEC-0) sobre NCM37C4.
3. Reglas de medición (N3 §13): mediana de 3 corridas, baseline matcheado por corrida, no perseguir deltas <5pp.
4. Traducciones obligatorias de comandos de internet a b11856: `--no-mmap`→`-lm none`, `--mlock`→`-lm mmap+mlock`, `--draft-max`→`--spec-draft-n-max` (N3 §14, N5 §13); y fijar SIEMPRE `--spec-draft-n-max` + `--spec-draft-p-min` explícitos (defaults de b11856: 16 y 0.75 ≠ master 3 y 0.00 — N3 §15).

**Regla del proyecto:** ninguna flag usada en comandos/configs puede salir de `InformacionCritica/llama-flags.txt` (dump b11856). Si una flag no está ahí, no existe.
