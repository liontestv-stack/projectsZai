# 03 — Software: llama.cpp, MTP, --n-cpu-moe y ecosystem

## 1. llama.cpp — requisitos de versión

| Requisito | Detalle |
|-----------|---------|
| Soporte arquitectura `qwen3_5_moe` | Necesario para cargar el GGUF — presente en builds recientes (2026) |
| MTP especulativo | **PR [#22673](https://github.com/ggml-org/llama.cpp/pull/22673)** (am17an), fusionado a master (anuncio r/LocalLLaMA "MTP support merged into llama.cpp") |
| Documentación oficial | [docs/speculative.md](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md) — implementa `draft`, `draft-eagle3`, `draft-dflash` y **`draft-mtp`** |
| Regla práctica | **Instalar la última release de llama.cpp** (o compilar master). Builds viejos = modelo no carga o sin draft-mtp |

## 2. Flags clave verificados (2026)

```text
-ngl / -ncmoe        --n-gpu-layers (poner 999 = max) y --n-cpu-moe N
                     N = capas cuyos expertos quedan en RAM.
                     Regla de la comunidad (openclawdc): -ngl SIEMPRE al máximo;
                     controlar memoria SOLO con -ncmoe. Barrer N y buscar el
                     "acantilado" de VRAM, retroceder un paso.
-fa / -fa on         --flash-attn: menos VRAM de KV + más rápido. Dejarlo siempre ON.
-ctk / -ctv          cuantización del KV cache: f16 (rápido), q8_0, q4_0, iq4_nl,
                     y en forks TurboQuant: turbo2/3/4. f16 > q8_0 en velocidad
                     cuando cabe; q8_0 es "función de memoria", no de velocidad.
-c                   contexto. Primero fijar el contexto que SE USA, luego barrer ncmoe.
-lm none / -lm mlock (antes --no-mmap / --mlock): con expertos en RAM, mmap puede
                     provocar evicciones; -lm none reportó bajar RAM 98%→71% a igual velocidad.
-b / -ub             buffers de batch en GPU: bajarlos (-b 1024 -ub 256) libera VRAM
                     para más expertos; penaliza prompt processing, no la generación.
--spec-type draft-mtp --spec-draft-n-max N   activa MTP (N=2 recomendado; probar 1-6).
--spec-draft-p-min 0.75  sube la aceptación de drafts lejanos (foro NVIDIA).
--mmproj ARCHIVO     habilita visión con el mmproj del repo.
-t N                 hilos CPU (= núcleos físicos en nuestro caso: 4).
```

## 3. Evidencia de foros/empresas (números reales)

| Fuente | Hardware | Modelo | Resultado |
|--------|----------|--------|-----------|
| [mdda.net](https://mdda.net/blog/tech/dl/llama-cpp-moe-on-an-old-gtx-1080) | GTX 1080 8GB + CPU vieja | Qwen 35B-A3B Q4_K_M, `-ngl 999 -ncmoe 30` | **~25 t/s** tg, 56-58 t/s pp |
| r/LocalLLaMA (2026) | 8GB VRAM | Qwen3.6 35B MoE, `-ncmoe 38` | 10-12 → **36.6 t/s** al tunear |
| r/LocalLLaMA | RTX 5090 | sweep -ncmoe 20→12 | 54 → 69.4 t/s; colapso a 27.5 al pasarse (VRAM spill silencioso) |
| [Foro NVIDIA (blainesworld)](https://forums.developer.nvidia.com/t/mtp-llama-cpp-a-look-at-qwen3-6-27b/370298) | DGX Spark GB10 | Qwen3.6-27B MTP Q4_K_M, draft-n-max 5 + p-min 0.75 | **28-31 t/s** estables, c1-c4; notas de crashes ocasionales en el PR |
| [Unsloth docs MTP](https://unsloth.ai/docs/models/mtp) | RTX 6000 | Qwen3.6-35B-A3B MTP | **240 t/s** (referencia techo) |
| **Nuestro rig (estimación física)** | i3-10100F + 1650 4GB + 16GB DDR4-2666 | APEX-I-MINI 12.2GB, expertos en RAM | **12-18 t/s esperadas** (base 10-16 + MTP) |

⚠️ Advertencias recopiladas:
- MTP: "gains are smaller on devices with lower memory bandwidth" (Unsloth) y "+~2GB RAM/VRAM" — en nuestro rig probar con y sin MTP.
- Crashes ocasionales reportados en el camino MTP (foro NVIDIA) → mantener builds actualizados.
- VRAM spill silencioso: si `-ncmoe` es muy bajo, no hay error, solo lentitud brutal. Medir siempre.

## 4. TurboQuant KV (opcional, fork)

- Fork [TheTom/llama-cpp-turboquant](https://github.com/TheTom/llama-cpp-turboquant) rama `feature/turboquant-kv-cache` (documentado en apex-quant README): KV cache 4.6× comprimido, `-ctk q8_0 -ctv turbo3 -fa on`, +14% prompt processing.
- Requiere compilar el fork (CMake + CUDA). En presupuesto $0 y Windows es factible pero opcional: **primero probar llama.cpp estándar con `-ctk q8_0 -ctv q8_0`**.
- Nota: builds recientes de mainline ya listan `turbo2/turbo3/turbo4` en la ayuda de `-ctk` (observado en documentación de flags) — verificar con `llama-server --help` antes de compilar nada.

## 5. Runtimes y compatibilidad con apps

| Runtime | ¿Sirve para este modelo? | Nota |
|---------|:---:|------|
| **llama-server** (llama.cpp) | ✅ RECOMENDADO | Expone API OpenAI (`/v1/chat/completions`), streaming, tool-calls, mmproj visión, y TODOS los flags MTP/ncmoe |
| Ollama | ⚠️ Parcial | Importa el GGUF (Modelfile) y da API OpenAI, pero NO expone `--spec-type draft-mtp` ni sweep fino de `-ncmoe` → perdemos el boost MTP |
| LM Studio | ⚠️ Parcial | Carga GGUF con GUI y servidor OpenAI; control MTP/ncmoe limitado según versión |
| LocalAI | ✅ | Compatible out-of-the-box con APEX (documentado por mudler); API OpenAI; alternativa a llama-server |
| vLLM / SGLang | ❌ | Requieren los pesos HF originales (no GGUF) y 20-70GB VRAM — no para este rig |

**Conclusión**: airi y pi dev hablan OpenAI → apuntarlos a `http://127.0.0.1:8080/v1` servido por `llama-server`. Cero scripts Python custom (la lección del proyecto anterior).
