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
  T11 E2E bloques mec+combo+ot -> MEC veredicto vs control en el informe y
      run cruzado -ot evaluado (SS18)
  T12 informe MD: contiene secciones y clave de override correcta
  --- bateria v1.1 (regresiones de la auditoria tras el HTTP 400 real) ---
  T13 merge base+diff: el comando lanzado SIEMPRE trae -m/-ngl/--port y el
      diff al final (causa raiz del HTTP 400: v1.0 lanzaba solo el diff)
  T14 identidad: sin linea de modelo en el log -> config invalida (fantasma)
  T15 HTTP 400 con cuerpo capturado en la nota; el barrido SOBREVIVE (rc 0)
  T16 server que muere en la carga -> fila NO con exit code, barrido sigue
  T17 resume v1.1: las filas NO se re-miden, las SI se saltan
  T18 consola.log SIEMPRE sin ANSI aunque USE_COLOR este activo
  --- bateria v1.2 (regresiones de la auditoria de COBERTURA) ---
  T04a 15 configs (nace el bloque ot con la config 15 D-OT-CTRL)
  T04h la config 15 replica NCM37C4 con UNA flag -ot, sin -ncmoe, cache 0
  T11c el run cruzado se mide y el informe emite su veredicto COMPRENDIDO
  T19 buffer CUDA0 evaluado en el arbol de decision (SS12.6, 2a via)
  T20 delta_vs_ancla_pct llenado en el CSV (columna muerta de la v1.1)
"""
import csv
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
-ot, --override-tensor PATTERN=BUFTYPE,...  override tensor buffer type
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
-lv, --log-verbosity N  Set the verbosity threshold
--host HOST            host
--port PORT            puerto
"""
    for q in quitar:
        txt = re.sub(r"^.*%s.*$\n?" % re.escape(q), "", txt, flags=re.M)
    open(ruta, "wb").write(txt.encode("utf-16-le"))


FAKE_SERVER_PLANTILLA = r'''#!/usr/bin/env python3
import json, re, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
PORT_FIJO = __PUERTO__
IGNORAR = __IGNORAR__
MODO = "__MODO__"
MODELLINE = __MODELLINE__
SINLOG = __SINLOG__
PROPSMODE = __PROPSMODE__
FITLINE = __FITLINE__
THINKER = __THINKER__
RUIDO = __RUIDO__
K = 8
args = sys.argv[1:]
if "--version" in args:
    print("version: 0.7.0-dev (build 11856, commit 3642238cc)"); sys.exit(0)
MODEL = "(sin -m)"
PORT = PORT_FIJO
for i, a in enumerate(args):
    if a == "--override-kv" and i + 1 < len(args):
        m = re.search(r"int:(\d+)", args[i + 1])
        if m and not IGNORAR:
            K = int(m.group(1))
    if a in ("-m", "--model") and i + 1 < len(args):
        MODEL = args[i + 1]
    if a == "--port" and i + 1 < len(args):
        PORT = int(args[i + 1])
print("RECIBIDO: " + " ".join(args).replace(MODEL, "<modelo>"), flush=True)
if MODO == "muere":
    print("error: failed to load model: no existe", flush=True)
    sys.exit(1)
if MODELLINE:
    print("main: model  = " + MODEL, flush=True)
if not SINLOG:
    print("llm_load_print_meta: general.architecture = qwen3_5_moe", flush=True)
    print("llm_load_print_meta: n_expert = 256", flush=True)
    print("llm_load_print_meta: n_expert_used = " + str(8 if IGNORAR else K), flush=True)
    print("CUDA0 compute buffer size : " + str(round(900.0 + 100.0 * K, 2)) + " MiB", flush=True)
if FITLINE:
    print("W common_fit_params: failed to fit params to free device memory: n_gpu_layers already set by user to 99, abort", flush=True)
print("main: server is listening on http://127.0.0.1:" + str(PORT) + " - starting the main loop", flush=True)
POSTS = [0]
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200); self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        elif self.path == "/props" and PROPSMODE:
            body = json.dumps({"model_meta": {"qwen3_5_moe.expert_used_count": (8 if IGNORAR else K)}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            body = {}
        POSTS[0] += 1
        if MODO == "http400" and POSTS[0] <= 1:
            msg = b'{"error":{"message":"the request exceeds the available context size"}}'
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return
        p = (body.get("prompt") or "").lower()
        if THINKER and ("17 x 23" in p or "don quijote" in p or "planeta rojo" in p):
            c = "<think>\nrazonamiento largo que el probe corta sin cerrar"
        elif "17 x 23" in p: c = "391"
        elif "don quijote" in p: c = "Cervantes"
        elif "planeta rojo" in p: c = "Marte"
        else: c = "Texto de medicion suficiente. " * 20
        tps = round(21.53 * (8.0 / K) * 0.5 + 10.77, 2)
        if RUIDO:
            tps = round(tps * (1.18 if POSTS[0] % 2 else 1.0), 2)
        self.send_response(200)
        self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"content": c, "timings": {
            "prompt_n": 32, "prompt_ms": 32.0, "prompt_per_second": 1000.0,
            "predicted_n": body.get("n_predict", 256),
            "predicted_ms": 1000.0,
            "predicted_per_second": tps,
        }}).encode())
HTTPServer(("127.0.0.1", PORT), H).serve_forever()
'''


