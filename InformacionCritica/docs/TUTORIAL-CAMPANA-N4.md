# TUTORIAL CAMPANA-N4.py — NIVEL 4: MEMORIA (VRAM/RAM) Y BALANCE DE RECURSOS
# (al completo: base nueva, arranque, campana, certificados, cierre)
# v1.0 — 2026-10-31 — casa: puerto 9932, MED3 (3 corridas), cliff-1 (0.70), 3712 MB, pageouts ~= 0

Este tutorial es la guia UNICA y COMPLETA para correr el NIVEL 4 en tu rig.
Si algo no esta aqui, no se hace: se pregunta en el chat y se escribe aqui.

---
## 0) QUE ES ESTA OLLA (y que NO es)

- CAMPANA-N4.py es el NIVEL 4 de la campana: el tema RAM y recursos.
  Hereda la cadena cerrada de la primera olla (CAMPANA.py, pasos 1..6).
- Tiene DOS pasos: P7 (rampa RAM: re-ancla + dosis fina CTXCP4 + sanity)
  y P8 (el cuerpo: escalera de VRAM NCM/MEC + certificados + cliff-1).
- Lleva dentro TODAS las pruebas y los logs: trampas anti-bugs T1-T18,
  puertas rojas, tabla de rc, bateria propia 47/47 VERDE, informe
  append-only, CSV y logs de server en APPEND.
- Anti-malware: huella de auto-verificacion (5F24E8CF...7ED1). Si alguien
  edita el archivo, SE NIEGA A CORRER (rc=3) y pide re-descarga.
- NO es y NO hace: no es el N5 (si pides 9 o 10 te responde donde vive el
  N5), NO escribe config.txt NUNCA (la receta final es del N5), no toca
  servers ajenos (solo los hijos que ella arranca, puerto 9932 propio).

---
## 1) LOS 4 ARCHIVOS DE LA BASE (tu caso: D:\ZLia)

La olla trabaja SOBRE SU CARPETA (la carpeta donde esta el .py, o la que
pases con --dir). En una base NUEVA como D:\ZLia hacen falta:

  1. CAMPANA-N4.py            <- la olla (con su huella intacta)
  2. campana-estado.json      <- EL RECIBO de la PRIMERA olla (pasos 1..6)
  3. config.txt               <- la receta de la casa (RUTA_SERVER,
                                 RUTA_MODELO, FLAGS_BASE, FLAGS_GANADORAS)
  4. nada mas (los logs los crea ella sola)

DONDE ESTA EL RECIBO: en la carpeta donde corrio la primera campana
(la de CAMPANA.py / los pasos 1 al 6). El archivo se llama
campana-estado.json y vive JUNTO a ese script. Copialo tal cual a
D:\ZLia. La puerta lo lee y comprueba: N3 cerrado Y paso 6 verde.
NO LO FABRIQUES A MANO: un recibo falso es exactamente lo que la
cadena esta disenada para rechazar.

Y config.txt: copia EL MISMO que ya usan tus otras ollas (el vivo).
Sin config.txt el AUTO se detiene en el prevuelo (es fatal, no aviso).

Rig quieto antes de medir: cierra el charlatan (no puede haber un server
vivo en el puerto 9932) y cierra apps/juegos/navegador pesado (higiene
R28: la medicion es de RAM, una ventana abierta la ensucia).

---
## 2) ARRANQUE (dobles clicks y comandos)

Dobles clicks (los .bat van JUNTO a la olla en D:\ZLia):

  - CAMPANA-N4.bat         = EL DOBLE CLICK Y YA: corre P7 y P8 en
                             orden, sin preguntas. Si la base tiene el
                             recibo, es la campana normal; si no lo
                             tiene, cruza la puerta A PROPOSITO y lo
                             deja escrito, y cocina igual.
  - CAMPANA-N4-AUTO.bat    = mismo contenido (por si ya le tenias
                             hecho el acceso directo).
  - CAMPANA-N4-ESTADO.bat  = solo la FOTO: que paso toca, como esta la
                             puerta, que queda escrito. Nunca bloquea.

