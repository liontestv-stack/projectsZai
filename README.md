# projectsZai
Proyectos creativos con IA - creado con Z.ai

## Estructura

| Carpeta | Rol |
|---------|-----|
| **`InformacionCritica/`** | 🔴 FUENTE OPERATIVA ACTUAL — leer primero: [`RUTAS.md`](InformacionCritica/RUTAS.md) (ruta al x2 de velocidad), [`llama-flags.txt`](InformacionCritica/llama-flags.txt) (dump del `--help` del build real del Director — fuente de verdad #1 de flags), [`flags-verificadas-LAIA.txt`](InformacionCritica/flags-verificadas-LAIA.txt) (destilado verificado + bloqueadas), [`RutasArchivos.md`](InformacionCritica/RutasArchivos.md) (rutas reales en disco) |
| **`investigacion/`** | 🔬 LOS 5 NIVELES DE VELOCIDAD (investigación profunda por rondas): [`README.md`](investigacion/README.md) índice — N1 recorte expertos, N2 cuant ligero, N3 eficiencia simple, N4 memoria VRAM/RAM, N5 draft externo GPU |
| `investigacion-35b-apex/` | Dossier de investigación completo (01-06): modelo, arquitectura, software, hardware, config, fuentes |

**Regla del proyecto:** ninguna flag usada en comandos/configs puede salir de
`InformacionCritica/llama-flags.txt`. Si una flag no está ahí, no existe.
