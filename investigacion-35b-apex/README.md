# 🔬 Investigación: Qwen3.6-35B-A3B APEX en i3-10100F + GTX 1650 (4GB)

> Dossier de inteligencia recopilado por LAIA (2026-10-24) por orden del Director.
> Misión: agotar todas las fuentes vitales sobre el modelo
> `SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF`
> y su viabilidad real en el rig: **i3-10100F · GTX 1650 4GB · 16GB RAM · SSD 500GB**.
> Presupuesto: **$0**.
>
> ⚠ **ACTUALIZADO (tarde 2026-10-24):** auditoría del build del Director (sin draft-mtp → RUTA 0: actualizar build), corrección del techo (el x2 es alcanzable: PR #22673 ">2x, ~75% acceptance") y tamaños reales de archivo (I-MINI = **14.27 GB**, no 12.2). Guía operativa vigente: **[../InformacionCritica/RUTAS.md](../InformacionCritica/RUTAS.md)**. Este dossier conserva el análisis de fondo; donde difiera, manda InformacionCritica.

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

| Tier | Tamaño real (API HF) | ¿Cabe en nuestro rig? |
|------|--------|:---:|
| I-Quality | 23.51 GB | ❌ Excede la RAM usable |
| I-Balanced | 25.96 GB | ❌ Excede la RAM usable |
| I-Compact | 17.02 GB | ❌ 16GB − OS ≈ 13GB usable → swap |
| **I-MINI** | **14.27 GB** | ✅ **La única opción real** — al filo: pageouts probables |

### Veredicto de viabilidad (detallado en 04)
- ✅ **VIABLE** con `APEX-I-MINI` + `llama-server` + `-ncmoe alto` (expertos en RAM, atención en GPU)
- 🎯 Velocidad esperada honesta (corregida): base **14-24 t/s** tras sweep → **28-36 t/s** con draft-mtp (PR #22673: ">2x con ~75% acceptance")
- 🏆 Frente al intento anterior: **MÁS velocidad (techo corregido), estable, con API OpenAI estándar → airi y pi dev conectan directo**, con visión opcional (mmproj incluido en el repo)
- ⚠️ Riesgo principal: RAM al filo (**14.27 GB reales** + OS en 16GB) → pageouts probables; mitigable con pagefile en SSD, mmap y cierre de apps
- 🚫 Lo que NO intentar: Ollama no expone `--spec-type draft-mtp` ni ajuste fino de `-ncmoe` → **llama-server es el camino**

### Los 3 comandos que lo resumen
```bash
# 1. Descargar (solo el tier viable + vision)
hf download SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF \
  --include "*MINI*" --include "mmproj*" --local-dir ./models

# 2. Servir (calibrado para 4GB VRAM + 16GB RAM — ver 05 para el sweep)
#    ⚠ draft-mtp requiere build actualizado (RUTA 0 en InformacionCritica/RUTAS.md)
./llama-server -m models/*APEX-I-MINI.gguf -ngl 999 -ncmoe 36 -c 16384 \
  -fa on -ctk q8_0 -ctv q8_0 --spec-type draft-mtp --spec-draft-n-max 2 \
  --host 127.0.0.1 --port 8080

# 3. Conectar airi / pi dev → http://127.0.0.1:8080/v1
```
