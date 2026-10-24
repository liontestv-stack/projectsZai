# RUTAS — Del techo real al objetivo x2 (16 → ~32 t/s)

> **Archivo crítico del proyecto.** Vive en `InformacionCritica/` junto a:
> - [`llama-flags.txt`](llama-flags.txt) — **FUENTE DE VERDAD #1**: dump real de `--help` del build del Director (UTF-16, intocado). Nada fuera de ese dump existe para este proyecto.
> - [`flags-verificadas-LAIA.txt`](flags-verificadas-LAIA.txt) — destilado verificado por LAIA (docs oficiales + auditoría del dump del Director).
> - [`RutasArchivos.md`](RutasArchivos.md) — rutas reales en disco: modelo `D:\ZLia\models\...APEX-I-MINI.gguf` · server `D:\llama.cpp\build\bin\llama-server.exe`.

**Rig:** i3-10100F (4C/8T) · GTX 1650 4GB · 16GB DDR4-2666 · SSD 500GB · Presupuesto $0
**Modelo:** `...APEX-I-MINI.gguf` (**14.27 GB reales**, verificado vía [API de HF](https://huggingface.co/api/models/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF?blobs=true); la tabla del autor dice "12.2 GB" de perfil — manda el archivo real. 20 capas MTP preservadas, heretic: −88% rechazos, 59.5k descargas/mes)

---

## 0. Corrección fundamental (el Director tenía razón)

**16 t/s NO es un techo físico. Era un síntoma de configuración.**

El cuello real es el ancho de banda de la DDR4-2666 (~38 GB/s útiles), pero ese cuello solo
gobierna la **lectura de expertos activos por token** (~1.0–1.1 GB/token en APEX Mini). La
aritmética honesta da un techo base de **~30–35 t/s** antes de trucos, y el truco correcto
(MTP) lo multiplica **sin gastar un byte más de ancho de banda**: un pase forward lee los
expertos UNA vez y verifica N tokens a la vez — N tokens por el precio de una lectura.

**Segunda causa identificada (auditoría 2026-10-24):** el archivo real pesa **14.27 GB**
sobre 16 GB de RAM → margen de ~1.5 GB para SO + KV + buffers → pageouts casi garantizados
con mmap. Eso roba t/s por sí solo. Mitigación: pagefile en el SSD dedicado (absorbe el
overflow), medir varianza, y contar con que **MTP multiplica igual** (la aceptación del
draft no cambia el tráfico de expertos por pase).

**PERO la auditoría del dump del Director (`llama-flags.txt`) reveló:** su build actual
**no tiene `draft-mtp`** (su `--spec-type` solo lista tipos n-gram; cero ocurrencias de
"mtp"). El build es una versión intermedia: tiene `--spec-draft-*` pero todavía usa el
sistema viejo de carga (`--mlock/--no-mmap`, sin `-lm`). **Por eso la RUTA 0 es
actualizar el build — sin eso, la palanca del x2 no existe.**

## 1. Las palancas, en orden de impacto

| # | Palanca | Flags | Estado en el build actual | Efecto esperado |
|---|---------|-------|---------------------------|-----------------|
| 0 | **Actualizar binario** | zip oficial precompilado (§3-A) o `git pull` + recompilar (§3-B) | ⛔ bloqueante para MTP | desbloquea el x2 |
| 1 | **MTP nativo** (20 capas preservadas en el GGUF) | `--spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0.75` | ❌ requiere RUTA 0 | **+20–50%** (dato del autor) y más con `p-min` |
| 2 | **Barrido `-ncmoe`** | `-ngl 99` + `-ncmoe N` | ✅ disponible HOY | base 20–28 t/s (vs 16) |
| 3 | **VRAM liberada** | `-fa on -ctk q8_0 -ctv q8_0` | ✅ disponible HOY | habilita la palanca 2 |

## 2. Evidencia (nada inventado; todo citado)

| Fuente | Hardware | Config | Resultado |
|--------|----------|--------|-----------|
| [Model card SC117](https://huggingface.co/SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF) | DGX Spark GB10 | `--spec-type draft-mtp --spec-draft-n-max 2` | **+20–50%** declarado por el autor; APEX Mini 12.2 GB: PPL 7.088, HellaSwag 81.0%, 74.4 t/s |
| [mdda.net](https://mdda.net/blog/tech/dl/llama-cpp-moe-on-an-old-gtx-1080) | GTX 1080 8GB + CPU vieja | `-ngl 999 -ncmoe 30`, 35B-A3B Q4_K_M | **~25 t/s** tg (24.94 medidos; verificado 2026-10-24) |
| r/LocalLLaMA (2026) | 8GB VRAM | `-ncmoe 38` tuneado | 10–12 → **36.6 t/s** |
| [Foro NVIDIA](https://forums.developer.nvidia.com/t/mtp-llama-cpp-a-look-at-qwen3-6-27b/370298) | DGX Spark GB10 | Qwen3.6-27B, `n-max 5` + `p-min 0.75` | **28–31 t/s** estables |
| [llama.cpp #25198](https://github.com/ggml-org/llama.cpp/discussions/25198) | RTX 5090 | `n-max 8` + `p-min 0.8` | 47 → **163–178 t/s** |
| **[PR #22673](https://github.com/ggml-org/llama.cpp/pull/22673)** "llama + spec: MTP Support" — VERIFICADO: fusionado **2026-05-16** | — | introduce `--spec-type draft-mtp`, `--spec-draft-n-max`, `ngram-mod`, `--spec-default` | declara **"more than 2x speed-up over baseline with ~75% acceptance"** |
| [Release notes v0.7.0](https://github.com/ggml-org/llama.cpp/releases/tag/v0.7.0) (oficial, 2026-10-15) | — | — | puerto default 8080→9931; nueva caché MoE en RAM host ("up to 2.2x faster decode"); nightly del día: b11856 |
| [Unsloth MTP](https://unsloth.ai/docs/models/mtp) | RTX 6000 | 35B-A3B MTP | 240 t/s (techo de referencia) |
| Auditoría del dump del Director | su build | `--help` completo | build intermedio: sin `draft-mtp`, con `--mlock/--no-mmap`, sin `-lm` |

---

## 3. RUTA 0 — Actualizar el binario (~10–15 min, $0) ← EMPEZAR AQUÍ

**¿Recompilar? NO es obligatorio.** Dos caminos; el 3-A no necesita Visual Studio ni
CUDA Toolkit. Ambos terminan igual: dump regenerado + b-number anotado.

Antes de tocar nada, registrar el punto de partida (la flag existe en tu build, línea 4
del dump):

```bat
D:\llama.cpp\build\bin\llama-server.exe --version
```

### 3-A.0 Verificación previa en TU máquina (2 min, antes de descargar nada)

```bat
D:\llama.cpp\build\bin\llama-server.exe --version
dir D:\llama.cpp\build\bin\*.dll
nvidia-smi
```

- 1ª: imprime tu **b-number VIEJO** → anótalo en el registro de abajo (pin de comparación).
- 2ª: lista las DLLs junto a tu exe actual (`cudart64_*.dll`, `cublas64_*.dll`,
  `cublasLt64_*.dll` si tu build es dinámico; si no aparece ninguna, tu build las lleva
  enlazadas por dentro — también vale).
- 3ª: arriba a la derecha dice **"CUDA Version"** = CUDA MÁXIMO que soporta tu driver.
  Para los zips 12.4 basta **≥ 12.0** (ideal ≥ 12.4). GTX 1650 con driver de los últimos
  años da 12.x de sobra.
- Lógica: tu build VIEJO ya corre el modelo en GPU → tu CUDA actual funciona. Los zips
  nuevos traen SUS PROPIAS DLLs (para eso existe el zip cudart): lo único compartido es
  el driver. Pegar las 3 salidas en el chat → LAIA las registra en el repo.

Variante que guarda las 3 salidas en un solo archivo (pegar después):

```bat
D:\llama.cpp\build\bin\llama-server.exe --version > D:\ZLia\revision-laia.txt 2>&1
dir D:\llama.cpp\build\bin\*.dll >> D:\ZLia\revision-laia.txt 2>&1
nvidia-smi >> D:\ZLia\revision-laia.txt 2>&1
echo LISTO — abrir D:\ZLia\revision-laia.txt
```

### 3-A.1 Descarga (nombres VERBATIM verificados 2026-10-24 en la página oficial de assets)

1. Ir a <https://github.com/ggml-org/llama.cpp/releases> → nightly b11856 (o el más
   reciente), descargar **LOS DOS zips, misma carpeta destino**:
   - `llama-b11856-bin-win-cuda-12.4-x64.zip` (binarios: exe + ggml-cuda.dll)
   - `cudart-llama-bin-win-cuda-12.4-x64.zip` (DLLs CUDA 12.4 — **OJO: este zip NO lleva
     el b-number en el nombre**; así es exactamente como se llama, verificado verbatim
     contra la página de assets del release)
   - Elegir **CUDA 12.4** (no 13.4): máxima compatibilidad con el driver de la GTX 1650.
   - Plan B solo si el driver diera problemas: `llama-b11856-bin-win-vulkan-x64.zip`
     (no usa CUDA para nada) — CUDA rinde más; vulkan solo como rescate.
2. Descomprimir AMBOS en una carpeta NUEVA, ej. `D:\llama.cpp\bin-new\` (las DLLs deben
   quedar junto a los .exe). **NO borrar** `D:\llama.cpp\build\bin\` — es tu rollback.
   Verificación inmediata: `dir D:\llama.cpp\bin-new\*.dll` debe mostrar las DLLs de la
   serie CUDA 12 (`cudart64_12.dll`, `cublas64_12.dll`, `cublasLt64_12.dll`) junto a los
   .exe. Si falta alguna, no se siguió descomprimiendo bien.
3. Verificar ANTES de usar (DEBE aparecer `draft-mtp`; PR #22673, fusionado 2026-05-16;
   `--version` es válido en todos los builds recientes):

```bat
D:\llama.cpp\bin-new\llama-server.exe --version
D:\llama.cpp\bin-new\llama-server.exe --help | findstr draft-mtp
```

   Si `findstr` no devuelve nada → no usar ese binario, avisar. Si en el zip NO existe
   `llama-server.exe` → **NO improvisar**: un blog tercero afirma que los binarios se
   consolidaron en `llama.exe serve`, pero el README oficial del server no lo menciona
   (claim NO verificado) — anotar qué .exe trae el zip y avisar antes de seguir.
4. Si `findstr draft-mtp` responde: regenerar el dump (igual que el actual, generado
   desde PowerShell → queda UTF-16 como el original):

```bat
D:\llama.cpp\bin-new\llama-server.exe --help > D:\ZLia\llama-flags-nuevo.txt
```

   Luego subir `llama-flags-nuevo.txt` a `InformacionCritica/` del repo en lugar del
   anterior (generado desde PowerShell conserva el formato UTF-16 del original). Cuando
   el nuevo dump esté en el repo, LAIA re-audita las flags contra él antes de ejecutar V2.

**Avisos verificados en las release notes oficiales v0.7.0 (2026-10-15):**
- El **puerto por defecto cambió de 8080 a 9931** → los comandos V1/V2 ya pasan
  `--port 8080` explícito: **NO quitarlo** o airi/pi perderá la conexión.
- Nueva palanca MoE: caché de expertos en RAM host (`moe_cache_size`, el autor declara
  "up to 2.2x faster decode") → candidata real para este rig, pero NO se toca hasta
  re-auditarla contra TU nuevo dump (regla del guardarrail 2).
- Las flags de MoE (`-cmoe/-ncmoe`) pueden haber cambiado de nombre/forma — por eso el
  paso 4 regenera el dump ANTES de ejecutar V2.

### 3-B. Recompilar tu build local (alternativa, mismo resultado)

Requisitos (docs/build.md): Visual Studio 2022 + CUDA Toolkit (nvcc en PATH). El
directorio `build/` existente se reutiliza — CMake reconfigura solo tras el pull.

```bat
cd D:\llama.cpp
git pull
cmake --build build --config Release -j
```

Verificación post-build (DEBE aparecer draft-mtp; PR #22673, fusionado 2026-05-16):

```bat
D:\llama.cpp\build\bin\llama-server.exe --version
D:\llama.cpp\build\bin\llama-server.exe --help | findstr draft-mtp
D:\llama.cpp\build\bin\llama-server.exe --help > InformacionCritica\llama-flags.txt   (regenerar el dump tras actualizar)
```

Si `git pull` rompe el build (deps nuevas): `rmdir /s /q build` y reconfigurar
`cmake -B build -DGGML_CUDA=ON` + compilar. Tras actualizar, **las reglas de carga
cambian** (`--mlock/--no-mmap` desaparecen, entra `-lm`) — ver sección 8.

📌 **ANOTAR el `b-number` que imprima `--version`** (ej. `b8797`) aquí abajo — es el pin
de versión del proyecto; todo diagnóstico futuro cita ese número. Anotar también el
b-number del build VIEJO como referencia de comparación:

```text
Build VIEJO (base 16 t/s): b-XXXX (pegar aquí) — fecha: __/__/____
Build actualizado:        b-XXXX (pegar aquí) — fecha: __/__/____
```

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
2. Draft pequeño en GPU: `-md <draft.gguf> -ngld all --spec-draft-n-max 4` (~0.6 GB extra). ⚠ El draft NO está en tu disco: hay que descargarlo primero (GGUF pequeño de la MISMA familia/tokenizer — ej. el 0.8B/2B de Qwen3.x en HF) y dejarlo en `D:\ZLia\models\`. Sin draft descargado esta opción no existe — usa la 1.

## 7. RUTA 4 — Alivio de VRAM (si el acantilado llega muy pronto)

De a una y midiendo: `-c 8192` → `-ub 128` → `-b 1024` → `-ctv q4_0` (mantener
`-ctk q8_0`). Nunca `-nkvo`: mandaría el KV a RAM y hundiría la generación.

## 8. RUTA 5 — Alivio de RAM (regla relativa al build, OJO)

- **Realidad del archivo real (14.27 GB / 16 GB de RAM):** margen ~1.5 GB → pageouts
  probables. Pagefile en el SSD dedicado, administrado por el sistema (absorbe overflow).
- **Build actual (auditado):** `--mmap` activo por defecto. Si hay pageouts →
  `--no-mmap` (carga plana, menos pageouts) — ⚠ con 14.27 GB proba primero con margen;
  si OOM, volver a mmap. `--mlock` **prohibido en este rig**, aunque la flag exista.
- **Build actualizado:** esas flags desaparecen; el control pasa a `-lm none` /
  `-lm mmap` / `-lm mlock`. Misma prohibición de mlock por RAM.

## 9. RUTA 6 — Planes B y C (solo si lo anterior falla)

- **Plan B (quant):** mirror APEX de LocalAI ([mudler](https://www.modelscope.cn/models/mudler/Qwen3.6-35B-A3B-APEX-GGUF)) o [MTP-GGUF de Unsloth](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF) — en 16 GB de RAM solo cabe I-MINI (14.27 GB, justo — ver sección 8). I-Compact (**17.02 GB**) e I-Quality (**23.51 GB**, verificados en API de HF) quedan fuera hasta haber hardware.
- **Plan C (rompe el $0):** +16 GB RAM (~$35 usado) habilita mlock e I-Compact; RTX 3060 12GB usada lleva TODOS los expertos a VRAM.

## 10. Conexión de airi / pi dev (intocable)

`llama-server` YA ES el servidor OpenAI (lección del proyecto anterior: cero scripts Python).

| App | Configuración |
|-----|---------------|
| **airi** | Provider OpenAI-compatible → `http://127.0.0.1:8080/v1` · API key `no-key` · Model `apex35b` |
| **pi dev** | Ídem, endpoint OpenAI apuntando a `/v1` |

⚠ **Tras actualizar el binario (v0.7.0+):** el puerto por defecto del server cambió de
8080 a 9931 → **mantener `--port 8080` explícito** en el comando (V1/V2 ya lo llevan).
Si algún día lo quitas, airi/pi deja de conectar sin mensaje de error claro.

**Visión (opcional, al FINAL de todo):** el repo SÍ incluye
`mmproj-Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-F16.gguf` (0.90 GB,
verificado en la API de HF) → flag `-mm <archivo>`. En este rig cuesta ~0.9 GB de
RAM/VRAM: activarlo solo después de tener el comando ganador estable.

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
7. Tras actualizar: **no quitar `--port 8080`** (default nuevo: 9931) y regenerar el dump
   antes de creerle a cualquier flag nueva (ej. la caché MoE en host de v0.7.0: auditar
   contra el dump primero, ejecutar después).

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
