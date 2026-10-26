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
"mtp"). El build es una versión intermedia — fechado 2026-10-24 vía `--version` + página
del commit en GitHub: fuente del **2026-05-06** (commit `2496f9c`, "mtmd : support
MiniCPM-V 4.6" #22529), **10 días ANTES** del merge de draft-mtp (PR #22673,
2026-05-16). Tiene `--spec-draft-*` pero todavía usa el sistema viejo de carga
(`--mlock/--no-mmap`, sin `-lm`). **Por eso la RUTA 0 es actualizar el build — sin eso,
la palanca del x2 no existe.**

## 1. Las palancas, en orden de impacto

| # | Palanca | Flags | Estado en el build actual | Efecto esperado |
|---|---------|-------|---------------------------|-----------------|
| 0 | **Actualizar binario** | zip oficial precompilado (§3-A) o `git pull` + recompilar (§3-B) | ⛔ bloqueante para MTP | desbloquea el x2 |
| 1 | **MTP nativo** (20 capas preservadas en el GGUF) | `--spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0.75` | ❌ requiere RUTA 0 | **+20–50%** (dato del autor) y más con `p-min` |
| 2 | **Barrido `-ncmoe`** | `-ngl 99` + `-ncmoe N` | ✅ disponible HOY | base 20–28 t/s (vs 16) |
| 3 | **VRAM liberada** | `-fa on -ctk q8_0 -ctv q8_0` | ✅ disponible HOY | habilita la palanca 2 |
| 4 | **Cache MoE en VRAM (LRU)** | `--moe-cache-mib N` | ❌ requiere RUTA 0 + re-auditoría | a probar (dato 5070 Ti: hasta x2; §3-C) |

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
   - Elegir **CUDA 12.4** (no 13.4): máxima compatibilidad con el driver de la GTX 1650
     — CONFIRMADO con tu hardware: driver 610.88 / CUDA UMD 13.3 → el 12.4 va de serie,
     el 13.4 NO (tu UMD es 13.3).
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
   Nota: la PRIMERA ejecución puede tardar más de lo normal — el driver JIT-compila el
   PTX para sm_75 (así cubre Turing el zip oficial, verbatim en §3-C.1); es normal y
   queda cacheado.
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

### 3-A.2 ¿Hay que descargar algo más? — cierre de dependencias VERIFICADO (2026-10-25)

Pregunta del Director: *"¿hay algo más aparte de llama.cpp que debamos descargar para
acelerar estabilidad, eficiencia o velocidad?"*. Respuesta corta: **NO — los DOS zips
de §3-A.1 ya lo son todo**. Esta vez la verificación no fue por documentación sino
**directa**: LAIA descargó los zips reales de b11856 y analizó su contenido binario.

**1) Contenido real del zip binario** (53 archivos, integridad OK):
- Trae TODOS los .exe (incl. `llama-server.exe` — el claim "llama.exe serve" queda
  definitivamente FALSO para b11856) y TODAS sus DLLs internas: `llama.dll`,
  `llama-server-impl.dll`, `llama-common.dll`, `mtmd.dll`, `ggml.dll`, `ggml-base.dll`,
  `ggml-cuda.dll`, `ggml-rpc.dll`, 15 variantes `ggml-cpu-*` (CPU dispatch automático),
  `libomp.dll` (OpenMP), etc.
- **No trae** `cudart64_12.dll` ni `cublas64_12.dll`/`cublasLt64_12.dll` → por eso el
  segundo zip. `ggml-cuda.dll` exige además `nvcuda.dll` = DLL del **driver NVIDIA**
  (ya instalado: nvidia-smi funciona).

**2) Análisis PE (imports normales + retardados) de los 53 binarios** — cierre de
dependencias completo. Lo único que el zip NO trae y se exige en Windows:
| DLL exigida | Quién la importa | De dónde sale | ¿Descarga extra? |
|---|---|---|---|
| `cudart64_12.dll`, `cublas64_12.dll` | `ggml-cuda.dll` | zip cudart (§3-A.1) | NO — ya en el plan |
| `nvcuda.dll` | `ggml-cuda.dll` | driver NVIDIA instalado | NO |
| `MSVCP140.dll` + `VCRUNTIME140(.1).dll` | casi todos | runtime VC++ 2015–2022 x64 | SOLO si fallara (VS2022 ya lo pone) |

