# 04 — Análisis del rig: i3-10100F + GTX 1650 + 16GB RAM + SSD 500GB (presupuesto $0)

## 1. Radiografía del hardware

| Componente | Specs | Implicación para el proyecto |
|------------|-------|------------------------------|
| **CPU** Intel i3-10100F (Comet Lake, 2020) | 4C/8T, 3.6-4.3 GHz, AVX2, max DDR4-2666 | 4 hilos físicos para expertos en RAM. Ancho de banda RAM = **~41.6 GB/s** (dual channel) → EL cuello de botella maestro |
| **GPU** GTX 1650 4GB (Turing TU117) | 4GB GDDR5/GDDR6, ~128-192 GB/s VRAM, CUDA cc 7.5 | Suficiente para: atención + KV cache + shared experts + capas MTP + buffers. NO para los expertos (no caben) |
| **RAM** 16GB DDR4-2666 | dual channel | Presupuesto real: ~13 GB usable tras OS. Modelo MINI = 12.2 GB → **ajustado pero viable con mmap** |
| **SSD** 500GB (dedicado al proyecto) | | Descarga de 13 GB holgada; mmap acelera recargas; espacio sobra para 2-3 variantes + experimentos |

## 2. Presupuesto de memoria (el cálculo que decide todo)

### RAM (16 GB)
```
  OS Windows + servicios          ~2.5-3.5 GB
  Expertos APEX-I-MINI en RAM     ~9.5-10.5 GB   (la mayor parte de los 12.2 GB)
  Cola/mmap page cache            compartido con lo anterior
  ─────────────────────────────────────────────
  TOTAL                           ~12-14 GB  → viable con margen estrecho
```
Reglas de supervivencia: cerrar navegador/apps pesadas al servir el modelo; NO usar `--mlock` (necesitaríamos ~10 GB bloqueados → OOM); mantener mmap (default) para que el SO pagee expertos fríos.

### VRAM (4 GB)
```
  Atención (40 capas) + shared + output + embd   ~1.2-1.8 GB
  KV cache (10 capas Gated Attention; DeltaNet=estado recurrente) q8_0 @16K  ~0.3-0.6 GB
  Buffers de cómputo (-b 1024 -ub 256)           ~0.3-0.5 GB
  Capa MTP + overhead especulativo               ~0.3-0.5 GB
  ─────────────────────────────────────────────
  TOTAL ~2.1-3.4 GB → cabe; si se pasa, subir -ncmoe / bajar -ub
```

## 3. Por qué tu experiencia anterior (16 t/s) era el techo correcto — y por qué ahora puede mejorar

- Física: A3B en DDR4-2666 → techo ~20 t/s; tus 16 t/s = sistema al 80% del límite físico. **No había error de configuración.**
- Lo que NO se puede: superar el ancho de banda de la DDR4 (sin cambiar RAM/CPU).
- Lo que SÍ se puede ganar sin gastar $1:
  1. **MTP nativo** (`draft-mtp`, +20-40% en el mejor caso) → posible 18-20+ t/s en respuestas donde la aceptación de drafts es alta (chat/código).
  2. **Sweep fino de `-ncmoe`** con la GTX 1650 cargando todo lo no-experto (antes quizá quedaba capa suelta en CPU).
  3. **KV q8_0 + flash-attn** → libera VRAM para bajar -ncmoe un par de pasos.
  4. **SSD dedicado + mmap** → carga inicial mucho más rápida que antes (500GB dedicado, sin competencia de disco).
- Expectativa honesta final: **12-18 t/s sostenidas, picos ~20 t/s** con MTP funcionando. Estabilidad y compatibilidad API = la ganancia estructural.

## 4. Plan de sweep (protocolo de ajuste, 30-60 min)

```bash
# Pasada 1 — arranque conservador que seguro cabe:
-ngl 999 -ncmoe 40 -fa on -c 16384 -b 1024 -ub 256 -t 4

# Pasada 2..n — bajar -ncmoe de a 2 hasta ver el acantilado:
40 → 38 → 36 → 34 ...
# Medir con llama-benchy o observando t/s del log.
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
| C | Este APEX-I-MINI (35B-A3B) | 12.2 GB | 12-18 t/s | Máxima inteligencia local disponible, tolerando la espera |
| D | Híbrido: A/B local + API barata para tareas pesadas | — | — | Nunca esperar al 35B para lo trivial |

Estrategia de Director pragmática: **servir los dos modelos** (puerto 8080 el 35B, Ollama el 2b) y que airi/pi dev decida por tarea.
