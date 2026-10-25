#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test E2E de abrir-qwen-apex.py v2.0-minimal con server falso.

Caso 1: nada vivo -> lanza el fake (sirve /health y muere a los 3 s),
muestra banner MODELO LISTO y sale limpio rc=0.
Caso 2: server ya vivo -> [AVISO] ya abierto, rc=0, NO lanza nada.
"""
import importlib.util
import io
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica", "abrir-qwen-apex.py"))
DIR = tempfile.mkdtemp(prefix="abrir_test_")
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

FAKE = os.path.join(DIR, "fake-server.py")
with open(FAKE, "w") as f:
    f.write(
        "#!/usr/bin/env python3\n"
        "import json, os, sys, threading, time\n"
        "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "vida = float(os.environ.get('FAKE_VIDA', '0'))\n"
        "if vida > 0: threading.Timer(vida, lambda: os._exit(0)).start()\n"
        "class H(BaseHTTPRequestHandler):\n"
        "    def log_message(self, *a): pass\n"
        "    def do_GET(self):\n"
        "        b = b'{\"status\": \"ok\"}'\n"
        "        self.send_response(200)\n"
        "        self.send_header('Content-Type', 'application/json')\n"
        "        self.send_header('Content-Length', str(len(b)))\n"
        "        self.end_headers()\n"
        "        self.wfile.write(b)\n"
        "HTTPServer(('127.0.0.1', %d), H).serve_forever()\n" % PUERTO)
os.chmod(FAKE, 0o755)

spec = importlib.util.spec_from_file_location("abrir", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# parches: fake server en el puerto del test, muere solo a los 3 s (rc 0)
m.RUTA_SERVER = FAKE
m.RUTA_MODELO = os.path.join(DIR, "modelo.gguf")
open(m.RUTA_MODELO, "w").write("x")
m.PORT = PUERTO
m.BASE_FLAGS = list(m.BASE_FLAGS)
m.BASE_FLAGS[m.BASE_FLAGS.index("--port") + 1] = str(PUERTO)
os.environ["FAKE_VIDA"] = "3"


def _correr():
    buf = io.StringIO()
    viejo = sys.stdout
    sys.stdout = buf
    try:
        rc = m.main()
    finally:
        sys.stdout = viejo
    return rc, buf.getvalue()


# caso 1: flujo completo (el fake muere solo a los 3 s)
rc, out = _correr()
check("caso 1 rc=0", rc == 0, "rc=%s" % rc)
check("caso 1 banner MODELO LISTO", "MODELO LISTO" in out)
check("caso 1 manda a CHATEAR-QWEN", "CHATEAR-QWEN.bat" in out)
check("caso 1 sin menu ni preguntas", "[1]" not in out and "opcion" not in out.lower())

# caso 2: ya hay server vivo en el puerto -> AVISO y no lanza nada
os.environ["FAKE_VIDA"] = "0"   # este fake es inmortal
guard_p = subprocess.Popen([sys.executable, FAKE])
time.sleep(1.0)
rc2, out2 = _correr()
check("caso 2 rc=0 con server vivo", rc2 == 0)
check("caso 2 avisa ya abierto", "YA esta abierto" in out2)
guard_p.terminate()
guard_p.wait()

import shutil
shutil.rmtree(DIR, ignore_errors=True)
print("\n" + "=" * 60)
if ok_fallos:
    print("FALLOS: %d -> %s" % (len(ok_fallos), ", ".join(ok_fallos)))
    sys.exit(1)
print("TEST E2E ABRIR-MINIMAL: TODO VERDE")
sys.exit(0)
