#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
diagnostico-velocidad.py v1.1 — el mecanico: ¿va a los t/s que debe?
====================================================================
Pregunta del Director (ronda 25): "crea un nuevo .py que sea diagnostico,
deberia ir a mas t/s con la receta completa".

Doble click en DIAGNOSTICO-VELOCIDAD.bat (con el server YA abierto) y responde
en 4 estaciones, con la honestidad de la casa (nada inventado):

  ESTACION 1 — CERTIFICADO DE LA RECETA VIVA: lee la linea de comandos REAL
     del proceso llama-server.exe (PowerShell) y la compara pieza por pieza
     con la receta original reconstruida desde config.txt. BONUS que resuelve
     el hueco SS23-B1: el --override-kv del comando vivo CERTIFICA los
     expertos con los que se abrio (sin override = 8, default de fabrica).
  ESTACION 2 — MEDICION AL ESTILO DEL LABORATORIO (protocolo SS8 VERBATIM del
     barrido): 4 pasadas x 256 tokens, temp 0, seed 424242, cache_prompt,
     se descarta la 1a, decode = media de las pasadas 2-4, los MISMOS 4
     prompts del barrido -> un numero COMPARABLE 1:1 con 17.80 / 21.53 /
     28.85. Este es el reloj INTERNO del server (el numero del chat es reloj
     de pared y sale mas bajo por las pausas del dia).
  ESTACION 3 — GUARDARRAILS DEL DIA: RAM libre (riesgo pagefile, el modelo
     ocupa 14.27 de 16 GB), GPU (temperatura, relojes vs maximo = throttle),
     plan de energia de Windows (GUID Equilibrado = recorta relojes).
  ESTACION 4 — EL VEREDICTO ("¿deberia ir a mas?"): el numero medido contra
     los rangos [M] del laboratorio + culpables concretos si va bajo.
     Rangos [M]: k=8 = 17.4-21.5 (suelo D-EXP10-CTRL 17.36, techo ORO-UB1K
     21.53, ruido +/-0.5 SS8); k=4 = 24-30 (28.85 D-EXP4 / 29.13 D-EXP4-UB1K,
     una sola sesion medida -> banda generosa) con zona gris 22.0-24.0.

QUE NO HACE: no lanza ni toca el server (solo lee /health, /props, /completion
y la linea de comandos del proceso), no cambia configs, no usa flags nuevas
(cero auditoria de dump necesaria), no chatea.
IMPORTANTE: NO chatear mientras mide (~1 min) — un turno del chat falsea todo.

Salida: consola + informe en RUTA_LOGS (default D:\ZLia\faseD-logs):
  diagnostico-AAAAMMDD-HHMMSS.md

Requisitos: Python 3.8+ solo stdlib. Las piezas de Windows (PowerShell,
GlobalMemoryStatusEx, powercfg, nvidia-smi) se saltan solas con nota si no
estan disponibles — el diagnostico NUNCA muere por una pieza ausente.