**3) OpenSSL NO hace falta** (hallazgo importante): el issue
[#19236](https://github.com/ggml-org/llama.cpp/issues/19236) reporta `0xC0000135`
(DLL faltante) en Windows por DLLs de OpenSSL desde b7736 ("remove libcurl, use
OpenSSL when available"), cerrado **"not planned" (2026-03-26)**. PERO el análisis PE
muestra que el build OFICIAL importa `CRYPT32.dll` (crypto nativa de Windows) y **ni
una sola referencia** a `libssl-3-x64`/`libcrypto-3-x64` en imports normales ni
retardados → el issue aplica solo a builds locales con `-DLLAMA_OPENSSL=ON`, no a los
zips oficiales. **No descargar OpenSSL.**

**4) Contenido real del zip cudart** (integridad OK — exactamente 3 archivos):
`cublas64_12.dll` (100,033,536 B) · `cublasLt64_12.dll` (473,551,360 B) ·
`cudart64_12.dll` (553,984 B). Serie 12.4, mismos tamaños que las DLLs que ya tienes
en `build\bin` (27/02/2024) — encaja de serie con tu driver 610.88 / UMD 13.3.

**5) Pines de integridad** (SHA-256 calculados por LAIA sobre los zips descargados de
la URL oficial; el Director puede comparar SU descarga con `certutil -hashfile
<archivo> SHA256` — si difieren, avisar antes de usar):
```
llama-b11856-bin-win-cuda-12.4-x64.zip  = 71d4ff57c9b59ce960ca5e9c28d0e26d8e631075c4d13af0c34f7f3a4fa1f094  (272,434,110 B)
cudart-llama-bin-win-cuda-12.4-x64.zip  = 8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6  (391,443,627 B)
```

**6) Extras CONDICIONALES (solo si se dan las condiciones — nada obligatorio hoy):**
- **VC++ Redistributable 2015–2022 x64** (descarga gratis de Microsoft, ~25 MB): solo si
  al lanzar el exe sale `0xC0000135`. Tu VS2022 ya instala ese runtime; comprobar sin
  descargar nada: `dir "C:\Windows\System32\msvcp140.dll"` (debe existir).
- **mmproj-F16.gguf** (0.90 GB, ya verificado en el repo SC117): SOLO si quieres
  entrada de imágenes (visión). Para chat de texto NO se descarga.
- **CUDA Toolkit**: SOLO si eliges RUTA 0-B (recompilar). Para el zip (0-A) no sirve.
- **Modelo draft aparte**: NO existe para draft-mtp — usa las cabezas MTP del propio
  I-MINI (docs/speculative.md verificado verbatim en §3-C). Ruta interina ngram no
  descarga nada tampoco.

**7) NO descargar (afirmaciones falsas comunes, descartadas):** cuDNN (llama.cpp no lo
usa), OpenSSL (punto 3), Python/HF-CLI (el modelo ya está en D:), driver NVIDIA nuevo
(610.88 verificado suficiente en §3-A.0), Vulkan runtime (solo plan de rescate).
**Palancas de velocidad que NO son descargas** (ya documentadas): cerrar
Firefox/Wallpaper Engine/Copilot antes de medir (~963 MiB VRAM), `-t 4`, plan de
energía Alto rendimiento, pagefile en D: (RUTA 5).

### 3-A.3 RUTA DIRECTA — todo en un solo pegado (2026-10-25, mismo resultado que 3-A.1)

Racional: los pasos manuales (navegador, certutil a mano, dir, extracción con
Explorador) son overhead. La ruta directa encadena TODO en un paste de PowerShell con
verificación automática VERDE/ROJO. No se recorta seguridad: hash automático, check
draft-mtp intacto, dump intacto. El `dir *.dll` desaparece porque con hash VERDE +
extracción completa las DLLs están garantizadas por construcción (y `--version` no
detectaría falta de CUDA: `ggml-cuda.dll` se carga dinámicamente en runtime).

**OPCIÓN A (recomendada — 633 MB, cero decisiones).** Abrir **Windows PowerShell**
(powershell.exe, el azul — así el dump queda UTF-16 como el original) y pegar:

```powershell
$ErrorActionPreference="Stop"
function Parar($que){ if($LASTEXITCODE -ne 0){ throw "FALLO en: $que" } }
$u="https://github.com/ggml-org/llama.cpp/releases/download/b11856"
$d="$env:USERPROFILE\Downloads"; $n="D:\llama.cpp\bin-new"
curl.exe -L -o "$d\llama-b11856-bin-win-cuda-12.4-x64.zip" "$u/llama-b11856-bin-win-cuda-12.4-x64.zip"; Parar "descarga bin"
curl.exe -L -o "$d\cudart-llama-bin-win-cuda-12.4-x64.zip" "$u/cudart-llama-bin-win-cuda-12.4-x64.zip"; Parar "descarga cudart"
$ok1=(Get-FileHash "$d\llama-b11856-bin-win-cuda-12.4-x64.zip" -Algorithm SHA256).Hash -eq "71d4ff57c9b59ce960ca5e9c28d0e26d8e631075c4d13af0c34f7f3a4fa1f094"
$ok2=(Get-FileHash "$d\cudart-llama-bin-win-cuda-12.4-x64.zip" -Algorithm SHA256).Hash -eq "8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6"
"zip bin    : $(if($ok1){'VERDE'}else{'ROJO — NO USAR'})"
"zip cudart : $(if($ok2){'VERDE'}else{'ROJO — NO USAR'})"
if(-not ($ok1 -and $ok2)){ throw "Hash distinto: borrar zip y repetir el paste" }
New-Item -ItemType Directory -Force -Path $n | Out-Null
tar -xf "$d\llama-b11856-bin-win-cuda-12.4-x64.zip" -C $n; Parar "extraccion bin"
tar -xf "$d\cudart-llama-bin-win-cuda-12.4-x64.zip" -C $n; Parar "extraccion cudart"
& "$n\llama-server.exe" --version
& "$n\llama-server.exe" --help | Select-String "draft-mtp"
& "$n\llama-server.exe" --help > D:\ZLia\llama-flags-nuevo.txt
"LISTO — pegar TODA la salida de consola en el chat"
```

