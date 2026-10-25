#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BARRIDO-QWEN-25 v1.0 (2026-10-25) - barrido automatico de 25 configuraciones
==============================================================================
Que hace: prueba UNA A UNA en bucle las 25 configuraciones seleccionadas del
informe-velocidad-sweep.md (secciones 6-7), mide t/s de generacion con
protocolo fijo y al final imprime el ranking + el comando ganador.

Protocolo de medicion (riguroso, igual para todas):
  - Prompt fijo de ~230 tokens, n_predict 256, cache_prompt true
  - 4 peticiones por config: se descarta la 1a (calentamiento) y se promedia 2-4
  - temp 0 (greedy) SOLO AQUI: es benchmark, no chat (excepcion documentada;
    el NO-greedy sigue vigente para chatear-qwen.py)
  - Fuente del dato: timings.predicted_per_second del JSON de /completion
    (la misma medicion que salia en los logs del server, via API)
  - Pausa de enfriamiento 60 s cada 8 configs (el i3 al 100% durante ~2 h
    puede throttlear y falsear la comparacion)
  - CSV append: si una config ya esta medida, se SALTA -> se puede cortar con
    Ctrl+C y relanzar sin perder nada
  - Log del server por config en sweep-logs\\NN-NOMBRE.log (auditable)

Config 23-25 (COMBO): se CONSTRUYEN solas con los ganadores medidos del CSV
(combinacion real, no pre-fijada). Ver _combo_dinamico().

Antes de correr:
  1. Cerrar Firefox / Wallpaper Engine / Copilot (roban ~963 MiB VRAM+RAM)
  2. Cerrar CUALQUIER llama-server abierto (el barrido aborta si /health responde)
  3. No usar el PC mientras corre (cada tick del mouse es ruido de medicion)

Doble click: BARRIDO-QWEN.bat  |  Duracion total ~2 h (resume por CSV)
Salidas: sweep-resultados.csv + sweep-logs\\ + ranking en pantalla
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
N_PREDICT = 256          # tokens generados por pasada
RUNS = 4                 # 1 calentamiento (descartado) + 3 medidas
PAUSA_CADA = 8           # configs entre pausas termicas
PAUSA_SEG = 60
DIR_LOGS = "sweep-logs"
ARCH_CSV = "sweep-resultados.csv"

URL = "http://%s:%d" % (HOST, PORT)

# BASE = replica exacta del ganador del sweep manual del 25-oct (config V1 v1.3).
BASE_FLAGS = [
    "-m", RUTA_MODELO, "-a", ALIAS,
    "-ngl", "99", "-cmoe",
    "-c", "16384", "-b", "2048", "-ub", "256",
    "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
    "-t", "4", "--prio", "2", "--no-mmproj",
    "--host", HOST, "--port", str(PORT),
]

MTP_STD = ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2"]