v1.1 (ronda 26, pedido del Director: "refinalo corrigue bugs, recuerdo que
a solo flags iba a 21 t/s minimo 8 cocineros"):
  - EL RECUERDO DEL DIRECTOR AHORA VIVE EN EL VEREDICTO, y es DATO
    CERTIFICADO: el sweep del 25-oct (informe-velocidad-sweep.md §11.1)
    midio la familia de flags SOLA a BASE 20.85 y LMNONE 21.50 (la receta de
    HOY lleva -lm none => su numero del sweep es 21.50), y ORO-UB1K 21.53
    (barrido-30). Ese "21 minimo" era el TECHO de los dias buenos, no el
    suelo (suelo certificado: 17.36, D-EXP10-CTRL). El veredicto NORMAL-K8
    lo dice ahora y separa dias buenos (>=20.5) de dias lentos dentro del
    rango.
  - BUGS corregidos: (a) si config.txt dice un puerto y el server vivo corre
    en OTRO (puerto editado despues de abrir), el diagnostico se negaba a
    diagnosticar ("No hay server") — ahora lee el puerto del comando vivo,
    lo comprueba con /health y diagnostica contra el VIVO con un AVISO;
    (b) con VARIOS procesos llama-server.exe (zombie de una sesion anterior)
    se comparaba solo el primero — ahora se comparan TODOS y gana el que
    coincide; (c) rutas de Windows con distinto CASE (D:\ vs d:\) daban "sin
    match" falso — las rutas (exe y modelo) se normalizan antes de comparar;
    las FLAGS no se tocan (son case-sensitivas); (d) si el exe no se llama
    llama-server.exe (RUTA_SERVER con otro nombre), la busqueda del proceso
    se repite con ese nombre; (e) salida blindada contra la codepage de la
    consola de Windows (errors=replace): un caracter no imprimible NUNCA
    mata el informe a medio escribir.
  - Bateria: el T06 tenia un `or` que volvia valida casi cualquier cosa —
    endurecido a igualdad exacta. Nuevos: T12d-f (recuerdo en veredicto),
    T15 (puerto del vivo), T16 (CASE de rutas), T17 (multi-proceso).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime

CONFIG_OFICIAL = r"D:\ZLia\config.txt"
ALIAS = "apex35b"
KEYS = ("RUTA_SERVER", "RUTA_MODELO", "RUTA_LOGS", "PUERTO",
        "EXPERTOS_TRABAJO", "EXPERTOS_CHARLA",
        "FLAGS_BASE", "SAMPLING", "FLAGS_GANADORAS")
HOST_DEF = "127.0.0.1"

# --- rangos [M] del laboratorio (barrido-30 + faseD v1.2 real, ruido +/-0.5) -
BAJO_DESDE = 16.9      # < suelo k=8 (17.36) - ruido  -> va mas lento de lo que debe
NORMAL_HASTA = 22.0    # <= techo k=8 (21.53) + ruido -> en rango k=8
K4_DESDE = 24.0        # >= banda k=4 (28.85/29.13 con banda generosa)

# --- referencias [M] CERTIFICADAS de la casa (todas medidas, cero invento) --
SWEEP_BASE = 20.85     # sweep 25-oct §11.1 #6: familia de flags SOLA (sin -lm none)
SWEEP_LMNONE = 21.50   # sweep 25-oct §11.1 #1: LA RECETA DE HOY (base + -lm none)
ORO_UB1K = 21.53       # barrido-30 id 32: receta + FLAGS_GANADORAS
FASED_FLOOR = 17.36    # faseD v1.2 D-EXP10-CTRL: suelo certificado k=8
FASED_ANCLA = 17.80    # faseD v1.2 D-ANCLA
DIA_BUENO_DESDE = 20.5  # >= esto = los dias ~21 certificados. El recuerdo del
# Director ("a solo flags iba a 21 t/s minimo, 8 cocineros") ES ese techo:
# LMNONE 21.50 [M] — el 21 es el TECHO de la familia, no el suelo.

# GUID del plan "Equilibrado" de Windows (documentado por Microsoft; se busca
# el GUID, no el nombre, para que funcione en Windows en cualquier idioma).
GUID_EQUILIBRADO = "381b4222-f694-41f0-9685-ff5bb260df2e"

# Los MISMOS 4 prompts del laboratorio (PROMPTS_MEDICION de
# barrido-n1-expertos.py, verbatim): misma familia, ~misma longitud.
PROMPTS_MEDICION = [
    "Describe en un parrafo como funciona una bicicleta: pedales, cadena y "
    "ruedas. Incluye un consejo basico de mantenimiento.",
    "Explica en un parrafo por que el cielo es azul durante el dia y rojo al "
    "atardecer, con palabras simples.",
    "Resume en un parrafo la historia de la imprenta de Gutenberg y por que "
    "cambio el mundo.",
    "Explica en un parrafo que es la fotosintesis: que entra en la hoja, que "
    "sale y por que importa, en palabras simples.",
]

USE_COLOR = False
try:
    USE_COLOR = sys.stdout.isatty()
except Exception:
    USE_COLOR = False


def _c(txt, code):
    if not USE_COLOR:
        return str(txt)
    return "\x1b[%sm%s\x1b[0m" % (code, txt)


def verde(t):
    return _c(t, "92")


def ambar(t):
    return _c(t, "33")


def rojo(t):
    return _c(t, "91")


def cia(t):
    return _c(t, "96")


# ------------------------------- config --------------------------------------
def encontrar_config():
    r"""Mismo orden que abrir-qwen-apex.py (post-reorden): env CONFIG_TXT ->
    D:\ZLia\config.txt -> junto a este script -> ../configs/ del repo."""
    candidatas = []
    if os.environ.get("CONFIG_TXT"):
        candidatas.append(os.environ["CONFIG_TXT"])
    candidatas.append(CONFIG_OFICIAL)
    _dir = os.path.dirname(os.path.abspath(__file__))
    candidatas.append(os.path.join(_dir, "config.txt"))
    candidatas.append(os.path.join(_dir, "..", "configs", "config.txt"))
    for c in candidatas:
        if c and os.path.exists(c):
            return c
    return None


def parsear_config(ruta):
    """clave = valor -> dict. Ignora comentarios (#) y lineas vacias."""
    cfg = {}
    with open(ruta, "r", encoding="utf-8", errors="replace") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            cfg[clave.strip()] = valor.strip()
    return cfg


def construir_esperado(cfg, perfil):
    """La receta original de la casa, reconstruida desde config.txt EXACTAMENTE
    como la arma abrir-qwen-apex.py v3.0 (mismo orden, last-wins al final)."""
    k = int(cfg.get("EXPERTOS_CHARLA", "4") if perfil == "charla"
            else cfg.get("EXPERTOS_TRABAJO", "8"))
    cmd = [cfg["RUTA_SERVER"], "-m", cfg["RUTA_MODELO"], "-a", ALIAS]
    cmd += cfg.get("FLAGS_BASE", "").split()
    if k != 8:
        cmd += ["--override-kv", "qwen35moe.expert_used_count=int:%d" % k]
    cmd += cfg.get("SAMPLING", "").split()
    cmd += cfg.get("FLAGS_GANADORAS", "").split()
    cmd += ["--host", HOST_DEF, "--port", cfg.get("PUERTO", "9931")]
    return cmd, k


# ------------------- certificado de la receta viva (Win) ---------------------
def _cmdline_por_nombre(nombre_proceso):
    """Linea de comandos de los procesos con ESE nombre via PowerShell
    (Get-CimInstance). Devuelve (lista_de_lineas, nota); (None, nota) si no
    hay procesos o la pieza no esta disponible (no-Windows / PowerShell
    fallo). NUNCA lanza excepciones hacia arriba."""
    if os.name != "nt":
        return None, "certificado de linea de comandos solo en Windows"
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='%s'\""
          " | Select-Object -ExpandProperty CommandLine" % nombre_proceso)
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=30)
    except Exception as e:
        return None, "no pude llamar a PowerShell (%s)" % e
    if r.returncode != 0:
        return None, "PowerShell devolvio error %s" % r.returncode
    lineas = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    if not lineas:
        return None, ("ningun proceso %s visible (¿otra ventana?)"
                      % nombre_proceso)
    return lineas, "%d proceso(s) %s encontrados" % (len(lineas),
                                                     nombre_proceso)


