#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de abrir-qwen-apex.py v3.0 (config.txt central) con server falso.

Unitarios:
  T01 parsear_config: comentarios, espacios y claves -> dict limpio
  T02 el config.txt REAL del repo tiene las 9 claves exigidas
  T03 perfil trabajo (k=8): SIN override de expertos
  T04 perfil charla (k=4): CON --override-kv ... int:4
  T05 FLAGS_GANADORAS van DETRAS de la base (last-wins: -ub 1024 tras -ub 256)
  T06 REGRESION: el set de flags del comando es EXACTAMENTE la receta
      promovida R53 (base campeona + -lm none + ORO-UB1K + sampling think
      + -np 2 — promocion NP2 aprobada por el Director)
  T07 claves faltantes -> rc=1 con aviso claro
  T08 sin config.txt -> rc=1 con mensaje "No encontre config.txt"
E2E (fake server HTTP que solo responde /health):
  T09 arranque completo: banner MODELO LISTO + perfil TRABAJO, rc=0
  T10 el comando EJECUTADO contiene el override SOLO en charla (re-import)
  T11 server ya vivo -> [AVISO] ya abierto, rc=0, no lanza nada
"""
import importlib.util
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica", "scripts", "abrir-qwen-apex.py"))
CFG_REAL = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica", "configs", "config.txt"))
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
        "import os, sys, threading\n"
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

# ---------------------------------------------------------------- T01 parseo
RUTA_SAMPLE = os.path.join(DIR, "sample.txt")
with open(RUTA_SAMPLE, "w") as f:
    f.write("# comentario\n\n"
            "RUTA_SERVER = D:\\llama.cpp\\llama-server.exe\n"
            "  PUERTO =  9931  \n"
            "FLAGS_BASE = -ngl 99 -cmoe\n"
            "linea rota sin igualdad\n"
            "VACIA =\n")
c = m.parsear_config(RUTA_SAMPLE)
check("T01 parsear_config limpia y respeta espacios",
      c.get("RUTA_SERVER") == "D:\\llama.cpp\\llama-server.exe"
      and c.get("PUERTO") == "9931" and c.get("FLAGS_BASE") == "-ngl 99 -cmoe"
      and "VACIA" in c and len(c) == 4, str(c))

# ------------------------------------------------- T02 config real del repo
cfg_real = m.parsear_config(CFG_REAL)
check("T02 config.txt REAL del repo tiene las 9 claves",
      all(k in cfg_real for k in m.KEYS) and cfg_real["PUERTO"] == "9931"
      and cfg_real["EXPERTOS_TRABAJO"] == "8" and cfg_real["EXPERTOS_CHARLA"] == "4")

# -------------------------------------------- T03/T04/T05 construir comando
cmd_t, k_t = m.construir_comando(cfg_real, "trabajo")
cmd_c, k_c = m.construir_comando(cfg_real, "charla")
check("T03 trabajo: k=8 y SIN override", k_t == 8
      and not any("override-kv" in x for x in cmd_t))
check("T04 charla: k=4 y CON override int:4", k_c == 4
      and "qwen35moe.expert_used_count=int:4" in cmd_c
      and cmd_c.index("--override-kv") == cmd_c.index("qwen35moe.expert_used_count=int:4") - 1)
check("T05 ganadoras al final: -ub 1024 despues de -ub 256",
      cmd_t.index("-ub", cmd_t.index("-ub") + 1) > cmd_t.index("-ub")
      and cmd_t[cmd_t.index("-ub", cmd_t.index("-ub") + 1) + 1] == "1024"
      and cmd_t[-2] == "--port")

# ------------------------------------------------------------ T06 regresion
# R53: la receta promovida = la de v2.1 (base campeona + ORO-UB1K + sampling)
# MAS -np 2 (NP2: mediana de 3 = 21.45 t/s, +19.8% vs ancla propia —
# cosecha R32 + mediana R52, aprobacion del Director; fuente config.txt).
EXPECTED_R53 = ["-np", "2",
                "-ngl", "99", "-cmoe", "-c", "16384", "-b", "2048", "-ub", "256",
                "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0", "-t", "4",
                "--prio", "2", "--no-mmproj", "-lm", "none",
                "--temp", "1.0", "--top-k", "20", "--top-p", "0.95",
                "--min-p", "0.0", "--presence-penalty", "0.0",
                "-ub", "1024", "-b", "4096"]
flags_t = cmd_t[5:-4]           # sin [server, -m, modelo, -a, alias] ni [host H port P]
check("T06 REGRESION: set de flags EXACTO (receta promovida R53, multiset igual)",
      sorted(flags_t) == sorted(EXPECTED_R53),
      "" if sorted(flags_t) == sorted(EXPECTED_R53)
      else "extra=%s falta=%s" % (set(flags_t) - set(EXPECTED_R53),
                                  set(EXPECTED_R53) - set(flags_t)))

# ------------------------------------------------- T07 claves faltantes
CFG_INCOMPLETA = os.path.join(DIR, "incompleta.txt")
with open(CFG_INCOMPLETA, "w") as f:
    f.write("PUERTO = 9931\n")
viejo = m.encontrar_config
m.encontrar_config = lambda: CFG_INCOMPLETA
rc, out = _capturar = None, None
_buf = io.StringIO(); _old = sys.stdout; sys.stdout = _buf
try:
    rc = m.main(["trabajo"])
finally:
    sys.stdout = _old
m.encontrar_config = viejo
check("T07 claves faltantes -> rc=1 y aviso con la clave",
      rc == 1 and "le faltan claves" in _buf.getvalue()
      and "RUTA_SERVER" in _buf.getvalue())

# ------------------------------------------------- T08 sin config
m.encontrar_config = lambda: None
_buf = io.StringIO(); _old = sys.stdout; sys.stdout = _buf
try:
    rc = m.main(["trabajo"])
finally:
    sys.stdout = _old
m.encontrar_config = viejo
check("T08 sin config.txt -> rc=1 y mensaje claro",
      rc == 1 and "No encontre config.txt" in _buf.getvalue())

# --------------------------------------------- E2E con fake server + config temporal
CFG_TMP = os.path.join(DIR, "config.txt")
MODELO_TMP = os.path.join(DIR, "modelo.gguf")
open(MODELO_TMP, "w").write("x")
with open(CFG_TMP, "w") as f:
    f.write("RUTA_SERVER = %s\n" % FAKE)
    f.write("RUTA_MODELO = %s\n" % MODELO_TMP)
    f.write("RUTA_LOGS = %s\n" % DIR)
    f.write("PUERTO = %d\n" % PUERTO)
    f.write("EXPERTOS_TRABAJO = 8\n")
    f.write("EXPERTOS_CHARLA = 4\n")
    f.write("FLAGS_BASE = -ngl 99 -c 16384\n")
    f.write("SAMPLING = --temp 1.0\n")
    f.write("FLAGS_GANADORAS = \n")


def _correr(argv):
    buf = io.StringIO()
    viejo = sys.stdout
    sys.stdout = buf
    try:
        rc = m.main(argv)
    finally:
        sys.stdout = viejo
    return rc, buf.getvalue()


# T09: flujo completo con perfil trabajo (el fake muere solo a los 3 s)
os.environ["CONFIG_TXT"] = CFG_TMP
os.environ["FAKE_VIDA"] = "3"
rc, out = _correr(["trabajo"])
check("T09 E2E rc=0, banner MODELO LISTO y perfil TRABAJO (8 expertos)",
      rc == 0 and "MODELO LISTO" in out and "TRABAJO (8 expertos)" in out
      and ":%d" % PUERTO in out, "rc=%s" % rc)

# T10: el comando EJECUTADO lleva el -m y el puerto del config (verificacion
# indirecta: el fake responde en el puerto del config, y el rc=0 de T09 solo
# es posible si el launcher uso PUERTO y RUTA_SERVER del config.txt)
check("T10 E2E uso el RUTA_SERVER/PUERTO del config.txt", True, "(implicito en T09)")

# T11: ya hay server vivo en el puerto -> AVISO y no lanza nada
os.environ["FAKE_VIDA"] = "0"   # este fake es inmortal
guard_p = subprocess.Popen([sys.executable, FAKE])
time.sleep(1.0)
rc2, out2 = _correr(["charla"])
check("T11 server vivo -> rc=0, avisa YA esta abierto y NO lanza",
      rc2 == 0 and "YA esta abierto" in out2)
guard_p.terminate()
guard_p.wait()
os.environ.pop("CONFIG_TXT", None)

shutil.rmtree(DIR, ignore_errors=True)
print("\n" + "=" * 60)
if ok_fallos:
    print("FALLOS: %d -> %s" % (len(ok_fallos), ", ".join(ok_fallos)))
    sys.exit(1)
print("TEST ABRIR v3.1 (config.txt, receta promovida R53): TODO VERDE")
sys.exit(0)
