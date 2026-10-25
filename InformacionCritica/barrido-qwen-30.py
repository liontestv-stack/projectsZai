#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BARRIDO-QWEN-30 v1.0 (2026-10-25) - barrido automatico de 30 configuraciones NUEVAS
====================================================================================
Que hace: prueba UNA A UNA en bucle 30 configuraciones que NUNCA se midieron
en el barrido-25 (nada repetido), con el mismo protocolo riguroso, y al final
imprime el ranking + el comando ganador + la linea FLAGS_GANADORAS.

PUNTO DE PARTIDA (medido, barrido 25/25 del 2026-10-25):
  campeon = -lm none  ->  21.50 t/s  (BASE sin lm none = 20.85)
  techo $0 declarado = 21.5-22 t/s  (cuello: ancho de banda DDR4)
Este barrido busca ROMPER ese techo con 4 familias nuevas + cierres:

  ANCLA (2)  - reproducen el campeon (21.50) y la base vieja (20.85) en esta
               MISMA corrida: sin esto, comparar contra numeros de otro dia
               no es valido (termicas, escritorio, estado del PC).
  EXP   (5)  - LA GRAN APUESTA y respuesta a la pregunta del Director
               ("bajar la cantidad de expertos ayudara?"): SÍ hay via runtime,
               sin tocar el GGUF: --override-kv qwen3moe.expert_used_count=int:N
               (verificada en fuentes publicas; por eso se mide N=10 control,
               8 sanity, 6/5/4 reduccion). Menos expertos activos = menos
               bytes leidos por token = la UNICA familia que ataca el cuello
               real. RIESGO: calidad (se valida chateando DESPUES).
               El control EXP10 (MAS expertos -> deberia ser MAS lento) y la
               lectura de n_expert_used en el log del server dicen si el
               override se aplico de verdad (nada se asume).
  FIT/NCM (7)- mover las ultimas capas de expertos a GPU: con -ngl auto el
               auto-fit empaqueta solo (aprendido §3: con -ngl 99 fijo
               desbordaba; aqui se usa fit libre o VRAM liberada con -c 8192
               /4096 + KV q4_0, las condiciones sancionadas en aprendido.md).
  AFINIDAD(5)- -Cr/-C/--cpu-strict: fijar los 4 hilos a nucleos concretos
               (evitar HT y el nucleo 0 de interrupciones). i3-10100F =
               4C/8T, ganancia esperada pequena pero es OFAT barato.
  CIERRES (9)- prio 3/0, poll 20/80, --no-host, -nr (repack off), KV q5_1,
               -lm dio, y los 3 COMBOS dinamicos del final (construidos con
               los ganadores medidos de esta corrida).

Protocolo de medicion (identico al barrido-25, con 2 mejoras documentadas):
  - Prompt fijo ~230 tokens, n_predict 256, cache_prompt true, temp 0 (greedy
    SOLO aqui: es benchmark, excepcion documentada)
  - 4 pasadas por config: se descarta la 1a (calentamiento) y se promedia 2-4
  - NUEVO: "ignore_eos": true en el request -> TODAS las pasadas generan
    exactamente 256 tokens (antes una config podia cortar antes por EOS y
    comparar ventanas distintas)
  - NUEVO: columna load_s (segundos de carga) y hparams (arch + n_expert +
    n_expert_used leidos del log del server: prueba objetiva de si el
    override de expertos aplico)
  - Pausa termica 60 s cada 8 configs; CSV append con RESUME (Ctrl+C seguro);
    log del server por config en sweep-logs-30\\NN-NOMBRE.log

Antes de correr:
  1. Cerrar Firefox / Wallpaper Engine / Copilot (roban VRAM+RAM y meten ruido)
  2. Cerrar CUALQUIER llama-server abierto (el script ABORTA si /health vive)
  3. No usar el PC mientras corre

Doble click: BARRIDO-QWEN-30.bat  |  Duracion ~1 h (resume por CSV)
Salidas: sweep-resultados-30.csv + sweep-logs-30\\ + ranking en pantalla

IMPORTANTE al interpretar (esta en el ranking tambien):
  - Si gana un EXP*: primero validar CALIDAD chateando (menos expertos activos
    puede degradar el modelo; la velocidad no lo dice). EXP4 es mas agresivo
    que EXP6.
  - Si el ganador trae -ncmoe o -ngl auto: NO pegarlo tal cual en el launcher
    (su BASE_FLAGS tiene -cmoe y -ngl 99: el -cmoe general gana y anula al
    -ncmoe). Hay que quitarlos a mano - el ranking imprime como.

