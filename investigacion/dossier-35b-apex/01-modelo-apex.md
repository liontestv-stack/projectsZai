# 01 — Ficha técnica del modelo APEX

> Fuente primaria: [SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF](https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF)
> Verificado vía API de HuggingFace el 2026-10-24.

## 1. Identidad

| Campo | Valor |
|-------|-------|
| Autor de la cuantización | **SC117** |
| Modelo base | [llmfan46/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved](https://huggingface.co/llmfan46/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved) |
| Modelo original | [Qwen/Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) (Qwen Team, abril 2026 — "Agentic Coding Power, Now Open to All") |
| Licencia | Apache-2.0 |
| Tareas | image-text-to-text (multimodal con mmproj) |
| Descargas / Likes | 59.517 / 152 (a 2026-10-24) |
| Última actualización | 2026-10-03 |
| Tags | `gguf` `qwen3_5_moe` `heretic` `uncensored` `abliterated` `mpoa` `mtp` `apex` |

## 2. Cadena de creación del modelo

```
Qwen/Qwen3.6-35B-A3B          (modelo oficial Qwen Team)
        │  Heretic v1.3.0 + MPOA
        ▼
llmfan46/...-uncensored-heretic-Native-MTP-Preserved
        │  (88% menos negativas de seguridad; KL = 0.0015)
        │  (MTP: "todas las capas MTP preservadas")
        ▼
SC117/...-APEX-GGUF           (requantización APEX, 4 tiers + mmproj)
```

- **Heretic** ([p-e-w/heretic](https://github.com/p-e-w/heretic), 35.6k ⭐): herramienta automática de remoción de censura por *abliteración direccional* + optimizador TPE (Optuna). Co-minimiza rechazos y divergencia KL. Soporta modelos híbridos como Qwen3.5. Última versión v1.4.0 (jun 2026).
- **MPOA**: técnica adicional de decensurado aplicada por llmfan46 (tag `mpoa` en HF). Menos documentada; tratar como método complementario a la abliteración.
- Resultado declarado: **10/100 refusals** en suite "Uncensored" vs 83/100 del original, con KL 0.0015 (daño casi nulo a la inteligencia del modelo).

## 3. Archivos del repo (verificados por API)

| Archivo | Rol |
|---------|-----|
| `...APEX-I-Quality.gguf` | Tier máxima calidad — **23.51 GB reales** (card: 21.90) |
| `...APEX-I-Balanced.gguf` | Tier equilibrado (recomendado por autor) — **25.96 GB reales** (card: 24.18) |
| `...APEX-I-Compact.gguf` | Mejor ratio calidad/tamaño — **17.02 GB reales** (card: 15.85) |
| `...APEX-I-MINI.gguf` | **★ El único viable en 16GB RAM — 14.27 GB reales** (card: 12.2 de perfil) |

| `mmproj-...APEX-F16.gguf` | Proyector de visión (~0.4B params, CLIP) — 0.90 GB reales |

⚠ **Tamaños "reales"** = bytes del archivo según la API de HF (2026-10-24, GB decimal). La card lista tamaños de perfil (GiB) y puede preceder a la actualización del repo del 2026-10-03. Consecuencia material: el I-MINI deja solo ~1.5 GB de margen sobre 16 GB de RAM → pageouts probables (ver [../../InformacionCritica/docs/RUTAS.md](../../InformacionCritica/docs/RUTAS.md) §0).

## 4. ¿Qué es APEX? ([mudler/apex-quant](https://github.com/mudler/apex-quant), equipo LocalAI, MIT)

Cuantización de **precisión mixta consciente de MoE**, sin parches de llama.cpp (usa flags estándar `--tensor-type-file` / `--tensor-type`):

1. **Clasifica cada tensor por rol**: experto enrutado (97% de pesos, tolera compresión), experto compartido (siempre activo, kurtosis 13.10 → necesita Q8_0), atención/SSM (Q6_K uniforme).
2. **Gradiente de precisión por capa**: bordes (L0-4, L35-39) Q6_K, cerca-bordes (L5-9, L30-34) Q5_K, medio (L10-29) Q4_K/IQ4_XS.
3. **Variante I-**: imatrix de calibración diversa (chat, código, razonamiento, tool-calling — sin Wikipedia) → mejor accuracy real y KL menor.
4. **Mini tier**: gradiente de capas + IQ2_S en medio + imatrix diversa → 12.2 GB de perfil (archivo real: 14.27 GB), diseñado para GPUs de 16GB VRAM.

### Benchmarks oficiales APEX (Qwen3.5-35B-A3B, DGX Spark GB10 122GB)

| Config | GB | PPL wikitext | HellaSwag | MMLU | ARC-C | TruthfulQA | tg128 |
|--------|-----|:---:|:---:|:---:|:---:|:---:|:---:|
| F16 | 64.6 | 6.537 | 82.5% | 41.5% | 56.9% | 37.2% | 30.4 |
| Q8_0 | 34.4 | 6.533 | 83.0% | 41.2% | 57.9% | 37.7% | 52.5 |
| APEX I-Quality | 21.3 | 6.552 | **83.5%** | 41.4% | 57.9% | **38.4%** | 63.1 |
| APEX I-Balanced | 23.6 | 6.548 | 83.0% | 41.0% | 57.5% | 37.5% | 61.4 |
| APEX I-Compact | 16.1 | 6.669 | 81.8% | **41.7%** | 55.5% | 37.9% | 69.8 |
| **APEX Mini** | **12.2** | 7.088 | 81.0% | 41.3% | 57.2% | 36.7% | **74.4** |
| bartowski IQ2_M (referencia) | 11.3 | 7.303 | 80.3% | 39.6% | 56.2% | 35.0% | 76.2 |

⚠ Tamaños de esta tabla = los de la model card (perfil/GiB); para presupuestar RAM usar los reales de §3.

**Lectura clave para nosotros**: APEX Mini (nuestro tier) pierde algo de perplexity (7.088 vs 6.537 F16) pero **mantiene MMLU/ARC casi intactos** (41.3%/57.2% vs 41.5%/56.9%) y supera a IQ2_M en TODO. La degradación real en uso es menor de lo que sugiere el PPL.

## 5. MTP nativo (el argumento de venta)

- El model card declara: *"All 20 MTP layers preserved"* (aunque la tabla de detalles dice "40 capas + 1 MTP layer" — inconsistency del card; en la práctica el flag funciona según los foros).
- Uso: `--spec-type draft-mtp --spec-draft-n-max 2` → **+20-50% de velocidad** declarada por el autor.
- Diferencia con otros GGUF de Qwen3.6: según Unsloth, *"The only model that still requires a separate MTP GGUF is Qwen3.6"* — los GGUF estándar de Qwen3.6 necesitan un archivo MTP aparte (ej. `unsloth/Qwen3.6-27B-MTP-GGUF`). **Este repo APEX lo lleva integrado** → un solo archivo, más simple.
- Costo de memoria MTP: **~2 GB extra de RAM/VRAM** (dato de Unsloth) — crítico en nuestro rig.

## 6. Ajustes de sampler recomendados (del model card)

| Modo | Parámetros |
|------|-----------|
| Thinking (general) | temp=1.0, top_p=0.95, top_k=20, presence_penalty=1.5 |
| Thinking (código) | temp=0.6, top_p=0.95, top_k=20 |
| Instruct (general) | temp=0.7, top_p=0.8, top_k=20, presence_penalty=1.5 |
| Instruct (razonamiento) | temp=1.0, top_p=1.0, top_k=40, presence_penalty=2.0 |

## 7. Descarga

```bash
# Solo lo necesario (MINI + mmproj) — ~15.2 GB en el SSD de 500GB (14.27 + 0.90)
pip install -U huggingface_hub
hf download SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF \
  --include "*MINI*" --include "mmproj*" --local-dir ./models
```
