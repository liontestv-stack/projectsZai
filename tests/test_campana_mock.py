#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de campana-10-pasos.py v1.0 con taller falso (sin GPU, sin red, sin
13 GB). Patron de la casa (test_barrido_n3_mock / test_abrir_mock): el
modulo se carga por importlib desde InformacionCritica/scripts (importa al
barrido real como companero), los directorios del rig son temporales y los
objetos pesados son FALSOS PERO REALISTAS:

  - CSVs de mediana falsos (3 carpetas b1/b2/b3 con ANCLA/NP2/ANCLA-FIN
    validas y una fila invalida que DEBE ser ignorada: solo valido=SI).
  - config.txt falso (claves de la casa) para la cirugia P2 y el humo P5.
  - GGUF fabricado A BYTES (magic + version + kvs: architecture, block_count
    256, expert_count 256, expert_used_count 8, nextn.*) para el parser.
  - SERVER FALSO: script python ejecutable que atiende /health y
    /v1/chat/completions (con timings) — reproduce el humo de P5 en los dos
    mundos: levanta y responde (VERIFICADO-HUMO-OK) y muere en la carga
    (FATAL con forense); mas el guardarrail de server ajeno vivo.

Verifica: puertas (p2 exige p1 GO, p3 exige p2, p4 exige N3 cerrado),
--fuerza queda escrito, cirugia P2 con backup + idempotente + --revert
byte-a-byte, mediana de 3 con ancla por corrida + bookend (GO / DUDOSO /
NO-GO / INCOMPLETO), informes APPEND-ONLY, estado json, autenticadores del
hito N2 PINADOS (bytes 14,069,266,720 + SHA256 36f9ec0e...7150), 20 prompts
del juez, pasos guiados 7-10, y el dispatch de main.
"""
import builtins
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import types

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.abspath(os.path.join(RAIZ, "..", "InformacionCritica",
                                      "scripts", "campana-10-pasos.py"))
DIR = tempfile.mkdtemp(prefix="campana_test_")
BASE = os.path.join(DIR, "base")
os.makedirs(BASE, exist_ok=True)
ok_fallos = []
n_checks = [0]


def check(nombre, cond, detalle=""):
    n_checks[0] += 1
    estado = "OK  " if cond else "FALLO"
    print("[%s] %s %s" % (estado, nombre, detalle))
    if not cond:
        ok_fallos.append(nombre)


spec = importlib.util.spec_from_file_location("campana", SCRIPT)
cam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cam)


def args(**kw):
    base = dict(dir=BASE, config=None, puerto=9931, b1=None, b2=None, b3=None,
                sin_corridas=True, revert=False, veredicto=None, tag=None,
                repo=cam.REPO_DEFAULT, dry_run=False, sin_humo=False,
                bat=None, fuerza=False)
    base.update(kw)
    return types.SimpleNamespace(**base)


def esperando(port):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p if port is None else port


# ---------------- fijar el terreno ------------------------------------------
FAKE_CONFIG = os.path.join(BASE, "config.txt")
CONFIG_ORIGINAL = (
    "# config falsa del taller\n"
    "RUTA_SERVER = %s\n"
    "RUTA_MODELO = D:\\ZLia\\models\\viejo.gguf\n"
    "PUERTO = 9931\n"
    "FLAGS_BASE = -ngl 99 -cmoe -c 16384 -fa on -ctk q8_0 -t 4 --no-mmproj -lm none\n"
    "SAMPLING = --temp 1.0 --top-k 20\n"
    "FLAGS_GANADORAS = -ub 1024 -b 4096\n"
)
with open(FAKE_CONFIG, "w", encoding="utf-8") as f:
    f.write(CONFIG_ORIGINAL % "SERVER_PLACEHOLDER")
ORIGINAL_CONFIG = open(FAKE_CONFIG, "rb").read()

CSV_HEAD = "proto,id,nombre,familia,fecha_hora,flags,load_s,valido,nota,decode_ts\n"


def fila(nombre, ts, valido="SI", nota=""):
    return "faseN3-v1,7,%s,SLOTS,2026-10-28 10:00:00,flags,3.0,%s,%s,%s\n" % (
        nombre, valido, nota, ts)


def carpeta_mediana(nombre, ancla, np2, fin,invalida=True):
    d = os.path.join(BASE, nombre)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "faseN3-resultados.csv"), "w", encoding="utf-8") as f:
        f.write(CSV_HEAD)
        f.write(fila("N3-ANCLA", ancla))
        f.write(fila("N3-NP2", np2))
        f.write(fila("N3-ANCLA-FIN", fin))
        if invalida:
            f.write(fila("N3-NP2", "99.9", valido="NO", nota="muerta de noche"))
    return d


B1 = carpeta_mediana("faseN3", 17.44, 21.41, 17.74)      # +22.8%
B2 = carpeta_mediana("faseN3-np2-b2", 17.50, 21.30, 17.60)  # +21.7%
B3 = carpeta_mediana("faseN3-np2-b3", 17.60, 21.60, 17.70)  # +22.7%
os.makedirs(os.path.join(B1, "logs-config"), exist_ok=True)
with open(os.path.join(B1, "logs-config", "12-NOCACHE.log"), "w",
          encoding="utf-8") as f:
    f.write("cache_reuse is not supported (exit 24055)\nrestored nada aqui\n")

ESTADO = os.path.join(BASE, "campana-estado.json")
INFORME = os.path.join(BASE, "campana-INFORME.md")


def rutas(**kw):
    a = args(**kw)
    return a, cam._rutas(a), cam.leer_estado(ESTADO)


# ================= U: piezas puras ==========================================

check("U01 SANITY_PROMPTS son %d y todos con carne" % cam.SANITY_TOTAL,
      len(cam.SANITY_PROMPTS) == 20 and all(len(t) > 5 for _, t in cam.SANITY_PROMPTS))
check("U02 hay tool-calling y trampa en los prompts",
      any("herramienta" in t for _, t in cam.SANITY_PROMPTS)
      and any("2030" in t for _, t in cam.SANITY_PROMPTS))

# autenticadores del hito N2 PINADOS (contra RUTAS.md L738 / N2 s18)
check("U03 bytes del hito pinnados", cam.MODELO_NUEVO_BYTES == 14069266720,
      str(cam.MODELO_NUEVO_BYTES))
check("U04 SHA256 del hito pinnado",
      cam.MODELO_NUEVO_SHA == "36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012"
      "e3d9e2495a90e7a7150", cam.MODELO_NUEVO_SHA[:8] + "...")
check("U05 nombre del archivo objetivo",
      cam.MODELO_NUEVO_NOMBRE == "Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf")

d1 = cam.cosechar_carpeta(B1)
check("U06 cosecha: 3 validas, muerta ignorada",
      d1 and d1["total_validas"] == 3 and len(d1["np2"]) == 1
      and abs(d1["np2"][0] - 21.41) < 1e-9)
check("U07 carpeta sin CSV -> None", cam.cosechar_carpeta(os.path.join(BASE, "nope")) is None)

v, det = cam.mediana_np2([("b1", d1), ("b2", cam.cosechar_carpeta(B2)),
                          ("b3", cam.cosechar_carpeta(B3))])
check("U08 mediana de 3 -> GO", v == "GO", "; ".join(det)[:80])
check("U09 deltas por ancla propia (~22.8/21.7/22.7)",
      any("22.8" in x for x in det) and any("21.7" in x for x in det)
      and any("22.7" in x for x in det))
check("U10 bookend estable anotado", any("ESTABLE" in x for x in det))

v2, _ = cam.mediana_np2([("solo", d1)])
check("U11 con 1 carpeta -> INCOMPLETO", v2 == "INCOMPLETO")

carpeta_nogo = carpeta_mediana("faseN3-nogo", 17.44, 17.96, 17.74)  # +3.0%
v3, _ = cam.mediana_np2([("a", cam.cosechar_carpeta(carpeta_nogo)),
                         ("b", cam.cosechar_carpeta(carpeta_nogo)),
                         ("c", cam.cosechar_carpeta(carpeta_nogo))])
check("U12 +3%% constante -> NO-GO", v3 == "NO-GO", v3)
carpeta_dudo = carpeta_mediana("faseN3-dudo", 17.44, 19.18, 17.74)  # +10.0%
v4, _ = cam.mediana_np2([("a", cam.cosechar_carpeta(carpeta_dudo)),
                         ("b", cam.cosechar_carpeta(carpeta_dudo)),
                         ("c", cam.cosechar_carpeta(carpeta_dudo))])
check("U13 +10%% constante -> DUDOSO", v4 == "DUDOSO", v4)

cfg = cam.leer_config(FAKE_CONFIG)
check("U14 leer_config: FLAGS_BASE y GANADORAS",
      cfg.get("FLAGS_GANADORAS") == "-ub 1024 -b 4096" and "-cmoe" in cfg["FLAGS_BASE"])

try:
    cam.fatal("prueba de caida")
    check("U15 fatal sale SystemExit", False)
except SystemExit as e:
    check("U15 fatal sale rc=2", e.code == 2)

# informe append-only
cam.informe(INFORME, "primerA", ["- a1"])
cam.informe(INFORME, "segundaB", ["- b1"])
txt = open(INFORME, encoding="utf-8").read()
check("U16 informe append-only conserva ambas",
      "primerA" in txt and "segundaB" in txt and txt.index("primerA") < txt.index("segundaB"))

# verificar_descarga con hash de verdad (pequeno, esperado pasado por parametro)
peque = os.path.join(DIR, "peque.bin")
contenido = b"APEX" * 1024
with open(peque, "wb") as f:
    f.write(contenido)
sha_peque = hashlib.sha256(contenido).hexdigest()
ok, lineas = cam.verificar_descarga(peque, sha_peque, len(contenido))
check("U17 verificar_descarga ok con hash real", ok and any("[OK]" in l for l in lineas))
ok2, lineas2 = cam.verificar_descarga(peque, "0" * 64, len(contenido))
check("U18 hash distinto -> FALLO certificado",
      not ok2 and any("SHA256" in l for l in lineas2))
ok3, lineas3 = cam.verificar_descarga(peque, sha_peque, 999)
check("U19 bytes distintos -> FALLO antes de hashear",
      not ok3 and any("bytes" in l for l in lineas3))


# GGUF fabricado a bytes
def gguf_falso(con_nextn=True):
    out = b"GGUF" + struct.pack("<I", 3) + struct.pack("<Q", 0)  # version, tensores

    def cad(s):
        b = s.encode("utf-8")
        return struct.pack("<Q", len(b)) + b

    kvs = [("general.architecture", 8, cad("qwen35moe")),
           ("general.name", 8, cad("qwen35moe-falso")),
           ("qwen35moe.block_count", 4, struct.pack("<I", 256)),
           ("qwen35moe.expert_count", 4, struct.pack("<I", 256)),
           ("qwen35moe.expert_used_count", 4, struct.pack("<I", 8))]
    if con_nextn:
        kvs.append(("qwen35moe.nextn.layer_count", 4, struct.pack("<I", 1)))
    out += struct.pack("<Q", len(kvs))
    for clave, tipo, valor in kvs:
        out += cad(clave) + struct.pack("<I", tipo) + valor
    return out + b"\x00" * 512  # padding: el parser solo lee cabecera


RUTA_GGUF = os.path.join(DIR, "falso.gguf")
with open(RUTA_GGUF, "wb") as f:
    f.write(gguf_falso(con_nextn=True))
meta, nextn, lineas_g = cam.verificar_gguf(RUTA_GGUF)
check("U20 parser GGUF: nextn detectado", meta is not None and nextn, str(nextn))
check("U21 parser GGUF: 256/8 y block_count",
      any("block_count = 256" in l for l in lineas_g)
      and any("expert_used_count = 8" in l for l in lineas_g))
RUTA_GGUF2 = os.path.join(DIR, "falso2.gguf")
with open(RUTA_GGUF2, "wb") as f:
    f.write(gguf_falso(con_nextn=False))
_, nextn2, _ = cam.verificar_gguf(RUTA_GGUF2)
check("U22 sin nextn -> AUSENTE (plan B, no fatal)", nextn2 == [])

print("")
print("== E2E: puertas, cirugia P2, cierre N3, pasos guiados ==")

# P2 sin p1 -> FATAL (puerta)
a, r, e = rutas()
try:
    cam.paso2(a, r, e)
    check("E01 p2 sin p1 = FATAL", False)
except SystemExit:
    check("E01 p2 sin p1 = FATAL con pista de puerta", True)

# P1 --sin-corridas sobre las 3 carpetas -> GO
a, r, e = rutas(b1=B1, b2=B2, b3=B3)
rc = cam.paso1(a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("E02 p1 cosecha -> veredicto GO en estado",
      rc == 0 and est["pasos"]["1"]["estado"] == "GO")
check("E03 informe trae P1", "P1 mediana" in open(INFORME, encoding="utf-8").read())

# P2 con confirmacion escrita -> PROMOVIDA + backup
builtins.input = lambda *a, **k: "PROMOVER"
a, r, e = rutas()
rc = cam.paso2(a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
cfg2 = cam.leer_config(FAKE_CONFIG)
backups = [f for f in os.listdir(BASE) if f.startswith("config.txt.bak-campana-p2")]
check("E04 p2 promueve: -np 2 en config", rc == 0
      and cfg2["FLAGS_BASE"].strip().endswith("-np 2"))
check("E05 backup creado y estado PROMOVIDA",
      len(backups) == 1 and est["pasos"]["2"]["estado"] == "PROMOVIDA")

# P2 idempotente
rc = cam.paso2(a, r, e)
backups2 = [f for f in os.listdir(BASE) if f.startswith("config.txt.bak-campana-p2")]
check("E06 p2 idempotente (sin backup nuevo)",
      rc == 0 and len(backups2) == 1)

# P2 revert byte-a-byte
builtins.input = lambda *a, **k: "PROMOVER"
a, r, e = rutas(revert=True)
rc = cam.paso2(a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("E07 revert restaura byte-a-byte",
      rc == 0 and open(FAKE_CONFIG, "rb").read() == ORIGINAL_CONFIG
      and est["pasos"]["2"]["estado"] == "REVERTIDA")

# volver a promover (para el resto del flujo)
builtins.input = lambda *a, **k: "PROMOVER"
a, r, e = rutas()
cam.paso2(a, r, e)

# P3 sin server -> FATAL; veredicto invalido -> FATAL
a, r, e = rutas()
try:
    cam.paso3(a, r, e)
    check("E08 p3 sin server = FATAL", False)
except SystemExit:
    check("E08 p3 sin server = FATAL (health)", True)
try:
    cam.paso3(args(veredicto="MEH"), r, e)
    check("E09 veredicto raro = FATAL", False)
except SystemExit:
    check("E09 veredicto raro = FATAL", True)

# P3 veredicto FALLA -> N3 no cerrado; OK -> cerrado
a, r, e = rutas(veredicto="FALLA")
cam.paso3(a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("E10 FALLA deja N3 abierto", est["n3"]["veredicto_sanity"] == "FALLA"
      and not est["n3"]["cerrado"])
a, r, e = rutas(veredicto="OK")
cam.paso3(a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("E11 OK cierra el N3", est["n3"]["cerrado"] is True)

# P4 puerta sin N3 (con estado viejo FALLA) ya cubierto por E10->E11;
# dry-run con cliente hf falso:
bin_falso = os.path.join(DIR, "hf")
with open(bin_falso, "w") as f:
    f.write("#!/bin/sh\necho fake-hf $@\n")
os.chmod(bin_falso, 0o755)
a, r, e = rutas(dry_run=True)
cam._binario_hf = lambda: [bin_falso]  # parche del taller
rc = cam.paso4(a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("E12 p4 dry-run: gate N3 pasa tras OK y no descarga",
      rc == 0 and json.load(open(ESTADO, encoding="utf-8"))["pasos"]
      .get("4", {}).get("estado") != "DESCARGADA")
cam._binario_hf = lambda: None
cam.gb_libres = lambda p: (100.0, 200.0)  # parche: disco grande para probar el cliente
try:
    cam.paso4(args(dir=BASE, fuerza=True), r, e)
    check("E13 p4 sin cliente hf = FATAL", False)
except SystemExit:
    check("E13 p4 sin cliente hf = FATAL con pista de pip", True)

# E13b/E13c — REPO_ALT desautenticado (verificacion de seguridad en vivo r37):
# el repo ALT sirve el archivo SIN MTP (otra huella) -> p4 debe rechazarlo
# ANTES de descargar, y --fuerza debe dejarlo escrito en el informe.
try:
    cam.paso4(args(dir=BASE, repo=cam.REPO_ALT), r, e)
    check("E13b p4 repo ALT sin --fuerza = FATAL", False)
except SystemExit:
    check("E13b p4 repo ALT sin --fuerza = FATAL (desautenticado 29-oct)", True)
rc = cam.paso4(args(dir=BASE, repo=cam.REPO_ALT, dry_run=True, fuerza=True), r, e)
con_fuerza_escrito = os.path.exists(r["informe"]) and (
    "repo ALT usado con --fuerza" in open(r["informe"], encoding="utf-8").read())
check("E13c p4 repo ALT con --fuerza + dry-run pasa y queda escrito",
      rc == 0 and con_fuerza_escrito)

# pasos guiados
a, r, e = rutas()
builtins.input = lambda *a, **k: "re-ancla 21.9 t/s con modelo nuevo"
cam.paso_guiado("7", a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("E14 guiado p7 registra nota",
      est["pasos"]["7"]["estado"] == "REGISTRADO" and "21.9" in est["pasos"]["7"]["nota"])
builtins.input = lambda *a, **k: ""
cam.paso_guiado("9", a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("E15 guiado p9 sin nota -> PENDIENTE", est["pasos"]["9"]["estado"] == "PENDIENTE")

# main: dispatch estado y paso desconocido
sys.argv = ["campana-10-pasos.py", "estado", "--dir", BASE]
check("E16 main estado rc=0", cam.main() == 0)
sys.argv = ["campana-10-pasos.py", "pX", "--dir", BASE]
check("E17 main paso raro rc=1", cam.main() == 1)
sys.argv = ["campana-10-pasos.py", "plan", "--dir", BASE]
check("E18 main plan rc=0", cam.main() == 0)

print("")
print("== E2E: humo P5 con server falso (los dos mundos + guardarrail) ==")

FAKE_MODEL = RUTA_GGUF  # ya es un GGUF falso con nextn
MODELS_DIR = os.path.join(BASE, "models")
os.makedirs(MODELS_DIR, exist_ok=True)
shutil.copy2(FAKE_MODEL, os.path.join(MODELS_DIR, cam.MODELO_NUEVO_NOMBRE))
_sha_modelo = hashlib.sha256(open(FAKE_MODEL, "rb").read()).hexdigest()
cam.MODELO_NUEVO_SHA = _sha_modelo            # parche del taller
cam.MODELO_NUEVO_BYTES = os.path.getsize(FAKE_MODEL)

FAKE_SERVER_OK = os.path.join(DIR, "server_ok.py")
with open(FAKE_SERVER_OK, "w") as f:
    f.write("""#!/usr/bin/env python3
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
PORT = 9931
a = sys.argv
if "--port" in a: PORT = int(a[a.index("--port") + 1])
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok":true}')
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        js = json.dumps({"choices": [{"message": {"content": "HUMO OK"}}],
                         "timings": {"predicted_per_second": 19.9}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(js)))
        self.end_headers(); self.wfile.write(js)