**OPCIÓN B (más ligera — descarga solo 260 MB, reutiliza tus 3 DLLs CUDA).** Tus
DLLs de `build\bin` son la MISMA serie 12.4 (27/02/2024); el zip cudart solo trae 3
archivos, así que si tus tamaños byte coinciden, son el mismo contenido:

```powershell
Get-ChildItem D:\llama.cpp\build\bin\cudart64_12.dll, D:\llama.cpp\build\bin\cublas64_12.dll, D:\llama.cpp\build\bin\cublasLt64_12.dll | Select-Object Name, Length
```
Esperado EXACTO: 553,984 / 100,033,536 / 473,551,360 bytes. Si coinciden los 3 →
mismo paste de la Opción A pero SIN las líneas de descarga ni hash ni extracción del
cudart, y en su lugar:
```powershell
copy D:\llama.cpp\build\bin\cudart64_12.dll, D:\llama.cpp\build\bin\cublas64_12.dll, D:\llama.cpp\build\bin\cublasLt64_12.dll $n\
```
Si algún tamaño difiere → no improvisar, usar la Opción A. (El `copy` toca COPIAS en
bin-new: tu build viejo no se modifica — rollback intacto.)

**VARIANTE .PY (100% automática, con veredicto de seguridad final):**
`InformacionCritica/actualizar-llama-b11856.py` — Python 3.8+, solo librería estándar,
cero pip installs. Hace el ciclo completo: descarga (con auto re-descarga si el tamaño
no cuadra) → SHA-256 fail-fast VERDE/ROJO → extracción anti zip-slip → archivos
críticos + tamaños byte-exactos de las 3 DLLs CUDA → sistema (nvcuda.dll, msvcp140.dll)
→ `--version` → `draft-mtp` → dump UTF-16 en D:\ZLia → RESUMEN con VEREDICTO GLOBAL.
Solo ejecuta `--version` y `--help`: NUNCA carga el modelo ni toca `build\bin`.
Probada por LAIA en los 3 caminos: limpio (VERDE, exit 0), zip truncado (re-descarga
automática), zip alterado con tamaño exacto (ROJO, exit 1, no extrae nada).
Uso: `py actualizar-llama-b11856.py` (o `python actualizar-llama-b11856.py`).

