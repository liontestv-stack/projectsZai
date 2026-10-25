#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tester-mtp.py v1.0 — testeo profesional del MTP (draft-mtp) en el rig
=====================================================================
Instrumento de medida del protocolo T2 (investigacion-mtp-100). Todo lo que
reporta es MEDIDO en vivo [M]; si un dato no aparece, pone N/D y no se
inventa nada (regla de oro de aprendido.md).

TRES MODOS:

  1) ADJUNTO (default) — mide TODO contra el server que YA corre en :9931
     (suite completa A-F: salud, prefill, decode, TPOT, deteccion MTP,
      acceptance del draft, calidad, estabilidad, concurrencia, sostenido,
      recursos). Salidas: consola + informe .json + .md

        python tester-mtp.py
        python tester-mtp.py --quick
        python tester-mtp.py --log-file server.log    (acceptance del log)

     Para tener el log: lanza el server asi  ... > server.log 2>&1
     (o usa el modo protocolo, que captura el log el solo).

  2) PROTOCOLO T2 (--protocolo) — el test completo del plan de investigacion:
     lanza el server con cada config (ancla -> draft-mtp -> p-min ->
     draft 100% CPU -> KV f16), mide con protocolo anti-inflado (5 prompts
     DISTINTOS, descarta la 1a), lee acceptance del log propio, compara y da
     veredicto con los criterios pre-registrados. Si acc(T2-B) < 50% lanza
     T2-E (p-min 0.85) el solo.

        python tester-mtp.py --protocolo --si
        python tester-mtp.py --protocolo --configs T2-0,T2-A
        python tester-mtp.py --protocolo --si --quick

  3) COMPARAR dos informes .json ya generados:

        python tester-mtp.py --compare informe-A.json informe-B.json

REGLAS QUE RESPETA (aprendido.md + barrido-30):
  - "ignore_eos": true -> TODAS las pasadas generan el numero EXACTO de tokens
  - con speculative activo, repetir el MISMO prompt infla fake (88->419 t/s,
  caso real del barrido-25); por eso decode SIEMPRE con prompts DISTINTOS y
  acceptance SIEMPRE del log, nunca inferida del t/s
  - la pasada 1 de decode se descarta (calentamiento); el prefill se mide
  en pasada FRIA dedicada (cache_prompt false)
  - una variable por vez: T2-A..E son el ancla del launcher v2.1 + SOLO los
  flags spec; el T2-0 debe reproducir el ancla 21.5 t/s en ESTA corrida

FUENTES [F] — flags verificadas verbatim en el dump del build b11856
(InformacionCritica/llama-flags-nuevo.txt):
  --spec-type draft-mtp (L390) · --spec-draft-n-max default 3 (L352)
  --spec-draft-p-min default 0.00 (L369) · --spec-draft-device "none = don't
  offload" (L379-381) · --spec-draft-ncmoe/-cmoed (L344-350) · -kvu default
  ON con slots auto (L450-452, no hace falta pasarla) · --draft-max REMOVIDO
  (L415, se usa --spec-draft-n-max) · --cache-reuse = reuso de KV por
  KV-shift (L620, NO es MTP). Metricas tipo "Draft attempted/accepted"
  vistas en discusion #25198; aqui se leen del log con regex multi-patron +
  muestras verbatim (best-effort, mismo espiritu que _accept_de_log del
  barrido-30).

