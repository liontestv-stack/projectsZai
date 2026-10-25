#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
abrir-qwen-apex.py — Lanzador del modelo Qwen APEX-I-MINI para el build b11856
==============================================================================
Especifico para:
  servidor : D:\\llama.cpp\\llama-server.exe   (build 11856, commit 3642238cc)
  modelo   : D:\\ZLia\\models\\...APEX-I-MINI.gguf (14,273,277,376 B verificado HF)

FLAGS: solo usa flags auditadas contra el dump real del build nuevo
       (InformacionCritica/llama-flags-nuevo.txt, 122,440 B, re-auditoria
       2026-10-25). Nada inventado. --mlock/--no-mmap NO EXISTEN en este build
       (sustituidas por -lm; default auto = mmap, que es lo que este rig quiere).

MODOS:
  (default)      V1 base: -cmoe (todos los expertos en CPU, boot garantizado)
  --ncmoe N      V1 con -ncmoe N (expertos de las primeras N capas en CPU)
  --sweep        barrido automatico de -ncmoe midiendo t/s reales del server
  --mtp          V2: + --spec-type draft-mtp --spec-draft-n-max 2 (tras el sweep)
  --dry-run      imprime el comando exacto y sale (no lanza nada)

USO:
  py abrir-qwen-apex.py
  py abrir-qwen-apex.py --ncmoe 16
  py abrir-qwen-apex.py --sweep
  py abrir-qwen-apex.py --mtp --ncmoe 16
  py abrir-qwen-apex.py --dry-run --mtp
  py abrir-qwen-apex.py --preset coding   (sampling oficial Qwen3.6)

SAMPLING (v1.2): --preset think|coding|fast inyecta los parametros de
sampling OFICIALES de Qwen3.6 (card + generation_config, verificado
2026-10-25; doc: config-sampling-qwen36.md). Default: think.
VISION: sin --mmproj se pasa --no-mmproj (text-only, ahorra ~0.9 GB VRAM).

REQUISITOS: Python 3.8+ (solo stdlib), Windows 10/11.
Rutas y puerto sobreescribibles: env LLAMA_SERVER / LLAMA_MODEL o CLI.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

if sys.version_info < (3, 8):
    raise SystemExit("Se requiere Python 3.8 o superior.")

# ------------------------------------------------------------------ constantes
DEFAULT_SERVER = os.environ.get("LLAMA_SERVER", r"D:\llama.cpp\llama-server.exe")
DEFAULT_MODEL = os.environ.get(
    "LLAMA_MODEL",
    r"D:\ZLia\models\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf",
)
MODEL_SIZE_ESPERADO = 14273277376        # verificado via API HuggingFace (?blobs=true)
ALIAS = "apex35b"

DLLS_CRITICAS = [   # el exe es un launcher fino (9,216 B) — analisis PE 3-A.2
    "llama-server-impl.dll", "llama.dll", "ggml-cuda.dll", "libomp.dll",
    "cudart64_12.dll", "cublas64_12.dll", "cublasLt64_12.dll",
]

BUILD_PIN = "11856"     # b11856 / commit 3642238cc (auditado 2026-10-25)
PORT_DEFAULT = 9931     # dump nuevo: "--port PORT  port to listen (default: 9931)"

# Presets de sampling OFICIALES de Qwen3.6-35B-A3B (card oficial +
# generation_config.json, fetch 2026-10-25; doc: config-sampling-qwen36.md).
# Flags verbatim del dump b11856. El default del server (temp 0.80, top-k 40,
# min-p 0.05) NO es el optimo de este modelo -> siempre fijar preset.
PRESETS = {
    "think":  ["--temp", "1.0", "--top-k", "20", "--top-p", "0.95",
               "--min-p", "0.0", "--presence-penalty", "0.0"],
    "coding": ["--temp", "0.6", "--top-k", "20", "--top-p", "0.95",
               "--min-p", "0.0", "--presence-penalty", "0.0"],
    "fast":   ["--temp", "0.7", "--top-k", "20", "--top-p", "0.80",
               "--min-p", "0.0", "--presence-penalty", "1.5"],
}

