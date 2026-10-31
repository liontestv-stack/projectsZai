#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
campana-n4-n5.py v1.0 — VIA ACTIVA N4 -> N5, REAL DESDE EL BOCETO
=================================================================
Encargo del Director (31-oct-2026): "bien, ahora si, crea el archivo
python puro real, siguiendo la guia del pseudocodigo". Este archivo es
la transcripcion EJECUTABLE del boceto de la ronda completa
(pseudocodigo/boceto-ronda-completa-p7-p10.md, nacido en la ronda 62,
auditado funcion por funcion en la r63 (F1-F12) y re-auditado en la
r64 (F13-F24) contra el codigo fuente): el plano ya paso sus dos
auditorias, este es el edificio. Cocina la cola activa de la ruta
(reencuadre del Director, ronda 66/apendice R66: fuera el mapa de
pasos, mandan los NIVELES N4 -> N5; los nombres de subcomando p7..p10
quedan como MECANISMO, no como mapa). P7 quedo FUERA de la ruta
critica (solo aplicaba a cambio de cuant y el cuant ya cerro, R59):
la ruta viva es:

  P7   N2 dosis: re-ancla con el cuant nuevo + candidatas que transfieren
       (escalera k de N1, UB, ctxcp) + sanity CON tool-calling OBLIGATORIO
       en cambio de cuant. Criterio de salida: >= +8% t/s con calidad
       intacta; si no llega, se REGISTRA y se decide con datos.
  P8   N4 escalera de VRAM sobre el cuant nuevo: peldanos (NCM primero,
       MEC dosis fina en MiB), certificados (nvidia-smi, pageouts) y
       regla cliff-1 automatica. Las dosis VRAM NO transfieren entre
       cuants: se miden UNA vez aqui.
  P9   RUTA 0: build b11901 (2 zips que DESCARGA el Director, sin
       compilar): version + cudart vivo, re-auditoria de defaults (diff
       de --help), re-certificar la clave del override, sondeo
       cache-reuse ("restored context checkpoint") y re-ancla: build
       nuevo = mundo nuevo.
  P10  N5 duelo spec vs NP2 (mediana de 3 medianas por brazo, spot ES
       POR CORRIDA, fallback --kv-unified off #25345) + RECETA FINAL con
       confirmacion, backup y re-lectura + el CIERRE DE CAMPAÑA (los 5
       niveles, escrito en el informe).

FAMILIA (regla del Director, r50: "crear otro, NO borrar el antiguo"):
  CAMPANA.py v1.7.2 (65D33CBA...DA4B1) y CAMPANA-v2.py v2.0 (52996E67...)
  cocinan los pasos 1..6; CAMPANA-6A10.py v1.0 (CFEADBEA...D1947) es la
  olla original de la que nacio este archivo (antes CAMPANA-6A10-v2.py,
  renombrado r67). Este archivo es su HERMANO:
  - NO borra, NO pisa y NO re-escribe NINGUNA de las tres ollas mayores:
    las tres quedan BYTE-INTACTAS y este archivo nace aparte.
  - MUNDO PROPIO NUEVO (r67, orden del Director "si ahora es n4
    cambiale el titulo, no mezcles cosas": ya NO comparte mundo con
    CAMPANA-6A10.py, que queda byte-intacta con el SUYO, virgen -
    nunca corrio): campana-n4-n5-estado.json + campana-n4-n5-INFORME.md
    append-only + carpetas campana-n4-n5-p7../p10 + puerto propio
    9932. Cada seccion del informe que escribe esta olla lleva la
    linea "- script: CAMPANA-N4-N5.py" (evidencia clara de quien
    escribio que).

DELTAS DOCUMENTADOS frente a CAMPANA-6A10.py byte-intacta (SOLO estos
tres; todo lo demas es conducta identica, verificada funcion por
funcion contra el boceto auditado y el codigo fuente):
  D1. La escalera de P8 DERIVADA ya nace CORREGIDA segun el plan R61
      (seccion 5) y las trampas T1/T2/T3 del boceto: peldanos NCM
      primero y activos, NGL-87/93 INACTIVAS al final y aparte, la flag
      MEC con su nombre REAL del dump (--moe-cache-mib; el placeholder
      --cmoe-cache NO existe), pilas de la segunda vuelta combinadas
      con ';' en UNA fila y SIN peldano de pagina mlock (prohibido sin
      headroom demostrado, plan R3: la variante RAM es WIN+DIO, solo si
      R0 detecta pageouts). La olla original deriva la tabla vieja y
      confia en la edicion manual del Director; esta nace lista.
  D2. Impresiones honestas: P9 anuncia "mediana de N corridas x M
      prompts" (la olla original decia "1 corrida" y corria MED3:
      cosmético F11 de la auditoria r63; la CONDUCTA MED3 es identica),
      al generar las tablas se muestran los avisos de la derivacion y el
      informe de P8 anota el HUECO para P10 como dato (4096 - VRAM del
      ganador; criterio de salida del PASO 8, plan R61).
  D3. Las secciones del informe llevan la linea "- script:" (ver
      arriba). Nada mas.

REGLAS que el script hace cumplir (las de la casa; las trampas T1-T18
del boceto §7 viven incrustadas donde corresponden):
  - PUERTAS: p8 exige p7 verde; p9 exige p8; p10 exige p9. --fuerza las
    salta A PROPOSITO y lo deja escrito en el informe. En MODO AUTO no
    existe fuerza: una puerta roja DETIENE el turno limpio (rc 2). [T9]
  - config.txt: SOLO el cierre de P10 escribe en el (receta final, con
    confirmacion, backup con marca de tiempo, escritura atomica tmp +
    os.replace y re-lectura de verificacion). Ningun otro paso lo toca.
    [T8] SAMPLING, RUTA_* y el cuant NUNCA se tocan (RUTA_MODELO manda).
  - el informe (campana-n4-n5-INFORME.md) es APPEND-ONLY: cada accion
    anade una seccion con fecha; nada se borra ni re-escribe.
  - MEDICION [T15/T16/T17]: calentamiento descartado al arrancar cada
    server (la GPU fria miente ~-15%, T6); sampling del medidor FIJO
    (temp 1.0, top_k 20, top_p 0.95, max_tokens 220: jamas cambiarlo
    entre dosis, es lo que hace comparables las corridas); t/s del
    propio server (timings); mediana por corrida y MEDIANA DE MEDIANAS
    por dosis (la mecanica de TODA la olla, F13); UNA dosis por
    corrida; reintento (1, con 3 s de espera) SOLO red/timeout/5xx, un
    4xx no se repite.
  - HORNILLA [T18]: puerto 9932 propio (la primera olla usa 9931);
    nunca levanta ni apaga servers ajenos: solo los hijos que ella
    misma arranca; logs de server en APPEND (acumulan sesiones con
    cabecera); health poll cada 2 s con tope de 7 min; un peldano
    muerto es DATO (viva=False), no un accidente.
  - ESCALERA [T1/T2/T3/T4/T5/T12/T13]: orden de archivo manda, peldanos
    NO acumulativos (pilas con ';'), sub pisa TODAS las apariciones,
    -ot en comma-list en UN solo flag, fila con <3 celdas se ignora,
    nvidia-smi es certificado BLANDO (avisa, nunca frena: lo que frena
    es el cliff), regla cliff-1 (t/s < 70% del ancla o muertos > 0).
  - stdlib-ONLY: cero dependencias nuevas, cero red salvo el localhost
    del propio server. Sin maleta: este archivo viaja SOLO.
  - HUELLA: auto-verificacion de huella propia al arranque (tamper ->
    parada limpia, rc 3), herencia del guardian de la casa. [tabla de
    rc del boceto §1: 0 verde, 2 puerta/fatal/dudoso/falla, 1
    excepcion, 130 Ctrl+C, 3 huella manipulada]
  - DOBLE CLICK = MODO AUTO: corre P7..P10 en orden, sin preguntas;
    las confirmaciones se auto-aceptan y quedan escritas; re-doble-
    click retoma donde quedo. --ofrecer no existe aqui: foto con
    `estado`. [T9: en AUTO --fuerza se ignora con aviso]

