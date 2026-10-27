#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test E2E de barrido-qwen-25.py con server falso (sin GPU, sin Windows).

El fake llama-server es un script python que el PROPIO barrido lanza con
Popen (igual que lanzara el llama-server real): sirve /health y /completion
en el puerto que le llega por --port, y lleva cuenta de arranques en un
archivo para dar tps distintos por config (10 + N_arranque).

Verifica: 25 filas en CSV, tps promediadas (constantes aqui), combos
dinamicos construidos con ganadores medidos, logs por config, ranking y
comando ganador, resume (2a corrida salta todo y no arranca nada nuevo),
regex de accept, y el guardarrail anti-server-vivo.
"""
import builtins
import importlib.util
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica", "scripts", "barrido-qwen-25.py"))
DIR = tempfile.mkdtemp(prefix="barrido_test_")
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


PUERTO = _libre()

# fake server ejecutable: sirve el puerto que le llega por --port, cuenta
# sus arranques en FAKE_COUNT y sirve tps = 10 + arranque
FAKE_SERVER = os.path.join(DIR, "fake-server.py")
FAKE_COUNT = os.path.join(DIR, "arranques.txt")
# el fake lee el contador de esta ruta via env (los hijos heredan el env del test)
os.environ["FAKE_COUNT"] = FAKE_COUNT
with open(FAKE_SERVER, "w") as f:
    f.write(
        "#!/usr/bin/env python3\n"
        "import json, os, sys, threading, time\n"
        "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "args = sys.argv[1:]\n"
        "port = 9931\n"
        "if '--port' in args: port = int(args[args.index('--port')+1])\n"
        "cnt = os.environ.get('FAKE_COUNT', '/tmp/fake_arranques.txt')\n"
        "def bump():\n"
        "    try: n = int(open(cnt).read().strip() or 0)\n"
        "    except Exception: n = 0\n"
        "    n += 1\n"
        "    open(cnt, 'w').write(str(n))\n"
        "    return n\n"
        "N = bump()\n"
        "class H(BaseHTTPRequestHandler):\n"
        "    def log_message(self, *a): pass\n"
        "    def _send(self, code, obj):\n"
        "        b = json.dumps(obj).encode()\n"
        "        self.send_response(code)\n"
        "        self.send_header('Content-Type', 'application/json')\n"
        "        self.send_header('Content-Length', str(len(b)))\n"
        "        self.end_headers()\n"
        "        self.wfile.write(b)\n"
        "    def do_GET(self):\n"
        "        if self.path == '/health': self._send(200, {'status':'ok'})\n"
        "        else: self._send(404, {'e':1})\n"
        "    def do_POST(self):\n"
        "        ln = int(self.headers.get('Content-Length', 0))\n"
        "        body = json.loads(self.rfile.read(ln) or b'{}')\n"
        "        assert body.get('temperature') == 0.0, 'temp debe ser 0'\n"
        "        assert body.get('cache_prompt') is True, 'cache_prompt true'\n"
        "        self._send(200, {'timings': {'predicted_per_second': 10.0 + N,\n"
        "            'prompt_per_second': 21.0, 'predicted_n': body.get('n_predict')}})\n"
        "httpd = HTTPServer(('127.0.0.1', port), H)\n"
        "httpd.serve_forever()\n")
os.chmod(FAKE_SERVER, 0o755)
open(FAKE_COUNT, "w").write("0")

MODELO = os.path.join(DIR, "modelo.gguf")
open(MODELO, "w").write("x")

# ---------- importar el barrido con parches ----------
spec = importlib.util.spec_from_file_location("barrido", SCRIPT)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

b.RUTA_SERVER = FAKE_SERVER
b.RUTA_MODELO = MODELO
b.HOST = "127.0.0.1"
b.PORT = PUERTO
b.URL = "http://127.0.0.1:%d" % PUERTO
# BASE_FLAGS se construyo al importar con "--port 9931" (valor por defecto):
# hay que re-parchear la lista ya construida o el fake server levantaria en
# 9931 y el health check del barrido (con PUERTO del test) nunca responderia
b.BASE_FLAGS[b.BASE_FLAGS.index("--port") + 1] = str(PUERTO)
b.N_PREDICT = 16
b.RUNS = 4
b.PAUSA_CADA = 1000
b.PAUSA_SEG = 0
b.DIR_LOGS = os.path.join(DIR, "sweep-logs")
b.ARCH_CSV = os.path.join(DIR, "sweep-resultados.csv")

builtins.input = lambda *a, **k: ""

# acelerar el test: el sleep real (3 s por config para liberar VRAM) solo tiene
# sentido con el server de verdad; aqui lo anulamos SOLO dentro del modulo del
# barrido (time.time/strftime se conservan)
import types
b.time = types.SimpleNamespace(time=time.time, strftime=time.strftime,
                               sleep=lambda s: None)


def _correr():
    buf = io.StringIO()
    viejo = sys.stdout
    sys.stdout = buf
    try:
        rc = b.main()
    finally:
        sys.stdout = viejo
    return rc, buf.getvalue()


# ---------- guardarrail: server vivo previo ABORTA ----------
guard = os.path.join(DIR, "guard-server.py")
with open(guard, "w") as f:
    f.write("#!/usr/bin/env python3\n"
            "import json, sys, time\n"
            "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
            "class H(BaseHTTPRequestHandler):\n"
            "    def log_message(self, *a): pass\n"
            "    def do_GET(self):\n"
            "        self.send_response(200)\n"
            "        self.send_header('Content-Length', '15')\n"
            "        self.end_headers()\n"
            "        self.wfile.write(b'{\"status\": \"ok\"}')\n"
            "HTTPServer(('127.0.0.1', %d), H).serve_forever()\n" % PUERTO)
os.chmod(guard, 0o755)
p_guard = subprocess.Popen([sys.executable, guard])
time.sleep(1.0)
try:
    rc_guard, out_guard = _correr()
    check("guardarrail aborta con server vivo", rc_guard == 1 and "ABORTADO" in out_guard)
finally:
    p_guard.terminate()
    p_guard.wait()
    time.sleep(0.5)

# ---------- corrida 1 completa ----------
rc, out = _correr()
check("rc=0 en corrida completa", rc == 0, "rc=%s" % rc)
if rc != 0:
    print("--- stdout de la corrida fallida ---")
    print(out[-3000:])
check("CSV existe", os.path.exists(b.ARCH_CSV))
filas = b._leer_csv()
check("25 filas en CSV", len(filas) == 25, "filas=%d" % len(filas))
check("todas con tps", all((f.get("tps") or "").strip() for f in filas.values()))

# el fake da tps = 10 + N_arranque; el server arranca 1 vez por config en orden
# -> config id N se midio con tps constante 10+N; promedio pasadas 2-4 = 10+N
check("BASE (id 1) tps=11.00", filas[1]["tps"] == "11.00", filas[1]["tps"])
check("config 13 tps=23.00", filas[13]["tps"] == "23.00", filas[13]["tps"])

# combos dinamicos: fase A sobre BASE (id1=11.0): 2..13 dan 12..23 -> TODOS ganan
# combo_a: np1, t5 (13.00 T5 > 12.00 T3), poll100 (16>15), lmnone (17),
#          moecache512 (19 >= 18)
fl23 = (filas[23].get("flags") or "").split()
check("COMBO-A incluye -np 1", "-np" in fl23 and "1" in fl23, filas[23]["flags"])
check("COMBO-A incluye -t 5 (T5>T3)", "-t" in fl23 and "5" in fl23)
check("COMBO-A incluye -lm none", "-lm" in fl23 and "none" in fl23)
check("COMBO-A incluye moe-cache 512", "--moe-cache-mib" in fl23 and "512" in fl23)
# fase B (14..22 dan 24..32): mejor MTP = id 22 (32.0, MTPCMOED) -> entra completo
fl24 = (filas[24].get("flags") or "").split()
check("COMBO-MTP trae el MTP ganador completo",
      "--spec-draft-cpu-moe" in fl24, filas[24]["flags"])
fl25 = (filas[25].get("flags") or "").split()
check("COMBO-MTP-PLUS = mismo ganador MTP",
      "--spec-draft-cpu-moe" in fl25, filas[25]["flags"])

# ranking: ganador global = id 25 (combo A + mismo MTP, tps 10+25=35)
check("RANKING FINAL impreso", "RANKING FINAL" in out)
check("GANADOR impreso", "GANADOR:" in out)
check("comando para pegar impreso", "FLAGS_GANADORAS =" in out)
check("comando completo impreso", FAKE_SERVER in out)
check("ranking pone 25 primero", " 1. 35.00 t/s  25-" in out,
      out.split("RANKING FINAL")[-1][:200].replace("\n", " | "))

# logs por config
logs = os.listdir(b.DIR_LOGS)
check("logs por config (>=25)", len([l for l in logs if l.endswith(".log")]) >= 25,
      "%d logs" % len(logs))

# ---------- regex de accept ----------
log_fake = os.path.join(b.DIR_LOGS, "accept-test.log")
open(log_fake, "w").write("x\nsome line\ndraft acceptance rate = 78.5% de tokens\n")
check("regex accept extrae 78.5", b._accept_del_log(log_fake) == "78.5",
      b._accept_del_log(log_fake))
open(log_fake, "w").write("sin accept aqui\n")
check("regex accept vacio si no hay", b._accept_del_log(log_fake) == "")

# ---------- corrida 2 (resume): nada pendiente, server NO debe arrancar ----------
open(FAKE_COUNT, "w").write("0")
rc2, out2 = _correr()
check("resume rc=0", rc2 == 0)
check("resume: 25 saltadas", out2.count("ya medida") == 25,
      "%d saltadas" % out2.count("ya medida"))
check("resume: 0 arranques nuevos", open(FAKE_COUNT).read().strip() == "0",
      "arranques=%s" % open(FAKE_COUNT).read().strip())

shutil.rmtree(DIR, ignore_errors=True)
print("\n" + "=" * 60)
if ok_fallos:
    print("FALLOS: %d -> %s" % (len(ok_fallos), ", ".join(ok_fallos)))
    sys.exit(1)
print("TEST E2E BARRIDO: TODO VERDE")
sys.exit(0)
