# 05 — Configuración recomendada paso a paso

## 0. Supuestos
- Windows 10/11 x64 (si es Linux, mismos flags; rutas cambian).
- SSD de 500GB dedicado (ej. `D:\apex35b\`).
- Cuenta con ~13 GB de descarga y ~13 GB de RAM libre al servir.

## 1. Instalar llama.cpp (5 min, sin compilar)

1. Ir a https://github.com/ggml-org/llama.cpp/releases
2. Descargar el binario **cudart + CUDA para Windows** (`llama-<version>-bin-win-cuda-cu12.*-x64.zip` — el más nuevo).
3. Descomprimir en `D:\apex35b\llama\`.
4. Verificar: abrir terminal en esa carpeta → `llama-server.exe --version` y confirmar que `--help` lista `--spec-type` con valor `draft-mtp` (si no aparece, la build es vieja → actualizar).

## 2. Descargar el modelo (solo lo viable)

```powershell
pip install -U "huggingface_hub[cli]"
hf download SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-GGUF `
  --include "*MINI*" --include "mmproj*" --local-dir D:\apex35b\models
```
→ Resultado: `APEX-I-MINI.gguf` (12.2 GB) + `mmproj-...F16.gguf` (~0.8 GB).

## 3. Comando de arranque (config inicial conservadora)

```powershell
D:\apex35b\llama\llama-server.exe ^
  -m D:\apex35b\models\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf ^
  --alias apex35b ^
  -ngl 999 -ncmoe 40 ^
  -c 16384 -b 1024 -ub 256 ^
  -fa on -ctk q8_0 -ctv q8_0 ^
  -t 4 --prio 2 ^
  --host 127.0.0.1 --port 8080 ^
  --jinja
```
Notas:
- `--jinja` activa el chat template del modelo (necesario para thinking/tool-calls correctos).
- `-ncmoe 40` = todos los expertos en RAM al inicio (garantía de arranque). El sweep bajará este número.
- Sin `--mlock` (16GB RAM no da para fijar 10 GB).
- Visión (opcional, probar DESPUÉS del sweep): añadir `--mmproj D:\apex35b\models\mmproj-...-F16.gguf`.

## 4. Sweep de rendimiento (protocolo del doc 04)

1. Medir t/s base con `-ncmoe 40`.
2. Bajar de a 2: `38, 36, 34...` hasta ver el acantilado (t/s se hunde) → retroceder 1 paso.
3. Con el ganador, activar MTP: `--spec-type draft-mtp --spec-draft-n-max 2` → probar `1..3` y `--spec-draft-p-min 0.75`.
4. Si VRAM se pasa (spill silencioso): subir `-ncmoe`, o bajar `-ub 128`, o `-c 8192`.
5. Dejar anotado el comando ganador en este archivo (commit final del Director).

## 5. Conectar airi y pi dev

| App | Configuración |
|-----|---------------|
| **airi** | Provider: OpenAI-compatible → Base URL `http://127.0.0.1:8080/v1` · API key: `no-key` · Model: `apex35b` |
| **pi dev** | Idem: endpoint OpenAI apuntando a `http://127.0.0.1:8080/v1` |

(Lección del proyecto anterior: **cero scripts Python custom** — llama-server ya ES el servidor OpenAI. Todo lo que hable "OpenAI-compatible" conecta directo.)

## 6. Sampler recomendado (del model card, aplicar en la app cliente)

| Modo | temp | top_p | top_k | presence |
|------|:---:|:---:|:---:|:---:|
| Thinking general | 1.0 | 0.95 | 20 | 1.5 |
| Código | 0.6 | 0.95 | 20 | — |
| Instruct general | 0.7 | 0.8 | 20 | 1.5 |
| Razonamiento | 1.0 | 1.0 | 40 | 2.0 |

## 7. Troubleshooting (errores esperables → solución)

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `unknown architecture qwen3_5_moe` | Build vieja de llama.cpp | Actualizar a la última release |
| OOM RAM al cargar | OS sin espacio | Cerrar apps; verificar que usas I-MINI (12.2) y no otro tier; mantener mmap |
| t/s brutalmente lentas de golpe | VRAM spill silencioso | Subir `-ncmoe`, bajar `-ub`, bajar contexto |
| MTP no aparece / error spec | Build sin PR #22673 | Actualizar llama.cpp; verificar `--help` |
| Generación se corta o basura | Contexto mayor que la memoria permite | Bajar `-c` (8192) |
| airi/pi no conectan | Falta `--jinja` o puerto mal | Verificar URL `/v1`, modelo `apex35b`, y log del server |
| Respuestas con rechazos de seguridad | Esperable en ~10% (88% menos que original) | Es la naturaleza del modelo; probar reformular |

## 8. Checklist de validación final

- [ ] `llama-server` arranca sin OOM con el comando ganador
- [ ] t/s medidas y anotadas (base y con MTP)
- [ ] airi conversa con streaming
- [ ] pi dev ejecuta una tarea con tool-calls
- [ ] (Opcional) imagen enviada por airi es descrita correctamente (mmproj activo)
- [ ] Comando final commiteado en este repo