# Las 25 (informe seccion 7). flags = DIFF sobre BASE_FLAGS.
CONFIGS = [
    {"id": 1,  "nombre": "BASE",         "flags": []},
    {"id": 2,  "nombre": "NP1",          "flags": ["-np", "1"]},
    {"id": 3,  "nombre": "T3",           "flags": ["-t", "3"]},
    {"id": 4,  "nombre": "T5",           "flags": ["-t", "5"]},
    {"id": 5,  "nombre": "POLL0",        "flags": ["--poll", "0"]},
    {"id": 6,  "nombre": "POLL100",      "flags": ["--poll", "100"]},
    {"id": 7,  "nombre": "LMNONE",       "flags": ["-lm", "none"]},
    {"id": 8,  "nombre": "MOECACHE256",  "flags": ["--moe-cache-mib", "256"]},
    {"id": 9,  "nombre": "MOECACHE512",  "flags": ["--moe-cache-mib", "512"]},
    {"id": 10, "nombre": "NOOPOFF",      "flags": ["--no-op-offload"]},
    {"id": 11, "nombre": "UB512",        "flags": ["-ub", "512"]},
    {"id": 12, "nombre": "KVQ4",         "flags": ["-ctk", "q4_0", "-ctv", "q4_0"]},
    {"id": 13, "nombre": "C8192",        "flags": ["-c", "8192"]},
    {"id": 14, "nombre": "MTPSTD",       "flags": list(MTP_STD)},
    {"id": 15, "nombre": "MTPNP1",       "flags": list(MTP_STD) + ["-np", "1"]},
    {"id": 16, "nombre": "MTPPMIN10",    "flags": list(MTP_STD) + ["-np", "1", "--spec-draft-p-min", "0.10"]},
    {"id": 17, "nombre": "MTPNMAX3",     "flags": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "3", "-np", "1"]},
    {"id": 18, "nombre": "MTPNMAX1",     "flags": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "1", "-np", "1"]},
    {"id": 19, "nombre": "MTPPSPLIT05",  "flags": list(MTP_STD) + ["-np", "1", "--spec-draft-p-split", "0.05"]},
    {"id": 20, "nombre": "MTPPROB",      "flags": list(MTP_STD) + ["-np", "1", "--spec-draft-sampling", "probabilistic"]},
    {"id": 21, "nombre": "MTPTD2",       "flags": list(MTP_STD) + ["-np", "1", "--spec-draft-threads", "2"]},
    {"id": 22, "nombre": "MTPCMOED",     "flags": list(MTP_STD) + ["-np", "1", "--spec-draft-cpu-moe"]},
    # 23-25: DINAMICAS (se rellenan al vuelo con los ganadores del CSV)
    {"id": 23, "nombre": "COMBO-A",        "flags": None},
    {"id": 24, "nombre": "COMBO-MTP",      "flags": None},
    {"id": 25, "nombre": "COMBO-MTP-PLUS", "flags": None},
]

# Prompt de medicion (~230 tokens de texto tecnico, fijo para todas las configs).
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

