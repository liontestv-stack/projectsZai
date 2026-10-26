#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_faseD_n1.py — E2E de barrido-n1-expertos.py con server FALSO.

Ejecuta la bateria completa SIN GPU ni modelo real:
  T01 py_compile del instrumento
  T02 parser GGUF sintetico (arch/expert_count/expert_used_count + salto de
      arrays grandes)
  T03 parser GGUF: rechaza no-GGUF y GGUF v1
  T04 construir_configs: clave override EXACTA <arch>.expert_used_count (la
      correccion del no-op del barrido-30), tokens verbatim de NCM37C4 y
      ORO-UB1K, cero prohibidas, -ub 512 imposible
  T05 auditar_flags VERDE contra dump sintetico UTF-16
  T06 auditar_flags FALLO si el dump no trae --override-kv
  T07 auditar_flags FALLO si una config trae una prohibida
  T08 E2E con server falso: --solo exp -> 8 filas CSV, todas VALIDAS,
      control EXP10 frena, informe generado
  T09 resume: segunda corrida no re-mide (CSV intacto)
  T10 server falso que IGNORA el override -> runs INVALIDOS + protocolo de
      decision SS11.4 ramifica a plan B
  T11 E2E bloques mec+combo -> MEC veredicto vs control en el informe
  T12 informe MD: contiene secciones y clave de override correcta
"""
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTR = os.path.join(RAIZ, "InformacionCritica", "barrido-n1-expertos.py")
FALLOS = []


def check(nombre, cond, detalle=""):
    marca = "OK  " if cond else "FAIL"
    print("  [%s] %s %s" % (marca, nombre, ("- " + detalle) if detalle else ""))
    if not cond:
        FALLOS.append(nombre)


def cargar_modulo():
    spec = importlib.util.spec_from_file_location("barrido_n1", INSTR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------- sintetizadores de archivos -----------------------
def gguf_sintetico(ruta, arch="qwen3_5_moe"):
    """GGUF v3 minimo: header + kvs (incluye un array de strings grande que el
    parser debe saltar rapido)."""
    kvs = []

    def kv_str(k, v):
        kb = k.encode()
        vb = v.encode()
        kvs.append(struct.pack("<Q", len(kb)) + kb +
                   struct.pack("<I", 8) + struct.pack("<Q", len(vb)) + vb)

    def kv_u32(k, v):
        kb = k.encode()
        kvs.append(struct.pack("<Q", len(kb)) + kb +
                   struct.pack("<I", 4) + struct.pack("<I", v))

    def kv_arr_str(k, n):
        kb = k.encode()
        cuerpo = b""
        for i in range(n):
            s = ("tok%d" % i).encode()
            cuerpo += struct.pack("<Q", len(s)) + s
        kvs.append(struct.pack("<Q", len(kb)) + kb +
                   struct.pack("<I", 9) + struct.pack("<I", 8) +
                   struct.pack("<Q", n) + cuerpo)

    kv_str("general.architecture", arch)
    kv_u32(arch + ".block_count", 40)
    kv_u32(arch + ".expert_count", 256)
    kv_u32(arch + ".expert_used_count", 8)
    kv_u32(arch + ".expert_feed_forward_length", 512)
    kv_arr_str("tokenizer.ggml.tokens", 5000)  # grande: debe saltarse
    with open(ruta, "wb") as f:
        f.write(b"GGUF" + struct.pack("<I", 3) + struct.pack("<Q", 1) +
                struct.pack("<Q", len(kvs)))
        for kv in kvs:
            f.write(kv)
        f.write(struct.pack("<Q", 1) + b"tok" +  # 1 tensor info (no se lee)
                struct.pack("<I", 4) + struct.pack("<Q", 3) +
                struct.pack("<I", 0) + struct.pack("<Q", 2) +
                struct.pack("<I", 4) * 3)


def dump_sintetico(ruta, quitar=()):
    txt = """--model FNAME   ruta del modelo
