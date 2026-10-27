# projectsZai
Proyectos creativos con IA — creado con Z.ai

Centro de operaciones del proyecto **Qwen3.6-35B-A3B APEX (I-MINI)** en el rig
**i3-10100F · GTX 1650 4GB · 16GB RAM · SSD 500GB (presupuesto $0)**: guías
operativas, instrumentos, investigación y memoria del proyecto.

## 🗺️ Mapa del repo

```
projectsZai/
├── InformacionCritica/      🔴 FUENTE OPERATIVA ACTUAL (leer primero)
│   ├── docs/                guías y análisis operativos
│   ├── scripts/             instrumentos .py del rig (abrir, chatear, barridos)
│   ├── bat/                 lanzadores de doble clic (.bat)
│   └── configs/             config.txt central + flags verificadas (whitelist)
├── investigacion/           🔬 INVESTIGACIÓN PROFUNDA
│   ├── niveles-velocidad/   los 5 niveles de velocidad (N1-N5) + historial de rondas
│   ├── dossier-35b-apex/    dossier completo del modelo (01-06)
│   └── configs/             informes PDF de investigación
└── tests/                   baterías de tests (mocks: sin GPU, sin Windows)
```

## 📖 Por dónde empezar

| Si quieres... | Ve a |
|---------------|------|
| La guía maestra (ruta al x2 de velocidad) | [`InformacionCritica/docs/RUTAS.md`](InformacionCritica/docs/RUTAS.md) |
| Abrir el modelo o chatear (doble clic) | [`InformacionCritica/bat/`](InformacionCritica/bat/) — `ABRIR-QWEN.bat` (trabajo) · `ABRIR-QWEN-CHARLA.bat` (charla) · `CHATEAR-QWEN.bat` (chat) |
| Editar la configuración (puerto, expertos, flags) | [`InformacionCritica/configs/config.txt`](InformacionCritica/configs/config.txt) — única fuente de configuración |
| Saber qué flags existen de verdad | [`configs/llama-flags.txt`](InformacionCritica/configs/llama-flags.txt) (dump #1) · [`llama-flags-nuevo.txt`](InformacionCritica/configs/llama-flags-nuevo.txt) (re-auditoría) · [`flags-verificadas-LAIA.txt`](InformacionCritica/configs/flags-verificadas-LAIA.txt) (destilado + bloqueadas) |
| Investigación de velocidad N1-N5 | [`investigacion/niveles-velocidad/`](investigacion/niveles-velocidad/) |
| El dossier completo del modelo APEX | [`investigacion/dossier-35b-apex/`](investigacion/dossier-35b-apex/) |
| Rutas reales en disco del rig | [`InformacionCritica/docs/RutasArchivos.md`](InformacionCritica/docs/RutasArchivos.md) |
| Ejecutar las pruebas del repo | [`tests/`](tests/) |

## 📂 Contenido de cada carpeta

### `InformacionCritica/` — fuente operativa actual

| Carpeta | Archivos | Rol |
|---------|----------|-----|
| `docs/` | [`RUTAS.md`](InformacionCritica/docs/RUTAS.md) | 🔴 Guía maestra: del techo real al objetivo x2 (16 → ~32 t/s). Leer primero |
| | [`config-sampling-qwen36.md`](InformacionCritica/docs/config-sampling-qwen36.md) | Configuración profesional del sampling (presets oficiales Qwen3.6, preset think) |
| | [`auditoria-flags-oro.md`](InformacionCritica/docs/auditoria-flags-oro.md) | Auditoría de las flags ORO |
| | [`informe-velocidad-sweep.md`](InformacionCritica/docs/informe-velocidad-sweep.md) · [`ideas-velocidad-30.md`](InformacionCritica/docs/ideas-velocidad-30.md) · [`aprendido.md`](InformacionCritica/docs/aprendido.md) · [`RutasArchivos.md`](InformacionCritica/docs/RutasArchivos.md) | informe del sweep, ideas, lecciones aprendidas y registro de rutas en disco |
| `scripts/` | [`abrir-qwen-apex.py`](InformacionCritica/scripts/abrir-qwen-apex.py) | lanzador del modelo (v3.0 — todo sale de config.txt) |
| | [`chatear-qwen.py`](InformacionCritica/scripts/chatear-qwen.py) | cliente de chat (hereda puerto y contexto de config.txt) |
| | [`barrido-n1-expertos.py`](InformacionCritica/scripts/barrido-n1-expertos.py) · [`barrido-qwen-25.py`](InformacionCritica/scripts/barrido-qwen-25.py) · [`barrido-qwen-30.py`](InformacionCritica/scripts/barrido-qwen-30.py) · [`barrido-total.py`](InformacionCritica/scripts/barrido-total.py) | instrumentos de medida t/s (protocolo de la casa) |
| | [`tester-mtp.py`](InformacionCritica/scripts/tester-mtp.py) · [`actualizar-llama-b11856.py`](InformacionCritica/scripts/actualizar-llama-b11856.py) · [`abrir-qwen-apex-v13-avanzado.py`](InformacionCritica/scripts/abrir-qwen-apex-v13-avanzado.py) | tester MTP, actualizador del build y variante avanzada del lanzador |
| `bat/` | [`ABRIR-QWEN.bat`](InformacionCritica/bat/ABRIR-QWEN.bat) · [`ABRIR-QWEN-CHARLA.bat`](InformacionCritica/bat/ABRIR-QWEN-CHARLA.bat) · [`CHATEAR-QWEN.bat`](InformacionCritica/bat/CHATEAR-QWEN.bat) | arranque diario: perfil TRABAJO (8 expertos) / CHARLA (4 expertos) / chat |
| | [`BARRIDO-N1.bat`](InformacionCritica/bat/BARRIDO-N1.bat) · [`BARRIDO-QWEN.bat`](InformacionCritica/bat/BARRIDO-QWEN.bat) · [`BARRIDO-QWEN-30.bat`](InformacionCritica/bat/BARRIDO-QWEN-30.bat) · [`BARRIDO-TOTAL.bat`](InformacionCritica/bat/BARRIDO-TOTAL.bat) · [`TESTER-MTP.bat`](InformacionCritica/bat/TESTER-MTP.bat) | lanzadores de los instrumentos |
| `configs/` | [`config.txt`](InformacionCritica/configs/config.txt) | ⚙️ CONFIG CENTRAL — única fuente de configuración (casa: `D:\ZLia\config.txt`) |
| | [`llama-flags.txt`](InformacionCritica/configs/llama-flags.txt) | dump `--help` del build real del Director — FUENTE DE VERDAD #1 de flags |
| | [`llama-flags-nuevo.txt`](InformacionCritica/configs/llama-flags-nuevo.txt) | dump re-auditado (2026-10-25) — fuente de la auditoría vigente |
| | [`flags-verificadas-LAIA.txt`](InformacionCritica/configs/flags-verificadas-LAIA.txt) | destilado verificado por LAIA + flags bloqueadas |

### `investigacion/` — investigación profunda

| Carpeta | Contenido |
|---------|-----------|
| [`niveles-velocidad/`](investigacion/niveles-velocidad/) | N1 recorte de expertos · N2 cuant ligero · N3 eficiencia simple · N4 memoria VRAM/RAM · N5 draft externo GPU. Cada nivel con su `*-resumen.md` de lectura rápida + [README](investigacion/niveles-velocidad/README.md) con índice, plan de pruebas por nivel e historial de rondas |
| [`dossier-35b-apex/`](investigacion/dossier-35b-apex/) | Dossier 01-06: [01 modelo](investigacion/dossier-35b-apex/01-modelo-apex.md) · [02 arquitectura](investigacion/dossier-35b-apex/02-arquitectura-qwen36.md) · [03 software](investigacion/dossier-35b-apex/03-software-llamacpp.md) · [04 hardware](investigacion/dossier-35b-apex/04-hardware-presupuesto-cero.md) · [05 config](investigacion/dossier-35b-apex/05-config-recomendada.md) · [06 fuentes](investigacion/dossier-35b-apex/06-fuentes.md) |
| [`configs/`](investigacion/configs/) | [informe-configs-archivos-tslash.pdf](investigacion/configs/informe-configs-archivos-tslash.pdf) |

### `tests/` — baterías de verificación (mocks, sin GPU)

| Test | Verifica | Checks |
|------|----------|--------|
| [`test_abrir_mock.py`](tests/test_abrir_mock.py) | `abrir-qwen-apex.py` v3.0 (config central, perfiles trabajo/charla, E2E) | 11 |
| [`test_chatear_mock.py`](tests/test_chatear_mock.py) | `chatear-qwen.py` (E2E contra mock SSE del server) | 24 |
| [`test_barrido_mock.py`](tests/test_barrido_mock.py) | `barrido-qwen-25.py` (E2E con server falso, resume) | 24 |
| [`test_faseD_n1.py`](tests/test_faseD_n1.py) | `barrido-n1-expertos.py` v1.2.1 (protocolo N1 completo) | 61 |

Ejecución: `python tests/test_<nombre>.py` desde la raíz del repo (120 checks en total).

## ⚠️ Reglas del proyecto

1. **Whitelist de flags:** ninguna flag usada en comandos/configs puede salir de
   `InformacionCritica/configs/llama-flags.txt`. Si una flag no está ahí, no existe.
   La re-auditoría vigente es [`llama-flags-nuevo.txt`](InformacionCritica/configs/llama-flags-nuevo.txt)
   y el destilado verificado está en [`flags-verificadas-LAIA.txt`](InformacionCritica/configs/flags-verificadas-LAIA.txt).
2. **Config central:** toda la configuración vive en `config.txt` (los programas la
   leen; no se edita configuración en ningún otro sitio). `config.txt` es la fuente
   de lo que se USA; el whitelist de flags es la fuente de lo que se AUDITA.
3. **Rig soportado:** `D:\llama.cpp\llama-server.exe` (build b11856) + APEX-I-MINI.gguf.
   NO se usa Ollama ni ningún otro runtime.
4. **Jerarquía de mando:** donde la investigación difiera de `InformacionCritica/`,
   manda `InformacionCritica/`.

## 🚀 Arranque rápido (en el rig)

1. Copiar `InformacionCritica/configs/config.txt` → `D:\ZLia\config.txt`
   (los scripts la buscan ahí primero; también la aceptan junto al script o en
   `InformacionCritica/configs/` del repo).
2. Doble clic en `InformacionCritica/bat/ABRIR-QWEN.bat` (perfil TRABAJO, 8 expertos)
   o `ABRIR-QWEN-CHARLA.bat` (perfil CHARLA, 4 expertos, ~+41% t/s).
3. Chatear con `InformacionCritica/bat/CHATEAR-QWEN.bat`.

Los `.bat` encuentran los `.py` solos: buscan en la carpeta plana de siempre
(`D:\ZLia`) y, si no está, en las subcarpetas del repo (`..\scripts\`).
