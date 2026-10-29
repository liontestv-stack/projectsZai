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

## 8. Anexo r47: LA MALETA — vuelve a ser UN archivo (pedido del Director: "demasiados links... un link para descargar campana desde git para actualizarlo y ya")
CAMPANA.py v1.7 es archivo unico de VERDAD: los cuatro companeros de rig viajan DENTRO (base64 + SHA256) y se despliegan solos en el primer arranque. El inventario de SEIS archivos del anexo r46-b queda REEMPLAZADO por este:
| # | Archivo | Cuándo | Bytes | SHA256 corto |
|---|---|---|---|---|
| 1 | **CAMPANA.py v1.7 (la maleta)** | SIEMPRE — unico descargable | 523,598 | B1748E3D...FAA7C |
Ya en el rig (fuera del repo): llama-server b11856, modelo APEX-I-MINI (14.27 GB, e4eae0e2...118d4), Python 3 stdlib-only.
Que despliega la maleta al primer arranque (verificado contra SHA incrustado ANTES de escribir; config.txt NUNCA se pisa si ya existe — P2 es su dueno; instrumentos que difieren se re-reemplazan con nota visible): barrido-n3-eficiencia.py (FDD277AB...AF68), barrido-n1-expertos.py (80C35ECB...78D0), llama-flags-nuevo.txt (20449FFD...4FAAD), config.txt semilla (746BC346...8EEC).
Fuente viva: campana-10-pasos.py v1.7 (SHA 56478C64...53C95). P6 SIN bat: lanza barrido-n1-expertos.py directo con el mismo python (--bat queda como respaldo). Bonus de la auditoria: cazado un "formato orfano" heredado de v1.6 (docstring de modo_auto formateado con %) que el test U24 llevaba sin ver — corregido en fuente y generado.

## 9. Anexo r48: auditoria antibugs de la maleta — CAMPANA.py v1.7.1 (pedido del Director: "dale otra revisada antibugs")
Siete hallazgos sobre la maleta r47 y su herencia, corregidos y probados:
| # | Hallazgo | Clase | Fix | Prueba nueva |
|---|---|---|---|---|
| 1 | Despliegue de maleta sin red de errores y ANTES de que existiera la pausa: payload corrupto o disco/permisos cerraban la ventana sin causa | grave (r47) | try/except propio: causa visible + pausa garantizada + rc fieles (3/130/1) | U30 (payload manoseado -> rc=3) |
| 2 | Dump que diferia + ../configs existente se dejaba VIEJO en silencio ("barrido usa ese" era FALSO: barrido prefiere SU dir) | media (r47) | dump difiere -> SIEMPRE self-heal con nota; ../configs solo si aqui falta (con nota) | U31a/U31b |
| 3 | La semilla respetaba ../configs pero el cuerpo no lo miraba: layout repo = AUTO muerto "no esta config.txt" | media (r47) | _rutas con fallback ../configs (patron dump ronda 21), abspath | E38 |
| 4 | Prevuelo AUTO exigia hf y 16 GB con P4 APARCADA (el turno "NO descarga nada") | heredada r43 | hf/disco solo si P4_APARCADA=False | E36/E37 |
| 5 | Escritura de payloads no atomica: disco lleno = payload truncado que la semilla no repara | baja (r47) | tmp + os.replace (patron guardar_estado) | patron ya probado |
| 6 | Comentarios rancios: bloque final decia cuerpo v1.6 (77A7AF69); docstring del generador con otra huella | doc (r47) | corregidos al regenerar | revision manual |
| 7 | estado p6 guardaba el .py bajo la clave "bat" | cosmetica (r47) | clave "instrumento" | revision manual |
Herramienta: el auditor de formatos del area tenia el regex roto (lL]? sin corchete -> 180 falsos positivos "aridad 0"); corregido: diff HEAD vs r48 = 0 hallazgos en ambos.
Baterias al cierre: campana 94/94 + campana-py 11/11 + mocks de la casa 5/5 + faseD VERDE + PTY 1 pausa + py_compile + pyflakes.
Huella nueva del paquete:
| Archivo | Cuándo | Bytes | SHA256 corto |
|---|---|---|---|
| **CAMPANA.py v1.7.1 (la maleta auditada)** | SIEMPRE — unico descargable | 529,241 | 3AB319AE...D60D |
Fuente viva: campana-10-pasos.py v1.7.1 (1D6CFB99...F6D8). La maleta despliega igual que la r47 (mismos 4 companeros, mismas SHAs de payloads); lo que cambia es que NADA cierra la ventana sin causa, el dump viejo siempre se autocura y el AUTO no exige descargas que no va a hacer.