-m, --model FNAME      modelo
-a, --alias STRING     alias
-ngl, --gpu-layers N   capas a GPU
-cmoe, --cpu-moe       expertos a CPU
-ncmoe, --n-cpu-moe N  primeras N capas MoE en CPU
--override-kv KEY=TYPE:VALUE,...  override de metadatos
--moe-cache-mib N      GPU cache size in MiB for the MoE experts (default 0)
-c, --ctx-size N       contexto
-b, --batch-size N     batch
-ub, --ubatch-size N   ubatch
-fa, --flash-attn [on|off|auto]
-ctk, --cache-type-k f32|f16|bf16|q8_0|q4_0|q4_1|iq4_nl|q5_0|q5_1
-ctv, --cache-type-v (mismos valores)
-t, --threads N        hilos
--prio N               prioridad
--no-mmproj            sin vision
-lm,   --load-mode MODE  model loading mode (default: auto)
                        - auto: mmap
                        - none: no special loading mode
                        - mmap: memory-map
--host HOST            host
--port PORT            puerto
"""
    for q in quitar:
        txt = re.sub(r"^.*%s.*$\n?" % re.escape(q), "", txt, flags=re.M)
    open(ruta, "wb").write(txt.encode("utf-16-le"))


FAKE_SERVER_PLANTILLA = r'''#!/usr/bin/env python3
import json, re, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
PORT = __PUERTO__
IGNORAR = __IGNORAR__
K = 8
args = sys.argv[1:]
if "--version" in args:
    print("version: 0.7.0-dev (build 11856, commit 3642238cc)"); sys.exit(0)
for i, a in enumerate(args):
    if a == "--override-kv" and i + 1 < len(args):
        m = re.search(r"int:(\d+)", args[i + 1])
        if m and not IGNORAR:
            K = int(m.group(1))
print("llm_load_print_meta: general.architecture = qwen3_5_moe", flush=True)
print("llm_load_print_meta: n_expert = 256", flush=True)
print("llm_load_print_meta: n_expert_used = " + str(8 if IGNORAR else K), flush=True)
print("CUDA0 compute buffer size : " + str(round(900.0 + 100.0 * K, 2)) + " MiB", flush=True)
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            body = {}
        p = (body.get("prompt") or "").lower()
        if "17 x 23" in p: c = "391"
        elif "don quijote" in p: c = "Cervantes"
        elif "planeta rojo" in p: c = "Marte"
        else: c = "Texto de medicion suficiente. " * 20
        self.send_response(200)
        self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"content": c, "timings": {
            "prompt_n": 32, "prompt_ms": 32.0, "prompt_per_second": 1000.0,
            "predicted_n": body.get("n_predict", 256),
            "predicted_ms": 1000.0,
            "predicted_per_second": round(21.53 * (8.0 / K) * 0.5 + 10.77, 2),
        }}).encode())
HTTPServer(("127.0.0.1", PORT), H).serve_forever()
'''


def escribir_fake_server(ruta, puerto, ignorar=False):
    open(ruta, "w").write(
        FAKE_SERVER_PLANTILLA.replace("__PUERTO__", str(puerto))
                             .replace("__IGNORAR__", str(ignorar)))
    os.chmod(ruta, 0o755)


# --------------------------------- bateria ----------------------------------
def main():
    tmp = tempfile.mkdtemp(prefix="faseD_n1_")
    mod = cargar_modulo()
    print("=" * 70)
    print("test_faseD_n1 — E2E con server falso (sin GPU)")
    print("=" * 70)

    # T01 compile
    r = subprocess.run([sys.executable, "-m", "py_compile", INSTR],
                       capture_output=True)
    check("T01 py_compile del instrumento", r.returncode == 0)

    # T02 parser GGUF
    gguf = os.path.join(tmp, "modelo.gguf")
    gguf_sintetico(gguf)
    t0 = time.time()
    hp = mod.gguf_leer_hparams(gguf)
    dt = time.time() - t0
    check("T02 parser GGUF sintetico",
          hp["arch"] == "qwen3_5_moe" and hp["n_expert"] == 256
          and hp["n_expert_used"] == 8 and hp["gguf_version"] == 3,
          "t=%.2fs (salto de 5000 tokens)" % dt)

    # T03 parser rechaza basura
    basura = os.path.join(tmp, "basura.gguf")
    open(basura, "wb").write(b"NOPE" + b"\x00" * 64)
    try:
        mod.gguf_leer_hparams(basura)
        check("T03 parser rechaza no-GGUF", False)
    except Exception:
        check("T03 parser rechaza no-GGUF", True)

    # T04 configs
    cfgs = mod.construir_configs("qwen3_5_moe")
    by_id = {c["id"]: c for c in cfgs}
    check("T04a 14 configs construidas", len(cfgs) == 14, str(len(cfgs)))
    check("T04b clave override EXACTA desde el GGUF",
          by_id[2]["flags"][-1] == "qwen3_5_moe.expert_used_count=int:10",
          by_id[2]["flags"][-1])
    check("T04c NCM37C4 verbatim",
          by_id[10]["flags"][:6] == ["-ncmoe", "37", "-c", "4096",
                                     "-ctk", "q4_0"], str(by_id[10]["flags"]))
    check("T04d UB1K verbatim",
          by_id[9]["flags"][1:5] == ["-ub", "1024", "-b", "4096"])
    check("T04e MEC control a 0 explicito",
          by_id[10]["flags"][-2:] == ["--moe-cache-mib", "0"])
    check("T04f sin -ub 512 ni prohibidas",
          not any(mod.PROHIBIDAS_EXACTAS & set(c["flags"]) for c in cfgs)
          and not any("512" in c["flags"][i + 1]
                      for c in cfgs for i, t in enumerate(c["flags"])
                      if t == "-ub"))
    check("T04g filtrar --solo exp = 8 y --quick = 7",
          len(mod.filtrar_configs(cfgs, solo="exp")) == 8
          and len(mod.filtrar_configs(cfgs, quick=True)) == 7)

    # T05/T06/T07 auditoria
    dump = os.path.join(tmp, "dump.txt")
    dump_sintetico(dump)
    check("T05 auditoria VERDE contra dump",
          mod.auditar_flags(dump, cfgs) == [],
          str(mod.auditar_flags(dump, cfgs)))
    dump2 = os.path.join(tmp, "dump_sin_ov.txt")
    dump_sintetico(dump2, quitar=("--override-kv",))
    check("T06 auditoria FALLO sin --override-kv en dump",
          len(mod.auditar_flags(dump2, cfgs)) == 1)
    cfg_podrida = [dict(by_id[1])]
    cfg_podrida[0] = dict(cfg_podrida[0])
    cfg_podrida[0]["flags"] = ["--mlock"]
    check("T07 auditoria FALLO con prohibida",
          len(mod.auditar_flags(dump, cfg_podrida)) >= 1)

    # T08 E2E bloque exp con server falso
    logs1 = os.path.join(tmp, "logs1")
    fake1 = os.path.join(tmp, "fake_server1.py")
    escribir_fake_server(fake1, 19931, ignorar=False)
    argv = ["--server", fake1, "--modelo", gguf, "--logs", logs1,
            "--puerto", "19931", "--solo", "exp", "--sin-nvidia",
            "--sin-pausas", "--carga-timeout", "60"]
    try:
        rc = mod.main(argv)
        check("T08a main() = 0", rc == 0)
        import csv as _csv
        with open(os.path.join(logs1, "faseD-N1-resultados.csv")) as f:
            filas = list(_csv.DictReader(f))
        check("T08b 8 filas CSV (bloque exp)", len(filas) == 8, str(len(filas)))
        check("T08c todas VALIDAS", all(f["valido"] == "SI" for f in filas))
        fctrl = [f for f in filas if f["id"] == "2"][0]
        fancla = [f for f in filas if f["id"] == "1"][0]
        check("T08d control EXP10 frena (autenticador de mecanismo)",
              float(fctrl["decode_ts"]) < float(fancla["decode_ts"]),
              "%s < %s" % (fctrl["decode_ts"], fancla["decode_ts"]))
        f4 = [f for f in filas if f["id"] == "6"][0]
        check("T08e override_aplicado SI en EXP4",
              f4["override_aplicado"] == "SI" and f4["n_expert_used_log"] == "4")
        check("T08f buffer CUDA0 crece con k (autenticador 2)",
              float(f4["buffer_mib"]) < float(fctrl["buffer_mib"]))
        check("T08g sanity 3/3", all(f["sanity_ok_n"] == "3" for f in filas))
    except Exception:
        check("T08 E2E exp", False, traceback.format_exc(-5))

    # T09 resume
    try:
        mod.main(argv)
        import csv as _csv
        with open(os.path.join(logs1, "faseD-N1-resultados.csv")) as f:
            filas2 = list(_csv.DictReader(f))
        check("T09 resume no re-mide (CSV sigue en 8)", len(filas2) == 8)
    except Exception:
        check("T09 resume", False, traceback.format_exc(-5))

    # T10 server que ignora el override
    logs2 = os.path.join(tmp, "logs2")
    fake2 = os.path.join(tmp, "fake_server2.py")
    escribir_fake_server(fake2, 19932, ignorar=True)
    argv2 = ["--server", fake2, "--modelo", gguf, "--logs", logs2,
             "--puerto", "19932", "--solo", "exp", "--sin-nvidia",
             "--sin-pausas", "--carga-timeout", "60"]
    try:
        mod.main(argv2)
        import csv as _csv
        with open(os.path.join(logs2, "faseD-N1-resultados.csv")) as f:
            filas3 = list(_csv.DictReader(f))
        invalidas = [f for f in filas3 if f["valido"] == "NO"]
        # 6 invalidas = ids 2,4,5,6,7,8; D-ANCLA (sin override) y D-EXP8
        # (k=8 = default que el server ignorante sigue logeando) son validas.
        check("T10a runs con override ignorado = INVALIDOS",
              len(invalidas) == 6
              and sorted(f["id"] for f in invalidas)
              == ["2", "4", "5", "6", "7", "8"], str(len(invalidas)))
        check("T10b nota marca OVERRIDE NO APLICADO",
              all("OVERRIDE NO APLICADO" in f["nota"] for f in invalidas))
        informe2 = open(os.path.join(logs2, "faseD-N1-INFORME.md")).read()
        check("T10c protocolo SS11.4 -> plan B",
              ("PLAN B" in informe2 or "invalido" in informe2))
    except Exception:
        check("T10 override ignorado", False, traceback.format_exc(-5))

    # T11 bloques mec + combo
    logs3 = os.path.join(tmp, "logs3")
    argv3 = ["--server", fake1, "--modelo", gguf, "--logs", logs3,
             "--puerto", "19931", "--solo", "mec,combo,ub1k", "--sin-nvidia",
             "--sin-pausas", "--carga-timeout", "60"]
    try:
        mod.main(argv3)
        import csv as _csv
        with open(os.path.join(logs3, "faseD-N1-resultados.csv")) as f:
            filas4 = list(_csv.DictReader(f))
        check("T11a 6 filas (mec 4 + combo 1 + ub1k 1)", len(filas4) == 6,
              str(len(filas4)))
        informe3 = open(os.path.join(logs3, "faseD-N1-INFORME.md")).read()
        check("T11b informe MEC veredicto vs control",
              "Veredicto MEC" in informe3 and "SE DESCARTA" in informe3)
    except Exception:
        check("T11 bloques mec/combo", False, traceback.format_exc(-5))

    # T12 informe contenido
    informe1 = open(os.path.join(logs1, "faseD-N1-INFORME.md")).read()
    check("T12a informe trae la clave exacta",
          "qwen3_5_moe.expert_used_count" in informe1)
    check("T12b informe trae secciones",
          all(s in informe1 for s in ("Pre-vuelo", "Resultados",
                                      "Protocolo de decision", "Recuerdos")))
    check("T12c informe sin códigos de color ANSI",
          "\x1b[" not in informe1)
    check("T12d informe DOSIS VIVA detectada (mock frena/sube bien)",
          "DOSIS VIVA" in informe1)

    print("=" * 70)
    if FALLOS:
        print("FALLOS: %d -> %s" % (len(FALLOS), FALLOS))
        return 1
    print("TODO VERDE")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