En consola (equivalente):

  py CAMPANA-N4.py estado        foto del estado
  py CAMPANA-N4.py plan          foto + donde viven los planes del N4
  py CAMPANA-N4.py               AUTO (P7..P8, sin preguntas)
  py CAMPANA-N4.py p7            paso 7 solo
  py CAMPANA-N4.py p8            paso 8 solo
  py CAMPANA-N4.py p7 --previa   ensayo: muestra la tabla SIN arrancar
                                 ningun server

Utiles (no obligatorios): --dir (otra carpeta base), --config (otro
config.txt), --puerto (def 9932), --corridas (def 3 = MED3),
--archivo (tabla propia de candidatas/escalera), --sin-sanity.

---
## 3) EL CAMINO AL COMPLETO

EL CAMINO — un solo doble click y ya:
  1. Doble click en CAMPANA-N4.bat. Ella sola: P7 (rampa RAM) y luego
     P8 (escalera de VRAM), sin preguntas.
  2. Si la base tiene el recibo (campana-estado.json), la puerta pasa
     verde y todo es campana normal. Si NO lo tiene, el lanzador cruza
     la puerta A PROPOSITO (queda ESCRITO en el informe) y cocina igual:
     mismo resultado, salto firmado.
  3. Corte de luz o ventana cerrada? Re-doble-click y retoma donde
     quedo (lo hecho queda escrito).
  4. Cuando puedas, trae el recibo de la base de la primera campana a
     esta carpeta (seccion 1): con recibo, ninguna puerta se cruza.

COMANDOS EQUIVALENTES (si prefieres consola — es lo mismo que hace el
doble click):
  py CAMPANA-N4.py p7 --fuerza
  py CAMPANA-N4.py p8 --fuerza

OJO: el MODO AUTO puro (py CAMPANA-N4.py sin argumentos) pide recibo
SI o SI y se detiene limpio sin el (T9): por eso el doble click usa
los pasos sueltos. Con recibo en la base, AUTO y doble click coinciden.

---
## 4) QUE HACE CADA PASO Y QUE CERTIFICA

P7 — rampa RAM (opcional pero recomendado):
  re-ancla (medir el punto de partida real) + dosis fina CTXCP4
  (libera ~1.5-1.8 GB de RAM) + sanity con anclas (si las respuestas
  se desvian, avisa; con --sin-sanity se omite a proposito).

P8 — el cuerpo del N4 (escalera de VRAM):
  - Escalera NCM/MEC en MiB: peldanos de 38 hacia abajo y dosis MEC;
    los peldanos NO se acumulan: cada uno se compone desde la receta
    base (pila de vuelta con ';'). NGL va despues de subir NCM.
  - Ancla MED3: 3 corridas x 8 prompts sobre la receta vigente (la GPU
    fria miente ~-15%: el ancla es la mediana medida, no la memoria).
  - CERTIFICADOS POR PELDANO:
      * nvidia-smi <= 3712 MB  (certificado BLANDO: avisa, nunca frena;
        si nvidia-smi no responde, el informe lo declara y el peldano
        no queda certificado a ciegas)
      * pageouts ~= 0 contados del log del server (certificado RAM:
        si hay derrame a disco, el peldano miente aunque el t/s sea bueno)
  - Regla cliff-1: si un peldano tira el t/s por debajo del 70% del
    ancla (CLIFF_FRACCION = 0.70), se declara CLIFF, se retrocede UN
    peldano y ahi queda LA FRONTERA. Muertos > 0 manda (T17).

---
## 5) COMO LEER LOS LOGS (donde vive cada cosa)

Todo en la base (D:\ZLia), mundo propio campana-n4-*:

  campana-n4-estado.json     estado vivo (paso, veredicto, frontera)
  campana-n4-INFORME.md      bitacora APPEND-ONLY (nada se sobreescribe)
  campana-n4-p7/  campana-n4-p8/    tablas, respuestas y datos por paso
  CSV de 9 columnas          una fila por peldano: incluye vram_mb,
                             pageouts, spot_ok, acciones
  logs del server            APPEND (acumulan sesiones con cabecera)

REGLA DE ORO: lo que no esta escrito en el informe no paso. La frontera
del N4 se DECIDE por lo que dicen estos logs (numero, hora y peldano),
no por impresiones.

