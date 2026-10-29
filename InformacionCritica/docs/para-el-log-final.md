# Para el log final — inventario de cierre de la campaña (LAIA, 2026-10-29)

Doc pedido por el Director en la auditoría r46 ("puedes añadir cosas mas que
necesites saber para el log final"). Es la hoja de ruta de CIERRE: qué está
cerrado, qué falta, con qué huellas y qué evidencia citar cuando se escriba
el log final de la campaña. APPEND-ONLY: nuevas rondas añaden secciones al
final, nada se reescribe.

## 1. El mapa grande (dónde estamos)

Plan de 5 niveles (aceptado en rondas 40-41): **N1 → N3 → N2 → N4 → Ruta 0 + N5**.
Estado actual: **N3 en cierre** — la medición ya existe, falta el veredicto
formal del sanity de 20 prompts (P3) que la marca como cerrada, revocable
solo por el juez humano (el Director).

- La secuencia completa vive en el piloto: `campana-10-pasos.py` (P1..P10).
- El AUTO de doble click (CAMPANA.py) corre **P1 → P2 → P3 → P6** y se detiene
  limpio antes del N1 formal si falta BARRIDO-N1.bat. P4-P5 están APARCADAS
  (r43): este turno NO descarga nada.
- Puertas rojas: P2 exige P1=GO; P3 exige P2; la puerta del juez (N3 cerrado)
  la hereda P6. `--fuerza` las salta a propósito y lo deja escrito en el
  informe — nunca se saltan solas.

## 2. Qué falta para cerrar el N3 (la receta exacta)

1. Copiar a `D:\ZLia`: **CAMPANA.py** (nuevo, r46) + `barrido-n3-eficiencia.py`
   + `config.txt` (los dos últimos ya están si no se tocaron).
2. Verificar huella: `certutil -hashfile CAMPANA.py SHA256` debe dar
   `12EDB74A...99CF7` (86,158 bytes).
3. Cerrar apps y el server diario; doble click (o `python CAMPANA.py`) = MODO
   AUTO: higiene → mediana NP2 → promoción -np 2 con backup → 20 prompts de
   sanity → veredicto OBJETIVO escrito en el informe. Tarda horas; dejarlo solo.
4. Al terminar: pegar `campana-INFORME.md` (y consola si acaso) — el juez
   humano cierra el N3 con eso. Si el veredicto es FALLA: `python CAMPANA.py
   p3 --veredicto FALLA` reabre y `p2 --revert` restaura la receta.

## 3. Decisiones ya tomadas que el log final debe citar

| Ronda | Decisión | Evidencia |
|---|---|---|
| r35/r36 | "mismo archivo, mismo SHA" era FALSA: REPO_ALT sirve variante SIN MTP; repo oficial único | docs del py, [F] |
| r42 | CAMPANA.bat archivo único (hoy retirado, histórico) | RutasArchivos 42-a |
| r43 | **Nos quedamos con el cuant vigente** (heretic v1.3.0+MPOA, KL 0.0015 + MTP nativo + APEX-I); UD-IQ3_XXS pinada como duelo revivable; P4-P5 aparcadas | Anexo R43 del plan, RutasArchivos 43-a |
| r44 | Hotfix bat: temporal único + errores visibles (incidente del py v1.5 residual en %TEMP%) | RutasArchivos 44-a |
| r45 | **Adiós al bat para siempre**: CAMPANA.py único con guardian de huella propia | RutasArchivos 45-a |
| r46 | Auditoría total: 6 bugs corregidos (batería rota por el retiro del bat, doble pausa, Ctrl+C sin capturar, rc fieles, assert no-op) | RutasArchivos 46-a |

## 4. Huellas del paquete del rig (verificar con certutil -hashfile ... SHA256)

| Archivo | Bytes | SHA256 (corto) |
|---|---|---|
| CAMPANA.py (r46, el que hay que llevar) | 86,158 | 12EDB74A...9CF7 |
| campana-10-pasos.py v1.6 (fuente íntegra) | 82,815 | 77A7AF69...F901 |
| barrido-n3-eficiencia.py v1.3 | 110,813 | FDD277AB...AF68 |
| config.txt (receta diaria) | 1,274 | 746BC346...8EEC |
| Modelo vigente SC117 APEX-I-MINI | 14,273,277,376 | e4eae0e2...118d4 |

Compañeros diarios (casa, no campaña): abrir-qwen-apex-v13-avanzado.py
2D38568F...185C, chatear-qwen.py A9151CC4...FFF3,
diagnostico-velocidad.py 9693F8BC...F365, barrido-n1-expertos.py
80C35ECB...78D0. Regla anti-manipulación: el guardian de CAMPANA.py
auto-verifica su propia huella al arrancar (PARADA LIMPIA si el disco no
clava) y el p5 certifica el SHA256 del modelo antes de usar nada.

## 5. Dónde vive la evidencia (citar por ruta, no de memoria)

- Evidencia N3: `investigacion/niveles-velocidad/evidencia/faseN3-20261028/`
  y `faseN3-np2-b3-20261028/` (INFORME + consola + datos JSON + CSV).
- +23% NP2 mediana: resumen en `nivel-3-eficiencia-simple-resumen.md` y el
  INFORME del barrido-n3.
- Informe append-only de la campaña en el rig: `D:\ZLia\campana-INFORME.md`
  (cada turno añade sección; nada se borra).
- Estado de la campaña: `D:\ZLia\campana-estado.json` (o `python CAMPANA.py
  estado`).

## 6. Lo aprendido que NO hay que repetir (lecciones para el log)

1. Un fallo de extracción/entorno NO debe ser invisible: todo `>nul 2>nul`
   está prohibido en la casa (causa del incidente 44).
2. Después de mover/retirar un archivo, TODAS las baterías se vuelven a
   correr (la de 90 checks estuvo rota en silencio una ronda — cazado en 46).
3. La ventana de doble click NUNCA se cierra sin causa visible: pausa única
   garantizada en éxito, FATAL de huella, Ctrl+C y excepción (r45+r46).
4. Nada se ejecuta sin huella previa: guardian del CAMPANA.py + SHA256 del
   modelo en p5. El rig no confía: verifica.
5. Regla de la casa intacta: los instrumentos finos de N2/N4/Ruta 0/N5 se
   fabrican CUANDO se llega a cada nivel, con los resultados del nivel
   anterior — no antes.

## 7. Anexo r46-b: inventario COMPLETO de dependencias (pedido del Director: "hay dependencias no informadas, cuales mas requiere")
Cuidado repartido tras el aviso del Director — el paquete de D:\ZLia son SEIS archivos del repo, no uno:
| # | Archivo | Para qué | Cuándo | Bytes | SHA256 corto |
|---|---|---|---|---|---|
| 1 | CAMPANA.py | el piloto | SIEMPRE | 86,158 | 12EDB74A...9CF7 |
| 2 | barrido-n3-eficiencia.py | motor: se IMPORTA al arrancar (colores, parser GGUF, SHA256 streaming, RAM, cliente HTTP); sin él FATAL | SIEMPRE | 110,813 | FDD277AB...AF68 |
| 3 | config.txt | receta diaria: RUTA_SERVER, RUTA_MODELO, FLAGS_BASE/GANADORAS; el prevuelo lo exige y P2 lo edita | SIEMPRE | 1,274 | 746BC346...8EEC |
| 4 | llama-flags-nuevo.txt | dump de flags b11856, fuente de verdad de la auditoría de flags; barrido-n3 hace FATAL sin él (junto al barrido o en configs/) | SIEMPRE | 122,440 | 20449FFD...4FAAD |
| 5 | BARRIDO-N1.bat | P6: N1 formal | SOLO P6 (si falta, el AUTO para limpio antes del N1) | 318 | 4FEAA264...4958 |
| 6 | barrido-n1-expertos.py | P6: el bat NO es autocontenido, lo envuelve a él | SOLO P6 | 85,457 | 80C35ECB...78D0 |
Ya en el rig y NO descargables del repo: D:\llama.cpp\llama-server.exe (build b11856 pinado, el barrido AVISA si el pin no clava), el modelo D:\ZLia\models\...APEX-I-MINI.gguf (14,273,277,376 B, e4eae0e2...118d4) y Python 3 (solo stdlib: argparse, csv, datetime, importlib, json, os, shutil, statistics, subprocess, sys, time, urllib, hashlib, re, struct, threading — CERO pip install).
Dependencias creadas por el propio script (no se descargan): campana-estado.json, campana-INFORME.md, campana-sanity-<tag>/, models/, backups de config.txt.
Lección al registro: el arnés PTY de la r46 probó arranque sin barrido y sin config, pero NO sin dump de flags — cazado por la pregunta del Director (el dump sí está en la cocina del rig desde las rondas de barrido; de ahí que los tests del lab no tropezaran con ello).