Solo stdlib (Python 3.8+). Opcional: psutil (RAM del proceso).
"""
import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
if os.name == "nt":
    os.system("")  # habilita ANSI en Windows 10+

# ------------------------- rutas y flags por defecto (RUTAS.md) -------------
RUTA_SERVER_DEF = r"D:\llama.cpp\llama-server.exe"
RUTA_MODELO_DEF = (r"D:\ZLia\models"
                   r"\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf")
HOST_DEF = "127.0.0.1"
PORT_DEF = 9931

# Launcher v2.1 verbatim (abrir-qwen-apex.py) + FLAGS_GANADORAS (ORO-UB1K).
# El T2-0 del protocolo DEBE reproducir exactamente esta invocacion.
BASE_FLAGS_LAUNCHER = [
    "-ngl", "99", "-cmoe",
    "-c", "16384", "-b", "2048", "-ub", "256",
    "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
    "-t", "4", "--prio", "2", "--no-mmproj",
    "--temp", "1.0", "--top-k", "20", "--top-p", "0.95",
    "--min-p", "0.0", "--presence-penalty", "0.0",
]
FLAGS_GANADORAS = ["-lm", "none", "-ub", "1024", "-b", "4096"]

KW_SPEC = ("draft", "spec", "mtp", "accept")
STD_TIMINGS = {"prompt_n", "prompt_ms", "prompt_per_token_ms", "prompt_per_second",
               "predicted_n", "predicted_ms", "predicted_per_token_ms",
               "predicted_per_second"}

USE_COLOR = True


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
    print(gray("-" * 76))
    print(bold("[%s] %s" % (tid, titulo)))
    print(gray("-" * 76))


def kv(k, v, w=44):
    print("  %-*s %s" % (w, k + ":", v))


# ------------------------------- estadistica --------------------------------
def media(xs):
    return statistics.fmean(xs) if xs else 0.0


def mediana(xs):
    return statistics.median(xs) if xs else 0.0


def desvest(xs):
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def p95(xs):
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * 0.95
    f = int(k)
    c2 = min(f + 1, len(s) - 1)
    return s[f] + (s[c2] - s[f]) * (k - f)


def pendiente(xs):
    """Pendiente de la regresion lineal simple y = a + b*i (drift)."""
    n = len(xs)
    if n < 2:
        return 0.0
    xm = (n - 1) / 2.0
    ym = media(xs)
    num = sum((i - xm) * (y - ym) for i, y in enumerate(xs))
    den = sum((i - xm) ** 2 for i in range(n))
    return num / den if den else 0.0


# --------------------------------- HTTP -------------------------------------
class TestSkip(Exception):
    """Un test que no aplica en este server: se omite, no se inventa."""
    pass


def _req(url, payload=None, headers=None, timeout=30):
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=hdrs,
                                 method="POST" if data is not None else "GET")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="replace")
        hdr = dict(r.headers.items())
    return body, (time.perf_counter() - t0) * 1000.0, hdr


def http_json(url, payload=None, headers=None, timeout=30):
    body, ms, hdr = _req(url, payload, headers, timeout)
    try:
        return json.loads(body), ms, hdr
    except ValueError:
        raise RuntimeError("respuesta no-JSON de %s: %s" % (url, body[:200]))


def salud(url, timeout=3):
    """-> (estado, detalle, ms) con estado en ok | cargando | apagado."""
    try:
        obj, ms, _ = http_json(url, timeout=timeout)
        return "ok", str(obj.get("status", obj)), ms
    except urllib.error.HTTPError as e:
        try:
            det = e.read().decode("utf-8", errors="replace")[:160]
        except Exception:
            det = ""
        return "cargando", det, 0.0
    except Exception as e:
        return "apagado", "%s: %s" % (type(e).__name__, e), 0.0


class Cliente:
    """Cliente /completion con medidas de cliente: TTFT, serie TPOT, wall."""

    def __init__(self, args):
        self.base = "http://%s:%d" % (args.host, args.port)
        self.headers = {"Content-Type": "application/json"}
        if getattr(args, "api_key", None):
            self.headers["Authorization"] = "Bearer " + args.api_key
        self.timing_extra = set()

    def completion(self, payload, stream=True, timeout=900, retries=1):
        payload = dict(payload)
        payload.setdefault("cache_prompt", True)
        err_last = None
        for intento in range(retries + 1):
            try:
                if stream:
                    return self._stream(payload, timeout)
                return self._nostream(payload, timeout)
            except urllib.error.HTTPError as e:
                try:
                    det = e.read().decode("utf-8", errors="replace")[:300]
                except Exception:
                    det = ""
                err_last = "HTTP %s: %s" % (e.code, det)
                if e.code in (429, 503, 408) and intento < retries:
                    time.sleep(2)
                    continue
                raise RuntimeError(err_last)
            except RuntimeError:
                raise
            except Exception as e:
                err_last = "%s: %s" % (type(e).__name__, e)
                if intento < retries:
                    time.sleep(2)
                    continue
                raise RuntimeError(err_last)
        raise RuntimeError(err_last or "fallo desconocido")

    def _nostream(self, payload, timeout):
        obj, ms, _ = http_json(self.base + "/completion", payload,
                               self.headers, timeout)
        if isinstance(obj, dict) and obj.get("error"):
            raise RuntimeError("server: %s" % json.dumps(obj["error"])[:300])
        tim = obj.get("timings") or {}
        self._oler(tim)
        return {"text": obj.get("content", "") or "", "ttft_ms": None,
                "tpot_list": [], "wall_ms": ms, "timings": tim, "final": obj,
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
        tlast = t0
        tpots = []
        piezas = []
        final = {}
        tim = {}
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
                    self._oler(tim)
                contenido = obj.get("content")
                if contenido:
                    ahora = time.perf_counter()
                    if ttft is None:
                        ttft = (ahora - t0) * 1000.0
                    else:
                        tpots.append((ahora - tlast) * 1000.0)
                    tlast = ahora
                    piezas.append(contenido)
                final = obj
        wall = (time.perf_counter() - t0) * 1000.0
        return {"text": "".join(piezas), "ttft_ms": ttft, "tpot_list": tpots,
                "wall_ms": wall, "timings": tim, "final": final,
                "tokens_evaluated": final.get("tokens_evaluated"),
                "tokens_predicted": final.get("tokens_predicted")}

    def _oler(self, tim):
        for k in tim:
            if k not in STD_TIMINGS:
                self.timing_extra.add(k)


def decode_ts(r):
    """t/s de generacion [M]: primero lo reportado por el server (timings),
    fallback con lo medido por el cliente. -> (valor, fuente)"""
    tim = r.get("timings") or {}
    v = tim.get("predicted_per_second")
    if v:
        return float(v), "server"
    pn = r.get("tokens_predicted") or 0
    pms = tim.get("predicted_ms")
    if pn and pms:
        return pn / (pms / 1000.0), "server"
    tp = r.get("tpot_list")
    if tp and media(tp) > 0:
        return 1000.0 / media(tp), "cliente"
    return 0.0, "N/D"


def prefill_ts(r):
    """t/s de prefill [M] (server timings, prompt_ms), fallback cliente."""
    tim = r.get("timings") or {}
    v = tim.get("prompt_per_second")
    if v:
        return float(v), "server"
    tev = r.get("tokens_evaluated") or 0
    pms = tim.get("prompt_ms")
    if tev and pms:
        return tev / (pms / 1000.0), "server"
    tt = r.get("ttft_ms")
    if tev and tt:
        return tev / (tt / 1000.0), "cliente"
    return 0.0, "N/D"


# --------------------------- prompts de benchmark ---------------------------
# Protocolo anti-inflado (aprendido + barrido-30): con spec activo, repetir
# el MISMO prompt infla fake el t/s -> prompts DISTINTOS por pasada.
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


def prompts_distintos(n, n_tokens):
    return [prompt_ref(n_tokens, s) for s in range(n)]


def prompt_repetitivo():
    lineas = []
    for i in range(28):
        lineas.append('{"id": %d, "user": "alpha", "event": "login", "agent": '
                      '"Mozilla/5.0", "status": 200, "path": "/api/v1/items"}' % (i % 50))
    return "\n".join(lineas) + "\n\nSummarize the JSON log above in one short sentence."


QA_SANITY = [
    ("Cual es la capital de Francia? Responde muy corto.", ["paris"]),
    ("Cuanto es 17 x 23? Responde solo el numero.", ["391"]),
    ("Quien escribio Don Quijote? Responde muy corto.", ["cervantes"]),
    ("Que planeta es conocido como el planeta rojo? Muy corto.", ["marte"]),
]

PROMPTS_CONFIANZA = [
    "La capital de Francia es", "El resultado de 12 + 30 es",
    "El autor de Don Quijote es", "El planeta rojo se llama",
    "El oceano mas grande es el", "La moneda de Japon es el",
    "El metal liquido a temperatura ambiente es", "El ajedrez se juega en un",
    "El simbolo quimico del oro es", "En invierno el agua se congela porque hace",
]


# ------------------------------- parsers ------------------------------------
def parse_metrics(texto):
    """Texto Prometheus -> (dict clave-limpia -> valor, set de nombres)."""
    vals = {}
    nombres = set()
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_:][A-Za-z0-9_:]*)(\{[^}]*\})?\s+(\S+)$", linea)
        if not m:
            continue
        nombre, labels, valor = m.group(1), m.group(2) or "", m.group(3)
        nombres.add(nombre)
        try:
            vals[nombre + labels] = float(valor)
        except ValueError:
            vals[nombre + labels] = valor
    return vals, nombres


def scan_keys(obj, kws, ruta=""):
    """Busca recursivamente claves que contengan alguna palabra de kws."""
    hits = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = (ruta + "." + k) if ruta else k
            if any(w in k.lower() for w in kws) and isinstance(v, (int, float, str, bool)):
                hits[p] = v
            if isinstance(v, (dict, list)):
                hits.update(scan_keys(v, kws, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:24]):
            hits.update(scan_keys(v, kws, "%s[%d]" % (ruta, i)))
    return hits


RE_ACC_PCT = re.compile(r"accept[^\n]*?(\d{1,3}(?:\.\d+)?)\s*%", re.IGNORECASE)
RE_ACC_PAR = re.compile(r"accepted?\s*[:=]?\s*(\d{1,3})\s*/\s*(\d{1,3})", re.IGNORECASE)
RE_DRAFTED = re.compile(
    r"drafted?\s*[:=,]?\s*(\d{1,4})[^\n]{0,40}?accept(?:ed)?\s*[:=]?\s*(\d{1,4})",
    re.IGNORECASE)
KW_LOG = ("accept", "draft", "spec", "mtp")


def aceptacion_de_log(txt):
    """Multi-patron sobre el log del server (best-effort, NO se inventa).
    Devuelve {tasas:[0-1], pares:[(acc,tot)], eventos, muestras:[lineas]}."""
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
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10)
        return int(out.stdout.strip().splitlines()[0])
    except Exception:
        return None


def ram_proceso(nombre="llama", pid=None):
    """RAM del proceso del server en MiB (psutil opcional)."""
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


# ------------------------- ciclo de vida del server -------------------------
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


def matar_server():
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe", "/T"],
                           capture_output=True, timeout=20)
        else:
            subprocess.run(["pkill", "-f", "llama-server"],
                           capture_output=True, timeout=10)
        time.sleep(3)
        return True
    except Exception:
        return False


def flags_servidor(args, extra=None):
    """Invocacion EXACTA del launcher v2.1 (+ FLAGS_GANADORAS) + extras de la
    config (last-wins en argparse, mecanismo verificado en los barridos)."""
    fl = ["-m", args.model, "-a", "apex35b"] + BASE_FLAGS_LAUNCHER + [
        "--host", args.host, "--port", str(args.port)] + FLAGS_GANADORAS
    if extra:
        fl += list(extra)
    return fl


def esperar_salud(args, proc, ruta_log, timeout=900):
    url = "http://%s:%d/health" % (args.host, args.port)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError("el server termino al arrancar (rc=%s) - ver %s"
                               % (proc.returncode, ruta_log))
        est, det, _ = salud(url)
        if est == "ok":
            return time.time() - t0
        time.sleep(2)
    raise RuntimeError("timeout %d s esperando /health - ver %s" % (timeout, ruta_log))


# ===================== MODO ADJUNTO: SUITE COMPLETA A-F =====================
class Suite:
    def __init__(self, args):
        self.args = args
        self.cli = Cliente(args)
        self.res = {}
        self.textos = []            # TODAS las salidas -> detector de basura E4
        self.props = None
        self.total_slots = 1
        self.n_ctx = None
        self.model_path = ""
        self.metrics_ini = None
        self.metrics_fin = None
        self.nombres_metrics = set()
        self.log_txt = ""
        self.t0_suite = None
        self._serie_512 = []

    def medir(self, tid, titulo, fn):
        section(tid, titulo)
        t0 = time.perf_counter()
        try:
            res = fn() or {}
            res["_estado"] = "ok"
        except TestSkip as e:
            print(yellow("  [OMITIDO] %s" % e))
            res = {"_estado": "omito", "_motivo": str(e)}
        except Exception as e:
            print(red("  [ERROR] %s: %s" % (type(e).__name__, e)))
            res = {"_estado": "error", "_error": "%s: %s" % (type(e).__name__, e)}
        res["_segundos"] = round(time.perf_counter() - t0, 1)
        self.res[tid] = res
        return res

    # ------------------------------ A: diagnostico --------------------------
    def A1(self):
        est, det, ms = salud(self.cli.base + "/health", timeout=5)
        if est != "ok":
            raise TestSkip("server no listo (%s: %s)" % (est, det[:80]))
        kv("salud", "%s (%.1f ms RTT)" % (det, ms))
        out = {"health": det, "health_rtt_ms": round(ms, 1)}
        try:
            modelos, _, _ = http_json(self.cli.base + "/v1/models", timeout=10)
            items = modelos.get("data") or []
            if items:
                mid = items[0].get("id", "")
                meta = items[0].get("meta") or {}
                kv("modelo (v1/models)", mid)
                kv("meta", "n_vocab=%s n_ctx_train=%s n_params=%s size=%s"
                   % (meta.get("n_vocab"), meta.get("n_ctx_train"),
                      meta.get("n_params"), meta.get("size")))
                out["model_id"] = mid
                out["meta"] = meta
        except Exception as e:
            kv("v1/models", "N/D (%s)" % e)
        return out

    def A2(self):
        props, _, _ = http_json(self.cli.base + "/props", timeout=10)
        self.props = props
        self.total_slots = int(props.get("total_slots") or 1)
        self.model_path = str(props.get("model_path") or "")
        dgs = props.get("default_generation_settings") or {}
        self.n_ctx = dgs.get("n_ctx")
        kv("model_path", self.model_path)
        kv("total_slots", self.total_slots)
        kv("n_ctx (default gen settings)", self.n_ctx)
        hits = scan_keys(props, KW_SPEC)
        if hits:
            print(cyan("  señales spec/draft/mtp en props:"))
            for k, v in hits.items():
                print("    %s = %s" % (k, v))
        else:
            print(gray("  sin claves spec/draft/mtp en props (normal: la API no las expone)"))
        if "mtp" in self.model_path.lower():
            print(cyan("  el nombre del GGUF contiene 'MTP' (capas preservadas en el archivo)"))
        return {"model_path": self.model_path, "total_slots": self.total_slots,
                "n_ctx": self.n_ctx, "props_spec_hits": hits}

    def A3(self):
        try:
            texto, _, _ = _req(self.cli.base + "/metrics", timeout=10)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise TestSkip("/metrics 404 - relanza el server con --metrics "
                               "si quieres el inventario Prometheus")
            raise
        vals, nombres = parse_metrics(texto)
        self.metrics_ini = vals
        self.nombres_metrics = nombres
        kv("metricas encontradas", len(nombres))
        kw = {k: v for k, v in vals.items() if any(w in k.lower() for w in KW_SPEC)}
        if kw:
            print(cyan("  contadores spec/draft/mtp detectados:"))
            for k, v in sorted(kw.items()):
                print("    %s = %s" % (k, v))
        interes = [n for n in sorted(nombres) if any(w in n for w in
                   ("tokens_total", "seconds_total", "kv_cache", "slot", "prompt", "predicted"))]
        for n in interes[:24]:
            ej = [v for k, v in vals.items() if k.startswith(n)]
            print("    %s = %s" % (n, ej[:2]))
        return {"n_nombres": len(nombres), "nombres": sorted(nombres),
                "spec_hits": kw, "valores": vals}

    # ------------------------------- B: prefill -----------------------------
    def B1(self):
        """Prefill FRIO (cache_prompt false): pasada 1 calienta, se descarta;
        la pasada real es prefill puro. Metricas: prompt t/s + TTFT."""
        tams = [256, 2048] if self.args.quick else [64, 256, 1024, 2048]
        filas = []
        for i, tam in enumerate(tams):
            calienta = (i == 0)
            r = self.cli.completion(
                {"prompt": prompt_ref(tam, 900 + tam), "n_predict": 1,
                 "temperature": 0, "cache_prompt": False, "ignore_eos": True},
                stream=True, timeout=self.args.timeout)
            ts, fuente = prefill_ts(r)
            tev = r.get("tokens_evaluated") or 0
            ttft = r.get("ttft_ms") or 0.0
            filas.append({"tokens_evaluados": tev, "ttft_ms": round(ttft, 1),
                          "prefill_ts": round(ts, 1), "fuente": fuente,
                          "calentamiento": calienta})
            if calienta:
                kv("calentamiento %5d tok" % tev, "(se descarta)")
            else:
                kv("prefill %5d tok" % tev, "%8.1f tok/s   TTFT %7.1f ms  [%s]"
                   % (ts, ttft, fuente))
        reales = [f for f in filas if not f["calentamiento"] and f["prefill_ts"]]
        max_pf = max((f["prefill_ts"] for f in reales), default=0.0)
        return {"filas": filas, "prefill_ts_max": round(max_pf, 1)}

    def B2(self):
        p = prompt_ref(256, 777)
        rc = self.cli.completion({"prompt": p, "n_predict": 1, "temperature": 0,
                                  "cache_prompt": False, "ignore_eos": True},
                                 stream=True, timeout=self.args.timeout)
        frio = rc.get("ttft_ms") or 0.0
        calientes = []
        for _ in range(3):
            rw = self.cli.completion({"prompt": p, "n_predict": 1, "temperature": 0,
                                      "cache_prompt": True, "ignore_eos": True},
                                     stream=True, timeout=self.args.timeout)
            if rw.get("ttft_ms"):
                calientes.append(rw["ttft_ms"])
        mejora = (1 - media(calientes) / frio) if (frio and calientes) else 0.0
        kv("TTFT frio", "%.1f ms" % frio)
        kv("TTFT calido (3x, misma KV)", "%.1f ms" % media(calientes))
        kv("ahorro por reuso de KV", "%.1f%%" % (mejora * 100))
        return {"ttft_frio_ms": round(frio, 1),
                "ttft_calido_ms": round(media(calientes), 1),
                "ahorro_pct": round(mejora * 100, 1)}

    # ------------------------------- C: decode ------------------------------
    def C1(self):
        """Decode escalado con protocolo anti-inflado: prompts DISTINTOS por
        pasada (+1 calentamiento que se descarta), ignore_eos, temp 0."""
        plan = [(256, 3)] if self.args.quick else [(128, 4), (256, 4), (512, 4)]
        out = {"tamanos": []}
        for npred, nprom in plan:
            ts_l, tp_l, cli_l = [], [], []
            serie = []
            prompts = prompts_distintos(nprom + 1, 128)
            for i, p in enumerate(prompts):
                r = self.cli.completion(
                    {"prompt": p, "n_predict": npred, "temperature": 0,
                     "seed": 42, "ignore_eos": True},
                    stream=True, timeout=self.args.timeout)
                self.textos.append(r["text"])
                if npred == 512:
                    serie = list(r.get("tpot_list") or [])
                ts, fuente = decode_ts(r)
                if i == 0:
                    continue  # calentamiento
                ts_l.append(ts)
                if r.get("tpot_list"):
                    tp_l += r["tpot_list"]
                if r.get("tokens_predicted"):
                    gen_ms = r["wall_ms"] - (r.get("ttft_ms") or 0)
                    if gen_ms > 0:
                        cli_l.append(r["tokens_predicted"] / (gen_ms / 1000.0))
            fila = {"n_predict": npred, "prompts_distintos": nprom,
                    "decode_ts_media": round(media(ts_l), 2),
                    "decode_ts_p50": round(mediana(ts_l), 2),
                    "decode_ts_p95": round(p95(ts_l), 2),
                    "decode_ts_sigma": round(desvest(ts_l), 2),
                    "tpot_ms": round(media(tp_l), 1),
                    "cliente_ts_media": round(media(cli_l), 2),
                    "fuente": fuente}
            out["tamanos"].append(fila)
            kv("decode %3d tok x%d prompts" % (npred, nprom),
               "%6.2f t/s (p50 %.2f p95 %.2f sigma %.2f) TPOT %.1f ms [cliente %.2f]"
               % (fila["decode_ts_media"], fila["decode_ts_p50"], fila["decode_ts_p95"],
                  fila["decode_ts_sigma"], fila["tpot_ms"], fila["cliente_ts_media"]))
            if npred == 512:
                self._serie_512 = serie
        return out

    def C2(self):
        if not self._serie_512 or len(self._serie_512) < 16:
            raise TestSkip("sin serie TPOT del run 512 (corre C1 completo, sin --quick)")
        serie = self._serie_512
        n = len(serie)
        q = max(1, n // 4)
        cuartos = []
        for i in range(4):
            tramo = serie[i * q:(i + 1) * q] if i < 3 else serie[3 * q:]
            tps = (len(tramo) / (sum(tramo) / 1000.0)) if tramo else 0.0
            cuartos.append(round(tps, 2))
        caida = (1 - cuartos[3] / cuartos[0]) if cuartos[0] else 0.0
        for i, v in enumerate(cuartos):
            kv("cuarto %d t/s" % (i + 1), "%.2f" % v)
        kv("degradacion 1o -> 4o", "%.1f%% %s" % (
            caida * 100, yellow("(vigilar)") if caida > 0.10 else green("(ok)")))
        return {"cuartos_ts": cuartos, "degradacion_pct": round(caida * 100, 1)}

    def C3(self):
        """Heuristica de draft: si hay especulativa con draft greedy (default
        del build, dump L374-377), el sampling greedy acepta MAS draft y el
        decode sube vs el preset creativo. Es heuristica, no acceptance real."""
        t0_l = []
        fuente0 = "server"
        c1 = self.res.get("C1") or {}
        fila256 = next((f for f in (c1.get("tamanos") or [])
                        if f.get("n_predict") == 256), None)
        if fila256:
            t0_l = [fila256["decode_ts_media"]]
            fuente0 = fila256.get("fuente", "server")
        else:
            for p in prompts_distintos(3, 128):
                r = self.cli.completion({"prompt": p, "n_predict": 256, "temperature": 0,
                                         "seed": 42, "ignore_eos": True},
                                        stream=True, timeout=self.args.timeout)
                self.textos.append(r["text"])
                ts, _ = decode_ts(r)
                t0_l.append(ts)
        t1_l = []
        for p in prompts_distintos(3, 128):
            r = self.cli.completion({"prompt": p, "n_predict": 256, "temperature": 1.0,
                                     "top_k": 20, "top_p": 0.95, "ignore_eos": True},
                                    stream=True, timeout=self.args.timeout)
            self.textos.append(r["text"])
            ts, _ = decode_ts(r)
            t1_l.append(ts)
        m0, m1 = media(t0_l), media(t1_l)
        ratio = (m0 / m1) if m1 else 0.0
        kv("t/s greedy (temp 0)", "%.2f [%s]" % (m0, fuente0))
        kv("t/s creativo (preset think 1.0/20/0.95)", "%.2f" % m1)
        kv("ratio greedy/creativo", "%.3f %s" % (
            ratio, cyan("(coherente con draft activo: greedy acepta mas)")
            if ratio > 1.08 else gray("(sin señal clara de draft)")))
        return {"decode_ts_greedy": round(m0, 2), "decode_ts_creativo": round(m1, 2),
                "ratio": round(ratio, 3)}


    # ------------------------------ D: MTP / spec ---------------------------
    def D1(self):
        """Deteccion MTP/especulativa agregando senales duras independientes:
        metrics, props, keys extra de timings, log, nombre del GGUF."""
        senales = []
        kw = {k: v for k, v in (self.metrics_ini or {}).items()
              if any(w in k.lower() for w in KW_SPEC)}
        if kw:
            senales.append({"fuente": "metrics", "datos": kw})
        hits = scan_keys(self.props or {}, KW_SPEC)
        if hits:
            senales.append({"fuente": "props", "datos": hits})
        if self.cli.timing_extra:
            senales.append({"fuente": "timings", "datos": sorted(self.cli.timing_extra)})
        if self.log_txt:
            acc = aceptacion_de_log(self.log_txt)
            if acc["eventos"]:
                senales.append({"fuente": "log", "datos": {
                    "eventos": acc["eventos"], "tasa_media": tasa_media(acc)}})
        if "mtp" in self.model_path.lower():
            senales.append({"fuente": "nombre_modelo", "datos": self.model_path})
        for s in senales:
            kv("señal %s" % s["fuente"], json.dumps(s["datos"], ensure_ascii=False)[:140])
        duras = sum(1 for s in senales
                    if s["fuente"] in ("metrics", "props", "timings", "log"))
        c3 = self.res.get("C3") or {}
        ratio = c3.get("ratio") or 0.0
        if duras >= 2:
            ver = "ACTIVA (>=2 señales duras independientes)"
        elif duras == 1:
            ver = "PROBABLE (1 señal dura; confirma con --protocolo o --compare)"
        elif ratio > 1.08:
            ver = "POSIBLE (solo heuristica de temperatura)"
        else:
            ver = "NO DETECTADA (server sin spec o sin telemetria; usa --protocolo)"
        kv("veredicto deteccion", bold(ver))
        return {"senales": senales, "duras": duras, "veredicto": ver}

    def D2(self):
        """cache_reuse = reuso de KV por KV-shift (dump L620). NO es MTP, pero
        es la especulativa 'gratis' por cache: se mide con texto repetitivo.
        Nota: si el server no acepta el campo por-request, las 4 medidas
        saldran iguales -> entonces es flag de lanzamiento (--cache-reuse N)."""
        p = prompt_repetitivo()
        filas = []
        for cr in ([0, 256] if self.args.quick else [0, 64, 128, 256]):
            r = self.cli.completion({"prompt": p, "n_predict": 128, "temperature": 0,
                                     "seed": 7, "ignore_eos": True, "cache_reuse": cr},
                                    stream=True, timeout=self.args.timeout)
            self.textos.append(r["text"])
            ts, fuente = decode_ts(r)
            ttft = r.get("ttft_ms") or 0.0
            filas.append({"cache_reuse": cr, "decode_ts": round(ts, 2),
                          "ttft_ms": round(ttft, 1)})
            kv("cache_reuse=%3d" % cr, "%6.2f t/s   TTFT %7.1f ms [%s]"
               % (ts, ttft, fuente))
        base = filas[0]["decode_ts"]
        mejor = max(filas, key=lambda f: f["decode_ts"])
        gan = 0.0
        if base:
            gan = (mejor["decode_ts"] / base - 1) * 100
            kv("mejor vs off", "%+.1f%% (cache_reuse=%d)" % (gan, mejor["cache_reuse"]))
        return {"filas": filas, "mejora_pct": round(gan, 1),
                "nota": "cache_reuse es KV-shift (L620), no MTP; si todas las filas "
                        "son iguales, es flag de lanzamiento: --cache-reuse N"}

    def D3(self):
        if self.args.log_file:
            # re-lectura JUSTO AHORA: el server escribe las lineas de
            # acceptance DURANTE los tests, no antes de que arranquemos
            try:
                with open(self.args.log_file, "r", encoding="utf-8",
                          errors="replace") as f:
                    self.log_txt = f.read()
            except Exception:
                pass
        if not self.log_txt:
            raise TestSkip("sin log del server: pasame --log-file server.log "
                           "(o usa --protocolo, que captura el log solo)")
        acc = aceptacion_de_log(self.log_txt)
        tm = tasa_media(acc)
        if tm is None:
            print(yellow("  no encontre lineas de aceptacion; muestras del log con "
                         "kw accept/draft/spec/mtp:"))
            for m in acc["muestras"][:6]:
                print(gray("    | " + m))
            raise TestSkip("acceptance no visible en el log (no se inventa; "
                           "revisa las muestras de arriba)")
        kv("eventos de aceptacion", acc["eventos"])
        kv("tasa media", "%.1f%%" % (tm * 100))
        if acc["pares"]:
            kv("tokens aceptados/evento (media)", "%.2f"
               % media([a for a, _ in acc["pares"]]))
        hist = {"<25%": 0, "25-50%": 0, "50-75%": 0, ">=75%": 0}
        for t in acc["tasas"] + [a / float(b) for a, b in acc["pares"]]:
            k = "<25%" if t < 0.25 else "25-50%" if t < 0.5 else \
                "50-75%" if t < 0.75 else ">=75%"
            hist[k] += 1
        kv("histograma", json.dumps(hist))
        ver = ("ALTA (>=70%: zona GO del criterio pre-registrado)" if tm >= 0.70 else
               "MEDIA (50-70%: marginal, decide el coste por turno)" if tm >= 0.50 else
               "BAJA (<50%: probar --spec-draft-p-min 0.85 una vez, dump L369)")
        kv("lectura", ver)
        print(gray("  muestras del log:"))
        for m in acc["muestras"][:6]:
            print(gray("    | " + m))
        return {"eventos": acc["eventos"], "tasa_media": round(tm, 4),
                "histograma": hist, "muestras": acc["muestras"][:8], "lectura": ver}

    # ------------------------------- E: calidad -----------------------------
    def E1(self):
        p = "Escribe una frase corta sobre el mar. " + prompt_ref(24, 321)
        salidas = []
        for _ in range(3):
            r = self.cli.completion({"prompt": p, "n_predict": 96, "temperature": 0,
                                     "seed": 42}, stream=True, timeout=self.args.timeout)
            salidas.append(r["text"])
        self.textos += salidas
        det = len(set(salidas)) == 1
        kv("3 peticiones identicas (temp 0, seed 42)",
           green("IDENTICAS") if det else red("DIFIEREN"))
        return {"determinista": det, "longitudes": [len(s) for s in salidas]}

    def E2(self):
        prs = PROMPTS_CONFIANZA[:4] if self.args.quick else PROMPTS_CONFIANZA
        probs = []
        for p in prs:
            r = self.cli.completion({"prompt": p, "n_predict": 24, "temperature": 0,
                                     "seed": 1, "n_probs": 5}, stream=True,
                                    timeout=self.args.timeout)
            self.textos.append(r["text"])
            for tok in (r["final"].get("completion_probabilities") or []):
                lp = tok.get("probs") or []
                if lp:
                    probs.append(max(float(x.get("prob", 0.0)) for x in lp))
        if not probs:
            raise TestSkip("el server no devolvio completion_probabilities (n_probs)")
        kv("tokens muestreados", len(probs))
        kv("confianza top-1 media", "%.3f" % media(probs))
        kv("nota", "proxy de calidad comparable entre configs (A/B) - no es PPL real")
        return {"tokens": len(probs), "top1_media": round(media(probs), 4),
                "top1_p50": round(mediana(probs), 4)}

    def E3(self):
        filas = []
        for q, keys in QA_SANITY:
            r = self.cli.completion({"prompt": q, "n_predict": 64, "temperature": 0,
                                     "seed": 1}, stream=True, timeout=self.args.timeout)
            txt = (r["text"] or "").strip().replace("\n", " ")
            self.textos.append(r["text"])
            ok = any(k in txt.lower() for k in keys)
            filas.append({"pregunta": q[:44], "ok": ok, "respuesta": txt[:90]})
            kv(("OK   " if ok else "FALLO"), "%s -> %s" % (q[:36], txt[:50] or "(vacio)"))
        n_ok = sum(1 for f in filas if f["ok"])
        kv("aciertos", "%d/%d" % (n_ok, len(filas)))
        return {"filas": filas, "aciertos": n_ok, "total": len(filas)}

    # ------------------------------- F: robustez ----------------------------
    def F1(self):
        n = 5 if self.args.quick else 12
        ts_l, errores = [], 0
        for i in range(n):
            try:
                r = self.cli.completion(
                    {"prompt": prompt_ref(128, 400 + i), "n_predict": 128,
                     "temperature": 0, "seed": 42, "ignore_eos": True},
                    stream=True, timeout=self.args.timeout)
                self.textos.append(r["text"])
                ts, _ = decode_ts(r)
                ts_l.append(ts)
                print("    req %2d: %6.2f t/s" % (i + 1, ts))
            except Exception as e:
                errores += 1
                print(red("    req %2d: ERROR %s" % (i + 1, e)))
        if not ts_l:
            raise TestSkip("ninguna peticion tuvo exito")
        der = pendiente(ts_l)
        kv("t/s media +/- sigma", "%.2f +/- %.2f" % (media(ts_l), desvest(ts_l)))
        kv("drift (t/s por peticion)", "%+.3f %s" % (
            der, yellow("(caida sostenida: throttling/calentamiento)")
            if der < -0.10 else green("(estable)")))
        kv("errores", errores)
        return {"n": n, "ts_media": round(media(ts_l), 2),
                "ts_sigma": round(desvest(ts_l), 2), "drift": round(der, 4),
                "errores": errores, "serie": [round(x, 2) for x in ts_l]}

    def F2(self):
        if self.args.quick:
            raise TestSkip("modo --quick")
        if self.total_slots < 2:
            raise TestSkip("total_slots=%d (relanza el server con -np 2 para "
                           "probar concurrencia)" % self.total_slots)
        resultados = {}
        for conc in [c for c in (2, 4) if c <= self.total_slots]:
            barrera = threading.Barrier(conc)
            saco = {}

            def trabajador(idx):
                cli = Cliente(self.args)
                payload = {"prompt": prompt_ref(128, 600 + idx), "n_predict": 256,
                           "temperature": 0, "seed": 42 + idx, "ignore_eos": True}
                barrera.wait()
                t0 = time.perf_counter()
                r = cli.completion(payload, stream=False, timeout=self.args.timeout)
                dt = time.perf_counter() - t0
                saco[idx] = (r.get("tokens_predicted") or 0, dt, r.get("text", ""))

            hilos = [threading.Thread(target=trabajador, args=(i,)) for i in range(conc)]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
            tok = sum(x[0] for x in saco.values())
            wall = max((x[1] for x in saco.values()), default=0.0)
            agg = tok / wall if wall else 0.0
            resultados[str(conc)] = {"tokens": tok, "wall_s": round(wall, 2),
                                     "ts_agregado": round(agg, 2)}
            kv("concurrencia %d" % conc, "%.2f t/s agregados (%d tok en %.1f s)"
               % (agg, tok, wall))
            self.textos += [x[2] for x in saco.values()]
        return {"concurrencias": resultados}

    def F3(self):
        if self.args.quick:
            raise TestSkip("modo --quick")
        dur = 45.0
        npre = int(dur * 25)  # ~25 t/s techo conservador
        r = self.cli.completion({"prompt": prompt_ref(64, 901), "n_predict": npre,
                                 "temperature": 0, "seed": 42, "ignore_eos": True},
                                stream=True, timeout=int(dur * 4))
        self.textos.append(r["text"])
        tp = r.get("tpot_list") or []
        if not tp:
            raise TestSkip("sin serie de tokens (server sin stream?)")
        ttft_s = (r.get("ttft_ms") or 0.0) / 1000.0
        t_abs = []
        accu = ttft_s
        for x in tp:
            accu += x / 1000.0
            t_abs.append(accu)
        total = t_abs[-1] if t_abs else 0.0
        vent = 5.0
        nw = max(1, int(total / vent))
        series = [0] * nw
        for t in t_abs:
            series[min(nw - 1, int(t / vent))] += 1
        ts_vent = [c / vent for c in series]
        for i, v in enumerate(ts_vent):
            print("    v%02d [%4.0f-%4.0f s): %6.2f t/s" % (
                i + 1, i * vent, (i + 1) * vent, v))
        decay = (1 - ts_vent[-1] / ts_vent[0]) if (ts_vent and ts_vent[0]) else 0.0
        kv("t/s medio sostenido", "%.2f en %.0f s" % (media(ts_vent), total))
        kv("decay ultima vs primera ventana", "%+.1f%% %s" % (
            decay * 100, yellow("(vigilar)") if decay > 0.10 else green("(plano)")))
        return {"ventanas_ts": [round(v, 2) for v in ts_vent],
                "medio": round(media(ts_vent), 2), "decay_pct": round(decay * 100, 1),
                "duracion_s": round(total, 1)}

    def E4(self):
        n = sum(basura_en(t) for t in self.textos)
        kv("salidas analizadas", len(self.textos))
        kv("firmas de corrupcion (////, punct. repetida)",
           red(str(n)) if n else "0")
        if n:
            kv("lectura", yellow("ALERTA bug #23577: NO adoptar config con basura"))
        return {"salidas": len(self.textos), "hits": n}

    def F4(self):
        v = vram_mib()
        kv("VRAM usada (nvidia-smi)", ("%d MiB" % v) if v is not None
           else "N/D (nvidia-smi no disponible)")
        ram = ram_proceso(nombre="llama")
        kv("RAM proceso llama", ("%.0f MiB" % ram) if ram
           else "N/D (psutil opcional: pip install psutil)")
        out = {"vram_mib": v, "ram_mib": round(ram) if ram else None}
        try:
            texto, _, _ = _req(self.cli.base + "/metrics", timeout=10)
            self.metrics_fin, _n2 = parse_metrics(texto)
        except Exception:
            self.metrics_fin = None
        if self.metrics_ini is not None and self.metrics_fin is not None:
            d_tok = None
            for k in self.metrics_fin:
                base_n = k.split("{")[0]
                if "predicted" in base_n and "total" in base_n and k in self.metrics_ini:
                    try:
                        d = self.metrics_fin[k] - self.metrics_ini[k]
                        if isinstance(d, (int, float)):
                            d_tok = d
                            break
                    except TypeError:
                        pass
            elapsed = time.time() - (self.t0_suite or time.time())
            if d_tok and elapsed > 0:
                kv("tokens generados en la suite", "%d en %.0f s -> %.2f t/s medio global"
                   % (d_tok, elapsed, d_tok / elapsed))
                out["tokens_suite"] = d_tok
                out["ts_global_suite"] = round(d_tok / elapsed, 2)
        return out

    # ------------------------------- resumen --------------------------------
    def resumen(self):
        R = self.res
        c1 = R.get("C1") or {}
        tam = c1.get("tamanos") or []
        f256 = next((f for f in tam if f.get("n_predict") == 256), None)
        f512 = next((f for f in tam if f.get("n_predict") == 512), None)
        b1 = R.get("B1") or {}
        b2 = R.get("B2") or {}
        d1 = R.get("D1") or {}
        d3 = R.get("D3") or {}
        e1 = R.get("E1") or {}
        e2 = R.get("E2") or {}
        e3 = R.get("E3") or {}
        e4 = R.get("E4") or {}
        f1 = R.get("F1") or {}
        f4 = R.get("F4") or {}
        pf_ts = b1.get("prefill_ts_max")
        dec = f256.get("decode_ts_media") if f256 else None
        coste = None
        if pf_ts and dec:
            coste = round(300.0 / pf_ts + 300.0 / dec, 2)
        return {
            "modo": "adjunto",
            "decode_ts_256": f256.get("decode_ts_media") if f256 else None,
            "decode_ts_512": f512.get("decode_ts_media") if f512 else None,
            "tpot_ms_256": f256.get("tpot_ms") if f256 else None,
            "prefill_ts_max": pf_ts,
            "ttft_frio_ms": b2.get("ttft_frio_ms"),
            "acceptance": d3.get("tasa_media"),
            "mtp_veredicto": d1.get("veredicto"),
            "top1_conf": e2.get("top1_media"),
            "determinista": e1.get("determinista"),
            "sanity": ("%s/%s" % (e3.get("aciertos"), e3.get("total"))) if e3 else None,
            "garbage_hits": e4.get("hits"),
            "estabilidad_ts": f1.get("ts_media"),
            "drift": f1.get("drift"),
            "vram_mib": f4.get("vram_mib"),
            "coste_turno_ms": coste,
        }

    def lineas_veredicto(self, s):
        out = []
        out.append("Deteccion MTP/spec: %s" % (s.get("mtp_veredicto") or "N/D"))
        acc = s.get("acceptance")
        if acc is not None:
            if acc >= 0.70:
                out.append("Acceptance %.1f%% >= 70%%: zona GO del criterio "
                           "pre-registrado" % (acc * 100))
            elif acc >= 0.50:
                out.append("Acceptance %.1f%% marginal (50-70%%): decide el "
                           "coste por turno" % (acc * 100))
            else:
                out.append("Acceptance %.1f%% < 50%%: probar --spec-draft-p-min "
                           "0.85 una vez (dump L369)" % (acc * 100))
        else:
            out.append("Acceptance N/D: sin log del server (no se inventa)")
        if s.get("garbage_hits"):
            out.append(red("ALERTA: %d firmas de corrupcion (bug #23577) - "
                           "NO adoptar esta config" % s["garbage_hits"]))
        if s.get("determinista") is False:
            out.append(red("AVISO: greedy NO determinista entre 3 pasadas"))
        if s.get("coste_turno_ms"):
            out.append("Coste por turno tipico [D] (prefill 300 tok frio + "
                       "300 tok decode): %.1f s" % (s["coste_turno_ms"] / 1000.0))
        return out


def run_adjunto(args):
    s = Suite(args)
    s.t0_suite = time.time()
    print(bold("=" * 76))
    print(bold("  MTP-TESTER v1.0 - modo ADJUNTO - Qwen3.6-35B-A3B APEX-I-MINI"))
    print(bold("  instrumento [M]: todo lo que imprime es medido en vivo"))
    print(bold("=" * 76))
    kv("objetivo", "http://%s:%d" % (args.host, args.port))
    kv("duracion estimada", "~3-4 min con --quick, ~9-12 min completa")
    if args.log_file:
        try:
            with open(args.log_file, "r", encoding="utf-8", errors="replace") as f:
                s.log_txt = f.read()
            print(cyan("[i] log del server: %s (%d lineas)"
                       % (args.log_file, s.log_txt.count("\n") + 1)))
        except Exception as e:
            print(yellow("[i] no pude leer --log-file: %s" % e))
    else:
        print(gray("[i] sin --log-file: la acceptance del draft (D3) quedara N/D;"))
        print(gray("    lanza el server con  ... > server.log 2>&1  y pasamela."))
    s.medir("A1", "Conectividad y salud", s.A1)
    s.medir("A2", "Props y configuracion", s.A2)
    s.medir("A3", "Metricas Prometheus (snapshot inicial)", s.A3)
    s.medir("B1", "Prefill escalado FRIO (cache_prompt false)", s.B1)
    s.medir("B2", "TTFT frio vs calido (reuso de KV)", s.B2)
    s.medir("C1", "Decode escalado - prompts DISTINTOS (anti-inflado)", s.C1)
    s.medir("C2", "Curva temporal (cuartos del run 512)", s.C2)
    s.medir("C3", "Impacto sampling: greedy vs preset think", s.C3)
    s.medir("D1", "Deteccion MTP / especulativa", s.D1)
    s.medir("D2", "cache_reuse sweep (KV-shift, dump L620)", s.D2)
    s.medir("D3", "Acceptance del draft (log del server)", s.D3)
    s.medir("E1", "Determinismo greedy", s.E1)
    s.medir("E2", "Confianza top-1 (n_probs)", s.E2)
    s.medir("E3", "Sanity factico", s.E3)
    s.medir("F1", "Estabilidad secuencial (drift/errores)", s.F1)
    s.medir("F2", "Concurrencia (slots)", s.F2)
    s.medir("F3", "Throughput sostenido", s.F3)
    s.medir("E4", "Detector de corrupcion global (bug #23577)", s.E4)
    s.medir("F4", "Recursos + metricas globales", s.F4)
    resumen = s.resumen()
    veredicto = s.lineas_veredicto(resumen)
    section("RESUMEN", "metricas canonicas y veredicto")
    kv("decode t/s (256)", resumen.get("decode_ts_256"))
    kv("TPOT ms (256)", resumen.get("tpot_ms_256"))
    kv("prefill t/s (max)", resumen.get("prefill_ts_max"))
    kv("acceptance draft", ("%.1f%%" % (resumen["acceptance"] * 100))
       if resumen.get("acceptance") is not None else "N/D")
    kv("confianza top-1", resumen.get("top1_conf"))
    kv("coste por turno [D]", resumen.get("coste_turno_ms"))
    print("")
    for ln in veredicto:
        print("  * " + ln)
    doc = {
        "meta": {
            "modo": "adjunto", "fecha": datetime.now().isoformat(),
            "server": s.cli.base, "modelo": s.model_path or "N/D",
            "flags": "(server ya corriendo; flags no visibles por API)",
            "quick": bool(args.quick), "log_file": args.log_file,
        },
        "props": s.props,
        "tests": s.res,
        "summary": resumen,
        "veredicto": [re.sub(r"\x1b\[[0-9;]*m", "", x) for x in veredicto],
    }
    jp, mp = guardar_informes(args, doc, "informe-mtp-adjunto")
    print("")
    print(green("[OK] informes:"))
    print("    " + jp)
    print("    " + mp)
    return 0


# ============================== INFORMES ====================================
def _md_tabla(cabs, filas):
    out = ["| " + " | ".join(str(c) for c in cabs) + " |",
           "|" + "---|" * len(cabs)]
    for f in filas:
        out.append("| " + " | ".join(str(x) for x in f) + " |")
    return "\n".join(out) + "\n"


def render_md(doc):
    L = []
    m = doc.get("meta") or {}
    L.append("# Informe MTP-TESTER (%s)" % m.get("modo", "?"))
    L.append("")
    L.append("- fecha: %s" % m.get("fecha"))
    L.append("- server: %s" % m.get("server"))
    L.append("- modelo: %s" % m.get("modelo"))
    L.append("- flags: %s" % (m.get("flags") or "(ancla launcher v2.1)"))
    L.append("")
    for tid, res in (doc.get("tests") or {}).items():
        L.append("## [%s] %s" % (tid, res.get("_estado", "")))
        L.append("")
        for k, v in res.items():
            if k.startswith("_"):
                continue
            if isinstance(v, list) and v and isinstance(v[0], dict):
                cabs = list(v[0].keys())
                L.append(_md_tabla(cabs, [[f.get(c, "") for c in cabs] for f in v]))
            elif isinstance(v, list):
                L.append("- %s: %s" % (k, ", ".join(str(x) for x in v[:12])))
            elif isinstance(v, dict):
                L.append("- %s: %s" % (k, json.dumps(v, ensure_ascii=False)[:300]))
            else:
                L.append("- %s: %s" % (k, v))
        L.append("")
    L.append("## Resumen")
    L.append("")
    s = doc.get("summary") or {}
    if isinstance(s, dict):
        L.append(_md_tabla(["metrica", "valor"], [[k, v] for k, v in s.items()
                                                  if not isinstance(v, (dict, list))]))
    L.append("## Veredicto")
    L.append("")
    for x in doc.get("veredicto") or []:
        L.append("- %s" % x)
    L.append("")
    return "\n".join(L)


def guardar_informes(args, doc, prefijo):
    ts = time.strftime("%Y%m%d-%H%M%S")
    pref = args.out or prefijo
    d = os.path.dirname(os.path.abspath(pref))
    if d and d != os.path.abspath("."):
        os.makedirs(d, exist_ok=True)
    base = "%s-%s" % (pref.rstrip("\\/") or prefijo, ts)
    jp = base + ".json"
    mp = base + ".md"
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, default=str)
    with open(mp, "w", encoding="utf-8") as f:
        f.write(render_md(doc))
    return jp, mp


# ============================== MODO PROTOCOLO T2 ===========================
# Criterios pre-registrados de investigacion-mtp-100 (RUTAS.md):
#   acc >= 70% y decode > base -> GO · acc >= 70% y decode <= base -> cuello de
#   computo, MTP cerrado (EAGLE-3 hereda veredicto) · acc < 50% -> probar
#   p-min 0.85 una vez (T2-E) · basura "////" o sanity roto -> NO adoptar.
CONFIGS_T2 = [
    {"id": "T2-0", "nombre": "ANCLA launcher v2.1", "spec": False, "flags": [],
     "hipotesis": "reproducir el ancla 21.5 t/s en ESTA corrida (base de "
                  "comparacion); sin esto ningun delta es creible"},
    {"id": "T2-A", "nombre": "draft-mtp n-max 2", "spec": True,
     "flags": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2"],
     "hipotesis": "n-max 2 = mejor acceptance en MoE 35B (PR #22673; benchmark "
                  "independiente: +22% con acc 76%)"},
    {"id": "T2-B", "nombre": "A + p-min 0.75", "spec": True,
     "flags": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2",
               "--spec-draft-p-min", "0.75"],
     "hipotesis": "p-min corta el draft cuando duda (NUNCA probado aqui; "
                  "comunidad 0.75-0.8, discusion #25198)"},
    {"id": "T2-C", "nombre": "B + draft 100% CPU", "spec": True,
     "flags": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2",
               "--spec-draft-p-min", "0.75", "--spec-draft-device", "none"],
     "hipotesis": "draft sin offload (dump L379-381: 'none = don't offload') "
                  "protege el prefill del golpe D2H del PR #22673"},
    {"id": "T2-D", "nombre": "A + KV f16", "spec": True,
     "flags": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2",
               "-ctk", "f16", "-ctv", "f16"],
     "hipotesis": "blindaje del leak #23635 (MTP + KV cuantizada); last-wins "
                  "sobre q8_0 del launcher (mecanismo del barrido)"},
]
T2_E = {"id": "T2-E", "nombre": "B + p-min 0.85", "spec": True,
        "flags": ["--spec-type", "draft-mtp", "--spec-draft-n-max", "2",
                  "--spec-draft-p-min", "0.85"],
        "hipotesis": "rescate del criterio pre-registrado si acc(T2-B) < 50%"}

CSV_COLS = ["ts", "cfg", "flags_extra", "load_s", "prefill_ts_512", "decode_ts_256",
            "decode_ts_sigma", "tpot_ms", "acceptance", "accept_eventos",
            "top1_conf", "determinista", "sanity", "garbage_hits", "vram_mib",
            "ram_mib", "coste_turno_ms", "log", "error"]


def _csv_append(args, res):
    ruta = args.csv or "tester-mtp-historial.csv"
    try:
        nuevo = not os.path.exists(ruta)
        with open(ruta, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLS)
            if nuevo:
                w.writeheader()
            fila = dict((k, res.get(k, "")) for k in CSV_COLS)
            if isinstance(fila.get("flags_extra"), list):
                fila["flags_extra"] = " ".join(fila["flags_extra"])
            if isinstance(fila.get("determinista"), bool):
                fila["determinista"] = int(fila["determinista"])
            w.writerow(fila)
    except Exception as e:
        print(yellow("  [i] no pude escribir el CSV de historial: %s" % e))


def _medida_compacta(args, cfg):
    """Bateria compacta por config (~3-4 min): prefill frio 512, decode 5
    prompts distintos x 256 (descarta la 1a), determinismo, top-1, sanity 2,
    recursos y coste por turno."""
    cli = Cliente(args)
    out = {}
    # 1) prefill FRIO 512
    r = cli.completion({"prompt": prompt_ref(512, 9001), "n_predict": 1,
                        "temperature": 0, "cache_prompt": False, "ignore_eos": True},
                       stream=True, timeout=args.timeout)
    pf, fuente_pf = prefill_ts(r)
    out["prefill_ts_512"] = round(pf, 1)
    out["prefill_fuente"] = fuente_pf
    out["prefill_tokens"] = r.get("tokens_evaluated") or 0
    # 2) decode anti-inflado
    ts_l, tp_l, textos = [], [], []
    for i, p in enumerate(prompts_distintos(5, 128)):
        rr = cli.completion({"prompt": p, "n_predict": 256, "temperature": 0,
                             "seed": 42, "ignore_eos": True},
                            stream=True, timeout=args.timeout)
        textos.append(rr.get("text", ""))
        ts, _ = decode_ts(rr)
        if i == 0:
            continue
        ts_l.append(ts)
        if rr.get("tpot_list"):
            tp_l += rr["tpot_list"]
    out["decode_ts_256"] = round(media(ts_l), 2)
    out["decode_ts_sigma"] = round(desvest(ts_l), 2)
    out["tpot_ms"] = round(media(tp_l), 1)
    out["garbage_hits"] = sum(basura_en(t) for t in textos)
    # 3) determinismo
    p_det = "Escribe una frase corta sobre el mar. " + prompt_ref(24, 321)
    ds = []
    for _ in range(2):
        rd = cli.completion({"prompt": p_det, "n_predict": 96, "temperature": 0,
                             "seed": 42}, stream=True, timeout=args.timeout)
        ds.append(rd.get("text", ""))
    textos += ds
    out["determinista"] = (len(set(ds)) == 1)
    # 4) confianza top-1 (4 prompts cortos)
    probs = []
    for p in PROMPTS_CONFIANZA[:4]:
        rc = cli.completion({"prompt": p, "n_predict": 24, "temperature": 0,
                             "seed": 1, "n_probs": 5}, stream=True,
                            timeout=args.timeout)
        for tok in (rc["final"].get("completion_probabilities") or []):
            lp = tok.get("probs") or []
            if lp:
                probs.append(max(float(x.get("prob", 0.0)) for x in lp))
    out["top1_conf"] = round(media(probs), 4) if probs else None
    # 5) sanity (2 preguntas)
    ac = 0
    for q, keys in QA_SANITY[:2]:
        rq = cli.completion({"prompt": q, "n_predict": 64, "temperature": 0,
                             "seed": 1}, stream=True, timeout=args.timeout)
        t = (rq.get("text") or "").lower()
        ac += 1 if any(k in t for k in keys) else 0
    out["sanity"] = "%d/2" % ac
    # 6) recursos
    out["vram_mib"] = vram_mib()
    ram = ram_proceso(nombre="llama")
    out["ram_mib"] = round(ram) if ram else None
    # 7) coste por turno [D]: prefill 300 tok frio + 300 tok decode
    if pf and out["decode_ts_256"]:
        out["coste_turno_ms"] = round(300.0 / pf + 300.0 / out["decode_ts_256"], 2)
    return out


def medir_config_protocolo(args, cfg, dir_logs):
    ruta_log = os.path.join(dir_logs, "%s-%s.log"
                            % (cfg["id"], time.strftime("%Y%m%d-%H%M%S")))
    flags = flags_servidor(args, cfg["flags"])
    print(gray("    log: " + ruta_log))
    print("    flags extra: %s" % (" ".join(cfg["flags"]) if cfg["flags"]
                                   else "(ninguna = ancla launcher v2.1)"))
    res = {"id": cfg["id"], "nombre": cfg["nombre"], "log": ruta_log,
           "flags_extra": list(cfg["flags"])}
    logf = open(ruta_log, "w", encoding="utf-8")
    proc = None
    try:
        try:
            proc = subprocess.Popen(
                [args.server] + flags, stdout=logf, stderr=subprocess.STDOUT,
                cwd=(os.path.dirname(os.path.abspath(args.server)) or "."))
        except Exception as e:
            res["error"] = "no pude lanzar el server: %s" % e
            return res
        try:
            res["load_s"] = round(esperar_salud(args, proc, ruta_log,
                                                args.load_timeout), 1)
        except Exception as e:
            res["error"] = str(e)
            return res
        print("    server arriba en %s s; midiendo bateria compacta..." % res["load_s"])
        try:
            res.update(_medida_compacta(args, cfg))
        except Exception as e:
            res["error"] = "%s: %s" % (type(e).__name__, e)
        return res
    finally:
        parar(proc)
        logf.close()
        try:
            with open(ruta_log, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read()
        except Exception:
            txt = ""
        acc = aceptacion_de_log(txt)
        res["acceptance"] = tasa_media(acc)
        res["accept_eventos"] = acc["eventos"]
        res["log_muestras"] = acc["muestras"][:6]
        if res.get("error"):
            res["log_cola"] = "\n".join(txt.splitlines()[-12:])


def _veredicto_cfg(base, r):
    if r.get("error"):
        return "FALLO: " + str(r["error"])[:46]
    if r["id"] == "T2-0":
        return "ancla"
    if r.get("garbage_hits"):
        return "NO adoptar: corrupcion #23577"
    if base is None or base.get("error"):
        return "sin ancla valida en esta corrida"
    acc = r.get("acceptance")
    dd = None
    if r.get("decode_ts_256") and base.get("decode_ts_256"):
        dd = r["decode_ts_256"] / base["decode_ts_256"] - 1
    if acc is None:
        return "acc N/D: revisar el log (no se inventa)"
    if acc >= 0.70 and dd is not None and dd > 0:
        return "GO: acc>=70% y decode %+.1f%%" % (dd * 100)
    if acc >= 0.70:
        return "CUELLO DE COMPUTO: acc alta pero decode no mejora -> MTP " \
               "cerrado (EAGLE-3 hereda el veredicto)"
    if acc < 0.50:
        return "acc<50%: probar p-min 0.85 (T2-E) una vez"
    return "MARGINAL (acc 50-70%): decide por coste por turno"


def _imprimir_tabla(cabs, filas):
    def lim(s):
        return re.sub(r"\x1b\[[0-9;]*m", "", str(s))
    ws = [max(len(lim(c)), max((len(lim(f[i])) for f in filas), default=0))
          for i, c in enumerate(cabs)]
    print("  " + "  ".join(lim(c).ljust(w) for c, w in zip(cabs, ws)))
    print(gray("  " + "-" * (sum(ws) + 2 * len(ws) - 2)))
    for f in filas:
        print("  " + "  ".join(lim(x).ljust(w) for x, w in zip(f, ws)))


def run_protocolo(args):
    url = "http://%s:%d/health" % (args.host, args.port)
    est, det, _ = salud(url, timeout=3)
    if est == "ok":
        if not args.si:
            print(red("[ABORTO] ya hay un server vivo en %s" % url))
            print("  medir con OTRO server vivo falsea todo (guardarrail del "
                  "barrido-25).")
            print("  Cierra ese server y vuelve; o pasa --si para que lo cierre yo.")
            return 2
        print(yellow("[i] server vivo detectado y --si: lo cierro primero..."))
        matar_server()
    dir_logs = args.log_dir or "mtp-logs"
    os.makedirs(dir_logs, exist_ok=True)
    ids = [x.strip().upper() for x in args.configs.split(",")] if args.configs else []
    cfgs = [c for c in CONFIGS_T2 if (not ids or c["id"] in ids)]
    if args.quick:
        pref = ("T2-0", "T2-A", "T2-B")
        filtradas = [c for c in cfgs if c["id"] in pref]
        cfgs = filtradas or cfgs[:2]
    if not cfgs:
        print(red("ninguna config valida tras los filtros (revisa --configs)"))
        return 2
    print(bold("=" * 76))
    print(bold("  MTP-TESTER v1.0 - PROTOCOLO T2 - Qwen3.6-35B-A3B APEX-I-MINI"))
    print(bold("  ancla launcher v2.1 + una variable spec por config"))
    print(bold("=" * 76))
    kv("server", args.server)
    kv("modelo", args.model)
    kv("configs", " -> ".join(c["id"] for c in cfgs))
    kv("duracion", "~4-5 min por config (+carga) con pausa termica entre ellas")
    resultados = []
    for i, cfg in enumerate(cfgs):
        print("")
        print(bold("=== %s - %s (%d/%d) ===" % (cfg["id"], cfg["nombre"],
                                                i + 1, len(cfgs))))
        print(gray("    hipotesis: " + cfg["hipotesis"]))
        res = medir_config_protocolo(args, cfg, dir_logs)
        resultados.append(res)
        _csv_append(args, res)
        if res.get("error"):
            print(red("    ERROR: %s" % res["error"]))
            for ln in (res.get("log_cola") or "").splitlines()[-6:]:
                print(red("      | " + ln))
        else:
            print("    carga %s s | prefill %s tok/s | decode %s t/s | TPOT %s ms"
                  % (res.get("load_s"), res.get("prefill_ts_512"),
                     res.get("decode_ts_256"), res.get("tpot_ms")))
            acc = res.get("acceptance")
            print("    acceptance %s (eventos %s) | VRAM %s MiB | basura %s | "
                  "sanity %s | top1 %s"
                  % (("%.1f%%" % (acc * 100)) if acc is not None else "N/D",
                     res.get("accept_eventos"), res.get("vram_mib"),
                     res.get("garbage_hits"), res.get("sanity"),
                     res.get("top1_conf")))
            for m in (res.get("log_muestras") or [])[:4]:
                print(gray("      log | " + m))
        # T2-E condicional del criterio pre-registrado
        if cfg["id"] == "T2-B" and not ids and not args.quick:
            accb = res.get("acceptance")
            if accb is not None and accb < 0.50 and \
                    not any(c["id"] == "T2-E" for c in cfgs):
                print(yellow("    [i] acc<50% en T2-B -> criterio pre-registrado: "
                             "lanzo T2-E (p-min 0.85)"))
                cfgs.append(T2_E)
        if i < len(cfgs) - 1:
            print(gray("    pausa termica %d s..." % args.pausa))
            time.sleep(max(0, args.pausa))
    base = next((r for r in resultados if r["id"] == "T2-0" and not r.get("error")),
                None)
    print("")
    print(bold("=== COMPARACION T2 (base = T2-0 ancla) ==="))
    cabs = ["cfg", "load_s", "prefill", "decode", "d%", "acc", "coste/turno",
            "top1", "basura", "sanity", "veredicto"]
    filas = []
    for r in resultados:
        if r.get("error"):
            filas.append([r["id"], "-", "-", "-", "-", "-", "-", "-", "-", "-",
                          _veredicto_cfg(base, r)])
            continue
        d = ""
        if base and r["id"] != "T2-0" and r.get("decode_ts_256") and \
                base.get("decode_ts_256"):
            d = "%+.1f%%" % ((r["decode_ts_256"] / base["decode_ts_256"] - 1) * 100)
        acc = r.get("acceptance")
        filas.append([r["id"], r.get("load_s"), r.get("prefill_ts_512"),
                      r.get("decode_ts_256"), d,
                      ("%.0f%%" % (acc * 100)) if acc is not None else "N/D",
                      r.get("coste_turno_ms"), r.get("top1_conf"),
                      r.get("garbage_hits"), r.get("sanity"),
                      _veredicto_cfg(base, r)])
    _imprimir_tabla(cabs, filas)
    # sugerencia de FLAGS_GANADORAS (flujo del launcher)
    gana = None
    for r in resultados:
        if r.get("error") or r.get("garbage_hits"):
            continue
        acc = r.get("acceptance")
        if r["id"] != "T2-0" and acc is not None and acc >= 0.50 and base:
            if r.get("coste_turno_ms") and base.get("coste_turno_ms") and \
                    r["coste_turno_ms"] < base["coste_turno_ms"]:
                if gana is None or r["coste_turno_ms"] < gana["coste_turno_ms"]:
                    gana = r
    print("")
    if gana:
        cfg_g = next(c for c in CONFIGS_T2 + [T2_E] if c["id"] == gana["id"])
        print(green("FLAGS_GANADORAS = %s   # %s (%s): acc %s, coste/turno %s ms "
                    "vs ancla %s ms" % (
                        json.dumps(cfg_g["flags"]), gana["id"], gana["nombre"],
                        ("%.0f%%" % (gana["acceptance"] * 100))
                        if gana.get("acceptance") is not None else "N/D",
                        gana.get("coste_turno_ms"), base.get("coste_turno_ms"))))
        print("     -> pegala en abrir-qwen-apex.py y VALIDA CHATEANDO "
              "(la calidad se gatea con uso real, no con este tester).")
    else:
        print(yellow("Ninguna config spec gano por coste total: MTP queda NO "
                     "adoptado por ahora."))
        if base and base.get("decode_ts_256"):
            print(gray("    ancla medida: %s t/s (T2-0)" % base["decode_ts_256"]))
    doc = {
        "meta": {
            "modo": "protocolo", "fecha": datetime.now().isoformat(),
            "server": args.server, "modelo": args.model,
            "flags": "ancla launcher v2.1 + FLAGS_GANADORAS + flags spec por config",
            "quick": bool(args.quick), "configs": [c["id"] for c in cfgs],
        },
        "configs_t2": {c["id"]: {"flags": c["flags"], "hipotesis": c["hipotesis"]}
                       for c in CONFIGS_T2 + [T2_E]},
        "tests": {"config-%s" % r["id"]: r for r in resultados},
        "summary": {
            "modo": "protocolo", "base": "T2-0",
            "configs": resultados,
            "ganador": gana["id"] if gana else None,
        },
        "veredicto": [_veredicto_cfg(base, r) for r in resultados],
    }
    jp, mp = guardar_informes(args, doc, "informe-mtp-T2")
    print("")
    print(green("[OK] informes:"))
    print("    " + jp)
    print("    " + mp)
    print(gray("    logs por config en: " + os.path.abspath(dir_logs)))
    print(gray("    historial CSV: " + (args.csv or "tester-mtp-historial.csv")))
    return 0


# ============================== COMPARADOR ==================================
_CLAVES_COMPARE = [
    ("decode_ts_256", "decode t/s (256)", "mayor"),
    ("decode_ts_512", "decode t/s (512)", "mayor"),
    ("tpot_ms_256", "TPOT ms", "menor"),
    ("prefill_ts_max", "prefill t/s (max)", "mayor"),
    ("prefill_ts_512", "prefill t/s (512)", "mayor"),
    ("ttft_frio_ms", "TTFT frio ms", "menor"),
    ("estabilidad_ts", "t/s estable medio", "mayor"),
    ("top1_conf", "confianza top-1", "mayor"),
    ("acceptance", "acceptance draft", "mayor"),
    ("coste_turno_ms", "coste/turno ms [D]", "menor"),
    ("garbage_hits", "basura (#23577)", "menor"),
    ("vram_mib", "VRAM MiB", "info"),
]


def _compare_adjunto(A, B, pa, pb):
    sa = A.get("summary") or {}
    sb = B.get("summary") or {}
    filas = []
    mejoras = 0
    empeoras = 0
    for k, lab, dirn in _CLAVES_COMPARE:
        a = sa.get(k)
        b = sb.get(k)
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            filas.append([lab, a if a is not None else "N/D",
                          b if b is not None else "N/D", "-", "-"])
            continue
        delta = ((b / a - 1) * 100) if a else 0.0
        if dirn == "info" or abs(delta) < 1.0:
            juan = "="
        elif (delta > 0) == (dirn == "mayor"):
            juan = "MEJORA"
            mejoras += 1
        else:
            juan = "EMPEORA"
            empeoras += 1
        filas.append([lab, round(a, 3), round(b, 3), "%+.1f%%" % delta, juan])
    _imprimir_tabla(["metrica", "A", "B", "delta", "veredicto"], filas)
    print("")
    print("  A = %s   B = %s" % (pa, pb))
    print("  balance: %d mejoras / %d empeoras (umbral 1%%)" % (mejoras, empeoras))
    d256 = None
    if isinstance(sa.get("decode_ts_256"), (int, float)) and \
            isinstance(sb.get("decode_ts_256"), (int, float)) and sa["decode_ts_256"]:
        d256 = (sb["decode_ts_256"] / sa["decode_ts_256"] - 1) * 100
    if d256 is not None:
        print("  decode 256: %+.1f%% con B  |  calidad (top-1): %s" % (
            d256, "ver fila arriba"))
        if d256 > 5 and sb.get("garbage_hits") in (0, None) and \
                sb.get("determinista") is not False:
            print(green("  VEREDICTO: B gana por decode sin señales de corrupcion"))
        elif d256 < -5:
            print(red("  VEREDICTO: B pierde por decode"))


def _compare_protocolo(A, B):
    def mapa(doc):
        cfgs = ((doc.get("summary") or {}).get("configs")) or []
        return dict((c.get("id"), c) for c in cfgs)
    ma, mb = mapa(A), mapa(B)
    ids = [i for i in ["T2-0", "T2-A", "T2-B", "T2-C", "T2-D", "T2-E"]
           if i in ma or i in mb]
    filas = []
    for i in ids:
        a, b = ma.get(i) or {}, mb.get(i) or {}
        def s(d, k):
            v = d.get(k)
            return round(v, 2) if isinstance(v, (int, float)) else (v if v else "N/D")
        filas.append([i, s(a, "decode_ts_256"), s(b, "decode_ts_256"),
                      s(a, "acceptance"), s(b, "acceptance"),
                      s(a, "coste_turno_ms"), s(b, "coste_turno_ms"),
                      s(a, "garbage_hits"), s(b, "garbage_hits")])
    _imprimir_tabla(["cfg", "decode A", "decode B", "acc A", "acc B",
                     "coste A", "coste B", "basura A", "basura B"], filas)
    print("")
    print("  Reproducibilidad T2: compara cada config entre las dos corridas;")
    print("  deltas >5% en decode o acceptance indican ruido ambiental "
          "(cierra apps, revisa termica) antes de creer cualquier verdicto.")


def cmd_compare(args):
    pa, pb = args.compare
    try:
        with open(pa, encoding="utf-8") as f:
            A = json.load(f)
        with open(pb, encoding="utf-8") as f:
            B = json.load(f)
    except Exception as e:
        print(red("no pude leer los informes: %s" % e))
        return 2
    ma = (A.get("meta") or {}).get("modo", "?")
    mb = (B.get("meta") or {}).get("modo", "?")
    print(bold("MTP-TESTER - COMPARADOR"))
    print("  A = %s (%s)" % (pa, ma))
    print("  B = %s (%s)" % (pb, mb))
    print("")
    if ma == "protocolo" and mb == "protocolo":
        _compare_protocolo(A, B)
    else:
        _compare_adjunto(A, B, pa, pb)
    return 0


# ================================= MAIN =====================================
EJEMPLOS = """ejemplos:
  python tester-mtp.py                            # suite completa al server :9931
  python tester-mtp.py --quick                    # suite rapida (~3-4 min)
  python tester-mtp.py --log-file server.log      # + acceptance del draft
  python tester-mtp.py --protocolo --si           # protocolo T2 completo
  python tester-mtp.py --protocolo --configs T2-0,T2-A
  python tester-mtp.py --compare A.json B.json    # comparar dos informes
