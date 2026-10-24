# 06 — Registro completo de fuentes

> Protocolo LAIA: toda fuente vital consultada el 2026-10-24, con lo que se extrajo de cada una.
> Clasificación: 🏢 compañía oficial · 👨‍💻 desarrollador/herramienta · 💬 foro/comunidad · 📰 análisis técnico.

## Modelo y empresas oficiales

1. 🏢 **HuggingFace — página del modelo** (SC117)
   https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF
   → Model card completo: tiers APEX (tamaños de perfil: 21.9 / 24.18 / 15.85 / 12.2; **tamaños reales de archivo: 23.51 / 25.96 / 17.02 / 14.27 GB** — ver fuente 2), benchmarks, MTP `--spec-type draft-mtp --spec-draft-n-max 2` (+20-50%), samplers recomendados, comandos llama.cpp/Ollama, links de la cadena de creación.

2. 🏢 **HuggingFace API — metadatos del repo**
   https://huggingface.co/api/models/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF
   → Lista exacta de archivos (4 GGUF + mmproj F16), tags (`qwen3_5_moe`, `mtp`, `apex`, `mpoa`...), Apache-2.0, 59.517 descargas, 152 likes, actualizado 2026-10-03.

3. 🏢 **Qwen Team — modelo original**
   https://huggingface.co/Qwen/Qwen3.6-35B-A3B · blog: https://qwen.ai/blog?id=qwen3.6-35b-a3b
   → Base oficial del modelo, licencia, posicionamiento ("Agentic Coding Power").

## Herramientas y sus desarrolladores

4. 👨‍💻 **APEX quantization — mudler (equipo LocalAI)**
   https://github.com/mudler/apex-quant (MIT, 482⭐, paper incluido)
   → Cómo funciona APEX (clasificación por rol: routed/shared/attention; gradiente de precisión por capas; imatrix diversa "sin Wikipedia"), tabla completa de benchmarks vs Q8_0/UD/IQ2_M, tiers y sus estrategias, TurboQuant KV fork, compatibilidad stock llama.cpp (`--tensor-type-file`), fix upstream a llama.cpp para arquitecturas híbridas.

5. 👨‍💻 **Heretic — p-e-w (Philipp Emanuel Weidmann)**
   https://github.com/p-e-w/heretic (AGPL-3.0, **35.6k⭐**, v1.4.0)
   → Qué es la abliteración direccional + optimización TPE/Optuna; soporte explícito de modelos híbridos Qwen3.5; métricas de calidad (KL bajo); más de 5.000 modelos derivados en la comunidad.

6. 👨‍💻 **Unsloth — guía oficial MTP**
   https://unsloth.ai/docs/models/mtp
   → Flags exactos (`--spec-type draft-mtp`, `--spec-draft-n-max 1-6`), coste de memoria MTP (~2 GB), requisitos por modelo (Qwen3.6 necesita MTP GGUF separado en su versión estándar — nuestro repo APEX lo trae integrado), benchmarks (240 t/s en RTX 6000), nota clave: "gains smaller on low memory bandwidth", build con `-DGGML_CUDA=ON`.

7. 👨‍💻 **llama.cpp — documentación oficial de decodificación especulativa**
   https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md
   → Implementaciones soportadas por llama-server: `draft`, `draft-eagle3`, `draft-dflash`, `draft-mtp`; cómo funcionan los drafts y la verificación en batch.

8. 👨‍💻 **PR #22673 de llama.cpp — "llama + spec: MTP Support" (am17an)**
   https://github.com/ggml-org/llama.cpp/pull/22673
   → Origen del soporte MTP; **fusionado a master el 2026-05-16; autor am17an (verificado vía página del PR, 2026-10-24)**.

## Foros y comunidad

9. 💬 **Foro NVIDIA (DGX Spark) — blainesworld, may 2026**
   https://forums.developer.nvidia.com/t/mtp-llama-cpp-a-look-at-qwen3-6-27b/370298
   → Comando real completo de llama-server con MTP; resultados medidos: 28-31 t/s con Qwen3.6-27B MTP Q4_K_M; truco `--spec-draft-p-min 0.75` para subir aceptación con draft-n-max alto; aviso de crashes ocasionales ligados al PR.