**Lo que NO se recorta en la ruta directa (y por qué):**
- Check `draft-mtp`: es el propósito de la actualización (PR #22673). Sin él,
  volaríamos a ciegas otra vez.
- Hash SHA-256: única garantía de que llegó EXACTAMENTE el build b11856 verificado
  (download truncado/proxy = zip roto que tar a veces extrae igual).
- Dump UTF-16: sin él no hay re-auditoría de flags antes de V2 (guardarrail 2).

**REGISTRO DE EJECUCIÓN REAL (2026-10-25, máquina del Director, script v1.0):**
- 15 checks ejecutados: descargas byte-exactas + **SHA-256 VERDE ×2** · extracción
  53+3 archivos · DLLs CUDA byte-exactas · `nvcuda.dll` y `msvcp140.dll` presentes ·
  **`draft-mtp` PRESENTE** · dump UTF-16 regenerado (122,440 B; el build nuevo trae
  más flags que el viejo: 101,962 B).
- **Versión del binario nuevo: `0.7.0-dev (build 11856, commit 3642238cc)`, built
  with Clang 20.1.8** — el CI oficial compila Windows con Clang (no MSVC como tu
  build viejo). b11856 confirmado = el nightly fijado.
- **Falso ROJO corregido (script v1.1)**: la versión sale por **stderr** (llama.cpp
  loggea ahí) y el script v1.0 solo miraba stdout → marcó FALLO indebidamente. Fix:
  aceptar stdout+stderr (probado con la salida real del Director). El binario real:
  TODO VERDE.
- **PIN NUEVO: build 11856 / commit 3642238cc** — sustituye al pin viejo
  `version: 1 (2496f9c)` (fuente 2026-05-06, sin draft-mtp).

**REGISTRO DE RUTA OPERATIVA NUEVA (2026-10-25, informada por el Director):**
- El binario nuevo ahora vive en **`D:\llama.cpp\llama-server.exe`** (raíz, movido
  desde `bin-new\`). `bin-new\` queda como origen verificado por el script.
- ADVERTENCIA técnica (análisis PE 3-A.2): `llama-server.exe` es un launcher fino
  de 9,216 B — la lógica vive en `llama-server-impl.dll`, `llama.dll`,
  `ggml-cuda.dll`, `libomp.dll`, las 15 `ggml-cpu-*.dll` y las 3 DLLs CUDA. TODAS
  deben quedar en la MISMA carpeta que el exe. Si solo se movió el .exe → error
  0xC0000135 al arrancar.
- Verificación de 10 s (PowerShell, pegar y reportar):
  ```powershell
  & D:\llama.cpp\llama-server.exe --version 2>&1
  # esperado: version: 0.7.0-dev (build 11856, commit 3642238cc)   (2>&1 OBLIGATORIO: la versión sale por stderr)
  & D:\llama.cpp\llama-server.exe -m D:\no-existe.gguf 2>&1 | Select-Object -First 10
  # esperado: lineas ggml_cuda_init: found 1 CUDA device ... + error failed to load model
  # = la pila CUDA completa (ggml-cuda.dll + cublas) carga bien en la carpeta nueva.
  # OJO: --version NO detecta falta de ggml-cuda.dll (se carga dinamicamente) — por eso el smoke test.
  ```
- Si `--version` falla con 0xC0000135 → solo se movió el exe. Arreglo: mover TODO
  el contenido de bin-new: `Move-Item D:\llama.cpp\bin-new\* D:\llama.cpp\ -Force`
- Dump del build nuevo: **`D:\ZLia\llama-flags-nuevo.txt`** (122,440 B, UTF-16LE) —
  generado por el script desde `bin-new` (mismo binario b11856, así que sigue
  siendo válido aunque el exe se haya movido). Es el archivo a subir a
  `InformacionCritica/` para la re-auditoría de flags antes de V2. Si el Director
  quiere regenerarlo desde la ruta nueva (idéntico resultado):
  ```powershell
  & D:\llama.cpp\llama-server.exe --help 2>&1 | Out-File D:\ZLia\llama-flags-nuevo.txt -Encoding unicode
  ```

**REGISTRO DE RE-AUDITORÍA DEL DUMP NUEVO (2026-10-25, subido por el Director):**
- `llama-flags-nuevo.txt` recibido (122,440 B byte-exacto), movido a
  `InformacionCritica/` y auditado con diff automático (98 → 97 flags) + grep
  verbatim. Detalle completo en `flags-verificadas-LAIA.txt` (bloque RE-AUDITORÍA).
- Confirmado en SU dump: `draft-mtp` en `--spec-type` (+ nuevos draft-eagle3/
  dflash/dspark), `-ncmoe/-cmoe`, `--moe-cache-mib` (default 0), `-lm` sustituye
  a `--mlock/--no-mmap/-dio` (muertas), `--jinja` default ON, `-fa on|off|auto`,
  **puerto default 9931**, `--spec-draft-n-max` default 3.
- Consecuencia operativa: V1/V2 siguen válidos cambiando ruta del server (raíz),
  puerto (9931) y sin `--jinja`.

### 3-A.4. LANZADOR AUTOMÁTICO del modelo (nuevo, 2026-10-25)

`InformacionCritica/abrir-qwen-apex.py` — Python 3.8+ solo stdlib, especifico del
modelo Qwen APEX-I-MINI (14,273,277,376 B verificado) y del build b11856. Usa
SOLO flags auditadas contra el dump nuevo. Fases:

- **Pre-flight**: 7 DLLs críticas junto al exe · `--version` combinando
  stdout+stderr (lección 3-k) con pin build 11856 · modelo byte-exacto
  (`--force` si difiere) · recordatorio de cerrar Firefox/Wallpaper/Copilot.
- **V1** (default, `-cmoe` boot garantizado) / **`--ncmoe N`** / **`--mtp`**
  (V2: `--spec-type draft-mtp --spec-draft-n-max 2`, mitigación #23577;
  `--spec-p-min 0.75` para replicar el V2 documentado).
- **`--sweep`**: barrido automático `-ncmoe` (cmoe,40,32,24,16 por defecto):
  lanza el server, espera `/health`, request de warmup (descarta JIT PTX),
  request de medición vía `/completion` (timings del propio server), cierra,
  siguiente; tabla final ordenada + ganador + log en `D:\ZLia\sweep-logs\`.
- **`--dry-run`**: imprime el comando exacto sin lanzar nada.
- NUNCA usa `--mlock` (prohibido por RAM), nunca `-nkvo`, nunca flags muertas.
- Puerto default 9931 (`--port 8080` si airi/pi lo espera).

```bat
py abrir-qwen-apex.py --dry-run          (ver el comando)
py abrir-qwen-apex.py                    (V1, abrir y chatear)
py abrir-qwen-apex.py --sweep            (barrido -ncmoe con medición t/s)
py abrir-qwen-apex.py --mtp --ncmoe N_GANADOR   (V2, objetivo ~28-36 t/s)
```

**DOBLE-CLICK (más simple, 2026-10-25):** bajar `ABRIR-QWEN.bat` y
`abrir-qwen-apex.py` a la MISMA carpeta → doble click en `ABRIR-QWEN.bat` →
menú en la ventana: **[1]** abrir y chatear (V1, solo Enter) · **[2]** barrido
del -ncmoe con medición · **[3]** MTP x2 (pide el ganador del barrido; Enter =
-cmoe seguro) · **[4]** solo ver el comando · **[0]** salir. La ventana se
mantiene abierta al cerrar el server (pause del bat). El doble click directo
al `.py` también funciona si Windows asocia .py al lanzador de Python.

**v2.0-MINIMAL (2026-10-25, sustituye al menú):** el Director pidió abrir y
ya. `abrir-qwen-apex.py` es ahora ~95 líneas sin menú ni preguntas: doble
click → espera /health → banner "MODELO LISTO" → la ventana mantiene vivo el
modelo (Ctrl+C o cerrar ventana lo apaga). Preset think OFICIAL fijo en
BASE_FLAGS; línea `FLAGS_GANADORAS = []` arriba para pegar el ganador del
barrido (van al final → last-wins en argparse). La versión completa con menú
quedó como `abrir-qwen-apex-v13-avanzado.py`. Test E2E 6/6
(scripts/test_abrir_mock.py).

**BARRIDO DE 25 CONFIGS (2026-10-25):** `BARRIDO-QWEN.bat` →
`barrido-qwen-25.py`. Prueba una a una las 25 configs del
`informe-velocidad-sweep.md` (§7): server up → 4 pasadas × 256 tokens vía
`/completion` + timings JSON (descarta la 1ª) → CSV append con resume → kill
→ siguiente; pausas térmicas 60 s cada 8; ABORTA si ya hay un server vivo;
configs 23-25 son COMBOS construidos al vuelo con los ganadores medidos;
ranking final + línea `FLAGS_GANADORAS` lista para pegar. Test E2E 22/22
(scripts/test_barrido_mock.py). Las 100 configuraciones y el porqué de cada
una: informe-velocidad-sweep.md §6.

### 3-A.5. SAMPLING profesional del modelo (nuevo, 2026-10-25)

Doc completo: **`config-sampling-qwen36.md`** (mismo directorio). Resumen:

- Qwen3.6 recomienda oficialmente 3 presets: **think** (temp 1.0, top_p 0.95,
  top_k 20, min_p 0), **coding** (temp 0.6, resto igual) y **fast**
  (temp 0.7, top_p 0.80, top_k 20) — fuentes: card oficial +
  `generation_config.json` de `Qwen/Qwen3.6-35B-A3B` (fetch textual).
- Los defaults del server b11856 (temp 0.80, top-k 40, min-p 0.05) NO
  coinciden → **el lanzador v1.3 los fija siempre** con `--preset
  think|coding|fast` (default think) y añade `--no-mmproj` (text-only,
  ahorra ~0.9 GB VRAM).
- No-thinking: `--chat-template-kwargs '{"enable_thinking":false}'` o
  `-rea off` o `--reasoning-budget 0` (todas en el dump). Thinking de
  turnos históricos: `--reasoning-preserve` (ya ON en el build, no se pasa).
  Tope de thinking con ctx 16K: `--reasoning-budget 4096`.
- El lanzador v1.3 integra el no-thinking (`--no-thinking`, método oficial
  del template), el budget, `--cache-reuse` (opt-in, probar tras el sweep)
  y `--spec-draft-ncmoe` (solo MTP); menú [5] CHAT RÁPIDO = fast + thinking
  OFF. Verificado en dry-run y menú simulado.
- Para CHATEAR con métricas: `CHATEAR-QWEN.bat` (o `py chatear-qwen.py`) en
  OTRA ventana con el server abierto — streaming token a token (thinking en
  gris, ambos formatos), t/s · TTFT · prefill · ctx real por turno, /stats,
  /reset, /guardar y sampling por request (/preset, /temp; NO greedy).
  Cliente solo stdlib, verificado con test E2E mock 18/18; la aceptación
  del draft MTP se ve en el LOG del server, no en el cliente.
- El sampling NO afecta al barrido `-ncmoe` (requests con temp 0.0).

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
Build VIEJO (base 16 t/s): version 1 (2496f9c) — fuente del 2026-05-06 (mtmd MiniCPM-V
  4.6, #22529), 10 días antes del merge de draft-mtp (#22673). Build local MSVC 19.44
  (VS2022 presente), clon sin tags (por eso "version: 1" y no b-number). Registrado
  2026-10-24.
VEREDICTO verificación 2026-10-24: VERDE para los zips CUDA 12.4 de b11856.
  - Driver: NVIDIA 610.88, CUDA UMD 13.3 → zip 12.4 SOPORTADO; el zip 13.4 queda
    DESCARTADO (tu driver llega a 13.3, no a 13.4).
  - DLLs junto al exe: cublas64_12 / cublasLt64_12 / cudart64_12 (serie CUDA 12.4,
    fechadas 27/02/2024) → build dinámico ya en serie 12; el cudart zip nuevo (12.4)
    encaja de serie.
  - GPU: GTX 1650, compute 7.5, VMM yes, 4095 MiB totales. ~963 MiB ya en uso por el
    escritorio (Firefox, Wallpaper Engine, Copilot) → cerrarlos antes del sweep:
    libera ~1 GB de VRAM.
  - D: SSD con 222 GB libres (espacio de sobra para los zips).
Build actualizado:        b-XXXX (pegar aquí) — fecha: __/__/____
```

### 3-C. ¿Qué versión exacta usar? — decisión respaldada (2026-10-25)

**RECOMENDADA: nightly b11856 (2026-10-24), zips CUDA 12.4 de §3-A.1.** Razones
verificadas:
1. `draft-mtp` vivo en master: el docs/speculative.md OFICIAL lo lista — verbatim:
   `| draft-mtp | Use Multi Token Prediction (MTP) heads from the main model |`
   (verificado 2026-10-25).
2. Incluye fixes POSTERIORES a v0.7.0 del cache MoE en host — p. ej. el gate que
   bloqueaba el cache en batches de verificación del draft (sin ese fix, MTP + cache
   puede salir perdiendo; reportado corregido con límite opt-in).
3. Tu driver (UMD 13.3) soporta el zip 12.4 — verificado EN TU MÁQUINA (§3 registro).

**FALLBACK: b11669 = v0.7.0** (verificado verbatim: nightly-tag.txt de v0.7.0 contiene
`b11669`; publicado 2026-10-15). Mismo feature set (draft-mtp + `--moe-cache-mib`),
9 días más conservador. Zips: `llama-b11669-bin-win-cuda-12.4-x64.zip` +
`cudart-llama-bin-win-cuda-12.4-x64.zip`. Úsalo si b11856 diera cualquier anomalía.

**RESCATE (último recurso): Vulkan** — `llama-b11856-bin-win-vulkan-x64.zip`. Dato
relevante: en #23577 un usuario con el bug CUDA de draft-mtp lo resolvió pasando a
Vulkan (aceptación estable ~0.89). CUDA rinde más; Vulkan solo si CUDA fallara.

**Riesgos conocidos documentados (no bloquean, se vigilan):**
- [#23577](https://github.com/ggml-org/llama.cpp/issues/23577) (may 2026): Qwen3.6 +
  draft-mtp en CUDA, bucle "////" tras sesiones MUY largas (aceptación → 0). Afectados:
  ctx 262k y CUDA 13.2 ("notorio por corrupción"). Estado NO verificado (la página no
  cargó en 2 intentos — no inventar cierre). Mitigación en este rig: ctx 16k, `n-max 2`,
  vigilar `draft acceptance rate`; si cae a 0.00 con ////, reiniciar server y avisar.
- [#23011](https://github.com/ggml-org/llama.cpp/issues/23011) (may 2026): self-MTP más
  lento en Metal (Apple) — NO aplica (tu backend es CUDA).
- [#30552](https://github.com/ggml-org/llama.cpp/issues/30552) (14 oct 2026): "crawl"
  reportado en ROCm/Vulkan con splits — NO aplica a CUDA single-GPU; se cita porque
  justifica tener el fallback b11669 a mano.
- [RFC #24528](https://github.com/ggml-org/llama.cpp/discussions/24528) (≈19 oct): se
  discute si el cache MoE debe quedar ON por defecto ("--moe-cache defaults to auto,
  which is ON"). Consecuencia práctica: en el build nuevo las reglas del sweep pueden
  cambiar → OBLIGATORIO regenerar dump y re-auditar ANTES de tocar `-ncmoe` (paso 4).

**Expectativa de comunidad con este modelo (calibrar, no promesas):**
| Fuente | Hardware | Resultado |
|--------|----------|-----------|
| r/LocalLLaMA ("80 tok/s") | 12 GB VRAM | >80 t/s con >80% aceptación (build reciente) |
| [Discusión #28584](https://github.com/ggml-org/llama.cpp/discussions/28584) | 16 GB VRAM | 24.9–25.9 t/s con contexto 400k+ |
| Matriz 5070 Ti (note.com, Qwen3.6-35B-A3B-MTP UD-Q4_K_XL) | 16 GB | cache MoE duplica: 90.78 → 181.29 t/s |
| Tu rig | 4 GB | absoluto menor, pero los RATIOS de MTP aplican igual |

**Regla de pin:** el build que gane las mediciones queda ANCLADO en §11; NO actualizar
a mitad de las mediciones del sweep/MTP.

### 3-C.1 Segunda verificación GPU + modelo (2026-10-25)

**GPU (GTX 1650, sm_75) vs zip b11856 CUDA 12.4 — VEREDICTO: COMPATIBLE.**
1. VERBATIM de `ggml/src/ggml-cuda/CMakeLists.txt` (master, descargado y verificado
   2026-10-25): `list(APPEND CMAKE_CUDA_ARCHITECTURES 75-virtual 80-virtual 86-real)` —
   **75 (Turing) va SIEMPRE en la lista por defecto**; con CUDA 12.4 se añaden además
   50/61/70-virtual. `75-virtual` = PTX embebido → el driver JIT-compila en la PRIMERA
   ejecución (primer arranque más lento; luego queda cacheado y el rendimiento es
   idéntico al de un binario nativo sm_75).
2. Sin reportes de fallos Turing/GTX-16xx en builds recientes (búsqueda 2026-10-25).
3. Tu máquina ya validó la cadena CUDA completa: driver UMD 13.3 ≥ 12.4, cc 7.5
   funcionando con tu build actual.
4. El gate de runtime (paso 3 de §3-A) detecta cualquier fallo en segundos, sin daño;
   fallbacks documentados (b11669, vulkan). Pendiente formal: no se pudo localizar el
   build.yml del CI (movido) para confirmar que no pisa la lista por defecto — ninguna
   evidencia en contra encontrada; el gate de runtime lo zanja en 1 minuto.

**Modelo (repo SC117 APEX) vs docs del proyecto — VEREDICTO: TODO COINCIDE.**

| Dato | API HF (bytes reales, 2026-10-25) | Nuestros docs | ✓ |
|---|---|---|---|
| I-MINI | 14,273,277,376 = 14.27 GB | 14.27 GB | ✓ |
| I-Compact / I-Quality / I-Balanced | 17.02 / 23.51 / 25.96 GB | ídem | ✓ |
| mmproj-F16 | 899,283,072 = 0.90 GB | 0.90 GB | ✓ |
| Descargas / última mod | 59,517 / 2026-10-03 | 59.5k | ✓ |
| Total repo | 81.67 GB | — | — |

Comando del AUTOR en la model card (confirma la estructura de nuestro V2):
`./llama-server -m ...APEX-I-Compact.gguf -ngl 99 -ncmoe 16 -c 131072 --spec-type draft-mtp --spec-draft-n-max 2`
→ el autor usa `-ncmoe` JUNTO con draft-mtp (indica que la flag sigue viva en builds con
MTP; igualmente se re-audita contra el dump nuevo — regla de oro). "20-50% speed boost"
re-confirmado. La card NO exige versión mínima de llama.cpp ni CC concreta → el gate de
runtime (paso 3) es el verificador definitivo.

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

**Sweep manual del Director (2026-10-25 07:08, logs en sweep-logs.7z):**
ganador `-cmoe` = **9.33 t/s** (prefill 21.08). `-ncmoe 16/24/32/40` =
7.33/5.90/5.86/5.58 — mover expertos a GPU con `-ngl 99` fijo EMPEORA (el
auto-fit de VRAM aborta y el driver desborda a RAM compartida; ver
informe-velocidad-sweep.md §2). Medición del 25-oct no comparable entre
configs (69 vs 256 tokens, 1 pasada): el barrido nuevo corrige el protocolo.

```text
(placeholder — pegar aquí el GANADOR del BARRIDO-QWEN.bat con su t/s:
 el barrido imprime al final la línea FLAGS_GANADORAS = [...] y el comando)
```

**BARRIDO-QWEN-25 — corrida completa 25/25 (2026-10-25, protocolo fijo:
4 pasadas × 256 tok, descarta la 1ª, promedia 2-4):**

- **BASE real = 20.85 t/s.** El 9.33 del sweep manual era artefacto de
  medición (69 tokens, calentamiento incluido, 1 sola pasada). El techo
  DDR4 estimado en el informe (~17-23) era correcto: ya estábamos cerca.
- **GANADOR: `LMNONE` (`-lm none`) = 21.50 t/s** (+0.65, +3.1%). 2º
  POLL100 21.42 · 3º POLL0 y COMBO-A 21.33 (empate exacto). El combo
  np1+poll100+lmnone NO suma más que el ganador solo (ruido ~±0.3).
- **draft-MTP mide NEGATIVO en este rig**: las 10 configs MTP quedan en
  16.6-18.9 (mejor 18.89 vs 20.85 base = -9%). La hipótesis H1 del informe
  (el 23 t/s fue MTP) queda REFUTADA. La ruta a 30 vía MTP: CERRADA aquí.
- **`--moe-cache-mib` es veneno en esta GPU**: 256 → 13.51, 512 → 17.22
  (roba VRAM a pesos densos). Descartado para siempre.
- Hilos: `-t 4` correcto (T3 = 18.29, T5 = 18.75; HT no ayuda).
- Comando ganador: `-m <modelo> -ngl 99 -cmoe -c 16384 -b 2048 -ub 256
  -fa on -ctk q8_0 -ctv q8_0 -t 4 --prio 2 --no-mmproj -lm none
  --host 127.0.0.1 --port 9931` (ya pegado en abrir-qwen-apex.py).
- Techo realista a $0: **~21.5-22 t/s**. Con XMP DDR4-3200 en BIOS:
  ~23-25 si los módulos lo permiten. **30 t/s exige otro hardware** (más
  VRAM para expertos o RAM más rápida). Veredicto completo: informe §11.

**BARRIDO-QWEN-30 v1.1 — preparado y verificado (2026-10-25), pendiente de correr:**

- **37 configs NUEVAS** que no repiten ninguna de las 25 (los ids 1-30 son
  los del v1.0 + 7 ORO ids 31-37 de la auditoría), con anclas de
  reproducibilidad y protocolo idéntico + mejoras (ignore_eos, load_s,
  hparams del log). Doble click: `BARRIDO-QWEN-30.bat` (~1 h 15, resumible).
- **Las 7 ORO de la auditoría b11856** (`auditoria-flags-oro.md` §6):
  31 ORO-TB8 `-tb 8` y 32 ORO-UB1K `-ub 1024 -b 4096` (frente PREFILL, el
  grupo de hilos/batch separado que nunca se tocó; -ub 512 NO se re-prueba:
  UB512 ya midió 20.77 en el 25), 33/34 ORO-NGRAMS/-NGRAMM `--spec-type
  ngram-simple/ngram-mod` (borrador gratis; protocolo especial de 4 prompts
  DISTINTOS + acceptance del log), 35 ORO-NOWARM `--no-warmup` (carga),
  36 ORO-CRAM512 `-cram 512` (RAM) y 37 ORO-SHIFT `--context-shift
  --cache-reuse 256` (retome en chats >16k). G3 (eagle3) = fase 3 con GGUF
  del draft; G6 (Defender) = exclusión manual medida con load_s de ANCLAS.
- **Log final con todas las métricas**: CSV de 23 columnas (proto,
  pf_r1..pf_r4, prompt_n, accept) y 3 rankings en pantalla: DECODE (t/s),
  PREFILL (tokens/s pasada 1 fría) y CARGA (s hasta /health, menos es
  mejor), + bloque NGRAM con acceptance.
- **La familia EXP responde la pregunta del Director**: bajar expertos
  activos SÍ se puede en runtime — `--override-kv
  qwen3moe.expert_used_count=int:N` (verbatim en el dump L162-165). Con
  control EXP10 (debe medir MENOS si el mecanismo aplica), sanity EXP8 y
  escalera 6/5/4. Esperanza honesta: EXP6 ~25-27, EXP4 ~28-33 (hipótesis,
  calidad por validar chateando ANTES de adoptar).
- Estudios: [`ideas-velocidad-30.md`](ideas-velocidad-30.md) +
  [`auditoria-flags-oro.md`](auditoria-flags-oro.md).
  Verificación: 80/80 checks (flags verbatim en el dump incluidas las 7
  ORO, prohibiciones de aprendido.md, no-repetición de las 25, -ub 512
  bloqueado, protocolo ngram, 3 rankings, migración de CSV idempotente).
  Aviso launcher: si gana un `-ncmoe`/`-ngl auto`, quitar
  `-cmoe`/`-ngl 99` de BASE_FLAGS a mano (el ranking lo imprime).
- Resultado: (placeholder — pegar aquí el GANADOR del BARRIDO-QWEN-30.bat
  con su t/s; el CSV va en sweep-resultados-30.csv)

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


---

## ANEXO RUTA 0 (2026-10-26, ronda 8) — Actualización SIN COMPILAR y blanco concreto

**RUTA 0 simplificada: no requiere git pull ni compilar.** Los releases publican binarios Windows precompilados listos:

1. **Blanco:** release etiquetado **b11901** (último a 26-Oct-2026; nuestro build actual b11856 → 45 builds, incluye todo v0.7.0: `draft-dspark`, `draft-dflash`+LiliCorr, `--moe-cache-mib` multi-GPU, restore nuevo de prompt-cache, puerto default 9931).
2. **Descargar DOS zips** (el gotcha #17812: sin el segundo, el server no ve la GPU):
   - `llama-b11901-bin-win-cuda-12.4-x64.zip` (elección conservadora para la 1650 Turing; la variante CUDA 13.4 existe pero el estado de low-bit en 13.4 es N/D, el aviso roto era de 13.2)
   - `cudart-llama-bin-win-cuda-12.4-x64.zip` (DLLs — extraer en la MISMA carpeta del exe)
3. **Después de instalar:** re-auditar defaults del build nuevo (los 25 del dump b11856 pueden cambiar; master ya difiere: n-max 3 vs 16, p-min 0.00 vs 0.75 — ver N3 §15) y generar dump nuevo de `--help` como FUENTE DE VERDAD paralela (no borrar `llama-flags.txt` actual).
4. **Descargas del hito con autenticador cerrado** (validar con `certutil -hashfile ... SHA256`):
   - Modelo: `Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf` — 14,069,266,720 B — SHA256 `36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012e3d9e2495a90e7a7150` (repo unsloth/Qwen3.6-35B-A3B-MTP-GGUF)
   - Sidecar S2: `Qwen3.6-35B-A3B-DSPARK-Q4_K_M.gguf` — 307,213,088 B — SHA256 `a3542c05bc21dba50acb47a60b81da0f1a240864bafd15a426e0fd6158be8cab` (repo williamliao/Qwen3.6-35B-A3B-DSPARK-GGUF)
   - Sidecar S2b (opcional): `DFlash Q8_0` 421 MB (repo de ronda 4)
5. Anexos de detalle: `investigacion/nivel-3-eficiencia-simple.md` §16 (procedimiento) · §15/§18/§15 de N2/N3/N5 (autenticadores y defaults).

Fuentes: github.com/ggml-org/llama.cpp/releases + releases.atom · discussion #17812 · lautenbacher.io (8-Jul) · API HF (lfs.oid, 26-Oct).