def cmdline_viva():
    """Linea de comandos REAL del/los proceso(s) llama-server.exe. Wrapper SIN
    argumentos (los tests la sustituyen con lambdas); la busqueda por otro
    nombre de exe vive en certificar_receta."""
    return _cmdline_por_nombre("llama-server.exe")


def _tokens(linea):
    """Divide una linea de comandos en tokens (respetando comillas simples)."""
    fuera, actual, en_comillas = [], "", False
    for ch in linea:
        if ch == '"':
            en_comillas = not en_comillas
        elif ch == " " and not en_comillas:
            if actual:
                fuera.append(actual)
            actual = ""
        else:
            actual += ch
    if actual:
        fuera.append(actual)
    return fuera


def k_de_cmdline(tokens):
    """Expertos VIVOS segun el comando: el override dice el k con el que se
    abrio el server (SS23-B1 resuelto por la puerta de atras honesta).
    Sin override = 8 (default de fabrica). None = comando raro."""
    for i, t in enumerate(tokens):
        if t == "--override-kv" and i + 1 < len(tokens):
            m = re.search(r"expert_used_count=int:(\d+)", tokens[i + 1])
            if m:
                return int(m.group(1))
            return None
    return 8


def puerto_de_tokens(tokens):
    """El puerto del comando vivo (el token que sigue a --port). None si la
    linea no lo declara."""
    for i, t in enumerate(tokens):
        if t == "--port" and i + 1 < len(tokens):
            return tokens[i + 1]
    return None


def _normcase_ruta(p):
    """Normaliza una RUTA para compararla: en Windows el caso no importa
    (D:\\ZLia y d:\\zlia son la misma) y el comando vivo llega con el caso
    que sea. En POSIX solo pasa a minusculas, para que los tests con lineas
    falsas se comporten igual que en el rig."""
    try:
        p = os.path.normcase(p)
    except Exception:
        pass
    return p.lower()


def normalizar_tokens(tokens):
    """Copia de los tokens con SOLO las rutas normalizadas (posicion 0 = exe,
    y el token que sigue a -m = modelo). Las FLAGS NO se tocan: son
    case-sensitivas y ahi vive el last-wins de -ub/-b."""
    t2 = list(tokens)
    if t2:
        t2[0] = _normcase_ruta(t2[0])
    for i, t in enumerate(t2):
        if t == "-m" and i + 1 < len(t2):
            t2[i + 1] = _normcase_ruta(t2[i + 1])
    return t2


