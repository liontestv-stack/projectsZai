#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
barrido-total.py v1.0 — EL INSTRUMENTO TOTAL (encargo del Director, 26-oct-2026)
================================================================================
"mira tu crea un .py que iniciar que haga todas las pruebas que quieras"
Hace correr SOLO la escalera completa, con los flags VERBATIM del dump b11856
y del launcher v2.1 (no hay ni una flag inventada). Fases:

  A  Auditoria del sistema (turbo, page faults, RAM/canales, GPU, Defender,
     herramientas) - sin server, ~2 min
  B  RE-ANCLA con el launcher v2.1 EXACTO + log capturado -> resuelve el
     misterio 17.11 (adjunto 25-oct) vs 21.53 (barrido-30), ~10 min
  C  Barrido de configs NO medidas o pendientes (TB8, UB2K, PRIOB2,
     NCM39Q8+UB1K, NCM37C4+UB1K, MLOCK, OP64), ~5 min/config
  D  Familia EXP (T1): dump de claves expert* del GGUF + retest
     --override-kv con la clave EXACTA y dosis-respuesta dinamica (V-2, V-4);
     cirugia de copia solo con --cirugia (llama.cpp gguf_new_metadata.py)
  E  Especulativas (T2 + B6): MTP-A/B/C con acceptance del log capturado +
     EAGLE-3 opcional (--eagle3 RUTA); criterios pre-registrados del plan;
     p-min 0.85 automatico si acc < 50%; detector de basura #23577
  F  Requant IQ2_M (OPCIONAL, --con-requant: requiere llama-quantize,
     llama-imatrix, --imatrix-data y ~30 GB de disco)
  G  Informe JSON + MD + CSV historial (crash-safe: parcial tras cada config)

Reglas de la casa que respeta este script:
  - [M] solo mediciones; N/D cuando no hay dato; nunca se inventa nada.
  - Prompts DISTINTOS por pasada (anti-inflado spec, barrido-25/30).
  - Acceptance SOLO del log del server (regexes multi-patron del tester).
  - Una variable por vez; ancla +-ruido (max(0.5 t/s, 2%) = zona muerta).
  - Jamas se toca el GGUF original; copias solo a _lab/ y solo si hay disco.

Uso:
  python barrido-total.py                    -> fases A,B,C,D,E,G (completo)
  python barrido-total.py --quick            -> version corta (~35-50 min)
  python barrido-total.py --fases A,B,C      -> solo esas fases
  python barrido-total.py --si               -> mata el server vivo si lo hay
  python barrido-total.py --eagle3 RUTA.gguf -> anade E4 (EAGLE-3)
"""
import argparse
import ctypes
import json
import os
import platform
import re
import shutil
import socket
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

# ------------------------- constantes del proyecto --------------------------
VERSION = "barrido-total v1.0 (2026-10-26)"

# Verbatim abrir-qwen-apex.py v2.1-minimal (repo InformacionCritica)
RUTA_SERVER_DEF = r"D:\llama.cpp\llama-server.exe"
RUTA_MODELO_DEF = (r"D:\ZLia\models"
                   r"\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf")
BASE_FLAGS_LAUNCHER = [
    "-ngl", "99", "-cmoe",
    "-c", "16384", "-b", "2048", "-ub", "256",
    "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
    "-t", "4", "--prio", "2", "--no-mmproj",
    "--temp", "1.0", "--top-k", "20", "--top-p", "0.95",
    "--min-p", "0.0", "--presence-penalty", "0.0",
]  # verbatim; -m/-a/--host/--port van aparte
FLAGS_GANADORAS = ["-lm", "none", "-ub", "1024", "-b", "4096"]  # ORO-UB1K

# Anclas historicas [M]
ANCLA_BARRIDO30 = 21.53   # config 32 ORO-UB1K, 26-oct-2026
MEDICION_ADJUNTO = 17.11  # informe-mtp-adjunto 2026-10-25 (flags invisibles)

PUERTO_DEF = 9931
HOST_DEF = "127.0.0.1"

STD_TIMINGS = {"prompt_n", "prompt_ms", "prompt_per_token_ms", "prompt_per_second",
               "predicted_n", "predicted_ms", "predicted_per_token_ms",
               "predicted_per_second"}

SANITY_PARES = [
    ("Cuanto es 17 x 23? Responde solo el numero.", ["391"]),
    ("Quien escribio Don Quijote? Responde muy corto.", ["cervantes"]),
    ("Que planeta es conocido como el planeta rojo? Responde muy corto.",
     ["marte"]),
]

USE_COLOR = sys.stdout.isatty() if hasattr(sys.stdout, "isatty") else False


def _c(txt, code):
    if not USE_COLOR:
        return str(txt)
    return "\x1b[%sm%s\x1b[0m" % (code, txt)


def bold(t): return _c(t, "1")
def red(t): return _c(t, "91")
def green(t): return _c(t, "92")
def yellow(t): return _c(t, "93")
def cyan(t): return _c(t, "96")
def gray(t): return _c(t, "90")


def section(tid, titulo):
    print("")
    print(gray("=" * 78))
    print(bold("[%s] %s" % (tid, titulo)))
    print(gray("=" * 78))


def kv(k, v, w=46):
    print("  %-*s %s" % (w, k + ":", v))


# ------------------------------- estadistica --------------------------------
def media(xs):
    return statistics.fmean(xs) if xs else 0.0


def mediana(xs):
    return statistics.median(xs) if xs else 0.0


def desvest(xs):
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def ruido_ts(ancla):
    """Zona muerta pre-registrada del plan: max(0.5 t/s, 2% del ancla)."""
    return max(0.5, 0.02 * ancla)


def clasifica(decode_medio, ancla):
    """-> (veredicto, delta_pct) con la zona muerta del plan."""
    if not ancla or not decode_medio:
        return "N/D", None
    delta = (decode_medio / float(ancla) - 1.0) * 100.0
    rz = ruido_ts(ancla)
    if decode_medio >= ancla + rz:
        return "GANA", delta
    if decode_medio <= ancla - rz:
        return "PIERDE", delta
    return "EMPATA", delta


# --------------------------- prompts de benchmark ---------------------------
# Protocolo anti-inflado (barrido-25/30 + tester-mtp): prompts DISTINTOS.
_PALABRAS = ("the of and to in is that it for as with was on are by this be from or an "
             "which one had not but what all were when we there can been more if will "
             "would about their other new some could time these two may then do first "
             "any my now such like our over man me even most made after also data "
             "model token system cache memory server decode prompt layer expert route "
             "draft accept predict stream batch kernel buffer context window weight "
             "matrix vector quantize").split()


def prompt_ref(n_tokens, semilla=0):
    """Prompt sintetico determinista; semilla distinta -> texto distinto."""
    n = max(8, int(n_tokens))
    palabras = [_PALABRAS[(semilla * 7 + j * 13) % len(_PALABRAS)] for j in range(n)]
    return ("Reference text %d for benchmarking. Read it and continue neutrally.\n"
            % semilla + " ".join(palabras))


# ---------------------------------- HTTP ------------------------------------
class TestSkip(Exception):
    """Una prueba que no aplica aqui: se omite, no se inventa."""
    pass


def _req(url, payload=None, timeout=30):
    data = None
    hdrs = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=hdrs,
                                 method="POST" if data is not None else "GET")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="replace")
    return body, (time.perf_counter() - t0) * 1000.0


def http_json(url, payload=None, timeout=30):
    body, ms = _req(url, payload, timeout)
    try:
        return json.loads(body), ms
    except ValueError:
        raise RuntimeError("respuesta no-JSON de %s: %s" % (url, body[:200]))


def salud(url, timeout=3):
    """-> (ok | cargando | apagado, detalle)."""
    try:
        obj, _ = http_json(url, timeout=timeout)
        return "ok", str(obj.get("status", obj))
    except urllib.error.HTTPError as e:
        return "cargando", "HTTP %s" % e.code
    except Exception as e:
        return "apagado", "%s: %s" % (type(e).__name__, e)


class Cliente:
    """Cliente /completion probado en tester-mtp.py v1.1 (19/19 QA)."""

    def __init__(self, host, port):
        self.base = "http://%s:%d" % (host, port)
        self.headers = {"Content-Type": "application/json"}

    def completion(self, payload, stream=True, timeout=900):
        payload = dict(payload)
        payload.setdefault("cache_prompt", True)
        if stream:
            return self._stream(payload, timeout)
        return self._nostream(payload, timeout)

    def _nostream(self, payload, timeout):
        obj, ms = http_json(self.base + "/completion", payload, timeout)
        if isinstance(obj, dict) and obj.get("error"):
            raise RuntimeError("server: %s" % json.dumps(obj["error"])[:300])
        tim = obj.get("timings") or {}
        return {"text": obj.get("content", "") or "",
                "wall_ms": ms, "timings": tim, "final": obj,
                "tokens_evaluated": obj.get("tokens_evaluated"),
                "tokens_predicted": obj.get("tokens_predicted")}

    def _stream(self, payload, timeout):
        payload = dict(payload)
        payload["stream"] = True
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base + "/completion", data=data,
                                     headers=self.headers, method="POST")
        t0 = time.perf_counter()
        ttft = None
        piezas = []
        tim = {}
        final = {}
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                linea = raw.decode("utf-8", errors="replace").strip()
                if not linea or not linea.startswith("data:"):
                    continue
                d = linea[5:].strip()
                if d == "[DONE]":
                    break
                try:
                    obj = json.loads(d)
                except ValueError:
                    continue
                if obj.get("error"):
                    raise RuntimeError("server: %s" % json.dumps(obj["error"])[:300])
                if obj.get("timings"):
                    tim = obj["timings"]
                contenido = obj.get("content")
                if contenido:
                    if ttft is None:
                        ttft = (time.perf_counter() - t0) * 1000.0
                    piezas.append(contenido)
                final = obj
        wall = (time.perf_counter() - t0) * 1000.0
        return {"text": "".join(piezas), "ttft_ms": ttft, "wall_ms": wall,
                "timings": tim, "final": final,
                "tokens_evaluated": final.get("tokens_evaluated"),
                "tokens_predicted": final.get("tokens_predicted")}


def decode_ts(r):
    """t/s de generacion [M]: server timings, fallback cliente."""
    tim = r.get("timings") or {}
    v = tim.get("predicted_per_second")
    if v:
        return float(v), "server"
    pn = r.get("tokens_predicted") or 0
    pms = tim.get("predicted_ms")
    if pn and pms:
        return pn / (pms / 1000.0), "server"
    return 0.0, "N/D"


def prefill_ts(r):
    """t/s de prefill [M] (server timings)."""
    tim = r.get("timings") or {}
    v = tim.get("prompt_per_second")
    if v:
        return float(v), "server"
    tev = r.get("tokens_evaluated") or 0
    pms = tim.get("prompt_ms")
    if tev and pms:
        return tev / (pms / 1000.0), "server"
    return 0.0, "N/D"


# --------------------- acceptance del log (tester verbatim) ------------------
RE_ACC_PCT = re.compile(r"accept[^\n]*?(\d{1,3}(?:\.\d+)?)\s*%", re.IGNORECASE)
RE_ACC_PAR = re.compile(r"accepted?\s*[:=]?\s*(\d{1,3})\s*/\s*(\d{1,3})", re.IGNORECASE)
RE_DRAFTED = re.compile(
    r"drafted?\s*[:=,]?\s*(\d{1,4})[^\n]{0,40}?accept(?:ed)?\s*[:=]?\s*(\d{1,4})",
    re.IGNORECASE)
KW_LOG = ("accept", "draft", "spec", "mtp")


def aceptacion_de_log(txt):
    """Multi-patron sobre el log del server (best-effort, NO se inventa)."""
    out = {"tasas": [], "pares": [], "eventos": 0, "muestras": []}
    if not txt:
        return out
    for a, b in RE_ACC_PAR.findall(txt):
        try:
            b = int(b)
            if b > 0:
                out["pares"].append((min(int(a), b), b))
        except ValueError:
            pass
    for a in RE_ACC_PCT.findall(txt):
        try:
            v = float(a) / 100.0
            if 0.0 <= v <= 1.0:
                out["tasas"].append(v)
        except ValueError:
            pass
    for a, b in RE_DRAFTED.findall(txt):
        try:
            b = int(b)
            if b > 0:
                out["pares"].append((min(int(a), b), b))
        except ValueError:
            pass
    out["eventos"] = len(out["pares"]) + len(out["tasas"])
    vistas = set()
    for linea in txt.splitlines():
        ll = linea.lower()
        if any(w in ll for w in KW_LOG):
            l2 = linea.strip()[:160]
            if l2 and l2 not in vistas:
                vistas.add(l2)
                out["muestras"].append(l2)
            if len(vistas) >= 8:
                break
    return out


def tasa_media(acc):
    if not acc or (not acc["pares"] and not acc["tasas"]):
        return None
    xs = [a / float(b) for a, b in acc["pares"]] + list(acc["tasas"])
    return media(xs)


def basura_en(texto):
    """Firma de corrupcion del bug #23577: '////' y puntuacion degenerada."""
    if not texto:
        return 0
    n = len(re.findall(r"(?:/{4,}|\\{4,})", texto))
    n += len(re.findall(r"([!?.,;:<>@#*~^]){8,}", texto))
    return n


