#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
campana-n4.py v1.0 — NIVEL 4: MEMORIA (VRAM/RAM) Y BALANCE DE RECURSOS
=====================================================================
Encargo del Director (31-oct-2026): "bien, ahora si, crea el archivo
python puro real, siguiendo la guia del pseudocodigo" (r65) + "vamos
por orden, el archivo debe ser solo campana n4, este nivel 4
mencionado previamente el tema ram y cosas del estilo lo en un archivo
todas las pruebas y logs necesarios antibugs anti malware" (r68): UNA
olla POR NIVEL, con su bateria, sus logs, sus trampas anti-bugs y su
huella anti-tamper. Este archivo es SOLO el NIVEL 4 (el tema RAM y
recursos del encargo R60: "memoria vram ram, analizar como gestionar
la ram y balancear los recursos del modelo para que no se realentice
por falta de recursos"): transcripcion EJECUTABLE de la parte del
boceto que le corresponde (pseudocodigo/boceto-ronda-completa-p7-p10.md,
nacido en la ronda 62, auditado r63 (F1-F12) y re-auditado r64
(F13-F24)): el plano ya paso sus dos auditorias, este es el edificio.
La ruta se gobierna por NIVELES desde la ronda 66 (apendice R66); los
nombres de subcomando quedan como MECANISMO, no como mapa:

  P7   la rampa RAM del NIVEL 4: re-ancla + candidatas de dosis fina
       (CTXCP4 libera ~1.5-1.8 GB de RAM — el "tema ram" literal; la
       leccion R32 manda: las promesas de RAM SE MIDEN, no se creen)
       + sanity con anclas (sin sanity el GO queda imposible, techo
       REGISTRADO, T11). Criterio de salida: >= +8% t/s con calidad
       intacta; si no llega, se REGISTRA y se decide con datos. La
       dosis N2 del mapa viejo quedo fuera de la ruta critica (R59:
       el cuant ya cerro); aqui vive como rampa y puerta de P8.
  P8   el cuerpo del NIVEL 4: escalera de VRAM (peldanos NCM primero,
       MEC dosis fina en MiB), certificados por arranque (nvidia-smi
       <= 3712 MB, pageouts ~= 0 = el "no se realentice por falta de
       recursos" literal) y regla cliff-1 automatica. Las dosis VRAM
       NO transfieren entre cuants: se miden UNA vez aqui.

NO vive aqui el N5 (RUTA 0 + duelo spec vs NP2 + receta final): vamos
por orden — nacera en SU archivo CAMPANA-N5.py cuando el Director lo
ordene. Su material queda vivo en tres sitios: los bloques p9/p10 de
CAMPANA-6A10.py byte-intacta, el git history de esta familia y el
boceto §4/§5. NADA se pierde.

FAMILIA (regla del Director, r50: "crear otro, NO borrar el antiguo"):
  CAMPANA.py v1.7.2 (65D33CBA...DA4B1) y CAMPANA-v2.py v2.0 (52996E67...)
  cocinan los pasos 1..6; CAMPANA-6A10.py v1.0 (CFEADBEA...D1947) es la
  olla original de la que nacio este archivo (CAMPANA-6A10-v2.py r65 ->
  CAMPANA-N4-N5.py r67 -> CAMPANA-N4.py r68). Este archivo es su
  HERMANO:
  - NO borra, NO pisa y NO re-escribe NINGUNA de las tres ollas mayores:
    las tres quedan BYTE-INTACTAS y este archivo nace aparte.
  - MUNDO PROPIO NUEVO (r67, orden del Director "si ahora es n4
    cambiale el titulo, no mezcles cosas"; r68 lo acota al nivel:
    "el archivo debe ser solo campana n4"): campana-n4-estado.json +
    campana-n4-INFORME.md append-only + carpetas campana-n4-p7../p8 +
    puerto propio 9932. Cada seccion del informe que escribe esta
    olla lleva la linea "- script: CAMPANA-N4.py" (evidencia clara de
    quien escribio que).

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
  D2. Impresiones honestas: las mediciones anuncian "mediana de N
      corridas x M prompts" (la olla original decia "1 corrida" y
      corria MED3: cosmético F11 de la auditoria r63; la CONDUCTA MED3
      es identica), al generar las tablas se muestran los avisos de la
      derivacion y el informe de P8 anota el HUECO para el draft (N5)
      como dato (4096 - VRAM del ganador; criterio de salida del N4,
      plan R61).
  D3. Las secciones del informe llevan la linea "- script:" (ver
      arriba). Nada mas.
  R68. Alcance N4 puro ("vamos por orden"): los bloques p9/p10 de la
      olla original NO viven aqui (el N5 nacera en SU archivo
      CAMPANA-N5.py). Consecuencia de casa: esta olla NO escribe
      config.txt NUNCA (la receta final era del cierre de P10/N5 y
      vive fuera).

REGLAS que el script hace cumplir (las de la casa; las trampas T1-T18
del boceto §7 viven incrustadas donde corresponden):
  - PUERTA: p8 exige p7 verde (o --fuerza, que la salta A PROPOSITO y
    lo deja escrito en el informe). En MODO AUTO no existe fuerza: una
    puerta roja DETIENE el turno limpio (rc 2). [T9]
  - config.txt: NINGUN paso de esta olla escribe en el (diferencia con
    la olla original: la receta final era del cierre de P10/N5 y vive
    fuera, r68). [T8] SAMPLING, RUTA_* y el cuant NUNCA se tocan
    (RUTA_MODELO manda).
  - el informe (campana-n4-INFORME.md) es APPEND-ONLY: cada accion
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
  - HUELLA (anti-tamper): auto-verificacion de huella propia al
    arranque (manipulacion -> parada limpia, rc 3), herencia del
    guardian de la casa. [tabla de rc: 0 verde, 2 puerta/fatal/dudoso/
    falla, 1 excepcion, 130 Ctrl+C, 3 huella manipulada]
  - DOBLE CLICK = MODO AUTO: corre P7..P8 en orden (el NIVEL 4), sin
    preguntas; las confirmaciones se auto-aceptan y quedan escritas;
    re-doble-click retoma donde quedo. --ofrecer no existe aqui: foto
    con `estado`. [T9: en AUTO --fuerza se ignora con aviso]

Todo vive junto al script (en el rig: D:\\ZLia). --dir cambia la base
y --config la receta. Cero toques a CAMPANA.py, CAMPANA-v2.py,
CAMPANA-6A10.py, config.txt ni a la evidencia de la primera olla. Si
este archivo y una olla byte-intacta se pelearan en el futuro, manda
el byte-intacto (boceto §0).
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

VERSION = ("campana-n4 v1.0 NIVEL 4: MEMORIA (VRAM/RAM) Y RECURSOS "
           "(2026-10-31, ronda 65: pedido del Director 'crea el archivo "
           "python puro real, siguiendo la guia del pseudocodigo'; "
           "ronda 67: renombrada CAMPANA-6A10-v2.py -> CAMPANA-N4-N5.py "
           "('si ahora es n4 cambiale el titulo, no mezcles cosas'); "
           "ronda 68: recorte por orden del Director 'vamos por orden, "
           "el archivo debe ser solo campana n4' — UNA olla POR NIVEL: "
           "solo P7 (rampa RAM) y P8 (escalera VRAM) viven aqui, el N5 "
           "(p9/p10) nacera en SU archivo CAMPANA-N5.py; transcripcion "
           "ejecutable del boceto r62 auditado r63/r64; CAMPANA.py "
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
SHA_AUTOCHEQUEO = "5F24E8CF369DBF393672EFE8F7ABF69860FF96BA566A5BE62A77AC6B6EE87ED1"

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
# El spot POR CORRIDA (F7) es capacidad del motor de medición: un brazo
# queda elegible solo con spot limpio en TODAS sus corridas (uso
# previsto: el duelo del N5, en su propio archivo — vamos por orden).
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
        "estado": os.path.join(base, "campana-n4-estado.json"),
        "informe": os.path.join(base, "campana-n4-INFORME.md"),
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
                if not isinstance(datos["pasos"], dict):
                    datos["pasos"] = {}
                return datos
        except Exception:
            # un estado corrupto NO se descarta en silencio (herencia r50,
            # F10): queda .corrupto-<ts> como evidencia y arranca limpio.
            try:
                _podrido = "%s.corrupto-%s" % (
                    ruta_estado,
                    datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
                os.replace(ruta_estado, _podrido)
                print(yellow("  aviso: campana-n4-estado.json ilegible; "
                             "evidencia guardada en %s" % os.path.basename(_podrido)))
            except Exception:
                pass
    return {"version": VERSION, "actualizado": "", "pasos": {}}


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
                   ["- script: CAMPANA-N4.py v1.0 (NIVEL 4, real desde el "
                    "boceto; r65/r67/r68)"] + list(lineas))


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
    print(bold(cyan("\n=== CAMPANA-N4 (NIVEL 4: memoria VRAM/RAM y "
                    "recursos) — %s ==="
                    % (estado.get("actualizado") or "sin empezar"))))
    print("  informe append-only: %s" % rutas["informe"])
    cerrada, det = _primera_olla(rutas)
    print("  puerta de entrada — primera olla: %s"
          % (green("CERRADA (se puede cocinar)") if cerrada
             else red("AUN ABIERTA (corre primero CAMPANA.py del 1 al 6)")))
    for d in det:
        print("    %s" % gray("- " + d))
    tabla = [("7", "rampa RAM: re-ancla + dosis fina (CTXCP4) + sanity"),
             ("8", "N4 escalera de VRAM (cliff-1) + certificados")]
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
    flog.write("===== server de campana-n4 %s (puerto %d) =====\n"
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

ARCHIVO_P7 = "campana-n4-p7-candidatas.txt"


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
    carpeta = os.path.join(rutas["base"], "campana-n4-p7")
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

ARCHIVO_P8 = "campana-n4-p8-escalera.txt"


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
    carpeta = os.path.join(rutas["base"], "campana-n4-p8")
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
    lineas_inf.append("- HUECO para el draft (N5, dato): hueco = 4096 - VRAM(ganador); "
                      "si la frontera es NCM37 -> ~901 MB (el nextn 858 cabe "
                      "sin margen); si es NCM36 -> ~572 MB (no cabe: -cmoed o "
                      "bajar una capa)")
    _inf(rutas, "P8 escalera VRAM -> %s" % est_p8, lineas_inf)
    print(green(bold("  P8 -> %s: %s" % (est_p8, resumen))))
    return 0 if est_p8 in ("GO", "REGISTRADO") else 2




# ============ MODO AUTO del NIVEL 4 (boceto §1) ==============================

PASOS_N4 = {"7": paso7, "8": paso8}
TITULOS_N4 = {"7": "rampa RAM (re-ancla + dosis fina + sanity)",
              "8": "N4 escalera de VRAM"}


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
    """DOBLE CLICK = MODO AUTO del NIVEL 4: corre P7..P8 en orden,
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
    print(bold(cyan("\n=== MODO AUTO — NIVEL 4 (pasos 7..8) ===")))
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
    _inf(rutas, "MODO AUTO n4 arrancado (el NIVEL 4: memoria VRAM/RAM y "
                "recursos)",
         ["- pasos 7..8 en orden, sin preguntas; mundo propio "
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
        for n in ("7", "8"):
            estado = leer_estado(rutas["estado"])   # re-lee estado en CADA vuelta
            est = estado["pasos"].get(n, {}).get("estado")
            if est in VERDES:
                print(cyan("\n  P%s ya estaba hecho (%s): se salta." % (n, est)))
                continue
            print(bold(cyan("\n--- P%s - %s ---" % (n, TITULOS_N4[n]))))
            rc = PASOS_N4[n](args, rutas, estado)
            _auto_informe_trail(rutas, "P%s" % n)
            if rc != 0:
                return _auto_detener(rutas, "P%s devolvio rc=%s (mira su "
                                     "salida arriba)" % (n, rc),
                                     ["- el paso no quedo verde; el "
                                      "re-doble-click retoma"])
        estado = leer_estado(rutas["estado"])
        hechos = [n for n in ("7", "8")
                  if estado["pasos"].get(n, {}).get("estado") in VERDES]
        _inf(rutas, "AUTO n4 FIN DE TURNO: pasos 7..8 gestionados",
             ["- verdes ahora: %s" % (", ".join("P%s" % x for x in hechos)
                                      or "ninguno")])
        print(green(bold("\n  FIN DE TURNO AUTO: pasos 7..8 gestionados.")))
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
        _inf(rutas, "AUTO n4 INTERRUMPIDO (Ctrl+C)",
             ["- lo hecho queda escrito; re-doble-click retoma donde quedo"])
        print(yellow("\n[AUTO] interrumpido (Ctrl+C): lo hecho queda escrito."))
        return 130
    except Exception:
        import traceback
        traceback.print_exc()
        _auto_informe_trail(rutas, "al fallar")
        try:
            _inf(rutas, "AUTO n4 INTERRUMPIDO (error inesperado)",
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
    _inf(rutas, "AUTO n4 DETENIDO: %s" % causa, lineas)
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
                    help="estado | plan | p7..p8 (sin argumento = MODO AUTO)")
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
        print(gray("  detalle completo: plan-p8-n4-experimentos.md (R61) + "
                   "nivel-4-memoria-vram-ram.md en el repo"))
        return 0
    if paso in PASOS_N4:
        return PASOS_N4[paso](args, rutas, estado)
    if paso in ("9", "10"):
        print(red("paso %s = N5: NO vive aqui (vamos por orden: UNA olla "
                  "por nivel). El N5 nacera en SU archivo CAMPANA-N5.py "
                  "cuando el Director lo ordene; su material esta vivo en "
                  "CAMPANA-6A10.py byte-intacta, el git history y el "
                  "boceto §4/§5." % args.paso))
        return 1
    print(red("paso desconocido: %s (usa estado | plan | p7..p8)" % args.paso))
    return 1


# ------------------------------------------------------------------ R65
# GUARDIAN DE HUELLA (herencia del guardian de la casa): auto-verificacion
# de huella propia, errores con causa visible y pausa garantizada al
# terminar o fallar. Este archivo es CAMPANA-N4.py (historia: nacio
# CAMPANA-6A10-v2.py en la ronda 65, renombrado CAMPANA-N4-N5.py en la
# ronda 67 y CAMPANA-N4.py en la ronda 68 por orden del Director "vamos
# por orden, el archivo debe ser solo campana n4"), el NIVEL 4
# (memoria VRAM/RAM y recursos): hermano de CAMPANA.py v1.7.2
# (65D33CBA...DA4B1), CAMPANA-v2.py v2.0 (52996E67...B1E86) y de
# CAMPANA-6A10.py v1.0 (CFEADBEA...D1947), que quedan BYTE-INTACTAS.
# Mundo propio campana-n4-*; esta olla NO escribe config.txt NUNCA (la
# receta final es del N5, en su archivo cuando llegue).

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
            print(red("         Re-descarga CAMPANA-N4.py del repo y "
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
