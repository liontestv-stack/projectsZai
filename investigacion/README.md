# INVESTIGACIÓN — Los 5 niveles de velocidad (Qwen3.6-35B-A3B en el rig)

Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB · Modelo actual: APEX-I-MINI (14.27 GB) · Plan de descarga: unsloth UD-IQ3_XXS-MTP (14.07 GB)

Etiquetas usadas en todos los archivos: **[F]** = verificado en fuente externa · **[M]** = medido en ESTE rig (sweeps/barridos propios) · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy.

Cada nivel tiene anexos por rondas de investigación (ronda 1 = cuerpo principal, ronda 2-5 = ANEXOS al final del archivo). Estado de la ronda 5 (2026-10-26):

| # | Archivo | Tema | Hallazgo mayor de la ronda 5 |
|---|---------|------|------------------------------|
| 1 | [`nivel-1-recorte-expertos.md`](nivel-1-recorte-expertos.md) | Recorte de expertos en runtime (fase D EXP) | **`--moe-cache-mib` YA existe en b11856** (default 0 = apagado): pool LRU de expertos CPU en VRAM; +60% reportado con este mismo modelo en 4050 6GB (PR #29887). Dosis D-MEC-512/768/1024 |
| 2 | [`nivel-2-cuant-ligero.md`](nivel-2-cuant-ligero.md) | Cuant más ligero ya hecho (sin requant local) | Inventario MTP al byte completo: **UD-IQ2_M (11.88 GB) y UD-IQ1_M (11.37 GB, ancla 86.9% top-1)** nuevos; mmproj/imatrix NO descargar; GSQ-RCO crece (aún sin 3.6) |
| 3 | [`nivel-3-eficiencia-simple.md`](nivel-3-eficiencia-simple.md) | Eficiencia simple (flags, cache, TTFT) | b11856 auditado vs upstream: YA tiene fixes FA-race y prompt-cache; solo le falta el fix Jinja b11869 (actualizar solo si tool-calls fallan). **Protocolo de medición: mediana de 3, varianza 9.4pp [F]** |
| 4 | [`nivel-4-memoria-vram-ram.md`](nivel-4-memoria-vram-ram.md) | Presupuesto de memoria al límite (VRAM/RAM) | MEC entra al presupuesto VRAM (3 competidores por los 1.2-1.7 GB libres); `-lm none` con número comunitario (RAM 98→71% mismo t/s); mmproj fuera del disco |
| 5 | [`nivel-5-draft-externo-gpu.md`](nivel-5-draft-externo-gpu.md) | Draft externo en GPU (fase S especulativa) | **Estudio controlado v4 en 3090 sobre nuestro modelo exacto: DFlash-n2 +26.3% > MTP-n2 +22.7%**; draft externo denso (0.8B) −73% = S6 eliminada; n2 domina a n4 |

## Orden de lectura operativa

1. Empezar por el **veredicto ejecutivo** (§0) de cada archivo.
2. La línea de ejecución en el rig hoy: `-ctxcp 4` + `--moe-cache-mib 512` sobre NCM37C4 → descargar UD-IQ3_XXS-MTP → fase E (MTP-n2) → fase S2 (DFlash-n2, sidecar 421 MB).
3. Reglas de medición (N3 §13): mediana de 3 corridas, baseline matcheado por corrida, no perseguir deltas <5pp.

**Regla del proyecto:** ninguna flag usada en comandos/configs puede salir de `InformacionCritica/llama-flags.txt` (dump b11856). Si una flag no está ahí, no existe.
