# 02 — Arquitectura Qwen3.6-35B-A3B (lo que importa para hardware modesto)

> Síntesis de: [llmkube.com — "Why Qwen 3.6 Doesn't Need --cpu-moe"](https://llmkube.com/blog/hybrid-moe-offloading-qwen-36-deltanet), model card de Qwen, apex-quant README.

## 1. Estructura

| Propiedad | Valor |
|-----------|-------|
| Familia | Qwen3.5 MoE (arquitectura híbrida con DeltaNet) |
| Parámetros totales | 35B |
| Activos por token | ~3B |
| Capas | 40 + capas MTP |
| Experto | 256 expertos enrutados, 8 activos/token (+1 compartido según análisis) |
| Contexto nativo | 262.144 tokens (256K) |
| Atención | Híbrida: **30 capas Gated DeltaNet + 10 capas Gated Attention** |

## 2. El detalle que define nuestra estrategia: DeltaNet

Qwen3.6 usa **Gated DeltaNet** (variante de atención lineal) en 30 de sus 40 capas:

- **No construye KV cache creciente** → mantiene un *estado recurrente compacto*.
- Solo las **10 capas Gated Attention** contribuyen al KV cache → **KV cache minúsculo** incluso a contextos enormes.
- Consecuencia práctica (dato llmkube): a 90K de contexto con KV q8_0, el modelo Q4_K_M completo cabe en 2×16GB de VRAM **sin offload**.
- **Para nosotros**: la carga de VRAM del contexto es baja → podemos darnos contextos de 16K-64K en una GTX 1650 sin que el KV cache nos explote. El cuello de botella es solo el tamaño de los pesos.

## 3. Por qué este modelo es especial para CPU-offload (MoE)

- Los pesos se concentran en **expertos enrutados** (la mayoría de los 35B), pero por token solo se activan 8/256.
- Al hacer offload de expertos a RAM: por token solo se leen los expertos activos → **el ancho de banda consumido por token es bajo** → un MoE es el ÚNICO tipo de modelo 35B que corre decente en RAM DDR4.
- Un modelo denso de 20B leería ~12 GB/token en Q4 → imposible (<1 t/s en DDR4). El MoE A3B lee ~0.3-0.5 GB/token → 10-25 t/s. **Esta es la razón física de todo el proyecto.**

## 4. Nota técnica sobre `--n-cpu-moe` con esta arquitectura

- En modelos MoE clásicos (Qwen3-Coder 30B), `--cpu-moe` es necesario cuando el modelo no cabe en VRAM, y paga coste de cómputo CPU por token.
- En Qwen3.6 **cuando cabe entero en VRAM**, activar el flag es dañino (21.7 vs 107.8 t/s en dual 16GB — dato llmkube). Pero **en 4GB VRAM no cabe entero** → el flag SÍ es necesario para nosotros. La regla: usar `-ncmoe` alto (dejar en GPU solo atención/shared/MTP) y barrer hacia abajo hasta el acantilado de VRAM.

## 5. MTP (Multi-Token Prediction / NextN)

- Capas MTP = módulos de predicción multi-token entrenados junto al modelo; permiten **decodificación especulativa autónoma** (el modelo se auto-borracha tokens y luego los verifica).
- llama.cpp lo soporta desde el **PR [#22673](https://github.com/ggml-org/llama.cpp/pull/22673)** (am17an), ya fusionado a master — ver [03-software-llamacpp.md](03-software-llamacpp.md).
- Beneficio reportado: +30-50% throughput en hardware con VRAM holgada (144 t/s en 16GB GPU — r/LocalLLaMA; 240 t/s Qwen3.6-35B-A3B MTP en RTX 6000 — Unsloth).
- En hardware de bajo ancho de banda (nuestro caso) la ganancia es menor pero real: los draft tokens se verifican en batch, aprovechando mejor cada lectura de expertos desde RAM.

## 6. Multimodalidad

- Repo incluye `mmproj-*-F16.gguf` (proyector CLIP ~0.4B) → el modelo acepta imágenes.
- En llama-server se habilita con `--mmproj`. Coste: ~0.8GB extra en VRAM/RAM — opcional en nuestro rig (evaluar tras el sweep).
