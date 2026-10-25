# CONFIG-SAMPLING-QWEN36 — Configuración profesional del modelo (llama.cpp b11856)

> **Stack del rig (único soportado):** `D:\llama.cpp\llama-server.exe` (build 11856, commit 3642238cc) + `APEX-I-MINI.gguf` (14.27 GB) + `abrir-qwen-apex.py`. **NO se usa Ollama ni ningún otro runtime.** Todas las flags de este documento están verificadas verbatim contra `llama-flags-nuevo.txt` (dump real del build del Director, re-auditoría 2026-10-25).

---

## §0. Jerarquía de fuentes (regla del proyecto: nada sin verificar)

| # | Fuente | Qué aporta | Estado |
|---|--------|-----------|--------|
| 1 | Model card oficial `Qwen/Qwen3.6-35B-A3B` (HF, consultada 2026-10-25) | Los 3 presets de sampling recomendados, modo thinking por defecto, contexto 262,144 | VERIFICADA (fetch textual) |
| 2 | `generation_config.json` oficial del mismo repo (fetch textual) | `{temperature: 1.0, top_k: 20, top_p: 0.95}` — **sin presence_penalty, sin min_p** | VERIFICADA (fetch textual) |
| 3 | `llama-flags-nuevo.txt` (122,440 B, UTF-16LE) | Única fuente de flags válidas del server b11856 | VERIFICADA (grep verbatim) |
| 4 | Doc familia Qwen3 (qwen.readthedocs.io/quickstart, capturada 2026-10-25) | Antecedente: "DO NOT use greedy decoding" (degradación y repeticiones sin fin) | VERIFICADA (antecedente de familia; para 3.6 manda la card) |
| 5 | PR #22673 (mergado 2026-05-16) | draft-mtp: ">2x speed-up with ~75% acceptance" | VERIFICADA (2026-10-24) |

---

## §1. Los 3 presets oficiales de Qwen3.6 (cita textual de la model card)

> *"We recommend using the following set of sampling parameters for generation"*

| Preset | temperature | top_p | top_k | min_p | presence_penalty | repetition_penalty |
|--------|-------------|-------|-------|-------|------------------|--------------------|
| **think** — Thinking, tareas generales (DEFAULT del modelo) | **1.0** | 0.95 | 20 | 0.0 | 1.5 según card / **0.0 según fábrica** (§1.1) | 1.0 |
| **coding** — Thinking, código preciso (WebDev, tool calls) | **0.6** | 0.95 | 20 | 0.0 | **0.0** | 1.0 |
| **fast** — Instruct / non-thinking | **0.7** | **0.80** | 20 | 0.0 | **1.5** | 1.0 |

### §1.1 La discrepancia del presence_penalty en "think" (resuelta con fuentes puras)

- La **card oficial** lista `presence_penalty=1.5` para thinking general.
- El **`generation_config.json` de fábrica** (fuente que los frameworks aplican por defecto) **NO incluye presence_penalty** — es decir, fábrica = `0.0` con `temperature 1.0, top_k 20, top_p 0.95`.
- **Decisión LAIA (documentada):** preset **think** usa `presence_penalty 0.0` (= fábrica). Razones: (a) es el valor con el que Qwen evalúa sus benchmarks (las notas de benchmark de la propia card usan `temp=1.0, top_p=0.95` sin mencionar penalties); (b) el único uso de 1.5 que ambas fuentes coinciden en recomendar es **non-thinking/fast**; (c) si el Director quiere probar la variante literal de la card, es un parámetro por-request (§3.2), reversible al instante sin relanzar.

### §1.2 Reglas que trascienden presets

- **Nada de greedy** (temperature 0) en chat real: la doc de la familia advierte degradación y repeticiones sin fin (el temperature 0 del sweep es una medición de t/s, no chat — no contradice esto).
- **Qwen3.6 NO soporta los soft-switch `/think` y `/nothink` de Qwen3** (card textual). El modo se controla por plantilla/API, no por texto en el prompt (§3.3).
- **El modelo piensa por defecto**: emite `<think>\n...\n\n` antes de la respuesta.

---

## §2. Defaults de TU server vs lo que el modelo quiere (por qué hay que fijarlos)

Flags verificadas en el dump b11856 con sus defaults de fábrica del server:

