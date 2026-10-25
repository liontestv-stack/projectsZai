Modelo Qwen = "D:\ZLia\models\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf"
Llama-server = "D:\llama.cpp\build\bin\llama-server.exe"

## Registro 3-A.2 — Cierre de dependencias de los zips b11856 (LAIA, 2026-10-25)
Zips oficiales descargados y analizados por LAIA (análisis PE: imports normales + retardados de los 53 binarios):
- `llama-b11856-bin-win-cuda-12.4-x64.zip` = 272,434,110 B — SHA-256 = 71d4ff57c9b59ce960ca5e9c28d0e26d8e631075c4d13af0c34f7f3a4fa1f094
- `cudart-llama-bin-win-cuda-12.4-x64.zip` = 391,443,627 B — SHA-256 = 8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6
- zip cudart = exactamente 3 DLLs serie 12.4: cublas64_12 (100,033,536 B) / cublasLt64_12 (473,551,360 B) / cudart64_12 (553,984 B)
- Faltantes del zip binario cubiertas por: zip cudart + nvcuda.dll (driver NVIDIA ya instalado) + MSVCP140/VCRUNTIME140 (runtime VC++, VS2022 ya presente)
- OpenSSL NO exigido por el build oficial (usa CRYPT32 de Windows) — issue #19236 no aplica a los zips
- VEREDICTO: no falta NADA más que descargar; extras condicionales documentados en RUTAS.md §3-A.2
