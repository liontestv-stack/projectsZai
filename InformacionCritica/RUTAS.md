# RUTAS — Del techo real al objetivo x2 (16 → ~32 t/s)

> **Archivo crítico del proyecto.** Compañero obligatorio: [`llama-flags.txt`](llama-flags.txt) —
> ninguna flag usada en este proyecto puede salir de esa lista. Verificadas contra la
> documentación oficial de llama.cpp el **2026-10-24**.

**Rig:** i3-10100F (4C/8T) · GTX 1650 4GB · 16GB DDR4-2666 · SSD 500GB · Presupuesto $0
**Modelo:** `SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF` → archivo `...APEX-I-MINI.gguf` (12.2 GB)

---

## 0. Corrección fundamental (el Director tenía razón)

**16 t/s NO es un techo físico. Era un síntoma de configuración.**

El cuello de botella real es el ancho de banda de la DDR4-2666 (~38 GB/s útiles), pero ese
cuello solo gobierna la **lectura de expertos activos por token** (~1.0–1.1 GB/token en
APEX Mini). La aritmética honesta da un techo base de **~30–35 t/s** antes de cualquier
truco, y el truco correcto (MTP) multiplica ese número sin gastar un byte más de ancho de
banda:

- **Verificación especulativa en batch:** un pase forward lee los expertos **una vez** y
  verifica N tokens a la vez. Si el draft acierta ~2 tokens por paso, obtienes ~2 tokens
  por el precio de **una** lectura de expertos. Eso es el x2 sin hardware nuevo.
- Lo que había a 16 t/s era una combinación de: sin barrido de `-ncmoe`, sin MTP, KV en
  f16 comiendo VRAM, y carga con mmap compitiendo con el sistema.

## 1. Las tres palancas (en orden de impacto)

| # | Palanca | Flags (de llama-flags.txt) | Efecto esperado aquí |
|---|---------|----------------------------|----------------------|
| 1 | **MTP nativo** — el GGUF trae las 20 capas MTP preservadas | `--spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0.75` | **+20–50%** (dato del propio autor SC117); más si se afina `p-min` |
| 2 | **Barrido `-ncmoe`** — atención/KV en GPU, expertos en RAM | `-ngl 99` + `-ncmoe N` (sweep) | base 20–28 t/s (vs 16 inicial) |
| 3 | **VRAM liberada** — KV cuantizado + flash attention | `-fa on -ctk q8_0 -ctv q8_0` (-ub/-c si aprieta) | habilita la palanca 2; evita el spill silencioso |

## 2. Evidencia (todo verificado, nada inventado)