| Flag (verbatim del dump) | Default b11856 | Qwen3.6 quiere | ¿Pasarla? |
|--------------------------|----------------|----------------|-----------|
| `--temp, --temperature N` | **0.80** | 1.0 / 0.6 / 0.7 según preset | **SÍ, siempre** |
| `--top-k N` | **40** | **20** | **SÍ, siempre** |
| `--top-p N` | 0.95 | 0.95 / 0.80 (fast) | **SÍ** (fast cambia) |
| `--min-p N` | **0.05** | **0.0** | **SÍ, siempre** |
| `--presence-penalty N` | 0.00 | 0.0 (think/coding) / 1.5 (fast) | **SÍ** (fast cambia) |
| `--repeat-penalty N` | 1.00 | 1.0 | No (default ya correcto) |
| `--repeat-last-n N` | 64 | — | No (dejar default) |
| `-s, --seed SEED` | -1 (aleatorio) | — | No (aleatorio está bien) |

**Conclusión material:** el server recién instalado NO está configurado óptimo para este modelo — top-k 40 y min-p 0.05 distorsionan la distribución con la que Qwen3.6 fue validado. Fijar los presets (§3) NO cambia el rendimiento (t/s) pero sí la calidad/coherencia del texto.

---

## §3. Cómo aplicar los presets en llama.cpp b11856 (flags todas del dump)

### §3.1 Por CLI — defaults del server (recomendado; el lanzador ya lo hace)

El `abrir-qwen-apex.py` (v1.1+) añade un `--preset {think,coding,fast}` (default `think`) que inyecta al comando del server:

```text
think  →  --temp 1.0 --top-k 20 --top-p 0.95 --min-p 0.0 --presence-penalty 0.0
coding →  --temp 0.6 --top-k 20 --top-p 0.95 --min-p 0.0 --presence-penalty 0.0
fast   →  --temp 0.7 --top-k 20 --top-p 0.80 --min-p 0.0 --presence-penalty 1.5
```

Ejemplo completo (V1 + preset coding):

```text
D:\llama.cpp\llama-server.exe -m D:\ZLia\models\...APEX-I-MINI.gguf -a apex35b -ngl 99 -cmoe -c 16384 -b 2048 -ub 256 -fa on -ctk q8_0 -ctv q8_0 -t 4 --prio 2 --no-mmproj --temp 0.6 --top-k 20 --top-p 0.95 --min-p 0.0 --presence-penalty 0.0 --host 127.0.0.1 --port 9931
```

### §3.2 Por request — cambiar sin relanzar (WebUI o API)

Cada request a `/v1/chat/completions` (o el WebUI de `http://127.0.0.1:9931`) puede sobreescribir sampling al vuelo: `temperature`, `top_p`, `top_k`, `min_p`, `presence_penalty`. Útil para probar la variante "card literal" de §1.1 sin tocar el server.

### §3.3 Modo non-thinking y preserve-thinking (specific Qwen3.6)

| Qué | Cómo (fuente verbatim) | Detalle |
|-----|------------------------|---------|
| **Respuestas directas sin thinking** | CLI: `--chat-template-kwargs '{"enable_thinking":false}'` (dump: *"sets additional params for the json template parser, must be a valid json object string"*) | Método oficial del template. Alternativa nativa llama.cpp: `-rea off` (`--reasoning [on\|off\|auto]`, default auto) o `--reasoning-budget 0` (dump: *"0 for immediate end"*) |
| **Preservar razonamiento de turnos históricos** (feature nueva Qwen3.6, útil en agentes) | CLI: `--reasoning-preserve` (dump: *"preserve reasoning trace in the full history, not just the last"*) | Equivalente al `preserve_thinking: true` de la card. Coste: consume más contexto |
| **Limitar el presupuesto de thinking** | CLI: `--reasoning-budget N` (dump: *"-1 for unrestricted, 0 for immediate end, N>0 for token budget"*, default -1) | Con contexto 16K, un budget (p.ej. 4096) evita que un thinking largo se coma el espacio de la respuesta |

