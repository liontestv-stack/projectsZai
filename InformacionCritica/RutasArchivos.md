Modelo Qwen = "D:\ZLia\models\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf"
Llama-server VIEJO (rollback) = "D:\llama.cpp\build\bin\llama-server.exe" — version: 1 (2496f9c), 2026-05-06, sin draft-mtp
Llama-server NUEVO b11856 (operativo desde 2026-10-25) = "D:\llama.cpp\llama-server.exe" — version: 0.7.0-dev (build 11856, commit 3642238cc); ver Registro 3-l

## Registro 3-A.2 — Cierre de dependencias de los zips b11856 (LAIA, 2026-10-25)
Zips oficiales descargados y analizados por LAIA (análisis PE: imports normales + retardados de los 53 binarios):
- `llama-b11856-bin-win-cuda-12.4-x64.zip` = 272,434,110 B — SHA-256 = 71d4ff57c9b59ce960ca5e9c28d0e26d8e631075c4d13af0c34f7f3a4fa1f094
- `cudart-llama-bin-win-cuda-12.4-x64.zip` = 391,443,627 B — SHA-256 = 8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6
- zip cudart = exactamente 3 DLLs serie 12.4: cublas64_12 (100,033,536 B) / cublasLt64_12 (473,551,360 B) / cudart64_12 (553,984 B)
- Faltantes del zip binario cubiertas por: zip cudart + nvcuda.dll (driver NVIDIA ya instalado) + MSVCP140/VCRUNTIME140 (runtime VC++, VS2022 ya presente)
- OpenSSL NO exigido por el build oficial (usa CRYPT32 de Windows) — issue #19236 no aplica a los zips
- VEREDICTO: no falta NADA más que descargar; extras condicionales documentados en RUTAS.md §3-A.2

## Registro 3-k — Veredicto del binario nuevo (LAIA, 2026-10-25)
Ejecución real del script en la máquina del Director (D:\llama.cpp\bin-new):
- SHA-256 VERDE ×2 (zips byte-idénticos a los verificados por LAIA) · extracción 53+3 · DLLs CUDA byte-exactas · nvcuda + msvcp140 OK · draft-mtp PRESENTE · dump UTF-16 (122,440 B)
- Pin NUEVO del binario: version: 0.7.0-dev (build 11856, commit 3642238cc), built with Clang 20.1.8
- Pin VIEJO reemplazado: version: 1 (2496f9c), MSVC 19.44, fuente 2026-05-06
- Falso ROJO del script v1.0 (versión por stderr, bug de LAIA) corregido en v1.1 — veredicto real: VERDE
- Pendiente: Director sube D:\ZLia\llama-flags-nuevo.txt a InformacionCritica/ → LAIA re-audita flags → V1 + sweep -ncmoe → V2 (draft-mtp)

## Registro 3-l — Ruta operativa nueva + ubicación del dump (LAIA, 2026-10-25)
- Ruta operativa NUEVA informada por el Director: D:\llama.cpp\llama-server.exe (raíz, movida desde D:\llama.cpp\bin-new\; bin-new queda como origen verificado por el script)
- Requisito de carpeta: el exe es un launcher fino (9,216 B) — necesitan acompañarlo en la MISMA carpeta llama-server-impl.dll, llama.dll, ggml-cuda.dll, libomp.dll, las 15 ggml-cpu-*.dll y las 3 CUDA (cudart64_12/cublas64_12/cublasLt64_12). Solo el .exe solo → 0xC0000135
- Verificación del Director (pendiente de pegar): `--version 2>&1` esperado build 11856/3642238cc + smoke test `-m D:\no-existe.gguf` esperado ggml_cuda_init + failed to load model (--version NO detecta falta de ggml-cuda.dll: carga dinámica)
- Dump del build nuevo: D:\ZLia\llama-flags-nuevo.txt (122,440 B, UTF-16LE), generado por el script desde bin-new = mismo binario b11856, válido tal cual; es el archivo a subir a InformacionCritica/ para la re-auditoría de flags antes de V2

## Registro 4-a — Re-auditoría del dump + lanzador del modelo (LAIA, 2026-10-25)
- Dump recibido: subido por el Director a la raíz del repo, movido a InformacionCritica/llama-flags-nuevo.txt (122,440 B byte-exacto). Auditado con diff automático (98→97 flags) + grep verbatim: draft-mtp CONFIRMADO (+draft-eagle3/dflash/dspark nuevos), -ncmoe/-cmoe y --moe-cache-mib presentes, -lm sustituye a --mlock/--no-mmap/-dio (muertas), --jinja default ON, -fa on|off|auto, puerto default 9931, --spec-draft-n-max default 3
- Lanzador NUEVO: InformacionCritica/abrir-qwen-apex.py — especifico Qwen APEX-I-MINI + b11856; pre-flight (DLLs, versión out+err con pin 11856, modelo byte-exacto 14,273,277,376 B), modos V1 (-cmoe default)/--ncmoe N/--mtp (n-max 2, mitigación #23577)/--sweep (mide t/s real vía /health + /completion timings; logs en D:\ZLia\sweep-logs)/--dry-run; puerto 9931 (--port 8080 para airi/pi); NUNCA --mlock/-nkvo/flags muertas
- Siguiente: Director ejecuta --sweep con escritorio cerrado → ganador -ncmoe → V2 --mtp → anotar en RUTAS §11
- Simplificado a DOBLE CLICK (mismo día): ABRIR-QWEN.bat (CRLF, cd a su propia carpeta, fallback py→python, pause final) + menú interactivo en abrir-qwen-apex.py al abrirse SIN argumentos: [1] abrir V1 · [2] barrido -ncmoe · [3] MTP x2 (Enter=-cmoe) · [4] ver comando · [0] salir. Condición de uso: ambos archivos en la MISMA carpeta

## Registro 5-b — Configuración de sampling profesional Qwen3.6 (LAIA, 2026-10-25)
- Investigación con fuentes puras de Qwen (SIN Ollama — no forma parte del stack): card oficial Qwen/Qwen3.6-35B-A3B (3 presets textuales), generation_config.json oficial (temp 1.0 / top_k 20 / top_p 0.95, SIN presence), doc familia Qwen3 (no greedy), dump b11856 (todas las flags verbatim)
- Doc NUEVO: InformacionCritica/config-sampling-qwen36.md — presets, discrepancia presence resuelta (fábrica=0.0 en thinking), defaults del server ≠ óptimo del modelo (top-k 40 vs 20, min-p 0.05 vs 0), cómo no-thinking y preserve-thinking con flags del dump, decisión --no-mmproj (text-only), MTP×sampling a medir, extras profesionales (cache-reuse/keep/budget)
- Lanzador v1.2: --preset {think,coding,fast} (default think) inyecta sampling oficial + --no-mmproj por defecto (o --mmproj FILE para visión); probado en dry-run los 3 presets y menú [4]; el sampling NO afecta al barrido (requests con temp 0.0)
- flags-verificadas-LAIA.txt: nueva sección D (presets + flags reasoning verbatim + reglas); RUTAS.md: nueva §3-A.5