Historial: barrido-qwen-25.py v1.1 = protocolo base (25 configs, 25 corridas
reales ya medidas). Este script NO repite ninguna de esas 25.
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

# ============================== CONFIG (editar aqui) ==============================
RUTA_SERVER = r"D:\llama.cpp\llama-server.exe"
RUTA_MODELO = (r"D:\ZLia\models"
               r"\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf")
ALIAS = "apex35b"
HOST = "127.0.0.1"
PORT = 9931
N_PREDICT = 256          # tokens generados por pasada (con ignore_eos: SIEMPRE 256)
RUNS = 4                 # 1 calentamiento (descartado) + 3 medidas
PAUSA_CADA = 8           # configs entre pausas termicas
PAUSA_SEG = 60
DIR_LOGS = "sweep-logs-30"
ARCH_CSV = "sweep-resultados-30.csv"

URL = "http://%s:%d" % (HOST, PORT)

# Campeon del barrido-25 (-lm none, 21.50 t/s) MENOS la colocacion de expertos:
# el -cmoe/-ncmoe va POR CONFIG (asi FIT/NCM pueden probar -ncmoe sin que el
# -cmoe general lo anule: en b11856 ambos flags juntos = gana el general).
BASE_FLAGS = [
    "-m", RUTA_MODELO, "-a", ALIAS,
    "-ngl", "99",
    "-c", "16384", "-b", "2048", "-ub", "256",
    "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
    "-t", "4", "--prio", "2", "--no-mmproj",
    "-lm", "none",
    "--host", HOST, "--port", str(PORT),
]

# Campeon publicado (fallback honesto si ANCHOR-B no tiene dato al armar combos)
TECHO_CONOCIDO = 21.50

# Colocacion de expertos: TODA config estatica debe traer -cmoe o -ncmoe
# (validado al arranque; si ninguno esta, el modelo completo iria a GPU y
# desbordaria la VRAM: error conocido, aprendido.md §3)
CM = ["-cmoe"]


def _ovexp(n):
    """Override runtime del numero de expertos activos (n_expert_used).
    La clave arch-especifica (qwen3moe.*) es la documentada en fuentes
    publicas para la familia Qwen3 MoE; la generica va como segundo tiro por
    si el arch del GGUF difiere. El control EXP10 y los hparams del log
    verifican si aplico (nada se asume)."""
    clave = ("qwen3moe.expert_used_count=int:%d,"
             "expert_used_count=int:%d" % (n, n))
    return ["--override-kv", clave]