HTTPServer(("127.0.0.1", PORT), H).serve_forever()
""")
os.chmod(FAKE_SERVER_OK, 0o755)

FAKE_SERVER_DIE = os.path.join(DIR, "server_die.py")
with open(FAKE_SERVER_DIE, "w") as f:
    f.write("#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n")
os.chmod(FAKE_SERVER_DIE, 0o755)

# guardarrail: server ajeno vivo -> FATAL
puerto_h = esperando(None)
ajeno = subprocess.Popen([sys.executable, FAKE_SERVER_OK, "--port", str(puerto_h)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(30):
    if cam.health_ok(puerto_h):
        break
    time.sleep(0.2)
cfg_texto = CONFIG_ORIGINAL % FAKE_SERVER_OK
with open(FAKE_CONFIG, "w", encoding="utf-8") as f:
    f.write(cfg_texto)
a, r, e = rutas(puerto=puerto_h)
try:
    cam.paso5(a, r, e)
    check("E19 humo con server ajeno vivo = FATAL", False)
except SystemExit:
    check("E19 humo con server ajeno vivo = FATAL (guardarrail)", True)
ajeno.terminate(); ajeno.wait(timeout=10)

# mundo feliz: humo completo -> VERIFICADO-HUMO-OK
time.sleep(0.5)
a, r, e = rutas(puerto=esperando(None))
rc = cam.paso5(a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("E20 humo feliz -> VERIFICADO-HUMO-OK",
      rc == 0 and est["pasos"]["5"]["estado"] == "VERIFICADO-HUMO-OK")
check("E21 humo midio t/s del server falso",
      any("19.9" in l for l in est["pasos"]["5"]["detalle"]))
check("E22 nextn del GGUF falso detectado en estado",
      bool(est["pasos"]["5"]["nextn"]) and "nextn.layer_count" in str(est["pasos"]["5"]["nextn"]))

# mundo muerto: server que muere en la carga -> FATAL con forense
with open(FAKE_CONFIG, "w", encoding="utf-8") as f:
    f.write(CONFIG_ORIGINAL % FAKE_SERVER_DIE)
a, r, e = rutas(puerto=esperando(None))
try:
    cam.paso5(a, r, e)
    check("E23 server muerto en carga = FATAL", False)
except SystemExit:
    check("E23 server muerto en carga = FATAL con forense", True)

# P6: bat inexistente -> FATAL
a, r, e = rutas()
try:
    cam.paso6(a, r, e)
    check("E24 p6 sin bat = FATAL", False)
except SystemExit:
    check("E24 p6 sin bat = FATAL con pista --bat", True)

print("")
print("== R36: regresion de la revision ni-un-solo-bug (v1.1) ==")

# N01/N02: la puerta de p3 NO se bloquea si p2 se re-ejecuta (YA-PROMOVIDA)
builtins.input = lambda *a, **k: "PROMOVER"
a, r, e = rutas()
cam.paso2(a, r, e)   # promueve (la config del taller ya no trae -np)
cam.paso2(a, r, e)   # re-corrida -> rama idempotente
est = json.load(open(ESTADO, encoding="utf-8"))
check("N01 re-corrida de p2 deja YA-PROMOVIDA con backup vivo",
      est["pasos"]["2"]["estado"] == "YA-PROMOVIDA"
      and est["pasos"]["2"].get("backup"))
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        cam.paso3(a, r, e)   # sin server: debe frenar el HEALTH, no la puerta
except SystemExit:
    pass
check("N02 p3 tras YA-PROMOVIDA pasa la puerta (frena el health, no la puerta)",
      "puerta p2" not in buf.getvalue() and "server vivo" in buf.getvalue())

# N03: "-np 20" NO se confunde con "-np 2" (bug de substring de v1.0)
cfg20 = (CONFIG_ORIGINAL % "SERVER_PLACEHOLDER").replace(
    "-lm none", "-lm none -np 20")
with open(FAKE_CONFIG, "w", encoding="utf-8") as f:
    f.write(cfg20)
a, r, e = rutas()
rc = cam.paso2(a, r, e)
toks = cam.leer_config(FAKE_CONFIG)["FLAGS_BASE"].split()
check("N03 -np 20 no cuenta como promovida: rc 1 y config intacta",
      rc == 1 and toks[toks.index("-np") + 1] == "20")

# N04: un p2 cancelado queda escrito en el informe (memoria append-only)
with open(FAKE_CONFIG, "w", encoding="utf-8") as f:
    f.write(CONFIG_ORIGINAL % "SERVER_PLACEHOLDER")
inf_antes = open(INFORME, encoding="utf-8").read()
builtins.input = lambda *a, **k: "NO"
a, r, e = rutas()
rc = cam.paso2(a, r, e)
inf_despues = open(INFORME, encoding="utf-8").read()
toks = cam.leer_config(FAKE_CONFIG)["FLAGS_BASE"].split()
check("N04 p2 cancelado queda en el informe y config intacta",
      rc == 1 and "CANCELADA" in inf_despues and len(inf_despues) > len(inf_antes)
      and "-np" not in toks)

# N05: higiene: D: por debajo del minimo AVISA (v1.0 lo pintaba verde)
gb_viejo = cam.gb_libres
cam.gb_libres = lambda p: (5.0, 100.0)
buf = io.StringIO()
a, r, e = rutas()
with contextlib.redirect_stdout(buf):
    cam.paso1(a, r, e)
cam.gb_libres = gb_viejo
check("N05 disco bajo minimo AVISA en ambos (ya no sale verde)",
      buf.getvalue().count("por DEBAJO") == 2)

# N06: estado json viejo o roto no revienta
ruta_vieja = os.path.join(DIR, "estado-viejo.json")
with open(ruta_vieja, "w", encoding="utf-8") as f:
    f.write('{"version": "vieja"}')
e6 = cam.leer_estado(ruta_vieja)
check("N06 json viejo sin pasos/n3 -> claves reparadas",
      isinstance(e6.get("pasos"), dict) and isinstance(e6.get("n3"), dict))
with open(ruta_vieja, "w", encoding="utf-8") as f:
    f.write('["roto"]')
e6b = cam.leer_estado(ruta_vieja)
check("N06b json no-dict -> estado limpio",
      e6b.get("pasos") == {} and e6b.get("n3") == {})

# N07: helpers puros de la v1.1
check("N07 _envuelve_gui: shim .cmd de Windows va en cmd /c",
      cam._envuelve_gui(["C:\\x\\hf.cmd", "download"], es_windows=True)
      == ["cmd", "/c", "C:\\x\\hf.cmd", "download"])
check("N07b _envuelve_gui: exe/shell pasa igual",
      cam._envuelve_gui([bin_falso, "download"], es_windows=True)
      == [bin_falso, "download"])
check("N07c _quita_modelo_de_flags saca -m colado",
      cam._quita_modelo_de_flags(["-ngl", "99", "-m", "viejo.gguf", "-fa", "on"])
      == ["-ngl", "99", "-fa", "on"])
check("N07d _quita_modelo_de_flags saca --model",
      cam._quita_modelo_de_flags(["--model", "x.gguf", "-fa", "on"]) == ["-fa", "on"])
check("N07e flags limpias pasan intactas",
      cam._quita_modelo_de_flags(["-ngl", "99", "-fa", "on"]) == ["-ngl", "99", "-fa", "on"])

# N08: paleta del estado: YA-PROMOVIDA no es alarma roja
check("N08 YA-PROMOVIDA es verde; NO-GO/REVERTIDA amarillos; FALLO rojo",
      "YA-PROMOVIDA" in cam.VERDES_ESTADO
      and "NO-GO" in cam.AMARILLOS_ESTADO and "REVERTIDA" in cam.AMARILLOS_ESTADO
      and "FALLO-CERTIFICADO" not in cam.AMARILLOS_ESTADO)

# N09: el veredicto del juez ACTUALIZA pasos["3"] (no espera eterna)
a, r, e = rutas(veredicto="OK")
cam.paso3(a, r, e)
est = json.load(open(ESTADO, encoding="utf-8"))
check("N09 veredicto OK queda en pasos['3'] y cierra N3",
      est["pasos"]["3"]["estado"] == "OK" and est["n3"]["cerrado"] is True)

# N10: doble click sin argumentos espera un Enter (y EOF no revienta)
argv_viejo, input_viejo = sys.argv, builtins.input
pausas = []


def _input_pausa(*a, **k):
    pausas.append(1)
    raise EOFError()


sys.argv = ["campana-10-pasos.py"]
builtins.input = _input_pausa
cam._pausa_doble_click(es_tty=True)
sys.argv = ["campana-10-pasos.py", "estado"]
cam._pausa_doble_click(es_tty=True)
sys.argv = argv_viejo
builtins.input = input_viejo
check("N10 doble click espera Enter, EOF no revienta y con args no molesta",
      len(pausas) == 1)

# N14: Ctrl+C durante la corrida del barrido -> pausa limpia (rc 130)
_rc_llamadas = []


def _call_falso(cmd):
    _rc_llamadas.append(cmd)
    raise KeyboardInterrupt()


call_viejo = cam.subprocess.call
cam.subprocess.call = _call_falso
builtins.input = lambda *a, **k: "EJECUTAR"
a, r, e = rutas(sin_corridas=False)
buf = io.StringIO()
rc = None
with contextlib.redirect_stdout(buf):
    try:
        rc = cam.paso1(a, r, e)
    except KeyboardInterrupt:
        rc = "TRACEBACK"
cam.subprocess.call = call_viejo
check("N14 Ctrl+C en la corrida -> rc 130 limpio (sin traceback)",
      rc == 130 and "INTERRUMPIDO" in buf.getvalue() and len(_rc_llamadas) == 1)

# N11: el forense del humo es ACUMULATIVO (nada se pisa entre intentos).
# Cada humo lanza SU PROPIO server (RUTA_SERVER) en un puerto LIBRE: el
# guardarrail de la casa exige que el puerto este libre antes de arrancar.
with open(FAKE_CONFIG, "w", encoding="utf-8") as f:
    f.write(CONFIG_ORIGINAL % FAKE_SERVER_OK)
a, r, e = rutas(puerto=esperando(None))
cam.paso5(a, r, e)
a, r, e = rutas(puerto=esperando(None))
cam.paso5(a, r, e)
log_txt = open(os.path.join(BASE, "campana-humo.log"), encoding="utf-8").read()
check("N11 forense del humo acumulativo (4 intentos: E20+E23+N11x2)",
      log_txt.count("===== intento de humo") == 4)

# N12: re-corrida del sanity archiva el RESUMEN anterior (evidencia no se pisa)
puerto_h2 = esperando(None)
srv2 = subprocess.Popen([sys.executable, FAKE_SERVER_OK, "--port", str(puerto_h2)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(30):
    if cam.health_ok(puerto_h2):
        break
    time.sleep(0.2)
a, r, e = rutas(puerto=puerto_h2, tag="n12")
cam.paso3(a, r, e)
cam.paso3(a, r, e)
carp_s = os.path.join(BASE, "campana-sanity-n12")
res = sorted(f for f in os.listdir(carp_s) if f.startswith("RESUMEN"))
check("N12 2a corrida del mismo tag archiva el RESUMEN anterior",
      len(res) == 2 and res[0].startswith("RESUMEN-") and res[-1] == "RESUMEN.md")
srv2.terminate()
srv2.wait(timeout=10)

# N13: el repo alternativo (mismo archivo y SHA) esta documentado
check("N13 REPO_ALT presente y distinto del default",
      cam.REPO_ALT == "unsloth/Qwen3.6-35B-A3B-GGUF" and cam.REPO_ALT != cam.REPO_DEFAULT)

print("")
if ok_fallos:
    print(cam.red("BATERIA campana: %d/%d FALLOS -> %s"
                  % (len(ok_fallos), n_checks[0], ", ".join(ok_fallos))))
    sys.exit(1)
print(cam.green("BATERIA campana: TODO VERDE (%d checks: U01-U22 + E01-E24 + N01-N14)"
                % n_checks[0]))
shutil.rmtree(DIR, ignore_errors=True)
sys.exit(0)