CSV_COLS = ["id", "nombre", "flags", "tps", "tps_r1", "tps_r2", "tps_r3", "tps_r4",
            "prefill_tps", "accept", "vram_mib", "notas", "fecha"]


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
    """POST /completion -> dict con tps, prefill y n de tokens."""
    body = json.dumps({
        "prompt": PROMPT,
        "n_predict": N_PREDICT,
        "temperature": 0.0,      # greedy SOLO para bench (excepcion documentada)
        "top_k": 1,
        "cache_prompt": True,    # las repeticiones no repiten prefill
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


def _accept_del_log(ruta_log):
    """Best-effort: ultima tasa de aceptacion del draft que aparezca en el log."""
    try:
        txt = open(ruta_log, "r", encoding="utf-8", errors="replace").read()
        ms = re.findall(r"accept[a-z]*[^0-9\n]*?([0-9]+(?:\.[0-9]+)?)\s*%",
                        txt, re.IGNORECASE)
        return ms[-1] if ms else ""
    except Exception:
        return ""


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
    logf = open(ruta_log, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [RUTA_SERVER] + BASE_FLAGS + flags,
        stdout=logf, stderr=subprocess.STDOUT,
        cwd=os.path.dirname(RUTA_SERVER) or ".")
    t0 = time.time()
    while time.time() - t0 < 600:          # la carga tarda ~45-90 s (logs reales)
        if proc.poll() is not None:        # el server murio al arrancar
            logf.close()
            raise RuntimeError("el server termino al arrancar (rc=%s) - ver %s"
                               % (proc.returncode, ruta_log))
        if _health_ok():
            logf.close()
            return proc
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


# ============================== COMBOS DINAMICOS ==============================
def _tps_de(filas, cid, default=None):
    try:
        return float(filas[cid]["tps"])
    except (KeyError, TypeError, ValueError):
        return default


def _combo_dinamico(filas):
    """Construye las configs 23-25 con los GANADORES medidos (fases A y B).
    Regla: para cada variable se compara el MAXIMO entre sus variantes medidas
    (p.ej. T3 vs T5) y ese maximo SOLO entra si supera a BASE. Si BASE no esta
    medida no hay referencia y la variable no entra (combo conservador)."""
    tb = t_base = _tps_de(filas, 1)   # None si BASE sin medir

    def _mejor_de(pares):
        """pares = [(id_config, flags), ...] -> (tps, flags) del maximo medido."""
        mejor = None
        for cid, fl in pares:
            t = _tps_de(filas, cid, -1.0)
            if t > -1 and (mejor is None or t > mejor[0]):
                mejor = (t, fl)
        return mejor

    ganadores = []   # flags que superaron a BASE
    if tb is not None and _tps_de(filas, 2, -1.0) > tb:
        ganadores += ["-np", "1"]
    m = _mejor_de([(3, ["-t", "3"]), (4, ["-t", "5"])])
    if m and tb is not None and m[0] > tb:
        ganadores += m[1]
    m = _mejor_de([(5, ["--poll", "0"]), (6, ["--poll", "100"])])
    if m and tb is not None and m[0] > tb:
        ganadores += m[1]
    if tb is not None and _tps_de(filas, 7, -1.0) > tb:
        ganadores += ["-lm", "none"]
    m = _mejor_de([(8, ["--moe-cache-mib", "256"]), (9, ["--moe-cache-mib", "512"])])
    if m and tb is not None and m[0] > tb:
        ganadores += m[1]

    combo_a = list(ganadores) if ganadores else ["-np", "1"]

    # mejor config MTP medida (ids 14-22)
    mejor_mtp_id, mejor_mtp_tps = None, -1.0
    for cid in range(14, 23):
        t = _tps_de(filas, cid, -1.0)
        if t > mejor_mtp_tps:
            mejor_mtp_id, mejor_mtp_tps = cid, t

    cfg24 = list(combo_a) + list(MTP_STD)
    cfg25 = list(combo_a) + list(MTP_STD) + ["--spec-draft-p-min", "0.10"]
    if mejor_mtp_id is not None and mejor_mtp_tps > 0:
        # el MTP ganador entra COMPLETO (si trae -np 1 duplicado con combo_a,
        # el ultimo gana en argparse: inofensivo; quitarlo perderia el caso
        # "np solo ayuda con MTP")
        extra = filas[mejor_mtp_id].get("flags") or ""
        fl = extra.split()
        cfg24 = list(combo_a) + fl
        cfg25 = list(combo_a) + fl          # afinado final = mejor MTP medida
    for c in (CONFIGS):
        if c["id"] == 23:
            c["flags"] = combo_a
        elif c["id"] == 24:
            c["flags"] = cfg24
        elif c["id"] == 25:
            c["flags"] = cfg25
    print("[i] Combos dinamicos construidos con los ganadores medidos:")
    print("    23 COMBO-A        =", " ".join(combo_a) or "(BASE puro)")
    print("    24 COMBO-MTP      =", " ".join(cfg24))
    print("    25 COMBO-MTP-PLUS =", " ".join(cfg25))


# ============================== MEDIR UNA CONFIG ==============================
def _medir_config(cfg):
    nombre_log = "%s-%02d-%s.log" % (time.strftime("%Y%m%d"), cfg["id"], cfg["nombre"])
    ruta_log = os.path.join(DIR_LOGS, nombre_log)
    flags = cfg["flags"] if cfg["flags"] is not None else []
    print("    flags: %s" % (" ".join(flags) if flags else "(BASE)"))
    t_arranque = time.time()
    proc = _lanzar_y_esperar(flags, ruta_log)
    print("    server arriba en %d s, midiendo %d pasadas x %d tokens..."
          % (time.time() - t_arranque, RUNS, N_PREDICT))
    tps_runs, prefill, notas = [], "", ""
    try:
        for i in range(1, RUNS + 1):
            r = _medir_una_vez()
            tps_runs.append(r["tps"])
            if r["prefill"]:
                prefill = "%.2f" % r["prefill"]
            print("      pasada %d/%d: %.2f t/s (gen)  prefill %s t/s"
                  % (i, RUNS, r["tps"] or -1, prefill or "?"))
    finally:
        accept = _accept_del_log(ruta_log)
        vram = _vram_mib()
        _parar(proc)

    validas = [t for t in tps_runs[1:] if isinstance(t, (int, float)) and t > 0]
    tps = sum(validas) / len(validas) if validas else ""
    if len(validas) < RUNS - 1:
        notas = "medidas incompletas"
    # warning del fit conocido (ncmoe + ngl fijo) para dejarlo registrado
    try:
        if "failed to fit" in open(ruta_log, encoding="utf-8", errors="replace").read():
            notas = (notas + "; " if notas else "") + "fit-abortado"
    except Exception:
        pass
    fila = {
        "id": cfg["id"], "nombre": cfg["nombre"],
        "flags": " ".join(flags), "tps": ("%.2f" % tps) if tps else "",
        "tps_r1": ("%.2f" % tps_runs[0]) if tps_runs[0] else "",
        "tps_r2": ("%.2f" % tps_runs[1]) if len(tps_runs) > 1 and tps_runs[1] else "",
        "tps_r3": ("%.2f" % tps_runs[2]) if len(tps_runs) > 2 and tps_runs[2] else "",
        "tps_r4": ("%.2f" % tps_runs[3]) if len(tps_runs) > 3 and tps_runs[3] else "",
        "prefill_tps": prefill, "accept": accept, "vram_mib": vram,
        "notas": notas, "fecha": _ts(),
    }
    _guardar_fila(fila)
    print("    ==> PROMEDIO (pasadas 2-%d): %s t/s%s"
          % (RUNS, fila["tps"] or "N/D",
             ("  [accept %s%%]" % accept) if accept else ""))
    return fila


# ============================== RANKING FINAL ==============================
def _ranking(filas):
    con_dato = [(float(f["tps"]), f) for f in filas.values()
                if f.get("tps") not in (None, "")]
    con_dato.sort(reverse=True)
    print("\n" + "=" * 74)
    print("RANKING FINAL (t/s promedio, pasadas 2-%d)" % RUNS)
    print("=" * 74)
    for i, (tps, f) in enumerate(con_dato, 1):
        extra = ("  accept %s%%" % f["accept"]) if f.get("accept") else ""
        print("  %2d. %5.2f t/s  %02d-%s%s" % (i, tps, int(f["id"]), f["nombre"], extra))
    if not con_dato:
        print("  (sin datos)")
        return None
    tps_ganador, ganador = con_dato[0]
    flags_g = ganador["flags"].split() if ganador["flags"] else []
    print("-" * 74)
    print("GANADOR: %02d-%s con %.2f t/s" % (int(ganador["id"]), ganador["nombre"], tps_ganador))
    print("\nPega esto en abrir-qwen-apex.py (v2.0), linea FLAGS_GANADORAS:\n")
    print("FLAGS_GANADORAS = %s" % repr(flags_g))
    print("\nComando completo equivalente:\n")
    print("%s %s" % (RUTA_SERVER, " ".join(BASE_FLAGS + flags_g)))
    print("=" * 74)
    return ganador


# ============================== MAIN ==============================
def main():
    print("=" * 74)
    print("BARRIDO-QWEN-25 v1.0 - %d configuraciones, ~2 h (resume por CSV)" % len(CONFIGS))
    print("=" * 74)
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
            if cfg["id"] == 23:
                # los combos se construyen AQUI: ids 1-22 ya tienen datos frescos
                # de esta corrida (o del resume). Es el "buscar combinaciones":
                # el combo se arma con los ganadores MEDIDOS, no pre-fijados.
                _combo_dinamico(filas)
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