# Las 30 (familias y motivacion en el docstring). flags = DIFF sobre BASE_FLAGS.
CONFIGS = [
    # ---- ANCLAS de reproducibilidad (ids 1-2) ----
    {"id": 1, "familia": "ANCLA", "nombre": "ANCHOR-B", "flags": list(CM),
     "hipotesis": "campeon -lm none reproducido en esta corrida (~21.50)"},
    {"id": 2, "familia": "ANCLA", "nombre": "ANCHOR-VJ", "flags": CM + ["-lm", "mmap"],
     "hipotesis": "base vieja reproducida (~20.85; auto del 25 = mmap)"},
    # ---- EXP: expertos activos por runtime (ids 3-7) ----
    {"id": 3, "familia": "EXP", "nombre": "EXP10", "flags": CM + _ovexp(10),
     "hipotesis": "CONTROL: +expertos => +bytes/token => deberia medir MENOS que ANCLA. Si no baja, el override no aplico"},
    {"id": 4, "familia": "EXP", "nombre": "EXP8", "flags": CM + _ovexp(8),
     "hipotesis": "SANITY: si el modelo ya usa 8, debe clavarce con ANCLA"},
    {"id": 5, "familia": "EXP", "nombre": "EXP6", "flags": CM + _ovexp(6),
     "hipotesis": "-25% bytes de expertos => +15-25% t/s (calidad por validar)"},
    {"id": 6, "familia": "EXP", "nombre": "EXP5", "flags": CM + _ovexp(5),
     "hipotesis": "-37% bytes de expertos => punto medio 5 vs 6"},
    {"id": 7, "familia": "EXP", "nombre": "EXP4", "flags": CM + _ovexp(4),
     "hipotesis": "-50% bytes de expertos => ruta a ~30 t/s (calidad MUY en riesgo)"},
    # ---- FIT: auto-fit de VRAM con margen (ids 8-10; aprendido §3: fit libre) ----
    {"id": 8, "familia": "FIT", "nombre": "FIT-A",
     "flags": ["-ngl", "auto", "-ncmoe", "34", "-fitt", "256"],
     "hipotesis": "fit empaqueta solo: ultimas capas de expertos a GPU (+5-7% t/s teorico); puede bajar ctx hasta 4096"},
    {"id": 9, "familia": "FIT", "nombre": "FIT-B",
     "flags": ["-ngl", "auto", "-ncmoe", "36", "-fitt", "256"],
     "hipotesis": "mas capas candidatas a GPU, fit decide cuantas caben"},
    {"id": 10, "familia": "FIT", "nombre": "FIT-C",
     "flags": ["-ngl", "auto", "-ncmoe", "32", "-fitt", "384"],
     "hipotesis": "margen mas conservador (384 MiB), menos riesgo de desborde"},
    # ---- NCMOE explicito con VRAM liberada (ids 11-14; condiciones de aprendido §3) ----
    {"id": 11, "familia": "NCM", "nombre": "NCM38",
     "flags": ["-ncmoe", "38", "-c", "8192", "-ctk", "q4_0", "-ctv", "q4_0"],
     "hipotesis": "2 capas de expertos a GPU (~0.55 GiB) caben con KV q4 8k"},
    {"id": 12, "familia": "NCM", "nombre": "NCM39",
     "flags": ["-ncmoe", "39", "-c", "8192", "-ctk", "q4_0", "-ctv", "q4_0"],
     "hipotesis": "1 capa a GPU, margen mas holgado que NCM38"},
    {"id": 13, "familia": "NCM", "nombre": "NCM39Q8",
     "flags": ["-ncmoe", "39", "-c", "8192"],
     "hipotesis": "igual que NCM39 pero conservando KV q8_0 (mejor calidad de KV)"},
    {"id": 14, "familia": "NCM", "nombre": "NCM37C4",
     "flags": ["-ncmoe", "37", "-c", "4096", "-ctk", "q4_0", "-ctv", "q4_0"],
     "hipotesis": "3 capas a GPU: agresivo, puede chocar el fit (quedaria anotado)"},
    # ---- AFINIDAD CPU (ids 15-19) ----
    {"id": 15, "familia": "AFF", "nombre": "CR03", "flags": CM + ["-Cr", "0-3"],
     "hipotesis": "fijar hilos a los 4 nucleos fisicos (Windows lista fisicos primero)"},
    {"id": 16, "familia": "AFF", "nombre": "CMASK55", "flags": CM + ["-C", "55"],
     "hipotesis": "mask 0x55 = logicos 0,2,4,6: hipotesis nucleos fisicos alternos"},
    {"id": 17, "familia": "AFF", "nombre": "STRICT",
     "flags": CM + ["-Cr", "0-3", "--cpu-strict", "1"],
     "hipotesis": "colocacion estricta: los hilos no migran entre nucleos"},
    {"id": 18, "familia": "AFF", "nombre": "STRICT55",
     "flags": CM + ["-C", "55", "--cpu-strict", "1"],
     "hipotesis": "igual que CMASK55 pero estricto"},
    {"id": 19, "familia": "AFF", "nombre": "CR14", "flags": CM + ["-Cr", "1-4"],
     "hipotesis": "esquivar el nucleo logico 0 (interrupciones/DPC del sistema)"},
    # ---- PRIORIDAD / POLL (ids 20-23) ----
    {"id": 20, "familia": "PRI", "nombre": "PRIO3", "flags": CM + ["--prio", "3"],
     "hipotesis": "realtime por encima del high del campeon (puede ignorarlo Windows)"},
    {"id": 21, "familia": "PRI", "nombre": "PRIO0", "flags": CM + ["--prio", "0"],
     "hipotesis": "cierre de curva: normal (0) vs high (2) del campeon"},
    {"id": 22, "familia": "PRI", "nombre": "POLL80", "flags": CM + ["--poll", "80"],
     "hipotesis": "entre default 50 y POLL100 (21.42): afinar el polling"},
    {"id": 23, "familia": "PRI", "nombre": "POLL20", "flags": CM + ["--poll", "20"],
     "hipotesis": "punto bajo de la curva (POLL0 21.33 / POLL100 21.42)"},
    # ---- BUFFERS / CARGA: cierres (ids 24-27) ----
    {"id": 24, "familia": "BUF", "nombre": "NOHOST", "flags": CM + ["--no-host"],
     "hipotesis": "bypass del host buffer: menos sincros CPU<->GPU (exploratoria)"},
    {"id": 25, "familia": "BUF", "nombre": "REPACKOFF", "flags": CM + ["-nr"],
     "hipotesis": "repack de pesos OFF (default on): en AVX2 podria no ayudar"},
    {"id": 26, "familia": "BUF", "nombre": "KVQ51",
     "flags": CM + ["-ctk", "q5_1", "-ctv", "q5_1"],
     "hipotesis": "cierre familia KV (aprendido §5: ruido esperado, q4 ya perdio)"},
    {"id": 27, "familia": "BUF", "nombre": "LMDIO", "flags": CM + ["-lm", "dio"],
     "hipotesis": "t/s ~ campeon esperado; el dato util es load_s (DirectIO vs none)"},
    # ---- COMBOS DINAMICOS (ids 28-30; se construyen con los ganadores medidos) ----
    {"id": 28, "familia": "COMBO", "nombre": "COMBO-TOP", "flags": None,
     "hipotesis": "fusion de los 2 mejores configs de esta corrida"},
    {"id": 29, "familia": "COMBO", "nombre": "COMBO-EXP", "flags": None,
     "hipotesis": "mejor EXP x mejor no-EXP (si ningun EXP gana: repro del COMBO-TOP)"},
    {"id": 30, "familia": "COMBO", "nombre": "COMBO-X3", "flags": None,
     "hipotesis": "fusion de los 3 mejores (mega-combo final)"},
]