"""


def main():
    global USE_COLOR
    ap = argparse.ArgumentParser(
        description="tester-mtp v1.0 - testeo profesional MTP/draft-mtp para "
                    "llama.cpp (rig Qwen APEX-I-MINI, protocolo T2)",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EJEMPLOS)
    ap.add_argument("--host", default=HOST_DEF)
    ap.add_argument("--port", type=int, default=PORT_DEF)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--timeout", type=int, default=900,
                    help="timeout por peticion (s)")
    ap.add_argument("--load-timeout", type=int, default=900,
                    help="timeout de carga del server en modo protocolo (s)")
    ap.add_argument("--quick", action="store_true",
                    help="suite reducida (~3-4 min)")
    ap.add_argument("--out", default="informe-mtp",
                    help="prefijo de los informes .json/.md")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--log-file", default=None,
                    help="log del server (stdout+stderr) para leer acceptance")
    ap.add_argument("--protocolo", action="store_true",
                    help="protocolo T2: lanza el server con cada config y compara")
    ap.add_argument("--si", action="store_true",
                    help="en protocolo: cierra un server vivo en el puerto")
    ap.add_argument("--server", default=RUTA_SERVER_DEF,
                    help="ruta del llama-server.exe")
    ap.add_argument("--model", default=RUTA_MODELO_DEF, help="ruta del GGUF")
    ap.add_argument("--configs", default=None,
                    help='protocolo: lista T2 separada por comas, p.ej. "T2-0,T2-A"')
    ap.add_argument("--log-dir", default="mtp-logs",
                    help="carpeta de logs del server en modo protocolo")
    ap.add_argument("--csv", default="tester-mtp-historial.csv",
                    help="CSV de historial del protocolo (append)")
    ap.add_argument("--pausa", type=int, default=20,
                    help="pausa termica entre configs del protocolo (s)")
    ap.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"),
                    help="comparar dos informes .json y salir")
    args = ap.parse_args()
    USE_COLOR = (not args.no_color) and sys.stdout.isatty() \
        and not os.environ.get("NO_COLOR")
    try:
        if args.compare:
            return cmd_compare(args)
        if args.protocolo:
            return run_protocolo(args)
        return run_adjunto(args)
    except KeyboardInterrupt:
        print("\n[interrupt] saliendo limpio...")
        return 130


if __name__ == "__main__":
    sys.exit(main())