| Fuente | Hardware | Config | Resultado |
|--------|----------|--------|-----------|
| [Model card SC117](https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF) | DGX Spark GB10 | `--spec-type draft-mtp --spec-draft-n-max 2` | **+20–50%** declarado por el autor; APEX Mini 12.2 GB: PPL 7.088, HellaSwag 81.0%, 74.4 t/s |
| [mdda.net — MoE en GTX 1080](https://mdda.net/blog/tech/dl/llama-cpp-moe-on-an-old-gpu) | GTX 1080 8GB + CPU vieja | `-ngl 999 -ncmoe 30`, 35B-A3B Q4_K_M | **~25 t/s** tg |
| r/LocalLLaMA (2026) | 8GB VRAM | `-ncmoe 38` tuneado, 35B MoE | 10–12 → **36.6 t/s** |
| [Foro NVIDIA (blainesworld)](https://forums.developer.nvidia.com/t/mtp-llama-cpp-a-look-at-qwen3-6-27b/370298) | DGX Spark GB10 | Qwen3.6-27B, `n-max 5` + `p-min 0.75` | **28–31 t/s** estables |
| [llama.cpp discussion #25198](https://github.com/ggml-org/llama.cpp/discussions/25198) | RTX 5090 | `n-max 8` + `p-min 0.8` | 47 → **163–178 t/s** (referencia del techo de aceptación) |
| [Unsloth — guía MTP](https://unsloth.ai/docs/models/mtp) | RTX 6000 | 35B-A3B MTP | 240 t/s (techo absoluto de referencia) |
| Física del rig | 38 GB/s ÷ ~1.05 GB/token | expertos en RAM, atención en GPU | ~30–35 t/s base posibles |

**Conclusión:** duplicar 16 → ~32 t/s en este rig sin gastar $1 está respaldado por las
tres palancas combinadas. No es optimismo: es ancho de banda + aceptación de draft.

---

## 3. RUTA 1 — Arranque garantizado (línea base, ~10 min)

Comando canónico (está consagrado al final de `llama-flags.txt`): `-ngl 99 -cmoe` pone
**todo** en su sitio sin oportunidad de OOM. Medir t/s con una pregunta larga repetida 3 veces.

```bat
D:\apex35b\llama\llama-server.exe ^
  -m D:\apex35b\models\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf ^
  -a apex35b ^
  -ngl 99 -cmoe ^
  -c 16384 -b 2048 -ub 256 ^
  -fa on -ctk q8_0 -ctv q8_0 ^
  -t 4 --prio 2 ^
  --jinja ^
  --host 127.0.0.1 --port 8080
```

(En PowerShell, sustituir `^` por `` ` `` al final de cada línea.)

## 4. RUTA 2 — Barrido de `-ncmoe` (el acantilado, ~40 min)

Con la línea base medida, liberar expertos de RAM hacia el acantilado de VRAM:

1. Sustituir `-cmoe` por `-ncmoe 48` → medir. Repetir: `44 → 40 → 36 → 32 …` de 4 en 4.
2. Vigilar VRAM con `nvidia-smi -l 1` (o Administrador de tareas → GPU).
3. **El acantilado es silencioso:** si te pasas, no hay error — la velocidad se hunde
   brutalmente. Al verlo, retroceder un paso y quedarse ahí.
4. Anotar el ganador en este archivo (sección 10).

## 5. RUTA 3 — MTP fino (el multiplicador, ~20 min)

Con el ganador del barrido, añadir la palanca 1 y afinar:

| Prueba | Flags a añadir | Qué mirar |
|--------|----------------|-----------|
| Base MTP | `--spec-type draft-mtp --spec-draft-n-max 2` | `draft acceptance rate` en el log del server |
| Afinado | `… --spec-draft-n-max 2 --spec-draft-p-min 0.75` | aceptación ≥ 0.70 |
| Agresivo (código) | `--spec-draft-n-max 4 --spec-draft-p-min 0.8` | t/s en tareas de código |
| Exploratorio | `--spec-draft-n-max 8 --spec-draft-p-min 0.8` | solo si la RAM/VRAM sobran |

- La aceptación del draft se imprime en el log: **ese número es la verdad**, no la sensación.
- Si el draft hunde el rendimiento (pasa en ancho de banda bajo), dejar `n-max 2` y listo:
  el +20–50% del autor ya está cobrado.
- Advertencia conocida: el camino MTP ha tenido crashes ocasionales en builds concretas →
  mantener llama.cpp actualizado y, si aparece, reportar versión exacta.

## 6. RUTA 4 — Alivio de VRAM (si el acantilado llega muy pronto)

Aplicar **de a una** y medir: `-c 8192` → `-ub 128` → `-b 1024` → `-ctv q4_0`
(manteniendo `-ctk q8_0`). Nunca usar `-nkvo`: mandaría el KV a RAM y hundiría todo.

## 7. RUTA 5 — Alivio de RAM (si hay pageouts / micro-congelamientos)

`--mlock` ya no existe (eliminado de llama.cpp en 2026 — ver BLOQUEADAS). El control es
`-lm`:

- Default `-lm auto` (mmap). Si el sistema pagina: probar `-lm none` (carga plana, menos
  pageouts). `mlock` queda **prohibido** en este rig: 12.2 GB de pesos sobre 16 GB de RAM.
- Mantener apps pesadas cerradas mientras se sirve el modelo.

## 8. RUTA 6 — Planes B y C (solo si lo anterior falla)

- **Plan B (quant):** mismo tier APEX Mini del mirror de LocalAI
  ([mudler/Qwen3.6-35B-A3B-APEX-GGUF](https://www.modelscope.cn/models/mudler/Qwen3.6-35B-A3B-APEX-GGUF)),
  o el [MTP-GGUF oficial de Unsloth](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF)
  (IQ4_NL **no cabe** en 16 GB de RAM → usar solo sus tiers ≤ 13 GB).
  NOTA: los tiers más grandes (I-Compact 15.85 GB, I-Quality 21.9 GB) exigen más RAM de la
  que existe — quedan fuera hasta que haya hardware.
- **Plan C (futuro, rompe el $0):** +16 GB RAM (~$35 usado) habilita `-lm mlock` y
  I-Compact; una RTX 3060 12GB usada mueve TODOS los expertos a VRAM y deja el CPU libre.

## 9. Conexión de airi / pi dev (intocable)

`llama-server` YA ES el servidor OpenAI (lección del proyecto anterior: cero scripts Python).

| App | Configuración |
|-----|---------------|
| **airi** | Provider OpenAI-compatible → `http://127.0.0.1:8080/v1` · API key `no-key` · Model `apex35b` |
| **pi dev** | Ídem, endpoint OpenAI apuntando a `/v1` |

## 10. Registro del comando ganador (lo escribe el Director tras medir)

```text
(placeholder — pegar aquí el comando vencedor con su t/s base y t/s MTP)
```

## 11. Guardarraíles

1. **SOLO flags de `llama-flags.txt`.** Si no está ahí, no existe (ni `-ncmoe` mal escrito,
   ni alias de 2024, ni magias de foro).
2. `--mlock`, `--no-mmap`, `--spec-type mtp`, `turbo*`, `--draft-max`: **bloqueadas** (lista completa en el txt).
3. Cero scripts Python custom. Cero Ollama para este modelo (no expone MTP ni `-ncmoe` fino).
4. Medir siempre: t/s de generación, aceptación del draft, VRAM y RAM en cada cambio. Sin
   medición no hay conclusión, solo anécdota.

## 12. Fuentes

- Documentación oficial speculative: https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md
- Server README (flags): https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- Manpage llama-server(1): https://manpages.debian.org/unstable/llama.cpp-tools/llama-server.1.en.html
- Model card del autor (SC117) — comando oficial, benchmarks APEX: https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF
- Discusión MTP + p-min (#25198): https://github.com/ggml-org/llama.cpp/discussions/25198
- Guía MTP de Unsloth: https://unsloth.ai/docs/models/mtp
- Foro NVIDIA (Qwen3.6-27B MTP en GB10): https://forums.developer.nvidia.com/t/mtp-llama-cpp-a-look-at-qwen3-6-27b/370298
- Flags explicadas 2026 (cambio -lm/--load-mode): https://openclawdc.com/blog/llama-cpp-flags-explained
- Dossier completo previo: [`investigacion-35b-apex/`](../investigacion-35b-apex/README.md)
