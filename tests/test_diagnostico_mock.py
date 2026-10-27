#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Test de diagnostico-velocidad.py v1.1 con server falso.

Unitarios:
  T01 parsear_config: comentarios, espacios y claves -> dict limpio
  T02 el config.txt REAL del repo tiene las 9 claves exigidas
  T03 construir_esperado trabajo (k=8): SIN override
  T04 construir_esperado charla (k=4): CON override int:4
  T05 clasificar_decode: BAJO / NORMAL-K8 / GRIS / HUELE-K4 / SIN-DATO
  T06 _tokens respeta comillas (igualdad EXACTA de la lista - v1.1: sin `or`)
  T07 k_de_cmdline: override int:4 -> 4, int:5 -> 5, sin override -> 8
  T08 diferenciar_receta: multiset (orden de -ub/-b no engana)
  T09 certificar_receta: vivo=trabajo MATCH, vivo=charla MATCH con k, vivo
      con flag extra -> sin match + sobran
  T10 parsear_gpu_csv: linea completa, linea con N/A, linea corta
  T11 culpritos: RAM al limite / GPU caliente / throttle / plan Equilibrado
  T12 veredicto: NORMAL-K8 responde "¿deberia ir a mas?"; HUELE-K4 apunta a
      CHARLA; OJO si k vivo != k esperado
  T12d NORMAL-K8 cita el RECUERDO certificado del Director (21 = TECHO sweep)
  T12e dia lento dentro del rango cita el suelo del lab (17.36)
  T12f BAJO: el freno es del DIA + el 21 era techo, no piso
  T12g dia bueno (>=20.5) reconoce los dias buenos del recuerdo
  T15 puerto_de_tokens: encuentra --port del vivo; None si no hay
  T16 rutas con distinto CASE (D:\ vs d:\) siguen dando MATCH (v1.1)
  T17 con DOS procesos vivos (zombie primero) se queda el que coincide (v1.1)
E2E (fake server HTTP: /health + POST /completion con timings enlatados):
  T13 corrida completa: rc=0, informe md escrito con el veredicto NORMAL-K8
  T14 sin server: rc=1 con mensaje claro "No hay server"