10. 💬 **r/LocalLLaMA — "MTP support merged into llama.cpp"**
    https://www.reddit.com/r/LocalLLaMA/comments/1tes1wx/ (título verificado; hilo protegido contra fetch)
    → Confirmación comunitaria del merge del soporte MTP.

11. 💬 **r/LocalLLaMA — "Qwen3.6 35B MoE on 8GB VRAM — working llama-server"**
    https://www.reddit.com/r/LocalLLaMA/comments/1srijdf/
    → `-ncmoe 38`: de 10-12 a **36.6 t/s**; recomendación de empezar con `--fit` y afinar manual.

12. 💬 **r/LocalLLM — "Anyone getting 20+ tokens/sec on RTX 1650 (4GB)?"**
    https://www.reddit.com/r/LocalLLM/comments/1t34qnb/ (título verificado; hilo protegido contra fetch)
    → Contexto comunitario del límite de nuestra GPU.

## Análisis técnicos independientes

13. 📰 **mdda.net — "Running ~30B MoE models on an old GTX 1080"**
    https://mdda.net/blog/tech/dl/llama-cpp-moe-on-an-old-gtx-1080
    → Guía práctica completa: `-ngl 999 -ncmoe 30 --no-mmap`, ~25 t/s (24.94 medidos; verificado 2026-10-24) con 35B-A3B; texto íntegro de flags `-ctk/-ctv` (incluye valores turbo de FORK — no mainline); smoke test con curl contra `/v1/chat/completions`.

14. 📰 **openclawdc.com — "--n-cpu-moe Explained (2026)"**
    https://openclawdc.com/blog/llama-cpp-moe-offload-flags-explained
    → Método del sweep ("find the cliff, then back off one step"), spill silencioso de VRAM, f16 vs q8_0 en KV (f16 más rápido si cabe), impacto de `-b/-ub`, `-lm none` bajando RAM 98%→71%.

15. 📰 **llmkube.com — "Why Qwen 3.6 Doesn't Need --cpu-moe"**
    https://llmkube.com/blog/hybrid-moe-offloading-qwen-36-deltanet
    → Arquitectura fina de Qwen3.6-35B-A3B: 40 capas (10 bloques de 3×DeltaNet+1×GatedAttention), 256 expertos (8+1 activos, intermedio 512), KV cache minúsculo por DeltaNet; por qué el flag ayuda solo cuando el modelo NO cabe en VRAM (nuestro caso exacto); medición 21.7 vs 107.8 t/s.

16. 📰 **localaimaster.com — "Best Ollama Models for 4GB VRAM"**
    https://localaimaster.com/vram/best-ollama-models-4gb-vram
    → Alternativas pequeñas verificadas para el rig (qwen3.5:2b 2.7GB, phi4-mini 2.5GB, qwen3:4b, granite4.1:3b, llama3.2:3b, qwen2.5-coder:3b, gemma3:1b) — plan B documentado.

## Referencias cruzadas del ecosistema

17. 🏢 **Ollama — compatibilidad API OpenAI**
    https://ollama.com/blog/openai-compatibility
    → Cómo conectan airi/pi dev a Ollama/llama-server vía `/v1` (formato exacto de request).

18. 💬 **r/LocalLLaMA — "How to run local code agent in a NVIDIA GeForce GTX [1650]"**
    https://www.reddit.com/r/LocalLLaMA/comments/1r8aiok/ (título verificado)
    → Experiencias de agentes de código sobre GTX 1650 (contexto para pi dev).

---

### Notas de método
- Hilos de Reddit protegidos contra lectura automatizada: se conservó lo verificable (títulos, resultados citados en fuentes secundarias).
- El model card tiene una inconsistencia menor ("40 capas + 1 MTP" vs "20 MTP layers preserved") — documentada tal cual; no afecta la operación (el flag `draft-mtp` funciona según foros y Unsloth).
- Toda cifra de velocidad de terceros depende de hardware distinto al nuestro; las esperadas para el rig están derivadas por física de ancho de banda en [04](04-hardware-presupuesto-cero.md).
