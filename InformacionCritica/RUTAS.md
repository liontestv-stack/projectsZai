# RUTAS — Del techo real al objetivo x2 (16 → ~32 t/s)

> **Archivo crítico del proyecto.** Vive en `InformacionCritica/` junto a:
> - [`llama-flags.txt`](llama-flags.txt) — **FUENTE DE VERDAD #1**: dump real de `--help` del build del Director (UTF-16, intocado). Nada fuera de ese dump existe para este proyecto.
> - [`flags-verificadas-LAIA.txt`](flags-verificadas-LAIA.txt) — destilado verificado por LAIA (docs oficiales + auditoría del dump del Director).
> - [`RutasArchivos.md`](RutasArchivos.md) — rutas reales en disco: modelo `D:\ZLia\models\...APEX-I-MINI.gguf` · server `D:\llama.cpp\build\bin\llama-server.exe`.

**Rig:** i3-10100F (4C/8T) · GTX 1650 4GB · 16GB DDR4-2666 · SSD 500GB · Presupuesto $0
**Modelo:** `...APEX-I-MINI.gguf` (12.2 GB, 20 capas MTP preservadas, heretic: −88% rechazos)

---

## 0. Corrección fundamental (el Director tenía razón)

**16 t/s NO es un techo físico. Era un síntoma de configuración.**

El cuello real es el ancho de banda de la DDR4-2666 (~38 GB/s útiles), pero ese cuello solo
gobierna la **lectura de expertos activos por token** (~1.0–1.1 GB/token en APEX Mini). La
aritmética honesta da un techo base de **~30–35 t/s** antes de trucos, y el truco correcto
(MTP) lo multiplica **sin gastar un byte más de ancho de banda**: un pase forward lee los
expertos UNA vez y verifica N tokens a la vez — N tokens por el precio de una lectura.

**PERO la auditoría del dump del Director (`llama-flags.txt`) reveló:** su build actual
**no tiene `draft-mtp`** (su `--spec-type` solo lista tipos n-gram; cero ocurrencias de
"mtp"). El build es una versión intermedia: tiene `--spec-draft-*` pero todavía usa el
sistema viejo de carga (`--mlock/--no-mmap`, sin `-lm`). **Por eso la RUTA 0 es
actualizar el build — sin eso, la palanca del x2 no existe.**

## 1. Las palancas, en orden de impacto

| # | Palanca | Flags | Estado en el build actual | Efecto esperado |
|---|---------|-------|---------------------------|-----------------|
| 0 | **Actualizar build** | `git pull` + recompilar | ⛔ bloqueante para MTP | desbloquea el x2 |
| 1 | **MTP nativo** (20 capas preservadas en el GGUF) | `--spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0.75` | ❌ requiere RUTA 0 | **+20–50%** (dato del autor) y más con `p-min` |
| 2 | **Barrido `-ncmoe`** | `-ngl 99` + `-ncmoe N` | ✅ disponible HOY | base 20–28 t/s (vs 16) |
| 3 | **VRAM liberada** | `-fa on -ctk q8_0 -ctv q8_0` | ✅ disponible HOY | habilita la palanca 2 |

## 2. Evidencia (nada inventado; todo citado)