# ------------------------------ recursos ------------------------------------
def vram_mib():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,temperature.gpu,clocks.sm",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10)
        partes = [p.strip() for p in out.stdout.strip().splitlines()[0].split(",")]
        return {"used": int(partes[0]), "total": int(partes[1]),
                "temp_c": partes[2] if len(partes) > 2 else "N/D",
                "clock_sm": partes[3] if len(partes) > 3 else "N/D"}
    except Exception:
        return None


def ram_sistema():
    """RAM total/libre en MiB via GlobalMemoryStatusEx (stdlib, sin locale)."""
    try:
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
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
        return {"total_mib": st.ullTotalPhys // (1024 * 1024),
                "libre_mib": st.ullAvailPhys // (1024 * 1024),
                "carga_pct": st.dwMemoryLoad}
    except Exception:
        try:
            # fallback POSIX para self-test
            with open("/proc/meminfo") as f:
                info = {l.split(":")[0]: int(l.split()[1]) for l in f if ":" in l}
            tot = info.get("MemTotal", 0) // 1024
            lib = info.get("MemAvailable", 0) // 1024
            return {"total_mib": tot, "libre_mib": lib,
                    "carga_pct": int(100 * (tot - lib) / tot) if tot else 0}
        except Exception:
            return None


def ram_proceso(nombre="llama", pid=None):
    """RAM del server en MiB (psutil opcional)."""
    try:
        import psutil
    except ImportError:
        return None
    try:
        if pid:
            return psutil.Process(pid).memory_info().rss / (1024.0 * 1024.0)
        for p in psutil.process_iter(["name"]):
            nm = (p.info.get("name") or "").lower()
            if nombre in nm:
                return p.memory_info().rss / (1024.0 * 1024.0)
    except Exception:
        return None
    return None


def powershell(cmd, timeout=30):
    """Ejecuta powershell -NoProfile y devuelve stdout o None (N/D honesto)."""
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                             capture_output=True, text=True, timeout=timeout)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
        return None
    except Exception:
        return None


def cpu_info():
    """Nucleos fisicos/logicos + nombre (Win32_Processor; fallback N/D)."""
    out = powershell("Get-CimInstance Win32_Processor | Select-Object -First 1 "
                     "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed "
                     "| ConvertTo-Json -Compress", timeout=20)
    try:
        o = json.loads(out)
        return {"nombre": o.get("Name"), "fisicos": int(o.get("NumberOfCores") or 0),
                "logicos": int(o.get("NumberOfLogicalProcessors") or 0),
                "mhz_base": int(o.get("MaxClockSpeed") or 0)}
    except Exception:
        return {"nombre": platform.processor() or "N/D", "fisicos": os.cpu_count(),
                "logicos": os.cpu_count(), "mhz_base": 0}


def dimms():
    """Modulos RAM verbatim (corroborar dual-channel; CPU-Z es la referencia)."""
    out = powershell("Get-CimInstance Win32_PhysicalMemory | Select-Object "
                     "BankLabel,DeviceLocator,Capacity,Speed,ConfiguredClockSpeed "
                     "| ConvertTo-Json -Compress", timeout=20)
    try:
        o = json.loads(out)
        if isinstance(o, dict):
            o = [o]
        filas = []
        for d in o:
            filas.append({"slot": str(d.get("BankLabel") or d.get("DeviceLocator") or "?"),
                          "gib": round((int(d.get("Capacity") or 0) / (1024.0 ** 3)), 1),
                          "speed": d.get("ConfiguredClockSpeed") or d.get("Speed")})
        slots = {f["slot"].split(" ")[0].upper() for f in filas}
        canales = len(slots) if len(filas) > 1 else 1
        return {"filas": filas, "canales_estimados": canales}
    except Exception:
        return None


def perf_muestras(n=6, intervalo=1.0):
    """Muestreo locale-proof via clases CIM WMI (nombres siempre en ingles):
    - PercentProcessorPerformance: >100 => turbo activo
    - PageFaultsPersec: fallos de pagina del sistema
    Devuelve dict con maximos/medios; N/D si no hay powershell."""
    res = {"turbo_pct_max": None, "turbo_pct_medio": None,
           "pagefaults_max": None, "pagefaults_medio": None, "n": 0}
    tps, pfs = [], []
    for _ in range(n):
        t = powershell("Get-CimInstance Win32_PerfFormattedData_Counters_"
                       "ProcessorInformation -Filter \"Name='_Total'\" | "
                       "Select-Object -ExpandProperty PercentProcessorPerformance",
                       timeout=15)
        if t is not None:
            try:
                tps.append(float(t.strip().strip("'")))
            except ValueError:
                pass
        p = powershell("Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory | "
                       "Select-Object -ExpandProperty PageFaultsPersec", timeout=15)
        if p is not None:
            try:
                pfs.append(float(p.strip()))
            except ValueError:
                pass
        if _ < n - 1:
            time.sleep(intervalo)
    if tps:
        res["turbo_pct_max"] = max(tps)
        res["turbo_pct_medio"] = media(tps)
    if pfs:
        res["pagefaults_max"] = max(pfs)
        res["pagefaults_medio"] = media(pfs)
    res["n"] = max(len(tps), len(pfs))
    return res


class MuestreadorPerf(threading.Thread):
    """Muestrea turbo/pagefaults EN PARALELO mientras se mide decode (fase B)."""

    def __init__(self, intervalo=2.0):
        super().__init__(daemon=True)
        self.intervalo = intervalo
        self.parar = threading.Event()
        self.tps, self.pfs = [], []

    def run(self):
        while not self.parar.is_set():
            t = powershell("Get-CimInstance Win32_PerfFormattedData_Counters_"
                           "ProcessorInformation -Filter \"Name='_Total'\" | "
                           "Select-Object -ExpandProperty PercentProcessorPerformance",
                           timeout=15)
            if t is not None:
                try:
                    self.tps.append(float(t.strip().strip("'")))
                except ValueError:
                    pass
            p = powershell("Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory | "
                           "Select-Object -ExpandProperty PageFaultsPersec", timeout=15)
            if p is not None:
                try:
                    self.pfs.append(float(p.strip()))
                except ValueError:
                    pass
            self.parar.wait(self.intervalo)

    def resultado(self):
        self.parar.set()
        try:
            self.join(timeout=20)
        except Exception:
            pass
        r = {"turbo_pct_max": max(self.tps) if self.tps else None,
             "turbo_pct_medio": media(self.tps) if self.tps else None,
             "pagefaults_max": max(self.pfs) if self.pfs else None,
             "pagefaults_medio": media(self.pfs) if self.pfs else None,
             "muestras": len(self.tps)}
        return r