---
## 6) TABLA DE CODIGOS DE SALIDA (rc)

  0     OK (paso verde, o foto escrita)
  1     error de uso / paso desconocido / pidiste 9 o 10 (el N5 vive
        en SU archivo cuando nazca)
  2     FATAL del ciclo: puerta roja sin --fuerza, config ausente,
        server vivo en el puerto, causa visible arriba
  3     HUELLA: el archivo fue tocado. PARADA LIMPIA, no se ejecuta
        nada. Re-descarga CAMPANA-N4.py y verifica su huella.
  130   Ctrl+C: parado limpio, lo hecho queda guardado en el informe

---
## 7) LAS PUERTAS (como funcionan)

  - Puerta de ENTRADA: la primera olla cerrada (campana-estado.json con
    N3 cerrado Y paso 6 verde en la base). En AUTO es dura; en p7/p8
    sueltos se cruza con --fuerza y queda escrito.
  - Puerta p7 -> P8: p8 exige p7 verde (GO o REGISTRADO). Con --fuerza
    se salta A PROPOSITO y el lado RAM de dosis fina queda SIN medir
    (pendiente) — lo deja anotado el informe.
  - Ninguna puerta se salta sola. Un salto siempre deja rastro.

---
## 8) LO QUE NO SE HACE NUNCA

  - NO editar CAMPANA-N4.py (ni "arreglarlo"): la huella lo detecta y
    muere rc=3. Re-descargar, nunca re-cocinar a mano.
  - NO fabricar ni retocar campana-estado.json (recibo falso = veneno).
  - NO cerrar la ventana a lo bruto a media medicion: usa Ctrl+C (rc=130
    limpio) o espera el turno; y si pasa algo, re-doble-click y retoma.
  - NO correr el AUTO con el charlatan abierto (puerto 9932) ni con
    juegos/apps pesadas abiertas (higiene R28: pageouts falsos).
  - NO pedirle a esta olla que escriba config.txt: NUNCA lo hace (la
    receta final es del N5, en su archivo cuando llegue).
  - NO mezclar campanas: cada olla tiene SU mundo (campana-*). No
    renombrar ni arrastrar logs de una base a otra a mano.

---
## 9) SI ALGO FALLA (causas visibles, por orden probable)

  "no encuentro campana-estado.json en ..."  -> solo bloquea al AUTO
     puro (py CAMPANA-N4.py sin argumentos). El doble click de
     CAMPANA-N4.bat ya lo cruza a proposito (queda escrito); igual,
     trae el recibo de la base vieja cuando puedas (seccion 1).
  "no hay config.txt en ..."                 -> copia el config.txt vivo
     de la casa a la base (seccion 1).
  "RUTA_SERVER no existe / RUTA_MODELO no existe" -> el config.txt de
     esa base apunta a rutas que no estan: corrige las rutas en TU
     config (la olla no lo toca nunca) o usa --config.
  "hay un server vivo en el puerto 9932"     -> apaga el charlatan y
     re-doble-click.
  "nvidia-smi no respondio" (aviso)          -> no bloquea, pero los
     certificados de VRAM de p8 saldran vacios: revisa el driver.
  "disco con < 4.0 GB libres" (aviso)        -> los logs caben, pero
     justos: libera espacio.
  "[FATAL] auto-verificacion de huella"      -> el archivo fue tocado o
     se re-guardo con otro formato: re-descarga CAMPANA-N4.py.
  La regla general: la causa queda ESCRITA (consola + informe). Lee la
  ultima seccion del informe, resuelve, re-doble-click.

---
## 10) CIERRE DEL NIVEL 4 (que me pegas y que viene despues)

Cuando el AUTO termine (veredicto escrito), pega en el chat:
  - las ultimas ~40 lineas de campana-n4-INFORME.md, y
  - el bloque de campana-n4-estado.json (o la foto del estado).
Con eso yo: decido si la frontera esta firmada (peldano ganador +
certificados), la registro append-only, y si cierra N4 TU ordenas el
N5: nacera CAMPANA-N5.py (RUTA 0 + duelo spec vs NP2 + receta final con
backup y re-lectura). Vamos por orden: una olla por nivel.

---
# FIN DEL TUTORIAL — la olla manda sobre este papel: si este tutorial y
# el comportamiento del archivo difieren, manda el archivo, y el
# desacuerdo se escribe aqui en la siguiente ronda.