PROBLEMAS = []


def problema(msg):
    PROBLEMAS.append(msg)
    print("  [FALLO] " + msg)


def aviso(msg):
    print("  [AVISO] " + msg)


def bien(msg):
    print("  [OK]    " + msg)


# ------------------------------------------------------------------ pre-flight
def preflight(args):
    print("=" * 70)
    print("FASE 0 — PRE-FLIGHT")
    print("=" * 70)
    exe = Path(args.server)
    modelo = Path(args.model)

    # 1) servidor
    if not exe.exists():
        problema("NO EXISTE el servidor: {}".format(exe))
        print("          (ruta nueva informada por el Director; si el binario sigue")
        print("           en bin-new: Move-Item D:\\llama.cpp\\bin-new\\* D:\\llama.cpp\\)")
        return False
    bien("servidor presente: {}".format(exe))

    # 2) DLLs criticas junto al exe (0xC0000135 si falta alguna)
    faltan = [d for d in DLLS_CRITICAS if not (exe.parent / d).exists()]
    if faltan:
        problema("falta(n) DLL critica(s) junto al exe: {}".format(", ".join(faltan)))
        print("          TODAS las DLLs del build deben vivir en la MISMA carpeta.")
        return False
    bien("7 DLLs criticas presentes junto al exe")

    # 3) version (LECCION 3-k: la version sale por STDERR -> combinar out+err)
    try:
        p = subprocess.run([str(exe), "--version"], capture_output=True, timeout=60)
        combined = (p.stdout.decode("utf-8", "replace") + "\n"
                    + p.stderr.decode("utf-8", "replace")).strip()
        linea = (combined.splitlines() or [""])[0]
        if p.returncode != 0 or not linea:
            problema("--version fallo (rc={}): {}".format(p.returncode, combined[:150]))
            return False
        bien("version: {}".format(linea))
        if BUILD_PIN not in combined:
            aviso("build DISTINTO al auditado (esperado build {} en el pin).".format(BUILD_PIN))
            aviso("las flags de este lanzador fueron auditadas contra el dump de b{}.".format(BUILD_PIN))
            if args.strict:
                problema("--strict: abortando por build distinto.")
                return False
    except Exception as ex:
        problema("no se pudo ejecutar --version: {}".format(ex))
        return False

    # 4) modelo (tamano byte-exacto; --force si es intencional)
    if not modelo.exists():
        problema("NO EXISTE el modelo: {}".format(modelo))
        return False
    real = modelo.stat().st_size
    if real != MODEL_SIZE_ESPERADO:
        aviso("tamano del modelo {} != verificado HF {}".format(real, MODEL_SIZE_ESPERADO))
        if not args.force:
            problema("tamano distinto al auditado. Si es intencional (--force), relanza.")
            return False
        aviso("--force: continuando con tamano distinto.")
    else:
        bien("modelo byte-exacto: {:,} B (14.27 GB)".format(real))

    # 5) recordatorio VRAM (medido 2026-10-25: ~963 MiB consumidos por escritorio)
    print()
    print("  RECUERDA: cerrar Firefox / Wallpaper Engine / Copilot ANTES de medir")
    print("  (~963 MiB de VRAM liberados; GTX 1650 solo tiene 4,095 MiB).")
    print("  El pagefile debe estar en el SSD (14.27 GB de pesos / 16 GB RAM).")
    return True