## 10. Anexo r49: repaso de la solucion de bugs — CAMPANA.py v1.7.2 (pedido del Director: "solucion de bugs repasa")
Baterias baseline TODO VERDE (94+11+5+faseD+PTY+py_compile+pyflakes) y auditoria fresca: los 3 hallazgos nuevos son del mismo sindrome "morir callado" que la casa ya extirpo del wrapper (r46) y de la maleta (r48) — esta vez el import del companero quedo desnudo.
1. IMPORT CON RED (medio): exec_module + aliasing de utilidades corrian a nivel de modulo sin try/except: un Ctrl+C o un error de disco/lectura/permisos cerraba la ventana del doble click sin causa ni pausa. Ahora: causa visible + pausa garantizada + rc fieles (int->int, texto->1; un exit() pelado del companero SIEMPRE es defecto del instrumento: rc 1, nunca 0 — ahi None no cuenta como exito).
2. CAUSA SIEMPRE VISIBLE (menor): el guard global tragaba el texto de un sys.exit("texto") capturado (el comentario asumia que fatal() ya lo habia impreso; falso en el caso general) -> ventana en blanco. Ahora el texto se imprime SIEMPRE (fix en el bloque final del generador).
3. HIGIENE DEL TMP (menor): un fallo a mitad de escritura de payload dejaba el tmp de la maleta huerfano; ahora el fallo lo limpia y la causa sube igual.
4. Cosmetico: "[FATAL] None" ahora es motivo honesto.
Leccion de la ronda: la familia "morir callado" vive donde hay codigo a nivel de modulo sin red — wrapper (r46), maleta (r48), import (r49): quedan auditados los tres caminos de arranque.
Baterias al cierre: campana 97/97 + campana-py 14/14 + mocks de la casa 5/5 + faseD VERDE + PTY 1 pausa + py_compile + pyflakes.
Huella nueva del paquete:
| Archivo | Cuándo | Bytes | SHA256 corto |
|---|---|---|---|
| **CAMPANA.py v1.7.2 (la maleta repasada)** | SIEMPRE — unico descargable | 533,605 | 65D33CBA...DA4B1 |
Fuente viva: campana-10-pasos.py v1.7.2 (12DA5AE1...3E127). La maleta despliega igual que la r47/r48 (mismos 4 companeros, mismas SHAs de payloads); lo que cambia es que el TERCER camino de arranque (el import) ya tambien tiene red, el texto de un sys.exit nunca se pierde y el tmp no queda huerfano.
## Anexo R50 — LA SEGUNDA OLLA (2026-10-30)
Correccion del Director sobre la r49: "era crear otro de 6 a 10, no borrar el antiguo campana". La v2 NO reemplaza: nace como CAMPANA-v2.py, archivo hermano, y CAMPANA.py v1.7.2 queda byte-intacta (verificado antes y despues de la cirugia). Barrido AST + lectura completa del cuerpo: 10 hallazgos nuevos (mina latente de indices en paso2, config.txt sin escritura atomica, revert sin red de evidencia/verificacion, estado corrupto descartado en silencio, el bucle del AUTO sin red contra Exception generica, tmp huerfano de guardar_estado, rama inalcanzable sin nombre honesto, higiene que mentia en posix, _chat_uno sin reintento ante tics del server, "13 GB" a mano). Detalle completo y pruebas: Registro 50-a en RutasArchivos.md.
Regla de convivencia de las dos ollas: el mundo (campana-estado.json, campana-INFORME.md, config.txt, models/) es el MISMO y compartido — usar UNA u OTRA, nunca ambas a la vez. Ambas despliegan la misma maleta (mismos 4 companeros, mismas SHAs) y tienen guardian de huella propia.
Baterias al cierre: contra la vieja 97/97 + 14/14; contra la nueva 110/110 + 18/18 (con E42-E52 y U26b-v2/U33 nuevos); casa 5/5 + faseD + PTY ambas (1 pausa, rc=2) + py_compile + pyflakes.
Huellas del paquete tras la r50:
| Archivo | Rol | Bytes | SHA256 crudo (certutil) |
|---|---|---|---|
| **CAMPANA.py v1.7.2** | olla ANTIGUA — intacta, sigue valida | 533,605 | 65D33CBA...DA4B1 |
| **CAMPANA-v2.py v2.0** | olla NUEVA — 10 hallazgos corregidos | 542,365 | 52996E67...B1E86 |
| campana-10-pasos.py v1.7.2 | fuente de la olla antigua (repo) | 529,885 | 12DA5AE1...3E127 |
Nota de huellas: la auto-huella interna del guardian de cada olla (EE62935F...E12EB en la v2; 4FBF323A...DDF en la v1.7.2) NO es el sha crudo del archivo: excluye la linea del SHA por diseno. Para verificar la descarga con certutil se usa el CRUDO de la tabla.
