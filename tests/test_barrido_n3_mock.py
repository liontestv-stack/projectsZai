#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de barrido-n3-eficiencia.py v1.0 con server falso (sin GPU, sin
Windows). Mismo patron de la casa (test_barrido_mock / test_diagnostico_mock):
el fake llama-server es un script python que el PROPIO barrido lanza con
Popen; sirve /health y /completion (stream y no-stream) en su --port y
escribe en SU stdout las lineas de log que el barrido usa como certificado
(restored context checkpoint / forcing full prompt re-processing / warning
#24055 / system_info USE_GRAPHS REPACK / listening on / loading model).

v1.2 anade: hotfix de campo del dossier_pc (literal partido en dos
statements crasheaba con 2 palos de RAM, primera corrida real 28-oct) con
datos realistas del rig (2 palos / 1 palo sin MT/s), y auditoria AST
permanente de cadenas de formato en TODOS los scripts (la clase del crash
no vuelve: U22-U24).

v1.3 anade: hotfix de campo 2 (la 1a corrida COMPLETA del rig 28-oct: 11
de 13 configs murieron en ~2.5 s con "fit abortado: VRAM insuficiente";
solo sobrevivieron las 2 con -ncmoe 37). Causa: la base salio sin la
colocacion -cmoe de la receta diaria y el comando pedia los 14.27 GB del
modelo EN la GPU de 4 GB. Vacuna: (a) el FAKE ahora SE NIEGA a arrancar
sin colocacion (-cmoe/-ncmoe) = reproduce el rig de 4 GB; (b) U25-U27
certifican la receta diaria completa en el ancla y la colocacion por
config; (c) E35: ancla muerta = FATAL inmediato con el forense del log en
la nota del CSV; (d) E36: el resume re-mide solas las filas muertas (la
recuperacion del campo sin tocar nada a mano).

Comportamiento del fake (reproduce los DOS mundos del hibrido #21831):
  - SI lleva --cache-reuse  -> linea 'restored context checkpoint' por POST
                               y TTFT PLANO (el cache trabaja)
  - SI lleva --no-cache-prompt -> sin lineas de cache y TTFT CRECE (todo
                               turno re-procesa: control by-design)
  - SI NO lleva ninguna     -> linea 'forcing full prompt re-processing'
                               (el comportamiento ACTUAL del hibrido) y
                               TTFT CRECE

Verifica: 13 filas en CSV todas validas, decode constante (deltas ~0 ->
EMPATA), certificados de cache por config (SANO/NO-APLICA), TTFT veredictos
(PLANO/CRECE), sanity 3/3, repro TTFT y probe agregado en el JSON, informe
md con bookend estable / joya certificada / combo seguro / control NOCACHE,
resume (2a corrida no arranca nada), --solo / --quick, --sin-ttft, warning
#24055 -> NO-SOPORTADO con RUTA 0 en el informe, guardarrail anti-server-
vivo, y auditoria de flags FATAL con dump podrido / VERDE con el dump real.
"""
import builtins
import importlib.util
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica",
                                      "scripts", "barrido-n3-eficiencia.py"))
DUMP_REAL = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica",
                                         "configs", "llama-flags-nuevo.txt"))
DIR = tempfile.mkdtemp(prefix="barrido_n3_test_")
ok_fallos = []


def check(nombre, cond, detalle=""):
    estado = "OK  " if cond else "FALLO"
    print("[%s] %s %s" % (estado, nombre, detalle))
    if not cond:
        ok_fallos.append(nombre)


def _libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


# ------------------------- el fake llama-server ------------------------------
FAKE_PLANTILLA = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Fake de llama-server para el E2E de barrido-n3 (sirve el puerto por --port;
# imprime a STDOUT las lineas de certificado que el barrido grepea).
import json, os, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

args = sys.argv[1:]
port = 9931
if "--port" in args: port = int(args[args.index("--port") + 1])
if "--version" in args:
    print("version: 7000 (b11856)")
    sys.exit(0)
# rama v1.3: SIN colocacion el rig de 4 GB muere en la carga (el modelo de
# 14.27 GB no cabe en la GPU) - la v1.2 de campo murio asi 11 veces.
FAKE_RECHAZA = os.environ.get("FAKE_RECHAZA") == "1"
if FAKE_RECHAZA or ("-cmoe" not in args and "-ncmoe" not in args):
    print("llama_model_load_internal: failed to allocate CUDA0 buffer "
          "(no cabe sin colocacion -cmoe/-ncmoe)", flush=True)
    print("CUDA error: out of memory", flush=True)
    sys.exit(1)
TIENE_REUSE = "--cache-reuse" in args
NOCACHE = "--no-cache-prompt" in args
WARN = os.environ.get("FAKE_REUSE_WARN") == "1"
MODELO = args[args.index("-m") + 1] if "-m" in args else "modelo.gguf"
STREAM_N = {"n": 0}

print("llama_model_load: loading model from %s" % MODELO, flush=True)
if WARN:
    print("srv load_model: cache_reuse is not supported by this context, "
          "it will be disabled", flush=True)
print("system_info: n_threads = 4 | AVX = 1 | USE_GRAPHS = 1 | REPACK = 1",
      flush=True)
print("main: listening on 127.0.0.1:%d" % port, flush=True)

def linea_cache():
    if TIENE_REUSE:
        print("srv update_slots: restored context checkpoint (37 tokens)",
              flush=True)
    elif not NOCACHE:
        print("srv update_slots: forcing full prompt re-processing due to "
              "lack of cache data (likely due to SWA or hybrid/recurrent "
              "memory)", flush=True)

def contenido(body):
    p = (body.get("prompt") or "").lower()
    if "17 x 23" in p: return "391"
    if "don quijote" in p: return "Cervantes"
    if "planeta rojo" in p: return "Marte"
    return "Entendido."

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _cab(self, code, tipo):
        self.send_response(code)
        self.send_header("Content-Type", tipo)
        self.end_headers()
    def do_GET(self):
        if self.path == "/health":
            self._cab(200, "application/json")
            self.wfile.write(b'{"status":"ok"}')
        else:
            self._cab(404, "application/json")
            self.wfile.write(b'{"e":1}')
    def do_POST(self):
        ln = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(ln) or b"{}")
        except Exception:
            body = {}
        linea_cache()
        if body.get("stream"):
            STREAM_N["n"] += 1
            if TIENE_REUSE:
                ttft = 0.05
            else:
                ttft = 0.05 + 0.12 * STREAM_N["n"]
            time.sleep(max(ttft, 0.0))
            self._cab(200, "text/event-stream")
            for i in range(int(body.get("n_predict") or 24)):
                ch = {"content": "a", "stop": False}
                self.wfile.write(("data: %s\\n\\n"
                                  % json.dumps(ch)).encode())
                self.wfile.flush()
                time.sleep(0.001)
            fin = {"content": "", "stop": True}
            self.wfile.write(("data: %s\\n\\n" % json.dumps(fin)).encode())
            self.wfile.write(b"data: [DONE]\\n\\n")
            self.wfile.flush()
        else:
            np_ = int(body.get("n_predict") or 0)
            obj = {"content": contenido(body),
                   "timings": {"predicted_per_second": 21.53,
                               "prompt_per_second": 57.0,
                               "predicted_n": np_}}
            b = json.dumps(obj).encode()
            self._cab(200, "application/json")
            self.wfile.write(b)

ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
'''


def _montar_escenario(nombre, env_extra=None):
    """Crea dir de logs + modelo falso + fake server ejecutable; devuelve
    dict de rutas/args comunes."""
    d = os.path.join(DIR, nombre)
    os.makedirs(d, exist_ok=True)
    fake = os.path.join(d, "fake-server.py")
    with open(fake, "w") as f:
        f.write(FAKE_PLANTILLA)
    os.chmod(fake, 0o755)
    modelo = os.path.join(d, "modelo-falso.gguf")
    with open(modelo, "wb") as f:
        f.write(b"GGUF-falso")
    logs = os.path.join(d, "logs")
    return {"dir": d, "fake": fake, "modelo": modelo, "logs": logs,
            "env": env_extra or {}}


def _correr_barrido(esc, puerto, extra_args=()):
    env = dict(os.environ)
    env["BARRIDO_PAUSA_S"] = "0"
    env.update(esc["env"])
    cmd = [sys.executable, SCRIPT, "--server", esc["fake"],
           "--modelo", esc["modelo"], "--logs", esc["logs"],
           "--puerto", str(puerto), "--sin-nvidia"] + list(extra_args)
    p = subprocess.run(cmd, capture_output=True, timeout=600, env=env)
    return p


def _leer_csv(esc):
    import csv as _csv
    ruta = os.path.join(esc["logs"], "faseN3-resultados.csv")
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(_csv.DictReader(f))


def _leer_informe(esc):
    ruta = os.path.join(esc["logs"], "faseN3-INFORME.md")
    return open(ruta, encoding="utf-8").read()


# =========================== 1. unitarios puros ==============================
print("--- UNITARIOS ---")
spec = importlib.util.spec_from_file_location("b3", SCRIPT)
b3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b3)

cfgs = b3.construir_configs()
check("U01: 13 configs con ids unicos 1..13",
      len(cfgs) == 13 and [c["id"] for c in cfgs] == list(range(1, 14)))
check("U02: ancla y bookend llevan SOLO su colocacion (-cmoe = receta diaria)",
      cfgs[0]["flags"] == ["-cmoe"] and cfgs[12]["flags"] == ["-cmoe"])
check("U03: REUSE lleva --cache-reuse 256 y SHIFT lleva shift+reuse (+colocacion)",
      cfgs[4]["flags"] == ["--cache-reuse", "256", "-cmoe"]
      and cfgs[5]["flags"] == ["--context-shift", "--cache-reuse", "256",
                               "-cmoe"])
check("U04: NCM37C4 verbatim del barrido-30 y SIN -cmoe general (leccion: "
      "el general anula al -ncmoe)",
      cfgs[7]["flags"] == ["-ncmoe", "37", "-c", "4096",
                           "-ctk", "q4_0", "-ctv", "q4_0"]
      and "-cmoe" not in cfgs[7]["flags"])
check("U05: COMBO-T = NCM37C4 + cache completa",
      all(t in cfgs[9]["flags"] for t in
          ("-ncmoe", "--cache-ram", "-ctxcp", "-cms", "--cache-reuse",
           "--context-shift")))
check("U06: TTFT_IDS = configs con cache + ancla + nocache",
      b3.TTFT_IDS == {1, 5, 6, 9, 10, 11, 12})
check("U07: base = receta diaria (UB1K) + -lv 4",
      b3.BASE_FLAGS_FIJAS[b3.BASE_FLAGS_FIJAS.index("-ub") + 1] == "1024"
      and "-lv" in b3.BASE_FLAGS_FIJAS)
check("U08: cero prohibidas en las 13 configs",
      not any(t in (b3.PROHIBIDAS_EXACTAS) for c in cfgs for t in c["flags"]))

probs_real = b3.auditar_flags(DUMP_REAL, cfgs,
                              ["-m", "M"] + list(b3.BASE_FLAGS_FIJAS))
check("U09: auditoria contra el dump REAL del repo = VERDE",
      probs_real == [], str(probs_real)[:200])

dump_podrido = os.path.join(DIR, "dump-podrido.txt")
open(dump_podrido, "w", encoding="utf-8").write("help: no hay nada aqui")
probs_podrido = b3.auditar_flags(dump_podrido, cfgs[:1], [])
check("U10: auditoria con dump podrido = FALLOS (no arranca)",
      len(probs_podrido) > 0)

check("U11: criterio_cache 5 estados",
      b3.criterio_cache(True, 1, 0, 0) == "NO-SOPORTADO"
      and b3.criterio_cache(True, 0, 3, 0) == "SANO"
      and b3.criterio_cache(True, 0, 0, 2) == "ROTO"
      and b3.criterio_cache(True, 0, 1, 1) == "MIXTO"
      and b3.criterio_cache(False, 0, 0, 0) == "NO-APLICA"
      and b3.criterio_cache(True, 0, 0, 0) == "SIN-DATOS")
check("U12: criterio_ttft PLANO/GRIS/CRECE/N/D",
      b3.criterio_ttft(1.0, 1.4) == "PLANO"
      and b3.criterio_ttft(1.0, 1.7) == "GRIS"
      and b3.criterio_ttft(1.0, 2.1) == "CRECE"
      and b3.criterio_ttft(None, 2.1) == "N/D")
check("U13: _dif_veredicto con ruido +/-0.5",
      b3._dif_veredicto(22.1, 21.53)[0] == "GANA"
      and b3._dif_veredicto(21.4, 21.53)[0] == "EMPATA"
      and b3._dif_veredicto(20.5, 21.53)[0] == "PIERDE")

# ---- prevuelo v1.1: parser GGUF sintetico + sha256 + nivel ------------------
import hashlib as _hl
import struct as _st


def _gguf_sintetico():
    """Construye bytes de una cabecera GGUF valida: 2 kvs escalares, 1 string
    grande que se salta, 1 array de strings (tokenizer) y 1 kv nextn."""
    def cad(s):
        b = s.encode()
        return _st.pack("<Q", len(b)) + b
    def kv_str(k, v):
        return cad(k) + _st.pack("<I", 8) + cad(v)
    def kv_u32(k, v):
        return cad(k) + _st.pack("<I", 4) + _st.pack("<I", v)
    cuerpo = b""
    cuerpo += kv_str("general.architecture", "qwen35moe")
    cuerpo += kv_str("general.name", "APEX-I-MINI")
    cuerpo += kv_u32("qwen35moe.expert_count", 256)
    cuerpo += kv_u32("qwen35moe.expert_used_count", 8)
    cuerpo += kv_u32("qwen35moe.context_length", 163840)
    cuerpo += kv_u32("qwen35moe.block_count", 56)
    cuerpo += kv_str("tokenizer.chat_template", "X" * 70000)   # > 64 KiB: salta
    arr = _st.pack("<I", 8) + _st.pack("<Q", 3)               # 3 strings
    for tok in ("hola", "mundo", "gguf"):
        arr += _st.pack("<Q", len(tok)) + tok.encode()
    cuerpo += cad("tokenizer.ggml.tokens") + _st.pack("<I", 9) + arr
    cuerpo += kv_u32("qwen35moe.nextn.backend", 1)             # MTP preserved
    return (b"GGUF" + _st.pack("<I", 3) + _st.pack("<Q", 0)
            + _st.pack("<Q", 9) + cuerpo)


GGUF_BIN = _gguf_sintetico()
gguf_ruta = os.path.join(DIR, "sintetico.gguf")
open(gguf_ruta, "wb").write(GGUF_BIN)
meta_gguf, err_gguf = b3.gguf_metadatos(gguf_ruta)
check("U14: parser GGUF sintetico lee kvs y salta arrays",
      err_gguf is None and meta_gguf.get("general.architecture") == "qwen35moe"
      and meta_gguf.get("general.name") == "APEX-I-MINI"
      and meta_gguf.get("qwen35moe.expert_count") == 256
      and meta_gguf.get("qwen35moe.expert_used_count") == 8
      and meta_gguf.get("qwen35moe.context_length") == 163840
      and meta_gguf.get("qwen35moe.block_count") == 56
      and meta_gguf.get("qwen35moe.nextn.backend") == 1
      and "gguf_version" in meta_gguf,
      "err=%s meta=%s" % (err_gguf, sorted(meta_gguf or {})))
check("U15: chat_template grande NO contamina los metadatos",
      meta_gguf is not None
      and not any("chat_template" in k for k in meta_gguf))
no_gguf = os.path.join(DIR, "no-gguf.bin")
open(no_gguf, "wb").write(b"esto no es un gguf")
meta2, err2 = b3.gguf_metadatos(no_gguf)
check("U16: archivo no-GGUF -> error limpio, nunca fatal",
      meta2 is None and err2 and "magic" in err2, str(err2))
sha_tst = os.path.join(DIR, "sha.bin")
open(sha_tst, "wb").write(b"1234567890" * 1000)
check("U17: sha256_archivo coincide con hashlib",
      b3.sha256_archivo(sha_tst) == _hl.sha256(b"1234567890" * 1000).hexdigest())
niv = b3.dossier_nivel(b3.construir_configs())
check("U18: dossier_nivel tiene campana/refs/muertos/pendientes/protocolo/dia",
      "N1 -> N3 -> N2 -> N4" in niv["campana"] and len(niv["refs"]) == 8
      and len(niv["muertos"]) == 6 and len(niv["pendientes"]) == 3
      and len(niv["protocolo"]) == 6 and "RAM al 97%" in niv["dia"]
      and len(niv["configs_hoy"]) == 13)
ps_r = b3._ps_json("Get-CimInstance Win32_OperatingSystem")
check("U19: _ps_json nunca fatal (None fuera de Windows o lista)",
      ps_r is None or isinstance(ps_r, list))
pc_d = b3.dossier_pc(con_nvidia=False)
mod_d = b3.dossier_modelo(gguf_ruta, len(GGUF_BIN), "version: 7000 (b11856)",
                          con_sha=True)
check("U20: dossier_modelo certifica bytes+sha+gguf+build",
      mod_d["bytes"] == len(GGUF_BIN) and not mod_d["bytes_ok"]
      and mod_d["sha256"] == _hl.sha256(GGUF_BIN).hexdigest()
      and mod_d["build_ok"] is True
      and mod_d.get("gguf", {}).get("qwen35moe.expert_used_count") == 8)
ctx_f = {"ruta_server": "fake", "base_flags_str": "-m M"}
md_p = b3.md_prevuelo(pc_d, mod_d, niv, ctx_f, [])
md_txt = "\n".join(md_p)
check("U21: md_prevuelo pinta las 5 secciones con N/D graceful",
      "PREVUELO COMPLETO" in md_txt and "### 0.1" in md_txt
      and "### 0.2" in md_txt and "### 0.3" in md_txt
      and "### 0.4" in md_txt and "### 0.5" in md_txt
      and "no disponible" in md_txt
      and "FABRICA" in md_txt)

# ---- v1.2: hotfix de campo (crash del dossier con 2 palos) + auditoria AST -
def _ps_falsa_ram(n_palos, con_vel=3200):
    """_ps_json falsa con datos realistas del rig (la rama Windows que el
    mock original no podia ejecutar en Linux: _ps_json real da None)."""
    def _f(q, timeout=60):
        if "Win32_OperatingSystem" in q:
            return [{"Caption": "Microsoft Windows 11 Pro",
                     "Version": "10.0.26100", "BuildNumber": "26100",
                     "OSArchitecture": "64 bits",
                     "LastBootUpTime": "20261028080000.000000+060"}]
        if "Win32_Processor" in q:
            return [{"Name": "CPU del rig", "NumberOfCores": 8,
                     "NumberOfLogicalProcessors": 16,
                     "MaxClockSpeed": 3200}]
        if "Win32_PhysicalMemory" in q:
            filas = []
            for _ in range(n_palos):
                filas.append({"Capacity": 8589934592, "Speed": con_vel,
                              "ConfiguredClockSpeed": con_vel})
            return filas
        if "PageFileUsage" in q:
            return [{"Name": "D:\\pagefile.sys", "AllocatedBaseSize": 5120,
                     "CurrentUsage": 1200, "PeakUsage": 4300}]
        if "LogicalDisk" in q:
            return [{"DeviceID": "C:", "Size": 476000000000,
                     "FreeSpace": 100000000000}]
        if "Get-Process" in q:
            return [{"Name": "llama-server", "MB": 14600},
                    {"Name": "chrome", "MB": 2100}]
        return None
    return _f

orig_ps = b3._ps_json
try:
    b3._ps_json = _ps_falsa_ram(2)          # EL RIG REAL: 2 palos de 8 GB
    pc2 = b3.dossier_pc(con_nvidia=False)
finally:
    b3._ps_json = orig_ps
check("U22: dossier_pc con 2 palos (rig real) -> ram_hardware sin crash",
      "2 modulos, 16.0 GB en total a 3200 MT/s" in (pc2.get("ram_hardware") or "")
      and "(dual channel si son 2)" in (pc2.get("ram_hardware") or ""),
      str(pc2.get("ram_hardware")))
try:
    b3._ps_json = _ps_falsa_ram(1, con_vel=None)   # 1 palo sin velocidad
    pc3 = b3.dossier_pc(con_nvidia=False)
finally:
    b3._ps_json = orig_ps
check("U23: dossier_pc con 1 palo sin MT/s -> '?' y sin crash",
      "1 modulos, 8.0 GB en total a ? MT/s" in (pc3.get("ram_hardware") or ""),
      str(pc3.get("ram_hardware")))

# ---- v1.3: certificado de receta + colocacion (hotfix de campo 2) ----------
full_ancla = list(b3.BASE_FLAGS_FIJAS) + list(cfgs[0]["flags"])
_faltan_vacio = b3.verificar_receta(full_ancla)
_faltan_roto = b3.verificar_receta(["-ngl", "99"])
check("U25: certificado de receta VERDE en el ancla (base + colocacion)",
      _faltan_vacio == [] and len(_faltan_roto) == 11
      and "-cmoe" in _faltan_roto and "-c 16384" in _faltan_roto
      and "-lm none" in _faltan_roto,
      "ancla=%s roto=%s" % (_faltan_vacio, _faltan_roto[:4]))
base_mala = [t for t in full_ancla if t != "-cmoe"]   # LA v1.2 DE CAMPO
check("U26: receta sin -cmoe -> el certificado la caza (la leccion del campo)",
      b3.verificar_receta(base_mala) == ["-cmoe"])
check("U27: colocacion por config en 13/13; una config sin ella se nombra",
      b3.verificar_colocacion(cfgs, list(b3.BASE_FLAGS_FIJAS)) == []
      and b3.verificar_colocacion(
          [{"id": 9, "nombre": "X", "flags": ["-c", "4096"]}],
          ["-ngl", "99"]) == ["#9 X"])

def _contar_ph(s):
    """Numero de placeholders % en una cadena de formato (%% no cuenta;
    un * en anchura/precision cuenta como arg extra)."""
    import re as _re
    n = 0
    for m2 in _re.finditer(r"%(?:\((?:[^)]*)\))?[-#0 +]*(?:\*|\d+)?"
                           r"(?:\.(?:\*|\d+))?[hlL]?([diouxXeEfFgGcrsa%])",
                           s):
        if m2.group(1) == "%":
            continue
        n += 1 + m2.group(0).count("*")
    return n

def _audit_formatos(ruta):
    """La clase del crash de campo, convertida en detector: (1) statement
    "literal" % (...) cuyo resultado se tira (literal partido en 2
    statements); (2) literal suelto como statement (no docstring); (3)
    aridad placeholders vs args."""
    import ast as _ast
    hall = []
    with open(ruta, encoding="utf-8") as f:
        arbol = _ast.parse(f.read(), ruta)
    docs = set()
    for nd in _ast.walk(arbol):
        if isinstance(nd, (_ast.Module, _ast.FunctionDef, _ast.ClassDef)):
            c = getattr(nd, "body", [])
            if (c and isinstance(c[0], _ast.Expr)
                    and isinstance(c[0].value, _ast.Constant)
                    and isinstance(c[0].value.value, str)):
                docs.add(id(c[0]))
    for nd in _ast.walk(arbol):
        if isinstance(nd, _ast.Expr):
            v = nd.value
            if (isinstance(v, _ast.BinOp) and isinstance(v.op, _ast.Mod)
                    and isinstance(v.left, _ast.Constant)
                    and isinstance(v.left.value, str)):
                hall.append((nd.lineno, "formato orfano (resultado tirado)"))
            elif (id(nd) not in docs and isinstance(v, _ast.Constant)
                  and isinstance(v.value, (str, int, float))):
                hall.append((nd.lineno, "literal suelto como statement"))
        elif (isinstance(nd, _ast.BinOp) and isinstance(nd.op, _ast.Mod)
              and isinstance(nd.left, _ast.Constant)
              and isinstance(nd.left.value, str)):
            fs = nd.left.value
            nf = _contar_ph(fs)
            der = nd.right
            if "%(" in fs:
                if isinstance(der, _ast.Tuple):
                    hall.append((nd.lineno, "mapping %(...)s con tupla"))
                continue
            if isinstance(der, _ast.Tuple):
                if any(isinstance(e, _ast.Starred) for e in der.elts):
                    continue
                na = len(der.elts)
            elif isinstance(der, (_ast.Dict, _ast.Call)):
                continue
            else:
                na = 1
            if nf != na:
                hall.append((nd.lineno, "aridad %d vs %d args: %r"
                             % (nf, na, fs[:60])))
    return hall

import glob as _glob
_hallazgos = []
for _ruta in sorted(_glob.glob(os.path.join(RAIZ, "..", "InformacionCritica",
                                           "scripts", "*.py"))):
    for _ln, _msg in _audit_formatos(_ruta):
        _hallazgos.append("%s:%d %s" % (os.path.basename(_ruta), _ln, _msg))
_fuente = open(SCRIPT, encoding="utf-8").read()
check("U24: auditoria AST de formatos en todos los scripts = 0 hallazgos",
      not _hallazgos
      and "[math]::Round(" in _fuente,
      str(_hallazgos[:3]))

# =========================== 2. E2E corrida completa =========================
print("--- E2E CORRIDA COMPLETA (13 configs) ---")
PUERTO1 = _libre()
S1 = _montar_escenario("e2e-completo")
t0 = time.time()
p1 = _correr_barrido(S1, PUERTO1)
t1 = time.time()
print("  (rc=%s, %.1f s)" % (p1.returncode, t1 - t0))
salida = p1.stdout.decode("utf-8", errors="replace") + \
    p1.stderr.decode("utf-8", errors="replace")
check("E01: corrida completa rc=0", p1.returncode == 0,
      salida[-400:] if p1.returncode != 0 else "")
check("E02: auditoria VERDE en consola", "cero prohibidas" in salida)

filas = _leer_csv(S1)
check("E03: CSV con 13 filas (todas las configs)",
      len(filas) == 13, "filas=%d" % len(filas))
check("E04: todas las filas validas SI",
      all(r["valido"] == "SI" for r in filas),
      "; ".join(r["nota"] for r in filas if r["valido"] != "SI")[:200])
check("E05: decode constante 21.53 (fake) y deltas ~0",
      all(abs(float(r["decode_ts"]) - 21.53) < 1e-6 for r in filas)
      and all(r["delta_vs_ancla_pct"] == "0.0" for r in filas
              if r["id"] != "1"))
por_id = {int(r["id"]): r for r in filas}
check("E06: cache SANO solo en las 5 configs con --cache-reuse",
      all(por_id[i]["cache_estado"] == "SANO" for i in (5, 6, 9, 10, 11))
      and all(por_id[i]["cache_estado"] == "NO-APLICA"
              for i in (1, 2, 3, 4, 7, 8, 12, 13)),
      "; ".join("%s=%s" % (i, por_id[i]["cache_estado"])
                for i in sorted(por_id)))
check("E07: certificados de log contados (restored/forcing)",
      all(int(por_id[i]["cache_restored_n"]) >= 5 for i in (5, 6, 9, 10, 11))
      and int(por_id[1]["cache_forcing_n"]) >= 4
      and int(por_id[12]["cache_forcing_n"]) == 0)
check("E08: TTFT PLANO con reuse y CRECE sin cache (repro #21831)",
      all(por_id[i]["ttft_veredicto"] == "PLANO" for i in (5, 6, 9, 10, 11))
      and por_id[1]["ttft_veredicto"] == "CRECE"
      and por_id[12]["ttft_veredicto"] == "CRECE")
check("E09: configs sin repro no llevan TTFT (ids 2,3,4,7,8,13)",
      all(por_id[i]["ttft_veredicto"] == "" for i in (2, 3, 4, 7, 8, 13)))
check("E10: sanity auto 3/3 en todas",
      all(r["sanity_ok_n"] == "3" and r["sanity_total"] == "3"
          for r in filas))
check("E11: probe agregado presente (agg_ts) en todas",
      all(float(r["agg_ts"]) > 0 for r in filas))
check("E12: RAM sistema registrada (ram_free0/1)",
      all(r["ram_free0_mib"] and r["ram_free1_mib"] for r in filas))
check("E13: system_info certificates (graphs/repack) en todas",
      all(r["graphs_ok"] == "SI" and r["repack_ok"] == "SI" for r in filas))

informe = _leer_informe(S1)
check("E14: informe tiene bookend estable",
      "BOOKEND ESTABLE" in informe, "")
check("E15: informe certifica la joya (REUSE SANO + TTFT PLANO)",
      "LA JOYA CERTIFICADA" in informe)
check("E16: informe promueve el COMBO-R (candidata #1)",
      "candidata #1 a config.txt" in informe)
check("E17: control NOCACHE crece como se esperaba",
      "N3-NOCACHE (control): TTFT CRECE como se esperaba" in informe)
check("E18: informe lleva referencias historicas [M] del barrido-30",
      "21.53" in informe and "22.49" in informe and "21.57" in informe)
check("E19: datos.json con repro turno a turno y agg",
      ("repro_ttft" in json.dumps(
          json.load(open(os.path.join(S1["logs"], "faseN3-datos.json"))))))

# ---- E2E del prevuelo completo (v1.1) ---------------------------------------
check("E28: informe lleva el PREVUELO COMPLETO con las 5 secciones",
      "PREVUELO COMPLETO" in informe and "### 0.1 El PC" in informe
      and "### 0.2 El modelo" in informe and "### 0.3 La receta viva"
      in informe and "### 0.4 El nivel N3" in informe
      and "### 0.5 El dia" in informe)
_sha_en_informe = [l for l in informe.splitlines() if "SHA256:" in l]
check("E29: sha256 del modelo fake en el informe (64 hex)",
      len(_sha_en_informe) == 1
      and len(_sha_en_informe[0].split("`")[1]) == 64,
      _sha_en_informe[:1])
check("E30: cabecera GGUF no-leible queda como nota (fake no es GGUF)",
      "Cabecera GGUF: NO leible" in informe)
check("E31: nivel N3 completo en el informe (refs + muertos + protocolo)",
      "ORO-UB1K (receta diaria" in informe and "Libro de muertos" in informe
      and "Mediana de 3" in informe and "Las 13 configs de hoy" in informe
      and "Ronda 28" in informe)
check("E32: consola anuncia el prevuelo",
      "PREVUELO COMPLETO" in salida)

# =========================== 3. resume =======================================
print("--- RESUME ---")
p2 = _correr_barrido(S1, PUERTO1)
salida2 = p2.stdout.decode("utf-8", errors="replace")
check("E20: resume 2a corrida rc=0 y salta las 13",
      p2.returncode == 0 and salida2.count("ya medida (valida)") == 13,
      "rc=%s saltadas=%d" % (p2.returncode,
                             salida2.count("ya medida (valida)")))

# =========================== 4. --solo / --quick / --sin-ttft ================
print("--- SUBCONJUNTOS ---")
PUERTO3 = _libre()
S3 = _montar_escenario("solo-ram")
p3 = _correr_barrido(S3, PUERTO3, ["--solo", "ram", "--sin-ttft"])
salida3 = p3.stdout.decode("utf-8", errors="replace")
filas3 = _leer_csv(S3)
check("E21: --solo ram = 3 configs (2,3,4) rc=0",
      p3.returncode == 0 and [int(r["id"]) for r in filas3] == [2, 3, 4],
      "rc=%s ids=%s" % (p3.returncode, [r["id"] for r in filas3]))
check("E22: --sin-ttft deja TTFT vacio",
      all(r["ttft_veredicto"] == "" and r["ttft_t2"] == ""
          for r in filas3))

PUERTO4 = _libre()
S4 = _montar_escenario("quick")
p4 = _correr_barrido(S4, PUERTO4, ["--quick"])
filas4 = _leer_csv(S4)
check("E23: --quick = 5 configs criticas (1,5,9,10,13)",
      p4.returncode == 0
      and [int(r["id"]) for r in filas4] == [1, 5, 9, 10, 13],
      "rc=%s ids=%s" % (p4.returncode, [r["id"] for r in filas4]))

# ---- --sin-prevuelo / --sin-sha256 ------------------------------------------
PUERTO6 = _libre()
S6 = _montar_escenario("sin-prevuelo")
p6 = _correr_barrido(S6, PUERTO6, ["--solo", "ram", "--sin-prevuelo",
                                   "--sin-ttft"])
salida6 = p6.stdout.decode("utf-8", errors="replace")
filas6 = _leer_csv(S6)
informe6 = _leer_informe(S6)
check("E33: --sin-prevuelo rc=0, 3 configs, dossier omitido",
      p6.returncode == 0 and [int(r["id"]) for r in filas6] == [2, 3, 4]
      and "dossier omitido" in salida6
      and "PREVUELO COMPLETO" not in informe6
      and "## 0. Pre-vuelo" in informe6,
      "rc=%s" % p6.returncode)
PUERTO6b = _libre()
S6b = _montar_escenario("sin-sha256")
p6b = _correr_barrido(S6b, PUERTO6b, ["--solo", "ram", "--sin-sha256",
                                      "--sin-ttft"])
informe6b = _leer_informe(S6b)
check("E34: --sin-sha256 mantiene el prevuelo pero omite el hash",
      p6b.returncode == 0 and "PREVUELO COMPLETO" in informe6b
      and "omitido (--sin-sha256)" in informe6b)

# =========================== 5. warning #24055 ===============================
print("--- WARNING #24055 (cache no soportada) ---")
PUERTO5 = _libre()
S5 = _montar_escenario("warn24055", env_extra={"FAKE_REUSE_WARN": "1"})
p5 = _correr_barrido(S5, PUERTO5, ["--solo", "cache"])
filas5 = _leer_csv(S5)
informe5 = _leer_informe(S5)
check("E24: warning -> cache NO-SOPORTADO en 5 y 6",
      p5.returncode == 0
      and all(r["cache_estado"] == "NO-SOPORTADO" for r in filas5)
      and all(r["cache_reuse_warn"] == "SI" for r in filas5),
      "; ".join(r["cache_estado"] for r in filas5))
check("E25: informe deriva a RUTA 0 con el motivo",
      "RUTA 0 gana un motivo" in informe5)

# =========================== 6. guardarrails =================================
print("--- GUARDARRAILS ---")
PUERTO7 = _libre()
S7 = _montar_escenario("puerto-ocupado")
proceso_falso = subprocess.Popen([sys.executable, S7["fake"],
                                  "--port", str(PUERTO7), "-cmoe"],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
try:
    time.sleep(1.0)
    p7 = _correr_barrido(S7, PUERTO7)
    salida7 = p7.stdout.decode("utf-8", errors="replace") + \
        p7.stderr.decode("utf-8", errors="replace")
    check("E26: /health vivo -> FATAL sin tocar nada",
          p7.returncode != 0 and "/health ya responde" in salida7,
          "rc=%s" % p7.returncode)
finally:
    proceso_falso.send_signal(signal.SIGTERM)
    proceso_false = None
    try:
        proceso_falso.wait(timeout=5)
    except Exception:
        proceso_falso.kill()

PUERTO8 = _libre()
S8 = _montar_escenario("server-muerto")
p8 = subprocess.run(
    [sys.executable, SCRIPT, "--server", os.path.join(S8["dir"], "NO-EXISTE"),
     "--modelo", S8["modelo"], "--logs", S8["logs"],
     "--puerto", str(PUERTO8)],
    capture_output=True, timeout=60,
    env={**os.environ, "BARRIDO_PAUSA_S": "0"})
check("E27: server inexistente -> FATAL claro",
      p8.returncode != 0 and "no existe el server" in
      (p8.stdout + p8.stderr).decode("utf-8", errors="replace"))

# ================ 7. ancla muerta = FATAL + recuperacion (v1.3) =============
print("--- ANCLA MUERTA = FATAL (hotfix de campo v1.3) ---")
PUERTO9 = _libre()
S9 = _montar_escenario("ancla-muerta", env_extra={"FAKE_RECHAZA": "1"})
p9 = _correr_barrido(S9, PUERTO9)
salida9 = p9.stdout.decode("utf-8", errors="replace") + \
    p9.stderr.decode("utf-8", errors="replace")
filas9 = _leer_csv(S9)
check("E35: ancla muerta -> FATAL inmediato, 1 fila invalida con forense",
      p9.returncode != 0 and "ANCLA" in salida9 and "no cargo" in salida9
      and len(filas9) == 1 and filas9[0]["valido"] == "NO"
      and "failed to allocate" in filas9[0]["nota"],
      "rc=%s filas=%d nota=%s"
      % (p9.returncode, len(filas9),
         filas9[0]["nota"][:140] if filas9 else "(sin filas)"))

# la recuperacion del campo: MISMA carpeta, fake sano -> el resume solo
# cuenta filas SI -> re-mide las 13 y la sesion se recupera sin tocar nada
S9["env"] = {}
p10 = _correr_barrido(S9, PUERTO9)
salida10 = p10.stdout.decode("utf-8", errors="replace")
filas10 = _leer_csv(S9)
_validos10 = sorted(int(r["id"]) for r in filas10 if r["valido"] == "SI")
check("E36: resume tras ancla muerta re-mide las 13 y recupera la sesion",
      p10.returncode == 0 and _validos10 == list(range(1, 14))
      and len(filas10) == 14,
      "rc=%s validos=%s filas=%d"
      % (p10.returncode, _validos10, len(filas10)))

print("")
if ok_fallos:
    print("TEST BARRIDO-N3: %d FALLOS -> %s" % (len(ok_fallos), ok_fallos))
    sys.exit(1)
print("TEST BARRIDO-N3: TODO VERDE")
