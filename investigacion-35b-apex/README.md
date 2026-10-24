# 🔬 Investigación: Qwen3.6-35B-A3B APEX en i3-10100F + GTX 1650 (4GB)

> Dossier de inteligencia recopilado por LAIA (2026-10-24) por orden del Director.
> Misión: agotar todas las fuentes vitales sobre el modelo
> `SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF`
> y su viabilidad real en el rig: **i3-10100F · GTX 1650 4GB · 16GB RAM · SSD 500GB**.
> Presupuesto: **$0**.

---

## 📑 Índice del dossier

| Archivo | Contenido |
|---------|-----------|
| [01-modelo-apex.md](01-modelo-apex.md) | Ficha completa del modelo: archivos, tiers APEX, benchmarks oficiales, decensorado, MTP |
| [02-arquitectura-qwen36.md](02-arquitectura-qwen36.md) | Arquitectura Qwen3.5 MoE: DeltaNet, expertos, KV cache, capas MTP |
| [03-software-llamacpp.md](03-software-llamacpp.md) | llama.cpp: soporte MTP (PR #22673), `--n-cpu-moe`, TurboQuant, versiones |
| [04-hardware-presupuesto-cero.md](04-hardware-presupuesto-cero.md) | Análisis componente por componente del rig + veredicto de viabilidad |
| [05-config-recomendada.md](05-config-recomendada.md) | Comando final calibrado, sweep de ajustes, conexión a airi/pi dev, troubleshooting |
| [06-fuentes.md](06-fuentes.md) | Todas las fuentes (oficiales, desarrolladores, foros) con lo extraído de cada una |

---

## ⚡ Resumen ejecutivo (lectura de 2 minutos)

### Qué es este modelo
Requantización **APEX** (por mudler / equipo LocalAI) del Qwen3.6-35B-A3B **decensurado con Heretic v1.3.0 + MPOA** (por llmfan46), que **conserva las 20 capas MTP nativas** para decodificación especulativa (`--spec-type draft-mtp`, +20-50% velocidad). Apache-2.0. 59.517 descargas, 152 likes.

### Hallazgo crítico para nuestro rig (16GB RAM)
El repo tiene 4 tiers. **Solo uno es viable en 16GB de RAM**:

| Tier | Tamaño | ¿Cabe en nuestro rig? |
|------|--------|:---:|
| I-Quality | 21.90 GB | ❌ Excede la RAM usable |
| I-Balanced | 24.18 GB | ❌ Excede la RAM usable |
| I-Compact | 15.85 GB | ❌ 16GB − OS ≈ 13GB usable → swap |
| **I-MINI** | **12.2 GB** | ✅ **La única opción real** |

### Veredicto de viabilidad (detallado en 04)
- ✅ **VIABLE** con `APEX-I-MINI` + `llama-server` + `-ncmoe alto` (expertos en RAM, atención en GPU)
- 🎯 Velocidad esperada honesta: **12-18 t/s** (base 10-16 + boost MTP 20-40%)
- 🏆 Frente al intento anterior: **misma velocidad pero estable, con API OpenAI estándar → airi y pi dev conectan directo**, con visión opcional (mmproj incluido en el repo)
- ⚠️ Riesgo principal: RAM al límite (12.2GB modelo + OS en 16GB) → mitigable con mmap y cierre de apps
- 🚫 Lo que NO intentar: Ollama no expone `--spec-type draft-mtp` ni ajuste fino de `-ncmoe` → **llama-server es el camino**

### Los 3 comandos que lo resumen
```bash
# 1. Descargar (solo el tier viable + vision)
hf download SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF \
  --include "*MINI*" --include "mmproj*" --local-dir ./models

# 2. Servir (calibrado para 4GB VRAM + 16GB RAM — ver 05 para el sweep)
./llama-server -m models/*APEX-I-MINI.gguf -ngl 999 -ncmoe 36 -c 16384 \
  -fa on -ctk q8_0 -ctv q8_0 --spec-type draft-mtp --spec-draft-n-max 2 \
  --host 127.0.0.1 --port 8080

# 3. Conectar airi / pi dev → http://127.0.0.1:8080/v1
```
