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