"""
import importlib.util
import os
import socket
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica",
                                      "scripts", "diagnostico-velocidad.py"))
CFG_REAL = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica",
                                        "configs", "config.txt"))
DIR = tempfile.mkdtemp(prefix="diag_test_")
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


spec = importlib.util.spec_from_file_location("diag", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# ---------------------------------------------------------------- T01 parseo
RUTA_SAMPLE = os.path.join(DIR, "sample.txt")
with open(RUTA_SAMPLE, "w") as f:
    f.write("# comentario\n\n"
            "RUTA_SERVER = D:\\llama.cpp\\llama-server.exe\n"
            "  PUERTO =  9931  \n"
            "FLAGS_BASE = -ngl 99 -cmoe\n"
            "linea rota sin igualdad\n")
c = m.parsear_config(RUTA_SAMPLE)
check("T01 parsear_config limpia y respeta espacios",
      c.get("RUTA_SERVER") == "D:\\llama.cpp\\llama-server.exe"
      and c.get("PUERTO") == "9931" and c.get("FLAGS_BASE") == "-ngl 99 -cmoe"
      and len(c) == 3, str(c))

# ------------------------------------------------- T02 config real del repo
cfg_real = m.parsear_config(CFG_REAL)
check("T02 config.txt REAL del repo tiene las 9 claves",
      all(k in cfg_real for k in m.KEYS) and cfg_real["PUERTO"] == "9931"
      and cfg_real["EXPERTOS_TRABAJO"] == "8"
      and cfg_real["EXPERTOS_CHARLA"] == "4")

# ------------------------------------------ T03/T04 construir esperado
cmd_t, k_t = m.construir_esperado(cfg_real, "trabajo")
cmd_c, k_c = m.construir_esperado(cfg_real, "charla")
check("T03 esperado trabajo: k=8 y SIN override", k_t == 8
      and not any("override-kv" in x for x in cmd_t))
check("T04 esperado charla: k=4 y CON override int:4", k_c == 4
      and "qwen35moe.expert_used_count=int:4" in cmd_c)

# ------------------------------------------------------------ T05 clasificar
pares = [(13.0, "BAJO"), (17.8, "NORMAL-K8"), (21.5, "NORMAL-K8"),
         (22.5, "GRIS"), (27.0, "HUELE-K4"), (None, "SIN-DATO")]
check("T05 clasificar_decode: los 5 veredictos",
      all(m.clasificar_decode(v)[0] == e for v, e in pares),
      str([(v, m.clasificar_decode(v)[0]) for v, e in pares]))

# ---------------------------------------------------------------- T06 tokens
linea = r'"C:\llama server\llama-server.exe" -m "C:\mis modelos\m.gguf" -ngl 99'
tk = m._tokens(linea)
# v1.1: igualdad EXACTA (la version anterior tenia un `or tk[-1]=="99"` que
# volvia valida casi cualquier salida rota de _tokens)
check("T06 _tokens respeta comillas (igualdad exacta)",
      tk == [r"C:\llama server\llama-server.exe", "-m",
             r"C:\mis modelos\m.gguf", "-ngl", "99"], str(tk))

# -------------------------------------------------------------- T07 k vivo
check("T07 k_de_cmdline: 4 / 5 / 8 / None",
      m.k_de_cmdline(["server", "--override-kv",
                      "qwen35moe.expert_used_count=int:4"]) == 4
      and m.k_de_cmdline(["server", "--override-kv",
                          "qwen35moe.expert_used_count=int:5"]) == 5
      and m.k_de_cmdline(["server", "-ngl", "99"]) == 8
      and m.k_de_cmdline(["server", "--override-kv", "otra.cosa=x"]) is None)

# -------------------------------------------------------- T08 multiset diff
a = ["-ub", "256", "-b", "2048", "-ub", "1024", "-b", "4096"]
b = ["-b", "4096", "-ub", "1024", "-ub", "256", "-b", "2048"]
f, s = m.diferenciar_receta(a, b)
check("T08 diferenciar_receta: multiset ignora el orden", not f and not s)
f, s = m.diferenciar_receta(["-cmoe", "-fa", "on"], ["-cmoe"])
check("T08b faltan/sobran correctos (vivo con flag extra -> sobran)",
      not f and s == ["-fa", "on"], "faltan=%s sobran=%s" % (f, s))
f, s = m.diferenciar_receta(["-cmoe"], ["-cmoe", "-fa", "on"])
check("T08c vivo sin una flag de la receta -> faltan",
      f == ["-fa", "on"] and not s, "faltan=%s sobran=%s" % (f, s))

# -------------------------------------------------- T09 certificar receta
vivo_t = " ".join(cmd_t)
vivo_c = " ".join(cmd_c)
vivo_raro = vivo_t + " -lv 4"
orig = m.cmdline_viva
try:
    m.cmdline_viva = lambda: ([vivo_t], "test")
    r = m.certificar_receta(cfg_real)
    t09a = r["match"] == "trabajo" and r["k_vivo"] == 8 and r["k_esperado"] == 8
    m.cmdline_viva = lambda: ([vivo_c], "test")
    r = m.certificar_receta(cfg_real)
    t09b = r["match"] == "charla" and r["k_vivo"] == 4 and r["k_esperado"] == 4
    m.cmdline_viva = lambda: ([vivo_raro], "test")
    r = m.certificar_receta(cfg_real)
    t09c = r["match"] is None and r["sobran"] == ["-lv", "4"] and r["k_vivo"] == 8
finally:
    m.cmdline_viva = orig
check("T09 certificar: trabajo MATCH / charla MATCH / flag extra sin match",
      t09a and t09b and t09c,
      "t09a=%s t09b=%s t09c=%s" % (t09a, t09b, t09c))

# ------------------------------------- T16 CASE de rutas (bug v1.0, fix v1.1)
vivo_lw = list(cmd_t)
vivo_lw[0] = vivo_lw[0].lower()
_im = vivo_lw.index("-m")
vivo_lw[_im + 1] = vivo_lw[_im + 1].lower()
try:
    m.cmdline_viva = lambda: ([" ".join(vivo_lw)], "test")
    r16 = m.certificar_receta(cfg_real)
    t16 = (r16["match"] == "trabajo" and not r16["faltan"]
           and not r16["sobran"])
finally:
    m.cmdline_viva = orig
check("T16 rutas con distinto CASE siguen dando MATCH (D:\\ vs d:\\)",
      t16, "match=%s faltan=%s sobran=%s" % (r16["match"],
                                             r16["faltan"], r16["sobran"]))

# --------------------------------- T17 multi-proceso (bug v1.0, fix v1.1)
try:
    m.cmdline_viva = lambda: ([vivo_raro, vivo_t], "test")
    r17 = m.certificar_receta(cfg_real)
    t17 = (r17["match"] == "trabajo" and not r17["faltan"]
           and not r17["sobran"] and r17["k_vivo"] == 8)
finally:
    m.cmdline_viva = orig
check("T17 con DOS procesos vivos (zombie primero) gana el que coincide",
      t17, "match=%s k=%s" % (r17["match"], r17["k_vivo"]))

# ------------------------------------------------------------ T15 puerto vivo
check("T15 puerto_de_tokens: --port del vivo / None si falta",
      m.puerto_de_tokens(["server", "--port", "9931"]) == "9931"
      and m.puerto_de_tokens(["server", "-ngl", "99"]) is None)

# ------------------------------------------------------------ T10 gpu csv
g = m.parsear_gpu_csv("71, 5, 2218, 4096, 1650, 1950, 55, 75\n")
check("T10 parsear_gpu_csv completo", g and g["temp_c"] == 71.0
      and g["mem_usada_mib"] == 2218.0 and g["reloj_max_mhz"] == 1950.0, str(g))
g = m.parsear_gpu_csv("71, 5, 2218, 4096, 1650, 1950, N/A, N/A\n")
check("T10b parsear_gpu_csv tolera N/A", g and g["watts"] is None)
check("T10c parsear_gpu_csv linea corta -> None",
      m.parsear_gpu_csv("71, 5\n") is None)

# ------------------------------------------------------------ T11 culpritos
ram_mala = {"carga_pct": 96, "libre_gb": 0.9, "total_gb": 16.0}
gpu_caliente = {"temp_c": 85, "util_pct": 70, "mem_usada_mib": 2218,
                "mem_total_mib": 4096, "reloj_mhz": 1400,
                "reloj_max_mhz": 1950}
plan_mal = {"texto": "GUID equilibrado", "equilibrado": True}
cul = m.culpritos(ram_mala, gpu_caliente, plan_mal)
check("T11 culpritos: RAM + GPU caliente + throttle + plan",
      len(cul) == 4, str(cul))
check("T11b culpritos: limpio -> vacio",
      m.culpritos({"carga_pct": 70, "libre_gb": 3.0, "total_gb": 16.0},
                  {"temp_c": 65, "util_pct": 90, "mem_usada_mib": 2218,
                   "mem_total_mib": 4096, "reloj_mhz": 1950,
                   "reloj_max_mhz": 1950}, None) == [])

# ------------------------------------------------------------- T12 veredicto
med = {"decode": 19.0, "prefill": 300.0, "detalle": []}
cert_ok = {"k_vivo": 8, "match": "trabajo", "k_esperado": 8,
           "faltan": [], "sobran": [], "nota": ""}
L = m.veredicto(med, cert_ok, None, None, None)
check("T12 veredicto NORMAL-K8 responde la pregunta",
      L[0].startswith("VEREDICTO: NORMAL-K8")
      and any("deberia ir a mas" in l for l in L)
      and any("reloj de pared" in l for l in L), str(L))
med_k4 = {"decode": 27.0, "prefill": 300.0, "detalle": []}
L = m.veredicto(med_k4, {"k_vivo": 4, "match": "charla", "k_esperado": 4,
                         "faltan": [], "sobran": [], "nota": ""},
                None, None, None)
check("T12b veredicto HUELE-K4 apunta a CHARLA",
      L[0].startswith("VEREDICTO: HUELE-K4") and any("CHARLA" in l for l in L))
cert_raro = {"k_vivo": 5, "match": "charla", "k_esperado": 4,
             "faltan": [], "sobran": [], "nota": ""}
L = m.veredicto(med_k4, cert_raro, None, None, None)
check("T12c OJO si k vivo != k esperado del config",
      any("OJO" in l and "k=5" in l for l in L), str(L))

# --------------------------------- T12d-f el recuerdo del Director en v1.1
L = m.veredicto(med, cert_ok, None, None, None)  # med decode 19.0 -> NORMAL-K8
check("T12d NORMAL-K8 cita el recuerdo certificado (21 = TECHO del sweep)",
      any("recuerdo" in l and "TECHO" in l and "21" in l for l in L), str(L))
med_lento = {"decode": 18.0, "prefill": 300.0, "detalle": []}
L = m.veredicto(med_lento, cert_ok, None, None, None)
check("T12e dia lento dentro del rango cita el suelo del lab (17.36)",
      any("dia lento" in l and "17.36" in l for l in L), str(L))
med_bajo = {"decode": 14.0, "prefill": 300.0, "detalle": []}
L = m.veredicto(med_bajo, cert_ok, None, None, None)
check("T12f BAJO: freno del DIA + tu 21 era TECHO del sweep, no piso",
      any("freno es del DIA" in l for l in L)
      and any("TECHO del sweep" in l for l in L), str(L))
med_bueno = {"decode": 21.2, "prefill": 300.0, "detalle": []}
L = m.veredicto(med_bueno, cert_ok, None, None, None)
check("T12g dia bueno (>=20.5) reconoce los dias buenos del recuerdo",
      any("dias buenos" in l for l in L), str(L))

# ---------------------------------------------------------------- E2E T13
PUERTO = _libre()
EST = {"pf": 312.5, "dec": 19.0}


class FakeH(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        b = b'{"status": "ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        n = len(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        cuerpo = json.dumps({
            "timings": {"prompt_per_second": EST["pf"],
                        "predicted_per_second": EST["dec"],
                        "predicted_n": 256},
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


import json  # noqa: E402  (tras definir el server, antes de usarlo)
srv = HTTPServer(("127.0.0.1", PUERTO), FakeH)
threading.Thread(target=srv.serve_forever, daemon=True).start()

cfg_e2e = dict(cfg_real)
cfg_e2e["PUERTO"] = str(PUERTO)
LOGS = os.path.join(DIR, "logs-e2e")
cfg_e2e["RUTA_LOGS"] = LOGS
cfg_path = os.path.join(DIR, "config-e2e.txt")
with open(cfg_path, "w") as f:
    for k in m.KEYS:
        f.write("%s = %s\n" % (k, cfg_e2e[k]))

viejo = os.environ.get("CONFIG_TXT")
os.environ["CONFIG_TXT"] = cfg_path
try:
    rc = m.main([])
finally:
    if viejo is None:
        os.environ.pop("CONFIG_TXT", None)
    else:
        os.environ["CONFIG_TXT"] = viejo
informes = [f for f in os.listdir(LOGS) if f.startswith("diagnostico-")] if \
    os.path.isdir(LOGS) else []
contenido = ""
if informes:
    with open(os.path.join(LOGS, informes[0]), encoding="utf-8") as f:
        contenido = f.read()
check("T13 E2E rc=0 + informe con NORMAL-K8 y decode 19.0",
      rc == 0 and len(informes) == 1 and "NORMAL-K8" in contenido
      and "19.00" in contenido and "Estacion 2" in contenido,
      "rc=%s informes=%s" % (rc, informes))

# ---------------------------------------------------------------- E2E T14
PUERTO2 = _libre()
cfg_e2e2 = dict(cfg_e2e)
cfg_e2e2["PUERTO"] = str(PUERTO2)
cfg_path2 = os.path.join(DIR, "config-e2e-2.txt")
with open(cfg_path2, "w") as f:
    for k in m.KEYS:
        f.write("%s = %s\n" % (k, cfg_e2e2[k]))
os.environ["CONFIG_TXT"] = cfg_path2
try:
    rc2 = m.main([])
finally:
    if viejo is None:
        os.environ.pop("CONFIG_TXT", None)
    else:
        os.environ["CONFIG_TXT"] = viejo
check("T14 sin server: rc=1 y mensaje claro", rc2 == 1)

# ---------------------------------------------------------------- resumen
print("")
if ok_fallos:
    print("FALLOS: %s" % ", ".join(ok_fallos))
    sys.exit(1)
print("TODO VERDE")
srv.shutdown()