# ------------------------------------------------------------------ comando
def construir_comando(args, ncmoe=None, cmoe=False, mtp=None):
    """Devuelve la lista de argumentos para llama-server. Todo auditado."""
    c = [
        args.server,
        "-m", args.model,
        "-a", ALIAS,
        "-ngl", "99",
    ]
    if cmoe:
        c.append("-cmoe")                       # TODOS los expertos en CPU
    elif ncmoe is not None:
        c += ["-ncmoe", str(ncmoe)]             # primeros N layers de expertos en CPU
    c += [
        "-c", str(args.ctx),
        "-b", "2048",
        "-ub", "256",
        "-fa", args.fa,                         # on|off|auto (default on)
        "-ctk", args.ctk,
        "-ctv", args.ctv,
        "-t", str(args.threads),
        "--prio", "2",                          # high (dump: low -1 .. high 2)
    ]
    if mtp is not None:
        c += ["--spec-type", "draft-mtp",       # auditado: presente en b11856
              "--spec-draft-n-max", str(mtp)]   # 2 = mitigacion issue #23577
        if args.spec_p_min is not None:
            c += ["--spec-draft-p-min", str(args.spec_p_min)]
    if args.moe_cache_mib is not None:
        c += ["--moe-cache-mib", str(args.moe_cache_mib)]
    # --jinja NO se pasa: en b11856 va enabled por defecto (dump verbatim)
    c += PRESETS[args.preset]                  # sampling oficial Qwen3.6 (v1.2)
    if args.mmproj:
        c += ["--mmproj", args.mmproj]         # vision: mmproj junto al modelo
    else:
        c.append("--no-mmproj")                # text-only: ahorra ~0.9 GB VRAM
    c += ["--host", args.host, "--port", str(args.port)]
    return c


def comando_a_string(c):
    return " ".join(str(x) for x in c)


# ------------------------------------------------------------------ sweep
def esperar_salud(port, timeout_s):
    """Poll GET /health hasta 200 (server listo). Devuelve True/False."""
    url = "http://127.0.0.1:{}/health".format(port)
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status == 200:
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 503:
                pass                      # cargando modelo — seguir
            else:
                pass
        except Exception:
            pass                          # aun no escucha
        time.sleep(2)
    return False