def defender_exclusiones():
    out = powershell("Get-MpPreference | Select-Object -ExpandProperty "
                     "ExclusionPath | ConvertTo-Json -Compress", timeout=20)
    if out is None:
        return None  # N/D (sin permiso o sin Defender)
    if not out.strip():
        return []
    try:
        o = json.loads(out)
        return o if isinstance(o, list) else [o]
    except ValueError:
        return [out.strip()]


def free_gib(ruta):
    try:
        unidad = os.path.splitdrive(os.path.abspath(ruta))[0] or os.path.splitdrive(os.getcwd())[0]
        return shutil.disk_usage(unidad + os.sep).free / (1024.0 ** 3)
    except Exception:
        return None


# ------------------------- ciclo de vida del server -------------------------
def puerto_libre(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        s.close()
        return False  # alguien responde
    except Exception:
        return True


def esperar_puerto_libre(host, port, intentos=10, pausa=2.0):
    """Fix Bug-5 del tester: esperar a que el puerto quede libre de verdad."""
    for i in range(intentos):
        if puerto_libre(host, port):
            return True
        time.sleep(pausa)
    return False


def matar_server(nombre_img=None):
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/IM", nombre_img or "llama-server.exe",
                            "/T"], capture_output=True, timeout=20)
        else:
            subprocess.run(["pkill", "-f", "llama-server|mock_llamacpp"],
                           capture_output=True, timeout=10)
        time.sleep(3)
        return True
    except Exception:
        return False


def parar(proc):
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


def construir_flags(args, extra=None, quitar_cmoe=False, modelo=None):
    """Invocacion launcher v2.1 EXACTA (+ FLAGS_GANADORAS al final) + extras.
    Last-wins verificado en barridos (el ultimo valor gana en este build).
    quitar_cmoe=True replica el mecanismo del barrido-30: el -cmoe/-ncmoe va
    POR CONFIG (asi NCM puede probar -ncmoe sin el -cmoe del launcher)."""
    base = [f for f in BASE_FLAGS_LAUNCHER if not (quitar_cmoe and f == "-cmoe")]
    fl = ["-m", modelo or args.modelo, "-a", "apex35b"] + base + [
        "--host", args.host, "--port", str(args.port)] + list(FLAGS_GANADORAS)
    if extra:
        fl += list(extra)
    return fl


def lanzar_server(args, flags, env_extra=None, ruta_log="server.log"):
    logf = open(ruta_log, "wb")
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.Popen([args.server] + flags, stdout=logf,
                                stderr=subprocess.STDOUT, cwd=os.path.dirname(args.server) or ".",
                                env=env)
    except Exception as e:
        logf.close()
        raise RuntimeError("no pude lanzar el server: %s" % e)
    logf.close()  # el hijo conserva el handle abierto
    return proc


def esperar_salud(args, proc, ruta_log, timeout=900):
    """Espera /health; si el proceso muere, devuelve las ultimas lineas del log."""
    url = "http://%s:%d/health" % (args.host, args.port)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc is not None and proc.poll() is not None:
            cola = ""
            try:
                with open(ruta_log, "r", errors="replace") as f:
                    cola = "".join(f.readlines()[-12:])
            except Exception:
                pass
            raise RuntimeError("el server termino al arrancar (rc=%s)\n--- log ---\n%s"
                               % (proc.returncode, cola))
        est, _ = salud(url)
        if est == "ok":
            return time.time() - t0
        time.sleep(2)
    raise RuntimeError("timeout %d s esperando /health - ver %s" % (timeout, ruta_log))


