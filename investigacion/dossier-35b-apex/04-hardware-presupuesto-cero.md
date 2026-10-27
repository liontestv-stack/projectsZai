# 04 — Análisis del rig: i3-10100F + GTX 1650 + 16GB RAM + SSD 500GB (presupuesto $0)

> ⚠ Doc original (mañana 2026-10-24); §1-§3 y §5 corregidos por auditoría (tamaños reales + techo corregido). Guía vigente: [../../InformacionCritica/docs/RUTAS.md](../../InformacionCritica/docs/RUTAS.md).

## 1. Radiografía del hardware

| Componente | Specs | Implicación para el proyecto |
|------------|-------|------------------------------|
| **CPU** Intel i3-10100F (Comet Lake, 2020) | 4C/8T, 3.6-4.3 GHz, AVX2, max DDR4-2666 | 4 hilos físicos para expertos en RAM. Ancho de banda RAM = **~41.6 GB/s** (dual channel) → EL cuello de botella maestro |
| **GPU** GTX 1650 4GB (Turing TU117) | 4GB GDDR5/GDDR6, ~128-192 GB/s VRAM, CUDA cc 7.5 | Suficiente para: atención + KV cache + shared experts + capas MTP + buffers. NO para los expertos (no caben) |
| **RAM** 16GB DDR4-2666 | dual channel | Presupuesto real: ~13 GB usable tras OS. Modelo MINI = **14.27 GB reales** → **al filo: pageouts probables** — pagefile en el SSD dedicado; mmap mantiene residente lo caliente |
| **SSD** 500GB (dedicado al proyecto) | | Descarga de 13 GB holgada; mmap acelera recargas; espacio sobra para 2-3 variantes + experimentos |

## 2. Presupuesto de memoria (el cálculo que decide todo)

### RAM (16 GB)
```
  OS Windows + servicios          ~2.5-3.5 GB
  Expertos APEX-I-MINI en RAM     ~11.5-12.5 GB  (de los 14.27 GB reales del archivo)
  Cola/mmap page cache            compartido con lo anterior
  ─────────────────────────────────────────────
  TOTAL                           ~14-16 GB  → al filo: pageouts probables
```
Reglas de supervivencia: cerrar navegador/apps pesadas al servir el modelo; NO usar `--mlock` (necesitaríamos ~12 GB bloqueados → OOM); mantener mmap (default) para que el SO pagee expertos fríos; pagefile en el SSD dedicado (absorbe el overflow de los 14.27 GB).

### VRAM (4 GB)
```
  Atención (40 capas) + shared + output + embd   ~1.2-1.8 GB
  KV cache (10 capas Gated Attention; DeltaNet=estado recurrente) q8_0 @16K  ~0.3-0.6 GB
  Buffers de cómputo (-b 1024 -ub 256)           ~0.3-0.5 GB
  Capa MTP + overhead especulativo               ~0.3-0.5 GB
  ─────────────────────────────────────────────
  TOTAL ~2.1-3.4 GB → cabe; si se pasa, subir -ncmoe / bajar -ub
```

## 3. CORREGIDO (2026-10-24, tras la corrección del Director): 16 t/s NO era el techo

- Física real: tg en MoE = leer SOLO los expertos activos (~1.0-1.2 GB/token en APEX Mini) → con ~38 GB/s útiles el techo base es **~25-35 t/s**, no 20. La lectura anterior ("techo ~20 t/s") era errónea.
- Causa 2 de los 16 t/s: el archivo real (14.27 GB) sobre 16 GB de RAM → pageouts; el disco roba t/s. Mitigación: pagefile en el SSD dedicado + sweep de `-ncmoe`.
- El multiplicador que no gasta ancho de banda: **draft-mtp** — un pase forward lee los expertos UNA vez y verifica N tokens. PR #22673 (fusionado 2026-05-16, verificado) declara **"more than 2x speed-up over baseline with ~75% acceptance"**.
- Lo que NO se puede: superar el ancho de banda de la DDR4 (sin cambiar RAM/CPU) — pero el techo real está por encima de lo que necesitamos.
- Expectativa honesta corregida: base **14-24 t/s** tras sweep (según pageouts) → **28-36 t/s** con draft-mtp. Protocolo y comandos vigentes: [../../InformacionCritica/docs/RUTAS.md](../../InformacionCritica/docs/RUTAS.md). Estabilidad y compatibilidad API siguen siendo la ganancia estructural.

## 4. Plan de sweep (protocolo de ajuste, 30-60 min)

```bash
# Pasada 1 — arranque conservador que seguro cabe:
-ngl 999 -ncmoe 40 -fa on -c 16384 -b 1024 -ub 256 -t 4

# Pasada 2..n — bajar -ncmoe de a 2 hasta ver el acantilado:
40 → 38 → 36 → 34 ...
# Medir con los t/s del log del server (o llama-bench si está compilado).
# Síntoma de acantilado: t/s se hunde de golpe → volver al valor anterior.

# Pasada MTP — con el mejor -ncmoe, alternar:
--spec-type draft-mtp --spec-draft-n-max 2   (probar 1,2,3; con y sin --spec-draft-p-min 0.75)
# Si MTP degrada u OOM → correr sin MTP (el modelo funciona igual).
```

## 5. Alternativas $0 si MINI no da la experiencia esperada

| Opción | Modelo | Tamaño | Velocidad esperada | Cuándo usarla |
|--------|--------|--------|:---:|---------------|
| A | `qwen3.5:2b` (Ollama) | 2.7 GB (cabe EN GPU) | 40-80 t/s | Chat fluido instantáneo, airi sin lag |
| B | `phi4-mini` / `qwen3:4b` | 2.5 GB | 25-50 t/s | Más inteligencia que el 2b, aún fluido |
| C | Este APEX-I-MINI (35B-A3B) | 14.27 GB | 14-24 t/s (28-36 con MTP) | Máxima inteligencia local disponible, tolerando la espera |
| D | Híbrido: A/B local + API barata para tareas pesadas | — | — | Nunca esperar al 35B para lo trivial |

Estrategia de Director pragmática: **servir los dos modelos** (puerto 8080 el 35B, Ollama el 2b) y que airi/pi dev decida por tarea.