def escribir_fake_server(ruta, puerto, ignorar=False, modo="ok", modeline=True,
                         sinlog=False, propsmode=False, fitline=False,
                         thinker=False, ruido=False):
    open(ruta, "w").write(
        FAKE_SERVER_PLANTILLA.replace("__PUERTO__", str(puerto))
                             .replace("__IGNORAR__", str(ignorar))
                             .replace("__MODO__", modo)
                             .replace("__MODELLINE__", str(modeline))
                             .replace("__SINLOG__", str(sinlog))
                             .replace("__PROPSMODE__", str(propsmode))
                             .replace("__FITLINE__", str(fitline))
                             .replace("__THINKER__", str(thinker))
                             .replace("__RUIDO__", str(ruido)))
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
    check("T04a 18 configs construidas", len(cfgs) == 18, str(len(cfgs)))
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
          and len(mod.filtrar_configs(cfgs, quick=True)) == 7
          and len(mod.filtrar_configs(cfgs, solo="ot")) == 1
          and len(mod.filtrar_configs(cfgs, solo="combo2")) == 2
          and len(mod.filtrar_configs(cfgs, solo="anclafin")) == 1)
    check("T04h run cruzado -ot: UNA flag, sin -ncmoe, cache 0, igual KV",
          by_id[15]["familia"] == "OT"
          and by_id[15]["flags"].count("-ot") == 1
          and "exps=CPU" in " ".join(by_id[15]["flags"])
          and "CUDA0" in " ".join(by_id[15]["flags"])
          and "-ncmoe" not in by_id[15]["flags"]
          and "-ctk" in by_id[15]["flags"]
          and by_id[15]["flags"][-2:] == ["--moe-cache-mib", "0"],
          str(by_id[15]["flags"]))
    check("T04i v1.2.1: bookend id16 = CM solo y stacks combo2 = NCM+MEC+ov",
          by_id[16]["familia"] == "ANCLA-FIN" and by_id[16]["flags"] == ["-cmoe"]
          and by_id[17]["flags"] == ["-ncmoe", "37", "-c", "4096", "-ctk", "q4_0",
                                     "-ctv", "q4_0", "--moe-cache-mib", "768",
                                     "--override-kv",
                                     "qwen3_5_moe.expert_used_count=int:4"]
          and by_id[18]["flags"][9] == "1024"
          and "-cmoe" not in by_id[17]["flags"],
          str(by_id[17]["flags"]))

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
        check("T08h auth_via = LOG (via 1) en las filas de override",
              f4["auth_via"] == "LOG"
              and [f for f in filas if f["id"] == "1"][0]["auth_via"] == "",
              f4["auth_via"])
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

    # T11 bloques mec + combo + ot
    logs3 = os.path.join(tmp, "logs3")
    argv3 = ["--server", fake1, "--modelo", gguf, "--logs", logs3,
             "--puerto", "19931", "--solo", "mec,combo,ub1k,ot", "--sin-nvidia",
             "--sin-pausas", "--carga-timeout", "60"]
    try:
        mod.main(argv3)
        import csv as _csv
        with open(os.path.join(logs3, "faseD-N1-resultados.csv")) as f:
            filas4 = list(_csv.DictReader(f))
        check("T11a 7 filas (mec 4 + combo 1 + ub1k 1 + ot 1)",
              len(filas4) == 7, str(len(filas4)))
        informe3 = open(os.path.join(logs3, "faseD-N1-INFORME.md")).read()
        check("T11b informe MEC veredicto vs control (empate = EMPATA, "
              "no descartado)",
              "Veredicto MEC" in informe3 and "EMPATA" in informe3)
        check("T11c run cruzado -ot medido, evaluado y COMPRENDIDO",
              any(f["id"] == "15" and "-ot" in f["flags"] for f in filas4)
              and "RUN CRUZADO -ot" in informe3
              and "COMPRENDIDO" in informe3,
              "cruzado_en_informe=%s" % ("RUN CRUZADO -ot" in informe3))
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

    # T19/T20 (bateria v1.2): buffer CUDA0 evaluado + delta_vs_ancla_pct
    with open(os.path.join(logs1, "faseD-N1-resultados.csv")) as f:
        filas20 = list(csv.DictReader(f))
    check("T19 buffer CUDA0 evaluado en el arbol (SS12.6, 2a via)",
          "SS12.6" in informe1 and "2a via" in informe1)
    check("T20a delta_vs_ancla_pct vacio SOLO en el ancla",
          all((r["delta_vs_ancla_pct"] == "") == (r["id"] == "1")
              for r in filas20),
          str([(r["id"], r["delta_vs_ancla_pct"]) for r in filas20]))
    fexp4 = [r for r in filas20 if r["id"] == "6"][0]
    check("T20b delta de EXP4 positivo y numerico",
          float(fexp4["delta_vs_ancla_pct"]) > 0,
          fexp4["delta_vs_ancla_pct"])

    # T13 merge base+diff (causa raiz del HTTP 400 de la v1.0)
    try:
        log1 = open(os.path.join(logs1, "logs-config",
                                 "01-D-ANCLA.log")).read()
        rec = [l for l in log1.splitlines() if l.startswith("RECIBIDO: ")][0]
        check("T13a base+diff en el comando lanzado",
              "-m " in rec and "-ngl 99" in rec and "--port 19931" in rec
              and "-cmoe" in rec and "-fa on" in rec and "-lm none" in rec,
              rec[:130])
        with open(os.path.join(logs1, "faseD-N1-resultados.csv")) as f:
            filas_m = list(csv.DictReader(f))
        fancla_m = [r for r in filas_m if r["id"] == "1"][0]
        check("T13b CSV flags = comando completo, diff al final",
              fancla_m["flags"].startswith("-m ")
              and "-cmoe" in fancla_m["flags"]
              and fancla_m["flags"].index("-lm none")
                  < fancla_m["flags"].index("-cmoe"))
    except Exception:
        check("T13 merge base+diff", False, traceback.format_exc(-5))

    # T14 identidad: sin linea de modelo en el log -> config invalida
    try:
        logs4 = os.path.join(tmp, "logs4")
        fake4 = os.path.join(tmp, "fake_server4.py")
        escribir_fake_server(fake4, 19934, ignorar=False, modeline=False)
        argv4 = ["--server", fake4, "--modelo", gguf, "--logs", logs4,
                 "--puerto", "19934", "--solo", "exp", "--sin-nvidia",
                 "--sin-pausas", "--carga-timeout", "60"]
        rc4 = mod.main(argv4)
        with open(os.path.join(logs4, "faseD-N1-resultados.csv")) as f:
            filas14 = list(csv.DictReader(f))
        check("T14a fantasma detectado: 8 filas NO, rc 0",
              rc4 == 0 and len(filas14) == 8
              and all(r["valido"] == "NO" for r in filas14))
        check("T14b nota de identidad",
              all("NO menciona el modelo esperado" in r["nota"]
                  for r in filas14))
    except Exception:
        check("T14 identidad", False, traceback.format_exc(-5))

    # T15 HTTP 400 con cuerpo capturado (regresion exacta del desastre v1.0)
    try:
        logs5 = os.path.join(tmp, "logs5")
        fake5 = os.path.join(tmp, "fake_server5.py")
        escribir_fake_server(fake5, 19935, modo="http400")
        argv5 = ["--server", fake5, "--modelo", gguf, "--logs", logs5,
                 "--puerto", "19935", "--solo", "exp", "--sin-nvidia",
                 "--sin-pausas", "--carga-timeout", "60"]
        rc5 = mod.main(argv5)
        with open(os.path.join(logs5, "faseD-N1-resultados.csv")) as f:
            filas15 = list(csv.DictReader(f))
        check("T15a el barrido SOBREVIVE a un 400 (8 filas, rc 0)",
              rc5 == 0 and len(filas15) == 8,
              "rc=%s filas=%d" % (rc5, len(filas15)))
        check("T15b cuerpo del 400 capturado en la nota",
              all("HTTP 400" in r["nota"]
                  and "exceeds the available context size" in r["nota"]
                  for r in filas15), filas15[0]["nota"][:130])
        check("T15c informe generado igualmente",
              os.path.exists(os.path.join(logs5, "faseD-N1-INFORME.md")))
    except Exception:
        check("T15 http400", False, traceback.format_exc(-5))

    # T16 server que muere durante la carga
    try:
        logs6 = os.path.join(tmp, "logs6")
        fake6 = os.path.join(tmp, "fake_server6.py")
        escribir_fake_server(fake6, 19936, modo="muere")
        argv6 = ["--server", fake6, "--modelo", gguf, "--logs", logs6,
                 "--puerto", "19936", "--solo", "exp", "--sin-nvidia",
                 "--sin-pausas", "--carga-timeout", "60"]
        rc6 = mod.main(argv6)
        with open(os.path.join(logs6, "faseD-N1-resultados.csv")) as f:
            filas16 = list(csv.DictReader(f))
        check("T16a muerte en carga = 8 filas NO, rc 0",
              rc6 == 0 and len(filas16) == 8
              and all(r["valido"] == "NO" for r in filas16))
        check("T16b nota de carga fallida",
              all("carga fallida" in r["nota"] for r in filas16))
    except Exception:
        check("T16 muerte en carga", False, traceback.format_exc(-5))

    # T17 resume v1.1: filas NO se re-miden; filas SI se saltan
    try:
        fake7 = os.path.join(tmp, "fake_server7.py")
        escribir_fake_server(fake7, 19935, modo="ok")
        argv17 = ["--server", fake7, "--modelo", gguf, "--logs", logs5,
                  "--puerto", "19935", "--solo", "exp", "--sin-nvidia",
                  "--sin-pausas", "--carga-timeout", "60"]
        rc17 = mod.main(argv17)
        with open(os.path.join(logs5, "faseD-N1-resultados.csv")) as f:
            filas17 = list(csv.DictReader(f))
        check("T17a 8 filas NO re-medidas -> CSV con 16 filas",
              rc17 == 0 and len(filas17) == 16, str(len(filas17)))
        check("T17b las nuevas 8 quedan validas",
              all(r["valido"] == "SI" for r in filas17[8:]))
    except Exception:
        check("T17 resume de fallidas", False, traceback.format_exc(-5))

    # T18 consola.log sin ANSI aunque USE_COLOR este activo
    try:
        mod.USE_COLOR = True
        logs8 = os.path.join(tmp, "logs8")
        argv18 = ["--server", fake1, "--modelo", gguf, "--logs", logs8,
                  "--puerto", "19931", "--solo", "ub1k", "--sin-nvidia",
                  "--sin-pausas", "--carga-timeout", "60"]
        mod.main(argv18)
        cons = open(os.path.join(logs8, "faseD-N1-consola.log")).read()
        check("T18a consola.log sin ANSI (USE_COLOR on)", "\x1b[" not in cons)
        check("T18b consola.log con contenido", "CORRIDA" in cons)
    except Exception:
        check("T18 consola sin ANSI", False, traceback.format_exc(-5))
    finally:
        mod.USE_COLOR = False

    # ---- bateria v1.2.1: telemetria de la corrida real reproducida ----
    # T21 corrida COMPLETA (18 configs) + bookend D-ANCLA-FIN + 'vs k=8'
    try:
        logs9 = os.path.join(tmp, "logs9")
        argv21 = ["--server", fake1, "--modelo", gguf, "--logs", logs9,
                  "--puerto", "19931", "--sin-nvidia", "--sin-pausas",
                  "--carga-timeout", "60"]
        rc21 = mod.main(argv21)
        import csv as _csv
        with open(os.path.join(logs9, "faseD-N1-resultados.csv")) as f:
            filas21 = list(_csv.DictReader(f))
        check("T21a corrida completa = 18 filas", rc21 == 0 and len(filas21) == 18,
              "rc=%s filas=%d" % (rc21, len(filas21)))
        ffin = [f for f in filas21 if f["id"] == "16"][0]
        check("T21b bookend id16 valido y con delta",
              ffin["valido"] == "SI" and ffin["nombre"] == "D-ANCLA-FIN"
              and ffin["delta_vs_ancla_pct"] != "")
        informe21 = open(os.path.join(logs9, "faseD-N1-INFORME.md")).read()
        check("T21c informe con BOOKEND, 'vs k=8' y leyenda override",
              "BOOKEND" in informe21 and "vs k=8" in informe21
              and "Leyenda override" in informe21)
    except Exception:
        check("T21 corrida completa + bookend", False,
              traceback.format_exc(-5))

    # T22 SIN hparams en el log (b11856 real) -> via COMP comportamental
    try:
        logs10 = os.path.join(tmp, "logs10")
        fake10 = os.path.join(tmp, "fake_server10.py")
        escribir_fake_server(fake10, 19937, ignorar=False, sinlog=True)
        argv22 = ["--server", fake10, "--modelo", gguf, "--logs", logs10,
                  "--puerto", "19937", "--solo", "exp", "--sin-nvidia",
                  "--sin-pausas", "--carga-timeout", "60"]
        rc22 = mod.main(argv22)
        import csv as _csv
        with open(os.path.join(logs10, "faseD-N1-resultados.csv")) as f:
            filas22 = list(_csv.DictReader(f))
        f6 = [f for f in filas22 if f["id"] == "6"][0]
        f2 = [f for f in filas22 if f["id"] == "2"][0]
        f3 = [f for f in filas22 if f["id"] == "3"][0]
        check("T22a sin log: EXP4 autenticado COMP y EXP10 freno COMP",
              rc22 == 0 and f6["auth_via"] == "COMP"
              and f6["valido"] == "SI" and f2["auth_via"] == "COMP"
              and f2["valido"] == "SI",
              "f6=%s/%s f2=%s/%s" % (f6["auth_via"], f6["valido"],
                                     f2["auth_via"], f2["valido"]))
        check("T22b EXP8 (k=8) = DEFAULT y ancla sin via",
              f3["auth_via"] == "DEFAULT" and f3["valido"] == "SI"
              and [f for f in filas22 if f["id"] == "1"][0]["auth_via"] == "")
    except Exception:
        check("T22 via COMP", False, traceback.format_exc(-5))

    # T23 via PROPS: sin log pero /props expone el hparam tras override
    try:
        logs11 = os.path.join(tmp, "logs11")
        fake11 = os.path.join(tmp, "fake_server11.py")
        escribir_fake_server(fake11, 19938, ignorar=False, sinlog=True,
                             propsmode=True)
        argv23 = ["--server", fake11, "--modelo", gguf, "--logs", logs11,
                  "--puerto", "19938", "--solo", "exp", "--sin-nvidia",
                  "--sin-pausas", "--carga-timeout", "60"]
        mod.main(argv23)
        import csv as _csv
        with open(os.path.join(logs11, "faseD-N1-resultados.csv")) as f:
            filas23 = list(_csv.DictReader(f))
        f6 = [f for f in filas23 if f["id"] == "6"][0]
        check("T23 /props expone expert_used_count -> auth_via PROPS",
              f6["auth_via"] == "PROPS" and f6["override_aplicado"] == "PROPS"
              and f6["valido"] == "SI", f6["auth_via"])
    except Exception:
        check("T23 via PROPS", False, traceback.format_exc(-5))

    # T24 sin log + override IGNORADO + curva plana -> NO RESPONDE (no-op)
    try:
        logs12 = os.path.join(tmp, "logs12")
        fake12 = os.path.join(tmp, "fake_server12.py")
        escribir_fake_server(fake12, 19939, ignorar=True, sinlog=True)
        argv24 = ["--server", fake12, "--modelo", gguf, "--logs", logs12,
                  "--puerto", "19939", "--solo", "exp", "--sin-nvidia",
                  "--sin-pausas", "--carga-timeout", "60"]
        mod.main(argv24)
        import csv as _csv
        with open(os.path.join(logs12, "faseD-N1-resultados.csv")) as f:
            filas24 = list(_csv.DictReader(f))
        invalidas = [f for f in filas24 if f["valido"] == "NO"]
        check("T24a no-op silencioso: 6 invalidos por curva plana",
              len(invalidas) == 6
              and all("OVERRIDE NO RESPONDE" in f["nota"] for f in invalidas),
              str([f["id"] for f in invalidas]))
        f3 = [f for f in filas24 if f["id"] == "3"][0]
        check("T24b EXP8 sigue valido (DEFAULT)", f3["valido"] == "SI")
    except Exception:
        check("T24 no-op comportamental", False, traceback.format_exc(-5))

    # T25 fit benigno: 'already set by user' NO invalida (regresion v1.2)
    try:
        logs13 = os.path.join(tmp, "logs13")
        fake13 = os.path.join(tmp, "fake_server13.py")
        escribir_fake_server(fake13, 19940, fitline=True)
        argv25 = ["--server", fake13, "--modelo", gguf, "--logs", logs13,
                  "--puerto", "19940", "--solo", "ub1k", "--sin-nvidia",
                  "--sin-pausas", "--carga-timeout", "60"]
        mod.main(argv25)
        import csv as _csv
        with open(os.path.join(logs13, "faseD-N1-resultados.csv")) as f:
            filas25 = list(_csv.DictReader(f))
        f9 = filas25[0]
        check("T25 fit-benigno: valido SI con nota informativa",
              f9["valido"] == "SI" and "auto-fit declino" in f9["nota"],
              "%s | %s" % (f9["valido"], f9["nota"][:80]))
    except Exception:
        check("T25 fit benigno", False, traceback.format_exc(-5))

    # T26 sanity TRUNCADA (<think> sin cerrar) no es fallo de calidad
    try:
        logs14 = os.path.join(tmp, "logs14")
        fake14 = os.path.join(tmp, "fake_server14.py")
        escribir_fake_server(fake14, 19941, thinker=True)
        argv26 = ["--server", fake14, "--modelo", gguf, "--logs", logs14,
                  "--puerto", "19941", "--solo", "ub1k", "--sin-nvidia",
                  "--sin-pausas", "--carga-timeout", "60"]
        mod.main(argv26)
        import csv as _csv
        with open(os.path.join(logs14, "faseD-N1-resultados.csv")) as f:
            filas26 = list(_csv.DictReader(f))
        f9 = filas26[0]
        check("T26 truncada: 0 OK + 3T, nota de probe, valido SI",
              f9["sanity_ok_n"] == "0" and f9["sanity_trunc_n"] == "3"
              and f9["valido"] == "SI"
              and "truncadas" in f9["nota"]
              and "fallos reales" not in f9["nota"],
              "%s/%s/%s | %s" % (f9["sanity_ok_n"], f9["sanity_trunc_n"],
                                 f9["valido"], f9["nota"][:80]))
    except Exception:
        check("T26 sanity truncada", False, traceback.format_exc(-5))

    # T27 dispersion entre pasadas (outlier en dec 2-4) queda anotada
    try:
        logs15 = os.path.join(tmp, "logs15")
        fake15 = os.path.join(tmp, "fake_server15.py")
        escribir_fake_server(fake15, 19942, ruido=True)
        argv27 = ["--server", fake15, "--modelo", gguf, "--logs", logs15,
                  "--puerto", "19942", "--solo", "ub1k", "--sin-nvidia",
                  "--sin-pausas", "--carga-timeout", "60"]
        mod.main(argv27)
        import csv as _csv
        with open(os.path.join(logs15, "faseD-N1-resultados.csv")) as f:
            filas27 = list(_csv.DictReader(f))
        f9 = filas27[0]
        check("T27 dispersion x1.18 anotada en CSV y nota",
              f9["dispers_max_min"].startswith("1.1")
              and "dispersion alta" in f9["nota"],
              "%s | %s" % (f9["dispers_max_min"], f9["nota"][:80]))
    except Exception:
        check("T27 dispersion", False, traceback.format_exc(-5))

    print("=" * 70)
    if FALLOS:
        print("FALLOS: %d -> %s" % (len(FALLOS), FALLOS))
        return 1
    print("TODO VERDE")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