def leer_log(ruta_log):
    try:
        with open(ruta_log, "r", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


# ============================ MOTOR DEL LABORATORIO ==========================
class Lab:
    def __init__(self, args):
        self.args = args
        self.cli = Cliente(args.host, args.port)
        self.res = {"meta": self._meta(), "A": None, "B": None,
                    "C": [], "D": None, "E": [], "F": None}
        self.ancla_medida = None      # [M] de la fase B
        self.carpetas = self._carpetas()
        self.textos = []              # todas las salidas -> basura #23577
        self._cargar_parcial_previo()

    def _cargar_parcial_previo(self):
        """Reanudacion: si hay parcial de una corrida anterior del MISMO modelo,
        arranco desde el (multi-sesion sin perder fases). --fresco ignora."""
        if getattr(self.args, "fresco", False):
            return
        base = self.args.out or "informe-barrido-total"
        ruta = base + "-parcial.json"
        if not os.path.isfile(ruta):
            return
        try:
            with open(ruta, encoding="utf-8") as f:
                prev = json.load(f)
            pm = prev.get("meta") or {}
            if pm.get("modelo") != self.args.modelo:
                print(gray("  (parcial previo de OTRO modelo: empiezo de cero)"))
                return
            n = 0
            for k in ("A", "B", "D", "F"):
                if prev.get(k):
                    self.res[k] = prev[k]
                    n += 1
            for k in ("C", "E"):
                if prev.get(k):
                    self.res[k] = prev[k]
                    n += 1
            b = self.res.get("B") or {}
            if b.get("decode_medio"):
                self.ancla_medida = b["decode_medio"]
            if n:
                print(gray("  (reanudo desde el parcial: %d fase(s) previas;"
                           " usa --fresco para empezar de cero)" % n))
        except Exception as e:
            print(gray("  (parcial previo ilegible: %s)" % e))

    def _meta(self):
        return {"version": VERSION, "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "modelo": self.args.modelo, "server": self.args.server,
                "host": self.args.host, "puerto": self.args.port,
                "quick": self.args.quick, "ancla_hist": self.args.ancla,
                "medicion_adjunto_25oct": MEDICION_ADJUNTO}

    def _carpetas(self):
        lab = os.path.join(os.path.dirname(os.path.abspath(self.args.modelo))
                           or ".", "_lab")
        if not os.path.isdir(lab):
            try:
                os.makedirs(lab)
            except Exception:
                lab = os.path.abspath("_lab")
                if not os.path.isdir(lab):
                    os.makedirs(lab)
        return {"lab": lab, "logs": lab}

    def guardar_parcial(self):
        """Crash-safe: volcar TODO lo acumulado hasta ahora."""
        try:
            base = self.args.out or "informe-barrido-total"
            with open(base + "-parcial.json", "w", encoding="utf-8") as f:
                json.dump(self.res, f, ensure_ascii=False, indent=1, default=str)
        except Exception as e:
            print(gray("  (no pude guardar parcial: %s)" % e))

    def ancla_referencia(self):
        """El ancla para comparar: si ya medimos la B, esa; si no, la historica."""
        return self.ancla_medida or self.args.ancla

    # ------------------------------------------------------------------ A --
    def fase_a(self):
        section("A", "AUDITORIA DEL SISTEMA (sin server, [M] + N/D honesto)")
        a = {}
        info = cpu_info()
        a["cpu"] = info
        kv("CPU", "%s (%d fisicos / %d logicos, base %s MHz)"
           % (info["nombre"], info["fisicos"], info["logicos"],
              info["mhz_base"] or "N/D"))
        r = ram_sistema()
        a["ram"] = r
        if r:
            kv("RAM", "total %d MiB, libre %d MiB, carga %d%%"
               % (r["total_mib"], r["libre_mib"], r["carga_pct"]))
        d = dimms()
        a["dimms"] = d
        if d:
            kv("DIMMs (corroboracion; CPU-Z manda)", "; ".join(
                "%s %.1f GiB @%s" % (f["slot"], f["gib"], f["speed"])
                for f in d["filas"]))
            kv("Canales estimados", "%s (Director confirmo DUAL con CPU-Z)"
               % d["canales_estimados"])
        g = vram_mib()
        a["gpu"] = g
        if g:
            kv("GPU", "VRAM %d/%d MiB, %s C, reloj SM %s"
               % (g["used"], g["total"], g["temp_c"], g["clock_sm"]))
        disc = free_gib(self.args.modelo)
        a["disco_libre_gib"] = disc
        kv("Disco libre (unidad del modelo)", "%.1f GiB" % disc if disc else "N/D")
        p = perf_muestras(n=5, intervalo=1.0)
        a["perf_idle"] = p
        if p["turbo_pct_max"] is not None:
            kv("Turbo (PercentProcessorPerformance, idle)",
               "max %.0f%% (>100 = turbo activo)" % p["turbo_pct_max"])
        else:
            kv("Turbo", "N/D (sin powershell CIM)")
        if p["pagefaults_max"] is not None:
            kv("Page faults/s (idle)", "max %.0f" % p["pagefaults_max"])
        dfe = defender_exclusiones()
        a["defender_exclusiones"] = dfe
        if dfe is None:
            kv("Defender exclusiones", "N/D (no legible sin admin?)")
        elif not dfe:
            kv("Defender exclusiones", yellow("NINGUNA -> G6 pendiente"))
        else:
            kv("Defender exclusiones", "%d rutas ok" % len(dfe))
        # herramientas
        a["tools"] = {
            "server_existe": os.path.isfile(self.args.server),
            "gguf_py": _importa_gguf(),
            "psutil": _importa("psutil"),
            "quantize": _busca_hermano("llama-quantize.exe", self.args.server),
            "imatrix": _busca_hermano("llama-imatrix.exe", self.args.server),
        }
        kv("Server exe", "ok" if a["tools"]["server_existe"]
           else red("NO EXISTE: %s" % self.args.server))
        kv("gguf-py (fase D)", "ok" if a["tools"]["gguf_py"] else "falta (pip install gguf)")
        kv("llama-quantize/imatrix (fase F)",
           "%s / %s" % (a["tools"]["quantize"] or "N/D", a["tools"]["imatrix"] or "N/D"))
        self.res["A"] = a
        self.guardar_parcial()

    # ------------------------------------------------------------------ B --
    def _medir_decode(self, pasadas, n_predict=256, semilla0=400):
        """Decode [M]: prompts DISTINTOS, temp 0, ignore_eos, warmup aparte."""
        serie = []
        for i in range(pasadas):
            p = prompt_ref(270 + i, semilla0 + 100 * i)
            r = self.cli.completion({"prompt": p, "n_predict": n_predict,
                                     "temperature": 0, "seed": 42 + i,
                                     "ignore_eos": True}, stream=True,
                                    timeout=self.args.timeout)
            self.textos.append(r["text"])
            v, fuente = decode_ts(r)
            serie.append(v)
            kv("decode %d/%d" % (i + 1, pasadas), "%.2f t/s (%s)"
               % (v, fuente))
        return serie

    def _medir_prefill(self, n_tokens=1050):
        p = prompt_ref(n_tokens, semilla=99001)
        r = self.cli.completion({"prompt": p, "n_predict": 1,
                                 "temperature": 0, "seed": 7}, stream=True,
                                timeout=self.args.timeout)
        v, fuente = prefill_ts(r)
        return v, r.get("timings") or {}, fuente

    def _sanity(self):
        ok = 0
        for q, claves in SANITY_PARES:
            r = self.cli.completion({"prompt": q, "n_predict": 48,
                                     "temperature": 0, "seed": 1}, stream=True,
                                    timeout=self.args.timeout)
            self.textos.append(r["text"])
            txt = (r["text"] or "").lower()
            if any(k in txt for k in claves):
                ok += 1
        return ok, len(SANITY_PARES)

    def _medir_config(self, nombre, extra, quitar_cmoe=False, env_extra=None,
                      modelo=None, spec=False, pasadas=None, log_nombre=None):
        """Ciclo completo: lanzar -> salud -> warmup -> decode -> prefill ->
        ttft calido -> sanity (si spec) -> aceptacion del log -> parar.
        Devuelve dict de metricas o dict _estado=error (nunca tumba el barrido)."""
        args = self.args
        ruta_log = os.path.join(self.carpetas["logs"], log_nombre or
                                ("server-%s.log" % re.sub(r"[^A-Za-z0-9]+", "_", nombre)))
        fl = construir_flags(args, extra, quitar_cmoe=quitar_cmoe, modelo=modelo)
        print(gray("  flags extra: %s" % (" ".join(extra) if extra else "(solo launcher)")))
        kv("log", ruta_log)
        res = {"nombre": nombre, "extra": extra or [], "log": ruta_log,
               "flags_invocacion": fl, "quitar_cmoe": quitar_cmoe}
        t0 = time.perf_counter()
        proc = None
        try:
            proc = lanzar_server(args, fl, env_extra=env_extra, ruta_log=ruta_log)
            load_s = esperar_salud(args, proc, ruta_log, timeout=args.load_timeout)
            res["load_s"] = round(load_s, 1)
            kv("load", "%.1f s" % load_s)
            g = vram_mib()
            res["vram"] = g
            if g:
                kv("VRAM tras carga", "%d/%d MiB" % (g["used"], g["total"]))
                if g["used"] > g["total"] - 200:
                    print(yellow("  [AVISO] VRAM casi llena (%d MiB libres)"
                                 % (g["total"] - g["used"])))
            rp = ram_proceso(pid=proc.pid)
            if rp:
                res["ram_server_mib"] = round(rp, 0)
                kv("RAM del server", "%.0f MiB" % rp)
            # warmup descartado (verificado en barridos)
            self.cli.completion({"prompt": prompt_ref(96, semilla=777),
                                 "n_predict": 96, "temperature": 0, "seed": 5,
                                 "ignore_eos": True}, stream=True,
                                timeout=args.timeout)
            pasadas = pasadas if pasadas is not None else (
                1 if args.quick else 2)
            serie = self._medir_decode(pasadas)
            res["decode_serie"] = [round(x, 2) for x in serie]
            res["decode_medio"] = round(media(serie), 2)
            res["decode_sigma"] = round(desvest(serie), 2)
            pv, tim, fuente = self._medir_prefill(1050 if not args.quick else 540)
            res["prefill_ts"] = round(pv, 1)
            res["prefill_fuente"] = fuente
            # TTFT calido: mismo prompt 2a vez (KV-shift)
            p2 = prompt_ref(270, semilla=555001)
            r1 = self.cli.completion({"prompt": p2, "n_predict": 1, "temperature": 0,
                                      "seed": 3}, stream=True, timeout=args.timeout)
            r2 = self.cli.completion({"prompt": p2, "n_predict": 1, "temperature": 0,
                                      "seed": 3}, stream=True, timeout=args.timeout)
            ttft_calido = (r2.get("timings") or {}).get("prompt_ms")
            res["ttft_calido_ms"] = round(float(ttft_calido), 1) if ttft_calido else None
            ok, tot = self._sanity()
            res["sanity"] = "%d/%d" % (ok, tot)
            kv("sanity", green(res["sanity"]) if ok == tot
               else yellow(res["sanity"]))
            if spec:
                acc = aceptacion_de_log(leer_log(ruta_log))
                res["acceptance"] = tasa_media(acc)
                res["acc_eventos"] = acc["eventos"]
                res["acc_muestras"] = acc["muestras"][:4]
                kv("acceptance (log)", "%.3f (%d eventos)"
                   % (res["acceptance"], acc["eventos"]) if res["acceptance"]
                   is not None else "N/D (sin eventos en el log)")
                # coste por turno: prefill ~300 frio + 256 decode
                pf = prompt_ref(300, semilla=97017)
                rct = self.cli.completion({"prompt": pf, "n_predict": 256,
                                           "temperature": 0, "seed": 11,
                                           "ignore_eos": True}, stream=True,
                                          timeout=args.timeout)
                t2 = rct.get("timings") or {}
                costo = (t2.get("prompt_ms") or 0) + (t2.get("predicted_ms") or 0)
                res["coste_turno_ms"] = round(float(costo), 1) if costo else None
            v, delta = clasifica(res.get("decode_medio"), self.ancla_referencia())
            res["delta_vs_ancla_pct"] = round(delta, 2) if delta is not None else None
            res["veredicto"] = v
            col = {"GANA": green, "PIERDE": red, "EMPATA": gray}.get(v, gray)
            kv("veredicto vs ancla %.2f" % self.ancla_referencia(),
               col("%s (%+.2f%%)" % (v, delta) if delta is not None else "N/D"))
        except Exception as e:
            res["_estado"] = "error"
            res["_error"] = "%s: %s" % (type(e).__name__, e)
            print(red("  [ERROR] %s" % res["_error"]))
        finally:
            parar(proc)
            if not esperar_puerto_libre(args.host, args.port):
                print(yellow("  [AVISO] el puerto %d sigue ocupado; espero mas..."
                             % args.port))
                esperar_puerto_libre(args.host, args.port, intentos=20, pausa=3.0)
        res["_segundos"] = round(time.perf_counter() - t0, 1)
        bas = sum(basura_en(t) for t in self.textos)
        res["basura_hits"] = bas
        self.textos = []
        return res

    def fase_b(self):
        section("B", "RE-ANCLA: launcher v2.1 EXACTO (flags conocidos, log capturado)")
        print(gray("  hipotesis a cerrar: adjunto 25-oct midio 17.11 con flags")
              + gray(" invisibles; ancla historica barrido-30 = %.2f" % self.args.ancla))
        mue = MuestreadorPerf(intervalo=2.0)
        mue.start()
        m = self._medir_config("B-ancla", [], pasadas=1 if self.args.quick else 3)
        m["perf_durante_decode"] = mue.resultado()
        pf = m.get("perf_durante_decode") or {}
        if pf.get("turbo_pct_max") is not None:
            kv("turbo DURANTE decode", "max %.0f%% (medio %.0f%%)"
               % (pf["turbo_pct_max"], pf.get("turbo_pct_medio") or 0))
            if pf["turbo_pct_max"] <= 105:
                print(yellow("  [AVISO] el CPU no supera ~100% de rendimiento: "
                             "posible modo ahorro o throttling"))
        if pf.get("pagefaults_max") is not None:
            kv("page faults/s DURANTE decode", "max %.0f (medio %.0f)"
               % (pf["pagefaults_max"], pf.get("pagefaults_medio") or 0))
            if pf["pagefaults_max"] > 20000:
                print(yellow("  [AVISO] page faults altos -> paginacion; mlock/fase C6"))
        else:
            kv("perf durante decode", "N/D")
        if m.get("decode_medio"):
            self.ancla_medida = m["decode_medio"]
            print("")
            kv("ANCLA MEDIDA HOY", bold("%.2f t/s" % self.ancla_medida))
            if self.ancla_medida >= self.args.ancla - ruido_ts(self.args.ancla):
                print(green("  -> coincide con el ancla historica %.2f: el 17.11 del"
                            % self.args.ancla))
                print(green("     adjunto fue el server mal lanzado. Misterio CERRADO."))
            elif self.ancla_medida <= MEDICION_ADJUNTO + ruido_ts(MEDICION_ADJUNTO):
                print(red("  -> coincide con el 17.11 del adjunto: no fueron los flags."))
                print(red("     El rig ha perdido ~20%% real. Hipotesis: termico,"
                          " paginas, o degradacion del entorno -> revisar A/fase F4"))
            else:
                print(yellow("  -> valor INTERMEDIO (%.2f): ni ancla ni adjunto."
                             % self.ancla_medida))
                print(yellow("     Usamos de aqui en adelante el ancla de HOY."))
        else:
            print(red("  sin ancla medida (error arriba); sigo con la historica %.2f"
                      % self.args.ancla))
        self.res["B"] = m
        self.guardar_parcial()

    # ------------------------------------------------------------------ C --
    def configs_c(self):
        """Configs NO medidas o PENDIENTES (launcher comentario + catalogo).
        NCM va SIN -cmoe (mecanismo barrido-30: cmoe por config)."""
        cfgs = [
            {"id": "C1", "nombre": "TB8", "extra": ["-tb", "8"],
             "nota": "hilos de batch/prefill a 8 (decode sigue -t 4)"},
            {"id": "C2", "nombre": "UB2K", "extra": ["-ub", "2048", "-b", "8192"],
             "nota": "escalada del ORO-UB1K (1024/4096): riesgo buffers VRAM"},
            {"id": "C3", "nombre": "PRIOB2", "extra": ["--prio-batch", "2"],
             "nota": "prioridad del hilo de batch (catalogo, nunca medida)"},
            {"id": "C4", "nombre": "NCM39Q8+UB1K", "quitar_cmoe": True,
             "extra": ["-ncmoe", "39", "-c", "8192"],
             "nota": "1 capa de expertos a GPU, ctx 8192, KV q8_0; combo PENDIENTE del launcher"},
            {"id": "C5", "nombre": "NCM37C4+UB1K", "quitar_cmoe": True,
             "extra": ["-ncmoe", "37", "-c", "4096", "-ctk", "q4_0", "-ctv", "q4_0"],
             "nota": "3 capas a GPU, ctx 4096, KV q4_0; 22.49 solo en barrido-30; combo PENDIENTE"},
            {"id": "C6", "nombre": "MLOCK", "extra": ["--mlock"],
             "nota": "fijar pesos en RAM; guardarrail RAM libre"},
            {"id": "C7", "nombre": "OP64",
             "env_extra": {"GGML_OP_OFFLOAD_MIN_BATCH": "64"},
             "nota": "umbral de op-offload a 64 (default 32; 20.48 fue no-op-offload)"},
        ]
        if self.args.quick:
            queridos = {"C1", "C2", "C5"}
            cfgs = [c for c in cfgs if c["id"] in queridos]
        return cfgs

    def fase_c(self):
        section("C", "BARRIDO DE CONFIGS (una variable por vez sobre el launcher)")
        self.res["C"] = []   # re-ejecutar la fase reemplaza su dato previo
        r = ram_sistema()
        for cfg in self.configs_c():
            print("")
            print(bold("--- %s %s ---" % (cfg["id"], cfg["nombre"])))
            if cfg["nota"]:
                print(gray("  %s" % cfg["nota"]))
            if cfg["id"] == "C6" and r and r["libre_mib"] < 13500:
                print(yellow("  [SKIP] RAM libre %d MiB < 13500: mlock puede colgar"
                             " el sistema" % r["libre_mib"]))
                self.res["C"].append({"id": "C6", "nombre": "MLOCK",
                                      "_estado": "omito",
                                      "_motivo": "RAM libre insuficiente"})
                continue
            m = self._medir_config(cfg["nombre"],
                                   cfg.get("extra"),
                                   quitar_cmoe=cfg.get("quitar_cmoe", False),
                                   env_extra=cfg.get("env_extra"))
            m["id"] = cfg["id"]
            self.res["C"].append(m)
            self.guardar_parcial()


def _importa(nombre):
    try:
        __import__(nombre)
        return True
    except Exception:
        return False


def _importa_gguf():
    return _importa("gguf")


def _busca_hermano(nombre, ruta_server):
    d = os.path.dirname(ruta_server)
    if d and os.path.isfile(os.path.join(d, nombre)):
        return os.path.join(d, nombre)
    return None


# =============================== FASES D / E =================================
# -------- parser GGUF minimo (solo metadatos; sin dependencias) --------------
_GGUF_T = {0: ("<B", 1), 1: ("<b", 1), 2: ("<H", 2), 3: ("<h", 2), 4: ("<I", 4),
           5: ("<i", 4), 6: ("<f", 4), 7: ("<B", 1), 10: ("<Q", 8), 11: ("<q", 8),
           12: ("<d", 8)}


def gguf_kv_dump(ruta, patron="expert"):
    """Lee SOLO los metadatos del GGUF (header + KV; ignora tensores).
    Devuelve {"arch": str, "kv": {clave: valor_escalar}, "claves": [todas]}.
    N/D honesto si el archivo no es GGUF. Pure-python: sin gguf-py."""
    import struct
    out = {"arch": None, "kv": {}, "claves": [], "n_kv": 0}
    try:
        f = open(ruta, "rb")
    except Exception as e:
        out["error"] = str(e)
        return out
    try:
        magic = f.read(4)
        if magic != b"GGUF":
            out["error"] = "no es GGUF (magic=%r)" % magic
            return out
        _ver, ntens, nkv = struct.unpack("<IQQ", f.read(20))

        def rstr():
            (n,) = struct.unpack("<Q", f.read(8))
            return f.read(n).decode("utf-8", errors="replace")

        def rval(t):
            if t == 8:
                return rstr()
            if t == 9:
                (tt,) = struct.unpack("<I", f.read(4))
                (cnt,) = struct.unpack("<Q", f.read(8))
                if tt == 8:
                    for _ in range(cnt):
                        (n,) = struct.unpack("<Q", f.read(8))
                        f.seek(n, 1)
                elif tt in _GGUF_T:
                    _, sz = _GGUF_T[tt]
                    f.seek(cnt * sz, 1)
                else:
                    raise ValueError("tipo array %d" % tt)
                return None
            if t in _GGUF_T:
                fmt, sz = _GGUF_T[t]
                if t == 7:
                    return bool(f.read(1)[0])
                (v,) = struct.unpack(fmt, f.read(sz))
                return v
            raise ValueError("tipo %d" % t)

        for _ in range(nkv):
            k = rstr()
            (t,) = struct.unpack("<I", f.read(4))
            v = rval(t)
            out["claves"].append(k)
            if patron.lower() in k.lower():
                out["kv"][k] = v
            if k == "general.architecture" and isinstance(v, str):
                out["arch"] = v
        out["n_kv"] = nkv
        return out
    except Exception as e:
        out["error"] = "%s: %s" % (type(e).__name__, e)
        return out
    finally:
        f.close()


def _claves_expert_candidatas(dump):
    """De las claves con 'expert', las que controlan cuantos expertos se usan."""
    cands = [k for k in dump["kv"] if "expert_used" in k.lower()]
    arch = dump["arch"]
    if arch:
        exactos = [k for k in cands
                   if k.lower() == "%s.expert_used_count" % arch.lower()]
        if exactos:
            return exactos, dump["kv"][exactos[0]]
    return cands, (dump["kv"].get(cands[0]) if cands else None)


def fase_d(self):
    section("D", "FAMILIA EXP (T1): override-kv con la clave EXACTA del GGUF")
    print(gray("  historial: el override-kv fue no-op en barrido-30, PERO se sospecha")
          + gray(" clave equivocada (tag HF qwen3_5_moe vs qwen3moe). Hoy: dump ->"))
    print(gray("  clave exacta -> dosis-respuesta dinamica (V-2, V-4). Sin copias."))
    d = {"dump": None, "configs": []}
    dump = gguf_kv_dump(self.args.modelo, patron="expert")
    d["dump"] = {"arch": dump.get("arch"), "n_kv": dump.get("n_kv"),
                 "error": dump.get("error"),
                 "kv_expert": {k: (str(v)[:80]) for k, v in dump.get("kv", {}).items()}}
    if dump.get("error"):
        print(red("  [ERROR] no pude leer el GGUF: %s" % dump["error"]))
        self.res["D"] = d
        self.guardar_parcial()
        return
    kv("general.architecture", dump.get("arch") or "N/D")
    kv("claves con 'expert'", ", ".join(sorted(dump["kv"]) or "NINGUNA"))
    if dump["kv"]:
        for k, v in sorted(dump["kv"].items()):
            kv("  %s" % k, v)
    cands, v_actual = _claves_expert_candidatas(dump)
    if not cands:
        print(yellow("  [OMITIDO] el GGUF no trae NINGUNA clave expert_used -> el")
              + yellow(" override-kv nunca podra aplicar. D2 cerrado como NO-VIA.")
              + yellow(" Solo quedaria cirugia (--cirugia, anade la clave)."))
        d["veredicto"] = "NO-VIA (clave inexistente en el GGUF)"
        self.res["D"] = d
        self.guardar_parcial()
        return
    if v_actual is None or not isinstance(v_actual, int):
        print(yellow("  [OMITIDO] valor actual de %s no es entero: %r"
                     % (cands[0], v_actual)))
        d["veredicto"] = "N/D (valor no entero)"
        self.res["D"] = d
        self.guardar_parcial()
        return
    kv("clave elegida", cands[0])
    kv("valor actual V", v_actual)
    if self.args.exp_valores:
        valores = [int(x) for x in self.args.exp_valores.split(",") if int(x) > 0]
    else:
        valores = sorted({max(1, v_actual - 2), max(1, v_actual - 4)})
    kv("dosis", str(valores))
    d["clave"] = cands[0]
    d["valor_actual"] = v_actual
    d["valores"] = valores
    serie_ctrl = self.ancla_referencia()
    for val in valores:
        print("")
        print(bold("--- D-EXP%d (override-kv %s=int:%d) ---" % (val, cands[0], val)))
        m = self._medir_config("D-EXP%d" % val,
                               ["--override-kv", "%s=int:%d" % (cands[0], val)])
        m["exp_valor"] = val
        d["configs"].append(m)
        self.guardar_parcial()
    # dosis-respuesta: monotonica => aplico; plano => no-op (cierre honesto)
    meds = [(c["exp_valor"], c.get("decode_medio") or 0.0)
            for c in d["configs"] if c.get("_estado") != "error"]
    if len(meds) >= 2:
        (v1, m1), (v2, m2) = meds[0], meds[1]
        rz = ruido_ts(serie_ctrl)
        if abs(m1 - m2) <= rz and abs(m1 - serie_ctrl) <= rz:
            d["veredicto"] = ("NO-OP: plano vs ancla y entre dosis -> el override"
                              " sigue sin aplicar (quedaria cirugia --cirugia)")
        elif (v1 < v2 and m1 > m2) or (v2 < v1 and m2 > m1):
            d["veredicto"] = ("APLICA: dosis-respuesta monotonica (menos expertos,"
                              " mas t/s) -> GO para afinar valor")
        else:
            d["veredicto"] = ("AMBIGUO: cambia el t/s pero sin monotonia clara;"
                              " repetir dosis o pasar a cirugia")
    elif meds:
        d["veredicto"] = "N/D (solo 1 dosis medida)"
    else:
        d["veredicto"] = "ERROR en todas las dosis"
    print("")
    kv("VEREDICTO EXP", bold(d["veredicto"]))
    self.res["D"] = d
    self.guardar_parcial()


def _criterio_spec(m, ancla):
    """Criterios pre-registrados del plan T2 (verbatim del worklog)."""
    if m.get("_estado") == "error":
        return "ERROR (server no arranco: OOM/flag; ver log)"
    if m.get("basura_hits", 0) > 0:
        return "NO ADOPTAR: basura '////' (bug #23577)"
    acc = m.get("acceptance")
    dec = m.get("decode_medio") or 0.0
    rz = ruido_ts(ancla)
    if acc is None:
        return "N/D: sin eventos de acceptance en el log (no se inventa)"
    if acc >= 0.70 and dec > ancla + rz:
        return "GO: acc alta y decode gana -> adoptar"
    if acc >= 0.70:
        return ("CUELLO DE COMPUTO: acc alta sin ganancia -> MTP cerrado;"
                " EAGLE-3 hereda el veredicto")
    if acc < 0.50:
        return "acc baja: se prueba p-min 0.85 una vez"
    return "MARGINAL (acc entre 0.5 y 0.7)"


def fase_e(self):
    section("E", "ESPECULATIVAS (T2 MTP + B6 EAGLE-3), acceptance del log real")
    print(gray("  ngram EXCLUIDO (veneno confirmado). Flags verbatim dump b11856:")
          + gray(" --spec-type draft-mtp (L390), --spec-draft-n-max,")
          + gray(" --spec-draft-p-min (default 0.00, L369), --spec-draft-device."))
    self.res["E"] = []   # re-ejecutar la fase reemplaza su dato previo
    cfgs = [
        {"id": "E1", "nombre": "MTP-A nmax2",
         "extra": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2"],
         "nota": "T2-A: n-max 2 (comunidad: el dulce de MoE)"},
        {"id": "E2", "nombre": "MTP-B nmax2 pmin075",
         "extra": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2",
                   "--spec-draft-p-min", "0.75"],
         "nota": "T2-B: p-min 0.75 (NVIDIA forum Qwen3.6 y comunidad 0.75-0.8)"},
        {"id": "E3", "nombre": "MTP-C +draftCPU",
         "extra": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2",
                   "--spec-draft-p-min", "0.75", "--spec-draft-device", "none"],
         "nota": "T2-C: draft 100%% CPU, protege el prefill del D2H"},
    ]
    if self.args.eagle3:
        cfgs.append({"id": "E4", "nombre": "EAGLE3",
                     "extra": ["-md", self.args.eagle3,
                               "--spec-type", "draft-eagle3", "-ngld", "all"],
                     "nota": "B6: draft denso 1 capa EN VRAM (coste CPU ~0)"})
    if self.args.quick:
        cfgs = [c for c in cfgs if c["id"] in ("E2", "E3")]
    ancla = self.ancla_referencia()
    for cfg in cfgs:
        print("")
        print(bold("--- %s %s ---" % (cfg["id"], cfg["nombre"])))
        if cfg["nota"]:
            print(gray("  " + cfg["nota"].replace("%%", "%")))
        m = self._medir_config(cfg["nombre"], cfg["extra"], spec=True)
        m["id"] = cfg["id"]
        m["criterio"] = _criterio_spec(m, ancla)
        col = green if m["criterio"].startswith("GO") else (
            red if ("NO ADOPTAR" in m["criterio"] or "ERROR" in m["criterio"])
            else yellow)
        kv("criterio pre-registrado", col(m["criterio"]))
        self.res["E"].append(m)
        self.guardar_parcial()
    # T2-E condicional: p-min 0.85 si la mejor acceptance < 50%
    con_acc = [m for m in self.res["E"]
               if m.get("acceptance") is not None and m.get("_estado") != "error"]
    if con_acc and max(m["acceptance"] for m in con_acc) < 0.50 \
            and not any(m["id"] == "E5" for m in self.res["E"]):
        print("")
        print(yellow("  [T2-E] mejor acc < 0.50 -> auto: p-min 0.85 una vez"))
        m = self._medir_config("MTP-E nmax2 pmin085",
                               ["--spec-type", "draft-mtp",
                                "--spec-draft-n-max", "2",
                                "--spec-draft-p-min", "0.85",
                                "--spec-draft-device", "none"], spec=True)
        m["id"] = "E5"
        m["criterio"] = _criterio_spec(m, ancla)
        kv("criterio pre-registrado", m["criterio"])
        self.res["E"].append(m)
    self.guardar_parcial()