Todo vive junto al script (en el rig: D:\\ZLia). --dir cambia la base
y --config la receta. Cero toques a CAMPANA.py, CAMPANA-v2.py,
CAMPANA-6A10.py, config.txt (salvo el cierre confirmado de P10) ni a la
evidencia de la primera olla. Si este archivo y la olla byte-intacta se
pelearan en el futuro, manda el byte-intacto (boceto §0).
"""
import argparse
import csv
import datetime
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request


# ---------------- paleta de la casa (ANSI, sin companeros) -------------------

def _usa_color():
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


TTY = _usa_color()


def _c(codigo, s):
    return "\033[%sm%s\033[0m" % (codigo, s) if TTY else s


def bold(s):
    return _c("1", s)


def red(s):
    return _c("31", s)


def green(s):
    return _c("32", s)


def yellow(s):
    return _c("33", s)


def cyan(s):
    return _c("36", s)


def gray(s):
    return _c("90", s)


# ---------------- utilidades de la casa --------------------------------------

def health_ok(puerto, timeout=3):
    """True si hay un server vivo atendiendo /health en el puerto."""
    try:
        with urllib.request.urlopen(
                "http://127.0.0.1:%d/health" % puerto, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def sha256_archivo(ruta, bloque=1024 * 1024):
    """SHA256 streaming (los 13 GB no se cargan a memoria)."""
    import hashlib
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while True:
            chunk = f.read(bloque)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def mediana(xs):
    """Semantica exacta (F16/T17): filtra no-numericos; 3 -> central;
    2 vivas -> promedio de ambas; 0 -> None (sin datos)."""
    xs = [x for x in xs if isinstance(x, (int, float))]
    return statistics.median(xs) if xs else None


def sin_tildes(s):
    """Valparaiso == Valparaíso a la hora de juzgar anclas de calidad."""
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn")


def gb_libres(ruta):
    try:
        u = shutil.disk_usage(ruta)
        return u.free / (1024.0 ** 3), u.total / (1024.0 ** 3)
    except Exception:
        return None, None


# ================= §0 CONSTANTES DE LA CASA (boceto §0) ======================
# leidas del codigo de la casa, no de memoria; los comentarios son las
# reglas que evitan bugs (boceto: "los comentarios # son las reglas").

AQUI = os.path.dirname(os.path.abspath(__file__))

VERSION = ("campana-n4-n5 v1.0 LA VIA ACTIVA N4 -> N5 REAL DESDE EL "
           "BOCETO (2026-10-31, ronda 65: pedido del Director 'crea el "
           "archivo python puro real, siguiendo la guia del "
           "pseudocodigo'; ronda 67: renombrada CAMPANA-6A10-v2.py -> "
           "CAMPANA-N4-N5.py por orden del Director 'si ahora es n4 "
           "cambiale el titulo, no mezcles cosas' — "
           "transcripcion ejecutable del boceto r62 auditado r63/r64; "
           "conducta identica a CAMPANA-6A10.py byte-intacta salvo los "
           "deltas D1/D2/D3 documentados en la cabecera; CAMPANA.py "
           "v1.7.2, CAMPANA-v2.py v2.0 y CAMPANA-6A10.py v1.0 quedan "
           "BYTE-INTACTAS)")

PUERTO_DEF = 9932          # hornilla propia (la primera olla usa 9931)
CORRIDAS_DEF = 3           # mediana de 3 corridas antes de proclamar (regla)
M_PROMPTS_DEF = 8          # prompts de medida por corrida (fijos; --m-prompts
                           #   corta los PRIMEROS N de la lista, no mezcla: F22)
MAX_TOKENS = 220           # mismo corte que el sanity de la casa
TEMP_MEDIDOR = 1.0         # sampling FIJO del medidor (F17/T15): IGUAL para
TOP_K_MEDIDOR = 20         #   todas las dosis -> es lo que hace comparables
TOP_P_MEDIDOR = 0.95       #   las corridas; jamas cambiarlo entre dosis
TIMEOUT_PROMPT = 180       # por prompt (1 reintento de 3 s SOLO red/timeout/5xx: T16)
TIMEOUT_CARGA = 420        # carga del modelo (7 min, igual que la casa)
KEEP_MIN_PP = 5.0          # no perseguir deltas < 5 pp (regla transversal)
N2_META_PP = 8.0           # criterio de salida del N2 (>= +8% [N2 s5])
CLIFF_FRACCION = 0.70      # t/s por debajo del 70% del ancla = CLIFF
VRAM_CERTIFICADO_MB = 3712  # certificado de la casa: nvidia-smi <= 3.7 GB
                           #   (BLANDO: avisa, nunca frena — T13)

# estados verdes/amarillos PROPIOS de esta olla (boceto §0)
VERDES = ("GO", "REGISTRADO", "OK", "CERRADO", "RATIFICADA", "EJECUTADO",
          "MOTIVO-CERRADO", "DUELO-HECHO")
AMARILLOS = ("PENDIENTE", "DUDOSO", "REVISAR", "INCOMPLETO")
ROJOS = ("FALLA", "MUERTO", "FALLO-CERTIFICADO")

# verdes que la PRIMERA olla escribe en campana-estado.json (los suyos)
VERDES_OLLA1 = ("GO", "PROMOVIDA", "YA-PROMOVIDA", "OK", "DESCARGADA",
                "VERIFICADO-HUMO-OK", "EJECUTADO", "REGISTRADO")

# confirmacion de huella: el builder incrusta el SHA en esta linea
SHA_AUTOCHEQUEO = "F6BD479DCBA1CAA1A3A80000D392A93EC80C59191A1BB02E3D89F7E56053D041"

# MODO AUTO: cuando esta activo, las confirmaciones se auto-aceptan y
# quedan escritas. NUNCA activa --fuerza: puerta roja = turno detenido.
AUTO = {"on": False, "aceptadas": []}


# ---------------- los prompts de esta mitad de la campana --------------------
# MEDIDA (8): fijos y deterministas, mezcla ES/codigo/tool/memoria. El t/s
# lo reporta el PROPIO server (timings), igual que el sanity de la casa.

PROMPTS_MEDIDA = [
    ("redaccion", "Escribe un parrafo corto (3 frases) sobre el mar de Chile."),
    ("codigo", "Escribe una funcion Python que imprima FizzBuzz del 1 al 15. Solo codigo."),
    ("matematica", "Cuantos minutos hay en 3 horas y 25 minutos? Responde solo el numero."),
    ("tool-clima", "Tienes la herramienta get_weather(ciudad). Muestra solo la llamada "
                   "JSON para consultar el clima de Santiago."),
    ("explica", "Explica en dos frases que es la VRAM de una tarjeta de video, como para un nino."),
    ("memoria", "Mi plaza favorita es la de Concepcion. En que ciudad dije que esta mi plaza favorita?"),
    ("traduccion", "Traduce al ingles: 'La olla hierve a fuego lento.'"),
    ("lista", "Dame 3 consejos para que un pan suba bien, en lista con vinetas, uno por linea."),
]

# SPOT (5): el spot-check ES por config (anclas deterministas + tool + trampa).
# En P10 corre POR CORRIDA (F7): el brazo queda elegible solo con spot
# limpio en TODAS sus corridas.

PROMPTS_SPOT = [
    ("ancla-aritmetica", "Cuanto es 17 * 23? Responde solo el numero."),          # 391
    ("ancla-memoria", "Mi color favorito es el verde. De que color te dije "
                      "que era mi favorito?"),                                    # verde
    ("ancla-seguimiento", "Me llamo Ana y trabajo en Valparaiso. En que ciudad "
                          "dije que trabajo?"),                                   # Valparaiso
    ("tool-buscar", "Tienes la herramienta buscar_productos(termino, max). Muestra "
                    "la llamada JSON para buscar 'teclado mecanico' con maximo 5."),
    ("trampa", "Quien gano la final del mundial de futbol de 2030? Si no lo sabes, "
               "di que no lo sabes."),
]

# SANITY de P7 (12): en CAMBIO DE CUANT el sanity con tool-calling es
# OBLIGATORIO (regla transversal) y tool-calling es la categoria que peor
# cuantiza [F]: doble motivo. Las 3 anclas van SIEMPRE dentro.

PROMPTS_SANITY_P7 = [
    ("ancla-aritmetica", "Cuanto es 17 * 23? Responde solo el numero."),
    ("ancla-memoria", "Mi color favorito es el verde. De que color te dije que era mi favorito?"),
    ("ancla-seguimiento", "Me llamo Ana y trabajo en Valparaiso. En que ciudad dije que trabajo?"),
    ("tool-clima", "Tienes la herramienta get_weather(ciudad). Usandola en formato JSON, "
                   "como consultarias el clima de Santiago? Muestra solo la llamada."),
    ("tool-buscar", "Tienes la herramienta buscar_productos(termino, max). Muestra la "
                    "llamada JSON para buscar 'teclado mecanico' con maximo 5 resultados."),
    ("tool-parse", "Convierte este texto a JSON con las claves nombre y edad: 'Maria, 34 anos'. "
                   "Devuelve solo el JSON."),
    ("tool-multi", "Tienes get_stock(ticker) y get_news(ticker). Escribe las DOS llamadas JSON "
                   "para consultar AAPL."),
    ("codigo-json", "Escribe una funcion Python que reciba un dict y devuelva un JSON string "
                    "ordenado por clave. Solo codigo."),
    ("trampa", "Quien gano la final del mundial de futbol de 2030? Si no lo sabes, di que no lo sabes."),
    ("dominio", "Para que sirve la flag -ngl 99 en llama.cpp? Una frase."),
    ("clasificacion", "Clasifica el sentimiento como positivo/negativo/neutral: "
                      "'El servicio fue lento pero la comida estaba excelente.'"),
    ("formato-lista", "Dame 3 consejos para dormir mejor, en lista con vinetas, uno por linea."),
]


def _anclas_chequeo(respuestas):
    """(ok, motivos): las 3 anclas deterministas de calidad (391, verde,
    Valparaiso) + todo con carne. Igual de estricto que el AUTO de la casa."""
    motivos = []
    por_nombre = dict(respuestas)
    if any(not (r or "").strip() for _, r in respuestas):
        motivos.append("hay respuestas vacias (sin carne)")
    a1 = sin_tildes(por_nombre.get("ancla-aritmetica", "") or "").lower()
    if "391" not in a1:
        motivos.append("ancla aritmetica: 17*23 no dio 391")
    a2 = sin_tildes(por_nombre.get("ancla-memoria", "") or "").lower()
    if "verde" not in a2:
        motivos.append("ancla memoria: no recordo el color verde")
    a3 = sin_tildes(por_nombre.get("ancla-seguimiento", "") or "").lower()
    if "valparaiso" not in a3:
        motivos.append("ancla seguimiento: no recordo Valparaiso")
    return (not motivos), motivos


# ============ §1 EL CICLO DE LA RONDA: memoria, rutas, informe ===============

def _rutas(args):
    base = os.path.abspath(args.dir) if args.dir else AQUI
    config = args.config or os.path.join(base, "config.txt")
    if not args.config and not os.path.exists(config):
        _cfg_repo = os.path.abspath(os.path.join(base, "..", "configs",
                                                 "config.txt"))
        if os.path.exists(_cfg_repo):
            config = _cfg_repo
    return {
        "base": base,
        "estado": os.path.join(base, "campana-n4-n5-estado.json"),
        "informe": os.path.join(base, "campana-n4-n5-INFORME.md"),
        "config": config,
        "models": os.path.join(base, "models"),
        "olla1": os.path.join(base, "campana-estado.json"),
    }


def leer_estado(ruta_estado):
    if os.path.exists(ruta_estado):
        try:
            with open(ruta_estado, encoding="utf-8") as f:
                datos = json.load(f)
            if isinstance(datos, dict):
                datos.setdefault("pasos", {})
                datos.setdefault("duelo", {})
                if not isinstance(datos["pasos"], dict):
                    datos["pasos"] = {}
                if not isinstance(datos["duelo"], dict):
                    datos["duelo"] = {}
                return datos
        except Exception:
            # un estado corrupto NO se descarta en silencio (herencia r50,
            # F10): queda .corrupto-<ts> como evidencia y arranca limpio.
            try:
                _podrido = "%s.corrupto-%s" % (
                    ruta_estado,
                    datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
                os.replace(ruta_estado, _podrido)
                print(yellow("  aviso: campana-n4-n5-estado.json ilegible; "
                             "evidencia guardada en %s" % os.path.basename(_podrido)))
            except Exception:
                pass
    return {"version": VERSION, "actualizado": "", "pasos": {}, "duelo": {}}


def guardar_estado(ruta_estado, estado):
    estado["version"] = VERSION
    estado["actualizado"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tmp = ruta_estado + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ruta_estado)
    except BaseException:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise


def informe(ruta_informe, titulo, lineas):
    """APPEND-ONLY: cada accion anade su seccion; nunca se re-escribe."""
    sello = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ruta_informe, "a", encoding="utf-8") as f:
        f.write("\n\n## %s — %s\n\n" % (sello, titulo))
        for ln in lineas:
            f.write("%s\n" % ln)
        f.flush()
    return ruta_informe


def _inf(rutas, titulo, lineas):
    """informe() de esta olla (delta D3): anade la linea de identidad del
    script, para que el informe append-only sepa quien escribio cada
    seccion."""
    return informe(rutas["informe"], titulo,
                   ["- script: CAMPANA-N4-N5.py v1.0 (real desde el "
                    "boceto, r65; renombre r67)"] + list(lineas))


def fatal(msg, pistas=()):
    """Puerta roja / freno con causa escrita. SIEMPRE sale rc=2 (tabla de
    rc del boceto §1)."""
    print(red("\n[FATAL] %s" % msg))
    for p in pistas:
        print(yellow("  pista: %s" % p))
    sys.exit(2)


def confirmar(palabra, pregunta):
    if AUTO["on"]:
        print(yellow("\n%s" % pregunta))
        print(cyan("  [AUTO] aceptado automaticamente (la aceptacion queda "
                   "escrita en el informe)."))
        AUTO["aceptadas"].append("%s — %s" % (palabra, pregunta))
        return True
    print(yellow("\n%s" % pregunta))
    try:
        resp = input(yellow("  escribe %s para confirmar (otra cosa cancela): "
                            % bold(palabra)))
    except EOFError:
        resp = ""
    if resp.strip().upper() != palabra:
        print(gray("  cancelado (no se toco nada)."))
        return False
    return True


def _pausa_doble_click(es_tty=None):
    """Doble click en Windows: la consola se cierra sola. Si el script se
    arranco SIN argumentos se espera un Enter antes de cerrar; con
    argumentos (uso real desde consola) no molesta."""
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


# ---------------- receta y cirugia de flags (T14) ----------------------------

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


def _quita_modelo(tokens):
    """Quita -m/--model <ruta> de la receta: el modelo lo pone SIEMPRE esta
    olla con RUTA_MODELO al final (un -m colado cargaria otro cuant)."""
    res, i = [], 0
    while i < len(tokens):
        if tokens[i] in ("-m", "--model"):
            i += 2
        else:
            res.append(tokens[i])
            i += 1
    return res


def _tokens_de_receta(cfg):
    """FLAGS_BASE + FLAGS_GANADORAS en tokens, SIN -m (el modelo va aparte).
    Espejo del lanzamiento de la casa (el ultimo valor gana: -ub 1024 -b
    4096 de FLAGS_GANADORAS pisan el -b 2048 -ub 256 de FLAGS_BASE)."""
    brutas = (cfg.get("FLAGS_BASE", "") + " " +
              cfg.get("FLAGS_GANADORAS", "")).split()
    return _quita_modelo(brutas)


def _acciona(tokens, acciones):
    """Cirugia de flags POR TOKENS (semantica exacta, T14):
      add:tok1,tok2   anade tokens al final (el ultimo valor gana)
      del:tok         borra TODAS las apariciones del token
      delpair:flag    borra flag + su valor (si el que sigue no es una flag)
      sub:viejo>nuevo sustituye TODAS las apariciones de un token por otro
    Varias acciones se separan con ';' (T3: las pilas van combinadas en
    UNA fila). Desconocido: se ignora (y queda en el informe como accion
    no entendida)."""
    out = list(tokens)
    if not acciones or not acciones.strip():
        return out
    for acc in acciones.split(";"):
        acc = acc.strip()
        if not acc or ":" not in acc:
            continue
        verbo, _, cuerpo = acc.partition(":")
        verbo = verbo.strip().lower()
        cuerpo = cuerpo.strip()
        if verbo == "add":
            out.extend(t for t in cuerpo.split(",") if t)
        elif verbo == "del":
            out = [t for t in out if t != cuerpo]
        elif verbo == "delpair":
            res, i = [], 0
            while i < len(out):
                if out[i] == cuerpo:
                    if i + 1 < len(out) and not out[i + 1].startswith("-"):
                        i += 2
                    else:
                        i += 1
                else:
                    res.append(out[i])
                    i += 1
            out = res
        elif verbo == "sub":
            viejo, _, nuevo = cuerpo.partition(">")
            if viejo:
                out = [nuevo if t == viejo else t for t in out]
    return out


# ---------------- tablas candidatas / escalera (el instrumento fino) ---------

def _leer_tabla(ruta):
    """Formato (separado por ' | '):  nombre | acciones | activa|inactiva | nota
    Lineas vacias y # se ignoran. Una fila con <3 celdas se IGNORA EN
    SILENCIO (T12: ¡peldano que creias activo y no corre!) — ninguna celda
    puede llevar '|'. activa/inactiva se lee por PREFIJO 'activa'.
    Devuelve lista de dicts."""
    filas = []
    with open(ruta, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            partes = [p.strip() for p in ln.split("|")]
            if len(partes) < 3 or not partes[0]:
                continue
            filas.append({
                "nombre": partes[0],
                "acciones": partes[1],
                "activa": partes[2].lower().startswith("activa"),
                "nota": partes[3].strip() if len(partes) > 3 else "",
            })
    return filas


def _escribe_tabla(ruta, lineas):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    return ruta


# ---------------- la puerta de entrada: la primera olla cerrada --------------

def _primera_olla(rutas):
    """(cerrada, detalles): lee campana-estado.json de la PRIMERA olla en la
    misma base. Formula EXACTA (F3): cerrada = (n3.cerrado is True O
    pasos["3"] verde_olla1) **Y** pasos["6"] verde_olla1."""
    det = []
    if not os.path.exists(rutas["olla1"]):
        return False, ["no encuentro campana-estado.json en %s (la primera "
                       "olla aun no corre en esta base)" % rutas["base"]]
    try:
        with open(rutas["olla1"], encoding="utf-8") as f:
            datos = json.load(f)
    except Exception as exc:
        return False, ["campana-estado.json ilegible: %r" % (exc,)]
    pasos1 = datos.get("pasos") if isinstance(datos.get("pasos"), dict) else {}
    n3 = datos.get("n3") if isinstance(datos.get("n3"), dict) else {}
    n3_ok = n3.get("cerrado") is True or pasos1.get("3", {}).get("estado") in VERDES_OLLA1
    p6_ok = pasos1.get("6", {}).get("estado") in VERDES_OLLA1
    det.append("N3 de la primera olla: %s" % ("CERRADO" if n3_ok else "ABIERTO"))
    det.append("P6 (N1 formal) de la primera olla: %s"
               % (pasos1.get("6", {}).get("estado") or "SIN P6"))
    return (n3_ok and p6_ok), det


def _color_estado(est):
    est = est or "PENDIENTE"
    if est in VERDES:
        return green(est)
    if est in ROJOS:
        return red(est)
    if est in AMARILLOS:
        return yellow(est)
    return yellow(est)


def mostrar_estado(rutas, estado):
    print(bold(cyan("\n=== CAMPANA-N4-N5 (la via activa N4 -> N5, real "
                    "desde el boceto) — %s ==="
                    % (estado.get("actualizado") or "sin empezar"))))
    print("  informe append-only: %s" % rutas["informe"])
    cerrada, det = _primera_olla(rutas)
    print("  puerta de entrada — primera olla: %s"
          % (green("CERRADA (se puede cocinar)") if cerrada
             else red("AUN ABIERTA (corre primero CAMPANA.py del 1 al 6)")))
    for d in det:
        print("    %s" % gray("- " + d))
    tabla = [("7", "N2 dosis re-aplicadas + sanity tool-calling"),
             ("8", "N4 escalera de VRAM (cliff-1)"),
             ("9", "RUTA 0: build b11901 + defaults + reuse"),
             ("10", "N5 duelo spec vs NP2 + receta final + cierre")]
    for n, titulo in tabla:
        paso = estado["pasos"].get(n, {})
        print("  P%-2s %-8s %s" % (n, _color_estado(paso.get("estado")),
                                   titulo))
        detalle = paso.get("resumen") or paso.get("nota")
        if detalle:
            print("        %s" % gray(str(detalle)[:110]))
    return 0


def _puerta(args, paso_hijo, previo, nombre_previo, verdes, frases):
    """La puerta roja del ciclo (T9): el paso exige el paso previo VERDE.
    --fuerza salta A PROPOSITO y queda escrito; en AUTO no existe (se
    ignora). Una puerta roja detiene el turno con causa escrita: nunca se
    salta sola."""
    est = previo.get("estado")
    if est in verdes:
        print(green("  puerta: %s verde (%s). %s" % (nombre_previo, est,
                                                     frases[0])))
        return
    if args.fuerza:
        print(yellow("  PUERTA SALTADA A PROPOSITO (--fuerza): %s = %s"
                     % (nombre_previo, est or "SIN %s" % nombre_previo)))
        return
    fatal("%s exige %s verde (estado actual: %s)"
          % (paso_hijo, nombre_previo, est or "SIN %s" % nombre_previo),
          ["corre p%s primero" % nombre_previo[1:].lower(),
           "--fuerza salta la puerta a proposito"])


# ---------------- la hornilla: server propio, medida y certificados ----------
# [T18] NUNCA levanta ni apaga servers ajenos: solo los hijos que esta
# olla arranca (el charlatan diario se respeta). Los logs de server van
# en APPEND (acumulan sesiones con cabecera).

def _vram_usada_mb():
    """MB de VRAM en uso (GPU 0) via nvidia-smi. Si la herramienta no esta,
    devuelve None: es un certificado BLANDO (T13), nunca un freno."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15)
        if out.returncode == 0 and out.stdout.strip():
            return int(float(out.stdout.strip().splitlines()[0]))
    except Exception:
        pass
    return None


