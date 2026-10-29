#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
campana-10-pasos.py v1.0 — PILOTO DE LA CAMPANA: los 10 pasos en un solo script
===============================================================================
Encargo del Director (28-oct-2026): "tengo mas espacio en D:, ahora planea
esos 10 pasos solidificarlos bien en un .py que haga todo".

Este script NO reemplaza a los instrumentos de cada nivel (regla de la casa:
"los instrumentos N3/N2/N4/N5 se generan con el mismo esqueleto del barrido
N1 conforme se llegue a cada nivel, sin adelantar trabajo"). Es el PILOTO que
los maneja en orden, con puertas (gates), pre-vuelos, certificados y memoria:

  estado        foto de la campana (que paso, que falta, que decidio el Director)
  p1            higiene (C:/D:/RAM) + log NOCACHE + mediana de 3 de NP2 (b2/b3
                via barrido-n3) + veredicto GO / NO-GO / DUDOSO
  p2            promocion de -np 2 en config.txt (con confirmacion escrita,
                backup con marca de tiempo y --revert)
  p3            sanity de 20 prompts contra el server vivo + veredicto OK/FALLA
                que CIERRA el N3 (FALLA -> instruye revert)
  p4            descarga UD-IQ3_XXS (14,069,266,720 B) con HF_HOME en D:
                (nunca en paralelo con mediciones; resumable; --dry-run)
  p5            verificacion + humo del cuant nuevo: SHA256 certificado
                36f9ec0e...7150 + parser GGUF (nextn.* = MTP dentro) + primer
                arranque con la receta promovida y 1 prompt (fail-fast)
  p6            N1 formal: lanza barrido-n1-expertos.py DIRECTO (sin bat;
                el instrumento viaja en la maleta)
  p7..p10       GUIADOS: checklist del nivel + registro de resultados
                (los instrumentos finos de N2/N4/RUTA0/N5 se generan cuando
                se llegue; aqui queda la ruta y la decision por escrito)

REGLAS que el script hace cumplir:
  - PUERTAS: p2 exige p1=GO; p3 exige p2; p4 exige N3 cerrado; p5 exige p4.
    --fuerza las salta APROPOSITO y lo deja escrito en el informe (la
    autoridad es del Director; la pista tambien).
  - config.txt SOLO se edita en p2, con confirmacion escrita y backup
    previo; --revert restaura el backup. Ningun otro paso toca la receta.
  - el informe (campana-INFORME.md) es APPEND-ONLY: cada accion anade una
    seccion con fecha; nada se borra ni reescribe.
  - las descargas corren cuando el rig NO mide; si hay que medir, se pausa.
  - FATAL nominado con forense: si algo muere, se imprime por que y donde
    mirar, y el estado queda guardado.
  - DOBLE CLICK = MODO AUTO (v1.5): los pasos 1..6 corren SOLOS, en orden,
    sin preguntas; cada confirmación auto-aceptada queda escrita en el
    informe; las puertas rojas y el SHA256 DETIENEN el turno limpio (nunca
    se saltan solos). --ofrecer = MODO CAMPANA de r39 (foto + oferta con SI).

Todo vive junto al script (en el rig: D:\ZLia): campana-estado.json,
campana-INFORME.md, campana-sanity-<tag>/, models/. --dir cambia la base.
Importa barrido-n3-eficiencia.py (mismo directorio) para reutilizar el
parser GGUF, el SHA256 streaming, el chequeo de RAM y el cliente HTTP:
si no esta al lado, FATAL (son el mismo paquete del rig).

CHANGELOG v1.1 (2026-10-28, ronda 36 — revision "ni un solo bug" pedida por
el Director: "yo hago doble click y hace todo automaticamente... hazle una
revision para que no tenga ni un solo bug"). 13 hallazgos corregidos, todos
verificados contra los compañeros reales (barrido-n3 v1.3, config.txt de la
casa, abrir-qwen-apex.py, tests de la casa):
  1. p3: la puerta moria si p2 se re-ejecutaba (YA-PROMOVIDA no contaba
     como promovida) — el Director quedaba bloqueado por un re-run inofensivo.
  2. p1: disco D: por debajo del minimo salia VERDE (higiene que no avisaba);
     ahora avisan AMBOS discos con su motivo.
  3. p2: el chequeo "-np 2" era por substring ("-np 20" engañaba) y la
     promocion se APILABA si ya habia un -np → ahora por tokens; si ya hay
     un -np distinto de 2, no se toca nada y queda escrito.
  4. p5: campana-humo.log se SOBREESCRIBIA en cada intento (se perdia el
     forense del intento anterior) → acumulativo con cabecera por intento.
  5. p5: el humo NO replicaba la receta de la casa (faltaba el override de
     expertos si EXPERTOS_TRABAJO != 8), moria feo sin RUTA_SERVER, y un
     -m pegado dentro de las flags habria cargado OTRO modelo → receta
     espejo del lanzador + limpieza de -m/--model + FATAL nominado.
  6. p1/p6: Ctrl+C mostraba traceback crudo → pausa limpia (rc 130).
  7. DOBLE CLICK: la ventana se cerraba sola antes de poder leerse → si el
     script se arranca SIN argumentos, espera un Enter al mostrar estado.
  8. estado: YA-PROMOVIDA / VERIFICADO-SIN-HUMO / NO-GO / REVERTIDA /
     INCOMPLETO pintados de rojo (alarma falsa) → paleta correcta.
  9. estado json viejo o roto (sin pasos/n3, o no-dict) reventaba después
     → lectura defensiva con setdefault.
 10. p4: un hf instalado como .bat/.cmd (shim de pip) no arrancaba en
     Windows (CreateProcess no corre shells) → envuelto en cmd /c.
 11. p3: el veredicto OK/FALLA no actualizaba pasos["3"] (quedaba
     "EN-ESPERA-DEL-JUEZ" para siempre en el estado) → actualizado; y una
     re-corrida del mismo tag PISABA el RESUMEN.md → el anterior se archiva.
 12. p2/p4/p6 cancelados por el Director no dejaban rastro en el informe →
     la memoria append-only ahora registra tambien las cancelaciones.
 13. REPO_ALT (repo alternativo con el mismo archivo y SHA) estaba muerto
     → documentado en la ayuda de --repo.
Bateria ampliada: test_campana_mock.py pasa de 46 a 65 checks ejecutados
TODO VERDE (N01-N14 nuevos; nota: r35 anunciaba "38 checks" y era un conteo
a la baja — papereria tambien corregida).

CHANGELOG v1.2 (2026-10-29, ronda 37 — verificacion de seguridad EN VIVO del
objetivo N2, pedida por el Director: "realiza una verificacion de seguridad
del archivo"). Verificacion contra la API publica de HuggingFace:
  1. OBJETIVO CONFIRMADO AUTENTICO: la API publica HOY UD-IQ3_XXS.gguf con
     EXACTAMENTE 14,069,266,720 bytes y SHA256 36f9ec0e...7150 — identicos
     a los pinados aqui desde la ronda 35 (comparados al caracter). El repo
     es de la org oficial unsloth, no gated, sin banner de seguridad.
  2. HALLAZGO (el unico ROJO): REPO_ALT estaba MAL DOCUMENTADO — la nota
     "mismo archivo, mismo SHA" (heredada de r35/r36) es FALSA. La API
     publica en unsloth/Qwen3.6-35B-A3B-GGUF el mismo NOMBRE de archivo
     pero SIN el modulo MTP (13,211,155,424 B, SHA256 9c964e65...88fbe) y
     sin ninguna variante -MTP (23 GGUF, 0 con MTP). Haberlo usado habria
     costado una descarga nocturna de 13 GB que p5 rechazaria por SHA.
  3. FIX: p4 rechaza --repo REPO_ALT con FATAL nominado ANTES de descargar
     (--fuerza lo salta dejandolo escrito en el informe); comentario de la
     constante y ayuda de --repo corregidos con la evidencia; el fallback
     real sigue siendo re-ejecutar p4 contra REPO_DEFAULT (hf RETOMA la
     descarga cortada, no empieza de cero).
Bateria: 67 checks (E13b/E13c nuevos).

CHANGELOG v1.3 (2026-10-29, ronda 38 — paperría de campo vista por el propio
Director en el rig, doble click con estado virgen): el título imprimía
"=== CAMPANA -  ===" VACIO — el respaldo "sin empezar" estaba escrito para
clave AUSENTE (.get con default), pero la clave "actualizado" nace con
cadena VACIA y .get() la devuelve tal cual. Fix: `or "sin empezar"` (cubre
ausente Y vacía). Tras cualquier paso, el título vuelve a mostrar la fecha
y hora real (guardar_estado la estampa en cada guardado). Bateria: 68
checks (N15 nuevo: estado virgen -> titulo 'sin empezar' + 10 PENDIENTE).

CHANGELOG v1.4 (2026-10-29, ronda 39 — pedido del Director aclarado de campo:
"el problema es que nada mas doble click me salia para cerrar con enter, no
hacia nada"). El doble click SOLO mostraba la foto (comportamiento r36) y
el Director esperaba que HICIERA. Fix de diseño, no de bug: MODO CAMPANA —
sin argumentos, además de la foto, calcula el SIGUIENTE PASO que toca
(_siguiente_paso: el primero no-VERDE; antes de p4 exige N3 cerrado), lo
describe en cristiano (QUE_HACE_PASO) y pide un SI escrito para ejecutarlo;
las puertas y confirmaciones internas de cada paso siguen mandando (el SI
de aquí solo abre la puerta del paso; el paso luego pide lo suyo). Todo lo
demás intacto: 'estado' explicito sigue siendo solo foto, CAMPANA.bat pN
sigue funcionando igual. Bateria 68 -> 73 checks (U16/U17 + E25/E26/E27).

CHANGELOG v1.5 (2026-10-29, ronda 41 — pedido del Director: "quiero dejarlo y
que haga todo automaticamente... que no me pida 'ejecutar' o escribir algo,
inicio y aunque tarde 2 horas dejarlo haciendo cosas y probando diferentes
cosas dejando siempre un log; prioridad es seguridad ante malware"). MODO AUTO:
  1. DOBLE CLICK (sin argumentos) = MODO AUTO: corre los pasos 1..6 en orden
     sin NINGUNA pregunta; cada confirmación interna (EJECUTAR/PROMOVER/
     DESCARGAR/LANZAR) se auto-acepta y DEJA ESCRITA su aceptación en el
     informe (append-only). --ofrecer conserva el MODO CAMPANA de r39.
  2. PREVUELO del AUTO antes de mover una sola medida: puerto libre, RAM
     (regla R28), config.txt con FLAGS_BASE y RUTA_SERVER reales, cliente hf
     y espacio en D: — si la noche no puede completarse, muere a los 5
     segundos con el motivo, no a las 2 horas.
  3. P3 en AUTO se basta solo: si no hay server vivo arranca UNO PROPIO con
     la receta diaria de config.txt (lo apaga al terminar), corre los 20
     prompts y aplica un veredicto OBJETIVO (0 errores HTTP + 20/20 con
     carne + 3 anclas deterministas: 391/verde/Valparaiso) que CIERRA el N3
     y queda marcado como revocable por el juez humano (p3 --veredicto).
  4. SEGURIDAD ANTE MALWARE (no negociable, ni en AUTO): solo el repo oficial
     (REPO_ALT sigue desautenticado y FATAL), el SHA256 certificado es
     obligatorio ANTES de usar nada (p5 fail-fast), y --fuerza no existe en
     AUTO (las puertas rojas DETIENEN el turno limpio, no se saltan).
  5. P7..P10 quedan para la siguiente fase: sus instrumentos finos se
     fabrican CON los resultados de 1..6 (regla de la casa); el AUTO para en
     el FIN DE TURNO con todo escrito. Re-doble-click retoma donde quedó.
Bateria 73 -> 84 checks (U18/U19 + E28-E33).

CHANGELOG v1.7 (2026-10-29, ronda 47 — pedido del Director: "demasiados
links... otra solucion modificando campana.py... un link para descargar
campana desde git para actualizarlo y ya"). LA MALETA — archivo unico de
verdad, heredero del espiritu del bat de r42 pero SIN sus pecados:
  1. Los cuatro companeros de rig viajan DENTRO (base64 + SHA256): el motor
     barrido-n3-eficiencia.py, el instrumento barrido-n1-expertos.py, el dump
     llama-flags-nuevo.txt y config.txt como SEMILLA. _despliega_maleta()
     los escribe al primer arranque: cada payload se verifica contra su SHA
     incrustado ANTES de escribir (PARADA LIMPIA si no clava); config.txt
     NUNCA se pisa si ya existe (P2 es su dueno); los instrumentos que
     difieren en disco se reemplazan por el de la maleta con nota visible.
  2. P6 sin bat: lanza barrido-n1-expertos.py DIRECTO con el mismo python
     (--bat queda como respaldo). El prevuelo y el AUTO ya no buscan el bat
     viejo: cero bats en la campana (directriz del Director).
  3. Cero pip install y cero terceros: la maleta y el piloto usan solo
     stdlib. Un solo link, un solo archivo, doble click y listo.

CHANGELOG v1.6 (2026-10-29, ronda 43 — el Director pidio analisis profesional
"ambos repos ... busca las diferencias y elige una" entre el cuant vigente
(SC117 APEX-I-MINI heretic+MTP) y la UD-IQ3_XXS de unsloth):
  1. IDENTIDAD ACLARADA: el modelo que el rig corre desde hace semanas es
     SC117/Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-
     I-MINI.gguf (14,273,277,376 B, SHA256 e4eae0e289b36039faa26f955ca0210
     25754e0c56130a16746749bb1491118d4): heretic v1.3.0+MPOA (88% menos
     rechazos con KL 0.0015) sobre Qwen3.6-35B-A3B, cuantizacion APEX-I
     (apex-quant de mudler: precision por ROL de tensor — experto routado,
     experto compartido, atencion) y las 20 capas MTP dentro del mismo GGUF.
  2. DECISION (Puerta A): NOS QUEDAMOS con el cuant vigente y P4-P5 quedan
     APARCADAS — el doble click YA NO descarga los 14.07 GB de unsloth.
     Razones: (a) heretic preservado (lo que el Director valoro: sin
     "soy un asistente, no tengo emociones"); (b) el MTP es IDENTICO en
     ambos (--spec-type draft-mtp --spec-draft-n-max 2): la UD no compra
     turbo extra; (c) MTP y -np 2 son incompatibles HOY (model card de
     unsloth) — el duelo spec-vs-NP2 de P10 se corre con el vigente igual;
     (d) TODA la evidencia N3 (+23% NP2) fue medida sobre este archivo;
     (e) 0 GB de descarga y 0 superficie nueva de riesgo. La UD-IQ3_XXS
     queda PINADA (bytes/SHA ya en este archivo) como duelo opcional de
     P10 y el acceso manual p4/p5 sigue vivo.
  3. _siguiente_paso y el AUTO saltan P4-P5 cuando P4_APARCADA=True
     (constante revivable a False); el salto queda ESCRITO en el informe.
Bateria 87 -> 90 checks (U25a/b salto aparcado, E35 AUTO sin descarga;
E28 prueba el orden completo con P4_APARCADA=False puntual).
"""
import argparse
import csv
import datetime
import importlib.util
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
import urllib.request

# ---------------- R47: LA MALETA (archivo unico, pedido del Director) -------
# "demasiados links... me das un link para descargar campana desde git para
# actualizarlo y ya" (29-oct-2026). Este piloto v1.7 viaja SOLO: lleva DENTRO
# (base64 + SHA256) a sus cuatro companeros de rig y los despliega en su
# carpeta en el primer arranque. Reglas de la maleta:
#   - cada payload se verifica contra su SHA incrustado ANTES de escribir; si
#     no clava, PARADA LIMPIA (nada se ejecuta) — anti-malware de la casa.
#   - config.txt es SEMILLA: SOLO se escribe si no existe (P2 es su dueno).
#     El layout de repo (config/dump en ../configs) tambien se respeta.
#   - los instrumentos (barridos, dump) que difieran en disco se REEMPLAZAN
#     por el de la maleta con nota visible (self-heal del paquete).
#   - cero pip install: la maleta y este script usan solo stdlib.
import base64
import hashlib

_MALETA = {'barrido-n1-expertos.py': ('80C35ECB085F375311A21B1ADB77EC8E87E072B0640F0D8923F8E35A37B578D0', 'instrumento'), 'barrido-n3-eficiencia.py': ('FDD277AB97AA136EC42804DAAA486B99D97C1475CC30A12DA6FA52E01C56AF68', 'instrumento'), 'config.txt': ('746BC34652073230B7270B692E313E4DE42AA6B6E3CCA4B45982678CFDFD8EEC', 'semilla'), 'llama-flags-nuevo.txt': ('20449FFDC30EC5B0288CEB4D1F43E750903746DD883464858BFAF9D32F04FAAD', 'dump')}

_MALETA_B64 = {
    "barrido-n1-expertos.py": (
"""
IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiIKYmFycmlk
by1uMS1leHBlcnRvcy5weSB2MS4wIOKAlCBGQVNFIEQgZGVsIE5JVkVMIDEgKHJlY29ydGUgZGUg
ZXhwZXJ0b3MgKyBNRUMpCj09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09
PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CkVuY2FyZ28gZGVsIERpcmVjdG9y
ICgyNy1vY3QtMjAyNiksIHNpZ3VpZW5kbyBsYSBSb25kYSAxMiAob3JkZW4gZGUgZWplY3VjaW9u
Ck4xIC0+IE4zIC0+IE4yIC0+IE40KTogInZhbW9zIG5pdmVsIHBvciBuaXZlbC4uLiBjcmVhIHRv
ZGFzIGxhcyBwcnVlYmFzIHF1ZQpuZWNlc2l0ZXMuLi4gdmVyaWZpY2EgbWlzIGZsYWdzIG51ZXZh
cyBwZXJtaXRpZGFzLi4uIGNyZWEgdW4gYXJjaGl2byAucHkgcXVlCmhhZ2EgdG9kYXMgbGFzIHBy
dWViYXMgeSBnZW5lcmUgdW4gbG9nIHBhcmEgcGFzYXIgeSBhbmFsaXphciIuCgpBbmFsaXphIHB1
bnRvIGEgcHVudG8gaW52ZXN0aWdhY2lvbi9uaXZlbC0xLXJlY29ydGUtZXhwZXJ0b3MubWQgKFNT
MC1TUzE5KSB5CnRyYWR1Y2UgU1VTIGRvc2lzIGEgY29uZmlncyBlamVjdXRhYmxlcy4gU09MTyBt
aWRlOiBubyBpbnZlbnRhIG5hZGEgKFtNXSkuCgogIEJMT1FVRSBFWFAgICAoYmFzZSBjYW1wZW9u
YSBkZWwgYmFycmlkby0zMCwgLWNtb2UgKyAtbmdsIDk5ICsgLWxtIG5vbmUpOgogICAgRC1BTkNM
QSAoMjEuNTMgW01dKSDCtyBELUVYUDEwLUNUUkwgKGNvbnRyb2w6IGRlYmVyaWEgRlJFTkFSIH4t
Ni41JSkgwrcKICAgIEQtRVhQOCAoc2FuaXR5ID0gZGVmYXVsdCkgwrcgRC1FWFA2LzUvNC8zLzIg
KGVzY2FsZXJhIFNTNTogKzguLisyOCUgW1RdKQogIEJMT1FVRSBVQjFLICBELUVYUDQtVUIxSyAo
YXBpbGFkbyBjb24gT1JPLVVCMUssIFNTNi40OiBzaW4gY29uZmxpY3RvIFtNXSkKICBCTE9RVUUg
TUVDICAgRC1OQ00zN0M0LU1FQzAgKGNvbnRyb2wgMjIuNDkgW01dKSDCtyBELU1FQy01MTIvMTAy
NC83NjgKICAgICAgICAgICAgICAgKC0tbW9lLWNhY2hlLW1pYiwgU1MxNC0xNjsgb3JkZW4gZGUg
ZG9zaXMgZmluYWwgU1MxNToKICAgICAgICAgICAgICAgIDAgLT4gNTEyIC0+IDEwMjQgLT4gNzY4
LCBjb250cm9sIGVuIGxhIE1JU01BIHNlc2lvbikKICBCTE9RVUUgQ09NQk8gRC1FWFA0LU5DTTM3
QzQgKHN0YWNrIEVYUCB4IE5DTSwgU1M4KQoKQ29ycmVjY2lvbmVzIHF1ZSBlc3RlIHNjcmlwdCBt
YXRlcmlhbGl6YSByZXNwZWN0byBhbCBiYXJyaWRvLTMwIChuby1vcCk6CiAgMS4gTGEgY2xhdmUg
ZGVsIG92ZXJyaWRlIHNlIGNvbnN0cnV5ZSBkZXNkZSBlbCBHR1VGIFJFQUw6IHBhcnNlciBwcm9w
aW8KICAgICAoc3RkbGliKSBsZWUgZ2VuZXJhbC5hcmNoaXRlY3R1cmUgZGVsIGFyY2hpdm8geSBh
cm1hIFVOQSBjbGF2ZQogICAgIDxhcmNoPi5leHBlcnRfdXNlZF9jb3VudD1pbnQ6Sy4gTnVuY2Eg
cXdlbjNtb2UuKiBhIGNpZWdhcyAoU1M0L1NTMTEuMSkuCiAgMi4gQXV0ZW50aWNhZG9yIE9CTElH
QVRPUklPIHBvciBydW46IGVsIGxvZyBkZWwgc2VydmVyIGRlYmUgbW9zdHJhcgogICAgICJuX2V4
cGVydF91c2VkID0gSyIgKFNTMTIuMiwgZGF0YXBvaW50ICM1MTE0KS4gU2luIGVzbzogcnVuIElO
VkFMSURPLgogIDMuIFNlZ3VuZG8gYXV0ZW50aWNhZG9yOiAiQ1VEQTAgY29tcHV0ZSBidWZmZXIg
c2l6ZSIgZGViZSBCQUpBUiBjb24gawogICAgIChTUzEyLjYpLiBTZSByZWdpc3RyYSBwb3IgcnVu
LgoKUmVnbGFzIGRlIGxhIGNhc2EgcmVzcGV0YWRhcyAoYXByZW5kaWRvLm1kICsgZmxhZ3MtdmVy
aWZpY2FkYXMtTEFJQS50eHQpOgogIC0gQXVkaXRvcmlhIGRlIGZsYWdzIEFOVEVTIGRlIGFycmFu
Y2FyOiBjYWRhIHRva2VuIHZlcmlmaWNhZG8gdmVyYmF0aW0KICAgIGNvbnRyYSBJbmZvcm1hY2lv
bkNyaXRpY2EvbGxhbWEtZmxhZ3MtbnVldm8udHh0IChkdW1wIFVURi0xNiBiMTE4NTYpLgogICAg
U2kgZmFsdGEgdW5vLCBBQk9SVEEgc2luIHRvY2FyIGVsIHNlcnZlci4KICAtIFBST0hJQklEQVMg
YWJvcnRhbiBlbCBhcnJhbnF1ZTogLS1tbG9jaywgLW5rdm8sIC11YiA1MTIsIHR1cmJvKiwKICAg
IC0tc3BlYy0qIChmYXNlIEQgbm8gdXNhIHNwZWMpLCBmbGFncyBtdWVydGFzICgtLW5vLW1tYXAv
LWRpby8tLWppbmphLy1kdCkuCiAgLSBNRUM6IGFwcmVuZGlkbyBTUzIgbWlkaW8gdmVuZW5vIGVu
IGxhIGJhc2UgdmllamEgKC1jbW9lLCBjdHggMTZrLCBLViBxOF8wLAogICAgMjU2LzUxMiBNaUIg
LT4gMTMuNTEvMTcuMjIpLiBMYSBpbnZlc3RpZ2FjaW9uIFNTMTQtMTYgKHBvc3RlcmlvciwgYXVk
aXRhZGEKICAgIGVuIHJvbmRhIDEwKSBtYW50aWVuZSBsYXMgZG9zaXMgU09MTyBzb2JyZSBOQ00z
N0M0IChmaXQgKyBLViBxNF8wICsgY3R4IDRrCiAgICBsaWJlcmFuIFZSQU0pIHkgU09MTyBjb24g
Y29udHJvbCBELU1FQy0wIGVuIGxhIG1pc21hIHNlc2lvbjogc2kgcGllcmRlLAogICAgc2UgZGVz
Y2FydGEuIEVzdGUgc2NyaXB0IGVqZWN1dGEgZXhhY3RhbWVudGUgZXNvLgogIC0gUHJvdG9jb2xv
IGRlIG1lZGljaW9uIGRlbCBiYXJyaWRvIChhcHJlbmRpZG8gU1M4KTogNCBwYXNhZGFzIHggMjU2
IHRva2VucywKICAgIHByb21wdHMgRElTVElOVE9TIG1pc21hIGZhbWlsaWEsIHRlbXAgMCwgc2Vl
ZCBmaWphLCBjYWNoZV9wcm9tcHQsIHNlCiAgICBkZXNjYXJ0YSBsYSAxYSwgZGVjb2RlID0gbWVk
aWEgMi00LCBwcmVmaWxsID0gcGFzYWRhIDEgZnJpYSwgcGF1c2FzCiAgICB0ZXJtaWNhcyA2MCBz
IGNhZGEgOCBjb25maWdzLCBDU1YgcmVhbnVkYWJsZSwgcnVpZG8gZGVjbGFyYWRvICsvLTAuMy0w
LjUuCiAgLSBTYW5pdHkgYXV0b21hdGljYSBkZSAzIHBhcmVzIGVuIGRvc2lzIGRlIGNhbGlkYWQg
KHRlbXAgMCkuIExhIHB1ZXJ0YSBkZQogICAgY2FsaWRhZCBDT01QTEVUQSBlcyBsYSBzYW5pdHkg
bWFudWFsIGRlIDIwIHByb21wdHMgZGVsIERpcmVjdG9yIChTUzUpLgogIC0gR3VhcmRhcnJhaWw6
IEFCT1JUQSBzaSAvaGVhbHRoIHlhIHJlc3BvbmRlIChtZWRpciBjb24gdW4gc2VydmVyIHZpdm8K
ICAgIGZhbHNlYSB0b2RvKS4gLS1zaSBsbyBtYXRhIGFudGVzIGRlIGFycmFuY2FyLgoKU2FsaWRh
cyAoY2FycGV0YSBkZSBsb2dzLCBkZWZhdWx0IEQ6XFxaTGlhXFxmYXNlRC1sb2dzKToKICBmYXNl
RC1OMS1JTkZPUk1FLm1kICAgICA8LSBpbmZvcm1lIHBhcmEgcGFzYXIgYWwgRGlyZWN0b3IvTEFJ
QQogIGZhc2VELU4xLXJlc3VsdGFkb3MuY3N2IDwtIENTViBjcmFzaC1zYWZlIHJlYW51ZGFibGUK
ICBmYXNlRC1OMS1kYXRvcy5qc29uICAgICA8LSBkYXRvcyBjcnVkb3MgY29tcGxldG9zCiAgZmFz
ZUQtTjEtY29uc29sYS5sb2cgICAgPC0gY29waWEgZGUgdG9kYSBsYSBjb25zb2xhCiAgbG9ncy1j
b25maWdcXE5OLU5PTUJSRS5sb2cgPC0gc3Rkb3V0K3N0ZGVyciBkZWwgc2VydmVyIHBvciBjb25m
aWcKClVzbzoKICBweSBiYXJyaWRvLW4xLWV4cGVydG9zLnB5ICAgICAgICAgICAgICAtPiAxOCBj
b25maWdzICh+NTAtNjUgbWluKQogIHB5IGJhcnJpZG8tbjEtZXhwZXJ0b3MucHkgLS1xdWljayAg
ICAgIC0+IDcgY29uZmlncyBjcml0aWNhcyAofjI1IG1pbikKICBweSBiYXJyaWRvLW4xLWV4cGVy
dG9zLnB5IC0tc29sbyBleHAgICAtPiBzb2xvIGJsb3F1ZSBFWFAKICBweSBiYXJyaWRvLW4xLWV4
cGVydG9zLnB5IC0tc29sbyBleHAsbWVjLGNvbWJvLGNvbWJvMixvdCxhbmNsYWZpbgogIHB5IGJh
cnJpZG8tbjEtZXhwZXJ0b3MucHkgLS1leHRyYS1rIDksNyAtPiBkb3NpcyBrIGV4dHJhIGVuIGVs
IGJsb3F1ZSBFWFAKICBweSBiYXJyaWRvLW4xLWV4cGVydG9zLnB5IC0tc2kgICAgICAgICAtPiBt
YXRhIHVuIHNlcnZlciB2aXZvIHkgc2lndWUKCkFVRElUT1JJQSB2MS4xICgyOC1vY3QtMjAyNiwg
dHJhcyBlbCBIVFRQIDQwMCBkZSBsYSBwcmltZXJhIGNvcnJpZGEgcmVhbCk6CiAgTGEgdjEuMCBs
YW56YWJhIGVsIHNlcnZlciBjb24gU09MTyBsb3MgZmxhZ3MgZGlmZiBkZSBjYWRhIGNvbmZpZyAo
cC5lai4KICBELUFOQ0xBIHF1ZWRhYmEgY29tbyBgbGxhbWEtc2VydmVyLmV4ZSAtY21vZWApOiBT
SU4gLW0sIFNJTiAtLXBvcnQgOTkzMSwKICBTSU4gY29udGV4dG8sIFNJTiAtZmEsIFNJTiBLViBj
dWFudGl6YWRhLiBFbCBzZXJ2ZXIgcXVlIHJlc3BvbmRpYSBlbiBlbAogIHB1ZXJ0byBubyBlcmEg
ZWwgbnVlc3RybyB5IFBPU1QgL2NvbXBsZXRpb24gZGV2b2x2aW8gSFRUUCA0MDA7IGFkZW1hcyBl
bAogIENVRVJQTyBkZWwgZXJyb3Igc2UgZGVzY2FydGFiYSB5IHVuYSBleGNlcGNpb24gbWF0YWJh
IFRPRE8gZWwgYmFycmlkby4KICBDb3JyZWNjaW9uZXMgbWF0ZXJpYWxpemFkYXM6CiAgMS4gQ1JJ
VElDTzogZWwgY29tYW5kbyBsYW56YWRvIGFob3JhIGVzIFNJRU1QUkUKICAgICBgc2VydmVyIC1t
IDxtb2RlbG8+IDxCQVNFX0ZMQUdTX0ZJSkFTPiA8ZmxhZ3MgZGlmZiBkZSBsYSBjb25maWc+YAog
ICAgIChlbCBkaWZmIHZhIGRldHJhcyB5IGdhbmE6IGxsYW1hLmNwcCBkZWphIGdhbmFyIGFsIHVs
dGltbyB2YWxvcikuCiAgMi4gRWwgY3VlcnBvIGRlIENVQUxRVUlFUiBlcnJvciBIVFRQIHNlIGNh
cHR1cmEgeSBzZSBpbXByaW1lIGVuIGNvbnNvbGEsCiAgICAgbm90YSBkZWwgQ1NWIHkgSlNPTjog
dW4gNDAwIHlhIG5vIGVzIHVuIG1pc3RlcmlvLgogIDMuIFVuIGZhbGxvIEhUVFAvY29uZXhpb24g
bWFyY2EgbGEgY29uZmlnIE5PLVZBTElEQSB5IGVsIGJhcnJpZG8gU0lHVUUKICAgICBjb24gbGEg
c2lndWllbnRlIChhbnRlczogdHJhY2ViYWNrIHkgbXVlcnRlIHRvdGFsLCBDU1YgdmFjaW8pLgog
IDQuIElkZW50aWRhZCBkZWwgc2VydmVyIHZlcmlmaWNhZGEgcG9yIHN1IGxvZzogc2kgbm8gbWVu
Y2lvbmEgZWwgbW9kZWxvCiAgICAgZXNwZXJhZG8sIGVzYSBjb25maWcgc2UgaW52YWxpZGEgKG51
bmNhIG1lZGlyIHVuIHNlcnZlciBmYW50YXNtYSBvCiAgICAgd2F0Y2hkb2cgcXVlIHNlIGN1ZWxn
dWUgZGVsIHB1ZXJ0bykuCiAgNS4gTXVlcnRlIGRlbCBzZXJ2ZXIgYSBtaXRhZCBkZSBtZWRpY2lv
biAtPiBkZXRlY3RhZGEgcG9yIGV4aXQgY29kZS4KICA2LiBSZXN1bWUgdjI6IHNvbG8gbGFzIGZp
bGFzIFNJIGN1ZW50YW4gY29tbyBoZWNoYXM7IGxhcyBOTyBzZSByZS1taWRlbi4KICA3LiBMYSBh
dWRpdG9yaWEgZGUgZmxhZ3MgY3VicmUgVEFNQklFTiBsYSBiYXNlICh2MS4wIHNvbG8gbWlyYWJh
IGVsIGRpZmYpLgogIDguIGNvbnNvbGEubG9nIFNJRU1QUkUgc2luIGNvbG9yZXMgQU5TSTsgY29u
c29sYSBXaW5kb3dzIGNvbiBWVCBoYWJpbGl0YWRvLgogIDkuIHN0ZGVyciB0YW1iaWVuIHZhIGFs
IGxvZzsgQ3RybCtDIGd1YXJkYSBpbmZvcm1lIHBhcmNpYWwgKHJjIDEzMCkuCiAxMC4gUGFyc2Vy
IEdHVUYgY29uIGJ1ZmZlciBkZSAxIE1pQiAoYXJyYXlzIGdpZ2FudGVzIHNhbHRhbiBtdWNobyBt
YXMKICAgICByYXBpZG8pLiBSZXRyaWVzIHNvbG8gcGFyYSBmYWxsb3MgdHJhbnNpdG9yaW9zICg1
eHgvNDI5L2NvbmV4aW9uKS4KCkFVRElUT1JJQSBERSBDT0JFUlRVUkEgdjEuMiAoMjAyNi0xMC0y
NywgZW5jYXJnbyBEaXJlY3RvcjogImFuYWxpemEgc2kgeWEKIHRpZW5lIHRvZG8gbG8gcXVlIGRl
YmVzIHByb2JhciBlbiBlbCBiYXJyaWRvIG4xIGV4cGVydG9zIik6CiAxMS4gTlVFVkEgY29uZmln
IDE1IEQtT1QtQ1RSTCAoYmxvcXVlIG90KTogZWwgcnVuIGF1dGVudGljYWRvciBjcnV6YWRvCiAg
ICAgLW90IGRlbCBTUzE4IHF1ZWRvICJkaXNwb25pYmxlIiBlbiBwYXBlbCBwZXJvIEpBTUFTIHNl
IG1hdGVyaWFsaXpvLgogICAgIFJlcGxpY2EgbGEgZXN0cnVjdHVyYSBkZSBOQ00zN0M0ICgzNyBj
YXBhcyBNb0UgZW4gQ1BVLCAzIGVuIEdQVTsKICAgICBzaGFyZWQvYXRlbi9LViBlbiBHUFUgcG9y
cXVlICdleHBzJyBubyBtYXRjaGVhICdzaGV4cCcpIGNvbiBVTkEgc29sYQogICAgIGZsYWcgLW90
IGRlIGxpc3RhIHBvciBjb21hcyB5IFNJTiAtbmNtb2U6IGRlYmUgY2xhdmFyIGVsIGNvbnRyb2wK
ICAgICBELU5DTTM3QzQtTUVDMCAoaGlzdG9yaWNvIDIyLjQ5IFtNXSkuIFByb3RvIFNJTiBjYW1i
aW9zIChmYXNlRC1OMS12Mik6CiAgICAgZWwgcmVzdW1lIHJldXRpbGl6YSBsYXMgZmlsYXMgdjEu
MSB5IHNvbG8gbWlkZSBsYSBudWV2YS4KIDEyLiBWZXJlZGljdG8gTUVDIGEgMyBlc3RhZG9zOiBh
bnRlcyB1biBFTVBBVEUgZGVudHJvIGRlbCBydWlkbyBzZQogICAgIGV0aXF1ZXRhYmEgInBpZXJk
ZSB2cyBjb250cm9sLi4uIFNFIERFU0NBUlRBIiAodW4gKzAuMTQgaW1wcmltaWEKICAgICAicGll
cmRlICgwLjE0KSIpLiBMYSBsZXRyYSBkZWwgU1MxNSBzb2xvIG9yZGVuYSBkZXNjYXJ0YXIgc2kg
bGEgZG9zaXMKICAgICBlcyBNQVMgTEVOVEEuIEFob3JhOiBHQU5BIC8gRU1QQVRBIChzaW4gR08s
IHNpbiBjYXN0aWdvKSAvIFBJRVJERS4KIDEzLiBFbCBidWZmZXIgQ1VEQTAgKDJvIGF1dGVudGlj
YWRvciwgU1MxMi42LzEyLjkuNSkgc2UgcmVnaXN0cmFiYSBwZXJvCiAgICAgbmFkaWUgbG8gZXZh
bHVhYmE6IGFob3JhIHByb3RvY29sb19kZWNpc2lvbiBjb21wYXJhIEVYUDQvMy8yIGNvbnRyYQog
ICAgIGVsIGFuY2xhIChkZWJlIEJBSkFSIGNvbiBrKSB5IGVtaXRlIGVsIHZlcmVkaWN0byBkZWwg
cnVuIGNydXphZG8gLW90CiAgICAgY29udHJhIGVsIGNvbnRyb2wgTkNNMzdDNCBkZSBsYSBtaXNt
YSBzZXNpb24uCiAxNC4gTGEgY29sdW1uYSBDU1YgZGVsdGFfdnNfYW5jbGFfcGN0IGV4aXN0aWEg
cGVybyBqYW1hcyBzZSBsbGVuYWJhICh5CiAgICAgbGFzIGNvbnN0YW50ZXMgaGlzdG9yaWNhcyAy
MS41My8yMi40OSBlc3RhYmFuIG11ZXJ0YXMpOiBlbCBkZWx0YSBzZQogICAgIGNhbGN1bGEgYWwg
dnVlbG8geSBlbCBpbmZvcm1lIGNpdGEgbGFzIHJlZmVyZW5jaWFzIGRlbCBiYXJyaWRvLTMwLgoK
QVVESVRPUklBIHYxLjIuMSAoMjAyNi0xMC0yNywgYW5hbGlzaXMgZGUgbGEgY29ycmlkYSByZWFs
IGZhc2VELWxvZ3MuN3o6CiAgICAgMTUvMTUgY29uZmlncyBtZWRpZGFzIHNpbiBjcmFzaCwgcGVy
byBUT0RBUyBsYXMgZGUgb3ZlcnJpZGUgbWFyY2FkYXMKICAgICBJTlZBTElETyBlbiBmYWxzbyk6
IHRyZXMgYnVncyBkZSBhdXRlbnRpY2FjaW9uIGNhemFkb3MgY29uIGxhCiAgICAgdGVsZW1ldHJp
YSByZWFsIHkgY29ycmVnaWRvczoKIDE1LiBDUklUSUNPOiBlbCBhdXRlbnRpY2Fkb3IgcG9yIGxv
ZyBlc3RhYmEgTVVFUlRPIGVuIGIxMTg1NjogZXNlIGJ1aWxkCiAgICAgTk8gaW1wcmltZSBocGFy
YW1zIChjZXJvIGxpbmVhcyBsbG1fbG9hZF9wcmludF9tZXRhL3ByaW50X2luZm8gZW4KICAgICBs
b2dzLWNvbmZpZykgLT4gbl9leHBlcnRfdXNlZF9sb2c9Tm9uZSBTSUVNUFJFIC0+IDEwIHJ1bnMg
ZGUgb3ZlcnJpZGUKICAgICBJTlZBTElET1MgZW4gZmFsc28uIExBIEVTQ0FMRVJBIE1JU01BICgx
Ny44MCAtPiAzNS4xMiBtb25vdG9uYSBjb24gaykKICAgICBkZW11ZXN0cmEgcXVlIGVsIG92ZXJy
aWRlIFNJIGFwbGljby4gQXV0ZW50aWNhY2lvbiBhaG9yYSBlbiA0IHZpYXM6CiAgICAgTE9HIChy
ZWdleCBhbXBsaWFkYSkgLT4gUFJPUFMgKEdFVCAvcHJvcHMsIHNvbG8gQ09ORklSTUEgc2kgZWwg
dmFsb3IKICAgICBjb2luY2lkZSkgLT4gQ09NUCAoY29tcG9ydGFtZW50YWw6IGxhIGRvc2lzIGRl
YmUgcmVzcG9uZGVyIHZzIGxhIHJlZgogICAgIGs9OCBkZSBzZXNpb24gbWFzIGFsbGEgZGVsIHJ1
aWRvKSAtPiBERUZBVUxUIChrPTggZXMgbm8tb3AgcG9yCiAgICAgZGlzZW5vKS4gTGEgdmlhIHVz
YWRhIHF1ZWRhIGVuIGxhIGNvbHVtbmEgQ1NWIGF1dGhfdmlhLgogMTYuIEZhbHNvIHBvc2l0aXZv
ICJmaXQgYWJvcnRhZG8iOiBsYSBsaW5lYQogICAgIGBjb21tb25fZml0X3BhcmFtczogZmFpbGVk
IHRvIGZpdCBwYXJhbXMgLi4uOiBuX2dwdV9sYXllcnMgYWxyZWFkeQogICAgIHNldCBieSB1c2Vy
IHRvIDk5LCBhYm9ydGAgZXMgZWwgQVVUTy1GSVQgREVDTElOQU5ETyBBQ1RVQVIgKG5nbCB5YQog
ICAgIGZpamFkbyBwb3IgdXN1YXJpbzsgZXNwZXJhZG8gZW4gVE9EQVMgZXN0YXMgY29uZmlncyks
IG5vIHVuIGZhbGxvIGRlCiAgICAgVlJBTS4gQWhvcmEgZXMgbm90YSBpbmZvcm1hdGl2YSB5IE5P
IGludmFsaWRhOyB1biBmaXQgcG9yIG90cmEgY2F1c2EKICAgICBvIHVuIGZhaWxlZCB0byBhbGxv
Y2F0ZSBzaWd1ZW4gaW52YWxpZGFuZG8uCiAxNy4gQW5jbGEgZGVwcmltaWRhIHBvciBzZXNnbyBk
ZSBhcnJhbnF1ZTogRC1FWFA4IChrPTggPSBkZWZhdWx0LCBuby1vcAogICAgIHBvciBkaXNlbm8p
IG1pZGlvICsxNS4yJSBzb2JyZSBlbCBhbmNsYTsgRVhQMTAgZnJlbm8gLTE1LjQlIHZzIEVYUDgu
CiAgICAgTGEgMWEgY29uZmlnIGRlIGxhIHNlc2lvbiBzYWxlIHNpc3RlbXRpY2FtZW50ZSBsZW50
YSAod2FybXVwIE9TL0dQVQogICAgIG5vIGN1cmFkbyBwb3IgZGVzY2FydGFyIHNvbG8gbGEgcGFz
YWRhIDEpLiBDb250cmFtZWRpZGFzOiAtbHYgNCBlbiBsYQogICAgIGJhc2UgKGxvZyB2ZXJib3Nv
OiBlbCBidWlsZCBwdWVkZSBpbXByaW1pciBocGFyYW1zKSwgTlVFVkEgY29uZmlnIDE2CiAgICAg
RC1BTkNMQS1GSU4gKGJvb2tlbmQ6IHJlLWFuY2xhIGFsIGNpZXJyZSwgbWlkZSBlbCBkcmlmdCBk
ZSBzZXNpb24pIHkKICAgICBlbCBpbmZvcm1lIGVtaXRlIGRlbHRhcyB0YW1iaWVuICJ2cyBrPTgi
IChFWFA4ID0gcmVmZXJlbmNpYSBkZSBzZXNpb24KICAgICBzYW5hKS4gTlVFVkFTIGNvbmZpZ3Mg
MTcvMTggKGJsb3F1ZSBjb21ibzIpOiBlbCBzdGFjayBmaW5hbCBvYmpldGl2bwogICAgIEVYUDQg
eCBOQ00zN0M0IHggTUVDLTc2OC8xMDI0IChjb21wb3NpY2lvbiBkZSBsb3MgZG9zIEdPKS4KIDE4
LiBTYW5pdHkgYXV0bzogbl9wcmVkaWN0IDQ4IC0+IDEyOCB5IGVzdGFkbyBUUlVOQ0FETzogc2kg
bGEgcmVzcHVlc3RhCiAgICAgcXVlZG8gZGVudHJvIGRlIHVuIDx0aGluaz4gc2luIGNlcnJhciAo
cmF6b25hbWllbnRvIGxhcmdvKSBubyBjdWVudGEKICAgICBjb21vIGZhbGxvIGRlIGNhbGlkYWQg
KGFydGVmYWN0byBkZWwgcHJvYmUpLCBzb2xvIGxvcyBmYWxsb3MgcmVhbGVzCiAgICAgKHJlc3B1
ZXN0YSB0ZXJtaW5hZGEgc2luIGxhIHBhbGFicmEgZXNwZXJhZGEpIGFsYXJtYW4uIGs9NS82IGRl
IGxhCiAgICAgY29ycmlkYSByZWFsICJmYWxsYWJhbiIgcG9yIGVzdG87IGs9MyBmYWxsbyBkZSB2
ZXJkYWQgKDQzMSAhPSAzOTEpLgogMTkuIERpc3BlcnNpb24gZW50cmUgcGFzYWRhczogc2kgbWF4
L21pbiBkZSBkZWMgMi00IHN1cGVyYSAxLjA4LCBub3RhIGVuCiAgICAgZWwgQ1NWIChsYSBNRUMt
NTEyIHJlYWwgdGVuaWEgdW4gb3V0bGllciAyMi4zNyBlbnRyZSAxOC4yLTE4LjkpLgogMjAuIFBy
b3RvIHN1YmUgYSBmYXNlRC1OMS12MyAoYmFzZSBhaG9yYSBsbGV2YSAtbHYgNCB5IGhheSAxOCBj
b25maWdzKToKICAgICBhbCBhcnJhbmNhciwgc2kgZWwgQ1NWIGV4aXN0ZW50ZSBlcyBkZSBvdHJv
IHByb3RvIHNlIEFSQ0hJVkEgY29tbwogICAgIGZhc2VELU4xLXJlc3VsdGFkb3MtPHByb3RvLXZp
ZWpvPi5jc3YgKG5hZGEgc2UgYm9ycmEpIHkgbGEgY29ycmlkYQogICAgIGVzIGNvbXBsZXRhLiBS
ZS1jb3JyaWRhIGNvbXBsZXRhIHJlY29tZW5kYWRhOiBlbCBhdXRoIGxpbXBpbyArIGJvb2tlbmQK
ICAgICArIHNhbml0eSAxMjgganVzdGlmaWNhIGxvcyB+NTAgbWluLgoiIiIKaW1wb3J0IGFyZ3Bh
cnNlCmltcG9ydCBjc3YKaW1wb3J0IGRhdGV0aW1lCmltcG9ydCBqc29uCmltcG9ydCBvcwppbXBv
cnQgcmUKaW1wb3J0IHN0cnVjdAppbXBvcnQgc3VicHJvY2VzcwppbXBvcnQgc3lzCmltcG9ydCB0
aW1lCmltcG9ydCB1cmxsaWIuZXJyb3IKaW1wb3J0IHVybGxpYi5yZXF1ZXN0CgojIC0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0gY29uc3RhbnRlcyBkZWwgcmlnIChSdXRhc0FyY2hpdm9zLm1kKSAt
LS0tLS0tLS0tLS0KVkVSU0lPTiA9ICJiYXJyaWRvLW4xLWV4cGVydG9zIHYxLjIuMSAoMjAyNi0x
MC0yNykiClBST1RPID0gImZhc2VELU4xLXYzIgoKUlVUQV9TRVJWRVJfREVGID0gciJEOlxsbGFt
YS5jcHBcbGxhbWEtc2VydmVyLmV4ZSIKUlVUQV9NT0RFTE9fREVGID0gKHIiRDpcWkxpYVxtb2Rl
bHMiCiAgICAgICAgICAgICAgICAgICByIlxRd2VuMy42LTM1Qi1BM0ItdW5jZW5zb3JlZC1oZXJl
dGljLU5hdGl2ZS1NVFAtUHJlc2VydmVkLUFQRVgtSS1NSU5JLmdndWYiKQpfU0NSSVBUX0RJUiA9
IG9zLnBhdGguZGlybmFtZShvcy5wYXRoLmFic3BhdGgoX19maWxlX18pKQpSVVRBX0RVTVBfREVG
ID0gb3MucGF0aC5qb2luKF9TQ1JJUFRfRElSLCAibGxhbWEtZmxhZ3MtbnVldm8udHh0IikKaWYg
bm90IG9zLnBhdGguZXhpc3RzKFJVVEFfRFVNUF9ERUYpOiAgICMgUm9uZGEgMjE6IGxheW91dCBk
ZWwgcmVwbwogICAgX2R1bXBfcmVwbyA9IG9zLnBhdGguam9pbihfU0NSSVBUX0RJUiwgIi4uIiwg
ImNvbmZpZ3MiLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAibGxhbWEtZmxhZ3MtbnVl
dm8udHh0IikKICAgIGlmIG9zLnBhdGguZXhpc3RzKF9kdW1wX3JlcG8pOgogICAgICAgIFJVVEFf
RFVNUF9ERUYgPSBfZHVtcF9yZXBvCkxPR1NfRElSX0RFRiA9IHIiRDpcWkxpYVxmYXNlRC1sb2dz
IgoKQUxJQVMgPSAiYXBleDM1YiIKSE9TVF9ERUYgPSAiMTI3LjAuMC4xIgpQVUVSVE9fREVGID0g
OTkzMQpCWVRFU19NT0RFTE9fRVNQRVJBRE9TID0gMTQyNzMyNzczNzYgICMgUnV0YXNBcmNoaXZv
cy5tZCAvIGZsYWdzLXZlcmlmaWNhZGFzCkJVSUxEX1BJTl9FU1BFUkFETyA9ICIxMTg1NiIgICAg
ICAgICAgIyAwLjcuMC1kZXYgKGJ1aWxkIDExODU2LCBjb21taXQgMzY0MjIzOGNjKQoKIyBBbmNs
YXMgaGlzdG9yaWNhcyBbTV0gKGJhcnJpZG8tMzAsIDI2LW9jdC0yMDI2KQpBTkNMQV9VQjFLID0g
MjEuNTMgICAgIyBpZCAzMiBPUk8tVUIxSyAvIEFOQ0hPUi1CIChkZWNvZGUpCk5DTTM3QzRfUkVG
ID0gMjIuNDkgICAjIGlkIDE0IE5DTTM3QzQgKGRlY29kZSwgKzQuNCUpClRFQ0hPX1JVSURPID0g
MC41ICAgICAjIGFwcmVuZGlkbyBTUzg6ICsvLTAuMy0wLjUgdC9zIC0+IHpvbmEgbXVlcnRhCgoj
IEJBU0VfRkxBR1MgPSB2ZXJiYXRpbSBiYXJyaWRvLXF3ZW4tMzAucHkgKGNhbXBlb24gLWxtIG5v
bmUgU0lOIGNvbG9jYWNpb247CiMgbGEgY29sb2NhY2lvbiB2YSBQT1IgQ09ORklHOiAtY21vZSBw
YXJhIEVYUCwgLW5jbW9lIDM3IHBhcmEgTUVDL05DTSkuCiMgTWFudGllbmUgLW5nbCA5OSB5IC1j
IDE2Mzg0IHBhcmEgcXVlIGxvcyBudW1lcm9zIHNlYW4gY29tcGFyYWJsZXMgMToxIGNvbgojIGVs
IGJhcnJpZG8tMzAgKEFOQ0hPUi1CIDIxLjUzLCBOQ00zN0M0IDIyLjQ5KS4KIyB2MS4yLjE6IC1s
diA0IChsb2cgdmVyYm9zbywgdmVyYmF0aW0gZW4gZWwgZHVtcCk6IGIxMTg1NiBOTyBpbXByaW1l
CiMgaHBhcmFtcyBhIHZlcmJvc2lkYWQgMyAobGEgY29ycmlkYSByZWFsIGxvIGRlbXVlc3RyYTog
Y2VybyBsaW5lYXMKIyBuX2V4cGVydF91c2VkIGVuIGxvZ3MtY29uZmlnKSB5IGVsIGF1dGVudGlj
YWRvciBwb3IgbG9nIGxhcyBuZWNlc2l0YS4KQkFTRV9GTEFHU19GSUpBUyA9IFsKICAgICItbmds
IiwgIjk5IiwKICAgICItYyIsICIxNjM4NCIsICItYiIsICIyMDQ4IiwgIi11YiIsICIyNTYiLAog
ICAgIi1mYSIsICJvbiIsICItY3RrIiwgInE4XzAiLCAiLWN0diIsICJxOF8wIiwKICAgICItdCIs
ICI0IiwgIi0tcHJpbyIsICIyIiwgIi0tbm8tbW1wcm9qIiwKICAgICItbG0iLCAibm9uZSIsCiAg
ICAiLWx2IiwgIjQiLAogICAgIi0taG9zdCIsIEhPU1RfREVGLCAiLS1wb3J0Iiwgc3RyKFBVRVJU
T19ERUYpLApdCkNNID0gWyItY21vZSJdClVCMUsgPSBbIi11YiIsICIxMDI0IiwgIi1iIiwgIjQw
OTYiXSAgICAgICAgICAgICMgaWQgMzIgdmVyYmF0aW0gYmFycmlkby0zMApOQ00zN0M0ID0gWyIt
bmNtb2UiLCAiMzciLCAiLWMiLCAiNDA5NiIsCiAgICAgICAgICAgIi1jdGsiLCAicTRfMCIsICIt
Y3R2IiwgInE0XzAiXSAgICAgICMgaWQgMTQgdmVyYmF0aW0gYmFycmlkby0zMAojIFNTMTg6IGVx
dWl2YWxlbnRlIC1vdCBkZSBOQ00zN0M0IGJham8gbGEgbGVjdHVyYSBkZWwgZHVtcCAoImZpcnN0
IE4iIGVuCiMgQ1BVIC0+IHF1ZWRhbiBlbiBHUFUgbGFzIGNhcGFzIDM3LTM5KS4gVW5hIHNvbGEg
ZmxhZywgbGlzdGEgcG9yIGNvbWFzCiMgKHJlcGV0aXIgLW90IGVzdGEgZGVwcmVjYWRvKTsgJ2V4
cHMnIE5PIG1hdGNoZWEgJ3NoZXhwJyAtPiBlbCBzaGFyZWQKIyBleHBlcnQsIGxhIGF0ZW5jaW9u
IHkgbGEgS1YgbnVuY2Egc2FsZW4gZGUgR1BVIChpZ3VhbCBxdWUgLW5jbW9lKS4KT1RfRVFVSVZB
TEVOVEUgPSAociJibGtcLigzWzctOV0pXC5mZm5fKGdhdGV8dXB8ZG93bilfZXhwcz1DVURBMCwi
CiAgICAgICAgICAgICAgICAgIHIiZXhwcz1DUFUiKQoKIyAtLS0tIHZhbG9yZXMgbGVnYWxlcyAo
dmVyYmF0aW0gZGVsIGR1bXAgYjExODU2LCBhdWRpdGFkb3MgMjctb2N0LTIwMjYpIC0tLS0tCkxN
X01PRE9TID0geyJhdXRvIiwgIm5vbmUiLCAibW1hcCIsICJtbG9jayIsICJtbWFwK21sb2NrIiwg
ImRpbyJ9CktWX1RJUE9TID0geyJmMzIiLCAiZjE2IiwgImJmMTYiLCAicThfMCIsICJxNF8wIiwg
InE0XzEiLCAiaXE0X25sIiwgInE1XzAiLCAicTVfMSJ9CkZBX1ZBTE9SRVMgPSB7Im9uIiwgIm9m
ZiIsICJhdXRvIn0KCiMgLS0tLSBwcm9oaWJpZGFzIChhcHJlbmRpZG8ubWQgU1MyL1NTNyArIGZs
YWdzLXZlcmlmaWNhZGFzIHNlY2Npb24gQykgLS0tLS0tLQpQUk9ISUJJREFTX0VYQUNUQVMgPSB7
CiAgICAiLS1tbG9jayIsICItbmt2byIsICItLW5vLWt2LW9mZmxvYWQiLCAiLS1kcmFmdC1tYXgi
LCAiLWRyYWZ0IiwKICAgICItLWRyYWZ0LW1pbiIsICItZHQiLCAiLS1kZWZyYWctdGhvbGQiLCAi
LS1uby1tbWFwIiwgIi0tZGlyZWN0LWlvIiwKICAgICItZGlvIiwgIi0tamluamEiLAp9ClBST0hJ
QklEQVNfUFJFRklKTyA9ICgiLS1zcGVjLSIsICItdHVyYm8iLCAidHVyYm8iKSAgIyBmYXNlIEQg
bm8gdXNhIHNwZWMKCiMgVG9rZW5zIHF1ZSBlbCBkdW1wIERFQkUgY29udGVuZXIgcGFyYSBxdWUg
ZXN0ZSBzY3JpcHQgYXJyYW5xdWUKRFVNUF9SRVFVRVJJRE9TID0gWwogICAgIi1tLCIsICItLW1v
ZGVsIiwgIi1hLCIsICItLWFsaWFzIiwgIi1uZ2wsIiwgIi0tZ3B1LWxheWVycyIsCiAgICAiLWNt
b2UsIiwgIi0tY3B1LW1vZSIsICItbmNtb2UsIiwgIi0tbi1jcHUtbW9lIiwKICAgICItLW92ZXJy
aWRlLWt2IiwgIi0tbW9lLWNhY2hlLW1pYiIsICItb3QsIiwgIi0tb3ZlcnJpZGUtdGVuc29yIiwK
ICAgICItbG0sIiwgIi0tbG9hZC1tb2RlIiwKICAgICItZmEsIiwgIi0tZmxhc2gtYXR0biIsICIt
Y3RrLCIsICItLWNhY2hlLXR5cGUtayIsICItY3R2LCIsCiAgICAiLS1jYWNoZS10eXBlLXYiLCAi
LWMsIiwgIi0tY3R4LXNpemUiLCAiLWIsIiwgIi0tYmF0Y2gtc2l6ZSIsCiAgICAiLXViLCIsICIt
LXViYXRjaC1zaXplIiwgIi10LCIsICItLXRocmVhZHMiLCAiLS1wcmlvIiwKICAgICItLW5vLW1t
cHJvaiIsICItLWhvc3QiLCAiLS1wb3J0IiwgInE4XzAiLCAicTRfMCIsCiAgICAib258b2ZmfGF1
dG8iLAogICAgIi1sdiwiLCAiLS1sb2ctdmVyYm9zaXR5IiwKXQoKIyAtLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tIHV0aWxpZGFkZXMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tClVTRV9DT0xPUiA9IEZhbHNlCnRyeToKICAgIFVTRV9DT0xPUiA9IHN5cy5zdGRvdXQuaXNh
dHR5KCkKZXhjZXB0IEV4Y2VwdGlvbjoKICAgIFVTRV9DT0xPUiA9IEZhbHNlCgoKZGVmIF9jKHR4
dCwgY29kZSk6CiAgICBpZiBub3QgVVNFX0NPTE9SOgogICAgICAgIHJldHVybiBzdHIodHh0KQog
ICAgcmV0dXJuICJceDFiWyVzbSVzXHgxYlswbSIgJSAoY29kZSwgdHh0KQoKCmRlZiBib2xkKHQp
OgogICAgcmV0dXJuIF9jKHQsICIxIikKCgpkZWYgcmVkKHQpOgogICAgcmV0dXJuIF9jKHQsICI5
MSIpCgoKZGVmIGdyZWVuKHQpOgogICAgcmV0dXJuIF9jKHQsICI5MiIpCgoKZGVmIHllbGxvdyh0
KToKICAgIHJldHVybiBfYyh0LCAiOTMiKQoKCmRlZiBjeWFuKHQpOgogICAgcmV0dXJuIF9jKHQs
ICI5NiIpCgoKZGVmIGdyYXkodCk6CiAgICByZXR1cm4gX2ModCwgIjkwIikKCgpfQU5TSV9SRSA9
IHJlLmNvbXBpbGUociJceDFiXFtbMC05O10qW0EtWmEtel0iKQoKCmNsYXNzIFRlZToKICAgICIi
IkNvcGlhIGxhIGNvbnNvbGEgYSB1biBhcmNoaXZvLiBFbiBlbCBBUkNISVZPIHNlIGVsaW1pbmFu
IGxvcyBjb2RpZ29zCiAgICBkZSBjb2xvciBBTlNJIChlbCBsb2cgc2UgbGVlL3BhcnNlYSBkZXNw
dWVzKTsgZW4gcGFudGFsbGEgc2UgY29uc2VydmFuCiAgICBzaSBsYSBjb25zb2xhIGxvcyBzb3Bv
cnRhLiIiIgoKICAgIGRlZiBfX2luaXRfXyhzZWxmLCBydXRhKToKICAgICAgICBzZWxmLnJ1dGEg
PSBydXRhCiAgICAgICAgc2VsZi5mID0gb3BlbihydXRhLCAidyIsIGVuY29kaW5nPSJ1dGYtOCIs
IGVycm9ycz0icmVwbGFjZSIpCgogICAgZGVmIHdyaXRlKHNlbGYsIHMpOgogICAgICAgIHRyeToK
ICAgICAgICAgICAgc3lzLl9fc3Rkb3V0X18ud3JpdGUocykKICAgICAgICBleGNlcHQgRXhjZXB0
aW9uOgogICAgICAgICAgICBwYXNzCiAgICAgICAgdHJ5OgogICAgICAgICAgICBzZWxmLmYud3Jp
dGUoX0FOU0lfUkUuc3ViKCIiLCBzKSkKICAgICAgICAgICAgc2VsZi5mLmZsdXNoKCkKICAgICAg
ICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBwYXNzCiAgICAgICAgcmV0dXJuIGxlbihz
KQoKICAgIGRlZiBmbHVzaChzZWxmKToKICAgICAgICB0cnk6CiAgICAgICAgICAgIHN5cy5fX3N0
ZG91dF9fLmZsdXNoKCkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBwYXNz
CiAgICAgICAgdHJ5OgogICAgICAgICAgICBzZWxmLmYuZmx1c2goKQogICAgICAgIGV4Y2VwdCBF
eGNlcHRpb246CiAgICAgICAgICAgIHBhc3MKCgpkZWYgYWhvcmEoKToKICAgIHJldHVybiBkYXRl
dGltZS5kYXRldGltZS5ub3coKS5zdHJmdGltZSgiJVktJW0tJWQgJUg6JU06JVMiKQoKCmRlZiBt
ZWRpYSh4cyk6CiAgICB4cyA9IFt4IGZvciB4IGluIHhzIGlmIHggaXMgbm90IE5vbmUgYW5kIHgg
PT0geF0KICAgIHJldHVybiBzdW0oeHMpIC8gbGVuKHhzKSBpZiB4cyBlbHNlIE5vbmUKCgpkZWYg
Zm10KHgsIG5kPTIsIHN1Zj0iIik6CiAgICBpZiB4IGlzIE5vbmU6CiAgICAgICAgcmV0dXJuICJO
L0QiCiAgICB0cnk6CiAgICAgICAgeCA9IGZsb2F0KHgpCiAgICBleGNlcHQgRXhjZXB0aW9uOgog
ICAgICAgIHJldHVybiBzdHIoeCkKICAgIHJldHVybiAoIiUuIiArIHN0cihuZCkgKyAiZiVzIikg
JSAoeCwgc3VmKQoKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tIGF1ZGl0b3JpYSBkZSBmbGFncyBj
b250cmEgZWwgZHVtcCAtLS0tLS0tLS0tLS0tLS0tLS0tLQpkZWYgZGVjb2RpZmljYXJfZHVtcChy
dXRhX2R1bXApOgogICAgcmF3ID0gb3BlbihydXRhX2R1bXAsICJyYiIpLnJlYWQoKQogICAgY2Fu
ZGlkYXRvcyA9IFtdCiAgICBmb3IgZW5jIGluICgidXRmLTE2LWxlIiwgInV0Zi0xNiIsICJ1dGYt
OCIpOgogICAgICAgIHRyeToKICAgICAgICAgICAgY2FuZGlkYXRvcy5hcHBlbmQocmF3LmRlY29k
ZShlbmMpKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgIGNvbnRpbnVlCiAg
ICBpZiBub3QgY2FuZGlkYXRvczoKICAgICAgICByYWlzZSBTeXN0ZW1FeGl0KHJlZCgiRkFUQUw6
IG5vIHB1ZGUgZGVjb2RpZmljYXIgZWwgZHVtcCAlcyIgJSBydXRhX2R1bXApKQogICAgZm9yIHR4
dCBpbiBjYW5kaWRhdG9zOgogICAgICAgIGlmICItLW1vZGVsIiBpbiB0eHQgb3IgIi0tb3ZlcnJp
ZGUta3YiIGluIHR4dDoKICAgICAgICAgICAgcmV0dXJuIHR4dAogICAgcmV0dXJuIG1heChjYW5k
aWRhdG9zLCBrZXk9bGVuKQoKCmRlZiBhdWRpdGFyX2ZsYWdzKHJ1dGFfZHVtcCwgbGlzdGFfY29u
ZmlncywgYmFzZV9mbGFncz0oKSk6CiAgICAiIiJWZXJpZmljYSBxdWUgVE9ET1MgbG9zIHRva2Vu
cyBkZSBmbGFnIGRlIFRPREFTIGxhcyBjb25maWdzIChiYXNlICsKICAgIGRpZmY7IHYxLjEgbGEg
QkFTRSB0YW1iaWVuIHNlIGF1ZGl0YSwgYW50ZXMgc2UgbGUgcGFzYWJhIHBvciBhbHRvKQogICAg
ZXN0ZW4gdmVyYmF0aW0gZW4gZWwgZHVtcCBkZWwgYnVpbGQgKGZ1ZW50ZSBkZSB2ZXJkYWQgIzEp
LiBBYm9ydGEgc2kKICAgIGZhbHRhIHVuby4gVGFtYmllbiByZXZpc2EgcHJvaGliaWRhcyB5IHZh
bG9yZXMgbGVnYWxlcy4gRGV2dWVsdmUgbGlzdGEKICAgIGRlIHByb2JsZW1hcyAodmFjaWEgPSB2
ZXJkZSkuIiIiCiAgICBwcm9ibGVtYXMgPSBbXQogICAgdHh0ID0gZGVjb2RpZmljYXJfZHVtcChy
dXRhX2R1bXApCiAgICBmYWx0YW4gPSBbdCBmb3IgdCBpbiBEVU1QX1JFUVVFUklET1MgaWYgdCBu
b3QgaW4gdHh0XQogICAgaWYgZmFsdGFuOgogICAgICAgIHByb2JsZW1hcy5hcHBlbmQoImVsIGR1
bXAgbm8gY29udGllbmUgKHJlcXVlcmlkb3MpOiAlcyIgJSBmYWx0YW4pCgogICAgdG9rZW5zX3Vz
YWRvcyA9IHNldCgpCiAgICBmb3IgY2ZnIGluIGxpc3RhX2NvbmZpZ3M6CiAgICAgICAgZmwgPSBs
aXN0KGJhc2VfZmxhZ3MpICsgbGlzdChjZmdbImZsYWdzIl0pCiAgICAgICAgZm9yIHRvayBpbiBm
bDoKICAgICAgICAgICAgaWYgdG9rLnN0YXJ0c3dpdGgoIi0iKToKICAgICAgICAgICAgICAgIHRv
a2Vuc191c2Fkb3MuYWRkKHRvaykKICAgICAgICBmb3IgcGFyIGluIFBST0hJQklEQVNfRVhBQ1RB
UzoKICAgICAgICAgICAgaWYgcGFyIGluIGZsOgogICAgICAgICAgICAgICAgcHJvYmxlbWFzLmFw
cGVuZCgiY29uZmlnICVzIHVzYSBQUk9ISUJJREEgJXMiICUgKGNmZ1siaWQiXSwgcGFyKSkKICAg
ICAgICBmb3IgdG9rIGluIGZsOgogICAgICAgICAgICBpZiBhbnkodG9rLnN0YXJ0c3dpdGgocCkg
b3IgdG9rID09IHAgZm9yIHAgaW4gUFJPSElCSURBU19QUkVGSUpPKToKICAgICAgICAgICAgICAg
IGlmIHRvayBub3QgaW4gKCItLW5vLW1tcHJvaiIsKToKICAgICAgICAgICAgICAgICAgICBwcm9i
bGVtYXMuYXBwZW5kKCJjb25maWcgJXMgdXNhIHByZWZpam8gcHJvaGliaWRvICVzIgogICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgJSAoY2ZnWyJpZCJdLCB0b2spKQogICAgIyAt
dWIgNTEyIHByb2hpYmlkbyAoYXByZW5kaWRvOiAyMC43NywgcnVpZG87IGVsIHZhbGlkYWRvciBy
ZWNoYXphKQogICAgZm9yIGNmZyBpbiBsaXN0YV9jb25maWdzOgogICAgICAgIGZsID0gbGlzdChi
YXNlX2ZsYWdzKSArIGxpc3QoY2ZnWyJmbGFncyJdKQogICAgICAgIGZvciBpLCB0b2sgaW4gZW51
bWVyYXRlKGZsKToKICAgICAgICAgICAgaWYgdG9rID09ICItdWIiIGFuZCBpICsgMSA8IGxlbihm
bCkgYW5kIGZsW2kgKyAxXSA9PSAiNTEyIjoKICAgICAgICAgICAgICAgIHByb2JsZW1hcy5hcHBl
bmQoImNvbmZpZyAlcyB1c2EgLXViIDUxMiAoUFJPSElCSURPKSIgJSBjZmdbImlkIl0pCiAgICAg
ICAgICAgIGlmIHRvayBpbiAoIi1jdGsiLCAiLWN0diIpIGFuZCBpICsgMSA8IGxlbihmbCk6CiAg
ICAgICAgICAgICAgICB2ID0gZmxbaSArIDFdCiAgICAgICAgICAgICAgICBpZiB2IG5vdCBpbiBL
Vl9USVBPUyBvciB2LnN0YXJ0c3dpdGgoInR1cmJvIik6CiAgICAgICAgICAgICAgICAgICAgcHJv
YmxlbWFzLmFwcGVuZCgiY29uZmlnICVzIHVzYSBLViBpbGVnYWwgJXIiICUgKGNmZ1siaWQiXSwg
dikpCiAgICAgICAgICAgIGlmIHRvayA9PSAiLWxtIiBhbmQgaSArIDEgPCBsZW4oZmwpIGFuZCBm
bFtpICsgMV0gbm90IGluIExNX01PRE9TOgogICAgICAgICAgICAgICAgcHJvYmxlbWFzLmFwcGVu
ZCgiY29uZmlnICVzIHVzYSAtbG0gaWxlZ2FsICVyIiAlIChjZmdbImlkIl0sIGZsW2kgKyAxXSkp
CiAgICAgICAgICAgIGlmIHRvayA9PSAiLWZhIiBhbmQgaSArIDEgPCBsZW4oZmwpIGFuZCBmbFtp
ICsgMV0gbm90IGluIEZBX1ZBTE9SRVM6CiAgICAgICAgICAgICAgICBwcm9ibGVtYXMuYXBwZW5k
KCJjb25maWcgJXMgdXNhIC1mYSBpbGVnYWwgJXIiICUgKGNmZ1siaWQiXSwgZmxbaSArIDFdKSkK
CiAgICBmb3IgdG9rIGluIHNvcnRlZCh0b2tlbnNfdXNhZG9zKToKICAgICAgICBpZiB0b2sgaW4g
KCItLW92ZXJyaWRlLWt2IiwgIi0tbW9lLWNhY2hlLW1pYiIpOgogICAgICAgICAgICBjb250aW51
ZSAgIyB5YSB2ZXJpZmljYWRvcyBlbiBEVU1QX1JFUVVFUklET1MKICAgICAgICBwYXRyb24gPSBy
ZS5lc2NhcGUodG9rKSArIHIiKD89W1xzLF18JCkiCiAgICAgICAgaWYgbm90IHJlLnNlYXJjaChw
YXRyb24sIHR4dCk6CiAgICAgICAgICAgIHByb2JsZW1hcy5hcHBlbmQoInRva2VuICVyIE5PIGFw
YXJlY2UgdmVyYmF0aW0gZW4gZWwgZHVtcCIgJSB0b2spCiAgICByZXR1cm4gcHJvYmxlbWFzCgoK
IyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIHBhcnNlciBHR1VGIChzdGRsaWIpIC0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tCl9HR1VGX1RBTSA9IHswOiAxLCAxOiAxLCAyOiAyLCAzOiAy
LCA0OiA0LCA1OiA0LCA2OiA0LCA3OiAxLCAxMDogOCwgMTE6IDgsIDEyOiA4fQpfR0dVRl9GTVQg
PSB7MDogIjxCIiwgMTogIjxiIiwgMjogIjxIIiwgMzogIjxoIiwgNDogIjxJIiwgNTogIjxpIiwK
ICAgICAgICAgICAgIDY6ICI8ZiIsIDEwOiAiPFEiLCAxMTogIjxxIiwgMTI6ICI8ZCJ9CgoKZGVm
IF9nZ3VmX3N0cmluZyhmKToKICAgIChuLCkgPSBzdHJ1Y3QudW5wYWNrKCI8USIsIGYucmVhZCg4
KSkKICAgIGlmIG4gPiAxMDAgKiAxMDI0ICogMTAyNDoKICAgICAgICByYWlzZSBWYWx1ZUVycm9y
KCJzdHJpbmcgR0dVRiBkZW1hc2lhZG8gbGFyZ286ICVkIiAlIG4pCiAgICBiID0gZi5yZWFkKG4p
CiAgICByZXR1cm4gYi5kZWNvZGUoInV0Zi04IiwgZXJyb3JzPSJyZXBsYWNlIikKCgpkZWYgX2dn
dWZfdmFsb3IoZiwgdnR5cGUsIHByb2Z1bmRpZGFkPTApOgogICAgaWYgcHJvZnVuZGlkYWQgPiA0
OgogICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoImFuaWRhbWllbnRvIEdHVUYgZGVtYXNpZGFkbyBw
cm9mdW5kbyIpCiAgICBpZiB2dHlwZSA9PSA4OgogICAgICAgIHJldHVybiBfZ2d1Zl9zdHJpbmco
ZikKICAgIGlmIHZ0eXBlIGluIF9HR1VGX0ZNVDoKICAgICAgICAodiwpID0gc3RydWN0LnVucGFj
ayhfR0dVRl9GTVRbdnR5cGVdLCBmLnJlYWQoX0dHVUZfVEFNW3Z0eXBlXSkpCiAgICAgICAgcmV0
dXJuIHYKICAgIGlmIHZ0eXBlID09IDc6CiAgICAgICAgcmV0dXJuIGJvb2woZi5yZWFkKDEpWzBd
KQogICAgaWYgdnR5cGUgPT0gOTogICMgYXJyYXk6IGVsZW1fdHlwZSB1MzIgKyBjb3VudCB1NjQg
KyBlbGVtcwogICAgICAgIChldHlwZSwpID0gc3RydWN0LnVucGFjaygiPEkiLCBmLnJlYWQoNCkp
CiAgICAgICAgKG4sKSA9IHN0cnVjdC51bnBhY2soIjxRIiwgZi5yZWFkKDgpKQogICAgICAgIGlm
IG4gPiA1XzAwMF8wMDA6CiAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoImFycmF5IEdHVUYg
ZGVtYXNpYWRvIGxhcmdvOiAlZCIgJSBuKQogICAgICAgIG91dCA9IFtdCiAgICAgICAgZm9yIF8g
aW4gcmFuZ2Uobik6CiAgICAgICAgICAgIGlmIGxlbihvdXQpID49IDg6ICAjIGJhc3RhIHVuYSBt
dWVzdHJhOyBzYWx0YSBlbCByZXN0byByYXBpZG8KICAgICAgICAgICAgICAgIF9nZ3VmX3NhbHRh
KGYsIGV0eXBlLCBwcm9mdW5kaWRhZCArIDEpCiAgICAgICAgICAgICAgICBjb250aW51ZQogICAg
ICAgICAgICBvdXQuYXBwZW5kKF9nZ3VmX3ZhbG9yKGYsIGV0eXBlLCBwcm9mdW5kaWRhZCArIDEp
KQogICAgICAgIHJldHVybiBvdXQKICAgIHJhaXNlIFZhbHVlRXJyb3IoInRpcG8gR0dVRiBkZXNj
b25vY2lkbzogJWQiICUgdnR5cGUpCgoKZGVmIF9nZ3VmX3NhbHRhKGYsIHZ0eXBlLCBwcm9mdW5k
aWRhZD0wKToKICAgIGlmIHZ0eXBlID09IDg6CiAgICAgICAgKG4sKSA9IHN0cnVjdC51bnBhY2so
IjxRIiwgZi5yZWFkKDgpKQogICAgICAgIGYuc2VlayhuLCAxKQogICAgICAgIHJldHVybgogICAg
aWYgdnR5cGUgaW4gX0dHVUZfRk1UOgogICAgICAgIGYuc2VlayhfR0dVRl9UQU1bdnR5cGVdLCAx
KQogICAgICAgIHJldHVybgogICAgaWYgdnR5cGUgPT0gNzoKICAgICAgICBmLnNlZWsoMSwgMSkK
ICAgICAgICByZXR1cm4KICAgIGlmIHZ0eXBlID09IDk6CiAgICAgICAgKGV0eXBlLCkgPSBzdHJ1
Y3QudW5wYWNrKCI8SSIsIGYucmVhZCg0KSkKICAgICAgICAobiwpID0gc3RydWN0LnVucGFjaygi
PFEiLCBmLnJlYWQoOCkpCiAgICAgICAgZm9yIF8gaW4gcmFuZ2Uobik6CiAgICAgICAgICAgIF9n
Z3VmX3NhbHRhKGYsIGV0eXBlLCBwcm9mdW5kaWRhZCArIDEpCiAgICAgICAgcmV0dXJuCiAgICBy
YWlzZSBWYWx1ZUVycm9yKCJ0aXBvIEdHVUYgZGVzY29ub2NpZG86ICVkIiAlIHZ0eXBlKQoKCmRl
ZiBnZ3VmX2xlZXJfaHBhcmFtcyhydXRhX21vZGVsbyk6CiAgICAiIiJMZWUgU09MTyBsYSByZWdp
b24gZGUgbWV0YWRhdGEgZGVsIEdHVUYgKHYyL3YzKTogZ2VuZXJhbC5hcmNoaXRlY3R1cmUsCiAg
ICBleHBlcnRfY291bnQgeSBleHBlcnRfdXNlZF9jb3VudCBkZWwgYXJjaC4gTm8gbGVlIHRlbnNv
cmVzIG5pIHRva2VuaXplcgogICAgY29tcGxldG8uIERldnVlbHZlIGRpY3QgY29uIGFyY2gsIG5f
ZXhwZXJ0LCBuX2V4cGVydF91c2VkLiIiIgogICAgZiA9IG9wZW4ocnV0YV9tb2RlbG8sICJyYiIs
IGJ1ZmZlcmluZz0xIDw8IDIwKQogICAgdHJ5OgogICAgICAgIG1hZ2ljID0gZi5yZWFkKDQpCiAg
ICAgICAgaWYgbWFnaWMgIT0gYiJHR1VGIjoKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigi
bm8gZXMgR0dVRiAobWFnaWM9JXIpIiAlIG1hZ2ljKQogICAgICAgICh2ZXJzaW9uLCkgPSBzdHJ1
Y3QudW5wYWNrKCI8SSIsIGYucmVhZCg0KSkKICAgICAgICBpZiB2ZXJzaW9uIDwgMjoKICAgICAg
ICAgICAgcmFpc2UgVmFsdWVFcnJvcigiR0dVRiB2JWQgbm8gc29wb3J0YWRvIHBvciBlc3RlIHBh
cnNlciIgJSB2ZXJzaW9uKQogICAgICAgICh0ZW5zb3JfY291bnQsKSA9IHN0cnVjdC51bnBhY2so
IjxRIiwgZi5yZWFkKDgpKQogICAgICAgIChrdl9jb3VudCwpID0gc3RydWN0LnVucGFjaygiPFEi
LCBmLnJlYWQoOCkpCgogICAgICAgICMgcGFzYWRhczogMSkgZ2VuZXJhbC5hcmNoaXRlY3R1cmUs
IDIpIGNsYXZlcyBkZWwgYXJjaCBjb25jcmV0bwogICAgICAgIHByaW1lcm8gPSB7fQogICAgICAg
IGZvciBfIGluIHJhbmdlKGt2X2NvdW50KToKICAgICAgICAgICAga2V5ID0gX2dndWZfc3RyaW5n
KGYpCiAgICAgICAgICAgICh2dHlwZSwpID0gc3RydWN0LnVucGFjaygiPEkiLCBmLnJlYWQoNCkp
CiAgICAgICAgICAgIHZhbCA9IF9nZ3VmX3ZhbG9yKGYsIHZ0eXBlKQogICAgICAgICAgICBwcmlt
ZXJvW2tleV0gPSB2YWwKICAgICAgICAgICAgaWYga2V5ID09ICJnZW5lcmFsLmFyY2hpdGVjdHVy
ZSI6CiAgICAgICAgICAgICAgICBicmVhawogICAgICAgIGFyY2ggPSBwcmltZXJvLmdldCgiZ2Vu
ZXJhbC5hcmNoaXRlY3R1cmUiKQogICAgICAgIGlmIG5vdCBhcmNoOgogICAgICAgICAgICByYWlz
ZSBWYWx1ZUVycm9yKCJlbCBHR1VGIG5vIHRyYWUgZ2VuZXJhbC5hcmNoaXRlY3R1cmUiKQoKICAg
ICAgICBidXNjYWRhcyA9IHthcmNoICsgIi5leHBlcnRfY291bnQiLCBhcmNoICsgIi5leHBlcnRf
dXNlZF9jb3VudCJ9CiAgICAgICAgZW5jb250cmFkbyA9IHt9CiAgICAgICAgaWYgc2V0KGJ1c2Nh
ZGFzKS5pc3N1YnNldChwcmltZXJvLmtleXMoKSk6CiAgICAgICAgICAgIGVuY29udHJhZG8gPSB7
azogcHJpbWVyb1trXSBmb3IgayBpbiBidXNjYWRhc30KICAgICAgICBlbHNlOgogICAgICAgICAg
ICBmLnNlZWsoMCkKICAgICAgICAgICAgZi5yZWFkKDQgKyA0ICsgOCArIDgpCiAgICAgICAgICAg
IGZvciBfIGluIHJhbmdlKGt2X2NvdW50KToKICAgICAgICAgICAgICAgIGtleSA9IF9nZ3VmX3N0
cmluZyhmKQogICAgICAgICAgICAgICAgKHZ0eXBlLCkgPSBzdHJ1Y3QudW5wYWNrKCI8SSIsIGYu
cmVhZCg0KSkKICAgICAgICAgICAgICAgIHZhbCA9IF9nZ3VmX3ZhbG9yKGYsIHZ0eXBlKQogICAg
ICAgICAgICAgICAgaWYga2V5IGluIGJ1c2NhZGFzOgogICAgICAgICAgICAgICAgICAgIGVuY29u
dHJhZG9ba2V5XSA9IHZhbAogICAgICAgICAgICAgICAgaWYgbGVuKGVuY29udHJhZG8pID09IGxl
bihidXNjYWRhcyk6CiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICByZXR1cm4gewog
ICAgICAgICAgICAiYXJjaCI6IGFyY2gsCiAgICAgICAgICAgICJnZ3VmX3ZlcnNpb24iOiB2ZXJz
aW9uLAogICAgICAgICAgICAidGVuc29yX2NvdW50IjogdGVuc29yX2NvdW50LAogICAgICAgICAg
ICAibl9leHBlcnQiOiBlbmNvbnRyYWRvLmdldChhcmNoICsgIi5leHBlcnRfY291bnQiKSwKICAg
ICAgICAgICAgIm5fZXhwZXJ0X3VzZWQiOiBlbmNvbnRyYWRvLmdldChhcmNoICsgIi5leHBlcnRf
dXNlZF9jb3VudCIpLAogICAgICAgIH0KICAgIGZpbmFsbHk6CiAgICAgICAgZi5jbG9zZSgpCgoK
IyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0gcHJvbXB0cyB5IGNvbmZpZ3MgZGUgbGEgZmFzZSBEIC0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tCiMgNCBwcm9tcHRzIERJU1RJTlRPUyBkZSBsYSBtaXNtYSBm
YW1pbGlhICh+bWlzbWEgbG9uZ2l0dWQpLiBDb24gY2FjaGVfcHJvbXB0CiMgbGEgcGFzYWRhIDEg
ZXMgcHJlZmlsbCBmcmlvIHJlYWw7IGxhcyBwYXNhZGFzIDItNCBubyByZXV0aWxpemFuIEtWIGVu
dHJlIHNpCiMgKHByZWZpam9zIGRpc3RpbnRvcykuIEFudGktaW5mbGFkbyBzcGVjIGhlcmVkYWRv
IGRlbCBiYXJyaWRvLTI1LzMwLgpQUk9NUFRTX01FRElDSU9OID0gWwogICAgIkRlc2NyaWJlIGVu
IHVuIHBhcnJhZm8gY29tbyBmdW5jaW9uYSB1bmEgYmljaWNsZXRhOiBwZWRhbGVzLCBjYWRlbmEg
eSAiCiAgICAicnVlZGFzLiBJbmNsdXllIHVuIGNvbnNlam8gYmFzaWNvIGRlIG1hbnRlbmltaWVu
dG8uIiwKICAgICJFeHBsaWNhIGVuIHVuIHBhcnJhZm8gcG9yIHF1ZSBlbCBjaWVsbyBlcyBhenVs
IGR1cmFudGUgZWwgZGlhIHkgcm9qbyBhbCAiCiAgICAiYXRhcmRlY2VyLCBjb24gcGFsYWJyYXMg
c2ltcGxlcy4iLAogICAgIlJlc3VtZSBlbiB1biBwYXJyYWZvIGxhIGhpc3RvcmlhIGRlIGxhIGlt
cHJlbnRhIGRlIEd1dGVuYmVyZyB5IHBvciBxdWUgIgogICAgImNhbWJpbyBlbCBtdW5kby4iLAog
ICAgIkV4cGxpY2EgZW4gdW4gcGFycmFmbyBxdWUgZXMgbGEgZm90b3NpbnRlc2lzOiBxdWUgZW50
cmEgZW4gbGEgaG9qYSwgcXVlICIKICAgICJzYWxlIHkgcG9yIHF1ZSBpbXBvcnRhLCBlbiBwYWxh
YnJhcyBzaW1wbGVzLiIsCl0KClNBTklUWV9QQVJFUyA9IFsKICAgICgiQ3VhbnRvIGVzIDE3IHgg
MjM/IFJlc3BvbmRlIHNvbG8gZWwgbnVtZXJvLiIsIFsiMzkxIl0pLAogICAgKCJRdWllbiBlc2Ny
aWJpbyBEb24gUXVpam90ZT8gUmVzcG9uZGUgbXV5IGNvcnRvLiIsIFsiY2VydmFudGVzIl0pLAog
ICAgKCJRdWUgcGxhbmV0YSBlcyBjb25vY2lkbyBjb21vIGVsIHBsYW5ldGEgcm9qbz8gUmVzcG9u
ZGUgbXV5IGNvcnRvLiIsCiAgICAgWyJtYXJ0ZSJdKSwKXQoKIyBFeHBlY3RhdGl2YXMgW1RdIGRl
bCBTUzUgZGVsIG5pdmVsLTEgKGJhbmRhIH4zMiBHQi9zKSBwYXJhIGVsIGluZm9ybWUKRVhQRUNU
X0VYUCA9IHsKICAgIDEwOiAoIkNPTlRST0w6IGRlYmVyaWEgRlJFTkFSIH4tNi41JSIsIDIxLjUz
ICogMC45MzUpLAogICAgODogKCJzYW5pdHkgPSBkZWZhdWx0IiwgMjEuNTMpLAogICAgNjogKCIr
OCUgZXNwZXJhZG8iLCAyMy4zKSwKICAgIDU6ICgiKzEyLjUlIGVzcGVyYWRvIiwgMjQuMiksCiAg
ICA0OiAoIisxNyUgZXNwZXJhZG8iLCAyNS4xKSwKICAgIDM6ICgiKzIyJSBlc3BlcmFkbzsgc2Fj
cmlmaWNpbyByZWFsIiwgMjYuNCksCiAgICAyOiAoIisyOCUgZXNwZXJhZG87IGNsaWZmIGRlIGNh
bGlkYWQiLCAyNy41KSwKfQoKCmRlZiBfb3ZleHAoYXJjaCwgbik6CiAgICAiIiJPdmVycmlkZSBy
dW50aW1lIGNvbiBsYSBjbGF2ZSBFWEFDVEEgbGVpZGEgZGVsIEdHVUYgKGNvcnJlY2Npb24gZGVs
CiAgICBuby1vcCBkZWwgYmFycmlkby0zMDogYXF1ZWxsYSB2ZXogc2UgdXNvIHF3ZW4zbW9lLiog
YSBjaWVnYXMpLiIiIgogICAgY2xhdmUgPSAiJXMuZXhwZXJ0X3VzZWRfY291bnQ9aW50OiVkIiAl
IChhcmNoLCBuKQogICAgcmV0dXJuIFsiLS1vdmVycmlkZS1rdiIsIGNsYXZlXSwgY2xhdmUKCgpk
ZWYgY29uc3RydWlyX2NvbmZpZ3MoYXJjaCwgYmxvcXVlPSIiLCBleHRyYV9rPSgpKToKICAgICIi
IkNvbnN0cnV5ZSBsYXMgY29uZmlncyBkZSBsYSBmYXNlIEQuIENhZGEgY29uZmlnID0gQkFTRSAr
IGZsYWdzIGRpZmYKICAgIChtaXNtbyBwYXRyb24gZGVsIGJhcnJpZG8tMzApLiBEZXZ1ZWx2ZSBs
aXN0YSBkZSBkaWN0cy4iIiIKICAgIGNvbmZpZ3MgPSBbXQoKICAgIGRlZiBhZGQoY2lkLCBmYW1p
bGlhLCBub21icmUsIGZsYWdzLCBoaXBvdGVzaXMpOgogICAgICAgIGNvbmZpZ3MuYXBwZW5kKHsi
aWQiOiBjaWQsICJmYW1pbGlhIjogZmFtaWxpYSwgIm5vbWJyZSI6IG5vbWJyZSwKICAgICAgICAg
ICAgICAgICAgICAgICAgImZsYWdzIjogZmxhZ3MsICJoaXBvdGVzaXMiOiBoaXBvdGVzaXN9KQoK
ICAgIGlmIGJsb3F1ZSBpbiAoIiIsICJleHAiKToKICAgICAgICBhZGQoMSwgIkFOQ0xBIiwgIkQt
QU5DTEEiLCBsaXN0KENNKSwKICAgICAgICAgICAgInJlLWFuY2xhIGRlIHNlc2lvbiAoYmFycmlk
by0zMDogMjEuNTMgW01dKTsgYmFzZWxpbmUgZGUgdG9kb3MgbG9zIGRlbHRhcyIpCiAgICAgICAg
YWRkKDIsICJFWFAiLCAiRC1FWFAxMC1DVFJMIiwgQ00gKyBfb3ZleHAoYXJjaCwgMTApWzBdLAog
ICAgICAgICAgICAiQ09OVFJPTCBhdXRlbnRpY2Fkb3I6ICsyNSUgYnl0ZXMgcm91dGVkIC0+IGRl
YmVyaWEgbWVkaXIgTUVOT1MgIgogICAgICAgICAgICAiKH4yMC4xKS4gU2kgbm8gZnJlbmEsIG92
ZXJyaWRlIHNvc3BlY2hvc28gKFNTNCkiKQogICAgICAgIGFkZCgzLCAiRVhQIiwgIkQtRVhQOCIs
IENNICsgX292ZXhwKGFyY2gsIDgpWzBdLAogICAgICAgICAgICAic2FuaXR5OiA9IGRlZmF1bHQg
KDgpLiBEZWJlIGNsYXZhcnNlIGNvbiBlbCBhbmNsYSB5IGxvZ2VhciAiCiAgICAgICAgICAgICJu
X2V4cGVydF91c2VkID0gOCAoU1MxMi4yKSIpCiAgICAgICAgYWRkKDQsICJFWFAiLCAiRC1FWFA2
IiwgQ00gKyBfb3ZleHAoYXJjaCwgNilbMF0sCiAgICAgICAgICAgICJlc2NhbGVyYSBTUzY6IH4r
OCUgW1RdLCBjYWxpZGFkIGRlc3ByZWNpYWJsZSBlbiBjaGF0IFtGXSIpCiAgICAgICAgYWRkKDUs
ICJFWFAiLCAiRC1FWFA1IiwgQ00gKyBfb3ZleHAoYXJjaCwgNSlbMF0sCiAgICAgICAgICAgICJl
c2NhbGVyYSBTUzU6IH4rMTIuNSUgW1RdLCBwdW50byBtZWRpbyIpCiAgICAgICAgYWRkKDYsICJF
WFAiLCAiRC1FWFA0IiwgQ00gKyBfb3ZleHAoYXJjaCwgNClbMF0sCiAgICAgICAgICAgICJlc2Nh
bGVyYSBTUzY6IH4rMTclIFtUXSwgfjk1LTk4JSBjYWxpZGFkIFtGIE1vRS1TcGVjXTsgdGVzdCBk
ZSAiCiAgICAgICAgICAgICJjb2hlcmVuY2lhIFNTMTEuNDogZGViZSBzdWJpciAxNS0xNyUiKQog
ICAgICAgIGFkZCg3LCAiRVhQIiwgIkQtRVhQMyIsIENNICsgX292ZXhwKGFyY2gsIDMpWzBdLAog
ICAgICAgICAgICAiZXNjYWxlcmEgU1M2OiB+KzIyJSBbVF07IHNhY3JpZmljaW8gcmVhbCAobWF0
aC9jb2RpZ28pIikKICAgICAgICBhZGQoOCwgIkVYUCIsICJELUVYUDIiLCBDTSArIF9vdmV4cChh
cmNoLCAyKVswXSwKICAgICAgICAgICAgImN1cmlvc2lkYWQgU1M2OiB+KzI4JSBbVF07IGNsaWZm
IGVzcGVyYWRvLCBzb2xvIGNvbiBjYWxpZGFkICIKICAgICAgICAgICAgInNhY3JpZmljYWJsZSIp
CiAgICAgICAgZm9yIGsgaW4gZXh0cmFfazoKICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAg
ICAga2sgPSBpbnQoaykKICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAg
ICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIGtrIGluICgxLCAyLCAzLCA0LCA1LCA2LCA3LCA4
LCA5LCAxMCwgMTIsIDE2KToKICAgICAgICAgICAgICAgIGFkZCg5MCArIGtrLCAiRVhQIiwgIkQt
RVhQJWQtRVhUIiAlIGtrLCBDTSArIF9vdmV4cChhcmNoLCBraylbMF0sCiAgICAgICAgICAgICAg
ICAgICAgImRvc2lzIGV4dHJhIHBlZGlkYSBwb3IgQ0xJICgtLWV4dHJhLWspIikKCiAgICBpZiBi
bG9xdWUgaW4gKCIiLCAidWIxayIpOgogICAgICAgIGFkZCg5LCAiVUIxSyIsICJELUVYUDQtVUIx
SyIsIENNICsgVUIxSyArIF9vdmV4cChhcmNoLCA0KVswXSwKICAgICAgICAgICAgInN0YWNrIFNT
Ni40OiBnYW5hZG9yIGNhbmRpZGF0byBFWFA0IGFwaWxhZG8gY29uIE9STy1VQjFLICIKICAgICAg
ICAgICAgIihwcmVmaWxsICsyNi41JSB5YSBtZWRpZG8pOyBzaW4gY29uZmxpY3RvIGRlIGZsYWdz
IFtNXSIpCgogICAgaWYgYmxvcXVlIGluICgiIiwgIm1lYyIpOgogICAgICAgIGFkZCgxMCwgIk1F
QyIsICJELU5DTTM3QzQtTUVDMCIsIGxpc3QoTkNNMzdDNCkgKyBbIi0tbW9lLWNhY2hlLW1pYiIs
ICIwIl0sCiAgICAgICAgICAgICJDT05UUk9MIE1FQyAoPSBOQ00zN0M0IGRlbCBiYXJyaWRvLTMw
LCAyMi40OSBbTV0pIGNvbiBjYWNoZSAiCiAgICAgICAgICAgICJleHBsaWNpdGFtZW50ZSBhIDA7
IG9ibGlnYXRvcmlvIHBhcmEgY2FkYSBBL0IgZGUgTUVDIChTUzE1KSIpCiAgICAgICAgYWRkKDEx
LCAiTUVDIiwgIkQtTUVDLTUxMiIsIGxpc3QoTkNNMzdDNCkgKyBbIi0tbW9lLWNhY2hlLW1pYiIs
ICI1MTIiXSwKICAgICAgICAgICAgImNhY2hlIGRlIGV4cGVydG9zIGNhbGllbnRlcyBlbiBWUkFN
IChTUzE0KTogKzM0Li42MCUgZW4gR1BVcyBhamVuYXM7ICIKICAgICAgICAgICAgImVuIGVzdGUg
cmlnIEdPL05PLUdPIHZzIGNvbnRyb2w7IGFwcmVuZGlkbyBTUzIgeWEgdmV0byAyNTYvNTEyIGVu
IGxhICIKICAgICAgICAgICAgImJhc2UgdmllamEgLT4gYXF1aSBzZSBtaWRlIHNvYnJlIE5DTTM3
QzQgY29uIGNvbnRyb2wgZW4gc2VzaW9uIChTUzE1KSIpCiAgICAgICAgYWRkKDEyLCAiTUVDIiwg
IkQtTUVDLTEwMjQiLCBsaXN0KE5DTTM3QzQpICsgWyItLW1vZS1jYWNoZS1taWIiLCAiMTAyNCJd
LAogICAgICAgICAgICAiZG9zaXMgZmluYSBTUzE1IChvcmRlbiBmaW5hbDogMCAtPiA1MTIgLT4g
MTAyNCAtPiA3NjgpOyBzaSBwaWVyZGUgIgogICAgICAgICAgICAidnMgY29udHJvbCwgc2UgZGVz
Y2FydGEiKQogICAgICAgIGFkZCgxMywgIk1FQyIsICJELU1FQy03NjgiLCBsaXN0KE5DTTM3QzQp
ICsgWyItLW1vZS1jYWNoZS1taWIiLCAiNzY4Il0sCiAgICAgICAgICAgICJkb3NpcyBmaW5hIFNT
MTUgKHRlcmNlcmEgZW4gb3JkZW4pOyBzaSBwaWVyZGUgdnMgY29udHJvbCwgc2UgZGVzY2FydGEi
KQoKICAgIGlmIGJsb3F1ZSBpbiAoIiIsICJjb21ibyIpOgogICAgICAgIGFkZCgxNCwgIkNPTUJP
IiwgIkQtRVhQNC1OQ00zN0M0IiwgbGlzdChOQ00zN0M0KSArIF9vdmV4cChhcmNoLCA0KVswXSwK
ICAgICAgICAgICAgInN0YWNrIFNTODogRVhQNCB4IE5DTTM3QzQgKGVsIGNvbXB1ZXN0byBkZWwg
b2JqZXRpdm8gKzUwJSkiKQoKICAgIGlmIGJsb3F1ZSBpbiAoIiIsICJvdCIpOgogICAgICAgIGFk
ZCgxNSwgIk9UIiwgIkQtT1QtQ1RSTCIsCiAgICAgICAgICAgIFsiLWMiLCAiNDA5NiIsICItY3Rr
IiwgInE0XzAiLCAiLWN0diIsICJxNF8wIiwKICAgICAgICAgICAgICItb3QiLCBPVF9FUVVJVkFM
RU5URSwgIi0tbW9lLWNhY2hlLW1pYiIsICIwIl0sCiAgICAgICAgICAgICJydW4gYXV0ZW50aWNh
ZG9yIGNydXphZG8gU1MxODogLW90IHJlcGxpY2EgbGEgZXN0cnVjdHVyYSBkZSAiCiAgICAgICAg
ICAgICJOQ00zN0M0ICgzNyBjYXBhcyBNb0UgZW4gQ1BVLCB1bHRpbWFzIDMgZW4gR1BVOyBzaGFy
ZWQvYXRlbi8iCiAgICAgICAgICAgICJLViBlbiBHUFUgcG9ycXVlICdleHBzJyBubyBtYXRjaGVh
ICdzaGV4cCcpIFNJTiAtbmNtb2UgeSBjb24gIgogICAgICAgICAgICAiVU5BIHNvbGEgZmxhZyBk
ZSBsaXN0YSBwb3IgY29tYXM7IGRlYmUgY2xhdmFyIGVsIGNvbnRyb2wgIgogICAgICAgICAgICAi
RC1OQ00zN0M0LU1FQzAgKGhpc3QuIDIyLjQ5IFtNXSk7IHNpIHNlIGRlc3ZpYSwgYnVnIGRlICIK
ICAgICAgICAgICAgImNvbXByZW5zaW9uIGRlbCBrbm9iIEFOVEVTIGRlIHNlZ3VpciBiYXJyaWVu
ZG8iKQoKICAgIGlmIGJsb3F1ZSBpbiAoIiIsICJjb21ibzIiKToKICAgICAgICAjIHYxLjIuMTog
ZWwgc3RhY2sgZmluYWwgb2JqZXRpdm8gPSBjb21wb3NpY2lvbiBkZSBsb3MgZG9zIEdPIGRlIGxh
CiAgICAgICAgIyBwcmltZXJhIGNvcnJpZGEgcmVhbCAob3ZlcnJpZGUgKyBNRUMgc29icmUgTkNN
MzdDNCkuIEVsIGFyYm9sCiAgICAgICAgIyBTUzExLjQgY2FzbyAxIHBpZGUgYXBpbGFyIGxhcyBk
b3NpcyB2aXZhczsgc2luIE1FQyBlbiBlbCBzdGFjawogICAgICAgICMgbnVuY2Egc2UgaGFiaWEg
bWVkaWRvIGVsIGNvbXB1ZXN0byBjb21wbGV0by4KICAgICAgICBhZGQoMTcsICJDT01CTzIiLCAi
RC1FWFA0LU5DTS1NRUM3NjgiLAogICAgICAgICAgICBsaXN0KE5DTTM3QzQpICsgWyItLW1vZS1j
YWNoZS1taWIiLCAiNzY4Il0gKyBfb3ZleHAoYXJjaCwgNClbMF0sCiAgICAgICAgICAgICJzdGFj
ayBmaW5hbCBvYmpldGl2bzogRVhQNCB4IE5DTTM3QzQgeCBNRUMtNzY4IChNRUMgZ2FubyArMzAu
NyUgIgogICAgICAgICAgICAidnMgY29udHJvbCBlbiBsYSBjb3JyaWRhIHJlYWwpOyBlbCBjb21w
dWVzdG8gZGUgbG9zIGRvcyBHTyIpCiAgICAgICAgYWRkKDE4LCAiQ09NQk8yIiwgIkQtRVhQNC1O
Q00tTUVDMTAyNCIsCiAgICAgICAgICAgIGxpc3QoTkNNMzdDNCkgKyBbIi0tbW9lLWNhY2hlLW1p
YiIsICIxMDI0Il0gKyBfb3ZleHAoYXJjaCwgNClbMF0sCiAgICAgICAgICAgICJzdGFjayBmaW5h
bCBvYmpldGl2byBjb24gTUVDLTEwMjQgKCszOC4wJSBlbiBsYSBjb3JyaWRhIHJlYWwsICIKICAg
ICAgICAgICAgInBlcm8gVlJBTSBhbCBib3JkZSBkZWwgZ3VhcmRhcnJhaWwgMzcwMCBNaUI7IGNv
biBFWFA0IGxvcyAiCiAgICAgICAgICAgICJpbnRlcm1lZGlvcyBNb0UgYmFqYW4geSBwdWVkZSBj
YWJlcikiKQoKICAgIGlmIGJsb3F1ZSBpbiAoIiIsICJhbmNsYWZpbiIpOgogICAgICAgICMgdjEu
Mi4xOiBib29rZW5kIGRlbCBzZXNnbyBkZSBhcnJhbnF1ZS4gTGEgY29ycmlkYSByZWFsIG1vc3Ry
byBsYQogICAgICAgICMgMWEgY29uZmlnIGRlIGxhIHNlc2lvbiBzaXN0ZW1hdGljYW1lbnRlIGxl
bnRhIChFWFA4IGs9ZGVmYXVsdAogICAgICAgICMgbWlkaW8gKzE1LjIlIHNvYnJlIGVsIGFuY2xh
KTogcmUtbWVkaXIgZWwgYW5jbGEgQUwgQ0lFUlJFIG1pZGUgZWwKICAgICAgICAjIGRyaWZ0IGRl
IHNlc2lvbiB5IHNhbmVhIGxhIGxlY3R1cmEgZGUgdG9kb3MgbG9zIGRlbHRhcy4KICAgICAgICBh
ZGQoMTYsICJBTkNMQS1GSU4iLCAiRC1BTkNMQS1GSU4iLCBsaXN0KENNKSwKICAgICAgICAgICAg
ImJvb2tlbmQ6IHJlLWFuY2xhIGFsIGNpZXJyZTsgfGZpbi1pbmljaW98ID4gcnVpZG8gPSBsYSBz
ZXNpb24gIgogICAgICAgICAgICAiZGVyaXZvIHkgbG9zIGRlbHRhcyB2cyBhbmNsYSBkZSBpbmlj
aW8gc2UgbGVlbiBjb24gY3VpZGFkbyIpCgogICAgcmV0dXJuIGNvbmZpZ3MKCgpCTE9RVUVTX0RF
ID0geyJleHAiOiBbMSwgMiwgMywgNCwgNSwgNiwgNywgOF0sCiAgICAgICAgICAgICAgInViMWsi
OiBbOV0sICJtZWMiOiBbMTAsIDExLCAxMiwgMTNdLCAiY29tYm8iOiBbMTRdLAogICAgICAgICAg
ICAgICJjb21ibzIiOiBbMTcsIDE4XSwgIm90IjogWzE1XSwgImFuY2xhZmluIjogWzE2XX0KUVVJ
Q0tfSURTID0gWzEsIDIsIDMsIDQsIDYsIDEwLCAxMV0KCgpkZWYgZmlsdHJhcl9jb25maWdzKGNv
bmZpZ3MsIHNvbG89Tm9uZSwgcXVpY2s9RmFsc2UpOgogICAgaWYgcXVpY2s6CiAgICAgICAgcmV0
dXJuIFtjIGZvciBjIGluIGNvbmZpZ3MgaWYgY1siaWQiXSBpbiBRVUlDS19JRFNdCiAgICBpZiBz
b2xvOgogICAgICAgIHBlZGlkb3MgPSBbcy5zdHJpcCgpIGZvciBzIGluIHNvbG8uc3BsaXQoIiwi
KSBpZiBzLnN0cmlwKCldCiAgICAgICAgaWRzID0gW10KICAgICAgICBmb3IgcCBpbiBwZWRpZG9z
OgogICAgICAgICAgICBpZiBwIG5vdCBpbiBCTE9RVUVTX0RFOgogICAgICAgICAgICAgICAgcmFp
c2UgU3lzdGVtRXhpdChyZWQoIi0tc29sbyBibG9xdWUgZGVzY29ub2NpZG86ICVzICh2YWxpZG9z
OiAlcykiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAlIChwLCAiLCIuam9p
bihzb3J0ZWQoQkxPUVVFU19ERSkpKSkpCiAgICAgICAgICAgIGlkcy5leHRlbmQoQkxPUVVFU19E
RVtwXSkKICAgICAgICByZXR1cm4gW2MgZm9yIGMgaW4gY29uZmlncyBpZiBjWyJpZCJdIGluIGlk
c10KICAgIHJldHVybiBjb25maWdzCgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0gY29u
dHJvbCBkZWwgc2VydmVyIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCmRlZiBoZWFsdGhf
b2socHVlcnRvLCB0aW1lb3V0PTIpOgogICAgdHJ5OgogICAgICAgIHIgPSB1cmxsaWIucmVxdWVz
dC51cmxvcGVuKAogICAgICAgICAgICAiaHR0cDovLyVzOiVkL2hlYWx0aCIgJSAoSE9TVF9ERUYs
IHB1ZXJ0byksIHRpbWVvdXQ9dGltZW91dCkKICAgICAgICByZXR1cm4gci5nZXRjb2RlKCkgPT0g
MjAwCiAgICBleGNlcHQgdXJsbGliLmVycm9yLkhUVFBFcnJvcjoKICAgICAgICByZXR1cm4gRmFs
c2UKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcmV0dXJuIEZhbHNlCgoKZGVmIHByb3Bz
X2V4cGVydF91c2VkKHB1ZXJ0bywgdGltZW91dD04KToKICAgICIiInYxLjIuMSAoMmEgdmlhIGRl
IGF1dGVudGljYWNpb24pOiBHRVQgL3Byb3BzIHkgYnVzY2EgZWwgaHBhcmFtCiAgICBleHBlcnRf
dXNlZF9jb3VudCAvIG5fZXhwZXJ0X3VzZWQgZW4gZWwgSlNPTi4gRGV2dWVsdmUgaW50IG8gTm9u
ZTsKICAgIGN1YWxxdWllciBmYWxsbyAoNDA0LCB0aW1lb3V0LCBKU09OIHJhcm8pID0gTm9uZSB5
IE5VTkNBIGVzIGZhdGFsLgogICAgT0pPOiBzb2xvIHNlIHVzYSBwYXJhIENPTkZJUk1BUiAodmFs
b3IgPT0gcGVkaWRhKTogc2kgL3Byb3BzIHJlZmxlamFyYQogICAgZWwgR0dVRiBjcnVkbyBlbiB2
ZXogZGVsIGhwYXJhbSB0cmFzIG92ZXJyaWRlLCB1biAnbm8gY29pbmNpZGUnIE5PCiAgICBwcnVl
YmEgdW4gbm8tb3AgKHBvciBlc28gdW4gZGVzYWN1ZXJkbyBlcyBJTkNPTkNMVVNPLCBubyBpbnZh
bGlkbykuIiIiCiAgICB0cnk6CiAgICAgICAgcmVxID0gdXJsbGliLnJlcXVlc3QuUmVxdWVzdCgK
ICAgICAgICAgICAgImh0dHA6Ly8lczolZC9wcm9wcyIgJSAoSE9TVF9ERUYsIHB1ZXJ0bykpCiAg
ICAgICAgd2l0aCB1cmxsaWIucmVxdWVzdC51cmxvcGVuKHJlcSwgdGltZW91dD10aW1lb3V0KSBh
cyByOgogICAgICAgICAgICB0eHQgPSByLnJlYWQoKS5kZWNvZGUoInV0Zi04IiwgZXJyb3JzPSJy
ZXBsYWNlIikKICAgICAgICBtID0gcmUuc2VhcmNoKHInIj8oW1x3Ll0qXC4/KT9leHBlcnRfdXNl
ZF9jb3VudCI/XHMqOlxzKihcZCspJywgdHh0KQogICAgICAgIGlmIG5vdCBtOgogICAgICAgICAg
ICBtID0gcmUuc2VhcmNoKHInIm5fZXhwZXJ0X3VzZWQiXHMqOlxzKihcZCspJywgdHh0KQogICAg
ICAgIHJldHVybiBpbnQobS5ncm91cCgyKSBpZiBtLmxhc3RpbmRleCBhbmQgbS5sYXN0aW5kZXgg
Pj0gMgogICAgICAgICAgICAgICAgICAgZWxzZSBtLmdyb3VwKDEpKSBpZiBtIGVsc2UgTm9uZQog
ICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICByZXR1cm4gTm9uZQoKCmRlZiBhdXRlbnRpY2Fy
X2NvbXBvcnRhbWVudGFsKGssIGRlY29kZSwgcHJldik6CiAgICAiIiJ2MS4yLjEgKDNhIHZpYSk6
IGN1YW5kbyBlbCBsb2cgeSAvcHJvcHMgY2FsbGFuIChiMTE4NTYgbm8gaW1wcmltZQogICAgaHBh
cmFtcyBhIHZlcmJvc2lkYWQgMyksIGxhIENVUlZBIGRlIHNlc2lvbiBlcyBsYSBmaXJtYSBkZWwg
b3ZlcnJpZGU6CiAgICBsYSBkb3NpcyBkZWJlIHJlc3BvbmRlciBtYXMgYWxsYSBkZWwgcnVpZG8g
ZGVjbGFyYWRvIChTUzg6ICsvLTAuMy0wLjUpLgogICAgUmVmZXJlbmNpYSBrPTggPSBtYXgoYW5j
bGEgaWQxLCBFWFA4IGlkMyk6IGNvbnNlcnZhZG9yIGFudGUgdW4gYW5jbGEKICAgIGRlcHJpbWlk
YSBwb3IgZWwgc2VzZ28gZGUgYXJyYW5xdWUgKGNvcnJpZGEgcmVhbDogRVhQOCArMTUuMiUgc29i
cmUgZWwKICAgIGFuY2xhKS4gaz04IGVzIHZhY3VvIChuby1vcCBwb3IgZGlzZW5vKS4gRGV2dWVs
dmUgVHJ1ZS9GYWxzZS9Ob25lCiAgICAoTm9uZSA9IHNpbiByZWZlcmVuY2lhcyBwYXJhIGRlY2lk
aXIpLiIiIgogICAgaWYgbm90IGRlY29kZSBvciBrID09IDg6CiAgICAgICAgcmV0dXJuIE5vbmUK
ICAgIHJlZnMgPSBbXQogICAgZm9yIGNpZCBpbiAoMSwgMyk6CiAgICAgICAgciA9IChwcmV2IG9y
IHt9KS5nZXQoY2lkKQogICAgICAgIHRyeToKICAgICAgICAgICAgdiA9IGZsb2F0KHIuZ2V0KCJk
ZWNvZGVfdHMiKSkgaWYgciBlbHNlIE5vbmUKICAgICAgICBleGNlcHQgKFR5cGVFcnJvciwgVmFs
dWVFcnJvcik6CiAgICAgICAgICAgIHYgPSBOb25lCiAgICAgICAgaWYgdjoKICAgICAgICAgICAg
cmVmcy5hcHBlbmQodikKICAgIGlmIG5vdCByZWZzOgogICAgICAgIHJldHVybiBOb25lCiAgICBy
ZWYgPSBtYXgocmVmcykKICAgIGlmIGsgPCA4OgogICAgICAgIHJldHVybiBkZWNvZGUgPiByZWYg
KyBURUNIT19SVUlETwogICAgcmV0dXJuIGRlY29kZSA8IHJlZiAtIFRFQ0hPX1JVSURPCgoKZGVm
IHZlcnNpb25fc2VydmVyKHJ1dGFfc2VydmVyKToKICAgIHRyeToKICAgICAgICBvdXQgPSBzdWJw
cm9jZXNzLnJ1bihbcnV0YV9zZXJ2ZXIsICItLXZlcnNpb24iXSwgY2FwdHVyZV9vdXRwdXQ9VHJ1
ZSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICB0aW1lb3V0PTMwKQogICAgICAgIHR4dCA9
ICgob3V0LnN0ZG91dCBvciBiIiIpICsgKG91dC5zdGRlcnIgb3IgYiIiKSkuZGVjb2RlKAogICAg
ICAgICAgICAidXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiKQogICAgICAgIHJldHVybiAiICIuam9p
bih0eHQuc3BsaXQoKSkKICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICByZXR1cm4g
Ik4vRCAoJXMpIiAlIGUKCgpkZWYgbWF0YXJfc2VydmVyX3Zpdm8ocHVlcnRvKToKICAgIGlmIGhl
YWx0aF9vayhwdWVydG8pOgogICAgICAgIHByaW50KHllbGxvdygiICBzZXJ2ZXIgdml2byBlbiBl
bCBwdWVydG8gJWQgLT4gdGFza2tpbGwgbGxhbWEtc2VydmVyLmV4ZSIgJSBwdWVydG8pKQogICAg
ICAgIHRyeToKICAgICAgICAgICAgc3VicHJvY2Vzcy5ydW4oWyJ0YXNra2lsbCIsICIvRiIsICIv
SU0iLCAibGxhbWEtc2VydmVyLmV4ZSJdLAogICAgICAgICAgICAgICAgICAgICAgICAgICBjYXB0
dXJlX291dHB1dD1UcnVlKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAg
ICAgcHJpbnQoeWVsbG93KCIgIHRhc2traWxsIG5vIGRpc3BvbmlibGUgYXF1aSAoJXMpOyBjZXJy
YXIgYSBtYW5vIiAlIGUpKQogICAgICAgIHRpbWUuc2xlZXAoMykKICAgICAgICBpZiBoZWFsdGhf
b2socHVlcnRvKToKICAgICAgICAgICAgcmFpc2UgU3lzdGVtRXhpdChyZWQoIkZBVEFMOiBlbCBw
dWVydG8gJWQgc2lndWUgcmVzcG9uZGllbmRvIHRyYXMgIgogICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAidGFza2tpbGwuIENlcnJhciBhIG1hbm8geSByZWludGVudGFyLiIgJSBwdWVy
dG8pKQoKCmRlZiBsYW56YXJfc2VydmVyKHJ1dGFfc2VydmVyLCBmbGFncywgbG9nX3BhdGgsIGNh
cmdhX3RpbWVvdXQpOgogICAgIiIiTGFuemEgbGxhbWEtc2VydmVyIGNvbiBsb3MgZmxhZ3MgRVhB
Q1RPUzsgc3Rkb3V0K3N0ZGVyciBhbCBsb2cuIiIiCiAgICBsb2dmID0gb3Blbihsb2dfcGF0aCwg
IndiIikKICAgIHByb2MgPSBzdWJwcm9jZXNzLlBvcGVuKFtydXRhX3NlcnZlcl0gKyBmbGFncywg
c3Rkb3V0PWxvZ2YsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBzdGRlcnI9c3VicHJvY2Vz
cy5TVERPVVQsIHN0ZGluPXN1YnByb2Nlc3MuREVWTlVMTCkKICAgIHQwID0gdGltZS50aW1lKCkK
ICAgIHdoaWxlIHRpbWUudGltZSgpIC0gdDAgPCBjYXJnYV90aW1lb3V0OgogICAgICAgIGlmIHBy
b2MucG9sbCgpIGlzIG5vdCBOb25lOgogICAgICAgICAgICBsb2dmLmNsb3NlKCkKICAgICAgICAg
ICAgcmV0dXJuIE5vbmUsIHRpbWUudGltZSgpIC0gdDAsICgiZWwgc2VydmVyIG11cmlvIGR1cmFu
dGUgbGEgIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJjYXJn
YSAoZXhpdCAlcykiICUgcHJvYy5yZXR1cm5jb2RlKQogICAgICAgIGlmIGhlYWx0aF9vayhQVUVS
VE9fREVGLCB0aW1lb3V0PTEuNSk6CiAgICAgICAgICAgIGxvZ2YuY2xvc2UoKQogICAgICAgICAg
ICByZXR1cm4gcHJvYywgdGltZS50aW1lKCkgLSB0MCwgIm9rIgogICAgICAgIHRpbWUuc2xlZXAo
MS4wKQogICAgdHJ5OgogICAgICAgIHByb2MudGVybWluYXRlKCkKICAgICAgICBwcm9jLndhaXQo
dGltZW91dD0xMCkKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgdHJ5OgogICAgICAgICAg
ICBwcm9jLmtpbGwoKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgIHBhc3MK
ICAgIGxvZ2YuY2xvc2UoKQogICAgcmV0dXJuIE5vbmUsIHRpbWUudGltZSgpIC0gdDAsICJ0aW1l
b3V0IGRlIGNhcmdhICglZCBzKSIgJSBjYXJnYV90aW1lb3V0CgoKZGVmIGFwYWdhcl9zZXJ2ZXIo
cHJvYyk6CiAgICB0cnk6CiAgICAgICAgcHJvYy50ZXJtaW5hdGUoKQogICAgICAgIHByb2Mud2Fp
dCh0aW1lb3V0PTE1KQogICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICB0cnk6CiAgICAgICAg
ICAgIHByb2Mua2lsbCgpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgcGFz
cwogICAgdGltZS5zbGVlcCgyKQoKCmRlZiBjb2xhX2xvZyhsb2dfcGF0aCwgbj0xMik6CiAgICAi
IiJVbHRpbWFzIGxpbmVhcyBkZWwgbG9nIGRlbCBzZXJ2ZXIgKGRpYWdub3N0aWNvIHJhcGlkbyBk
ZSBmYWxsb3MpLiIiIgogICAgdHJ5OgogICAgICAgIGxpbmVhcyA9IG9wZW4obG9nX3BhdGgsICJy
YiIpLnJlYWQoKS5kZWNvZGUoCiAgICAgICAgICAgICJ1dGYtOCIsIGVycm9ycz0icmVwbGFjZSIp
LnNwbGl0bGluZXMoKQogICAgICAgIHZpdmFzID0gW2wuc3RyaXAoKSBmb3IgbCBpbiBsaW5lYXMg
aWYgbC5zdHJpcCgpXQogICAgICAgIHJldHVybiAiIHwgIi5qb2luKHZpdmFzWy1uOl0pWzo3MDBd
CiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHJldHVybiAiKGxvZyBubyBkaXNwb25pYmxl
KSIKCgpkZWYgbGVlcl9sb2dfc2VydmVyKGxvZ19wYXRoLCBtb2RlbG9fYmFzZW5hbWU9Tm9uZSwg
cHVlcnRvPU5vbmUpOgogICAgdHJ5OgogICAgICAgIHR4dCA9IG9wZW4obG9nX3BhdGgsICJyYiIp
LnJlYWQoKS5kZWNvZGUoInV0Zi04IiwgZXJyb3JzPSJyZXBsYWNlIikKICAgIGV4Y2VwdCBFeGNl
cHRpb246CiAgICAgICAgcmV0dXJuIHt9CiAgICBkYXRvcyA9IHt9CiAgICBtID0gcmUuc2VhcmNo
KHIiKD86bGxtX2xvYWRfcHJpbnRfbWV0YXxwcmludF9pbmZvKTpccypnZW5lcmFsXC5hcmNoaXRl
Y3R1cmUiCiAgICAgICAgICAgICAgICAgIHIiXHMqPVxzKihcUyspIiwgdHh0KQogICAgaWYgbm90
IG06CiAgICAgICAgbSA9IHJlLnNlYXJjaChyImFyY2hccyo9XHMqKHF3ZW5cdyopIiwgdHh0KQog
ICAgZGF0b3NbImFyY2hfbG9nIl0gPSBtLmdyb3VwKDEpIGlmIG0gZWxzZSBOb25lCiAgICAjIHYx
LjIuMTogdmFyaWFudGVzIGFtcGxpYWRhcy4gYjExODU2IGEgdmVyYm9zaWRhZCAzIE5PIGltcHJp
bWUgaHBhcmFtcwogICAgIyAoY29ycmlkYSByZWFsOiBjZXJvIGxpbmVhcyk7IGNvbiAtbHYgNCBl
bCBidWlsZCBwdWVkZSBpbXByaW1pcmxvcyBjb24KICAgICMgY3VhbHF1aWVyIHByZWZpam8gKHBy
aW50X2luZm8sIG1vZGVsIG1ldGEsIGxsYW1hLmNvbnRleHQuLi4pLiBMYSBmb3JtYQogICAgIyAi
aW50Ok4iIGRlbCBlY28gZGVsIG92ZXJyaWRlIE5PIG1hdGNoZWEgKGVzIGV4cGVydF91c2VkX2Nv
dW50LCBvdHJvCiAgICAjIG5vbWJyZTsgeSAnaW50OicgaW1waWRlIChcZCspIGlubWVkaWF0byku
CiAgICBtID0gcmUuc2VhcmNoKHIiKD86bGxtX2xvYWRfcHJpbnRfbWV0YXxwcmludF9pbmZvKTpc
cypuX2V4cGVydFxzKj1ccyooXGQrKSIsIHR4dCkKICAgIGlmIG5vdCBtOgogICAgICAgIG0gPSBy
ZS5zZWFyY2gociJcYm5fZXhwZXJ0XHMqWzo9XVxzKihcZCspIiwgdHh0KQogICAgZGF0b3NbIm5f
ZXhwZXJ0X2xvZyJdID0gaW50KG0uZ3JvdXAoMSkpIGlmIG0gZWxzZSBOb25lCiAgICBtID0gcmUu
c2VhcmNoKHIiKD86bGxtX2xvYWRfcHJpbnRfbWV0YXxwcmludF9pbmZvKTpccypuX2V4cGVydF91
c2VkXHMqPVxzKihcZCspIiwKICAgICAgICAgICAgICAgICAgdHh0KQogICAgaWYgbm90IG06CiAg
ICAgICAgbSA9IHJlLnNlYXJjaChyIlxibl9leHBlcnRfdXNlZFxzKls6PV1ccyooXGQrKSIsIHR4
dCkKICAgIGRhdG9zWyJuX2V4cGVydF91c2VkX2xvZyJdID0gaW50KG0uZ3JvdXAoMSkpIGlmIG0g
ZWxzZSBOb25lCiAgICBtID0gcmUuc2VhcmNoKHIiQ1VEQTAgY29tcHV0ZSBidWZmZXIgc2l6ZVxz
KjpccyooW1xkLl0rKVxzKihbTUtHXSlpQiIsIHR4dCkKICAgIGlmIG06CiAgICAgICAgZmFjdG9y
ID0geyJNIjogMS4wLCAiSyI6IDEuMCAvIDEwMjQuMCwgIkciOiAxMDI0LjB9W20uZ3JvdXAoMild
CiAgICAgICAgZGF0b3NbImJ1ZmZlcl9taWIiXSA9IHJvdW5kKGZsb2F0KG0uZ3JvdXAoMSkpICog
ZmFjdG9yLCAxKQogICAgZWxzZToKICAgICAgICBkYXRvc1siYnVmZmVyX21pYiJdID0gTm9uZQog
ICAgIyB2MS4yLjE6ICJmYWlsZWQgdG8gZml0IHBhcmFtcyIgTk8gZXMgc2llbXByZSB1biBmYWxs
by4gTGEgbGluZWEKICAgICMgYGNvbW1vbl9maXRfcGFyYW1zOiBmYWlsZWQgdG8gZml0IHBhcmFt
cyB0byBmcmVlIGRldmljZSBtZW1vcnk6CiAgICAjIG5fZ3B1X2xheWVycyBhbHJlYWR5IHNldCBi
eSB1c2VyIHRvIDk5LCBhYm9ydGAgZXMgZWwgQVVUTy1GSVQKICAgICMgREVDTElOQU5ETyBBQ1RV
QVIgcG9ycXVlIGVsIHVzdWFyaW8geWEgZmlqbyAtbmdsOiBiZW5pZ25vIHkgZXNwZXJhZG8KICAg
ICMgZW4gdG9kYXMgZXN0YXMgY29uZmlncyAobGEgY29ycmlkYSByZWFsIGxvIG1vc3RybyBlbiBs
YXMgNiBkZSBsYQogICAgIyBmYW1pbGlhIE5DTS9NRUMvT1QgeSBsYSB2MS4yIGxhcyBpbnZhbGlk
byBlbiBmYWxzbykuIFNvbG8gaW52YWxpZGFuCiAgICAjIHVuIGZpdCBwb3IgT1RSQSBjYXVzYSBv
IHVuIGZhaWxlZCB0byBhbGxvY2F0ZSAoVlJBTSBkZSB2ZXJkYWQpLgogICAgZGF0b3NbImZpdF9h
Ym9ydCJdID0gRmFsc2UKICAgIGRhdG9zWyJmaXRfaW5mbyJdID0gIiIKICAgIG1maXQgPSByZS5z
ZWFyY2gociJmYWlsZWQgdG8gZml0IHBhcmFtc1teXHJcbl0qIiwgdHh0KQogICAgaWYgbWZpdDoK
ICAgICAgICBpZiAiYWxyZWFkeSBzZXQgYnkgdXNlciIgaW4gbWZpdC5ncm91cCgwKToKICAgICAg
ICAgICAgZGF0b3NbImZpdF9pbmZvIl0gPSAoImF1dG8tZml0IGRlY2xpbm8gKG5nbCB5YSBmaWph
ZG8gcG9yICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgInVzdWFyaW87IGVzcGVy
YWRvLCBiZW5pZ25vKSIpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgZGF0b3NbImZpdF9hYm9y
dCJdID0gVHJ1ZQogICAgaWYgImZhaWxlZCB0byBhbGxvY2F0ZSIgaW4gdHh0OgogICAgICAgIGRh
dG9zWyJmaXRfYWJvcnQiXSA9IFRydWUKICAgIGRhdG9zWyJzeXNtZW1fd2FybiJdID0gKCJzeXNt
ZW0gZmFsbGJhY2siIGluIHR4dC5sb3dlcigpCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBv
ciAic2hhcmVkIG1lbW9yeSIgaW4gdHh0Lmxvd2VyKCkpCiAgICBpZiBkYXRvcy5nZXQoIm5fZXhw
ZXJ0X3VzZWRfbG9nIikgaXMgbm90IE5vbmUgYW5kICJuX2V4cGVydF91c2VkIiBpbiB0eHQ6CiAg
ICAgICAgZGF0b3NbIm92ZXJyaWRlX2FwbGljYWRvIl0gPSBUcnVlCiAgICBlbHNlOgogICAgICAg
IGRhdG9zWyJvdmVycmlkZV9hcGxpY2FkbyJdID0gRmFsc2UKICAgICMgaWRlbnRpZGFkICh2MS4x
KTogZWwgbG9nIGRlYmUgUFJPQkFSIHF1ZSBlc3RlIHNlcnZlciBjYXJnYSBOVUVTVFJPCiAgICAj
IG1vZGVsbzsgc2kgbm8sIG90cm8gcHJvY2VzbyAod2F0Y2hkb2cvcHJveHkvc2VydmVyIHZpZWpv
KSBvY3VwYSBlbAogICAgIyBwdWVydG8geSBtZWRpcmxvIGZhbHNlYXJpYSB0b2RvIHNpbiBydWlk
byBuaW5ndW5vLgogICAgaWYgbW9kZWxvX2Jhc2VuYW1lIGlzIG5vdCBOb25lOgogICAgICAgIGRh
dG9zWyJtb2RlbG9fZW5fbG9nIl0gPSBtb2RlbG9fYmFzZW5hbWUubG93ZXIoKSBpbiB0eHQubG93
ZXIoKQogICAgaWYgcHVlcnRvIGlzIG5vdCBOb25lOgogICAgICAgIGRhdG9zWyJwdWVydG9fZW5f
bG9nIl0gPSAoImxpc3RlbmluZyBvbiIgaW4gdHh0CiAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICBhbmQgKCI6JWQiICUgcHVlcnRvKSBpbiB0eHQpCiAgICByZXR1cm4gZGF0b3MKCgpk
ZWYgdnJhbV9udmlkaWEoKToKICAgIHRyeToKICAgICAgICBvdXQgPSBzdWJwcm9jZXNzLnJ1bigK
ICAgICAgICAgICAgWyJudmlkaWEtc21pIiwgIi0tcXVlcnktZ3B1PW1lbW9yeS51c2VkLG1lbW9y
eS50b3RhbCIsCiAgICAgICAgICAgICAiLS1mb3JtYXQ9Y3N2LG5vaGVhZGVyLG5vdW5pdHMiXSwK
ICAgICAgICAgICAgY2FwdHVyZV9vdXRwdXQ9VHJ1ZSwgdGltZW91dD0xNSkKICAgICAgICBsaW5l
YSA9IG91dC5zdGRvdXQuZGVjb2RlKCJ1dGYtOCIsIGVycm9ycz0icmVwbGFjZSIpLnN0cmlwKCku
c3BsaXRsaW5lcygpCiAgICAgICAgaWYgbm90IGxpbmVhOgogICAgICAgICAgICByZXR1cm4gTm9u
ZQogICAgICAgIHVzYWRhLCB0b3RhbCA9IGxpbmVhWzBdLnNwbGl0KCIsIilbOjJdCiAgICAgICAg
cmV0dXJuIGludCh1c2FkYS5zdHJpcCgpKSwgaW50KHRvdGFsLnN0cmlwKCkpCiAgICBleGNlcHQg
RXhjZXB0aW9uOgogICAgICAgIHJldHVybiBOb25lCgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0gbWVkaWNpb24gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCmNs
YXNzIE1lYXNFcnJvcihSdW50aW1lRXJyb3IpOgogICAgIiIiRmFsbG8gZGUgbWVkaWNpb24gY29u
IGRpYWdub3N0aWNvIChIVFRQIDR4eC81eHgsIHNlcnZlciBtdWVydG8uLi4pLiIiIgoKCmRlZiBf
cG9zdF9qc29uKHVybCwgY3VlcnBvLCB0aW1lb3V0LCBwcm9jPU5vbmUsIHJlaW50ZW50b3M9Mik6
CiAgICAiIiJQT1NUIGFwcGxpY2F0aW9uL2pzb24uIHYxLjE6IGNhcHR1cmEgZWwgQ1VFUlBPIGRl
IGN1YWxxdWllciBlcnJvcgogICAgSFRUUCAoZWwgNDAwIGRlIGxhIHYxLjAgcXVlZG8gc2luIGRp
YWdub3N0aWNvIHBvcnF1ZSBzZSBkZXNjYXJ0YWJhKSB5CiAgICByZWludGVudGEgU09MTyBmYWxs
b3MgdHJhbnNpdG9yaW9zICg1eHgvNDI5L2NvbmV4aW9uKS4gTG9zIDR4eCBzb24KICAgIHJlY2hh
em9zIGRlbCBwZWRpZG86IGZhbGxhbiBkZSBpbm1lZGlhdG8gQ09OIGVsIG1lbnNhamUgZGVsIHNl
cnZlci4iIiIKICAgIGRhdG9zID0gY3VlcnBvIGlmIGlzaW5zdGFuY2UoY3VlcnBvLCBieXRlcykg
ZWxzZSBcCiAgICAgICAganNvbi5kdW1wcyhjdWVycG8pLmVuY29kZSgidXRmLTgiKQogICAgdWx0
aW1vID0gTm9uZQogICAgZm9yIGludGVudG8gaW4gcmFuZ2UocmVpbnRlbnRvcyArIDEpOgogICAg
ICAgIGlmIHByb2MgaXMgbm90IE5vbmUgYW5kIHByb2MucG9sbCgpIGlzIG5vdCBOb25lOgogICAg
ICAgICAgICByYWlzZSBNZWFzRXJyb3IoImVsIHNlcnZlciBtdXJpbyBhIG1pdGFkIGRlIGxhIG1l
ZGljaW9uICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICIoZXhpdCBjb2RlICVzKSIgJSBw
cm9jLnJldHVybmNvZGUpCiAgICAgICAgcmVxID0gdXJsbGliLnJlcXVlc3QuUmVxdWVzdCh1cmws
IGRhdGE9ZGF0b3MsIG1ldGhvZD0iUE9TVCIsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICBoZWFkZXJzPXsiQ29udGVudC1UeXBlIjogImFwcGxpY2F0aW9uL2pzb24ifSkKICAg
ICAgICB0cnk6CiAgICAgICAgICAgIHdpdGggdXJsbGliLnJlcXVlc3QudXJsb3BlbihyZXEsIHRp
bWVvdXQ9dGltZW91dCkgYXMgcjoKICAgICAgICAgICAgICAgIHJldHVybiBqc29uLmxvYWRzKHIu
cmVhZCgpLmRlY29kZSgidXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiKSkKICAgICAgICBleGNlcHQg
dXJsbGliLmVycm9yLkhUVFBFcnJvciBhcyBlOgogICAgICAgICAgICBkZXRhbGxlID0gIiIKICAg
ICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgZGV0YWxsZSA9IGUucmVhZCgpLmRlY29kZSgi
dXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiKVs6NDAwXQogICAgICAgICAgICBleGNlcHQgRXhjZXB0
aW9uOgogICAgICAgICAgICAgICAgcGFzcwogICAgICAgICAgICB1bHRpbW8gPSBNZWFzRXJyb3Io
IkhUVFAgJWQgZW4gJXMgLT4gJXMiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAlIChl
LmNvZGUsIHVybCwgZGV0YWxsZSBvciAiKHNpbiBjdWVycG8pIikpCiAgICAgICAgICAgIGlmIDQw
MCA8PSBlLmNvZGUgPCA1MDAgYW5kIGUuY29kZSAhPSA0Mjk6CiAgICAgICAgICAgICAgICByYWlz
ZSB1bHRpbW8KICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgIHVsdGlt
byA9IE1lYXNFcnJvcigiY29uZXhpb24gZmFsbG8gZW4gJXM6ICVyIiAlICh1cmwsIGUpKQogICAg
ICAgIGlmIGludGVudG8gPCByZWludGVudG9zOgogICAgICAgICAgICB0aW1lLnNsZWVwKDgpCiAg
ICByYWlzZSB1bHRpbW8KCgpkZWYgcGFzYWRhc19tZWRpY2lvbihwdWVydG8sIHByb21wdHMsIG5f
cHJlZGljdD0yNTYsIHNlZWQ9NDI0MjQyLCB0aW1lb3V0PTYwMCwKICAgICAgICAgICAgICAgICAg
ICAgcHJvYz1Ob25lKToKICAgICIiIjQgcGFzYWRhcyB4IG5fcHJlZGljdCB0b2tlbnMuIERldnVl
bHZlIChwcmVmaWxsX3RzLCBbZGVjIHIxLi5yNF0sCiAgICBkZXRhbGxlcykuIFByZWZpbGwgPSBw
YXNhZGEgMSBmcmlhIChwcm9tcHRfcGVyX3NlY29uZCk7IGRlY29kZSA9IG1lZGlhCiAgICAyLTQg
ZGUgcHJlZGljdGVkX3Blcl9zZWNvbmQgKHByb3RvY29sbyBhcHJlbmRpZG8gU1M4KS4gcHJvYyBz
ZSB2aWdpbGE6CiAgICBzaSBlbCBzZXJ2ZXIgbXVlcmUgYSBtaXRhZCwgTWVhc0Vycm9yIChubyB1
biB0aW1lb3V0IGNpZWdvKS4iIiIKICAgIHVybCA9ICJodHRwOi8vJXM6JWQvY29tcGxldGlvbiIg
JSAoSE9TVF9ERUYsIHB1ZXJ0bykKICAgIHByZWZpbGwgPSBOb25lCiAgICBkZWNzID0gW10KICAg
IGRldGFsbGUgPSBbXQogICAgZm9yIGksIHAgaW4gZW51bWVyYXRlKHByb21wdHMpOgogICAgICAg
IGN1ZXJwbyA9IHsKICAgICAgICAgICAgInByb21wdCI6IHAsICJuX3ByZWRpY3QiOiBuX3ByZWRp
Y3QsICJ0ZW1wZXJhdHVyZSI6IDAuMCwKICAgICAgICAgICAgInNlZWQiOiBzZWVkLCAiY2FjaGVf
cHJvbXB0IjogVHJ1ZSwgImlnbm9yZV9lb3MiOiBUcnVlLAogICAgICAgICAgICAic3RyZWFtIjog
RmFsc2UsCiAgICAgICAgfQogICAgICAgIHQwID0gdGltZS50aW1lKCkKICAgICAgICBkID0gX3Bv
c3RfanNvbih1cmwsIGN1ZXJwbywgdGltZW91dD10aW1lb3V0LCBwcm9jPXByb2MpCiAgICAgICAg
dCA9IGQuZ2V0KCJ0aW1pbmdzIiwge30pIG9yIHt9CiAgICAgICAgcGYgPSB0LmdldCgicHJvbXB0
X3Blcl9zZWNvbmQiKQogICAgICAgIGRlYyA9IHQuZ2V0KCJwcmVkaWN0ZWRfcGVyX3NlY29uZCIp
CiAgICAgICAgcG4gPSB0LmdldCgicHJlZGljdGVkX24iKQogICAgICAgIGRldGFsbGUuYXBwZW5k
KHsicGFzYWRhIjogaSArIDEsICJwcm9tcHRfcGVyX3NlY29uZCI6IHBmLAogICAgICAgICAgICAg
ICAgICAgICAgICAicHJlZGljdGVkX3Blcl9zZWNvbmQiOiBkZWMsICJwcmVkaWN0ZWRfbiI6IHBu
LAogICAgICAgICAgICAgICAgICAgICAgICAic193YWxsIjogcm91bmQodGltZS50aW1lKCkgLSB0
MCwgMSl9KQogICAgICAgIGlmIGkgPT0gMDoKICAgICAgICAgICAgcHJlZmlsbCA9IHBmCiAgICAg
ICAgZWxzZToKICAgICAgICAgICAgZGVjcy5hcHBlbmQoZGVjKQogICAgcmV0dXJuIHByZWZpbGws
IGRlY3MsIGRldGFsbGUKCgpkZWYgc2FuaXR5X2NoYXQocHVlcnRvLCBuX3ByZWRpY3Q9MTI4LCBz
ZWVkPTQyNDI0MiwgdGltZW91dD0xODApOgogICAgIiIidjEuMi4xOiBuX3ByZWRpY3QgNDggLT4g
MTI4IHkgVFJFUyBlc3RhZG9zIHBvciBwYXI6IE9LIChwYWxhYnJhCiAgICBlc3BlcmFkYSksIFRS
VU5DQURPIChsYSByZXNwdWVzdGEgcXVlZG8gZGVudHJvIGRlIHVuIDx0aGluaz4gc2luCiAgICBj
ZXJyYXI6IGFydGVmYWN0byBkZWwgcHJvYmUsIE5PIGVzIGZhbGxvIGRlIGNhbGlkYWQ7IGxhIGNv
cnJpZGEgcmVhbAogICAgInJvYm8iIGEgaz01LzYgcG9yIGVzdG8pIHkgRkFMTE8gcmVhbCAocmVz
cHVlc3RhIHRlcm1pbmFkYSBzaW4gbGEKICAgIHBhbGFicmEgZXNwZXJhZGE6IGs9MyByZWFsIGZh
bGxvIDQzMSAhPSAzOTEpLiBEZXZ1ZWx2ZQogICAgKG9rX24sIHRydW5jX24sIHRvdGFsLCBkZXRh
bGxlKS4iIiIKICAgIHVybCA9ICJodHRwOi8vJXM6JWQvY29tcGxldGlvbiIgJSAoSE9TVF9ERUYs
IHB1ZXJ0bykKICAgIG9rX24gPSAwCiAgICB0cnVuY19uID0gMAogICAgZGV0YWxsZSA9IFtdCiAg
ICBmb3IgcHJlZ3VudGEsIGVzcGVyYWRvcyBpbiBTQU5JVFlfUEFSRVM6CiAgICAgICAgY3VlcnBv
ID0gewogICAgICAgICAgICAicHJvbXB0IjogcHJlZ3VudGEsICJuX3ByZWRpY3QiOiBuX3ByZWRp
Y3QsICJ0ZW1wZXJhdHVyZSI6IDAuMCwKICAgICAgICAgICAgInNlZWQiOiBzZWVkLCAiY2FjaGVf
cHJvbXB0IjogRmFsc2UsICJzdHJlYW0iOiBGYWxzZSwKICAgICAgICB9CiAgICAgICAgdHJ5Ogog
ICAgICAgICAgICBkID0gX3Bvc3RfanNvbih1cmwsIGN1ZXJwbywgdGltZW91dD10aW1lb3V0LCBy
ZWludGVudG9zPTApCiAgICAgICAgICAgIHR4dCA9IChkLmdldCgiY29udGVudCIpIG9yICIiKQog
ICAgICAgIGV4Y2VwdCBNZWFzRXJyb3IgYXMgZToKICAgICAgICAgICAgdHh0ID0gIkVSUk9SOiAl
cyIgJSBlCiAgICAgICAgbG93ID0gdHh0Lmxvd2VyKCkKICAgICAgICBoaXQgPSBhbnkoZS5sb3dl
cigpIGluIGxvdyBmb3IgZSBpbiBlc3BlcmFkb3MpCiAgICAgICAgdHJ1bmMgPSAobm90IGhpdCBh
bmQgIjx0aGluaz4iIGluIGxvdwogICAgICAgICAgICAgICAgIGFuZCAiPC90aGluaz4iIG5vdCBp
biBsb3cgYW5kIG5vdCBsb3cuc3RhcnRzd2l0aCgiZXJyb3I6IikpCiAgICAgICAgaWYgaGl0Ogog
ICAgICAgICAgICBva19uICs9IDEKICAgICAgICBlbGlmIHRydW5jOgogICAgICAgICAgICB0cnVu
Y19uICs9IDEKICAgICAgICBkZXRhbGxlLmFwcGVuZCh7InByZWd1bnRhIjogcHJlZ3VudGEsICJl
c3BlcmFkbyI6IGVzcGVyYWRvcywKICAgICAgICAgICAgICAgICAgICAgICAgIm9rIjogaGl0LCAi
dHJ1bmNhZG8iOiB0cnVuYywgInJlc3B1ZXN0YSI6IHR4dFs6MTYwXX0pCiAgICAgICAgaWYgdHh0
LnN0YXJ0c3dpdGgoIkVSUk9SOiIpOgogICAgICAgICAgICBicmVhayAgIyBzZXJ2ZXIgY2FpZG86
IGxhcyByZXN0YW50ZXMgZmFsbGFyYW4gaWd1YWwgKHYxLjEpCiAgICByZXR1cm4gb2tfbiwgdHJ1
bmNfbiwgbGVuKFNBTklUWV9QQVJFUyksIGRldGFsbGUKCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0gQ1NWIC8gcmVzdW1lIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0K
Q09MVU1OQVMgPSBbInByb3RvIiwgImlkIiwgIm5vbWJyZSIsICJmYW1pbGlhIiwgImZlY2hhX2hv
cmEiLCAiZmxhZ3MiLAogICAgICAgICAgICAibG9hZF9zIiwgInZhbGlkbyIsICJub3RhIiwgInBy
ZWZpbGxfdHMiLAogICAgICAgICAgICAiZGVjX3IyIiwgImRlY19yMyIsICJkZWNfcjQiLCAiZGVj
b2RlX3RzIiwKICAgICAgICAgICAgIm92ZXJyaWRlX3BlZGlkYSIsICJuX2V4cGVydF91c2VkX2xv
ZyIsICJvdmVycmlkZV9hcGxpY2FkbyIsCiAgICAgICAgICAgICJhcmNoX2dndWYiLCAiYXJjaF9s
b2ciLCAibl9leHBlcnRfbG9nIiwgImJ1ZmZlcl9taWIiLAogICAgICAgICAgICAidnJhbV91c2Fk
YV9taWIiLCAidnJhbV90b3RhbF9taWIiLAogICAgICAgICAgICAic2FuaXR5X29rX24iLCAic2Fu
aXR5X3RvdGFsIiwgImRlbHRhX3ZzX2FuY2xhX3BjdCIsCiAgICAgICAgICAgICJhdXRoX3ZpYSIs
ICJzYW5pdHlfdHJ1bmNfbiIsICJkaXNwZXJzX21heF9taW4iXQoKCmRlZiBjc3ZfcnV0YShkaXJf
bG9ncyk6CiAgICByZXR1cm4gb3MucGF0aC5qb2luKGRpcl9sb2dzLCAiZmFzZUQtTjEtcmVzdWx0
YWRvcy5jc3YiKQoKCmRlZiBjc3ZfcHJvdG9fZGUocnV0YV9jc3YpOgogICAgIiIiUHJvdG8gZGUg
bGEgcHJpbWVyYSBmaWxhIGRlIGRhdG9zIGRlIHVuIENTViBleGlzdGVudGUgKCcnIHNpIG5vIGhh
eSkuIiIiCiAgICB0cnk6CiAgICAgICAgd2l0aCBvcGVuKHJ1dGFfY3N2LCAiciIsIG5ld2xpbmU9
IiIsIGVuY29kaW5nPSJ1dGYtOCIpIGFzIGY6CiAgICAgICAgICAgIGZvciByb3cgaW4gY3N2LkRp
Y3RSZWFkZXIoZik6CiAgICAgICAgICAgICAgICByZXR1cm4gcm93LmdldCgicHJvdG8iKSBvciAi
IgogICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICBwYXNzCiAgICByZXR1cm4gIiIKCgpkZWYg
Y3N2X2Nhcmdhcl9oZWNob3MocnV0YV9jc3YpOgogICAgIiIiRGljdCBpZC0+ZmlsYSBkZSBjb3Jy
aWRhcyBwcmV2aWFzIHZhbGlkYXMgKG1pc21vIHByb3RvKS4gdjEuMTogc29sbwogICAgbGFzIGZp
bGFzIFNJIGN1ZW50YW4gY29tbyBoZWNoYXM7IHVuYSBjb25maWcgcXVlIGZhbGxvIHNlIHJlLW1p
ZGUuIiIiCiAgICBoZWNob3MgPSB7fQogICAgaWYgbm90IG9zLnBhdGguZXhpc3RzKHJ1dGFfY3N2
KToKICAgICAgICByZXR1cm4gaGVjaG9zCiAgICB0cnk6CiAgICAgICAgd2l0aCBvcGVuKHJ1dGFf
Y3N2LCAiciIsIG5ld2xpbmU9IiIsIGVuY29kaW5nPSJ1dGYtOCIpIGFzIGY6CiAgICAgICAgICAg
IGZvciByb3cgaW4gY3N2LkRpY3RSZWFkZXIoZik6CiAgICAgICAgICAgICAgICBpZiByb3cuZ2V0
KCJwcm90byIpID09IFBST1RPIGFuZCByb3cuZ2V0KCJ2YWxpZG8iKSA9PSAiU0kiOgogICAgICAg
ICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICAgICAgaGVjaG9zW2ludChyb3db
ImlkIl0pXSA9IHJvdwogICAgICAgICAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAg
ICAgICAgICAgICAgICAgICAgIHBhc3MKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcGFz
cwogICAgcmV0dXJuIGhlY2hvcwoKCmRlZiBjc3ZfYXBwZW5kKHJ1dGFfY3N2LCBmaWxhKToKICAg
IG51ZXZvID0gbm90IG9zLnBhdGguZXhpc3RzKHJ1dGFfY3N2KQogICAgd2l0aCBvcGVuKHJ1dGFf
Y3N2LCAiYSIsIG5ld2xpbmU9IiIsIGVuY29kaW5nPSJ1dGYtOCIpIGFzIGY6CiAgICAgICAgdyA9
IGNzdi5EaWN0V3JpdGVyKGYsIGZpZWxkbmFtZXM9Q09MVU1OQVMpCiAgICAgICAgaWYgbnVldm86
CiAgICAgICAgICAgIHcud3JpdGVoZWFkZXIoKQogICAgICAgIHcud3JpdGVyb3coZmlsYSkKCgoj
IC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBlamVjdWNpb24gZGUgdW5hIGNvbmZpZyAtLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0KZGVmIG1lZGlyX2NvbmZpZyhjZmcsIGNvbnRleHRvLCByZXN1
bHRhZG9zX3ByZXY9Tm9uZSk6CiAgICAiIiJDb3JyZSBVTkEgY29uZmlnIGNvbXBsZXRhOiBzZXJ2
ZXIgdXAgLT4gNCBwYXNhZGFzIC0+IHNhbml0eSAtPiBkb3duLgogICAgRGV2dWVsdmUgZGljdCBm
aWxhIENTViArIGRhdG9zIGNvbXBsZXRvcy4gcmVzdWx0YWRvc19wcmV2ID0gZmlsYXMgeWEKICAg
IG1lZGlkYXMgZGUgbGEgc2VzaW9uIChwYXJhIGxhIGF1dGVudGljYWNpb24gY29tcG9ydGFtZW50
YWwpLiIiIgogICAgZGlyX2xvZ3MgPSBjb250ZXh0b1siZGlyX2xvZ3MiXQogICAgbG9nX3BhdGgg
PSBvcy5wYXRoLmpvaW4oZGlyX2xvZ3MsICJsb2dzLWNvbmZpZyIsCiAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAiJTAyZC0lcy5sb2ciICUgKGNmZ1siaWQiXSwgY2ZnWyJub21icmUiXSkpCiAg
ICBmaWxhID0ge2M6ICIiIGZvciBjIGluIENPTFVNTkFTfQogICAgZmlsYS51cGRhdGUoeyJwcm90
byI6IFBST1RPLCAiaWQiOiBjZmdbImlkIl0sICJub21icmUiOiBjZmdbIm5vbWJyZSJdLAogICAg
ICAgICAgICAgICAgICJmYW1pbGlhIjogY2ZnWyJmYW1pbGlhIl0sICJmZWNoYV9ob3JhIjogYWhv
cmEoKSwKICAgICAgICAgICAgICAgICAiZmxhZ3MiOiAiICIuam9pbihjZmdbImZsYWdzIl0pfSkK
ICAgIGNvbXBsZXRvID0geyJpZCI6IGNmZ1siaWQiXSwgIm5vbWJyZSI6IGNmZ1sibm9tYnJlIl0s
CiAgICAgICAgICAgICAgICAiZmFtaWxpYSI6IGNmZ1siZmFtaWxpYSJdLCAiZmxhZ3MiOiBjZmdb
ImZsYWdzIl0sCiAgICAgICAgICAgICAgICAiaGlwb3Rlc2lzIjogY2ZnWyJoaXBvdGVzaXMiXSwg
ImxvZyI6IGxvZ19wYXRofQoKICAgICMgdjEuMTogZWwgY29tYW5kbyBsYW56YWRvIGVzIFNJRU1Q
UkUgYmFzZSArIGRpZmYgKGVsIHVsdGltbyB2YWxvciBnYW5hCiAgICAjIGVuIGxsYW1hLmNwcCku
IExhIHYxLjAgbGFuemFiYSBTT0xPIGVsIGRpZmY6IEQtQU5DTEEgcXVlZGFiYSBjb21vCiAgICAj
IGBsbGFtYS1zZXJ2ZXIuZXhlIC1jbW9lYCAoc2luIC1tLCBzaW4gLS1wb3J0LCBzaW4gLWMuLi4p
OiBhaGkgbmFjaW8KICAgICMgZWwgSFRUUCA0MDAgZGUgbGEgcHJpbWVyYSBjb3JyaWRhIHJlYWwu
CiAgICBmbGFnc19mdWxsID0gbGlzdChjb250ZXh0by5nZXQoImJhc2VfZmxhZ3MiKSBvciBbXSkg
KyBsaXN0KGNmZ1siZmxhZ3MiXSkKICAgIGZpbGFbImZsYWdzIl0gPSAiICIuam9pbihmbGFnc19m
dWxsKQogICAgY29tcGxldG9bImZsYWdzIl0gPSBmbGFnc19mdWxsCgogICAgcHJpbnQoY3lhbigi
ICBbJTAyZF0gJXM6IGxhbnphbmRvIHNlcnZlci4uLiIgJSAoY2ZnWyJpZCJdLCBjZmdbIm5vbWJy
ZSJdKSkpCiAgICBwcm9jLCBsb2FkX3MsIGVzdGFkbyA9IGxhbnphcl9zZXJ2ZXIoY29udGV4dG9b
InJ1dGFfc2VydmVyIl0sIGZsYWdzX2Z1bGwsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgbG9nX3BhdGgsIGNvbnRleHRvWyJjYXJnYV90aW1lb3V0Il0pCiAgICBmaWxh
WyJsb2FkX3MiXSA9ICIlLjFmIiAlIGxvYWRfcyBpZiBsb2FkX3MgZWxzZSAiIgogICAgY29tcGxl
dG9bImxvYWRfcyJdID0gcm91bmQobG9hZF9zLCAxKSBpZiBsb2FkX3MgZWxzZSBOb25lCiAgICBp
ZiBwcm9jIGlzIE5vbmU6CiAgICAgICAgZmlsYVsidmFsaWRvIl0gPSAiTk8iCiAgICAgICAgZmls
YVsibm90YSJdID0gImNhcmdhIGZhbGxpZGE6ICVzIiAlIGVzdGFkbwogICAgICAgIGxvZ190eHQg
PSBsZWVyX2xvZ19zZXJ2ZXIobG9nX3BhdGgpCiAgICAgICAgaWYgbG9nX3R4dC5nZXQoImZpdF9h
Ym9ydCIpOgogICAgICAgICAgICBmaWxhWyJub3RhIl0gKz0gIiAoZml0IGFib3J0YWRvOiBWUkFN
IGluc3VmaWNpZW50ZSBwYXJhIGVzdGEgY29uZmlnKSIKICAgICAgICBwcmludChyZWQoIiAgICBG
QUlMIGNhcmdhICglcykiICUgZmlsYVsibm90YSJdKSkKICAgICAgICBwcmludChyZWQoIiAgICBj
b2xhIGRlbCBsb2c6ICVzIiAlIGNvbGFfbG9nKGxvZ19wYXRoKSkpCiAgICAgICAgY29tcGxldG8u
dXBkYXRlKHsidmFsaWRvIjogRmFsc2UsICJub3RhIjogZmlsYVsibm90YSJdLAogICAgICAgICAg
ICAgICAgICAgICAgICAgImxvZ19kYXRvcyI6IGxvZ190eHQsICJsb2dfY29sYSI6IGNvbGFfbG9n
KGxvZ19wYXRoKX0pCiAgICAgICAgcmV0dXJuIGZpbGEsIGNvbXBsZXRvCgogICAgdHJ5OgogICAg
ICAgIGxvZ190eHQgPSBsZWVyX2xvZ19zZXJ2ZXIobG9nX3BhdGgsCiAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICBtb2RlbG9fYmFzZW5hbWU9b3MucGF0aC5iYXNlbmFtZSgKICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBjb250ZXh0by5nZXQoInJ1dGFfbW9kZWxv
Iikgb3IgIiIpLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgcHVlcnRvPWNvbnRl
eHRvLmdldCgicHVlcnRvIiwgUFVFUlRPX0RFRikpCiAgICAgICAgIyAtLS0tIGlkZW50aWRhZCBk
ZWwgc2VydmVyICh2MS4xKTogbnVuY2EgbWVkaXIgdW4gZmFudGFzbWEgLS0tLQogICAgICAgIGlm
IGxvZ190eHQuZ2V0KCJtb2RlbG9fZW5fbG9nIikgaXMgRmFsc2U6CiAgICAgICAgICAgIGZpbGFb
InZhbGlkbyJdID0gIk5PIgogICAgICAgICAgICBmaWxhWyJub3RhIl0gPSAoImVsIGxvZyBkZWwg
c2VydmVyIE5PIG1lbmNpb25hIGVsIG1vZGVsbyBlc3BlcmFkbyAiCiAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAiKCVzKTogb3RybyBwcm9jZXNvIG9jdXBhIGVsIHB1ZXJ0byAlcyBvIGVsICIK
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICJhcnJhbnF1ZSBmdWUgcmVlbXBsYXphZG8iCiAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAlIChjb250ZXh0by5nZXQoInJ1dGFfbW9kZWxvIiks
CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBjb250ZXh0by5nZXQoInB1ZXJ0byIsIFBV
RVJUT19ERUYpKSkKICAgICAgICAgICAgcHJpbnQocmVkKCIgICAgRkFJTCBpZGVudGlkYWQ6ICVz
IiAlIGZpbGFbIm5vdGEiXSkpCiAgICAgICAgICAgIHByaW50KHJlZCgiICAgIGNvbGEgZGVsIGxv
ZzogJXMiICUgY29sYV9sb2cobG9nX3BhdGgpKSkKICAgICAgICAgICAgY29tcGxldG8udXBkYXRl
KHsidmFsaWRvIjogRmFsc2UsICJub3RhIjogZmlsYVsibm90YSJdLAogICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICJsb2dfZGF0b3MiOiBsb2dfdHh0LAogICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICJsb2dfY29sYSI6IGNvbGFfbG9nKGxvZ19wYXRoKX0pCiAgICAgICAgICAgIHJldHVy
biBmaWxhLCBjb21wbGV0bwogICAgICAgIGlmIGxvZ190eHQuZ2V0KCJwdWVydG9fZW5fbG9nIikg
aXMgRmFsc2U6CiAgICAgICAgICAgIHByaW50KHllbGxvdygiICAgIEFWSVNPOiBlbCBsb2cgbm8g
Y29uZmlybWEgJ2xpc3RlbmluZyBvbicgZW4gZWwgIgogICAgICAgICAgICAgICAgICAgICAgICAg
InB1ZXJ0byAlcyAoc2UgY29udGludWEsIHBlcm8gcmV2aXNhcikiCiAgICAgICAgICAgICAgICAg
ICAgICAgICAlIGNvbnRleHRvLmdldCgicHVlcnRvIiwgUFVFUlRPX0RFRikpKQogICAgICAgIG92
ZXJyaWRlX3BlZGlkYSA9IE5vbmUKICAgICAgICBmbCA9IGNmZ1siZmxhZ3MiXQogICAgICAgIGZv
ciBpLCB0b2sgaW4gZW51bWVyYXRlKGZsKToKICAgICAgICAgICAgaWYgdG9rID09ICItLW92ZXJy
aWRlLWt2IiBhbmQgaSArIDEgPCBsZW4oZmwpOgogICAgICAgICAgICAgICAgbSA9IHJlLnNlYXJj
aChyImV4cGVydF91c2VkX2NvdW50PWludDooXGQrKSIsIGZsW2kgKyAxXSkKICAgICAgICAgICAg
ICAgIGlmIG06CiAgICAgICAgICAgICAgICAgICAgb3ZlcnJpZGVfcGVkaWRhID0gaW50KG0uZ3Jv
dXAoMSkpCiAgICAgICAgZmlsYVsib3ZlcnJpZGVfcGVkaWRhIl0gPSBzdHIob3ZlcnJpZGVfcGVk
aWRhKSBpZiBvdmVycmlkZV9wZWRpZGEgZWxzZSAiIgogICAgICAgICMgLS0tLSB2MS4yLjE6IEFV
VEVOVElDQUNJT04gRU4gNCBWSUFTIChTUzEyLjIpIC0tLS0KICAgICAgICAjIGIxMTg1NiBhIHZl
cmJvc2lkYWQgMyBOTyBpbXByaW1lIGhwYXJhbXM6IGxhIHYxLjIgaW52YWxpZG8gZW4KICAgICAg
ICAjIGZhbHNvIDEwIHJ1bnMgZGUgb3ZlcnJpZGUgKGxhIGVzY2FsZXJhIHJlYWwgZGVtb3N0cm8g
cXVlIGVsCiAgICAgICAgIyBvdmVycmlkZSBTSSBhcGxpY28pLiBPcmRlbjogTE9HIC0+IFBST1BT
IC0+IENPTVAgLT4gREVGQVVMVC4KICAgICAgICBhcGxpY2FkbyA9IE5vbmUgICAgICAgICAgICAj
IFRydWUvRmFsc2UvTm9uZSg9c2luIGRhdG8gZGUgdmlhIDEtMikKICAgICAgICBhdXRoX3ZpYSA9
ICIiCiAgICAgICAgcHJvcHNfayA9IE5vbmUKICAgICAgICBpZiBvdmVycmlkZV9wZWRpZGEgaXMg
bm90IE5vbmU6CiAgICAgICAgICAgIG51X2xvZyA9IGxvZ190eHQuZ2V0KCJuX2V4cGVydF91c2Vk
X2xvZyIpCiAgICAgICAgICAgIGlmIG51X2xvZyBpcyBub3QgTm9uZToKICAgICAgICAgICAgICAg
IGFwbGljYWRvID0gKG51X2xvZyA9PSBvdmVycmlkZV9wZWRpZGEpCiAgICAgICAgICAgICAgICBh
dXRoX3ZpYSA9ICJMT0ciCiAgICAgICAgICAgIGlmIGFwbGljYWRvIGlzIE5vbmU6CiAgICAgICAg
ICAgICAgICBwcm9wc19rID0gcHJvcHNfZXhwZXJ0X3VzZWQoY29udGV4dG8uZ2V0KCJwdWVydG8i
LCBQVUVSVE9fREVGKSkKICAgICAgICAgICAgICAgIGlmIHByb3BzX2sgPT0gb3ZlcnJpZGVfcGVk
aWRhOgogICAgICAgICAgICAgICAgICAgIGFwbGljYWRvID0gVHJ1ZQogICAgICAgICAgICAgICAg
ICAgIGF1dGhfdmlhID0gIlBST1BTIgogICAgICAgICAgICAgICAgIyAoc2kgcHJvcHMgZGEgT1RS
TyB2YWxvciwgZXMgSU5DT05DTFVTTzogL3Byb3BzIHBvZHJpYQogICAgICAgICAgICAgICAgIyBy
ZWZsZWphciBlbCBHR1VGIGNydWRvIHkgbm8gZWwgaHBhcmFtIHRyYXMgb3ZlcnJpZGU7CiAgICAg
ICAgICAgICAgICAjIHNlIGNhZSBhIGxhIHZpYSBjb21wb3J0YW1lbnRhbCBzaW4gY2FzdGlnYXIp
CiAgICAgICAgICAgIGlmIGFwbGljYWRvIGlzIE5vbmUgYW5kIG92ZXJyaWRlX3BlZGlkYSA9PSA4
OgogICAgICAgICAgICAgICAgIyBrPTggPSBkZWZhdWx0IGRlbCBHR1VGOiBuby1vcCBwb3IgZGlz
ZW5vLCBuYWRhIHB1ZWRlCiAgICAgICAgICAgICAgICAjIGZhbGxhcjsgbGEgbWVkaWRhIFNJRU1Q
UkUgZXMgdW4gaz04IHZhbGlkby4KICAgICAgICAgICAgICAgIGFwbGljYWRvID0gVHJ1ZQogICAg
ICAgICAgICAgICAgYXV0aF92aWEgPSAiREVGQVVMVCIKICAgICAgICBmaWxhWyJhdXRoX3ZpYSJd
ID0gYXV0aF92aWEKICAgICAgICBmaWxhWyJvdmVycmlkZV9hcGxpY2FkbyJdID0gKHsiTE9HIjog
IlNJIn0uZ2V0KGF1dGhfdmlhLCBhdXRoX3ZpYSkKICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgIGlmIGF1dGhfdmlhIGVsc2UKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICgiTk8iIGlmIG92ZXJyaWRlX3BlZGlkYSBpcyBub3QgTm9uZQogICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgIGVsc2UgIiIpKQogICAgICAgIGZpbGFbIm5fZXhwZXJ0
X3VzZWRfbG9nIl0gPSBzdHIobG9nX3R4dC5nZXQoIm5fZXhwZXJ0X3VzZWRfbG9nIikgb3IgIiIp
CiAgICAgICAgZmlsYVsiYXJjaF9nZ3VmIl0gPSBjb250ZXh0by5nZXQoImFyY2hfZ2d1ZiIpIG9y
ICIiCiAgICAgICAgZmlsYVsiYXJjaF9sb2ciXSA9IGxvZ190eHQuZ2V0KCJhcmNoX2xvZyIpIG9y
ICIiCiAgICAgICAgZmlsYVsibl9leHBlcnRfbG9nIl0gPSBzdHIobG9nX3R4dC5nZXQoIm5fZXhw
ZXJ0X2xvZyIpIG9yICIiKQogICAgICAgIGZpbGFbImJ1ZmZlcl9taWIiXSA9IHN0cihsb2dfdHh0
LmdldCgiYnVmZmVyX21pYiIpIG9yICIiKQogICAgICAgIHZyYW0gPSBOb25lIGlmIGNvbnRleHRv
WyJzaW5fbnZpZGlhIl0gZWxzZSB2cmFtX252aWRpYSgpCiAgICAgICAgaWYgdnJhbToKICAgICAg
ICAgICAgZmlsYVsidnJhbV91c2FkYV9taWIiXSwgZmlsYVsidnJhbV90b3RhbF9taWIiXSA9IHN0
cih2cmFtWzBdKSwgc3RyKHZyYW1bMV0pCiAgICAgICAgICAgIGlmIHZyYW1bMF0gPiAzNzAwOgog
ICAgICAgICAgICAgICAgcHJpbnQoeWVsbG93KCIgICAgQVZJU08gVlJBTTogJWQgTWlCIHVzYWRv
cyAoPjM3MDAsIHJpZXNnbyBkZSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgInN5c21l
bSBmYWxsYmFjaykiICUgdnJhbVswXSkpCgogICAgICAgIHZhbGlkbyA9IFRydWUKICAgICAgICBu
b3RhcyA9IFtdCiAgICAgICAgaWYgbG9nX3R4dC5nZXQoImZpdF9pbmZvIik6CiAgICAgICAgICAg
ICMgdjEuMi4xOiBpbmZvcm1hdGl2YSwgTk8gaW52YWxpZGEgKGF1dG8tZml0IGRlY2xpbmFuZG8p
CiAgICAgICAgICAgIG5vdGFzLmFwcGVuZChsb2dfdHh0LmdldCgiZml0X2luZm8iKSkKICAgICAg
ICBpZiBsb2dfdHh0LmdldCgiZml0X2Fib3J0Iik6CiAgICAgICAgICAgIHZhbGlkbyA9IEZhbHNl
CiAgICAgICAgICAgIG5vdGFzLmFwcGVuZCgiZml0IGFib3J0YWRvIGVuIGVsIGxvZyAoY2F1c2Eg
cmVhbCwgbm8gZWwgYXV0by1maXQpIikKICAgICAgICBpZiBsb2dfdHh0LmdldCgic3lzbWVtX3dh
cm4iKToKICAgICAgICAgICAgbm90YXMuYXBwZW5kKCJhdmlzbyBzeXNtZW0vc2hhcmVkIGVuIGVs
IGxvZyAocG9zaWJsZSBzcGlsbCkiKQoKICAgICAgICBtZWRfb2sgPSBGYWxzZQogICAgICAgIHBy
aW50KGN5YW4oIiAgICBtaWRpZW5kbzogNCBwYXNhZGFzIHggMjU2IHRva2VucyAodGVtcCAwLCBw
cm9tcHRzICIKICAgICAgICAgICAgICAgICAgICJkaXN0aW50b3MpLi4uIikpCiAgICAgICAgdHJ5
OgogICAgICAgICAgICBwcmVmaWxsLCBkZWNzLCBkZXRhbGxlID0gcGFzYWRhc19tZWRpY2lvbihQ
VUVSVE9fREVGLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICBQUk9NUFRTX01FRElDSU9OLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICBwcm9jPXByb2MpCiAgICAgICAgICAgIG1lZF9vayA9IFRy
dWUKICAgICAgICBleGNlcHQgTWVhc0Vycm9yIGFzIGU6CiAgICAgICAgICAgIHZhbGlkbyA9IEZh
bHNlICAjIHYxLjE6IHVuYSBtZWRpY2lvbiBxdWUgZmFsbG8gSkFNQVMgZXMgdmFsaWRhCiAgICAg
ICAgICAgIG5vdGFzLmFwcGVuZCgibWVkaWNpb24gZmFsbG86ICVzIiAlIGUpCiAgICAgICAgICAg
IHByaW50KHJlZCgiICAgIEZBSUwgbWVkaWNpb246ICVzIiAlIGUpKQogICAgICAgIGV4Y2VwdCBF
eGNlcHRpb24gYXMgZToKICAgICAgICAgICAgdmFsaWRvID0gRmFsc2UKICAgICAgICAgICAgbm90
YXMuYXBwZW5kKCJtZWRpY2lvbiBmYWxsbyAoaW5lc3BlcmFkbyk6ICVyIiAlIGUpCiAgICAgICAg
ICAgIHByaW50KHJlZCgiICAgIEZBSUwgbWVkaWNpb246ICVyIiAlIGUpKQogICAgICAgIGlmIG1l
ZF9vazoKICAgICAgICAgICAgZGVjID0gbWVkaWEoZGVjcykKICAgICAgICAgICAgZmlsYVsicHJl
ZmlsbF90cyJdID0gZm10KHByZWZpbGwsIDEpCiAgICAgICAgICAgIGZvciBqLCB2IGluIGVudW1l
cmF0ZShkZWNzKToKICAgICAgICAgICAgICAgIGZpbGFbImRlY19yJWQiICUgKGogKyAyKV0gPSBm
bXQodiwgMikKICAgICAgICAgICAgZmlsYVsiZGVjb2RlX3RzIl0gPSBmbXQoZGVjLCAyKQogICAg
ICAgICAgICBjb21wbGV0by51cGRhdGUoeyJwcmVmaWxsX3RzIjogcHJlZmlsbCwgImRlY19yMl9h
X3I0IjogZGVjcywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAiZGVjb2RlX3RzIjogZGVj
LCAicGFzYWRhcyI6IGRldGFsbGUsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImxvZ19k
YXRvcyI6IGxvZ190eHQsICJ2cmFtIjogdnJhbX0pCgogICAgICAgICAgICAjIC0tLS0gdjEuMi4x
OiB2ZXJlZGljdG8gb3ZlcnJpZGUgUE9TVC1tZWRpY2lvbiAtLS0tCiAgICAgICAgICAgICMgbGEg
dmlhIGNvbXBvcnRhbWVudGFsIG5lY2VzaXRhIGVsIGRlY29kZSBtZWRpZG86IGxhIGRlY2lzaW9u
CiAgICAgICAgICAgICMgc2UgY29tcGxldGEgQVFVSSwgbm8gYW50ZXMgZGUgbWVkaXIuCiAgICAg
ICAgICAgIGlmIG92ZXJyaWRlX3BlZGlkYSBpcyBub3QgTm9uZSBhbmQgYXBsaWNhZG8gaXMgTm9u
ZToKICAgICAgICAgICAgICAgIGNvbXAgPSBhdXRlbnRpY2FyX2NvbXBvcnRhbWVudGFsKG92ZXJy
aWRlX3BlZGlkYSwgZGVjLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgcmVzdWx0YWRvc19wcmV2KQogICAgICAgICAgICAgICAgaWYgY29tcCBpcyBUcnVl
OgogICAgICAgICAgICAgICAgICAgIGFwbGljYWRvID0gVHJ1ZQogICAgICAgICAgICAgICAgICAg
IGF1dGhfdmlhID0gIkNPTVAiCiAgICAgICAgICAgICAgICAgICAgZmlsYVsiYXV0aF92aWEiXSA9
ICJDT01QIgogICAgICAgICAgICAgICAgICAgIGZpbGFbIm92ZXJyaWRlX2FwbGljYWRvIl0gPSAi
Q09NUCIKICAgICAgICAgICAgICAgIGVsaWYgY29tcCBpcyBGYWxzZToKICAgICAgICAgICAgICAg
ICAgICBhcGxpY2FkbyA9IEZhbHNlCiAgICAgICAgICAgICAgICAgICAgZmlsYVsib3ZlcnJpZGVf
YXBsaWNhZG8iXSA9ICJOTyIKICAgICAgICAgICAgICAgICMgY29tcCBOb25lOiBzaW4gcmVmZXJl
bmNpYXMgaz04IGVuIHNlc2lvbiAtPiBubyBhdXRlbnRpY2FkbwogICAgICAgICAgICBpZiBvdmVy
cmlkZV9wZWRpZGEgaXMgbm90IE5vbmUgYW5kIGFwbGljYWRvIGlzIG5vdCBUcnVlOgogICAgICAg
ICAgICAgICAgdmFsaWRvID0gRmFsc2UKICAgICAgICAgICAgICAgIGlmIGFwbGljYWRvIGlzIEZh
bHNlIGFuZCAiTE9HIiA9PSAoZmlsYS5nZXQoImF1dGhfdmlhIikgb3IgIiIpOgogICAgICAgICAg
ICAgICAgICAgIG5vdGFzLmFwcGVuZCgiT1ZFUlJJREUgTk8gQVBMSUNBRE8gKGxvZyBuX2V4cGVy
dF91c2VkPSVzICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIiE9ICVkKTogcnVu
IElOVkFMSURPIHBvciByZWdsYSBTUzEyLjIiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICUgKGxvZ190eHQuZ2V0KCJuX2V4cGVydF91c2VkX2xvZyIpLAogICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICBvdmVycmlkZV9wZWRpZGEpKQogICAgICAgICAgICAgICAgZWxp
ZiBhcGxpY2FkbyBpcyBGYWxzZToKICAgICAgICAgICAgICAgICAgICBub3Rhcy5hcHBlbmQoIk9W
RVJSSURFIE5PIFJFU1BPTkRFIChkZWNvZGUgJS4yZiB2cyByZWYgIgogICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAiaz04IGRlIHNlc2lvbik6IGxhIGN1cnZhIG5vIHJlYWNjaW9uYSBh
IGxhICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImRvc2lzIC0+IHNvc3BlY2hh
IGRlIG5vLW9wIChTUzQvU1MxMi4yKSIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
JSBkZWMpCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIG5vdGFzLmFw
cGVuZCgiT1ZFUlJJREUgTk8gQVVURU5USUNBRE8gKGxvZyBzaW4gaHBhcmFtcywgIgogICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAiL3Byb3BzIHNpbiBkYXRvIHkgc2luIHJlZmVyZW5j
aWFzIGs9OCBlbiAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJsYSBzZXNpb24p
OiByZS1jb3JycmlyIHNlc2lvbiBjb21wbGV0YSBvICIKICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgInN1YmlyIC1sdiAoU1MxMi4yKSIpCiAgICAgICAgICAgICMgZGlzcGVyc2lvbiBl
bnRyZSBwYXNhZGFzICh2MS4yLjEpOiBvdXRsaWVyIHZpc2libGUgKGxhIE1FQy01MTIKICAgICAg
ICAgICAgIyByZWFsIHRlbmlhIDIyLjM3IGVudHJlIDE4LjItMTguOSkKICAgICAgICAgICAgaWYg
bGVuKGRlY3MpID49IDIgYW5kIG1pbihkZWNzKSA+IDA6CiAgICAgICAgICAgICAgICBkaXNwID0g
bWF4KGRlY3MpIC8gbWluKGRlY3MpCiAgICAgICAgICAgICAgICBmaWxhWyJkaXNwZXJzX21heF9t
aW4iXSA9ICIlLjNmIiAlIGRpc3AKICAgICAgICAgICAgICAgIGlmIGRpc3AgPiAxLjA4OgogICAg
ICAgICAgICAgICAgICAgIG5vdGFzLmFwcGVuZCgiZGlzcGVyc2lvbiBhbHRhIGVuIHBhc2FkYXMg
KG1heC9taW49JS4yZik6ICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImNvbmZp
cm1hciBjb24gbWVkaWFuYSBkZSAzIChTUzE1KSIgJSBkaXNwKQogICAgICAgICAgICBjb21wbGV0
b1siYXV0aF92aWEiXSA9IGF1dGhfdmlhCiAgICAgICAgICAgIGNvbXBsZXRvWyJwcm9wc19rIl0g
PSBwcm9wc19rCgogICAgICAgICAgICBpZiBjb250ZXh0b1siY29uX3Nhbml0eSJdOgogICAgICAg
ICAgICAgICAgb2tfbiwgdHJ1bmNfbiwgdG90LCBzZGV0ID0gc2FuaXR5X2NoYXQoUFVFUlRPX0RF
RikKICAgICAgICAgICAgICAgIGZpbGFbInNhbml0eV9va19uIl0gPSBzdHIob2tfbikKICAgICAg
ICAgICAgICAgIGZpbGFbInNhbml0eV90cnVuY19uIl0gPSBzdHIodHJ1bmNfbikKICAgICAgICAg
ICAgICAgIGZpbGFbInNhbml0eV90b3RhbCJdID0gc3RyKHRvdCkKICAgICAgICAgICAgICAgIGNv
bXBsZXRvWyJzYW5pdHkiXSA9IHNkZXQKICAgICAgICAgICAgICAgIGlmIG9rX24gPT0gdG90Ogog
ICAgICAgICAgICAgICAgICAgIG1hcmNhID0gZ3JlZW4oIiVkLyVkIiAlIChva19uLCB0b3QpKQog
ICAgICAgICAgICAgICAgZWxpZiB0cnVuY19uIGFuZCAob2tfbiArIHRydW5jX24gPT0gdG90KToK
ICAgICAgICAgICAgICAgICAgICBtYXJjYSA9IHllbGxvdygiJWQgT0sgKyAlZFQvJWQiICUgKG9r
X24sIHRydW5jX24sIHRvdCkpCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAg
ICAgIG1hcmNhID0gcmVkKCIlZC8lZCAoJWRUKSIgJSAob2tfbiwgdG90LCB0cnVuY19uKSkKICAg
ICAgICAgICAgICAgIHByaW50KCIgICAgc2FuaXR5IGF1dG86ICVzIiAlIG1hcmNhKQogICAgICAg
ICAgICAgICAgaWYgb2tfbiA8IHRvdDoKICAgICAgICAgICAgICAgICAgICBpZiB0cnVuY19uIGFu
ZCAob2tfbiArIHRydW5jX24gPT0gdG90KToKICAgICAgICAgICAgICAgICAgICAgICAgbm90YXMu
YXBwZW5kKCJzYW5pdHkgJWQgT0sgKyAlZCB0cnVuY2FkYXMgKHByb2JlICIKICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICJjb3J0byBkZW50cm8gZGUgPHRoaW5rPiwgbm8gZXMg
ZmFsbG8gIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImRlIGNhbGlkYWQp
IiAlIChva19uLCB0cnVuY19uKSkKICAgICAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAg
ICAgICAgICAgICAgICBub3Rhcy5hcHBlbmQoInNhbml0eSBjb24gZmFsbG9zIHJlYWxlcyAoJWQv
MyBPSywgIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIiVkIHRydW5jYWRh
cykiICUgKG9rX24sIHRydW5jX24pKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIGNvbXBsZXRv
LnVwZGF0ZSh7ImxvZ19kYXRvcyI6IGxvZ190eHQsICJlcnJvcmVzIjogbGlzdChub3Rhcyl9KQog
ICAgICAgIGZpbGFbInZhbGlkbyJdID0gIlNJIiBpZiB2YWxpZG8gZWxzZSAiTk8iCiAgICAgICAg
ZmlsYVsibm90YSJdID0gIjsgIi5qb2luKG5vdGFzKQogICAgICAgIGVzdGFkb19ydW4gPSBncmVl
bigiVkFMSURPIikgaWYgdmFsaWRvIGVsc2UgcmVkKCJJTlZBTElETyIpCiAgICAgICAgcHJpbnQo
IiAgICBkZWNvZGUgJXMgdC9zIHwgcHJlZmlsbCAlcyB0b2svcyB8ICVzICVzIgogICAgICAgICAg
ICAgICUgKGJvbGQoZm10KGZpbGEuZ2V0KCJkZWNvZGVfdHMiKSBvciBOb25lKSksCiAgICAgICAg
ICAgICAgICAgZm10KGZpbGEuZ2V0KCJwcmVmaWxsX3RzIikgb3IgTm9uZSwgMCksIGVzdGFkb19y
dW4sCiAgICAgICAgICAgICAgICAgZ3JheSgoIjsgIiArICI7ICIuam9pbihub3RhcykpIGlmIG5v
dGFzIGVsc2UgIiIpKSkKICAgIGZpbmFsbHk6CiAgICAgICAgYXBhZ2FyX3NlcnZlcihwcm9jKQog
ICAgcmV0dXJuIGZpbGEsIGNvbXBsZXRvCgoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0gaW5mb3JtZSAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCmRlZiBwcm90
b2NvbG9fZGVjaXNpb24ocmVzdWx0YWRvcywgYW5jbGFfZGVjKToKICAgICIiIkV2YWx1YSBhdXRv
bWF0aWNhbWVudGUgZWwgYXJib2wgZGUgZGVjaXNpb24gU1MxMS40IGRlbCBuaXZlbC0xLiIiIgog
ICAgbGluZWFzID0gW10KICAgIGFuY2xhID0gcmVzdWx0YWRvcy5nZXQoMSkKICAgIGV4cDQgPSBy
ZXN1bHRhZG9zLmdldCg2KQogICAgZXhwMTAgPSByZXN1bHRhZG9zLmdldCgyKQogICAgZXhwOCA9
IHJlc3VsdGFkb3MuZ2V0KDMpCiAgICAjIHJ1biBhdXRlbnRpY2Fkb3IgY3J1emFkbyAtb3QgKFNT
MTgpOiBOTyBkZXBlbmRlIGRlbCBhbmNsYSBFWFAgLT4gdmEKICAgICMgYW50ZXMgZGVsIGd1YXJk
aWEgKGVuIC0tc29sbyBtZWMsb3QgZWwgYW5jbGEgbm8gZXhpc3RlIHkgZWwgdmVyZWRpY3RvCiAg
ICAjIGRlbCBjcnV6YWRvIGlndWFsbWVudGUgZGViZSBzYWxpcikKICAgIG90ID0gcmVzdWx0YWRv
cy5nZXQoMTUpCiAgICBpZiBvdCBhbmQgb3QuZ2V0KCJkZWNvZGVfdHMiKToKICAgICAgICBtZWMw
ID0gcmVzdWx0YWRvcy5nZXQoMTApCiAgICAgICAgcmVmID0gbWVjMC5nZXQoImRlY29kZV90cyIp
IGlmIChtZWMwIGFuZCBtZWMwLmdldCgiZGVjb2RlX3RzIikpIFwKICAgICAgICAgICAgZWxzZSBO
b25lCiAgICAgICAgaWYgcmVmOgogICAgICAgICAgICBkZXN2ID0gYWJzKG90WyJkZWNvZGVfdHMi
XSAvIHJlZiAtIDEuMCkKICAgICAgICAgICAgaWYgZGVzdiA8PSBtYXgoVEVDSE9fUlVJRE8gLyBy
ZWYsIDAuMDIpOgogICAgICAgICAgICAgICAgbGluZWFzLmFwcGVuZCgiLSBSVU4gQ1JVWkFETyAt
b3QgKFNTMTgpOiAlLjJmIHZzIGNvbnRyb2wgIgogICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAiTkNNMzdDNCAlLjJmIChoaXN0LiAyMi40OSk6IGtub2IgLW90ICIKICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgIkNPTVBSRU5ESURPLCBvZmZsb2FkIHZhbGlkYWRvIHBvciAyYSB2aWEi
CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICUgKG90WyJkZWNvZGVfdHMiXSwgcmVmKSkK
ICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgIGxpbmVhcy5hcHBlbmQoIi0gUlVOIENS
VVpBRE8gLW90IChTUzE4KTogJS4yZiBzZSBERVNWSUEgZGVsICIKICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgImNvbnRyb2wgTkNNMzdDNCAlLjJmICglLjFmJSUpOiBidWcgZGUgIgogICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAiY29tcHJlbnNpb24gZGVsIGtub2IgQU5URVMgZGUg
c2VndWlyIGJhcnJpZW5kbyIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgJSAob3RbImRl
Y29kZV90cyJdLCByZWYsIGRlc3YgKiAxMDApKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIGxp
bmVhcy5hcHBlbmQoIi0gUlVOIENSVVpBRE8gLW90IChTUzE4KTogJS4yZiB0L3MgKHNpbiBjb250
cm9sICIKICAgICAgICAgICAgICAgICAgICAgICAgICAiTkNNMzdDNCBlbiBzZXNpb247IGhpc3Qu
IDIyLjQ5IFtNXSkiCiAgICAgICAgICAgICAgICAgICAgICAgICAgJSBvdFsiZGVjb2RlX3RzIl0p
CiAgICBpZiBub3QgYW5jbGEgb3Igbm90IGFuY2xhLmdldCgiZGVjb2RlX3RzIik6CiAgICAgICAg
bGluZWFzLmFwcGVuZCgiLSBBTkNMQSBzaW4gZGF0bzogbm8gc2UgcHVlZGUgZXZhbHVhciBlbCBh
cmJvbCAocnVuIGludmFsaWRvPykiKQogICAgICAgIHJldHVybiBsaW5lYXMKICAgICMgLS0tLSBC
T09LRU5EICh2MS4yLjEpOiBELUFOQ0xBLUZJTiBhbCBjaWVycmUgbWlkZSBlbCBkcmlmdCBkZSBz
ZXNpb24KICAgIGFuY2xhZmluID0gcmVzdWx0YWRvcy5nZXQoMTYpCiAgICBpZiBhbmNsYWZpbiBh
bmQgYW5jbGFmaW4uZ2V0KCJkZWNvZGVfdHMiKToKICAgICAgICBkcmlmdCA9IGFuY2xhZmluWyJk
ZWNvZGVfdHMiXSAvIGFuY2xhWyJkZWNvZGVfdHMiXSAtIDEuMAogICAgICAgIGlmIGFicyhkcmlm
dCkgPD0gbWF4KFRFQ0hPX1JVSURPIC8gYW5jbGFbImRlY29kZV90cyJdLCAwLjAyKToKICAgICAg
ICAgICAgbGluZWFzLmFwcGVuZCgiLSBCT09LRU5EIGFuY2xhLWNpZXJyZTogJS4yZiB2cyBpbmlj
aW8gJS4yZiAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgIihkcmlmdCAlKy4xZiUlKTogc2Vz
aW9uIEVTVEFCTEUsIGxvcyBkZWx0YXMgIgogICAgICAgICAgICAgICAgICAgICAgICAgICJyZWxh
dGl2b3Mgc29uIGZpYWJsZXMiCiAgICAgICAgICAgICAgICAgICAgICAgICAgJSAoYW5jbGFmaW5b
ImRlY29kZV90cyJdLCBhbmNsYVsiZGVjb2RlX3RzIl0sCiAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgZHJpZnQgKiAxMDApKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIGxpbmVhcy5hcHBl
bmQoIi0gQk9PS0VORCBhbmNsYS1jaWVycmU6ICUuMmYgdnMgaW5pY2lvICUuMmYgIgogICAgICAg
ICAgICAgICAgICAgICAgICAgICIoZHJpZnQgJSsuMWYlJSk6IExBIFNFU0lPTiBERVJJVk87IGxl
ZXIgbG9zICIKICAgICAgICAgICAgICAgICAgICAgICAgICAiZGVsdGFzIGNvbiBjdWlkYWRvIHkg
cHJlZmVyaXIgY29tcGFyYWNpb25lcyAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgImRlbnRy
byBkZSBsYSBtaXNtYSB2ZW50YW5hIgogICAgICAgICAgICAgICAgICAgICAgICAgICUgKGFuY2xh
ZmluWyJkZWNvZGVfdHMiXSwgYW5jbGFbImRlY29kZV90cyJdLAogICAgICAgICAgICAgICAgICAg
ICAgICAgICAgIGRyaWZ0ICogMTAwKSkKICAgICMgLS0tLSBDT05UUk9MIEVYUDEwOiBjb21wYXJh
ciBQUklNRVJPIGNvbnRyYSBFWFA4IChrPTggZGUgc2VzaW9uKTsKICAgICMgbGEgY29ycmlkYSBy
ZWFsIG1vc3RybyBxdWUgZWwgYW5jbGEgZGUgQVJSQU5RVUUgc2FsZSBkZXByaW1pZGEKICAgICMg
KEVYUDggaz1kZWZhdWx0IG1pZGlvICsxNS4yJSBzb2JyZSBlbGxhKSB5IGNvbnRyYSBlbCBhbmNs
YSBlbAogICAgIyBjb250cm9sIHBhcmVjaWEgIm5vIGZyZW5hciIgc2llbmRvIHF1ZSBmcmVubyAt
MTUuNCUgdnMgRVhQOC4KICAgIHJlZjggPSBOb25lCiAgICBpZiBleHA4IGFuZCBleHA4LmdldCgi
ZGVjb2RlX3RzIik6CiAgICAgICAgcmVmOCA9IGV4cDhbImRlY29kZV90cyJdCiAgICBlbGlmIGFu
Y2xhLmdldCgiZGVjb2RlX3RzIik6CiAgICAgICAgcmVmOCA9IGFuY2xhWyJkZWNvZGVfdHMiXQog
ICAgaWYgZXhwMTAgYW5kIGV4cDEwLmdldCgiZGVjb2RlX3RzIikgYW5kIHJlZjg6CiAgICAgICAg
aWYgZXhwMTBbImRlY29kZV90cyJdIDwgcmVmOCAtIFRFQ0hPX1JVSURPOgogICAgICAgICAgICBs
aW5lYXMuYXBwZW5kKCItIENPTlRST0wgRVhQMTAgZnJlbm8gdnMgcmVmIGs9OCAoJS4yZiA8ICUu
MmYgLSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgInJ1aWRvOyAlKy4xZiUlKTogZWwgbWVj
YW5pc21vIG92ZXJyaWRlIFJFU1BPTkRFICIKICAgICAgICAgICAgICAgICAgICAgICAgICAiW01d
IiAlIChleHAxMFsiZGVjb2RlX3RzIl0sIHJlZjgsCiAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgKGV4cDEwWyJkZWNvZGVfdHMiXSAvIHJlZjggLSAxLjApICogMTAwKSkKICAgICAg
ICAgICAgaWYgZXhwOCBhbmQgZXhwOC5nZXQoImRlY29kZV90cyIpIGFuZCBhbmNsYS5nZXQoImRl
Y29kZV90cyIpIFwKICAgICAgICAgICAgICAgICAgICBhbmQgYWJzKGV4cDhbImRlY29kZV90cyJd
IC0gYW5jbGFbImRlY29kZV90cyJdKSA+IFRFQ0hPX1JVSURPOgogICAgICAgICAgICAgICAgbGlu
ZWFzLmFwcGVuZCgiLSBPSk8gc2VzZ28gZGUgYXJyYW5xdWU6IEVYUDggKGs9OD1kZWZhdWx0KSAi
CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJtaWRpbyAlKy4xZiUlIHNvYnJlIGVsIGFu
Y2xhIC0+IGVsIGFuY2xhIGRlICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImluaWNp
byBzYWxlIGRlcHJpbWlkYTsgdXNhciBFWFA4IGNvbW8gcmVmIGRlICIKICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgInNlc2lvbiB5IGxlZXIgJ3ZzIGFuY2xhJyBjb21vIGluZmxhZG9zIgog
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAlICgoZXhwOFsiZGVjb2RlX3RzIl0gLyBhbmNs
YVsiZGVjb2RlX3RzIl0KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIC0gMS4wKSAq
IDEwMCkpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgbGluZWFzLmFwcGVuZCgiLSBDT05UUk9M
IEVYUDEwIE5PIGZyZW5vICglLjJmID49IHJlZiBrPTggJS4yZiAtICIKICAgICAgICAgICAgICAg
ICAgICAgICAgICAicnVpZG8pOiBvdmVycmlkZSBTT1NQRUNIT1NPIC0+IHRyYXRhciBjb21vICIK
ICAgICAgICAgICAgICAgICAgICAgICAgICAic29zcGVjaGEgZGUgbm8tb3AgKFNTNCkiCiAgICAg
ICAgICAgICAgICAgICAgICAgICAgJSAoZXhwMTBbImRlY29kZV90cyJdLCByZWY4KSkKICAgIGlm
IGV4cDQgYW5kIGV4cDQuZ2V0KCJkZWNvZGVfdHMiKSBhbmQgYW5jbGEuZ2V0KCJkZWNvZGVfdHMi
KToKICAgICAgICBkZWx0YSA9IGV4cDRbImRlY29kZV90cyJdIC8gYW5jbGFbImRlY29kZV90cyJd
IC0gMS4wCiAgICAgICAgaWYgZXhwNC5nZXQoInZhbGlkbyIpICE9ICJTSSI6CiAgICAgICAgICAg
IGxpbmVhcy5hcHBlbmQoIi0gRVhQNCBpbnZhbGlkbyAoJXMpOiByZXNvbHZlciBsYSBhdXRlbnRp
Y2FjaW9uICIKICAgICAgICAgICAgICAgICAgICAgICAgICAiQU5URVMgZGUgc2VndWlyIGxhIGVz
Y2FsZXJhIiAlIGV4cDQuZ2V0KCJub3RhIiwgIiIpKQogICAgICAgIGVsaWYgZGVsdGEgPj0gMC4x
MDoKICAgICAgICAgICAgbGluZWFzLmFwcGVuZCgiLSBET1NJUyBWSVZBOiBFWFA0ICslLjFmJSUg
KGVzcGVyYWRvIDE1LTE3JSUpOiAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgImVzY2FsZXJh
IGs9Ni0+NC0+MyBDT05GSVJNQURBOyBzZWd1aXIgY29uIEVYUDMgeSAiCiAgICAgICAgICAgICAg
ICAgICAgICAgICAgInNhbml0eSBtYW51YWwgZGUgMjAgcHJvbXB0cyAoU1M1KSBhbnRlcyBkZSBm
aWphciBrICIKICAgICAgICAgICAgICAgICAgICAgICAgICAib3BlcmF0aXZvIChTUzExLjQgY2Fz
byAxKSIgJSAoZGVsdGEgKiAxMDApKQogICAgICAgIGVsaWYgZGVsdGEgPiAwOgogICAgICAgICAg
ICBsaW5lYXMuYXBwZW5kKCItIEVYUDQgc3ViZSBzb2xvICslLjFmJSUgKDwxMCUlKSBjb24gbl9l
eHBlcnRfdXNlZCAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgImNvcnJlY3RvOiBsYSBiYW5k
YSB5YSBubyBkb21pbmEgLT4gcmV2aXNhciAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgImNv
bG9jYWNpb24gTkNNMzdDNC9GSVQtQSBhbnRlcyBkZSBiYWphciBrIChTUzExLjQgIgogICAgICAg
ICAgICAgICAgICAgICAgICAgICJjYXNvIDIpIiAlIChkZWx0YSAqIDEwMCkpCiAgICAgICAgZWxz
ZToKICAgICAgICAgICAgbGluZWFzLmFwcGVuZCgiLSBFWFA0IFBMQU5PIG8gbmVnYXRpdm8gQ09O
IG92ZXJyaWRlIGFwbGljYWRvOiBlbCAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgImJ1aWxk
IGlnbm9yYSBsYSBkb3NpcyAtPiBQTEFOIEI6IFJVVEEgMCAoYnVpbGQgIgogICAgICAgICAgICAg
ICAgICAgICAgICAgICJiMTE5MDEsIDIgemlwcykgKFNTMTEuNCBjYXNvIDMpIiAlICgpKQogICAg
IyAybyBhdXRlbnRpY2Fkb3IgZXZhbHVhZG8gKFNTMTIuNi9TUzEyLjkuNSk6IGVsIGJ1ZmZlciBD
VURBMCBkZWJlCiAgICAjIEJBSkFSIGNvbiBrIChtZW5vcyBleHBlcnRvcyBhY3Rpdm9zID0gaW50
ZXJtZWRpb3MgTW9FIG1lbm9yZXMpLiBIYXN0YQogICAgIyB2MS4xIHNlIHJlZ2lzdHJhYmEgeSBu
YWRpZSBsbyBsZWlhLgogICAgdHJ5OgogICAgICAgIGJfYW5jbGEgPSBmbG9hdChhbmNsYS5nZXQo
ImJ1ZmZlcl9taWIiKSkgaWYgYW5jbGEgZWxzZSBOb25lCiAgICBleGNlcHQgKFR5cGVFcnJvciwg
VmFsdWVFcnJvcik6CiAgICAgICAgYl9hbmNsYSA9IE5vbmUKICAgIGlmIG5vdCBiX2FuY2xhOgog
ICAgICAgIGxpbmVhcy5hcHBlbmQoIi0gYnVmZmVyIENVREEwIE4vRCAoYjExODU2IG5vIGltcHJp
bWUgJ0NVREEwIGNvbXB1dGUgIgogICAgICAgICAgICAgICAgICAgICAgImJ1ZmZlciBzaXplJyBl
biBlbCBsb2cgZGUgZXN0YSBzZXNpb24pOiBsYSAyYSB2aWEgZGVsICIKICAgICAgICAgICAgICAg
ICAgICAgICJidWZmZXIgbm8gZXN0YSBkaXNwb25pYmxlOyBxdWVkYW4gTE9HL1BST1BTL0NPTVAi
KQogICAgaWYgYl9hbmNsYToKICAgICAgICBmb3IgY2lkLCBrayBpbiAoKDYsIDQpLCAoNywgMyks
ICg4LCAyKSk6CiAgICAgICAgICAgIHIgPSByZXN1bHRhZG9zLmdldChjaWQpCiAgICAgICAgICAg
IHRyeToKICAgICAgICAgICAgICAgIGIgPSBmbG9hdChyLmdldCgiYnVmZmVyX21pYiIpKSBpZiBy
IGVsc2UgTm9uZQogICAgICAgICAgICBleGNlcHQgKFR5cGVFcnJvciwgVmFsdWVFcnJvcik6CiAg
ICAgICAgICAgICAgICBiID0gTm9uZQogICAgICAgICAgICBpZiBub3QgYjoKICAgICAgICAgICAg
ICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIGIgPCBiX2FuY2xhOgogICAgICAgICAgICAgICAg
bGluZWFzLmFwcGVuZCgiLSBCT05VUyBTUzEyLjY6IGJ1ZmZlciBDVURBMCBkZSBFWFAlZCA9ICUu
MGYgIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAiTWlCIHZzIGFuY2xhICUuMGYgTWlC
ICgtJS4wZiUlKTogbWVub3MgZXhwZXJ0b3MgIgogICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAiYWN0aXZvcyBsaWJlcmEgVlJBTSAoMmEgdmlhIGRlIGF1dGVudGljYWNpb24pIgogICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAlIChraywgYiwgYl9hbmNsYSwgKDEgLSBiIC8gYl9hbmNs
YSkgKiAxMDApKQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgbGluZWFzLmFwcGVu
ZCgiLSBCT05VUyBTUzEyLjY6IGJ1ZmZlciBDVURBMCBkZSBFWFAlZCBOTyBiYWpvICIKICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgIiglLjBmIHZzIGFuY2xhICUuMGYgTWlCKTogcmV2aXNh
ciAoZXNwZXJhZG8gIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAibWVub3IgY29uIGsg
YmFqbykiICUgKGtrLCBiLCBiX2FuY2xhKSkKICAgIHJldHVybiBsaW5lYXMKCgpkZWYgZ2VuZXJh
cl9pbmZvcm1lKGRpcl9sb2dzLCBjb250ZXh0bywgcmVzdWx0YWRvcywgY29tcGxldG9zLCBwcm9i
bGVtYXNfZmxhZ3MpOgogICAgbWQgPSBbXQogICAgbWQuYXBwZW5kKCIjIElORk9STUUgRkFTRSBE
IOKAlCBOSVZFTCAxOiByZWNvcnRlIGRlIGV4cGVydG9zICsgTUVDIikKICAgIG1kLmFwcGVuZCgi
IikKICAgIG1kLmFwcGVuZCgiR2VuZXJhZG86ICVzIMK3ICVzIMK3IHByb3RvICVzIiAlIChhaG9y
YSgpLCBWRVJTSU9OLCBQUk9UTykpCiAgICBtZC5hcHBlbmQoIiIpCiAgICBtZC5hcHBlbmQoIiMj
IDAuIFByZS12dWVsbyIpCiAgICBtZC5hcHBlbmQoIiIpCiAgICBtZC5hcHBlbmQoIi0gU2VydmVy
OiBgJXNgIiAlIGNvbnRleHRvWyJydXRhX3NlcnZlciJdKQogICAgbWQuYXBwZW5kKCItIFBpbiBk
ZWwgc2VydmVyOiAlcyIgJSAoY29udGV4dG8uZ2V0KCJwaW4iKSBvciAiTi9EIikKICAgICAgICAg
ICAgICArICgiIiBpZiBCVUlMRF9QSU5fRVNQRVJBRE8gaW4gKGNvbnRleHRvLmdldCgicGluIikg
b3IgIiIpCiAgICAgICAgICAgICAgICAgZWxzZSAiICAqKk9KTzogc2UgZXNwZXJhYmEgYnVpbGQg
JXMqKiIgJSBCVUlMRF9QSU5fRVNQRVJBRE8pKQogICAgbWQuYXBwZW5kKCItIE1vZGVsbzogYCVz
YCIgJSBjb250ZXh0b1sicnV0YV9tb2RlbG8iXSkKICAgIGlmIGNvbnRleHRvLmdldCgiYnl0ZXNf
bW9kZWxvIikgaXMgbm90IE5vbmU6CiAgICAgICAgb2tfYnl0ZXMgPSBjb250ZXh0b1siYnl0ZXNf
bW9kZWxvIl0gPT0gQllURVNfTU9ERUxPX0VTUEVSQURPUwogICAgICAgIG1kLmFwcGVuZCgiLSBC
eXRlcyBkZWwgbW9kZWxvOiAlcyAoZXNwZXJhZG9zICVzKSVzIgogICAgICAgICAgICAgICAgICAl
IChjb250ZXh0b1siYnl0ZXNfbW9kZWxvIl0sIEJZVEVTX01PREVMT19FU1BFUkFET1MsCiAgICAg
ICAgICAgICAgICAgICAgICIiIGlmIG9rX2J5dGVzIGVsc2UgIiAgKipOTyBDT0lOQ0lERU4qKiIp
KQogICAgaHAgPSBjb250ZXh0by5nZXQoImhwYXJhbXMiKSBvciB7fQogICAgbWQuYXBwZW5kKCIt
IEdHVUY6IGFyY2ggPSBgJXNgIMK3IG5fZXhwZXJ0ID0gJXMgwrcgbl9leHBlcnRfdXNlZCA9ICVz
ICIKICAgICAgICAgICAgICAiKHBhcnNlciBwcm9waW8sIEdHVUYgdiVzKSIKICAgICAgICAgICAg
ICAlIChocC5nZXQoImFyY2giKSwgaHAuZ2V0KCJuX2V4cGVydCIpLCBocC5nZXQoIm5fZXhwZXJ0
X3VzZWQiKSwKICAgICAgICAgICAgICAgICBocC5nZXQoImdndWZfdmVyc2lvbiIpKSkKICAgIG1k
LmFwcGVuZCgiLSBBdWRpdG9yaWEgZGUgZmxhZ3M6ICVzIgogICAgICAgICAgICAgICUgKCJWRVJE
RSAtIHRvZG9zIGxvcyB0b2tlbnMgdmVyYmF0aW0gZW4gZWwgZHVtcCBiMTE4NTYiCiAgICAgICAg
ICAgICAgICAgaWYgbm90IHByb2JsZW1hc19mbGFncyBlbHNlICJGQUxMT1M6ICVzIiAlIHByb2Js
ZW1hc19mbGFncykpCiAgICBtZC5hcHBlbmQoIi0gQ2xhdmUgb3ZlcnJpZGUgdXNhZGE6IGAlc2Ai
ICUgKGNvbnRleHRvLmdldCgiY2xhdmUiKSBvciAiTi9EIikpCiAgICBtZC5hcHBlbmQoIi0gQ29t
YW5kbyBiYXNlIHBvciBjb25maWc6IGAlc2AgKCsgZGlmZiBkZSBsYSBjb25maWc7IGVsICIKICAg
ICAgICAgICAgICAidWx0aW1vIHZhbG9yIGdhbmEpIiAlIChjb250ZXh0by5nZXQoImJhc2VfZmxh
Z3Nfc3RyIikgb3IgIk4vRCIpKQogICAgbWQuYXBwZW5kKCIiKQogICAgbWQuYXBwZW5kKCIjIyAx
LiBSZXN1bHRhZG9zIikKICAgIG1kLmFwcGVuZCgiIikKICAgIGFuY2xhID0gcmVzdWx0YWRvcy5n
ZXQoMSkgb3Ige30KICAgIGFuY2xhX2RlYyA9IGFuY2xhLmdldCgiZGVjb2RlX3RzIikKICAgIGV4
cDhfcmVmID0gKHJlc3VsdGFkb3MuZ2V0KDMpIG9yIHt9KS5nZXQoImRlY29kZV90cyIpCiAgICBt
ZC5hcHBlbmQoIkFuY2xhIGRlIHNlc2lvbiAoRC1BTkNMQSk6ICVzIHQvcyAocmVmZXJlbmNpYSBi
YXJyaWRvLTMwOiAyMS41MykiCiAgICAgICAgICAgICAgJSBmbXQoYW5jbGFfZGVjKSkKICAgIGlm
IGV4cDhfcmVmIGFuZCBhbmNsYV9kZWMgYW5kIGFicyhleHA4X3JlZiAtIGFuY2xhX2RlYykgPiBU
RUNIT19SVUlETyBcCiAgICAgICAgICAgIGFuZCAocmVzdWx0YWRvcy5nZXQoMykgb3Ige30pLmdl
dCgiYXV0aF92aWEiKSA9PSAiREVGQVVMVCI6CiAgICAgICAgbWQuYXBwZW5kKCIiKQogICAgICAg
IG1kLmFwcGVuZCgiKipPSk8gc2VzZ28gZGUgYXJyYW5xdWUqKjogRC1FWFA4IChrPTggPSBkZWZh
dWx0LCBuby1vcCBwb3IgIgogICAgICAgICAgICAgICAgICAiZGlzZW5vKSBtaWRpbyAlKy4xZiUl
IHNvYnJlIGVsIGFuY2xhIC0+IGVsIGFuY2xhIGRlIGluaWNpbyAiCiAgICAgICAgICAgICAgICAg
ICJzYWxlIGRlcHJpbWlkYTsgbGEgY29sdW1uYSAndnMgaz04JyB1c2EgRVhQOCBjb21vIHJlZmVy
ZW5jaWEgIgogICAgICAgICAgICAgICAgICAiZGUgc2VzaW9uIChsb3MgJ3ZzIGFuY2xhJyBxdWVk
YW4gaW5mbGFkb3MpLiIKICAgICAgICAgICAgICAgICAgJSAoKGV4cDhfcmVmIC8gYW5jbGFfZGVj
IC0gMS4wKSAqIDEwMCkpCiAgICBtZC5hcHBlbmQoIiIpCiAgICBtZC5hcHBlbmQoInwgaWQgfCBj
b25maWcgfCBmbGFncyB8IGRlY29kZSB0L3MgfCB2cyBhbmNsYSB8IHZzIGs9OCB8IGVzcGVyYWRv
IHwgIgogICAgICAgICAgICAgICJwcmVmaWxsIHwgb3ZlcnJpZGUgfCBidWZmZXIgTWlCIHwgVlJB
TSBNaUIgfCBzYW5pdHkgfCB2YWxpZG8gfCIpCiAgICBtZC5hcHBlbmQoInwtLS18LS0tfC0tLXwt
LS18LS0tfC0tLXwtLS18LS0tfC0tLXwtLS18LS0tfC0tLXwtLS18IikKICAgIGZvciBjaWQgaW4g
c29ydGVkKHJlc3VsdGFkb3MpOgogICAgICAgIHIgPSByZXN1bHRhZG9zW2NpZF0KICAgICAgICBk
ID0gci5nZXQoImRlY29kZV90cyIpCiAgICAgICAgZGVsdGEgPSAoIislMC4xZiUlIiAlICgoZCAv
IGFuY2xhX2RlYyAtIDEpICogMTAwKQogICAgICAgICAgICAgICAgIGlmIChkIGFuZCBhbmNsYV9k
ZWMpIGVsc2UgIk4vRCIpCiAgICAgICAgaWYgY2lkID09IDMgb3Igbm90IChkIGFuZCBleHA4X3Jl
Zik6CiAgICAgICAgICAgIGRlbHRhOCA9ICItIiBpZiBjaWQgPT0gMyBlbHNlICJOL0QiCiAgICAg
ICAgZWxzZToKICAgICAgICAgICAgZGVsdGE4ID0gIiUrMC4xZiUlIiAlICgoZCAvIGV4cDhfcmVm
IC0gMSkgKiAxMDApCiAgICAgICAgZXNwZXJhZG8gPSAiIgogICAgICAgIG0gPSByZS5zZWFyY2go
ciJpbnQ6KFxkKykiLCByLmdldCgib3ZlcnJpZGVfcGVkaWRhIikgb3IgIiIpCiAgICAgICAgaWYg
bSBhbmQgaW50KG0uZ3JvdXAoMSkpIGluIEVYUEVDVF9FWFA6CiAgICAgICAgICAgIGVzcGVyYWRv
ID0gRVhQRUNUX0VYUFtpbnQobS5ncm91cCgxKSldWzBdCiAgICAgICAgZWxpZiByLmdldCgiZmFt
aWxpYSIpID09ICJPVCI6CiAgICAgICAgICAgIGVzcGVyYWRvID0gInJ1biBjcnV6YWRvIFNTMTg6
IH5jb250cm9sIE5DTTM3QzQgKDIyLjQ5IFtNXSkiCiAgICAgICAgZWxpZiByLmdldCgiZmFtaWxp
YSIpID09ICJDT01CTzIiOgogICAgICAgICAgICBlc3BlcmFkbyA9ICJzdGFjayBmaW5hbDogRVhQ
NCB4IE5DTTM3QzQgeCBNRUMgKGxvcyBkb3MgR08gYXBpbGFkb3MpIgogICAgICAgIGVsaWYgci5n
ZXQoImZhbWlsaWEiKSA9PSAiQU5DTEEtRklOIjoKICAgICAgICAgICAgZXNwZXJhZG8gPSAiYm9v
a2VuZDogfmFuY2xhIGRlIGluaWNpbyBkZW50cm8gZGVsIHJ1aWRvIgogICAgICAgIGZsYWdzX2Nv
cnRvcyA9IChyLmdldCgiZmxhZ3MiKSBvciAiIikucmVwbGFjZSgKICAgICAgICAgICAgY29udGV4
dG8uZ2V0KCJiYXNlX2ZsYWdzX3N0ciIsICIiKSwgIiIpLnN0cmlwKCkKICAgICAgICBva24gPSBy
LmdldCgic2FuaXR5X29rX24iKSBvciAiLSIKICAgICAgICB0cm4gPSByLmdldCgic2FuaXR5X3Ry
dW5jX24iKSBvciAiIgogICAgICAgIHNhbl90eHQgPSAoIiVzKyVzVC8lcyIgJSAob2tuLCB0cm4s
IHIuZ2V0KCJzYW5pdHlfdG90YWwiKSBvciAiLSIpCiAgICAgICAgICAgICAgICAgICBpZiB0cm4g
bm90IGluICgiIiwgIjAiKSBlbHNlICIlcy8lcyIgJSAob2tuLCByLmdldCgic2FuaXR5X3RvdGFs
Iikgb3IgIi0iKSkKICAgICAgICBtZC5hcHBlbmQoInwgJXMgfCAlcyB8IGAlc2AgfCAlcyB8ICVz
IHwgJXMgfCAlcyB8ICVzIHwgJXMlcyB8ICVzIHwgJXMvJXMgfCAiCiAgICAgICAgICAgICAgICAg
ICIlcyB8ICVzIHwiCiAgICAgICAgICAgICAgICAgICUgKGNpZCwgci5nZXQoIm5vbWJyZSIpLCBm
bGFnc19jb3J0b3Mgb3IgIkJBU0UiLAogICAgICAgICAgICAgICAgICAgICBmbXQoZCksIGRlbHRh
LCBkZWx0YTgsIGVzcGVyYWRvLCBmbXQoci5nZXQoInByZWZpbGxfdHMiKSwgMCksCiAgICAgICAg
ICAgICAgICAgICAgIHIuZ2V0KCJvdmVycmlkZV9wZWRpZGEiKSBvciAiLSIsCiAgICAgICAgICAg
ICAgICAgICAgICgiLT4gIiArIHN0cihyLmdldCgib3ZlcnJpZGVfYXBsaWNhZG8iKSBvciAiLSIp
KSwKICAgICAgICAgICAgICAgICAgICAgci5nZXQoImJ1ZmZlcl9taWIiKSBvciAiTi9EIiwKICAg
ICAgICAgICAgICAgICAgICAgci5nZXQoInZyYW1fdXNhZGFfbWliIikgb3IgIk4vRCIsCiAgICAg
ICAgICAgICAgICAgICAgIHIuZ2V0KCJ2cmFtX3RvdGFsX21pYiIpIG9yICJOL0QiLAogICAgICAg
ICAgICAgICAgICAgICBzYW5fdHh0LAogICAgICAgICAgICAgICAgICAgICByLmdldCgidmFsaWRv
Iikgb3IgIiIpKQogICAgdmlhcyA9IHt9CiAgICBmb3IgY2lkIGluIHNvcnRlZChyZXN1bHRhZG9z
KToKICAgICAgICB2ID0gKHJlc3VsdGFkb3NbY2lkXS5nZXQoImF1dGhfdmlhIikgb3IgIiIpLnN0
cmlwKCkKICAgICAgICBpZiB2OgogICAgICAgICAgICB2aWFzW3ZdID0gdmlhcy5nZXQodiwgMCkg
KyAxCiAgICBtZC5hcHBlbmQoIiIpCiAgICBtZC5hcHBlbmQoIkxleWVuZGEgb3ZlcnJpZGU6IFNJ
ID0gYXV0ZW50aWNhZG8gdmlhIExPRyAoaHBhcmFtcyBpbXByZXNvcykgwrcgIgogICAgICAgICAg
ICAgICJQUk9QUyA9IHZpYSBHRVQgL3Byb3BzIMK3IENPTVAgPSBjb21wb3J0YW1lbnRhbCAobGEg
Y3VydmEgZGUgIgogICAgICAgICAgICAgICJzZXNpb24gcmVzcG9uZGUgYSBsYSBkb3NpcyBtYXMg
YWxsYSBkZWwgcnVpZG87IHJlZiBrPTggPSAiCiAgICAgICAgICAgICAgIm1heChhbmNsYSwgRVhQ
OCkpIMK3IERFRkFVTFQgPSBrPTggbm8tb3AgcG9yIGRpc2VubyDCtyBOTyA9IG5vICIKICAgICAg
ICAgICAgICAiYXBsaWNhZG8vbm8gYXV0ZW50aWNhZG8uIFZpYXMgdXNhZGFzIGVuIGVzdGEgc2Vz
aW9uOiAlcy4iCiAgICAgICAgICAgICAgJSAoIiwgIi5qb2luKCIlcyB4JWQiICUgKGssIHYpIGZv
ciBrLCB2IGluIHNvcnRlZCh2aWFzLml0ZW1zKCkpKQogICAgICAgICAgICAgICAgIG9yICJuaW5n
dW5hIChzaW4gcnVucyBkZSBvdmVycmlkZSkiKSkKICAgIG1kLmFwcGVuZCgiIikKICAgIG1kLmFw
cGVuZCgiUmVmZXJlbmNpYXMgaGlzdG9yaWNhcyBkZWwgYmFycmlkby0zMCBbTV06IGFuY2xhL09S
Ty1VQjFLID0gIgogICAgICAgICAgICAgICIlLjJmIHQvcyAtIE5DTTM3QzQgPSAlLjJmIHQvcyAo
KzQuNCUlKTsgcnVpZG8gZGVjbGFyYWRvICIKICAgICAgICAgICAgICAiKy8tMC4zLTAuNSB0L3Mu
IExhIGNvbHVtbmEgJ3ZzIGFuY2xhJyBjb21wYXJhIGNvbnRyYSBlbCAiCiAgICAgICAgICAgICAg
IkFOQ0xBIERFIEVTVEEgU0VTSU9OLCBubyBjb250cmEgZXN0b3MgbnVtZXJvcy4iCiAgICAgICAg
ICAgICAgJSAoQU5DTEFfVUIxSywgTkNNMzdDNF9SRUYpKQogICAgbWQuYXBwZW5kKCIiKQogICAg
bWQuYXBwZW5kKCIjIyAyLiBQcm90b2NvbG8gZGUgZGVjaXNpb24gU1MxMS40IChldmFsdWFjaW9u
IGF1dG9tYXRpY2EpIikKICAgIG1kLmFwcGVuZCgiIikKICAgIG1kLmV4dGVuZChwcm90b2NvbG9f
ZGVjaXNpb24ocmVzdWx0YWRvcywgYW5jbGFfZGVjKSBvcgogICAgICAgICAgICAgIFsiLSAoc2lu
IGRhdG9zIHN1ZmljaWVudGVzKSJdKQogICAgbWQuYXBwZW5kKCIiKQogICAgbWVjX2N0cmwgPSBy
ZXN1bHRhZG9zLmdldCgxMCkKICAgIGlmIG1lY19jdHJsIGFuZCBtZWNfY3RybC5nZXQoImRlY29k
ZV90cyIpOgogICAgICAgIG1kLmFwcGVuZCgiIyMgMy4gVmVyZWRpY3RvIE1FQyAoY29udHJvbCBE
LU1FQy0wIGVuIGxhIG1pc21hIHNlc2lvbjsgIgogICAgICAgICAgICAgICAgICAiY29udHJvbCBo
aXN0b3JpY28gTkNNMzdDNCA9IDIyLjQ5IFtNXTogZWwgTUVDMCBkZSBlc3RhICIKICAgICAgICAg
ICAgICAgICAgInNlc2lvbiBkZWJlcmlhIGNsYXZhcmxvIGRlbnRybyBkZWwgcnVpZG8pIikKICAg
ICAgICBtZC5hcHBlbmQoIiIpCiAgICAgICAgZm9yIGNpZCBpbiAoMTEsIDEyLCAxMyk6CiAgICAg
ICAgICAgIHIgPSByZXN1bHRhZG9zLmdldChjaWQpCiAgICAgICAgICAgIGlmIG5vdCByIG9yIG5v
dCByLmdldCgiZGVjb2RlX3RzIik6CiAgICAgICAgICAgICAgICBjb250aW51ZQogICAgICAgICAg
ICBkaWYgPSByWyJkZWNvZGVfdHMiXSAtIG1lY19jdHJsWyJkZWNvZGVfdHMiXQogICAgICAgICAg
ICBpZiBkaWYgPiBURUNIT19SVUlETzoKICAgICAgICAgICAgICAgIHZlcmVkaWN0byA9ICgiR0FO
QSB2cyBjb250cm9sICgrJS4yZik6IHByb3BvbmVyIGNvbW8gZG9zaXMiCiAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgJSBkaWYpCiAgICAgICAgICAgIGVsaWYgZGlmID49IC1URUNIT19SVUlE
TzoKICAgICAgICAgICAgICAgIHZlcmVkaWN0byA9ICgiRU1QQVRBIGNvbiBlbCBjb250cm9sICgl
Ky4yZiwgZGVudHJvIGRlbCAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgInJ1aWRvICsv
LSUuMmYpOiBlbCBjYWNoZSBOTyBhcG9ydGEgYXF1aSAtPiBzZSAiCiAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgInF1ZWRhIE9GRiAoc2luIGNhc3RpZ287IFNTMTUgc29sbyBkZXNjYXJ0YSBz
aSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIlBJRVJERSkiICUgKGRpZiwgVEVDSE9f
UlVJRE8pKQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgdmVyZWRpY3RvID0gKCJQ
SUVSREUgdnMgY29udHJvbCAoJS4yZik6IFNFIERFU0NBUlRBIChyZWdsYSAiCiAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgIlNTMTUsIGNhc28gNjAwIE1pQikiICUgZGlmKQogICAgICAgICAg
ICAjIHYxLjIuMTogZGlzcGVyc2lvbiBlbnRyZSBwYXNhZGFzIHZpc2libGUgZW4gZWwgdmVyZWRp
Y3RvIChsYQogICAgICAgICAgICAjIE1FQy01MTIgcmVhbCB0ZW5pYSB1biBvdXRsaWVyIDIyLjM3
IGVudHJlIDE4LjItMTguOSkKICAgICAgICAgICAgZXh0cmEgPSAiIgogICAgICAgICAgICB0cnk6
CiAgICAgICAgICAgICAgICBwYXNhZGFzID0gW2Zsb2F0KHJbImRlY19yJXMiICUgaV0pIGZvciBp
IGluICgyLCAzLCA0KQogICAgICAgICAgICAgICAgICAgICAgICAgICBpZiByLmdldCgiZGVjX3Il
cyIgJSBpKV0KICAgICAgICAgICAgICAgIGlmIGxlbihwYXNhZGFzKSA+PSAyIGFuZCBtaW4ocGFz
YWRhcykgPiAwOgogICAgICAgICAgICAgICAgICAgIGV4dHJhID0gIiAocGFzYWRhcyAlcywgZGlz
cGVyc2lvbiB4JS4yZiVzKSIgJSAoCiAgICAgICAgICAgICAgICAgICAgICAgICIvIi5qb2luKCIl
LjJmIiAlIHAgZm9yIHAgaW4gcGFzYWRhcyksCiAgICAgICAgICAgICAgICAgICAgICAgIG1heChw
YXNhZGFzKSAvIG1pbihwYXNhZGFzKSwKICAgICAgICAgICAgICAgICAgICAgICAgIjsgT1VUTElF
UiAtPiBjb25maXJtYXIgY29uIG1lZGlhbmEgZGUgMyIKICAgICAgICAgICAgICAgICAgICAgICAg
aWYgbWF4KHBhc2FkYXMpIC8gbWluKHBhc2FkYXMpID4gMS4wOCBlbHNlICIiKQogICAgICAgICAg
ICBleGNlcHQgKFR5cGVFcnJvciwgVmFsdWVFcnJvcik6CiAgICAgICAgICAgICAgICBwYXNzCiAg
ICAgICAgICAgIG1kLmFwcGVuZCgiLSAlczogJXMgdC9zIHZzIGNvbnRyb2wgJXMgLT4gJXMlcyIK
ICAgICAgICAgICAgICAgICAgICAgICUgKHJbIm5vbWJyZSJdLCBmbXQoclsiZGVjb2RlX3RzIl0p
LAogICAgICAgICAgICAgICAgICAgICAgICAgZm10KG1lY19jdHJsWyJkZWNvZGVfdHMiXSksIHZl
cmVkaWN0bywgZXh0cmEpKQogICAgICAgIG1kLmFwcGVuZCgiIikKICAgIG1kLmFwcGVuZCgiIyMg
NC4gUmVjdWVyZG9zIGRlIGxhIGNhc2EgYXBsaWNhZG9zIikKICAgIG1kLmFwcGVuZCgiIikKICAg
IG1kLmFwcGVuZCgiLSBhcHJlbmRpZG8gU1MyIChNRUMgdmVuZW5vIGVuIGxhIGJhc2UgdmllamEp
OiBhcXVpIE1FQyBjb3JyZSAiCiAgICAgICAgICAgICAgIlNPTE8gc29icmUgTkNNMzdDNCBjb24g
Y29udHJvbCBELU1FQy0wIGVuIGxhIE1JU01BIHNlc2lvbjsgc2kgIgogICAgICAgICAgICAgICJw
aWVyZGUsIHNlIGRlc2NhcnRhLiBMYSBkb3NpcyAyNTYgTWlCIG5pIHNlIHBydWViYSAoeWEgbWVk
aWRhKS4iKQogICAgbWQuYXBwZW5kKCItIGFwcmVuZGlkbyBTUzg6IDQgcGFzYWRhcyB4IDI1NiB0
b2tlbnMsIHNlIGRlc2NhcnRhIGxhIDFhLCAiCiAgICAgICAgICAgICAgInRlbXAgMCwgcHJvbXB0
cyBkaXN0aW50b3M7IHJ1aWRvIGRlY2xhcmFkbyArLy0wLjMtMC41IHQvczsgIgogICAgICAgICAg
ICAgICJkZWx0YXMgPDVwcCBubyBzZSBwZXJzaWd1ZW4gc2luIG1lZGlhbmEgZGUgMyBjb3JyaWRh
cy4iKQogICAgbWQuYXBwZW5kKCItIFNhbml0eSBtYW51YWwgZGUgMjAgcHJvbXB0cyAoMTAgY2hh
dCBFUywgNSBjb2RpZ28sICIKICAgICAgICAgICAgICAiNSB0b29sLWNhbGxpbmcpIFBFTkRJRU5U
RSBkZWwgRGlyZWN0b3IgcGFyYSBmaWphciBrIG9wZXJhdGl2byAiCiAgICAgICAgICAgICAgIihs
YSBhdXRvIGRlIDMgcGFyZXMgc29sbyBlcyBodW1vLWRldGVjdG9yKS4iKQogICAgbWQuYXBwZW5k
KCIiKQogICAgbWQuYXBwZW5kKCIjIyA1LiBBcmNoaXZvcyBkZSBlc3RhIGNvcnJpZGEiKQogICAg
bWQuYXBwZW5kKCIiKQogICAgbWQuYXBwZW5kKCItIENTVjogYGZhc2VELU4xLXJlc3VsdGFkb3Mu
Y3N2YCAocmVhbnVkYWJsZSkiKQogICAgbWQuYXBwZW5kKCItIERhdG9zOiBgZmFzZUQtTjEtZGF0
b3MuanNvbmAiKQogICAgbWQuYXBwZW5kKCItIENvbnNvbGE6IGBmYXNlRC1OMS1jb25zb2xhLmxv
Z2AiKQogICAgbWQuYXBwZW5kKCItIExvZ3MgZGVsIHNlcnZlcjogYGxvZ3MtY29uZmlnL05OLW5v
bWJyZS5sb2dgIikKICAgIG1kLmFwcGVuZCgiIikKICAgIHJ1dGFfbWQgPSBvcy5wYXRoLmpvaW4o
ZGlyX2xvZ3MsICJmYXNlRC1OMS1JTkZPUk1FLm1kIikKICAgIG9wZW4ocnV0YV9tZCwgInciLCBl
bmNvZGluZz0idXRmLTgiKS53cml0ZSgiXG4iLmpvaW4obWQpICsgIlxuIikKCiAgICBkYXRvc19q
c29uID0geyJ2ZXJzaW9uIjogVkVSU0lPTiwgInByb3RvIjogUFJPVE8sICJmZWNoYSI6IGFob3Jh
KCksCiAgICAgICAgICAgICAgICAgICJjb250ZXh0byI6IHtrOiB2IGZvciBrLCB2IGluIGNvbnRl
eHRvLml0ZW1zKCkKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGlmIGsgbm90IGluICgi
dGVlIiwpfSwKICAgICAgICAgICAgICAgICAgInJ1bnMiOiBsaXN0KGNvbXBsZXRvcy52YWx1ZXMo
KSl9CiAgICBvcGVuKG9zLnBhdGguam9pbihkaXJfbG9ncywgImZhc2VELU4xLWRhdG9zLmpzb24i
KSwgInciLAogICAgICAgICBlbmNvZGluZz0idXRmLTgiKS53cml0ZShqc29uLmR1bXBzKGRhdG9z
X2pzb24sIGVuc3VyZV9hc2NpaT1GYWxzZSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICBpbmRlbnQ9MSwgZGVmYXVsdD1zdHIpKQogICAgcmV0dXJuIHJ1dGFfbWQK
CgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBtYWluIC0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KZGVmIG1haW4oYXJndj1Ob25lKToKICAgIGdsb2JhbCBQ
VUVSVE9fREVGCiAgICBhcCA9IGFyZ3BhcnNlLkFyZ3VtZW50UGFyc2VyKAogICAgICAgIGRlc2Ny
aXB0aW9uPVZFUlNJT04gKyAiIOKAlCBmYXNlIEQgZGVsIG5pdmVsIDEgKGV4cGVydG9zICsgTUVD
KSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tcXVpY2siLCBhY3Rpb249InN0b3JlX3RydWUiLAog
ICAgICAgICAgICAgICAgICAgIGhlbHA9InNvbG8gNyBjb25maWdzIGNyaXRpY2FzICh+MjUgbWlu
KSIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tc29sbyIsIHR5cGU9c3RyLCBkZWZhdWx0PSIiLAog
ICAgICAgICAgICAgICAgICAgIGhlbHA9ImJsb3F1ZXMgc2VwYXJhZG9zIHBvciBjb21hOiAiCiAg
ICAgICAgICAgICAgICAgICAgICAgICAiZXhwLHViMWssbWVjLGNvbWJvLGNvbWJvMixvdCxhbmNs
YWZpbiIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tZXh0cmEtayIsIHR5cGU9c3RyLCBkZWZhdWx0
PSIiLAogICAgICAgICAgICAgICAgICAgIGhlbHA9ImRvc2lzIGsgZXh0cmEgcGFyYSBlbCBibG9x
dWUgRVhQLCBwLmVqLiA5LDciKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXNlcnZlciIsIHR5cGU9
c3RyLCBkZWZhdWx0PVJVVEFfU0VSVkVSX0RFRikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1tb2Rl
bG8iLCB0eXBlPXN0ciwgZGVmYXVsdD1SVVRBX01PREVMT19ERUYpCiAgICBhcC5hZGRfYXJndW1l
bnQoIi0tbG9ncyIsIHR5cGU9c3RyLCBkZWZhdWx0PUxPR1NfRElSX0RFRikKICAgIGFwLmFkZF9h
cmd1bWVudCgiLS1wdWVydG8iLCB0eXBlPWludCwgZGVmYXVsdD1QVUVSVE9fREVGKQogICAgYXAu
YWRkX2FyZ3VtZW50KCItLWNhcmdhLXRpbWVvdXQiLCB0eXBlPWludCwgZGVmYXVsdD02MDApCiAg
ICBhcC5hZGRfYXJndW1lbnQoIi0tc2kiLCBhY3Rpb249InN0b3JlX3RydWUiLAogICAgICAgICAg
ICAgICAgICAgIGhlbHA9Im1hdGFyIHVuIHNlcnZlciB2aXZvIGFudGVzIGRlIGVtcGV6YXIiKQog
ICAgYXAuYWRkX2FyZ3VtZW50KCItLXNpbi1zYW5pdHkiLCBhY3Rpb249InN0b3JlX3RydWUiKQog
ICAgYXAuYWRkX2FyZ3VtZW50KCItLXNpbi1udmlkaWEiLCBhY3Rpb249InN0b3JlX3RydWUiKQog
ICAgYXAuYWRkX2FyZ3VtZW50KCItLXNpbi1wYXVzYXMiLCBhY3Rpb249InN0b3JlX3RydWUiKQog
ICAgYXJncyA9IGFwLnBhcnNlX2FyZ3MoYXJndikKCiAgICBQVUVSVE9fREVGID0gYXJncy5wdWVy
dG8KICAgICMgdjEuMSBDQVVTQSBSQUlaIGRlbCBIVFRQIDQwMDogYW50ZXMgZWwgc2VydmVyIHNl
IGxhbnphYmEgY29uIGVsIGRpZmYgZGUKICAgICMgbGEgY29uZmlnIGEgc2VjYXMgKHNpbiAtbSwg
c2luIC0tcG9ydCwgc2luIC1jLCBzaW4gLWZhKS4gQWhvcmEgbGEgYmFzZQogICAgIyBTSUVNUFJF
IGxsZXZhIGVsIG1vZGVsbyB5IHRvZG9zIGxvcyBmbGFncyBmaWpvcyBkZWwgcHJvdG9jb2xvLgog
ICAgYmFzZV9mbGFncyA9IFsiLW0iLCBhcmdzLm1vZGVsb10gKyBsaXN0KEJBU0VfRkxBR1NfRklK
QVMpCiAgICBmb3IgaSwgdG9rIGluIGVudW1lcmF0ZShiYXNlX2ZsYWdzKToKICAgICAgICBpZiB0
b2sgPT0gIi0tcG9ydCIgYW5kIGkgKyAxIDwgbGVuKGJhc2VfZmxhZ3MpOgogICAgICAgICAgICBi
YXNlX2ZsYWdzW2kgKyAxXSA9IHN0cihhcmdzLnB1ZXJ0bykKCiAgICB0cnk6CiAgICAgICAgc3lz
LnN0ZG91dC5yZWNvbmZpZ3VyZShlbmNvZGluZz0idXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiKQog
ICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICBwYXNzCiAgICBpZiBvcy5uYW1lID09ICJudCI6
CiAgICAgICAgdHJ5OgogICAgICAgICAgICBvcy5zeXN0ZW0oIiIpICAjIGhhYmlsaXRhIGNvZGln
b3MgVlQvQU5TSSBlbiBsYSBjb25zb2xhIFdpbmRvd3MKICAgICAgICBleGNlcHQgRXhjZXB0aW9u
OgogICAgICAgICAgICBwYXNzCgogICAgb3MubWFrZWRpcnMoYXJncy5sb2dzLCBleGlzdF9vaz1U
cnVlKQogICAgb3MubWFrZWRpcnMob3MucGF0aC5qb2luKGFyZ3MubG9ncywgImxvZ3MtY29uZmln
IiksIGV4aXN0X29rPVRydWUpCiAgICB0ZWUgPSBUZWUob3MucGF0aC5qb2luKGFyZ3MubG9ncywg
ImZhc2VELU4xLWNvbnNvbGEubG9nIikpCiAgICBzeXMuc3Rkb3V0ID0gdGVlICAjIHRvZGEgbGEg
Y29uc29sYSBxdWVkYSBjb3BpYWRhIGFsIGxvZwogICAgc3lzLnN0ZGVyciA9IHRlZSAgIyB2MS4x
OiBsb3MgdHJhY2ViYWNrcyBUQU1CSUVOIHZhbiBhbCBsb2cKCiAgICBwcmludChncmF5KCI9IiAq
IDc4KSkKICAgIHByaW50KGJvbGQoVkVSU0lPTikpCiAgICBwcmludChncmF5KCI9IiAqIDc4KSkK
ICAgIHByaW50KCIgIHNlcnZlciA6ICVzIiAlIGFyZ3Muc2VydmVyKQogICAgcHJpbnQoIiAgbW9k
ZWxvIDogJXMiICUgYXJncy5tb2RlbG8pCiAgICBwcmludCgiICBsb2dzICAgOiAlcyIgJSBhcmdz
LmxvZ3MpCiAgICBwcmludCgiICBwdWVydG8gOiAlZCIgJSBhcmdzLnB1ZXJ0bykKCiAgICAjIC0t
LS0gMC4gcHJlLXZ1ZWxvIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLQogICAgaWYgbm90IG9zLnBhdGguZXhpc3RzKGFyZ3Muc2VydmVyKToKICAg
ICAgICByYWlzZSBTeXN0ZW1FeGl0KHJlZCgiRkFUQUw6IG5vIGV4aXN0ZSBlbCBzZXJ2ZXI6ICVz
IiAlIGFyZ3Muc2VydmVyKSkKICAgIGlmIG5vdCBvcy5wYXRoLmV4aXN0cyhhcmdzLm1vZGVsbyk6
CiAgICAgICAgcmFpc2UgU3lzdGVtRXhpdChyZWQoIkZBVEFMOiBubyBleGlzdGUgZWwgbW9kZWxv
OiAlcyIgJSBhcmdzLm1vZGVsbykpCiAgICBpZiBub3Qgb3MucGF0aC5leGlzdHMoUlVUQV9EVU1Q
X0RFRik6CiAgICAgICAgcmFpc2UgU3lzdGVtRXhpdChyZWQoIkZBVEFMOiBubyBleGlzdGUgZWwg
ZHVtcCBkZSBmbGFnczogJXMgKGVsIHNjcmlwdCAiCiAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgIk5PIGFycmFuY2Egc2luIHN1IGZ1ZW50ZSBkZSB2ZXJkYWQpIiAlIFJVVEFfRFVNUF9ERUYp
KQoKICAgIGJ5dGVzX21vZGVsbyA9IG9zLnBhdGguZ2V0c2l6ZShhcmdzLm1vZGVsbykKICAgIGlm
IGJ5dGVzX21vZGVsbyAhPSBCWVRFU19NT0RFTE9fRVNQRVJBRE9TOgogICAgICAgIHByaW50KHll
bGxvdygiICBBVklTTzogZWwgbW9kZWxvIG1pZGUgJWQgQiB5IFJ1dGFzQXJjaGl2b3MgZGljZSAl
ZCBCICIKICAgICAgICAgICAgICAgICAgICAgIi0+IHZlcmlmaWNhciBxdWUgZXMgZWwgQVBFWC1J
LU1JTkkgY29ycmVjdG8iCiAgICAgICAgICAgICAgICAgICAgICUgKGJ5dGVzX21vZGVsbywgQllU
RVNfTU9ERUxPX0VTUEVSQURPUykpKQoKICAgIHBpbiA9IHZlcnNpb25fc2VydmVyKGFyZ3Muc2Vy
dmVyKQogICAgaWYgQlVJTERfUElOX0VTUEVSQURPIG5vdCBpbiBwaW46CiAgICAgICAgcHJpbnQo
eWVsbG93KCIgIEFWSVNPOiBlbCBwaW4gZGVsIHNlcnZlciBubyBtZW5jaW9uYSBidWlsZCAlczog
JXMiCiAgICAgICAgICAgICAgICAgICAgICUgKEJVSUxEX1BJTl9FU1BFUkFETywgcGluWzoxMjBd
KSkpCgogICAgcHJpbnQoY3lhbigiWzBdIFBBUlNFUiBHR1VGIChjb3JyZWNjaW9uIGRlbCBuby1v
cCBkZWwgYmFycmlkby0zMCkuLi4iKSkKICAgIHRyeToKICAgICAgICBocCA9IGdndWZfbGVlcl9o
cGFyYW1zKGFyZ3MubW9kZWxvKQogICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgIHJh
aXNlIFN5c3RlbUV4aXQocmVkKCJGQVRBTDogcGFyc2VyIEdHVUYgZmFsbG86ICVzIiAlIGUpKQog
ICAgYXJjaCA9IGhwWyJhcmNoIl0KICAgIGNsYXZlLCBfID0gX292ZXhwKGFyY2gsIDgpCiAgICBw
cmludCgiICBhcmNoID0gJXMgKEdHVUYgdiVzKSDCtyBuX2V4cGVydCA9ICVzIMK3IG5fZXhwZXJ0
X3VzZWQgPSAlcyIKICAgICAgICAgICUgKGJvbGQoYXJjaCksIGhwWyJnZ3VmX3ZlcnNpb24iXSwg
aHBbIm5fZXhwZXJ0Il0sCiAgICAgICAgICAgICBocFsibl9leHBlcnRfdXNlZCJdKSkKICAgIGlm
IGhwWyJuX2V4cGVydCJdICE9IDI1NiBvciBocFsibl9leHBlcnRfdXNlZCJdICE9IDg6CiAgICAg
ICAgcHJpbnQoeWVsbG93KCIgIEFWSVNPOiBzZSBlc3BlcmFiYW4gMjU2IGV4cGVydG9zIC8gOCB1
c2Fkb3MgKGZpY2hhICIKICAgICAgICAgICAgICAgICAgICAgIk4xIFNTMSkuIFJldmlzYXIgcXVl
IGVzdGUgZXMgZWwgR0dVRiBjb3JyZWN0by4iKSkKCiAgICBleHRyYV9rID0gW3ggZm9yIHggaW4g
YXJncy5leHRyYV9rLnNwbGl0KCIsIikgaWYgeC5zdHJpcCgpXQogICAgY29uZmlncyA9IGNvbnN0
cnVpcl9jb25maWdzKGFyY2gsIGV4dHJhX2s9ZXh0cmFfaykKICAgIGNvbmZpZ3MgPSBmaWx0cmFy
X2NvbmZpZ3MoY29uZmlncywgc29sbz1hcmdzLnNvbG8sIHF1aWNrPWFyZ3MucXVpY2spCgogICAg
cHJpbnQoY3lhbigiWzBdIEFVRElUT1JJQSBERSBGTEFHUyBjb250cmEgZWwgZHVtcCBiMTE4NTYu
Li4iKSkKICAgIHByb2JsZW1hcyA9IGF1ZGl0YXJfZmxhZ3MoUlVUQV9EVU1QX0RFRiwgY29uZmln
cywgYmFzZV9mbGFncykKICAgIGlmIHByb2JsZW1hczoKICAgICAgICBmb3IgcCBpbiBwcm9ibGVt
YXM6CiAgICAgICAgICAgIHByaW50KHJlZCgiICBGQUxMTzogJXMiICUgcCkpCiAgICAgICAgcmFp
c2UgU3lzdGVtRXhpdChyZWQoIkZBVEFMOiBsYSBhdWRpdG9yaWEgZGUgZmxhZ3MgZmFsbG8gKCVk
KS4gTmFkYSBzZSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImVqZWN1dGE6IHJldmlz
YXIgY29uZmlncyBvIHJlZ2VuZXJhciBlbCBkdW1wLiIKICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAlIGxlbihwcm9ibGVtYXMpKSkKICAgIHByaW50KGdyZWVuKCIgIFZFUkRFOiAlZCBjb25m
aWdzLCB0b2RvcyBsb3MgdG9rZW5zIHZlcmJhdGltIGVuIGVsIGR1bXAsICIKICAgICAgICAgICAg
ICAgICJjZXJvIHByb2hpYmlkYXMiICUgbGVuKGNvbmZpZ3MpKSkKCiAgICBpZiBhcmdzLnNpOgog
ICAgICAgIG1hdGFyX3NlcnZlcl92aXZvKGFyZ3MucHVlcnRvKQogICAgZWxpZiBoZWFsdGhfb2so
YXJncy5wdWVydG8pOgogICAgICAgIHJhaXNlIFN5c3RlbUV4aXQocmVkKCJGQVRBTDogL2hlYWx0
aCB5YSByZXNwb25kZSBlbiBlbCBwdWVydG8gJWQuIEhheSAiCiAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgInVuIHNlcnZlciB2aXZvIChtZWRpciBjb24gZWwgZmFsc2VhIHRvZG8pLiAiCiAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgIkNlcnJhcmxvIG8gcmVsYW56YXIgY29uIC0tc2ku
IiAlIGFyZ3MucHVlcnRvKSkKCiAgICBjb250ZXh0byA9IHsicnV0YV9zZXJ2ZXIiOiBhcmdzLnNl
cnZlciwgInJ1dGFfbW9kZWxvIjogYXJncy5tb2RlbG8sCiAgICAgICAgICAgICAgICAiZGlyX2xv
Z3MiOiBhcmdzLmxvZ3MsICJwaW4iOiBwaW4sCiAgICAgICAgICAgICAgICAiYnl0ZXNfbW9kZWxv
IjogYnl0ZXNfbW9kZWxvLCAiaHBhcmFtcyI6IGhwLAogICAgICAgICAgICAgICAgImFyY2hfZ2d1
ZiI6IGFyY2gsICJjbGF2ZSI6IGNsYXZlLAogICAgICAgICAgICAgICAgImNhcmdhX3RpbWVvdXQi
OiBhcmdzLmNhcmdhX3RpbWVvdXQsCiAgICAgICAgICAgICAgICAiY29uX3Nhbml0eSI6IG5vdCBh
cmdzLnNpbl9zYW5pdHksCiAgICAgICAgICAgICAgICAic2luX252aWRpYSI6IGFyZ3Muc2luX252
aWRpYSwKICAgICAgICAgICAgICAgICJwdWVydG8iOiBhcmdzLnB1ZXJ0bywKICAgICAgICAgICAg
ICAgICJiYXNlX2ZsYWdzX3N0ciI6ICIgIi5qb2luKGJhc2VfZmxhZ3MpLAogICAgICAgICAgICAg
ICAgImJhc2VfZmxhZ3MiOiBiYXNlX2ZsYWdzfQoKICAgICMgLS0tLSAxLiBjb3JyaWRhIC0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCiAgICBw
cmludChjeWFuKCJbMV0gQ09SUklEQTogJWQgY29uZmlncyAocGF1c2EgdGVybWljYSA2MCBzIGNh
ZGEgOCkiCiAgICAgICAgICAgICAgICUgbGVuKGNvbmZpZ3MpKSkKICAgIHJ1dGFfY3N2ID0gY3N2
X3J1dGEoYXJncy5sb2dzKQogICAgIyB2MS4yLjE6IHNpIGVsIENTViBkZWwgZGlyZWN0b3JpbyBl
cyBkZSBPVFJPIHByb3RvLCBzZSBBUkNISVZBIChuYWRhIHNlCiAgICAjIGJvcnJhKSB5IGxhIGNv
cnJpZGEgYXJyYW5jYSBsaW1waWE6IG1lemNsYXIgcHJvdG9zIGZhbHNlYXJpYSBlbCByZXN1bWUu
CiAgICBwcm90b192aWVqbyA9IGNzdl9wcm90b19kZShydXRhX2NzdikKICAgIGlmIHByb3RvX3Zp
ZWpvIGFuZCBwcm90b192aWVqbyAhPSBQUk9UTzoKICAgICAgICBkZXN0aW5vID0gb3MucGF0aC5q
b2luKGFyZ3MubG9ncywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJmYXNlRC1OMS1y
ZXN1bHRhZG9zLSVzLmNzdiIgJSBwcm90b192aWVqbykKICAgICAgICB0cnk6CiAgICAgICAgICAg
IG9zLnJlcGxhY2UocnV0YV9jc3YsIGRlc3Rpbm8pCiAgICAgICAgICAgIHByaW50KHllbGxvdygi
ICBwcm90byBudWV2byAoJXMpOiBlbCBDU1YgJyVzJyBzZSBBUkNISVZBIGNvbW8gJXMgIgogICAg
ICAgICAgICAgICAgICAgICAgICAgIihuYWRhIHNlIGJvcnJhKTsgbGEgY29ycmlkYSBlcyBjb21w
bGV0YSIKICAgICAgICAgICAgICAgICAgICAgICAgICUgKFBST1RPLCBwcm90b192aWVqbywgb3Mu
cGF0aC5iYXNlbmFtZShkZXN0aW5vKSkpKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToK
ICAgICAgICAgICAgcHJpbnQoeWVsbG93KCIgIEFWSVNPOiBubyBwdWRlIGFyY2hpdmFyIGVsIENT
ViBkZSAlcyAoJXIpIgogICAgICAgICAgICAgICAgICAgICAgICAgJSAocHJvdG9fdmllam8sIGUp
KSkKICAgIGhlY2hvcyA9IGNzdl9jYXJnYXJfaGVjaG9zKHJ1dGFfY3N2KQogICAgcGVuZGllbnRl
cyA9IFtjIGZvciBjIGluIGNvbmZpZ3MgaWYgY1siaWQiXSBub3QgaW4gaGVjaG9zXQogICAgaWYg
bGVuKHBlbmRpZW50ZXMpIDwgbGVuKGNvbmZpZ3MpOgogICAgICAgIHByaW50KGdyYXkoIiAgcmVz
dW1lOiAlZCB5YSBtZWRpZGFzLCAlZCBwZW5kaWVudGVzIgogICAgICAgICAgICAgICAgICAgJSAo
bGVuKGNvbmZpZ3MpIC0gbGVuKHBlbmRpZW50ZXMpLCBsZW4ocGVuZGllbnRlcykpKSkKCiAgICBy
ZXN1bHRhZG9zLCBjb21wbGV0b3MgPSB7fSwge30KICAgIGZvciBjaWQsIHJvdyBpbiBoZWNob3Mu
aXRlbXMoKToKICAgICAgICB0cnk6CiAgICAgICAgICAgIGRlYyA9IGZsb2F0KHJvdy5nZXQoImRl
Y29kZV90cyIpIG9yICIiKSBvciBOb25lCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAg
ICAgICAgZGVjID0gTm9uZQogICAgICAgIHJlc3VsdGFkb3NbY2lkXSA9IGRpY3Qocm93KQogICAg
ICAgIHJlc3VsdGFkb3NbY2lkXVsiZGVjb2RlX3RzIl0gPSBkZWMKICAgICAgICBjb21wbGV0b3Nb
Y2lkXSA9IGRpY3Qocm93KQoKICAgIGhlY2hhc19zZXNpb24gPSAwCiAgICBpbnRlcnJ1bXBpZG8g
PSBGYWxzZQogICAgdHJ5OgogICAgICAgIGZvciBjZmcgaW4gY29uZmlnczoKICAgICAgICAgICAg
aWYgY2ZnWyJpZCJdIGluIGhlY2hvczoKICAgICAgICAgICAgICAgIHByaW50KGdyYXkoIiAgWyUw
MmRdICVzOiB5YSBtZWRpZGEgKHZhbGlkYSksIHNhbHRvIgogICAgICAgICAgICAgICAgICAgICAg
ICAgICAlIChjZmdbImlkIl0sIGNmZ1sibm9tYnJlIl0pKSkKICAgICAgICAgICAgICAgIGNvbnRp
bnVlCiAgICAgICAgICAgIGlmIGhlY2hhc19zZXNpb24gYW5kIGhlY2hhc19zZXNpb24gJSA4ID09
IDAgYW5kIG5vdCBhcmdzLnNpbl9wYXVzYXM6CiAgICAgICAgICAgICAgICBwcmludCh5ZWxsb3co
IiAgcGF1c2EgdGVybWljYSA2MCBzIChwcm90ZWdlIGxhIG1lZGljaW9uKS4uLiIpKQogICAgICAg
ICAgICAgICAgdGltZS5zbGVlcCg2MCkKICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAg
ZmlsYSwgY29tcGxldG8gPSBtZWRpcl9jb25maWcoY2ZnLCBjb250ZXh0bywKICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHJlc3VsdGFkb3NfcHJldj1yZXN1bHRh
ZG9zKQogICAgICAgICAgICBleGNlcHQgS2V5Ym9hcmRJbnRlcnJ1cHQ6CiAgICAgICAgICAgICAg
ICByYWlzZQogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgICAg
ICAjIHYxLjE6IHVuYSBjb25maWcgSkFNQVMgdHVtYmEgZWwgYmFycmlkbyAobGEgdjEuMCBtdXJp
byBjb24KICAgICAgICAgICAgICAgICMgdHJhY2ViYWNrIGVuIGxhIGNvbmZpZyAwMSB5IGVsIHJl
c3RvIHNlIHBlcmRpbyBlbnRlcm8pCiAgICAgICAgICAgICAgICBmaWxhID0ge2M6ICIiIGZvciBj
IGluIENPTFVNTkFTfQogICAgICAgICAgICAgICAgZmlsYS51cGRhdGUoeyJwcm90byI6IFBST1RP
LCAiaWQiOiBjZmdbImlkIl0sCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIm5vbWJyZSI6
IGNmZ1sibm9tYnJlIl0sICJmYW1pbGlhIjogY2ZnWyJmYW1pbGlhIl0sCiAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgImZlY2hhX2hvcmEiOiBhaG9yYSgpLCAidmFsaWRvIjogIk5PIiwKICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAibm90YSI6ICJleGNlcGNpb24gbm8gY2FwdHVyYWRh
OiAlciIgJSBlfSkKICAgICAgICAgICAgICAgIGNvbXBsZXRvID0geyJpZCI6IGNmZ1siaWQiXSwg
Im5vbWJyZSI6IGNmZ1sibm9tYnJlIl0sCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAiZmFt
aWxpYSI6IGNmZ1siZmFtaWxpYSJdLCAidmFsaWRvIjogRmFsc2UsCiAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAibm90YSI6IGZpbGFbIm5vdGEiXSwgImV4Y2VwY2lvbiI6IHJlcHIoZSl9CiAg
ICAgICAgICAgICAgICBwcmludChyZWQoIiAgWyUwMmRdIEVYQ0VQQ0lPTiBubyBjYXB0dXJhZGE6
ICVyIiAlIChjZmdbImlkIl0sIGUpKSkKICAgICAgICAgICAgaWYgKGNmZ1siaWQiXSAhPSAxIGFu
ZCBmaWxhLmdldCgiZGVjb2RlX3RzIikKICAgICAgICAgICAgICAgICAgICBhbmQgKHJlc3VsdGFk
b3MuZ2V0KDEpIG9yIHt9KS5nZXQoImRlY29kZV90cyIpKToKICAgICAgICAgICAgICAgICMgdjEu
MjogbGEgY29sdW1uYSBleGlzdGlhIGRlc2RlIGxhIHYxLjAgcGVybyBqYW1hcyBzZSBsbGVuYWJh
CiAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgZmlsYVsiZGVsdGFfdnNf
YW5jbGFfcGN0Il0gPSAiJS4xZiIgJSAoCiAgICAgICAgICAgICAgICAgICAgICAgIChmbG9hdChm
aWxhWyJkZWNvZGVfdHMiXSkKICAgICAgICAgICAgICAgICAgICAgICAgIC8gcmVzdWx0YWRvc1sx
XVsiZGVjb2RlX3RzIl0gLSAxLjApICogMTAwKQogICAgICAgICAgICAgICAgZXhjZXB0IChUeXBl
RXJyb3IsIFZhbHVlRXJyb3IsIFplcm9EaXZpc2lvbkVycm9yKToKICAgICAgICAgICAgICAgICAg
ICBwYXNzCiAgICAgICAgICAgIGNzdl9hcHBlbmQocnV0YV9jc3YsIGZpbGEpCiAgICAgICAgICAg
IHRyeToKICAgICAgICAgICAgICAgIGRlYyA9IGZsb2F0KGZpbGEuZ2V0KCJkZWNvZGVfdHMiKSBv
ciAiIikgb3IgTm9uZQogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICAg
ICAgZGVjID0gTm9uZQogICAgICAgICAgICByZXN1bHRhZG9zW2NmZ1siaWQiXV0gPSBkaWN0KGZp
bGEpCiAgICAgICAgICAgIHJlc3VsdGFkb3NbY2ZnWyJpZCJdXVsiZGVjb2RlX3RzIl0gPSBkZWMK
ICAgICAgICAgICAgY29tcGxldG9zW2NmZ1siaWQiXV0gPSBjb21wbGV0bwogICAgICAgICAgICBo
ZWNoYXNfc2VzaW9uICs9IDEKICAgIGV4Y2VwdCBLZXlib2FyZEludGVycnVwdDoKICAgICAgICBp
bnRlcnJ1bXBpZG8gPSBUcnVlCiAgICAgICAgcHJpbnQoeWVsbG93KCJcbiAgSU5URVJSVU1QSURP
IChDdHJsK0MpOiBndWFyZGFuZG8gaW5mb3JtZSBwYXJjaWFsOyAiCiAgICAgICAgICAgICAgICAg
ICAgICJsbyB5YSBtZWRpZG8gcXVlZGEgZW4gZWwgQ1NWIHkgc2UgcmVhbnVkYSBkZXNwdWVzLi4u
IikpCgogICAgIyAtLS0tIDIuIGluZm9ybWUgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KICAgIHByaW50KGN5YW4oIlsyXSBJTkZPUk1FLi4u
IikpCiAgICBydXRhX21kID0gZ2VuZXJhcl9pbmZvcm1lKGFyZ3MubG9ncywgY29udGV4dG8sIHJl
c3VsdGFkb3MsIGNvbXBsZXRvcywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgcHJvYmxl
bWFzKQogICAgcHJpbnQoZ3JlZW4oIiAgJXMiICUgcnV0YV9tZCkpCiAgICBwcmludChncmVlbigi
ICAlcyIgJSBydXRhX2NzdikpCiAgICBwcmludChncmVlbigiICAlcyIgJSBvcy5wYXRoLmpvaW4o
YXJncy5sb2dzLCAiZmFzZUQtTjEtZGF0b3MuanNvbiIpKSkKICAgIHByaW50KGdyZWVuKCIgICVz
IiAlIG9zLnBhdGguam9pbihhcmdzLmxvZ3MsICJmYXNlRC1OMS1jb25zb2xhLmxvZyIpKSkKICAg
IHByaW50KCIiKQogICAgcHJpbnQoYm9sZCgiUGFyYSBwYXNhciBhbCBhbmFsaXNpczogZmFzZUQt
TjEtSU5GT1JNRS5tZCArICIKICAgICAgICAgICAgICAgImZhc2VELU4xLXJlc3VsdGFkb3MuY3N2
ICgrIGNhcnBldGEgbG9ncy1jb25maWcgc2kgc2UgcGlkZSkuIikpCiAgICByZXR1cm4gMTMwIGlm
IGludGVycnVtcGlkbyBlbHNlIDAKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgc3lz
LmV4aXQobWFpbigpKQo=
"""
    ),
    "barrido-n3-eficiencia.py": (
"""
IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiIKYmFycmlk
by1uMy1lZmljaWVuY2lhLnB5IHYxLjMg4oCUIENPU0VDSEEgZGVsIE5JVkVMIDMgKGVmaWNpZW5j
aWEgc2ltcGxlKQo9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09
PT09PT09PT09PT09PT09PT09PT09PT09PQpFbmNhcmdvIGRlbCBEaXJlY3RvciAoMjgtb2N0LTIw
MjYpOiAiZGVqZW1vcyBkZSBsYWRvIGVsIGRpYWdub3N0aWNvLCBxdWUKaGFjZW1vcyIgLT4gZWwg
c2lndWllbnRlIHBhc28gZGVsIG9yZGVuIGFwcm9iYWRvIChSb25kYSAxMjogTjEgLT4gTjMgLT4g
TjIKLT4gTjQpIGVzIGNvc2VjaGFyIGxvIHF1ZSBxdWVkYSB2aXZvIGRlbCBOSVZFTCAzIGNvbiBl
bCBtZXRvZG8gZGUgbGEgY2FzYQooRVNDQUxFUkEgKyBDT05UUk9MICsgQ0VSVElGSUNBRE8gKyBH
VUFSREFSUkFJTFMgKyBJTkZPUk1FKS4KCkxvIHF1ZSBmYWx0YSBwb3IgbWVkaXIgZW4gZWwgcmln
IChuaXZlbC0zLWVmaWNpZW5jaWEtc2ltcGxlLm1kLCAiZXN0YWRvIGRlCmNvc2VjaGEiIFNTMTMg
KyBwbGFuIGRlIHBydWViYXMgcm9uZGEgMTkpOgogICgxKSBDT01CTyBHQU5BRE9SRVMganVudG9z
OiBPUk8tVUIxSyAoeWEgZW4gbGEgYmFzZSkgeCBOQ00zN0M0IHgKICAgICAgY2FjaGUtcmV1c2Uv
cmFtL2Ntcy9jdHhjcC9jb250ZXh0LXNoaWZ0IChTUzguMS9TUzExLjcpLgogICgyKSBMQSBKT1lB
OiBjYWNoZSBkZSBwcm9tcHRzIGVuIGVsIEhJQlJJRE8gKFNTMyk6IC0tY2FjaGUtcmV1c2UgMjU2
ICsKICAgICAgdmFsaWRhY2lvbiBPQkxJR0FUT1JJQSBjb24gZWwgcmVwcm8gZGUgdHVybm9zIGNy
ZWNpZW50ZXMgKGxpbmVhcwogICAgICAicmVzdG9yZWQgY29udGV4dCBjaGVja3BvaW50IiB2cyAi
Zm9yY2luZyBmdWxsIHByb21wdCByZS1wcm9jZXNzaW5nIiwKICAgICAgaXNzdWVzICMyMTgzMS8j
MjQwNTU7ICMyNDA1NSBwdWVkZSBBVVRPLURFU0hBQklMSVRBUiBsYSBjYWNoZTogZWwKICAgICAg
d2FybmluZyBkZWwgYXJyYW5xdWUgZXMgY2VydGlmaWNhZG8sIG5vIG9wY2lvbikuCiAgKDMpIGRv
c2lzIGRlIFJBTTogLS1jYWNoZS1yYW0gNTEyIChPUk8tQ1JBTTUxMiBtaWRpbyBkZWNvZGUgaW50
YWN0byB5CiAgICAgIGxpYmVyYSB+Ny43IEdCIGRlbCBkZWZhdWx0IDgxOTIpLCAtY3R4Y3AgNCAo
Y2hlY2twb2ludHMgMzItPjQ6CiAgICAgIH42MyBNQi9jaGVja3BvaW50IEdETiA9IH4yIEdCIHBv
dGVuY2lhbGVzIC0+IGxpYmVyYSB+MS41LTEuOCBHQikgeQogICAgICAtY21zIDEwMjQgKGNhZGVu
Y2lhIGRlIGNoZWNrcG9pbnRzIHBhcmEgY2hhdCBjb250aW51bykuCiAgKDQpIC1ucCAyICh0aHJv
dWdocHV0IGFncmVnYWRvICsxNCUgW00gU1M0XTsgY3R4IDE2Mzg0IHNlIHJlcGFydGU6CiAgICAg
IDgxOTIgcG9yIHNsb3Q7IFNPTE8gc2luIHNwZWMgLSBTUzExLjQgTVRQIGV4aWdlIC1ucCAxLCBh
cXVpIG5vIGhheSkuCiAgKDUpIEEvQiBjYWNoZSBPRkYgKC0tbm8tY2FjaGUtcHJvbXB0KTogY29u
dHJvbCBkZWwgcHJvdG9jb2xvIChTUzE0OiBzaQogICAgICBlbCBkZWNvZGUgZ2FuYSBwZXJvIGVs
IFRURlQgZGVsIGNoYXQgZW1wZW9yYSwgc2VwYXJhciBsb3MgZG9zIGVmZWN0b3MpLgoKTGEgQkFT
RSBkZSBlc3RhIGZhc2UgZXMgbGEgUkVDRVRBIERJQVJJQSAoY29uZmlnLnR4dCBGTEFHU19CQVNF
ICsKRkxBR1NfR0FOQURPUkFTID0gT1JPLVVCMUssIGF1ZGl0b3JpYSBSMjQpICsgLWx2IDQgcGFy
YSBxdWUgZWwgbG9nIGRlamUKbG9zIGNlcnRpZmljYWRvcyBkZSBjYWNoZS4gUG9yIGVzbyBlbCBh
bmNsYSBkZSBlc3RhIHNlc2lvbiBFUyBsYSByZWNldGEKcXVlIEFCUklSLVFXRU4uYmF0IGxhbnph
IGhveTogbG9zIGRlbHRhcyBzZSBsZWVuIGRpcmVjdG8gc29icmUgbGEgdmlkYQpyZWFsIGRlbCBE
aXJlY3RvciAobm8gc29icmUgdW4gYW5jbGEgZGUgbGFib3JhdG9yaW8pLgoKdjEuMyAoaG90Zml4
IGRlIGNhbXBvIDI4LW9jdCwgcHJpbWVyYSBjb3JyaWRhIGNvbXBsZXRhIGRlbCByaWcpOiBsYQpD
T0xPQ0FDSU9OIHZhIFBPUiBDT05GSUcgKGxlY2Npb24gYmFycmlkby1xd2VuLTMwOiBlbiBiMTE4
NTYgLWNtb2UgeQotbmNtb2UganVudG9zID0gZ2FuYSBlbCBnZW5lcmFsIHkgYW51bGEgYWwgLW5j
bW9lKS4gTGEgdjEuMiBzYWxpbyBzaW4KY29sb2NhY2lvbiBlbiAxMSBkZSAxMyBjb25maWdzOiBl
bCBjb21hbmRvIHBlZGlhIGxvcyAxNC4yNyBHQiBkZWwgbW9kZWxvCkVOIGxhIEdQVSBkZSA0IEdC
IHkgMTEgY29uZmlncyBtdXJpZXJvbiBlbiB+Mi41IHMgKGV4aXQgMSwgImZpdCBhYm9ydGFkbzoK
VlJBTSBpbnN1ZmljaWVudGUiKTsgc29sbyBzb2JyZXZpdmllcm9uIGxhcyAyIHF1ZSBsbGV2YWJh
biAtbmNtb2UgMzcuCkFob3JhOiAoYSkgY2FkYSBjb25maWcgdHJhZSBzdSBjb2xvY2FjaW9uIChB
TkNMQS9DVFJML1JBTS9DQUNIRS9TTE9UUy8KQ09NQk8tUiA9IC1jbW9lOyBOQ00zN0M0IHkgQ09N
Qk8tVCA9IC1uY21vZSAzNyB2ZXJiYXRpbSBiYXJyaWRvLTMwKTsKKGIpIENFUlRJRklDQURPIERF
IFJFQ0VUQTogZWwgYW5jbGEgREVCRSBjb250ZW5lciBsYSByZWNldGEgZGlhcmlhCmV4YWN0YSAo
Y29uZmlnLnR4dCBGTEFHU19CQVNFICsgRkxBR1NfR0FOQURPUkFTKSBvIEZBVEFMIGFudGVzIGRl
IG1lZGlyCuKAlCBsYSBhdWRpdG9yaWEgZGUgZmxhZ3MgdmUgcXVlIGNhZGEgdG9rZW4gRVhJU1RF
IGVuIGVsIGR1bXAsIHBlcm8gbm8gcXVlCmVsIGNvbWFuZG8gY29udGVuZ2EgTEEgUkVDRVRBIENP
TVBMRVRBOiBwb3IgZXNvIHBhc28gVkVSREUgeSBtdXJpbzsKKGMpIHJlZ2xhIGJhcnJpZG8tMzAg
bWF0ZXJpYWxpemFkYTogVE9EQSBjb25maWcgbmVjZXNpdGEgLWNtb2UvLW5jbW9lIG8KRkFUQUw7
IChkKSBhbmNsYSBtdWVydGEgPSBGQVRBTCBpbm1lZGlhdG8gKHNpbiBiYXNlbGluZSBubyBoYXkg
c2VzaW9uKQp5IGxhIG5vdGEgZGVsIENTViBndWFyZGEgZWwgZm9yZW5zZSBkZWwgbG9nOyAoZSkg
ZWwgcmVzdW1lIHNvbG8gY3VlbnRhCmZpbGFzIHZhbGlkYXMgKHlhIGVyYSBhc2kpOiByZS1jb3Bp
YXIgeSByZXBldGlyIGVsIGNvbWFuZG8gcmUtbWlkZSBzb2xhcwpsYXMgY29uZmlncyBtdWVydGFz
LgoKQ0VSVElGSUNBRE9TIGRlIGVzdGUgYmFycmlkbyAodW4ga25vYiBzaW4gY2VydGlmaWNhZG8g
PSBuby1vcCBzb3NwZWNob3NvKToKICAtIENBQ0hFOiBsaW5lYXMgZGUgbG9nIChTUzMuMy9TUzEw
LjMpOiB3YXJuaW5nICJjYWNoZV9yZXVzZSBpcyBub3QKICAgIHN1cHBvcnRlZCIgPSBOTy1TT1BP
UlRBRE87ICJyZXN0b3JlZCBjb250ZXh0IGNoZWNrcG9pbnQiID0gU0FOTzsKICAgICJmb3JjaW5n
IGZ1bGwgcHJvbXB0IHJlLXByb2Nlc3NpbmciID0gUk9UTyAoaGlicmlkbyAjMjE4MzEpLgogIC0g
VFRGVDogcmVwcm8gZGUgNiB0dXJub3MgY3JlY2llbnRlcyBjb24gc3RyZWFtOnRydWUgKHByb3h5
IGRlCiAgICB0aW1lX3N0YXJ0dHJhbnNmZXIsIFNTMy4zL1NTMTMpOiBQTEFOTyA9IGVsIGNhY2hl
IHRyYWJhamE7IENSRUNFID0KICAgIGNhZGEgdHVybm8gcmUtcGFnYSBlbCBwcm9tcHQuIE4zLU5P
Q0FDSEUgZXMgZWwgY29udHJvbCBxdWUgREVCRSBjcmVjZXIuCiAgLSBSQU06IFJBTSBsaWJyZSBk
ZWwgc2lzdGVtYSAoR2xvYmFsTWVtb3J5U3RhdHVzRXgpICsgV29ya2luZ1NldCBkZWwKICAgIHBy
b2Nlc28gKEdldC1DaW1JbnN0YW5jZSkgYW50ZXMvZGVzcHVlczogZWwgY2VydGlmaWNhZG8gZGUg
Q1JBTTUxMgogICAgKC03LjcgR0IgZXNwZXJhZG8pIHkgZGUgQ1RYQ1A0ICgtMS41LTEuOCBHQiBl
c3BlcmFkbykuCiAgLSBBR1JFR0FETzogcHJvYmUgY29uY3VycmVudGUgZGUgMiBwZWRpZG9zIHNp
bXVsdGFuZW9zIChlbCArMTQlIGRlIC1ucCAyCiAgICBzb2xvIGFwYXJlY2UgY29uIGNvbmN1cnJl
bmNpYSByZWFsKS4KICAtIHN5c3RlbV9pbmZvIGRlbCBhcnJhbnF1ZTogVVNFX0dSQVBIUyA9IDEg
fCBSRVBBQ0sgPSAxIChTUzExLjYsIGdyYXRpcykuCgpSZWdsYXMgZGUgbGEgY2FzYSByZXNwZXRh
ZGFzIChhcHJlbmRpZG8ubWQgKyBwcm90b2NvbG8gU1M4L1NTMTMpOgogIC0gQXVkaXRvcmlhIGRl
IGZsYWdzIEFOVEVTIGRlIGFycmFuY2FyOiBjYWRhIHRva2VuIHZlcmJhdGltIGNvbnRyYSBlbAog
ICAgZHVtcCBiMTE4NTYgKGZ1ZW50ZSBkZSB2ZXJkYWQgIzEpLiBGYWx0YSB1bm8gLT4gRkFUQUws
IG5hZGEgc2UgdG9jYS4KICAtIFBST0hJQklEQVMgYWJvcnRhbjogLS1tbG9jaywgLW5rdm8sIC11
YiA1MTIsIC0tc3BlYy0qIChhcXVpIE5PIGhheQogICAgc3BlYyksIGZsYWdzIG11ZXJ0YXMgKC0t
bm8tbW1hcC8tZGlvLy0tamluamEvLWR0KS4KICAtIFByb3RvY29sbyBTUzg6IDQgcGFzYWRhcyB4
IDI1NiB0b2tlbnMsIHByb21wdHMgZGlzdGludG9zIG1pc21hIGZhbWlsaWEsCiAgICB0ZW1wIDAs
IHNlZWQgZmlqYSwgY2FjaGVfcHJvbXB0LCBzZSBkZXNjYXJ0YSBsYSAxYSAocHJlZmlsbCA9IHBh
c2FkYSAxCiAgICBmcmlhLCBkZWNvZGUgPSBtZWRpYSAyLTQpLCBwYXVzYXMgdGVybWljYXMgNjAg
cyBjYWRhIDggY29uZmlncywgQ1NWCiAgICByZWFudWRhYmxlLCBydWlkbyBkZWNsYXJhZG8gKy8t
MC4zLTAuNSB0L3MuCiAgLSBFc3R1ZGlvIHRoYzEwMDYgdjQgKFNTMTMpOiBlbCBtaXNtbyBjb25m
aWcgYWJhcmNhIDkuNCBwcCBlbnRyZSBjb3JyaWRhcwogICAgLT4gbWVkaWFuYSBkZSAzIGNvcnJp
ZGFzIHBhcmEgbGFzIGNlbGRhcyBjbGF2ZSBBTlRFUyBkZSBwcm9jbGFtYXIgdW5hCiAgICBnYW5h
bmNpYTsgbnVuY2EgY29tcGFyYXIgY29udHJhIGVsIGFuY2xhIGRlIE9UUkEgc2VzaW9uOyBkZWx0
YXMgPDVwcCBubwogICAgc2UgcGVyc2lndWVuLgogIC0gU2FuaXR5IGF1dG9tYXRpY2EgZGUgMyBw
YXJlcyAodGVtcCAwKTogaHVtby1kZXRlY3Rvci4gTGEgcHVlcnRhIGRlCiAgICBjYWxpZGFkIENP
TVBMRVRBIHNpZ3VlIHNpZW5kbyBsYSBzYW5pdHkgbWFudWFsIGRlIDIwIHByb21wdHMuCiAgLSBH
dWFyZGFycmFpbDogQUJPUlRBIHNpIC9oZWFsdGggeWEgcmVzcG9uZGUgKC0tc2kgbG8gbWF0YSku
IFZSQU0gPjM3MDAKICAgIE1pQiA9IGF2aXNvIChzeXNtZW0gZmFsbGJhY2spLgogIC0gRWwgbGli
cm8gZGUgbXVlcnRvcyBkZWwgTjMgTk8gc2UgcmUtbWlkZTogbmdyYW0gc3BlYyAoYWNjZXB0YW5j
ZSAwLjAwKSwKICAgIGFmaW5pZGFkICgtOS4uLTM4JSksIEZJVC1DICgtMzglKSwgcmVwYWNrIG9m
ZiAoLTUlKSwgS1YgcTVfMSAoMCUpLAogICAgUE9MTCAocnVpZG8pLCBUQjggKG11ZXJ0bykuCgpT
YWxpZGFzIChjYXJwZXRhIGRlIGxvZ3MsIGRlZmF1bHQgRDpcXFpMaWFcXGZhc2VELWxvZ3MpOgog
IGZhc2VOMy1JTkZPUk1FLm1kICAgICA8LSBpbmZvcm1lIHBhcmEgcGFzYXIgYWwgRGlyZWN0b3Iv
TEFJQQogIGZhc2VOMy1yZXN1bHRhZG9zLmNzdiA8LSBDU1YgY3Jhc2gtc2FmZSByZWFudWRhYmxl
CiAgZmFzZU4zLWRhdG9zLmpzb24gICAgIDwtIGRhdG9zIGNydWRvcyBjb21wbGV0b3MKICBmYXNl
TjMtY29uc29sYS5sb2cgICAgPC0gY29waWEgZGUgdG9kYSBsYSBjb25zb2xhCiAgbG9ncy1jb25m
aWdcXE5OLU5PTUJSRS5sb2cgPC0gc3Rkb3V0K3N0ZGVyciBkZWwgc2VydmVyIHBvciBjb25maWcK
ClVzbzoKICBweSBiYXJyaWRvLW4zLWVmaWNpZW5jaWEucHkgICAgICAgICAgICAtPiAxMyBjb25m
aWdzICh+MzUtNDUgbWluKQogIHB5IGJhcnJpZG8tbjMtZWZpY2llbmNpYS5weSAtLXF1aWNrICAg
IC0+IDUgY29uZmlncyBjcml0aWNhcyAofjE4IG1pbikKICBweSBiYXJyaWRvLW4zLWVmaWNpZW5j
aWEucHkgLS1zb2xvIHJhbSAgICAgICAgKENSQU01MTIvQ1RYQ1A0L0NNUzEwMjQpCiAgcHkgYmFy
cmlkby1uMy1lZmljaWVuY2lhLnB5IC0tc29sbyBjYWNoZSAgICAgIChSRVVTRS9TSElGVCkKICBw
eSBiYXJyaWRvLW4zLWVmaWNpZW5jaWEucHkgLS1zb2xvIGNvbWJvICAgICAgKENPTUJPLVIvQ09N
Qk8tVC9OUDItQykKICBweSBiYXJyaWRvLW4zLWVmaWNpZW5jaWEucHkgLS1zb2xvIGFuY2xhLGNh
Y2hlLGNvbWJvLGFuY2xhZmluCiAgcHkgYmFycmlkby1uMy1lZmljaWVuY2lhLnB5IC0tc2luLXR0
ZnQgIC0+IHNhbHRhIGVsIHJlcHJvIGRlIHR1cm5vcwogIHB5IGJhcnJpZG8tbjMtZWZpY2llbmNp
YS5weSAtLXNpICAgICAgICAtPiBtYXRhIHVuIHNlcnZlciB2aXZvIHkgc2lndWUKICBweSBiYXJy
aWRvLW4zLWVmaWNpZW5jaWEucHkgLS1zaW4tcHJldnVlbG8gIC0+IG9taXRlIGVsIGRvc3NpZXIg
UEMvbW9kZWxvL25pdmVsCiAgcHkgYmFycmlkby1uMy1lZmljaWVuY2lhLnB5IC0tc2luLXNoYTI1
NiAgICAtPiBwcmV2dWVsbyBzaW4gZWwgaGFzaCBkZWwgbW9kZWxvCgpQUkVWVUVMTyBDT01QTEVU
TyAodjEuMSwgcGVkaWRvIERpcmVjdG9yICd0b2RvIGxvIHF1ZSBoYXlhIHF1ZSBzYWJlciBzb2Jy
ZSBtaQpQQywgZWwgbW9kZWxvIHkgZWwgbml2ZWwgYW50ZXMgZGUgY29tZW56YXInKTogYW50ZXMg
ZGUgbWVkaXIgQU5ZIGNvbmZpZywgZWwKYmFycmlkbyBlc2NyaWJlIGVuIGVsIGluZm9ybWUgbGEg
c2VjY2lvbiAwIGNvbiAoMC4xKSBlbCBoYXJkd2FyZSBkZWwgZGlhIChTTywKQ1BVLCBSQU0gcG9y
IG1vZHVsbywgcGFnZWZpbGUsIGRpc2NvcywgR1BVICsgZHJpdmVyLCBwbGFuIGRlIGVuZXJnaWEs
IHVwdGltZSwKdG9wIHByb2Nlc29zIGRlIFJBTSksICgwLjIpIGxhIGlkZW50aWRhZCBjZXJ0aWZp
Y2FkYSBkZWwgbW9kZWxvIChieXRlcywgU0hBMjU2LAptZXRhZGF0b3MgR0dVRjogYXJjaCwgZXhw
ZXJ0b3MgZGUgZmFicmljYSwgY29udGV4dG8sIGJsb2NrcywgbmV4dG4vTVRQKSB5IGxhCnZlcnNp
b24vcGluIGRlbCBzZXJ2ZXIsICgwLjMpIGxhIHJlY2V0YSB2aXZhICsgYXVkaXRvcmlhIGRlIGZs
YWdzLCAoMC40KSBlbAplc3RhZG8gZGVsIG5pdmVsIE4zIChyZWZlcmVuY2lhcyBbTV0sIGxpYnJv
IGRlIG11ZXJ0b3MsIHBlbmRpZW50ZXMgcXVlIGNvc2VjaGEsCnByb3RvY29sbyBkZSBkZWNpc2lv
bikgeSBsYSBjYW1wYW5hIGNvbXBsZXRhLCAoMC41KSBlbCBkaWEgKHJlY29yZGF0b3JpbyBSMjg6
ClJBTSBhbCA5NyUpLiBUb2RvIE5PLUZBVEFMIChwaWV6YXMgV2luZG93cyBhdXNlbnRlcyAtPiBu
b3RhLCBudW5jYSBjcmFzaCkuCgpQUk9NT0NJT046IGVsIGluZm9ybWUgZW1pdGUgImNhbmRpZGF0
YXMgYSBjb25maWcudHh0IiBjb24gc3UgY2VydGlmaWNhZG87CmxhIHByb21vY2lvbiBmb3JtYWwg
bGEgYXBydWViYSBlbCBEaXJlY3RvciBlZGl0YW5kbyBVTkEgbGluZWEgZGUgY29uZmlnLnR4dAoo
cGFnbyBkZWwgY29uZmlnIGNlbnRyYWwsIHJvbmRhIDIwKS4gU2kgbGEgY2FjaGUgc2FsZSBST1RP
IG8gTk8tU09QT1JUQURPCmVuIGIxMTg1NiwgZWwgbW90aXZvIGRlIFJVVEEgMCAoYnVpbGQgbnVl
dm8pIHF1ZWRhIHJlZ2lzdHJhZG8gY29uIGVsIGRhdG8uCiIiIgppbXBvcnQgYXJncGFyc2UKaW1w
b3J0IGNzdgppbXBvcnQgZGF0ZXRpbWUKaW1wb3J0IGhhc2hsaWIKaW1wb3J0IGpzb24KaW1wb3J0
IG9zCmltcG9ydCByZQppbXBvcnQgc3RydWN0CmltcG9ydCBzdWJwcm9jZXNzCmltcG9ydCBzeXMK
aW1wb3J0IHRocmVhZGluZwppbXBvcnQgdGltZQppbXBvcnQgdXJsbGliLmVycm9yCmltcG9ydCB1
cmxsaWIucmVxdWVzdAoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIGNvbnN0YW50ZXMgZGVs
IHJpZyAoUnV0YXNBcmNoaXZvcy5tZCkgLS0tLS0tLS0tLS0tClZFUlNJT04gPSAiYmFycmlkby1u
My1lZmljaWVuY2lhIHYxLjMgKDIwMjYtMTAtMjgsIGhvdGZpeCBkZSBjYW1wbyAyOiBjb2xvY2Fj
aW9uIHBvciBjb25maWcgKyBjZXJ0aWZpY2FkbyBkZSByZWNldGEgKyBhbmNsYS1tdWVydGE9RkFU
QUw7IDExIGNvbmZpZ3MgbXVyaWVyb24gc2luIC1jbW9lIGVuIGxhIDFhIGNvcnJpZGEgY29tcGxl
dGEpIgpQUk9UTyA9ICJmYXNlTjMtdjEiCgpSVVRBX1NFUlZFUl9ERUYgPSByIkQ6XGxsYW1hLmNw
cFxsbGFtYS1zZXJ2ZXIuZXhlIgpSVVRBX01PREVMT19ERUYgPSAociJEOlxaTGlhXG1vZGVscyIK
ICAgICAgICAgICAgICAgICAgIHIiXFF3ZW4zLjYtMzVCLUEzQi11bmNlbnNvcmVkLWhlcmV0aWMt
TmF0aXZlLU1UUC1QcmVzZXJ2ZWQtQVBFWC1JLU1JTkkuZ2d1ZiIpCl9TQ1JJUFRfRElSID0gb3Mu
cGF0aC5kaXJuYW1lKG9zLnBhdGguYWJzcGF0aChfX2ZpbGVfXykpClJVVEFfRFVNUF9ERUYgPSBv
cy5wYXRoLmpvaW4oX1NDUklQVF9ESVIsICJsbGFtYS1mbGFncy1udWV2by50eHQiKQppZiBub3Qg
b3MucGF0aC5leGlzdHMoUlVUQV9EVU1QX0RFRik6ICAgIyBSb25kYSAyMTogbGF5b3V0IGRlbCBy
ZXBvCiAgICBfZHVtcF9yZXBvID0gb3MucGF0aC5qb2luKF9TQ1JJUFRfRElSLCAiLi4iLCAiY29u
ZmlncyIsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJsbGFtYS1mbGFncy1udWV2by50
eHQiKQogICAgaWYgb3MucGF0aC5leGlzdHMoX2R1bXBfcmVwbyk6CiAgICAgICAgUlVUQV9EVU1Q
X0RFRiA9IF9kdW1wX3JlcG8KTE9HU19ESVJfREVGID0gciJEOlxaTGlhXGZhc2VELWxvZ3MiCgpB
TElBUyA9ICJhcGV4MzViIgpIT1NUX0RFRiA9ICIxMjcuMC4wLjEiClBVRVJUT19ERUYgPSA5OTMx
CkJZVEVTX01PREVMT19FU1BFUkFET1MgPSAxNDI3MzI3NzM3NiAgIyBSdXRhc0FyY2hpdm9zLm1k
IC8gZmxhZ3MtdmVyaWZpY2FkYXMKQlVJTERfUElOX0VTUEVSQURPID0gIjExODU2IiAgICAgICAg
ICAjIDAuNy4wLWRldiAoYnVpbGQgMTE4NTYsIGNvbW1pdCAzNjQyMjM4Y2MpCgojIFJlZmVyZW5j
aWFzIGhpc3RvcmljYXMgW01dIChiYXJyaWRvLTMwLCAyNS8yNi1vY3QtMjAyNikKQU5DTEFfVUIx
SyA9IDIxLjUzICAgICAjIGlkIDMyIE9STy1VQjFLIChkZWNvZGUpID0gcmVjZXRhIGRpYXJpYQpO
Q00zN0M0X1JFRiA9IDIyLjQ5ICAgICMgaWQgMTQgTkNNMzdDNCAoZGVjb2RlLCArNC40JSkg4oCU
IFNJTiBVQjFLIGVuY2ltYQpDUkFNNTEyX1JFRiA9IDIxLjU3ICAgICMgT1JPLUNSQU01MTI6IGRl
Y29kZSBpbnRhY3RvLCAtNy43IEdCIFJBTSBkZSBjYWNoZQpTSElGVF9SRUYgPSAyMS4zOSAgICAg
ICMgT1JPLVNISUZUOiAtLWNvbnRleHQtc2hpZnQgLS1jYWNoZS1yZXVzZSAyNTYgc2luIGNvc3Rl
ClRFQ0hPX1JVSURPID0gMC41ICAgICAgIyBhcHJlbmRpZG8gU1M4OiArLy0wLjMtMC41IHQvcyAt
PiB6b25hIG11ZXJ0YQoKIyBCQVNFX0ZMQUdTID0gbGEgUkVDRVRBIERJQVJJQSBtYXRlcmlhbGl6
YWRhIChjb25maWcudHh0IEZMQUdTX0JBU0UgY29uCiMgLWIvLXViIHBpc2Fkb3MgcG9yIEZMQUdT
X0dBTkFET1JBUyA9IE9STy1VQjFLLCBsYXN0LXdpbnMpICsgLWx2IDQgcGFyYSBsb3MKIyBjZXJ0
aWZpY2Fkb3MgZGUgY2FjaGUgZW4gZWwgbG9nLiBBdWRpdG9yaWEgUjI0OiBjb21hbmRvIGlkZW50
aWNvIGFsIHF1ZQojIGxhbnphbiBsb3MgLmJhdCAoc2Fsdm8gLWx2IDQsIHNvbG8gbG9nOyBOTyB0
b2NhIGxhIG1lZGljaW9uKS4KQkFTRV9GTEFHU19GSUpBUyA9IFsKICAgICItbmdsIiwgIjk5IiwK
ICAgICItYyIsICIxNjM4NCIsCiAgICAiLXViIiwgIjEwMjQiLCAiLWIiLCAiNDA5NiIsICAgICAg
ICAgICAgIyBGTEFHU19HQU5BRE9SQVMgKE9STy1VQjFLKQogICAgIi1mYSIsICJvbiIsICItY3Rr
IiwgInE4XzAiLCAiLWN0diIsICJxOF8wIiwKICAgICItdCIsICI0IiwgIi0tcHJpbyIsICIyIiwg
Ii0tbm8tbW1wcm9qIiwKICAgICItbG0iLCAibm9uZSIsCiAgICAiLWx2IiwgIjQiLAogICAgIi0t
aG9zdCIsIEhPU1RfREVGLCAiLS1wb3J0Iiwgc3RyKFBVRVJUT19ERUYpLApdCgojIENPTE9DQUNJ
T04gUE9SIENPTkZJRyAobGVjY2lvbiBiYXJyaWRvLXF3ZW4tMzAsIG1hdGVyaWFsaXphZGEgZW4g
djEuMyk6CiMgZW4gYjExODU2IC1jbW9lIHkgLW5jbW9lIGp1bnRvcyA9IGdhbmEgZWwgR0VORVJB
TCAoLWNtb2UpIHkgYW51bGEgYWwKIyAtbmNtb2U7IHBvciBlc28gbGEgYmFzZSBOTyBsbGV2YSBj
b2xvY2FjaW9uIHkgQ0FEQSBjb25maWcgdHJhZSBsYSBzdXlhOgojIGxhIEFOQ0xBIHkgdG9kbyBl
bCByZXN0byBsbGV2YW4gLWNtb2UgKD0gbGEgcmVjZXRhIGRpYXJpYTogZXhwZXJ0b3MgZW4KIyBS
QU0pOyBOQ00zN0M0IHkgQ09NQk8tVCBsbGV2YW4gLW5jbW9lIDM3LiBIT1RGSVggZGUgY2FtcG8g
KDI4LW9jdCwgMWEKIyBjb3JyaWRhIGNvbXBsZXRhKTogbGEgdjEuMiBzYWxpbyBTSU4gY29sb2Nh
Y2lvbiBlbiAxMSBkZSAxMyBjb25maWdzIC0+CiMgZWwgY29tYW5kbyBwZWRpYSBsb3MgMTQuMjcg
R0IgZGVsIG1vZGVsbyBFTiBsYSBHUFUgZGUgNCBHQiB5IGVsIHNlcnZlcgojIG1vcmlhIGVuIH4y
LjUgcyAoZXhpdCAxKTsgc29sbyBzb2JyZXZpdmllcm9uIGxhcyAyIGNvbiAtbmNtb2UgMzcuCkNN
ID0gWyItY21vZSJdCgojIENFUlRJRklDQURPIERFIFJFQ0VUQSBkZWwgQU5DTEE6IHRva2VucyBF
WEFDVE9TIGRlIGxhIHJlY2V0YSBkaWFyaWEKIyAoY29uZmlnLnR4dCBGTEFHU19CQVNFICsgRkxB
R1NfR0FOQURPUkFTLCB1bHRpbW8gdmFsb3IgZ2FuYSkuIEVsIEFOQ0xBCiMgKGlkIDEpIERFQkUg
Y29udGVuZXJsb3MgdG9kb3MgQU5URVMgZGUgbWVkaXIgbmFkYTogc2luIHJlY2V0YSBkaWFyaWEg
bm8KIyBoYXkgYmFzZWxpbmUgeSBlbCBwcm90b2NvbG8gZGUgZGVjaXNpb24gZW50ZXJvIHF1ZWRh
IHNpbiBwYXRhLiBMZWNjaW9uCiMgZGVsIGNhbXBvIDI4LW9jdDogbGEgYXVkaXRvcmlhIGRlIGZs
YWdzIHZlcmlmaWNhIHF1ZSBjYWRhIHRva2VuIGRlbAojIGNvbWFuZG8gRVhJU1RFIGVuIGVsIGR1
bXAsIG5vIHF1ZSBlbCBjb21hbmRvIHRyYWlnYSBMQSBSRUNFVEEgQ09NUExFVEEKIyAoZmFsdGFi
YSAtY21vZSB5IHRvZG8gcGFzbyBWRVJERSBpZ3VhbCkuCkNFUlRJRklDQURPX1JFQ0VUQSA9IFsK
ICAgICgiLW5nbCIsICI5OSIpLCAoIi1jbW9lIiwgTm9uZSksICgiLWMiLCAiMTYzODQiKSwKICAg
ICgiLXViIiwgIjEwMjQiKSwgKCItYiIsICI0MDk2IiksCiAgICAoIi1mYSIsICJvbiIpLCAoIi1j
dGsiLCAicThfMCIpLCAoIi1jdHYiLCAicThfMCIpLAogICAgKCItdCIsICI0IiksICgiLS1wcmlv
IiwgIjIiKSwgKCItLW5vLW1tcHJvaiIsIE5vbmUpLAogICAgKCItbG0iLCAibm9uZSIpLApdCgoj
IGRvc2lzIE4zICh2ZXJiYXRpbSBkZWwgZHVtcCBiMTE4NTYsIGF1ZGl0YWRhcyAyOC1vY3QtMjAy
NikKQ1JBTTUxMiA9IFsiLS1jYWNoZS1yYW0iLCAiNTEyIl0KQ1RYQ1A0ID0gWyItY3R4Y3AiLCAi
NCJdCkNUWENQOCA9IFsiLWN0eGNwIiwgIjgiXQpDTVMxMDI0ID0gWyItY21zIiwgIjEwMjQiXQpS
RVVTRTI1NiA9IFsiLS1jYWNoZS1yZXVzZSIsICIyNTYiXQpTSElGVCA9IFsiLS1jb250ZXh0LXNo
aWZ0Il0KTkNNMzdDNCA9IFsiLW5jbW9lIiwgIjM3IiwgIi1jIiwgIjQwOTYiLAogICAgICAgICAg
ICItY3RrIiwgInE0XzAiLCAiLWN0diIsICJxNF8wIl0gICAjIGlkIDE0IHZlcmJhdGltIGJhcnJp
ZG8tMzAKCiMgLS0tLSB2YWxvcmVzIGxlZ2FsZXMgKHZlcmJhdGltIGRlbCBkdW1wIGIxMTg1Nikg
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQpMTV9NT0RPUyA9IHsiYXV0byIsICJub25lIiwg
Im1tYXAiLCAibWxvY2siLCAibW1hcCttbG9jayIsICJkaW8ifQpLVl9USVBPUyA9IHsiZjMyIiwg
ImYxNiIsICJiZjE2IiwgInE4XzAiLCAicTRfMCIsICJxNF8xIiwgImlxNF9ubCIsICJxNV8wIiwg
InE1XzEifQpGQV9WQUxPUkVTID0geyJvbiIsICJvZmYiLCAiYXV0byJ9CgojIC0tLS0gcHJvaGli
aWRhcyAoYXByZW5kaWRvLm1kIFNTMi9TUzcgKyBmbGFncy12ZXJpZmljYWRhcyBzZWNjaW9uIEMp
IC0tLS0tLS0KUFJPSElCSURBU19FWEFDVEFTID0gewogICAgIi0tbWxvY2siLCAiLW5rdm8iLCAi
LS1uby1rdi1vZmZsb2FkIiwgIi0tZHJhZnQtbWF4IiwgIi1kcmFmdCIsCiAgICAiLS1kcmFmdC1t
aW4iLCAiLWR0IiwgIi0tZGVmcmFnLXRob2xkIiwgIi0tbm8tbW1hcCIsICItLWRpcmVjdC1pbyIs
CiAgICAiLWRpbyIsICItLWppbmphIiwKfQpQUk9ISUJJREFTX1BSRUZJSk8gPSAoIi0tc3BlYy0i
LCAiLXR1cmJvIiwgInR1cmJvIikgICMgTjMgbm8gdXNhIHNwZWMKCiMgVG9rZW5zIHF1ZSBlbCBk
dW1wIERFQkUgY29udGVuZXIgcGFyYSBxdWUgZXN0ZSBzY3JpcHQgYXJyYW5xdWUKRFVNUF9SRVFV
RVJJRE9TID0gWwogICAgIi1tLCIsICItLW1vZGVsIiwgIi1hLCIsICItLWFsaWFzIiwgIi1uZ2ws
IiwgIi0tZ3B1LWxheWVycyIsCiAgICAiLWNtb2UsIiwgIi0tY3B1LW1vZSIsICItbmNtb2UsIiwg
Ii0tbi1jcHUtbW9lIiwKICAgICItbG0sIiwgIi0tbG9hZC1tb2RlIiwgIi1mYSwiLCAiLS1mbGFz
aC1hdHRuIiwgIi1jdGssIiwKICAgICItLWNhY2hlLXR5cGUtayIsICItY3R2LCIsICItLWNhY2hl
LXR5cGUtdiIsICItYywiLCAiLS1jdHgtc2l6ZSIsCiAgICAiLWIsIiwgIi0tYmF0Y2gtc2l6ZSIs
ICItdWIsIiwgIi0tdWJhdGNoLXNpemUiLCAiLXQsIiwgIi0tdGhyZWFkcyIsCiAgICAiLS1wcmlv
IiwgIi0tbm8tbW1wcm9qIiwgIi0taG9zdCIsICItLXBvcnQiLCAicThfMCIsICJxNF8wIiwKICAg
ICJvbnxvZmZ8YXV0byIsICItbHYsIiwgIi0tbG9nLXZlcmJvc2l0eSIsCiAgICAjIC0tLS0gTjM6
IGNhY2hlIC8gY2hlY2twb2ludHMgLyBzbG90cyAoZHVtcCBiMTE4NTYgdmVyaWZpY2FkbyAyOC1v
Y3QpIC0tLS0KICAgICItLWNhY2hlLXJldXNlIiwgIi1jcmFtLCIsICItLWNhY2hlLXJhbSIsCiAg
ICAiLWN0eGNwLCIsICItLWN0eC1jaGVja3BvaW50cyIsICItY21zLCIsICItLWNoZWNrcG9pbnQt
bWluLXN0ZXAiLAogICAgIi0tY29udGV4dC1zaGlmdCIsICItbnAsIiwgIi0tcGFyYWxsZWwiLCAi
LS1jYWNoZS1wcm9tcHQiLAogICAgIi0tbm8tY2FjaGUtcHJvbXB0IiwgIi1rdnUsIiwgIi0ta3Yt
dW5pZmllZCIsCl0KCiMgcGF1c2EgdGVybWljYSAoU1M4KTogNjAgcyBjYWRhIFBBVVNBX0NBREEg
Y29uZmlnczsgZW52IHBhcmEgdGVzdHMKUEFVU0FfVEVSTUlDQV9TID0gaW50KG9zLmVudmlyb24u
Z2V0KCJCQVJSSURPX1BBVVNBX1MiLCAiNjAiKSBvciAwKQpQQVVTQV9DQURBID0gOAoKIyAtLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIHV0aWxpZGFkZXMgLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tClVTRV9DT0xPUiA9IEZhbHNlCnRyeToKICAgIFVTRV9DT0xPUiA9IHN5
cy5zdGRvdXQuaXNhdHR5KCkKZXhjZXB0IEV4Y2VwdGlvbjoKICAgIFVTRV9DT0xPUiA9IEZhbHNl
CgoKZGVmIF9jKHR4dCwgY29kZSk6CiAgICBpZiBub3QgVVNFX0NPTE9SOgogICAgICAgIHJldHVy
biBzdHIodHh0KQogICAgcmV0dXJuICJceDFiWyVzbSVzXHgxYiIgJSAoY29kZSwgdHh0KQoKCmRl
ZiBib2xkKHQpOgogICAgcmV0dXJuIF9jKHQsICIxbSIpCgoKZGVmIHJlZCh0KToKICAgIHJldHVy
biBfYyh0LCAiMzFtIikKCgpkZWYgZ3JlZW4odCk6CiAgICByZXR1cm4gX2ModCwgIjMybSIpCgoK
ZGVmIHllbGxvdyh0KToKICAgIHJldHVybiBfYyh0LCAiMzNtIikKCgpkZWYgY3lhbih0KToKICAg
IHJldHVybiBfYyh0LCAiMzZtIikKCgpkZWYgZ3JheSh0KToKICAgIHJldHVybiBfYyh0LCAiOTBt
IikKCgpfQU5TSV9SRSA9IHJlLmNvbXBpbGUociJceDFiXFtbMC05O10qW0EtWmEtel0iKQoKCmNs
YXNzIFRlZToKICAgICIiIkNvcGlhIHRvZG8gbG8gcXVlIHNhbGUgcG9yIHN0ZG91dC9zdGRlcnIg
YSB1biBhcmNoaXZvIGRlIGxvZyAoc2luCiAgICBjb2RpZ29zIEFOU0ksIHNpZW1wcmUgdXRmLTgp
IOKAlCB2MS4xIGRlbCBiYXJyaWRvIE4xOiBzdGRlcnIgVEFNQklFTi4iIiIKCiAgICBkZWYgX19p
bml0X18oc2VsZiwgcnV0YSk6CiAgICAgICAgc2VsZi5hcmNoID0gb3BlbihydXRhLCAiYWIiKQog
ICAgICAgIHNlbGYuc3Rkb3V0ID0gc3lzLnN0ZG91dAogICAgICAgIHNlbGYuc3RkZXJyID0gc3lz
LnN0ZGVycgoKICAgIGRlZiB3cml0ZShzZWxmLCB0eHQpOgogICAgICAgIHRyeToKICAgICAgICAg
ICAgc2VsZi5hcmNoLndyaXRlKF9BTlNJX1JFLnN1YigiIiwgdHh0KS5lbmNvZGUoInV0Zi04Iiwg
InJlcGxhY2UiKSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBwYXNzCiAg
ICAgICAgdHJ5OgogICAgICAgICAgICBzZWxmLnN0ZG91dC53cml0ZSh0eHQpCiAgICAgICAgZXhj
ZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgcGFzcwogICAgICAgIHJldHVybiBsZW4odHh0KQoK
ICAgIGRlZiBmbHVzaChzZWxmKToKICAgICAgICB0cnk6CiAgICAgICAgICAgIHNlbGYuYXJjaC5m
bHVzaCgpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgcGFzcwogICAgICAg
IHRyeToKICAgICAgICAgICAgc2VsZi5zdGRvdXQuZmx1c2goKQogICAgICAgIGV4Y2VwdCBFeGNl
cHRpb246CiAgICAgICAgICAgIHBhc3MKCiAgICBkZWYgaXNhdHR5KHNlbGYpOgogICAgICAgIHJl
dHVybiBGYWxzZQoKICAgIGRlZiByZWNvbmZpZ3VyZShzZWxmLCAqYSwgKiprKToKICAgICAgICBw
YXNzCgogICAgZGVmIGNsb3NlKHNlbGYpOgogICAgICAgIHRyeToKICAgICAgICAgICAgc2VsZi5h
cmNoLmNsb3NlKCkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBwYXNzCgoK
ZGVmIGFob3JhKCk6CiAgICByZXR1cm4gZGF0ZXRpbWUuZGF0ZXRpbWUubm93KCkuc3RyZnRpbWUo
IiVZLSVtLSVkICVIOiVNOiVTIikKCgpkZWYgbWVkaWEoeHMpOgogICAgeHMgPSBbeCBmb3IgeCBp
biB4cyBpZiB4IGlzIG5vdCBOb25lIGFuZCB4ID09IHhdCiAgICByZXR1cm4gc3VtKHhzKSAvIGxl
bih4cykgaWYgeHMgZWxzZSBOb25lCgoKZGVmIGZtdCh4LCBuZD0yLCBzdWY9IiIpOgogICAgaWYg
eCBpcyBOb25lOgogICAgICAgIHJldHVybiAiTi9EIgogICAgdHJ5OgogICAgICAgIHggPSBmbG9h
dCh4KQogICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICByZXR1cm4gc3RyKHgpCiAgICByZXR1
cm4gKCIlLiIgKyBzdHIobmQpICsgImYlcyIpICUgKHgsIHN1ZikKCgojIC0tLS0tLS0tLS0tLS0t
LS0tLS0tLSBhdWRpdG9yaWEgZGUgZmxhZ3MgY29udHJhIGVsIGR1bXAgLS0tLS0tLS0tLS0tLS0t
LS0tLS0KZGVmIGRlY29kaWZpY2FyX2R1bXAocnV0YV9kdW1wKToKICAgIHJhdyA9IG9wZW4ocnV0
YV9kdW1wLCAicmIiKS5yZWFkKCkKICAgIGNhbmRpZGF0b3MgPSBbXQogICAgZm9yIGVuYyBpbiAo
InV0Zi0xNi1sZSIsICJ1dGYtMTYiLCAidXRmLTgiKToKICAgICAgICB0cnk6CiAgICAgICAgICAg
IGNhbmRpZGF0b3MuYXBwZW5kKHJhdy5kZWNvZGUoZW5jKSkKICAgICAgICBleGNlcHQgRXhjZXB0
aW9uOgogICAgICAgICAgICBjb250aW51ZQogICAgaWYgbm90IGNhbmRpZGF0b3M6CiAgICAgICAg
cmFpc2UgU3lzdGVtRXhpdChyZWQoIkZBVEFMOiBubyBwdWRlIGRlY29kaWZpY2FyIGVsIGR1bXAg
JXMiICUgcnV0YV9kdW1wKSkKICAgIGZvciB0eHQgaW4gY2FuZGlkYXRvczoKICAgICAgICBpZiAi
LS1tb2RlbCIgaW4gdHh0IG9yICItLW92ZXJyaWRlLWt2IiBpbiB0eHQ6CiAgICAgICAgICAgIHJl
dHVybiB0eHQKICAgIHJldHVybiBtYXgoY2FuZGlkYXRvcywga2V5PWxlbikKCgpkZWYgYXVkaXRh
cl9mbGFncyhydXRhX2R1bXAsIGxpc3RhX2NvbmZpZ3MsIGJhc2VfZmxhZ3M9KCkpOgogICAgIiIi
VmVyaWZpY2EgcXVlIFRPRE9TIGxvcyB0b2tlbnMgZGUgZmxhZyBkZSBUT0RBUyBsYXMgY29uZmln
cyAoYmFzZSArCiAgICBkaWZmKSBlc3RlbiB2ZXJiYXRpbSBlbiBlbCBkdW1wIGRlbCBidWlsZCAo
ZnVlbnRlIGRlIHZlcmRhZCAjMSkuIEFib3J0YQogICAgc2kgZmFsdGEgdW5vLiBUYW1iaWVuIHJl
dmlzYSBwcm9oaWJpZGFzIHkgdmFsb3JlcyBsZWdhbGVzLiBEZXZ1ZWx2ZQogICAgbGlzdGEgZGUg
cHJvYmxlbWFzICh2YWNpYSA9IHZlcmRlKS4iIiIKICAgIHByb2JsZW1hcyA9IFtdCiAgICB0eHQg
PSBkZWNvZGlmaWNhcl9kdW1wKHJ1dGFfZHVtcCkKICAgIGZhbHRhbiA9IFt0IGZvciB0IGluIERV
TVBfUkVRVUVSSURPUyBpZiB0IG5vdCBpbiB0eHRdCiAgICBpZiBmYWx0YW46CiAgICAgICAgcHJv
YmxlbWFzLmFwcGVuZCgiZWwgZHVtcCBubyBjb250aWVuZSAocmVxdWVyaWRvcyk6ICVzIiAlIGZh
bHRhbikKCiAgICB0b2tlbnNfdXNhZG9zID0gc2V0KCkKICAgIGZvciBjZmcgaW4gbGlzdGFfY29u
ZmlnczoKICAgICAgICBmbCA9IGxpc3QoYmFzZV9mbGFncykgKyBsaXN0KGNmZ1siZmxhZ3MiXSkK
ICAgICAgICBmb3IgdG9rIGluIGZsOgogICAgICAgICAgICBpZiB0b2suc3RhcnRzd2l0aCgiLSIp
OgogICAgICAgICAgICAgICAgdG9rZW5zX3VzYWRvcy5hZGQodG9rKQogICAgICAgIGZvciBwYXIg
aW4gUFJPSElCSURBU19FWEFDVEFTOgogICAgICAgICAgICBpZiBwYXIgaW4gZmw6CiAgICAgICAg
ICAgICAgICBwcm9ibGVtYXMuYXBwZW5kKCJjb25maWcgJXMgdXNhIFBST0hJQklEQSAlcyIgJSAo
Y2ZnWyJpZCJdLCBwYXIpKQogICAgICAgIGZvciB0b2sgaW4gZmw6CiAgICAgICAgICAgIGlmIGFu
eSh0b2suc3RhcnRzd2l0aChwKSBvciB0b2sgPT0gcCBmb3IgcCBpbiBQUk9ISUJJREFTX1BSRUZJ
Sk8pOgogICAgICAgICAgICAgICAgaWYgdG9rIG5vdCBpbiAoIi0tbm8tbW1wcm9qIiwgIi0tbm8t
Y2FjaGUtcHJvbXB0Iik6CiAgICAgICAgICAgICAgICAgICAgcHJvYmxlbWFzLmFwcGVuZCgiY29u
ZmlnICVzIHVzYSBwcmVmaWpvIHByb2hpYmlkbyAlcyIKICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICUgKGNmZ1siaWQiXSwgdG9rKSkKICAgIGZvciBjZmcgaW4gbGlzdGFfY29u
ZmlnczoKICAgICAgICBmbCA9IGxpc3QoYmFzZV9mbGFncykgKyBsaXN0KGNmZ1siZmxhZ3MiXSkK
ICAgICAgICBmb3IgaSwgdG9rIGluIGVudW1lcmF0ZShmbCk6CiAgICAgICAgICAgIGlmIHRvayA9
PSAiLXViIiBhbmQgaSArIDEgPCBsZW4oZmwpIGFuZCBmbFtpICsgMV0gPT0gIjUxMiI6CiAgICAg
ICAgICAgICAgICBwcm9ibGVtYXMuYXBwZW5kKCJjb25maWcgJXMgdXNhIC11YiA1MTIgKFBST0hJ
QklETykiICUgY2ZnWyJpZCJdKQogICAgICAgICAgICBpZiB0b2sgaW4gKCItY3RrIiwgIi1jdHYi
KSBhbmQgaSArIDEgPCBsZW4oZmwpOgogICAgICAgICAgICAgICAgdiA9IGZsW2kgKyAxXQogICAg
ICAgICAgICAgICAgaWYgdiBub3QgaW4gS1ZfVElQT1Mgb3Igdi5zdGFydHN3aXRoKCJ0dXJibyIp
OgogICAgICAgICAgICAgICAgICAgIHByb2JsZW1hcy5hcHBlbmQoImNvbmZpZyAlcyB1c2EgS1Yg
aWxlZ2FsICVyIiAlIChjZmdbImlkIl0sIHYpKQogICAgICAgICAgICBpZiB0b2sgPT0gIi1sbSIg
YW5kIGkgKyAxIDwgbGVuKGZsKSBhbmQgZmxbaSArIDFdIG5vdCBpbiBMTV9NT0RPUzoKICAgICAg
ICAgICAgICAgIHByb2JsZW1hcy5hcHBlbmQoImNvbmZpZyAlcyB1c2EgLWxtIGlsZWdhbCAlciIK
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgJSAoY2ZnWyJpZCJdLCBmbFtpICsgMV0p
KQogICAgICAgICAgICBpZiB0b2sgPT0gIi1mYSIgYW5kIGkgKyAxIDwgbGVuKGZsKSBhbmQgZmxb
aSArIDFdIG5vdCBpbiBGQV9WQUxPUkVTOgogICAgICAgICAgICAgICAgcHJvYmxlbWFzLmFwcGVu
ZCgiY29uZmlnICVzIHVzYSAtZmEgaWxlZ2FsICVyIgogICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAlIChjZmdbImlkIl0sIGZsW2kgKyAxXSkpCiAgICAgICAgICAgIGlmIHRvayA9PSAi
LWN0eGNwIiBhbmQgaSArIDEgPCBsZW4oZmwpIGFuZCBub3QgZmxbaSArIDFdLmlzZGlnaXQoKToK
ICAgICAgICAgICAgICAgIHByb2JsZW1hcy5hcHBlbmQoImNvbmZpZyAlcyB1c2EgLWN0eGNwIGls
ZWdhbCAlciIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgJSAoY2ZnWyJpZCJdLCBm
bFtpICsgMV0pKQogICAgICAgICAgICBpZiB0b2sgaW4gKCItY21zIiwgIi0tY2FjaGUtcmFtIiwg
Ii0tY2FjaGUtcmV1c2UiLCAiLW5wIikgXAogICAgICAgICAgICAgICAgICAgIGFuZCBpICsgMSA8
IGxlbihmbCkgYW5kIG5vdCBmbFtpICsgMV0ubHN0cmlwKCItIikuaXNkaWdpdCgpOgogICAgICAg
ICAgICAgICAgcHJvYmxlbWFzLmFwcGVuZCgiY29uZmlnICVzIHVzYSAlcyBjb24gdmFsb3IgaWxl
Z2FsICVyIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAlIChjZmdbImlkIl0sIHRv
aywgZmxbaSArIDFdKSkKCiAgICBmb3IgdG9rIGluIHNvcnRlZCh0b2tlbnNfdXNhZG9zKToKICAg
ICAgICBwYXRyb24gPSByZS5lc2NhcGUodG9rKSArIHIiKD89W1xzLF18JCkiCiAgICAgICAgaWYg
bm90IHJlLnNlYXJjaChwYXRyb24sIHR4dCk6CiAgICAgICAgICAgIHByb2JsZW1hcy5hcHBlbmQo
InRva2VuICVyIE5PIGFwYXJlY2UgdmVyYmF0aW0gZW4gZWwgZHVtcCIgJSB0b2spCiAgICByZXR1
cm4gcHJvYmxlbWFzCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0gcHJvbXB0cyBkZWwgcHJv
dG9jb2xvIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KUFJPTVBUU19NRURJQ0lPTiA9IFsK
ICAgICJEZXNjcmliZSBlbiB1biBwYXJyYWZvIGNvbW8gZnVuY2lvbmEgdW5hIGJpY2ljbGV0YTog
cGVkYWxlcywgY2FkZW5hIHkgIgogICAgInJ1ZWRhcy4gSW5jbHV5ZSB1biBjb25zZWpvIGJhc2lj
byBkZSBtYW50ZW5pbWllbnRvLiIsCiAgICAiRXhwbGljYSBlbiB1biBwYXJyYWZvIHBvciBxdWUg
ZWwgY2llbG8gZXMgYXp1bCBkdXJhbnRlIGVsIGRpYSB5IHJvam8gYWwgIgogICAgImF0YXJkZWNl
ciwgY29uIHBhbGFicmFzIHNpbXBsZXMuIiwKICAgICJSZXN1bWUgZW4gdW4gcGFycmFmbyBsYSBo
aXN0b3JpYSBkZSBsYSBpbXByZW50YSBkZSBHdXRlbmJlcmcgeSBwb3IgcXVlICIKICAgICJjYW1i
aW8gZWwgbXVuZG8uIiwKICAgICJFeHBsaWNhIGVuIHVuIHBhcnJhZm8gcXVlIGVzIGxhIGZvdG9z
aW50ZXNpczogcXVlIGVudHJhIGVuIGxhIGhvamEsIHF1ZSAiCiAgICAic2FsZSB5IHBvciBxdWUg
aW1wb3J0YSwgZW4gcGFsYWJyYXMgc2ltcGxlcy4iLApdCgpTQU5JVFlfUEFSRVMgPSBbCiAgICAo
IkN1YW50byBlcyAxNyB4IDIzPyBSZXNwb25kZSBzb2xvIGVsIG51bWVyby4iLCBbIjM5MSJdKSwK
ICAgICgiUXVpZW4gZXNjcmliaW8gRG9uIFF1aWpvdGU/IFJlc3BvbmRlIG11eSBjb3J0by4iLCBb
ImNlcnZhbnRlcyJdKSwKICAgICgiUXVlIHBsYW5ldGEgZXMgY29ub2NpZG8gY29tbyBlbCBwbGFu
ZXRhIHJvam8/IFJlc3BvbmRlIG11eSBjb3J0by4iLAogICAgIFsibWFydGUiXSksCl0KCiMgUkVQ
Uk8gREUgVFVSTk9TIENSRUNJRU5URVMgKFNTMy4zKTogcHJlZmlqbyBlc3RhYmxlICsgcGFycmFm
byBudWV2byBwb3IKIyB0dXJuby4gTG8gaW5tdXRhYmxlIEFSUklCQSwgbG8gdm9sYXRpbCBhbCBm
aW5hbCAocmVnbGEgU1MzLjI6IHNpIGxhCiMgcGxhbnRpbGxhIG11dGEgZWwgaW5pY2lvLCBlbCBw
cmVmaWpvIGNvbXBhcnRpZG8gc2Ugcm9tcGUgeSBsYSBjYWNoZSBubwojIGFjaWVydGEpLiBUVEZU
ID0gdGltZS10by1maXJzdC1jaHVuayBjb24gc3RyZWFtOnRydWUgKHByb3h5IGRlCiMgdGltZV9z
dGFydHRyYW5zZmVyIGRlbCBjdXJsIGRlbCByZXBybyBvcmlnaW5hbCkuClBST01QVF9SRVBST19C
QVNFID0gKAogICAgIkVyZXMgdW4gYXNpc3RlbnRlIHF1ZSByZXNwb25kZSBjb3J0by4gQ29udmVy
c2FjaW9uIGNvbiBoaXN0b3JpYWw6XG5cbiIKICAgICJUZW1hOiBlbCBmYXJvIGRlIHVuIHB1ZXJ0
by4gVW4gZmFybyBlcyB1bmEgdG9ycmUgY29uIHVuYSBsdXogcG90ZW50ZSAiCiAgICAicXVlIGdp
cmEgeSBhdmlzYSBhIGxvcyBiYXJjb3MgZG9uZGUgZXN0YSBsYSBjb3N0YSB5IGRvbmRlIGVzdGFu
IGxvcyAiCiAgICAicGVsaWdyb3MuIEFudGVzIGxvIHZpZ2lsYWJhIHVuYSBwZXJzb25hIHF1ZSBl
bmNlbmRpYSBsYSBsYW1wYXJhIGFsICIKICAgICJhbm9jaGVjZXI7IGhveSBsYSBsdXogZXMgZWxl
Y3RyaWNhIHkgYXV0b21hdGljYS4gTGEgbHV6IHNlIGFncnVwYSBlbiAiCiAgICAiZGVzdGVsbG9z
IGNvbiB1biByaXRtbyBwcm9waW8sIHkgY2FkYSBmYXJvIGRlbCBtdW5kbyB0aWVuZSB1biByaXRt
byAiCiAgICAiZGlzdGludG8gcGFyYSBxdWUgZWwgbWFyaW5lcm8gc2VwYSBjdWFsIGVzdGEgdmll
bmRvLlxuXG4iCikKVFVSTk9TX1JFUFJPX0VYVFJBID0gWwogICAgIlR1cm5vIDE6IEN1ZW50YSBl
biB1bmEgZnJhc2UgY29tbyBzZSBsbGFtYWJhIGxhIHBlcnNvbmEgcXVlIGN1aWRhYmEgIgogICAg
ImVsIGZhcm8geSBxdWUgaGFjw61hIGFsIGF0YXJkZWNlci4iLAogICAgIlR1cm5vIDI6IEV4cGxp
Y2EgYnJldmVtZW50ZSBwb3IgcXVlIGNhZGEgZmFybyB0aWVuZSB1biByaXRtbyBkZSAiCiAgICAi
ZGVzdGVsbG9zIGRpc3RpbnRvIHkgcGFyYSBxdWUgbGUgc2lydmUgZXNvIGFsIG1hcmluZXJvLiIs
CiAgICAiVHVybm8gMzogUmVzdW1lIGVuIHVuYSBmcmFzZSBxdWUgY2FtYmlvIGN1YW5kbyBsYSBs
YW1wYXJhIHBhc28gZGUgIgogICAgImFjZWl0ZSBhIGVsZWN0cmljaWRhZCwgeSBxdWUgdmVudGFq
YSB0cmFqbyBkZSBub2NoZS4iLAogICAgIlR1cm5vIDQ6IE1lbmNpb25hIGVuIHVuYSBmcmFzZSBk
b3MgcGVsaWdyb3MgdGlwaWNvcyBxdWUgdW4gZmFybyAiCiAgICAiYXl1ZGEgYSBldml0YXIgY2Vy
Y2EgZGUgbGEgY29zdGEuIiwKICAgICJUdXJubyA1OiBFeHBsaWNhIGVuIHVuYSBmcmFzZSBxdWUg
ZXMgbGEgbmllYmxhIHBhcmEgdW4gbWFyaW5lcm8geSAiCiAgICAicXVlIG90cmEgc2VuYWwgc2Ug
dXNhIGN1YW5kbyBsYSBsdXogZGVsIGZhcm8gbm8gc2UgdmUuIiwKICAgICJUdXJubyA2OiBDaWVy
cmEgY29uIHVuYSBmcmFzZTogcG9yIHF1ZSBzaWd1ZSB0ZW5pZW5kbyBzZW50aWRvIHRlbmVyICIK
ICAgICJmYXJvcyBob3kgcXVlIGV4aXN0ZW4gZWwgR1BTIHkgbG9zIHNhdGVsaXRlcy4iLApdClBS
T01QVF9SRVBST19DT0xBID0gKCJcblxuUmVzcG9uZGUgU09MTyBhIGxvIG51ZXZvIGRlbCBoaXN0
b3JpYWwgY29uIFVOQSAiCiAgICAgICAgICAgICAgICAgICAgICJmcmFzZSBjb3J0YSBlbiBlc3Bh
bm9sLiIpClJFUFJPX1RVUk5PUyA9IDYgICAgICAgICAgIyB0dXJub3MgZGVsIHJlcHJvICgxIGZy
aWEgKyA1IHV0aWxlcykKUkVQUk9fTl9QUkVESUNUID0gMjQgICAgICAjIHJlc3B1ZXN0YXMgY29y
dGFzOiBtYW5kYSBlbCBUVEZULCBubyBlbCBkZWNvZGUKCgpkZWYgY29uc3RydWlyX2NvbmZpZ3Mo
KToKICAgICIiIkNvbnN0cnV5ZSBsYXMgY29uZmlncyBkZSBsYSBjb3NlY2hhIE4zLiBDYWRhIGNv
bmZpZyA9IEJBU0UgKHJlY2V0YQogICAgZGlhcmlhICsgLWx2IDQpICsgZmxhZ3MgZGlmZiAoZWwg
dWx0aW1vIHZhbG9yIGdhbmEgZW4gbGxhbWEuY3BwKS4KICAgIExhIENPTE9DQUNJT04gdmEgZW4g
ZWwgZGlmZiBQT1IgQ09ORklHIChsZWNjaW9uIGJhcnJpZG8tMzAgKyBob3RmaXggZGUKICAgIGNh
bXBvIHYxLjMpOiBhZGQoKSBpbnllY3RhIC1jbW9lIGVuIHRvZGEgY29uZmlnIHF1ZSBubyB0cmFp
Z2EgLW5jbW9lLiIiIgogICAgY29uZmlncyA9IFtdCgogICAgZGVmIGFkZChjaWQsIGZhbWlsaWEs
IG5vbWJyZSwgZmxhZ3MsIGhpcG90ZXNpcyk6CiAgICAgICAgZmwgPSBsaXN0KGZsYWdzKQogICAg
ICAgIGlmICItbmNtb2UiIG5vdCBpbiBmbDoKICAgICAgICAgICAgZmwgKz0gbGlzdChDTSkgICAj
IHJlY2V0YSBkaWFyaWE6IGV4cGVydG9zIGVuIFJBTSAoLWNtb2UpCiAgICAgICAgY29uZmlncy5h
cHBlbmQoeyJpZCI6IGNpZCwgImZhbWlsaWEiOiBmYW1pbGlhLCAibm9tYnJlIjogbm9tYnJlLAog
ICAgICAgICAgICAgICAgICAgICAgICAiZmxhZ3MiOiBmbCwgImhpcG90ZXNpcyI6IGhpcG90ZXNp
c30pCgogICAgYWRkKDEsICJBTkNMQSIsICJOMy1BTkNMQSIsIFtdLAogICAgICAgICJjb250cm9s
IGRlIHNlc2lvbiA9IExBIFJFQ0VUQSBESUFSSUEgKEZMQUdTX0JBU0UgKyBGTEFHU19HQU5BRE9S
QVMgIgogICAgICAgICJkZSBjb25maWcudHh0LCBhdWRpdG9yaWEgUjI0KTogYmFzZWxpbmUgZGUg
dG9kb3MgbG9zIGRlbHRhczsgc2luICIKICAgICAgICAiY2FjaGUtcmV1c2UgZWwgaGlicmlkbyBw
dWVkZSBtb3N0cmFyICdmb3JjaW5nIGZ1bGwgcmUtcHJvY2Vzc2luZycgIgogICAgICAgICIoIzIx
ODMxKTogZXNlIGVzIGVsIGNvbXBvcnRhbWllbnRvIGRlIEhPWSwgbm8gdW4gZmFsbG8gZGVsIGJh
cnJpZG8iKQogICAgYWRkKDIsICJSQU0iLCAiTjMtQ1JBTTUxMiIsIGxpc3QoQ1JBTTUxMiksCiAg
ICAgICAgIi0tY2FjaGUtcmFtIDgxOTIgKGRlZmF1bHQpIC0+IDUxMjogbGEgY2FjaGUgZGUgcHJv
bXB0cyBkZWwgaG9zdCAiCiAgICAgICAgImRlamEgZGUgcGVsZWFyIGNvbiBlbCBtb2RlbG8gZGUg
MTQuMjcgR0IgZW4gMTYgR0I7IE9STy1DUkFNNTEyICIKICAgICAgICAibWlkaW8gZGVjb2RlIGlu
dGFjdG8gKCUuMmYpIHkgLTcuNyBHQiBbTV07IGNlcnRpZmljYWRvID0gUkFNICIKICAgICAgICAi
bGlicmUvcHJvY2VzbyBzdWJlIiAlIENSQU01MTJfUkVGKQogICAgYWRkKDMsICJSQU0iLCAiTjMt
Q1RYQ1A0IiwgbGlzdChDVFhDUDQpLAogICAgICAgICItY3R4Y3AgMzIgKGRlZmF1bHQpIC0+IDQ6
IGNhZGEgY2hlY2twb2ludCBHRE4gcGVzYSB+NjMgTUIgLT4gZWwgIgogICAgICAgICJkZWZhdWx0
IHB1ZWRlIHBlZGlyIH4yIEdCIGRlIFJBTTsgZG9zaXMgbWFzIGRlZmVuZGlibGUgZGVsIE4zICIK
ICAgICAgICAiKFNTMTIvU1MxMyk7IGNlcnRpZmljYWRvID0gV29ya2luZ1NldCBkZWwgcHJvY2Vz
byBiYWphIH4xLjUtMS44IEdCIikKICAgIGFkZCg0LCAiUkFNIiwgIk4zLUNNUzEwMjQiLCBsaXN0
KENNUzEwMjQpLAogICAgICAgICItY21zIDgxOTIgKGRlZmF1bHQpIC0+IDEwMjQ6IGNoZWNrcG9p
bnRzIG1hcyBzZWd1aWRvcyBlbiBjaGF0ICIKICAgICAgICAiY29udGludW8gKHNpbiBjaGF0cyBk
ZSAxNksgY2FiZW4gPD0yOyBTUzEwLjEpOyB2YSBkZSBsYSBtYW5vIGNvbiAiCiAgICAgICAgIi1j
dHhjcCB5IC1jcmFtIikKICAgIGFkZCg1LCAiQ0FDSEUiLCAiTjMtUkVVU0UiLCBsaXN0KFJFVVNF
MjU2KSwKICAgICAgICAiTEEgSk9ZQSAoU1MzKTogLS1jYWNoZS1yZXVzZSAyNTYgcmVjaWNsYSBl
bCBwcmVmaWpvIHBvciBjaHVua3MgIgogICAgICAgICIoZGVmYXVsdCAwID0gT0ZGIGVuIGIxMTg1
Nik7IGVuIGNvbXVuaWRhZCBUVEZUIC05MyUgZW4gcHJvbXB0cyAiCiAgICAgICAgInJlcGV0aWRv
cyAoIzIwNTc0KTsgT1JPLVNISUZUIHlhIG1pZGlvIHJldXNlIHNpbiBjb3N0ZSBkZSBkZWNvZGU7
ICIKICAgICAgICAiT0pPICMyNDA1NTogZWwgYXJyYW5xdWUgcHVlZGUgYXV0by1kZXNoYWJpbGl0
YXJsYSAod2FybmluZyA9ICIKICAgICAgICAiY2VydGlmaWNhZG8gTk8tU09QT1JUQURPIC0+IFJV
VEEgMCBnYW5hIG1vdGl2bykiKQogICAgYWRkKDYsICJDQUNIRSIsICJOMy1TSElGVCIsIGxpc3Qo
U0hJRlQpICsgbGlzdChSRVVTRTI1NiksCiAgICAgICAgImZhbWlsaWEgT1JPLVNISUZUIHZlcmJh
dGltICglLjJmIFtNXSwgc2luIGNvc3RlKTogLS1jb250ZXh0LXNoaWZ0ICIKICAgICAgICAicGFy
YSBjb252ZXJzYWNpb25lcyBsYXJnYXMgKyByZXVzZSAyNTY7IGNlcnRpZmljYWRvIGRvYmxlOiBs
aW5lYXMgIgogICAgICAgICJkZSBsb2cgKyBUVEZUIHBsYW5vIGVuIGVsIHJlcHJvIiAlIFNISUZU
X1JFRikKICAgIGFkZCg3LCAiU0xPVFMiLCAiTjMtTlAyIiwgWyItbnAiLCAiMiJdLAogICAgICAg
ICIyIHNsb3RzOiB0aHJvdWdocHV0IGFncmVnYWRvICsxNCUlIFtNIFNTNF0gY29uIGNvbmN1cnJl
bmNpYSByZWFsOyAiCiAgICAgICAgIi1jIDE2Mzg0IHNlIHJlcGFydGUgKDgxOTIgcG9yIHNsb3Qs
IHNvYnJhIHBhcmEgY2hhdCk7IFNPTE8gc2luICIKICAgICAgICAic3BlYyAoU1MxMS40OiBNVFAg
ZXhpZ2UgLW5wIDEsIGFxdWkgbm8gaGF5IHNwZWMpOyBjZXJ0aWZpY2FkbyA9ICIKICAgICAgICAi
cHJvYmUgY29uY3VycmVudGUgZGUgMiBwZWRpZG9zIikKICAgIGFkZCg4LCAiTkNNIiwgIk4zLU5D
TTM3QzQtVUIiLCBsaXN0KE5DTTM3QzQpLAogICAgICAgICJjb2xvY2FjaW9uIGNhbXBlb25hICgl
LjJmIFtNXSkgQVBJTEFEQSBjb24gbGEgcmVjZXRhIGRpYXJpYSAiCiAgICAgICAgIihVQjFLIHlh
IGVuIGxhIGJhc2UpOiBQUklNRVIgZGF0byBkZWwgc3RhY2sgT1JPLVVCMUsgeCBOQ00zN0M0ICIK
ICAgICAgICAiKHBlbmRpZW50ZSBTUzEzLTEpOyBwYWdhIGNvbiBjdHggNDA5NiB5IEtWIHE0XzAi
ICUgTkNNMzdDNF9SRUYpCiAgICBhZGQoOSwgIkNPTUJPIiwgIk4zLUNPTUJPLVIiLAogICAgICAg
IGxpc3QoQ1JBTTUxMikgKyBsaXN0KENUWENQNCkgKyBsaXN0KENNUzEwMjQpICsgbGlzdChSRVVT
RTI1NikKICAgICAgICArIGxpc3QoU0hJRlQpLAogICAgICAgICJjb21ibyBSQU0gc2VndXJvIHNv
YnJlIGxhIHJlY2V0YSBkaWFyaWEgU0lOIHRvY2FyIGNvbG9jYWNpb246ICIKICAgICAgICAiY3Jh
bSA1MTIgKyBjdHhjcCA0ICsgY21zIDEwMjQgKyByZXVzZSAyNTYgKyBzaGlmdDsgZXhwZWN0YXRp
dmE6ICIKICAgICAgICAiZGVjb2RlIH49IGFuY2xhLCBSQU0gbGliZXJhZGEsIFRURlQgcGxhbm87
IGxhIGNhbmRpZGF0YSBuYXR1cmFsICIKICAgICAgICAiYSBjb25maWcudHh0IHNpIGNlcnRpZmlj
YSIpCiAgICBhZGQoMTAsICJDT01CTyIsICJOMy1DT01CTy1UIiwKICAgICAgICBsaXN0KE5DTTM3
QzQpICsgbGlzdChDUkFNNTEyKSArIGxpc3QoQ1RYQ1A4KSArIGxpc3QoQ01TMTAyNCkKICAgICAg
ICArIGxpc3QoUkVVU0UyNTYpICsgbGlzdChTSElGVCksCiAgICAgICAgImNvbWJvIGdhbmFkb3Jl
cyBTUzguMS9TUzExLjc6IE5DTTM3QzQgeCBjcmFtL2N0eGNwL2Ntcy9yZXVzZS8iCiAgICAgICAg
InNoaWZ0IChzaW4gLW5wKTsgZXhwZWN0YXRpdmEgZGVjb2RlIH4yMi41LTIzLjUgW1RdOyBjdHgg
NDA5NiBkZSAiCiAgICAgICAgIk5DTTM3QzQgbWFuZGEgKHNpbmdsZSBzbG90KTsgY29udHJvbCBk
ZSBzZXNpb24gPSBpZCA4IikKICAgIGFkZCgxMSwgIkNPTUJPIiwgIk4zLU5QMi1DIiwKICAgICAg
ICBbIi1ucCIsICIyIl0gKyBsaXN0KENSQU01MTIpICsgbGlzdChDVFhDUDgpICsgbGlzdChDTVMx
MDI0KQogICAgICAgICsgbGlzdChSRVVTRTI1NikgKyBsaXN0KFNISUZUKSwKICAgICAgICAiY29t
Ym8gc2xvdHMgU1MxMS43IHNpbiBOQ006IC1ucCAyICg4MTkyIGN0eCBwb3Igc2xvdCkgeCBjYWNo
ZSAiCiAgICAgICAgImNvbXBsZXRhOyBwYXJhIGVsIGNhc28gZGUgMiBzZXNpb25lcyBhIGxhIHZl
ejsgY2VydGlmaWNhZG8gPSAiCiAgICAgICAgInByb2JlIGNvbmN1cnJlbnRlIikKICAgIGFkZCgx
MiwgIkNUUkwiLCAiTjMtTk9DQUNIRSIsIFsiLS1uby1jYWNoZS1wcm9tcHQiXSwKICAgICAgICAi
Y29udHJvbCBkZWwgQS9CIGNhY2hlIChTUzE0KTogc2luIGNhY2hlIGRlIHByb21wdHMgVE9ETyB0
dXJubyAiCiAgICAgICAgInJlLXByb2Nlc2EgLT4gZWwgcmVwcm8gREVCRSBjcmVjZXIgbGluZWFs
OyBzZXBhcmEgZWwgZWZlY3RvICIKICAgICAgICAiY2FjaGUgZGVsIGVmZWN0byBkZWNvZGU7IHRh
bWJpZW4gY2FsaWJyYSBlbCAlcmVhbCBkZWwgY2FjaGUiKQogICAgYWRkKDEzLCAiQU5DTEEtRklO
IiwgIk4zLUFOQ0xBLUZJTiIsIFtdLAogICAgICAgICJib29rZW5kIChsZWNjaW9uIHYxLjIuMSk6
IHJlLWFuY2xhIGFsIGNpZXJyZTsgfGZpbi1pbmljaW98ID4gNSUgPSAiCiAgICAgICAgImxhIHNl
c2lvbiBkZXJpdm8geSBsb3MgZGVsdGFzIHNlIGxlZW4gY29uIGN1aWRhZG8iKQogICAgcmV0dXJu
IGNvbmZpZ3MKCgpkZWYgdmVyaWZpY2FyX3JlY2V0YShhbmNsYV9mbGFncywgY2VydD1Ob25lKToK
ICAgICIiIkNFUlRJRklDQURPIERFIFJFQ0VUQSAodjEuMyk6IGRldnVlbHZlIGxvcyBpdGVtcyBk
ZWwgY2VydGlmaWNhZG8gcXVlCiAgICBGQUxUQU4gZW4gbG9zIGZsYWdzIGZpbmFsZXMgZGVsIEFO
Q0xBIChiYXNlICsgZGlmZikuIFtdID0gbGEgcmVjZXRhCiAgICBkaWFyaWEgdml2ZSBjb21wbGV0
YS4gUGFyZXMgKGZsYWcsIHZhbG9yKTogZGViZW4gYXBhcmVjZXIgYWR5YWNlbnRlczsKICAgIChm
bGFnLCBOb25lKTogZWwgdG9rZW4gZGViZSBleGlzdGlyLiIiIgogICAgZmFsdGFuID0gW10KICAg
IHRva2VucyA9IGxpc3QoYW5jbGFfZmxhZ3Mgb3IgW10pCiAgICBmb3IgZmxhZywgdmFsb3IgaW4g
KGNlcnQgaWYgY2VydCBpcyBub3QgTm9uZSBlbHNlIENFUlRJRklDQURPX1JFQ0VUQSk6CiAgICAg
ICAgaWYgdmFsb3IgaXMgTm9uZToKICAgICAgICAgICAgaWYgZmxhZyBub3QgaW4gdG9rZW5zOgog
ICAgICAgICAgICAgICAgZmFsdGFuLmFwcGVuZChmbGFnKQogICAgICAgIGVsc2U6CiAgICAgICAg
ICAgIG9rID0gRmFsc2UKICAgICAgICAgICAgZm9yIGksIHQgaW4gZW51bWVyYXRlKHRva2Vucyk6
CiAgICAgICAgICAgICAgICBpZiB0ID09IGZsYWcgYW5kIGkgKyAxIDwgbGVuKHRva2VucykgYW5k
IHRva2Vuc1tpICsgMV0gPT0gdmFsb3I6CiAgICAgICAgICAgICAgICAgICAgb2sgPSBUcnVlCiAg
ICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgaWYgbm90IG9rOgogICAgICAgICAg
ICAgICAgZmFsdGFuLmFwcGVuZCgiJXMgJXMiICUgKGZsYWcsIHZhbG9yKSkKICAgIHJldHVybiBm
YWx0YW4KCgpkZWYgdmVyaWZpY2FyX2NvbG9jYWNpb24oY29uZmlncywgYmFzZV9mbGFncz0oKSk6
CiAgICAiIiJSZWdsYSBkZWwgYmFycmlkby0zMCBtYXRlcmlhbGl6YWRhICh2MS4zKTogVE9ETyBj
b21hbmRvIGZpbmFsIGRlYmUKICAgIHRyYWVyIHN1IGNvbG9jYWNpb24gKC1jbW9lIG8gLW5jbW9l
KS4gU2luIGVsbGEgZWwgbW9kZWxvIGRlIDE0LjI3IEdCCiAgICBubyBjYWJlIGVuIGxhIEdQVSBk
ZSA0IEdCICgxMSBjb25maWdzIG11ZXJ0YXMgZW4gZWwgY2FtcG8gMjgtb2N0KS4KICAgIERldnVl
bHZlIGxvcyBub21icmVzIGRlIGxhcyBjb25maWdzIHF1ZSBubyBsYSBsbGV2YW4uIiIiCiAgICBt
YWxhcyA9IFtdCiAgICBmb3IgYyBpbiBjb25maWdzOgogICAgICAgIGZ1bGwgPSBsaXN0KGJhc2Vf
ZmxhZ3Mgb3IgW10pICsgbGlzdChjWyJmbGFncyJdKQogICAgICAgIGlmICItY21vZSIgbm90IGlu
IGZ1bGwgYW5kICItbmNtb2UiIG5vdCBpbiBmdWxsOgogICAgICAgICAgICBtYWxhcy5hcHBlbmQo
IiMlZCAlcyIgJSAoY1siaWQiXSwgY1sibm9tYnJlIl0pKQogICAgcmV0dXJuIG1hbGFzCgoKQkxP
UVVFU19ERSA9IHsiYW5jbGEiOiBbMV0sICJyYW0iOiBbMiwgMywgNF0sICJjYWNoZSI6IFs1LCA2
XSwgInNsb3RzIjogWzddLAogICAgICAgICAgICAgICJuY20iOiBbOF0sICJjb21ibyI6IFs5LCAx
MCwgMTFdLCAiY3RybCI6IFsxMl0sCiAgICAgICAgICAgICAgImFuY2xhZmluIjogWzEzXX0KUVVJ
Q0tfSURTID0gWzEsIDUsIDksIDEwLCAxM10KVFRGVF9JRFMgPSB7MSwgNSwgNiwgOSwgMTAsIDEx
LCAxMn0gICAjIGNvbmZpZ3MgZG9uZGUgZWwgVFRGVCBFUyBlbCBjZXJ0aWZpY2FkbwpUSUVORV9S
RVVTRSA9ICgiLS1jYWNoZS1yZXVzZSIsKQoKCmRlZiBmaWx0cmFyX2NvbmZpZ3MoY29uZmlncywg
c29sbz1Ob25lLCBxdWljaz1GYWxzZSk6CiAgICBpZiBxdWljazoKICAgICAgICByZXR1cm4gW2Mg
Zm9yIGMgaW4gY29uZmlncyBpZiBjWyJpZCJdIGluIFFVSUNLX0lEU10KICAgIGlmIHNvbG86CiAg
ICAgICAgcGVkaWRvcyA9IFtzLnN0cmlwKCkgZm9yIHMgaW4gc29sby5zcGxpdCgiLCIpIGlmIHMu
c3RyaXAoKV0KICAgICAgICBpZHMgPSBbXQogICAgICAgIGZvciBwIGluIHBlZGlkb3M6CiAgICAg
ICAgICAgIGlmIHAgbm90IGluIEJMT1FVRVNfREU6CiAgICAgICAgICAgICAgICByYWlzZSBTeXN0
ZW1FeGl0KHJlZCgiLS1zb2xvIGJsb3F1ZSBkZXNjb25vY2lkbzogJXMgKHZhbGlkb3M6ICVzKSIK
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICUgKHAsICIsIi5qb2luKHNvcnRl
ZChCTE9RVUVTX0RFKSkpKSkKICAgICAgICAgICAgaWRzLmV4dGVuZChCTE9RVUVTX0RFW3BdKQog
ICAgICAgIHJldHVybiBbYyBmb3IgYyBpbiBjb25maWdzIGlmIGNbImlkIl0gaW4gaWRzXQogICAg
cmV0dXJuIGNvbmZpZ3MKCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBjb250cm9sIGRl
bCBzZXJ2ZXIgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KZGVmIGhlYWx0aF9vayhwdWVy
dG8sIHRpbWVvdXQ9Mik6CiAgICB0cnk6CiAgICAgICAgciA9IHVybGxpYi5yZXF1ZXN0LnVybG9w
ZW4oCiAgICAgICAgICAgICJodHRwOi8vJXM6JWQvaGVhbHRoIiAlIChIT1NUX0RFRiwgcHVlcnRv
KSwgdGltZW91dD10aW1lb3V0KQogICAgICAgIHJldHVybiByLmdldGNvZGUoKSA9PSAyMDAKICAg
IGV4Y2VwdCB1cmxsaWIuZXJyb3IuSFRUUEVycm9yOgogICAgICAgIHJldHVybiBGYWxzZQogICAg
ZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICByZXR1cm4gRmFsc2UKCgpkZWYgdmVyc2lvbl9zZXJ2
ZXIocnV0YV9zZXJ2ZXIpOgogICAgdHJ5OgogICAgICAgIG91dCA9IHN1YnByb2Nlc3MucnVuKFty
dXRhX3NlcnZlciwgIi0tdmVyc2lvbiJdLCBjYXB0dXJlX291dHB1dD1UcnVlLAogICAgICAgICAg
ICAgICAgICAgICAgICAgICAgIHRpbWVvdXQ9MzApCiAgICAgICAgdHh0ID0gKChvdXQuc3Rkb3V0
IG9yIGIiIikgKyAob3V0LnN0ZGVyciBvciBiIiIpKS5kZWNvZGUoCiAgICAgICAgICAgICJ1dGYt
OCIsIGVycm9ycz0icmVwbGFjZSIpCiAgICAgICAgcmV0dXJuICIgIi5qb2luKHR4dC5zcGxpdCgp
KQogICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgIHJldHVybiAiTi9EICglcykiICUg
ZQoKCmRlZiBtYXRhcl9zZXJ2ZXJfdml2byhwdWVydG8pOgogICAgaWYgaGVhbHRoX29rKHB1ZXJ0
byk6CiAgICAgICAgcHJpbnQoeWVsbG93KCIgIHNlcnZlciB2aXZvIGVuIGVsIHB1ZXJ0byAlZCAt
PiB0YXNra2lsbCBsbGFtYS1zZXJ2ZXIuZXhlIiAlIHB1ZXJ0bykpCiAgICAgICAgdHJ5OgogICAg
ICAgICAgICBzdWJwcm9jZXNzLnJ1bihbInRhc2traWxsIiwgIi9GIiwgIi9JTSIsICJsbGFtYS1z
ZXJ2ZXIuZXhlIl0sCiAgICAgICAgICAgICAgICAgICAgICAgICAgIGNhcHR1cmVfb3V0cHV0PVRy
dWUpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICBwcmludCh5ZWxs
b3coIiAgdGFza2tpbGwgbm8gZGlzcG9uaWJsZSBhcXVpICglcyk7IGNlcnJhciBhIG1hbm8iICUg
ZSkpCiAgICAgICAgdGltZS5zbGVlcCgzKQogICAgICAgIGlmIGhlYWx0aF9vayhwdWVydG8pOgog
ICAgICAgICAgICByYWlzZSBTeXN0ZW1FeGl0KHJlZCgiRkFUQUw6IGVsIHB1ZXJ0byAlZCBzaWd1
ZSByZXNwb25kaWVuZG8gdHJhcyAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJ0
YXNra2lsbC4gQ2VycmFyIGEgbWFubyB5IHJlaW50ZW50YXIuIiAlIHB1ZXJ0bykpCgoKZGVmIGxh
bnphcl9zZXJ2ZXIocnV0YV9zZXJ2ZXIsIGZsYWdzLCBsb2dfcGF0aCwgY2FyZ2FfdGltZW91dCk6
CiAgICAiIiJMYW56YSBsbGFtYS1zZXJ2ZXIgY29uIGxvcyBmbGFncyBFWEFDVE9TOyBzdGRvdXQr
c3RkZXJyIGFsIGxvZy4iIiIKICAgIGxvZ2YgPSBvcGVuKGxvZ19wYXRoLCAid2IiKQogICAgcHJv
YyA9IHN1YnByb2Nlc3MuUG9wZW4oW3J1dGFfc2VydmVyXSArIGZsYWdzLCBzdGRvdXQ9bG9nZiwK
ICAgICAgICAgICAgICAgICAgICAgICAgICAgIHN0ZGVycj1zdWJwcm9jZXNzLlNURE9VVCwgc3Rk
aW49c3VicHJvY2Vzcy5ERVZOVUxMKQogICAgdDAgPSB0aW1lLnRpbWUoKQogICAgd2hpbGUgdGlt
ZS50aW1lKCkgLSB0MCA8IGNhcmdhX3RpbWVvdXQ6CiAgICAgICAgaWYgcHJvYy5wb2xsKCkgaXMg
bm90IE5vbmU6CiAgICAgICAgICAgIGxvZ2YuY2xvc2UoKQogICAgICAgICAgICByZXR1cm4gTm9u
ZSwgdGltZS50aW1lKCkgLSB0MCwgKCJlbCBzZXJ2ZXIgbXVyaW8gZHVyYW50ZSBsYSAiCiAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImNhcmdhIChleGl0ICVzKSIg
JSBwcm9jLnJldHVybmNvZGUpCiAgICAgICAgaWYgaGVhbHRoX29rKFBVRVJUT19ERUYsIHRpbWVv
dXQ9MS41KToKICAgICAgICAgICAgbG9nZi5jbG9zZSgpCiAgICAgICAgICAgIHJldHVybiBwcm9j
LCB0aW1lLnRpbWUoKSAtIHQwLCAib2siCiAgICAgICAgdGltZS5zbGVlcCgxLjApCiAgICB0cnk6
CiAgICAgICAgcHJvYy50ZXJtaW5hdGUoKQogICAgICAgIHByb2Mud2FpdCh0aW1lb3V0PTEwKQog
ICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICB0cnk6CiAgICAgICAgICAgIHByb2Mua2lsbCgp
CiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgcGFzcwogICAgbG9nZi5jbG9z
ZSgpCiAgICByZXR1cm4gTm9uZSwgdGltZS50aW1lKCkgLSB0MCwgInRpbWVvdXQgZGUgY2FyZ2Eg
KCVkIHMpIiAlIGNhcmdhX3RpbWVvdXQKCgpkZWYgYXBhZ2FyX3NlcnZlcihwcm9jKToKICAgIHRy
eToKICAgICAgICBwcm9jLnRlcm1pbmF0ZSgpCiAgICAgICAgcHJvYy53YWl0KHRpbWVvdXQ9MTUp
CiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHRyeToKICAgICAgICAgICAgcHJvYy5raWxs
KCkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBwYXNzCiAgICB0aW1lLnNs
ZWVwKDIpCgoKZGVmIGNvbGFfbG9nKGxvZ19wYXRoLCBuPTEyKToKICAgICIiIlVsdGltYXMgbGlu
ZWFzIGRlbCBsb2cgZGVsIHNlcnZlciAoZGlhZ25vc3RpY28gcmFwaWRvIGRlIGZhbGxvcykuIiIi
CiAgICB0cnk6CiAgICAgICAgbGluZWFzID0gb3Blbihsb2dfcGF0aCwgInJiIikucmVhZCgpLmRl
Y29kZSgKICAgICAgICAgICAgInV0Zi04IiwgZXJyb3JzPSJyZXBsYWNlIikuc3BsaXRsaW5lcygp
CiAgICAgICAgdml2YXMgPSBbbC5zdHJpcCgpIGZvciBsIGluIGxpbmVhcyBpZiBsLnN0cmlwKCld
CiAgICAgICAgcmV0dXJuICIgfCAiLmpvaW4odml2YXNbLW46XSlbOjcwMF0KICAgIGV4Y2VwdCBF
eGNlcHRpb246CiAgICAgICAgcmV0dXJuICIobG9nIG5vIGRpc3BvbmlibGUpIgoKCmRlZiBsZWVy
X2xvZ19zZXJ2ZXIobG9nX3BhdGgsIG1vZGVsb19iYXNlbmFtZT1Ob25lLCBwdWVydG89Tm9uZSk6
CiAgICAiIiJMZWUgZWwgbG9nIGRlbCBzZXJ2ZXIgeSBleHRyYWUgbGEgaWRlbnRpZGFkICsgbG9z
IENFUlRJRklDQURPUyBkZWwKICAgIE4zOiB3YXJuaW5nIGRlIGNhY2hlX3JldXNlICgjMjQwNTUp
LCBsaW5lYXMgcmVzdG9yZWQvZm9yY2luZyAoIzIxODMxKSwKICAgIHN5c3RlbV9pbmZvIChVU0Vf
R1JBUEhTL1JFUEFDSyksIGZpdCBhYm9ydGFkbyB2cyBkZWNsaW5hZG8sIHN5c21lbS4iIiIKICAg
IHRyeToKICAgICAgICB0eHQgPSBvcGVuKGxvZ19wYXRoLCAicmIiKS5yZWFkKCkuZGVjb2RlKCJ1
dGYtOCIsIGVycm9ycz0icmVwbGFjZSIpCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHJl
dHVybiB7fQogICAgbG93ID0gdHh0Lmxvd2VyKCkKICAgIGRhdG9zID0ge30KICAgICMgLS0tLSBp
ZGVudGlkYWQ6IG51bmNhIG1lZGlyIHVuIGZhbnRhc21hIC0tLS0KICAgIGlmIG1vZGVsb19iYXNl
bmFtZSBpcyBub3QgTm9uZToKICAgICAgICBkYXRvc1sibW9kZWxvX2VuX2xvZyJdID0gbW9kZWxv
X2Jhc2VuYW1lLmxvd2VyKCkgaW4gdHh0Lmxvd2VyKCkKICAgIGlmIHB1ZXJ0byBpcyBub3QgTm9u
ZToKICAgICAgICBkYXRvc1sicHVlcnRvX2VuX2xvZyJdID0gKCJsaXN0ZW5pbmcgb24iIGluIGxv
dwogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgYW5kICgiOiVkIiAlIHB1ZXJ0bykg
aW4gbG93KQogICAgIyAtLS0tIGNlcnRpZmljYWRvcyBkZSBjYWNoZSAoTjMgU1MzLjMvU1MxMC4z
L1NTMTQpIC0tLS0KICAgIGRhdG9zWyJjYWNoZV9yZXVzZV93YXJuIl0gPSAoImNhY2hlX3JldXNl
IGlzIG5vdCBzdXBwb3J0ZWQiIGluIGxvdykKICAgIGRhdG9zWyJjYWNoZV9yZXN0b3JlZF9uIl0g
PSBsZW4oCiAgICAgICAgcmUuZmluZGFsbChyInJlc3RvcmVkIGNvbnRleHQgY2hlY2twb2ludCIs
IGxvdykpCiAgICBkYXRvc1siY2FjaGVfZm9yY2luZ19uIl0gPSBsZW4oCiAgICAgICAgcmUuZmlu
ZGFsbChyImZvcmNpbmcgZnVsbCBwcm9tcHQgcmUtcHJvY2Vzc2luZyIsIGxvdykpCiAgICBtID0g
cmUuc2VhcmNoKHIic3lzdGVtX2luZm86W15cclxuXSoiLCB0eHQpCiAgICBzaSA9IG0uZ3JvdXAo
MCkgaWYgbSBlbHNlICIiCiAgICBkYXRvc1siZ3JhcGhzX29rIl0gPSAoIlVTRV9HUkFQSFMgPSAx
IiBpbiBzaSkKICAgIGRhdG9zWyJyZXBhY2tfb2siXSA9ICgiUkVQQUNLID0gMSIgaW4gc2kpCiAg
ICAjIC0tLS0gZml0IGFib3J0YWRvIHZzIGRlY2xpbmFkbyAobGVjY2lvbiB2MS4yLjEgZGVsIE4x
KSAtLS0tCiAgICBkYXRvc1siZml0X2Fib3J0Il0gPSBGYWxzZQogICAgZGF0b3NbImZpdF9pbmZv
Il0gPSAiIgogICAgbWZpdCA9IHJlLnNlYXJjaChyImZhaWxlZCB0byBmaXQgcGFyYW1zW15cclxu
XSoiLCB0eHQpCiAgICBpZiBtZml0OgogICAgICAgIGlmICJhbHJlYWR5IHNldCBieSB1c2VyIiBp
biBtZml0Lmdyb3VwKDApOgogICAgICAgICAgICBkYXRvc1siZml0X2luZm8iXSA9ICgiYXV0by1m
aXQgZGVjbGlubyAobmdsIHlhIGZpamFkbyBwb3IgIgogICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAidXN1YXJpbzsgZXNwZXJhZG8sIGJlbmlnbm8pIikKICAgICAgICBlbHNlOgogICAg
ICAgICAgICBkYXRvc1siZml0X2Fib3J0Il0gPSBUcnVlCiAgICBpZiAiZmFpbGVkIHRvIGFsbG9j
YXRlIiBpbiBsb3c6CiAgICAgICAgZGF0b3NbImZpdF9hYm9ydCJdID0gVHJ1ZQogICAgZGF0b3Nb
InN5c21lbV93YXJuIl0gPSAoInN5c21lbSBmYWxsYmFjayIgaW4gbG93CiAgICAgICAgICAgICAg
ICAgICAgICAgICAgICBvciAic2hhcmVkIG1lbW9yeSIgaW4gbG93KQogICAgcmV0dXJuIGRhdG9z
CgoKZGVmIHZyYW1fbnZpZGlhKCk6CiAgICB0cnk6CiAgICAgICAgb3V0ID0gc3VicHJvY2Vzcy5y
dW4oCiAgICAgICAgICAgIFsibnZpZGlhLXNtaSIsICItLXF1ZXJ5LWdwdT1tZW1vcnkudXNlZCxt
ZW1vcnkudG90YWwiLAogICAgICAgICAgICAgIi0tZm9ybWF0PWNzdixub2hlYWRlcixub3VuaXRz
Il0sCiAgICAgICAgICAgIGNhcHR1cmVfb3V0cHV0PVRydWUsIHRpbWVvdXQ9MTUpCiAgICAgICAg
bGluZWEgPSBvdXQuc3Rkb3V0LmRlY29kZSgidXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiKS5zdHJp
cCgpLnNwbGl0bGluZXMoKQogICAgICAgIGlmIG5vdCBsaW5lYToKICAgICAgICAgICAgcmV0dXJu
IE5vbmUKICAgICAgICB1c2FkYSwgdG90YWwgPSBsaW5lYVswXS5zcGxpdCgiLCIpWzoyXQogICAg
ICAgIHJldHVybiBpbnQodXNhZGEuc3RyaXAoKSksIGludCh0b3RhbC5zdHJpcCgpKQogICAgZXhj
ZXB0IEV4Y2VwdGlvbjoKICAgICAgICByZXR1cm4gTm9uZQoKCmRlZiByYW1fc2lzdGVtYSgpOgog
ICAgIiIiKGxpYnJlX21pYiwgdG90YWxfbWliKSBkZWwgc2lzdGVtYS4gV2luZG93czogR2xvYmFs
TWVtb3J5U3RhdHVzRXgKICAgIChjdHlwZXMsIHNpbiBkZXBlbmRlbmNpYXMpOyBMaW51eDogL3By
b2MvbWVtaW5mbzsgb3RybzogTm9uZS4gTnVuY2EKICAgIGVzIGZhdGFsLiIiIgogICAgdHJ5Ogog
ICAgICAgIGlmIG9zLm5hbWUgPT0gIm50IjoKICAgICAgICAgICAgaW1wb3J0IGN0eXBlcwoKICAg
ICAgICAgICAgY2xhc3MgTUVNT1JZU1RBVFVTRVgoY3R5cGVzLlN0cnVjdHVyZSk6CiAgICAgICAg
ICAgICAgICBfZmllbGRzXyA9IFsoImR3TGVuZ3RoIiwgY3R5cGVzLmNfdWxvbmcpLAogICAgICAg
ICAgICAgICAgICAgICAgICAgICAgKCJkd01lbW9yeUxvYWQiLCBjdHlwZXMuY191bG9uZyksCiAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAoInVsbFRvdGFsUGh5cyIsIGN0eXBlcy5jX3Vsb25n
bG9uZyksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAoInVsbEF2YWlsUGh5cyIsIGN0eXBl
cy5jX3Vsb25nbG9uZyksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAoInVsbFRvdGFsUGFn
ZUZpbGUiLCBjdHlwZXMuY191bG9uZ2xvbmcpLAogICAgICAgICAgICAgICAgICAgICAgICAgICAg
KCJ1bGxBdmFpbFBhZ2VGaWxlIiwgY3R5cGVzLmNfdWxvbmdsb25nKSwKICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICgidWxsVG90YWxWaXJ0dWFsIiwgY3R5cGVzLmNfdWxvbmdsb25nKSwKICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICgidWxsQXZhaWxWaXJ0dWFsIiwgY3R5cGVzLmNfdWxv
bmdsb25nKSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICgidWxsQXZhaWxFeHRlbmRlZFZp
cnR1YWwiLCBjdHlwZXMuY191bG9uZ2xvbmcpXQoKICAgICAgICAgICAgc3QgPSBNRU1PUllTVEFU
VVNFWCgpCiAgICAgICAgICAgIHN0LmR3TGVuZ3RoID0gY3R5cGVzLnNpemVvZihNRU1PUllTVEFU
VVNFWCkKICAgICAgICAgICAgY3R5cGVzLndpbmRsbC5rZXJuZWwzMi5HbG9iYWxNZW1vcnlTdGF0
dXNFeChjdHlwZXMuYnlyZWYoc3QpKQogICAgICAgICAgICByZXR1cm4gKGludChzdC51bGxBdmFp
bFBoeXMgLy8gKDEwMjQgKiAxMDI0KSksCiAgICAgICAgICAgICAgICAgICAgaW50KHN0LnVsbFRv
dGFsUGh5cyAvLyAoMTAyNCAqIDEwMjQpKSkKICAgICAgICBpZiBvcy5uYW1lID09ICJwb3NpeCI6
CiAgICAgICAgICAgIGQgPSB7fQogICAgICAgICAgICB3aXRoIG9wZW4oIi9wcm9jL21lbWluZm8i
KSBhcyBmOgogICAgICAgICAgICAgICAgZm9yIGxpbmUgaW4gZjoKICAgICAgICAgICAgICAgICAg
ICBwYXJ0cyA9IGxpbmUuc3BsaXQoKQogICAgICAgICAgICAgICAgICAgIGlmIGxlbihwYXJ0cykg
Pj0gMjoKICAgICAgICAgICAgICAgICAgICAgICAgZFtwYXJ0c1swXS5yc3RyaXAoIjoiKV0gPSBp
bnQocGFydHNbMV0pICAjIGtCCiAgICAgICAgICAgIGxpYnJlID0gZC5nZXQoIk1lbUF2YWlsYWJs
ZSIsIGQuZ2V0KCJNZW1GcmVlIikpCiAgICAgICAgICAgIGlmIGxpYnJlIGlzIG5vdCBOb25lIGFu
ZCAiTWVtVG90YWwiIGluIGQ6CiAgICAgICAgICAgICAgICByZXR1cm4gKGxpYnJlIC8vIDEwMjQs
IGRbIk1lbVRvdGFsIl0gLy8gMTAyNCkKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcGFz
cwogICAgcmV0dXJuIE5vbmUKCgpkZWYgcmFtX3Byb2Nlc29fbWliKHBpZCk6CiAgICAiIiJXb3Jr
aW5nU2V0IGRlbCBwcm9jZXNvIHNlcnZlciBlbiBNaUIgKFdpbmRvd3MgdmlhIEdldC1DaW1JbnN0
YW5jZSksCiAgICBvIE5vbmUgZnVlcmEgZGUgV2luZG93cyAvIHNpIGxhIGNvbnN1bHRhIGZhbGxh
LiBOdW5jYSBlcyBmYXRhbC4iIiIKICAgIGlmIG9zLm5hbWUgIT0gIm50IiBvciBub3QgcGlkOgog
ICAgICAgIHJldHVybiBOb25lCiAgICB0cnk6CiAgICAgICAgb3V0ID0gc3VicHJvY2Vzcy5ydW4o
CiAgICAgICAgICAgIFsicG93ZXJzaGVsbCIsICItTm9Qcm9maWxlIiwgIi1Db21tYW5kIiwKICAg
ICAgICAgICAgICIoR2V0LUNpbUluc3RhbmNlIFdpbjMyX1Byb2Nlc3MgLUZpbHRlciAnUHJvY2Vz
c0lkPSVkJykiCiAgICAgICAgICAgICAiLldvcmtpbmdTZXRTaXplIiAlIGludChwaWQpXSwKICAg
ICAgICAgICAgY2FwdHVyZV9vdXRwdXQ9VHJ1ZSwgdGltZW91dD0zMCkKICAgICAgICB0eHQgPSAo
b3V0LnN0ZG91dCBvciBiIiIpLmRlY29kZSgidXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiKS5zdHJp
cCgpCiAgICAgICAgcmV0dXJuIHJvdW5kKGludCh0eHQpIC8gKDEwMjQgKiAxMDI0KSwgMSkgaWYg
dHh0LmlzZGlnaXQoKSBlbHNlIE5vbmUKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcmV0
dXJuIE5vbmUKCgojIC0tLS0tLS0tLS0tLS0gcHJldnVlbG8gY29tcGxldG86IFBDICsgbW9kZWxv
ICsgbml2ZWwgKFJvbmRhIDI5KSAtLS0tLS0tLS0tLS0tCiMgUGVkaWRvIERpcmVjdG9yOiAiaGF6
bG8gY29tcGxldG8gY29uIHRvZG8gbG8gcXVlIHZhIGEgbmVjZXNpdGFyIHNhYmVyIHNvYnJlCiMg
bWkgcGMsIGVsIG1vZGVsbyB5IHRvZG8gc29icmUgZWwgbml2ZWwgZW4gZWwgcXVlIGVzdGFtb3Mg
YW50ZXMgZGUgY29tZW56YXIiLgojIFRPRE8gbm8tZmF0YWw6IHNpIHVuYSBwaWV6YSBubyBleGlz
dGUgKGZ1ZXJhIGRlIFdpbmRvd3MsIHNpbiBudmlkaWEtc21pKSwKIyBxdWVkYSBsYSBub3RhICIo
bm8gZGlzcG9uaWJsZSkiIHkgZWwgYmFycmlkbyBzaWd1ZS4KCl9DTEFWRVNfR0dVRiA9ICggICAj
IGZpbHRybyBwb3N0LXBhcnNlbyAoc3Vic3RyaW5nL2Zpbik6IGxvIHF1ZSB2YSBhbCBpbmZvcm1l
CiAgICAiZ2VuZXJhbC5hcmNoaXRlY3R1cmUiLCAiZ2VuZXJhbC5uYW1lIiwgImdlbmVyYWwuc2l6
ZV9sYWJlbCIsCiAgICAiZ2VuZXJhbC5maWxlX3R5cGUiLCAiZ2VuZXJhbC5xdWFudGl6YXRpb25f
aW1hdHJpeCIsCiAgICAiLmV4cGVydF9jb3VudCIsICIuZXhwZXJ0X3VzZWRfY291bnQiLCAiLmV4
cGVydF9mZWVkX2ZvcndhcmRfbGVuZ3RoIiwKICAgICIuY29udGV4dF9sZW5ndGgiLCAiLmJsb2Nr
X2NvdW50IiwgIi5lbWJlZGRpbmdfbGVuZ3RoIiwKICAgICIuYXR0ZW50aW9uLmhlYWRfY291bnQi
LCAiLmF0dGVudGlvbi5rZXlfbGVuZ3RoIiwKICAgICJuZXh0biIsICJzaGFyZWRfZXhwZXJ0Iiwg
InRva2VuaXplci5nZ21sLm1vZGVsIiwKKQpfVEFNX0dHVUYgPSB7MDogMSwgMTogMSwgMjogMiwg
MzogMiwgNDogNCwgNTogNCwgNjogNCwgNzogMSwKICAgICAgICAgICAgIDEwOiA4LCAxMTogOCwg
MTI6IDh9Cl9GTVRfR0dVRiA9IHswOiAiPEIiLCAxOiAiPGIiLCAyOiAiPEgiLCAzOiAiPGgiLCA0
OiAiPEkiLCA1OiAiPGkiLAogICAgICAgICAgICAgNjogIjxmIiwgNzogIjw/IiwgMTA6ICI8USIs
IDExOiAiPHEiLCAxMjogIjxkIn0KCgpjbGFzcyBfTGVjdG9yOgogICAgIiIiTGVjdG9yIGNvbiBi
dWZmZXIgZGUgMSBNaUIgKGxlY2Npb24gZGVsIHBhcnNlciBOMSByb25kYSAxNCk6IGV2aXRhIHVu
CiAgICBzeXNjYWxsIHBvciBjYW1wbyBlbiBjYWJlY2VyYXMgZ3JhbmRlcyAodG9rZW5pemVyID0g
ZGVjZW5hcyBkZSBtaWxlcyBkZQogICAgc3RyaW5ncykgeSBzYWx0YSBzaW4gbWF0ZXJpYWxpemFy
IGNvbiBzZWVrIHJlbGF0aXZvLiIiIgoKICAgIGRlZiBfX2luaXRfXyhzZWxmLCBmLCB0YW09MSA8
PCAyMCk6CiAgICAgICAgc2VsZi5mLCBzZWxmLnRhbSA9IGYsIHRhbQogICAgICAgIHNlbGYuYnVm
ID0gYiIiCiAgICAgICAgc2VsZi5wb3MgPSAwCgogICAgZGVmIF9sbGVuYXIoc2VsZiwgbik6CiAg
ICAgICAgd2hpbGUgbGVuKHNlbGYuYnVmKSAtIHNlbGYucG9zIDwgbjoKICAgICAgICAgICAgY2h1
bmsgPSBzZWxmLmYucmVhZChtYXgoc2VsZi50YW0sIG4pKQogICAgICAgICAgICBpZiBub3QgY2h1
bms6CiAgICAgICAgICAgICAgICByYWlzZSBFT0ZFcnJvcigiR0dVRiB0cnVuY2FkbyIpCiAgICAg
ICAgICAgIHJlc3RvID0gc2VsZi5idWZbc2VsZi5wb3M6XSArIGNodW5rCiAgICAgICAgICAgIHNl
bGYuYnVmLCBzZWxmLnBvcyA9IHJlc3RvLCAwCgogICAgZGVmIGxlZXIoc2VsZiwgbik6CiAgICAg
ICAgc2VsZi5fbGxlbmFyKG4pCiAgICAgICAgZCA9IHNlbGYuYnVmW3NlbGYucG9zOnNlbGYucG9z
ICsgbl0KICAgICAgICBzZWxmLnBvcyArPSBuCiAgICAgICAgcmV0dXJuIGQKCiAgICBkZWYgdTMy
KHNlbGYpOgogICAgICAgIHJldHVybiBzdHJ1Y3QudW5wYWNrKCI8SSIsIHNlbGYubGVlcig0KSlb
MF0KCiAgICBkZWYgdTY0KHNlbGYpOgogICAgICAgIHJldHVybiBzdHJ1Y3QudW5wYWNrKCI8USIs
IHNlbGYubGVlcig4KSlbMF0KCiAgICBkZWYgY2FkZW5hKHNlbGYpOgogICAgICAgIG4gPSBzZWxm
LnU2NCgpCiAgICAgICAgcmV0dXJuIHNlbGYubGVlcihuKS5kZWNvZGUoInV0Zi04IiwgZXJyb3Jz
PSJyZXBsYWNlIikKCiAgICBkZWYgc2FsdGFyKHNlbGYsIG4pOgogICAgICAgIGRpc3AgPSBsZW4o
c2VsZi5idWYpIC0gc2VsZi5wb3MKICAgICAgICBpZiBuIDw9IGRpc3A6CiAgICAgICAgICAgIHNl
bGYucG9zICs9IG4KICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgbiAtPSBkaXNwCiAgICAgICAg
c2VsZi5idWYsIHNlbGYucG9zID0gYiIiLCAwCiAgICAgICAgc2VsZi5mLnNlZWsobiwgMSkKCgpk
ZWYgZ2d1Zl9tZXRhZGF0b3MocnV0YSk6CiAgICAiIiJMZWUgU09MTyBsYSBjYWJlY2VyYSBHR1VG
IChrdnM7IGNlcm8gdGVuc29yZXMpIHkgZGV2dWVsdmUKICAgIChtZXRhZGF0b3NfZmlsdHJhZG9z
LCBOb25lKSBvIChOb25lLCBlcnJvcikuIExhcyBjbGF2ZXMgZGUgaW50ZXJlcwogICAgKF9DTEFW
RVNfR0dVRikgaW5jbHV5ZW4gbmV4dG4gKE1UUCBwcmVzZXJ2ZWQpIHkgZXhwZXJ0X3VzZWRfY291
bnQgZGUKICAgIGZhYnJpY2EuIE51bmNhIGVzIGZhdGFsLiIiIgogICAgdHJ5OgogICAgICAgIHdp
dGggb3BlbihydXRhLCAicmIiKSBhcyBmOgogICAgICAgICAgICBsZSA9IF9MZWN0b3IoZikKICAg
ICAgICAgICAgaWYgbGUubGVlcig0KSAhPSBiIkdHVUYiOgogICAgICAgICAgICAgICAgcmV0dXJu
IE5vbmUsICJubyBlcyBHR1VGIChtYWdpYyBkaXN0aW50bykiCiAgICAgICAgICAgIHZlcnNpb24g
PSBsZS51MzIoKQogICAgICAgICAgICBsZS51NjQoKSAgICAgICAgICAgICAgICAgICAgICAgIyB0
ZW5zb3JfY291bnQgKG5vIGxvIHJlY29ycmVtb3MpCiAgICAgICAgICAgIG5fa3YgPSBsZS51NjQo
KQogICAgICAgICAgICBjcnVkb3MgPSB7fQogICAgICAgICAgICBmb3IgXyBpbiByYW5nZShuX2t2
KToKICAgICAgICAgICAgICAgIGNsYXZlID0gbGUuY2FkZW5hKCkKICAgICAgICAgICAgICAgIHRp
cG8gPSBsZS51MzIoKQogICAgICAgICAgICAgICAgaWYgdGlwbyA9PSA4OiAgICAgICAgICAgICAg
IyBzdHJpbmcKICAgICAgICAgICAgICAgICAgICBuID0gbGUudTY0KCkKICAgICAgICAgICAgICAg
ICAgICBpZiBuIDw9IDY1NTM2OgogICAgICAgICAgICAgICAgICAgICAgICBjcnVkb3NbY2xhdmVd
ID0gbGUubGVlcihuKS5kZWNvZGUoCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAidXRmLTgi
LCBlcnJvcnM9InJlcGxhY2UiKQogICAgICAgICAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAg
ICAgICAgICAgICAgIGxlLnNhbHRhcihuKQogICAgICAgICAgICAgICAgZWxpZiB0aXBvID09IDk6
ICAgICAgICAgICAgIyBhcnJheTogc2Ugc2FsdGEgZW50ZXJvCiAgICAgICAgICAgICAgICAgICAg
ZXRpcG8gPSBsZS51MzIoKQogICAgICAgICAgICAgICAgICAgIG4gPSBsZS51NjQoKQogICAgICAg
ICAgICAgICAgICAgIGlmIGV0aXBvID09IDg6CiAgICAgICAgICAgICAgICAgICAgICAgIGZvciBf
IGluIHJhbmdlKG4pOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgbGUuc2FsdGFyKGxlLnU2
NCgpKQogICAgICAgICAgICAgICAgICAgIGVsaWYgZXRpcG8gaW4gX1RBTV9HR1VGOgogICAgICAg
ICAgICAgICAgICAgICAgICBsZS5zYWx0YXIobiAqIF9UQU1fR0dVRltldGlwb10pCiAgICAgICAg
ICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAgICAgICAgcmV0dXJuIE5vbmUsICgi
YXJyYXkgY29uIHRpcG8gZGUgZWxlbWVudG8gIgogICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICJkZXNjb25vY2lkbyAlZCIgJSBldGlwbykKICAgICAgICAgICAgICAgIGVsaWYg
dGlwbyBpbiBfVEFNX0dHVUY6CiAgICAgICAgICAgICAgICAgICAgdiA9IHN0cnVjdC51bnBhY2so
X0ZNVF9HR1VGW3RpcG9dLCBsZS5sZWVyKF9UQU1fR0dVRlt0aXBvXSkpWzBdCiAgICAgICAgICAg
ICAgICAgICAgY3J1ZG9zW2NsYXZlXSA9IGJvb2wodikgaWYgdGlwbyA9PSA3IGVsc2UgdgogICAg
ICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAgICByZXR1cm4gTm9uZSwgInRpcG8g
R0dVRiBkZXNjb25vY2lkbyAlZCIgJSB0aXBvCiAgICAgICAgbWV0YWRhdG9zID0geyJnZ3VmX3Zl
cnNpb24iOiB2ZXJzaW9ufQogICAgICAgIGZvciBrLCB2IGluIHNvcnRlZChjcnVkb3MuaXRlbXMo
KSk6CiAgICAgICAgICAgIGlmIGFueShrID09IGMgb3Igay5lbmRzd2l0aChjKSBvciBjIGluIGsg
Zm9yIGMgaW4gX0NMQVZFU19HR1VGKToKICAgICAgICAgICAgICAgIG1ldGFkYXRvc1trXSA9IHYK
ICAgICAgICByZXR1cm4gbWV0YWRhdG9zLCBOb25lCiAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6
CiAgICAgICAgcmV0dXJuIE5vbmUsIHJlcHIoZSkKCgpkZWYgc2hhMjU2X2FyY2hpdm8ocnV0YSwg
bm90aWZpY2Fkb3I9Tm9uZSk6CiAgICAiIiJTSEEyNTYgZW4gc3RyZWFtaW5nICgxIE1pQiBwb3Ig
cGFzbyk7IGF2YW56YSBjYWRhIH4yIEdCIHNpIGhheQogICAgbm90aWZpY2Fkb3IuIENlcnRpZmlj
YSBFTCBhcmNoaXZvIGV4YWN0byAoY3VhbnQgY29ycmVjdG8sIE4yKS4iIiIKICAgIGggPSBoYXNo
bGliLnNoYTI1NigpCiAgICB0YW0gPSBvcy5wYXRoLmdldHNpemUocnV0YSkKICAgIGhlY2hvLCBw
cm94ID0gMCwgMiA8PCAzMAogICAgd2l0aCBvcGVuKHJ1dGEsICJyYiIpIGFzIGY6CiAgICAgICAg
d2hpbGUgVHJ1ZToKICAgICAgICAgICAgY2h1bmsgPSBmLnJlYWQoMSA8PCAyMCkKICAgICAgICAg
ICAgaWYgbm90IGNodW5rOgogICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgaC51cGRh
dGUoY2h1bmspCiAgICAgICAgICAgIGhlY2hvICs9IGxlbihjaHVuaykKICAgICAgICAgICAgaWYg
bm90aWZpY2Fkb3IgYW5kIGhlY2hvID49IHByb3ggYW5kIHRhbSA+ICgxIDw8IDMwKToKICAgICAg
ICAgICAgICAgIG5vdGlmaWNhZG9yKCIgIHNoYTI1Ni4uLiAlZC8lZCBHQiIgJSAoaGVjaG8gPj4g
MzAsIHRhbSA+PiAzMCkpCiAgICAgICAgICAgICAgICBwcm94ICs9IDIgPDwgMzAKICAgIHJldHVy
biBoLmhleGRpZ2VzdCgpCgoKZGVmIF9wc19qc29uKGNvbWFuZG9fcHMsIHRpbWVvdXQ9NjApOgog
ICAgIiIiRWplY3V0YSB1bmEgY29uc3VsdGEgUG93ZXJTaGVsbCAoR2V0LUNpbUluc3RhbmNlIC4u
LiBDb252ZXJ0VG8tSnNvbikgeQogICAgZGV2dWVsdmUgbGlzdGEvZGljdCwgbyBOb25lIGZ1ZXJh
IGRlIFdpbmRvd3MgLyBzaSBmYWxsYS4gTnVuY2EgZXMgZmF0YWwuIiIiCiAgICBpZiBvcy5uYW1l
ICE9ICJudCI6CiAgICAgICAgcmV0dXJuIE5vbmUKICAgIHRyeToKICAgICAgICBvdXQgPSBzdWJw
cm9jZXNzLnJ1bihbInBvd2Vyc2hlbGwiLCAiLU5vUHJvZmlsZSIsICItQ29tbWFuZCIsCiAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgIGNvbWFuZG9fcHNdLCBjYXB0dXJlX291dHB1dD1UcnVl
LCB0aW1lb3V0PXRpbWVvdXQpCiAgICAgICAgdHh0ID0gKG91dC5zdGRvdXQgb3IgYiIiKS5kZWNv
ZGUoInV0Zi04IiwgZXJyb3JzPSJyZXBsYWNlIikuc3RyaXAoKQogICAgICAgIGlmIG5vdCB0eHQ6
CiAgICAgICAgICAgIHJldHVybiBOb25lCiAgICAgICAgZCA9IGpzb24ubG9hZHModHh0KQogICAg
ICAgIGlmIGlzaW5zdGFuY2UoZCwgZGljdCk6CiAgICAgICAgICAgIGQgPSBbZF0KICAgICAgICBy
ZXR1cm4gZAogICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICByZXR1cm4gTm9uZQoKCmRlZiBk
b3NzaWVyX3BjKGNvbl9udmlkaWE9VHJ1ZSk6CiAgICAiIiJFc3RhY2lvbiAwLjEgZGVsIHByZXZ1
ZWxvOiBlbCBoYXJkd2FyZSB5IGVsIGVzdGFkbyBkZWwgZGlhLiIiIgogICAgZCA9IHt9CiAgICBz
b3MgPSBfcHNfanNvbigiR2V0LUNpbUluc3RhbmNlIFdpbjMyX09wZXJhdGluZ1N5c3RlbSB8IFNl
bGVjdC1PYmplY3QgIgogICAgICAgICAgICAgICAgICAgIkNhcHRpb24sVmVyc2lvbixCdWlsZE51
bWJlcixPU0FyY2hpdGVjdHVyZSxMYXN0Qm9vdFVwVGltZSIKICAgICAgICAgICAgICAgICAgICIg
fCBDb252ZXJ0VG8tSnNvbiAtQ29tcHJlc3MiKQogICAgaWYgc29zOgogICAgICAgIHMgPSBzb3Nb
MF0KICAgICAgICBkWyJzbyJdID0gIiVzIMK3ICVzIMK3IGJ1aWxkICVzICh2ZXJzaW9uICVzKSIg
JSAoCiAgICAgICAgICAgIHMuZ2V0KCJDYXB0aW9uIikgb3IgIj8iLCBzLmdldCgiT1NBcmNoaXRl
Y3R1cmUiKSBvciAiPyIsCiAgICAgICAgICAgIHMuZ2V0KCJCdWlsZE51bWJlciIpIG9yICI/Iiwg
cy5nZXQoIlZlcnNpb24iKSBvciAiPyIpCiAgICAgICAgbSA9IHJlLm1hdGNoKHIiKFxkezE0fSki
LCBzdHIocy5nZXQoIkxhc3RCb290VXBUaW1lIikgb3IgIiIpKQogICAgICAgIGlmIG06CiAgICAg
ICAgICAgIHRyeToKICAgICAgICAgICAgICAgIGFycmFuY28gPSBkYXRldGltZS5kYXRldGltZS5z
dHJwdGltZShtLmdyb3VwKDEpLCAiJVklbSVkJUglTSVTIikKICAgICAgICAgICAgICAgIGRbImVu
Y2VuZGlkb19ob3JhcyJdID0gcm91bmQoCiAgICAgICAgICAgICAgICAgICAgKGRhdGV0aW1lLmRh
dGV0aW1lLm5vdygpIC0gYXJyYW5jbykudG90YWxfc2Vjb25kcygpIC8gMzYwMCwgMSkKICAgICAg
ICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgICAgIHBhc3MKICAgIGNwdXMgPSBf
cHNfanNvbigiR2V0LUNpbUluc3RhbmNlIFdpbjMyX1Byb2Nlc3NvciB8IFNlbGVjdC1PYmplY3Qg
TmFtZSwiCiAgICAgICAgICAgICAgICAgICAgIk51bWJlck9mQ29yZXMsTnVtYmVyT2ZMb2dpY2Fs
UHJvY2Vzc29ycyxNYXhDbG9ja1NwZWVkIgogICAgICAgICAgICAgICAgICAgICIgfCBDb252ZXJ0
VG8tSnNvbiAtQ29tcHJlc3MiKQogICAgaWYgY3B1czoKICAgICAgICBjID0gY3B1c1swXQogICAg
ICAgIGRbImNwdSJdID0gIiVzICglZCBudWNsZW9zIC8gJWQgaGlsb3MsICVzIE1IeiBtYXgpIiAl
ICgKICAgICAgICAgICAgc3RyKGMuZ2V0KCJOYW1lIikgb3IgIj8iKS5zdHJpcCgpLCBjLmdldCgi
TnVtYmVyT2ZDb3JlcyIpIG9yIDAsCiAgICAgICAgICAgIGMuZ2V0KCJOdW1iZXJPZkxvZ2ljYWxQ
cm9jZXNzb3JzIikgb3IgMCwKICAgICAgICAgICAgYy5nZXQoIk1heENsb2NrU3BlZWQiKSBvciAi
PyIpCiAgICBwYWxvcyA9IF9wc19qc29uKCJHZXQtQ2ltSW5zdGFuY2UgV2luMzJfUGh5c2ljYWxN
ZW1vcnkgfCBTZWxlY3QtT2JqZWN0ICIKICAgICAgICAgICAgICAgICAgICAgIkNhcGFjaXR5LFNw
ZWVkLENvbmZpZ3VyZWRDbG9ja1NwZWVkIHwgQ29udmVydFRvLUpzb24gIgogICAgICAgICAgICAg
ICAgICAgICAiLUNvbXByZXNzIikKICAgIGlmIHBhbG9zOgogICAgICAgIGNhcHMgPSBbaW50KHgu
Z2V0KCJDYXBhY2l0eSIpIG9yIDApIGZvciB4IGluIHBhbG9zXQogICAgICAgIHZlbHMgPSBzb3J0
ZWQoe3N0cih4LmdldCgiQ29uZmlndXJlZENsb2NrU3BlZWQiKQogICAgICAgICAgICAgICAgICAg
ICAgICAgICBvciB4LmdldCgiU3BlZWQiKSBvciAiPyIpIGZvciB4IGluIHBhbG9zfSkKICAgICAg
ICAjIEhPVEZJWCBjYW1wbyAyOC1vY3Q6IGVsIGxpdGVyYWwgaWJhIHBhcnRpZG8gZW4gZG9zIHN0
YXRlbWVudHMgc2luCiAgICAgICAgIyBwYXJlbnRlc2lzIC0+ICJzb24gMikiICUgKDMgYXJncykg
PSBUeXBlRXJyb3IgZW4gZWwgcmlnICgyIHBhbG9zKS4KICAgICAgICAjIExvcyBwYXJlbnRlc2lz
IHJlc3RhdXJhbiBsYSBjb25jYXRlbmFjaW9uIHkgZWwgJSBzb2JyZSBlbCBsaXRlcmFsCiAgICAg
ICAgIyBDT01QTEVUTyAoY2F6YWRvIGVuIGxhIHByaW1lcmEgY29ycmlkYSByZWFsIGRlbCBwcmV2
dWVsbykuCiAgICAgICAgZFsicmFtX2hhcmR3YXJlIl0gPSAoCiAgICAgICAgICAgICIlZCBtb2R1
bG9zLCAlcyBHQiBlbiB0b3RhbCBhICVzIE1UL3MgKGR1YWwgY2hhbm5lbCBzaSBzb24gMikiCiAg
ICAgICAgICAgICUgKGxlbihwYWxvcyksIGZtdChzdW0oY2FwcykgLyAoMTAyNCAqKiAzKSwgMSks
CiAgICAgICAgICAgICAgICIvIi5qb2luKHZlbHMpKSkKICAgIHBmID0gX3BzX2pzb24oIkdldC1D
aW1JbnN0YW5jZSBXaW4zMl9QYWdlRmlsZVVzYWdlIHwgU2VsZWN0LU9iamVjdCBOYW1lLCIKICAg
ICAgICAgICAgICAgICAgIkFsbG9jYXRlZEJhc2VTaXplLEN1cnJlbnRVc2FnZSxQZWFrVXNhZ2Ug
fCBDb252ZXJ0VG8tSnNvbiAiCiAgICAgICAgICAgICAgICAgICItQ29tcHJlc3MiKQogICAgaWYg
cGY6CiAgICAgICAgcCA9IHBmWzBdCiAgICAgICAgZFsicGFnZWZpbGUiXSA9ICIlcyByZXNlcnZh
ZG8gJXMgTUIgwrcgZW4gdXNvICVzIE1CIMK3IHBpY28gJXMgTUIiICUgKAogICAgICAgICAgICBw
LmdldCgiTmFtZSIpIG9yICI/IiwgcC5nZXQoIkFsbG9jYXRlZEJhc2VTaXplIikgb3IgIj8iLAog
ICAgICAgICAgICBwLmdldCgiQ3VycmVudFVzYWdlIikgb3IgIj8iLCBwLmdldCgiUGVha1VzYWdl
Iikgb3IgIj8iKQogICAgZGsgPSBfcHNfanNvbigiR2V0LUNpbUluc3RhbmNlIFdpbjMyX0xvZ2lj
YWxEaXNrIC1GaWx0ZXIgJ0RyaXZlVHlwZT0zJyB8ICIKICAgICAgICAgICAgICAgICAgIlNlbGVj
dC1PYmplY3QgRGV2aWNlSUQsU2l6ZSxGcmVlU3BhY2UgfCBDb252ZXJ0VG8tSnNvbiAiCiAgICAg
ICAgICAgICAgICAgICItQ29tcHJlc3MiKQogICAgaWYgZGs6CiAgICAgICAgcGFydGVzID0gW10K
ICAgICAgICBmb3IgeCBpbiBkazoKICAgICAgICAgICAgdG90ID0gaW50KHguZ2V0KCJTaXplIikg
b3IgMCkKICAgICAgICAgICAgbGliID0gaW50KHguZ2V0KCJGcmVlU3BhY2UiKSBvciAwKQogICAg
ICAgICAgICBpZiB0b3Q6CiAgICAgICAgICAgICAgICBwYXJ0ZXMuYXBwZW5kKCIlcyBsaWJyZSAl
cy8lcyBHQiIgJSAoCiAgICAgICAgICAgICAgICAgICAgeC5nZXQoIkRldmljZUlEIikgb3IgIj8i
LCBmbXQobGliIC8gKDEwMjQgKiogMyksIDApLAogICAgICAgICAgICAgICAgICAgIGZtdCh0b3Qg
LyAoMTAyNCAqKiAzKSwgMCkpKQogICAgICAgIGRbImRpc2NvcyJdID0gIiB8ICIuam9pbihwYXJ0
ZXMpCiAgICBpZiBjb25fbnZpZGlhOgogICAgICAgIHRyeToKICAgICAgICAgICAgb3V0ID0gc3Vi
cHJvY2Vzcy5ydW4oCiAgICAgICAgICAgICAgICBbIm52aWRpYS1zbWkiLCAiLS1xdWVyeS1ncHU9
bmFtZSxkcml2ZXJfdmVyc2lvbixtZW1vcnkudG90YWwsIgogICAgICAgICAgICAgICAgICJ0ZW1w
ZXJhdHVyZS5ncHUiLCAiLS1mb3JtYXQ9Y3N2LG5vaGVhZGVyLG5vdW5pdHMiXSwKICAgICAgICAg
ICAgICAgIGNhcHR1cmVfb3V0cHV0PVRydWUsIHRpbWVvdXQ9MTUpCiAgICAgICAgICAgIGxpbmVh
ID0gb3V0LnN0ZG91dC5kZWNvZGUoInV0Zi04IiwgZXJyb3JzPSJyZXBsYWNlIikuc3RyaXAoKQog
ICAgICAgICAgICBpZiBsaW5lYToKICAgICAgICAgICAgICAgIHAgPSBbcS5zdHJpcCgpIGZvciBx
IGluIGxpbmVhLnNwbGl0bGluZXMoKVswXS5zcGxpdCgiLCIpXQogICAgICAgICAgICAgICAgaWYg
bGVuKHApID49IDQ6CiAgICAgICAgICAgICAgICAgICAgZFsiZ3B1Il0gPSAiJXMgwrcgZHJpdmVy
ICVzIMK3ICVzIE1pQiDCtyAlcyBDIiAlIHR1cGxlKHBbOjRdKQogICAgICAgIGV4Y2VwdCBFeGNl
cHRpb246CiAgICAgICAgICAgIHBhc3MKICAgIHRyeToKICAgICAgICBvdXQgPSBzdWJwcm9jZXNz
LnJ1bihbInBvd2VyY2ZnIiwgIi9nZXRhY3RpdmVzY2hlbWUiXSwKICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICBjYXB0dXJlX291dHB1dD1UcnVlLCB0aW1lb3V0PTE1KQogICAgICAgIG0gPSBy
ZS5zZWFyY2gociJcKChbXildKylcKSIsIG91dC5zdGRvdXQuZGVjb2RlKAogICAgICAgICAgICAi
dXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiKSkKICAgICAgICBpZiBtOgogICAgICAgICAgICBkWyJw
bGFuX2VuZXJnaWEiXSA9IG0uZ3JvdXAoMSkKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAg
cGFzcwogICAgciA9IHJhbV9zaXN0ZW1hKCkKICAgIGlmIHI6CiAgICAgICAgZFsicmFtX2Fob3Jh
Il0gPSAibGlicmUgJXMgTWlCIGRlICVzIE1pQiAoJS4wZiUlIGVuIHVzbykiICUgKAogICAgICAg
ICAgICBmbXQoclswXSwgMCksIGZtdChyWzFdLCAwKSwgKDEgLSByWzBdIC8gclsxXSkgKiAxMDAp
CiAgICB0b3AgPSBfcHNfanNvbigiR2V0LVByb2Nlc3MgfCBTb3J0LU9iamVjdCBXUyAtRGVzY2Vu
ZGluZyB8ICIKICAgICAgICAgICAgICAgICAgICJTZWxlY3QtT2JqZWN0IC1GaXJzdCA0IE5hbWUs
QHtuPSdNQic7ZT17W21hdGhdOjpSb3VuZCgiCiAgICAgICAgICAgICAgICAgICAiJF8uV1MvMU1C
KX19IHwgQ29udmVydFRvLUpzb24gLUNvbXByZXNzIiwgdGltZW91dD00NSkKICAgIGlmIHRvcDoK
ICAgICAgICBkWyJyYW1fY29tZXBhbmVzIl0gPSAiLCAiLmpvaW4oCiAgICAgICAgICAgICIlcyAl
cyBNQiIgJSAoeC5nZXQoIk5hbWUiKSBvciAiPyIsIHguZ2V0KCJNQiIpIG9yICI/IikKICAgICAg
ICAgICAgZm9yIHggaW4gdG9wWzo0XSkKICAgIHJldHVybiBkCgoKZGVmIGRvc3NpZXJfbW9kZWxv
KHJ1dGEsIGJ5dGVzX21vZGVsbywgcGluLCBjb25fc2hhPVRydWUsIG5vdGlmaWNhZG9yPU5vbmUp
OgogICAgIiIiRXN0YWNpb24gMC4yOiBpZGVudGlkYWQgY2VydGlmaWNhZGEgZGVsIG1vZGVsbyAo
Ynl0ZXMsIFNIQTI1NiwgR0dVRikKICAgICsgdmVyc2lvbi9waW4gZGVsIHNlcnZlci4iIiIKICAg
IGQgPSB7InJ1dGEiOiBydXRhLCAiYnl0ZXMiOiBieXRlc19tb2RlbG8sCiAgICAgICAgICJieXRl
c19lc3BlcmFkb3MiOiBCWVRFU19NT0RFTE9fRVNQRVJBRE9TLAogICAgICAgICAiYnl0ZXNfb2si
OiBieXRlc19tb2RlbG8gPT0gQllURVNfTU9ERUxPX0VTUEVSQURPUywKICAgICAgICAgInNlcnZl
cl92ZXJzaW9uIjogcGluIG9yICJOL0QiLAogICAgICAgICAiYnVpbGRfZXNwZXJhZG8iOiBCVUlM
RF9QSU5fRVNQRVJBRE8sCiAgICAgICAgICJidWlsZF9vayI6IGJvb2wocGluKSBhbmQgQlVJTERf
UElOX0VTUEVSQURPIGluIHBpbn0KICAgIGlmIGNvbl9zaGE6CiAgICAgICAgZFsic2hhMjU2Il0g
PSBzaGEyNTZfYXJjaGl2byhydXRhLCBub3RpZmljYWRvcikKICAgIG1ldGEsIGVyciA9IGdndWZf
bWV0YWRhdG9zKHJ1dGEpCiAgICBpZiBlcnI6CiAgICAgICAgZFsiZ2d1Zl9lcnJvciJdID0gZXJy
CiAgICBlbGlmIG1ldGE6CiAgICAgICAgZFsiZ2d1ZiJdID0gbWV0YQogICAgcmV0dXJuIGQKCgpk
ZWYgZG9zc2llcl9uaXZlbChjb25maWdzKToKICAgICIiIkVzdGFjaW9uIDAuNDogZWwgZXN0YWRv
IGRlbCBuaXZlbCBOMyB5IGRlIGxhIGNhbXBhbmEsIGluY3J1c3RhZG8gY29tbwogICAgY29uc3Rh
bnRlcyAoZWwgcmlnIGNvcnJlIFNJTiBlbCByZXBvKS4gRnVlbnRlczogbml2ZWwtMyBTUzAtU1Mx
OSwKICAgIG5pdmVsLTEgU1MxNC1TUzMwLCBSRUFETUUgcm9uZGFzIDEyLzI0LzI4LiIiIgogICAg
cmV0dXJuIHsKICAgICAgICAiY2FtcGFuYSI6ICgiT3JkZW4gYXByb2JhZG8gKHJvbmRhIDEyKTog
TjEgLT4gTjMgLT4gTjIgLT4gTjQgLT4gIgogICAgICAgICAgICAgICAgICAgICJSVVRBIDAgKyBO
NS4gRXN0YWRvIGhveTogTjEgbWVkaWRvIChrPTggdGVjaG8gMjEuNTMgLyAiCiAgICAgICAgICAg
ICAgICAgICAgIms9NCArNDElID0gMjguODUtMjkuMTMgLyBrPTMgZmFsbGEgYXJpdG1ldGljYSAv
IGs9MiAiCiAgICAgICAgICAgICAgICAgICAgImNvbGFwc287IGZhbHRhIGJhcnJpZG8gZm9ybWFs
IHYxLjIuMSArIHNhbml0eSAyMCAiCiAgICAgICAgICAgICAgICAgICAgInByb21wdHMpIC0gTjMg
RU4gQ1VSU08gKGVzdGEgY29ycmlkYSkgLSBOMiwgTjQgeSAiCiAgICAgICAgICAgICAgICAgICAg
IlJVVEEgMCArIE41IHBlbmRpZW50ZXMuIiksCiAgICAgICAgInJlZnMiOiBbCiAgICAgICAgICAg
ICgiT1JPLVVCMUsgKHJlY2V0YSBkaWFyaWEsIGFuY2xhIGRlbCBiYXJyaWRvLTMwIGlkIDMyKSIs
CiAgICAgICAgICAgICAiMjEuNTMgdC9zIFtNXSIpLAogICAgICAgICAgICAoIk5DTTM3QzQgKGNv
bG9jYWNpb24gY2FtcGVvbmEsIGlkIDE0LCBTSU4gVUIxSyBlbmNpbWEpIiwKICAgICAgICAgICAg
ICIyMi40OSB0L3MgW01dIiksCiAgICAgICAgICAgICgiT1JPLUNSQU01MTIgKGRlY29kZSBpbnRh
Y3RvLCAtNy43IEdCIFJBTSkiLCAiMjEuNTcgdC9zIFtNXSIpLAogICAgICAgICAgICAoIk9STy1T
SElGVCAoc2hpZnQgKyByZXVzZSAyNTYsIHNpbiBjb3N0ZSkiLCAiMjEuMzkgdC9zIFtNXSIpLAog
ICAgICAgICAgICAoIms9NCBDSEFSTEEgKEQtRVhQNCAvIEQtRVhQNC1VQjFLLCArNDElKSIsCiAg
ICAgICAgICAgICAiMjguODUgLyAyOS4xMyB0L3MgW01dIiksCiAgICAgICAgICAgICgiU3VlbG8g
az04IGNvbiBsYSBNSVNNQSByZWNldGEgb3RybyBkaWEiLCAiMTcuMzYgLyAxNy44MCBbTV0iKSwK
ICAgICAgICAgICAgKCJUZWNobyBkZSBsYSBmYW1pbGlhIGZsYWdzIGs9OCAoc3dlZXAgTE1OT05F
KSIsICIyMS41MCBbTV0iKSwKICAgICAgICAgICAgKCJSdWlkbyBkZWNsYXJhZG8gLyBkaXNwZXJz
aW9uIGVudHJlIGNvcnJpZGFzIiwKICAgICAgICAgICAgICIrLy0wLjMtMC41IHQvcyDCtyA5LjQg
cHAgKHRoYzEwMDYgdjQpIiksCiAgICAgICAgXSwKICAgICAgICAibXVlcnRvcyI6IFsKICAgICAg
ICAgICAgIm5ncmFtIHNwZWM6IGFjY2VwdGFuY2UgMC4wMC0wLjE2IFtNXSAtIG11ZXJ0byIsCiAg
ICAgICAgICAgICJhZmluaWRhZCBDUFUtR1BVICgtb3QpOiAtOS4uLTM4JSBbTV0gLSBtdWVydG8i
LAogICAgICAgICAgICAiRklULUMgKGN1YW50IGNhY2hlIGYxNi0+cSk6IC0zOCUgW01dIC0gbXVl
cnRvIiwKICAgICAgICAgICAgInJlcGFjayBvZmY6IC01JSBbTV0gLSBtdWVydG8iLAogICAgICAg
ICAgICAiS1YgcTVfMTogMCUgZGUgY2FtYmlvIFtNXSAtIG11ZXJ0byIsCiAgICAgICAgICAgICJQ
T0xMOiBydWlkbyDCtyBUQjg6IG11ZXJ0byIsCiAgICAgICAgXSwKICAgICAgICAicGVuZGllbnRl
cyI6IFsKICAgICAgICAgICAgIlN0YWNrIFVCMUsgeCBOQ00zN0M0IChTUzEzLTEpOiBQUklNRVIg
ZGF0byA9IGlkIDggZGUgZXN0YSAiCiAgICAgICAgICAgICJjb3JyaWRhIChlbCAyMi40OSBoaXN0
b3JpY28gZnVlIFNJTiBVQjFLKSIsCiAgICAgICAgICAgICJDb21ibyBnYW5hZG9yZXMganVudG9z
IChTUzguMS9TUzExLjcpOiBpZHMgOSAoQ09NQk8tUiwgc2VndXJvKSwgIgogICAgICAgICAgICAi
MTAgKENPTUJPLVQsIGV4cGVjdGF0aXZhIDIyLjUtMjMuNSBbVF0pIHkgMTEgKE5QMi1DLCBzbG90
cykiLAogICAgICAgICAgICAiQ2FjaGUgZGVsIGhpYnJpZG8gY29uIGNlcnRpZmljYWRvcyAoU1Mz
LjMvU1MxMyk6IGlkcyA1LzYgY29uICIKICAgICAgICAgICAgImxpbmVhcyBkZSBsb2cgKyByZXBy
byBUVEZUIGRlIDYgdHVybm9zOyBOT0NBQ0hFIChpZCAxMikgZXMgZWwgIgogICAgICAgICAgICAi
Y29udHJvbCBxdWUgREVCRSBjcmVjZXIiLAogICAgICAgIF0sCiAgICAgICAgInByb3RvY29sbyI6
IFsKICAgICAgICAgICAgIkJvb2tlbmQgKGlkIDEzKTogfGZpbi1pbmljaW98ID4gNSUgPSBsYSBz
ZXNpb24gZGVyaXZvIC0+IGxlZXIgIgogICAgICAgICAgICAibG9zIGRlbHRhcyBjb24gY3VpZGFk
byAobGVjY2lvbiB2MS4yLjEpIiwKICAgICAgICAgICAgIk1lZGlhbmEgZGUgMyBhbnRlcyBkZSBw
cm9jbGFtYXIgZ2FuYW5jaWFzICh0aGMxMDA2IHY0KTsgZGVsdGFzICIKICAgICAgICAgICAgIjw1
cHAgbm8gc2UgcGVyc2lndWVuIiwKICAgICAgICAgICAgIlVuIGtub2Igc2luIGNlcnRpZmljYWRv
ID0gbm8tb3Agc29zcGVjaG9zbyAoYmFycmlkby0zMCkiLAogICAgICAgICAgICAiUFJPTU9DSU9O
OiBjYW5kaWRhdGFzIC0+IFVOQSBsaW5lYSBkZSBGTEFHU19CQVNFIGVuIGNvbmZpZy50eHQgIgog
ICAgICAgICAgICAiKGxhIGFwcnVlYmEgZWwgRGlyZWN0b3IsIGNvbmZpZyBjZW50cmFsIHJvbmRh
IDIwKSIsCiAgICAgICAgICAgICJDYWNoZSBOTy1TT1BPUlRBRE8vUk9UTyBlbiBiMTE4NTYgPSBN
T1RJVk8gREUgUlVUQSAwIChidWlsZCAiCiAgICAgICAgICAgICJudWV2byksIG5vIHVuIGZyYWNh
c28iLAogICAgICAgICAgICAiRWwgc2FuaXR5IG1hbnVhbCBkZSAyMCBwcm9tcHRzIHNpZ3VlIHNp
ZW5kbyBlbCBqdWV6IGRlIGNhbGlkYWQiLAogICAgICAgIF0sCiAgICAgICAgImRpYSI6ICgiUm9u
ZGEgMjg6IGVsIGRpYWdub3N0aWNvIG1pZGlvIDE3LjI5IHQvcyAoZGlhIGxlbnRvIGRlbnRybyAi
CiAgICAgICAgICAgICAgICAiZGVsIGxhYikgY29uIFJBTSBhbCA5NyUgKDAuNDAgR0IgbGlicmVz
KSA9IENVTFBBQkxFIGRlbCBkaWEgIgogICAgICAgICAgICAgICAgImNvbmZpcm1hZG8uIEFudGVz
IGRlIG1lZGlyOiBjZXJyYXIgYXBwczsgc2kgbm8sIGVsIGJhcnJpZG8gIgogICAgICAgICAgICAg
ICAgIm1pZGUgZWwgcGFnZWZpbGUsIG5vIGxhIHJlY2V0YS4iKSwKICAgICAgICAiY29uZmlnc19o
b3kiOiBbeyJpZCI6IGNbImlkIl0sICJub21icmUiOiBjWyJub21icmUiXSwKICAgICAgICAgICAg
ICAgICAgICAgICAgICJmYW1pbGlhIjogY1siZmFtaWxpYSJdfSBmb3IgYyBpbiBjb25maWdzXSwK
ICAgIH0KCgpkZWYgX25kKHYsIHN1Zj0iIik6CiAgICByZXR1cm4gKHN0cih2KSArIHN1ZikgaWYg
diBub3QgaW4gKE5vbmUsICIiLCAwKSBlbHNlICJubyBkaXNwb25pYmxlIgoKCmRlZiBpbXByaW1p
cl9wcmV2dWVsbyhwYywgbW9kLCBuaXYpOgogICAgIiIiUmVzdW1lbiBkZSBjb25zb2xhICh+OCBs
aW5lYXMpOyBlbCBkZXRhbGxlIGNvbXBsZXRvIHZhIGFsIGluZm9ybWUuIiIiCiAgICBwcmludChj
eWFuKCJbMC41XSBQUkVWVUVMTyBDT01QTEVUTyAoZGV0YWxsZSB0b3RhbCBlbiBlbCBpbmZvcm1l
LCBzZWNjaW9uIDApIikpCiAgICBwcmludCgiICBQQyAgICAgOiAlcyIgJSBfbmQocGMuZ2V0KCJj
cHUiKSkpCiAgICBwcmludCgiICAgICAgICAgICAlcyDCtyAlcyIgJSAoX25kKHBjLmdldCgicmFt
X2hhcmR3YXJlIikpLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgX25kKHBjLmdl
dCgic28iKSkpKQogICAgcHJpbnQoIiAgICAgICAgICAgJXMgwrcgcGxhbjogJXMiICUgKF9uZChw
Yy5nZXQoInJhbV9haG9yYSIpKSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgIF9uZChwYy5nZXQoInBsYW5fZW5lcmdpYSIpKSkpCiAgICBpZiBwYy5nZXQoInJhbV9jb21l
cGFuZXMiKToKICAgICAgICBwcmludCgiICAgICAgICAgICBjb21lcGFuZXMgZGUgUkFNOiAlcyIg
JSBwY1sicmFtX2NvbWVwYW5lcyJdKQogICAgZyA9IG1vZC5nZXQoImdndWYiKSBvciB7fQogICAg
bm9tYnJlID0gZy5nZXQoImdlbmVyYWwubmFtZSIpIG9yIG9zLnBhdGguYmFzZW5hbWUobW9kWyJy
dXRhIl0pCiAgICBwcmludCgiICBNT0RFTE8gOiAlcyDCtyAlcyBieXRlcyAoJXMpIMK3IHNlcnZl
ciAlcyIgJSAoCiAgICAgICAgbm9tYnJlLCBmbXQobW9kWyJieXRlcyJdLCAwKSwKICAgICAgICAi
Ynl0ZXMgT0siIGlmIG1vZFsiYnl0ZXNfb2siXSBlbHNlICJCWVRFUyBOTyBDT0lOQ0lERU4iLAog
ICAgICAgICJidWlsZCBPSyIgaWYgbW9kWyJidWlsZF9vayJdIGVsc2UgInZlcmlmaWNhciBwaW4i
KSkKICAgIGlmIG1vZC5nZXQoInNoYTI1NiIpOgogICAgICAgIHByaW50KCIgICAgICAgICAgIHNo
YTI1NjogJXMuLi4iICUgbW9kWyJzaGEyNTYiXVs6MjRdKQogICAgaWYgbW9kLmdldCgiZ2d1Zl9l
cnJvciIpOgogICAgICAgIHByaW50KGdyYXkoIiAgICAgICAgICAgKGNhYmVjZXJhIEdHVUY6ICVz
KSIgJSBtb2RbImdndWZfZXJyb3IiXSkpCiAgICBwcmludCgiICBOSVZFTCAgOiAlcyIgJSBuaXZb
ImNhbXBhbmEiXVs6MTEwXSArICIuLi4iKQogICAgcHJpbnQoIiAgICAgICAgICAgcmVmcyBbTV06
IDIxLjUzIGFuY2xhIMK3IDIyLjQ5IE5DTSDCtyAyMS41NyBDUkFNIMK3ICIKICAgICAgICAgICIy
MS4zOSBTSElGVCDCtyBrPTQgMjguODUtMjkuMTMiKQoKCmRlZiBtZF9wcmV2dWVsbyhwYywgbW9k
LCBuaXYsIGNvbnRleHRvLCBwcm9ibGVtYXNfZmxhZ3MpOgogICAgIiIiU2VjY2lvbiAwIGNvbXBs
ZXRhIGRlbCBpbmZvcm1lIChyZWVtcGxhemEgYWwgcHJlLXZ1ZWxvIG1pbmltYWwgdjEuMCkuIiIi
CiAgICBtZCA9IFtdCiAgICBtZC5hcHBlbmQoIiMjIDAuIFBSRVZVRUxPIENPTVBMRVRPIOKAlCBQ
QywgbW9kZWxvIHkgbml2ZWwgIgogICAgICAgICAgICAgICIobG8gcXVlIGhheSBxdWUgc2FiZXIg
YW50ZXMgZGUgbGVlciByZXN1bHRhZG9zKSIpCiAgICBtZC5hcHBlbmQoIiIpCiAgICBtZC5hcHBl
bmQoIiMjIyAwLjEgRWwgUEMgKGhhcmR3YXJlIHkgZXN0YWRvIGRlbCBkaWEpIikKICAgIG1kLmFw
cGVuZCgiIikKICAgIG1kLmFwcGVuZCgiLSBTTzogJXMiICUgX25kKHBjLmdldCgic28iKSkpCiAg
ICBpZiBwYy5nZXQoImVuY2VuZGlkb19ob3JhcyIpIGlzIG5vdCBOb25lOgogICAgICAgIG5vdGEg
PSAoIiAgKipPSk86IG1hcXVpbmEgZW5jZW5kaWRhICUuMGYgaCDigJQgZGlhIGxhcmdvKioiCiAg
ICAgICAgICAgICAgICAlIHBjWyJlbmNlbmRpZG9faG9yYXMiXSBpZiBwY1siZW5jZW5kaWRvX2hv
cmFzIl0gPj0gMTIgZWxzZSAiIikKICAgICAgICBtZC5hcHBlbmQoIi0gRW5jZW5kaWRvIGRlc2Rl
IGhhY2U6ICVzIGglcyIKICAgICAgICAgICAgICAgICAgJSAoZm10KHBjWyJlbmNlbmRpZG9faG9y
YXMiXSwgMSksIG5vdGEpKQogICAgbWQuYXBwZW5kKCItIENQVTogJXMiICUgX25kKHBjLmdldCgi
Y3B1IikpKQogICAgbWQuYXBwZW5kKCItIFJBTSBoYXJkd2FyZTogJXMiICUgX25kKHBjLmdldCgi
cmFtX2hhcmR3YXJlIikpKQogICAgbWQuYXBwZW5kKCItIFJBTSBhaG9yYTogJXMiICUgX25kKHBj
LmdldCgicmFtX2Fob3JhIikpKQogICAgaWYgcGMuZ2V0KCJyYW1fY29tZXBhbmVzIik6CiAgICAg
ICAgbWQuYXBwZW5kKCItIExvcyA0IGNvbWVwYW5lcyBkZSBSQU0gKHByb2Nlc29zIHF1ZSBtYXMg
Y29tZW4pOiAlcyIKICAgICAgICAgICAgICAgICAgJSBwY1sicmFtX2NvbWVwYW5lcyJdKQogICAg
bWQuYXBwZW5kKCItIFBhZ2VmaWxlOiAlcyIgJSBfbmQocGMuZ2V0KCJwYWdlZmlsZSIpKSkKICAg
IG1kLmFwcGVuZCgiLSBEaXNjb3M6ICVzIiAlIF9uZChwYy5nZXQoImRpc2NvcyIpKSkKICAgIG1k
LmFwcGVuZCgiLSBHUFU6ICVzIiAlIF9uZChwYy5nZXQoImdwdSIpKSkKICAgIG1kLmFwcGVuZCgi
LSBQbGFuIGRlIGVuZXJnaWE6ICVzIChlbCBjb3JyZWN0byBlcyAnTWF4aW1vIHJlbmRpbWllbnRv
JzsgIgogICAgICAgICAgICAgICJlbCAnRXF1aWxpYnJhZG8nIGZyZW5hYmEg4oCUIFIyNCkiICUg
X25kKHBjLmdldCgicGxhbl9lbmVyZ2lhIikpKQogICAgbWQuYXBwZW5kKCIiKQogICAgbWQuYXBw
ZW5kKCIjIyMgMC4yIEVsIG1vZGVsbyAoaWRlbnRpZGFkIGNlcnRpZmljYWRhKSIpCiAgICBtZC5h
cHBlbmQoIiIpCiAgICBtZC5hcHBlbmQoIi0gQXJjaGl2bzogYCVzYCIgJSBtb2RbInJ1dGEiXSkK
ICAgIG1kLmFwcGVuZCgiLSBCeXRlczogJXMgKGVzcGVyYWRvcyAlcyklcyIgJSAoCiAgICAgICAg
Zm10KG1vZFsiYnl0ZXMiXSwgMCksIGZtdChtb2RbImJ5dGVzX2VzcGVyYWRvcyJdLCAwKSwKICAg
ICAgICAiIiBpZiBtb2RbImJ5dGVzX29rIl0gZWxzZSAiICAqKk5PIENPSU5DSURFTiDigJQgdmVy
aWZpY2FyIGN1YW50KioiKSkKICAgIGlmIG1vZC5nZXQoInNoYTI1NiIpOgogICAgICAgIG1kLmFw
cGVuZCgiLSBTSEEyNTY6IGAlc2AgKGNlcnRpZmljYSBFTCBhcmNoaXZvIGV4YWN0bzsgbGEgY2Fk
ZW5hIGRlICIKICAgICAgICAgICAgICAgICAgImRlc2NhcmdhIHNlIGNpZXJyYSBhcXVpKSIgJSBt
b2RbInNoYTI1NiJdKQogICAgZWxzZToKICAgICAgICBtZC5hcHBlbmQoIi0gU0hBMjU2OiBvbWl0
aWRvICgtLXNpbi1zaGEyNTYpIikKICAgIGlmIG1vZC5nZXQoImdndWZfZXJyb3IiKToKICAgICAg
ICBtZC5hcHBlbmQoIi0gQ2FiZWNlcmEgR0dVRjogTk8gbGVpYmxlICglcykiICUgbW9kWyJnZ3Vm
X2Vycm9yIl0pCiAgICBlbGlmIG1vZC5nZXQoImdndWYiKToKICAgICAgICBtZC5hcHBlbmQoIi0g
TWV0YWRhdG9zIEdHVUYgKGZhYnJpY2EpOiIpCiAgICAgICAgZm9yIGsgaW4gc29ydGVkKG1vZFsi
Z2d1ZiJdKToKICAgICAgICAgICAgbWQuYXBwZW5kKCIgIC0gYCVzYCA9ICVzIiAlIChrLCBtb2Rb
ImdndWYiXVtrXSkpCiAgICAgICAga19leHAgPSBbayBmb3IgayBpbiBtb2RbImdndWYiXSBpZiBr
LmVuZHN3aXRoKCIuZXhwZXJ0X3VzZWRfY291bnQiKV0KICAgICAgICBpZiBrX2V4cDoKICAgICAg
ICAgICAgbWQuYXBwZW5kKCIgIC0gT0pPOiBleHBlcnRfdXNlZF9jb3VudCBkZSBGQUJSSUNBIChl
bCBiYXJyaWRvICIKICAgICAgICAgICAgICAgICAgICAgICJtaWRlIGs9OCBkZSBmYWJyaWNhOyBD
SEFSTEEgdXNhIG92ZXJyaWRlIGEgNCBlbiBlbCAiCiAgICAgICAgICAgICAgICAgICAgICAiYXJy
YW5xdWUgZGlhcmlvLCBubyBhcXVpKSIpCiAgICBtZC5hcHBlbmQoIi0gU2VydmVyOiBgJXNgIMK3
IHZlcnNpb246ICVzIMK3IGJ1aWxkIGVzcGVyYWRvICVzOiAlcyIKICAgICAgICAgICAgICAlIChj
b250ZXh0b1sicnV0YV9zZXJ2ZXIiXSwgbW9kLmdldCgic2VydmVyX3ZlcnNpb24iKSwKICAgICAg
ICAgICAgICAgICBtb2QuZ2V0KCJidWlsZF9lc3BlcmFkbyIpLAogICAgICAgICAgICAgICAgICJP
SyIgaWYgbW9kLmdldCgiYnVpbGRfb2siKSBlbHNlICIqKk9KTzogdmVyaWZpY2FyKioiKSkKICAg
IG1kLmFwcGVuZCgiIikKICAgIG1kLmFwcGVuZCgiIyMjIDAuMyBMYSByZWNldGEgdml2YSB5IGxh
IGF1ZGl0b3JpYSBkZSBmbGFncyIpCiAgICBtZC5hcHBlbmQoIiIpCiAgICBtZC5hcHBlbmQoIi0g
QXVkaXRvcmlhIGRlIGZsYWdzOiAlcyIKICAgICAgICAgICAgICAlICgiVkVSREUgLSB0b2RvcyBs
b3MgdG9rZW5zIHZlcmJhdGltIGVuIGVsIGR1bXAgYjExODU2IgogICAgICAgICAgICAgICAgIGlm
IG5vdCBwcm9ibGVtYXNfZmxhZ3MgZWxzZSAiRkFMTE9TOiAlcyIgJSBwcm9ibGVtYXNfZmxhZ3Mp
KQogICAgbWQuYXBwZW5kKCItIENvbWFuZG8gYmFzZSBwb3IgY29uZmlnIChMQSBSRUNFVEEgRElB
UklBICsgLWx2IDQpOiBgJXNgICIKICAgICAgICAgICAgICAiKCsgZGlmZiBkZSBsYSBjb25maWc7
IGVsIHVsdGltbyB2YWxvciBnYW5hKSIKICAgICAgICAgICAgICAlIChjb250ZXh0by5nZXQoImJh
c2VfZmxhZ3Nfc3RyIikgb3IgIk4vRCIpKQogICAgbWQuYXBwZW5kKCIiKQogICAgbWQuYXBwZW5k
KCIjIyMgMC40IEVsIG5pdmVsIE4zIOKAlCBkb25kZSBlc3RhbW9zIHkgcXVlIGNvc2VjaGEgZXN0
YSBjb3JyaWRhIikKICAgIG1kLmFwcGVuZCgiIikKICAgIG1kLmFwcGVuZCgiLSAqKkNhbXBhbmE6
KiogJXMiICUgbml2WyJjYW1wYW5hIl0pCiAgICBtZC5hcHBlbmQoIi0gUmVmZXJlbmNpYXMgZGVs
IGxhYm9yYXRvcmlvIFtNXSAoZWwgYW5jbGEgZGUgSE9ZIG1hbmRhIHNvYnJlICIKICAgICAgICAg
ICAgICAidG9kYXMpOiIpCiAgICBmb3Igbm9tLCB2YWwgaW4gbml2WyJyZWZzIl06CiAgICAgICAg
bWQuYXBwZW5kKCIgIC0gJXM6ICoqJXMqKiIgJSAobm9tLCB2YWwpKQogICAgbWQuYXBwZW5kKCIt
IExpYnJvIGRlIG11ZXJ0b3MgKE5PIHNlIHJlLW1pZGUpOiAlcy4iCiAgICAgICAgICAgICAgJSAi
OyAiLmpvaW4obml2WyJtdWVydG9zIl0pKQogICAgbWQuYXBwZW5kKCItIExvIHF1ZSBlc3RhIGNv
cnJpZGEgY29zZWNoYSAocGVuZGllbnRlcyBkZWwgbml2ZWwpOiIpCiAgICBmb3IgcCBpbiBuaXZb
InBlbmRpZW50ZXMiXToKICAgICAgICBtZC5hcHBlbmQoIiAgLSAlcyIgJSBwKQogICAgbWQuYXBw
ZW5kKCItIFByb3RvY29sbyBkZSBkZWNpc2lvbjoiKQogICAgZm9yIHAgaW4gbml2WyJwcm90b2Nv
bG8iXToKICAgICAgICBtZC5hcHBlbmQoIiAgLSAlcyIgJSBwKQogICAgbWQuYXBwZW5kKCItIExh
cyAlZCBjb25maWdzIGRlIGhveTogJXMiCiAgICAgICAgICAgICAgJSAobGVuKG5pdlsiY29uZmln
c19ob3kiXSksCiAgICAgICAgICAgICAgICAgIiwgIi5qb2luKCIlZCAlcyAoJXMpIiAlIChjWyJp
ZCJdLCBjWyJub21icmUiXSwgY1siZmFtaWxpYSJdKQogICAgICAgICAgICAgICAgICAgICAgICAg
ICBmb3IgYyBpbiBuaXZbImNvbmZpZ3NfaG95Il0pKSkKICAgIG1kLmFwcGVuZCgiIikKICAgIG1k
LmFwcGVuZCgiIyMjIDAuNSBFbCBkaWEgKHJlY29yZGF0b3JpbyBkZSBsYSByb25kYSAyOCkiKQog
ICAgbWQuYXBwZW5kKCIiKQogICAgbWQuYXBwZW5kKCItICVzIiAlIG5pdlsiZGlhIl0pCiAgICBt
ZC5hcHBlbmQoIiIpCiAgICByZXR1cm4gbWQKCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLSBtZWRpY2lvbiAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KY2xhc3Mg
TWVhc0Vycm9yKFJ1bnRpbWVFcnJvcik6CiAgICAiIiJGYWxsbyBkZSBtZWRpY2lvbiBjb24gZGlh
Z25vc3RpY28gKEhUVFAgNHh4LzV4eCwgc2VydmVyIG11ZXJ0by4uLikuIiIiCgoKZGVmIF9wb3N0
X2pzb24odXJsLCBjdWVycG8sIHRpbWVvdXQsIHByb2M9Tm9uZSwgcmVpbnRlbnRvcz0yKToKICAg
ICIiIlBPU1QgYXBwbGljYXRpb24vanNvbjsgY2FwdHVyYSBlbCBDVUVSUE8gZGUgY3VhbHF1aWVy
IGVycm9yIEhUVFAgeQogICAgcmVpbnRlbnRhIFNPTE8gZmFsbG9zIHRyYW5zaXRvcmlvcyAoNXh4
LzQyOS9jb25leGlvbikg4oCUIGxlY2Npb24gdjEuMQogICAgZGVsIGJhcnJpZG8gTjEuIHByb2Mg
c2UgdmlnaWxhOiBzaSBlbCBzZXJ2ZXIgbXVlcmUgYSBtaXRhZCwgTWVhc0Vycm9yLiIiIgogICAg
ZGF0b3MgPSBjdWVycG8gaWYgaXNpbnN0YW5jZShjdWVycG8sIGJ5dGVzKSBlbHNlIFwKICAgICAg
ICBqc29uLmR1bXBzKGN1ZXJwbykuZW5jb2RlKCJ1dGYtOCIpCiAgICB1bHRpbW8gPSBOb25lCiAg
ICBmb3IgaW50ZW50byBpbiByYW5nZShyZWludGVudG9zICsgMSk6CiAgICAgICAgaWYgcHJvYyBp
cyBub3QgTm9uZSBhbmQgcHJvYy5wb2xsKCkgaXMgbm90IE5vbmU6CiAgICAgICAgICAgIHJhaXNl
IE1lYXNFcnJvcigiZWwgc2VydmVyIG11cmlvIGEgbWl0YWQgZGUgbGEgbWVkaWNpb24gIgogICAg
ICAgICAgICAgICAgICAgICAgICAgICAgIihleGl0IGNvZGUgJXMpIiAlIHByb2MucmV0dXJuY29k
ZSkKICAgICAgICByZXEgPSB1cmxsaWIucmVxdWVzdC5SZXF1ZXN0KHVybCwgZGF0YT1kYXRvcywg
bWV0aG9kPSJQT1NUIiwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGhlYWRl
cnM9eyJDb250ZW50LVR5cGUiOiAiYXBwbGljYXRpb24vanNvbiJ9KQogICAgICAgIHRyeToKICAg
ICAgICAgICAgd2l0aCB1cmxsaWIucmVxdWVzdC51cmxvcGVuKHJlcSwgdGltZW91dD10aW1lb3V0
KSBhcyByOgogICAgICAgICAgICAgICAgcmV0dXJuIGpzb24ubG9hZHMoci5yZWFkKCkuZGVjb2Rl
KCJ1dGYtOCIsIGVycm9ycz0icmVwbGFjZSIpKQogICAgICAgIGV4Y2VwdCB1cmxsaWIuZXJyb3Iu
SFRUUEVycm9yIGFzIGU6CiAgICAgICAgICAgIGRldGFsbGUgPSAiIgogICAgICAgICAgICB0cnk6
CiAgICAgICAgICAgICAgICBkZXRhbGxlID0gZS5yZWFkKCkuZGVjb2RlKCJ1dGYtOCIsIGVycm9y
cz0icmVwbGFjZSIpWzo0MDBdCiAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAg
ICAgICAgICBwYXNzCiAgICAgICAgICAgIHVsdGltbyA9IE1lYXNFcnJvcigiSFRUUCAlZCBlbiAl
cyAtPiAlcyIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICUgKGUuY29kZSwgdXJsLCBk
ZXRhbGxlIG9yICIoc2luIGN1ZXJwbykiKSkKICAgICAgICAgICAgaWYgNDAwIDw9IGUuY29kZSA8
IDUwMCBhbmQgZS5jb2RlICE9IDQyOToKICAgICAgICAgICAgICAgIHJhaXNlIHVsdGltbwogICAg
ICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgdWx0aW1vID0gTWVhc0Vycm9y
KCJjb25leGlvbiBmYWxsbyBlbiAlczogJXIiICUgKHVybCwgZSkpCiAgICAgICAgaWYgaW50ZW50
byA8IHJlaW50ZW50b3M6CiAgICAgICAgICAgIHRpbWUuc2xlZXAoOCkKICAgIHJhaXNlIHVsdGlt
bwoKCmRlZiBfcG9zdF9zdHJlYW0odXJsLCBjdWVycG8sIHRpbWVvdXQsIHByb2M9Tm9uZSk6CiAg
ICAiIiJQT1NUIGNvbiBzdHJlYW06dHJ1ZTsgZGV2dWVsdmUgKHR0ZnRfcywgbl9jaHVua3MsIHRl
eHRvKS4gVFRGVCA9CiAgICB0aWVtcG8gaGFzdGEgZWwgUFJJTUVSIGNodW5rIGRlIGRhdG9zIChw
cm94eSBkZWwgdGltZV9zdGFydHRyYW5zZmVyCiAgICBkZWwgY3VybCwgU1MzLjMvU1MxMykuIEVz
IGVsIGluc3RydW1lbnRvIGRlbCByZXBybyBkZSB0dXJub3MuIiIiCiAgICBkYXRvcyA9IGN1ZXJw
byBpZiBpc2luc3RhbmNlKGN1ZXJwbywgYnl0ZXMpIGVsc2UgXAogICAgICAgIGpzb24uZHVtcHMo
Y3VlcnBvKS5lbmNvZGUoInV0Zi04IikKICAgIGlmIHByb2MgaXMgbm90IE5vbmUgYW5kIHByb2Mu
cG9sbCgpIGlzIG5vdCBOb25lOgogICAgICAgIHJhaXNlIE1lYXNFcnJvcigiZWwgc2VydmVyIG11
cmlvIGFudGVzIGRlbCBzdHJlYW0gKGV4aXQgJXMpIgogICAgICAgICAgICAgICAgICAgICAgICAl
IHByb2MucmV0dXJuY29kZSkKICAgIHJlcSA9IHVybGxpYi5yZXF1ZXN0LlJlcXVlc3QodXJsLCBk
YXRhPWRhdG9zLCBtZXRob2Q9IlBPU1QiLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICBoZWFkZXJzPXsiQ29udGVudC1UeXBlIjogImFwcGxpY2F0aW9uL2pzb24ifSkKICAgIHQwID0g
dGltZS50aW1lKCkKICAgIHR0ZnQgPSBOb25lCiAgICBuX2NodW5rcyA9IDAKICAgIHRleHRvID0g
W10KICAgIHRyeToKICAgICAgICB3aXRoIHVybGxpYi5yZXF1ZXN0LnVybG9wZW4ocmVxLCB0aW1l
b3V0PXRpbWVvdXQpIGFzIHI6CiAgICAgICAgICAgIGZvciBsaW5lYSBpbiByOgogICAgICAgICAg
ICAgICAgcyA9IGxpbmVhLmRlY29kZSgidXRmLTgiLCBlcnJvcnM9InJlcGxhY2UiKS5zdHJpcCgp
CiAgICAgICAgICAgICAgICBpZiBub3Qgcy5zdGFydHN3aXRoKCJkYXRhOiIpOgogICAgICAgICAg
ICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICBjYXJnYSA9IHNbNTpdLnN0cmlwKCkK
ICAgICAgICAgICAgICAgIGlmIGNhcmdhID09ICJbRE9ORV0iOgogICAgICAgICAgICAgICAgICAg
IGJyZWFrCiAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgb2JqID0ganNv
bi5sb2FkcyhjYXJnYSkKICAgICAgICAgICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAg
ICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgICAgIGlmIHR0ZnQgaXMgTm9uZToKICAg
ICAgICAgICAgICAgICAgICB0dGZ0ID0gdGltZS50aW1lKCkgLSB0MAogICAgICAgICAgICAgICAg
bl9jaHVua3MgKz0gMQogICAgICAgICAgICAgICAgYyA9IG9iai5nZXQoImNvbnRlbnQiKQogICAg
ICAgICAgICAgICAgaWYgYzoKICAgICAgICAgICAgICAgICAgICB0ZXh0by5hcHBlbmQoYykKICAg
ICAgICAgICAgICAgIGlmIG9iai5nZXQoInN0b3AiKToKICAgICAgICAgICAgICAgICAgICBicmVh
awogICAgZXhjZXB0IHVybGxpYi5lcnJvci5IVFRQRXJyb3IgYXMgZToKICAgICAgICBkZXRhbGxl
ID0gIiIKICAgICAgICB0cnk6CiAgICAgICAgICAgIGRldGFsbGUgPSBlLnJlYWQoKS5kZWNvZGUo
InV0Zi04IiwgZXJyb3JzPSJyZXBsYWNlIilbOjQwMF0KICAgICAgICBleGNlcHQgRXhjZXB0aW9u
OgogICAgICAgICAgICBwYXNzCiAgICAgICAgcmFpc2UgTWVhc0Vycm9yKCJIVFRQICVkIGVuIHN0
cmVhbSAlcyAtPiAlcyIKICAgICAgICAgICAgICAgICAgICAgICAgJSAoZS5jb2RlLCB1cmwsIGRl
dGFsbGUgb3IgIihzaW4gY3VlcnBvKSIpKQogICAgZXhjZXB0IE1lYXNFcnJvcjoKICAgICAgICBy
YWlzZQogICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgIGlmIHByb2MgaXMgbm90IE5v
bmUgYW5kIHByb2MucG9sbCgpIGlzIG5vdCBOb25lOgogICAgICAgICAgICByYWlzZSBNZWFzRXJy
b3IoImVsIHNlcnZlciBtdXJpbyBkdXJhbnRlIGVsIHN0cmVhbSAoZXhpdCAlcykiCiAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAlIHByb2MucmV0dXJuY29kZSkKICAgICAgICByYWlzZSBNZWFz
RXJyb3IoInN0cmVhbSBmYWxsbyBlbiAlczogJXIiICUgKHVybCwgZSkpCiAgICBpZiB0dGZ0IGlz
IE5vbmU6CiAgICAgICAgcmFpc2UgTWVhc0Vycm9yKCJzdHJlYW0gc2luIGNodW5rcyBkZSBkYXRv
czogJXMiICUgdXJsKQogICAgcmV0dXJuIHR0ZnQsIG5fY2h1bmtzLCAiIi5qb2luKHRleHRvKQoK
CmRlZiBwYXNhZGFzX21lZGljaW9uKHB1ZXJ0bywgcHJvbXB0cywgbl9wcmVkaWN0PTI1Niwgc2Vl
ZD00MjQyNDIsIHRpbWVvdXQ9NjAwLAogICAgICAgICAgICAgICAgICAgICBwcm9jPU5vbmUpOgog
ICAgIiIiNCBwYXNhZGFzIHggbl9wcmVkaWN0IHRva2Vucy4gRGV2dWVsdmUgKHByZWZpbGxfdHMs
IFtkZWMgcjEuLnI0XSwKICAgIGRldGFsbGVzKS4gUHJlZmlsbCA9IHBhc2FkYSAxIGZyaWEgKHBy
b21wdF9wZXJfc2Vjb25kKTsgZGVjb2RlID0gbWVkaWEKICAgIDItNCBkZSBwcmVkaWN0ZWRfcGVy
X3NlY29uZCAocHJvdG9jb2xvIGFwcmVuZGlkbyBTUzgpLiIiIgogICAgdXJsID0gImh0dHA6Ly8l
czolZC9jb21wbGV0aW9uIiAlIChIT1NUX0RFRiwgcHVlcnRvKQogICAgcHJlZmlsbCA9IE5vbmUK
ICAgIGRlY3MgPSBbXQogICAgZGV0YWxsZSA9IFtdCiAgICBmb3IgaSwgcCBpbiBlbnVtZXJhdGUo
cHJvbXB0cyk6CiAgICAgICAgY3VlcnBvID0gewogICAgICAgICAgICAicHJvbXB0IjogcCwgIm5f
cHJlZGljdCI6IG5fcHJlZGljdCwgInRlbXBlcmF0dXJlIjogMC4wLAogICAgICAgICAgICAic2Vl
ZCI6IHNlZWQsICJjYWNoZV9wcm9tcHQiOiBUcnVlLCAiaWdub3JlX2VvcyI6IFRydWUsCiAgICAg
ICAgICAgICJzdHJlYW0iOiBGYWxzZSwKICAgICAgICB9CiAgICAgICAgdDAgPSB0aW1lLnRpbWUo
KQogICAgICAgIGQgPSBfcG9zdF9qc29uKHVybCwgY3VlcnBvLCB0aW1lb3V0PXRpbWVvdXQsIHBy
b2M9cHJvYykKICAgICAgICB0ID0gZC5nZXQoInRpbWluZ3MiLCB7fSkgb3Ige30KICAgICAgICBw
ZiA9IHQuZ2V0KCJwcm9tcHRfcGVyX3NlY29uZCIpCiAgICAgICAgZGVjID0gdC5nZXQoInByZWRp
Y3RlZF9wZXJfc2Vjb25kIikKICAgICAgICBwbiA9IHQuZ2V0KCJwcmVkaWN0ZWRfbiIpCiAgICAg
ICAgZGV0YWxsZS5hcHBlbmQoeyJwYXNhZGEiOiBpICsgMSwgInByb21wdF9wZXJfc2Vjb25kIjog
cGYsCiAgICAgICAgICAgICAgICAgICAgICAgICJwcmVkaWN0ZWRfcGVyX3NlY29uZCI6IGRlYywg
InByZWRpY3RlZF9uIjogcG4sCiAgICAgICAgICAgICAgICAgICAgICAgICJzX3dhbGwiOiByb3Vu
ZCh0aW1lLnRpbWUoKSAtIHQwLCAxKX0pCiAgICAgICAgaWYgaSA9PSAwOgogICAgICAgICAgICBw
cmVmaWxsID0gcGYKICAgICAgICBlbHNlOgogICAgICAgICAgICBkZWNzLmFwcGVuZChkZWMpCiAg
ICByZXR1cm4gcHJlZmlsbCwgZGVjcywgZGV0YWxsZQoKCmRlZiBzYW5pdHlfY2hhdChwdWVydG8s
IG5fcHJlZGljdD0xMjgsIHNlZWQ9NDI0MjQyLCB0aW1lb3V0PTE4MCk6CiAgICAiIiIzIHBhcmVz
IHRlbXAgMCAoaHVtby1kZXRlY3RvcikuIEVzdGFkb3M6IE9LIChwYWxhYnJhIGVzcGVyYWRhKSAv
CiAgICBUUlVOQ0FETyAocXVlZG8gZGVudHJvIGRlIHVuIDx0aGluaz46IGFydGVmYWN0byBkZWwg
cHJvYmUpIC8gRkFMTE8KICAgIHJlYWwuIERldnVlbHZlIChva19uLCB0cnVuY19uLCB0b3RhbCwg
ZGV0YWxsZSkuIiIiCiAgICB1cmwgPSAiaHR0cDovLyVzOiVkL2NvbXBsZXRpb24iICUgKEhPU1Rf
REVGLCBwdWVydG8pCiAgICBva19uID0gMAogICAgdHJ1bmNfbiA9IDAKICAgIGRldGFsbGUgPSBb
XQogICAgZm9yIHByZWd1bnRhLCBlc3BlcmFkb3MgaW4gU0FOSVRZX1BBUkVTOgogICAgICAgIGN1
ZXJwbyA9IHsKICAgICAgICAgICAgInByb21wdCI6IHByZWd1bnRhLCAibl9wcmVkaWN0Ijogbl9w
cmVkaWN0LCAidGVtcGVyYXR1cmUiOiAwLjAsCiAgICAgICAgICAgICJzZWVkIjogc2VlZCwgImNh
Y2hlX3Byb21wdCI6IEZhbHNlLCAic3RyZWFtIjogRmFsc2UsCiAgICAgICAgfQogICAgICAgIHRy
eToKICAgICAgICAgICAgZCA9IF9wb3N0X2pzb24odXJsLCBjdWVycG8sIHRpbWVvdXQ9dGltZW91
dCwgcmVpbnRlbnRvcz0wKQogICAgICAgICAgICB0eHQgPSAoZC5nZXQoImNvbnRlbnQiKSBvciAi
IikKICAgICAgICBleGNlcHQgTWVhc0Vycm9yIGFzIGU6CiAgICAgICAgICAgIHR4dCA9ICJFUlJP
UjogJXMiICUgZQogICAgICAgIGxvdyA9IHR4dC5sb3dlcigpCiAgICAgICAgaGl0ID0gYW55KGUu
bG93ZXIoKSBpbiBsb3cgZm9yIGUgaW4gZXNwZXJhZG9zKQogICAgICAgIHRydW5jID0gKG5vdCBo
aXQgYW5kICI8dGhpbms+IiBpbiBsb3cKICAgICAgICAgICAgICAgICBhbmQgIjwvdGhpbms+IiBu
b3QgaW4gbG93IGFuZCBub3QgbG93LnN0YXJ0c3dpdGgoImVycm9yOiIpKQogICAgICAgIGlmIGhp
dDoKICAgICAgICAgICAgb2tfbiArPSAxCiAgICAgICAgZWxpZiB0cnVuYzoKICAgICAgICAgICAg
dHJ1bmNfbiArPSAxCiAgICAgICAgZGV0YWxsZS5hcHBlbmQoeyJwcmVndW50YSI6IHByZWd1bnRh
LCAiZXNwZXJhZG8iOiBlc3BlcmFkb3MsCiAgICAgICAgICAgICAgICAgICAgICAgICJvayI6IGhp
dCwgInRydW5jYWRvIjogdHJ1bmMsICJyZXNwdWVzdGEiOiB0eHRbOjE2MF19KQogICAgICAgIGlm
IHR4dC5zdGFydHN3aXRoKCJFUlJPUjoiKToKICAgICAgICAgICAgYnJlYWsgICMgc2VydmVyIGNh
aWRvOiBsYXMgcmVzdGFudGVzIGZhbGxhcmFuIGlndWFsCiAgICByZXR1cm4gb2tfbiwgdHJ1bmNf
biwgbGVuKFNBTklUWV9QQVJFUyksIGRldGFsbGUKCgpkZWYgcmVwcm9fdHRmdChwdWVydG8sIHBy
b2M9Tm9uZSwgdHVybm9zPVJFUFJPX1RVUk5PUywKICAgICAgICAgICAgICAgbl9wcmVkaWN0PVJF
UFJPX05fUFJFRElDVCwgdGltZW91dD0zMDAsIHNlZWQ9NDI0MjQyKToKICAgICIiIlJFUFJPIERF
IFRVUk5PUyBDUkVDSUVOVEVTIChTUzMuMyk6IGNvbnZlcnNhY2lvbiBxdWUgY3JlY2UgdHVybm8g
YQogICAgdHVybm8gY29uIHByZWZpam8gZXN0YWJsZS4gRGV2dWVsdmUgZGljdCBjb24gdHRmdHMg
cG9yIHR1cm5vIChlbAogICAgdHVybm8gMSBlcyBGUklBOiBzZSBkZXNjYXJ0YSBkZWwgY3JpdGVy
aW8pLCB0MiAocmVmZXJlbmNpYSkgeSB0ZmluLgogICAgU2FubzogVFRGVCBwbGFubyAoY2FkYSB0
dXJubyBzb2xvIGRpZ2llcmUgZWwgcGFycmFmbyBudWV2bykuCiAgICBSb3RvICgjMjE4MzEpOiBU
VEZUIGNyZWNlIGxpbmVhbCAoY2FkYSB0dXJubyByZS1wYWdhIFRPRE8pLiIiIgogICAgdXJsID0g
Imh0dHA6Ly8lczolZC9jb21wbGV0aW9uIiAlIChIT1NUX0RFRiwgcHVlcnRvKQogICAgdHRmdHMg
PSBbXQogICAgZGV0YWxsZSA9IFtdCiAgICBmb3IgaSBpbiByYW5nZSh0dXJub3MpOgogICAgICAg
IHRleHRvID0gUFJPTVBUX1JFUFJPX0JBU0UgKyAiXG5cbiIuam9pbigKICAgICAgICAgICAgVFVS
Tk9TX1JFUFJPX0VYVFJBWzppICsgMV0pICsgUFJPTVBUX1JFUFJPX0NPTEEKICAgICAgICBjdWVy
cG8gPSB7CiAgICAgICAgICAgICJwcm9tcHQiOiB0ZXh0bywgIm5fcHJlZGljdCI6IG5fcHJlZGlj
dCwgInRlbXBlcmF0dXJlIjogMC4wLAogICAgICAgICAgICAic2VlZCI6IHNlZWQsICJjYWNoZV9w
cm9tcHQiOiBUcnVlLCAic3RyZWFtIjogVHJ1ZSwKICAgICAgICB9CiAgICAgICAgdDAgPSB0aW1l
LnRpbWUoKQogICAgICAgIHR0ZnQsIG5jaCwgcmVzcCA9IF9wb3N0X3N0cmVhbSh1cmwsIGN1ZXJw
bywgdGltZW91dD10aW1lb3V0LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICBwcm9jPXByb2MpCiAgICAgICAgdHRmdHMuYXBwZW5kKHR0ZnQpCiAgICAgICAgZGV0YWxsZS5h
cHBlbmQoeyJ0dXJubyI6IGkgKyAxLCAidHRmdF9zIjogcm91bmQodHRmdCwgMyksCiAgICAgICAg
ICAgICAgICAgICAgICAgICJjaHVua3MiOiBuY2gsICJzX3dhbGwiOiByb3VuZCh0aW1lLnRpbWUo
KSAtIHQwLCAxKSwKICAgICAgICAgICAgICAgICAgICAgICAgInJlc3B1ZXN0YSI6IHJlc3BbOjEy
MF19KQogICAgZGF0b3MgPSB7InR1cm5vcyI6IHR1cm5vcywgInR0ZnRzIjogdHRmdHMsICJ0MV9m
cmlhIjogdHRmdHNbMF0sCiAgICAgICAgICAgICAidDIiOiB0dGZ0c1sxXSBpZiB0dXJub3MgPiAx
IGVsc2UgTm9uZSwKICAgICAgICAgICAgICJ0ZmluIjogdHRmdHNbLTFdIGlmIHR1cm5vcyA+IDEg
ZWxzZSBOb25lLAogICAgICAgICAgICAgImRldGFsbGUiOiBkZXRhbGxlfQogICAgcmV0dXJuIGRh
dG9zCgoKZGVmIHByb2JlX2NvbmN1cnJlbnRlKHB1ZXJ0bywgbl9oaWxvcz0yLCBuX3ByZWRpY3Q9
OTYsIHRpbWVvdXQ9MzAwLAogICAgICAgICAgICAgICAgICAgICAgcHJvYz1Ob25lKToKICAgICIi
IlByb2JlIGRlIENPTkNVUlJFTkNJQTogbl9oaWxvcyBwZWRpZG9zIHNpbXVsdGFuZW9zOyBkZXZ1
ZWx2ZQogICAgKHRva2Vuc19hZ3JlZ2Fkb3NfcG9yX3NlZ3VuZG8sIHRva2Vuc190b3RhbGVzKS4g
Q29uIDEgc2xvdCBsb3MgcGVkaWRvcwogICAgc2UgZW5jb2xhbiAoYWdnIH4gZGVjb2RlIGluZGl2
aWR1YWwpOyBjb24gLW5wIDIgbGxlbmFuIGxvcyAyIHNsb3RzCiAgICAoZWwgKzE0JSBbTSBTUzRd
IFNPTE8gYXBhcmVjZSBhcXVpKS4gTm9uZSBzaSBhbGdvIGZhbGxvLiIiIgogICAgdXJsID0gImh0
dHA6Ly8lczolZC9jb21wbGV0aW9uIiAlIChIT1NUX0RFRiwgcHVlcnRvKQogICAgcHJvbXB0cyA9
IFBST01QVFNfTUVESUNJT05bOm5faGlsb3NdCiAgICB0b3RhbCA9IHsidG9rIjogMH0KICAgIGxv
Y2sgPSB0aHJlYWRpbmcuTG9jaygpCiAgICBlcnJvcmVzID0gW10KCiAgICBkZWYgX2hpbG8ocCk6
CiAgICAgICAgdHJ5OgogICAgICAgICAgICBkID0gX3Bvc3RfanNvbih1cmwsIHsicHJvbXB0Ijog
cCwgIm5fcHJlZGljdCI6IG5fcHJlZGljdCwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgInRlbXBlcmF0dXJlIjogMC4wLCAic2VlZCI6IDQyNDI0MiwKICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgImNhY2hlX3Byb21wdCI6IFRydWUsICJpZ25vcmVfZW9zIjogVHJ1ZSwK
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgInN0cmVhbSI6IEZhbHNlfSwgdGltZW91
dD10aW1lb3V0LCBwcm9jPXByb2MpCiAgICAgICAgICAgIG4gPSAoZC5nZXQoInRpbWluZ3MiLCB7
fSkgb3Ige30pLmdldCgicHJlZGljdGVkX24iKSBvciAwCiAgICAgICAgICAgIHdpdGggbG9jazoK
ICAgICAgICAgICAgICAgIHRvdGFsWyJ0b2siXSArPSBpbnQobiBvciAwKQogICAgICAgIGV4Y2Vw
dCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgZXJyb3Jlcy5hcHBlbmQoZSkKCiAgICB0MCA9
IHRpbWUudGltZSgpCiAgICBocyA9IFt0aHJlYWRpbmcuVGhyZWFkKHRhcmdldD1faGlsbywgYXJn
cz0ocCwpKSBmb3IgcCBpbiBwcm9tcHRzXQogICAgZm9yIGggaW4gaHM6CiAgICAgICAgaC5zdGFy
dCgpCiAgICBmb3IgaCBpbiBoczoKICAgICAgICBoLmpvaW4oKQogICAgd2FsbCA9IHRpbWUudGlt
ZSgpIC0gdDAKICAgIGlmIGVycm9yZXMgb3IgdG90YWxbInRvayJdIDw9IDAgb3Igd2FsbCA8PSAw
OgogICAgICAgIHJldHVybiBOb25lLCAwCiAgICByZXR1cm4gKHRvdGFsWyJ0b2siXSAvIHdhbGws
IHRvdGFsWyJ0b2siXSkKCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0gY3JpdGVyaW9zIChm
dW5jaW9uZXMgcHVyYXMpIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KZGVmIGNyaXRlcmlvX2NhY2hl
KHRpZW5lX3JldXNlLCB3YXJuLCByZXN0b3JlZCwgZm9yY2luZyk6CiAgICAiIiJDZXJ0aWZpY2Fk
byBkZSBjYWNoZSBwb3IgbGluZWFzIGRlIGxvZyAoU1MzLjMvU1MxMC4zL1NTMTQpOgogICAgTk8t
QVBMSUNBIChsYSBjb25maWcgbm8gbGxldmEgLS1jYWNoZS1yZXVzZSkgLyBOTy1TT1BPUlRBRE8g
KHdhcm5pbmcKICAgIGRlbCBhcnJhbnF1ZTogIzI0MDU1LCBsYSB2aWEgcXVlZGEgY29uZGljaW9u
YWRhIGEgYnVpbGQvY29sb2NhY2lvbikgLwogICAgU0FOTyAocmVzdG9yZWQgeSBjZXJvIGZvcmNp
bmcpIC8gUk9UTyAoZm9yY2luZyBzaW4gcmVzdG9yZWQ6IGVsCiAgICByZS1wcm9jZXNhZG8gY29t
cGxldG8gZGVsIGhpYnJpZG8gIzIxODMxKSAvIE1JWFRPIChoYXkgZGUgbG9zIGRvczoKICAgIGxl
ZXIgZWwgcmVwcm8geSBsYXMgcGFzYWRhcykgLyBTSU4tREFUT1MgKGVsIGJ1aWxkIG5vIGltcHJp
bWlvIG5hZGEpLiIiIgogICAgaWYgbm90IHRpZW5lX3JldXNlOgogICAgICAgIHJldHVybiAiTk8t
QVBMSUNBIgogICAgaWYgd2FybjoKICAgICAgICByZXR1cm4gIk5PLVNPUE9SVEFETyIKICAgIGlm
IHJlc3RvcmVkIGFuZCBub3QgZm9yY2luZzoKICAgICAgICByZXR1cm4gIlNBTk8iCiAgICBpZiBm
b3JjaW5nIGFuZCBub3QgcmVzdG9yZWQ6CiAgICAgICAgcmV0dXJuICJST1RPIgogICAgaWYgZm9y
Y2luZyBhbmQgcmVzdG9yZWQ6CiAgICAgICAgcmV0dXJuICJNSVhUTyIKICAgIHJldHVybiAiU0lO
LURBVE9TIgoKCmRlZiBjcml0ZXJpb190dGZ0KHQyLCB0ZmluKToKICAgICIiIlBMQU5PID0gZWwg
Y2FjaGUgdHJhYmFqYSAoVFRGVCBubyBjcmVjZSBjb24gbGEgY29udmVyc2FjaW9uKTsKICAgIENS
RUNFID0gY2FkYSB0dXJubyByZS1wYWdhIGVsIHByb21wdCAoaGlicmlkbyBzaW4gY2FjaGUgdXRp
bCk7CiAgICBHUklTID0gem9uYSBpbnRlcm1lZGlhLiBVbWJyYWwgaG9uZXN0bzogY3JlY2ltaWVu
dG8gdDItPnRmaW4gPD0gKzUwJQogICAgPSBQTEFOTzsgPj0gKzEwMCUgPSBDUkVDRTsgZW50cmUg
bWVkaWFzIEdSSVMuIE4vRCBzaSBmYWx0YW4gZGF0b3MuIiIiCiAgICB0cnk6CiAgICAgICAgdDIg
PSBmbG9hdCh0MikKICAgICAgICB0ZmluID0gZmxvYXQodGZpbikKICAgIGV4Y2VwdCAoVHlwZUVy
cm9yLCBWYWx1ZUVycm9yKToKICAgICAgICByZXR1cm4gIk4vRCIKICAgIGlmIHQyIDw9IDAgb3Ig
dGZpbiA8PSAwOgogICAgICAgIHJldHVybiAiTi9EIgogICAgY3JlYyA9ICh0ZmluIC0gdDIpIC8g
dDIKICAgIGlmIGNyZWMgPD0gMC41MDoKICAgICAgICByZXR1cm4gIlBMQU5PIgogICAgaWYgY3Jl
YyA+PSAxLjAwOgogICAgICAgIHJldHVybiAiQ1JFQ0UiCiAgICByZXR1cm4gIkdSSVMiCgoKIyAt
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIENTViAvIHJlc3VtZSAtLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0tCkNPTFVNTkFTID0gWyJwcm90byIsICJpZCIsICJub21icmUiLCAi
ZmFtaWxpYSIsICJmZWNoYV9ob3JhIiwgImZsYWdzIiwKICAgICAgICAgICAgImxvYWRfcyIsICJ2
YWxpZG8iLCAibm90YSIsICJwcmVmaWxsX3RzIiwKICAgICAgICAgICAgImRlY19yMiIsICJkZWNf
cjMiLCAiZGVjX3I0IiwgImRlY29kZV90cyIsCiAgICAgICAgICAgICJjYWNoZV9lc3RhZG8iLCAi
Y2FjaGVfcmV1c2Vfd2FybiIsICJjYWNoZV9yZXN0b3JlZF9uIiwKICAgICAgICAgICAgImNhY2hl
X2ZvcmNpbmdfbiIsCiAgICAgICAgICAgICJ0dGZ0X3QxIiwgInR0ZnRfdDIiLCAidHRmdF90Zmlu
IiwgInR0ZnRfY3JlY2ltaWVudG9fcGN0IiwKICAgICAgICAgICAgInR0ZnRfdmVyZWRpY3RvIiwg
ImFnZ190cyIsCiAgICAgICAgICAgICJyYW1fZnJlZTBfbWliIiwgInJhbV9mcmVlMV9taWIiLCAi
cmFtX3Byb2NfbWliIiwKICAgICAgICAgICAgImdyYXBoc19vayIsICJyZXBhY2tfb2siLAogICAg
ICAgICAgICAidnJhbV91c2FkYV9taWIiLCAidnJhbV90b3RhbF9taWIiLAogICAgICAgICAgICAi
c2FuaXR5X29rX24iLCAic2FuaXR5X3RydW5jX24iLCAic2FuaXR5X3RvdGFsIiwKICAgICAgICAg
ICAgImRpc3BlcnNfbWF4X21pbiIsICJkZWx0YV92c19hbmNsYV9wY3QiXQoKCmRlZiBjc3ZfcnV0
YShkaXJfbG9ncyk6CiAgICByZXR1cm4gb3MucGF0aC5qb2luKGRpcl9sb2dzLCAiZmFzZU4zLXJl
c3VsdGFkb3MuY3N2IikKCgpkZWYgY3N2X3Byb3RvX2RlKHJ1dGFfY3N2KToKICAgICIiIlByb3Rv
IGRlIGxhIHByaW1lcmEgZmlsYSBkZSBkYXRvcyBkZSB1biBDU1YgZXhpc3RlbnRlICgnJyBzaSBu
byBoYXkpLiIiIgogICAgdHJ5OgogICAgICAgIHdpdGggb3BlbihydXRhX2NzdiwgInIiLCBuZXds
aW5lPSIiLCBlbmNvZGluZz0idXRmLTgiKSBhcyBmOgogICAgICAgICAgICBmb3Igcm93IGluIGNz
di5EaWN0UmVhZGVyKGYpOgogICAgICAgICAgICAgICAgcmV0dXJuIHJvdy5nZXQoInByb3RvIikg
b3IgIiIKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgcGFzcwogICAgcmV0dXJuICIiCgoK
ZGVmIGNzdl9jYXJnYXJfaGVjaG9zKHJ1dGFfY3N2KToKICAgICIiIkRpY3QgaWQtPmZpbGEgZGUg
Y29ycmlkYXMgcHJldmlhcyB2YWxpZGFzIChtaXNtbyBwcm90bykuIFNvbG8gbGFzCiAgICBmaWxh
cyBTSSBjdWVudGFuIGNvbW8gaGVjaGFzOyB1bmEgY29uZmlnIHF1ZSBmYWxsbyBzZSByZS1taWRl
LiIiIgogICAgaGVjaG9zID0ge30KICAgIGlmIG5vdCBvcy5wYXRoLmV4aXN0cyhydXRhX2Nzdik6
CiAgICAgICAgcmV0dXJuIGhlY2hvcwogICAgdHJ5OgogICAgICAgIHdpdGggb3BlbihydXRhX2Nz
diwgInIiLCBuZXdsaW5lPSIiLCBlbmNvZGluZz0idXRmLTgiKSBhcyBmOgogICAgICAgICAgICBm
b3Igcm93IGluIGNzdi5EaWN0UmVhZGVyKGYpOgogICAgICAgICAgICAgICAgaWYgcm93LmdldCgi
cHJvdG8iKSA9PSBQUk9UTyBhbmQgcm93LmdldCgidmFsaWRvIikgPT0gIlNJIjoKICAgICAgICAg
ICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgICAgIGhlY2hvc1tpbnQocm93WyJp
ZCJdKV0gPSByb3cKICAgICAgICAgICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAg
ICAgICAgICAgICAgICAgICBwYXNzCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIHBhc3MK
ICAgIHJldHVybiBoZWNob3MKCgpkZWYgY3N2X2FwcGVuZChydXRhX2NzdiwgZmlsYSk6CiAgICBu
dWV2byA9IG5vdCBvcy5wYXRoLmV4aXN0cyhydXRhX2NzdikKICAgIHdpdGggb3BlbihydXRhX2Nz
diwgImEiLCBuZXdsaW5lPSIiLCBlbmNvZGluZz0idXRmLTgiKSBhcyBmOgogICAgICAgIHcgPSBj
c3YuRGljdFdyaXRlcihmLCBmaWVsZG5hbWVzPUNPTFVNTkFTKQogICAgICAgIGlmIG51ZXZvOgog
ICAgICAgICAgICB3LndyaXRlaGVhZGVyKCkKICAgICAgICB3LndyaXRlcm93KGZpbGEpCgojIC0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBlamVjdWNpb24gZGUgdW5hIGNvbmZpZyAtLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0KZGVmIG1lZGlyX2NvbmZpZyhjZmcsIGNvbnRleHRvKToKICAgICIi
IkNvcnJlIFVOQSBjb25maWcgY29tcGxldGE6IFJBTSBpbmljaWFsIC0+IHNlcnZlciB1cCAtPiA0
IHBhc2FkYXMgLT4KICAgIHNhbml0eSAtPiByZXBybyBUVEZUIChzaSBhcGxpY2EpIC0+IHByb2Jl
IGNvbmN1cnJlbnRlIC0+IFJBTSBmaW5hbCAtPgogICAgY2VydGlmaWNhZG9zIGRlbCBsb2cgLT4g
ZG93bi4gRGV2dWVsdmUgKGZpbGEgQ1NWLCBkYXRvcyBjb21wbGV0b3MpLiIiIgogICAgZGlyX2xv
Z3MgPSBjb250ZXh0b1siZGlyX2xvZ3MiXQogICAgbG9nX3BhdGggPSBvcy5wYXRoLmpvaW4oZGly
X2xvZ3MsICJsb2dzLWNvbmZpZyIsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAiJTAyZC0l
cy5sb2ciICUgKGNmZ1siaWQiXSwgY2ZnWyJub21icmUiXSkpCiAgICBmaWxhID0ge2M6ICIiIGZv
ciBjIGluIENPTFVNTkFTfQogICAgZmlsYS51cGRhdGUoeyJwcm90byI6IFBST1RPLCAiaWQiOiBj
ZmdbImlkIl0sICJub21icmUiOiBjZmdbIm5vbWJyZSJdLAogICAgICAgICAgICAgICAgICJmYW1p
bGlhIjogY2ZnWyJmYW1pbGlhIl0sICJmZWNoYV9ob3JhIjogYWhvcmEoKSwKICAgICAgICAgICAg
ICAgICAiZmxhZ3MiOiAiICIuam9pbihjZmdbImZsYWdzIl0pfSkKICAgIGNvbXBsZXRvID0geyJp
ZCI6IGNmZ1siaWQiXSwgIm5vbWJyZSI6IGNmZ1sibm9tYnJlIl0sCiAgICAgICAgICAgICAgICAi
ZmFtaWxpYSI6IGNmZ1siZmFtaWxpYSJdLCAiZmxhZ3MiOiBjZmdbImZsYWdzIl0sCiAgICAgICAg
ICAgICAgICAiaGlwb3Rlc2lzIjogY2ZnWyJoaXBvdGVzaXMiXSwgImxvZyI6IGxvZ19wYXRofQoK
ICAgICMgZWwgY29tYW5kbyBsYW56YWRvIGVzIFNJRU1QUkUgYmFzZSArIGRpZmYgKGVsIHVsdGlt
byB2YWxvciBnYW5hKQogICAgZmxhZ3NfZnVsbCA9IGxpc3QoY29udGV4dG8uZ2V0KCJiYXNlX2Zs
YWdzIikgb3IgW10pICsgbGlzdChjZmdbImZsYWdzIl0pCiAgICBmaWxhWyJmbGFncyJdID0gIiAi
LmpvaW4oZmxhZ3NfZnVsbCkKICAgIGNvbXBsZXRvWyJmbGFncyJdID0gZmxhZ3NfZnVsbAoKICAg
IHJhbTAgPSByYW1fc2lzdGVtYSgpCiAgICBpZiByYW0wOgogICAgICAgIGZpbGFbInJhbV9mcmVl
MF9taWIiXSA9IHN0cihyYW0wWzBdKQogICAgICAgIGNvbXBsZXRvWyJyYW0wIl0gPSByYW0wCgog
ICAgcHJpbnQoY3lhbigiICBbJTAyZF0gJXM6IGxhbnphbmRvIHNlcnZlci4uLiIgJSAoY2ZnWyJp
ZCJdLCBjZmdbIm5vbWJyZSJdKSkpCiAgICBwcm9jLCBsb2FkX3MsIGVzdGFkbyA9IGxhbnphcl9z
ZXJ2ZXIoY29udGV4dG9bInJ1dGFfc2VydmVyIl0sIGZsYWdzX2Z1bGwsCiAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgbG9nX3BhdGgsIGNvbnRleHRvWyJjYXJnYV90aW1l
b3V0Il0pCiAgICBmaWxhWyJsb2FkX3MiXSA9ICIlLjFmIiAlIGxvYWRfcyBpZiBsb2FkX3MgZWxz
ZSAiIgogICAgY29tcGxldG9bImxvYWRfcyJdID0gcm91bmQobG9hZF9zLCAxKSBpZiBsb2FkX3Mg
ZWxzZSBOb25lCiAgICBpZiBwcm9jIGlzIE5vbmU6CiAgICAgICAgZmlsYVsidmFsaWRvIl0gPSAi
Tk8iCiAgICAgICAgZmlsYVsibm90YSJdID0gImNhcmdhIGZhbGxpZGE6ICVzIiAlIGVzdGFkbwog
ICAgICAgIGxvZ190eHQgPSBsZWVyX2xvZ19zZXJ2ZXIobG9nX3BhdGgpCiAgICAgICAgaWYgbG9n
X3R4dC5nZXQoImZpdF9hYm9ydCIpOgogICAgICAgICAgICBmaWxhWyJub3RhIl0gKz0gIiAoZml0
IGFib3J0YWRvOiBWUkFNIGluc3VmaWNpZW50ZSBwYXJhIGVzdGEgY29uZmlnKSIKICAgICAgICAj
IGZvcmVuc2UgZW4gZWwgQ1NWICh2MS4zKTogZWwgY2FtcG8gMjgtb2N0IG5lY2VzaXRvIGVsIGxv
ZyBlbiBsYQogICAgICAgICMgbWFubyBwYXJhIGRpYWdub3N0aWNhciBzaW4gYWJyaXIgbG9ncy1j
b25maWcgYSBtYW5vCiAgICAgICAgZmlsYVsibm90YSJdICs9ICIgfCBsb2c6ICVzIiAlIGNvbGFf
bG9nKGxvZ19wYXRoLCBuPTMpWzoyMjBdCiAgICAgICAgcHJpbnQocmVkKCIgICAgRkFJTCBjYXJn
YSAoJXMpIiAlIGZpbGFbIm5vdGEiXSkpCiAgICAgICAgcHJpbnQocmVkKCIgICAgY29sYSBkZWwg
bG9nOiAlcyIgJSBjb2xhX2xvZyhsb2dfcGF0aCkpKQogICAgICAgIGNvbXBsZXRvLnVwZGF0ZSh7
InZhbGlkbyI6IEZhbHNlLCAibm90YSI6IGZpbGFbIm5vdGEiXSwKICAgICAgICAgICAgICAgICAg
ICAgICAgICJsb2dfZGF0b3MiOiBsb2dfdHh0LCAibG9nX2NvbGEiOiBjb2xhX2xvZyhsb2dfcGF0
aCl9KQogICAgICAgIHJldHVybiBmaWxhLCBjb21wbGV0bwoKICAgIHRyeToKICAgICAgICBtb2Rl
bG9fYmFzZW5hbWUgPSBvcy5wYXRoLmJhc2VuYW1lKGNvbnRleHRvLmdldCgicnV0YV9tb2RlbG8i
KSBvciAiIikKICAgICAgICBwdWVydG8gPSBjb250ZXh0by5nZXQoInB1ZXJ0byIsIFBVRVJUT19E
RUYpCiAgICAgICAgbG9nX3R4dCA9IGxlZXJfbG9nX3NlcnZlcihsb2dfcGF0aCwgbW9kZWxvX2Jh
c2VuYW1lPW1vZGVsb19iYXNlbmFtZSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
IHB1ZXJ0bz1wdWVydG8pCiAgICAgICAgIyAtLS0tIGlkZW50aWRhZCBkZWwgc2VydmVyOiBudW5j
YSBtZWRpciB1biBmYW50YXNtYSAtLS0tCiAgICAgICAgaWYgbG9nX3R4dC5nZXQoIm1vZGVsb19l
bl9sb2ciKSBpcyBGYWxzZToKICAgICAgICAgICAgZmlsYVsidmFsaWRvIl0gPSAiTk8iCiAgICAg
ICAgICAgIGZpbGFbIm5vdGEiXSA9ICgiZWwgbG9nIGRlbCBzZXJ2ZXIgTk8gbWVuY2lvbmEgZWwg
bW9kZWxvIGVzcGVyYWRvICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICIoJXMpOiBvdHJv
IHByb2Nlc28gb2N1cGEgZWwgcHVlcnRvICVzIG8gZWwgIgogICAgICAgICAgICAgICAgICAgICAg
ICAgICAgImFycmFucXVlIGZ1ZSByZWVtcGxhemFkbyIKICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICUgKGNvbnRleHRvLmdldCgicnV0YV9tb2RlbG8iKSwgcHVlcnRvKSkKICAgICAgICAgICAg
cHJpbnQocmVkKCIgICAgRkFJTCBpZGVudGlkYWQ6ICVzIiAlIGZpbGFbIm5vdGEiXSkpCiAgICAg
ICAgICAgIHByaW50KHJlZCgiICAgIGNvbGEgZGVsIGxvZzogJXMiICUgY29sYV9sb2cobG9nX3Bh
dGgpKSkKICAgICAgICAgICAgY29tcGxldG8udXBkYXRlKHsidmFsaWRvIjogRmFsc2UsICJub3Rh
IjogZmlsYVsibm90YSJdLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICJsb2dfZGF0b3Mi
OiBsb2dfdHh0LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICJsb2dfY29sYSI6IGNvbGFf
bG9nKGxvZ19wYXRoKX0pCiAgICAgICAgICAgIHJldHVybiBmaWxhLCBjb21wbGV0bwogICAgICAg
IGlmIGxvZ190eHQuZ2V0KCJwdWVydG9fZW5fbG9nIikgaXMgRmFsc2U6CiAgICAgICAgICAgIHBy
aW50KHllbGxvdygiICAgIEFWSVNPOiBlbCBsb2cgbm8gY29uZmlybWEgJ2xpc3RlbmluZyBvbicg
ZW4gZWwgIgogICAgICAgICAgICAgICAgICAgICAgICAgInB1ZXJ0byAlcyAoc2UgY29udGludWEs
IHBlcm8gcmV2aXNhcikiICUgcHVlcnRvKSkKCiAgICAgICAgdmFsaWRvID0gVHJ1ZQogICAgICAg
IG5vdGFzID0gW10KICAgICAgICBpZiBsb2dfdHh0LmdldCgiZml0X2luZm8iKToKICAgICAgICAg
ICAgbm90YXMuYXBwZW5kKGxvZ190eHQuZ2V0KCJmaXRfaW5mbyIpKQogICAgICAgIGlmIGxvZ190
eHQuZ2V0KCJmaXRfYWJvcnQiKToKICAgICAgICAgICAgdmFsaWRvID0gRmFsc2UKICAgICAgICAg
ICAgbm90YXMuYXBwZW5kKCJmaXQgYWJvcnRhZG8gZW4gZWwgbG9nIChjYXVzYSByZWFsLCBubyBl
bCBhdXRvLWZpdCkiKQogICAgICAgIGlmIGxvZ190eHQuZ2V0KCJzeXNtZW1fd2FybiIpOgogICAg
ICAgICAgICBub3Rhcy5hcHBlbmQoImF2aXNvIHN5c21lbS9zaGFyZWQgZW4gZWwgbG9nIChwb3Np
YmxlIHNwaWxsKSIpCgogICAgICAgIHZyYW0gPSBOb25lIGlmIGNvbnRleHRvWyJzaW5fbnZpZGlh
Il0gZWxzZSB2cmFtX252aWRpYSgpCiAgICAgICAgaWYgdnJhbToKICAgICAgICAgICAgZmlsYVsi
dnJhbV91c2FkYV9taWIiXSwgZmlsYVsidnJhbV90b3RhbF9taWIiXSA9IHN0cih2cmFtWzBdKSwg
c3RyKHZyYW1bMV0pCiAgICAgICAgICAgIGlmIHZyYW1bMF0gPiAzNzAwOgogICAgICAgICAgICAg
ICAgcHJpbnQoeWVsbG93KCIgICAgQVZJU08gVlJBTTogJWQgTWlCIHVzYWRvcyAoPjM3MDAsIHJp
ZXNnbyBkZSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgInN5c21lbSBmYWxsYmFjayki
ICUgdnJhbVswXSkpCgogICAgICAgICMgLS0tLSBtZWRpY2lvbiBlc3RpbG8gbGFib3JhdG9yaW8g
KFNTOCB2ZXJiYXRpbSkgLS0tLQogICAgICAgIG1lZF9vayA9IEZhbHNlCiAgICAgICAgcHJpbnQo
Y3lhbigiICAgIG1pZGllbmRvOiA0IHBhc2FkYXMgeCAyNTYgdG9rZW5zICh0ZW1wIDAsIHByb21w
dHMgIgogICAgICAgICAgICAgICAgICAgImRpc3RpbnRvcykuLi4iKSkKICAgICAgICB0cnk6CiAg
ICAgICAgICAgIHByZWZpbGwsIGRlY3MsIGRldGFsbGUgPSBwYXNhZGFzX21lZGljaW9uKHB1ZXJ0
bywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
UFJPTVBUU19NRURJQ0lPTiwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgcHJvYz1wcm9jKQogICAgICAgICAgICBtZWRfb2sgPSBUcnVlCiAgICAg
ICAgZXhjZXB0IE1lYXNFcnJvciBhcyBlOgogICAgICAgICAgICB2YWxpZG8gPSBGYWxzZSAgIyB1
bmEgbWVkaWNpb24gcXVlIGZhbGxvIEpBTUFTIGVzIHZhbGlkYQogICAgICAgICAgICBub3Rhcy5h
cHBlbmQoIm1lZGljaW9uIGZhbGxvOiAlcyIgJSBlKQogICAgICAgICAgICBwcmludChyZWQoIiAg
ICBGQUlMIG1lZGljaW9uOiAlcyIgJSBlKSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6
CiAgICAgICAgICAgIHZhbGlkbyA9IEZhbHNlCiAgICAgICAgICAgIG5vdGFzLmFwcGVuZCgibWVk
aWNpb24gZmFsbG8gKGluZXNwZXJhZG8pOiAlciIgJSBlKQogICAgICAgICAgICBwcmludChyZWQo
IiAgICBGQUlMIG1lZGljaW9uOiAlciIgJSBlKSkKCiAgICAgICAgaWYgbWVkX29rOgogICAgICAg
ICAgICBkZWMgPSBtZWRpYShkZWNzKQogICAgICAgICAgICBmaWxhWyJwcmVmaWxsX3RzIl0gPSBm
bXQocHJlZmlsbCwgMSkKICAgICAgICAgICAgZm9yIGosIHYgaW4gZW51bWVyYXRlKGRlY3MpOgog
ICAgICAgICAgICAgICAgZmlsYVsiZGVjX3IlZCIgJSAoaiArIDIpXSA9IGZtdCh2LCAyKQogICAg
ICAgICAgICBmaWxhWyJkZWNvZGVfdHMiXSA9IGZtdChkZWMsIDIpCiAgICAgICAgICAgIGNvbXBs
ZXRvLnVwZGF0ZSh7InByZWZpbGxfdHMiOiBwcmVmaWxsLCAiZGVjX3IyX2FfcjQiOiBkZWNzLAog
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICJkZWNvZGVfdHMiOiBkZWMsICJwYXNhZGFzIjog
ZGV0YWxsZX0pCiAgICAgICAgICAgICMgZGlzcGVyc2lvbiBlbnRyZSBwYXNhZGFzIChsZWNjaW9u
IHYxLjIuMTogb3V0bGllciB2aXNpYmxlKQogICAgICAgICAgICBpZiBsZW4oZGVjcykgPj0gMiBh
bmQgbWluKGRlY3MpID4gMDoKICAgICAgICAgICAgICAgIGRpc3AgPSBtYXgoZGVjcykgLyBtaW4o
ZGVjcykKICAgICAgICAgICAgICAgIGZpbGFbImRpc3BlcnNfbWF4X21pbiJdID0gIiUuM2YiICUg
ZGlzcAogICAgICAgICAgICAgICAgaWYgZGlzcCA+IDEuMDg6CiAgICAgICAgICAgICAgICAgICAg
bm90YXMuYXBwZW5kKCJkaXNwZXJzaW9uIGFsdGEgZW4gcGFzYWRhcyAobWF4L21pbj0lLjJmKTog
IgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAiY29uZmlybWFyIGNvbiBtZWRpYW5h
IGRlIDMgKFNTMTMpIiAlIGRpc3ApCgogICAgICAgICAgICAjIC0tLS0gc2FuaXR5IGF1dG8gKGh1
bW8tZGV0ZWN0b3IpIC0tLS0KICAgICAgICAgICAgaWYgY29udGV4dG9bImNvbl9zYW5pdHkiXToK
ICAgICAgICAgICAgICAgIG9rX24sIHRydW5jX24sIHRvdCwgc2RldCA9IHNhbml0eV9jaGF0KHB1
ZXJ0bykKICAgICAgICAgICAgICAgIGZpbGFbInNhbml0eV9va19uIl0gPSBzdHIob2tfbikKICAg
ICAgICAgICAgICAgIGZpbGFbInNhbml0eV90cnVuY19uIl0gPSBzdHIodHJ1bmNfbikKICAgICAg
ICAgICAgICAgIGZpbGFbInNhbml0eV90b3RhbCJdID0gc3RyKHRvdCkKICAgICAgICAgICAgICAg
IGNvbXBsZXRvWyJzYW5pdHkiXSA9IHNkZXQKICAgICAgICAgICAgICAgIGlmIG9rX24gPT0gdG90
OgogICAgICAgICAgICAgICAgICAgIG1hcmNhID0gZ3JlZW4oIiVkLyVkIiAlIChva19uLCB0b3Qp
KQogICAgICAgICAgICAgICAgZWxpZiB0cnVuY19uIGFuZCAob2tfbiArIHRydW5jX24gPT0gdG90
KToKICAgICAgICAgICAgICAgICAgICBtYXJjYSA9IHllbGxvdygiJWQgT0sgKyAlZFQvJWQiICUg
KG9rX24sIHRydW5jX24sIHRvdCkpCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAg
ICAgICAgIG1hcmNhID0gcmVkKCIlZC8lZCAoJWRUKSIgJSAob2tfbiwgdG90LCB0cnVuY19uKSkK
ICAgICAgICAgICAgICAgIHByaW50KCIgICAgc2FuaXR5IGF1dG86ICVzIiAlIG1hcmNhKQogICAg
ICAgICAgICAgICAgaWYgb2tfbiA8IHRvdDoKICAgICAgICAgICAgICAgICAgICBpZiB0cnVuY19u
IGFuZCAob2tfbiArIHRydW5jX24gPT0gdG90KToKICAgICAgICAgICAgICAgICAgICAgICAgbm90
YXMuYXBwZW5kKCJzYW5pdHkgJWQgT0sgKyAlZCB0cnVuY2FkYXMgKHByb2JlICIKICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICJjb3J0byBkZW50cm8gZGUgPHRoaW5rPiwgbm8g
ZXMgZmFsbG8gIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgImRlIGNhbGlk
YWQpIiAlIChva19uLCB0cnVuY19uKSkKICAgICAgICAgICAgICAgICAgICBlbHNlOgogICAgICAg
ICAgICAgICAgICAgICAgICBub3Rhcy5hcHBlbmQoInNhbml0eSBjb24gZmFsbG9zIHJlYWxlcyAo
JWQvMyBPSywgIgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIiVkIHRydW5j
YWRhcykiICUgKG9rX24sIHRydW5jX24pKQoKICAgICAgICAgICAgIyAtLS0tIHJlcHJvIGRlIHR1
cm5vcyBjcmVjaWVudGVzIChUVEZUIC8gY2VydGlmaWNhZG8gY2FjaGUpIC0tLS0KICAgICAgICAg
ICAgaWYgY2ZnWyJpZCJdIGluIFRURlRfSURTIGFuZCBub3QgY29udGV4dG8uZ2V0KCJzaW5fdHRm
dCIpOgogICAgICAgICAgICAgICAgcHJpbnQoY3lhbigiICAgIHJlcHJvIFRURlQ6ICVkIHR1cm5v
cyBjcmVjaWVudGVzIChzdHJlYW0pLi4uIgogICAgICAgICAgICAgICAgICAgICAgICAgICAlIFJF
UFJPX1RVUk5PUykpCiAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgcmVw
ID0gcmVwcm9fdHRmdChwdWVydG8sIHByb2M9cHJvYykKICAgICAgICAgICAgICAgICAgICBjb21w
bGV0b1sicmVwcm9fdHRmdCJdID0gcmVwCiAgICAgICAgICAgICAgICAgICAgZmlsYVsidHRmdF90
MSJdID0gZm10KHJlcC5nZXQoInQxX2ZyaWEiKSwgMikKICAgICAgICAgICAgICAgICAgICBmaWxh
WyJ0dGZ0X3QyIl0gPSBmbXQocmVwLmdldCgidDIiKSwgMikKICAgICAgICAgICAgICAgICAgICBm
aWxhWyJ0dGZ0X3RmaW4iXSA9IGZtdChyZXAuZ2V0KCJ0ZmluIiksIDIpCiAgICAgICAgICAgICAg
ICAgICAgaWYgcmVwLmdldCgidDIiKSBhbmQgcmVwLmdldCgidGZpbiIpOgogICAgICAgICAgICAg
ICAgICAgICAgICBjcmVjID0gKHJlcFsidGZpbiJdIC8gcmVwWyJ0MiJdIC0gMS4wKSAqIDEwMAog
ICAgICAgICAgICAgICAgICAgICAgICBmaWxhWyJ0dGZ0X2NyZWNpbWllbnRvX3BjdCJdID0gIiUu
MGYiICUgY3JlYwogICAgICAgICAgICAgICAgICAgIGZpbGFbInR0ZnRfdmVyZWRpY3RvIl0gPSBj
cml0ZXJpb190dGZ0KHJlcC5nZXQoInQyIiksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgcmVwLmdldCgidGZpbiIpKQogICAgICAgICAg
ICAgICAgICAgIHByaW50KCIgICAgVFRGVCB0Mj0lcyBzIC0+IHRmaW49JXMgcyAoJXMpIgogICAg
ICAgICAgICAgICAgICAgICAgICAgICUgKGZtdChyZXAuZ2V0KCJ0MiIpLCAyKSwgZm10KHJlcC5n
ZXQoInRmaW4iKSwgMiksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZmlsYVsidHRmdF92
ZXJlZGljdG8iXSkpCiAgICAgICAgICAgICAgICBleGNlcHQgTWVhc0Vycm9yIGFzIGU6CiAgICAg
ICAgICAgICAgICAgICAgbm90YXMuYXBwZW5kKCJyZXBybyBUVEZUIGZhbGxvOiAlcyIgJSBlKQog
ICAgICAgICAgICAgICAgICAgIHByaW50KHJlZCgiICAgIEZBSUwgcmVwcm86ICVzIiAlIGUpKQoK
ICAgICAgICAgICAgIyAtLS0tIHByb2JlIGRlIGNvbmN1cnJlbmNpYSAoY2VydGlmaWNhZG8gZGUg
LW5wKSAtLS0tCiAgICAgICAgICAgIGlmIG5vdCBjb250ZXh0by5nZXQoInNpbl9wcm9iZSIpOgog
ICAgICAgICAgICAgICAgYWdnLCB0b2sgPSBwcm9iZV9jb25jdXJyZW50ZShwdWVydG8sIHByb2M9
cHJvYykKICAgICAgICAgICAgICAgIGlmIGFnZzoKICAgICAgICAgICAgICAgICAgICBmaWxhWyJh
Z2dfdHMiXSA9IGZtdChhZ2csIDIpCiAgICAgICAgICAgICAgICAgICAgY29tcGxldG9bImFnZyJd
ID0geyJ0b2tlbnNfcyI6IGFnZywgInRva2VucyI6IHRva30KCiAgICAgICAgICAgICMgLS0tLSBS
QU0gZmluYWwgKyBjZXJ0aWZpY2Fkb3MgZGVsIGxvZyAoeWEgY29uIGVsIHJlcHJvIGRlbnRybykg
LS0tLQogICAgICAgICAgICByYW0xID0gcmFtX3Npc3RlbWEoKQogICAgICAgICAgICBpZiByYW0x
OgogICAgICAgICAgICAgICAgZmlsYVsicmFtX2ZyZWUxX21pYiJdID0gc3RyKHJhbTFbMF0pCiAg
ICAgICAgICAgICAgICBjb21wbGV0b1sicmFtMSJdID0gcmFtMQogICAgICAgICAgICBycHJvYyA9
IHJhbV9wcm9jZXNvX21pYihwcm9jLnBpZCkKICAgICAgICAgICAgaWYgcnByb2M6CiAgICAgICAg
ICAgICAgICBmaWxhWyJyYW1fcHJvY19taWIiXSA9IGZtdChycHJvYywgMSkKICAgICAgICAgICAg
ICAgIGNvbXBsZXRvWyJyYW1fcHJvY19taWIiXSA9IHJwcm9jCiAgICAgICAgICAgIGxvZ190eHQy
ID0gbGVlcl9sb2dfc2VydmVyKGxvZ19wYXRoLCBtb2RlbG9fYmFzZW5hbWU9bW9kZWxvX2Jhc2Vu
YW1lLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBwdWVydG89cHVlcnRv
KQogICAgICAgICAgICBsb2dfdHh0LnVwZGF0ZSh7azogdiBmb3IgaywgdiBpbiBsb2dfdHh0Mi5p
dGVtcygpCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBpZiBrIGluICgiY2FjaGVfcmV1c2Vf
d2FybiIsICJjYWNoZV9yZXN0b3JlZF9uIiwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICJjYWNoZV9mb3JjaW5nX24iLCAiZ3JhcGhzX29rIiwKICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICJyZXBhY2tfb2siKX0pCiAgICAgICAgICAgIHRpZW5lX3JldXNl
ID0gYW55KHRvayA9PSAiLS1jYWNoZS1yZXVzZSIgZm9yIHRvayBpbiBjZmdbImZsYWdzIl0pCiAg
ICAgICAgICAgIGZpbGFbImNhY2hlX3JldXNlX3dhcm4iXSA9ICJTSSIgaWYgbG9nX3R4dC5nZXQo
ImNhY2hlX3JldXNlX3dhcm4iKSBlbHNlICIiCiAgICAgICAgICAgIGZpbGFbImNhY2hlX3Jlc3Rv
cmVkX24iXSA9IHN0cihsb2dfdHh0LmdldCgiY2FjaGVfcmVzdG9yZWRfbiIpIG9yICIwIikKICAg
ICAgICAgICAgZmlsYVsiY2FjaGVfZm9yY2luZ19uIl0gPSBzdHIobG9nX3R4dC5nZXQoImNhY2hl
X2ZvcmNpbmdfbiIpIG9yICIwIikKICAgICAgICAgICAgZmlsYVsiZ3JhcGhzX29rIl0gPSAiU0ki
IGlmIGxvZ190eHQuZ2V0KCJncmFwaHNfb2siKSBlbHNlICIiCiAgICAgICAgICAgIGZpbGFbInJl
cGFja19vayJdID0gIlNJIiBpZiBsb2dfdHh0LmdldCgicmVwYWNrX29rIikgZWxzZSAiIgogICAg
ICAgICAgICBjZXN0YWRvID0gY3JpdGVyaW9fY2FjaGUodGllbmVfcmV1c2UsCiAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICBsb2dfdHh0LmdldCgiY2FjaGVfcmV1c2Vfd2FybiIp
LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgbG9nX3R4dC5nZXQoImNhY2hl
X3Jlc3RvcmVkX24iKSBvciAwLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
bG9nX3R4dC5nZXQoImNhY2hlX2ZvcmNpbmdfbiIpIG9yIDApCiAgICAgICAgICAgIGZpbGFbImNh
Y2hlX2VzdGFkbyJdID0gY2VzdGFkbwogICAgICAgICAgICBjb21wbGV0b1siY2FjaGVfZXN0YWRv
Il0gPSBjZXN0YWRvCiAgICAgICAgICAgIGlmIGNlc3RhZG8gPT0gIk5PLVNPUE9SVEFETyI6CiAg
ICAgICAgICAgICAgICBub3Rhcy5hcHBlbmQoImNhY2hlX3JldXNlIE5PIFNPUE9SVEFEQSBlbiBl
c3RlIGNvbnRleHRvICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAiKCMyNDA1NSk6IGxh
IHZpYSBxdWVkYSBjb25kaWNpb25hZGEgYSBidWlsZC8iCiAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgImNvbG9jYWNpb24gLT4gUlVUQSAwIGdhbmEgdW4gbW90aXZvIikKICAgICAgICAgICAg
ZWxpZiBjZXN0YWRvID09ICJST1RPIjoKICAgICAgICAgICAgICAgIG5vdGFzLmFwcGVuZCgiY2Fj
aGUgUk9UTyBlbiBlbCByZXBybyAoIzIxODMxKTogJ2ZvcmNpbmcgZnVsbCAiCiAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgInByb21wdCByZS1wcm9jZXNzaW5nJyBzaW4gY2hlY2twb2ludHMg
dXRpbGVzIikKICAgICAgICAgICAgZWxpZiBjZXN0YWRvID09ICJNSVhUTyI6CiAgICAgICAgICAg
ICAgICBub3Rhcy5hcHBlbmQoImNhY2hlIE1JWFRBOiBoYXkgcmVzdG9yZWQgWSBmb3JjaW5nOyBs
ZWVyIGVsICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAicmVwcm8gdHVybm8gYSB0dXJu
byAoSlNPTikiKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIGNvbXBsZXRvLnVwZGF0ZSh7ImVy
cm9yZXMiOiBsaXN0KG5vdGFzKX0pCgogICAgICAgIGZpbGFbInZhbGlkbyJdID0gIlNJIiBpZiB2
YWxpZG8gZWxzZSAiTk8iCiAgICAgICAgZmlsYVsibm90YSJdID0gIjsgIi5qb2luKG5vdGFzKQog
ICAgICAgIGVzdGFkb19ydW4gPSBncmVlbigiVkFMSURPIikgaWYgdmFsaWRvIGVsc2UgcmVkKCJJ
TlZBTElETyIpCiAgICAgICAgcHJpbnQoIiAgICBkZWNvZGUgJXMgdC9zIHwgcHJlZmlsbCAlcyB0
b2svcyB8IGFnZyAlcyB0b2svcyB8ICVzICVzIgogICAgICAgICAgICAgICUgKGJvbGQoZm10KGZp
bGEuZ2V0KCJkZWNvZGVfdHMiKSBvciBOb25lKSksCiAgICAgICAgICAgICAgICAgZm10KGZpbGEu
Z2V0KCJwcmVmaWxsX3RzIikgb3IgTm9uZSwgMCksCiAgICAgICAgICAgICAgICAgZm10KGZpbGEu
Z2V0KCJhZ2dfdHMiKSBvciBOb25lLCAwKSwgZXN0YWRvX3J1biwKICAgICAgICAgICAgICAgICBn
cmF5KCgiOyAiICsgIjsgIi5qb2luKG5vdGFzKSkgaWYgbm90YXMgZWxzZSAiIikpKQogICAgZmlu
YWxseToKICAgICAgICBhcGFnYXJfc2VydmVyKHByb2MpCiAgICByZXR1cm4gZmlsYSwgY29tcGxl
dG8KCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBpbmZvcm1lIC0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KZGVmIF9kaWZfdmVyZWRpY3RvKGRlYywgYW5jbGFf
ZGVjKToKICAgICIiIkdBTkEvRU1QQVRBL1BJRVJERSB2cyBhbmNsYSBjb24gZWwgcnVpZG8gZGVj
bGFyYWRvICsvLTAuNSAoU1M4KS4iIiIKICAgIGlmIG5vdCBkZWMgb3Igbm90IGFuY2xhX2RlYzoK
ICAgICAgICByZXR1cm4gIk4vRCIsIDAuMAogICAgZGlmID0gZGVjIC0gYW5jbGFfZGVjCiAgICBp
ZiBkaWYgPiBURUNIT19SVUlETzoKICAgICAgICByZXR1cm4gIkdBTkEiLCBkaWYKICAgIGlmIGRp
ZiA+PSAtVEVDSE9fUlVJRE86CiAgICAgICAgcmV0dXJuICJFTVBBVEEiLCBkaWYKICAgIHJldHVy
biAiUElFUkRFIiwgZGlmCgoKZGVmIHByb3RvY29sb19kZWNpc2lvbihyZXN1bHRhZG9zLCBhbmNs
YV9kZWMpOgogICAgIiIiRXZhbHVhIGF1dG9tYXRpY2FtZW50ZSBlbCBhcmJvbCBkZWwgTjM6IGJv
b2tlbmQsIGZhbWlsaWEgUkFNLCBmYW1pbGlhCiAgICBjYWNoZSAoY2VydGlmaWNhZG8gKyBUVEZU
KSwgc2xvdHMgKHByb2JlIGFncmVnYWRvKSwgTkNNIGFwaWxhZGEsIGNvbWJvcwogICAgeSBlbCBj
b250cm9sIE5PQ0FDSEUuIERldnVlbHZlIGxpbmVhcyBtZC4iIiIKICAgIGxpbmVhcyA9IFtdCgog
ICAgZGVmIGRlY19kZShjaWQpOgogICAgICAgIHIgPSByZXN1bHRhZG9zLmdldChjaWQpIG9yIHt9
CiAgICAgICAgdHJ5OgogICAgICAgICAgICByZXR1cm4gZmxvYXQoci5nZXQoImRlY29kZV90cyIp
KSBpZiByLmdldCgiZGVjb2RlX3RzIikgZWxzZSBOb25lCiAgICAgICAgZXhjZXB0IChUeXBlRXJy
b3IsIFZhbHVlRXJyb3IpOgogICAgICAgICAgICByZXR1cm4gTm9uZQoKICAgIGRlZiBhZ2dfZGUo
Y2lkKToKICAgICAgICByID0gcmVzdWx0YWRvcy5nZXQoY2lkKSBvciB7fQogICAgICAgIHRyeToK
ICAgICAgICAgICAgcmV0dXJuIGZsb2F0KHIuZ2V0KCJhZ2dfdHMiKSkgaWYgci5nZXQoImFnZ190
cyIpIGVsc2UgTm9uZQogICAgICAgIGV4Y2VwdCAoVHlwZUVycm9yLCBWYWx1ZUVycm9yKToKICAg
ICAgICAgICAgcmV0dXJuIE5vbmUKCiAgICAjIC0tLS0gYm9va2VuZCAtLS0tCiAgICBmaW4gPSBk
ZWNfZGUoMTMpCiAgICBpZiBhbmNsYV9kZWMgYW5kIGZpbjoKICAgICAgICBkcmlmdCA9IChmaW4g
LyBhbmNsYV9kZWMgLSAxLjApICogMTAwCiAgICAgICAgaWYgYWJzKGRyaWZ0KSA8PSA1LjA6CiAg
ICAgICAgICAgIGxpbmVhcy5hcHBlbmQoIi0gQk9PS0VORCBFU1RBQkxFOiBhbmNsYSBmaW4gJS4y
ZiB2cyBpbmljaW8gJS4yZiAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgIiglKy4xZiUlLCBk
ZW50cm8gZGVsICsvLTUlJSk6IGxvcyBkZWx0YXMgZGUgbGEgIgogICAgICAgICAgICAgICAgICAg
ICAgICAgICJzZXNpb24gc2UgbGVlbiBsaW1waW9zLiIgJSAoZmluLCBhbmNsYV9kZWMsIGRyaWZ0
KSkKICAgICAgICBlbHNlOgogICAgICAgICAgICBsaW5lYXMuYXBwZW5kKCItIERFUklWQSBERSBT
RVNJT04gJSsuMWYlJSAoYW5jbGEgJS4yZiAtPiBmaW4gIgogICAgICAgICAgICAgICAgICAgICAg
ICAgICIlLjJmKTogbGVlciBsb3MgZGVsdGFzIGNvbiBjdWlkYWRvIChsZWNjaW9uICIKICAgICAg
ICAgICAgICAgICAgICAgICAgICAidjEuMi4xOiBsYSAxYSBjb25maWcgc2FsZSBsZW50YSB5IGVs
IGRpYSBzZSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgIm11ZXZlKS4iICUgKGRyaWZ0LCBh
bmNsYV9kZWMsIGZpbikpCgogICAgIyAtLS0tIGZhbWlsaWEgUkFNICgyLDMsNCk6IGRlY29kZSAr
IFJBTSAtLS0tCiAgICBycHJvY19hbmNsYSA9IE5vbmUKICAgIHRyeToKICAgICAgICBycHJvY19h
bmNsYSA9IGZsb2F0KChyZXN1bHRhZG9zLmdldCgxKSBvciB7fSkuZ2V0KCJyYW1fcHJvY19taWIi
KSBvciAiIikgb3IgTm9uZQogICAgZXhjZXB0IChUeXBlRXJyb3IsIFZhbHVlRXJyb3IpOgogICAg
ICAgIHBhc3MKICAgIGZvciBjaWQgaW4gKDIsIDMsIDQpOgogICAgICAgIHIgPSByZXN1bHRhZG9z
LmdldChjaWQpIG9yIHt9CiAgICAgICAgZGVjID0gZGVjX2RlKGNpZCkKICAgICAgICB2LCBkaWYg
PSBfZGlmX3ZlcmVkaWN0byhkZWMsIGFuY2xhX2RlYykKICAgICAgICBpZiBub3QgZGVjOgogICAg
ICAgICAgICBjb250aW51ZQogICAgICAgIGV4dHJhID0gIiIKICAgICAgICBycHJvYyA9IE5vbmUK
ICAgICAgICB0cnk6CiAgICAgICAgICAgIHJwcm9jID0gZmxvYXQoci5nZXQoInJhbV9wcm9jX21p
YiIpIG9yICIiKSBvciBOb25lCiAgICAgICAgZXhjZXB0IChUeXBlRXJyb3IsIFZhbHVlRXJyb3Ip
OgogICAgICAgICAgICBwYXNzCiAgICAgICAgaWYgcnByb2MgYW5kIHJwcm9jX2FuY2xhOgogICAg
ICAgICAgICBkZWx0YSA9IHJwcm9jX2FuY2xhIC0gcnByb2MKICAgICAgICAgICAgaWYgZGVsdGEg
Pj0gMzAwOgogICAgICAgICAgICAgICAgZXh0cmEgPSAoIjsgUkFNIHByb2Nlc28gLSUuMGYgTWlC
IChjZXJ0aWZpY2FkbyBkZSBsYSBkb3NpcykiCiAgICAgICAgICAgICAgICAgICAgICAgICAlIGRl
bHRhKQogICAgICAgICAgICBlbGlmIGRlbHRhIDw9IC0zMDA6CiAgICAgICAgICAgICAgICBleHRy
YSA9ICgiOyBPSk86IFJBTSBwcm9jZXNvICslLjBmIE1pQiAobGEgZG9zaXMgTk8gbGliZXJvKSIK
ICAgICAgICAgICAgICAgICAgICAgICAgICUgKC1kZWx0YSkpCiAgICAgICAgICAgIGVsc2U6CiAg
ICAgICAgICAgICAgICBleHRyYSA9ICI7IFJBTSBwcm9jZXNvIH5wbGFuYSAoJSsuMGYgTWlCKSIg
JSBkZWx0YQogICAgICAgIGlmIHYgPT0gIlBJRVJERSI6CiAgICAgICAgICAgIHZlciA9ICgiUElF
UkRFICglLjJmKTogU0UgREVTQ0FSVEEgKG5vIHNlIHByb21vY2lvbmEgdW5hIGRvc2lzICIKICAg
ICAgICAgICAgICAgICAgICJxdWUgZnJlbmEpIiAlIGRpZikKICAgICAgICBlbGlmIHYgPT0gIkdB
TkEiOgogICAgICAgICAgICB2ZXIgPSAiR0FOQSB2cyBhbmNsYSAoKyUuMmYpOiBjYW5kaWRhdGEg
ZnVlcnRlIGEgY29uZmlnLnR4dCIgJSBkaWYKICAgICAgICBlbHNlOgogICAgICAgICAgICB2ZXIg
PSAoIkVNUEFUQSAoJSsuMmYsIGRlbnRybyBkZWwgcnVpZG8pOiBkZWNvZGUgaW50YWN0byAtPiAi
CiAgICAgICAgICAgICAgICAgICAiY2FuZGlkYXRhIGEgY29uZmlnLnR4dCBQT1IgTEEgUkFNLCBu
byBwb3IgZGVjb2RlIiAlIGRpZikKICAgICAgICBsaW5lYXMuYXBwZW5kKCItICVzOiBkZWNvZGUg
JXMgdnMgYW5jbGEgJXMgLT4gJXMlcyIKICAgICAgICAgICAgICAgICAgICAgICUgKHIuZ2V0KCJu
b21icmUiKSwgZm10KGRlYyksIGZtdChhbmNsYV9kZWMpLCB2ZXIsIGV4dHJhKSkKCiAgICAjIC0t
LS0gZmFtaWxpYSBjYWNoZSAoNSw2KTogY2VydGlmaWNhZG8gKyBUVEZUICsgZGVjb2RlIC0tLS0K
ICAgIGZvciBjaWQgaW4gKDUsIDYpOgogICAgICAgIHIgPSByZXN1bHRhZG9zLmdldChjaWQpIG9y
IHt9CiAgICAgICAgZGVjID0gZGVjX2RlKGNpZCkKICAgICAgICBpZiBub3QgZGVjOgogICAgICAg
ICAgICBjb250aW51ZQogICAgICAgIHYsIGRpZiA9IF9kaWZfdmVyZWRpY3RvKGRlYywgYW5jbGFf
ZGVjKQogICAgICAgIGVzdGFkbyA9IHIuZ2V0KCJjYWNoZV9lc3RhZG8iKSBvciAiTi9EIgogICAg
ICAgIHR2ZXIgPSByLmdldCgidHRmdF92ZXJlZGljdG8iKSBvciAiTi9EIgogICAgICAgIGlmIGVz
dGFkbyA9PSAiTk8tU09QT1JUQURPIjoKICAgICAgICAgICAgbGluZWFzLmFwcGVuZCgiLSAlczog
Y2FjaGUgTk8gU09QT1JUQURBICgjMjQwNTUpIC0+IGxhIHZpYSAiCiAgICAgICAgICAgICAgICAg
ICAgICAgICAgImNhY2hlLXJldXNlIHF1ZWRhIGNvbmRpY2lvbmFkYSBhIGJ1aWxkL2NvbG9jYWNp
b247ICIKICAgICAgICAgICAgICAgICAgICAgICAgICAiUlVUQSAwIGdhbmEgdW4gbW90aXZvIChk
ZWNvZGUgZGUgZXN0YSBzZXNpb246ICVzICIKICAgICAgICAgICAgICAgICAgICAgICAgICAidC9z
LCAlcyB2cyBhbmNsYSkuIgogICAgICAgICAgICAgICAgICAgICAgICAgICUgKHIuZ2V0KCJub21i
cmUiKSwgZm10KGRlYyksIHYpKQogICAgICAgIGVsaWYgZXN0YWRvID09ICJTQU5PIiBhbmQgdHZl
ciA9PSAiUExBTk8iOgogICAgICAgICAgICBsaW5lYXMuYXBwZW5kKCItICVzOiBjYWNoZSBTQU5P
ICsgVFRGVCBQTEFOTyArIGRlY29kZSAlcyB2cyAiCiAgICAgICAgICAgICAgICAgICAgICAgICAg
ImFuY2xhICglcywgJSsuMmYpIC0+IExBIEpPWUEgQ0VSVElGSUNBREE6ICIKICAgICAgICAgICAg
ICAgICAgICAgICAgICAiY2FuZGlkYXRhIGEgY29uZmlnLnR4dC4iICUgKHIuZ2V0KCJub21icmUi
KSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
IGZtdChkZWMpLCB2LCBkaWYpKQogICAgICAgIGVsaWYgZXN0YWRvID09ICJST1RPIiBvciB0dmVy
ID09ICJDUkVDRSI6CiAgICAgICAgICAgIGxpbmVhcy5hcHBlbmQoIi0gJXM6IGNhY2hlICVzIC8g
VFRGVCAlcyAoZGVjb2RlICVzLCAlcykgLT4gZWwgIgogICAgICAgICAgICAgICAgICAgICAgICAg
ICJoaWJyaWRvIHJlLXByb2Nlc2E7IG1pdGlnYWNpb25lczogUlVUQSAwIChjcGVudCAiCiAgICAg
ICAgICAgICAgICAgICAgICAgICAgIm5vIGV4aXN0ZSBlbiBiMTE4NTYpLCBwYXJjaGUsIG8gYWNl
cHRhciBlbCBjb3N0ZSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgIm1lZGlkby4iICUgKHIu
Z2V0KCJub21icmUiKSwgZXN0YWRvLCB0dmVyLAogICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICBmbXQoZGVjKSwgdikpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgbGluZWFz
LmFwcGVuZCgiLSAlczogY2FjaGUgJXMgLyBUVEZUICVzIChkZWNvZGUgJXMsICVzICUrLjJmKSAi
CiAgICAgICAgICAgICAgICAgICAgICAgICAgIi0+IHJldmlzYXIgZWwgSlNPTiB0dXJubyBhIHR1
cm5vIGFudGVzIGRlICIKICAgICAgICAgICAgICAgICAgICAgICAgICAiZGVjaWRpci4iICUgKHIu
Z2V0KCJub21icmUiKSwgZXN0YWRvLCB0dmVyLAogICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgZm10KGRlYyksIHYsIGRpZikpCgogICAgIyAtLS0tIHNsb3RzICg3KTogcHJv
YmUgYWdyZWdhZG8gLS0tLQogICAgZGVjNyA9IGRlY19kZSg3KQogICAgaWYgZGVjNzoKICAgICAg
ICBhZ2c3ID0gYWdnX2RlKDcpCiAgICAgICAgYWdnMSA9IGFnZ19kZSgxKQogICAgICAgIGV4dHJh
ID0gIiIKICAgICAgICBpZiBhZ2c3IGFuZCBhZ2cxOgogICAgICAgICAgICBnID0gKGFnZzcgLyBh
Z2cxIC0gMS4wKSAqIDEwMAogICAgICAgICAgICBleHRyYSA9ICgiOyBwcm9iZSBhZ3JlZ2FkbyAl
LjFmIHZzIGFuY2xhICUuMWYgdG9rL3MgKCUrLjFmJSUpIgogICAgICAgICAgICAgICAgICAgICAl
IChhZ2c3LCBhZ2cxLCBnKSkKICAgICAgICAgICAgaWYgZyA+PSA1LjA6CiAgICAgICAgICAgICAg
ICBleHRyYSArPSAiIC0+IGNvbmN1cnJlbmNpYSBjZXJ0aWZpY2FkYS4iCiAgICAgICAgICAgIGVs
c2U6CiAgICAgICAgICAgICAgICBleHRyYSArPSAiIC0+IFNJTiBnYW5hbmNpYSBkZSBjb25jdXJy
ZW5jaWEgbWVkaWJsZS4iCiAgICAgICAgbGluZWFzLmFwcGVuZCgiLSBOMy1OUDI6IGRlY29kZSBw
b3Igc2xvdCAlcyB2cyBhbmNsYSAoJXMgJSsuMmYpOyAiCiAgICAgICAgICAgICAgICAgICAgICAi
ZWwgKzE0JSUgW00gU1M0XSBzb2xvIGFwYXJlY2UgY29uIDIgc2VzaW9uZXMgYSBsYSAiCiAgICAg
ICAgICAgICAgICAgICAgICAidmV6LiVzIiAlIChmbXQoZGVjNyksCiAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICBfZGlmX3ZlcmVkaWN0byhkZWM3LCBhbmNsYV9kZWMpWzBdLAogICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgX2RpZl92ZXJlZGljdG8oZGVjNywgYW5jbGFf
ZGVjKVsxXSwgZXh0cmEpKQoKICAgICMgLS0tLSBOQ00gYXBpbGFkYSAoOCkgdnMgaGlzdG9yaWNv
IHkgdnMgY29tYm8gKDEwKSAtLS0tCiAgICBkZWM4ID0gZGVjX2RlKDgpCiAgICBpZiBkZWM4Ogog
ICAgICAgIHYsIGRpZiA9IF9kaWZfdmVyZWRpY3RvKGRlYzgsIGFuY2xhX2RlYykKICAgICAgICBy
ZWYgPSAiIgogICAgICAgIGlmIE5DTTM3QzRfUkVGOgogICAgICAgICAgICBkOCA9IChkZWM4IC8g
TkNNMzdDNF9SRUYgLSAxLjApICogMTAwCiAgICAgICAgICAgIHJlZiA9ICgiIChoaXN0b3JpY28g
TkNNMzdDNCBzaW4gVUIxSzogJS4yZjsgZWwgc3RhY2sgVUIxSyB4IE5DTSAiCiAgICAgICAgICAg
ICAgICAgICAic2FsZSAlKy4xZiUlKSIgJSAoTkNNMzdDNF9SRUYsIGQ4KSkKICAgICAgICBsaW5l
YXMuYXBwZW5kKCItIE4zLU5DTTM3QzQtVUI6ICVzIHQvcyB2cyBhbmNsYSAoJXMsICUrLjJmKSVz
LiIKICAgICAgICAgICAgICAgICAgICAgICUgKGZtdChkZWM4KSwgdiwgZGlmLCByZWYpKQogICAg
ZGVjMTAgPSBkZWNfZGUoMTApCiAgICBpZiBkZWMxMCBhbmQgZGVjODoKICAgICAgICBkaWYxMDgg
PSBkZWMxMCAtIGRlYzgKICAgICAgICBpZiBkaWYxMDggPiBURUNIT19SVUlETzoKICAgICAgICAg
ICAgdmVyID0gKCJHQU5BICUrLjJmIHNvYnJlIE5DTTM3QzQgc29sYTogZWwgY29tYm8gZGUgbGEg
U1M4LjEgIgogICAgICAgICAgICAgICAgICAgImNlcnRpZmljYSAtPiBjYW5kaWRhdG8gYSBjb25m
aWcudHh0IGNvbiAtYyA0MDk2IiAlIGRpZjEwOCkKICAgICAgICBlbGlmIGRpZjEwOCA+PSAtVEVD
SE9fUlVJRE86CiAgICAgICAgICAgIHZlciA9ICgiRU1QQVRBIGNvbiBOQ00zN0M0IHNvbGEgKCUr
LjJmKTogZWwgY2FjaGUgbm8gc3VtYSBkZWNvZGUgIgogICAgICAgICAgICAgICAgICAgImFoaSwg
cGVybyBzdW1hIFJBTS9UVEZUOyBkZWNpZGlyIGNvbiBlbCBjZXJ0aWZpY2FkbyAiCiAgICAgICAg
ICAgICAgICAgICAiY2FjaGUgZGUgZXN0YSBmaWxhIiAlIGRpZjEwOCkKICAgICAgICBlbHNlOgog
ICAgICAgICAgICB2ZXIgPSAoIlBJRVJERSAlKy4yZiB2cyBOQ00zN0M0IHNvbGE6IHJldmlzYXIg
bGEgVlJBTSBkZSBsYSAiCiAgICAgICAgICAgICAgICAgICAiY29sdW1uYSBidWZmZXIvVlJBTSBh
bnRlcyBkZSBkZXNjYXJ0YXIiICUgZGlmMTA4KQogICAgICAgIGxpbmVhcy5hcHBlbmQoIi0gTjMt
Q09NQk8tVDogJXMgdC9zIHZzIE5DTTM3QzQtVUIgZGUgZXN0YSBzZXNpb24gIgogICAgICAgICAg
ICAgICAgICAgICAgIiglcyk6ICVzIiAlIChmbXQoZGVjMTApLCBmbXQoZGVjOCksIHZlcikpCgog
ICAgIyAtLS0tIGNvbWJvcyBSQU0gKDkpOiBsYSBwcm9tb2Npb24gbmF0dXJhbCAtLS0tCiAgICBk
ZWM5ID0gZGVjX2RlKDkpCiAgICBpZiBkZWM5OgogICAgICAgIHYsIGRpZiA9IF9kaWZfdmVyZWRp
Y3RvKGRlYzksIGFuY2xhX2RlYykKICAgICAgICBlc3Q5ID0gKHJlc3VsdGFkb3MuZ2V0KDkpIG9y
IHt9KS5nZXQoImNhY2hlX2VzdGFkbyIpIG9yICJOL0QiCiAgICAgICAgdHY5ID0gKHJlc3VsdGFk
b3MuZ2V0KDkpIG9yIHt9KS5nZXQoInR0ZnRfdmVyZWRpY3RvIikgb3IgIk4vRCIKICAgICAgICBp
ZiB2ICE9ICJQSUVSREUiIGFuZCBlc3Q5IGluICgiU0FOTyIsICJOTy1BUExJQ0EiKSBhbmQgdHY5
ICE9ICJDUkVDRSI6CiAgICAgICAgICAgIGxpbmVhcy5hcHBlbmQoIi0gTjMtQ09NQk8tUjogZGVj
b2RlICVzICglcyAlKy4yZikgY29uIFJBTSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgImxp
YmVyYWRhIHkgY2FjaGUgJXMvVFRGVCAlcyAtPiBDT01CTyBTRUdVUk8gIgogICAgICAgICAgICAg
ICAgICAgICAgICAgICJjZXJ0aWZpY2FkbzogY2FuZGlkYXRhICMxIGEgY29uZmlnLnR4dC4iCiAg
ICAgICAgICAgICAgICAgICAgICAgICAgJSAoZm10KGRlYzkpLCB2LCBkaWYsIGVzdDksIHR2OSkp
CiAgICAgICAgZWxzZToKICAgICAgICAgICAgbGluZWFzLmFwcGVuZCgiLSBOMy1DT01CTy1SOiBk
ZWNvZGUgJXMgKCVzICUrLjJmKSwgY2FjaGUgJXMsICIKICAgICAgICAgICAgICAgICAgICAgICAg
ICAiVFRGVCAlcyAtPiBOTyBzZSBwcm9tb2Npb25hIHRhbCBjdWFsOyBzZXBhcmFyICIKICAgICAg
ICAgICAgICAgICAgICAgICAgICAiZG9zaXMgY29uIC0tc29sbyByYW0gLyAtLXNvbG8gY2FjaGUu
IgogICAgICAgICAgICAgICAgICAgICAgICAgICUgKGZtdChkZWM5KSwgdiwgZGlmLCBlc3Q5LCB0
djkpKQoKICAgICMgLS0tLSBjb250cm9sIE5PQ0FDSEUgKDEyKTogREVCRSBjcmVjZXIgLS0tLQog
ICAgcjEyID0gcmVzdWx0YWRvcy5nZXQoMTIpIG9yIHt9CiAgICBpZiByMTIuZ2V0KCJkZWNvZGVf
dHMiKToKICAgICAgICB0djEyID0gcjEyLmdldCgidHRmdF92ZXJlZGljdG8iKSBvciAiTi9EIgog
ICAgICAgIHYxMiwgZGlmMTIgPSBfZGlmX3ZlcmVkaWN0byhkZWNfZGUoMTIpLCBhbmNsYV9kZWMp
CiAgICAgICAgaWYgdHYxMiA9PSAiQ1JFQ0UiOgogICAgICAgICAgICBsaW5lYXMuYXBwZW5kKCIt
IE4zLU5PQ0FDSEUgKGNvbnRyb2wpOiBUVEZUICVzIGNvbW8gc2UgZXNwZXJhYmEgIgogICAgICAg
ICAgICAgICAgICAgICAgICAgICIoc2luIGNhY2hlIFRPRE8gdHVybm8gcmUtcGFnYSk7IGRlY29k
ZSAlcyAoJXMgIgogICAgICAgICAgICAgICAgICAgICAgICAgICIlKy4yZik6IGVsIGNhY2hlIG5v
IHBhZ2EgZGVjb2RlLCBwYWdhIFRURlQuIgogICAgICAgICAgICAgICAgICAgICAgICAgICUgKHR2
MTIsIGZtdChkZWNfZGUoMTIpKSwgdjEyLCBkaWYxMikpCiAgICAgICAgZWxzZToKICAgICAgICAg
ICAgbGluZWFzLmFwcGVuZCgiLSBOMy1OT0NBQ0hFIChjb250cm9sKTogVFRGVCAlcyBJTkVTUEVS
QURPICIKICAgICAgICAgICAgICAgICAgICAgICAgICAiKGRlYmVyaWEgQ1JFY2VyIHNpbiBjYWNo
ZSkgLT4gcmV2aXNhciBlbCBsb2cgIgogICAgICAgICAgICAgICAgICAgICAgICAgICIoZWwgY2Fj
aGUgcXVpemFzIG5vIHNlIGFwYWdvIGRlIHZlcmRhZCkuIgogICAgICAgICAgICAgICAgICAgICAg
ICAgICUgdHYxMikKICAgIHJldHVybiBsaW5lYXMKCgpkZWYgZ2VuZXJhcl9pbmZvcm1lKGRpcl9s
b2dzLCBjb250ZXh0bywgcmVzdWx0YWRvcywgY29tcGxldG9zLCBwcm9ibGVtYXNfZmxhZ3MpOgog
ICAgbWQgPSBbXQogICAgbWQuYXBwZW5kKCIjIElORk9STUUgRkFTRSBOMyDigJQgTklWRUwgMzog
ZWZpY2llbmNpYSBzaW1wbGUgKGNvc2VjaGEpIikKICAgIG1kLmFwcGVuZCgiIikKICAgIG1kLmFw
cGVuZCgiR2VuZXJhZG86ICVzIMK3ICVzIMK3IHByb3RvICVzIiAlIChhaG9yYSgpLCBWRVJTSU9O
LCBQUk9UTykpCiAgICBtZC5hcHBlbmQoIiIpCiAgICBwcmV2ID0gY29udGV4dG8uZ2V0KCJwcmV2
dWVsbyIpCiAgICBpZiBwcmV2OgogICAgICAgICMgdjEuMTogbGEgc2VjY2lvbiAwIGVzIGVsIGRv
c3NpZXIgY29tcGxldG8gUEMgKyBtb2RlbG8gKyBuaXZlbAogICAgICAgIG1kLmV4dGVuZChtZF9w
cmV2dWVsbyhwcmV2WyJwYyJdLCBwcmV2WyJtb2RlbG8iXSwgcHJldlsibml2ZWwiXSwKICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgY29udGV4dG8sIHByb2JsZW1hc19mbGFncykpCiAgICBl
bHNlOgogICAgICAgIG1kLmFwcGVuZCgiIyMgMC4gUHJlLXZ1ZWxvIikKICAgICAgICBtZC5hcHBl
bmQoIiIpCiAgICAgICAgbWQuYXBwZW5kKCItIFNlcnZlcjogYCVzYCIgJSBjb250ZXh0b1sicnV0
YV9zZXJ2ZXIiXSkKICAgICAgICBtZC5hcHBlbmQoIi0gUGluIGRlbCBzZXJ2ZXI6ICVzIiAlIChj
b250ZXh0by5nZXQoInBpbiIpIG9yICJOL0QiKQogICAgICAgICAgICAgICAgICArICgiIiBpZiBC
VUlMRF9QSU5fRVNQRVJBRE8gaW4gKGNvbnRleHRvLmdldCgicGluIikgb3IgIiIpCiAgICAgICAg
ICAgICAgICAgICAgIGVsc2UgIiAgKipPSk86IHNlIGVzcGVyYWJhIGJ1aWxkICVzKioiICUgQlVJ
TERfUElOX0VTUEVSQURPKSkKICAgICAgICBtZC5hcHBlbmQoIi0gTW9kZWxvOiBgJXNgIiAlIGNv
bnRleHRvWyJydXRhX21vZGVsbyJdKQogICAgICAgIGlmIGNvbnRleHRvLmdldCgiYnl0ZXNfbW9k
ZWxvIikgaXMgbm90IE5vbmU6CiAgICAgICAgICAgIG9rX2J5dGVzID0gY29udGV4dG9bImJ5dGVz
X21vZGVsbyJdID09IEJZVEVTX01PREVMT19FU1BFUkFET1MKICAgICAgICAgICAgbWQuYXBwZW5k
KCItIEJ5dGVzIGRlbCBtb2RlbG86ICVzIChlc3BlcmFkb3MgJXMpJXMiCiAgICAgICAgICAgICAg
ICAgICAgICAlIChjb250ZXh0b1siYnl0ZXNfbW9kZWxvIl0sIEJZVEVTX01PREVMT19FU1BFUkFE
T1MsCiAgICAgICAgICAgICAgICAgICAgICAgICAiIiBpZiBva19ieXRlcyBlbHNlICIgICoqTk8g
Q09JTkNJREVOKioiKSkKICAgICAgICBtZC5hcHBlbmQoIi0gQXVkaXRvcmlhIGRlIGZsYWdzOiAl
cyIKICAgICAgICAgICAgICAgICAgJSAoIlZFUkRFIC0gdG9kb3MgbG9zIHRva2VucyB2ZXJiYXRp
bSBlbiBlbCBkdW1wIGIxMTg1NiIKICAgICAgICAgICAgICAgICAgICAgaWYgbm90IHByb2JsZW1h
c19mbGFncyBlbHNlICJGQUxMT1M6ICVzIiAlIHByb2JsZW1hc19mbGFncykpCiAgICAgICAgbWQu
YXBwZW5kKCItIENvbWFuZG8gYmFzZSBwb3IgY29uZmlnIChMQSBSRUNFVEEgRElBUklBICsgLWx2
IDQpOiBgJXNgICIKICAgICAgICAgICAgICAgICAgIigrIGRpZmYgZGUgbGEgY29uZmlnOyBlbCB1
bHRpbW8gdmFsb3IgZ2FuYSkiCiAgICAgICAgICAgICAgICAgICUgKGNvbnRleHRvLmdldCgiYmFz
ZV9mbGFnc19zdHIiKSBvciAiTi9EIikpCiAgICAgICAgbWQuYXBwZW5kKCIiKQogICAgbWQuYXBw
ZW5kKCIjIyAxLiBSZXN1bHRhZG9zIikKICAgIG1kLmFwcGVuZCgiIikKICAgIGFuY2xhX2RlYyA9
IE5vbmUKICAgIGExID0gcmVzdWx0YWRvcy5nZXQoMSkgb3Ige30KICAgIHRyeToKICAgICAgICBh
bmNsYV9kZWMgPSBmbG9hdChhMS5nZXQoImRlY29kZV90cyIpKSBpZiBhMS5nZXQoImRlY29kZV90
cyIpIGVsc2UgTm9uZQogICAgZXhjZXB0IChUeXBlRXJyb3IsIFZhbHVlRXJyb3IpOgogICAgICAg
IGFuY2xhX2RlYyA9IE5vbmUKICAgIG1kLmFwcGVuZCgiQW5jbGEgZGUgc2VzaW9uIChOMy1BTkNM
QSA9IHJlY2V0YSBkaWFyaWEpOiAlcyB0L3MgIgogICAgICAgICAgICAgICIocmVmZXJlbmNpYSBi
YXJyaWRvLTMwIE9STy1VQjFLOiAlLjJmOyBsYSBkZSBIT1kgbWFuZGEpIgogICAgICAgICAgICAg
ICUgKGZtdChhbmNsYV9kZWMpLCBBTkNMQV9VQjFLKSkKICAgIG1kLmFwcGVuZCgiIikKICAgIG1k
LmFwcGVuZCgifCBpZCB8IGNvbmZpZyB8IGZsYWdzIGRpZmYgfCBkZWNvZGUgdC9zIHwgdnMgYW5j
bGEgfCBwcmVmaWxsIHwgIgogICAgICAgICAgICAgICJjYWNoZSB8IFRURlQgKHQyLT50ZmluKSB8
IFJBTSBwcm9jIE1pQiB8IGFnZyB0b2svcyB8IFZSQU0gTWlCIHwgIgogICAgICAgICAgICAgICJz
YW5pdHkgfCB2YWxpZG8gfCIpCiAgICBtZC5hcHBlbmQoInwtLS18LS0tfC0tLXwtLS18LS0tfC0t
LXwtLS18LS0tfC0tLXwtLS18LS0tfC0tLXwtLS18IikKICAgIGZvciBjaWQgaW4gc29ydGVkKHJl
c3VsdGFkb3MpOgogICAgICAgIHIgPSByZXN1bHRhZG9zW2NpZF0KICAgICAgICBkID0gTm9uZQog
ICAgICAgIHRyeToKICAgICAgICAgICAgZCA9IGZsb2F0KHIuZ2V0KCJkZWNvZGVfdHMiKSkgaWYg
ci5nZXQoImRlY29kZV90cyIpIGVsc2UgTm9uZQogICAgICAgIGV4Y2VwdCAoVHlwZUVycm9yLCBW
YWx1ZUVycm9yKToKICAgICAgICAgICAgZCA9IE5vbmUKICAgICAgICBkZWx0YSA9ICgiKyUwLjFm
JSUiICUgKChkIC8gYW5jbGFfZGVjIC0gMSkgKiAxMDApCiAgICAgICAgICAgICAgICAgaWYgKGQg
YW5kIGFuY2xhX2RlYykgZWxzZSAiTi9EIikKICAgICAgICBmbGFnc19jb3J0b3MgPSAoci5nZXQo
ImZsYWdzIikgb3IgIiIpLnJlcGxhY2UoCiAgICAgICAgICAgIGNvbnRleHRvLmdldCgiYmFzZV9m
bGFnc19zdHIiLCAiIiksICIiKS5zdHJpcCgpCiAgICAgICAgdHRmdCA9ICItIgogICAgICAgIGlm
IHIuZ2V0KCJ0dGZ0X3QyIikgb3Igci5nZXQoInR0ZnRfdGZpbiIpOgogICAgICAgICAgICB0dGZ0
ID0gIiVzIC0+ICVzIHMgKCVzKSIgJSAoZm10KHIuZ2V0KCJ0dGZ0X3QyIiksIDIpLAogICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZm10KHIuZ2V0KCJ0dGZ0X3RmaW4iKSwg
MiksCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICByLmdldCgidHRmdF92
ZXJlZGljdG8iKSBvciAiTi9EIikKICAgICAgICBva24gPSByLmdldCgic2FuaXR5X29rX24iKSBv
ciAiLSIKICAgICAgICB0cm4gPSByLmdldCgic2FuaXR5X3RydW5jX24iKSBvciAiIgogICAgICAg
IHNhbl90eHQgPSAoIiVzKyVzVC8lcyIgJSAob2tuLCB0cm4sIHIuZ2V0KCJzYW5pdHlfdG90YWwi
KSBvciAiLSIpCiAgICAgICAgICAgICAgICAgICBpZiB0cm4gbm90IGluICgiIiwgIjAiKSBlbHNl
CiAgICAgICAgICAgICAgICAgICAiJXMvJXMiICUgKG9rbiwgci5nZXQoInNhbml0eV90b3RhbCIp
IG9yICItIikpCiAgICAgICAgbWQuYXBwZW5kKCJ8ICVzIHwgJXMgfCBgJXNgIHwgJXMgfCAlcyB8
ICVzIHwgJXMgfCAlcyB8ICVzIHwgJXMgfCAlcy8lcyB8ICIKICAgICAgICAgICAgICAgICAgIiVz
IHwgJXMgfCIKICAgICAgICAgICAgICAgICAgJSAoY2lkLCByLmdldCgibm9tYnJlIiksIGZsYWdz
X2NvcnRvcyBvciAiQkFTRSIsCiAgICAgICAgICAgICAgICAgICAgIGZtdChkKSwgZGVsdGEsIGZt
dChyLmdldCgicHJlZmlsbF90cyIpLCAwKSwKICAgICAgICAgICAgICAgICAgICAgci5nZXQoImNh
Y2hlX2VzdGFkbyIpIG9yICItIiwgdHRmdCwKICAgICAgICAgICAgICAgICAgICAgci5nZXQoInJh
bV9wcm9jX21pYiIpIG9yICJOL0QiLAogICAgICAgICAgICAgICAgICAgICByLmdldCgiYWdnX3Rz
Iikgb3IgIk4vRCIsCiAgICAgICAgICAgICAgICAgICAgIHIuZ2V0KCJ2cmFtX3VzYWRhX21pYiIp
IG9yICJOL0QiLAogICAgICAgICAgICAgICAgICAgICByLmdldCgidnJhbV90b3RhbF9taWIiKSBv
ciAiTi9EIiwKICAgICAgICAgICAgICAgICAgICAgc2FuX3R4dCwgci5nZXQoInZhbGlkbyIpIG9y
ICIiKSkKICAgIG1kLmFwcGVuZCgiIikKICAgIG1kLmFwcGVuZCgiUmVmZXJlbmNpYXMgaGlzdG9y
aWNhcyBkZWwgYmFycmlkby0zMCBbTV06IE9STy1VQjFLIChhbmNsYSBkZSAiCiAgICAgICAgICAg
ICAgImxhIHJlY2V0YSBkaWFyaWEpID0gJS4yZiB0L3MgLSBOQ00zN0M0IChzaW4gVUIxSykgPSAl
LjJmIC0gIgogICAgICAgICAgICAgICJPUk8tQ1JBTTUxMiA9ICUuMmYgKGRlY29kZSBpbnRhY3Rv
LCAtNy43IEdCKSAtIE9STy1TSElGVCAiCiAgICAgICAgICAgICAgIihzaGlmdCtyZXVzZSkgPSAl
LjJmLiBSdWlkbyBkZWNsYXJhZG8gKy8tMC4zLTAuNSB0L3M7IGVsICIKICAgICAgICAgICAgICAi
bWlzbW8gY29uZmlnIGFiYXJjYSA5LjRwcCBlbnRyZSBjb3JyaWRhcyAodGhjMTAwNiB2NCk6ICIK
ICAgICAgICAgICAgICAibWVkaWFuYSBkZSAzIGFudGVzIGRlIHByb2NsYW1hciBnYW5hbmNpYXMu
IgogICAgICAgICAgICAgICUgKEFOQ0xBX1VCMUssIE5DTTM3QzRfUkVGLCBDUkFNNTEyX1JFRiwg
U0hJRlRfUkVGKSkKICAgIG1kLmFwcGVuZCgiIikKICAgIG1kLmFwcGVuZCgiIyMgMi4gQ2VydGlm
aWNhZG9zIGRlIGNhY2hlIChsaW5lYXMgZGUgbG9nICsgcmVwcm8pIikKICAgIG1kLmFwcGVuZCgi
IikKICAgIG1kLmFwcGVuZCgifCBpZCB8IGNvbmZpZyB8IHdhcm5pbmcgIzI0MDU1IHwgcmVzdG9y
ZWQgfCBmb3JjaW5nICMyMTgzMSB8ICIKICAgICAgICAgICAgICAiZXN0YWRvIHwiKQogICAgbWQu
YXBwZW5kKCJ8LS0tfC0tLXwtLS18LS0tfC0tLXwtLS18IikKICAgIGZvciBjaWQgaW4gc29ydGVk
KHJlc3VsdGFkb3MpOgogICAgICAgIHIgPSByZXN1bHRhZG9zW2NpZF0KICAgICAgICBtZC5hcHBl
bmQoInwgJXMgfCAlcyB8ICVzIHwgJXMgfCAlcyB8ICVzIHwiCiAgICAgICAgICAgICAgICAgICUg
KGNpZCwgci5nZXQoIm5vbWJyZSIpLAogICAgICAgICAgICAgICAgICAgICByLmdldCgiY2FjaGVf
cmV1c2Vfd2FybiIpIG9yICItIiwKICAgICAgICAgICAgICAgICAgICAgci5nZXQoImNhY2hlX3Jl
c3RvcmVkX24iKSBvciAiLSIsCiAgICAgICAgICAgICAgICAgICAgIHIuZ2V0KCJjYWNoZV9mb3Jj
aW5nX24iKSBvciAiLSIsCiAgICAgICAgICAgICAgICAgICAgIHIuZ2V0KCJjYWNoZV9lc3RhZG8i
KSBvciAiLSIpKQogICAgbWQuYXBwZW5kKCIiKQogICAgbWQuYXBwZW5kKCJMZWN0dXJhOiBOTy1B
UExJQ0EgPSBsYSBjb25maWcgbm8gbGxldmEgLS1jYWNoZS1yZXVzZSDCtyAiCiAgICAgICAgICAg
ICAgIk5PLVNPUE9SVEFETyA9IGVsIGJ1aWxkIGRlY2xpbm8gbGEgY2FjaGUgZW4gZWwgYXJyYW5x
dWUgIgogICAgICAgICAgICAgICIoIzI0MDU1KSDCtyBTQU5PID0gY2hlY2twb2ludHMgcmVzdGF1
cmFkb3MgeSBjZXJvIHJlLXByb2Nlc2FkbyAiCiAgICAgICAgICAgICAgIsK3IFJPVE8gPSAnZm9y
Y2luZyBmdWxsIHByb21wdCByZS1wcm9jZXNzaW5nJyAoIzIxODMxLCBlbCAiCiAgICAgICAgICAg
ICAgImhpYnJpZG8gcmUtcGFnYSBlbCBwcm9tcHQpIMK3IE1JWFRPL1NJTi1EQVRPUyA9IGxlZXIg
ZWwgSlNPTi4iKQogICAgbWQuYXBwZW5kKCIiKQogICAgbWQuYXBwZW5kKCIjIyAzLiBQcm90b2Nv
bG8gZGUgZGVjaXNpb24gTjMgKGV2YWx1YWNpb24gYXV0b21hdGljYSkiKQogICAgbWQuYXBwZW5k
KCIiKQogICAgbWQuZXh0ZW5kKHByb3RvY29sb19kZWNpc2lvbihyZXN1bHRhZG9zLCBhbmNsYV9k
ZWMpIG9yCiAgICAgICAgICAgICAgWyItIChzaW4gZGF0b3Mgc3VmaWNpZW50ZXMpIl0pCiAgICBt
ZC5hcHBlbmQoIiIpCiAgICBtZC5hcHBlbmQoIiMjIDQuIFJlY3VlcmRvcyBkZSBsYSBjYXNhIGFw
bGljYWRvcyIpCiAgICBtZC5hcHBlbmQoIiIpCiAgICBtZC5hcHBlbmQoIi0gUHJvdG9jb2xvIFNT
OCB2ZXJiYXRpbTogNCBwYXNhZGFzIHggMjU2IHRva2Vucywgc2UgZGVzY2FydGEgIgogICAgICAg
ICAgICAgICJsYSAxYSwgdGVtcCAwLCBwcm9tcHRzIGRpc3RpbnRvcywgc2VlZCBmaWphOyBydWlk
byBkZWNsYXJhZG8gIgogICAgICAgICAgICAgICIrLy0wLjMtMC41IHQvcy4iKQogICAgbWQuYXBw
ZW5kKCItIEVzdHVkaW8gdGhjMTAwNiB2NCAoU1MxMyk6IGVsIG1pc21vIGNvbmZpZyBhYmFyY2Eg
OS40IHBwICIKICAgICAgICAgICAgICAiZW50cmUgY29ycmlkYXMgLT4gbGFzIGNlbGRhcyBxdWUg
R0FORU4gYXF1aSBzZSBjb25maXJtYW4gY29uICIKICAgICAgICAgICAgICAibWVkaWFuYSBkZSAz
IGNvcnJpZGFzIChvIC0tcXVpY2sgZW4gb3RybyBibG9xdWUgaG9yYXJpbykgIgogICAgICAgICAg
ICAgICJBTlRFUyBkZSBwcm9jbGFtYXIgbGEgZ2FuYW5jaWE7IG51bmNhIGNvbXBhcmFyIGNvbnRy
YSBlbCAiCiAgICAgICAgICAgICAgImFuY2xhIGRlIE9UUkEgc2VzaW9uLiIpCiAgICBtZC5hcHBl
bmQoIi0gRWwgbGlicm8gZGUgbXVlcnRvcyBkZWwgTjMgTk8gc2UgcmUtbWlkZTogbmdyYW0gc3Bl
YyAiCiAgICAgICAgICAgICAgIihhY2NlcHRhbmNlIDAuMDAtMC4xNiksIGFmaW5pZGFkICgtOS4u
LTM4JSksIEZJVC1DICgtMzglKSwgIgogICAgICAgICAgICAgICJyZXBhY2sgb2ZmICgtNSUpLCBL
ViBxNV8xICgwJSksIFBPTEwvVEI4IChydWlkby9tdWVydG8pLiIpCiAgICBtZC5hcHBlbmQoIi0g
U2FuaXR5IG1hbnVhbCBkZSAyMCBwcm9tcHRzIGRlbCBEaXJlY3Rvcjogc2lndWUgc2llbmRvIGxh
ICIKICAgICAgICAgICAgICAicHVlcnRhIGRlIGNhbGlkYWQgY29tcGxldGEgKGxhIGF1dG8gZGUg
MyBwYXJlcyBzb2xvIGVzICIKICAgICAgICAgICAgICAiaHVtby1kZXRlY3RvcikuIikKICAgIG1k
LmFwcGVuZCgiLSBQUk9NT0NJT046IGxhcyBjYW5kaWRhdGFzIGEgY29uZmlnLnR4dCBxdWUgc2Fs
Z2FuIGFxdWkgc2UgIgogICAgICAgICAgICAgICJwcm9tdWV2ZW4gZWRpdGFuZG8gVU5BIGxpbmVh
IGRlIEZMQUdTX0JBU0UgKHBhZ28gZGVsIGNvbmZpZyAiCiAgICAgICAgICAgICAgImNlbnRyYWws
IHJvbmRhIDIwKTsgbGEgYXByb2JhY2lvbiBmb3JtYWwgZXMgZGVsIERpcmVjdG9yLiIpCiAgICBt
ZC5hcHBlbmQoIi0gU2kgbGEgY2FjaGUgc2FsZSBOTy1TT1BPUlRBRE8gbyBST1RPIGVuIGIxMTg1
NjogcXVlZGEgIgogICAgICAgICAgICAgICJyZWdpc3RyYWRvIGNvbW8gTU9USVZPIERFIFJVVEEg
MCAoYnVpbGQgbnVldm8gY29uIGNwZW50IC8gIgogICAgICAgICAgICAgICJmaXggZGVsIGNoZWNr
cG9pbnQpLCBubyBjb21vIGZyYWNhc28gZGUgbGEgaWRlYS4iKQogICAgbWQuYXBwZW5kKCIiKQog
ICAgbWQuYXBwZW5kKCIjIyA1LiBBcmNoaXZvcyBkZSBlc3RhIGNvcnJpZGEiKQogICAgbWQuYXBw
ZW5kKCIiKQogICAgbWQuYXBwZW5kKCItIENTVjogYGZhc2VOMy1yZXN1bHRhZG9zLmNzdmAgKHJl
YW51ZGFibGUpIikKICAgIG1kLmFwcGVuZCgiLSBEYXRvczogYGZhc2VOMy1kYXRvcy5qc29uYCAo
cmVwcm8gVFRGVCB0dXJubyBhIHR1cm5vLCAiCiAgICAgICAgICAgICAgInNhbml0eSwgcHJvYmUg
YWdyZWdhZG8sIFJBTSkiKQogICAgbWQuYXBwZW5kKCItIENvbnNvbGE6IGBmYXNlTjMtY29uc29s
YS5sb2dgIikKICAgIG1kLmFwcGVuZCgiLSBMb2dzIGRlbCBzZXJ2ZXI6IGBsb2dzLWNvbmZpZy9O
Ti1ub21icmUubG9nYCIpCiAgICBtZC5hcHBlbmQoIiIpCiAgICBydXRhX21kID0gb3MucGF0aC5q
b2luKGRpcl9sb2dzLCAiZmFzZU4zLUlORk9STUUubWQiKQogICAgb3BlbihydXRhX21kLCAidyIs
IGVuY29kaW5nPSJ1dGYtOCIpLndyaXRlKCJcbiIuam9pbihtZCkgKyAiXG4iKQoKICAgIGRhdG9z
X2pzb24gPSB7InZlcnNpb24iOiBWRVJTSU9OLCAicHJvdG8iOiBQUk9UTywgImZlY2hhIjogYWhv
cmEoKSwKICAgICAgICAgICAgICAgICAgImNvbnRleHRvIjoge2s6IHYgZm9yIGssIHYgaW4gY29u
dGV4dG8uaXRlbXMoKQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgaWYgayBub3QgaW4g
KCJ0ZWUiLCl9LAogICAgICAgICAgICAgICAgICAicnVucyI6IGxpc3QoY29tcGxldG9zLnZhbHVl
cygpKX0KICAgIG9wZW4ob3MucGF0aC5qb2luKGRpcl9sb2dzLCAiZmFzZU4zLWRhdG9zLmpzb24i
KSwgInciLAogICAgICAgICBlbmNvZGluZz0idXRmLTgiKS53cml0ZShqc29uLmR1bXBzKGRhdG9z
X2pzb24sIGVuc3VyZV9hc2NpaT1GYWxzZSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICBpbmRlbnQ9MSwgZGVmYXVsdD1zdHIpKQogICAgcmV0dXJuIHJ1dGFfbWQK
CgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0gbWFpbiAtLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0KZGVmIG1haW4oYXJndj1Ob25lKToKICAgIGdsb2JhbCBQ
VUVSVE9fREVGCiAgICBhcCA9IGFyZ3BhcnNlLkFyZ3VtZW50UGFyc2VyKAogICAgICAgIGRlc2Ny
aXB0aW9uPVZFUlNJT04gKyAiIOKAlCBjb3NlY2hhIGRlbCBuaXZlbCAzIChlZmljaWVuY2lhIHNp
bXBsZSkiKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXF1aWNrIiwgYWN0aW9uPSJzdG9yZV90cnVl
IiwKICAgICAgICAgICAgICAgICAgICBoZWxwPSJzb2xvIDUgY29uZmlncyBjcml0aWNhcyAofjE4
IG1pbikiKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXNvbG8iLCB0eXBlPXN0ciwgZGVmYXVsdD0i
IiwKICAgICAgICAgICAgICAgICAgICBoZWxwPSJibG9xdWVzIHNlcGFyYWRvcyBwb3IgY29tYTog
IgogICAgICAgICAgICAgICAgICAgICAgICAgImFuY2xhLHJhbSxjYWNoZSxzbG90cyxuY20sY29t
Ym8sY3RybCxhbmNsYWZpbiIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tc2VydmVyIiwgdHlwZT1z
dHIsIGRlZmF1bHQ9UlVUQV9TRVJWRVJfREVGKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLW1vZGVs
byIsIHR5cGU9c3RyLCBkZWZhdWx0PVJVVEFfTU9ERUxPX0RFRikKICAgIGFwLmFkZF9hcmd1bWVu
dCgiLS1sb2dzIiwgdHlwZT1zdHIsIGRlZmF1bHQ9TE9HU19ESVJfREVGKQogICAgYXAuYWRkX2Fy
Z3VtZW50KCItLXB1ZXJ0byIsIHR5cGU9aW50LCBkZWZhdWx0PVBVRVJUT19ERUYpCiAgICBhcC5h
ZGRfYXJndW1lbnQoIi0tY2FyZ2EtdGltZW91dCIsIHR5cGU9aW50LCBkZWZhdWx0PTYwMCkKICAg
IGFwLmFkZF9hcmd1bWVudCgiLS1zaSIsIGFjdGlvbj0ic3RvcmVfdHJ1ZSIsCiAgICAgICAgICAg
ICAgICAgICAgaGVscD0ibWF0YXIgdW4gc2VydmVyIHZpdm8gYW50ZXMgZGUgZW1wZXphciIpCiAg
ICBhcC5hZGRfYXJndW1lbnQoIi0tc2luLXR0ZnQiLCBhY3Rpb249InN0b3JlX3RydWUiLAogICAg
ICAgICAgICAgICAgICAgIGhlbHA9InNhbHRhciBlbCByZXBybyBkZSB0dXJub3MgY3JlY2llbnRl
cyIpCiAgICBhcC5hZGRfYXJndW1lbnQoIi0tc2luLXByb2JlIiwgYWN0aW9uPSJzdG9yZV90cnVl
IiwKICAgICAgICAgICAgICAgICAgICBoZWxwPSJzYWx0YXIgZWwgcHJvYmUgZGUgY29uY3VycmVu
Y2lhIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1zaW4tc2FuaXR5IiwgYWN0aW9uPSJzdG9yZV90
cnVlIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1zaW4tbnZpZGlhIiwgYWN0aW9uPSJzdG9yZV90
cnVlIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1zaW4tcGF1c2FzIiwgYWN0aW9uPSJzdG9yZV90
cnVlIikKICAgIGFwLmFkZF9hcmd1bWVudCgiLS1zaW4tcHJldnVlbG8iLCBhY3Rpb249InN0b3Jl
X3RydWUiLAogICAgICAgICAgICAgICAgICAgIGhlbHA9Im9taXRpciBlbCBkb3NzaWVyIGNvbXBs
ZXRvIFBDL21vZGVsby9uaXZlbCAodjEuMCkiKQogICAgYXAuYWRkX2FyZ3VtZW50KCItLXNpbi1z
aGEyNTYiLCBhY3Rpb249InN0b3JlX3RydWUiLAogICAgICAgICAgICAgICAgICAgIGhlbHA9InBy
ZXZ1ZWxvIHNpbiBlbCBoYXNoIGRlbCBtb2RlbG8gKH4xIG1pbiBhaG9ycm8pIikKICAgIGFyZ3Mg
PSBhcC5wYXJzZV9hcmdzKGFyZ3YpCgogICAgUFVFUlRPX0RFRiA9IGFyZ3MucHVlcnRvCiAgICAj
IGVsIGNvbWFuZG8gbGFuemFkbyBlcyBTSUVNUFJFIGJhc2UgKyBkaWZmIChlbCB1bHRpbW8gdmFs
b3IgZ2FuYSk7CiAgICAjIGxhIGJhc2UgPSBMQSBSRUNFVEEgRElBUklBIChjb25maWcudHh0IEZM
QUdTX0JBU0UgKyBGTEFHU19HQU5BRE9SQVMsCiAgICAjIGF1ZGl0b3JpYSBSMjQpICsgLWx2IDQg
cGFyYSBsb3MgY2VydGlmaWNhZG9zIGRlbCBsb2cuCiAgICBiYXNlX2ZsYWdzID0gWyItbSIsIGFy
Z3MubW9kZWxvXSArIGxpc3QoQkFTRV9GTEFHU19GSUpBUykKICAgIGZvciBpLCB0b2sgaW4gZW51
bWVyYXRlKGJhc2VfZmxhZ3MpOgogICAgICAgIGlmIHRvayA9PSAiLS1wb3J0IiBhbmQgaSArIDEg
PCBsZW4oYmFzZV9mbGFncyk6CiAgICAgICAgICAgIGJhc2VfZmxhZ3NbaSArIDFdID0gc3RyKGFy
Z3MucHVlcnRvKQoKICAgIHRyeToKICAgICAgICBzeXMuc3Rkb3V0LnJlY29uZmlndXJlKGVuY29k
aW5nPSJ1dGYtOCIsIGVycm9ycz0icmVwbGFjZSIpCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAg
ICAgIHBhc3MKICAgIGlmIG9zLm5hbWUgPT0gIm50IjoKICAgICAgICB0cnk6CiAgICAgICAgICAg
IG9zLnN5c3RlbSgiIikgICMgaGFiaWxpdGEgY29kaWdvcyBWVC9BTlNJIGVuIGxhIGNvbnNvbGEg
V2luZG93cwogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgIHBhc3MKCiAgICBv
cy5tYWtlZGlycyhhcmdzLmxvZ3MsIGV4aXN0X29rPVRydWUpCiAgICBvcy5tYWtlZGlycyhvcy5w
YXRoLmpvaW4oYXJncy5sb2dzLCAibG9ncy1jb25maWciKSwgZXhpc3Rfb2s9VHJ1ZSkKICAgIHRl
ZSA9IFRlZShvcy5wYXRoLmpvaW4oYXJncy5sb2dzLCAiZmFzZU4zLWNvbnNvbGEubG9nIikpCiAg
ICBzeXMuc3Rkb3V0ID0gdGVlCiAgICBzeXMuc3RkZXJyID0gdGVlCgogICAgcHJpbnQoZ3JheSgi
PSIgKiA3OCkpCiAgICBwcmludChib2xkKFZFUlNJT04pKQogICAgcHJpbnQoZ3JheSgiPSIgKiA3
OCkpCiAgICBwcmludCgiICBzZXJ2ZXIgOiAlcyIgJSBhcmdzLnNlcnZlcikKICAgIHByaW50KCIg
IG1vZGVsbyA6ICVzIiAlIGFyZ3MubW9kZWxvKQogICAgcHJpbnQoIiAgbG9ncyAgIDogJXMiICUg
YXJncy5sb2dzKQogICAgcHJpbnQoIiAgcHVlcnRvIDogJWQiICUgYXJncy5wdWVydG8pCgogICAg
IyAtLS0tIDAuIHByZS12dWVsbyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0KICAgIGlmIG5vdCBvcy5wYXRoLmV4aXN0cyhhcmdzLnNlcnZlcik6
CiAgICAgICAgcmFpc2UgU3lzdGVtRXhpdChyZWQoIkZBVEFMOiBubyBleGlzdGUgZWwgc2VydmVy
OiAlcyIgJSBhcmdzLnNlcnZlcikpCiAgICBpZiBub3Qgb3MucGF0aC5leGlzdHMoYXJncy5tb2Rl
bG8pOgogICAgICAgIHJhaXNlIFN5c3RlbUV4aXQocmVkKCJGQVRBTDogbm8gZXhpc3RlIGVsIG1v
ZGVsbzogJXMiICUgYXJncy5tb2RlbG8pKQogICAgaWYgbm90IG9zLnBhdGguZXhpc3RzKFJVVEFf
RFVNUF9ERUYpOgogICAgICAgIHJhaXNlIFN5c3RlbUV4aXQocmVkKCJGQVRBTDogbm8gZXhpc3Rl
IGVsIGR1bXAgZGUgZmxhZ3M6ICVzIChlbCBzY3JpcHQgIgogICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICJOTyBhcnJhbmNhIHNpbiBzdSBmdWVudGUgZGUgdmVyZGFkKSIgJSBSVVRBX0RVTVBf
REVGKSkKCiAgICBieXRlc19tb2RlbG8gPSBvcy5wYXRoLmdldHNpemUoYXJncy5tb2RlbG8pCiAg
ICBpZiBieXRlc19tb2RlbG8gIT0gQllURVNfTU9ERUxPX0VTUEVSQURPUzoKICAgICAgICBwcmlu
dCh5ZWxsb3coIiAgQVZJU086IGVsIG1vZGVsbyBtaWRlICVkIEIgeSBSdXRhc0FyY2hpdm9zIGRp
Y2UgJWQgQiAiCiAgICAgICAgICAgICAgICAgICAgICItPiB2ZXJpZmljYXIgcXVlIGVzIGVsIEFQ
RVgtSS1NSU5JIGNvcnJlY3RvIgogICAgICAgICAgICAgICAgICAgICAlIChieXRlc19tb2RlbG8s
IEJZVEVTX01PREVMT19FU1BFUkFET1MpKSkKCiAgICBwaW4gPSB2ZXJzaW9uX3NlcnZlcihhcmdz
LnNlcnZlcikKICAgIGlmIEJVSUxEX1BJTl9FU1BFUkFETyBub3QgaW4gcGluOgogICAgICAgIHBy
aW50KHllbGxvdygiICBBVklTTzogZWwgcGluIGRlbCBzZXJ2ZXIgbm8gbWVuY2lvbmEgYnVpbGQg
JXM6ICVzIgogICAgICAgICAgICAgICAgICAgICAlIChCVUlMRF9QSU5fRVNQRVJBRE8sIHBpbls6
MTIwXSkpKQoKICAgIGNvbmZpZ3MgPSBmaWx0cmFyX2NvbmZpZ3MoY29uc3RydWlyX2NvbmZpZ3Mo
KSwgc29sbz1hcmdzLnNvbG8sCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHF1aWNrPWFy
Z3MucXVpY2spCgogICAgcHJpbnQoY3lhbigiWzBdIEFVRElUT1JJQSBERSBGTEFHUyBjb250cmEg
ZWwgZHVtcCBiMTE4NTYuLi4iKSkKICAgIHByb2JsZW1hcyA9IGF1ZGl0YXJfZmxhZ3MoUlVUQV9E
VU1QX0RFRiwgY29uZmlncywgYmFzZV9mbGFncykKICAgIGlmIHByb2JsZW1hczoKICAgICAgICBm
b3IgcCBpbiBwcm9ibGVtYXM6CiAgICAgICAgICAgIHByaW50KHJlZCgiICBGQUxMTzogJXMiICUg
cCkpCiAgICAgICAgcmFpc2UgU3lzdGVtRXhpdChyZWQoIkZBVEFMOiBsYSBhdWRpdG9yaWEgZGUg
ZmxhZ3MgZmFsbG8gKCVkKS4gTmFkYSBzZSAiCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ImVqZWN1dGE6IHJldmlzYXIgY29uZmlncyBvIHJlZ2VuZXJhciBlbCBkdW1wLiIKICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAlIGxlbihwcm9ibGVtYXMpKSkKICAgIHByaW50KGdyZWVuKCIg
IFZFUkRFOiAlZCBjb25maWdzLCB0b2RvcyBsb3MgdG9rZW5zIHZlcmJhdGltIGVuIGVsIGR1bXAs
ICIKICAgICAgICAgICAgICAgICJjZXJvIHByb2hpYmlkYXMiICUgbGVuKGNvbmZpZ3MpKSkKCiAg
ICAjIC0tLS0gY2VydGlmaWNhZG8gZGUgcmVjZXRhICsgY29sb2NhY2lvbiAodjEuMywgaG90Zml4
IGRlIGNhbXBvKSAtLS0tLS0tCiAgICAjIGVsIGNhbXBvIDI4LW9jdCBwYXNvIGxhIGF1ZGl0b3Jp
YSBWRVJERSB5IGF1biBhc2kgbXVyaW8gMTEgY29uZmlnczogbGEKICAgICMgYXVkaXRvcmlhIHZl
IFRPS0VOUyBlbiBlbCBkdW1wLCBubyBsYSBSRUNFVEEgQ09NUExFVEEgZGVsIGNvbWFuZG8uCiAg
ICBhbmNsYV9yZWYgPSBuZXh0KChjIGZvciBjIGluIGNvbnN0cnVpcl9jb25maWdzKCkgaWYgY1si
aWQiXSA9PSAxKSwgTm9uZSkKICAgIGlmIGFuY2xhX3JlZiBpcyBub3QgTm9uZToKICAgICAgICBm
YWx0YW4gPSB2ZXJpZmljYXJfcmVjZXRhKGxpc3QoYmFzZV9mbGFncykgKyBsaXN0KGFuY2xhX3Jl
ZlsiZmxhZ3MiXSkpCiAgICAgICAgaWYgZmFsdGFuOgogICAgICAgICAgICByYWlzZSBTeXN0ZW1F
eGl0KHJlZCgKICAgICAgICAgICAgICAgICJGQVRBTDogbGEgcmVjZXRhIGJhc2UgTk8gZXMgbGEg
ZGlhcmlhIGNlcnRpZmljYWRhOiBmYWx0YW4gIgogICAgICAgICAgICAgICAgIiVzIChjb25maWcu
dHh0IEZMQUdTX0JBU0UgKyBGTEFHU19HQU5BRE9SQVMpLiBTaW4gbGEgcmVjZXRhICIKICAgICAg
ICAgICAgICAgICJkaWFyaWEgZWwgYW5jbGEgbm8gZXMgZWwgYW5jbGE6IG5hZGEgc2UgbWlkZS4i
CiAgICAgICAgICAgICAgICAlICIsICIuam9pbihmYWx0YW4pKSkKICAgICAgICBwcmludChncmVl
bigiICBWRVJERTogcmVjZXRhIGRpYXJpYSBjZXJ0aWZpY2FkYSBlbiBlbCBhbmNsYSAiCiAgICAg
ICAgICAgICAgICAgICAgIihpbmNsdWlkYSBsYSBjb2xvY2FjaW9uIC1jbW9lKSIpKQogICAgc2lu
X2NvbG9jID0gdmVyaWZpY2FyX2NvbG9jYWNpb24oY29uZmlncywgYmFzZV9mbGFncykKICAgIGlm
IHNpbl9jb2xvYzoKICAgICAgICByYWlzZSBTeXN0ZW1FeGl0KHJlZCgKICAgICAgICAgICAgIkZB
VEFMOiBjb25maWdzIFNJTiBjb2xvY2FjaW9uICgtY21vZS8tbmNtb2UpOiAlcyAobGVjY2lvbiAi
CiAgICAgICAgICAgICJiYXJyaWRvLTMwOiBzaW4gY29sb2NhY2lvbiBlbCBtb2RlbG8gZGUgMTQu
MjcgR0Igbm8gY2FiZSBlbiBsYSAiCiAgICAgICAgICAgICJHUFUgZGUgNCBHQiB5IGVsIHNlcnZl
ciBtdWVyZSBlbiBsYSBjYXJnYSkiCiAgICAgICAgICAgICUgIiwgIi5qb2luKHNpbl9jb2xvYykp
KQogICAgcHJpbnQoZ3JlZW4oIiAgVkVSREU6IGNvbG9jYWNpb24gcG9yIGNvbmZpZyBlbiAlZC8l
ZCBjb25maWdzIgogICAgICAgICAgICAgICAgJSAobGVuKGNvbmZpZ3MpIC0gbGVuKHNpbl9jb2xv
YyksIGxlbihjb25maWdzKSkpKQoKICAgIGlmIGFyZ3Muc2k6CiAgICAgICAgbWF0YXJfc2VydmVy
X3Zpdm8oYXJncy5wdWVydG8pCiAgICBlbGlmIGhlYWx0aF9vayhhcmdzLnB1ZXJ0byk6CiAgICAg
ICAgcmFpc2UgU3lzdGVtRXhpdChyZWQoIkZBVEFMOiAvaGVhbHRoIHlhIHJlc3BvbmRlIGVuIGVs
IHB1ZXJ0byAlZC4gSGF5ICIKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAidW4gc2VydmVy
IHZpdm8gKG1lZGlyIGNvbiBlbCBmYWxzZWEgdG9kbykuICIKICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAiQ2VycmFybG8gbyByZWxhbnphciBjb24gLS1zaS4iICUgYXJncy5wdWVydG8pKQoK
ICAgICMgLS0tLSAwLjUgcHJldnVlbG8gY29tcGxldG8gKFBDICsgbW9kZWxvICsgbml2ZWwpIC0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tCiAgICBwcmV2dWVsbyA9IE5vbmUKICAgIGlmIG5vdCBhcmdz
LnNpbl9wcmV2dWVsbzoKICAgICAgICBwcmludChjeWFuKCJbMC41XSBQUkVWVUVMTyBDT01QTEVU
TzogUEMgKyBtb2RlbG8gKyBuaXZlbCAiCiAgICAgICAgICAgICAgICAgICAiKH4xLTIgbWluIHBv
ciBlbCBzaGEyNTYgZGVsIG1vZGVsbzsgLS1zaW4tc2hhMjU2IGxvIHNhbHRhKSIpKQogICAgICAg
IHBjX2QgPSBkb3NzaWVyX3BjKGNvbl9udmlkaWE9bm90IGFyZ3Muc2luX252aWRpYSkKICAgICAg
ICBtb2RfZCA9IGRvc3NpZXJfbW9kZWxvKGFyZ3MubW9kZWxvLCBieXRlc19tb2RlbG8sIHBpbiwK
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNvbl9zaGE9bm90IGFyZ3Muc2luX3NoYTI1
Niwgbm90aWZpY2Fkb3I9cHJpbnQpCiAgICAgICAgbml2X2QgPSBkb3NzaWVyX25pdmVsKGNvbmZp
Z3MpCiAgICAgICAgcHJldnVlbG8gPSB7InBjIjogcGNfZCwgIm1vZGVsbyI6IG1vZF9kLCAibml2
ZWwiOiBuaXZfZH0KICAgICAgICBpbXByaW1pcl9wcmV2dWVsbyhwY19kLCBtb2RfZCwgbml2X2Qp
CiAgICBlbHNlOgogICAgICAgIHByaW50KGdyYXkoIiAgLS1zaW4tcHJldnVlbG86IGRvc3NpZXIg
b21pdGlkbyAoY29tcG9ydGFtaWVudG8gdjEuMCkiKSkKCiAgICBjb250ZXh0byA9IHsicnV0YV9z
ZXJ2ZXIiOiBhcmdzLnNlcnZlciwgInJ1dGFfbW9kZWxvIjogYXJncy5tb2RlbG8sCiAgICAgICAg
ICAgICAgICAiZGlyX2xvZ3MiOiBhcmdzLmxvZ3MsICJwaW4iOiBwaW4sCiAgICAgICAgICAgICAg
ICAiYnl0ZXNfbW9kZWxvIjogYnl0ZXNfbW9kZWxvLAogICAgICAgICAgICAgICAgImNhcmdhX3Rp
bWVvdXQiOiBhcmdzLmNhcmdhX3RpbWVvdXQsCiAgICAgICAgICAgICAgICAiY29uX3Nhbml0eSI6
IG5vdCBhcmdzLnNpbl9zYW5pdHksCiAgICAgICAgICAgICAgICAic2luX252aWRpYSI6IGFyZ3Mu
c2luX252aWRpYSwKICAgICAgICAgICAgICAgICJzaW5fdHRmdCI6IGFyZ3Muc2luX3R0ZnQsCiAg
ICAgICAgICAgICAgICAic2luX3Byb2JlIjogYXJncy5zaW5fcHJvYmUsCiAgICAgICAgICAgICAg
ICAicHVlcnRvIjogYXJncy5wdWVydG8sCiAgICAgICAgICAgICAgICAiYmFzZV9mbGFnc19zdHIi
OiAiICIuam9pbihiYXNlX2ZsYWdzKSwKICAgICAgICAgICAgICAgICJiYXNlX2ZsYWdzIjogYmFz
ZV9mbGFncywKICAgICAgICAgICAgICAgICJwcmV2dWVsbyI6IHByZXZ1ZWxvfQoKICAgICMgLS0t
LSAxLiBjb3JyaWRhIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tCiAgICBwcmludChjeWFuKCJbMV0gQ09SUklEQTogJWQgY29uZmlncyAocGF1
c2EgdGVybWljYSAlZCBzIGNhZGEgJWQpIgogICAgICAgICAgICAgICAlIChsZW4oY29uZmlncyks
IFBBVVNBX1RFUk1JQ0FfUywgUEFVU0FfQ0FEQSkpKQogICAgcnV0YV9jc3YgPSBjc3ZfcnV0YShh
cmdzLmxvZ3MpCiAgICBwcm90b192aWVqbyA9IGNzdl9wcm90b19kZShydXRhX2NzdikKICAgIGlm
IHByb3RvX3ZpZWpvIGFuZCBwcm90b192aWVqbyAhPSBQUk9UTzoKICAgICAgICBkZXN0aW5vID0g
b3MucGF0aC5qb2luKGFyZ3MubG9ncywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICJm
YXNlTjMtcmVzdWx0YWRvcy0lcy5jc3YiICUgcHJvdG9fdmllam8pCiAgICAgICAgdHJ5OgogICAg
ICAgICAgICBvcy5yZXBsYWNlKHJ1dGFfY3N2LCBkZXN0aW5vKQogICAgICAgICAgICBwcmludCh5
ZWxsb3coIiAgcHJvdG8gbnVldm8gKCVzKTogZWwgQ1NWICclcycgc2UgQVJDSElWQSBjb21vICVz
ICIKICAgICAgICAgICAgICAgICAgICAgICAgICIobmFkYSBzZSBib3JyYSk7IGxhIGNvcnJpZGEg
ZXMgY29tcGxldGEiCiAgICAgICAgICAgICAgICAgICAgICAgICAlIChQUk9UTywgcHJvdG9fdmll
am8sIG9zLnBhdGguYmFzZW5hbWUoZGVzdGlubykpKSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9u
IGFzIGU6CiAgICAgICAgICAgIHByaW50KHllbGxvdygiICBBVklTTzogbm8gcHVkZSBhcmNoaXZh
ciBlbCBDU1YgZGUgJXMgKCVyKSIKICAgICAgICAgICAgICAgICAgICAgICAgICUgKHByb3RvX3Zp
ZWpvLCBlKSkpCiAgICBoZWNob3MgPSBjc3ZfY2FyZ2FyX2hlY2hvcyhydXRhX2NzdikKICAgIHBl
bmRpZW50ZXMgPSBbYyBmb3IgYyBpbiBjb25maWdzIGlmIGNbImlkIl0gbm90IGluIGhlY2hvc10K
ICAgIGlmIGxlbihwZW5kaWVudGVzKSA8IGxlbihjb25maWdzKToKICAgICAgICBwcmludChncmF5
KCIgIHJlc3VtZTogJWQgeWEgbWVkaWRhcywgJWQgcGVuZGllbnRlcyIKICAgICAgICAgICAgICAg
ICAgICUgKGxlbihjb25maWdzKSAtIGxlbihwZW5kaWVudGVzKSwgbGVuKHBlbmRpZW50ZXMpKSkp
CgogICAgcmVzdWx0YWRvcywgY29tcGxldG9zID0ge30sIHt9CiAgICBmb3IgY2lkLCByb3cgaW4g
aGVjaG9zLml0ZW1zKCk6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBkZWMgPSBmbG9hdChyb3cu
Z2V0KCJkZWNvZGVfdHMiKSBvciAiIikgb3IgTm9uZQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246
CiAgICAgICAgICAgIGRlYyA9IE5vbmUKICAgICAgICByZXN1bHRhZG9zW2NpZF0gPSBkaWN0KHJv
dykKICAgICAgICByZXN1bHRhZG9zW2NpZF1bImRlY29kZV90cyJdID0gZGVjCiAgICAgICAgY29t
cGxldG9zW2NpZF0gPSBkaWN0KHJvdykKCiAgICBoZWNoYXNfc2VzaW9uID0gMAogICAgaW50ZXJy
dW1waWRvID0gRmFsc2UKICAgIHRyeToKICAgICAgICBmb3IgY2ZnIGluIGNvbmZpZ3M6CiAgICAg
ICAgICAgIGlmIGNmZ1siaWQiXSBpbiBoZWNob3M6CiAgICAgICAgICAgICAgICBwcmludChncmF5
KCIgIFslMDJkXSAlczogeWEgbWVkaWRhICh2YWxpZGEpLCBzYWx0byIKICAgICAgICAgICAgICAg
ICAgICAgICAgICAgJSAoY2ZnWyJpZCJdLCBjZmdbIm5vbWJyZSJdKSkpCiAgICAgICAgICAgICAg
ICBjb250aW51ZQogICAgICAgICAgICBpZiAoaGVjaGFzX3Nlc2lvbiBhbmQgaGVjaGFzX3Nlc2lv
biAlIFBBVVNBX0NBREEgPT0gMAogICAgICAgICAgICAgICAgICAgIGFuZCBub3QgYXJncy5zaW5f
cGF1c2FzIGFuZCBQQVVTQV9URVJNSUNBX1MgPiAwKToKICAgICAgICAgICAgICAgIHByaW50KHll
bGxvdygiICBwYXVzYSB0ZXJtaWNhICVkIHMgKHByb3RlZ2UgbGEgbWVkaWNpb24pLi4uIgogICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICUgUEFVU0FfVEVSTUlDQV9TKSkKICAgICAgICAgICAg
ICAgIHRpbWUuc2xlZXAoUEFVU0FfVEVSTUlDQV9TKQogICAgICAgICAgICB0cnk6CiAgICAgICAg
ICAgICAgICBmaWxhLCBjb21wbGV0byA9IG1lZGlyX2NvbmZpZyhjZmcsIGNvbnRleHRvKQogICAg
ICAgICAgICBleGNlcHQgS2V5Ym9hcmRJbnRlcnJ1cHQ6CiAgICAgICAgICAgICAgICByYWlzZQog
ICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgICAgICAjIHVuYSBj
b25maWcgSkFNQVMgdHVtYmEgZWwgYmFycmlkbyAobGVjY2lvbiB2MS4xIGRlbCBOMSkKICAgICAg
ICAgICAgICAgIGZpbGEgPSB7YzogIiIgZm9yIGMgaW4gQ09MVU1OQVN9CiAgICAgICAgICAgICAg
ICBmaWxhLnVwZGF0ZSh7InByb3RvIjogUFJPVE8sICJpZCI6IGNmZ1siaWQiXSwKICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAibm9tYnJlIjogY2ZnWyJub21icmUiXSwgImZhbWlsaWEiOiBj
ZmdbImZhbWlsaWEiXSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAiZmVjaGFfaG9yYSI6
IGFob3JhKCksICJ2YWxpZG8iOiAiTk8iLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICJu
b3RhIjogImV4Y2VwY2lvbiBubyBjYXB0dXJhZGE6ICVyIiAlIGV9KQogICAgICAgICAgICAgICAg
Y29tcGxldG8gPSB7ImlkIjogY2ZnWyJpZCJdLCAibm9tYnJlIjogY2ZnWyJub21icmUiXSwKICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICJmYW1pbGlhIjogY2ZnWyJmYW1pbGlhIl0sICJ2YWxp
ZG8iOiBGYWxzZSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICJub3RhIjogZmlsYVsibm90
YSJdLCAiZXhjZXBjaW9uIjogcmVwcihlKX0KICAgICAgICAgICAgICAgIHByaW50KHJlZCgiICBb
JTAyZF0gRVhDRVBDSU9OIG5vIGNhcHR1cmFkYTogJXIiICUgKGNmZ1siaWQiXSwgZSkpKQogICAg
ICAgICAgICBpZiAoY2ZnWyJpZCJdICE9IDEgYW5kIGZpbGEuZ2V0KCJkZWNvZGVfdHMiKQogICAg
ICAgICAgICAgICAgICAgIGFuZCAocmVzdWx0YWRvcy5nZXQoMSkgb3Ige30pLmdldCgiZGVjb2Rl
X3RzIikpOgogICAgICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgIGZpbGFbImRl
bHRhX3ZzX2FuY2xhX3BjdCJdID0gIiUuMWYiICUgKAogICAgICAgICAgICAgICAgICAgICAgICAo
ZmxvYXQoZmlsYVsiZGVjb2RlX3RzIl0pCiAgICAgICAgICAgICAgICAgICAgICAgICAvIHJlc3Vs
dGFkb3NbMV1bImRlY29kZV90cyJdIC0gMS4wKSAqIDEwMCkKICAgICAgICAgICAgICAgIGV4Y2Vw
dCAoVHlwZUVycm9yLCBWYWx1ZUVycm9yLCBaZXJvRGl2aXNpb25FcnJvcik6CiAgICAgICAgICAg
ICAgICAgICAgcGFzcwogICAgICAgICAgICBjc3ZfYXBwZW5kKHJ1dGFfY3N2LCBmaWxhKQogICAg
ICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBkZWMgPSBmbG9hdChmaWxhLmdldCgiZGVjb2Rl
X3RzIikgb3IgIiIpIG9yIE5vbmUKICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAg
ICAgICAgICAgIGRlYyA9IE5vbmUKICAgICAgICAgICAgcmVzdWx0YWRvc1tjZmdbImlkIl1dID0g
ZGljdChmaWxhKQogICAgICAgICAgICByZXN1bHRhZG9zW2NmZ1siaWQiXV1bImRlY29kZV90cyJd
ID0gZGVjCiAgICAgICAgICAgIGNvbXBsZXRvc1tjZmdbImlkIl1dID0gY29tcGxldG8KICAgICAg
ICAgICAgaGVjaGFzX3Nlc2lvbiArPSAxCiAgICAgICAgICAgICMgLS0tLSBhbmNsYSBtdWVydGEg
PSBGQVRBTCAodjEuMywgY2FtcG8gMjgtb2N0KSAtLS0tLS0tLS0tLS0tLS0tLQogICAgICAgICAg
ICAjIHNpbiBiYXNlbGluZSBkZSBzZXNpb24gZWwgcHJvdG9jb2xvIGVudGVybyBxdWVkYSBzaW4g
cGF0YQogICAgICAgICAgICAjIChib29rZW5kIGltcG9zaWJsZSwgZGVsdGFzIE4vRCk6IHNlZ3Vp
ciBtaWRpZW5kbyBlcyB0aXJhciBlbAogICAgICAgICAgICAjIGRpYS4gTGEgZmlsYSBxdWVkYSBl
biBlbCBDU1YgeSBlbCByZXN1bWUgcmUtbWlkZSBzb2xhLgogICAgICAgICAgICBpZiBjZmdbImlk
Il0gPT0gMSBhbmQgZmlsYS5nZXQoInZhbGlkbyIpICE9ICJTSSI6CiAgICAgICAgICAgICAgICBw
cmludChyZWQoIiAgY29sYSBkZWwgbG9nIGRlbCBhbmNsYTogJXMiCiAgICAgICAgICAgICAgICAg
ICAgICAgICAgJSAoY29tcGxldG9zLmdldCgxLCB7fSkuZ2V0KCJsb2dfY29sYSIpIG9yICJOL0Qi
KSkpCiAgICAgICAgICAgICAgICByYWlzZSBTeXN0ZW1FeGl0KHJlZCgKICAgICAgICAgICAgICAg
ICAgICAiRkFUQUw6IGVsIEFOQ0xBIChpZCAxID0gbGEgcmVjZXRhIGRpYXJpYSkgbm8gY2FyZ28g
KCVzKS4gIgogICAgICAgICAgICAgICAgICAgICJTaW4gYW5jbGEgbm8gaGF5IGJhc2VsaW5lOiBi
b29rZW5kIGltcG9zaWJsZSB5IGRlbHRhcyAiCiAgICAgICAgICAgICAgICAgICAgIk4vRCAtPiBu
YWRhIG1hcyBzZSBtaWRlIGVuIGVzdGEgc2VzaW9uLiBDYXVzYSB0aXBpY2E6IGxhICIKICAgICAg
ICAgICAgICAgICAgICAicmVjZXRhIGJhc2Ugbm8gY29pbmNpZGUgY29uIGNvbmZpZy50eHQgKGNv
bG9jYWNpb24gLWNtb2UgIgogICAgICAgICAgICAgICAgICAgICJhdXNlbnRlID0gZWwgbW9kZWxv
IG5vIGNhYmUgZW4gbGEgR1BVKS4gUmV2aXNhciAiCiAgICAgICAgICAgICAgICAgICAgImxvZ3Mt
Y29uZmlnLzAxLU4zLUFOQ0xBLmxvZzsgZWwgcmVzdW1lIHJlLW1pZGUgc29sYSBlc3RhICIKICAg
ICAgICAgICAgICAgICAgICAiY29uZmlnIGFsIHJlcGV0aXIgZWwgY29tYW5kby4iICUgZmlsYS5n
ZXQoIm5vdGEiLCAiIikpKQogICAgZXhjZXB0IEtleWJvYXJkSW50ZXJydXB0OgogICAgICAgIGlu
dGVycnVtcGlkbyA9IFRydWUKICAgICAgICBwcmludCh5ZWxsb3coIlxuICBJTlRFUlJVTVBJRE8g
KEN0cmwrQyk6IGd1YXJkYW5kbyBpbmZvcm1lIHBhcmNpYWw7ICIKICAgICAgICAgICAgICAgICAg
ICAgImxvIHlhIG1lZGlkbyBxdWVkYSBlbiBlbCBDU1YgeSBzZSByZWFudWRhIGRlc3B1ZXMuLi4i
KSkKCiAgICAjIC0tLS0gMi4gaW5mb3JtZSAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQogICAgcHJpbnQoY3lhbigiWzJdIElORk9STUUuLi4i
KSkKICAgIHJ1dGFfbWQgPSBnZW5lcmFyX2luZm9ybWUoYXJncy5sb2dzLCBjb250ZXh0bywgcmVz
dWx0YWRvcywgY29tcGxldG9zLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICBwcm9ibGVt
YXMpCiAgICBwcmludChncmVlbigiICAlcyIgJSBydXRhX21kKSkKICAgIHByaW50KGdyZWVuKCIg
ICVzIiAlIHJ1dGFfY3N2KSkKICAgIHByaW50KGdyZWVuKCIgICVzIiAlIG9zLnBhdGguam9pbihh
cmdzLmxvZ3MsICJmYXNlTjMtZGF0b3MuanNvbiIpKSkKICAgIHByaW50KGdyZWVuKCIgICVzIiAl
IG9zLnBhdGguam9pbihhcmdzLmxvZ3MsICJmYXNlTjMtY29uc29sYS5sb2ciKSkpCiAgICBwcmlu
dCgiIikKICAgIHByaW50KGJvbGQoIlBhcmEgcGFzYXIgYWwgYW5hbGlzaXM6IGZhc2VOMy1JTkZP
Uk1FLm1kICsgIgogICAgICAgICAgICAgICAiZmFzZU4zLXJlc3VsdGFkb3MuY3N2ICgrIGNhcnBl
dGEgbG9ncy1jb25maWcgc2kgc2UgcGlkZSkuIikpCiAgICByZXR1cm4gMTMwIGlmIGludGVycnVt
cGlkbyBlbHNlIDAKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgc3lzLmV4aXQobWFp
bigpKQo=
"""
    ),
    "config.txt": (
"""
IyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09
PT09PT0KIyAgQ09ORklHIENFTlRSQUwgZGVsIHByb3llY3RvICAoY2FzYTogRDpcWkxpYVxjb25m
aWcudHh0KQojICBUT0RBIGxhIGNvbmZpZ3VyYWNpb24gdml2ZSBBUVVJLiBMb3MgcHJvZ3JhbWFz
IChhYnJpciwKIyAgY2hhdGVhcikgbGVlbiBlc3RlIGFyY2hpdm8uIEFxdWkgc2UgZWRpdGEsIGVu
IG5pbmd1biBvdHJvLgojICBGb3JtYXRvOiAgQ0xBVkUgPSB2YWxvciAgICAobGluZWFzIGNvbiAj
ID0gY29tZW50YXJpb3MpCiMgPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09
PT09PT09PT09PT09PT09PT09PT09CgojIC0tLSBSdXRhcyAtLS0KUlVUQV9TRVJWRVIgPSBEOlxs
bGFtYS5jcHBcbGxhbWEtc2VydmVyLmV4ZQpSVVRBX01PREVMTyA9IEQ6XFpMaWFcbW9kZWxzXFF3
ZW4zLjYtMzVCLUEzQi11bmNlbnNvcmVkLWhlcmV0aWMtTmF0aXZlLU1UUC1QcmVzZXJ2ZWQtQVBF
WC1JLU1JTkkuZ2d1ZgpSVVRBX0xPR1MgPSBEOlxaTGlhXGZhc2VELWxvZ3MKCiMgLS0tIFJlZCAt
LS0KUFVFUlRPID0gOTkzMQoKIyAtLS0gRXhwZXJ0b3MgKGVsIHRydWNvIGRlIGxvcyBjb2NpbmVy
b3MpIC0tLQojIDggPSBjb21vIHZpbm8gZGUgZmFicmljYSAocHJvZ3JhbWFyKSAvIDQgPSBjaGFy
bGEgY2FzdWFsICh+KzQxJSB0L3MpCkVYUEVSVE9TX1RSQUJBSk8gPSA4CkVYUEVSVE9TX0NIQVJM
QSA9IDQKCiMgLS0tIEZsYWdzIGRlbCBzZXJ2ZXIgLS0tCiMgRkxBR1NfQkFTRSA9IGJhc2UgY2Ft
cGVvbmEgdmVyaWZpY2FkYS4gU0FNUExJTkcgPSBwcmVzZXQgInRoaW5rIgojIG9maWNpYWwgZGUg
bGEgY2FyZCBRd2VuMy42LiBGTEFHU19HQU5BRE9SQVMgdmFuIEFMIEZJTkFMIHkgZWwKIyB1bHRp
bW8gdmFsb3IgZ2FuYSAoYXPDrSBzZSBwaXNhIC11Yi8tYiBkZSBsYSBiYXNlKS4KIyAoTGFzIGZs
YWdzIFBFUk1JVElEQVMgc2UgYXVkaXRhbiBjb250cmEgSW5mb3JtYWNpb25Dcml0aWNhXGxsYW1h
LWZsYWdzLW51ZXZvLnR4dCkKRkxBR1NfQkFTRSA9IC1uZ2wgOTkgLWNtb2UgLWMgMTYzODQgLWIg
MjA0OCAtdWIgMjU2IC1mYSBvbiAtY3RrIHE4XzAgLWN0diBxOF8wIC10IDQgLS1wcmlvIDIgLS1u
by1tbXByb2ogLWxtIG5vbmUKU0FNUExJTkcgPSAtLXRlbXAgMS4wIC0tdG9wLWsgMjAgLS10b3At
cCAwLjk1IC0tbWluLXAgMC4wIC0tcHJlc2VuY2UtcGVuYWx0eSAwLjAKRkxBR1NfR0FOQURPUkFT
ID0gLXViIDEwMjQgLWIgNDA5Ngo=
"""
    ),
    "llama-flags-nuevo.txt": (
"""
//4tAC0ALQAtAC0AIABjAG8AbQBtAG8AbgAgAHAAYQByAGEAbQBzACAALQAtAC0ALQAtAA0ACgAN
AAoALQBoACwAIAAgACAAIAAtAC0AaABlAGwAcAAsACAALQAtAHUAcwBhAGcAZQAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIABwAHIAaQBuAHQAIAB1AHMAYQBnAGUAIABhAG4AZAAg
AGUAeABpAHQADQAKAC0ALQB2AGUAcgBzAGkAbwBuACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBoAG8AdwAgAHYAZQByAHMAaQBv
AG4AIABhAG4AZAAgAGIAdQBpAGwAZAAgAGkAbgBmAG8ADQAKAC0AYwBsACwAIAAgACAALQAtAGMA
YQBjAGgAZQAtAGwAaQBzAHQAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAcwBoAG8AdwAgAGwAaQBzAHQAIABvAGYAIABtAG8AZABlAGwAcwAgAGkAbgAgAGMAYQBjAGgA
ZQANAAoALQAtAGMAbwBtAHAAbABlAHQAaQBvAG4ALQBiAGEAcwBoACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABwAHIAaQBuAHQAIABzAG8AdQByAGMAZQAtAGEA
YgBsAGUAIABiAGEAcwBoACAAYwBvAG0AcABsAGUAdABpAG8AbgAgAHMAYwByAGkAcAB0ACAAZgBv
AHIAIABsAGwAYQBtAGEALgBjAHAAcAANAAoALQB0ACwAIAAgACAAIAAtAC0AdABoAHIAZQBhAGQA
cwAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABuAHUAbQBi
AGUAcgAgAG8AZgAgAEMAUABVACAAdABoAHIAZQBhAGQAcwAgAHQAbwAgAHUAcwBlACAAZAB1AHIA
aQBuAGcAIABnAGUAbgBlAHIAYQB0AGkAbwBuACAAKABkAGUAZgBhAHUAbAB0ADoAIAAtADEAKQAN
AAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBf
AFQASABSAEUAQQBEAFMAKQANAAoALQB0AGIALAAgACAAIAAtAC0AdABoAHIAZQBhAGQAcwAtAGIA
YQB0AGMAaAAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABuAHUAbQBiAGUAcgAg
AG8AZgAgAHQAaAByAGUAYQBkAHMAIAB0AG8AIAB1AHMAZQAgAGQAdQByAGkAbgBnACAAYgBhAHQA
YwBoACAAYQBuAGQAIABwAHIAbwBtAHAAdAAgAHAAcgBvAGMAZQBzAHMAaQBuAGcAIAAoAGQAZQBm
AGEAdQBsAHQAOgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABzAGEAbQBlACAAYQBzACAALQAt
AHQAaAByAGUAYQBkAHMAKQANAAoALQBDACwAIAAgACAAIAAtAC0AYwBwAHUALQBtAGEAcwBrACAA
TQAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABDAFAAVQAgAGEAZgBm
AGkAbgBpAHQAeQAgAG0AYQBzAGsAOgAgAGEAcgBiAGkAdAByAGEAcgBpAGwAeQAgAGwAbwBuAGcA
IABoAGUAeAAuACAAQwBvAG0AcABsAGUAbQBlAG4AdABzACAAYwBwAHUALQByAGEAbgBnAGUADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAKABkAGUAZgBhAHUAbAB0ADoAIAAiACIAKQANAAoALQBD
AHIALAAgACAAIAAtAC0AYwBwAHUALQByAGEAbgBnAGUAIABsAG8ALQBoAGkAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAByAGEAbgBnAGUAIABvAGYAIABDAFAAVQBzACAAZgBvAHIAIABh
AGYAZgBpAG4AaQB0AHkALgAgAEMAbwBtAHAAbABlAG0AZQBuAHQAcwAgAC0ALQBjAHAAdQAtAG0A
YQBzAGsADQAKAC0ALQBjAHAAdQAtAHMAdAByAGkAYwB0ACAAPAAwAHwAMQA+ACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdQBzAGUAIABzAHQAcgBpAGMAdAAgAEMA
UABVACAAcABsAGEAYwBlAG0AZQBuAHQAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADAAKQANAAoALQAt
AHAAcgBpAG8AIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIABzAGUAdAAgAHAAcgBvAGMAZQBzAHMALwB0AGgAcgBlAGEAZAAg
AHAAcgBpAG8AcgBpAHQAeQAgADoAIABsAG8AdwAoAC0AMQApACwAIABuAG8AcgBtAGEAbAAoADAA
KQAsACAAbQBlAGQAaQB1AG0AKAAxACkALAAgAGgAaQBnAGgAKAAyACkALAANAAoAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAByAGUAYQBsAHQAaQBtAGUAKAAzACkAIAAoAGQAZQBmAGEAdQBsAHQAOgAg
ADAAKQANAAoALQAtAHAAbwBsAGwAIAA8ADAALgAuAC4AMQAwADAAPgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB1AHMAZQAgAHAAbwBsAGwAaQBuAGcAIABs
AGUAdgBlAGwAIAB0AG8AIAB3AGEAaQB0ACAAZgBvAHIAIAB3AG8AcgBrACAAKAAwACAALQAgAG4A
bwAgAHAAbwBsAGwAaQBuAGcALAAgAGQAZQBmAGEAdQBsAHQAOgAgADUAMAApAA0ACgAtAEMAYgAs
ACAAIAAgAC0ALQBjAHAAdQAtAG0AYQBzAGsALQBiAGEAdABjAGgAIABNACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAEMAUABVACAAYQBmAGYAaQBuAGkAdAB5ACAAbQBhAHMAawA6ACAAYQBy
AGIAaQB0AHIAYQByAGkAbAB5ACAAbABvAG4AZwAgAGgAZQB4AC4AIABDAG8AbQBwAGwAZQBtAGUA
bgB0AHMAIABjAHAAdQAtAHIAYQBuAGcAZQAtAGIAYQB0AGMAaAANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAHMAYQBtAGUAIABhAHMAIAAtAC0AYwBwAHUALQBt
AGEAcwBrACkADQAKAC0AQwByAGIALAAgACAALQAtAGMAcAB1AC0AcgBhAG4AZwBlAC0AYgBhAHQA
YwBoACAAbABvAC0AaABpACAAIAAgACAAIAAgACAAIAAgACAAcgBhAG4AZwBlAHMAIABvAGYAIABD
AFAAVQBzACAAZgBvAHIAIABhAGYAZgBpAG4AaQB0AHkALgAgAEMAbwBtAHAAbABlAG0AZQBuAHQA
cwAgAC0ALQBjAHAAdQAtAG0AYQBzAGsALQBiAGEAdABjAGgADQAKAC0ALQBjAHAAdQAtAHMAdABy
AGkAYwB0AC0AYgBhAHQAYwBoACAAPAAwAHwAMQA+ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAdQBzAGUAIABzAHQAcgBpAGMAdAAgAEMAUABVACAAcABsAGEAYwBlAG0AZQBuAHQAIAAo
AGQAZQBmAGEAdQBsAHQAOgAgAHMAYQBtAGUAIABhAHMAIAAtAC0AYwBwAHUALQBzAHQAcgBpAGMA
dAApAA0ACgAtAC0AcAByAGkAbwAtAGIAYQB0AGMAaAAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHMAZQB0ACAAcAByAG8AYwBlAHMAcwAvAHQA
aAByAGUAYQBkACAAcAByAGkAbwByAGkAdAB5ACAAOgAgADAALQBuAG8AcgBtAGEAbAAsACAAMQAt
AG0AZQBkAGkAdQBtACwAIAAyAC0AaABpAGcAaAAsACAAMwAtAHIAZQBhAGwAdABpAG0AZQANAAoA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADAAKQANAAoALQAtAHAA
bwBsAGwALQBiAGEAdABjAGgAIAA8ADAAfAAxAD4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAB1AHMAZQAgAHAAbwBsAGwAaQBuAGcAIAB0AG8AIAB3AGEAaQB0ACAA
ZgBvAHIAIAB3AG8AcgBrACAAKABkAGUAZgBhAHUAbAB0ADoAIABzAGEAbQBlACAAYQBzACAALQAt
AHAAbwBsAGwAKQANAAoALQBjACwAIAAgACAAIAAtAC0AYwB0AHgALQBzAGkAegBlACAATgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABzAGkAegBlACAAbwBmACAAdABo
AGUAIABwAHIAbwBtAHAAdAAgAGMAbwBuAHQAZQB4AHQAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADAA
LAAgADAAIAA9ACAAbABvAGEAZABlAGQAIABmAHIAbwBtACAAbQBvAGQAZQBsACkADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBDAFQAWABf
AFMASQBaAEUAKQANAAoALQBuACwAIAAgACAAIAAtAC0AcAByAGUAZABpAGMAdAAsACAALQAtAG4A
LQBwAHIAZQBkAGkAYwB0ACAATgAgACAAIAAgACAAIAAgACAAIABuAHUAbQBiAGUAcgAgAG8AZgAg
AHQAbwBrAGUAbgBzACAAdABvACAAcAByAGUAZABpAGMAdAAgACgAZABlAGYAYQB1AGwAdAA6ACAA
LQAxACwAIAAtADEAIAA9ACAAaQBuAGYAaQBuAGkAdAB5ACkADQAKACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBOAF8AUABSAEUARABJAEMAVAAp
AA0ACgAtAGIALAAgACAAIAAgAC0ALQBiAGEAdABjAGgALQBzAGkAegBlACAATgAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGwAbwBnAGkAYwBhAGwAIABtAGEAeABpAG0AdQBt
ACAAYgBhAHQAYwBoACAAcwBpAHoAZQAgACgAZABlAGYAYQB1AGwAdAA6ACAAMgAwADQAOAApAA0A
CgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8A
QgBBAFQAQwBIACkADQAKAC0AdQBiACwAIAAgACAALQAtAHUAYgBhAHQAYwBoAC0AcwBpAHoAZQAg
AE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcABoAHkAcwBpAGMAYQBsACAA
bQBhAHgAaQBtAHUAbQAgAGIAYQB0AGMAaAAgAHMAaQB6AGUAIAAoAGQAZQBmAGEAdQBsAHQAOgAg
ADUAMQAyACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBB
AF8AQQBSAEcAXwBVAEIAQQBUAEMASAApAA0ACgAtAC0AawBlAGUAcAAgAE4AIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4AdQBt
AGIAZQByACAAbwBmACAAdABvAGsAZQBuAHMAIAB0AG8AIABrAGUAZQBwACAAZgByAG8AbQAgAHQA
aABlACAAaQBuAGkAdABpAGEAbAAgAHAAcgBvAG0AcAB0ACAAKABkAGUAZgBhAHUAbAB0ADoAIAAw
ACwAIAAtADEAIAA9AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGEAbABsACkADQAKAC0ALQBz
AHcAYQAtAGYAdQBsAGwAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAdQBzAGUAIABmAHUAbABsAC0AcwBpAHoAZQAgAFMAVwBBACAAYwBh
AGMAaABlACAAKABkAGUAZgBhAHUAbAB0ADoAIABmAGEAbABzAGUAKQANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABbACgAbQBvAHIAZQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABpAG4AZgBv
ACkAXQAoAGgAdAB0AHAAcwA6AC8ALwBnAGkAdABoAHUAYgAuAGMAbwBtAC8AZwBnAG0AbAAtAG8A
cgBnAC8AbABsAGEAbQBhAC4AYwBwAHAALwBwAHUAbABsAC8AMQAzADEAOQA0ACMAaQBzAHMAdQBl
AGMAbwBtAG0AZQBuAHQALQAyADgANgA4ADMANAAzADAANQA1ACkADQAKACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBTAFcAQQBfAEYAVQBMAEwA
KQANAAoALQBmAGEALAAgACAAIAAtAC0AZgBsAGEAcwBoAC0AYQB0AHQAbgAgAFsAbwBuAHwAbwBm
AGYAfABhAHUAdABvAF0AIAAgACAAIAAgACAAIABzAGUAdAAgAEYAbABhAHMAaAAgAEEAdAB0AGUA
bgB0AGkAbwBuACAAdQBzAGUAIAAoACcAbwBuACcALAAgACcAbwBmAGYAJwAsACAAbwByACAAJwBh
AHUAdABvACcALAAgAGQAZQBmAGEAdQBsAHQAOgAgACcAYQB1AHQAbwAnACkADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBGAEwAQQBTAEgA
XwBBAFQAVABOACkADQAKAC0ALQBwAGUAcgBmACwAIAAtAC0AbgBvAC0AcABlAHIAZgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdwBoAGUAdABoAGUAcgAgAHQA
bwAgAGUAbgBhAGIAbABlACAAaQBuAHQAZQByAG4AYQBsACAAbABpAGIAbABsAGEAbQBhACAAcABl
AHIAZgBvAHIAbQBhAG4AYwBlACAAdABpAG0AaQBuAGcAcwAgACgAZABlAGYAYQB1AGwAdAA6AA0A
CgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGYAYQBsAHMAZQApAA0ACgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AUABFAFIARgApAA0ACgAtAGUA
LAAgACAAIAAgAC0ALQBlAHMAYwBhAHAAZQAsACAALQAtAG4AbwAtAGUAcwBjAGEAcABlACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgAHcAaABlAHQAaABlAHIAIAB0AG8AIABwAHIAbwBjAGUAcwBzACAA
ZQBzAGMAYQBwAGUAcwAgAHMAZQBxAHUAZQBuAGMAZQBzACAAKABcAG4ALAAgAFwAcgAsACAAXAB0
ACwAIABcACcALAAgAFwAIgAsACAAXABcACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABk
AGUAZgBhAHUAbAB0ADoAIAB0AHIAdQBlACkADQAKAC0ALQByAG8AcABlAC0AcwBjAGEAbABpAG4A
ZwAgAHsAbgBvAG4AZQAsAGwAaQBuAGUAYQByACwAeQBhAHIAbgB9ACAAIAAgACAAIAAgACAAUgBv
AFAARQAgAGYAcgBlAHEAdQBlAG4AYwB5ACAAcwBjAGEAbABpAG4AZwAgAG0AZQB0AGgAbwBkACwA
IABkAGUAZgBhAHUAbAB0AHMAIAB0AG8AIABsAGkAbgBlAGEAcgAgAHUAbgBsAGUAcwBzACAAcwBw
AGUAYwBpAGYAaQBlAGQAIABiAHkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdABoAGUAIABt
AG8AZABlAGwADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBB
AF8AQQBSAEcAXwBSAE8AUABFAF8AUwBDAEEATABJAE4ARwBfAFQAWQBQAEUAKQANAAoALQAtAHIA
bwBwAGUALQBzAGMAYQBsAGUAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIABSAG8AUABFACAAYwBvAG4AdABlAHgAdAAgAHMAYwBhAGwAaQBuAGcA
IABmAGEAYwB0AG8AcgAsACAAZQB4AHAAYQBuAGQAcwAgAGMAbwBuAHQAZQB4AHQAIABiAHkAIABh
ACAAZgBhAGMAdABvAHIAIABvAGYAIABOAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBu
AHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AUgBPAFAARQBfAFMAQwBBAEwARQApAA0ACgAtAC0A
cgBvAHAAZQAtAGYAcgBlAHEALQBiAGEAcwBlACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgAFIAbwBQAEUAIABiAGEAcwBlACAAZgByAGUAcQB1AGUAbgBjAHkA
LAAgAHUAcwBlAGQAIABiAHkAIABOAFQASwAtAGEAdwBhAHIAZQAgAHMAYwBhAGwAaQBuAGcAIAAo
AGQAZQBmAGEAdQBsAHQAOgAgAGwAbwBhAGQAZQBkACAAZgByAG8AbQANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABtAG8AZABlAGwAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2
ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFIATwBQAEUAXwBGAFIARQBRAF8AQgBBAFMARQApAA0A
CgAtAC0AcgBvAHAAZQAtAGYAcgBlAHEALQBzAGMAYQBsAGUAIABOACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAFIAbwBQAEUAIABmAHIAZQBxAHUAZQBuAGMAeQAgAHMA
YwBhAGwAaQBuAGcAIABmAGEAYwB0AG8AcgAsACAAZQB4AHAAYQBuAGQAcwAgAGMAbwBuAHQAZQB4
AHQAIABiAHkAIABhACAAZgBhAGMAdABvAHIAIABvAGYAIAAxAC8ATgANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFIATwBQAEUAXwBGAFIA
RQBRAF8AUwBDAEEATABFACkADQAKAC0ALQB5AGEAcgBuAC0AbwByAGkAZwAtAGMAdAB4ACAATgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAWQBhAFIATgA6ACAA
bwByAGkAZwBpAG4AYQBsACAAYwBvAG4AdABlAHgAdAAgAHMAaQB6AGUAIABvAGYAIABtAG8AZABl
AGwAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADAAIAA9ACAAbQBvAGQAZQBsACAAdAByAGEAaQBuAGkA
bgBnAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGMAbwBuAHQAZQB4AHQAIABzAGkAegBlACkA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcA
XwBZAEEAUgBOAF8ATwBSAEkARwBfAEMAVABYACkADQAKAC0ALQB5AGEAcgBuAC0AZQB4AHQALQBm
AGEAYwB0AG8AcgAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
WQBhAFIATgA6ACAAZQB4AHQAcgBhAHAAbwBsAGEAdABpAG8AbgAgAG0AaQB4ACAAZgBhAGMAdABv
AHIAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAC0AMQAuADAAMAAsACAAMAAuADAAIAA9ACAAZgB1AGwA
bAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABpAG4AdABlAHIAcABvAGwAYQB0AGkAbwBuACkA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcA
XwBZAEEAUgBOAF8ARQBYAFQAXwBGAEEAQwBUAE8AUgApAA0ACgAtAC0AeQBhAHIAbgAtAGEAdAB0
AG4ALQBmAGEAYwB0AG8AcgAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAFkAYQBSAE4AOgAgAHMAYwBhAGwAZQAgAHMAcQByAHQAKAB0ACkAIABvAHIAIABhAHQAdABl
AG4AdABpAG8AbgAgAG0AYQBnAG4AaQB0AHUAZABlACAAKABkAGUAZgBhAHUAbAB0ADoAIAAtADEA
LgAwADAAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEA
XwBBAFIARwBfAFkAQQBSAE4AXwBBAFQAVABOAF8ARgBBAEMAVABPAFIAKQANAAoALQAtAHkAYQBy
AG4ALQBiAGUAdABhAC0AcwBsAG8AdwAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIABZAGEAUgBOADoAIABoAGkAZwBoACAAYwBvAHIAcgBlAGMAdABpAG8AbgAg
AGQAaQBtACAAbwByACAAYQBsAHAAaABhACAAKABkAGUAZgBhAHUAbAB0ADoAIAAtADEALgAwADAA
KQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIA
RwBfAFkAQQBSAE4AXwBCAEUAVABBAF8AUwBMAE8AVwApAA0ACgAtAC0AeQBhAHIAbgAtAGIAZQB0
AGEALQBmAGEAcwB0ACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAFkAYQBSAE4AOgAgAGwAbwB3ACAAYwBvAHIAcgBlAGMAdABpAG8AbgAgAGQAaQBtACAAbwBy
ACAAYgBlAHQAYQAgACgAZABlAGYAYQB1AGwAdAA6ACAALQAxAC4AMAAwACkADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBZAEEAUgBOAF8A
QgBFAFQAQQBfAEYAQQBTAFQAKQANAAoALQBrAHYAbwAsACAAIAAtAC0AawB2AC0AbwBmAGYAbABv
AGEAZAAsACAALQBuAGsAdgBvACwAIAAtAC0AbgBvAC0AawB2AC0AbwBmAGYAbABvAGEAZAANAAoA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAB3AGgAZQB0AGgAZQByACAAdABvACAAZQBuAGEAYgBsAGUA
IABLAFYAIABjAGEAYwBoAGUAIABvAGYAZgBsAG8AYQBkAGkAbgBnACAAKABkAGUAZgBhAHUAbAB0
ADoAIABlAG4AYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6
ACAATABMAEEATQBBAF8AQQBSAEcAXwBLAFYAXwBPAEYARgBMAE8AQQBEACkADQAKAC0ALQByAGUA
cABhAGMAawAsACAALQBuAHIALAAgAC0ALQBuAG8ALQByAGUAcABhAGMAawAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAdwBoAGUAdABoAGUAcgAgAHQAbwAgAGUAbgBhAGIAbABlACAAdwBlAGkA
ZwBoAHQAIAByAGUAcABhAGMAawBpAG4AZwAgACgAZABlAGYAYQB1AGwAdAA6ACAAZQBuAGEAYgBs
AGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBf
AEEAUgBHAF8AUgBFAFAAQQBDAEsAKQANAAoALQAtAG4AbwAtAGgAbwBzAHQAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABiAHkAcABh
AHMAcwAgAGgAbwBzAHQAIABiAHUAZgBmAGUAcgAgAGEAbABsAG8AdwBpAG4AZwAgAGUAeAB0AHIA
YQAgAGIAdQBmAGYAZQByAHMAIAB0AG8AIABiAGUAIAB1AHMAZQBkAA0ACgAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ATgBPAF8ASABPAFMAVAAp
AA0ACgAtAGMAdABrACwAIAAgAC0ALQBjAGEAYwBoAGUALQB0AHkAcABlAC0AawAgAFQAWQBQAEUA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAEsAVgAgAGMAYQBjAGgAZQAgAGQAYQB0AGEAIAB0
AHkAcABlACAAZgBvAHIAIABLAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGEAbABsAG8AdwBl
AGQAIAB2AGEAbAB1AGUAcwA6ACAAZgAzADIALAAgAGYAMQA2ACwAIABiAGYAMQA2ACwAIABxADgA
XwAwACwAIABxADQAXwAwACwAIABxADQAXwAxACwAIABpAHEANABfAG4AbAAsACAAcQA1AF8AMAAs
ACAAcQA1AF8AMQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGQAZQBmAGEAdQBsAHQAOgAg
AGYAMQA2ACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBB
AF8AQQBSAEcAXwBDAEEAQwBIAEUAXwBUAFkAUABFAF8ASwApAA0ACgAtAGMAdAB2ACwAIAAgAC0A
LQBjAGEAYwBoAGUALQB0AHkAcABlAC0AdgAgAFQAWQBQAEUAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgAEsAVgAgAGMAYQBjAGgAZQAgAGQAYQB0AGEAIAB0AHkAcABlACAAZgBvAHIAIABWAA0A
CgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGEAbABsAG8AdwBlAGQAIAB2AGEAbAB1AGUAcwA6ACAA
ZgAzADIALAAgAGYAMQA2ACwAIABiAGYAMQA2ACwAIABxADgAXwAwACwAIABxADQAXwAwACwAIABx
ADQAXwAxACwAIABpAHEANABfAG4AbAAsACAAcQA1AF8AMAAsACAAcQA1AF8AMQANAAoAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGYAMQA2ACkADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBDAEEAQwBIAEUA
XwBUAFkAUABFAF8AVgApAA0ACgAtAGQAdAAsACAAIAAgAC0ALQBkAGUAZgByAGEAZwAtAHQAaABv
AGwAZAAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAEsAVgAgAGMAYQBjAGgA
ZQAgAGQAZQBmAHIAYQBnAG0AZQBuAHQAYQB0AGkAbwBuACAAdABoAHIAZQBzAGgAbwBsAGQAIAAo
AEQARQBQAFIARQBDAEEAVABFAEQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2
ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEQARQBGAFIAQQBHAF8AVABIAE8ATABEACkADQAKAC0A
LQByAHAAYwAgAFMARQBSAFYARQBSAFMAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAYwBvAG0AbQBhAC0AcwBlAHAAYQByAGEAdABlAGQAIABsAGkA
cwB0ACAAbwBmACAAUgBQAEMAIABzAGUAcgB2AGUAcgBzACAAKABoAG8AcwB0ADoAcABvAHIAdAAp
AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBH
AF8AUgBQAEMAKQANAAoALQBsAG0ALAAgACAAIAAtAC0AbABvAGEAZAAtAG0AbwBkAGUAIABNAE8A
RABFACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABtAG8AZABlAGwAIABsAG8AYQBk
AGkAbgBnACAAbQBvAGQAZQAgACgAZABlAGYAYQB1AGwAdAA6ACAAYQB1AHQAbwApAA0ACgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgAC0AIABhAHUAdABvADoAIABtAG0AYQBwACwAIAB1AG4AbABlAHMA
cwAgAGEAIABkAGUAdgBpAGMAZQAgAGQAbwBlAHMAIABuAG8AdAAgAHMAdQBwAHAAbwByAHQAIABp
AHQADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAALQAgAG4AbwBuAGUAOgAgAG4AbwAgAHMAcABl
AGMAaQBhAGwAIABsAG8AYQBkAGkAbgBnACAAbQBvAGQAZQANAAoAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAtACAAbQBtAGEAcAA6ACAAbQBlAG0AbwByAHkALQBtAGEAcAAgAG0AbwBkAGUAbAAgACgA
aQBmACAAbQBtAGEAcAAgAGQAaQBzAGEAYgBsAGUAZAAsACAAcwBsAG8AdwBlAHIAIABsAG8AYQBk
ACAAYgB1AHQAIABtAGEAeQAgAHIAZQBkAHUAYwBlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AHAAYQBnAGUAbwB1AHQAcwAgAGkAZgAgAG4AbwB0ACAAdQBzAGkAbgBnACAAbQBsAG8AYwBrACkA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAALQAgAG0AbABvAGMAawA6ACAAZgBvAHIAYwBlACAA
cwB5AHMAdABlAG0AIAB0AG8AIABrAGUAZQBwACAAbQBvAGQAZQBsACAAaQBuACAAUgBBAE0AIABy
AGEAdABoAGUAcgAgAHQAaABhAG4AIABzAHcAYQBwAHAAaQBuAGcAIABvAHIADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAYwBvAG0AcAByAGUAcwBzAGkAbgBnAA0ACgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgAC0AIABtAG0AYQBwACsAbQBsAG8AYwBrADoAIABtAG0AYQBwACAAKwAgAGYAbwByAGMA
ZQAgAHMAeQBzAHQAZQBtACAAdABvACAAawBlAGUAcAAgAG0AbwBkAGUAbAAgAGkAbgAgAFIAQQBN
ACAAcgBhAHQAaABlAHIAIAB0AGgAYQBuAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHMAdwBh
AHAAcABpAG4AZwAgAG8AcgAgAGMAbwBtAHAAcgBlAHMAcwBpAG4AZwANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAtACAAZABpAG8AOgAgAHUAcwBlACAARABpAHIAZQBjAHQASQBPACAAaQBmACAA
YQB2AGEAaQBsAGEAYgBsAGUADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBMAE8AQQBEAF8A
TQBPAEQARQApAA0ACgAtAGwAegBtACwAIAAgAC0ALQBsAGEAegB5AC0AbQBvAGQAZQAgAE0ATwBE
AEUAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG8AbgAtAGQAZQBtAGEAbgBkACAA
cgBlAGEAZABpAG4AZwAgAG8AZgAgAGMAZQByAHQAYQBpAG4AIAB0AGUAbgBzAG8AcgBzACwAIABm
AG8AcgAgAGUAeABhAG0AcABsAGUAIABwAGUAcgAtAGwAYQB5AGUAcgAgAGUAbQBiAGUAZABkAGkA
bgBnAHMADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABkAGUAZgBhAHUAbAB0ADoAIABhAHUA
dABvACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAALQAgAG8AbgA6ACAAcgBlAGEAZAAgAHQA
aABlACAAcgBvAHcAcwAgAG8AZgAgAHMAdQBjAGgAIAB0AGUAbgBzAG8AcgBzACAAZgByAG8AbQAg
AGQAaQBzAGsAIABvAG4AIABkAGUAbQBhAG4AZAAgAGkAbgBzAHQAZQBhAGQAIABvAGYADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAawBlAGUAcABpAG4AZwAgAHQAaABlAG0AIAByAGUAcwBpAGQA
ZQBuAHQAIAAoAHIAZQBxAHUAaQByAGUAcwAgAG0AbQBhAHAAKQANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAtACAAYQB1AHQAbwA6ACAAbwBuACwAIABiAHUAdAAgAG8AbgBsAHkAIABmAG8AcgAg
AHQAZQBuAHMAbwByAHMAIABsAGEAcgBnAGUAcgAgAHQAaABhAG4AIAA0ACAARwBpAEIADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAALQAgAG8AZgBmADoAIABhAGwAdwBhAHkAcwAgAGsAZQBlAHAA
IAB0AGgAZQBtACAAcgBlAHMAaQBkAGUAbgB0AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgA
ZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ATABBAFoAWQBfAE0ATwBEAEUAKQANAAoALQAt
AG4AdQBtAGEAIABUAFkAUABFACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIABhAHQAdABlAG0AcAB0ACAAbwBwAHQAaQBtAGkAegBhAHQAaQBv
AG4AcwAgAHQAaABhAHQAIABoAGUAbABwACAAbwBuACAAcwBvAG0AZQAgAE4AVQBNAEEAIABzAHkA
cwB0AGUAbQBzAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC0AIABkAGkAcwB0AHIAaQBiAHUA
dABlADoAIABzAHAAcgBlAGEAZAAgAGUAeABlAGMAdQB0AGkAbwBuACAAZQB2AGUAbgBsAHkAIABv
AHYAZQByACAAYQBsAGwAIABuAG8AZABlAHMADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAALQAg
AGkAcwBvAGwAYQB0AGUAOgAgAG8AbgBsAHkAIABzAHAAYQB3AG4AIAB0AGgAcgBlAGEAZABzACAA
bwBuACAAQwBQAFUAcwAgAG8AbgAgAHQAaABlACAAbgBvAGQAZQAgAHQAaABhAHQAIABlAHgAZQBj
AHUAdABpAG8AbgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABzAHQAYQByAHQAZQBkACAAbwBu
AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC0AIABuAHUAbQBhAGMAdABsADoAIAB1AHMAZQAg
AHQAaABlACAAQwBQAFUAIABtAGEAcAAgAHAAcgBvAHYAaQBkAGUAZAAgAGIAeQAgAG4AdQBtAGEA
YwB0AGwADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAaQBmACAAcgB1AG4AIAB3AGkAdABoAG8A
dQB0ACAAdABoAGkAcwAgAHAAcgBlAHYAaQBvAHUAcwBsAHkALAAgAGkAdAAgAGkAcwAgAHIAZQBj
AG8AbQBtAGUAbgBkAGUAZAAgAHQAbwAgAGQAcgBvAHAAIAB0AGgAZQAgAHMAeQBzAHQAZQBtAA0A
CgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHAAYQBnAGUAIABjAGEAYwBoAGUAIABiAGUAZgBvAHIA
ZQAgAHUAcwBpAG4AZwAgAHQAaABpAHMADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBlAGUA
IABoAHQAdABwAHMAOgAvAC8AZwBpAHQAaAB1AGIALgBjAG8AbQAvAGcAZwBtAGwALQBvAHIAZwAv
AGwAbABhAG0AYQAuAGMAcABwAC8AaQBzAHMAdQBlAHMALwAxADQAMwA3AA0ACgAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ATgBVAE0AQQApAA0A
CgAtAGQAZQB2ACwAIAAgAC0ALQBkAGUAdgBpAGMAZQAgADwAZABlAHYAMQAsAGQAZQB2ADIALAAu
AC4APgAgACAAIAAgACAAIAAgACAAIAAgAGMAbwBtAG0AYQAtAHMAZQBwAGEAcgBhAHQAZQBkACAA
bABpAHMAdAAgAG8AZgAgAGQAZQB2AGkAYwBlAHMAIAB0AG8AIAB1AHMAZQAgAGYAbwByACAAbwBm
AGYAbABvAGEAZABpAG4AZwAgACgAbgBvAG4AZQAgAD0AIABkAG8AbgAnAHQADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAbwBmAGYAbABvAGEAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AHUAcwBlACAALQAtAGwAaQBzAHQALQBkAGUAdgBpAGMAZQBzACAAdABvACAAcwBlAGUAIABhACAA
bABpAHMAdAAgAG8AZgAgAGEAdgBhAGkAbABhAGIAbABlACAAZABlAHYAaQBjAGUAcwANAAoAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEQARQBW
AEkAQwBFACkADQAKAC0ALQBsAGkAcwB0AC0AZABlAHYAaQBjAGUAcwAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcAByAGkAbgB0ACAAbABpAHMAdAAg
AG8AZgAgAGEAdgBhAGkAbABhAGIAbABlACAAZABlAHYAaQBjAGUAcwAgAGEAbgBkACAAZQB4AGkA
dAANAAoALQBvAHQALAAgACAAIAAtAC0AbwB2AGUAcgByAGkAZABlAC0AdABlAG4AcwBvAHIAIAA8
AHQAZQBuAHMAbwByACAAbgBhAG0AZQAgAHAAYQB0AHQAZQByAG4APgA9ADwAYgB1AGYAZgBlAHIA
IAB0AHkAcABlAD4ALAAuAC4ALgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABvAHYAZQByAHIA
aQBkAGUAIAB0AGUAbgBzAG8AcgAgAGIAdQBmAGYAZQByACAAdAB5AHAAZQANAAoAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAE8AVgBFAFIAUgBJ
AEQARQBfAFQARQBOAFMATwBSACkADQAKAC0AYwBtAG8AZQAsACAALQAtAGMAcAB1AC0AbQBvAGUA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAawBlAGUAcAAg
AGEAbABsACAATQBpAHgAdAB1AHIAZQAgAG8AZgAgAEUAeABwAGUAcgB0AHMAIAAoAE0AbwBFACkA
IAB3AGUAaQBnAGgAdABzACAAaQBuACAAdABoAGUAIABDAFAAVQANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEMAUABVAF8ATQBPAEUAKQAN
AAoALQBuAGMAbQBvAGUALAAgAC0ALQBuAC0AYwBwAHUALQBtAG8AZQAgAE4AIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIABrAGUAZQBwACAAdABoAGUAIABNAGkAeAB0AHUAcgBl
ACAAbwBmACAARQB4AHAAZQByAHQAcwAgACgATQBvAEUAKQAgAHcAZQBpAGcAaAB0AHMAIABvAGYA
IAB0AGgAZQAgAGYAaQByAHMAdAAgAE4AIABsAGEAeQBlAHIAcwAgAGkAbgAgAHQAaABlAA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAEMAUABVAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgA
ZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ATgBfAEMAUABVAF8ATQBPAEUAKQANAAoALQAt
AG0AbwBlAC0AYwBhAGMAaABlAC0AbQBpAGIAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIABHAFAAVQAgAGMAYQBjAGgAZQAgAHMAaQB6AGUAIABpAG4AIABN
AGkAQgAgAGYAbwByACAAdABoAGUAIABNAG8ARQAgAGUAeABwAGUAcgB0AHMAIABrAGUAcAB0ACAA
aQBuACAAdABoAGUAIABDAFAAVQAuACAAdwBpAHQAaAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IABtAHUAbAB0AGkAcABsAGUAIABHAFAAVQBzACwAIABpAHQAIABpAHMAIABzAHAAbABpAHQAIABh
AG0AbwBuAGcAIAB0AGgAZQBtACAAbABpAGsAZQAgAHQAaABlACAAbABhAHkAZQByAHMAIAAoAC0A
LQB0AGUAbgBzAG8AcgAtAHMAcABsAGkAdAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgA
ZABlAGYAYQB1AGwAdAA6ACAAMAAsACAAZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBNAE8ARQBfAEMAQQBD
AEgARQBfAE0ASQBCACkADQAKAC0AbgBjAGYAZgBuACwAIAAtAC0AbgAtAGMAcAB1AC0AZgBmAG4A
IABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAawBlAGUAcAAgAHQAaABl
ACAAZABlAG4AcwBlACAARgBGAE4AIAB3AGUAaQBnAGgAdABzACAAbwBmACAAdABoAGUAIABmAGkA
cgBzAHQAIABOACAAbABhAHkAZQByAHMAIABpAG4AIAB0AGgAZQAgAEMAUABVAA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACgAZABlAG4AcwBlACAAbQBvAGQAZQBsAHMAOwAgAGYAbwByACAATQBv
AEUAIABlAHgAcABlAHIAdAAgAHcAZQBpAGcAaAB0AHMAIAB1AHMAZQAgAC0ALQBuAC0AYwBwAHUA
LQBtAG8AZQApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0A
QQBfAEEAUgBHAF8ATgBfAEMAUABVAF8ARgBGAE4AKQANAAoALQBuAGcAbAAsACAAIAAtAC0AZwBw
AHUALQBsAGEAeQBlAHIAcwAsACAALQAtAG4ALQBnAHAAdQAtAGwAYQB5AGUAcgBzACAATgAgACAA
IABtAGEAeAAuACAAbgB1AG0AYgBlAHIAIABvAGYAIABsAGEAeQBlAHIAcwAgAHQAbwAgAHMAdABv
AHIAZQAgAGkAbgAgAFYAUgBBAE0ALAAgAGUAaQB0AGgAZQByACAAYQBuACAAZQB4AGEAYwB0ACAA
bgB1AG0AYgBlAHIALAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAnAGEAdQB0AG8AJwAsACAA
bwByACAAJwBhAGwAbAAnACAAKABkAGUAZgBhAHUAbAB0ADoAIABhAHUAdABvACkADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBOAF8ARwBQ
AFUAXwBMAEEAWQBFAFIAUwApAA0ACgAtAHMAbQAsACAAIAAgAC0ALQBzAHAAbABpAHQALQBtAG8A
ZABlACAAewBuAG8AbgBlACwAbABhAHkAZQByACwAcgBvAHcALAB0AGUAbgBzAG8AcgB9AA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAGgAbwB3ACAAdABvACAAcwBwAGwAaQB0ACAAdABoAGUAIABt
AG8AZABlAGwAIABhAGMAcgBvAHMAcwAgAG0AdQBsAHQAaQBwAGwAZQAgAEcAUABVAHMALAAgAG8A
bgBlACAAbwBmADoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAALQAgAG4AbwBuAGUAOgAgAHUA
cwBlACAAbwBuAGUAIABHAFAAVQAgAG8AbgBsAHkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
LQAgAGwAYQB5AGUAcgAgACgAZABlAGYAYQB1AGwAdAApADoAIABzAHAAbABpAHQAIABsAGEAeQBl
AHIAcwAgAGEAbgBkACAASwBWACAAYQBjAHIAbwBzAHMAIABHAFAAVQBzACAAKABwAGkAcABlAGwA
aQBuAGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC0AIAByAG8AdwA6ACAAcwBwAGwA
aQB0ACAAdwBlAGkAZwBoAHQAIABhAGMAcgBvAHMAcwAgAEcAUABVAHMAIABiAHkAIAByAG8AdwBz
ACAAKABwAGEAcgBhAGwAbABlAGwAaQB6AGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AC0AIAB0AGUAbgBzAG8AcgA6ACAAcwBwAGwAaQB0ACAAdwBlAGkAZwBoAHQAcwAgAGEAbgBkACAA
SwBWACAAYQBjAHIAbwBzAHMAIABHAFAAVQBzACAAKABwAGEAcgBhAGwAbABlAGwAaQB6AGUAZAAs
AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAEUAWABQAEUAUgBJAE0ARQBOAFQAQQBMACkADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBT
AFAATABJAFQAXwBNAE8ARABFACkADQAKAC0AdABzACwAIAAgACAALQAtAHQAZQBuAHMAbwByAC0A
cwBwAGwAaQB0ACAATgAwACwATgAxACwATgAyACwALgAuAC4AIAAgACAAIAAgACAAZgByAGEAYwB0
AGkAbwBuACAAbwBmACAAdABoAGUAIABtAG8AZABlAGwAIAB0AG8AIABvAGYAZgBsAG8AYQBkACAA
dABvACAAZQBhAGMAaAAgAEcAUABVACwAIABjAG8AbQBtAGEALQBzAGUAcABhAHIAYQB0AGUAZAAg
AGwAaQBzAHQAIABvAGYADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcAByAG8AcABvAHIAdABp
AG8AbgBzACwAIABlAC4AZwAuACAAMwAsADEADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABl
AG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBUAEUATgBTAE8AUgBfAFMAUABMAEkAVAApAA0A
CgAtAG0AZwAsACAAIAAgAC0ALQBtAGEAaQBuAC0AZwBwAHUAIABJAE4ARABFAFgAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHQAaABlACAARwBQAFUAIAB0AG8AIAB1AHMAZQAgAGYA
bwByACAAdABoAGUAIABtAG8AZABlAGwAIAAoAHcAaQB0AGgAIABzAHAAbABpAHQALQBtAG8AZABl
ACAAPQAgAG4AbwBuAGUAKQAsACAAbwByACAAZgBvAHIADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAaQBuAHQAZQByAG0AZQBkAGkAYQB0AGUAIAByAGUAcwB1AGwAdABzACAAYQBuAGQAIABLAFYA
IAAoAHcAaQB0AGgAIABzAHAAbABpAHQALQBtAG8AZABlACAAPQAgAHIAbwB3ACkAIAAoAGQAZQBm
AGEAdQBsAHQAOgAgADAAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABM
AEwAQQBNAEEAXwBBAFIARwBfAE0AQQBJAE4AXwBHAFAAVQApAA0ACgAtAGYAaQB0ACwAIAAgAC0A
LQBmAGkAdAAgAFsAbwBuAHwAbwBmAGYAXQAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgAHcAaABlAHQAaABlAHIAIAB0AG8AIABhAGQAagB1AHMAdAAgAHUAbgBzAGUAdAAgAGEA
cgBnAHUAbQBlAG4AdABzACAAdABvACAAZgBpAHQAIABpAG4AIABkAGUAdgBpAGMAZQAgAG0AZQBt
AG8AcgB5ACAAKAAnAG8AbgAnACAAbwByAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACcAbwBm
AGYAJwAsACAAZABlAGYAYQB1AGwAdAA6ACAAJwBvAG4AJwApAA0ACgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ARgBJAFQAKQANAAoALQBmAGkA
dAB0ACwAIAAtAC0AZgBpAHQALQB0AGEAcgBnAGUAdAAgAE0AaQBCADAALABNAGkAQgAxACwATQBp
AEIAMgAsAC4ALgAuAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHQAYQByAGcAZQB0ACAAbQBh
AHIAZwBpAG4AIABwAGUAcgAgAGQAZQB2AGkAYwBlACAAZgBvAHIAIAAtAC0AZgBpAHQALAAgAGMA
bwBtAG0AYQAtAHMAZQBwAGEAcgBhAHQAZQBkACAAbABpAHMAdAAgAG8AZgAgAHYAYQBsAHUAZQBz
ACwADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBpAG4AZwBsAGUAIAB2AGEAbAB1AGUAIABp
AHMAIABiAHIAbwBhAGQAYwBhAHMAdAAgAGEAYwByAG8AcwBzACAAYQBsAGwAIABkAGUAdgBpAGMA
ZQBzACwAIABkAGUAZgBhAHUAbAB0ADoAIAAxADAAMgA0AA0ACgAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ARgBJAFQAXwBUAEEAUgBHAEUAVAAp
AA0ACgAtAGYAaQB0AGMALAAgAC0ALQBmAGkAdAAtAGMAdAB4ACAATgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG0AaQBuAGkAbQB1AG0AIABjAHQAeAAgAHMAaQB6
AGUAIAB0AGgAYQB0ACAAYwBhAG4AIABiAGUAIABzAGUAdAAgAGIAeQAgAC0ALQBmAGkAdAAgAG8A
cAB0AGkAbwBuACwAIABkAGUAZgBhAHUAbAB0ADoAIAA0ADAAOQA2AA0ACgAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ARgBJAFQAXwBDAFQAWAAp
AA0ACgAtAC0AYwBoAGUAYwBrAC0AdABlAG4AcwBvAHIAcwAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGMAaABlAGMAawAgAG0AbwBkAGUAbAAgAHQAZQBu
AHMAbwByACAAZABhAHQAYQAgAGYAbwByACAAaQBuAHYAYQBsAGkAZAAgAHYAYQBsAHUAZQBzACAA
KABkAGUAZgBhAHUAbAB0ADoAIABmAGEAbABzAGUAKQANAAoALQAtAG8AdgBlAHIAcgBpAGQAZQAt
AGsAdgAgAEsARQBZAD0AVABZAFAARQA6AFYAQQBMAFUARQAsAC4ALgAuACAAIAAgACAAIAAgACAA
IABhAGQAdgBhAG4AYwBlAGQAIABvAHAAdABpAG8AbgAgAHQAbwAgAG8AdgBlAHIAcgBpAGQAZQAg
AG0AbwBkAGUAbAAgAG0AZQB0AGEAZABhAHQAYQAgAGIAeQAgAGsAZQB5AC4AIAB0AG8AIABzAHAA
ZQBjAGkAZgB5ACAAbQB1AGwAdABpAHAAbABlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG8A
dgBlAHIAcgBpAGQAZQBzACwAIABlAGkAdABoAGUAcgAgAHUAcwBlACAAYwBvAG0AbQBhAC0AcwBl
AHAAYQByAGEAdABlAGQAIAB2AGEAbAB1AGUAcwAuAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AHQAeQBwAGUAcwA6ACAAaQBuAHQALAAgAGYAbABvAGEAdAAsACAAYgBvAG8AbAAsACAAcwB0AHIA
LgAgAGUAeABhAG0AcABsAGUAOgAgAC0ALQBvAHYAZQByAHIAaQBkAGUALQBrAHYADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAdABvAGsAZQBuAGkAegBlAHIALgBnAGcAbQBsAC4AYQBkAGQAXwBi
AG8AcwBfAHQAbwBrAGUAbgA9AGIAbwBvAGwAOgBmAGEAbABzAGUALAB0AG8AawBlAG4AaQB6AGUA
cgAuAGcAZwBtAGwALgBhAGQAZABfAGUAbwBzAF8AdABvAGsAZQBuAD0AYgBvAG8AbAA6AGYAYQBs
AHMAZQANAAoALQAtAG8AcAAtAG8AZgBmAGwAbwBhAGQALAAgAC0ALQBuAG8ALQBvAHAALQBvAGYA
ZgBsAG8AYQBkACAAIAAgACAAIAAgACAAIAAgACAAIAB3AGgAZQB0AGgAZQByACAAdABvACAAbwBm
AGYAbABvAGEAZAAgAGgAbwBzAHQAIAB0AGUAbgBzAG8AcgAgAG8AcABlAHIAYQB0AGkAbwBuAHMA
IAB0AG8AIABkAGUAdgBpAGMAZQAgACgAZABlAGYAYQB1AGwAdAA6ACAAdAByAHUAZQApAA0ACgAt
AC0AbABvAHIAYQAgAEYATgBBAE0ARQAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAHAAYQB0AGgAIAB0AG8AIABMAG8AUgBBACAAYQBkAGEAcAB0
AGUAcgAgACgAdQBzAGUAIABjAG8AbQBtAGEALQBzAGUAcABhAHIAYQB0AGUAZAAgAHYAYQBsAHUA
ZQBzACAAdABvACAAbABvAGEAZAAgAG0AdQBsAHQAaQBwAGwAZQANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABhAGQAYQBwAHQAZQByAHMAKQANAAoALQAtAGwAbwByAGEALQBzAGMAYQBsAGUAZAAg
AEYATgBBAE0ARQA6AFMAQwBBAEwARQAsAC4ALgAuACAAIAAgACAAIAAgACAAIAAgACAAIABwAGEA
dABoACAAdABvACAATABvAFIAQQAgAGEAZABhAHAAdABlAHIAIAB3AGkAdABoACAAdQBzAGUAcgAg
AGQAZQBmAGkAbgBlAGQAIABzAGMAYQBsAGkAbgBnACAAKABmAG8AcgBtAGEAdAA6AA0ACgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgAEYATgBBAE0ARQA6AFMAQwBBAEwARQAsAC4ALgAuACkADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAbgBvAHQAZQA6ACAAdQBzAGUAIABjAG8AbQBtAGEALQBzAGUA
cABhAHIAYQB0AGUAZAAgAHYAYQBsAHUAZQBzAA0ACgAtAC0AYwBvAG4AdAByAG8AbAAtAHYAZQBj
AHQAbwByACAARgBOAEEATQBFACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGEA
ZABkACAAYQAgAGMAbwBuAHQAcgBvAGwAIAB2AGUAYwB0AG8AcgANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABuAG8AdABlADoAIAB1AHMAZQAgAGMAbwBtAG0AYQAtAHMAZQBwAGEAcgBhAHQAZQBk
ACAAdgBhAGwAdQBlAHMAIAB0AG8AIABhAGQAZAAgAG0AdQBsAHQAaQBwAGwAZQAgAGMAbwBuAHQA
cgBvAGwAIAB2AGUAYwB0AG8AcgBzAA0ACgAtAC0AYwBvAG4AdAByAG8AbAAtAHYAZQBjAHQAbwBy
AC0AcwBjAGEAbABlAGQAIABGAE4AQQBNAEUAOgBTAEMAQQBMAEUALAAuAC4ALgANAAoAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIABhAGQAZAAgAGEAIABjAG8AbgB0AHIAbwBsACAAdgBlAGMAdABvAHIA
IAB3AGkAdABoACAAdQBzAGUAcgAgAGQAZQBmAGkAbgBlAGQAIABzAGMAYQBsAGkAbgBnACAAUwBD
AEEATABFAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4AbwB0AGUAOgAgAHUAcwBlACAAYwBv
AG0AbQBhAC0AcwBlAHAAYQByAGEAdABlAGQAIAB2AGEAbAB1AGUAcwAgACgAZgBvAHIAbQBhAHQA
OgAgAEYATgBBAE0ARQA6AFMAQwBBAEwARQAsAC4ALgAuACkADQAKAC0ALQBjAG8AbgB0AHIAbwBs
AC0AdgBlAGMAdABvAHIALQBsAGEAeQBlAHIALQByAGEAbgBnAGUAIABTAFQAQQBSAFQAIABFAE4A
RAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABsAGEAeQBlAHIAIAByAGEAbgBnAGUAIAB0AG8A
IABhAHAAcABsAHkAIAB0AGgAZQAgAGMAbwBuAHQAcgBvAGwAIAB2AGUAYwB0AG8AcgAoAHMAKQAg
AHQAbwAsACAAcwB0AGEAcgB0ACAAYQBuAGQAIABlAG4AZAAgAGkAbgBjAGwAdQBzAGkAdgBlAA0A
CgAtAG0ALAAgACAAIAAgAC0ALQBtAG8AZABlAGwAIABGAE4AQQBNAEUAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG0AbwBkAGUAbAAgAHAAYQB0AGgAIAB0AG8AIABsAG8A
YQBkAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEA
UgBHAF8ATQBPAEQARQBMACkADQAKAC0AbQB1ACwAIAAgACAALQAtAG0AbwBkAGUAbAAtAHUAcgBs
ACAATQBPAEQARQBMAF8AVQBSAEwAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbQBvAGQAZQBsACAA
ZABvAHcAbgBsAG8AYQBkACAAdQByAGwAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAHUAbgB1AHMAZQBk
ACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBS
AEcAXwBNAE8ARABFAEwAXwBVAFIATAApAA0ACgAtAGQAcgAsACAAIAAgAC0ALQBkAG8AYwBrAGUA
cgAtAHIAZQBwAG8AIABbADwAcgBlAHAAbwA+AC8AXQA8AG0AbwBkAGUAbAA+AFsAOgBxAHUAYQBu
AHQAXQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABEAG8AYwBrAGUAcgAgAEgAdQBiACAAbQBv
AGQAZQBsACAAcgBlAHAAbwBzAGkAdABvAHIAeQAuACAAcgBlAHAAbwAgAGkAcwAgAG8AcAB0AGkA
bwBuAGEAbAAsACAAZABlAGYAYQB1AGwAdAAgAHQAbwAgAGEAaQAvAC4AIABxAHUAYQBuAHQADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAaQBzACAAbwBwAHQAaQBvAG4AYQBsACwAIABkAGUAZgBh
AHUAbAB0ACAAdABvACAAOgBsAGEAdABlAHMAdAAuAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AGUAeABhAG0AcABsAGUAOgAgAGcAZQBtAG0AYQAzAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACgAZABlAGYAYQB1AGwAdAA6ACAAdQBuAHUAcwBlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEQATwBDAEsARQBSAF8AUgBFAFAA
TwApAA0ACgAtAGgAZgAsACAAIAAgAC0AaABmAHIALAAgAC0ALQBoAGYALQByAGUAcABvACAAPAB1
AHMAZQByAD4ALwA8AG0AbwBkAGUAbAA+AFsAOgBxAHUAYQBuAHQAXQANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABIAHUAZwBnAGkAbgBnACAARgBhAGMAZQAgAG0AbwBkAGUAbAAgAHIAZQBwAG8A
cwBpAHQAbwByAHkAOwAgAHEAdQBhAG4AdAAgAGkAcwAgAG8AcAB0AGkAbwBuAGEAbAAsACAAYwBh
AHMAZQAtAGkAbgBzAGUAbgBzAGkAdABpAHYAZQAsAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AGQAZQBmAGEAdQBsAHQAIAB0AG8AIABRADQAXwBLAF8ATQAsACAAbwByACAAZgBhAGwAbABzACAA
YgBhAGMAawAgAHQAbwAgAHQAaABlACAAZgBpAHIAcwB0ACAAZgBpAGwAZQAgAGkAbgAgAHQAaABl
ACAAcgBlAHAAbwAgAGkAZgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABRADQAXwBLAF8ATQAg
AGQAbwBlAHMAbgAnAHQAIABlAHgAaQBzAHQALgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABt
AG0AcAByAG8AagAgAGkAcwAgAGEAbABzAG8AIABkAG8AdwBuAGwAbwBhAGQAZQBkACAAYQB1AHQA
bwBtAGEAdABpAGMAYQBsAGwAeQAgAGkAZgAgAGEAdgBhAGkAbABhAGIAbABlAC4AIAB0AG8AIABk
AGkAcwBhAGIAbABlACwAIABhAGQAZAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAtAC0AbgBv
AC0AbQBtAHAAcgBvAGoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAZQB4AGEAbQBwAGwAZQA6
ACAAZwBnAG0AbAAtAG8AcgBnAC8ARwBMAE0ALQA0AC4ANwAtAEYAbABhAHMAaAAtAEcARwBVAEYA
OgBRADQAXwBLAF8ATQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGQAZQBmAGEAdQBsAHQA
OgAgAHUAbgB1AHMAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAA
TABMAEEATQBBAF8AQQBSAEcAXwBIAEYAXwBSAEUAUABPACkADQAKAC0AaABmAGYALAAgACAALQAt
AGgAZgAtAGYAaQBsAGUAIABGAEkATABFACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAASAB1AGcAZwBpAG4AZwAgAEYAYQBjAGUAIABtAG8AZABlAGwAIABmAGkAbABlAC4AIABJ
AGYAIABzAHAAZQBjAGkAZgBpAGUAZAAsACAAaQB0ACAAdwBpAGwAbAAgAG8AdgBlAHIAcgBpAGQA
ZQAgAHQAaABlACAAcQB1AGEAbgB0ACAAaQBuAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC0A
LQBoAGYALQByAGUAcABvACAAKABkAGUAZgBhAHUAbAB0ADoAIAB1AG4AdQBzAGUAZAApAA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ASABG
AF8ARgBJAEwARQApAA0ACgAtAGgAZgB0ACwAIAAgAC0ALQBoAGYALQB0AG8AawBlAG4AIABUAE8A
SwBFAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAEgAdQBnAGcAaQBuAGcAIABG
AGEAYwBlACAAYQBjAGMAZQBzAHMAIAB0AG8AawBlAG4AIAAoAGQAZQBmAGEAdQBsAHQAOgAgAHYA
YQBsAHUAZQAgAGYAcgBvAG0AIABIAEYAXwBUAE8ASwBFAE4AIABlAG4AdgBpAHIAbwBuAG0AZQBu
AHQADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdgBhAHIAaQBhAGIAbABlACkADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAASABGAF8AVABPAEsARQBOACkADQAKAC0ALQBs
AG8AZwAtAGQAaQBzAGEAYgBsAGUAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAATABvAGcAIABkAGkAcwBhAGIAbABlAA0ACgAtAC0AbABvAGcALQBm
AGkAbABlACAARgBOAEEATQBFACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgAEwAbwBnACAAdABvACAAZgBpAGwAZQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEwATwBHAF8ARgBJAEwARQApAA0ACgAt
AC0AbABvAGcALQBqAHMAbwBuAGwALAAgAC0ALQBuAG8ALQBsAG8AZwAtAGoAcwBvAG4AbAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAEwAbwBnACAAYQBzACAASgBTAE8ATgBMACAAKABvAG4AZQAg
AEoAUwBPAE4AIABvAGIAagBlAGMAdAAgAHAAZQByACAAbABpAG4AZQApACAAdABvACAAcwB0AGQA
bwB1AHQALAAgAHQAaABpAHMAIABhAGwAcwBvACAAZABpAHMAYQBiAGwAZQBzAA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAGMAbwBsAG8AcgBlAGQAIABsAG8AZwBnAGkAbgBnACAAKABkAGUAZgBh
AHUAbAB0ADoAIABkAGkAcwBhAGIAbABlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAo
AGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEwATwBHAF8ASgBTAE8ATgBMACkADQAKAC0A
LQBsAG8AZwAtAGMAbwBsAG8AcgBzACAAWwBvAG4AfABvAGYAZgB8AGEAdQB0AG8AXQAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAUwBlAHQAIABjAG8AbABvAHIAZQBkACAAbABvAGcAZwBpAG4A
ZwAgACgAJwBvAG4AJwAsACAAJwBvAGYAZgAnACwAIABvAHIAIAAnAGEAdQB0AG8AJwAsACAAZABl
AGYAYQB1AGwAdAA6ACAAJwBhAHUAdABvACcAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAn
AGEAdQB0AG8AJwAgAGUAbgBhAGIAbABlAHMAIABjAG8AbABvAHIAcwAgAHcAaABlAG4AIABvAHUA
dABwAHUAdAAgAGkAcwAgAHQAbwAgAGEAIAB0AGUAcgBtAGkAbgBhAGwADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBMAE8ARwBfAEMATwBM
AE8AUgBTACkADQAKAC0AdgAsACAAIAAgACAALQAtAHYAZQByAGIAbwBzAGUALAAgAC0ALQBsAG8A
ZwAtAHYAZQByAGIAbwBzAGUAIAAgACAAIAAgACAAIAAgACAAUwBlAHQAIAB2AGUAcgBiAG8AcwBp
AHQAeQAgAGwAZQB2AGUAbAAgAHQAbwAgAGkAbgBmAGkAbgBpAHQAeQAgACgAaQAuAGUALgAgAGwA
bwBnACAAYQBsAGwAIABtAGUAcwBzAGEAZwBlAHMALAAgAHUAcwBlAGYAdQBsACAAZgBvAHIADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAZABlAGIAdQBnAGcAaQBuAGcAKQANAAoALQAtAG8AZgBm
AGwAaQBuAGUAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIABPAGYAZgBsAGkAbgBlACAAbQBvAGQAZQA6ACAAZgBvAHIAYwBlAHMAIAB1
AHMAZQAgAG8AZgAgAGMAYQBjAGgAZQAsACAAcAByAGUAdgBlAG4AdABzACAAbgBlAHQAdwBvAHIA
awAgAGEAYwBjAGUAcwBzAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwA
TABBAE0AQQBfAEEAUgBHAF8ATwBGAEYATABJAE4ARQApAA0ACgAtAGwAdgAsACAAIAAgAC0ALQB2
AGUAcgBiAG8AcwBpAHQAeQAsACAALQAtAGwAbwBnAC0AdgBlAHIAYgBvAHMAaQB0AHkAIABOACAA
IAAgAFMAZQB0ACAAdABoAGUAIAB2AGUAcgBiAG8AcwBpAHQAeQAgAHQAaAByAGUAcwBoAG8AbABk
AC4AIABNAGUAcwBzAGEAZwBlAHMAIAB3AGkAdABoACAAYQAgAGgAaQBnAGgAZQByACAAdgBlAHIA
YgBvAHMAaQB0AHkAIAB3AGkAbABsACAAYgBlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGkA
ZwBuAG8AcgBlAGQALgAgAFYAYQBsAHUAZQBzADoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAtACAAMAA6ACAAZwBlAG4AZQByAGkAYwAgAG8AdQB0AHAAdQB0AA0ACgAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAALQAgADEAOgAgAGUAcgByAG8AcgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAC0AIAAyADoAIAB3AGEAcgBuAGkAbgBnAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
LQAgADMAOgAgAGkAbgBmAG8ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAtACAANAA6ACAA
dAByAGEAYwBlACAAKABtAG8AcgBlACAAaQBuAGYAbwApAA0ACgAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAALQAgADUAOgAgAGQAZQBiAHUAZwANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGQA
ZQBmAGEAdQBsAHQAOgAgADMAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAANAAoAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEwATwBHAF8A
VgBFAFIAQgBPAFMASQBUAFkAKQANAAoALQAtAGwAbwBnAC0AcAByAGUAZgBpAHgALAAgAC0ALQBu
AG8ALQBsAG8AZwAtAHAAcgBlAGYAaQB4ACAAIAAgACAAIAAgACAAIAAgACAAIABFAG4AYQBiAGwA
ZQAgAHAAcgBlAGYAaQB4ACAAaQBuACAAbABvAGcAIABtAGUAcwBzAGEAZwBlAHMADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBMAE8ARwBf
AFAAUgBFAEYASQBYACkADQAKAC0ALQBsAG8AZwAtAHQAaQBtAGUAcwB0AGEAbQBwAHMALAAgAC0A
LQBuAG8ALQBsAG8AZwAtAHQAaQBtAGUAcwB0AGEAbQBwAHMAIAAgACAARQBuAGEAYgBsAGUAIAB0
AGkAbQBlAHMAdABhAG0AcABzACAAaQBuACAAbABvAGcAIABtAGUAcwBzAGEAZwBlAHMADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBMAE8A
RwBfAFQASQBNAEUAUwBUAEEATQBQAFMAKQANAAoALQAtAHMAcABlAGMALQBkAHIAYQBmAHQALQB0
AHkAcABlAC0AawAsACAALQBjAHQAawBkACwAIAAtAC0AYwBhAGMAaABlAC0AdAB5AHAAZQAtAGsA
LQBkAHIAYQBmAHQAIABUAFkAUABFAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAEsAVgAgAGMA
YQBjAGgAZQAgAGQAYQB0AGEAIAB0AHkAcABlACAAZgBvAHIAIABLACAAZgBvAHIAIAB0AGgAZQAg
AGQAcgBhAGYAdAAgAG0AbwBkAGUAbAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABhAGwAbABv
AHcAZQBkACAAdgBhAGwAdQBlAHMAOgAgAGYAMwAyACwAIABmADEANgAsACAAYgBmADEANgAsACAA
cQA4AF8AMAAsACAAcQA0AF8AMAAsACAAcQA0AF8AMQAsACAAaQBxADQAXwBuAGwALAAgAHEANQBf
ADAALAAgAHEANQBfADEADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABkAGUAZgBhAHUAbAB0
ADoAIABmADEANgApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABB
AE0AQQBfAEEAUgBHAF8AUwBQAEUAQwBfAEQAUgBBAEYAVABfAEMAQQBDAEgARQBfAFQAWQBQAEUA
XwBLACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0AC0AdAB5AHAAZQAtAHYALAAgAC0AYwB0
AHYAZAAsACAALQAtAGMAYQBjAGgAZQAtAHQAeQBwAGUALQB2AC0AZAByAGEAZgB0ACAAVABZAFAA
RQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABLAFYAIABjAGEAYwBoAGUAIABkAGEAdABhACAA
dAB5AHAAZQAgAGYAbwByACAAVgAgAGYAbwByACAAdABoAGUAIABkAHIAYQBmAHQAIABtAG8AZABl
AGwADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAYQBsAGwAbwB3AGUAZAAgAHYAYQBsAHUAZQBz
ADoAIABmADMAMgAsACAAZgAxADYALAAgAGIAZgAxADYALAAgAHEAOABfADAALAAgAHEANABfADAA
LAAgAHEANABfADEALAAgAGkAcQA0AF8AbgBsACwAIABxADUAXwAwACwAIABxADUAXwAxAA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACgAZABlAGYAYQB1AGwAdAA6ACAAZgAxADYAKQANAAoAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFMAUABF
AEMAXwBEAFIAQQBGAFQAXwBDAEEAQwBIAEUAXwBUAFkAUABFAF8AVgApAA0ACgANAAoADQAKAC0A
LQAtAC0ALQAgAHMAYQBtAHAAbABpAG4AZwAgAHAAYQByAGEAbQBzACAALQAtAC0ALQAtAA0ACgAN
AAoALQAtAHMAYQBtAHAAbABlAHIAcwAgAFMAQQBNAFAATABFAFIAUwAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIABzAGEAbQBwAGwAZQByAHMAIAB0AGgAYQB0ACAAdwBp
AGwAbAAgAGIAZQAgAHUAcwBlAGQAIABmAG8AcgAgAGcAZQBuAGUAcgBhAHQAaQBvAG4AIABpAG4A
IAB0AGgAZQAgAG8AcgBkAGUAcgAsACAAcwBlAHAAYQByAGEAdABlAGQAIABiAHkADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAJwA7ACcADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABkAGUA
ZgBhAHUAbAB0ADoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcABlAG4AYQBsAHQAaQBlAHMA
OwBkAHIAeQA7AHQAbwBwAF8AbgBfAHMAaQBnAG0AYQA7AHQAbwBwAF8AawA7AHQAeQBwAF8AcAA7
AHQAbwBwAF8AcAA7AG0AaQBuAF8AcAA7AHgAdABjADsAdABlAG0AcABlAHIAYQB0AHUAcgBlACkA
DQAKAC0AcwAsACAAIAAgACAALQAtAHMAZQBlAGQAIABTAEUARQBEACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAUgBOAEcAIABzAGUAZQBkACAAKABkAGUAZgBhAHUA
bAB0ADoAIAAtADEALAAgAHUAcwBlACAAcgBhAG4AZABvAG0AIABzAGUAZQBkACAAZgBvAHIAIAAt
ADEAKQANAAoALQAtAHMAYQBtAHAAbABlAHIALQBzAGUAcQAsACAALQAtAHMAYQBtAHAAbABpAG4A
ZwAtAHMAZQBxACAAUwBFAFEAVQBFAE4AQwBFAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHMA
aQBtAHAAbABpAGYAaQBlAGQAIABzAGUAcQB1AGUAbgBjAGUAIABmAG8AcgAgAHMAYQBtAHAAbABl
AHIAcwAgAHQAaABhAHQAIAB3AGkAbABsACAAYgBlACAAdQBzAGUAZAAgACgAZABlAGYAYQB1AGwA
dAA6AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGUAZABzAGsAeQBwAG0AeAB0ACkADQAKAC0A
LQBpAGcAbgBvAHIAZQAtAGUAbwBzACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAaQBnAG4AbwByAGUAIABlAG4AZAAgAG8AZgAgAHMAdAByAGUA
YQBtACAAdABvAGsAZQBuACAAYQBuAGQAIABjAG8AbgB0AGkAbgB1AGUAIABnAGUAbgBlAHIAYQB0
AGkAbgBnACAAKABpAG0AcABsAGkAZQBzAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC0ALQBs
AG8AZwBpAHQALQBiAGkAYQBzACAARQBPAFMALQBpAG4AZgApAA0ACgAtAC0AdABlAG0AcAAsACAA
LQAtAHQAZQBtAHAAZQByAGEAdAB1AHIAZQAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgAHQAZQBtAHAAZQByAGEAdAB1AHIAZQAgACgAZABlAGYAYQB1AGwAdAA6ACAAMAAuADgA
MAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEA
UgBHAF8AVABFAE0AUABFAFIAQQBUAFUAUgBFACkADQAKAC0ALQB0AG8AcAAtAGsAIABOACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
dABvAHAALQBrACAAcwBhAG0AcABsAGkAbgBnACAAKABkAGUAZgBhAHUAbAB0ADoAIAA0ADAALAAg
ADAAIAA9ACAAZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABl
AG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBUAE8AUABfAEsAKQANAAoALQAtAHQAbwBwAC0A
cAAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAB0AG8AcAAtAHAAIABzAGEAbQBwAGwAaQBuAGcAIAAoAGQAZQBmAGEAdQBsAHQA
OgAgADAALgA5ADUALAAgADEALgAwACAAPQAgAGQAaQBzAGEAYgBsAGUAZAApAA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AVABPAFAAXwBQ
ACkADQAKAC0ALQBtAGkAbgAtAHAAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbQBpAG4ALQBwACAAcwBhAG0AcABsAGkAbgBn
ACAAKABkAGUAZgBhAHUAbAB0ADoAIAAwAC4AMAA1ACwAIAAwAC4AMAAgAD0AIABkAGkAcwBhAGIA
bABlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEA
XwBBAFIARwBfAE0ASQBOAF8AUAApAA0ACgAtAC0AdABvAHAALQBuAHMAaQBnAG0AYQAsACAALQAt
AHQAbwBwAC0AbgAtAHMAaQBnAG0AYQAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgAHQAbwBwAC0A
bgAtAHMAaQBnAG0AYQAgAHMAYQBtAHAAbABpAG4AZwAgACgAZABlAGYAYQB1AGwAdAA6ACAALQAx
AC4AMAAwACwAIAAtADEALgAwACAAPQAgAGQAaQBzAGEAYgBsAGUAZAApAA0ACgAtAC0AeAB0AGMA
LQBwAHIAbwBiAGEAYgBpAGwAaQB0AHkAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgAHgAdABjACAAcAByAG8AYgBhAGIAaQBsAGkAdAB5ACAAKABkAGUAZgBhAHUA
bAB0ADoAIAAwAC4AMAAwACwAIAAwAC4AMAAgAD0AIABkAGkAcwBhAGIAbABlAGQAKQANAAoALQAt
AHgAdABjAC0AdABoAHIAZQBzAGgAbwBsAGQAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAB4AHQAYwAgAHQAaAByAGUAcwBoAG8AbABkACAAKABkAGUAZgBh
AHUAbAB0ADoAIAAwAC4AMQAwACwAIAAxAC4AMAAgAD0AIABkAGkAcwBhAGIAbABlAGQAKQANAAoA
LQAtAHQAeQBwAGkAYwBhAGwALAAgAC0ALQB0AHkAcABpAGMAYQBsAC0AcAAgAE4AIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIABsAG8AYwBhAGwAbAB5ACAAdAB5AHAAaQBjAGEAbAAgAHMA
YQBtAHAAbABpAG4AZwAsACAAcABhAHIAYQBtAGUAdABlAHIAIABwACAAKABkAGUAZgBhAHUAbAB0
ADoAIAAxAC4AMAAwACwAIAAxAC4AMAAgAD0AIABkAGkAcwBhAGIAbABlAGQAKQANAAoALQAtAHIA
ZQBwAGUAYQB0AC0AbABhAHMAdAAtAG4AIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIABsAGEAcwB0ACAAbgAgAHQAbwBrAGUAbgBzACAAdABvACAAYwBvAG4A
cwBpAGQAZQByACAAZgBvAHIAIABwAGUAbgBhAGwAaQB6AGUAIAAoAGQAZQBmAGEAdQBsAHQAOgAg
ADYANAAsACAAMAAgAD0AIABkAGkAcwBhAGIAbABlAGQAKQANAAoALQAtAHIAZQBwAGUAYQB0AC0A
cABlAG4AYQBsAHQAeQAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIABwAGUAbgBhAGwAaQB6AGUAIAByAGUAcABlAGEAdAAgAHMAZQBxAHUAZQBuAGMAZQAgAG8A
ZgAgAHQAbwBrAGUAbgBzACAAKABkAGUAZgBhAHUAbAB0ADoAIAAxAC4AMAAwACwAIAAxAC4AMAAg
AD0AIABkAGkAcwBhAGIAbABlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2
ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFIARQBQAEUAQQBUAF8AUABFAE4AQQBMAFQAWQApAA0A
CgAtAC0AcAByAGUAcwBlAG4AYwBlAC0AcABlAG4AYQBsAHQAeQAgAE4AIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHIAZQBwAGUAYQB0ACAAYQBsAHAAaABhACAAcAByAGUA
cwBlAG4AYwBlACAAcABlAG4AYQBsAHQAeQAgACgAZABlAGYAYQB1AGwAdAA6ACAAMAAuADAAMAAs
ACAAMAAuADAAIAA9ACAAZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBQAFIARQBTAEUATgBDAEUAXwBQAEUA
TgBBAEwAVABZACkADQAKAC0ALQBmAHIAZQBxAHUAZQBuAGMAeQAtAHAAZQBuAGEAbAB0AHkAIABO
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcgBlAHAAZQBhAHQAIABhAGwA
cABoAGEAIABmAHIAZQBxAHUAZQBuAGMAeQAgAHAAZQBuAGEAbAB0AHkAIAAoAGQAZQBmAGEAdQBs
AHQAOgAgADAALgAwADAALAAgADAALgAwACAAPQAgAGQAaQBzAGEAYgBsAGUAZAApAA0ACgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ARgBSAEUA
UQBVAEUATgBDAFkAXwBQAEUATgBBAEwAVABZACkADQAKAC0ALQBkAHIAeQAtAG0AdQBsAHQAaQBw
AGwAaQBlAHIAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
cwBlAHQAIABEAFIAWQAgAHMAYQBtAHAAbABpAG4AZwAgAG0AdQBsAHQAaQBwAGwAaQBlAHIAIAAo
AGQAZQBmAGEAdQBsAHQAOgAgADAALgAwADAALAAgADAALgAwACAAPQAgAGQAaQBzAGEAYgBsAGUA
ZAApAA0ACgAtAC0AZAByAHkALQBiAGEAcwBlACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHMAZQB0ACAARABSAFkAIABzAGEAbQBwAGwA
aQBuAGcAIABiAGEAcwBlACAAdgBhAGwAdQBlACAAKABkAGUAZgBhAHUAbAB0ADoAIAAxAC4ANwA1
ACkADQAKAC0ALQBkAHIAeQAtAGEAbABsAG8AdwBlAGQALQBsAGUAbgBnAHQAaAAgAE4AIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBlAHQAIABhAGwAbABvAHcAZQBkACAAbABl
AG4AZwB0AGgAIABmAG8AcgAgAEQAUgBZACAAcwBhAG0AcABsAGkAbgBnACAAKABkAGUAZgBhAHUA
bAB0ADoAIAAyACkADQAKAC0ALQBkAHIAeQAtAHAAZQBuAGEAbAB0AHkALQBsAGEAcwB0AC0AbgAg
AE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBlAHQAIABEAFIAWQAgAHAA
ZQBuAGEAbAB0AHkAIABmAG8AcgAgAHQAaABlACAAbABhAHMAdAAgAG4AIAB0AG8AawBlAG4AcwAg
ACgAZABlAGYAYQB1AGwAdAA6ACAANgA0ACwAIAAwACAAPQAgAGQAaQBzAGEAYgBsAGUAKQANAAoA
LQAtAGQAcgB5AC0AcwBlAHEAdQBlAG4AYwBlAC0AYgByAGUAYQBrAGUAcgAgAFMAVABSAEkATgBH
ACAAIAAgACAAIAAgACAAIAAgACAAIABhAGQAZAAgAHMAZQBxAHUAZQBuAGMAZQAgAGIAcgBlAGEA
awBlAHIAIABmAG8AcgAgAEQAUgBZACAAcwBhAG0AcABsAGkAbgBnACwAIABjAGwAZQBhAHIAaQBu
AGcAIABvAHUAdAAgAGQAZQBmAGEAdQBsAHQAIABiAHIAZQBhAGsAZQByAHMADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAKAAnAFwAbgAnACwAIAAnADoAJwAsACAAJwAiACcALAAgACcAKgAnACkA
IABpAG4AIAB0AGgAZQAgAHAAcgBvAGMAZQBzAHMAOwAgAHUAcwBlACAAIgBuAG8AbgBlACIAIAB0
AG8AIABuAG8AdAAgAHUAcwBlACAAYQBuAHkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBl
AHEAdQBlAG4AYwBlACAAYgByAGUAYQBrAGUAcgBzAA0ACgAtAC0AYQBkAGEAcAB0AGkAdgBlAC0A
dABhAHIAZwBlAHQAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AGEAZABhAHAAdABpAHYAZQAtAHAAOgAgAHMAZQBsAGUAYwB0ACAAdABvAGsAZQBuAHMAIABuAGUA
YQByACAAdABoAGkAcwAgAHAAcgBvAGIAYQBiAGkAbABpAHQAeQAgACgAdgBhAGwAaQBkACAAcgBh
AG4AZwBlACAAMAAuADAAIAB0AG8ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAMQAuADAAOwAg
AG4AZQBnAGEAdABpAHYAZQAgAD0AIABkAGkAcwBhAGIAbABlAGQAKQAgACgAZABlAGYAYQB1AGwA
dAA6ACAALQAxAC4AMAAwACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAWwAoAG0AbwByAGUA
IABpAG4AZgBvACkAXQAoAGgAdAB0AHAAcwA6AC8ALwBnAGkAdABoAHUAYgAuAGMAbwBtAC8AZwBn
AG0AbAAtAG8AcgBnAC8AbABsAGEAbQBhAC4AYwBwAHAALwBwAHUAbABsAC8AMQA3ADkAMgA3ACkA
DQAKAC0ALQBhAGQAYQBwAHQAaQB2AGUALQBkAGUAYwBhAHkAIABOACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAYQBkAGEAcAB0AGkAdgBlAC0AcAA6ACAAZABlAGMA
YQB5ACAAcgBhAHQAZQAgAGYAbwByACAAdABhAHIAZwBlAHQAIABhAGQAYQBwAHQAYQB0AGkAbwBu
ACAAbwB2AGUAcgAgAHQAaQBtAGUALgAgAGwAbwB3AGUAcgAgAHYAYQBsAHUAZQBzAA0ACgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgAGEAcgBlACAAbQBvAHIAZQAgAHIAZQBhAGMAdABpAHYAZQAsACAA
aABpAGcAaABlAHIAIAB2AGEAbAB1AGUAcwAgAGEAcgBlACAAbQBvAHIAZQAgAHMAdABhAGIAbABl
AC4ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKAB2AGEAbABpAGQAIAByAGEAbgBnAGUAIAAw
AC4AMAAgAHQAbwAgADAALgA5ADkAKQAgACgAZABlAGYAYQB1AGwAdAA6ACAAMAAuADkAMAApAA0A
CgAtAC0AZAB5AG4AYQB0AGUAbQBwAC0AcgBhAG4AZwBlACAATgAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGQAeQBuAGEAbQBpAGMAIAB0AGUAbQBwAGUAcgBhAHQA
dQByAGUAIAByAGEAbgBnAGUAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADAALgAwADAALAAgADAALgAw
ACAAPQAgAGQAaQBzAGEAYgBsAGUAZAApAA0ACgAtAC0AZAB5AG4AYQB0AGUAbQBwAC0AZQB4AHAA
IABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGQAeQBu
AGEAbQBpAGMAIAB0AGUAbQBwAGUAcgBhAHQAdQByAGUAIABlAHgAcABvAG4AZQBuAHQAIAAoAGQA
ZQBmAGEAdQBsAHQAOgAgADEALgAwADAAKQANAAoALQAtAG0AaQByAG8AcwB0AGEAdAAgAE4AIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB1AHMA
ZQAgAE0AaQByAG8AcwB0AGEAdAAgAHMAYQBtAHAAbABpAG4AZwAuAA0ACgAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgAFQAbwBwACAASwAsACAATgB1AGMAbABlAHUAcwAgAGEAbgBkACAATABvAGMAYQBs
AGwAeQAgAFQAeQBwAGkAYwBhAGwAIABzAGEAbQBwAGwAZQByAHMAIABhAHIAZQAgAGkAZwBuAG8A
cgBlAGQAIABpAGYAIAB1AHMAZQBkAC4ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABkAGUA
ZgBhAHUAbAB0ADoAIAAwACwAIAAwACAAPQAgAGQAaQBzAGEAYgBsAGUAZAAsACAAMQAgAD0AIABN
AGkAcgBvAHMAdABhAHQALAAgADIAIAA9ACAATQBpAHIAbwBzAHQAYQB0ACAAMgAuADAAKQANAAoA
LQAtAG0AaQByAG8AcwB0AGEAdAAtAGwAcgAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIABNAGkAcgBvAHMAdABhAHQAIABsAGUAYQByAG4AaQBuAGcA
IAByAGEAdABlACwAIABwAGEAcgBhAG0AZQB0AGUAcgAgAGUAdABhACAAKABkAGUAZgBhAHUAbAB0
ADoAIAAwAC4AMQAwACkADQAKAC0ALQBtAGkAcgBvAHMAdABhAHQALQBlAG4AdAAgAE4AIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAATQBpAHIAbwBzAHQAYQB0
ACAAdABhAHIAZwBlAHQAIABlAG4AdAByAG8AcAB5ACwAIABwAGEAcgBhAG0AZQB0AGUAcgAgAHQA
YQB1ACAAKABkAGUAZgBhAHUAbAB0ADoAIAA1AC4AMAAwACkADQAKAC0AbAAsACAAIAAgACAALQAt
AGwAbwBnAGkAdAAtAGIAaQBhAHMAIABUAE8ASwBFAE4AXwBJAEQAKAArAC8ALQApAEIASQBBAFMA
IAAgACAAbQBvAGQAaQBmAGkAZQBzACAAdABoAGUAIABsAGkAawBlAGwAaQBoAG8AbwBkACAAbwBm
ACAAdABvAGsAZQBuACAAYQBwAHAAZQBhAHIAaQBuAGcAIABpAG4AIAB0AGgAZQAgAGMAbwBtAHAA
bABlAHQAaQBvAG4ALAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABpAC4AZQAuACAAYAAtAC0A
bABvAGcAaQB0AC0AYgBpAGEAcwAgADEANQAwADQAMwArADEAYAAgAHQAbwAgAGkAbgBjAHIAZQBh
AHMAZQAgAGwAaQBrAGUAbABpAGgAbwBvAGQAIABvAGYAIAB0AG8AawBlAG4AIAAnACAASABlAGwA
bABvACcALAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABvAHIAIABgAC0ALQBsAG8AZwBpAHQA
LQBiAGkAYQBzACAAMQA1ADAANAAzAC0AMQBgACAAdABvACAAZABlAGMAcgBlAGEAcwBlACAAbABp
AGsAZQBsAGkAaABvAG8AZAAgAG8AZgAgAHQAbwBrAGUAbgAgACcAIABIAGUAbABsAG8AJwANAAoA
LQAtAGcAcgBhAG0AbQBhAHIAIABHAFIAQQBNAE0AQQBSACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIABCAE4ARgAtAGwAaQBrAGUAIABnAHIAYQBtAG0AYQByACAA
dABvACAAYwBvAG4AcwB0AHIAYQBpAG4AIABnAGUAbgBlAHIAYQB0AGkAbwBuAHMAIAAoAHMAZQBl
ACAAcwBhAG0AcABsAGUAcwAgAGkAbgAgAGcAcgBhAG0AbQBhAHIAcwAvAA0ACgAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgAGQAaQByACkADQAKAC0ALQBnAHIAYQBtAG0AYQByAC0AZgBpAGwAZQAgAEYA
TgBBAE0ARQAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAZgBpAGwAZQAg
AHQAbwAgAHIAZQBhAGQAIABnAHIAYQBtAG0AYQByACAAZgByAG8AbQANAAoALQBqACwAIAAgACAA
IAAtAC0AagBzAG8AbgAtAHMAYwBoAGUAbQBhACAAUwBDAEgARQBNAEEAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABKAFMATwBOACAAcwBjAGgAZQBtAGEAIAB0AG8AIABjAG8AbgBzAHQAcgBhAGkA
bgAgAGcAZQBuAGUAcgBhAHQAaQBvAG4AcwAgACgAaAB0AHQAcABzADoALwAvAGoAcwBvAG4ALQBz
AGMAaABlAG0AYQAuAG8AcgBnAC8AKQAsACAAZQAuAGcALgANAAoAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIABgAHsAIgB0AHkAcABlACIAOgAgACIAbwBiAGoAZQBjAHQAIgB9AGAAIABmAG8AcgAgAGEA
bgB5ACAASgBTAE8ATgAgAG8AYgBqAGUAYwB0AA0ACgAtAGoAZgAsACAAIAAgAC0ALQBqAHMAbwBu
AC0AcwBjAGgAZQBtAGEALQBmAGkAbABlACAARgBJAEwARQAgACAAIAAgACAAIAAgACAAIAAgAEYA
aQBsAGUAIABjAG8AbgB0AGEAaQBuAGkAbgBnACAAYQAgAEoAUwBPAE4AIABzAGMAaABlAG0AYQAg
AHQAbwAgAGMAbwBuAHMAdAByAGEAaQBuACAAZwBlAG4AZQByAGEAdABpAG8AbgBzAA0ACgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACgAaAB0AHQAcABzADoALwAvAGoAcwBvAG4ALQBzAGMAaABlAG0A
YQAuAG8AcgBnAC8AKQAsACAAZQAuAGcALgAgAGAAewAiAHQAeQBwAGUAIgA6ACAAIgBvAGIAagBl
AGMAdAAiAH0AYAAgAGYAbwByACAAYQBuAHkAIABKAFMATwBOAA0ACgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgAG8AYgBqAGUAYwB0AA0ACgAtAGIAcwAsACAAIAAgAC0ALQBiAGEAYwBrAGUAbgBkAC0A
cwBhAG0AcABsAGkAbgBnACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGUAbgBhAGIAbABl
ACAAYgBhAGMAawBlAG4AZAAgAHMAYQBtAHAAbABpAG4AZwAgACgAZQB4AHAAZQByAGkAbQBlAG4A
dABhAGwAKQAgACgAZABlAGYAYQB1AGwAdAA6ACAAZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBCAEEAQwBL
AEUATgBEAF8AUwBBAE0AUABMAEkATgBHACkADQAKAA0ACgANAAoALQAtAC0ALQAtACAAcwBwAGUA
YwB1AGwAYQB0AGkAdgBlACAAcABhAHIAYQBtAHMAIAAtAC0ALQAtAC0ADQAKAA0ACgAtAC0AcwBw
AGUAYwAtAGQAcgBhAGYAdAAtAGgAZgAsACAALQBoAGYAZAAsACAALQBoAGYAcgBkACwAIAAtAC0A
aABmAC0AcgBlAHAAbwAtAGQAcgBhAGYAdAAgADwAdQBzAGUAcgA+AC8APABtAG8AZABlAGwAPgBb
ADoAcQB1AGEAbgB0AF0ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAUwBhAG0AZQAgAGEAcwAg
AC0ALQBoAGYALQByAGUAcABvACwAIABiAHUAdAAgAGYAbwByACAAdABoAGUAIABkAHIAYQBmAHQA
IABtAG8AZABlAGwAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAHUAbgB1AHMAZQBkACkADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBTAFAARQBD
AF8ARABSAEEARgBUAF8ASABGAF8AUgBFAFAATwApAA0ACgAtAC0AcwBwAGUAYwAtAGQAcgBhAGYA
dAAtAHQAaAByAGUAYQBkAHMALAAgAC0AdABkACwAIAAtAC0AdABoAHIAZQBhAGQAcwAtAGQAcgBh
AGYAdAAgAE4ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbgB1AG0AYgBlAHIAIABvAGYAIAB0
AGgAcgBlAGEAZABzACAAdABvACAAdQBzAGUAIABkAHUAcgBpAG4AZwAgAGcAZQBuAGUAcgBhAHQA
aQBvAG4AIAAoAGQAZQBmAGEAdQBsAHQAOgAgAHMAYQBtAGUAIABhAHMADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAALQAtAHQAaAByAGUAYQBkAHMAKQANAAoALQAtAHMAcABlAGMALQBkAHIAYQBm
AHQALQB0AGgAcgBlAGEAZABzAC0AYgBhAHQAYwBoACwAIAAtAHQAYgBkACwAIAAtAC0AdABoAHIA
ZQBhAGQAcwAtAGIAYQB0AGMAaAAtAGQAcgBhAGYAdAAgAE4ADQAKACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAbgB1AG0AYgBlAHIAIABvAGYAIAB0AGgAcgBlAGEAZABzACAAdABvACAAdQBzAGUAIABk
AHUAcgBpAG4AZwAgAGIAYQB0AGMAaAAgAGEAbgBkACAAcAByAG8AbQBwAHQAIABwAHIAbwBjAGUA
cwBzAGkAbgBnACAAKABkAGUAZgBhAHUAbAB0ADoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
cwBhAG0AZQAgAGEAcwAgAC0ALQB0AGgAcgBlAGEAZABzAC0AZAByAGEAZgB0ACkADQAKAC0ALQBz
AHAAZQBjAC0AZAByAGEAZgB0AC0AYwBwAHUALQBtAGEAcwBrACwAIAAtAEMAZAAsACAALQAtAGMA
cAB1AC0AbQBhAHMAawAtAGQAcgBhAGYAdAAgAE0ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
RAByAGEAZgB0ACAAbQBvAGQAZQBsACAAQwBQAFUAIABhAGYAZgBpAG4AaQB0AHkAIABtAGEAcwBr
AC4AIABDAG8AbQBwAGwAZQBtAGUAbgB0AHMAIABjAHAAdQAtAHIAYQBuAGcAZQAtAGQAcgBhAGYA
dAAgACgAZABlAGYAYQB1AGwAdAA6AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHMAYQBtAGUA
IABhAHMAIAAtAC0AYwBwAHUALQBtAGEAcwBrACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0
AC0AYwBwAHUALQByAGEAbgBnAGUALAAgAC0AQwByAGQALAAgAC0ALQBjAHAAdQAtAHIAYQBuAGcA
ZQAtAGQAcgBhAGYAdAAgAGwAbwAtAGgAaQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABSAGEA
bgBnAGUAcwAgAG8AZgAgAEMAUABVAHMAIABmAG8AcgAgAGEAZgBmAGkAbgBpAHQAeQAuACAAQwBv
AG0AcABsAGUAbQBlAG4AdABzACAALQAtAGMAcAB1AC0AbQBhAHMAawAtAGQAcgBhAGYAdAANAAoA
LQAtAHMAcABlAGMALQBkAHIAYQBmAHQALQBjAHAAdQAtAHMAdAByAGkAYwB0ACwAIAAtAC0AYwBw
AHUALQBzAHQAcgBpAGMAdAAtAGQAcgBhAGYAdAAgADwAMAB8ADEAPgANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABVAHMAZQAgAHMAdAByAGkAYwB0ACAAQwBQAFUAIABwAGwAYQBjAGUAbQBlAG4A
dAAgAGYAbwByACAAZAByAGEAZgB0ACAAbQBvAGQAZQBsACAAKABkAGUAZgBhAHUAbAB0ADoAIABz
AGEAbQBlACAAYQBzAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC0ALQBjAHAAdQAtAHMAdABy
AGkAYwB0ACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0AC0AcAByAGkAbwAsACAALQAtAHAA
cgBpAG8ALQBkAHIAYQBmAHQAIABOACAAIAAgACAAIAAgACAAcwBlAHQAIABkAHIAYQBmAHQAIABw
AHIAbwBjAGUAcwBzAC8AdABoAHIAZQBhAGQAIABwAHIAaQBvAHIAaQB0AHkAIAA6ACAAMAAtAG4A
bwByAG0AYQBsACwAIAAxAC0AbQBlAGQAaQB1AG0ALAAgADIALQBoAGkAZwBoACwADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAMwAtAHIAZQBhAGwAdABpAG0AZQAgACgAZABlAGYAYQB1AGwAdAA6
ACAAMAApAA0ACgAtAC0AcwBwAGUAYwAtAGQAcgBhAGYAdAAtAHAAbwBsAGwALAAgAC0ALQBwAG8A
bABsAC0AZAByAGEAZgB0ACAAPAAwAHwAMQA+ACAAIAAgAFUAcwBlACAAcABvAGwAbABpAG4AZwAg
AHQAbwAgAHcAYQBpAHQAIABmAG8AcgAgAGQAcgBhAGYAdAAgAG0AbwBkAGUAbAAgAHcAbwByAGsA
IAAoAGQAZQBmAGEAdQBsAHQAOgAgAHMAYQBtAGUAIABhAHMAIAAtAC0AcABvAGwAbAApAA0ACgAt
AC0AcwBwAGUAYwAtAGQAcgBhAGYAdAAtAGMAcAB1AC0AbQBhAHMAawAtAGIAYQB0AGMAaAAsACAA
LQBDAGIAZAAsACAALQAtAGMAcAB1AC0AbQBhAHMAawAtAGIAYQB0AGMAaAAtAGQAcgBhAGYAdAAg
AE0ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAARAByAGEAZgB0ACAAbQBvAGQAZQBsACAAQwBQ
AFUAIABhAGYAZgBpAG4AaQB0AHkAIABtAGEAcwBrAC4AIABDAG8AbQBwAGwAZQBtAGUAbgB0AHMA
IABjAHAAdQAtAHIAYQBuAGcAZQAtAGQAcgBhAGYAdAAgACgAZABlAGYAYQB1AGwAdAA6AA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAHMAYQBtAGUAIABhAHMAIAAtAC0AYwBwAHUALQBtAGEAcwBr
ACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0AC0AYwBwAHUALQBzAHQAcgBpAGMAdAAtAGIA
YQB0AGMAaAAsACAALQAtAGMAcAB1AC0AcwB0AHIAaQBjAHQALQBiAGEAdABjAGgALQBkAHIAYQBm
AHQAIAA8ADAAfAAxAD4ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAVQBzAGUAIABzAHQAcgBp
AGMAdAAgAEMAUABVACAAcABsAGEAYwBlAG0AZQBuAHQAIABmAG8AcgAgAGQAcgBhAGYAdAAgAG0A
bwBkAGUAbAAgACgAZABlAGYAYQB1AGwAdAA6ACAALQAtAGMAcAB1AC0AcwB0AHIAaQBjAHQALQBk
AHIAYQBmAHQAKQANAAoALQAtAHMAcABlAGMALQBkAHIAYQBmAHQALQBwAHIAaQBvAC0AYgBhAHQA
YwBoACwAIAAtAC0AcAByAGkAbwAtAGIAYQB0AGMAaAAtAGQAcgBhAGYAdAAgAE4ADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAcwBlAHQAIABkAHIAYQBmAHQAIABwAHIAbwBjAGUAcwBzAC8AdABo
AHIAZQBhAGQAIABwAHIAaQBvAHIAaQB0AHkAIAA6ACAAMAAtAG4AbwByAG0AYQBsACwAIAAxAC0A
bQBlAGQAaQB1AG0ALAAgADIALQBoAGkAZwBoACwADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
MwAtAHIAZQBhAGwAdABpAG0AZQAgACgAZABlAGYAYQB1AGwAdAA6ACAAMAApAA0ACgAtAC0AcwBw
AGUAYwAtAGQAcgBhAGYAdAAtAHAAbwBsAGwALQBiAGEAdABjAGgALAAgAC0ALQBwAG8AbABsAC0A
YgBhAHQAYwBoAC0AZAByAGEAZgB0ACAAPAAwAHwAMQA+AA0ACgAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAFUAcwBlACAAcABvAGwAbABpAG4AZwAgAHQAbwAgAHcAYQBpAHQAIABmAG8AcgAgAGQAcgBh
AGYAdAAgAG0AbwBkAGUAbAAgAHcAbwByAGsAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAC0ALQBwAG8A
bABsAC0AZAByAGEAZgB0ACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0AC0AbwB2AGUAcgBy
AGkAZABlAC0AdABlAG4AcwBvAHIALAAgAC0AbwB0AGQALAAgAC0ALQBvAHYAZQByAHIAaQBkAGUA
LQB0AGUAbgBzAG8AcgAtAGQAcgBhAGYAdAAgADwAdABlAG4AcwBvAHIAIABuAGEAbQBlACAAcABh
AHQAdABlAHIAbgA+AD0APABiAHUAZgBmAGUAcgAgAHQAeQBwAGUAPgAsAC4ALgAuAA0ACgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgAG8AdgBlAHIAcgBpAGQAZQAgAHQAZQBuAHMAbwByACAAYgB1AGYA
ZgBlAHIAIAB0AHkAcABlACAAZgBvAHIAIABkAHIAYQBmAHQAIABtAG8AZABlAGwADQAKAC0ALQBz
AHAAZQBjAC0AZAByAGEAZgB0AC0AYwBwAHUALQBtAG8AZQAsACAALQBjAG0AbwBlAGQALAAgAC0A
LQBjAHAAdQAtAG0AbwBlAC0AZAByAGEAZgB0AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGsA
ZQBlAHAAIABhAGwAbAAgAE0AaQB4AHQAdQByAGUAIABvAGYAIABFAHgAcABlAHIAdABzACAAKABN
AG8ARQApACAAdwBlAGkAZwBoAHQAcwAgAGkAbgAgAHQAaABlACAAQwBQAFUAIABmAG8AcgAgAHQA
aABlACAAZAByAGEAZgB0AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG0AbwBkAGUAbAANAAoA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFMA
UABFAEMAXwBEAFIAQQBGAFQAXwBDAFAAVQBfAE0ATwBFACkADQAKAC0ALQBzAHAAZQBjAC0AZABy
AGEAZgB0AC0AbgAtAGMAcAB1AC0AbQBvAGUALAAgAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0AC0A
bgBjAG0AbwBlACwAIAAtAG4AYwBtAG8AZQBkACwAIAAtAC0AbgAtAGMAcAB1AC0AbQBvAGUALQBk
AHIAYQBmAHQAIABOAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGsAZQBlAHAAIAB0AGgAZQAg
AE0AaQB4AHQAdQByAGUAIABvAGYAIABFAHgAcABlAHIAdABzACAAKABNAG8ARQApACAAdwBlAGkA
ZwBoAHQAcwAgAG8AZgAgAHQAaABlACAAZgBpAHIAcwB0ACAATgAgAGwAYQB5AGUAcgBzACAAaQBu
ACAAdABoAGUADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAQwBQAFUAIABmAG8AcgAgAHQAaABl
ACAAZAByAGEAZgB0ACAAbQBvAGQAZQBsAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBu
AHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AUwBQAEUAQwBfAEQAUgBBAEYAVABfAE4AXwBDAFAA
VQBfAE0ATwBFACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0AC0AbgAtAG0AYQB4ACAATgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbgB1AG0AYgBlAHIAIABvAGYA
IAB0AG8AawBlAG4AcwAgAHQAbwAgAGQAcgBhAGYAdAAgAGYAbwByACAAcwBwAGUAYwB1AGwAYQB0
AGkAdgBlACAAZABlAGMAbwBkAGkAbgBnACAAKABkAGUAZgBhAHUAbAB0ADoAIAAzACkADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBTAFAA
RQBDAF8ARABSAEEARgBUAF8ATgBfAE0AQQBYACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0
AC0AbgAtAG0AaQBuACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
bQBpAG4AaQBtAHUAbQAgAG4AdQBtAGIAZQByACAAbwBmACAAZAByAGEAZgB0ACAAdABvAGsAZQBu
AHMAIAB0AG8AIAB1AHMAZQAgAGYAbwByACAAcwBwAGUAYwB1AGwAYQB0AGkAdgBlACAAZABlAGMA
bwBkAGkAbgBnAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZABlAGYAYQB1AGwAdAA6ACAA
MAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEA
UgBHAF8AUwBQAEUAQwBfAEQAUgBBAEYAVABfAE4AXwBNAEkATgApAA0ACgAtAC0AcwBwAGUAYwAt
AGQAcgBhAGYAdAAtAG4ALQB1AGIAYQB0AGMAaAAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgAHAAaAB5AHMAaQBjAGEAbAAgAG0AYQB4AGkAbQB1AG0AIABiAGEAdABjAGgAIABz
AGkAegBlACAAbwBmACAAdABoAGUAIABkAHIAYQBmAHQAIABjAG8AbgB0AGUAeAB0ACwAIAB1AHMA
ZQAgAGEAIABzAG0AYQBsAGwAZQByACAAdgBhAGwAdQBlAA0ACgAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAHQAbwAgAHMAcABhAHIAZQAgAFYAUgBBAE0AIAAoAGQAZQBmAGEAdQBsAHQAOgAgADAAIAAt
ACAAcwBhAG0AZQAgAGEAcwAgAC0ALQBuAC0AdQBiAGEAdABjAGgAKQANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFMAUABFAEMAXwBEAFIA
QQBGAFQAXwBOAF8AVQBCAEEAVABDAEgAKQANAAoALQAtAHMAcABlAGMALQBzAHkAbgB0AGgALQBs
AGUAbgAgAEwAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB0AGEA
cgBnAGUAdAAgAG0AZQBhAG4AIABzAHkAbgB0AGgAZQB0AGkAYwAgAGEAYwBjAGUAcAB0AGEAbgBj
AGUAIABsAGUAbgBnAHQAaAAsACAAaQBuAGMAbAB1AGQAaQBuAGcAIAB0AGgAZQAgAHQAYQByAGcA
ZQB0ACAAdABvAGsAZQBuAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAYgBlAG4AYwBoAG0A
YQByAGsAaQBuAGcAIABvAG4AbAB5ACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4A
dgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBTAFAARQBDAF8AUwBZAE4AVABIAF8ATABFAE4AKQAN
AAoALQAtAHMAcABlAGMALQBzAHkAbgB0AGgALQByAGEAdABlAHMAIABQADAALABQADEALAAuAC4A
LgAgACAAIAAgACAAIAAgACAAIAAgACAAIABjAG8AbQBtAGEALQBzAGUAcABhAHIAYQB0AGUAZAAg
AHUAbgBjAG8AbgBkAGkAdABpAG8AbgBhAGwAIABwAGUAcgAtAHAAbwBzAGkAdABpAG8AbgAgAHMA
eQBuAHQAaABlAHQAaQBjACAAYQBjAGMAZQBwAHQAYQBuAGMAZQANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABwAHIAbwBiAGEAYgBpAGwAaQB0AGkAZQBzACAAKABiAGUAbgBjAGgAbQBhAHIAawBp
AG4AZwAgAG8AbgBsAHkAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABM
AEwAQQBNAEEAXwBBAFIARwBfAFMAUABFAEMAXwBTAFkATgBUAEgAXwBSAEEAVABFAFMAKQANAAoA
LQAtAHMAcABlAGMALQBkAHIAYQBmAHQALQBwAC0AcwBwAGwAaQB0ACwAIAAtAC0AZAByAGEAZgB0
AC0AcAAtAHMAcABsAGkAdAAgAFAADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBwAGUAYwB1
AGwAYQB0AGkAdgBlACAAZABlAGMAbwBkAGkAbgBnACAAcwBwAGwAaQB0ACAAcAByAG8AYgBhAGIA
aQBsAGkAdAB5ACAAKABkAGUAZgBhAHUAbAB0ADoAIAAwAC4AMQAwACkADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBTAFAARQBDAF8ARABS
AEEARgBUAF8AUABfAFMAUABMAEkAVAApAA0ACgAtAC0AcwBwAGUAYwAtAGQAcgBhAGYAdAAtAHAA
LQBtAGkAbgAsACAALQAtAGQAcgBhAGYAdAAtAHAALQBtAGkAbgAgAFAAIAAgACAAIAAgAG0AaQBu
AGkAbQB1AG0AIABzAHAAZQBjAHUAbABhAHQAaQB2AGUAIABkAGUAYwBvAGQAaQBuAGcAIABwAHIA
bwBiAGEAYgBpAGwAaQB0AHkAIAAoAGcAcgBlAGUAZAB5ACkAIAAoAGQAZQBmAGEAdQBsAHQAOgAg
ADAALgAwADAAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBN
AEEAXwBBAFIARwBfAFMAUABFAEMAXwBEAFIAQQBGAFQAXwBQAF8ATQBJAE4AKQANAAoALQAtAHMA
cABlAGMALQBkAHIAYQBmAHQALQBiAGEAYwBrAGUAbgBkAC0AcwBhAG0AcABsAGkAbgBnACwAIAAt
AC0AbgBvAC0AcwBwAGUAYwAtAGQAcgBhAGYAdAAtAGIAYQBjAGsAZQBuAGQALQBzAGEAbQBwAGwA
aQBuAGcADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbwBmAGYAbABvAGEAZAAgAGQAcgBhAGYA
dAAgAHMAYQBtAHAAbABpAG4AZwAgAHQAbwAgAHQAaABlACAAYgBhAGMAawBlAG4AZAAgACgAZABl
AGYAYQB1AGwAdAA6ACAAZQBuAGEAYgBsAGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AUwBQAEUAQwBfAEQAUgBBAEYAVABfAEIA
QQBDAEsARQBOAEQAXwBTAEEATQBQAEwASQBOAEcAKQANAAoALQAtAHMAcABlAGMALQBkAHIAYQBm
AHQALQBzAGEAbQBwAGwAaQBuAGcAIAB7AGcAcgBlAGUAZAB5ACwAcAByAG8AYgBhAGIAaQBsAGkA
cwB0AGkAYwB9AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGgAbwB3ACAAdABoAGUAIABkAHIA
YQBmAHQAIABpAHMAIABzAGEAbQBwAGwAZQBkADoAIABnAHIAZQBlAGQAeQAgAHQAYQBrAGUAcwAg
AGkAdABzACAAYQByAGcAbQBhAHgALAAgAHAAcgBvAGIAYQBiAGkAbABpAHMAdABpAGMADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAcwBhAG0AcABsAGUAcwAgAGkAdAAgAGEAbgBkACAAaABhAHMA
IAB0AGgAZQAgAHQAYQByAGcAZQB0ACAAdgBlAHIAaQBmAHkAIABiAHkAIAByAGUAagBlAGMAdABp
AG8AbgAgAHMAYQBtAHAAbABpAG4AZwAgACgAZABlAGYAYQB1AGwAdAA6AA0ACgAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgAGcAcgBlAGUAZAB5ACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABl
AG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBTAFAARQBDAF8ARABSAEEARgBUAF8AUwBBAE0A
UABMAEkATgBHACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0AC0AZABlAHYAaQBjAGUALAAg
AC0AZABlAHYAZAAsACAALQAtAGQAZQB2AGkAYwBlAC0AZAByAGEAZgB0ACAAPABkAGUAdgAxACwA
ZABlAHYAMgAsAC4ALgA+AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGMAbwBtAG0AYQAtAHMA
ZQBwAGEAcgBhAHQAZQBkACAAbABpAHMAdAAgAG8AZgAgAGQAZQB2AGkAYwBlAHMAIAB0AG8AIAB1
AHMAZQAgAGYAbwByACAAbwBmAGYAbABvAGEAZABpAG4AZwAgAHQAaABlACAAZAByAGEAZgB0ACAA
bQBvAGQAZQBsAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAbgBvAG4AZQAgAD0AIABkAG8A
bgAnAHQAIABvAGYAZgBsAG8AYQBkACwAIABkAGUAZgBhAHUAbAB0ADoAIABmAG8AbABsAG8AdwBz
ACAALQAtAGQAZQB2AGkAYwBlACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdQBzAGUAIAAt
AC0AbABpAHMAdAAtAGQAZQB2AGkAYwBlAHMAIAB0AG8AIABzAGUAZQAgAGEAIABsAGkAcwB0ACAA
bwBmACAAYQB2AGEAaQBsAGEAYgBsAGUAIABkAGUAdgBpAGMAZQBzAA0ACgAtAC0AcwBwAGUAYwAt
AGQAcgBhAGYAdAAtAG4AZwBsACwAIAAtAG4AZwBsAGQALAAgAC0ALQBnAHAAdQAtAGwAYQB5AGUA
cgBzAC0AZAByAGEAZgB0ACwAIAAtAC0AbgAtAGcAcAB1AC0AbABhAHkAZQByAHMALQBkAHIAYQBm
AHQAIABOAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG0AYQB4AC4AIABuAHUAbQBiAGUAcgAg
AG8AZgAgAGQAcgBhAGYAdAAgAG0AbwBkAGUAbAAgAGwAYQB5AGUAcgBzACAAdABvACAAcwB0AG8A
cgBlACAAaQBuACAAVgBSAEEATQAsACAAZQBpAHQAaABlAHIAIABhAG4AIABlAHgAYQBjAHQADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAbgB1AG0AYgBlAHIALAAgACcAYQB1AHQAbwAnACwAIABv
AHIAIAAnAGEAbABsACcAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGEAdQB0AG8AKQANAAoAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAE4AXwBHAFAA
VQBfAEwAQQBZAEUAUgBTAF8ARABSAEEARgBUACkADQAKAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0
AC0AbQBvAGQAZQBsACwAIAAtAG0AZAAsACAALQAtAG0AbwBkAGUAbAAtAGQAcgBhAGYAdAAgAEYA
TgBBAE0ARQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABkAHIAYQBmAHQAIABtAG8AZABlAGwA
IABmAG8AcgAgAHMAcABlAGMAdQBsAGEAdABpAHYAZQAgAGQAZQBjAG8AZABpAG4AZwAgACgAZABl
AGYAYQB1AGwAdAA6ACAAdQBuAHUAcwBlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAo
AGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFMAUABFAEMAXwBEAFIAQQBGAFQAXwBNAE8A
RABFAEwAKQANAAoALQAtAHMAcABlAGMALQB0AHkAcABlACAAbgBvAG4AZQAsAGQAcgBhAGYAdAAt
AHMAaQBtAHAAbABlACwAZAByAGEAZgB0AC0AZQBhAGcAbABlADMALABkAHIAYQBmAHQALQBtAHQA
cAAsAGQAcgBhAGYAdAAtAGQAZgBsAGEAcwBoACwAZAByAGEAZgB0AC0AZABzAHAAYQByAGsALABu
AGcAcgBhAG0ALQBzAGkAbQBwAGwAZQAsAG4AZwByAGEAbQAtAG0AYQBwAC0AawAsAG4AZwByAGEA
bQAtAG0AYQBwAC0AawA0AHYALABuAGcAcgBhAG0ALQBtAG8AZAAsAG4AZwByAGEAbQAtAGMAYQBj
AGgAZQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABjAG8AbQBtAGEALQBzAGUAcABhAHIAYQB0
AGUAZAAgAGwAaQBzAHQAIABvAGYAIAB0AHkAcABlAHMAIABvAGYAIABzAHAAZQBjAHUAbABhAHQA
aQB2AGUAIABkAGUAYwBvAGQAaQBuAGcAIAB0AG8AIAB1AHMAZQAgACgAZABlAGYAYQB1AGwAdAA6
AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4AbwBuAGUAKQANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEA
XwBBAFIARwBfAFMAUABFAEMAXwBUAFkAUABFACkADQAKAC0ALQBzAHAAZQBjAC0AbgBnAHIAYQBt
AC0AbQBvAGQALQBuAC0AbQBpAG4AIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
bQBpAG4AaQBtAHUAbQAgAG4AdQBtAGIAZQByACAAbwBmACAAbgBnAHIAYQBtACAAdABvAGsAZQBu
AHMAIAB0AG8AIAB1AHMAZQAgAGYAbwByACAAbgBnAHIAYQBtAC0AYgBhAHMAZQBkACAAcwBwAGUA
YwB1AGwAYQB0AGkAdgBlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGQAZQBjAG8AZABpAG4A
ZwAgACgAZABlAGYAYQB1AGwAdAA6ACAANAA4ACkADQAKAC0ALQBzAHAAZQBjAC0AbgBnAHIAYQBt
AC0AbQBvAGQALQBuAC0AbQBhAHgAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
bQBhAHgAaQBtAHUAbQAgAG4AdQBtAGIAZQByACAAbwBmACAAbgBnAHIAYQBtACAAdABvAGsAZQBu
AHMAIAB0AG8AIAB1AHMAZQAgAGYAbwByACAAbgBnAHIAYQBtAC0AYgBhAHMAZQBkACAAcwBwAGUA
YwB1AGwAYQB0AGkAdgBlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGQAZQBjAG8AZABpAG4A
ZwAgACgAZABlAGYAYQB1AGwAdAA6ACAANgA0ACkADQAKAC0ALQBzAHAAZQBjAC0AbgBnAHIAYQBt
AC0AbQBvAGQALQBuAC0AbQBhAHQAYwBoACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
bgBnAHIAYQBtAC0AbQBvAGQAIABsAG8AbwBrAHUAcAAgAGwAZQBuAGcAdABoACAAKABkAGUAZgBh
AHUAbAB0ADoAIAAyADQAKQANAAoALQAtAHMAcABlAGMALQBuAGcAcgBhAG0ALQBzAGkAbQBwAGwA
ZQAtAHMAaQB6AGUALQBuACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIABuAGcAcgBhAG0AIABz
AGkAegBlACAATgAgAGYAbwByACAAbgBnAHIAYQBtAC0AcwBpAG0AcABsAGUAIABzAHAAZQBjAHUA
bABhAHQAaQB2AGUAIABkAGUAYwBvAGQAaQBuAGcALAAgAGwAZQBuAGcAdABoACAAbwBmACAAbABv
AG8AawB1AHAADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbgAtAGcAcgBhAG0AIAAoAGQAZQBm
AGEAdQBsAHQAOgAgADEAMgApAA0ACgAtAC0AcwBwAGUAYwAtAG4AZwByAGEAbQAtAHMAaQBtAHAA
bABlAC0AcwBpAHoAZQAtAG0AIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4AZwByAGEAbQAg
AHMAaQB6AGUAIABNACAAZgBvAHIAIABuAGcAcgBhAG0ALQBzAGkAbQBwAGwAZQAgAHMAcABlAGMA
dQBsAGEAdABpAHYAZQAgAGQAZQBjAG8AZABpAG4AZwAsACAAbABlAG4AZwB0AGgAIABvAGYAIABk
AHIAYQBmAHQADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbQAtAGcAcgBhAG0AIAAoAGQAZQBm
AGEAdQBsAHQAOgAgADQAOAApAA0ACgAtAC0AcwBwAGUAYwAtAG4AZwByAGEAbQAtAHMAaQBtAHAA
bABlAC0AbQBpAG4ALQBoAGkAdABzACAATgAgACAAIAAgACAAIAAgACAAIAAgAG0AaQBuAGkAbQB1
AG0AIABoAGkAdABzACAAZgBvAHIAIABuAGcAcgBhAG0ALQBzAGkAbQBwAGwAZQAgAHMAcABlAGMA
dQBsAGEAdABpAHYAZQAgAGQAZQBjAG8AZABpAG4AZwAgACgAZABlAGYAYQB1AGwAdAA6ACAAMQAp
AA0ACgAtAC0AcwBwAGUAYwAtAG4AZwByAGEAbQAtAG0AYQBwAC0AawAtAHMAaQB6AGUALQBuACAA
TgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4AZwByAGEAbQAgAHMAaQB6AGUAIABOACAAZgBv
AHIAIABuAGcAcgBhAG0ALQBtAGEAcAAtAGsAIABzAHAAZQBjAHUAbABhAHQAaQB2AGUAIABkAGUA
YwBvAGQAaQBuAGcALAAgAGwAZQBuAGcAdABoACAAbwBmACAAbABvAG8AawB1AHAADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAbgAtAGcAcgBhAG0AIAAoAGQAZQBmAGEAdQBsAHQAOgAgADEAMgAp
AA0ACgAtAC0AcwBwAGUAYwAtAG4AZwByAGEAbQAtAG0AYQBwAC0AawAtAHMAaQB6AGUALQBtACAA
TgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4AZwByAGEAbQAgAHMAaQB6AGUAIABNACAAZgBv
AHIAIABuAGcAcgBhAG0ALQBtAGEAcAAtAGsAIABzAHAAZQBjAHUAbABhAHQAaQB2AGUAIABkAGUA
YwBvAGQAaQBuAGcALAAgAGwAZQBuAGcAdABoACAAbwBmACAAZAByAGEAZgB0AA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAG0ALQBnAHIAYQBtACAAKABkAGUAZgBhAHUAbAB0ADoAIAA0ADgAKQAN
AAoALQAtAHMAcABlAGMALQBuAGcAcgBhAG0ALQBtAGEAcAAtAGsALQBtAGkAbgAtAGgAaQB0AHMA
IABOACAAIAAgACAAIAAgACAAIAAgACAAIABtAGkAbgBpAG0AdQBtACAAaABpAHQAcwAgAGYAbwBy
ACAAbgBnAHIAYQBtAC0AbQBhAHAALQBrACAAcwBwAGUAYwB1AGwAYQB0AGkAdgBlACAAZABlAGMA
bwBkAGkAbgBnACAAKABkAGUAZgBhAHUAbAB0ADoAIAAxACkADQAKAC0ALQBzAHAAZQBjAC0AbgBn
AHIAYQBtAC0AbQBhAHAALQBrADQAdgAtAHMAaQB6AGUALQBuACAATgAgACAAIAAgACAAIAAgACAA
IAAgACAAbgBnAHIAYQBtACAAcwBpAHoAZQAgAE4AIABmAG8AcgAgAG4AZwByAGEAbQAtAG0AYQBw
AC0AawA0AHYAIABzAHAAZQBjAHUAbABhAHQAaQB2AGUAIABkAGUAYwBvAGQAaQBuAGcALAAgAGwA
ZQBuAGcAdABoACAAbwBmACAAbABvAG8AawB1AHAADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
bgAtAGcAcgBhAG0AIAAoAGQAZQBmAGEAdQBsAHQAOgAgADEAMgApAA0ACgAtAC0AcwBwAGUAYwAt
AG4AZwByAGEAbQAtAG0AYQBwAC0AawA0AHYALQBzAGkAegBlAC0AbQAgAE4AIAAgACAAIAAgACAA
IAAgACAAIAAgAG4AZwByAGEAbQAgAHMAaQB6AGUAIABNACAAZgBvAHIAIABuAGcAcgBhAG0ALQBt
AGEAcAAtAGsANAB2ACAAcwBwAGUAYwB1AGwAYQB0AGkAdgBlACAAZABlAGMAbwBkAGkAbgBnACwA
IABsAGUAbgBnAHQAaAAgAG8AZgAgAGQAcgBhAGYAdAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IABtAC0AZwByAGEAbQAgACgAZABlAGYAYQB1AGwAdAA6ACAANAA4ACkADQAKAC0ALQBzAHAAZQBj
AC0AbgBnAHIAYQBtAC0AbQBhAHAALQBrADQAdgAtAG0AaQBuAC0AaABpAHQAcwAgAE4AIAAgACAA
IAAgACAAIAAgACAAbQBpAG4AaQBtAHUAbQAgAGgAaQB0AHMAIABmAG8AcgAgAG4AZwByAGEAbQAt
AG0AYQBwAC0AawA0AHYAIABzAHAAZQBjAHUAbABhAHQAaQB2AGUAIABkAGUAYwBvAGQAaQBuAGcA
IAAoAGQAZQBmAGEAdQBsAHQAOgAgADEAKQANAAoALQAtAGQAcgBhAGYAdAAsACAALQAtAGQAcgBh
AGYAdAAtAG4ALAAgAC0ALQBkAHIAYQBmAHQALQBtAGEAeAAgAE4AIAAgACAAIAAgACAAIAB0AGgA
ZQAgAGEAcgBnAHUAbQBlAG4AdAAgAGgAYQBzACAAYgBlAGUAbgAgAHIAZQBtAG8AdgBlAGQALgAg
AHUAcwBlACAALQAtAHMAcABlAGMALQBkAHIAYQBmAHQALQBuAC0AbQBhAHgAIABvAHIADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAALQAtAHMAcABlAGMALQBuAGcAcgBhAG0ALQBtAG8AZAAtAG4A
LQBtAGEAeAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEA
XwBBAFIARwBfAEQAUgBBAEYAVABfAE0AQQBYACkADQAKAC0ALQBkAHIAYQBmAHQALQBtAGkAbgAs
ACAALQAtAGQAcgBhAGYAdAAtAG4ALQBtAGkAbgAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAA
dABoAGUAIABhAHIAZwB1AG0AZQBuAHQAIABoAGEAcwAgAGIAZQBlAG4AIAByAGUAbQBvAHYAZQBk
AC4AIAB1AHMAZQAgAC0ALQBzAHAAZQBjAC0AZAByAGEAZgB0AC0AbgAtAG0AaQBuACAAbwByAA0A
CgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC0ALQBzAHAAZQBjAC0AbgBnAHIAYQBtAC0AbQBvAGQA
LQBuAC0AbQBpAG4ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEA
TQBBAF8AQQBSAEcAXwBEAFIAQQBGAFQAXwBNAEkATgApAA0ACgAtAC0AcwBwAGUAYwAtAG4AZwBy
AGEAbQAtAHMAaQB6AGUALQBuACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAHQAaABlACAAYQByAGcAdQBtAGUAbgB0ACAAaABhAHMAIABiAGUAZQBuACAAcgBlAG0AbwB2
AGUAZAAuACAAdQBzAGUAIAB0AGgAZQAgAHIAZQBzAHAAZQBjAHQAaQB2AGUADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAALQAtAHMAcABlAGMALQBuAGcAcgBhAG0ALQAqAC0AcwBpAHoAZQAtAG4A
IABvAHIAIAAtAC0AcwBwAGUAYwAtAG4AZwByAGEAbQAtAG0AbwBkAC0AbgAtAG0AYQB0AGMAaAAN
AAoALQAtAHMAcABlAGMALQBuAGcAcgBhAG0ALQBzAGkAegBlAC0AbQAgAE4AIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB0AGgAZQAgAGEAcgBnAHUAbQBlAG4AdAAgAGgAYQBz
ACAAYgBlAGUAbgAgAHIAZQBtAG8AdgBlAGQALgAgAHUAcwBlACAAdABoAGUAIAByAGUAcwBwAGUA
YwB0AGkAdgBlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAC0ALQBzAHAAZQBjAC0AbgBnAHIA
YQBtAC0AKgAtAHMAaQB6AGUALQBtAA0ACgAtAC0AcwBwAGUAYwAtAG4AZwByAGEAbQAtAG0AaQBu
AC0AaABpAHQAcwAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHQAaABlACAA
YQByAGcAdQBtAGUAbgB0ACAAaABhAHMAIABiAGUAZQBuACAAcgBlAG0AbwB2AGUAZAAuACAAdQBz
AGUAIAB0AGgAZQAgAHIAZQBzAHAAZQBjAHQAaQB2AGUADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAALQAtAHMAcABlAGMALQBuAGcAcgBhAG0ALQAqAC0AbQBpAG4ALQBoAGkAdABzAA0ACgANAAoA
DQAKAC0ALQAtAC0ALQAgAGUAeABhAG0AcABsAGUALQBzAHAAZQBjAGkAZgBpAGMAIABwAGEAcgBh
AG0AcwAgAC0ALQAtAC0ALQANAAoADQAKAC0AbABjAHMALAAgACAALQAtAGwAbwBvAGsAdQBwAC0A
YwBhAGMAaABlAC0AcwB0AGEAdABpAGMAIABGAE4AQQBNAEUAIAAgACAAIAAgACAAcABhAHQAaAAg
AHQAbwAgAHMAdABhAHQAaQBjACAAbABvAG8AawB1AHAAIABjAGEAYwBoAGUAIAB0AG8AIAB1AHMA
ZQAgAGYAbwByACAAbABvAG8AawB1AHAAIABkAGUAYwBvAGQAaQBuAGcAIAAoAG4AbwB0ACAAdQBw
AGQAYQB0AGUAZAAgAGIAeQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABnAGUAbgBlAHIAYQB0
AGkAbwBuACkADQAKAC0AbABjAGQALAAgACAALQAtAGwAbwBvAGsAdQBwAC0AYwBhAGMAaABlAC0A
ZAB5AG4AYQBtAGkAYwAgAEYATgBBAE0ARQAgACAAIAAgACAAcABhAHQAaAAgAHQAbwAgAGQAeQBu
AGEAbQBpAGMAIABsAG8AbwBrAHUAcAAgAGMAYQBjAGgAZQAgAHQAbwAgAHUAcwBlACAAZgBvAHIA
IABsAG8AbwBrAHUAcAAgAGQAZQBjAG8AZABpAG4AZwAgACgAdQBwAGQAYQB0AGUAZAAgAGIAeQAN
AAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIABnAGUAbgBlAHIAYQB0AGkAbwBuACkADQAKAC0ALQBr
AHYALQB1AG4AaQBmAGkAZQBkAC0AcABlAHIALQBzAGwAbwB0ACAATgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAYwBvAG4AdABlAHgAdAAgAGwAaQBtAGkAdAAgAHAAZQByACAAcABh
AHIAYQBsAGwAZQBsACAAcwBsAG8AdAAgACgAZABlAGYAYQB1AGwAdAA6ACAAdQBuAHMAZQB0ACwA
IABiAGUAaABhAHYAaQBvAHIAIAB1AG4AYwBoAGEAbgBnAGUAZAApAC4ADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAdwBoAGUAbgAgAHMAZQB0ACAAdwBpAHQAaABvAHUAdAAgAC0AYwAvAC0ALQBj
AHQAeAAtAHMAaQB6AGUALAAgAHQAaABlACAAcwBoAGEAcgBlAGQAIABLAFYAIABwAG8AbwBsACAA
aQBzACAAcwBpAHoAZQBkACAAdABvAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4AXwBwAGEA
cgBhAGwAbABlAGwAKgBOAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwA
TABBAE0AQQBfAEEAUgBHAF8ASwBWAF8AVQBOAEkARgBJAEUARABfAFAARQBSAF8AUwBMAE8AVAAp
AA0ACgAtAGMAdAB4AGMAcAAsACAALQAtAGMAdAB4AC0AYwBoAGUAYwBrAHAAbwBpAG4AdABzACwA
IAAtAC0AcwB3AGEALQBjAGgAZQBjAGsAcABvAGkAbgB0AHMAIABOAA0ACgAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgAG0AYQB4ACAAbgB1AG0AYgBlAHIAIABvAGYAIABjAG8AbgB0AGUAeAB0ACAAYwBo
AGUAYwBrAHAAbwBpAG4AdABzACAAdABvACAAYwByAGUAYQB0AGUAIABwAGUAcgAgAHMAbABvAHQA
IAAoAGQAZQBmAGEAdQBsAHQAOgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAzADIAKQBbACgA
bQBvAHIAZQAgAGkAbgBmAG8AKQBdACgAaAB0AHQAcABzADoALwAvAGcAaQB0AGgAdQBiAC4AYwBv
AG0ALwBnAGcAbQBsAC0AbwByAGcALwBsAGwAYQBtAGEALgBjAHAAcAAvAHAAdQBsAGwALwAxADUA
MgA5ADMAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEA
XwBBAFIARwBfAEMAVABYAF8AQwBIAEUAQwBLAFAATwBJAE4AVABTACkADQAKAC0AYwBtAHMALAAg
ACAALQAtAGMAaABlAGMAawBwAG8AaQBuAHQALQBtAGkAbgAtAHMAdABlAHAAIABOACAAIAAgACAA
IAAgACAAIAAgACAAbQBpAG4AaQBtAHUAbQAgAHMAcABhAGMAaQBuAGcAIABiAGUAdAB3AGUAZQBu
ACAAYwBvAG4AdABlAHgAdAAgAGMAaABlAGMAawBwAG8AaQBuAHQAcwAgAGkAbgAgAHQAbwBrAGUA
bgBzACAAKABkAGUAZgBhAHUAbAB0ADoAIAA4ADEAOQAyACwADQAKACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAMAAgAD0AIABuAG8AIABtAGkAbgBpAG0AdQBtACkADQAKACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBDAEgARQBDAEsAUABPAEkATgBU
AF8ATQBJAE4AXwBTAFAAQQBDAEkATgBHAF8ATgBUACkADQAKAC0AYwByAGEAbQAsACAALQAtAGMA
YQBjAGgAZQAtAHIAYQBtACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAcwBlAHQAIAB0AGgAZQAgAG0AYQB4AGkAbQB1AG0AIABjAGEAYwBoAGUAIABzAGkAegBlACAA
aQBuACAATQBpAEIAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADgAMQA5ADIALAAgADAAIABmAG8AcgAg
AGQAZQBjAGkAcwBpAG8AbgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABtAG8AZABlAGwAcwAs
ACAALQAxACAALQAgAG4AbwAgAGwAaQBtAGkAdAAsACAAMAAgAC0AIABkAGkAcwBhAGIAbABlACkA
WwAoAG0AbwByAGUADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAaQBuAGYAbwApAF0AKABoAHQA
dABwAHMAOgAvAC8AZwBpAHQAaAB1AGIALgBjAG8AbQAvAGcAZwBtAGwALQBvAHIAZwAvAGwAbABh
AG0AYQAuAGMAcABwAC8AcAB1AGwAbAAvADEANgAzADkAMQApAA0ACgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AQwBBAEMASABFAF8AUgBBAE0A
KQANAAoALQBrAHYAdQAsACAAIAAtAC0AawB2AC0AdQBuAGkAZgBpAGUAZAAsACAALQBuAG8ALQBr
AHYAdQAsACAALQAtAG4AbwAtAGsAdgAtAHUAbgBpAGYAaQBlAGQADQAKACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAdQBzAGUAIABzAGkAbgBnAGwAZQAgAHUAbgBpAGYAaQBlAGQAIABLAFYAIABiAHUA
ZgBmAGUAcgAgAHMAaABhAHIAZQBkACAAYQBjAHIAbwBzAHMAIABhAGwAbAAgAHMAZQBxAHUAZQBu
AGMAZQBzACAAKABkAGUAZgBhAHUAbAB0ADoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAZQBu
AGEAYgBsAGUAZAAgAGkAZgAgAG4AdQBtAGIAZQByACAAbwBmACAAcwBsAG8AdABzACAAaQBzACAA
YQB1AHQAbwApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0A
QQBfAEEAUgBHAF8ASwBWAF8AVQBOAEkARgBJAEUARAApAA0ACgAtAC0AYwBhAGMAaABlAC0AaQBk
AGwAZQAtAHMAbABvAHQAcwAsACAALQAtAG4AbwAtAGMAYQBjAGgAZQAtAGkAZABsAGUALQBzAGwA
bwB0AHMADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBhAHYAZQAgAGkAZABsAGUAIABzAGwA
bwB0AHMAIAB0AG8AIAB0AGgAZQAgAHAAcgBvAG0AcAB0ACAAYwBhAGMAaABlACAAbwBuACAAbgBl
AHcAIAB0AGEAcwBrACwAIABhAG4AZAAgAGMAbABlAGEAcgAgAHQAaABlAG0AIAB3AGgAZQBuAA0A
CgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHUAcwBpAG4AZwAgAHUAbgBpAGYAaQBlAGQAIABLAFYA
IAAoAGQAZQBmAGEAdQBsAHQAOgAgAGUAbgBhAGIAbABlAGQALAAgAHIAZQBxAHUAaQByAGUAcwAg
AGMAYQBjAGgAZQAtAHIAYQBtACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6
ACAATABMAEEATQBBAF8AQQBSAEcAXwBDAEEAQwBIAEUAXwBJAEQATABFAF8AUwBMAE8AVABTACkA
DQAKAC0ALQBjAG8AbgB0AGUAeAB0AC0AcwBoAGkAZgB0ACwAIAAtAC0AbgBvAC0AYwBvAG4AdABl
AHgAdAAtAHMAaABpAGYAdAAgACAAIAAgACAAdwBoAGUAdABoAGUAcgAgAHQAbwAgAHUAcwBlACAA
YwBvAG4AdABlAHgAdAAgAHMAaABpAGYAdAAgAG8AbgAgAGkAbgBmAGkAbgBpAHQAZQAgAHQAZQB4
AHQAIABnAGUAbgBlAHIAYQB0AGkAbwBuACAAKABkAGUAZgBhAHUAbAB0ADoADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBDAE8ATgBUAEUAWABUAF8AUwBIAEkA
RgBUACkADQAKAC0AcgAsACAAIAAgACAALQAtAHIAZQB2AGUAcgBzAGUALQBwAHIAbwBtAHAAdAAg
AFAAUgBPAE0AUABUACAAIAAgACAAIAAgACAAIAAgACAAaABhAGwAdAAgAGcAZQBuAGUAcgBhAHQA
aQBvAG4AIABhAHQAIABQAFIATwBNAFAAVAAsACAAcgBlAHQAdQByAG4AIABjAG8AbgB0AHIAbwBs
ACAAaQBuACAAaQBuAHQAZQByAGEAYwB0AGkAdgBlACAAbQBvAGQAZQANAAoALQBzAHAALAAgACAA
IAAtAC0AcwBwAGUAYwBpAGEAbAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABzAHAAZQBjAGkAYQBsACAAdABvAGsAZQBuAHMAIABvAHUAdABwAHUAdAAgAGUA
bgBhAGIAbABlAGQAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGYAYQBsAHMAZQApAA0ACgAtAC0AdwBh
AHIAbQB1AHAALAAgAC0ALQBuAG8ALQB3AGEAcgBtAHUAcAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAHcAaABlAHQAaABlAHIAIAB0AG8AIABwAGUAcgBmAG8AcgBtACAAdwBh
AHIAbQB1AHAAIAB3AGkAdABoACAAYQBuACAAZQBtAHAAdAB5ACAAcgB1AG4AIAAoAGQAZQBmAGEA
dQBsAHQAOgAgAGUAbgBhAGIAbABlAGQAKQANAAoALQAtAHMAcABtAC0AaQBuAGYAaQBsAGwAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB1AHMA
ZQAgAFMAdQBmAGYAaQB4AC8AUAByAGUAZgBpAHgALwBNAGkAZABkAGwAZQAgAHAAYQB0AHQAZQBy
AG4AIABmAG8AcgAgAGkAbgBmAGkAbABsACAAKABpAG4AcwB0AGUAYQBkACAAbwBmAA0ACgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgAFAAcgBlAGYAaQB4AC8AUwB1AGYAZgBpAHgALwBNAGkAZABkAGwA
ZQApACAAYQBzACAAcwBvAG0AZQAgAG0AbwBkAGUAbABzACAAcAByAGUAZgBlAHIAIAB0AGgAaQBz
AC4AIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGQAaQBzAGEAYgBsAGUAZAApAA0ACgAtAC0AcABvAG8A
bABpAG4AZwAgAHsAbgBvAG4AZQAsAG0AZQBhAG4ALABjAGwAcwAsAGwAYQBzAHQALAByAGEAbgBr
AH0AIAAgACAAIAAgAHAAbwBvAGwAaQBuAGcAIAB0AHkAcABlACAAZgBvAHIAIABlAG0AYgBlAGQA
ZABpAG4AZwBzACwAIAB1AHMAZQAgAG0AbwBkAGUAbAAgAGQAZQBmAGEAdQBsAHQAIABpAGYAIAB1
AG4AcwBwAGUAYwBpAGYAaQBlAGQADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6
ACAATABMAEEATQBBAF8AQQBSAEcAXwBQAE8ATwBMAEkATgBHACkADQAKAC0AbgBwACwAIAAgACAA
LQAtAHAAYQByAGEAbABsAGUAbAAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAbgB1AG0AYgBlAHIAIABvAGYAIABzAGUAcgB2AGUAcgAgAHMAbABvAHQAcwAgACgA
ZABlAGYAYQB1AGwAdAA6ACAALQAxACwAIAAtADEAIAA9ACAAYQB1AHQAbwApAA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ATgBfAFAAQQBS
AEEATABMAEUATAApAA0ACgAtAGMAYgAsACAAIAAgAC0ALQBjAG8AbgB0AC0AYgBhAHQAYwBoAGkA
bgBnACwAIAAtAG4AbwBjAGIALAAgAC0ALQBuAG8ALQBjAG8AbgB0AC0AYgBhAHQAYwBoAGkAbgBn
AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHcAaABlAHQAaABlAHIAIAB0AG8AIABlAG4AYQBi
AGwAZQAgAGMAbwBuAHQAaQBuAHUAbwB1AHMAIABiAGEAdABjAGgAaQBuAGcAIAAoAGEALgBrAC4A
YQAgAGQAeQBuAGEAbQBpAGMAIABiAGEAdABjAGgAaQBuAGcAKQANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGUAbgBhAGIAbABlAGQAKQANAAoAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEMATwBOAFQAXwBC
AEEAVABDAEgASQBOAEcAKQANAAoALQBtAG0ALAAgACAAIAAtAC0AbQBtAHAAcgBvAGoAIABGAEkA
TABFACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABwAGEAdABoACAAdABv
ACAAYQAgAG0AdQBsAHQAaQBtAG8AZABhAGwAIABwAHIAbwBqAGUAYwB0AG8AcgAgAGYAaQBsAGUA
LgAgAHMAZQBlACAAdABvAG8AbABzAC8AbQB0AG0AZAAvAFIARQBBAEQATQBFAC4AbQBkAA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAG4AbwB0AGUAOgAgAGkAZgAgAC0AaABmACAAaQBzACAAdQBz
AGUAZAAsACAAdABoAGkAcwAgAGEAcgBnAHUAbQBlAG4AdAAgAGMAYQBuACAAYgBlACAAbwBtAGkA
dAB0AGUAZAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEA
XwBBAFIARwBfAE0ATQBQAFIATwBKACkADQAKAC0AbQBtAHUALAAgACAALQAtAG0AbQBwAHIAbwBq
AC0AdQByAGwAIABVAFIATAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAVQBSAEwA
IAB0AG8AIABhACAAbQB1AGwAdABpAG0AbwBkAGEAbAAgAHAAcgBvAGoAZQBjAHQAbwByACAAZgBp
AGwAZQAuACAAcwBlAGUAIAB0AG8AbwBsAHMALwBtAHQAbQBkAC8AUgBFAEEARABNAEUALgBtAGQA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcA
XwBNAE0AUABSAE8ASgBfAFUAUgBMACkADQAKAC0ALQBtAG0AcAByAG8AagAtAGEAdQB0AG8ALAAg
AC0ALQBuAG8ALQBtAG0AcAByAG8AagAsACAALQAtAG4AbwAtAG0AbQBwAHIAbwBqAC0AYQB1AHQA
bwANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB3AGgAZQB0AGgAZQByACAAdABvACAAdQBzAGUA
IABtAHUAbAB0AGkAbQBvAGQAYQBsACAAcAByAG8AagBlAGMAdABvAHIAIABmAGkAbABlACAAKABp
AGYAIABhAHYAYQBpAGwAYQBiAGwAZQApACwAIAB1AHMAZQBmAHUAbAAgAHcAaABlAG4ADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAdQBzAGkAbgBnACAALQBoAGYAIAAoAGQAZQBmAGEAdQBsAHQA
OgAgAGUAbgBhAGIAbABlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoA
IABMAEwAQQBNAEEAXwBBAFIARwBfAE0ATQBQAFIATwBKAF8AQQBVAFQATwApAA0ACgAtAC0AbQBt
AHAAcgBvAGoALQBvAGYAZgBsAG8AYQBkACwAIAAtAC0AbgBvAC0AbQBtAHAAcgBvAGoALQBvAGYA
ZgBsAG8AYQBkACAAIAAgAHcAaABlAHQAaABlAHIAIAB0AG8AIABlAG4AYQBiAGwAZQAgAEcAUABV
ACAAbwBmAGYAbABvAGEAZABpAG4AZwAgAGYAbwByACAAbQB1AGwAdABpAG0AbwBkAGEAbAAgAHAA
cgBvAGoAZQBjAHQAbwByACAAKABkAGUAZgBhAHUAbAB0ADoADQAKACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAZQBuAGEAYgBsAGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYA
OgAgAEwATABBAE0AQQBfAEEAUgBHAF8ATQBNAFAAUgBPAEoAXwBPAEYARgBMAE8AQQBEACkADQAK
AC0AbQBtAGQAZQB2ACwAIAAtAC0AbQBtAHAAcgBvAGoALQBkAGUAdgBpAGMAZQAgAEQARQBWAEkA
QwBFACAAIAAgACAAIAAgACAAIAAgACAAZABlAHYAaQBjAGUAIAB0AG8AIAB1AHMAZQAgAGYAbwBy
ACAAbQB1AGwAdABpAG0AbwBkAGEAbAAgAHAAcgBvAGoAZQBjAHQAbwByACAAKABuAG8AbgBlACAA
PQAgAGQAbwBuACcAdAAgAG8AZgBmAGwAbwBhAGQALAAgAGQAZQBmAGEAdQBsAHQAOgANAAoAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIABmAG8AbABsAG8AdwBzACAALQAtAGQAZQB2AGkAYwBlACkADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAdQBzAGUAIAAtAC0AbABpAHMAdAAtAGQAZQB2AGkAYwBl
AHMAIAB0AG8AIABzAGUAZQAgAGEAIABsAGkAcwB0ACAAbwBmACAAYQB2AGEAaQBsAGEAYgBsAGUA
IABkAGUAdgBpAGMAZQBzAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAE0A
VABNAEQAXwBCAEEAQwBLAEUATgBEAF8ARABFAFYASQBDAEUAKQANAAoALQAtAGkAbQBhAGcAZQAt
AG0AaQBuAC0AdABvAGsAZQBuAHMAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABtAGkAbgBpAG0AdQBtACAAbgB1AG0AYgBlAHIAIABvAGYAIAB0AG8AawBlAG4AcwAg
AGUAYQBjAGgAIABpAG0AYQBnAGUAIABjAGEAbgAgAHQAYQBrAGUALAAgAG8AbgBsAHkAIAB1AHMA
ZQBkACAAYgB5ACAAdgBpAHMAaQBvAG4ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbQBvAGQA
ZQBsAHMAIAB3AGkAdABoACAAZAB5AG4AYQBtAGkAYwAgAHIAZQBzAG8AbAB1AHQAaQBvAG4AIAAo
AGQAZQBmAGEAdQBsAHQAOgAgAHIAZQBhAGQAIABmAHIAbwBtACAAbQBvAGQAZQBsACkADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBJAE0A
QQBHAEUAXwBNAEkATgBfAFQATwBLAEUATgBTACkADQAKAC0ALQBpAG0AYQBnAGUALQBtAGEAeAAt
AHQAbwBrAGUAbgBzACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
bQBhAHgAaQBtAHUAbQAgAG4AdQBtAGIAZQByACAAbwBmACAAdABvAGsAZQBuAHMAIABlAGEAYwBo
ACAAaQBtAGEAZwBlACAAYwBhAG4AIAB0AGEAawBlACwAIABvAG4AbAB5ACAAdQBzAGUAZAAgAGIA
eQAgAHYAaQBzAGkAbwBuAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG0AbwBkAGUAbABzACAA
dwBpAHQAaAAgAGQAeQBuAGEAbQBpAGMAIAByAGUAcwBvAGwAdQB0AGkAbwBuACAAKABkAGUAZgBh
AHUAbAB0ADoAIAByAGUAYQBkACAAZgByAG8AbQAgAG0AbwBkAGUAbAApAA0ACgAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ASQBNAEEARwBFAF8A
TQBBAFgAXwBUAE8ASwBFAE4AUwApAA0ACgAtAC0AbQB0AG0AZAAtAGIAYQB0AGMAaAAtAG0AYQB4
AC0AdABvAGsAZQBuAHMAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG0AYQB4AGkA
bQB1AG0AIABuAHUAbQBiAGUAcgAgAG8AZgAgAGkAbQBhAGcAZQAgAHQAbwBrAGUAbgBzACAAcABl
AHIAIABiAGEAdABjAGgAIAB3AGgAZQBuACAAZQBuAGMAbwBkAGkAbgBnACAAaQBtAGEAZwBlAHMA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABkAGUAZgBhAHUAbAB0ADoAIAAxADAAMgA0ACkA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcA
XwBNAFQATQBEAF8AQgBBAFQAQwBIAF8ATQBBAFgAXwBUAE8ASwBFAE4AUwApAA0ACgAtAC0AdgBp
AGQAZQBvAC0AZgBwAHMAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAHQAYQByAGcAZQB0ACAAdgBpAGQAZQBvACAAZgByAGEAbQBlACAAcgBh
AHQAZQAgACgAZABlAGYAYQB1AGwAdAA6ACAANAAuADAAKQANAAoAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFYASQBEAEUATwBfAEYAUABTACkA
DQAKAC0ALQB2AGkAZABlAG8ALQB0AGkAbQBlAHMAdABhAG0AcAAtAGkAbgB0AGUAcgB2AGEAbAAg
AE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAaQBuAHQAZQByAHYAYQBsACAAaQBuACAAbQBpAGwA
bABpAHMAZQBjAG8AbgBkAHMAIABiAGUAdAB3AGUAZQBuACAAdABlAHgAdAAgAHQAaQBtAGUAcwB0
AGEAbQBwAHMAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADUAMAAwADAAKQANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFYASQBEAEUATwBfAFQA
SQBNAEUAUwBUAEEATQBQAF8ASQBOAFQARQBSAFYAQQBMACkADQAKAC0ALQB2AGkAZABlAG8ALQBm
AGYAbQBwAGUAZwAtAGQAaQByACAARABJAFIAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAcABhAHQAaAAgAHQAbwAgAHQAaABlACAAZABpAHIAZQBjAHQAbwByAHkAIABjAG8AbgB0
AGEAaQBuAGkAbgBnACAAZgBmAG0AcABlAGcAIABhAG4AZAAgAGYAZgBwAHIAbwBiAGUAIAAoAGQA
ZQBmAGEAdQBsAHQAOgAgAHMAZQBhAHIAYwBoAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGkA
bgAgAFAAQQBUAEgAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwA
QQBNAEEAXwBBAFIARwBfAFYASQBEAEUATwBfAEYARgBNAFAARQBHAF8ARABJAFIAKQANAAoALQBh
ACwAIAAgACAAIAAtAC0AYQBsAGkAYQBzACAAUwBUAFIASQBOAEcAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIABzAGUAdAAgAG0AbwBkAGUAbAAgAG4AYQBtAGUAIABhAGwAaQBh
AHMAZQBzACwAIABjAG8AbQBtAGEALQBzAGUAcABhAHIAYQB0AGUAZAAgACgAdABvACAAYgBlACAA
dQBzAGUAZAAgAGIAeQAgAEEAUABJACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4A
dgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBBAEwASQBBAFMAKQANAAoALQAtAHQAYQBnAHMAIABT
AFQAUgBJAE4ARwAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABzAGUAdAAgAG0AbwBkAGUAbAAgAHQAYQBnAHMALAAgAGMAbwBtAG0AYQAtAHMAZQBw
AGEAcgBhAHQAZQBkACAAKABpAG4AZgBvAHIAbQBhAHQAaQBvAG4AYQBsACwAIABuAG8AdAAgAHUA
cwBlAGQAIABmAG8AcgAgAHIAbwB1AHQAaQBuAGcAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFQAQQBHAFMAKQANAAoALQAtAGUAbQBi
AGQALQBuAG8AcgBtAGEAbABpAHoAZQAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIABuAG8AcgBtAGEAbABpAHMAYQB0AGkAbwBuACAAZgBvAHIAIABlAG0AYgBl
AGQAZABpAG4AZwBzACAAKABkAGUAZgBhAHUAbAB0ADoAIAAyACkAIAAoAC0AMQA9AG4AbwBuAGUA
LAAgADAAPQBtAGEAeAAgAGEAYgBzAG8AbAB1AHQAZQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IABpAG4AdAAxADYALAAgADEAPQB0AGEAeABpAGMAYQBiACwAIAAyAD0AZQB1AGMAbABpAGQAZQBh
AG4ALAAgAD4AMgA9AHAALQBuAG8AcgBtACkADQAKAC0ALQBoAG8AcwB0ACAASABPAFMAVAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAASQBQ
ACAAYQBkAGQAcgBlAHMAcwBlAHMAIAB0AG8AIABsAGkAcwB0AGUAbgAgAG8AbgAsACAAYwBvAG0A
bQBhAC0AcwBlAHAAYQByAGEAdABlAGQALAAgAG8AcgAgAFUATgBJAFgAIABzAG8AYwBrAGUAdAAg
AHAAYQB0AGgAcwANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABlAG4AZABpAG4AZwAgAGkAbgAg
AC4AcwBvAGMAawA7ACAAdwBpAHQAaAAgAG0AdQBsAHQAaQBwAGwAZQAgAFQAQwBQACAAYQBkAGQA
cgBlAHMAcwBlAHMALAAgADoAOgAgAGIAaQBuAGQAcwAgAEkAUAB2ADYAIABvAG4AbAB5ADsADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAbwB2AGUAcgBsAGEAcABwAGkAbgBnACAAYQBkAGQAcgBl
AHMAcwBlAHMAIAByAGUAcwB1AGwAdAAgAGkAbgAgAHUAbgBkAGUAZgBpAG4AZQBkACAAYgBlAGgA
YQB2AGkAbwByACAAKABkAGUAZgBhAHUAbAB0ADoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
MQAyADcALgAwAC4AMAAuADEAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoA
IABMAEwAQQBNAEEAXwBBAFIARwBfAEgATwBTAFQAKQANAAoALQAtAHAAbwByAHQAIABQAE8AUgBU
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IABwAG8AcgB0ACAAdABvACAAbABpAHMAdABlAG4AIAAoAGQAZQBmAGEAdQBsAHQAOgAgADkAOQAz
ADEAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBB
AFIARwBfAFAATwBSAFQAKQANAAoALQAtAHIAZQB1AHMAZQAtAHAAbwByAHQAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABhAGwAbABvAHcAIABt
AHUAbAB0AGkAcABsAGUAIABzAG8AYwBrAGUAdABzACAAdABvACAAYgBpAG4AZAAgAHQAbwAgAHQA
aABlACAAcwBhAG0AZQAgAHAAbwByAHQAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGQAaQBzAGEAYgBs
AGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBf
AEEAUgBHAF8AUgBFAFUAUwBFAF8AUABPAFIAVAApAA0ACgAtAC0AcABhAHQAaAAgAFAAQQBUAEgA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AHAAYQB0AGgAIAB0AG8AIABzAGUAcgB2AGUAIABzAHQAYQB0AGkAYwAgAGYAaQBsAGUAcwAgAGYA
cgBvAG0AIAAoAGQAZQBmAGEAdQBsAHQAOgAgACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
KABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBTAFQAQQBUAEkAQwBfAFAAQQBUAEgAKQAN
AAoALQAtAGMAbwByAHMALQBvAHIAaQBnAGkAbgBzACAATwBSAEkARwBJAE4AUwAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIABjAG8AbQBtAGEALQBzAGUAcABhAHIAYQB0AGUAZAAg
AGwAaQBzAHQAIABvAGYAIABhAGwAbABvAHcAZQBkACAAbwByAGkAZwBpAG4AcwAgAGYAbwByACAA
QwBPAFIAUwAgACgAZABlAGYAYQB1AGwAdAA6ACAAKgApAA0ACgAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAGkAZgAgAHMAZQB0ACAAdABvACAAcwBwAGUAYwBpAGEAbAAgAHYAYQBsAHUAZQAgACcAbABv
AGMAYQBsAGgAbwBzAHQAJwAsACAAcgBlAGYAbABlAGMAdAAgAHQAaABlACAATwByAGkAZwBpAG4A
IABoAGUAYQBkAGUAcgAgAG8AbgBsAHkAIABpAGYADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
aQB0ACAAaQBzACAAbABvAGMAYQBsAGgAbwBzAHQADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
KABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBDAE8AUgBTAF8ATwBSAEkARwBJAE4AUwAp
AA0ACgAtAC0AYwBvAHIAcwAtAG0AZQB0AGgAbwBkAHMAIABNAEUAVABIAE8ARABTACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGMAbwBtAG0AYQAtAHMAZQBwAGEAcgBhAHQAZQBk
ACAAbABpAHMAdAAgAG8AZgAgAGEAbABsAG8AdwBlAGQAIABtAGUAdABoAG8AZABzACAAZgBvAHIA
IABDAE8AUgBTACAAKABkAGUAZgBhAHUAbAB0ADoAIABHAEUAVAAsACAAUABPAFMAVAAsAA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAEQARQBMAEUAVABFACwAIABPAFAAVABJAE8ATgBTACkADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBD
AE8AUgBTAF8ATQBFAFQASABPAEQAUwApAA0ACgAtAC0AYwBvAHIAcwAtAGgAZQBhAGQAZQByAHMA
IABIAEUAQQBEAEUAUgBTACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGMAbwBt
AG0AYQAtAHMAZQBwAGEAcgBhAHQAZQBkACAAbABpAHMAdAAgAG8AZgAgAGEAbABsAG8AdwBlAGQA
IABoAGUAYQBkAGUAcgBzACAAZgBvAHIAIABDAE8AUgBTACAAKABkAGUAZgBhAHUAbAB0ADoAIAAq
ACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBS
AEcAXwBDAE8AUgBTAF8ASABFAEEARABFAFIAUwApAA0ACgAtAC0AYwBvAHIAcwAtAGMAcgBlAGQA
ZQBuAHQAaQBhAGwAcwAsACAALQAtAG4AbwAtAGMAbwByAHMALQBjAHIAZQBkAGUAbgB0AGkAYQBs
AHMADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdwBoAGUAdABoAGUAcgAgAHQAbwAgAGEAbABs
AG8AdwAgAGMAcgBlAGQAZQBuAHQAaQBhAGwAcwAgAGYAbwByACAAQwBPAFIAUwAgACgAZABlAGYA
YQB1AGwAdAA6ACAAZQBuAGEAYgBsAGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4A
bwB0AGUAOgAgAGkAZgAgAHQAaABpAHMAIABpAHMAIABlAG4AYQBiAGwAZQBkACAAYQBuAGQAIAAt
AC0AYwBvAHIAcwAtAG8AcgBpAGcAaQBuAHMAIABpAHMAIABzAGUAdAAgAHQAbwAgACoAIAAoAGQA
ZQBmAGEAdQBsAHQAKQAsACAAdABoAGUADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAATwByAGkA
ZwBpAG4AIABoAGUAYQBkAGUAcgAgAHcAaQBsAGwAIABiAGUAIABlAGMAaABvAGUAZAAgAGIAYQBj
AGsALAAgAGEAbgBkACAAYwByAGUAZABlAG4AdABpAGEAbABzACAAdwBpAGwAbAAgAGEAbAB3AGEA
eQBzACAAYgBlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGEAbABsAG8AdwBlAGQADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBDAE8A
UgBTAF8AQwBSAEUARABFAE4AVABJAEEATABTACkADQAKAC0ALQBhAHAAaQAtAHAAcgBlAGYAaQB4
ACAAUABSAEUARgBJAFgAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
cAByAGUAZgBpAHgAIABwAGEAdABoACAAdABoAGUAIABzAGUAcgB2AGUAcgAgAHMAZQByAHYAZQBz
ACAAZgByAG8AbQAsACAAdwBpAHQAaABvAHUAdAAgAHQAaABlACAAdAByAGEAaQBsAGkAbgBnACAA
cwBsAGEAcwBoAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZABlAGYAYQB1AGwAdAA6ACAA
KQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIA
RwBfAEEAUABJAF8AUABSAEUARgBJAFgAKQANAAoALQAtAHUAaQAtAGMAbwBuAGYAaQBnACwAIAAt
AC0AdwBlAGIAdQBpAC0AYwBvAG4AZgBpAGcAIABKAFMATwBOACAAIAAgACAAIAAgACAAIABKAFMA
TwBOACAAdABoAGEAdAAgAHAAcgBvAHYAaQBkAGUAcwAgAGQAZQBmAGEAdQBsAHQAIABVAEkAIABz
AGUAdAB0AGkAbgBnAHMAIAAoAG8AdgBlAHIAcgBpAGQAZQBzACAAVQBJACAAZABlAGYAYQB1AGwA
dABzACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8A
QQBSAEcAXwBVAEkAXwBDAE8ATgBGAEkARwApAA0ACgAtAC0AdQBpAC0AYwBvAG4AZgBpAGcALQBm
AGkAbABlACwAIAAtAC0AdwBlAGIAdQBpAC0AYwBvAG4AZgBpAGcALQBmAGkAbABlACAAUABBAFQA
SAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABKAFMATwBOACAAZgBpAGwAZQAgAHQAaABhAHQA
IABwAHIAbwB2AGkAZABlAHMAIABkAGUAZgBhAHUAbAB0ACAAVQBJACAAcwBlAHQAdABpAG4AZwBz
ACAAKABvAHYAZQByAHIAaQBkAGUAcwAgAFUASQAgAGQAZQBmAGEAdQBsAHQAcwApAA0ACgAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AVQBJAF8A
QwBPAE4ARgBJAEcAXwBGAEkATABFACkADQAKAC0ALQB1AGkALQBtAGMAcAAtAHAAcgBvAHgAeQAs
ACAALQAtAHcAZQBiAHUAaQAtAG0AYwBwAC0AcAByAG8AeAB5ACwAIAAtAC0AbgBvAC0AdQBpAC0A
bQBjAHAALQBwAHIAbwB4AHkALAAgAC0ALQBuAG8ALQB3AGUAYgB1AGkALQBtAGMAcAAtAHAAcgBv
AHgAeQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABlAHgAcABlAHIAaQBtAGUAbgB0AGEAbAA6
ACAAdwBoAGUAdABoAGUAcgAgAHQAbwAgAGUAbgBhAGIAbABlACAATQBDAFAAIABDAE8AUgBTACAA
cAByAG8AeAB5ACAALQAgAGQAbwAgAG4AbwB0ACAAZQBuAGEAYgBsAGUAIABpAG4ADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAdQBuAHQAcgB1AHMAdABlAGQAIABlAG4AdgBpAHIAbwBuAG0AZQBu
AHQAcwAgACgAZABlAGYAYQB1AGwAdAA6ACAAZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBVAEkAXwBNAEMA
UABfAFAAUgBPAFgAWQApAA0ACgAtAC0AdABvAG8AbABzACAAVABPAE8ATAAxACwAVABPAE8ATAAy
ACwALgAuAC4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGUAeABwAGUAcgBpAG0A
ZQBuAHQAYQBsADoAIAB3AGgAZQB0AGgAZQByACAAdABvACAAZQBuAGEAYgBsAGUAIABiAHUAaQBs
AHQALQBpAG4AIAB0AG8AbwBsAHMAIABmAG8AcgAgAEEASQAgAGEAZwBlAG4AdABzACAALQAgAGQA
bwAgAG4AbwB0AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGUAbgBhAGIAbABlACAAaQBuACAA
dQBuAHQAcgB1AHMAdABlAGQAIABlAG4AdgBpAHIAbwBuAG0AZQBuAHQAcwAgACgAZABlAGYAYQB1
AGwAdAA6ACAAbgBvACAAdABvAG8AbABzACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcwBw
AGUAYwBpAGYAeQAgACIAYQBsAGwAIgAgAHQAbwAgAGUAbgBhAGIAbABlACAAYQBsAGwAIAB0AG8A
bwBsAHMADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAYQB2AGEAaQBsAGEAYgBsAGUAIAB0AG8A
bwBsAHMAOgAgAHIAZQBhAGQAXwBmAGkAbABlACwAIABmAGkAbABlAF8AZwBsAG8AYgBfAHMAZQBh
AHIAYwBoACwAIABnAHIAZQBwAF8AcwBlAGEAcgBjAGgALAANAAoAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIABlAHgAZQBjAF8AcwBoAGUAbABsAF8AYwBvAG0AbQBhAG4AZAAsACAAdwByAGkAdABlAF8A
ZgBpAGwAZQAsACAAZQBkAGkAdABfAGYAaQBsAGUALAAgAGcAZQB0AF8AaQBuAGYAbwANAAoAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIABuAG8AdABlADoAIABmAG8AcgAgAHMAZQBjAHUAcgBpAHQAeQAg
AHIAZQBhAHMAbwBuAHMALAAgAHQAaABpAHMAIAB3AGkAbABsACAAbABpAG0AaQB0ACAALQAtAGMA
bwByAHMALQBvAHIAaQBnAGkAbgBzACAAdABvAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGwA
bwBjAGEAbABoAG8AcwB0ACAAYgB5ACAAZABlAGYAYQB1AGwAdAANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFQATwBPAEwAUwApAA0ACgAt
AC0AdABvAG8AbABzAC0AcgB1AG4AdABpAG0AZQAgAE8AUABUAEkATwBOACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAGUAeABwAGUAcgBpAG0AZQBuAHQAYQBsADoAIAByAHUAbgAg
AHQAbwBvAGwAcwAgAGkAbgAgAGEAIABzAGUAcABhAHIAYQB0AGUAIAByAHUAbgB0AGkAbQBlACAA
ZQBuAHYAaQByAG8AbgBtAGUAbgB0ACAAKABkAGUAZgBhAHUAbAB0ADoADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAbgBvAG4AZQAsACAAdQBzAGUAIABoAG8AcwB0ACAAZQBuAHYAaQByAG8AbgBt
AGUAbgB0ACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAYQB2AGEAaQBsAGEAYgBsAGUAIABv
AHAAdABpAG8AbgBzADoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAJwBkAG8AYwBrAGUAcgA6
ADwAaQBtAGEAZwBlAD4AJwAsACAAJwBwAG8AZABtAGEAbgA6ADwAaQBtAGEAZwBlAD4AJwA6ACAA
cwBwAGkAbgAgAHUAcAAgAGEAIABuAGUAdwAgAGMAbwBuAHQAYQBpAG4AZQByACAAYQBuAGQAIABy
AGUAdQBzAGUADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAaQB0ACAAZgBvAHIAIABhAGwAbAAg
AGkAbgB2AG8AYwBhAHQAaQBvAG4AcwAsACAAYwBsAGUAYQBuACAAdQBwACAAbwBuACAAcwBlAHIA
dgBlAHIAIABlAHgAaQB0AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACcAZABvAGMAawBlAHIA
LQBjAG8AbgB0AGEAaQBuAGUAcgA6ADwAaQBkAD4AJwAsACAAJwBwAG8AZABtAGEAbgAtAGMAbwBu
AHQAYQBpAG4AZQByADoAPABpAGQAPgAnADoAIAB1AHMAZQAgAGEAbgAgAGUAeABpAHMAdABpAG4A
ZwANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABjAG8AbgB0AGEAaQBuAGUAcgAgAGIAeQAgAEkA
RAAsACAAdwBvAG4AJwB0ACAAcwB0AG8AcAAgAG8AbgAgAHMAZQByAHYAZQByACAAZQB4AGkAdAAN
AAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAnAHMAcwBoADoAPAB0AGEAcgBnAGUAdAA+ACcAOgAg
AHIAdQBuACAAdABvAG8AbABzACAAbwBuACAAYQAgAHIAZQBtAG8AdABlACAAUABPAFMASQBYACAA
aABvAHMAdAAgAG8AdgBlAHIAIABTAFMASAAsACAAawBlAHkALQBiAGEAcwBlAGQADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAYQB1AHQAaAAgAGEAbgBkACAAYQAgAHQAcgB1AHMAdABlAGQAIABo
AG8AcwB0ACAAawBlAHkAIABhAHIAZQAgAHIAZQBxAHUAaQByAGUAZAANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBN
AEEAXwBBAFIARwBfAFQATwBPAEwAUwBfAFIAVQBOAFQASQBNAEUAKQANAAoALQAtAG0AYwBwAC0A
cwBlAHIAdgBlAHIAcwAtAGMAbwBuAGYAaQBnACAAUABBAFQASAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABlAHgAcABlAHIAaQBtAGUAbgB0AGEAbAA6ACAAcABhAHQAaAAgAHQAbwAgAEoA
UwBPAE4AIABmAGkAbABlACAAdwBpAHQAaAAgAE0AQwBQACAAcwBlAHIAdgBlAHIAIABkAGUAZgBp
AG4AaQB0AGkAbwBuAHMADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABDAHUAcgBzAG8AcgAt
AGMAbwBtAHAAYQB0AGkAYgBsAGUAIABmAG8AcgBtAGEAdAApACAALQAgAGQAbwAgAG4AbwB0ACAA
ZQBuAGEAYgBsAGUAIABpAG4AIAB1AG4AdAByAHUAcwB0AGUAZAAgAGUAbgB2AGkAcgBvAG4AbQBl
AG4AdABzAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZABlAGYAYQB1AGwAdAA6ACAAbgBv
AG4AZQApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG4AbwB0AGUAOgAgAGYAbwByACAAcwBl
AGMAdQByAGkAdAB5ACAAcgBlAGEAcwBvAG4AcwAsACAAdABoAGkAcwAgAHcAaQBsAGwAIABsAGkA
bQBpAHQAIAAtAC0AYwBvAHIAcwAtAG8AcgBpAGcAaQBuAHMAIAB0AG8ADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAbABvAGMAYQBsAGgAbwBzAHQAIABiAHkAIABkAGUAZgBhAHUAbAB0AA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ATQBD
AFAAXwBTAEUAUgBWAEUAUgBTAF8AQwBPAE4ARgBJAEcAKQANAAoALQAtAG0AYwBwAC0AcwBlAHIA
dgBlAHIAcwAtAGoAcwBvAG4AIABKAFMATwBOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIABlAHgAcABlAHIAaQBtAGUAbgB0AGEAbAA6ACAAaQBuAGwAaQBuAGUAIABKAFMATwBOACAA
dwBpAHQAaAAgAE0AQwBQACAAcwBlAHIAdgBlAHIAIABkAGUAZgBpAG4AaQB0AGkAbwBuAHMADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAKABDAHUAcgBzAG8AcgAtAGMAbwBtAHAAYQB0AGkAYgBs
AGUAIABmAG8AcgBtAGEAdAApACAALQAgAGQAbwAgAG4AbwB0ACAAZQBuAGEAYgBsAGUAIABpAG4A
IAB1AG4AdAByAHUAcwB0AGUAZAAgAGUAbgB2AGkAcgBvAG4AbQBlAG4AdABzAA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACgAZABlAGYAYQB1AGwAdAA6ACAAbgBvAG4AZQApAA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAG4AbwB0AGUAOgAgAGYAbwByACAAcwBlAGMAdQByAGkAdAB5ACAAcgBl
AGEAcwBvAG4AcwAsACAAdABoAGkAcwAgAHcAaQBsAGwAIABsAGkAbQBpAHQAIAAtAC0AYwBvAHIA
cwAtAG8AcgBpAGcAaQBuAHMAIAB0AG8ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbABvAGMA
YQBsAGgAbwBzAHQAIABiAHkAIABkAGUAZgBhAHUAbAB0AA0ACgAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8ATQBDAFAAXwBTAEUAUgBWAEUAUgBT
AF8ASgBTAE8ATgApAA0ACgAtAGEAZwAsACAAIAAgAC0ALQBhAGcAZQBuAHQALAAgAC0AbgBvAC0A
YQBnACwAIAAtAC0AbgBvAC0AYQBnAGUAbgB0ACAAIAAgACAAIAAgAHcAaABlAHQAaABlAHIAIAB0
AG8AIABlAG4AYQBiAGwAZQAgAEMATwBSAFMAIABwAHIAbwB4AHkAIABhAG4AZAAgAGEAbABsACAA
YgB1AGkAbAB0AC0AaQBuACAAdABvAG8AbABzACAALQAgAGQAbwAgAG4AbwB0ACAAZQBuAGEAYgBs
AGUAIABpAG4ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdQBuAHQAcgB1AHMAdABlAGQAIABl
AG4AdgBpAHIAbwBuAG0AZQBuAHQAcwAgACgAZABlAGYAYQB1AGwAdAA6ACAAZABpAHMAYQBiAGwA
ZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbgBvAHQAZQA6ACAAZgBvAHIAIABzAGUA
YwB1AHIAaQB0AHkAIAByAGUAYQBzAG8AbgBzACwAIAB0AGgAaQBzACAAdwBpAGwAbAAgAGwAaQBt
AGkAdAAgAC0ALQBjAG8AcgBzAC0AbwByAGkAZwBpAG4AcwAgAHQAbwANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABsAG8AYwBhAGwAaABvAHMAdAAgAGIAeQAgAGQAZQBmAGEAdQBsAHQADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBBAEcA
RQBOAFQAKQANAAoALQAtAHUAaQAsACAAIAAtAC0AdwBlAGIAdQBpACwAIAAtAC0AbgBvAC0AdQBp
ACwAIAAtAC0AbgBvAC0AdwBlAGIAdQBpACAAIAAgACAAIAB3AGgAZQB0AGgAZQByACAAdABvACAA
ZQBuAGEAYgBsAGUAIAB0AGgAZQAgAFcAZQBiACAAVQBJACAAKABkAGUAZgBhAHUAbAB0ADoAIABl
AG4AYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABM
AEEATQBBAF8AQQBSAEcAXwBVAEkAKQANAAoALQAtAGMAbwBuAG4AZQBjAHQAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAeABw
AGUAcgBpAG0AZQBuAHQAYQBsACkAIABvAHAAZQBuACAAYQAgAHAAZQBlAHIALQB0AG8ALQBwAGUA
ZQByACAAdAB1AG4AbgBlAGwAIABmAG8AcgAgAHMAZQByAHYAZQByACAAdQBzAGkAbgBnAA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAGwAbABhAG0AYQAtAGMAbwBuAG4AZQBjAHQAIAAoAGQAZQBm
AGEAdQBsAHQAOgAgAGQAaQBzAGEAYgBsAGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AQwBPAE4ATgBFAEMAVAApAA0ACgAtAC0A
YwBvAG4AbgBlAGMAdAAtAGMAbwBkAGUAIABDAE8ARABFACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgAG0AYQBuAHUAYQBsAGwAeQAgAHMAcABlAGMAaQBmAHkAIABhACAA
NAAwAC0AYwBoAGEAcgBhAGMAdABlAHIAIABjAG8AZABlACAAZgBvAHIAIAAtAC0AYwBvAG4AbgBl
AGMAdAAgACgAZABlAGYAYQB1AGwAdAA6ACAAZwBlAG4AZQByAGEAdABlAA0ACgAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgAGEAIABuAGUAdwAgAG8AbgBlACAAZgBvAHIAIABlAGEAYwBoACAAcgB1AG4A
KQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIA
RwBfAEMATwBOAE4ARQBDAFQAXwBDAE8ARABFACkADQAKAC0ALQBlAG0AYgBlAGQAZABpAG4AZwAs
ACAALQAtAGUAbQBiAGUAZABkAGkAbgBnAHMAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
cgBlAHMAdAByAGkAYwB0ACAAdABvACAAbwBuAGwAeQAgAHMAdQBwAHAAbwByAHQAIABlAG0AYgBl
AGQAZABpAG4AZwAgAHUAcwBlACAAYwBhAHMAZQA7ACAAdQBzAGUAIABvAG4AbAB5ACAAdwBpAHQA
aAAgAGQAZQBkAGkAYwBhAHQAZQBkAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGUAbQBiAGUA
ZABkAGkAbgBnACAAbQBvAGQAZQBsAHMAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGQAaQBzAGEAYgBs
AGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBf
AEEAUgBHAF8ARQBNAEIARQBEAEQASQBOAEcAUwApAA0ACgAtAC0AcgBlAHIAYQBuAGsALAAgAC0A
LQByAGUAcgBhAG4AawBpAG4AZwAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AGUAbgBhAGIAbABlACAAcgBlAHIAYQBuAGsAaQBuAGcAIABlAG4AZABwAG8AaQBuAHQAIABvAG4A
IABzAGUAcgB2AGUAcgAgACgAZABlAGYAYQB1AGwAdAA6ACAAZABpAHMAYQBiAGwAZQBkACkADQAK
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBS
AEUAUgBBAE4ASwBJAE4ARwApAA0ACgAtAC0AYQBwAGkALQBrAGUAeQAgAEsARQBZACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAEEAUABJACAAawBl
AHkAIAB0AG8AIAB1AHMAZQAgAGYAbwByACAAYQB1AHQAaABlAG4AdABpAGMAYQB0AGkAbwBuACwA
IABtAHUAbAB0AGkAcABsAGUAIABrAGUAeQBzACAAYwBhAG4AIABiAGUAIABwAHIAbwB2AGkAZABl
AGQAIABhAHMAIABhAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGMAbwBtAG0AYQAtAHMAZQBw
AGEAcgBhAHQAZQBkACAAbABpAHMAdAAgACgAZABlAGYAYQB1AGwAdAA6ACAAbgBvAG4AZQApAA0A
CgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUABJAF8A
SwBFAFkAKQANAAoALQAtAGEAcABpAC0AawBlAHkALQBmAGkAbABlACAARgBOAEEATQBFACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABwAGEAdABoACAAdABvACAAZgBpAGwA
ZQAgAGMAbwBuAHQAYQBpAG4AaQBuAGcAIABBAFAASQAgAGsAZQB5AHMALAAgAG8AbgBlACAAcABl
AHIAIABsAGkAbgBlADsAIABsAGkAbgBlAHMAIABzAHQAYQByAHQAaQBuAGcAIAB3AGkAdABoACAA
YQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABoAGEAcwBoACAAYQByAGUAIAB0AHIAZQBhAHQA
ZQBkACAAYQBzACAAYwBvAG0AbQBlAG4AdABzACAAKABkAGUAZgBhAHUAbAB0ADoAIABuAG8AbgBl
ACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBS
AEcAXwBBAFAASQBfAEsARQBZAF8ARgBJAEwARQApAA0ACgAtAC0AcwBzAGwALQBrAGUAeQAtAGYA
aQBsAGUAIABGAE4AQQBNAEUAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AHAAYQB0AGgAIAB0AG8AIABmAGkAbABlACAAYQAgAFAARQBNAC0AZQBuAGMAbwBkAGUAZAAgAFMA
UwBMACAAcAByAGkAdgBhAHQAZQAgAGsAZQB5AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgA
ZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8AUwBTAEwAXwBLAEUAWQBfAEYASQBMAEUAKQAN
AAoALQAtAHMAcwBsAC0AYwBlAHIAdAAtAGYAaQBsAGUAIABGAE4AQQBNAEUAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIABwAGEAdABoACAAdABvACAAZgBpAGwAZQAgAGEAIABQ
AEUATQAtAGUAbgBjAG8AZABlAGQAIABTAFMATAAgAGMAZQByAHQAaQBmAGkAYwBhAHQAZQANAAoA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAFMA
UwBMAF8AQwBFAFIAVABfAEYASQBMAEUAKQANAAoALQAtAGMAaABhAHQALQB0AGUAbQBwAGwAYQB0
AGUALQBrAHcAYQByAGcAcwAgAFMAVABSAEkATgBHACAAIAAgACAAIAAgACAAIAAgACAAIABzAGUA
dABzACAAYQBkAGQAaQB0AGkAbwBuAGEAbAAgAHAAYQByAGEAbQBzACAAZgBvAHIAIAB0AGgAZQAg
AGoAcwBvAG4AIAB0AGUAbQBwAGwAYQB0AGUAIABwAGEAcgBzAGUAcgAsACAAbQB1AHMAdAAgAGIA
ZQAgAGEAIAB2AGEAbABpAGQADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAagBzAG8AbgAgAG8A
YgBqAGUAYwB0ACAAcwB0AHIAaQBuAGcALAAgAGUALgBnAC4AIAAnAHsAIgBrAGUAeQAxACIAOgAi
AHYAYQBsAHUAZQAxACIALAAiAGsAZQB5ADIAIgA6ACIAdgBhAGwAdQBlADIAIgB9ACcADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBDAEgA
QQBUAF8AVABFAE0AUABMAEEAVABFAF8ASwBXAEEAUgBHAFMAKQANAAoALQB0AG8ALAAgACAAIAAt
AC0AdABpAG0AZQBvAHUAdAAgAE4AIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABzAGUAcgB2AGUAcgAgAHIAZQBhAGQALwB3AHIAaQB0AGUAIAB0AGkAbQBlAG8AdQB0
ACAAaQBuACAAcwBlAGMAbwBuAGQAcwAgACgAZABlAGYAYQB1AGwAdAA6ACAAMwA2ADAAMAApAA0A
CgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBHAF8A
VABJAE0ARQBPAFUAVAApAA0ACgAtAC0AcwBzAGUALQBwAGkAbgBnAC0AaQBuAHQAZQByAHYAYQBs
ACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHMAZQByAHYAZQByACAA
UwBTAEUAIABwAGkAbgBnACAAaQBuAHQAZQByAHYAYQBsACAAaQBuACAAcwBlAGMAbwBuAGQAcwAg
ACgALQAxACAAPQAgAGQAaQBzAGEAYgBsAGUAZAAsACAAZABlAGYAYQB1AGwAdAA6ACAAMwAwACkA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcA
XwBTAFMARQBfAFAASQBOAEcAXwBJAE4AVABFAFIAVgBBAEwAKQANAAoALQAtAHQAaAByAGUAYQBk
AHMALQBoAHQAdABwACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABuAHUAbQBiAGUAcgAgAG8AZgAgAHQAaAByAGUAYQBkAHMAIAB1AHMAZQBkACAAdABv
ACAAcAByAG8AYwBlAHMAcwAgAEgAVABUAFAAIAByAGUAcQB1AGUAcwB0AHMAIAAoAGQAZQBmAGEA
dQBsAHQAOgAgAC0AMQApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwA
TABBAE0AQQBfAEEAUgBHAF8AVABIAFIARQBBAEQAUwBfAEgAVABUAFAAKQANAAoALQAtAGMAYQBj
AGgAZQAtAHAAcgBvAG0AcAB0ACwAIAAtAC0AbgBvAC0AYwBhAGMAaABlAC0AcAByAG8AbQBwAHQA
IAAgACAAIAAgACAAIAB3AGgAZQB0AGgAZQByACAAdABvACAAZQBuAGEAYgBsAGUAIABwAHIAbwBt
AHAAdAAgAGMAYQBjAGgAaQBuAGcAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGUAbgBhAGIAbABlAGQA
KQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIA
RwBfAEMAQQBDAEgARQBfAFAAUgBPAE0AUABUACkADQAKAC0ALQBjAGEAYwBoAGUALQByAGUAdQBz
AGUAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
bQBpAG4AIABjAGgAdQBuAGsAIABzAGkAegBlACAAdABvACAAYQB0AHQAZQBtAHAAdAAgAHIAZQB1
AHMAaQBuAGcAIABmAHIAbwBtACAAdABoAGUAIABjAGEAYwBoAGUAIAB2AGkAYQAgAEsAVgAgAHMA
aABpAGYAdABpAG4AZwAsAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHIAZQBxAHUAaQByAGUA
cwAgAHAAcgBvAG0AcAB0ACAAYwBhAGMAaABpAG4AZwAgAHQAbwAgAGIAZQAgAGUAbgBhAGIAbABl
AGQAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADAAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABb
ACgAYwBhAHIAZAApAF0AKABoAHQAdABwAHMAOgAvAC8AZwBnAG0AbAAuAGEAaQAvAGYAMAAuAHAA
bgBnACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8A
QQBSAEcAXwBDAEEAQwBIAEUAXwBSAEUAVQBTAEUAKQANAAoALQAtAG0AZQB0AHIAaQBjAHMAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IABlAG4AYQBiAGwAZQAgAHAAcgBvAG0AZQB0AGgAZQB1AHMAIABjAG8AbQBwAGEAdABpAGIAbABl
ACAAbQBlAHQAcgBpAGMAcwAgAGUAbgBkAHAAbwBpAG4AdAAgACgAZABlAGYAYQB1AGwAdAA6ACAA
ZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAA
TABMAEEATQBBAF8AQQBSAEcAXwBFAE4ARABQAE8ASQBOAFQAXwBNAEUAVABSAEkAQwBTACkADQAK
AC0ALQBwAHIAbwBwAHMAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAZQBuAGEAYgBsAGUAIABjAGgAYQBuAGcAaQBuAGcAIABn
AGwAbwBiAGEAbAAgAHAAcgBvAHAAZQByAHQAaQBlAHMAIAB2AGkAYQAgAFAATwBTAFQAIAAvAHAA
cgBvAHAAcwAgACgAZABlAGYAYQB1AGwAdAA6ACAAZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBFAE4ARABQ
AE8ASQBOAFQAXwBQAFIATwBQAFMAKQANAAoALQAtAHMAbABvAHQAcwAsACAALQAtAG4AbwAtAHMA
bABvAHQAcwAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABlAHgAcABv
AHMAZQAgAHMAbABvAHQAcwAgAG0AbwBuAGkAdABvAHIAaQBuAGcAIABlAG4AZABwAG8AaQBuAHQA
IAAoAGQAZQBmAGEAdQBsAHQAOgAgAGUAbgBhAGIAbABlAGQAKQANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEUATgBEAFAATwBJAE4AVABf
AFMATABPAFQAUwApAA0ACgAtAC0AcwBsAG8AdAAtAHMAYQB2AGUALQBwAGEAdABoACAAUABBAFQA
SAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHAAYQB0AGgAIAB0AG8AIABz
AGEAdgBlACAAcwBsAG8AdAAgAGsAdgAgAGMAYQBjAGgAZQAgACgAZABlAGYAYQB1AGwAdAA6ACAA
ZABpAHMAYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAA
TABMAEEATQBBAF8AQQBSAEcAXwBTAEwATwBUAF8AUwBBAFYARQBfAFAAQQBUAEgAKQANAAoALQAt
AG0AZQBkAGkAYQAtAHAAYQB0AGgAIABQAEEAVABIACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIABkAGkAcgBlAGMAdABvAHIAeQAgAGYAbwByACAAbABvAGEAZABp
AG4AZwAgAGwAbwBjAGEAbAAgAG0AZQBkAGkAYQAgAGYAaQBsAGUAcwA7ACAAZgBpAGwAZQBzACAA
YwBhAG4AIABiAGUAIABhAGMAYwBlAHMAcwBlAGQAIAB2AGkAYQANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABmAGkAbABlADoALwAvACAAVQBSAEwAcwAgAHUAcwBpAG4AZwAgAHIAZQBsAGEAdABp
AHYAZQAgAHAAYQB0AGgAcwAgACgAZABlAGYAYQB1AGwAdAA6ACAAZABpAHMAYQBiAGwAZQBkACkA
DQAKAC0ALQBtAG8AZABlAGwAcwAtAGQAaQByACAAUABBAFQASAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAZABpAHIAZQBjAHQAbwByAHkAIABjAG8AbgB0AGEA
aQBuAGkAbgBnACAAbQBvAGQAZQBsAHMAIABmAG8AcgAgAHQAaABlACAAcgBvAHUAdABlAHIAIABz
AGUAcgB2AGUAcgAgACgAZABlAGYAYQB1AGwAdAA6ACAAZABpAHMAYQBiAGwAZQBkACkADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBNAE8A
RABFAEwAUwBfAEQASQBSACkADQAKAC0ALQBtAG8AZABlAGwAcwAtAHAAcgBlAHMAZQB0ACAAUABB
AFQASAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcABhAHQAaAAgAHQA
bwAgAEkATgBJACAAZgBpAGwAZQAgAGMAbwBuAHQAYQBpAG4AaQBuAGcAIABtAG8AZABlAGwAIABw
AHIAZQBzAGUAdABzACAAZgBvAHIAIAB0AGgAZQAgAHIAbwB1AHQAZQByACAAcwBlAHIAdgBlAHIA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABkAGUAZgBhAHUAbAB0ADoAIABkAGkAcwBhAGIA
bABlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEA
XwBBAFIARwBfAE0ATwBEAEUATABTAF8AUABSAEUAUwBFAFQAKQANAAoALQAtAG0AbwBkAGUAbABz
AC0AbQBhAHgAIABOACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABmAG8AcgAgAHIAbwB1AHQAZQByACAAcwBlAHIAdgBlAHIALAAgAG0AYQB4AGkAbQB1
AG0AIABuAHUAbQBiAGUAcgAgAG8AZgAgAG0AbwBkAGUAbABzACAAdABvACAAbABvAGEAZAAgAHMA
aQBtAHUAbAB0AGEAbgBlAG8AdQBzAGwAeQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGQA
ZQBmAGEAdQBsAHQAOgAgADQALAAgADAAIAA9ACAAdQBuAGwAaQBtAGkAdABlAGQAKQANAAoAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAE0ATwBE
AEUATABTAF8ATQBBAFgAKQANAAoALQAtAG0AbwBkAGUAbABzAC0AYQB1AHQAbwBsAG8AYQBkACwA
IAAtAC0AbgBvAC0AbQBvAGQAZQBsAHMALQBhAHUAdABvAGwAbwBhAGQADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAZgBvAHIAIAByAG8AdQB0AGUAcgAgAHMAZQByAHYAZQByACwAIAB3AGgAZQB0
AGgAZQByACAAdABvACAAYQB1AHQAbwBtAGEAdABpAGMAYQBsAGwAeQAgAGwAbwBhAGQAIABtAG8A
ZABlAGwAcwAgACgAZABlAGYAYQB1AGwAdAA6AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGUA
bgBhAGIAbABlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwA
QQBNAEEAXwBBAFIARwBfAE0ATwBEAEUATABTAF8AQQBVAFQATwBMAE8AQQBEACkADQAKAC0ALQBq
AGkAbgBqAGEALAAgAC0ALQBuAG8ALQBqAGkAbgBqAGEAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAdwBoAGUAdABoAGUAcgAgAHQAbwAgAHUAcwBlACAAagBpAG4AagBh
ACAAdABlAG0AcABsAGEAdABlACAAZQBuAGcAaQBuAGUAIABmAG8AcgAgAGMAaABhAHQAIAAoAGQA
ZQBmAGEAdQBsAHQAOgAgAGUAbgBhAGIAbABlAGQAKQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAoAGUAbgB2ADoAIABMAEwAQQBNAEEAXwBBAFIARwBfAEoASQBOAEoAQQApAA0ACgAtAC0AcgBl
AGEAcwBvAG4AaQBuAGcALQBmAG8AcgBtAGEAdAAgAEYATwBSAE0AQQBUACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAGMAbwBuAHQAcgBvAGwAcwAgAHcAaABlAHQAaABlAHIAIAB0AGgAbwB1
AGcAaAB0ACAAdABhAGcAcwAgAGEAcgBlACAAYQBsAGwAbwB3AGUAZAAgAGEAbgBkAC8AbwByACAA
ZQB4AHQAcgBhAGMAdABlAGQAIABmAHIAbwBtACAAdABoAGUADQAKACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAcgBlAHMAcABvAG4AcwBlACwAIABhAG4AZAAgAGkAbgAgAHcAaABpAGMAaAAgAGYAbwBy
AG0AYQB0ACAAdABoAGUAeQAnAHIAZQAgAHIAZQB0AHUAcgBuAGUAZAA7ACAAbwBuAGUAIABvAGYA
OgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAtACAAbgBvAG4AZQA6ACAAbABlAGEAdgBlAHMA
IAB0AGgAbwB1AGcAaAB0AHMAIAB1AG4AcABhAHIAcwBlAGQAIABpAG4AIABgAG0AZQBzAHMAYQBn
AGUALgBjAG8AbgB0AGUAbgB0AGAADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAALQAgAGQAZQBl
AHAAcwBlAGUAawA6ACAAcAB1AHQAcwAgAHQAaABvAHUAZwBoAHQAcwAgAGkAbgAgAGAAbQBlAHMA
cwBhAGcAZQAuAHIAZQBhAHMAbwBuAGkAbgBnAF8AYwBvAG4AdABlAG4AdABgAA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAC0AIABkAGUAZQBwAHMAZQBlAGsALQBsAGUAZwBhAGMAeQA6ACAAawBl
AGUAcABzACAAYAA8AHQAaABpAG4AawA+AGAAIAB0AGEAZwBzACAAaQBuACAAYABtAGUAcwBzAGEA
ZwBlAC4AYwBvAG4AdABlAG4AdABgACAAdwBoAGkAbABlAA0ACgAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAGEAbABzAG8AIABwAG8AcAB1AGwAYQB0AGkAbgBnACAAYABtAGUAcwBzAGEAZwBlAC4AcgBl
AGEAcwBvAG4AaQBuAGcAXwBjAG8AbgB0AGUAbgB0AGAADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAKABkAGUAZgBhAHUAbAB0ADoAIABhAHUAdABvACkADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBUAEgASQBOAEsAKQANAAoALQByAGUA
YQAsACAAIAAtAC0AcgBlAGEAcwBvAG4AaQBuAGcAIABbAG8AbgB8AG8AZgBmAHwAYQB1AHQAbwBd
ACAAIAAgACAAIAAgACAAIABVAHMAZQAgAHIAZQBhAHMAbwBuAGkAbgBnAC8AdABoAGkAbgBrAGkA
bgBnACAAaQBuACAAdABoAGUAIABjAGgAYQB0ACAAKAAnAG8AbgAnACwAIAAnAG8AZgBmACcALAAg
AG8AcgAgACcAYQB1AHQAbwAnACwAIABkAGUAZgBhAHUAbAB0ADoADQAKACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAJwBhAHUAdABvACcAIAAoAGQAZQB0AGUAYwB0ACAAZgByAG8AbQAgAHQAZQBtAHAA
bABhAHQAZQApACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEA
TQBBAF8AQQBSAEcAXwBSAEUAQQBTAE8ATgBJAE4ARwApAA0ACgAtAC0AcgBlAGEAcwBvAG4AaQBu
AGcALQBlAGYAZgBvAHIAdAAgAEwARQBWAEUATAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgAHIAZQBhAHMAbwBuAGkAbgBnACAAZQBmAGYAbwByAHQAIABsAGUAdgBlAGwAIABnAGkAdgBl
AG4AIAB0AG8AIAB0AGgAZQAgAGMAaABhAHQAIAB0AGUAbQBwAGwAYQB0AGUAOgAgACcAZABlAGYA
YQB1AGwAdAAnACAAdABvACAAawBlAGUAcAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB0AGgA
ZQAgAHQAZQBtAHAAbABhAHQAZQAgAGQAZQBmAGEAdQBsAHQALAANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABvAHIAIABhACAAbABlAHYAZQBsACAAcwB1AGMAaAAgAGEAcwAgACcAbQBpAG4AaQBt
AGEAbAAnACwAIAAnAGwAbwB3ACcALAAgACcAbQBlAGQAaQB1AG0AJwAsACAAJwBoAGkAZwBoACcA
LAAgACcAeABoAGkAZwBoACcAIABvAHIADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAJwBtAGEA
eAAnACAAKABkAGUAZgBhAHUAbAB0ADoAIABkAGUAZgBhAHUAbAB0ACkADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBSAEUAQQBTAE8ATgBJ
AE4ARwBfAEUARgBGAE8AUgBUACkADQAKAC0ALQByAGUAYQBzAG8AbgBpAG4AZwAtAGIAdQBkAGcA
ZQB0ACAATgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdABvAGsAZQBu
ACAAYgB1AGQAZwBlAHQAIABmAG8AcgAgAHQAaABpAG4AawBpAG4AZwA6ACAALQAxACAAZgBvAHIA
IAB1AG4AcgBlAHMAdAByAGkAYwB0AGUAZAAsACAAMAAgAGYAbwByACAAaQBtAG0AZQBkAGkAYQB0
AGUAIABlAG4AZAAsAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAE4APgAwACAAZgBvAHIAIAB0
AG8AawBlAG4AIABiAHUAZABnAGUAdAAgACgAZABlAGYAYQB1AGwAdAA6ACAALQAxACkADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBUAEgA
SQBOAEsAXwBCAFUARABHAEUAVAApAA0ACgAtAC0AcgBlAGEAcwBvAG4AaQBuAGcALQBiAHUAZABn
AGUAdAAtAG0AZQBzAHMAYQBnAGUAIABNAEUAUwBTAEEARwBFACAAIAAgACAAIAAgAG0AZQBzAHMA
YQBnAGUAIABpAG4AagBlAGMAdABlAGQAIABiAGUAZgBvAHIAZQAgAHQAaABlACAAZQBuAGQALQBv
AGYALQB0AGgAaQBuAGsAaQBuAGcAIAB0AGEAZwAgAHcAaABlAG4AIAByAGUAYQBzAG8AbgBpAG4A
ZwAgAGIAdQBkAGcAZQB0AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGkAcwAgAGUAeABoAGEA
dQBzAHQAZQBkACAAKABkAGUAZgBhAHUAbAB0ADoAIABuAG8AbgBlACkADQAKACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBBAF8AQQBSAEcAXwBUAEgASQBOAEsAXwBC
AFUARABHAEUAVABfAE0ARQBTAFMAQQBHAEUAKQANAAoALQAtAHIAZQBhAHMAbwBuAGkAbgBnAC0A
cAByAGUAcwBlAHIAdgBlACwAIAAtAC0AbgBvAC0AcgBlAGEAcwBvAG4AaQBuAGcALQBwAHIAZQBz
AGUAcgB2AGUADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcAByAGUAcwBlAHIAdgBlACAAcgBl
AGEAcwBvAG4AaQBuAGcAIAB0AHIAYQBjAGUAIABpAG4AIAB0AGgAZQAgAGYAdQBsAGwAIABoAGkA
cwB0AG8AcgB5ACwAIABuAG8AdAAgAGoAdQBzAHQAIAB0AGgAZQAgAGwAYQBzAHQADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAYQBzAHMAaQBzAHQAYQBuAHQAIABtAGUAcwBzAGEAZwBlACAAKABk
AGUAZgBhAHUAbAB0ADoAIABlAG4AYQBiAGwAZQBkACkADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAYwBvAG0AcABhAHQAaQBiAGwAZQAgAHcAaQB0AGgAIABjAGUAcgB0AGEAaQBuACAAdABlAG0A
cABsAGEAdABlAHMAIABoAGEAdgBpAG4AZwAgACcAcwB1AHAAcABvAHIAdABzAF8AcAByAGUAcwBl
AHIAdgBlAF8AcgBlAGEAcwBvAG4AaQBuAGcAJwANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABj
AGEAcABhAGIAaQBsAGkAdAB5AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGUAeABhAG0AcABs
AGUAOgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABoAHQAdABwAHMAOgAvAC8AZABvAGMAcwAu
AHoALgBhAGkALwBnAHUAaQBkAGUAcwAvAGMAYQBwAGEAYgBpAGwAaQB0AGkAZQBzAC8AdABoAGkA
bgBrAGkAbgBnAC0AbQBvAGQAZQAjAHAAcgBlAHMAZQByAHYAZQBkAC0AdABoAGkAbgBrAGkAbgBn
AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0AQQBfAEEAUgBH
AF8AUgBFAEEAUwBPAE4ASQBOAEcAXwBQAFIARQBTAEUAUgBWAEUAKQANAAoALQAtAGMAaABhAHQA
LQB0AGUAbQBwAGwAYQB0AGUAIABKAEkATgBKAEEAXwBUAEUATQBQAEwAQQBUAEUAIAAgACAAIAAg
ACAAIAAgACAAIABzAGUAdAAgAGMAdQBzAHQAbwBtACAAagBpAG4AagBhACAAYwBoAGEAdAAgAHQA
ZQBtAHAAbABhAHQAZQAgACgAZABlAGYAYQB1AGwAdAA6ACAAdABlAG0AcABsAGEAdABlACAAdABh
AGsAZQBuACAAZgByAG8AbQAgAG0AbwBkAGUAbAAnAHMADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAbQBlAHQAYQBkAGEAdABhACkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAaQBmACAAcwB1
AGYAZgBpAHgALwBwAHIAZQBmAGkAeAAgAGEAcgBlACAAcwBwAGUAYwBpAGYAaQBlAGQALAAgAHQA
ZQBtAHAAbABhAHQAZQAgAHcAaQBsAGwAIABiAGUAIABkAGkAcwBhAGIAbABlAGQADQAKACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAbwBuAGwAeQAgAGMAbwBtAG0AbwBuAGwAeQAgAHUAcwBlAGQAIAB0
AGUAbQBwAGwAYQB0AGUAcwAgAGEAcgBlACAAYQBjAGMAZQBwAHQAZQBkACAAKAB1AG4AbABlAHMA
cwAgAC0ALQBqAGkAbgBqAGEAIABpAHMAIABzAGUAdAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IABiAGUAZgBvAHIAZQAgAHQAaABpAHMAIABmAGwAYQBnACkAOgANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIABsAGkAcwB0ACAAbwBmACAAYgB1AGkAbAB0AC0AaQBuACAAdABlAG0AcABsAGEAdABl
AHMAOgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABiAGEAaQBsAGkAbgBnACwAIABiAGEAaQBs
AGkAbgBnAC0AdABoAGkAbgBrACwAIABiAGEAaQBsAGkAbgBnADIALAAgAGMAaABhAHQAZwBsAG0A
MwAsACAAYwBoAGEAdABnAGwAbQA0ACwAIABjAGgAYQB0AG0AbAAsAA0ACgAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgAGMAbwBtAG0AYQBuAGQALQByACwAIABkAGUAZQBwAHMAZQBlAGsALAAgAGQAZQBl
AHAAcwBlAGUAawAtAG8AYwByACwAIABkAGUAZQBwAHMAZQBlAGsAMgAsACAAZABlAGUAcABzAGUA
ZQBrADMALAAgAGUAeABhAG8AbgBlAC0AbQBvAGUALAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IABlAHgAYQBvAG4AZQAzACwAIABlAHgAYQBvAG4AZQA0ACwAIABmAGEAbABjAG8AbgAzACwAIABn
AGUAbQBtAGEALAAgAGcAaQBnAGEAYwBoAGEAdAAsACAAZwBsAG0AZQBkAGcAZQAsACAAZwBwAHQA
LQBvAHMAcwAsACAAZwByAGEAbgBpAHQAZQAsAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGcA
cgBhAG4AaQB0AGUALQA0AC4AMAAsACAAZwByAGEAbgBpAHQAZQAtADQALgAxACwAIABnAHIAbwBr
AC0AMgAsACAAaAB1AG4AeQB1AGEAbgAtAGQAZQBuAHMAZQAsACAAaAB1AG4AeQB1AGEAbgAtAG0A
bwBlACwADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAaAB1AG4AeQB1AGEAbgAtAHYAbAAsACAA
awBpAG0AaQAtAGsAMgAsACAAbABsAGEAbQBhADIALAAgAGwAbABhAG0AYQAyAC0AcwB5AHMALAAg
AGwAbABhAG0AYQAyAC0AcwB5AHMALQBiAG8AcwAsAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AGwAbABhAG0AYQAyAC0AcwB5AHMALQBzAHQAcgBpAHAALAAgAGwAbABhAG0AYQAzACwAIABsAGwA
YQBtAGEANAAsACAAbQBlAGcAcgBlAHoALAAgAG0AaQBuAGkAYwBwAG0ALAAgAG0AaQBzAHQAcgBh
AGwALQB2ADEALAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABtAGkAcwB0AHIAYQBsAC0AdgAz
ACwAIABtAGkAcwB0AHIAYQBsAC0AdgAzAC0AdABlAGsAawBlAG4ALAAgAG0AaQBzAHQAcgBhAGwA
LQB2ADcALAAgAG0AaQBzAHQAcgBhAGwALQB2ADcALQB0AGUAawBrAGUAbgAsACAAbQBvAG4AYQBy
AGMAaAAsAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG8AcABlAG4AYwBoAGEAdAAsACAAbwBy
AGkAbwBuACwAIABwAGEAbgBnAHUALQBlAG0AYgBlAGQAZABlAGQALAAgAHAAaABpADMALAAgAHAA
aABpADQALAAgAHIAdwBrAHYALQB3AG8AcgBsAGQALAAgAHMAZQBlAGQAXwBvAHMAcwAsAA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAHMAbQBvAGwAdgBsAG0ALAAgAHMAbwBsAGEAcgAtAG8AcABl
AG4ALAAgAHYAaQBjAHUAbgBhACwAIAB2AGkAYwB1AG4AYQAtAG8AcgBjAGEALAAgAHkAYQBuAGQA
ZQB4ACwAIAB6AGUAcABoAHkAcgANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoA
IABMAEwAQQBNAEEAXwBBAFIARwBfAEMASABBAFQAXwBUAEUATQBQAEwAQQBUAEUAKQANAAoALQAt
AGMAaABhAHQALQB0AGUAbQBwAGwAYQB0AGUALQBmAGkAbABlACAASgBJAE4ASgBBAF8AVABFAE0A
UABMAEEAVABFAF8ARgBJAEwARQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABzAGUAdAAgAGMA
dQBzAHQAbwBtACAAagBpAG4AagBhACAAYwBoAGEAdAAgAHQAZQBtAHAAbABhAHQAZQAgAGYAaQBs
AGUAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAHQAZQBtAHAAbABhAHQAZQAgAHQAYQBrAGUAbgAgAGYA
cgBvAG0ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbQBvAGQAZQBsACcAcwAgAG0AZQB0AGEA
ZABhAHQAYQApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGkAZgAgAHMAdQBmAGYAaQB4AC8A
cAByAGUAZgBpAHgAIABhAHIAZQAgAHMAcABlAGMAaQBmAGkAZQBkACwAIAB0AGUAbQBwAGwAYQB0
AGUAIAB3AGkAbABsACAAYgBlACAAZABpAHMAYQBiAGwAZQBkAA0ACgAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgAG8AbgBsAHkAIABjAG8AbQBtAG8AbgBsAHkAIAB1AHMAZQBkACAAdABlAG0AcABsAGEA
dABlAHMAIABhAHIAZQAgAGEAYwBjAGUAcAB0AGUAZAAgACgAdQBuAGwAZQBzAHMAIAAtAC0AagBp
AG4AagBhACAAaQBzACAAcwBlAHQADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAYgBlAGYAbwBy
AGUAIAB0AGgAaQBzACAAZgBsAGEAZwApADoADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbABp
AHMAdAAgAG8AZgAgAGIAdQBpAGwAdAAtAGkAbgAgAHQAZQBtAHAAbABhAHQAZQBzADoADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAYgBhAGkAbABpAG4AZwAsACAAYgBhAGkAbABpAG4AZwAtAHQA
aABpAG4AawAsACAAYgBhAGkAbABpAG4AZwAyACwAIABjAGgAYQB0AGcAbABtADMALAAgAGMAaABh
AHQAZwBsAG0ANAAsACAAYwBoAGEAdABtAGwALAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABj
AG8AbQBtAGEAbgBkAC0AcgAsACAAZABlAGUAcABzAGUAZQBrACwAIABkAGUAZQBwAHMAZQBlAGsA
LQBvAGMAcgAsACAAZABlAGUAcABzAGUAZQBrADIALAAgAGQAZQBlAHAAcwBlAGUAawAzACwAIABl
AHgAYQBvAG4AZQAtAG0AbwBlACwADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAZQB4AGEAbwBu
AGUAMwAsACAAZQB4AGEAbwBuAGUANAAsACAAZgBhAGwAYwBvAG4AMwAsACAAZwBlAG0AbQBhACwA
IABnAGkAZwBhAGMAaABhAHQALAAgAGcAbABtAGUAZABnAGUALAAgAGcAcAB0AC0AbwBzAHMALAAg
AGcAcgBhAG4AaQB0AGUALAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABnAHIAYQBuAGkAdABl
AC0ANAAuADAALAAgAGcAcgBhAG4AaQB0AGUALQA0AC4AMQAsACAAZwByAG8AawAtADIALAAgAGgA
dQBuAHkAdQBhAG4ALQBkAGUAbgBzAGUALAAgAGgAdQBuAHkAdQBhAG4ALQBtAG8AZQAsAA0ACgAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgAGgAdQBuAHkAdQBhAG4ALQB2AGwALAAgAGsAaQBtAGkALQBr
ADIALAAgAGwAbABhAG0AYQAyACwAIABsAGwAYQBtAGEAMgAtAHMAeQBzACwAIABsAGwAYQBtAGEA
MgAtAHMAeQBzAC0AYgBvAHMALAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABsAGwAYQBtAGEA
MgAtAHMAeQBzAC0AcwB0AHIAaQBwACwAIABsAGwAYQBtAGEAMwAsACAAbABsAGEAbQBhADQALAAg
AG0AZQBnAHIAZQB6ACwAIABtAGkAbgBpAGMAcABtACwAIABtAGkAcwB0AHIAYQBsAC0AdgAxACwA
DQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbQBpAHMAdAByAGEAbAAtAHYAMwAsACAAbQBpAHMA
dAByAGEAbAAtAHYAMwAtAHQAZQBrAGsAZQBuACwAIABtAGkAcwB0AHIAYQBsAC0AdgA3ACwAIABt
AGkAcwB0AHIAYQBsAC0AdgA3AC0AdABlAGsAawBlAG4ALAAgAG0AbwBuAGEAcgBjAGgALAANAAoA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIABvAHAAZQBuAGMAaABhAHQALAAgAG8AcgBpAG8AbgAsACAA
cABhAG4AZwB1AC0AZQBtAGIAZQBkAGQAZQBkACwAIABwAGgAaQAzACwAIABwAGgAaQA0ACwAIABy
AHcAawB2AC0AdwBvAHIAbABkACwAIABzAGUAZQBkAF8AbwBzAHMALAANAAoAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIABzAG0AbwBsAHYAbABtACwAIABzAG8AbABhAHIALQBvAHAAZQBuACwAIAB2AGkA
YwB1AG4AYQAsACAAdgBpAGMAdQBuAGEALQBvAHIAYwBhACwAIAB5AGEAbgBkAGUAeAAsACAAegBl
AHAAaAB5AHIADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAKABlAG4AdgA6ACAATABMAEEATQBB
AF8AQQBSAEcAXwBDAEgAQQBUAF8AVABFAE0AUABMAEEAVABFAF8ARgBJAEwARQApAA0ACgAtAC0A
cwBrAGkAcAAtAGMAaABhAHQALQBwAGEAcgBzAGkAbgBnACwAIAAtAC0AbgBvAC0AcwBrAGkAcAAt
AGMAaABhAHQALQBwAGEAcgBzAGkAbgBnAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGYAbwBy
AGMAZQAgAGEAIABwAHUAcgBlACAAYwBvAG4AdABlAG4AdAAgAHAAYQByAHMAZQByACwAIABlAHYA
ZQBuACAAaQBmACAAYQAgAEoAaQBuAGoAYQAgAHQAZQBtAHAAbABhAHQAZQAgAGkAcwAgAHMAcABl
AGMAaQBmAGkAZQBkADsADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAbQBvAGQAZQBsACAAdwBp
AGwAbAAgAG8AdQB0AHAAdQB0ACAAZQB2AGUAcgB5AHQAaABpAG4AZwAgAGkAbgAgAHQAaABlACAA
YwBvAG4AdABlAG4AdAAgAHMAZQBjAHQAaQBvAG4ALAAgAGkAbgBjAGwAdQBkAGkAbgBnACAAYQBu
AHkADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAcgBlAGEAcwBvAG4AaQBuAGcAIABhAG4AZAAv
AG8AcgAgAHQAbwBvAGwAIABjAGEAbABsAHMAIAAoAGQAZQBmAGEAdQBsAHQAOgAgAGQAaQBzAGEA
YgBsAGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACgAZQBuAHYAOgAgAEwATABBAE0A
QQBfAEEAUgBHAF8AUwBLAEkAUABfAEMASABBAFQAXwBQAEEAUgBTAEkATgBHACkADQAKAC0ALQBw
AHIAZQBmAGkAbABsAC0AYQBzAHMAaQBzAHQAYQBuAHQALAAgAC0ALQBuAG8ALQBwAHIAZQBmAGkA
bABsAC0AYQBzAHMAaQBzAHQAYQBuAHQADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdwBoAGUA
dABoAGUAcgAgAHQAbwAgAHAAcgBlAGYAaQBsAGwAIAB0AGgAZQAgAGEAcwBzAGkAcwB0AGEAbgB0
ACcAcwAgAHIAZQBzAHAAbwBuAHMAZQAgAGkAZgAgAHQAaABlACAAbABhAHMAdAAgAG0AZQBzAHMA
YQBnAGUAIABpAHMAIABhAG4ADQAKACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAYQBzAHMAaQBzAHQA
YQBuAHQAIABtAGUAcwBzAGEAZwBlACAAKABkAGUAZgBhAHUAbAB0ADoAIABwAHIAZQBmAGkAbABs
ACAAZQBuAGEAYgBsAGUAZAApAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHcAaABlAG4AIAB0
AGgAaQBzACAAZgBsAGEAZwAgAGkAcwAgAHMAZQB0ACwAIABpAGYAIAB0AGgAZQAgAGwAYQBzAHQA
IABtAGUAcwBzAGEAZwBlACAAaQBzACAAYQBuACAAYQBzAHMAaQBzAHQAYQBuAHQAIABtAGUAcwBz
AGEAZwBlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHQAaABlAG4AIABpAHQAIAB3AGkAbABs
ACAAYgBlACAAdAByAGUAYQB0AGUAZAAgAGEAcwAgAGEAIABmAHUAbABsACAAbQBlAHMAcwBhAGcA
ZQAgAGEAbgBkACAAbgBvAHQAIABwAHIAZQBmAGkAbABsAGUAZAANAAoAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAoAGUAbgB2ADoAIABMAEwAQQBNAEEA
XwBBAFIARwBfAFAAUgBFAEYASQBMAEwAXwBBAFMAUwBJAFMAVABBAE4AVAApAA0ACgAtAHMAcABz
ACwAIAAgAC0ALQBzAGwAbwB0AC0AcAByAG8AbQBwAHQALQBzAGkAbQBpAGwAYQByAGkAdAB5ACAA
UwBJAE0ASQBMAEEAUgBJAFQAWQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABoAG8AdwAgAG0A
dQBjAGgAIAB0AGgAZQAgAHAAcgBvAG0AcAB0ACAAbwBmACAAYQAgAHIAZQBxAHUAZQBzAHQAIABt
AHUAcwB0ACAAbQBhAHQAYwBoACAAdABoAGUAIABwAHIAbwBtAHAAdAAgAG8AZgAgAGEAIABzAGwA
bwB0ACAAaQBuAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAG8AcgBkAGUAcgAgAHQAbwAgAHUA
cwBlACAAdABoAGEAdAAgAHMAbABvAHQAIAAoAGQAZQBmAGEAdQBsAHQAOgAgADAALgAxADAALAAg
ADAALgAwACAAPQAgAGQAaQBzAGEAYgBsAGUAZAApAA0ACgAtAC0AbABvAHIAYQAtAGkAbgBpAHQA
LQB3AGkAdABoAG8AdQB0AC0AYQBwAHAAbAB5ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
AGwAbwBhAGQAIABMAG8AUgBBACAAYQBkAGEAcAB0AGUAcgBzACAAdwBpAHQAaABvAHUAdAAgAGEA
cABwAGwAeQBpAG4AZwAgAHQAaABlAG0AIAAoAGEAcABwAGwAeQAgAGwAYQB0AGUAcgAgAHYAaQBh
ACAAUABPAFMAVAANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAvAGwAbwByAGEALQBhAGQAYQBw
AHQAZQByAHMAKQAgACgAZABlAGYAYQB1AGwAdAA6ACAAZABpAHMAYQBiAGwAZQBkACkADQAKAC0A
LQBzAGwAZQBlAHAALQBpAGQAbABlAC0AcwBlAGMAbwBuAGQAcwAgAFMARQBDAE8ATgBEAFMAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAbgB1AG0AYgBlAHIAIABvAGYAIABzAGUAYwBvAG4AZABzACAA
bwBmACAAaQBkAGwAZQBuAGUAcwBzACAAYQBmAHQAZQByACAAdwBoAGkAYwBoACAAdABoAGUAIABz
AGUAcgB2AGUAcgAgAHcAaQBsAGwAIABzAGwAZQBlAHAADQAKACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAKABkAGUAZgBhAHUAbAB0ADoAIAAtADEAOwAgAC0AMQAgAD0AIABkAGkAcwBhAGIAbABlAGQA
KQANAAoALQAtAGwAbwBnAC0AcAByAG8AbQBwAHQAcwAtAGQAaQByACAAUABBAFQASAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABMAG8AZwAgAHAAcgBvAG0AcAB0AHMAIAB0AG8A
IABkAGkAcgBlAGMAdABvAHIAeQAgACgAYQB1AHQAbwAtAGMAcgBlAGEAdABlAGQAIABpAGYAIABu
AG8AdAAgAHAAcgBlAHMAZQBuAHQAOwAgAG8AbgBsAHkAIAB1AHMAZQBkACAAZgBvAHIADQAKACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAZABlAGIAdQBnAGcAaQBuAGcALAAgAGQAZQBmAGEAdQBsAHQA
OgAgAGQAaQBzAGEAYgBsAGUAZAApAA0ACgAtAC0AZQBtAGIAZAAtAGcAZQBtAG0AYQAtAGQAZQBm
AGEAdQBsAHQAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHUAcwBlACAA
ZABlAGYAYQB1AGwAdAAgAEUAbQBiAGUAZABkAGkAbgBnAEcAZQBtAG0AYQAgAG0AbwBkAGUAbAAg
ACgAbgBvAHQAZQA6ACAAYwBhAG4AIABkAG8AdwBuAGwAbwBhAGQAIAB3AGUAaQBnAGgAdABzACAA
ZgByAG8AbQAgAHQAaABlAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGkAbgB0AGUAcgBuAGUA
dAApAA0ACgAtAC0AZgBpAG0ALQBxAHcAZQBuAC0AMQAuADUAYgAtAGQAZQBmAGEAdQBsAHQAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHUAcwBlACAAZABlAGYAYQB1AGwAdAAgAFEA
dwBlAG4AIAAyAC4ANQAgAEMAbwBkAGUAcgAgADEALgA1AEIAIAAoAG4AbwB0AGUAOgAgAGMAYQBu
ACAAZABvAHcAbgBsAG8AYQBkACAAdwBlAGkAZwBoAHQAcwAgAGYAcgBvAG0AIAB0AGgAZQANAAoA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIABpAG4AdABlAHIAbgBlAHQAKQANAAoALQAtAGYAaQBtAC0A
cQB3AGUAbgAtADMAYgAtAGQAZQBmAGEAdQBsAHQAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAB1AHMAZQAgAGQAZQBmAGEAdQBsAHQAIABRAHcAZQBuACAAMgAuADUAIABDAG8A
ZABlAHIAIAAzAEIAIAAoAG4AbwB0AGUAOgAgAGMAYQBuACAAZABvAHcAbgBsAG8AYQBkACAAdwBl
AGkAZwBoAHQAcwAgAGYAcgBvAG0AIAB0AGgAZQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABp
AG4AdABlAHIAbgBlAHQAKQANAAoALQAtAGYAaQBtAC0AcQB3AGUAbgAtADcAYgAtAGQAZQBmAGEA
dQBsAHQAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB1AHMAZQAgAGQAZQBm
AGEAdQBsAHQAIABRAHcAZQBuACAAMgAuADUAIABDAG8AZABlAHIAIAA3AEIAIAAoAG4AbwB0AGUA
OgAgAGMAYQBuACAAZABvAHcAbgBsAG8AYQBkACAAdwBlAGkAZwBoAHQAcwAgAGYAcgBvAG0AIAB0
AGgAZQANAAoAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIABpAG4AdABlAHIAbgBlAHQAKQANAAoALQAt
AGYAaQBtAC0AcQB3AGUAbgAtADcAYgAtAHMAcABlAGMAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAB1AHMAZQAgAFEAdwBlAG4AIAAyAC4ANQAgAEMAbwBkAGUAcgAg
ADcAQgAgACsAIAAwAC4ANQBCACAAZAByAGEAZgB0ACAAZgBvAHIAIABzAHAAZQBjAHUAbABhAHQA
aQB2AGUAIABkAGUAYwBvAGQAaQBuAGcAIAAoAG4AbwB0AGUAOgAgAGMAYQBuAA0ACgAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgAGQAbwB3AG4AbABvAGEAZAAgAHcAZQBpAGcAaAB0AHMAIABmAHIAbwBt
ACAAdABoAGUAIABpAG4AdABlAHIAbgBlAHQAKQANAAoALQAtAGYAaQBtAC0AcQB3AGUAbgAtADEA
NABiAC0AcwBwAGUAYwAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB1
AHMAZQAgAFEAdwBlAG4AIAAyAC4ANQAgAEMAbwBkAGUAcgAgADEANABCACAAKwAgADAALgA1AEIA
IABkAHIAYQBmAHQAIABmAG8AcgAgAHMAcABlAGMAdQBsAGEAdABpAHYAZQAgAGQAZQBjAG8AZABp
AG4AZwAgACgAbgBvAHQAZQA6AA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGMAYQBuACAAZABv
AHcAbgBsAG8AYQBkACAAdwBlAGkAZwBoAHQAcwAgAGYAcgBvAG0AIAB0AGgAZQAgAGkAbgB0AGUA
cgBuAGUAdAApAA0ACgAtAC0AZgBpAG0ALQBxAHcAZQBuAC0AMwAwAGIALQBkAGUAZgBhAHUAbAB0
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHUAcwBlACAAZABlAGYAYQB1AGwA
dAAgAFEAdwBlAG4AIAAzACAAQwBvAGQAZQByACAAMwAwAEIAIABBADMAQgAgAEkAbgBzAHQAcgB1
AGMAdAAgACgAbgBvAHQAZQA6ACAAYwBhAG4AIABkAG8AdwBuAGwAbwBhAGQAIAB3AGUAaQBnAGgA
dABzAA0ACgAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAGYAcgBvAG0AIAB0AGgAZQAgAGkAbgB0AGUA
cgBuAGUAdAApAA0ACgAtAC0AZwBwAHQALQBvAHMAcwAtADIAMABiAC0AZABlAGYAYQB1AGwAdAAg
ACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgAHUAcwBlACAAZwBwAHQALQBvAHMA
cwAtADIAMABiACAAKABuAG8AdABlADoAIABjAGEAbgAgAGQAbwB3AG4AbABvAGEAZAAgAHcAZQBp
AGcAaAB0AHMAIABmAHIAbwBtACAAdABoAGUAIABpAG4AdABlAHIAbgBlAHQAKQANAAoALQAtAGcA
cAB0AC0AbwBzAHMALQAxADIAMABiAC0AZABlAGYAYQB1AGwAdAAgACAAIAAgACAAIAAgACAAIAAg
ACAAIAAgACAAIAAgACAAIAB1AHMAZQAgAGcAcAB0AC0AbwBzAHMALQAxADIAMABiACAAKABuAG8A
dABlADoAIABjAGEAbgAgAGQAbwB3AG4AbABvAGEAZAAgAHcAZQBpAGcAaAB0AHMAIABmAHIAbwBt
ACAAdABoAGUAIABpAG4AdABlAHIAbgBlAHQAKQANAAoALQAtAHYAaQBzAGkAbwBuAC0AZwBlAG0A
bQBhAC0ANABiAC0AZABlAGYAYQB1AGwAdAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAB1
AHMAZQAgAEcAZQBtAG0AYQAgADMAIAA0AEIAIABRAEEAVAAgACgAbgBvAHQAZQA6ACAAYwBhAG4A
IABkAG8AdwBuAGwAbwBhAGQAIAB3AGUAaQBnAGgAdABzACAAZgByAG8AbQAgAHQAaABlACAAaQBu
AHQAZQByAG4AZQB0ACkADQAKAC0ALQB2AGkAcwBpAG8AbgAtAGcAZQBtAG0AYQAtADEAMgBiAC0A
ZABlAGYAYQB1AGwAdAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAdQBzAGUAIABHAGUAbQBt
AGEAIAAzACAAMQAyAEIAIABRAEEAVAAgACgAbgBvAHQAZQA6ACAAYwBhAG4AIABkAG8AdwBuAGwA
bwBhAGQAIAB3AGUAaQBnAGgAdABzACAAZgByAG8AbQAgAHQAaABlACAAaQBuAHQAZQByAG4AZQB0
ACkADQAKAC0ALQBzAHAAZQBjAC0AZABlAGYAYQB1AGwAdAAgACAAIAAgACAAIAAgACAAIAAgACAA
IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAZQBuAGEAYgBsAGUAIABkAGUAZgBhAHUAbAB0
ACAAcwBwAGUAYwB1AGwAYQB0AGkAdgBlACAAZABlAGMAbwBkAGkAbgBnACAAYwBvAG4AZgBpAGcA
DQAKAA==
"""
    ),
}


def _maleta_sha(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(1 << 20), b""):
            h.update(trozo)
    return h.hexdigest().upper()


def _maleta_escribe(ruta, nombre, sha):
    datos = base64.b64decode("".join(_MALETA_B64[nombre].split()))
    if hashlib.sha256(datos).hexdigest().upper() != sha:
        raise SystemExit("[FATAL] maleta: el payload de %s NO clava con su SHA "
                         "incrustado. Re-descarga CAMPANA.py del repo oficial."
                         % nombre)
    with open(ruta, "wb") as f:
        f.write(datos)


def _existe_cerca(nombre, aqui):
    return (os.path.exists(os.path.join(aqui, nombre)) or
            os.path.exists(os.path.join(aqui, "..", "configs", nombre)))


def _despliega_maleta():
    aqui = os.path.dirname(os.path.abspath(__file__))
    notas = []
    for nombre, (sha, modo) in sorted(_MALETA.items()):
        ruta = os.path.join(aqui, nombre)
        if modo == "semilla":
            if os.path.exists(ruta) or _existe_cerca(nombre, aqui):
                continue  # el config del Director (o el de repo): NO se toca
        elif os.path.exists(ruta):
            if _maleta_sha(ruta) == sha:
                continue  # intacto en disco: nada que hacer
            if modo == "dump" and not os.path.exists(
                    os.path.join(aqui, "..", "configs", nombre)):
                notas.append("  %s: difiere del certificado -> REEMPLAZADO "
                             "por el de la maleta" % nombre)
                _maleta_escribe(ruta, nombre, sha)
                continue
            if modo == "dump":
                continue  # hay dump en ../configs: barrido usa ese
            notas.append("  %s: difiere del certificado -> REEMPLAZADO por el "
                         "de la maleta" % nombre)
            _maleta_escribe(ruta, nombre, sha)
            continue
        elif modo == "dump" and _existe_cerca(nombre, aqui):
            continue  # layout de repo: barrido lo encuentra en ../configs
        notas.append("  %s: desplegado de la maleta (SHA verificado)" % nombre)
        _maleta_escribe(ruta, nombre, sha)
    return notas


_notas_maleta = _despliega_maleta()
if _notas_maleta:
    print("MALETA (R47): companeros desplegados/verificados:")
    for _n in _notas_maleta:
        print(_n)


AQUI = os.path.dirname(os.path.abspath(__file__))
VERSION = ("campana-10-pasos v1.7 LA MALETA (2026-10-29, ronda 47: archivo unico de "
           "verdad - los companeros de rig viajan dentro y se despliegan solos; "
           "P6 sin bat; P4-P5 aparcadas r43; doble click = pasos 1..6 sin preguntas y SIN descarga)")

# R43 — decision del Director (delego: "elige una", elegida A): el cuant
# vigente SC117 APEX-I-Mini ya trae heretic + MTP nativo, asi que p4 (descarga
# 14.07 GB de unsloth) y p5 (verificacion de ese archivo) quedan APARCADAS.
# True = el AUTO y _siguiente_paso saltan p4/p5 (queda escrito); el acceso
# manual `p4`/`p5` sigue vivo para un duelo explicito. False = plan original.
P4_APARCADA = True

# MODO AUTO: cuando esta activo, las confirmaciones se auto-aceptan y quedan
# escritas (evidencia append-only). NUNCA activa --fuerza: las puertas rojas
# (repo ALT, SHA256, GO del p1) detienen el turno limpio, no se saltan.
AUTO = {"on": False, "aceptadas": []}


def _pausa_doble_click(es_tty=None):
    """Doble click en Windows: la consola se cierra sola al terminar y el
    Director no alcanza a leer nada. Si el script se arranco SIN argumentos
    (doble click puro) se espera un Enter antes de cerrar; con argumentos
    (uso real desde consola/bat) no molesta."""
    if len(sys.argv) <= 1:
        if es_tty is None:
            try:
                es_tty = sys.stdin.isatty()
            except Exception:
                es_tty = False
        if es_tty:
            try:
                input("\n(Enter para cerrar)")
            except Exception:
                pass


# ---------------- importacion del companero de taller (barrido N3) ----------
_BARRIDO = os.path.join(AQUI, "barrido-n3-eficiencia.py")
if not os.path.exists(_BARRIDO):
    print("[FATAL] no encuentro barrido-n3-eficiencia.py junto a mi (%s)." % AQUI)
    print("        El piloto y el barrido viajan JUNTOS en D:\\ZLia.")
    _pausa_doble_click()
    sys.exit(2)
_spec = importlib.util.spec_from_file_location("barrido_n3", _BARRIDO)
bn3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bn3)

c, bold, red = bn3._c, bn3.bold, bn3.red
green, yellow, cyan, gray = bn3.green, bn3.yellow, bn3.cyan, bn3.gray
health_ok, ram_sistema = bn3.health_ok, bn3.ram_sistema
sha256_archivo, gguf_metadatos = bn3.sha256_archivo, bn3.gguf_metadatos

# ---------------- constantes del hito N2 (autenticadores cerrados) ----------
MODELO_NUEVO_NOMBRE = "Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf"
MODELO_NUEVO_BYTES = 14069266720
MODELO_NUEVO_SHA = ("36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012e3d9e249"
                    "5a90e7a7150")
REPO_DEFAULT = "unsloth/Qwen3.6-35B-A3B-MTP-GGUF"  # RUTAS.md L738: MTP preserved
# REPO_ALT DESAUTENTICADO en vivo (API HF 2026-10-29, verificacion r37):
# sirve el MISMO NOMBRE de archivo pero SIN modulo MTP (13,211,155,424 B,
# SHA256 9c964e65...88fbe) y sin variante -MTP. La nota vieja "mismo
# archivo, mismo SHA" era FALSA. p4 lo rechaza antes de descargar.
REPO_ALT = "unsloth/Qwen3.6-35B-A3B-GGUF"
REPO_ALT_MOTIVO = ("la API de HF (29-oct) publica en este repo el UD-IQ3_XXS "
                   "SIN modulo MTP (13,211,155,424 B, SHA256 9c964e65...88fbe) "
                   "y sin ninguna variante -MTP: NO es el archivo del hito N2 "
                   "y p5 lo rechazaria por SHA despues de horas de descarga")
GO_PCT, NOGO_PCT = 15.0, 5.0
DISCO_MIN_GB = 16.0      # para la descarga en D:
DISCO_HIGIENE_GB = 25.0  # aviso de higiene en C: (pagefile vive en C:)
SANITY_TOTAL = 20

# ---------------- los 20 prompts del juez (p3) ------------------------------
# Mezcla obligatoria: espanol, codigo, tool-calling, memoria corta, trampa.
SANITY_PROMPTS = [
    ("casual", "Hola! Que tal? Responde en una frase amable."),
    ("explica-simple", "Explica en dos frases que es la RAM de un computador, como para un nino."),
    ("codigo-fizzbuzz", "Escribe una funcion Python que imprima FizzBuzz del 1 al 15. Solo codigo."),
    ("matematica", "Cuanto es 17 * 23? Responde solo el numero."),
    ("traduccion", "Traduce al ingles: 'El perro corre por la playa al atardecer.'"),
    ("resumen", "Resume en una frase: 'El server de llama.cpp carga el modelo en la GPU, atiende peticiones HTTP y devuelve tokens generados uno a uno hasta completar la respuesta.'"),
    ("logica", "Todos los gatos son mamiferos. Algunos mamiferos nadan. Se puede concluir que todos los gatos nadan? Responde si o no y explica en una frase."),
    ("memoria-corta", "Mi color favorito es el verde. Sin pensar en nada mas, de que color te dije que era mi favorito?"),
    ("formato-lista", "Dame 3 consejos para dormir mejor, en lista con vinetas, uno por linea."),
    ("trampa-futuro", "Quien gano la final del mundial de futbol de 2030? Si no lo sabes, di que no lo sabes."),
    ("tool-clima", "Tienes la herramienta get_weather(ciudad). Usandola en formato JSON, como consultarias el clima de Santiago? Muestra solo la llamada."),
    ("tool-buscar", "Tienes la herramienta buscar_productos(termino, max). Muestra la llamada JSON para buscar 'teclado mecanico' con maximo 5 resultados."),
    ("redaccion", "Escribe un parrafo corto (3 frases) sobre el mar de Chile."),
    ("codigo-bug", "Este codigo tiene un bug: def suma(a,b): return a-b. Dime cual es y corrigelo en una linea."),
    ("clasificacion", "Clasifica el sentimiento como positivo/negativo/neutral: 'El servicio fue lento pero la comida estaba excelente.'"),
    ("creativo", "Escribe un haiku (3 versos) sobre el desierto de Atacama."),
    ("multilingue", "Traduce 'buenos dias' al ingles, frances y aleman, en una linea."),
    ("seguimiento", "Me llamo Ana y trabajo en Valparaiso. En que ciudad dije que trabajo?"),
    ("dominio", "Para que sirve la flag -ngl 99 en llama.cpp? Una frase."),
    ("despedida", "Despidete en una frase corta y amable."),
]

# ---------------- memoria de la campana -------------------------------------

def _rutas(args):
    base = os.path.abspath(args.dir) if args.dir else AQUI
    return {
        "base": base,
        "estado": os.path.join(base, "campana-estado.json"),
        "informe": os.path.join(base, "campana-INFORME.md"),
        "config": args.config or os.path.join(base, "config.txt"),
        "models": os.path.join(base, "models"),
    }


def leer_estado(ruta_estado):
    if os.path.exists(ruta_estado):
        try:
            with open(ruta_estado, encoding="utf-8") as f:
                datos = json.load(f)
            if isinstance(datos, dict):
                # defensa: un json viejo o a medio escribir no revienta despues
                datos.setdefault("pasos", {})
                datos.setdefault("n3", {})
                return datos
        except Exception:
            pass
    return {"version": VERSION, "actualizado": "", "pasos": {}, "n3": {}}


def guardar_estado(ruta_estado, estado):
    estado["version"] = VERSION
    estado["actualizado"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tmp = ruta_estado + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ruta_estado)


def informe(ruta_informe, titulo, lineas):
    """APPEND-ONLY: cada accion anade su seccion; nunca se reescribe."""
    sello = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ruta_informe, "a", encoding="utf-8") as f:
        f.write("\n\n## %s — %s\n\n" % (sello, titulo))
        for ln in lineas:
            f.write("%s\n" % ln)
        f.flush()
    return ruta_informe


def fatal(msg, pistas=()):
    print(red("\n[FATAL] %s" % msg))
    for p in pistas:
        print(yellow("  pista: %s" % p))
    sys.exit(2)


def confirmar(palabra, pregunta):
    if AUTO["on"]:
        print(yellow("\n%s" % pregunta))
        print(cyan("  [AUTO] aceptado automaticamente (la aceptacion queda escrita "
                   "en el informe)."))
        AUTO["aceptadas"].append("%s — %s" % (palabra, pregunta))
        return True
    print(yellow("\n%s" % pregunta))
    try:
        resp = input(yellow("  escribe %s para confirmar (otra cosa cancela): " % bold(palabra)))
    except EOFError:
        resp = ""
    if resp.strip().upper() != palabra:
        print(gray("  cancelado (no se toco nada)."))
        return False
    return True


def gb_libres(ruta):
    try:
        u = shutil.disk_usage(ruta)
        return u.free / (1024.0 ** 3), u.total / (1024.0 ** 3)
    except Exception:
        return None, None


def leer_config(ruta_config):
    """CLAVE = valor -> dict (lineas con # se ignoran). Igual que la casa."""
    if not os.path.exists(ruta_config):
        fatal("no encuentro config.txt en %s" % ruta_config,
              ["pasa --config D:\\ZLia\\config.txt"])
    cfg = {}
    with open(ruta_config, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


# ---------------- CSV del barrido: clasificacion de filas -------------------

def cosechar_carpeta(carpeta):
    """Lee faseN3-resultados.csv de una carpeta y devuelve las filas
    validas que importan para la mediana: ANCLA, NP2 (SLOTS) y ANCLA-FIN.
    (csv_cargar_hechos de la casa: solo valido=SI.)"""
    ruta = os.path.join(carpeta, "faseN3-resultados.csv")
    if not os.path.exists(ruta):
        return None
    filas = {"ancla": [], "np2": [], "anclafin": [], "total_validas": 0}
    try:
        with open(ruta, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("valido") or "").strip().upper() != "SI":
                    continue
                filas["total_validas"] += 1
                nom = (row.get("nombre") or "").upper()
                ts = row.get("decode_ts") or ""
                try:
                    ts = float(ts)
                except Exception:
                    continue
                if nom.startswith("N3-ANCLA") and "FIN" in nom:
                    filas["anclafin"].append(ts)
                elif nom.startswith("N3-ANCLA"):
                    filas["ancla"].append(ts)
                elif nom == "N3-NP2":
                    filas["np2"].append(ts)
    except Exception as e:
        return {"error": repr(e)}
    return filas


def mediana_np2(datos_carpetas):
    """Por carpeta: delta NP2 vs SU ancla. Veredicto con la mediana de los
    deltas (regla de la casa: mediana de 3, ancla por corrida)."""
    deltas, absolutos, detalle = [], [], []
    for nombre, filas in datos_carpetas:
        if not filas or filas.get("error") or not filas.get("np2") or not filas.get("ancla"):
            detalle.append("%s: N/D (ancla o NP2 no validas)" % nombre)
            continue
        ancla = statistics.median(filas["ancla"])
        np2 = statistics.median(filas["np2"])
        delta = (np2 / ancla - 1.0) * 100.0
        drift = ""
        if filas.get("anclafin"):
            fin = statistics.median(filas["anclafin"])
            d = abs(fin / ancla - 1.0) * 100.0
            drift = " (bookend %+.1f%%%s)" % ((fin / ancla - 1.0) * 100.0,
                                              ", sesion ESTABLE" if d < 5 else ", ATENCION >5%")
        deltas.append(delta)
        absolutos.append(np2)
        detalle.append("%s: ancla %.2f -> NP2 %.2f = %+.1f%%%s"
                       % (nombre, ancla, np2, delta, drift))
    if len(deltas) < 3:
        veredicto = "INCOMPLETO"
    else:
        m = statistics.median(deltas)
        veredicto = "GO" if m >= GO_PCT else ("NO-GO" if m < NOGO_PCT else "DUDOSO")
        detalle.append("mediana de los deltas: %+.1f%% -> %s" % (m, veredicto))
        if absolutos:
            detalle.append("t/s absolutos NP2: %s (mediana %.2f)"
                           % (", ".join("%.2f" % a for a in absolutos),
                              statistics.median(absolutos)))
    return veredicto, detalle


# ---------------- P1: higiene + mediana + NOCACHE ---------------------------

def paso1(args, rutas, estado):
    b1 = args.b1 or os.path.join(rutas["base"], "faseN3")
    b2 = args.b2 or os.path.join(rutas["base"], "faseN3-np2-b2")
    b3 = args.b3 or os.path.join(rutas["base"], "faseN3-np2-b3")
    lineas = []
    print(bold(cyan("\n=== P1 - higiene + mediana de 3 de NP2 ===")))

    # -- higiene (nunca fatal; advierte) --
    for etiqueta, ruta, minimo in (("C: (pagefile)", "C:\\" if os.name == "nt" else "/", DISCO_HIGIENE_GB),
                                   ("D: (trabajo)", "D:\\" if os.name == "nt" else "/", DISCO_MIN_GB)):
        libre, total = gb_libres(ruta)
        if libre is None:
            print(gray("  disco %s: (no disponible)" % etiqueta))
            continue
        msg = "  disco %s: %.1f GB libres de %.1f" % (etiqueta, libre, total)
        if libre < minimo:
            # AMBOS discos avisan (v1.0 solo miraba C: y D: bajo salia VERDE)
            detalle = ("higiene: pagefile en C:" if etiqueta.startswith("C:")
                       else "minimo para la descarga del cuant")
            print(yellow(msg + yellow("  <- por DEBAJO de %.0f GB (%s)" % (minimo, detalle))))
            lineas.append("- disco %s: %.1f GB libres (< %.0f GB: %s)"
                          % (etiqueta, libre, minimo, detalle))
        else:
            print(green(msg))
            lineas.append("- disco %s: %.1f GB libres de %.1f" % (etiqueta, libre, total))
    ram = ram_sistema()
    if ram:
        libre_mib, total_mib = ram
        pct = 100.0 * (total_mib - libre_mib) / max(total_mib, 1)
        estilo = green if pct < 70 else yellow
        print(estilo("  RAM: %.0f%% usada (%.1f GB libres de %.1f) — regla R28: apps cerradas antes de medir"
                     % (pct, libre_mib / 1024.0, total_mib / 1024.0)))
        lineas.append("- RAM: %.0f%% usada al iniciar" % pct)

    # -- log NOCACHE (2 min que cierran la anomalia) --
    for raiz in (b1, os.path.dirname(b1)):
        if not raiz:
            continue
        cand = os.path.join(raiz, "logs-config", "12-NOCACHE.log")
        if os.path.exists(cand):
            print(cyan("  log NOCACHE: %s" % cand))
            try:
                with open(cand, encoding="utf-8", errors="replace") as f:
                    utiles = [ln.rstrip() for ln in f
                              if any(s in ln for s in ("cache_reuse", "restored", "forcing", "not supported"))]
                for ln in utiles[:12]:
                    print("    %s" % gray(ln[:160]))
                lineas.append("- NOCACHE log: %d lineas utiles (%s)" % (len(utiles), os.path.basename(cand)))
            except Exception as e:
                print(yellow("    (no pude leerlo: %r)" % e))
            break
    else:
        print(gray("  log NOCACHE: no encontrado (no fatal; anotado)"))
        lineas.append("- NOCACHE log: no encontrado en b1")

    # -- las 2 corridas de mediana (barrido v1.3; reanudable) --
    if not args.sin_corridas:
        try:
            for carpeta in (b2, b3):
                if not confirmar("EJECUTAR", "Se lanzara el barrido (~6-8 min) en carpeta '%s' con --solo ancla,slots,anclafin. El rig debe estar QUIETO (sin descargas, apps cerradas)." % carpeta):
                    fatal("mediana incompleta: el Director cancelo la corrida de %s" % carpeta,
                          ["re-lanza p1 cuando puedas dejar el rig quieto",
                           "o usa p1 --sin-corridas para cosechar lo ya medido"])
                cmd = [sys.executable, _BARRIDO, "--logs", carpeta,
                       "--solo", "ancla,slots,anclafin"]
                print(cyan("  $ %s" % " ".join(cmd)))
                rc = subprocess.call(cmd)
                if rc != 0:
                    fatal("el barrido salio con rc=%d en %s" % (rc, carpeta),
                          ["mira el final de la salida de arriba (forense)",
                           "el resume de la casa re-mide solo lo muerto: repite p1"])
        except KeyboardInterrupt:
            print(yellow("\n  INTERRUMPIDO (Ctrl+C): corrida pausada. El resume "
                         "de la casa re-mide solo lo muerto: repite p1."))
            return 130
    else:
        print(gray("  (--sin-corridas: cosechando lo que ya hay en las carpetas)"))

    # -- cosecha y veredicto --
    carpetas = [("b1=%s" % b1, cosechar_carpeta(b1)),
                ("b2=%s" % b2, cosechar_carpeta(b2)),
                ("b3=%s" % b3, cosechar_carpeta(b3))]
    print(bold("\n  cosecha de la mediana:"))
    for nombre, filas in carpetas:
        if filas is None:
            print(yellow("    %s: SIN CSV (¿carpeta correcta?)" % nombre))
        elif filas.get("error"):
            print(yellow("    %s: CSV ilegible (%s)" % (nombre, filas["error"])))
        else:
            print("    %s: validas=%d ancla=%d np2=%d anclafin=%d"
                  % (nombre, filas["total_validas"], len(filas["ancla"]),
                     len(filas["np2"]), len(filas["anclafin"])))
    veredicto, detalle = mediana_np2(carpetas)
    for d in detalle:
        print("    %s" % d)
    color = {"GO": green, "NO-GO": red, "DUDOSO": yellow}.get(veredicto, yellow)
    print(color(bold("  VEREDICTO P1: %s" % veredicto)))
    if veredicto == "GO":
        print("  -> pasa a p2: promocion de -np 2 en config.txt")
    elif veredicto == "NO-GO":
        print("  -> NP2 no aguanta: CMS1024 (plan B) o se queda como esta")
    elif veredicto == "DUDOSO":
        print("  -> zona de decision del Director (entre %.0f%% y %.0f%%)" % (NOGO_PCT, GO_PCT))

    estado["pasos"]["1"] = {"estado": veredicto, "carpetas": [n for n, _ in carpetas],
                            "detalle": detalle}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P1 mediana de 3 de NP2 -> %s" % veredicto, lineas + detalle)
    return 0


# ---------------- P2: promocion de -np 2 (la UNICA cirugia) -----------------

def _linea_flags_base(ruta_config):
    with open(ruta_config, encoding="utf-8") as f:
        for i, ln in enumerate(f):
            if ln.strip().startswith("FLAGS_BASE ="):
                return i, ln.rstrip("\n")
    return None, None


def paso2(args, rutas, estado):
    print(bold(cyan("\n=== P2 - promocion de -np 2 en config.txt ===")))
    if args.revert:
        return _p2_revert(rutas, estado)
    p1 = estado["pasos"].get("1", {})
    if p1.get("estado") != "GO" and not args.fuerza:
        fatal("la puerta p1 no esta en GO (estado actual: %s)" % (p1.get("estado") or "SIN P1"),
              ["corre p1 primero (mediana de 3 de NP2)",
               "si el Director decide saltarse la puerta: p2 --fuerza (queda escrito)"])
    ruta = rutas["config"]
    i, linea = _linea_flags_base(ruta)
    if i is None:
        fatal("no encuentro la linea FLAGS_BASE en %s" % ruta)
    # -np se busca por TOKENS, no por substring: "-np 20" no es "-np 2",
    # y si ya hay un -np distinto, la promocion NO se apila encima
    tokens = linea.split()
    ya_np = None
    for bandera in ("-np", "--parallel"):
        if bandera in tokens:
            i = tokens.index(bandera)
            ya_np = tokens[i + 1] if i + 1 < len(tokens) else "?"
            break
    if ya_np == "2":
        print(yellow("  FLAGS_BASE ya contiene -np 2: nada que hacer (idempotente)."))
        previo = estado["pasos"].get("2", {})
        estado["pasos"]["2"] = {"estado": "YA-PROMOVIDA",
                                "backup": previo.get("backup"),
                                "linea": previo.get("linea", linea)}
        guardar_estado(rutas["estado"], estado)
        return 0
    if ya_np is not None:
        print(yellow("  FLAGS_BASE ya trae -np %s (no 2): NO se toca nada." % ya_np))
        print(yellow("  El numero de slots ya lo decidio otra mano: revisa y decide tu."))
        informe(rutas["informe"], "P2 promocion ABORTADA: FLAGS_BASE ya trae -np %s" % ya_np,
                ["- linea: `%s`" % linea, "- config.txt intacto (nada editado)"])
        return 1
    nueva = linea + " -np 2"
    print("  linea actual : %s" % gray(linea))
    print("  linea nueva  : %s" % green(nueva))
    print(yellow("  matices aceptados: contexto 8192 por sesion (con -c 16384), "
                "WorkingSet +965 MiB, SS11.4 (MTP exige -np 1, se decide en p10)."))
    if not confirmar("PROMOVER", "Se editara %s (backup automatico antes)." % ruta):
        print(gray("  cancelado: config.txt intacto."))
        informe(rutas["informe"], "P2 promocion CANCELADA por el Director",
                ["- config.txt intacto (nada editado)"])
        return 1
    backup = "%s.bak-campana-p2-%s" % (ruta, datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(ruta, backup)
    with open(ruta, encoding="utf-8") as f:
        contenido = f.readlines()
    contenido[i] = nueva + "\n"
    with open(ruta, "w", encoding="utf-8") as f:
        f.writelines(contenido)
    _, verifica = _linea_flags_base(ruta)
    if not verifica or "-np 2" not in verifica:
        fatal("la edicion no quedo aplicada; restaura el backup: %s" % backup)
    print(green("  promovida. backup: %s" % backup))
    estado["pasos"]["2"] = {"estado": "PROMOVIDA", "backup": backup, "linea": nueva}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P2 promocion -np 2 -> PROMOVIDA",
            ["- config: %s" % ruta, "- backup: %s" % backup,
             "- linea nueva: `%s`" % nueva,
             "- siguiente: p3 (sanity 20 prompts como juez)"])
    print(cyan("  siguiente: arranca el server como siempre y corre p3."))
    return 0


def _p2_revert(rutas, estado):
    ruta = rutas["config"]
    info = estado["pasos"].get("2", {})
    backup = info.get("backup")
    if not backup or not os.path.exists(backup):
        # fallback: el backup mas reciente junto a config.txt
        candidatos = sorted(
            f for f in os.listdir(os.path.dirname(ruta) or ".")
            if f.startswith(os.path.basename(ruta) + ".bak-campana-p2-"))
        if not candidatos:
            fatal("no hay backup registrado para revertir",
                  ["busca config.txt.bak-campana-p2-* a mano junto a config.txt"])
        backup = os.path.join(os.path.dirname(ruta), candidatos[-1])
    shutil.copy2(backup, ruta)
    print(green("  config.txt restaurado desde %s" % backup))
    estado["pasos"]["2"] = {"estado": "REVERTIDA", "backup": backup}
    estado["n3"]["cerrado"] = False
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P2 revert: config.txt restaurada",
            ["- backup usado: %s" % backup])
    return 0


# ---------------- P3: sanity de 20 prompts (el juez) ------------------------

def _chat_uno(puerto, texto, timeout=180):
    cuerpo = json.dumps({
        "messages": [{"role": "user", "content": texto}],
        "max_tokens": 220, "temperature": 1.0, "top_k": 20, "top_p": 0.95,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d/v1/chat/completions" % puerto, data=cuerpo,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        js = json.loads(r.read().decode("utf-8", errors="replace"))
    contenido = ""
    try:
        contenido = js["choices"][0]["message"]["content"] or ""
    except Exception:
        contenido = json.dumps(js)[:400]
    tps = None
    try:
        tps = float(js["timings"]["predicted_per_second"])
    except Exception:
        pass
    return contenido, tps


def _p3_corre_sanity(args, rutas, estado, carpeta, tag):
    """Corre los 20 prompts contra el server vivo del puerto args.puerto (el
    que llama comprueba antes que HAY server). Deja prompt-NN-*.txt + RESUMEN
    (archivando el anterior si existe), guarda estado e informe, y devuelve
    (fallas_http, respuestas) para que el AUTO aplique su veredicto objetivo."""
    puerto = args.puerto
    print(cyan("  server vivo en %d. %d prompts, 1 por uno..." % (puerto, SANITY_TOTAL)))
    resumen, fallas, respuestas = [], 0, []
    for i, (nombre, texto) in enumerate(SANITY_PROMPTS, 1):
        try:
            contenido, tps = _chat_uno(puerto, texto)
        except Exception as e:
            contenido, tps, fallas = "[ERROR HTTP] %r" % e, None, fallas + 1
        respuestas.append((nombre, contenido))
        with open(os.path.join(carpeta, "prompt-%02d-%s.txt" % (i, nombre)),
                  "w", encoding="utf-8") as f:
            f.write("PROMPT: %s\n\nRESPUESTA:\n%s\n" % (texto, contenido))
        primera = contenido.strip().splitlines()[0][:70] if contenido.strip() else "(vacia)"
        tps_s = "%.1f t/s" % tps if tps else "-"
        estilo = green if "[ERROR" not in contenido and contenido.strip() else red
        print(estilo("  %02d/%02d %-18s %-12s %s" % (i, SANITY_TOTAL, nombre, tps_s, primera)))
        resumen.append("| %02d | %s | %s | %s |" % (i, nombre, tps_s, primera.replace("|", "/")))
    if fallas:
        print(red("  %d/%d prompts con error HTTP: revisa el log del server." % (fallas, SANITY_TOTAL)))
    ruta_res = os.path.join(carpeta, "RESUMEN.md")
    if os.path.exists(ruta_res):
        # re-corrida del mismo tag: el resumen ANTERIOR se archiva (la
        # evidencia de la casa nunca se pisa; el informe guarda todas)
        viejo = os.path.join(carpeta, "RESUMEN-%s.md"
                             % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.replace(ruta_res, viejo)
        print(gray("  resumen anterior archivado: %s" % os.path.basename(viejo)))
    with open(ruta_res, "w", encoding="utf-8") as f:
        f.write("# Sanity %s — %d prompts (juez: Director)\n\n"
                "(respuestas completas en prompt-NN-*.txt junto a este archivo)\n\n"
                "| # | tipo | velocidad | primera linea |\n|---|------|-----------|---------------|\n"
                % (tag, SANITY_TOTAL))
        f.write("\n".join(resumen) + "\n")
    print(green("  resumen: %s" % ruta_res))
    estado["pasos"]["3"] = {"estado": "EN-ESPERA-DEL-JUEZ", "carpeta": carpeta,
                            "errores_http": fallas}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P3 sanity %d prompts ejecutado (%s)" % (SANITY_TOTAL, tag),
            ["- carpeta: %s" % carpeta, "- errores http: %d" % fallas,
             "- esperando veredicto: p3 --veredicto OK|FALLA"])
    return fallas, respuestas


def _sanity_auto_veredicto(fallas, respuestas):
    """(veredicto, motivos) — el criterio OBJETIVO del AUTO para el juez:
    0 errores HTTP + 20/20 respuestas con carne + 3 anclas deterministas de
    calidad (aritmetica 391, memoria 'verde', seguimiento 'Valparaiso').
    El juez HUMANO sigue siendo el Director: el OK del AUTO es revocable
    leyendo el RESUMEN y cerrando con p3 --veredicto FALLA (+ p2 --revert)."""
    motivos = []
    if fallas:
        motivos.append("%d/%d prompts con error HTTP" % (fallas, SANITY_TOTAL))
    contenido = {n: (t or "") for n, t in respuestas}
    vacias = [n for n, t in contenido.items() if not t.strip()]
    if vacias:
        motivos.append("respuestas vacias: %s" % ", ".join(vacias))
    if "391" not in contenido.get("matematica", ""):
        motivos.append("ancla aritmetica (17x23=391) fallo")
    if "verde" not in contenido.get("memoria-corta", "").lower():
        motivos.append("ancla memoria (color favorito) fallo")
    if "valpara" not in contenido.get("seguimiento", "").lower():
        motivos.append("ancla seguimiento (ciudad) fallo")
    return ("FALLA" if motivos else "OK"), motivos


def paso3(args, rutas, estado):
    print(bold(cyan("\n=== P3 - sanity de 20 prompts (el juez) ===")))
    if args.veredicto:
        v = args.veredicto.strip().upper()
        if v not in ("OK", "FALLA"):
            fatal("veredicto debe ser OK o FALLA")
        estado["n3"]["veredicto_sanity"] = v
        estado.setdefault("pasos", {}).setdefault("3", {})
        if v == "OK":
            estado["n3"]["cerrado"] = True
            estado["pasos"]["3"]["estado"] = "OK"
            print(green(bold("  N3 CERRADO con promocion aceptada. Campana desbloqueada hasta p10.")))
            lineas = ["- veredicto del Director: OK", "- N3 CERRADO con -np 2 promovida"]
        else:
            estado["n3"]["cerrado"] = False
            estado["pasos"]["3"]["estado"] = "FALLA"
            print(red("  FALLA registrada. La casa instruye: p2 --revert (5 segundos) y reportar que fallo."))
            lineas = ["- veredicto del Director: FALLA", "- accion: p2 --revert + registrar que fallo"]
        estado["n3"]["cerrado_en"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        guardar_estado(rutas["estado"], estado)
        informe(rutas["informe"], "P3 veredicto del juez -> %s" % v, lineas)
        return 0
    p2 = estado["pasos"].get("2", {})
    if p2.get("estado") not in ("PROMOVIDA", "YA-PROMOVIDA") and not args.fuerza:
        fatal("la puerta p2 no esta PROMOVIDA (estado: %s)" % (p2.get("estado") or "SIN P2"),
              ["promueve con p2 primero (el sanity juzga la receta NUEVA)",
               "o --fuerza si sabes lo que haces (queda escrito)"])
    if not health_ok(args.puerto):
        fatal("no hay server vivo en el puerto %d" % args.puerto,
              ["arranca el server como siempre (ABRIR-QWEN.bat) y reintenta",
               "o pasa --puerto si usa otro"])
    tag = args.tag or ("np2" if p2.get("estado") in ("PROMOVIDA", "YA-PROMOVIDA") else "libre")
    carpeta = os.path.join(rutas["base"], "campana-sanity-%s" % tag)
    os.makedirs(carpeta, exist_ok=True)
    _p3_corre_sanity(args, rutas, estado, carpeta, tag)
    print(yellow("  LEE las 20 respuestas (tu eres el catador) y cierra con:"))
    print("    py campana-10-pasos.py p3 --veredicto OK      (20/20 -> N3 CERRADO)")
    print("    py campana-10-pasos.py p3 --veredicto FALLA   (algo se rompio -> revert)")
    return 0


# ---------------- P4: descarga del cuant nuevo (fuera de la ruta critica) ----

def _binario_hf():
    for binario in ("hf", "huggingface-cli"):
        ruta = shutil.which(binario)
        if ruta:
            return [ruta]
    return None


def _envuelve_gui(cmd, es_windows=None):
    """En Windows, un ejecutable instalado como .bat/.cmd (shim de pip) no
    arranca con exec directo: CreateProcess no corre shells. Se envuelve en
    cmd /c. En Linux/macOS (o un .exe) pasa igual."""
    if es_windows is None:
        es_windows = (os.name == "nt")
    if cmd and es_windows and os.path.splitext(cmd[0])[1].lower() in (".bat", ".cmd"):
        return ["cmd", "/c"] + cmd
    return cmd


def _quita_modelo_de_flags(flags):
    """Quita un -m/--model <ruta> pegado dentro de las flags: el modelo del
    humo va a parte y SIEMPRE es el nuevo (un -m colado cargaria otro cuant
    y el humo mentiria)."""
    while "-m" in flags or "--model" in flags:
        i = flags.index("-m") if "-m" in flags else flags.index("--model")
        del flags[i:i + 2]
    return flags


def paso4(args, rutas, estado):
    print(bold(cyan("\n=== P4 - descarga UD-IQ3_XXS (corre cuando el rig NO mide) ===")))
    if args.repo == REPO_ALT and not args.fuerza:
        fatal("el repo alternativo esta DESAUTENTICADO: %s" % REPO_ALT_MOTIVO,
              ["usa el repo por defecto (%s)" % REPO_DEFAULT,
               "si la descarga se corto, re-ejecuta p4 igual: hf RETOMA donde iba",
               "si de verdad quieres el repo ALT: --fuerza (queda escrito, y p5 "
               "rechazara el archivo por SHA salvo que unsloth lo arregle)"])
    if args.repo == REPO_ALT and args.fuerza:
        informe(rutas["informe"], "P4 repo ALT usado con --fuerza",
                ["- %s" % REPO_ALT_MOTIVO,
                 "- el archivo bajado NO pasara el SHA256 de p5 salvo que "
                 "unsloth lo haya cambiado de vuelta"])
    if not estado["n3"].get("cerrado") and not args.fuerza:
        fatal("la puerta p3 no cerro el N3 (veredicto: %s)"
              % (estado["n3"].get("veredicto_sanity") or "SIN P3"),
              ["cierra el N3 con p3 --veredicto OK (o FALLA + revert)",
               "o --fuerza si el Director decide adelantarla (queda escrito)"])
    os.makedirs(rutas["models"], exist_ok=True)
    destino = os.path.join(rutas["models"], MODELO_NUEVO_NOMBRE)
    if os.path.exists(destino):
        tam = os.path.getsize(destino)
        print(yellow("  el archivo YA existe (%.2f GB). Si venia de una descarga cortada, "
                     "el propio hf retoma; para verificarlo directo: p5." % (tam / 1024.0 ** 3)))
    cache_hf = os.path.join(rutas["base"], "hf-cache")
    os.makedirs(cache_hf, exist_ok=True)
    binario = _binario_hf()
    cmd = (binario or ["hf"]) + ["download", args.repo, MODELO_NUEVO_NOMBRE,
                                 "--local-dir", rutas["models"]]
    libre, total = gb_libres(rutas["models"])
    print("  destino    : %s" % destino)
    print("  tamano     : %.2f GB exactos (%d B)" % (MODELO_NUEVO_BYTES / 1024.0 ** 3, MODELO_NUEVO_BYTES))
    print("  cache HF   : %s (EN D:, fuera de C:)" % cache_hf)
    print("  comando    : %s" % " ".join(cmd))
    if libre is not None:
        estilo = green if libre >= DISCO_MIN_GB else red
        print(estilo("  disco D:   : %.1f GB libres (minimo %.0f)" % (libre, DISCO_MIN_GB)))
        if libre < DISCO_MIN_GB:
            if args.dry_run:
                print(red("  (dry-run: no frena aqui, pero en descarga real esto es FATAL)"))
            else:
                fatal("D: sin espacio suficiente para la descarga",
                      ["libera espacio o pasa --dir a otro disco con sitio"])
    if not binario:
        if args.dry_run:
            print(red("  (dry-run: sin cliente hf instalado; en real esto es FATAL "
                      "-> pip install -U \"huggingface_hub[cli]\")"))
        else:
            fatal("no encuentro el cliente de HuggingFace (hf / huggingface-cli)",
                  ["instalalo con: pip install -U \"huggingface_hub[cli]\""])
    if args.dry_run:
        print(yellow("  (--dry-run: nada se descargo)"))
        return 0
    if not confirmar("DESCARGAR", "Arranca la descarga (%.2f GB). Puede correr sola de noche; "
                                  "Ctrl+C la PAUSA y p4 la retoma." % (MODELO_NUEVO_BYTES / 1024.0 ** 3)):
        print(gray("  cancelado."))
        informe(rutas["informe"], "P4 descarga CANCELADA por el Director",
                ["- nada se descargo en este intento"])
        return 1
    env = dict(os.environ)
    env["HF_HOME"] = cache_hf
    try:
        rc = subprocess.call(_envuelve_gui(cmd), env=env)
    except KeyboardInterrupt:
        print(yellow("\n  INTERRUMPIDO (Ctrl+C): pausada. p4 la retoma mas tarde."))
        return 130
    if rc != 0:
        fatal("el cliente de HF salio con rc=%d" % rc,
              ["repite p4: la descarga retoma donde quedo"])
    tam = os.path.getsize(destino) if os.path.exists(destino) else 0
    if tam != MODELO_NUEVO_BYTES:
        fatal("bytes en disco (%d) != certificados (%d)" % (tam, MODELO_NUEVO_BYTES),
              ["puede ser descarga incompleta: repite p4 (retoma)",
               "el autenticador de bytes es cerrado [F RUTAS.md L738]"])
    print(green("  bytes exactos en disco: %d [OK] (certificado [F])" % tam))
    estado["pasos"]["4"] = {"estado": "DESCARGADA", "ruta": destino, "bytes": tam}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P4 descarga UD-IQ3_XXS -> DESCARGADA",
            ["- ruta: %s" % destino, "- bytes: %d (certificado)" % tam,
             "- cache HF en: %s" % cache_hf, "- siguiente: p5 (SHA256 + parser + humo)"])
    print(cyan("  siguiente: p5 (fail-fast: SHA256 + parser nextn + humo)."))
    return 0


# ---------------- P5: verificacion + humo del cuant nuevo -------------------

def verificar_descarga(ruta, sha_esperado, bytes_esperados):
    """(ok, lineas). Bytes exactos + SHA256 streaming con el certificado [F]."""
    lineas, ok = [], True
    tam = os.path.getsize(ruta)
    if tam != bytes_esperados:
        lineas.append("bytes en disco %d != certificados %d" % (tam, bytes_esperados))
        return False, lineas
    lineas.append("bytes exactos: %d [OK]" % tam)
    print(cyan("  SHA256 en streaming (13 GB, ~1-2 min)..."))
    sha = sha256_archivo(ruta, notificador=lambda s: print(gray(s)))
    if sha != sha_esperado:
        lineas.append("SHA256 %s != certificado %s" % (sha, sha_esperado))
        return False, lineas
    lineas.append("SHA256 [OK] certificado %s...%s" % (sha[:8], sha[-4:]))
    return ok, lineas


def verificar_gguf(ruta):
    """(metadatos, nextn_ok, lineas): parser GGUF de la casa (cero tensores)."""
    meta, err = gguf_metadatos(ruta)
    lineas = []
    if meta is None:
        return None, False, ["parser GGUF fallo: %s" % err]
    nextn = [k for k in meta if "nextn" in k]
    for clave in ("general.architecture",):
        if clave in meta:
            lineas.append("%s = %s" % (clave, meta[clave]))
    for k in sorted(meta):
        if k.endswith(".block_count") or k.endswith(".expert_count") or k.endswith(".expert_used_count"):
            lineas.append("%s = %s" % (k, meta[k]))
    lineas.append("tensores nextn (MTP dentro): %s" % (sorted(nextn) if nextn else "NINGUNO"))
    return meta, nextn, lineas  # nextn = LISTA de claves ([] = ausente)


def paso5(args, rutas, estado):
    print(bold(cyan("\n=== P5 - verificacion + humo del cuant nuevo (fail-fast) ===")))
    p4 = estado["pasos"].get("4", {})
    ruta = p4.get("ruta") or os.path.join(rutas["models"], MODELO_NUEVO_NOMBRE)
    if not os.path.exists(ruta):
        fatal("no esta el modelo nuevo en %s" % ruta,
              ["descarga primero: p4", "o pasa --dir si cambio de carpeta"])
    lineas = []
    ok_sha, lineas_sha = verificar_descarga(ruta, MODELO_NUEVO_SHA, MODELO_NUEVO_BYTES)
    for ln in lineas_sha:
        print("  %s" % (green(ln) if "[OK]" in ln else red(ln)))
    if not ok_sha:
        estado["pasos"]["5"] = {"estado": "FALLO-CERTIFICADO", "detalle": lineas_sha}
        guardar_estado(rutas["estado"], estado)
        informe(rutas["informe"], "P5 certificacion -> FALLO", ["- %s" % l for l in lineas_sha])
        fatal("el archivo NO es el certificado: NO se usa. Repite p4 (retoma) o re-descarga.",
              lineas_sha)
    meta, nextn, lineas_gguf = verificar_gguf(ruta)
    for ln in lineas_gguf:
        print("  %s" % (green(ln) if "nextn" in ln and "NINGUNO" not in ln else gray(ln)))
    if meta is None:
        fatal("la cabecera GGUF no se pudo leer", lineas_gguf)
    if not nextn:
        print(yellow("  SIN tensores nextn: el MTP NO viene dentro -> plan B draft separado "
                     "(doc N5); la descarga sigue siendo valida como cuant base."))
        lineas.append("- nextn: AUSENTE (plan B draft separado)")
    else:
        lineas.append("- nextn: PRESENTE (%d claves)" % len(nextn))
    lineas += ["- %s" % l for l in lineas_sha + lineas_gguf]

    if args.sin_humo:
        print(yellow("  (--sin-humo: verificacion lista; humo saltado a proposito)"))
        estado["pasos"]["5"] = {"estado": "VERIFICADO-SIN-HUMO", "nextn": nextn, "detalle": lineas}
        guardar_estado(rutas["estado"], estado)
        informe(rutas["informe"], "P5 verificacion (sin humo)", ["- %s" % l for l in lineas])
        return 0

    # -- humo: receta promovida + modelo nuevo, 1 prompt, y se apaga --
    cfg = leer_config(rutas["config"])
    puerto = args.puerto
    if health_ok(puerto):
        fatal("ya hay un server vivo en el puerto %d (guardarrail de la casa)" % puerto,
              ["apaga el server diario antes del humo", "o usa --puerto 9932"])
    servidor = cfg.get("RUTA_SERVER", "")
    if not servidor:
        fatal("config.txt no trae RUTA_SERVER (el humo no sabe QUE server arrancar)",
              ["revisa config.txt: RUTA_SERVER = ruta del llama-server.exe"])
    if not os.path.exists(servidor):
        fatal("el server no esta donde dice config.txt: %s" % servidor,
              ["revisa RUTA_SERVER en config.txt"])
    flags = (cfg.get("FLAGS_BASE", "") + " " + cfg.get("FLAGS_GANADORAS", "")).split()
    # el modelo va A PARTE y SIEMPRE es el nuevo (ver _quita_modelo_de_flags)
    flags = _quita_modelo_de_flags(flags)
    # MISMA regla del lanzador de la casa (abrir-qwen-apex.py): el override
    # de expertos SOLO se anade si EXPERTOS_TRABAJO != 8 (8 = de fabrica);
    # sin esto el humo corria una receta DIFERENTE a la diaria
    try:
        k = int(cfg.get("EXPERTOS_TRABAJO", "8"))
    except Exception:
        k = 8
    if k != 8:
        flags += ["--override-kv", "qwen35moe.expert_used_count=int:%d" % k]
    cmd = [servidor, "-m", ruta] + flags + [
        "--host", "127.0.0.1", "--port", str(puerto)]
    log_humo = os.path.join(rutas["base"], "campana-humo.log")
    print(cyan("  humo: arrancando server con el modelo NUEVO (puerto %d)..." % puerto))
    print(gray("  $ %s" % " ".join(cmd)))
    # forense ACUMULATIVO: cada intento anade su cabecera; nada se pisa
    with open(log_humo, "a", encoding="utf-8") as flog:
        flog.write("===== intento de humo %s (puerto %d) =====\n"
                   % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), puerto))
        flog.flush()
        proc = subprocess.Popen(cmd, stdout=flog, stderr=subprocess.STDOUT)
        try:
            fin = time.time() + 420
            while time.time() < fin:
                if proc.poll() is not None:
                    fatal("el server murio durante la carga del modelo nuevo (rc=%s)" % proc.returncode,
                          ["forense en %s" % log_humo,
                           "si dice VRAM insuficiente, el cuant nuevo necesito otra colocacion"])
                if health_ok(puerto):
                    break
                time.sleep(2)
            else:
                fatal("el server no levanto en 7 min", ["forense en %s" % log_humo])
            try:
                contenido, tps = _chat_uno(puerto, "Responde solo: HUMO OK")
            except Exception as e:
                fatal("el humo no pudo hablar con el server: %r" % e,
                      ["forense en %s" % log_humo])
            print(green("  respuesta del humo: %s" % contenido.strip()[:80]))
            if tps:
                print(green("  velocidad: %.1f t/s" % tps))
                lineas.append("- humo: %.1f t/s" % tps)
            lineas.append("- humo: respuesta OK con la receta promovida + modelo nuevo")
        finally:
            # el humo lanzo SU PROPIO hijo: lo termina directo (multiplataforma,
            # sin taskkill y sin riesgo de matar un server ajeno)
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
    print(green("  HUMO SANO: el cuant nuevo carga y responde con la receta de la casa."))
    estado["pasos"]["5"] = {"estado": "VERIFICADO-HUMO-OK", "nextn": nextn, "detalle": lineas}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P5 verificacion + humo -> OK", ["- %s" % l for l in lineas])
    print(cyan("  siguiente: p6 (N1 formal) o directo a p7 cuando puedas."))
    return 0


# ---------------- P6: N1 formal (barrido-n1-expertos.py, SIN bat) -----------

def paso6(args, rutas, estado):
    print(bold(cyan("\n=== P6 - N1 formal (barrido-n1-expertos.py, ~50-65 min) ===")))
    n1 = args.bat or os.path.join(rutas["base"], "barrido-n1-expertos.py")
    if not os.path.exists(n1):
        fatal("no encuentro barrido-n1-expertos.py",
              ["la maleta de CAMPANA.py lo despliega junto a si mismo en el "
               "primer arranque; si vienes del archivo viejo, pasalo con "
               "--bat D:\\ZLia\\barrido-n1-expertos.py"])
    print("  instrumento: %s (directo con python; sin bat desde la r47)" % n1)
    print(yellow("  corre CON la receta ya promovida (-np 2): sus numeros viven en el mundo final."))
    if not confirmar("LANZAR", "Ocupara el rig ~50-65 min. Sin descargas ni apps en paralelo."):
        print(gray("  cancelado."))
        informe(rutas["informe"], "P6 N1 formal CANCELADO por el Director",
                ["- el instrumento no se lanzo"])
        return 1
    cmd = [sys.executable, n1]
    try:
        rc = subprocess.call(cmd, cwd=os.path.dirname(os.path.abspath(n1)))
    except KeyboardInterrupt:
        print(yellow("\n  INTERRUMPIDO (Ctrl+C): N1 formal pausado. El resume de "
                     "la casa permite repetirlo."))
        return 130
    if rc != 0:
        fatal("barrido-n1-expertos.py salio con rc=%d" % rc,
              ["revisa su salida/informe; el resume de la casa permite repetirlo"])
    estado["pasos"]["6"] = {"estado": "EJECUTADO", "bat": n1}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P6 N1 formal -> EJECUTADO",
            ["- instrumento: %s" % n1, "- rc: %d" % rc,
             "- recuerda: sanity tras N1 (p3 --tag n1 con el server del cuant actual)"])
    print(cyan("  siguiente: sanity del N1 (p3 --tag n1) y luego p7 (N2 dosis)."))
    return 0


# ---------------- P7..P10: guiados (el instrumento fino se genera al llegar) -

CHECKLISTS = {
    "7": ("N2 - dosis re-aplicadas sobre el cuant nuevo",
          ["re-ancla con el modelo nuevo (misma receta promovida)",
           "re-aplicar: escalera k de N1 (transfiere: es arquitectura)",
           "re-aplicar: cache de prompts y -ctxcp 4 (ahora con ~1 GB mas de margen)",
           "UB1K SOLO donde no estorbe (R32: UB1K x NCM = -16.5%)",
           "re-check rapido de NCM37C4 (dosis de capas: no transfiere limpia)",
           "sanity con tool-calling OBLIGATORIO (p3 --tag n2 con el modelo nuevo en config)"],
          "criterio: >= +8% t/s con calidad intacta y ~+1 GB RAM libre [N2 s5]"),
    "8": ("N4 - escalera de VRAM sobre el cuant nuevo",
          ["escalera ascendente de ngl/limites (una dosis por corrida, ancla por sesion)",
           "MEC dosis fina en MiB; regla cliff-1 (para UNO antes del cliff)",
           "certificados: nvidia-smi <= 3.7 GB, delta de buffer en log, pageouts ~ 0"],
          "criterio: frontera VRAM estable sin cliff; modo dual ratificado"),
    "9": ("RUTA 0 - build b11901 (2 zips, sin compilar)",
          ["descargar (cuando el rig NO mide): llama-b11901-bin-win-cuda-12.4-x64.zip",
           "+ el zip de cudart DLLs del mismo release (sin el cudart la GPU queda dormida)",
           "re-auditoria de defaults del build nuevo (dump vs llama-flags)",
           "re-certificar overrides: la clave qwen35moe.expert_used_count puede cambiar",
           "probar si cache-reuse revive (busca 'restored context checkpoint' en el log)",
           "re-ancla completa: el build nuevo es un mundo nuevo"],
          "criterio: reuse vivo o motivo cerrado con certificado; overrides aplicados"),
    "10": ("N5 - duelo spec vs NP2 + receta final",
           ["fase E: MTP-n2 (el draft puede venir dentro del GGUF nuevo: revisa p5 nextn)",
            "fase S: DSpark Q4_K_M n2/n3 (A/B conf-min 0.5-0.7) -> DFlash-n2 -> EAGLE3",
            "fijar SIEMPRE --spec-draft-n-max y --spec-draft-p-min explicitos",
            "DUELO: receta con NP2 sin spec vs receta con spec sin NP2 (mediana de 3)",
            "ojo #25345 kv-unified: si el draft calla, --kv-unified off",
            "spot-check ES por config; gana el mejor t/s x calidad"],
           "criterio: >= +25% [M] con spot-check limpio; luego receta final con backup"),
}


def paso_guiado(n, args, rutas, estado):
    titulo, items, criterio = CHECKLISTS[n]
    print(bold(cyan("\n=== P%s - %s (guiado) ===" % (n, titulo))))
    print(yellow("  (el instrumento fino de este nivel se genera con el esqueleto de "
                 "la casa cuando se llega: aqui la ruta y la decision por escrito)"))
    for it in items:
        print("    [ ] %s" % it)
    print("  %s" % gray(criterio))
    try:
        nota = input(yellow("  resultado/decision de este paso (linea libre, Enter para dejar pendiente): ")).strip()
    except EOFError:
        nota = ""
    registro = {"estado": "REGISTRADO" if nota else "PENDIENTE"}
    if nota:
        registro["nota"] = nota
    estado["pasos"][n] = registro
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P%s %s -> %s" % (n, titulo.split(" ·")[0], registro["estado"]),
            (["- nota del Director: %s" % nota] if nota else ["- pendiente"]) +
            ["- checklist aplicada (%d items)" % len(items)])
    print(cyan("  registrado en campana-estado.json y campana-INFORME.md"))
    return 0


# ---------------- estado / plan / main --------------------------------------

VERDES_ESTADO = ("GO", "PROMOVIDA", "YA-PROMOVIDA", "OK", "DESCARGADA",
                 "VERIFICADO-HUMO-OK", "EJECUTADO", "REGISTRADO")
AMARILLOS_ESTADO = ("DUDOSO", "PENDIENTE", "EN-ESPERA-DEL-JUEZ", "INCOMPLETO",
                    "VERIFICADO-SIN-HUMO", "REVERTIDA", "NO-GO")


def mostrar_estado(rutas, estado):
    print(bold(cyan("\n=== CAMPANA - %s ===" % (estado.get("actualizado") or "sin empezar"))))
    print("  informe append-only: %s" % rutas["informe"])
    tabla = [("1", "mediana NP2 (higiene + NOCACHE)"), ("2", "promocion -np 2"),
             ("3", "sanity 20 prompts -> cierra N3"), ("4", "descarga UD-IQ3_XXS"),
             ("5", "verificacion + humo del cuant"), ("6", "N1 formal (sin bat)"),
             ("7", "N2 dosis re-aplicadas"), ("8", "N4 escalera VRAM"),
             ("9", "RUTA 0 build b11901"), ("10", "N5 duelo spec vs NP2 + receta final")]
    for n, titulo in tabla:
        paso = estado["pasos"].get(n, {})
        et = paso.get("estado", "PENDIENTE")
        estilo = green if et in VERDES_ESTADO else (yellow if et in AMARILLOS_ESTADO else red)
        print("   P%-3s %-38s %s" % (n, titulo, estilo(et)))
    n3 = estado.get("n3", {})
    print("  N3: cerrado=%s veredicto_sanity=%s" % (n3.get("cerrado", False),
                                                    n3.get("veredicto_sanity", "-")))
    print(gray("  regla: descargas cuando el rig NO mide; mediana de 3; --fuerza salta "
               "puertas y lo deja escrito."))
    return 0


# ---------------- MODO CAMPANA (doble click) ---------------------------------

QUE_HACE_PASO = {
    "1": "higiene (discos + RAM) + mediana de 3 de NP2 — mide 3 corridas (~15 min)",
    "2": "anade -np 2 a config.txt con backup automatico (5 min; --revert restaura)",
    "3": "sanity de 20 prompts: abre el server antes (ABRIR-QWEN.bat) y TU lees "
         "las respuestas (~20-30 min)",
    "4": "descarga el cerebro nuevo (14.07 GB): mejor DE NOCHE; Ctrl+C pausa y p4 retoma",
    "5": "verifica lo bajado (bytes + SHA256 + MTP dentro) + humo del server (~10 min)",
    "6": "N1 formal con barrido-n1-expertos.py (~50-65 min, mide 18 configs)",
    "7": "guiado N2: re-aplicar las dosis al cuant nuevo (te pide una nota)",
    "8": "guiado N4: escalera de VRAM (te pide una nota)",
    "9": "guiado RUTA 0: build b11901 y re-ancla (te pide una nota)",
    "10": "guiado N5: duelo spec vs NP2 + receta final de campana (te pide una nota)",
}


def _siguiente_paso(estado):
    """Numero del siguiente paso (1..10) o None si la campana esta cerrada.
    Regla: el primero cuyo estado no este VERDE; antes de p4 se exige el N3
    cerrado (si el juez no firmo, lo que toca es el veredicto de p3)."""
    for n in range(1, 11):
        if P4_APARCADA and n in (4, 5):
            continue
        if estado.get("pasos", {}).get(str(n), {}).get("estado") not in VERDES_ESTADO:
            # R43: con p4/p5 aparcadas, el primer paso no-aparcado >= 4 (hoy p6)
            # HEREDA la puerta del juez: sin N3 cerrado, lo que toca es el
            # veredicto de p3 (el U17 del taller cazó este hueco).
            if n >= 4 and not estado.get("n3", {}).get("cerrado"):
                return 3
            return n
    return None


def modo_campana(args, rutas, estado):
    """DOBLE CLICK = modo campana: muestra la foto y OFRECE ejecutar el paso
    que toca. Nada corre sin un SI escrito del Director; el SI de aqui solo
    abre la puerta del paso — despues el paso pide SUS confirmaciones y deja
    TODO escrito en el informe (append-only)."""
    mostrar_estado(rutas, estado)
    n = _siguiente_paso(estado)
    if n is None:
        print(green("\n  Los 10 pasos estan VERDE: campana cerrada. Felicidades, Director."))
        return 0
    print(bold(cyan("\n  SIGUIENTE PASO: P%s" % n)))
    print(cyan("  %s" % QUE_HACE_PASO[str(n)]))
    try:
        respuesta = input(cyan("  escribe SI y Enter para ejecutar P%s ahora "
                               "(otra cosa = solo mirar): " % n))
    except (EOFError, KeyboardInterrupt):
        respuesta = ""
        print()
    if respuesta.strip().upper() != "SI":
        print(gray("  ok, solo miraste. Para correrlo a mano: CAMPANA.bat p%s" % n))
        return 0
    informe(rutas["informe"], "MODO CAMPANA: Director acepto ejecutar P%s" % n,
            ["- %s" % QUE_HACE_PASO[str(n)]])
    if str(n) in CHECKLISTS:
        return paso_guiado(str(n), args, rutas, estado)
    return {1: paso1, 2: paso2, 3: paso3, 4: paso4,
            5: paso5, 6: paso6}[n](args, rutas, estado)


# ---------------- MODO AUTO (doble click, pedido del Director 29-oct) -------

PASOS_AUTO = {1: paso1, 2: paso2, 4: paso4, 5: paso5, 6: paso6}
AUTO_ULTIMO = 6   # p7..p10 son GUIADOS: sus instrumentos finos se fabrican
                  # con los resultados de 1..6 (regla de la casa); el AUTO
                  # termina su turno ahi, con todo escrito.


def _prevuelo_auto(args, rutas, estado):
    """(fatales, avisos) ANTES de mover una sola medida: si la noche no puede
    completarse, mejor morir a los 5 segundos con el motivo que a las 2
    horas. Solo FATALiza lo que bloquea SIEMPRE; lo demas son avisos."""
    fatales, avisos = [], []
    if health_ok(args.puerto):
        fatales.append("hay un server vivo en el puerto %d: apagalo antes del "
                       "AUTO (el rig debe estar quieto para medir)" % args.puerto)
    ram = ram_sistema()
    if ram:
        libre_mib, total_mib = ram
        usada = 100.0 * (total_mib - libre_mib) / max(total_mib, 1)
        if usada >= 80.0:
            fatales.append("RAM al %.0f%% usada ANTES de empezar (regla R28: cierra "
                           "apps; si no, el barrido mide el pagefile, no la receta)" % usada)
        elif usada >= 70.0:
            avisos.append("RAM al %.0f%%: ideal cerrar apps antes de medir (R28)" % usada)
    if not os.path.exists(rutas["config"]):
        fatales.append("no esta config.txt en %s" % rutas["config"])
    else:
        cfg = leer_config(rutas["config"])
        if not (cfg.get("FLAGS_BASE") or "").strip():
            fatales.append("config.txt sin FLAGS_BASE (p2 no puede promover)")
        if not (cfg.get("RUTA_SERVER") or "").strip():
            fatales.append("config.txt sin RUTA_SERVER (p3/p5 no pueden arrancar server)")
        elif not os.path.exists(cfg["RUTA_SERVER"]):
            fatales.append("RUTA_SERVER no existe en disco: %s" % cfg["RUTA_SERVER"])
    if not _binario_hf():
        fatales.append("sin cliente de HuggingFace (hf): la descarga de p4 no puede "
                       "correr (instala con: pip install -U \"huggingface_hub[cli]\")")
    base_disco = rutas["models"] if os.path.isdir(rutas["models"]) else rutas["base"]
    libre, _tot = gb_libres(base_disco)
    if libre is not None and libre < DISCO_MIN_GB:
        fatales.append("disco sin espacio para la descarga de 14.07 GB (%.1f GB "
                       "libres, minimo %.0f)" % (libre, DISCO_MIN_GB))
    n1 = args.bat or os.path.join(rutas["base"], "barrido-n1-expertos.py")
    if not os.path.exists(n1):
        avisos.append("barrido-n1-expertos.py no encontrado (la maleta lo "
                      "despliega al arrancar): el AUTO llegara hasta p5 y "
                      "parara limpio antes del N1 formal")
    return fatales, avisos


def _arranca_server_receta(rutas, args, log_path, timeout_s=420):
    """Arranca el server DIARIO con la receta de config.txt (FLAGS_BASE +
    FLAGS_GANADORAS, modelo actual incluido) y espera a que el health
    responda. Devuelve el Popen: QUIEN LLAMA es dueno de apagarlo (nunca
    toca servers ajenos). Patron de seguridad identico al humo de p5:
    log propio acumulativo + fail-fast si el server muere en la carga."""
    cfg = leer_config(rutas["config"])
    servidor = cfg.get("RUTA_SERVER", "")
    if not servidor or not os.path.exists(servidor):
        fatal("RUTA_SERVER no valido para arrancar el server del sanity: %r" % servidor,
              ["revisa RUTA_SERVER en config.txt"])
    flags = (cfg.get("FLAGS_BASE", "") + " " + cfg.get("FLAGS_GANADORAS", "")).split()
    cmd = [servidor] + flags + ["--host", "127.0.0.1", "--port", str(args.puerto)]
    print(gray("  $ %s" % " ".join(cmd)))
    flog = open(log_path, "a", encoding="utf-8")
    flog.write("===== server del sanity AUTO %s (puerto %d) =====\n"
               % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), args.puerto))
    flog.flush()
    proc = subprocess.Popen(cmd, stdout=flog, stderr=subprocess.STDOUT)
    try:
        fin = time.time() + timeout_s
        while time.time() < fin:
            if proc.poll() is not None:
                fatal("el server del sanity murio durante la carga (rc=%s)" % proc.returncode,
                      ["forense en %s" % log_path])
            if health_ok(args.puerto):
                break
            time.sleep(2)
        else:
            fatal("el server del sanity no levanto en %d min" % (timeout_s // 60),
                  ["forense en %s" % log_path])
    except BaseException:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        raise
    finally:
        flog.close()
    return proc


def _auto_apaga(proc):
    """Apaga SOLO el hijo que este AUTO lanzo (multiplataforma, sin taskkill
    y sin riesgo de matar un server ajeno)."""
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _auto_informe_trail(rutas, etiqueta):
    """Deja escritas en el informe las confirmaciones auto-aceptadas de este
    tramo (evidencia append-only; vacia el acumulador)."""
    if AUTO["aceptadas"]:
        informe(rutas["informe"], "AUTO (%s): confirmaciones auto-aceptadas" % etiqueta,
                ["- %s" % x for x in AUTO["aceptadas"]])
        AUTO["aceptadas"] = []


def _auto_detener(rutas, causa, lineas):
    """Detencion LIMPIA del turno: todo lo hecho queda escrito y se explica
    la causa. Devuelve rc 2 (nunca se salta una puerta roja)."""
    _auto_informe_trail(rutas, "al detenerse")
    informe(rutas["informe"], "AUTO DETENIDO: %s" % causa, lineas)
    print(red("\n[AUTO DETENIDO] %s" % causa))
    for ln in lineas:
        print(yellow("  %s" % ln))
    print(cyan("  lo hecho queda escrito. Re-doble-click cuando resuelvas la causa: "
               "todo retoma donde quedo."))
    return 2


def _auto_paso3(args, rutas, estado):
    """P3 en AUTO: si no hay server vivo, arranca UNO PROPIO con la receta
    diaria (lo apaga al terminar), corre los 20 prompts y aplica el veredicto
    OBJETIVO (0 errores + 20/20 con carne + 3 anclas). Si OK cierra el N3
    (revocable por el Director con p3 --veredicto FALLA); si FALLA, detiene
    el turno dejando las respuestas para el juez humano."""
    print(bold(cyan("\n=== P3 (AUTO) - sanity de 20 prompts con server propio ===")))
    p2 = estado["pasos"].get("2", {})
    if p2.get("estado") not in ("PROMOVIDA", "YA-PROMOVIDA"):
        return _auto_detener(rutas, "P3 exige p2 promovida (estado: %s)"
                             % (p2.get("estado") or "SIN P2"),
                             ["- la mediana p1 no dio GO o p2 no corrio: revisa el informe"])
    tag = "np2" if p2.get("estado") in ("PROMOVIDA", "YA-PROMOVIDA") else "libre"
    carpeta = os.path.join(rutas["base"], "campana-sanity-%s" % tag)
    os.makedirs(carpeta, exist_ok=True)
    proc = None
    if health_ok(args.puerto):
        print(cyan("  usando el server vivo en el puerto %d (NO es mio: no lo toco "
                   "al terminar)." % args.puerto))
    else:
        print(cyan("  no hay server vivo: el AUTO arranca uno con la receta diaria "
                   "(puerto %d) y lo apaga al terminar..." % args.puerto))
        log_srv = os.path.join(rutas["base"], "campana-sanity-%s-server.log" % tag)
        proc = _arranca_server_receta(rutas, args, log_srv)
    try:
        fallas, respuestas = _p3_corre_sanity(args, rutas, estado, carpeta, tag)
    finally:
        if proc is not None:
            _auto_apaga(proc)
    v, motivos = _sanity_auto_veredicto(fallas, respuestas)
    if v == "OK":
        estado["n3"]["veredicto_sanity"] = "OK"
        estado["n3"]["cerrado"] = True
        estado["n3"]["cerrado_en"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estado["pasos"]["3"] = {"estado": "OK", "carpeta": carpeta,
                                "errores_http": fallas, "veredicto_auto": True}
        guardar_estado(rutas["estado"], estado)
        informe(rutas["informe"], "P3 (AUTO) veredicto objetivo -> OK: N3 CERRADO",
                ["- criterio: 0 errores HTTP + 20/20 respuestas con carne + 3 anclas "
                 "(391 / verde / Valparaiso)",
                 "- veredicto AUTO, revocable: lee %s y si algo no te gusta cierra "
                 "con p3 --veredicto FALLA (+ p2 --revert)" % carpeta])
        print(green(bold("  N3 CERRADO con el veredicto objetivo del AUTO "
                         "(revocable por el Director).")))
        return 0
    estado["pasos"]["3"] = {"estado": "EN-ESPERA-DEL-JUEZ", "carpeta": carpeta,
                            "errores_http": fallas}
    guardar_estado(rutas["estado"], estado)
    return _auto_detener(rutas,
                         "el sanity no paso el criterio objetivo: %s" % "; ".join(motivos),
                         ["- las 20 respuestas estan en %s (tu eres el catador)" % carpeta,
                          "- cierra a mano con: py campana-10-pasos.py p3 --veredicto OK (o FALLA)"])


def modo_auto(args, rutas, estado):
    """DOBLE CLICK = MODO AUTO (pedido del Director 29-oct: 'doble click y que
    haga todo automaticamente... aunque tarde 2 horas... dejando siempre un
    log; prioridad es seguridad ante malware'). Corre los pasos 1..6 en orden
    SIN preguntar nada: las confirmaciones se auto-aceptan y quedan escritas.
    Seguridad no negociable: solo el repo oficial, SHA256 certificado
    obligatorio ANTES de usar nada (p5 fail-fast), y ninguna puerta roja se
    salta: si algo esta mal, el turno SE DETIENE LIMPIO con su log y el
    re-doble-click retoma donde quedo."""
    AUTO["on"] = True
    AUTO["aceptadas"] = []
    print(bold(cyan("\n=== MODO AUTO — la campana trabaja sola (pasos 1..%d) ===" % AUTO_ULTIMO)))
    print(cyan("  sin preguntas: las confirmaciones se auto-aceptan y quedan escritas."))
    print(cyan("  seguridad: solo repo oficial + SHA256 certificado obligatorio; "
               "puertas rojas = parada limpia."))
    if P4_APARCADA:
        print(cyan("  P4-P5 APARCADAS (Anexo R43): el cuant vigente ya trae "
                   "heretic+MTP; este turno NO descarga nada."))
    mostrar_estado(rutas, estado)
    fatales, avisos = _prevuelo_auto(args, rutas, estado)
    resumen_prevuelo = ("OK" if not fatales and not avisos
                        else ("avisos: " + "; ".join(avisos) if avisos else "FATAL"))
    informe(rutas["informe"], "MODO AUTO arrancado (pedido del Director 29-oct)",
            ["- pasos 1..%d en orden, sin preguntas; confirmaciones quedan escritas" % AUTO_ULTIMO,
             "- seguridad: repo oficial unico + SHA256 obligatorio antes de usar nada; "
             "--fuerza no existe en AUTO",
             "- prevuelo: %s" % resumen_prevuelo])
    for av in avisos:
        print(yellow("  aviso del prevuelo: %s" % av))
    if fatales:
        return _auto_detener(rutas, "el prevuelo encontro bloqueos (mejor ahora que "
                             "a las 2 horas)", ["- %s" % f for f in fatales])
    try:
        for n in range(1, AUTO_ULTIMO + 1):
            if P4_APARCADA and n in (4, 5):
                print(cyan("\n  P%d APARCADA (Anexo R43): fuera del turno, sin "
                           "descarga." % n))
                continue
            estado = leer_estado(rutas["estado"])
            est = estado["pasos"].get(str(n), {}).get("estado")
            if est in VERDES_ESTADO:
                print(cyan("\n  P%d ya estaba hecho (%s): se salta." % (n, est)))
                continue
            if n == 3:
                rc = _auto_paso3(args, rutas, estado)
            else:
                rc = PASOS_AUTO[n](args, rutas, estado)
            _auto_informe_trail(rutas, "P%d" % n)
            if rc != 0:
                return _auto_detener(rutas, "P%d devolvio rc=%d (mira su salida arriba)" % (n, rc),
                                     ["- el paso no quedo verde; el re-doble-click retoma"])
        estado = leer_estado(rutas["estado"])
        hechos = [n for n in range(1, AUTO_ULTIMO + 1)
                  if estado["pasos"].get(str(n), {}).get("estado") in VERDES_ESTADO]
        lineas_fin = ["- verdes ahora: %s" % (", ".join("P%d" % x for x in hechos) or "ninguno"),
                      "- P7..P10: siguiente fase (sus instrumentos finos se fabrican CON "
                      "estos resultados; regla de la casa)"]
        if P4_APARCADA:
            lineas_fin.append("- P4-P5 APARCADAS por decision del Director (Anexo R43): "
                              "el cuant vigente SC117 APEX-I-Mini ya trae heretic+MTP "
                              "(SHA e4eae0e2...118d4); la UD-IQ3_XXS queda pinada como "
                              "duelo opcional de P10")
        informe(rutas["informe"], "AUTO FIN DE TURNO: pasos 1..%d gestionados" % AUTO_ULTIMO,
                lineas_fin)
        print(green(bold("\n  FIN DE TURNO AUTO: pasos 1..%d gestionados." % AUTO_ULTIMO)))
        print(green("  verdes: %s" % (", ".join("P%d" % x for x in hechos) or "ninguno")))
        print("  log completo : %s" % rutas["informe"])
        print("  estado       : %s" % rutas["estado"])
        print(cyan("  P7..P10: siguiente fase — se fabrican con estos resultados."))
        return 0
    except SystemExit:
        return _auto_detener(rutas, "una puerta/freno del paso detuvo el turno "
                             "(mira el [FATAL] de arriba)",
                             ["- nada se salto: la puerta roja manda, incluso en AUTO",
                              "- lo hecho quedo escrito; resuelve la causa y re-doble-click"])
    except KeyboardInterrupt:
        _auto_informe_trail(rutas, "al interrumpirse")
        informe(rutas["informe"], "AUTO INTERRUMPIDO (Ctrl+C)",
                ["- lo hecho queda escrito; re-doble-click retoma donde quedo"])
        print(yellow("\n[AUTO] interrumpido (Ctrl+C): lo hecho queda escrito."))
        return 130


def main():
    ap = argparse.ArgumentParser(description=VERSION)
    ap.add_argument("paso", nargs="?", default=None,
                    help="estado | plan | p1..p10 (sin argumento = MODO AUTO)")
    ap.add_argument("--dir", help="carpeta base de la campana (def: junto al script)")
    ap.add_argument("--config", help="ruta de config.txt (def: base/config.txt)")
    ap.add_argument("--puerto", type=int, default=9931)
    ap.add_argument("--b1", help="p1: carpeta de la corrida 1 (def: base/faseN3)")
    ap.add_argument("--b2", help="p1: carpeta de la corrida 2 (def: base/faseN3-np2-b2)")
    ap.add_argument("--b3", help="p1: carpeta de la corrida 3 (def: base/faseN3-np2-b3)")
    ap.add_argument("--sin-corridas", action="store_true",
                    help="p1: cosechar sin lanzar corridas nuevas")
    ap.add_argument("--revert", action="store_true", help="p2: restaurar backup")
    ap.add_argument("--veredicto", help="p3: OK | FALLA (cierra el N3)")
    ap.add_argument("--tag", help="p3: etiqueta de la carpeta de sanity")
    ap.add_argument("--repo", default=REPO_DEFAULT,
                    help="p4: repo HF (def: %s). El ALT (%s) esta "
                         "DESAUTENTICADO en vivo 29-oct: sirve la variante "
                         "SIN MTP y p4 lo rechaza"
                         % (REPO_DEFAULT, REPO_ALT))
    ap.add_argument("--dry-run", action="store_true", help="p4: mostrar sin descargar")
    ap.add_argument("--sin-humo", action="store_true", help="p5: solo certificar, sin server")
    ap.add_argument("--bat", help="p6: ruta de barrido-n1-expertos.py (respaldo; la maleta ya lo despliega)")
    ap.add_argument("--ofrecer", action="store_true",
                    help="sin paso: MODO CAMPANA r39 (foto + oferta con SI escrito); "
                         "el doble click sin esto ahora es MODO AUTO")
    ap.add_argument("--fuerza", action="store_true",
                    help="saltar puertas A PROPOSITO (queda escrito en el informe)")
    args = ap.parse_args()
    rutas = _rutas(args)
    estado = leer_estado(rutas["estado"])

    if args.paso is None:
        rc = (modo_campana(args, rutas, estado) if args.ofrecer
              else modo_auto(args, rutas, estado))
        _pausa_doble_click()
        return rc

    bruto = args.paso.lower()
    paso = bruto[1:] if (bruto.startswith("p") and bruto[1:].isdigit()) else bruto
    if paso == "estado":
        rc = mostrar_estado(rutas, estado)
        _pausa_doble_click()
        return rc
    if paso == "plan":
        mostrar_estado(rutas, estado)
        print(gray("  detalle completo: plan-siguientes-10-pasos.md en el repo"))
        return 0
    if paso == "1":
        return paso1(args, rutas, estado)
    if paso == "2":
        return paso2(args, rutas, estado)
    if paso == "3":
        return paso3(args, rutas, estado)
    if paso == "4":
        return paso4(args, rutas, estado)
    if paso == "5":
        return paso5(args, rutas, estado)
    if paso == "6":
        return paso6(args, rutas, estado)
    if paso in CHECKLISTS:
        return paso_guiado(paso, args, rutas, estado)
    print(red("paso desconocido: %s (usa estado | plan | p1..p10)" % args.paso))
    return 1


if __name__ == "__main__":
    sys.exit(main())