# =============================== FASE F (opcional) ===========================
def fase_f(self):
    section("F", "REQUANT IQ2_M (opcional; sacrifica calidad por bytes)")
    rz = {"quantize": _busca_hermano("llama-quantize.exe", self.args.server),
          "imatrix": _busca_hermano("llama-imatrix.exe", self.args.server),
          "data": self.args.imatrix_data, "disco": free_gib(self.args.modelo)}
    if not rz["quantize"] or not rz["imatrix"]:
        print(yellow("  [OMITIDO] faltan llama-quantize/llama-imatrix junto al server"))
        self.res["F"] = {"_estado": "omito", "_motivo": "sin herramientas", "rutas": rz}
        return
    if not self.args.imatrix_data or not os.path.isfile(self.args.imatrix_data):
        print(yellow("  [OMITIDO] hace falta --imatrix-data <archivo de calibracion>"))
        self.res["F"] = {"_estado": "omito", "_motivo": "sin imatrix-data", "rutas": rz}
        return
    if (rz["disco"] or 0) < 30.0:
        print(yellow("  [SKIP] disco libre %.1f GiB < 30" % (rz["disco"] or 0)))
        self.res["F"] = {"_estado": "omito", "_motivo": "disco", "rutas": rz}
        return
    lab = self.carpetas["lab"]
    ruta_imx = os.path.join(lab, "imatrix-i-mini.gguf")
    ruta_q2 = os.path.join(lab, "APEX-I-MINI-IQ2_M.gguf")
    f = {"imatrix": None, "quant": None, "medicion": None}
    try:
        print(gray("  [1/3] llama-imatrix (puede tardar horas; Ctrl+C = abortar"
                   " y conservar parcial)"))
        t0 = time.time()
        cmd = [rz["imatrix"], "-m", self.args.modelo, "-f", self.args.imatrix_data,
               "-o", ruta_imx, "-t", "4"]
        subprocess.run(cmd, timeout=self.args.imax_timeout,
                       capture_output=True, text=True)
        if not os.path.isfile(ruta_imx):
            raise RuntimeError("imatrix no genero salida")
        f["imatrix"] = {"s": round(time.time() - t0, 1), "ruta": ruta_imx}
        print(gray("  [2/3] llama-quantize IQ2_M"))
        cmd = [rz["quantize"], "--imatrix", ruta_imx, self.args.modelo,
               ruta_q2, "IQ2_M"]
        out = subprocess.run(cmd, timeout=7200, capture_output=True, text=True)
        if not os.path.isfile(ruta_q2):
            raise RuntimeError("quantize fallo: %s" % (out.stderr or out.stdout)[-400:])
        f["quant"] = {"ruta": ruta_q2,
                      "gib": round(os.path.getsize(ruta_q2) / (1024.0 ** 3), 2)}
        print(gray("  [3/3] medicion del IQ2_M (con sanity como puerta de calidad)"))
        m = self._medir_config("F-IQ2M", [], modelo=ruta_q2)
        m["criterio"] = ("CALIDAD EN RIESGO: sanity %s (gate del plan)" % m.get("sanity")
                         if m.get("sanity") not in (None, "3/3") else
                         "sanity ok; decide el Director con el delta")
        f["medicion"] = m
    except KeyboardInterrupt:
        print(yellow("  [INTERRUPTED] conservo el parcial y salgo"))
        raise
    except Exception as e:
        f["error"] = "%s: %s" % (type(e).__name__, e)
        print(red("  [ERROR] %s" % f["error"]))
    self.res["F"] = f
    self.guardar_parcial()


