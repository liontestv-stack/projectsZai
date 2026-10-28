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
import hashlib
import importlib.util
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


def check(nombre, cond, detalle=""):
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
if ok_fallos:
    print(cam.red("BATERIA campana: %d FALLOS -> %s" % (len(ok_fallos), ", ".join(ok_fallos))))
    sys.exit(1)
print(cam.green("BATERIA campana: TODO VERDE (38 checks: U01-U22 + E01-E24)"))
shutil.rmtree(DIR, ignore_errors=True)
sys.exit(0)