def health_ok(puerto, timeout=4):
    """¿Responde /health en ese puerto? (un 503 de carga cuenta como no
    listo, que es lo honesto mientras el modelo entra)."""
    try:
        with urllib.request.urlopen(
                "http://%s:%s/health" % (HOST_DEF, puerto),
                timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def diferenciar_receta(vivo, esperado):
    """Compara DOS listas de tokens como multiset (orden y repeticiones
    importan: -ub 256 ... -ub 1024 es distinto de solo uno). Devuelve
    (faltan, sobran): FALTAN = tokens que la receta esperada tiene y el vivo
    no; SOBRAN = tokens que el vivo tiene y la receta no."""
    cf, cs = Counter(vivo), Counter(esperado)
    faltan = sorted((cs - cf).elements())
    sobran = sorted((cf - cs).elements())
    return faltan, sobran


def certificar_receta(cfg, lineas=None):
    """Estacion 1 completa. Devuelve dict con: k_vivo, match ('trabajo' |
    'charla' | None), faltan, sobran, nota. Nunca lanza excepciones.
    lineas: lineas de comandos vivas ya leidas (main/tests); None = leer aqui.
    Con VARIOS procesos vivos (zombies incluidos) se comparan TODOS y gana
    el de menos diferencias; el match exacto corta al instante."""
    res = {"k_vivo": None, "match": None, "k_esperado": None,
           "faltan": [], "sobran": [], "nota": ""}
    if lineas is None:
        lineas, nota = cmdline_viva()
        res["nota"] = nota
    else:
        res["nota"] = "%d linea(s) de comando inyectadas" % len(lineas)
    if not lineas:
        # Ultima chance honesta: el exe puede no llamarse llama-server.exe
        nombre = os.path.basename((cfg.get("RUTA_SERVER") or "").strip())
        if nombre and nombre.lower() != "llama-server.exe" and os.name == "nt":
            lineas, nota = _cmdline_por_nombre(nombre)
            res["nota"] = "%s (buscado por RUTA_SERVER: %s)" % (nota, nombre)
    if not lineas:
        return res
    esperadas = []
    for nombre in ("trabajo", "charla"):
        try:
            esp, _k = construir_esperado(cfg, nombre)
        except Exception:
            continue
        esperadas.append((nombre, _k, normalizar_tokens(esp)))
    if not esperadas:
        return res
    mejor = None
    for linea in lineas:
        vivo = normalizar_tokens(_tokens(linea))
        k_vivo = k_de_cmdline(vivo)
        for nombre, _k, esp in esperadas:
            faltan, sobran = diferenciar_receta(vivo, esp)
            total = len(faltan) + len(sobran)
            if total == 0:
                res["match"] = nombre
                res["k_vivo"] = k_vivo
                res["k_esperado"] = _k
                res["faltan"] = []
                res["sobran"] = []
                return res
            if mejor is None or total < mejor["_total"]:
                mejor = {"k_vivo": k_vivo, "k_esperado": _k,
                         "faltan": faltan, "sobran": sobran,
                         "_total": total}
    if mejor:
        res["k_vivo"] = mejor["k_vivo"]
        res["k_esperado"] = mejor["k_esperado"]
        res["faltan"] = mejor["faltan"]
        res["sobran"] = mejor["sobran"]
    return res

# ---------------- estacion 2: medicion estilo laboratorio --------------------
def _post_json(url, cuerpo, timeout=600):
    req = urllib.request.Request(
        url, data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        cuerpo_err = ""
        try:
            cuerpo_err = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        raise RuntimeError("HTTP %s: %s" % (e.code, cuerpo_err))
    except Exception as e:
        raise RuntimeError("conexion: %s" % e)


def pasadas_medicion(puerto, prompts, n_predict=256, seed=424242,
                     timeout=600):
    """VERBATIM del protocolo del barrido (SS8): 4 pasadas x n_predict.
    Prefill = pasada 1 fria (prompt_per_second); decode = media de las
    pasadas 2-4 (predicted_per_second). Devuelve (prefill_ts, decode_ts,
    detalle). Usa el reloj INTERNO del server -> comparable 1:1 con el lab."""
    url = "http://%s:%s/completion" % (HOST_DEF, puerto)
    prefill = None
    decs = []
    detalle = []
    for i, p in enumerate(prompts):
        cuerpo = {
            "prompt": p, "n_predict": n_predict, "temperature": 0.0,
            "seed": seed, "cache_prompt": True, "ignore_eos": True,
            "stream": False,
        }
        d = _post_json(url, cuerpo, timeout=timeout)
        t = d.get("timings", {}) or {}
        pf = t.get("prompt_per_second")
        dec = t.get("predicted_per_second")
        pn = t.get("predicted_n")
        detalle.append({"pasada": i + 1, "prompt_per_second": pf,
                        "predicted_per_second": dec, "predicted_n": pn})
        if i == 0:
            prefill = pf
        else:
            decs.append(dec)
    dec_final = (sum(decs) / len(decs)) if decs and all(
        v is not None for v in decs) else None
    return prefill, dec_final, detalle


# ---------------- estacion 3: guardarrails del dia ---------------------------
def ram_status():
    """RAM del sistema (Windows: GlobalMemoryStatusEx). None si no disponible."""
    if os.name != "nt":
        return None
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        st = MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            return None
        return {"carga_pct": int(st.dwMemoryLoad),
                "libre_gb": round(st.ullAvailPhys / 1024 ** 3, 2),
                "total_gb": round(st.ullTotalPhys / 1024 ** 3, 2)}
    except Exception:
        return None


def parsear_gpu_csv(salida):
    """Parsea la linea CSV de nvidia-smi (nounits) -> dict. Tolerante a N/A."""
    if not salida:
        return None
    partes = [p.strip() for p in salida.strip().splitlines()[0].split(",")]
    if len(partes) < 8:
        return None

    def num(s):
        try:
            return float(s)
        except ValueError:
            return None

    claves = ("temp_c", "util_pct", "mem_usada_mib", "mem_total_mib",
              "reloj_mhz", "reloj_max_mhz", "watts", "watts_max")
    d = dict(zip(claves, (num(p) for p in partes)))
    return d if any(v is not None for v in d.values()) else None


def gpu_status():
    """nvidia-smi best-effort: temperatura, util, VRAM, relojes vs maximo."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        r = subprocess.run(
            [exe, "--query-gpu=temperature.gpu,utilization.gpu,"
                  "memory.used,memory.total,clocks.current.graphics,"
                  "clocks.max.graphics,power.draw,power.limit",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return parsear_gpu_csv(r.stdout or "")


def plan_energia():
    """Plan activo de Windows (powercfg). Flag por GUID (idioma-independiente)."""
    if os.name != "nt":
        return None
    try:
        r = subprocess.run(["powercfg", "/getactivescheme"],
                           capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    texto = (r.stdout or "").strip()
    return {"texto": texto, "equilibrado": GUID_EQUILIBRADO in texto.lower()}


def culpritos(ram, gpu, plan):
    """Culpables concretos de un dia lento, con umbrales de la casa.
    Devuelve lista de strings (vacía = sin culpables claros)."""
    out = []
    if ram:
        if ram["libre_gb"] < 1.5 or ram["carga_pct"] >= 95:
            out.append("RAM al limite: %.2f GB libres (%d%% en uso) — "
                       "riesgo pagefile con un modelo de 14.27 GB"
                       % (ram["libre_gb"], ram["carga_pct"]))
    if gpu:
        if gpu.get("temp_c") is not None and gpu["temp_c"] >= 80:
            out.append("GPU caliente: %d C (>=80: el reloj ya baja)"
                       % gpu["temp_c"])
        rj, rm = gpu.get("reloj_mhz"), gpu.get("reloj_max_mhz")
        if rj and rm and rm > 0 and rj < 0.85 * rm and (
                (gpu.get("util_pct") or 0) >= 40):
            out.append("GPU en throttle: reloj %d de %d MHz (<85%% del max)"
                       % (rj, rm))
    if plan and plan.get("equilibrado"):
        out.append("Plan de energia Equilibrado (recorta relojes; el plan "
                   "de la casa es Alto rendimiento)")
    return out


# ------------------- estacion 4: clasificacion y veredicto -------------------
def clasificar_decode(dec):
    """El numero medido contra los rangos [M] del lab. Devuelve
    (etiqueta, explicacion_corta)."""
    if dec is None:
        return ("SIN-DATO", "no hubo medicion valida del server")
    if dec < BAJO_DESDE:
        return ("BAJO", "por debajo del suelo k=8 del lab (17.36 [M] - "
                        "ruido): algo del dia esta frenando")
    if dec <= NORMAL_HASTA:
        return ("NORMAL-K8", "dentro del rango k=8 medido en el lab "
                             "(17.4-21.5 [M]): la receta va como debe")
    if dec < K4_DESDE:
        return ("GRIS", "entre el techo k=8 y la banda k=4: ambiguo, "
                        "resolver con el ratio 8-vs-4 (SS28)")
    return ("HUELE-K4", "en la banda k=4 medida en el lab (24-30 [M]): "
                        "esto huele a CHARLA abierta")


def veredicto(med, cert, ram, gpu, plan):
    """Las lineas finales (consola e informe). Nunca lanza excepciones."""
    dec = med.get("decode")
    etiqueta, explicacion = clasificar_decode(dec)
    L = []
    L.append("VEREDICTO: %s — %s" % (etiqueta, explicacion))
    if etiqueta == "NORMAL-K8":
        L.append("  -> A tu pregunta '¿deberia ir a mas?': NO con 8 cocineros. "
                 "El techo fisico del rig con flags es ~21.5 [M]: sweep "
                 "25-oct BASE %.2f y LMNONE %.2f (la receta de HOY lleva "
                 "-lm none) + ORO-UB1K %.2f. Para MAS t/s: CHARLA (4 "
                 "expertos, banda 24-30 [M])."
                 % (SWEEP_BASE, SWEEP_LMNONE, ORO_UB1K))
        L.append("  -> Tu recuerdo ('a solo flags iba a 21 minimo con 8 "
                 "cocineros') ES dato certificado: %.2f [M] es el numero del "
                 "sweep para esta receta. Ese 21 era el TECHO de los dias "
                 "buenos, no el suelo (suelo certificado: %.2f [M])."
                 % (SWEEP_LMNONE, FASED_FLOOR))
        if dec is not None and dec >= DIA_BUENO_DESDE:
            L.append("  -> Estas EN los dias buenos (~21): coincide con tu "
                     "recuerdo. Receta completa, maquina rindiendo lo suyo.")
        else:
            L.append("  -> Dentro del lab pero por debajo de tu 21: dia lento "
                     "de los que el lab tambien midio (%.2f-%.2f [M] con la "
                     "MISMA receta otro dia). Culpables del dia, abajo. El "
                     "dia bueno vuelve a ~21 solo (menos apps, GPU fria)."
                     % (FASED_FLOOR, FASED_ANCLA))
        L.append("  -> El numero del CHAT sale mas bajo que este porque es "
                 "reloj de pared (cuenta pausas del dia); el de aqui es el "
                 "reloj interno del server, medido como en el laboratorio.")
    elif etiqueta == "BAJO":
        L.append("  -> Con la receta completa el lab NUNCA midio menos de "
                 "%.2f [M]: si esto mide menos, el freno es del DIA, no de "
                 "la receta (ver culpables abajo)." % FASED_FLOOR)
        L.append("  -> Tu 21 recordado era el TECHO del sweep (LMNONE %.2f "
                 "[M]), no el piso: contra ese techo, hoy falta dia o hay "
                 "culpable (arriba)." % SWEEP_LMNONE)
    elif etiqueta == "HUELE-K4":
        L.append("  -> Si abriste CHARLA: todo correcto. Si abriste TRABAJO "
                 "y mide esto: mejor que el lab — anotalo (seria noticia).")
    elif etiqueta == "GRIS":
        L.append("  -> Resuelve con el experimento del ratio (SS28): TRABAJO "
                 "/modo 8 vs CHARLA /modo 4, misma pregunta, 2a-3a respuesta.")
    if cert["match"] and cert["k_esperado"] is not None:
        if cert["k_vivo"] is not None and cert["k_vivo"] != cert["k_esperado"]:
            L.append("  OJO: config.txt dice %s=%d pero el comando vivo lleva "
                     "k=%d — ¿editaste config.txt despues de abrir? Cierra y "
                     "reabre para que cuente." % (cert["match"],
                                                  cert["k_esperado"],
                                                  cert["k_vivo"]))
    culprits = culpritos(ram, gpu, plan)
    if etiqueta == "BAJO" and not culprits and cert["match"]:
        L.append("  Sin culpables claros (RAM/GPU/plan OK) y receta viva OK: "
                 "anota este numero en el repo y corre el barrido formal "
                 "(BARRIDO-N1.bat) — un BAJO sin causa merece sesion limpia.")
    for c in culprits:
        L.append("  CULPABLE: " + c)
    return L


# ------------------------------- informe -------------------------------------
def escribir_informe(cfg, ruta_cfg, cert, med, ram, gpu, plan, lineas_final):
    """Escribe diagnostico-AAAAMMDD-HHMMSS.md en RUTA_LOGS. Devuelve la ruta
    o None (mejor un diagnostico sin archivo que un fallo entero)."""
    est = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = cfg.get("RUTA_LOGS") or "."
    try:
        os.makedirs(base, exist_ok=True)
        ruta = os.path.join(base, "diagnostico-%s.md" % est)
    except Exception:
        return None
    P = []
    P.append("# DIAGNOSTICO DE VELOCIDAD — %s" % est)
    P.append("")
    P.append("diagnostico-velocidad v1.1 · config: %s · pregunta: '¿deberia "
             "ir a mas t/s con la receta completa?'" % ruta_cfg)
    P.append("")
    P.append("## Estacion 1 — receta viva (certificado)")
    P.append("")
    if cert["match"]:
        P.append("- MATCH con la receta '%s' reconstruida desde config.txt "
                 "(k vivo del comando: %s)" % (cert["match"],
                                               cert["k_vivo"]))
    else:
        P.append("- SIN match exacto. k vivo segun comando: %s" % cert["k_vivo"])
        if cert["faltan"] or cert["sobran"]:
            P.append("  - Faltan en el vivo: %s" % (cert["faltan"] or "-"))
            P.append("  - Sobran en el vivo: %s" % (cert["sobran"] or "-"))
        P.append("  - Nota: %s" % (cert["nota"] or "-"))
    P.append("")
    P.append("## Estacion 2 — medicion estilo laboratorio (SS8)")
    P.append("")
    P.append("- decode (media pasadas 2-4, reloj del server): %s t/s"
             % ("%.2f" % med["decode"] if med.get("decode") else "n/d"))
    P.append("- prefill (pasada 1 fria): %s tok/s"
             % ("%.0f" % med["prefill"] if med.get("prefill") else "n/d"))
    for d in med.get("detalle", []):
        P.append("  - pasada %d: decode %s · prefill %s · n %s" % (
            d["pasada"],
            "%.2f" % d["predicted_per_second"] if d["predicted_per_second"]
            else "n/d",
            "%.0f" % d["prompt_per_second"] if d["prompt_per_second"]
            else "n/d",
            d["predicted_n"]))
    P.append("")
    P.append("## Estacion 3 — guardarrails del dia")
    P.append("")
    P.append("- RAM: %s" % (json.dumps(ram) if ram else "no disponible"))
    P.append("- GPU: %s" % (json.dumps(gpu) if gpu else "nvidia-smi no "
                            "disponible"))
    P.append("- Plan energia: %s" % (plan["texto"] if plan else
                                     "no disponible"))
    P.append("")
    P.append("## Estacion 4 — veredicto")
    P.append("")
    P.extend(lineas_final)
    P.append("")
    P.append("Referencias [M] certificadas: sweep 25-oct BASE %.2f / LMNONE "
             "%.2f (la receta de HOY: base + -lm none) · faseD v1.2 suelo "
             "%.2f (D-EXP10-CTRL), ancla %.2f, D-EXP8 20.51 · ORO-UB1K %.2f "
             "· k=4: D-EXP4 28.85, D-EXP4-UB1K 29.13 · ruido +/-0.5 (SS8). "
             "Zona gris 22.0-24.0. Recuerdo del Director ('a solo flags iba "
             "a 21 minimo con 8 cocineros') = LMNONE %.2f — el 21 es el "
             "TECHO certificado de la familia, no el suelo."
             % (SWEEP_BASE, SWEEP_LMNONE, FASED_FLOOR, FASED_ANCLA,
                ORO_UB1K, SWEEP_LMNONE))
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(P) + "\n")
        return ruta
    except Exception:
        return None


# --------------------------------- main --------------------------------------
def _blindar_salida():
    """La consola de Windows no debe matar el informe por un caracter que su
    codepage no conozca (redirigido con cp850: UnicodeEncodeError a mitad de
    veredicto). Se conserva la codificacion; solo se vuelve tolerante."""
    for s in (sys.stdout, sys.stderr):
        try:
            if s is not None and hasattr(s, "reconfigure"):
                s.reconfigure(errors="replace")
        except Exception:
            pass


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    _blindar_salida()
    print(cia("=" * 70))
    print(cia("  DIAGNOSTICO DE VELOCIDAD — Qwen APEX-I-MINI (b11856) v1.1"))
    print(cia("  ¿va a los t/s que debe con la receta completa?"))
    print(cia("=" * 70))

    ruta_cfg = encontrar_config()
    if not ruta_cfg:
        print(rojo("[ERROR] No encontre config.txt (D:\\ZLia\\config.txt o "
                   "junto al script)."))
        return 1
    cfg = parsear_config(ruta_cfg)
    faltan = [k for k in KEYS if k not in cfg]
    if faltan:
        print(rojo("[ERROR] A config.txt le faltan claves: %s" % ", ".join(faltan)))
        return 1
    puerto = cfg.get("PUERTO", "9931")

    print("\n[1/4] CERTIFICADO DE LA RECETA VIVA")
    lineas_vivas, _nota_cmd = cmdline_viva()
    puerto_vivo = None
    if health_ok(puerto):
        puerto_vivo = puerto
    else:
        for l in (lineas_vivas or []):
            p = puerto_de_tokens(_tokens(l))
            if p and p != puerto and health_ok(p):
                puerto_vivo = p
                print(ambar(
                    "  AVISO: config.txt dice puerto %s pero el server vivo "
                    "responde en el %s (¿editaste el puerto despues de "
                    "abrir?). Se diagnostica contra el VIVO." % (puerto, p)))
                break
    if not puerto_vivo:
        print(rojo("  No hay server que responda en el puerto %s." % puerto))
        if lineas_vivas:
            print("  Hay proceso llama-server abierto pero no contesta: puede")
            print("  estar aun cargando (~1-2 min). Espera el cartel MODELO")
            print("  LISTO y vuelve a lanzar el diagnostico.")
        else:
            print("  Abre primero el modelo: doble click en ABRIR-QWEN.bat")
            print("  (este diagnostico mide el server VIVO; no abre otro).")
        return 1
    if puerto_vivo != puerto:
        puerto = puerto_vivo
    cert = certificar_receta(cfg, lineas=lineas_vivas)
    if cert["match"]:
        print(verde("  RECETA VIVA = ORIGINAL '%s' (piezas exactas desde "
                    "config.txt). k vivo: %s" % (cert["match"],
                                                 cert["k_vivo"])))
    else:
        print(ambar("  Sin match exacto con la receta de config.txt."))
        if cert["faltan"]:
            print(ambar("    Faltan en el vivo: %s" % cert["faltan"]))
        if cert["sobran"]:
            print(ambar("    Sobran en el vivo: %s" % cert["sobran"]))
        print("    (%s)" % cert["nota"])
        print("    ¿Editaste config.txt DESPUES de abrir el server? "
              "Cierra y reabre.")

    print("\n[2/4] MEDICION ESTILO LABORATORIO (4 pasadas x 256 tok, temp 0)")
    print("  NO chatees mientras mide (~1 min).")
    try:
        prefill, dec, detalle = pasadas_medicion(puerto, PROMPTS_MEDICION)
    except Exception as e:
        print(rojo("  Fallo la medicion: %s" % e))
        prefill, dec, detalle = None, None, []
    if dec:
        print(verde("  decode (media 2-4): %.2f t/s" % dec))
        if prefill:
            print("  prefill (pasada 1 fria): %.0f tok/s" % prefill)
    else:
        print(ambar("  Sin numero de decode (mira el fallo arriba)."))
    med = {"decode": dec, "prefill": prefill, "detalle": detalle}

    print("\n[3/4] GUARDARRAILS DEL DIA")
    ram = ram_status()
    gpu = gpu_status()
    plan = plan_energia()
    if ram:
        print("  RAM: %d%% en uso, %.2f GB libres de %.2f GB" % (
            ram["carga_pct"], ram["libre_gb"], ram["total_gb"]))
    else:
        print("  RAM: no disponible en este sistema")
    if gpu:
        print("  GPU: %d C · util %d%% · VRAM %d/%d MiB · reloj %d/%d MHz" % (
            gpu.get("temp_c") or 0, gpu.get("util_pct") or 0,
            gpu.get("mem_usada_mib") or 0, gpu.get("mem_total_mib") or 0,
            gpu.get("reloj_mhz") or 0, gpu.get("reloj_max_mhz") or 0))
    else:
        print("  GPU: nvidia-smi no disponible (se salta)")
    if plan:
        print("  Plan de energia: %s" % plan["texto"])

    print("\n[4/4] VEREDICTO")
    lineas = veredicto(med, cert, ram, gpu, plan)
    for l in lineas:
        print(("  " + l) if not l.startswith("VEREDICTO") else cia(l))

    ruta_inf = escribir_informe(cfg, ruta_cfg, cert, med, ram, gpu, plan,
                                lineas)
    if ruta_inf:
        print("\nInforme guardado: %s" % ruta_inf)
    else:
        print("\n(no pude escribir el informe en RUTA_LOGS; el veredicto de "
              "arriba es completo)")
    print("")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
        sys.exit(130)