def _cuenta_en_log(ruta_log, palabra):
    """Cuantas lineas del log del server contienen la palabra (minusculas)."""
    try:
        with open(ruta_log, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for ln in f if palabra.lower() in ln.lower())
    except Exception:
        return None


def _auto_apaga(proc):
    """Apaga SOLO el hijo que esta olla lanzo (nunca un server ajeno)."""
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _arranca_server(cmd, log_path, puerto, timeout_s=TIMEOUT_CARGA):
    """Arranca UN server propio y espera al health (poll cada 2 s, tope 7
    min, F21). Si muere en la carga devuelve (None, rc) — en un barrido un
    peldano muerto es DATO (cliff), no un accidente. (proc, None) si vivo."""
    flog = open(log_path, "a", encoding="utf-8")
    flog.write("===== server de campana-n4-n5 %s (puerto %d) =====\n"
               % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), puerto))
    flog.write("$ %s\n" % " ".join(cmd))
    flog.flush()
    try:
        proc = subprocess.Popen(cmd, stdout=flog, stderr=subprocess.STDOUT)
    finally:
        flog.close()
    fin = time.time() + timeout_s
    while time.time() < fin:
        if proc.poll() is not None:
            return None, proc.returncode
        if health_ok(puerto):
            return proc, None
        time.sleep(2)
    _auto_apaga(proc)
    return None, "sin health en %d min" % (timeout_s // 60)


def _chat_uno(puerto, texto, timeout=TIMEOUT_PROMPT, reintentos=1):
    """UN prompt -> (contenido, tps). UN reintento (3 s) SOLO para
    tropiezos de red/timeout/5xx (herencia r50); un 4xx no se repite
    (T16). El sampling es el FIJO del medidor (T15)."""
    cuerpo = json.dumps({
        "messages": [{"role": "user", "content": texto}],
        "max_tokens": MAX_TOKENS, "temperature": TEMP_MEDIDOR,
        "top_k": TOP_K_MEDIDOR, "top_p": TOP_P_MEDIDOR,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d/v1/chat/completions" % puerto, data=cuerpo,
        headers={"Content-Type": "application/json"})
    js = None
    for _intento in range(1 + max(0, reintentos)):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                js = json.loads(r.read().decode("utf-8", errors="replace"))
            break
        except urllib.error.HTTPError as _e:
            if _e.code < 500 or _intento >= reintentos:
                raise
        except (urllib.error.URLError, OSError):
            if _intento >= reintentos:
                raise
        time.sleep(3)
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


def _corrida(args, rutas, etiqueta, k, acciones, carpeta, con_spot=False):
    """UNA corrida del barrido propio: server PROPIO con la receta diaria +
    cirugia de la dosis, calentamiento descartado (T6: la GPU fria miente
    ~-15%), M prompts de medida (t/s del propio server), spot opcional
    (POR CORRIDA, F7), apagada limpia. Devuelve dict de datos; un peldano
    muerto es DATO (viva=False). Si config/modelo/paths estan rotos, FATAL
    nominado ANTES de arrancar."""
    cfg = leer_config(rutas["config"])
    servidor = cfg.get("RUTA_SERVER", "")
    modelo = cfg.get("RUTA_MODELO", "")
    if not servidor or not os.path.exists(servidor):
        fatal("RUTA_SERVER no valido: %r" % servidor,
              ["revisa RUTA_SERVER en config.txt"])
    if not modelo or not os.path.exists(modelo):
        fatal("RUTA_MODELO no valido: %r" % modelo,
              ["revisa RUTA_MODELO en config.txt (el cuant que manda HOY)"])
    tokens = _acciona(_tokens_de_receta(cfg), acciones)
    cmd = [servidor] + tokens + ["-m", modelo,
                                 "--host", "127.0.0.1", "--port", str(args.puerto)]
    os.makedirs(carpeta, exist_ok=True)
    log_srv = os.path.join(carpeta, "server-%s-c%d.log" % (etiqueta, k))
    print(gray("  $ %s" % " ".join(cmd)))
    proc, rc = _arranca_server(cmd, log_srv, args.puerto)
    datos = {"etiqueta": etiqueta, "corrida": k, "viva": proc is not None,
             "rc": rc, "mediana": None, "tps": [], "errores": 0,
             "vram_mb": None, "pageouts": None, "spot_ok": None,
             "spot_resumen": "", "log": log_srv, "acciones": acciones or ""}
    if proc is None:
        print(red("  el server NO levanto con esta dosis (rc=%s): peldano "
                  "muerto, queda como dato." % rc))
        return datos
    try:
        try:
            _chat_uno(args.puerto, "Calienta la plancha: responde 'lista'.",
                      timeout=300)
        except Exception:
            pass  # el calentamiento se descarta SIEMPRE (ancla por sesion, T6)
        tps, errores = [], 0
        for nombre, texto in PROMPTS_MEDIDA[:max(1, args.m_prompts)]:
            try:
                _, t = _chat_uno(args.puerto, texto)
            except Exception:
                t, errores = None, errores + 1
            if t:
                tps.append(t)
            print(gray("    c%d %-16s %s" % (k, nombre,
                                             "%.1f t/s" % t if t else "error")))
        datos["tps"] = tps
        datos["errores"] = errores
        datos["mediana"] = mediana(tps)   # corrida = mediana de sus prompts (F13)
        if con_spot:
            respuestas = []
            for nombre, texto in PROMPTS_SPOT:
                try:
                    contenido, _ = _chat_uno(args.puerto, texto)
                except Exception as exc:
                    contenido = "[ERROR HTTP] %r" % (exc,)
                respuestas.append((nombre, contenido))
                primera = (contenido.strip().splitlines() or ["(vacia)"])[0][:60]
                print(gray("    spot %-18s %s" % (nombre, primera)))
            ok, motivos = _anclas_chequeo(respuestas)
            datos["spot_ok"] = ok
            datos["spot_resumen"] = "; ".join(motivos) if motivos else \
                "anclas OK (391/verde/Valparaiso)"
        datos["vram_mb"] = _vram_usada_mb()
        datos["pageouts"] = _cuenta_en_log(log_srv, "pageout")
    finally:
        _auto_apaga(proc)
    return datos


def _fila_csv(datos):
    return [
        datos["etiqueta"], datos["corrida"], datos["viva"],
        ("%.2f" % datos["mediana"]) if datos["mediana"] else "",
        datos["errores"],
        datos["vram_mb"] if datos["vram_mb"] is not None else "",
        datos["pageouts"] if datos["pageouts"] is not None else "",
        "" if datos["spot_ok"] is None else datos["spot_ok"],
        datos["acciones"],
    ]


CSV_COLS = ["dosis", "corrida", "viva", "mediana_tps", "errores",
            "vram_mb", "pageouts", "spot_ok", "acciones"]


def _guarda_csv(carpeta, nombre, datos):
    """Una fila por corrida; el CSV nunca se pisa: se suma (evidencia)."""
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    nuevo = not os.path.exists(ruta)
    with open(ruta, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(CSV_COLS)
        w.writerow(_fila_csv(datos))
    return ruta


def _lanza_corridas(args, rutas, etiqueta, acciones, carpeta, con_spot=False):
    """Mediana de CORRIDAS corridas para una dosis (regla de la casa: una
    corrida no prueba nada). La mecanica de TODA la olla (F13): cada
    corrida = mediana de los t/s de sus prompts; la dosis = mediana de
    las medianas de corrida. Devuelve (medianas, datos_por_corrida)."""
    ms, por_corrida = [], []
    for k in range(1, max(1, args.corridas) + 1):
        print(cyan("  [%s] corrida %d/%d..." % (etiqueta, k, args.corridas)))
        d = _corrida(args, rutas, etiqueta, k, acciones, carpeta, con_spot)
        _guarda_csv(carpeta, "resultados.csv", d)
        por_corrida.append(d)
        if d["viva"] and d["mediana"]:
            ms.append(d["mediana"])
    return ms, por_corrida


# ============ §2 P7 — N2 DOSIS (re-ancla + candidatas + sanity) ==============

ARCHIVO_P7 = "campana-n4-n5-p7-candidatas.txt"


def _deriva_candidatas(cfg):
    """Deriva candidatas de la RECETA REAL (regla de la casa: el instrumento
    fino se genera cuando se llega, con lo que hay en config.txt, sin
    inventar flags). DOS ramas (F9): receta SIN pin de k -> PIN desde
    EXPERTOS_TRABAJO ACTIVO + vecinos 7/9 inactivos; receta CON pin ->
    re-aplica el pin ACTIVO + solo el vecino pin-1 inactivo.
    Devuelve (lineas_para_el_archivo, avisos)."""
    tokens = _tokens_de_receta(cfg)
    lineas = [
        "# CANDIDATAS P7 — N2 dosis sobre el cuant vigente (el vestidor).",
        "# Formato por linea:  nombre | acciones | activa|inactiva | nota",
        "#   acciones: add:tok,tok ; del:tok ; delpair:flag ; sub:viejo>nuevo",
        "# Una dosis por corrida. La ANCLA (receta tal cual) SIEMPRE corre",
        "# primero y no se edita. Criterio: delta >= +5 pp se considera real;",
        "# >= +8 pp con sanity OK cierra el N2 (>= +8% t/s [N2 s5]).",
        "# Edita libremente y vuelve a correr p7 (lo ya medido se suma al CSV).",
        "ANCLA | | ancla | la receta diaria tal cual (re-ancla del cuant)",
    ]
    avisos = []
    # --- la escalera k de N1 (transfiere: es arquitectura) ---
    pin = None
    for i, t in enumerate(tokens):
        if t == "--override-kv" and i + 1 < len(tokens) and \
                "expert_used_count=" in tokens[i + 1]:
            try:
                pin = int(tokens[i + 1].split("=", 1)[1])
            except Exception:
                pin = None
    if pin is None:
        # la receta no fija k: el cuant nuevo vino de fabrica con el suyo.
        # Se PINA el k de trabajo de la casa (config EXPERTOS_TRABAJO) para
        # que el cuant nuevo juegue con las MISMAS reglas que el viejo.
        try:
            pin = int(cfg.get("EXPERTOS_TRABAJO", "") or 8)
        except Exception:
            pin = 8
        lineas.append(
            "K-N1-PIN%d | add:--override-kv,qwen35moe.expert_used_count=%d | activa | "
            "pina el k de trabajo de la casa sobre el cuant nuevo"
            % (pin, pin))
        lineas.append(
            "K-N1-%d | add:--override-kv,qwen35moe.expert_used_count=%d | inactiva | "
            "vecino de la escalera k (activa si quieres la escalera completa)"
            % (pin - 1, pin - 1))
        lineas.append(
            "K-N1-%d | add:--override-kv,qwen35moe.expert_used_count=%d | inactiva | "
            "vecino de la escalera k" % (pin + 1, pin + 1))
        avisos.append("la receta NO pina expert_used_count: se derivo la "
                      "candidata K-N1-PIN%d desde EXPERTOS_TRABAJO" % pin)
    else:
        lineas.append(
            "K-N1-%d | add:--override-kv,qwen35moe.expert_used_count=%d | activa | "
            "re-aplica el pin de k de la receta (transfiere: arquitectura)" % (pin, pin))
        lineas.append(
            "K-N1-%d | add:--override-kv,qwen35moe.expert_used_count=%d | inactiva | "
            "vecino de la escalera k" % (pin - 1, pin - 1))
    # --- UB1K (leccion R32: UB1K x NCM = -16.5%: solo donde no estorbe) ---
    if "-ub" in tokens:
        lineas.append(
            "SIN-UB1K | delpair:-ub;delpair:-b | inactiva | vuelve a -ub/-b de "
            "FLAGS_BASE (activa si el cuant nuevo se porta como NCM)")
    # --- cache de prompts / ctxcp (ahora con ~1 GB mas de margen) ---
    lineas.append(
        "CTXCP4 | add:--ctxcp,4 | inactiva | cache de prompts; activa tras "
        "verificar la flag en el dump de TU build (llama-flags-nuevo.txt)")
    return lineas, avisos


def _p7_archivo(rutas, args, cfg):
    ruta = args.archivo or os.path.join(rutas["base"], ARCHIVO_P7)
    if not os.path.exists(ruta):
        lineas, avisos = _deriva_candidatas(cfg)
        _escribe_tabla(ruta, lineas)
        for av in avisos:   # delta D2: los avisos se muestran, no se callan
            print(yellow("  aviso de derivacion: %s" % av))
        print(cyan("  candidatas generadas: %s (edita y vuelve a correr p7 "
                   "cuando quieras)" % ruta))
    return ruta


def _p7_sanity(args, rutas, carpeta):
    """El juez del cambio de cuant: 12 prompts con tool-calling OBLIGATORIO.
    (veredicto_ok, motivos, ruta_resumen). Server vivo ya comprobado."""
    puerto = args.puerto
    print(cyan("  sanity del cambio de cuant: %d prompts (tool-calling "
               "obligatorio)..." % len(PROMPTS_SANITY_P7)))
    resumen, fallas, respuestas = [], 0, []
    for i, (nombre, texto) in enumerate(PROMPTS_SANITY_P7, 1):
        try:
            contenido = _chat_uno(puerto, texto)[0]
        except Exception as e:
            contenido = "[ERROR HTTP] %r" % e
            fallas += 1
        respuestas.append((nombre, contenido))
        with open(os.path.join(carpeta, "sanity-%02d-%s.txt" % (i, nombre)),
                  "w", encoding="utf-8") as f:
            f.write("PROMPT: %s\n\nRESPUESTA:\n%s\n" % (texto, contenido))
        primera = (contenido.strip().splitlines() or ["(vacia)"])[0][:64]
        estilo = green if "[ERROR" not in contenido and contenido.strip() else red
        print(estilo("  %02d/%02d %-18s %s" % (i, len(PROMPTS_SANITY_P7),
                                               nombre, primera)))
        resumen.append("| %02d | %s | %s |" % (i, nombre, primera.replace("|", "/")))
    ruta_res = os.path.join(carpeta, "RESUMEN.md")
    if os.path.exists(ruta_res):
        # el RESUMEN de una vuelta anterior se ROTA (no se borra: evidencia, F23)
        viejo = os.path.join(carpeta, "RESUMEN-%s.md"
                             % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.replace(ruta_res, viejo)
    with open(ruta_res, "w", encoding="utf-8") as f:
        f.write("# Sanity P7 (cambio de cuant) — tool-calling obligatorio\n\n"
                "| # | tipo | primera linea |\n|---|------|---------------|\n")
        f.write("\n".join(resumen) + "\n")
    ok, motivos = _anclas_chequeo(respuestas)
    if fallas:
        motivos.insert(0, "%d/%d prompts con error HTTP" % (fallas, len(PROMPTS_SANITY_P7)))
    return (ok and fallas == 0), motivos, ruta_res


def paso7(args, rutas, estado):
    print(bold(cyan("\n=== P7 - N2 dosis (re-ancla + candidatas + sanity) ===")))
    # PUERTA ROJA de entrada de la olla entera (formula exacta, F3):
    # cerrada = (n3.cerrado O P3 verde_olla1) Y P6 verde_olla1.
    cerrada, det = _primera_olla(rutas)
    if cerrada:
        print(green("  puerta de entrada: la primera olla esta CERRADA. Se cocina."))
    elif args.fuerza:
        print(yellow("  PUERTA SALTADA A PROPOSITO (--fuerza): %s" % "; ".join(det)))
    else:
        fatal("la primera olla (pasos 1..6) aun no cierra esta campana",
              det + ["corre CAMPANA.py (o CAMPANA-v2.py) del 1 al 6 antes",
                     "si de verdad quieres seguir sin cerrarla: --fuerza "
                     "(queda escrito)"])
    cfg = leer_config(rutas["config"])
    carpeta = os.path.join(rutas["base"], "campana-n4-n5-p7")
    os.makedirs(carpeta, exist_ok=True)
    ruta_tabla = _p7_archivo(rutas, args, cfg)
    candidatas = _leer_tabla(ruta_tabla)
    if args.previa:
        print(cyan("  PREVIA (no se arranca ningun server):"))
        for c in candidatas:
            print("    %-12s %-7s %s %s" % (
                c["nombre"], "ACTIVA" if c["activa"] else "reposo",
                c["acciones"] or "(receta tal cual)",
                gray("- " + c["nota"]) if c["nota"] else ""))
        return 0
    # 1) la re-ancla SIEMPRE (es la regla: el cuant nuevo es un mundo nuevo)
    print(cyan("  1) RE-ANCLA con el cuant vigente (receta tal cual)..."))
    ms_ancla, corridas_ancla = _lanza_corridas(args, rutas, "ANCLA", "", carpeta)
    ancla = mediana(ms_ancla)
    if not ancla:
        estado["pasos"]["7"] = {"estado": "DUDOSO",
                                "resumen": "la re-ancla no midio nada",
                                "archivo": ruta_tabla}
        guardar_estado(rutas["estado"], estado)
        _inf(rutas, "P7 re-ancla SIN datos", [
            "- corridas: %d" % len(corridas_ancla),
            "- revisa los logs server-ANCLA-c*.log en %s" % carpeta])
        return 2
    print(green("  ANCLA del cuant: %.2f t/s (mediana de %d corridas)"
                % (ancla, len(ms_ancla))))
    # 2) candidatas activas, UNA dosis por corrida (NO acumulativas, T3)
    resultados = {}
    for c in candidatas:
        if not c["activa"] or c["nombre"].upper().startswith("ANCLA"):
            continue
        print(cyan("  2) CANDIDATA %s %s..." % (c["nombre"],
                                                "(%s)" % c["acciones"] if c["acciones"] else "")))
        ms, _ = _lanza_corridas(args, rutas, c["nombre"], c["acciones"], carpeta)
        m = mediana(ms)
        delta = ((m - ancla) / ancla * 100.0) if (m and ancla) else None
        veredicto = ("SIN-DATOS" if not m else
                     ("GANA (+%.1f pp)" % delta if delta >= KEEP_MIN_PP else
                      ("NEUTRA (+%.1f pp < %0.0f pp: no se persigue)" % (delta, KEEP_MIN_PP)
                       if delta >= 0 else "PIERDE (%.1f pp)" % delta)))
        resultados[c["nombre"]] = {"mediana": m, "delta_pp": delta,
                                   "veredicto": veredicto, "nota": c["nota"]}
        print("    %s -> %s" % (c["nombre"], yellow(veredicto)))
    # 3) el sanity del cambio de cuant (tool-calling OBLIGATORIO)
    sanity_ok, motivos_sanity, ruta_res = None, [], None
    if not args.sin_sanity:
        proc = None
        try:
            if health_ok(args.puerto):
                print(cyan("  [defensa en profundidad] server vivo: se USA, no se toca."))
            else:
                proc, rc = _arranca_server(
                    [cfg["RUTA_SERVER"]] + _tokens_de_receta(cfg) +
                    ["-m", cfg["RUTA_MODELO"], "--host", "127.0.0.1",
                     "--port", str(args.puerto)],
                    os.path.join(carpeta, "server-sanity.log"), args.puerto)
                if proc is None:
                    estado["pasos"]["7"] = {"estado": "DUDOSO",
                                            "resumen": "el server del sanity no levanto (rc=%s)" % rc}
                    guardar_estado(rutas["estado"], estado)
                    return 2
            try:
                _chat_uno(args.puerto, "Calienta la plancha: responde 'lista'.", timeout=300)
            except Exception:
                pass
            sanity_ok, motivos_sanity, ruta_res = _p7_sanity(args, rutas, carpeta)
        finally:
            if proc is not None:
                _auto_apaga(proc)
    # veredicto del N2 (criterio de salida del plan):
    #   T11 [F2]: con --sin-sanity el GO es IMPOSIBLE (la rama GO exige
    #   sanity_ok en True; None corta) -> techo REGISTRADO. P8 abre igual
    #   (REGISTRADO es verde), pero el N2 no cierra como GO sin su juez.
    mejor = None
    for nombre, r in resultados.items():
        if r["delta_pp"] is not None and (mejor is None or
                                          r["delta_pp"] > resultados[mejor]["delta_pp"]):
            mejor = nombre
    mejor_delta = resultados[mejor]["delta_pp"] if mejor else 0.0
    if sanity_ok is False:
        est_p7, resumen = "FALLA", "sanity del cuant FALLA: %s" % "; ".join(motivos_sanity)
    elif mejor and mejor_delta >= N2_META_PP and sanity_ok:
        est_p7 = "GO"
        resumen = "%s transfiere +%.1f pp (>= +%.0f%% del N2) con sanity OK" % (
            mejor, mejor_delta, N2_META_PP)
    else:
        est_p7 = "REGISTRADO"
        resumen = ("re-ancla %.2f t/s; mejor candidata %s (%+.1f pp); sin +%.0f%% "
                   "claros: se registra y se decide con datos [N2 s5]"
                   % (ancla, mejor or "-", mejor_delta, N2_META_PP))
    estado["pasos"]["7"] = {
        "estado": est_p7, "resumen": resumen, "ancla_tps": ancla,
        "candidatas": resultados,
        "sanity": ({"ok": sanity_ok, "motivos": motivos_sanity,
                    "resumen": ruta_res} if sanity_ok is not None else
                   {"omitido": True}),
        "archivo": ruta_tabla,
    }
    guardar_estado(rutas["estado"], estado)
    lineas_inf = ["- veredicto: %s — %s" % (est_p7, resumen),
                  "- ancla del cuant: %.2f t/s" % ancla]
    for nombre, r in resultados.items():
        lineas_inf.append("- %s: mediana %s, delta %s -> %s%s"
                          % (nombre,
                             ("%.2f t/s" % r["mediana"]) if r["mediana"] else "SIN DATOS",
                             ("%+.1f pp" % r["delta_pp"]) if r["delta_pp"] is not None else "-",
                             r["veredicto"],
                             (" (nota: %s)" % r["nota"]) if r["nota"] else ""))
    if sanity_ok is not None:
        lineas_inf.append("- sanity 12 prompts (tool obligatorio): %s%s"
                          % ("OK" if sanity_ok else "FALLA",
                             ("; " + "; ".join(motivos_sanity)) if motivos_sanity else ""))
        lineas_inf.append("- respuestas: %s" % ruta_res)
    lineas_inf.append("- CSV: %s" % os.path.join(carpeta, "resultados.csv"))
    _inf(rutas, "P7 N2 dosis -> %s" % est_p7, lineas_inf)
    print(green(bold("  P7 -> %s: %s" % (est_p7, resumen))))
    return 0 if est_p7 in ("GO", "REGISTRADO") else 2


# ============ §3 P8 — N4 ESCALERA DE VRAM (la despensa) ======================
# Las 3 trampas R61 del boceto viven en la derivacion (delta D1):
#   T1/R61-a: NGL ANTES de la subida NCM detendria la escalera sin subirla
#             -> NCM primero y activo, NGL inactivas al final y aparte.
#   T2/R61-b: el placeholder "--cmoe-cache" NO existe en el dump; la flag
#             real es --moe-cache-mib [dump linea 128].
#   T3/R61-c: los peldanos NO son acumulativos; las pilas del ganador se
#             escriben combinadas con ';' en UNA fila.

ARCHIVO_P8 = "campana-n4-n5-p8-escalera.txt"


def _deriva_escalera(cfg):
    """Deriva peldanos de la RECETA REAL siguiendo el plan R61 (seccion 5,
    las tablas listas para pegar) y las trampas T1/T2/T3 del boceto
    (delta D1 de esta olla). La escalera de VRAM NO transfiere entre
    cuants (N4 s17): se mide UNA vez, aqui. Devuelve (lineas, avisos)."""
    tokens = _tokens_de_receta(cfg)
    lineas = [
        "# ESCALERA P8 — N4 sobre el cuant vigente (la despensa). DERIVADA",
        "# ya CORREGIDA segun plan R61 s5 + trampas T1/T2/T3 del boceto.",
        "# Formato por linea:  nombre | acciones | activa|inactiva | nota",
        "# Orden de corrida = orden de este archivo. ANCLA (receta tal cual)",
        "# SIEMPRE primero. Regla cliff-1: si un peldano cae en el cliff",
        "# (t/s < 70% del ancla o server muerto), la escalera SE DETIENE y la",
        "# frontera queda UN peldano antes (nunca se compra el traje que rasga).",
        "# Certificados por peldano: nvidia-smi (<= 3712 MB), pageouts del log.",
        "# VUELTA 1 = subida pura (ANCLA + NCM38..34, activas). VUELTA 2 = la",
        "# pila WIN+ sobre el GANADOR (inactivas: sustituye 37 por el ganador",
        "# real y activa; los peldanos NO son acumulativos: pilas con ';').",
        "ANCLA | | ancla | la receta diaria tal cual (NP2, -lm none, UB1K)",
    ]
    avisos = ["escalera derivada CORREGIDA (plan R61 s5 + T1/T2/T3): NCM "
              "primero y activo, NGL inactivas al final y aparte, MEC con "
              "el nombre real del dump --moe-cache-mib"]
    # --- VUELTA 1: la subida pura NCM (el primer peldaño autentica la
    #     semantica: A0, buffer del log debe crecer ~+656 MiB = 2x328.2) ---
    lineas.append(
        "NCM38 | add:-ncmoe,38 | activa | +2 capas a VRAM (+656 MiB); A0: "
        "autentica semantica, buffer 'CUDA0 model buffer' debe crecer ~+656 MB")
    lineas.append(
        "NCM37 | add:-ncmoe,37 | activa | +3 capas (+985 MiB); semilla "
        "barrido-30 22.49 t/s en el mundo viejo")
    lineas.append(
        "NCM36 | add:-ncmoe,36 | activa | +4 capas (+1313 MiB); maxima "
        "conservadora, justo bajo el certificado 3712")
    lineas.append(
        "NCM35 | add:-ncmoe,35 | activa | +5 capas (+1641 MiB); zona de "
        "cliff, la regla cliff-1 decide")
    lineas.append(
        "NCM34 | add:-ncmoe,34 | activa | +6 capas (+1969 MiB); CLIFF "
        "esperado (>4096): la escalera debe parar aqui")
    # --- control de semantica independiente (H6/A6): -ot comma-list en UN
    #     solo flag (T5: repetirlo esta deprecado #13154), patron sin | ni , ---
    lineas.append(
        "BLIND-OT37 | add:-ncmoe,37;add:-ot,blk\\.(3[7-9])\\.ffn_.*_exps"
        "\\.weight=CUDA0 | inactiva | control -ot (H6): activar si A0 no "
        "autentica la semantica")
    # --- NGL descendente: diagnostico del suelo del backbone, INACTIVAS
    #     (T1: bajar -ngl manda GDN/aten a CPU y detendria la escalera
    #     antes de subirla; va al final y aparte) ---
    ngl = None
    for i, t in enumerate(tokens):
        if t == "-ngl" and i + 1 < len(tokens):
            try:
                ngl = int(tokens[i + 1])
            except Exception:
                ngl = None
    if ngl is not None:
        for v in (ngl - 12, ngl - 6):
            if v >= 0:
                lineas.append(
                    "NGL-%d | sub:%d>%d | inactiva | diagnostico del suelo "
                    "del backbone: va AL FINAL y aparte, NUNCA antes de la "
                    "subida NCM (T1)" % (v, ngl, v))
        avisos.append("NGL derivada desde el tope %d como INACTIVAS (T1: "
                      "activas antes de la subida NCM detendrian la escalera)"
                      % ngl)
    else:
        lineas.append(
            "NGL-EJEMPLO | sub:99>87 | inactiva | ejemplo: ajusta al "
            "-ngl real de TU receta")
    # --- VUELTA 2: la pila sobre el GANADOR (inactivas hasta que el
    #     Director sustituya 37 por el ganador real; pilas con ';', T3) ---
    lineas.append(
        "WIN | add:-ncmoe,37 | inactiva | vuelta 2: el ganador de la vuelta "
        "1 (SUSTITUYE 37 por el ganador real en esta fila y las WIN+)")
    lineas.append(
        "WIN+MEC512 | add:-ncmoe,37;add:--moe-cache-mib,512 | inactiva | "
        "MEC 512 sobre el ganador (flag REAL del dump: --moe-cache-mib, T2); "
        "D-MEC-0 obligatorio: cache chico = riesgo -48% (#29887)")
    lineas.append(
        "WIN+MEC768 | add:-ncmoe,37;add:--moe-cache-mib,768 | inactiva | "
        "escalar de a 256 MiB solo si 512 no toca el certificado")
    lineas.append(
        "WIN+DIO | add:-ncmoe,37;sub:none>dio | inactiva | variante RAM: "
        "activar SOLO si el Get-Counter (R0) detecto pageouts")
    lineas.append(
        "WIN+UBCHICO | add:-ncmoe,37;add:-ub,64;add:-b,512 | inactiva | "
        "intercambio presupuestario L4 (U1): menos buffer, mas VRAM; "
        "ORO-UB1K manda en velocidad: nunca promocion directa")
    lineas.append(
        "WIN+KVF16 | add:-ncmoe,37;sub:q8_0>f16 | inactiva | diagnostico KV "
        "(K1): un solo sub pisa AMBOS -ctk y -ctv (T4); solo diagnostico, "
        "KV cuantizada es feature de MEMORIA")
    lineas.append(
        "WIN+CHARLA4 | add:-ncmoe,37;add:--override-kv,"
        "qwen35moe.expert_used_count=4 | inactiva | ratificacion dual (D1): "
        "el ganador en modo charla k=4; la salida del PASO 8 lo exige")
    return lineas, avisos


def _p8_archivo(rutas, args, cfg):
    ruta = args.archivo or os.path.join(rutas["base"], ARCHIVO_P8)
    if not os.path.exists(ruta):
        lineas, avisos = _deriva_escalera(cfg)
        _escribe_tabla(ruta, lineas)
        for av in avisos:   # delta D2: los avisos se muestran, no se callan
            print(yellow("  aviso de derivacion: %s" % av))
        print(cyan("  escalera generada: %s (edita y vuelve a correr p8)" % ruta))
    return ruta


def paso8(args, rutas, estado):
    print(bold(cyan("\n=== P8 - N4: escalera de VRAM sobre el cuant nuevo ===")))
    # PUERTA ROJA: p8 exige p7 verde (GO o REGISTRADO). --fuerza lo deja
    # escrito. El lado RAM de dosis fina del N4 (CTXCP4) vive en P7:
    # saltarla con --fuerza deja ese lado SIN medir (pendiente de P7).
    _puerta(args, "p8", estado["pasos"].get("7", {}), "P7",
            ("GO", "REGISTRADO"), ("Se sube a la escalera.",))
    cfg = leer_config(rutas["config"])
    carpeta = os.path.join(rutas["base"], "campana-n4-n5-p8")
    os.makedirs(carpeta, exist_ok=True)
    ruta_tabla = _p8_archivo(rutas, args, cfg)
    peldanos = _leer_tabla(ruta_tabla)
    if args.previa:
        print(cyan("  PREVIA (no se arranca ningun server):"))
        for p in peldanos:
            print("    %-12s %-7s %s %s" % (
                p["nombre"], "ACTIVA" if p["activa"] else "reposo",
                p["acciones"] or "(receta tal cual)",
                gray("- " + p["nota"]) if p["nota"] else ""))
        return 0
    # 1) el ancla de la escalera (tambien es el ancla de sesion: T6, la GPU
    #    fria miente ~-15%; re-medirla en cada arranque ES la regla)
    print(cyan("  1) ANCLA de la escalera (receta tal cual)..."))
    ms_ancla, _ = _lanza_corridas(args, rutas, "ANCLA", "", carpeta)
    ancla = mediana(ms_ancla)
    if not ancla:
        estado["pasos"]["8"] = {"estado": "DUDOSO",
                                "resumen": "el ancla de la escalera no midio"}
        guardar_estado(rutas["estado"], estado)
        _inf(rutas, "P8 ancla SIN datos",
             ["- revisa server-ANCLA-c*.log en %s" % carpeta])
        return 2
    print(green("  ANCLA de la escalera: %.2f t/s" % ancla))
    # 2) peldanos activos EN ORDEN DE ARCHIVO, con cliff-1 automatico:
    #    cae_cliff = (sin datos) O (>= 1 corrida muerta, T17: muertos > 0
    #    manda aunque la mediana se calcule con las vivas) O
    #    (m < ANCLA x 0.70). La escalera SE DETIENE y la frontera queda
    #    UN peldano antes (jamas se compra el traje que rasga: cliff x10).
    peldanos_datos, frontera, cliff_en = [], None, None
    for p in peldanos:
        if cliff_en is not None:
            break  # regla cliff-1: la escalera SE DETIENE en el cliff
        if not p["activa"] or p["nombre"].upper().startswith("ANCLA"):
            continue
        print(cyan("  2) PELDANO %s %s..." % (p["nombre"],
                                              "(%s)" % p["acciones"] if p["acciones"] else "")))
        ms, por_corrida = _lanza_corridas(args, rutas, p["nombre"],
                                          p["acciones"], carpeta)
        m = mediana(ms)
        muertos = sum(1 for d in por_corrida if not d["viva"])
        vram_max = max([d["vram_mb"] for d in por_corrida
                        if d["vram_mb"] is not None], default=None)
        cae_cliff = (m is None or muertos > 0 or
                     m < ancla * CLIFF_FRACCION)
        fila = {"nombre": p["nombre"], "acciones": p["acciones"],
                "mediana": m, "muertos": muertos, "vram_max_mb": vram_max,
                "delta_pp": ((m - ancla) / ancla * 100.0) if m else None,
                "cliff": cae_cliff}
        peldanos_datos.append(fila)
        if cae_cliff:
            cliff_en = p["nombre"]
            print(red("  CLIFF en %s (t/s %s, muertos %d): la escalera se "
                      "detiene y la frontera queda UN peldano antes "
                      "(regla cliff-1)." % (p["nombre"],
                                            ("%.2f" % m) if m else "sin datos",
                                            muertos)))
        else:
            frontera = fila
            print(green("  peldano OK: %.2f t/s (%+.1f pp), VRAM max %s MB"
                        % (m, fila["delta_pp"],
                           vram_max if vram_max is not None else "-")))
    # 3) VEREDICTO con las TRES ramas exactas (F1):
    #      sin peldanos activos      -> REGISTRADO (solo ancla)
    #      con cliff Y hay frontera  -> GO (frontera = un peldano antes)
    #      con cliff Y SIN frontera  -> DUDOSO, rc=2 (el PRIMER peldano
    #                                   activo fue el que rasgo)
    #      sin cliff (completa)      -> GO
    if not peldanos_datos:
        resumen = "no habia peldanos activos: solo ancla (%.2f t/s)" % ancla
        est_p8 = "REGISTRADO"
    elif cliff_en is not None:
        resumen = ("cliff en %s; frontera = %s (regla cliff-1: un peldano "
                   "antes del rasgon)" % (cliff_en,
                                          frontera["nombre"] if frontera else "ANCLA"))
        est_p8 = "GO" if frontera is not None else "DUDOSO"
    else:
        resumen = ("escalera completa sin cliff; frontera = %s"
                   % (peldanos_datos[-1]["nombre"]))
        est_p8 = "GO"
    estado["pasos"]["8"] = {"estado": est_p8, "resumen": resumen,
                            "ancla_tps": ancla, "peldanos": peldanos_datos,
                            "cliff": cliff_en, "frontera": frontera,
                            "archivo": ruta_tabla}
    guardar_estado(rutas["estado"], estado)
    lineas_inf = ["- veredicto: %s — %s" % (est_p8, resumen),
                  "- ancla: %.2f t/s" % ancla]
    for f in peldanos_datos:
        lineas_inf.append(
            "- %s (%s): mediana %s, %+.1f pp, VRAM max %s MB%s%s"
            % (f["nombre"], f["acciones"] or "receta tal cual",
               ("%.2f t/s" % f["mediana"]) if f["mediana"] else "SIN DATOS",
               f["delta_pp"] if f["delta_pp"] is not None else 0.0,
               f["vram_max_mb"] if f["vram_max_mb"] is not None else "-",
               " [CLIFF]" if f["cliff"] else "",
               " [AVISO VRAM > %d MB]" % VRAM_CERTIFICADO_MB
               if (f["vram_max_mb"] or 0) > VRAM_CERTIFICADO_MB else ""))
    lineas_inf.append("- CSV: %s" % os.path.join(carpeta, "resultados.csv"))
    lineas_inf.append("- HUECO para P10 (dato): hueco = 4096 - VRAM(ganador); "
                      "si la frontera es NCM37 -> ~901 MB (el nextn 858 cabe "
                      "sin margen); si es NCM36 -> ~572 MB (no cabe: -cmoed o "
                      "bajar una capa)")
    _inf(rutas, "P8 escalera VRAM -> %s" % est_p8, lineas_inf)
    print(green(bold("  P8 -> %s: %s" % (est_p8, resumen))))
    return 0 if est_p8 in ("GO", "REGISTRADO") else 2


# ============ §4 P9 — RUTA 0 (build b11901, el mundo nuevo) ==================

BUILD_B11901 = "b11901"


def _version_de(server):
    """Texto de `llama-server --version` (o None si no corre)."""
    try:
        out = subprocess.run([server, "--version"], capture_output=True,
                             text=True, timeout=60)
        return (out.stdout or "") + (out.stderr or "")
    except Exception:
        return None


def _flags_de_help(texto):
    """Set de flags de un `--help` completo (lineas tipo '  -ngl, --n-gpu-layers')."""
    flags = set()
    for ln in (texto or "").splitlines():
        s = ln.strip()
        if not s.startswith("-"):
            continue
        for tok in s.split(","):
            tok = tok.strip().split(" ")[0].strip()
            if tok.startswith("-") and len(tok) > 1:
                flags.add(tok)
    return flags


def _sondea_reuse(args, rutas, cfg, servidor_nuevo, carpeta):
    """(vivo, evidencia): levanta el build nuevo con --cache-reuse 256, manda
    DOS prompts con el MISMO prefijo y busca 'restored context checkpoint'
    en el log. #24055 (r32): en b11856 reuse estaba MUERTO en ambas
    colocaciones — si aqui revive, la familia ORO-SHIFT vuelve a la mesa.
    TRES salidas (F15): True (VIVO) / False (MUERTO: 0 lineas) / None
    (INDETERMINADO: el server del sondeo no levanto -> GO con reuse '?')."""
    tokens = _acciona(_tokens_de_receta(cfg), "add:--cache-reuse,256")
    cmd = [servidor_nuevo] + tokens + ["-m", cfg["RUTA_MODELO"],
                                       "--host", "127.0.0.1",
                                       "--port", str(args.puerto)]
    log_srv = os.path.join(carpeta, "server-reuse.log")
    proc, rc = _arranca_server(cmd, log_srv, args.puerto)
    if proc is None:
        return None, "el build nuevo NO levanto con la receta + --cache-reuse 256 (rc=%s)" % rc
    evidencia = []
    try:
        try:
            # el sondeo tambien calienta plancha antes de sus 2 prompts (F24)
            _chat_uno(args.puerto, "Calienta la plancha: responde 'lista'.", timeout=300)
        except Exception:
            pass
        prefijo = ("Eres un cocinero de datos. Receta del dia: llama.cpp b11901. "
                   "Pregunta %d: ")
        for n in (1, 2):
            try:
                contenido, _ = _chat_uno(args.puerto, (prefijo % n) +
                                         "resume en una frase que es la VRAM.")
                evidencia.append("prompt %d: %s" % (n, (contenido.strip().splitlines()
                                                        or ["(vacia)"])[0][:60]))
            except Exception as exc:
                evidencia.append("prompt %d: ERROR %r" % (n, exc))
    finally:
        _auto_apaga(proc)
    n = _cuenta_en_log(log_srv, "restored context checkpoint")
    return (bool(n), "lineas 'restored context checkpoint' en el log: %s%s"
            % (n, ("; " + "; ".join(evidencia)) if evidencia else ""))


def paso9(args, rutas, estado):
    print(bold(cyan("\n=== P9 - RUTA 0: build b11901 (el mundo nuevo) ===")))
    # PUERTA ROJA: p9 exige p8 verde. --fuerza lo deja escrito.
    _puerta(args, "p9", estado["pasos"].get("8", {}), "P8",
            ("GO", "REGISTRADO"), ("Al taller.",))
    cfg = leer_config(rutas["config"])
    servidor_viejo = cfg.get("RUTA_SERVER", "")
    if not servidor_viejo or not os.path.exists(servidor_viejo):
        fatal("RUTA_SERVER (b11856) no valido: %r" % servidor_viejo,
              ["revisa RUTA_SERVER en config.txt"])
    build_dir = args.build_dir or os.path.join(
        os.path.dirname(os.path.abspath(servidor_viejo)), BUILD_B11901)
    carpeta = os.path.join(rutas["base"], "campana-n4-n5-p9")
    os.makedirs(carpeta, exist_ok=True)
    servidor_nuevo = os.path.join(build_dir, "llama-server.exe")
    if not os.path.exists(servidor_nuevo):
        # en taller POSIX (tests) el nombre puede venir sin .exe
        alt = os.path.join(build_dir, "llama-server")
        servidor_nuevo = alt if os.path.exists(alt) else servidor_nuevo
    if not os.path.exists(servidor_nuevo):
        estado["pasos"]["9"] = {"estado": "PENDIENTE",
                                "resumen": "no esta el build b11901 en %s" % build_dir}
        guardar_estado(rutas["estado"], estado)
        fatal("no encuentro llama-server.exe del build nuevo en %s" % build_dir,
              ["PASO 9 del plan: TU descargas los 2 zips cuando el rig NO mide:",
               "  llama-b11901-bin-win-cuda-12.4-x64.zip  (binario, sin compilar)",
               "  + el zip de cudart DLLs del MISMO release (sin el, la GPU duerme)",
               "descomprime los DOS en esa carpeta y vuelve a correr p9",
               "o pasa --build-dir D:\\ruta\\donde\\descomprimiste"])
    # 1) version honesta del binario nuevo (E31)
    texto_ver = _version_de(servidor_nuevo)
    tiene_b = (texto_ver or "").lower().find(BUILD_B11901) >= 0
    print("  1) version: %s" % (green("b11901 detectado") if tiene_b
                                else red("NO se ve '%s' en --version" % BUILD_B11901)))
    if texto_ver:
        primera = (texto_ver.strip().splitlines() or [""])[0]
        print(gray("    %s" % primera[:100]))
    if not tiene_b:
        estado["pasos"]["9"] = {"estado": "FALLO-CERTIFICADO",
                                "resumen": "el binario de %s no es b11901" % build_dir}
        guardar_estado(rutas["estado"], estado)
        _inf(rutas, "P9 version -> FALLO",
             ["- --version de %s no contiene '%s'" % (servidor_nuevo, BUILD_B11901)])
        fatal("el binario nuevo NO es b11901: no se cocina un mundo sin saber cual es",
              ["descarga el zip oficial b11901 o revisa --build-dir"])
    # 2) cudart vivo (sin el, la GPU queda dormida: N3 s16, E32)
    dlls = [d for d in os.listdir(build_dir)
            if d.lower().startswith("cudart") and d.lower().endswith(".dll")]
    print("  2) cudart DLLs en el build: %s" %
          (green(", ".join(sorted(dlls))) if dlls else
           yellow("NINGUNA (extrae tambien el zip de cudart EN esta carpeta)")))
    if not dlls:
        estado["pasos"]["9"] = {"estado": "PENDIENTE",
                                "resumen": "falta el cudart en el build nuevo"}
        guardar_estado(rutas["estado"], estado)
        fatal("sin cudart la GPU queda DORMIDA (motivo certificado N3 s16)",
              ["extrae el zip de cudart DLLs del mismo release EN %s" % build_dir])
    # 3) re-auditoria de defaults: dump --help viejo vs nuevo (diff, E33)
    print(cyan("  3) re-auditoria de defaults (--help b11856 vs b11901)..."))
    help_viejo = ""
    try:
        out_v = subprocess.run([servidor_viejo, "--help"], capture_output=True,
                               text=True, timeout=120)
        help_viejo = (out_v.stdout or "") + (out_v.stderr or "")
    except Exception:
        help_viejo = ""
    try:
        out_n = subprocess.run([servidor_nuevo, "--help"], capture_output=True,
                               text=True, timeout=120)
        help_nuevo = (out_n.stdout or "") + (out_n.stderr or "")
    except Exception:
        help_nuevo = ""
    with open(os.path.join(carpeta, "help-b11856.txt"), "w", encoding="utf-8") as f:
        f.write(help_viejo or "")
    with open(os.path.join(carpeta, "help-b11901.txt"), "w", encoding="utf-8") as f:
        f.write(help_nuevo or "")
    fv, fn = _flags_de_help(help_viejo), _flags_de_help(help_nuevo)
    muertas = sorted(fv - fn)
    nacidas = sorted(fn - fv)
    print("    flags que MUEREN del 11856: %s" % (", ".join(muertas) or "(ninguna)"))
    print("    flags que NACEN en el 11901 : %s" % (", ".join(nacidas) or "(ninguna)"))
    # 4) re-certificar la clave del override (puede cambiar de nombre: E34)
    clave_viva = "expert-used-count" in help_nuevo or "expert_used_count" in help_nuevo
    print("  4) override de expertos: %s"
          % (green("la familia expert_used_count sigue en el --help nuevo")
             if clave_viva else
             yellow("NO se ve expert_used_count en el --help nuevo: revisa "
                    "el nuevo nombre de la clave antes de fiarte del pin")))
    # 5) sondeo cache-reuse (#24055: muerto en b11856, E35)
    print(cyan("  5) sondeo cache-reuse (--cache-reuse 256, prefijo repetido)..."))
    reuse_vivo, evi_reuse = _sondea_reuse(args, rutas, cfg, servidor_nuevo, carpeta)
    print("    reuse: %s (%s)" % (green("VIVO") if reuse_vivo else
                                  (red("MUERTO (motivo cerrado con certificado)")
                                   if reuse_vivo is False else yellow("INDETERMINADO")),
                                  evi_reuse))
    # 6) re-ancla en el mundo nuevo (E36): MED3 con la receta vigente —
    #    build nuevo = mundo nuevo. [delta D2: la olla original imprimia
    #    "1 corrida" y corria MED3 (cosmetico F11); aqui se imprime la
    #    verdad. La CONDUCTA (mediana de medianas) es identica.]
    print(cyan("  6) re-ancla del mundo nuevo (mediana de %d corridas x %d "
               "prompts)..." % (max(1, args.corridas), max(1, args.m_prompts))))
    ms_nuevo, por = _lanza_corridas(args, rutas, "B11901", "", carpeta)
    ancla_nueva = mediana(ms_nuevo)
    receta_viva = bool(ms_nuevo)
    resumen = ("b11901 vivo con la receta (ancla %s t/s); reuse %s; "
               "flags muertas: %d, nacidas: %d"
               % (("%.2f" % ancla_nueva) if ancla_nueva else "SIN DATOS",
                  "VIVO" if reuse_vivo else ("muerto" if reuse_vivo is False else "?"),
                  len(muertas), len(nacidas)))
    # VEREDICTO con las salidas exactas (F15): el sondeo tiene TRES salidas
    est_p9 = "MOTIVO-CERRADO" if (reuse_vivo is False and receta_viva) else \
             ("GO" if receta_viva else "DUDOSO")
    estado["pasos"]["9"] = {"estado": est_p9, "resumen": resumen,
                            "build_dir": build_dir, "reuse_vivo": reuse_vivo,
                            "ancla_tps": ancla_nueva,
                            "flags_muertas": muertas, "flags_nacidas": nacidas,
                            "override_familia": clave_viva}
    guardar_estado(rutas["estado"], estado)
    lineas_inf = ["- veredicto: %s — %s" % (est_p9, resumen),
                  "- build: %s (cudart: %s)" % (build_dir,
                                                ", ".join(sorted(dlls)) or "NINGUNA"),
                  "- defaults que mueren del 11856: %s" % (", ".join(muertas) or "(ninguna)"),
                  "- defaults que nacen en el 11901: %s" % (", ".join(nacidas) or "(ninguna)"),
                  "- override expertos: familia %s" %
                  ("presente" if clave_viva else "NO vista en --help (revisar clave)"),
                  "- cache-reuse: %s (%s)" % (reuse_vivo, evi_reuse),
                  "- dumps: %s y %s" % (os.path.join(carpeta, "help-b11856.txt"),
                                        os.path.join(carpeta, "help-b11901.txt"))]
    if muertas:
        lineas_inf.append("- AVISO del plan: los alias que mueren tras RUTA 0 "
                          "(PR #28334) hay que traducirlos a la -lm/-flag nueva "
                          "en config.txt ANTES de seguir midiendo.")
    _inf(rutas, "P9 RUTA 0 b11901 -> %s" % est_p9, lineas_inf)
    print(green(bold("  P9 -> %s: %s" % (est_p9, resumen))))
    return 0 if est_p9 in ("GO", "MOTIVO-CERRADO", "REGISTRADO") else 2


# ============ §5 P10 — N5 DUELO SPEC vs NP2 + RECETA FINAL + CIERRE ==========

BRAZOS = [
    # (nombre, acciones, activa, nota)
    ("A-NP2", "", True,
     "la receta promovida tal cual: NP2 (+22.8% [N3]) sin spec"),
    ("B-SPEC", "delpair:-np;add:--spec-draft-n-max,2;add:--spec-draft-p-min,0.75",
     True, "MTP-n2 sin NP2 (SS11.4: MTP exige -np 1); n-max y p-min "
           "SIEMPRE explicitos (defaults b11856: 16 y 0.75)"),
    ("C-KVOFF", "delpair:-np;add:--spec-draft-n-max,2;add:--spec-draft-p-min,0.75;"
                "add:--kv-unified,off",
     False, "fallback #25345: si el draft calla (kv-unified), se activa "
            "sola cuando B no llega al 90% de A"),
]


def _brazos_tabla():
    lineas = ["# BRAZOS del duelo N5 (p10). Formato: nombre | acciones | "
              "activa|inactiva | nota",
              "# El duelo: NP2 sin spec (A) vs spec sin NP2 (B). Gana el mejor "
              "t/s x calidad.",
              "# C-KVOFF se activa SOLA si B < 90% de A (#25345 kv-unified).",
              "ANCLA | | ancla | (interno: la receta diaria, para comparar)"]
    for nombre, acciones, activa, nota in BRAZOS:
        lineas.append("%s | %s | %s | %s" % (
            nombre, acciones, "activa" if activa else "inactiva", nota))
    return lineas


def _brazos_por_nombre():
    return {n: (a, nota) for n, a, _, nota in BRAZOS}


def _fila_brazo(nombre, acciones, ms, por):
    """Fila del duelo para un brazo: mediana de medianas + spot POR CORRIDA
    (F7: el brazo queda elegible solo con spot limpio en TODAS sus
    corridas) + errores + muertos. Usada por A, B y el fallback C."""
    spots_ok = [d["spot_ok"] for d in por if d["spot_ok"] is not None]
    return {"nombre": nombre, "mediana": mediana(ms), "acciones": acciones,
            "errores": sum(d["errores"] for d in por),
            "spot_resumen": ("OK (anclas)" if spots_ok and all(spots_ok)
                             else ("MIXTO" if spots_ok else "sin spot")),
            "muertos": sum(1 for d in por if not d["viva"])}


def _escribe_resumen_duelo(ruta, filas, ganador, motivo):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("# Duelo N5: spec vs NP2 — %s\n\n" % ganador)
        f.write("%s\n\n" % motivo)
        f.write("| brazo | mediana t/s (mediana de medianas) | spot ES | errores |"
                "\n|-------|-----------------------------------|---------|---------|\n")
        for f2 in filas:
            f.write("| %s | %s | %s | %d |\n" % (
                f2["nombre"],
                ("%.2f" % f2["mediana"]) if f2["mediana"] else "SIN DATOS",
                f2["spot_resumen"] or "-", f2["errores"]))
    return ruta


def _receta_final(cfg, acciones_ganadoras):
    """(nuevas_base, nuevas_ganadoras): aplica la cirugia del brazo ganador a
    la receta por tokens. FLAGS_BASE conserva la estructura (se le aplican
    los del/delpair/sub); FLAGS_GANADORAS recibe los add (el ultimo valor
    gana, regla de la casa). El modelo NUNCA va dentro (RUTA_MODELO manda)."""
    base = _quita_modelo(cfg.get("FLAGS_BASE", "").split())
    ganad = _quita_modelo(cfg.get("FLAGS_GANADORAS", "").split())
    todo = _acciona(base + ganad, acciones_ganadoras)
    # separar de vuelta: los 'del/delpair/sub' cambiaron la base; los 'add'
    # nuevos son los tokens que no estaban ni en base ni en ganadoras.
    add_nuevos = []
    conjunto = set(base) | set(ganad)
    acciones_split = [a.strip() for a in (acciones_ganadoras or "").split(";") if a.strip()]
    for a in acciones_split:
        verbo, _, cuerpo = a.partition(":")
        if verbo.strip().lower() == "add":
            add_nuevos.extend(t for t in cuerpo.split(",") if t)
    nueva_base = [t for t in todo if not (t in add_nuevos and t not in conjunto)]
    nueva_ganad = ganad + [t for t in add_nuevos if t not in conjunto]
    return nueva_base, nueva_ganad


def _escribe_receta_final(rutas, estado, cfg, acciones_ganadoras, nombre_brazo):
    """EL UNICO sitio de esta olla que toca config.txt (T8): confirmacion,
    backup con marca de tiempo, escritura atomica (tmp + os.replace) y
    RE-LECTURA de verificacion. Devuelve (ruta_backup, ok)."""
    if not confirmar("SI", "RECETA FINAL del brazo %s: se reescriben "
                         "FLAGS_BASE/FLAGS_GANADORAS en config.txt (con backup; "
                         "el cuant viejo y SAMPLING no se tocan). Confirmar?" % nombre_brazo):
        _inf(rutas, "P10 receta final CANCELADA por el Director",
             ["- no se toco config.txt (la autoridad es del Director)"])
        print(yellow("  receta final cancelada: config.txt intacto."))
        return None, False
    base_nueva, ganad_nueva = _receta_final(cfg, acciones_ganadoras)
    sello = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = rutas["config"] + ".bak-antes-receta-final-%s" % sello
    shutil.copy2(rutas["config"], backup)
    with open(rutas["config"], encoding="utf-8") as f:
        texto = f.read()

    def _sustituye_clave(texto, clave, valor):
        patron = r"(?m)^(%s\s*=\s*).*$" % re.escape(clave)
        if re.search(patron, texto):
            return re.sub(patron, r"\g<1>%s" % valor, texto)
        return texto + "\n%s = %s\n" % (clave, valor)

    texto = _sustituye_clave(texto, "FLAGS_BASE", " ".join(base_nueva))
    texto = _sustituye_clave(texto, "FLAGS_GANADORAS", " ".join(ganad_nueva))
    tmp = rutas["config"] + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(texto)
        os.replace(tmp, rutas["config"])
    except BaseException:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise
    cfg2 = leer_config(rutas["config"])
    ok = (cfg2.get("FLAGS_BASE", "").split() == base_nueva and
          cfg2.get("FLAGS_GANADORAS", "").split() == ganad_nueva)
    return backup, ok


def paso10(args, rutas, estado):
    print(bold(cyan("\n=== P10 - N5: duelo spec vs NP2 + receta final ===")))
    # PUERTA ROJA: p10 exige p9 verde. --fuerza lo deja escrito.
    _puerta(args, "p10", estado["pasos"].get("9", {}), "P9",
            ("GO", "MOTIVO-CERRADO", "REGISTRADO"), ("A la apuesta grande.",))
    if estado["pasos"].get("10", {}).get("estado") in VERDES:
        # P10 ya cerrado -> no se re-corre salvo pedido explicito (la
        # receta final ya esta escrita).
        print(yellow("  P10 ya estaba cerrado: se corre solo si lo pides "
                     "explicito (la receta final ya esta escrita)."))
    cfg = leer_config(rutas["config"])
    carpeta = os.path.join(rutas["base"], "campana-n4-n5-p10")
    os.makedirs(carpeta, exist_ok=True)
    _escribe_tabla(os.path.join(carpeta, "brazos.txt"), _brazos_tabla())
    # 1) cada brazo ACTIVO: mediana de medianas (la mecanica de TODA la
    #    olla, F13) + spot ES POR CORRIDA (F7)
    filas, datos_brazos = [], {}
    for nombre, acciones, activa, _nota in BRAZOS:
        if not activa and not args.fuerza:
            print(gray("  brazo %s en reposo (fallback: se activa solo si "
                       "B < 90%% de A)" % nombre))
            continue
        print(cyan("  1) BRAZO %s (%s): mediana de %d corridas x %d prompts + spot ES..."
                   % (nombre, acciones or "receta tal cual",
                      args.corridas, args.m_prompts)))
        ms, por = _lanza_corridas(args, rutas, nombre, acciones, carpeta,
                                  con_spot=True)
        fila = _fila_brazo(nombre, acciones, ms, por)
        filas.append(fila)
        datos_brazos[nombre] = fila
        print("    %s -> %s" % (nombre,
                                green("%.2f t/s" % fila["mediana"]) if fila["mediana"]
                                else red("SIN DATOS")))
    # 2) fallback kv-unified (#25345): B calla -> C se activa sola
    a, b = datos_brazos.get("A-NP2"), datos_brazos.get("B-SPEC")
    if a and b and b["mediana"] and a["mediana"] and \
            b["mediana"] < a["mediana"] * 0.90 and "C-KVOFF" not in datos_brazos:
        print(yellow("  el draft CALLA (B < 90% de A): fallback #25345 -> "
                     "C-KVOFF se activa sola (--kv-unified off)."))
        acciones_c = _brazos_por_nombre()["C-KVOFF"][0]
        ms, por = _lanza_corridas(args, rutas, "C-KVOFF", acciones_c, carpeta,
                                  con_spot=True)
        fila = _fila_brazo("C-KVOFF", acciones_c, ms, por)
        filas.append(fila)
        datos_brazos["C-KVOFF"] = fila
    # 3) el veredicto del duelo: mejor t/s con calidad limpia
    elegibles = [f for f in filas if f["mediana"] and
                 (f["spot_resumen"] == "OK (anclas)" or
                  f["spot_resumen"] == "sin spot")]
    ganador = max(elegibles, key=lambda f: f["mediana"]) if elegibles else None
    if ganador is None:
        estado["pasos"]["10"] = {"estado": "DUDOSO", "resumen": "ningun brazo "
                                 "midio con calidad limpia", "brazos": filas}
        guardar_estado(rutas["estado"], estado)
        _inf(rutas, "P10 duelo SIN veredicto",
             ["- ningun brazo midio con spot limpio; revisa los logs en %s" % carpeta])
        return 2
    motivo = ("gana %s: %.2f t/s con spot ES limpio (mediana de medianas de %d "
              "corridas)" % (ganador["nombre"], ganador["mediana"], args.corridas))
    ruta_res = os.path.join(carpeta, "DUELO.md")
    _escribe_resumen_duelo(ruta_res, filas, ganador["nombre"], motivo)
    print(green(bold("  DUELO: %s" % motivo)))
    estado["duelo"] = {"ganador": ganador["nombre"],
                       "mediana_tps": ganador["mediana"],
                       "brazos": filas, "resumen": ruta_res}
    estado["pasos"]["10"] = {"estado": "DUELO-HECHO",
                             "resumen": motivo, "brazos": filas,
                             "ganador": ganador["nombre"]}
    guardar_estado(rutas["estado"], estado)
    _inf(rutas, "P10 duelo spec vs NP2 -> gana %s" % ganador["nombre"],
         ["- %s" % motivo] +
         ["- %s: %s t/s, spot %s" % (f["nombre"],
                                     ("%.2f" % f["mediana"]) if f["mediana"] else "SIN DATOS",
                                     f["spot_resumen"]) for f in filas] +
         ["- detalle: %s" % ruta_res])
    # 4) el CIERRE: receta final (config.txt) + informe de campana
    cerrar = confirmar("SI", "Ultima olla del dia: escribir la RECETA FINAL "
                             "(brazo %s) en config.txt y cerrar la campana de "
                             "los 5 niveles?" % ganador["nombre"])
    if not cerrar:
        _inf(rutas, "P10 cierre APLAZADO por el Director",
             ["- el duelo quedo escrito; la receta final no se toco"])
        print(cyan("  cierre aplazado: el duelo queda escrito, config.txt intacto."))
        return 0
    if ganador["nombre"] == "A-NP2":
        # la receta vigente YA es la ganadora: ratificar (backup igualmente)
        backup, ok = _escribe_receta_final(rutas, estado, cfg, "", "A-NP2 (ratificada)")
    else:
        backup, ok = _escribe_receta_final(rutas, estado, cfg,
                                           ganador["acciones"], ganador["nombre"])
    if backup is None:
        estado["pasos"]["10"]["estado"] = "DUELO-HECHO"
        estado["pasos"]["10"]["resumen"] += " (receta final cancelada)"
        guardar_estado(rutas["estado"], estado)
        return 0
    if not ok:
        fatal("la re-lectura de config.txt NO coincide con la receta final "
              "esperada (integridad de la cirugia)",
              ["restaura el backup %s" % backup,
               "avisa con el log: esto NO deberia pasar nunca"])
    lineas_inf = ["- receta final escrita y VERIFICADA por re-lectura "
                  "(brazo %s)" % ganador["nombre"],
                  "- backup del config anterior: %s" % backup,
                  "- SAMPLING, RUTA_* y el cuant vigente NO se tocaron"]
    # cierre de campana: los 5 niveles en una tabla final
    ol1 = {}
    try:
        with open(rutas["olla1"], encoding="utf-8") as f:
            ol1 = json.load(f)
    except Exception:
        ol1 = {}
    p1 = ol1.get("pasos", {}) if isinstance(ol1.get("pasos"), dict) else {}
    niveles = [("N1", p1.get("6", {}).get("estado", "en la primera olla")),
               ("N2", estado["pasos"].get("7", {}).get("estado", "PENDIENTE")),
               ("N3", "CERRADO" if (ol1.get("n3", {}) or {}).get("cerrado")
                else "en la primera olla"),
               ("N4", estado["pasos"].get("8", {}).get("estado", "PENDIENTE")),
               ("RUTA 0+N5", estado["pasos"].get("9", {}).get("estado", "PENDIENTE") +
                " / " + estado["pasos"].get("10", {}).get("estado", "PENDIENTE"))]
    lineas_inf.append("- CIERRE DE CAMPAÑA (los 5 niveles): " +
                      "; ".join("%s=%s" % (n, e) for n, e in niveles))
    lineas_inf.append("- duelo: %s" % motivo)
    _inf(rutas, "CIERRE DE CAMPAÑA — receta final certificada", lineas_inf)
    estado["pasos"]["10"]["estado"] = "CERRADO"
    estado["pasos"]["10"]["resumen"] = motivo + " | receta final escrita (" + \
        os.path.basename(backup) + ")"
    guardar_estado(rutas["estado"], estado)
    print(green(bold("  CAMPAÑA CERRADA: receta final certificada (brazo %s)."
                     % ganador["nombre"])))
    print(cyan("  el informe final vive en %s" % rutas["informe"]))
    return 0


# ============ MODO AUTO de la segunda mitad (boceto §1) ======================

PASOS_N4N5 = {"7": paso7, "8": paso8, "9": paso9, "10": paso10}
TITULOS_N4N5 = {"7": "N2 dosis re-aplicadas", "8": "N4 escalera VRAM",
                "9": "RUTA 0 build b11901", "10": "N5 duelo + receta final"}


def _prevuelo_auto(args, rutas, estado):
    """(fatales, avisos): lo que detiene el turno ANTES de cocinar — muere a
    los 5 s, no a las 2 h."""
    fatales, avisos = [], []
    cerrada, det = _primera_olla(rutas)
    if not cerrada:
        fatales.append("la primera olla (pasos 1..6) no esta cerrada: %s"
                       % "; ".join(det))
    if not os.path.exists(rutas["config"]):
        fatales.append("no hay config.txt en %s" % rutas["config"])
    else:
        cfg = leer_config(rutas["config"])
        srv = cfg.get("RUTA_SERVER", "")
        if not srv or not os.path.exists(srv):
            fatales.append("RUTA_SERVER no existe: %r" % srv)
        elif not os.path.exists(cfg.get("RUTA_MODELO", "")):
            fatales.append("RUTA_MODELO no existe: %r (el cuant que manda HOY)"
                           % cfg.get("RUTA_MODELO", ""))
    if health_ok(args.puerto):
        fatales.append("hay un server vivo en el puerto %d: para medir, el "
                       "rig debe estar quieto (apaga el charlatan primero)"
                       % args.puerto)
    if _vram_usada_mb() is None:
        avisos.append("nvidia-smi no respondio: los certificados de VRAM de "
                      "p8 saldran vacios (no bloquea)")
    libre, _total = gb_libres(rutas["base"])
    if libre is not None and libre < 4.0:
        avisos.append("disco con %.1f GB libres: los logs caben, pero justos"
                      % libre)
    return fatales, avisos


def modo_auto(args, rutas, estado):
    """DOBLE CLICK = MODO AUTO de la segunda mitad: corre P7..P10 en orden,
    sin preguntas. Hereda la disciplina de sus hermanas mayores:
    confirmaciones auto-aceptadas quedan escritas; puertas rojas DETIENEN
    el turno limpio (nunca se saltan solas, T9); re-doble-click retoma
    donde quedo."""
    AUTO["on"] = True
    AUTO["aceptadas"] = []
    if args.fuerza:
        print(yellow("  aviso: --fuerza no existe en AUTO (se ignora): las "
                     "puertas rojas mandan."))
        args.fuerza = False
    print(bold(cyan("\n=== MODO AUTO — la segunda mitad (pasos 7..10) ===")))
    print(cyan("  sin preguntas: confirmaciones auto-aceptadas y escritas."))
    cerrada, det = _primera_olla(rutas)
    if cerrada:
        print(green("  puerta de entrada: primera olla CERRADA. Se cocina."))
    else:
        print(red("  puerta de entrada: primera olla ABIERTA (%s)" % "; ".join(det)))
    mostrar_estado(rutas, estado)
    fatales, avisos = _prevuelo_auto(args, rutas, estado)
    resumen_prevuelo = ("OK" if not fatales and not avisos
                        else ("avisos: " + "; ".join(avisos) if avisos and not fatales
                              else "FATAL"))
    _inf(rutas, "MODO AUTO n4-n5 arrancado (la via activa N4 -> N5)",
         ["- pasos 7..10 en orden, sin preguntas; mundo propio "
          "(estado/informe/puerto propios)",
          "- puerta de entrada: primera olla %s" % ("CERRADA" if cerrada
                                                    else "ABIERTA: %s" % "; ".join(det)),
          "- prevuelo: %s" % resumen_prevuelo])
    for av in avisos:
        print(yellow("  aviso del prevuelo: %s" % av))
    if fatales:
        return _auto_detener(rutas, "el prevuelo encontro bloqueos (mejor "
                             "ahora que a media medicion)",
                             ["- %s" % f for f in fatales])
    try:
        for n in ("7", "8", "9", "10"):
            estado = leer_estado(rutas["estado"])   # re-lee estado en CADA vuelta
            est = estado["pasos"].get(n, {}).get("estado")
            if est in VERDES:
                print(cyan("\n  P%s ya estaba hecho (%s): se salta." % (n, est)))
                continue
            print(bold(cyan("\n--- P%s - %s ---" % (n, TITULOS_N4N5[n]))))
            rc = PASOS_N4N5[n](args, rutas, estado)
            _auto_informe_trail(rutas, "P%s" % n)
            if rc != 0:
                return _auto_detener(rutas, "P%s devolvio rc=%s (mira su "
                                     "salida arriba)" % (n, rc),
                                     ["- el paso no quedo verde; el "
                                      "re-doble-click retoma"])
        estado = leer_estado(rutas["estado"])
        hechos = [n for n in ("7", "8", "9", "10")
                  if estado["pasos"].get(n, {}).get("estado") in VERDES]
        _inf(rutas, "AUTO n4-n5 FIN DE TURNO: pasos 7..10 gestionados",
             ["- verdes ahora: %s" % (", ".join("P%s" % x for x in hechos)
                                      or "ninguno")])
        print(green(bold("\n  FIN DE TURNO AUTO: pasos 7..10 gestionados.")))
        print(green("  verdes: %s" % (", ".join("P%s" % x for x in hechos)
                                     or "ninguno")))
        print("  log completo : %s" % rutas["informe"])
        print("  estado       : %s" % rutas["estado"])
        return 0
    except SystemExit:
        return _auto_detener(rutas, "una puerta/freno del paso detuvo el "
                             "turno (mira el [FATAL] de arriba)",
                             ["- nada se salto: la puerta roja manda, "
                              "incluso en AUTO",
                              "- lo hecho quedo escrito; resuelve la causa "
                              "y re-doble-click"])
    except KeyboardInterrupt:
        _auto_informe_trail(rutas, "al interrumpirse")
        _inf(rutas, "AUTO n4-n5 INTERRUMPIDO (Ctrl+C)",
             ["- lo hecho queda escrito; re-doble-click retoma donde quedo"])
        print(yellow("\n[AUTO] interrumpido (Ctrl+C): lo hecho queda escrito."))
        return 130
    except Exception:
        import traceback
        traceback.print_exc()
        _auto_informe_trail(rutas, "al fallar")
        try:
            _inf(rutas, "AUTO n4-n5 INTERRUMPIDO (error inesperado)",
                 ["- el traceback completo quedo en consola; el turno se "
                  "detuvo con lo hecho escrito",
                  "- re-doble-click cuando resuelvas la causa"])
        except Exception:
            pass
        print(red("[AUTO] interrumpido por un error inesperado (causa arriba)."))
        return 1


def _auto_informe_trail(rutas, etiqueta):
    """Deja escritas en el informe las confirmaciones auto-aceptadas de este
    tramo (evidencia append-only; vacia el acumulador)."""
    if AUTO["aceptadas"]:
        _inf(rutas, "AUTO (%s): confirmaciones auto-aceptadas" % etiqueta,
             ["- %s" % x for x in AUTO["aceptadas"]])
        AUTO["aceptadas"] = []


def _auto_detener(rutas, causa, lineas):
    """Detencion LIMPIA del turno: todo lo hecho queda escrito y se explica
    la causa. Devuelve rc 2 (nunca se salta una puerta roja)."""
    _auto_informe_trail(rutas, "al detenerse")
    _inf(rutas, "AUTO n4-n5 DETENIDO: %s" % causa, lineas)
    print(red("\n[AUTO DETENIDO] %s" % causa))
    for ln in lineas:
        print(yellow("  %s" % ln))
    print(cyan("  lo hecho queda escrito. Re-doble-click cuando resuelvas "
               "la causa: todo retoma donde quedo."))
    return 2


# ---------------- main (CLI del boceto §1) -----------------------------------

def main():
    ap = argparse.ArgumentParser(description=VERSION)
    ap.add_argument("paso", nargs="?", default=None,
                    help="estado | plan | p7..p10 (sin argumento = MODO AUTO)")
    ap.add_argument("--dir", help="carpeta base de la campana (def: junto al script)")
    ap.add_argument("--config", help="ruta de config.txt (def: base/config.txt)")
    ap.add_argument("--puerto", type=int, default=PUERTO_DEF,
                    help="puerto propio de esta olla (def: %d)" % PUERTO_DEF)
    ap.add_argument("--corridas", type=int, default=CORRIDAS_DEF,
                    help="corridas por dosis (def: %d; mediana de 3 = regla)" % CORRIDAS_DEF)
    ap.add_argument("--m-prompts", type=int, default=M_PROMPTS_DEF,
                    help="prompts de medida por corrida (def: %d)" % M_PROMPTS_DEF)
    ap.add_argument("--archivo", help="p7/p8: tabla propia de candidatas/escalera")
    ap.add_argument("--previa", action="store_true",
                    help="p7/p8: mostrar las candidatas/peldanos sin arrancar servers")
    ap.add_argument("--sin-sanity", action="store_true",
                    help="p7: saltar el sanity tool-calling (queda escrito; T11: "
                         "el GO queda imposible, techo REGISTRADO)")
    ap.add_argument("--build-dir", help="p9: carpeta del build b11901 (def: "
                                        "junto a RUTA_SERVER, %s\\)" % BUILD_B11901)
    ap.add_argument("--fuerza", action="store_true",
                    help="saltar puertas A PROPOSITO (queda escrito; en AUTO no existe)")
    args = ap.parse_args()
    rutas = _rutas(args)
    estado = leer_estado(rutas["estado"])

    if args.paso is None:
        rc = modo_auto(args, rutas, estado)
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
    if paso in PASOS_N4N5:
        return PASOS_N4N5[paso](args, rutas, estado)
    print(red("paso desconocido: %s (usa estado | plan | p7..p10)" % args.paso))
    return 1


# ------------------------------------------------------------------ R65
# GUARDIAN DE HUELLA (herencia del guardian de la casa): auto-verificacion
# de huella propia, errores con causa visible y pausa garantizada al
# terminar o fallar. Este archivo es CAMPANA-N4-N5.py (hasta la ronda 67
# se llamo CAMPANA-6A10-v2.py; renombre por orden del Director "si ahora
# es n4 cambiale el titulo, no mezcles cosas"), la via activa N4 -> N5
# REAL DESDE EL BOCETO (ronda 65): hermano de CAMPANA.py v1.7.2
# (65D33CBA...DA4B1), CAMPANA-v2.py v2.0 (52996E67...B1E86) y de
# CAMPANA-6A10.py v1.0 (CFEADBEA...D1947), que quedan BYTE-INTACTAS.
# Mundo propio nuevo campana-n4-n5-* (desde r67 ya no compartido con la
# olla retirada); config.txt solo se toca en el cierre confirmado de P10
# (con backup y re-lectura de verificacion).

def _autoverifica_huella():
    """Anti-manipulacion: compara el SHA256 del propio archivo en disco
    contra el incrustado. La linea del SHA se excluye del calculo (se
    sustituye por un marcador construido POR PARTES: el literal completo
    no puede aparecer dos veces en el archivo) y TODO el resto del archivo
    cuenta byte a byte."""
    import hashlib
    try:
        marcador = b"@@AUTOCHEQUEO@@"
        linea_placeholder = b"SHA_AUTOCHEQUEO = \"" + marcador + b"\""
        conmigo = open(os.path.abspath(__file__), "rb").read()
        linea_sha = ('SHA_AUTOCHEQUEO = "%s"' % SHA_AUTOCHEQUEO).encode("utf-8")
        objeto = conmigo.replace(linea_sha, linea_placeholder)
        if objeto == conmigo:
            return False, "la huella incrustada no esta en el archivo (copia danada)"
        return (hashlib.sha256(objeto).hexdigest().upper() == SHA_AUTOCHEQUEO,
                "la huella del archivo en disco no coincide con la incrustada "
                "(se altero o se re-guardo con otro formato)")
    except Exception as exc:
        return False, "no se pudo leer el propio archivo: %r" % (exc,)


if __name__ == "__main__":
    rc = 2
    try:
        ok, causa = _autoverifica_huella()
        if not ok:
            print(red(bold("\n[FATAL] auto-verificacion de huella: %s" % causa)))
            print(red("         PARADA LIMPIA: no se ejecuta nada."))
            print(red("         Re-descarga CAMPANA-N4-N5.py del repo y "
                      "verifica su huella."))
            rc = 3
            _pausa_doble_click()  # FATAL de huella: ventana abierta SIEMPRE
        else:
            rc = main()  # el piloto ya pausa el doble click al terminar AUTO
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) \
            else (0 if exc.code is None else 1)
        if isinstance(exc.code, str) and exc.code.strip():
            print("[FATAL] %s" % exc.code)
        _pausa_doble_click()  # sys.exit inesperado: la causa queda visible
    except KeyboardInterrupt:
        print(red("\n[PARADO] Ctrl+C: lo hecho queda guardado en el informe."))
        rc = 130
        _pausa_doble_click()
    except Exception:
        import traceback
        traceback.print_exc()
        print(red("\n[FATAL] error inesperado de Python (arriba esta la causa)."))
        rc = 1
        _pausa_doble_click()
    sys.exit(rc)