# Prompt de medicion (~230 tokens, fijo para todas las configs; mismo del 25)
PROMPT = (
    "Resume la arquitectura de un motor de inference local. El pipeline empieza "
    "cuando el usuario escribe una pregunta en la ventana de chat. El tokenizer "
    "corta el texto en subpalabras y cada subpalabra se convierte en un entero del "
    "vocabulario. Esos enteros entran al modelo como una secuencia y se procesan "
    "capa por capa. Cada capa tiene dos bloques: atencion y red feed-forward. La "
    "atencion permite que cada posicion mire a las demas posiciones del contexto y "
    "decida que informacion es relevante. La red feed-forward transforma esa "
    "informacion de forma no lineal. En los modelos mixture-of-experts la "
    "feed-forward no es una sola red: hay muchas redes expertas y un enrutador que "
    "elige unas pocas para cada token. Por eso el numero de parametros activos es "
    "mucho menor que el total y por eso la velocidad de generacion depende del "
    "ancho de banda de memoria donde viven los expertos. Si los expertos estan en "
    "la CPU, cada token generado exige leerlos de la RAM del sistema. Si estan en "
    "la GPU, se leen de la VRAM que es mas rapida pero tambien mas pequena. "
    "Finalmente la salida del modelo es una distribucion de probabilidad sobre el "
    "vocabulario y el sampler elige el siguiente token segun temperatura, top-k y "
    "top-p. Ese token se anade a la secuencia y el ciclo se repite hasta el final. "
    "Ahora resume este texto en cinco puntos breves."
)

CSV_COLS = ["id", "nombre", "familia", "flags", "tps", "tps_r1", "tps_r2",
            "tps_r3", "tps_r4", "prefill_tps", "n_gen", "vram_mib", "load_s",
            "hparams", "notas", "fecha"]

# Estado global minimo para el diagnostico EXP (hparams de la ANCLA)
_HP_ANCLA = {"log": "", "ruta": ""}


def _ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ============================== SALUD Y MEDICION ==============================
def _health_ok(timeout=2):
    try:
        with urllib.request.urlopen(URL + "/health", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _medir_una_vez():
    """POST /completion -> dict con tps, prefill, n tokens.
    ignore_eos: true -> todas las pasadas generan EXACTAMENTE n_predict tokens
    (mejora del protocolo vs barrido-25: ventanas identicas siempre)."""
    body = json.dumps({
        "prompt": PROMPT,
        "n_predict": N_PREDICT,
        "temperature": 0.0,      # greedy SOLO para bench (excepcion documentada)
        "top_k": 1,
        "cache_prompt": True,    # las repeticiones no repiten prefill
        "ignore_eos": True,      # ventanas de medicion identicas entre configs
    }).encode("utf-8")
    req = urllib.request.Request(URL + "/completion", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read().decode("utf-8", errors="replace"))
    t = data.get("timings", {}) or {}
    return {
        "tps": t.get("predicted_per_second"),
        "prefill": t.get("prompt_per_second"),
        "n_gen": t.get("predicted_n"),
    }


def _hparams_de_log(ruta_log):
    """Best-effort: arch + conteos de expertos que el loader imprime al cargar.
    Devuelve "" si el log no los trae (entonces el diagnostico EXP queda
    'sin datos' y no se inventa nada)."""
    try:
        txt = open(ruta_log, "r", encoding="utf-8", errors="replace").read()
    except Exception:
        return ""
    partes = []
    m = re.search(r"arch\s*=\s*([A-Za-z0-9_\-]+)", txt)
    if m:
        partes.append("arch=" + m.group(1))
    m = re.search(r"n_expert\s*=\s*(\d+)", txt)
    if m:
        partes.append("n_expert=" + m.group(1))
    m = re.search(r"n_expert_used\s*=\s*(\d+)", txt)
    if m:
        partes.append("n_expert_used=" + m.group(1))
    return ";".join(partes)


def _vram_mib():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10)
        return str(int(out.stdout.strip().splitlines()[0]))
    except Exception:
        return ""