**Nota de contexto:** el modelo soporta 262,144 nativo y la card recomienda ≥128K para thinking; este rig corre `-c 16384` (mitigación issue #23577 para MTP). Con 16K, thinking largos + preserve pueden agotar el contexto antes de la respuesta final: si ves respuestas cortadas, o bajas a `-c 12288`, o activas `--reasoning-budget 4096`, o usas preset fast para chat cotidiano.

---

## §4. Visión (mmproj) — decisión para este rig

El modelo base es multimodal (vision encoder). El dump confirma: *"mmproj is also downloaded automatically if available. to disable, add --no-mmproj"* y *"--mmproj-offload ... (default: enabled)"*.

**Decisión para el rig:** el lanzador pasa **`--no-mmproj`** (text-only). Razones: (a) el mmproj consume ~0.90 GB de VRAM que la GTX 1650 4GB no tiene de sobra durante decode; (b) el GGUF local no lleva mmproj anexo — mantenerlo fuera elimina toda sorpresa de descarga automática; (c) el Director no usa visión hoy. Si algún día quiere imágenes: descargar el `mmproj-F16.gguf` (~0.90 GB) junto al modelo y relanzar con `--mmproj D:\ZLia\models\mmproj-F16.gguf` (el launcher lo soporta vía `--mmproj FILE`, que desactiva el `--no-mmproj`).

---

## §5. MTP × sampling — qué está verificado y qué toca medir

Verificado hasta hoy:
- `--spec-type draft-mtp` presente y usable en b11856 (dump verbatim); `--spec-draft-n-max` default 3, mitigación #23577 usa 2 con `-c 16384`.
- PR #22673 declara *"more than 2x speed-up with ~75% acceptance"*; V2 documentado añade `--spec-draft-p-min 0.75` (dump: *"minimum speculative decoding probability (greedy)"*, default 0.00).
- El dump muestra stats de aceptación en el log del server (líneas `draft acceptance rate = ...`) — el Director podrá LEER la aceptación real de su rig en `sweep-logs`.

No verificado (a medir en el rig, no afirmado):
- El efecto de temperature 1.0 (preset think) sobre la tasa de aceptación de los drafts. Si el speedup V2 se siente menor en chat thinking que en fast, es el candidato #1 a investigar. El protocolo: tras el sweep, medir V2 con preset fast vs think y comparar `draft acceptance rate` en el log.

---

## §6. Extras profesionales del server (todas en el dump; ninguna necesaria hoy)

| Flag | Default | Para qué serviría en este rig |
|------|---------|-------------------------------|
| `--cache-reuse N` | 0 | Reusar KV entre turnos por KV-shifting (chats largos con system prompt fijo; requiere prompt caching). Candidato a probar DESPUÉS del sweep |
| `--keep N` | 0 | Mantener tokens del prompt inicial (con system prompt grande, `--keep` evita que se evicte) |
| `-np, --parallel N` | -1 (auto) | Slots paralelos. En este rig: 1 solo slot (cada slot reparte KV) — NO tocar |
| `-to, --timeout N` | 3600 | Timeout de lectura/escritura; el default sobra |
| `--slots` | enabled | Endpoint de monitorización de slots (útil para depurar) |
| `--grammar` / `-j, --json-schema` | — | Salida estructurada (JSON forzado) por request |
| `--warmup, --no-warmup` | enabled | El warmup hace el JIT PTX de la primera ejecución (coste ya conocido del rig) |
| `-kvu, --kv-unified` | (ver dump) | Buffer KV unificado compartido entre secuencias; irrelevante con 1 slot |

---

## §7. Guardarraíles

1. **Ninguna flag de este documento está inventada**: todas verbatim de `llama-flags-nuevo.txt` o de la card/generation_config oficial de Qwen3.6-35B-A3B (fetch 2026-10-25).
2. **El sampling NO afecta al sweep** que ya tiene agendado el Director: las mediciones del barrido `-ncmoe` usan requests con `temperature: 0.0` explícito — los defaults CLI del server quedan sobrescritos por request.
3. **Cambios en el lanzador v1.1**: `--preset` (sampling) y `--no-mmproj`. Ninguno altera el rendimiento medible del sweep; ambos mejoran la configuración de chat real.
4. Preset default del lanzador = **think** (el modelo piensa por defecto; es su modo natural).
5. Si aparece mezcla de idiomas en respuestas thinking: primera sospecha `presence_penalty` — probar 1.5 por-request (variante literal de la card, §1.1) y anotar el resultado en RUTAS §11.

## §8. Fuentes (URLs consultadas 2026-10-25)

- Card oficial: `https://huggingface.co/Qwen/Qwen3.6-35B-A3B` (presets, thinking por defecto, no-soft-switch, preserve_thinking, contexto 262,144)
- `https://huggingface.co/Qwen/Qwen3.6-35B-A3B/raw/main/generation_config.json` (fábrica: temp 1.0 / top_k 20 / top_p 0.95, sin presence)
- Doc familia: `https://qwen.readthedocs.io/en/latest/getting_started/quickstart.html` (no greedy; antecedente Qwen3)
- Dump propio: `InformacionCritica/llama-flags-nuevo.txt` (todas las flags CLI citadas)
- PR ggml-org/llama.cpp#22673 (draft-mtp, ~75% acceptance) — verificado 2026-10-24
- Card cuantizador: `https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF` (comando ejemplo del autor: `-ncmoe 16 ... --spec-type draft-mtp --spec-draft-n-max 2`)