| Fuente | Hardware | Config | Resultado |
|--------|----------|--------|-----------|
| [Model card SC117](https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF) | DGX Spark GB10 | `--spec-type draft-mtp --spec-draft-n-max 2` | **+20–50%** declarado por el autor; APEX Mini 12.2 GB: PPL 7.088, HellaSwag 81.0%, 74.4 t/s |
| [mdda.net](https://mdda.net/blog/tech/dl/llama-cpp-moe-on-an-old-gpu) | GTX 1080 8GB + CPU vieja | `-ngl 999 -ncmoe 30`, 35B-A3B Q4_K_M | **~25 t/s** tg |
| r/LocalLLaMA (2026) | 8GB VRAM | `-ncmoe 38` tuneado | 10–12 → **36.6 t/s** |
| [Foro NVIDIA](https://forums.developer.nvidia.com/t/mtp-llama-cpp-a-look-at-qwen3-6-27b/370298) | DGX Spark GB10 | Qwen3.6-27B, `n-max 5` + `p-min 0.75` | **28–31 t/s** estables |
| [llama.cpp #25198](https://github.com/ggml-org/llama.cpp/discussions/25198) | RTX 5090 | `n-max 8` + `p-min 0.8` | 47 → **163–178 t/s** |
| [Unsloth MTP](https://unsloth.ai/docs/models/mtp) | RTX 6000 | 35B-A3B MTP | 240 t/s (techo de referencia) |
| Auditoría del dump del Director | su build | `--help` completo | build intermedio: sin `draft-mtp`, con `--mlock/--no-mmap`, sin `-lm` |

---

## 3. RUTA 0 — Actualizar el build local (~15 min, $0) ← EMPEZAR AQUÍ

El server vive en `D:\llama.cpp\build\bin\` → es un build local de fuentes. Actualizarlo:

```bat
cd D:\llama.cpp
git pull
cmake --build build --config Release -j
```

Verificación post-build (DEBE aparecer draft-mtp):

```bat
D:\llama.cpp\build\bin\llama-server.exe --version
D:\llama.cpp\build\bin\llama-server.exe --help | findstr draft-mtp
D:\llama.cpp\build\bin\llama-server.exe --help > InformacionCritica\llama-flags.txt   (regenerar el dump tras actualizar)
```

Si `git pull` rompe el build (deps nuevas): `rmdir /s /q build` y reconfigurar
`cmake -B build -DGGML_CUDA=ON` + compilar. Tras actualizar, **las reglas de carga
cambian** (`--mlock/--no-mmap` desaparecen, entra `-lm`) — ver sección 8.

## 4. RUTA 1 — Arranque garantizado (línea base, HOY, ~10 min)

Comando canónico V1 (consagrado en `flags-verificadas-LAIA.txt`): `-ngl 99 -cmoe` pone
todo en su sitio sin OOM posible. Medir t/s con un prompt largo repetido 3 veces.

```bat
D:\llama.cpp\build\bin\llama-server.exe ^
  -m D:\ZLia\models\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf ^
  -a apex35b ^
  -ngl 99 -cmoe ^
  -c 16384 -b 2048 -ub 256 ^
  -fa on -ctk q8_0 -ctv q8_0 ^
  -t 4 --prio 2 ^
  --jinja ^
  --host 127.0.0.1 --port 8080
```

(En PowerShell, sustituir `^` por `` ` ``.)

## 5. RUTA 2 — Barrido de `-ncmoe` (el acantilado, ~40 min)

1. Sustituir `-cmoe` por `-ncmoe 48` → medir. Repetir de 4 en 4: `44 → 40 → 36 → 32 …`
2. Vigilar VRAM (`nvidia-smi -l 1` o Administrador de tareas → GPU).
3. **El acantilado es silencioso:** pasado el límite no hay error, la velocidad se hunde.
   Retroceder un paso y quedarse.
4. Anotar el ganador en la sección 11.

## 6. RUTA 3 — El multiplicador: MTP (tras RUTA 0) + interinos (HOY)

**Con build actualizado (V2):** añadir
`--spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0.75`
→ leer `draft acceptance rate` en el log (ese número es la verdad). Probar luego
`n-max 4` y `n-max 8` con `--spec-draft-p-min 0.8` (matriz completa en
`flags-verificadas-LAIA.txt`). Si el draft hunde el rendimiento, quedarse en `n-max 2`:
el +20–50% ya está cobrado.

**Interinos válidos HOY (build sin MTP), en orden de preferencia:**
1. `--spec-type ngram-mod --spec-ngram-mod-n-match 24 --spec-ngram-mod-n-min 48 --spec-ngram-mod-n-max 64 --spec-draft-n-max 64` — gratis, brilla en código/repeticiones.
2. Draft pequeño en GPU: `-md D:\ZLia\models\qwen36-0.8b-q4_0.gguf -ngld all --spec-draft-n-max 4` (~0.6 GB de RAM/VRAM extra).

## 7. RUTA 4 — Alivio de VRAM (si el acantilado llega muy pronto)

De a una y midiendo: `-c 8192` → `-ub 128` → `-b 1024` → `-ctv q4_0` (mantener
`-ctk q8_0`). Nunca `-nkvo`: mandaría el KV a RAM y hundiría la generación.

## 8. RUTA 5 — Alivio de RAM (regla relativa al build, OJO)

- **Build actual (auditado):** `--mmap` activo por defecto. Si hay pageouts →
  `--no-mmap` (carga plana, menos pageouts). `--mlock` **prohibido en este rig**
  (12.2 GB de pesos sobre 16 GB de RAM), aunque la flag exista.
- **Build actualizado:** esas flags desaparecen; el control pasa a `-lm none` /
  `-lm mmap` / `-lm mlock`. Misma prohibición de mlock por RAM.

## 9. RUTA 6 — Planes B y C (solo si lo anterior falla)

- **Plan B (quant):** mirror APEX de LocalAI ([mudler](https://www.modelscope.cn/models/mudler/Qwen3.6-35B-A3B-APEX-GGUF)) o [MTP-GGUF de Unsloth](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF) — solo tiers ≤ 13 GB caben en 16 GB de RAM. I-Compact (15.85 GB) e I-Quality (21.9 GB) quedan fuera hasta haber hardware.
- **Plan C (rompe el $0):** +16 GB RAM (~$35 usado) habilita mlock e I-Compact; RTX 3060 12GB usada lleva TODOS los expertos a VRAM.

## 10. Conexión de airi / pi dev (intocable)

`llama-server` YA ES el servidor OpenAI (lección del proyecto anterior: cero scripts Python).

| App | Configuración |
|-----|---------------|
| **airi** | Provider OpenAI-compatible → `http://127.0.0.1:8080/v1` · API key `no-key` · Model `apex35b` |
| **pi dev** | Ídem, endpoint OpenAI apuntando a `/v1` |

## 11. Registro del comando ganador (lo escribe el Director tras medir)

```text
(placeholder — pegar aquí el comando vencedor con su t/s base y t/s MTP)
```

## 12. Guardarraíles

1. **Fuente de verdad #1 = `llama-flags.txt`** (tu build). #2 = `flags-verificadas-LAIA.txt`. Si una flag no está en ninguno: **no existe**.
2. Tras cada actualización del build: **regenerar el dump** (`--help > llama-flags.txt`) y re-verificar.
3. Bloqueadas siempre: `turbo*` en KV, `--spec-type mtp` (mal escrito), `--mlock` en este rig, `-nkvo`, `-ngl` bajo como control de memoria, `--draft-max` (nombre muerto).
4. Tras actualizar build: `--mlock/--no-mmap/--direct-io` dejan de existir → usar `-lm`.
5. Cero scripts Python custom. Cero Ollama para este modelo (no expone MTP ni `-ncmoe` fino).
6. Medir siempre: t/s, aceptación del draft, VRAM y RAM. Sin medición no hay conclusión.

## 13. Fuentes

- Dump del build del Director: [`llama-flags.txt`](llama-flags.txt) · Rutas reales: [`RutasArchivos.md`](RutasArchivos.md)
- Documentación oficial speculative: https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md
- Server README (flags): https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- Model card del autor (SC117): https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF
- Discusión MTP + p-min (#25198): https://github.com/ggml-org/llama.cpp/discussions/25198
- Guía MTP de Unsloth: https://unsloth.ai/docs/models/mtp
- Foro NVIDIA (Qwen3.6-27B MTP): https://forums.developer.nvidia.com/t/mtp-llama-cpp-a-look-at-qwen3-6-27b/370298
- Flags explicadas 2026 (cambio -lm/--load-mode): https://openclawdc.com/blog/llama-cpp-flags-explained
- Dossier completo: [`investigacion-35b-apex/`](../investigacion-35b-apex/README.md)