def medir(port, n_predict, prompt):
    """POST /completion y devuelve (t_gen, t_prefill, contenido_vacio)."""
    body = json.dumps({
        "prompt": prompt,
        "n_predict": n_predict,
        "temperature": 0.0,
        "cache_prompt": False,
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:{}/completion".format(port),
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    t = j.get("timings", {})
    return (t.get("predicted_per_second"), t.get("prompt_per_second"))


def lanzar_y_medir(args, ncmoe, cmoe, etiqueta, log_path, prompt):
    """Lanza el server con una config, mide 2 requests y lo cierra."""
    cmd = construir_comando(args, ncmoe=ncmoe, cmoe=cmoe, mtp=None)
    print("\n--> [{}] lanzando... (log: {})".format(etiqueta, log_path))
    print("    " + comando_a_string(cmd))
    with open(log_path, "w", encoding="utf-8") as lf:
        proc = subprocess.Popen(
            cmd, stdout=lf, stderr=subprocess.STDOUT,
            cwd=str(Path(args.server).parent))
    try:
        if not esperar_salud(args.port, timeout_s=600):
            print("    [FALLO] el server no llego a 'listening' en 600 s — ver el log.")
            return None
        # request 1: warmup (ademas compila PTX JIT la primera vez — descartada)
        try:
            medir(args.port, 16, prompt)
        except Exception as ex:
            print("    [AVISO] warmup fallo: {}".format(ex))
        # request 2: medicion
        t_gen, t_pre = medir(args.port, 256, prompt)
        if t_gen is None:
            print("    [AVISO] la respuesta no trajo timings; ver log.")
            return None
        print("    generacion: {:.2f} t/s   prefill: {:.2f} t/s".format(t_gen, t_pre or 0))
        return (t_gen, t_pre)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except Exception:
            proc.kill()
        time.sleep(4)                     # dejar que Windows libere la VRAM


def modo_sweep(args):
    valores = [v.strip().lower() for v in args.sweep_values.split(",") if v.strip()]
    prompt = "Explica en dos frases por que el cielo es azul."
    stamp = time.strftime("%Y%m%d-%H%M%S")
    base_log = Path(args.log_dir)
    base_log.mkdir(parents=True, exist_ok=True)
    resultados = []
    print("=" * 70)
    print("SWEEP -ncmoe (V1, sin MTP — aislar la variable; MTP se activa despues)")
    print("=" * 70)
    for i, v in enumerate(valores):
        etiqueta = "cmoe" if v == "cmoe" else "ncmoe-{}".format(v)
        log_path = str(base_log / "sweep-{}-{}.log".format(etiqueta, stamp))
        if v == "cmoe":
            r = lanzar_y_medir(args, None, True, etiqueta, log_path, prompt)
        else:
            r = lanzar_y_medir(args, int(v), False, etiqueta, log_path, prompt)
        if r:
            resultados.append((etiqueta, r[0], r[1]))
    if not resultados:
        print("\nROJO: ninguna configuracion midio t/s. Revisar logs en {}".format(base_log))
        return 1
    resultados.sort(key=lambda x: -x[1])
    print("\n" + "=" * 70)
    print("RESULTADOS (generacion t/s, de mejor a peor):")
    for etiqueta, t_gen, t_pre in resultados:
        print("  {:12s} {:8.2f} t/s   (prefill {:8.2f} t/s)".format(etiqueta, t_gen, t_pre or 0))
    ganador = resultados[0][0]
    linea = ["SWEEP {} — ganador: {}".format(stamp, ganador)]
    for etiqueta, t_gen, t_pre in resultados:
        linea.append("  {:12s} {:8.2f} t/s (prefill {:8.2f})".format(etiqueta, t_gen, t_pre or 0))
    res_path = Path(args.log_dir) / "sweep-ncmoe-resultados.txt"
    with open(res_path, "a", encoding="utf-8") as f:
        f.write("\n".join(linea) + "\n")
    print("\nGANADOR: {} -> usar: py abrir-qwen-apex.py {} --mtp".format(
        ganador,
        "" if ganador == "cmoe" else "--ncmoe {}".format(ganador.split("-")[1])))
    print("resultados anexados en: {}".format(res_path))
    return 0


# ------------------------------------------------------------------ menu
def menu_interactivo(args):
    """Doble-click (sin argumentos): menu de 4 opciones. Muta args y devuelve."""
    print("=" * 70)
    print("   QWEN APEX-I-MINI  (35B)  -  build b11856 con draft-mtp")
    print("=" * 70)
    print()
    print("  [1] ABRIR el modelo y chatear        (V1 seguro, Enter)")
    print("  [2] BARRIDO -ncmoe con medicion t/s  (1a vez: ~15-30 min)")
    print("  [3] ABRIR con MTP x2                 (V2, tras el barrido)")
    print("  [4] Solo VER el comando, sin abrir   (dry-run)")
    print("  [0] Salir")
    print()
    op = input("  Elige una opcion [1]: ").strip() or "1"
    print()
    if op == "0":
        return 0
    if op == "2":
        args.sweep = True
        return None
    if op == "3":
        args.mtp = True
        v = input("  valor -ncmoe del barrido (Enter = -cmoe, seguro): ").strip()
        args.ncmoe = int(v) if v.isdigit() else None
        return None
    if op == "4":
        cmd = construir_comando(args, ncmoe=args.ncmoe,
                                cmoe=(args.ncmoe is None),
                                mtp=(args.spec_n_max if args.mtp else None))
        print("  COMANDO EXACTO:\n    " + comando_a_string(cmd))
        input("\n  (Enter para cerrar)... ")
        return 0
    return None          # opcion 1 (default): V1 tal cual


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(
        description="Lanzador Qwen APEX-I-MINI para llama.cpp b11856 (rig del Director)")
    ap.add_argument("--server", default=DEFAULT_SERVER)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--mtp", action="store_true", help="V2: draft-mtp (PR #22673)")
    ap.add_argument("--ncmoe", type=int, default=None,
                    help="expertos de las primeras N capas en CPU (sustituye -cmoe)")
    ap.add_argument("--sweep", action="store_true", help="barrido automatico -ncmoe")
    ap.add_argument("--sweep-values", default="cmoe,40,32,24,16")
    ap.add_argument("--port", type=int, default=PORT_DEFAULT,
                    help="default 9931 (cambio v0.7.0; airi/pi puede querer 8080)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--ctx", type=int, default=16384,
                    help="16384 = mitigacion issue #23577 para MTP")
    ap.add_argument("--fa", default="on", choices=["on", "off", "auto"])
    ap.add_argument("--ctk", default="q8_0")
    ap.add_argument("--ctv", default="q8_0")
    ap.add_argument("--threads", type=int, default=4, help="4 fisicos del i3-10100F")
    ap.add_argument("--spec-n-max", type=int, default=2,
                    help="solo --mtp: tokens a draftear (2 = mitigacion #23577)")
    ap.add_argument("--spec-p-min", type=float, default=None,
                    help="solo --mtp: umbral p-min (p.ej. 0.75 como V2 documentado)")
    ap.add_argument("--moe-cache-mib", type=int, default=None, dest="moe_cache_mib",
                    help="cache GPU MiB para expertos en CPU (auditado: default 0=off)")
    ap.add_argument("--preset", default="think", choices=sorted(PRESETS),
                    help="sampling oficial Qwen3.6: think|coding|fast "
                         "(config-sampling-qwen36.md); NO afecta al sweep")
    ap.add_argument("--mmproj", default=None,
                    help="mmproj-F16.gguf para vision; sin el se pasa --no-mmproj")
    ap.add_argument("--log-dir", default=r"D:\ZLia\sweep-logs")
    ap.add_argument("--dry-run", action="store_true",
                    help="imprime el comando exacto y sale (sin pre-flight ni lanzar)")
    ap.add_argument("--force", action="store_true",
                    help="aceptar tamano de modelo distinto al verificado")
    ap.add_argument("--strict", action="store_true",
                    help="abortar si el build no es b" + BUILD_PIN)
    args = ap.parse_args()

    # DOBLE-CLICK: sin argumentos -> menu de 4 opciones en la misma ventana
    if len(sys.argv) == 1:
        m = menu_interactivo(args)
        if m is not None:
            return m

    if args.dry_run:
        cmd = construir_comando(args, ncmoe=args.ncmoe,
                                cmoe=(args.ncmoe is None),
                                mtp=(args.spec_n_max if args.mtp else None))
        print("DRY-RUN — comando exacto:\n")
        print(comando_a_string(cmd))
        if args.sweep:
            print("\n(sweep mediria estos valores en secuencia: {})".format(args.sweep_values))
        return 0

    if os.name != "nt":
        print("Este lanzador es para Windows (rig del Director). En este SO solo --dry-run.")
        return 1

    print("LAIA — LANZADOR QWEN APEX-I-MINI (build b{}, draft-mtp disponible)".format(BUILD_PIN))
    if not preflight(args):
        print("\nROJO: pre-flight fallo. NADA se lanzo. Corrige y vuelve.")
        return 1

    if args.sweep:
        return modo_sweep(args)

    modo = "V2 draft-mtp (n-max {},{}{})".format(
        args.spec_n_max,
        " p-min {}".format(args.spec_p_min) if args.spec_p_min is not None else "",
        " ncmoe {}".format(args.ncmoe) if args.ncmoe is not None else " cmoe") \
        if args.mtp else \
        "V1 base ({})".format("ncmoe {}".format(args.ncmoe) if args.ncmoe is not None else "cmoe")
    cmd = construir_comando(args, ncmoe=args.ncmoe,
                            cmoe=(args.ncmoe is None),
                            mtp=(args.spec_n_max if args.mtp else None))
    print("\nMODO: " + modo + "  |  sampling preset: " + args.preset)
    print("COMANDO:\n  " + comando_a_string(cmd) + "\n")
    print("WebUI/API: http://127.0.0.1:{}   (Ctrl+C para parar)".format(args.port))
    if args.mtp and args.port != 8080:
        print("(nota: si airi/pi esperaba el puerto 8080 viejo, relanza con --port 8080)")
    try:
        rc = subprocess.call(cmd, cwd=str(Path(args.server).parent))
        return rc if rc is not None else 0
    except KeyboardInterrupt:
        print("\nInterrumpido.")
        return 130


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
        sys.exit(130)
