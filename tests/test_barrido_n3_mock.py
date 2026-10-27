#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de barrido-n3-eficiencia.py v1.0 con server falso (sin GPU, sin
Windows). Mismo patron de la casa (test_barrido_mock / test_diagnostico_mock):
el fake llama-server es un script python que el PROPIO barrido lanza con
Popen; sirve /health y /completion (stream y no-stream) en su --port y
escribe en SU stdout las lineas de log que el barrido usa como certificado
(restored context checkpoint / forcing full prompt re-processing / warning
#24055 / system_info USE_GRAPHS REPACK / listening on / loading model).

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
check("U02: ancla y bookend sin flags (receta diaria pura)",
      cfgs[0]["flags"] == [] and cfgs[12]["flags"] == [])
check("U03: REUSE lleva --cache-reuse 256 y SHIFT lleva shift+reuse",
      cfgs[4]["flags"] == ["--cache-reuse", "256"]
      and cfgs[5]["flags"] == ["--context-shift", "--cache-reuse", "256"])
check("U04: NCM37C4 verbatim del barrido-30",
      cfgs[7]["flags"] == ["-ncmoe", "37", "-c", "4096",
                           "-ctk", "q4_0", "-ctv", "q4_0"])
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
                                  "--port", str(PUERTO7)],
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

print("")
if ok_fallos:
    print("TEST BARRIDO-N3: %d FALLOS -> %s" % (len(ok_fallos), ok_fallos))
    sys.exit(1)
print("TEST BARRIDO-N3: TODO VERDE")