# ============================== CICLO DE VIDA SERVER ==============================
def _parar(proc):
    if proc is None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True, timeout=15)
        else:
            proc.terminate()
        proc.wait(timeout=15)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    time.sleep(3)  # dejar que VRAM/RAM se liberen de verdad


def _lanzar_y_esperar(flags, ruta_log):
    """Lanza el server con BASE_FLAGS + flags. Devuelve (proc, load_s)."""
    logf = open(ruta_log, "w", encoding="utf-8")
    t0 = time.time()
    proc = subprocess.Popen(
        [RUTA_SERVER] + BASE_FLAGS + flags,
        stdout=logf, stderr=subprocess.STDOUT,
        cwd=os.path.dirname(RUTA_SERVER) or ".")
    while time.time() - t0 < 600:          # la carga tarda ~45-90 s (logs reales)
        if proc.poll() is not None:        # el server murio al arrancar
            logf.close()
            raise RuntimeError("el server termino al arrancar (rc=%s) - ver %s"
                               % (proc.returncode, ruta_log))
        if _health_ok():
            logf.close()
            return proc, time.time() - t0
        time.sleep(2)
    _parar(proc)
    logf.close()
    raise RuntimeError("timeout 600 s esperando /health - ver %s" % ruta_log)


# ============================== CSV / RESUME ==============================
def _leer_csv():
    filas = {}
    if os.path.exists(ARCH_CSV):
        with open(ARCH_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    filas[int(row["id"])] = row
                except (ValueError, KeyError):
                    pass
    return filas


def _guardar_fila(fila):
    nuevo = not os.path.exists(ARCH_CSV)
    with open(ARCH_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        if nuevo:
            w.writeheader()
        w.writerow(fila)


def _tps_de(filas, cid, default=None):
    try:
        return float(filas[cid]["tps"])
    except (KeyError, TypeError, ValueError):
        return default


# ============================== COMBOS DINAMICOS ==============================
def _fusionar(*listas):
    """Une listas de flags sin duplicar claves (gana la PRIMERA aparicion).
    Los flags booleanos ("-cmoe") se reconocen porque el token siguiente
    empieza por '-' o es fin de lista."""
    visto, salida = set(), []
    for fl in listas:
        i = 0
        while i < len(fl):
            tok = fl[i]
            if not tok.startswith("-"):
                i += 1
                continue
            par = [tok]
            if i + 1 < len(fl) and not fl[i + 1].startswith("-"):
                par.append(fl[i + 1])
            if tok not in visto:
                visto.add(tok)
                salida.extend(par)
            i += len(par)
    return salida


def _combos_dinamicos(filas):
    """Construye las configs 28-30 con los GANADORES medidos de esta corrida
    (todo lo que supere a la ANCLA id 1). Sin dato de ancla usa el campeon
    publicado (TECHO_CONOCIDO, 21.50 del barrido-25) y lo dice en pantalla."""
    t_ancla = _tps_de(filas, 1, None)
    if t_ancla is None:
        print("[i] ANCLA sin dato en el CSV; referencia = campeon publicado "
              "%.2f t/s (barrido-25)" % TECHO_CONOCIDO)
        t_ancla = TECHO_CONOCIDO

    ganadores = []   # (tps, config) de todo lo que supero a la ancla
    for c in CONFIGS:
        if c["id"] in (1, 2) or c["id"] > 27:
            continue
        t = _tps_de(filas, c["id"], None)
        if t is not None and t > t_ancla:
            ganadores.append((t, c))
    ganadores.sort(key=lambda par: par[0], reverse=True)
    top = [c for _, c in ganadores[:3]]

    if top:
        cfg28 = _fusionar(top[0]["flags"], top[1]["flags"]) if len(top) >= 2 \
            else list(top[0]["flags"])
        exps = [(t, c) for t, c in ganadores if c.get("familia") == "EXP"]
        if exps:
            no_exp = [(t, c) for t, c in ganadores if c.get("familia") != "EXP"]
            if no_exp:
                cfg29 = _fusionar(exps[0][1]["flags"], no_exp[0][1]["flags"])
            else:
                cfg29 = list(exps[0][1]["flags"])
        else:
            cfg29 = list(cfg28)   # repro del mismo combo (2a medida = varianza)
            print("[i] Ningun EXP gano a la ancla: COMBO-EXP = repro del COMBO-TOP")
        cfg30 = _fusionar(*[c["flags"] for c in top]) if len(top) >= 3 else list(cfg28)
    else:
        print("[i] Nada supero a la ancla: combos = ancla repetida (dato de varianza)")
        cfg28, cfg29, cfg30 = list(CM), list(CM), list(CM)

    for c in CONFIGS:
        if c["id"] == 28:
            c["flags"] = cfg28
        elif c["id"] == 29:
            c["flags"] = cfg29
        elif c["id"] == 30:
            c["flags"] = cfg30
    print("[i] Combos dinamicos construidos con los ganadores medidos:")
    print("    28 COMBO-TOP =", " ".join(cfg28) or "(ancla pura)")
    print("    29 COMBO-EXP =", " ".join(cfg29) or "(ancla pura)")
    print("    30 COMBO-X3  =", " ".join(cfg30) or "(ancla pura)")


# ============================== MEDIR UNA CONFIG ==============================
def _diagnostico_exp(cfg, ruta_log):
    """Para familia EXP: compara n_expert_used del log de esta config contra
    el de la ANCLA. Prueba objetiva de si el override-kv aplico."""
    if cfg.get("familia") != "EXP":
        return ""
    hp = _hparams_de_log(ruta_log)
    if not _HP_ANCLA["log"] or not hp:
        return "hparams no visibles en log (diagnostico manual)"
    m_a = re.search(r"n_expert_used=(\d+)", _HP_ANCLA["log"])
    m_c = re.search(r"n_expert_used=(\d+)", hp)
    if not m_a or not m_c:
        return "hparams incompletos (diagnostico manual)"
    if m_c.group(1) != m_a.group(1):
        return "override APLICADO (n_expert_used %s->%s)" % (m_a.group(1), m_c.group(1))
    return "override NO aplico (n_expert_used sigue %s)" % m_a.group(1)


def _medir_config(cfg):
    nombre_log = "%s-%02d-%s.log" % (time.strftime("%Y%m%d"), cfg["id"], cfg["nombre"])
    ruta_log = os.path.join(DIR_LOGS, nombre_log)
    flags = cfg["flags"] if cfg["flags"] is not None else []
    print("    flags: %s" % (" ".join(flags) if flags else "(BASE)"))
    proc = None
    try:
        proc, load_s = _lanzar_y_esperar(flags, ruta_log)
    finally:
        if proc is None:
            raise
    print("    server arriba en %d s (carga), midiendo %d pasadas x %d tokens..."
          % (load_s, RUNS, N_PREDICT))
    tps_runs, prefill, n_gen = [], "", ""
    try:
        for i in range(1, RUNS + 1):
            r = _medir_una_vez()
            tps_runs.append(r["tps"])
            if r["prefill"]:
                prefill = "%.2f" % r["prefill"]
            if r["n_gen"]:
                n_gen = str(r["n_gen"])
            print("      pasada %d/%d: %.2f t/s (gen)  prefill %s t/s"
                  % (i, RUNS, r["tps"] or -1, prefill or "?"))
    finally:
        vram = _vram_mib()
        hp = _hparams_de_log(ruta_log)
        _parar(proc)

    if cfg["id"] == 1:
        _HP_ANCLA["log"] = hp
        _HP_ANCLA["ruta"] = ruta_log
        if hp:
            print("    [hparams ANCLA] %s" % hp)
        else:
            print("    [i] el log no trae arch/n_expert_used; el diagnostico EXP")
            print("        quedara 'manual' (mirar el log %s a mano)" % ruta_log)

    validas = [t for t in tps_runs[1:] if isinstance(t, (int, float)) and t > 0]
    tps = sum(validas) / len(validas) if validas else ""
    notas = []
    if len(validas) < RUNS - 1:
        notas.append("medidas incompletas")
    # warning del fit conocido (ncmoe + ngl fijo) para dejarlo registrado
    try:
        if "failed to fit" in open(ruta_log, encoding="utf-8", errors="replace").read():
            notas.append("fit-abortado (desborde VRAM: dato INVALIDO para comparar)")
    except Exception:
        pass
    d_exp = _diagnostico_exp(cfg, ruta_log)
    if d_exp:
        notas.append(d_exp)
    fila = {
        "id": cfg["id"], "nombre": cfg["nombre"],
        "familia": cfg.get("familia", ""),
        "flags": " ".join(flags),
        "tps": ("%.2f" % tps) if tps else "",
        "tps_r1": ("%.2f" % tps_runs[0]) if tps_runs[0] else "",
        "tps_r2": ("%.2f" % tps_runs[1]) if len(tps_runs) > 1 and tps_runs[1] else "",
        "tps_r3": ("%.2f" % tps_runs[2]) if len(tps_runs) > 2 and tps_runs[2] else "",
        "tps_r4": ("%.2f" % tps_runs[3]) if len(tps_runs) > 3 and tps_runs[3] else "",
        "prefill_tps": prefill, "n_gen": n_gen, "vram_mib": vram,
        "load_s": ("%.0f" % load_s) if load_s else "",
        "hparams": hp, "notas": "; ".join(notas), "fecha": _ts(),
    }
    _guardar_fila(fila)
    print("    ==> PROMEDIO (pasadas 2-%d): %s t/s%s"
          % (RUNS, fila["tps"] or "N/D",
             ("  [%s]" % fila["notas"]) if fila["notas"] else ""))
    return fila


# ============================== RANKING FINAL ==============================
def _ranking(filas):
    con_dato = [(float(f["tps"]), f) for f in filas.values()
                if f.get("tps") not in (None, "")]
    con_dato.sort(key=lambda par: par[0], reverse=True)   # fix v1.1 del 25: solo el numero
    print("\n" + "=" * 74)
    print("RANKING FINAL (t/s promedio, pasadas 2-%d, ignore_eos on)" % RUNS)
    print("=" * 74)
    for i, (tps, f) in enumerate(con_dato, 1):
        nota = ("  [%s]" % f["notas"]) if f.get("notas") else ""
        print("  %2d. %5.2f t/s  %02d-%s%s" % (i, tps, int(f["id"]), f["nombre"], nota))
    if not con_dato:
        print("  (sin datos)")
        return None
    tps_ganador, ganador = con_dato[0]
    flags_g = ganador["flags"].split() if ganador["flags"] else []
    print("-" * 74)
    print("GANADOR: %02d-%s con %.2f t/s (carga %s s)"
          % (int(ganador["id"]), ganador["nombre"], tps_ganador,
             ganador.get("load_s") or "?"))

    # Advertencias de interpretacion (nada se asume, todo se dice)
    fam = ganador.get("familia") or ""
    if "EXP" in ganador["nombre"] or fam == "EXP":
        print("\n  AVISO CALIDAD: el ganador cambia el NUMERO DE EXPERTOS ACTIVOS.")
        print("  Menos expertos = mas velocidad PERO posible perdida de calidad.")
        print("  ANTES de adoptarlo: CHATEAR-QWEN.bat y probarlo con trabajo real.")
        print("  Si la calidad no sirve: tomar el mejor config que NO sea EXP*.")
    if "-ncmoe" in flags_g or "-ngl" in flags_g:
        print("\n  AVISO LAUNCHER: el ganador trae %s." %
              ("/".join([x for x in ("-ncmoe", "-ngl") if x in flags_g])))
        print("  abrir-qwen-apex.py tiene '-cmoe' y '-ngl 99' en BASE_FLAGS: el")
        print("  -cmoe general ANULA al -ncmoe. Para adoptar: quitar '-cmoe' y")
        print("  '-ngl 99' de BASE_FLAGS a mano, y pegar FLAGS_GANADORAS al final.")
    for t, f in con_dato:
        if f.get("notas") and "fit-abortado" in f["notas"]:
            print("\n  OJO: %s mide con fit-abortado (desborde VRAM): dato invalido"
                  % f["nombre"])

    print("\nPega esto en abrir-qwen-apex.py (v2.0), linea FLAGS_GANADORAS:\n")
    print("FLAGS_GANADORAS = %s" % repr(flags_g))
    print("\nComando completo equivalente:\n")
    print("%s %s" % (RUTA_SERVER, " ".join(BASE_FLAGS + flags_g)))
    print("=" * 74)
    return ganador


# ============================== VALIDACION DE ARRANQUE ==============================
def _validar_configs():
    """Fail-fast: 30 configs, ids unicos 1..30, y TODA config estatica con
    colocacion de expertos explicita (-cmoe o -ncmoe)."""
    errores = []
    if len(CONFIGS) != 30:
        errores.append("hay %d configs, deben ser 30" % len(CONFIGS))
    ids = sorted(c["id"] for c in CONFIGS)
    if ids != list(range(1, 31)):
        errores.append("ids no son 1..30 unicos: %s" % ids)
    for c in CONFIGS:
        if c["flags"] is None:
            continue
        if "-cmoe" not in c["flags"] and "-ncmoe" not in c["flags"]:
            errores.append("%02d-%s sin -cmoe/-ncmoe (el modelo completo iria a "
                           "GPU y desbordaria)" % (c["id"], c["nombre"]))
        if "-lm" in c["flags"] and "mlock" in c["flags"]:
            errores.append("%02d-%s usa mlock (PROHIBIDO, aprendido.md §7)"
                           % (c["id"], c["nombre"]))
    return errores


# ============================== MAIN ==============================
def main():
    print("=" * 74)
    print("BARRIDO-QWEN-30 v1.0 - %d configuraciones NUEVAS, ~1 h (resume por CSV)"
          % len(CONFIGS))
    print("Campeon a superar: 21.50 t/s (-lm none, barrido-25 del 2026-10-25)")
    print("=" * 74)
    errores = _validar_configs()
    if errores:
        for e in errores:
            print("[ERROR] %s" % e)
        return 1
    if not os.path.exists(RUTA_SERVER):
        print("[ERROR] No existe el server: %s" % RUTA_SERVER)
        return 1
    if not os.path.exists(RUTA_MODELO):
        print("[ERROR] No existe el modelo: %s" % RUTA_MODELO)
        return 1
    if _health_ok():
        print("[ABORTADO] Ya hay un llama-server vivo en %s" % URL)
        print("           Medir con otro server corriendo falsea TODO. Cierrelo y relance.")
        return 1
    if os.name != "nt":
        print("[AVISO] Este script esta pensado para Windows; en otro SO solo correra")
        print("        el server si las rutas existen (modo prueba).")
    os.makedirs(DIR_LOGS, exist_ok=True)

    filas = _leer_csv()
    pendientes = [c for c in CONFIGS
                  if not (filas.get(c["id"], {}).get("tps") or "").strip()]
    ya = len(CONFIGS) - len(pendientes)
    print("[i] Ya medidas: %d | Pendientes: %d" % (ya, len(pendientes)))
    print("[i] Familias: 2 anclas + 5 EXP (expertos activos) + 3 FIT + 4 NCMOE")
    print("    + 5 afinidad + 4 prio/poll + 4 cierres + 3 combos dinamicos")
    print("[i] Checklist: Firefox/Wallpaper Engine/Copilot CERRADOS, PC sin usar,")
    print("    ventilacion libre. Cada tick del mouse es ruido de medicion.")
    try:
        input("Enter para empezar, Ctrl+C para salir... ")
    except KeyboardInterrupt:
        print("\n[cancelado]")
        return 0

    n_desde_pausa = 0
    try:
        for cfg in CONFIGS:
            if (filas.get(cfg["id"], {}).get("tps") or "").strip():
                print("[%02d/%02d] %s: ya medida (%s t/s), salto"
                      % (cfg["id"], len(CONFIGS), cfg["nombre"],
                         filas[cfg["id"]]["tps"]))
                continue
            if cfg["id"] == 28:
                # los combos se construyen AQUI: ids 1-27 ya tienen datos
                # frescos de esta corrida (o del resume)
                _combos_dinamicos(filas)
            print("\n[%02d/%02d] %s" % (cfg["id"], len(CONFIGS), cfg["nombre"]))
            fila = _medir_config(cfg)
            filas[cfg["id"]] = fila
            n_desde_pausa += 1
            if n_desde_pausa >= PAUSA_CADA and cfg["id"] < len(CONFIGS):
                print("\n[i] Pausa termica %d s para que la CPU no throttee..." % PAUSA_SEG)
                time.sleep(PAUSA_SEG)
                n_desde_pausa = 0
    except KeyboardInterrupt:
        print("\n[i] Cortado con Ctrl+C. El CSV conserva lo medido; relance para continuar.")
        _ranking(filas)
        return 0
    except Exception as e:
        print("\n[ERROR] %s" % e)
        print("       El CSV conserva lo medido; revise el log de la config fallida.")
        _ranking(filas)
        return 1

    _ranking(filas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