# =============================== FASE G: INFORME =============================
def _fmt(v, nd=2):
    if v is None:
        return "N/D"
    if isinstance(v, float):
        return ("%." + str(nd) + "f") % v
    return str(v)


def fase_g(self):
    section("G", "INFORME FINAL (JSON + MD + CSV historial)")
    base = self.args.out or "informe-barrido-total"
    # si se invoca G SOLO (sin fases de medicion en esta corrida), recuperar
    # el parcial para NO sobrescribir el informe con uno vacio
    hay_datos = any([self.res.get("B"), self.res.get("C"), self.res.get("E"),
                     self.res.get("D")])
    if not hay_datos and os.path.isfile(base + "-parcial.json"):
        try:
            with open(base + "-parcial.json", encoding="utf-8") as f:
                self.res = json.load(f)
            b = self.res.get("B") or {}
            if b.get("decode_medio"):
                self.ancla_medida = b["decode_medio"]
            print(gray("  (sin mediciones en esta corrida: recupero el parcial"))
            print(gray("   %s-parcial.json para el informe)" % base))
        except Exception as e:
            print(yellow("  (no pude recuperar el parcial: %s)" % e))
    self.res["meta"]["fin"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        with open(base + ".json", "w", encoding="utf-8") as f:
            json.dump(self.res, f, ensure_ascii=False, indent=1, default=str)
        kv("JSON", base + ".json")
    except Exception as e:
        print(red("  [ERROR] JSON: %s" % e))
    ancla = self.ancla_referencia()
    # ---------- ranking de TODAS las configs medidas ----------
    filas = []
    if self.res.get("B") and self.res["B"].get("decode_medio"):
        filas.append({"fase": "B", **{k: self.res["B"].get(k) for k in
                     ("nombre", "decode_medio", "decode_sigma", "veredicto",
                      "prefill_ts", "load_s", "sanity")}})
    for m in self.res.get("C") or []:
        if m.get("decode_medio"):
            filas.append({"fase": m.get("id", "C"), **{k: m.get(k) for k in
                         ("nombre", "decode_medio", "decode_sigma", "veredicto",
                          "prefill_ts", "load_s", "sanity")}})
    for m in (self.res.get("D") or {}).get("configs") or []:
        if m.get("decode_medio"):
            filas.append({"fase": "D", **{k: m.get(k) for k in
                         ("nombre", "decode_medio", "decode_sigma", "veredicto",
                          "prefill_ts", "load_s", "sanity")}})
    for m in self.res.get("E") or []:
        if m.get("decode_medio"):
            filas.append({"fase": m.get("id", "E"), **{k: m.get(k) for k in
                         ("nombre", "decode_medio", "decode_sigma", "veredicto",
                          "prefill_ts", "load_s", "sanity")}})
    mf = (self.res.get("F") or {}).get("medicion") or {}
    if mf.get("decode_medio"):
        filas.append({"fase": "F", **{k: mf.get(k) for k in
                     ("nombre", "decode_medio", "decode_sigma", "veredicto",
                      "prefill_ts", "load_s", "sanity")}})
    filas = [f for f in filas if f.get("decode_medio")]
    filas.sort(key=lambda x: -(x.get("decode_medio") or 0))
    # ---------- CSV historial (append; unidades ms desde v1.0) ----------
    try:
        nuevo_csv = not os.path.isfile("barrido-total-historial.csv")
        with open("barrido-total-historial.csv", "a", encoding="utf-8") as f:
            if nuevo_csv:
                f.write("fecha,fase,id,nombre,decode_medio,decode_sigma,"
                        "delta_pct,veredicto,prefill_ts,ttft_calido_ms,load_s,"
                        "acceptance,sanity,basura_hits,coste_turno_ms\n")
            allm = []
            if self.res.get("B"):
                allm.append(("B", self.res["B"]))
            allm += [("C", m) for m in self.res.get("C") or []]
            allm += [("D", m) for m in (self.res.get("D") or {}).get("configs") or []]
            allm += [("E", m) for m in self.res.get("E") or []]
            if mf:
                allm.append(("F", mf))
            for fase, m in allm:
                if not m or not m.get("decode_medio"):
                    continue
                f.write(",".join(str(x) for x in [
                    self.res["meta"].get("fin"), fase, m.get("id", ""),
                    m.get("nombre", ""), m.get("decode_medio"),
                    m.get("decode_sigma"), m.get("delta_vs_ancla_pct"),
                    m.get("veredicto"), m.get("prefill_ts"),
                    m.get("ttft_calido_ms"), m.get("load_s"),
                    (("%.3f" % m["acceptance"]) if m.get("acceptance") is not None else ""),
                    m.get("sanity"), m.get("basura_hits", 0),
                    m.get("coste_turno_ms", "")]) + "\n")
        kv("CSV", "barrido-total-historial.csv (%s)" % ("nuevo" if nuevo_csv else "append"))
    except Exception as e:
        print(red("  [ERROR] CSV: %s" % e))
    # ---------- MD ----------
    L = []
    L.append("# Informe BARRIDO-TOTAL")
    L.append("")
    L.append("- fecha: %s" % self.res["meta"]["fin"])
    L.append("- modelo: %s" % self.res["meta"]["modelo"])
    L.append("- server: %s" % self.res["meta"]["server"])
    L.append("- modo: %s" % ("quick" if self.res["meta"]["quick"] else "completo"))
    L.append("- ancla historica (barrido-30): %.2f t/s | medicion adjunto 25-oct: %.2f t/s"
             % (self.args.ancla, MEDICION_ADJUNTO))
    L.append("")
    a = self.res.get("A") or {}
    L.append("## [A] Auditoria del sistema")
    if a:
        c = a.get("cpu") or {}
        L.append("- CPU: %s (%s fisicos/%s logicos)" % (c.get("nombre"), c.get("fisicos"), c.get("logicos")))
        r = a.get("ram") or {}
        L.append("- RAM: total %s MiB, libre %s MiB" % (r.get("total_mib"), r.get("libre_mib")))
        dm = a.get("dimms")
        if dm:
            L.append("- DIMMs: %s (canales estimados: %s; CPU-Z del Director manda)"
                     % ("; ".join("%s %.1fGiB@%s" % (x["slot"], x["gib"], x["speed"])
                                  for x in dm["filas"]), dm["canales_estimados"]))
        pi = a.get("perf_idle") or {}
        L.append("- Turbo idle: %s | PageFaults/s idle: %s"
                 % (_fmt(pi.get("turbo_pct_max"), 0), _fmt(pi.get("pagefaults_max"), 0)))
        L.append("- Defender exclusiones: %s" % (a.get("defender_exclusiones") or "N/D"))
        L.append("- Disco libre: %s GiB" % _fmt(a.get("disco_libre_gib"), 1))
    else:
        L.append("- (no corrida)")
    L.append("")
    b = self.res.get("B") or {}
    L.append("## [B] Re-ancla (launcher v2.1 exacto)")
    if b:
        L.append("- decode_medio: %s t/s (serie %s)" % (_fmt(b.get("decode_medio")), b.get("decode_serie")))
        L.append("- prefill: %s t/s | ttft_calido: %s ms | load: %s s"
                 % (_fmt(b.get("prefill_ts"), 1), _fmt(b.get("ttft_calido_ms"), 1), _fmt(b.get("load_s"))))
        if b.get("decode_medio"):
            L.append("- **misterio 17.11 vs %.2f: veredicto del script en consola; el ancla de HOY es %.2f**"
                     % (self.args.ancla, self.ancla_medida or self.args.ancla))
    else:
        L.append("- (no corrida)")
    L.append("")
    L.append("## [C] Barrido de configs")
    L.append("")
    L.append("| id | config | decode t/s | sigma | delta%% | veredicto | prefill | sanity |")
    L.append("|---|---|---|---|---|---|---|---|")
    for m in self.res.get("C") or []:
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            m.get("id"), m.get("nombre"), _fmt(m.get("decode_medio")),
            _fmt(m.get("decode_sigma")), _fmt(m.get("delta_vs_ancla_pct")),
            m.get("veredicto", m.get("_estado", "")),
            _fmt(m.get("prefill_ts"), 1), m.get("sanity", "-")))
    L.append("")
    d = self.res.get("D") or {}
    L.append("## [D] Familia EXP (T1)")
    if d:
        L.append("- dump GGUF: arch=%s, claves expert: %s"
                 % (_fmt(d.get("dump", {}).get("arch")), d.get("dump", {}).get("kv_expert")))
        L.append("- clave: %s | valor actual: %s | dosis: %s"
                 % (_fmt(d.get("clave")), _fmt(d.get("valor_actual")), d.get("valores")))
        for m in d.get("configs") or []:
            L.append("- EXP%s: decode %s t/s (%s)" % (m.get("exp_valor"),
                      _fmt(m.get("decode_medio")), m.get("veredicto")))
        L.append("- **veredicto: %s**" % d.get("veredicto", "N/D"))
    else:
        L.append("- (no corrida)")
    L.append("")
    L.append("## [E] Especulativas (MTP/EAGLE) con acceptance del log")
    L.append("")
    L.append("| id | config | decode t/s | acceptance | coste turno ms | sanity | criterio |")
    L.append("|---|---|---|---|---|---|---|")
    for m in self.res.get("E") or []:
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            m.get("id"), m.get("nombre"), _fmt(m.get("decode_medio")),
            _fmt(m.get("acceptance"), 3), _fmt(m.get("coste_turno_ms"), 0),
            m.get("sanity", "-"), (m.get("criterio") or "").replace("|", "/")))
    L.append("")
    f = self.res.get("F")
    if f:
        L.append("## [F] Requant IQ2_M")
        mm = f.get("medicion") or {}
        L.append("- imatrix: %s | quant: %s GiB" % (_fmt((f.get("imatrix") or {}).get("s"), 0),
                 _fmt((f.get("quant") or {}).get("gib"), 2)))
        L.append("- medicion IQ2_M: decode %s t/s | sanity %s | %s"
                 % (_fmt(mm.get("decode_medio")), mm.get("sanity"), mm.get("criterio")))
        L.append("")
    L.append("## RANKING (todas las configs, decode desc)")
    L.append("")
    L.append("| # | fase | config | decode t/s | delta%% vs %.2f | veredicto |" % ancla)
    L.append("|---|---|---|---|---|---|")
    for i, fl_ in enumerate(filas[:12], 1):
        v, delta = clasifica(fl_.get("decode_medio"), ancla)
        L.append("| %d | %s | %s | %s | %s | %s |" % (
            i, fl_.get("fase"), fl_.get("nombre"), _fmt(fl_.get("decode_medio")),
            _fmt(delta), v))
    L.append("")
    L.append("## RECOMENDACION")
    L.append("")
    cand_rec = list(self.res.get("C") or [])
    if mf:
        cand_rec.append(mf)
    for m in cand_rec:
        if m.get("veredicto") != "GANA":
            continue
        if m.get("extra"):
            base_txt = ("quita -cmoe del launcher y anade" if m.get("quitar_cmoe")
                        else "anade al final del launcher (FLAGS_GANADORAS)")
            L.append("- %s gana (%s t/s): %s `%s`"
                     % (m.get("nombre"), _fmt(m.get("decode_medio")), base_txt,
                        " ".join(m.get("extra") or [])))
        elif m.get("nombre") == "OP64":
            L.append("- OP64 gana (%s t/s): variable de entorno GGML_OP_OFFLOAD_MIN_BATCH=64 "
                     "antes de lanzar el server" % _fmt(m.get("decode_medio")))
    go_spec = [m for m in self.res.get("E") or []
               if (m.get("criterio") or "").startswith("GO")]
    if go_spec:
        m = go_spec[0]
        L.append("- %s: GO de especulativa (%s, acc %.3f): anade `%s`"
                 % (m.get("nombre"), _fmt(m.get("decode_medio")),
                    m.get("acceptance"), " ".join(m.get("extra") or [])))
    if (d.get("veredicto") or "").startswith("APLICA"):
        L.append("- EXP: anade al launcher `--override-kv %s=int:<valor>`"
                 " (dosis respuesta confirmada)" % d.get("clave"))
    if not any(m.get("veredicto") == "GANA" for m in self.res.get("C") or []) \
            and not go_spec and not (d.get("veredicto") or "").startswith("APLICA"):
        L.append("- Ninguna config gana hoy la zona muerta; el ranking queda como"
                 " evidencia y el plan pasa por el binario nuevo (b11871+) o requant.")
    try:
        with open(base + ".md", "w", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
        kv("MD", base + ".md")
    except Exception as e:
        print(red("  [ERROR] MD: %s" % e))
    print("")
    print(bold("TOP-3 configs de hoy:"))
    for i, fl_ in enumerate(filas[:3], 1):
        print("  %d) [%s] %s = %s t/s" % (i, fl_.get("fase"), fl_.get("nombre"),
                                          _fmt(fl_.get("decode_medio"))))


# cirugia opcional (T1 plan B): copia del GGUF con la clave reescrita
def fase_d_cirugia(lab):
    section("D2", "CIRUGIA EXP (--cirugia): copia con expert_used_count reescrito")
    d = lab.res.get("D") or {}
    clave = d.get("clave")
    if not clave:
        print(yellow("  [OMITIDO] sin clave expert del dump (corre la fase D antes)"))
        return
    script = _busca_gguf_new_metadata()
    if not script:
        print(yellow("  [OMITIDO] no encontre gguf_new_metadata.py en D:\\llama.cpp"))
        return
    disc = free_gib(lab.args.modelo)
    if (disc or 0) < 16.0:
        print(yellow("  [SKIP] disco libre %.1f GiB < 16" % (disc or 0)))
        return
    val = d.get("valores", [6])[0]
    orig = lab.args.modelo
    dst = os.path.join(lab.carpetas["lab"], "APEX-I-MINI-EXP%d.gguf" % val)
    if not os.path.isfile(dst):
        formas = [["%s=int:%d" % (clave, val)], ["%s=%d" % (clave, val)]]
        okcmd = None
        for kvarg in formas:
            cmd = [sys.executable, script, orig, dst] + kvarg
            print(gray("  $ %s" % " ".join(cmd)))
            try:
                out = subprocess.run(cmd, timeout=14400, capture_output=True, text=True)
                if out.returncode == 0 and os.path.isfile(dst):
                    okcmd = kvarg
                    break
            except Exception as e:
                print(red("  fallo cirugia: %s" % e))
        if not okcmd:
            d["cirugia"] = {"_estado": "error", "_error": "gguf_new_metadata no acepto"}
            lab.guardar_parcial()
            return
        d["cirugia"] = {"_estado": "ok", "cmd": okcmd, "ruta": dst}
    else:
        print(gray("  (la copia ya existia: %s)" % dst))
        d["cirugia"] = {"_estado": "ok", "ruta": dst}
    m = lab._medir_config("D2-CIRUGIA-EXP%d" % val, [], modelo=dst)
    m["id"] = "D2"
    d.setdefault("configs", []).append(m)
    lab.guardar_parcial()


def _busca_gguf_new_metadata():
    d = os.path.dirname(RUTA_SERVER_DEF)
    cands = [
        os.path.join(d, "gguf-py", "gguf", "scripts", "gguf_new_metadata.py"),
        r"D:\llama.cpp\gguf-py\gguf\scripts\gguf_new_metadata.py",
        r"D:\llama.cpp\gguf-py\examples\gguf_new_metadata.py",
    ]
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


# enlace de las fases D/E/F/G al motor (definidas como funciones libres)
Lab.fase_d = fase_d
Lab.fase_e = fase_e
Lab.fase_f = fase_f
Lab.fase_g = fase_g


# ================================== MAIN =====================================
def main():
    ap = argparse.ArgumentParser(
        description="barrido-total: la escalera completa automatizada (A-G)")
    ap.add_argument("--fases", default="A,B,C,D,E,G",
                    help="fases a correr, p.ej. A,B,C (default: A,B,C,D,E,G)")
    ap.add_argument("--quick", action="store_true",
                    help="version corta: menos pasadas y configs")
    ap.add_argument("--si", action="store_true",
                    help="matar el server vivo si el puerto esta ocupado")
    ap.add_argument("--host", default=HOST_DEF)
    ap.add_argument("--puerto", type=int, default=PUERTO_DEF)
    ap.add_argument("--server", default=RUTA_SERVER_DEF)
    ap.add_argument("--modelo", default=RUTA_MODELO_DEF)
    ap.add_argument("--ancla", type=float, default=ANCLA_BARRIDO30,
                    help="ancla historica para deltas (default 21.53)")
    ap.add_argument("--out", default=None, help="prefijo de informes")
    ap.add_argument("--timeout", type=int, default=600,
                    help="timeout por request de completion (s)")
    ap.add_argument("--load-timeout", dest="load_timeout", type=int, default=900,
                    help="timeout de carga del server (s)")
    ap.add_argument("--exp-valores", dest="exp_valores", default=None,
                    help="dosis EXP separadas por comas (default: V-2,V-4 dinamicas)")
    ap.add_argument("--eagle3", default=None,
                    help="ruta al draft GGUF EAGLE-3 para activar E4")
    ap.add_argument("--con-requant", dest="con_requant", action="store_true",
                    help="activa fase F (requant IQ2_M; horas)")
    ap.add_argument("--imatrix-data", dest="imatrix_data", default=None,
                    help="archivo de calibracion para llama-imatrix")
    ap.add_argument("--imax-timeout", dest="imax_timeout", type=int, default=7200)
    ap.add_argument("--cirugia", action="store_true",
                    help="fase D2: copia del GGUF con la clave reescrita (lento)")
    ap.add_argument("--fresco", action="store_true",
                    help="ignora el parcial anterior y empieza de cero")
    args = ap.parse_args()
    args.port = args.puerto  # alias de compatibilidad interno (dest vs uso)

    print(bold(VERSION))
    print(gray("  Director: este instrumento corre la escalera A-G con los flags"))
    print(gray("  verbatim del launcher v2.1 y del dump b11856. Nada inventado."))
    fases = [x.strip().upper() for x in args.fases.split(",") if x.strip()]
    necesita_server = any(f in fases for f in ("B", "C", "D", "E", "F"))
    # ---- guardarrails de arranque ----
    if os.name == "nt" and not os.path.isfile(args.server) and necesita_server:
        print(red("[FATAL] no existe el server: %s" % args.server))
        print("        revisa --server o el launcher. No invento mediciones.")
        return 2
    if necesita_server and not os.path.isfile(args.modelo):
        print(red("[FATAL] no existe el modelo: %s" % args.modelo))
        return 2
    if necesita_server and not puerto_libre(args.host, args.puerto):
        print(yellow("[AVISO] el puerto %d esta OCUPADO (server vivo?)."
                     % args.puerto))
        if not args.si:
            print("  sin --si no toco nada: cierra el server tu mismo o relanza con --si")
            return 2
        print("  --si: mato llama-server y espero el puerto...")
        matar_server(os.path.basename(args.server) or None)
        if not esperar_puerto_libre(args.host, args.puerto):
            print(red("[FATAL] el puerto sigue ocupado tras taskkill"))
            return 2
    if necesita_server:
        est, det = salud("http://%s:%d/health" % (args.host, args.puerto))
        if est != "apagado":
            print(red("[FATAL] algo responde en el puerto y no es libre"))
            return 2
    # ---- estimacion ----
    est_min = 0
    if "A" in fases:
        est_min += 2
    if "B" in fases:
        est_min += 6 if args.quick else 12
    if "C" in fases:
        est_min += len(lab_configs_c_para_estimar(args)) * (3 if args.quick else 5)
    if "D" in fases:
        est_min += 12 if args.quick else 20
    if "E" in fases:
        est_min += 12 if args.quick else 26
    if "F" in fases and args.con_requant:
        est_min += 180
    print("")
    print("Fases: %s | estimacion: ~%d min" % (",".join(fases), est_min))
    if args.quick:
        print(gray("  modo quick: 1 pasada decode, menos configs (ciencia primero,"
                   " profundidad despues)"))
    lab = Lab(args)
    t0 = time.time()
    rc = 0
    try:
        if "A" in fases:
            lab.fase_a()
        if "B" in fases:
            lab.fase_b()
        if "C" in fases:
            lab.fase_c()
        if "D" in fases:
            lab.fase_d()
            if args.cirugia:
                fase_d_cirugia(lab)
        if "E" in fases:
            lab.fase_e()
        if "F" in fases:
            if args.con_requant:
                lab.fase_f()
            else:
                print(gray("\n[F] requant apagado (usa --con-requant --imatrix-data ...)"))
        if "G" in fases:
            lab.fase_g()
    except KeyboardInterrupt:
        print("")
        print(yellow("[INTERRUPTED] conservo el parcial y apago el server limpio"))
        lab.guardar_parcial()
        rc = 130
    matar_server(os.path.basename(args.server) or None)
    if "G" not in fases and rc == 0:
        lab.guardar_parcial()
        print(gray("parcial guardado (usa --fases G para emitir el informe final)"))
    print("")
    print(bold("Fin: %.1f min | parcial: %s" % ((time.time() - t0) / 60.0,
              (args.out or "informe-barrido-total") + "-parcial.json")))
    return rc


def lab_configs_c_para_estimar(args):
    """Cuantas configs C habra (para la estimacion), sin instanciar Lab."""
    tot = 7
    if args.quick:
        tot = 3
    return range(tot)


if __name__ == "__main__":
    sys.exit(main())
