#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
actualizar-llama-b11856.py — RUTA DIRECTA automatica (rig del Director)
========================================================================
Descarga, verifica (SHA-256), descomprime y audita el binario oficial
llama.cpp b11856 (CUDA 12.4) + su zip cudart, y al final emite un
VEREDICTO DE SEGURIDAD GLOBAL (VERDE / ROJO).

QUE HACE:
  1) Descarga los 2 zips oficiales (si ya existen con tamano exacto, los reutiliza).
  2) Verifica SHA-256 de ambos contra los pines calculados por LAIA (2026-10-25).
  3) Descomprime AMBOS en D:\\llama.cpp\\bin-new con proteccion anti zip-slip.
  4) Verifica archivos criticos + tamaños byte-exactos de las 3 DLLs CUDA 12.4.
  5) Verifica el sistema: nvcuda.dll (driver NVIDIA) y MSVCP140.dll (runtime VC++).
  6) Ejecuta SOLO "llama-server.exe --version" y "--help" (NUNCA carga el modelo,
     NUNCA modifica tu build viejo en build\\bin).
  7) Confirma la presencia de "draft-mtp" en la ayuda (soporte MTP, PR #22673).
  8) Regenera el dump D:\\ZLia\\llama-flags-nuevo.txt en UTF-16 (como el original).
  9) RESUMEN final: VEREDICTO GLOBAL + instruccion de pegar la salida en el chat.

REQUISITOS: Python 3.8+ (solo libreria estandar, cero pip installs), Windows 10/11.
USO:        py actualizar-llama-b11856.py      (o: python actualizar-llama-b11856.py)
NOTA:       Todas las rutas se pueden sobreescribir con variables de entorno
            LLAMA_DL_DIR, LLAMA_TARGET, LLAMA_DUMP (util para pruebas).
"""

import hashlib
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

if sys.version_info < (3, 8):
    raise SystemExit("Se requiere Python 3.8 o superior.")

# ------------------------------------------------------------------ constants
B11856 = "https://github.com/ggml-org/llama.cpp/releases/download/b11856"

ZIPS = [
    {
        "name": "llama-b11856-bin-win-cuda-12.4-x64.zip",
        "url": B11856 + "/llama-b11856-bin-win-cuda-12.4-x64.zip",
        "size": 272434110,
        "sha256": "71d4ff57c9b59ce960ca5e9c28d0e26d8e631075c4d13af0c34f7f3a4fa1f094",
    },
    {
        "name": "cudart-llama-bin-win-cuda-12.4-x64.zip",
        "url": B11856 + "/cudart-llama-bin-win-cuda-12.4-x64.zip",
        "size": 391443627,
        "sha256": "8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6",
    },
]

CUDA_DLLS = {          # tamaños byte-exactos verificados por LAIA en el zip cudart
    "cudart64_12.dll": 553984,
    "cublas64_12.dll": 100033536,
    "cublasLt64_12.dll": 473551360,
}

CRITICAL_FILES = [
    "llama-server.exe",
    "ggml-cuda.dll",
    "libomp.dll",
] + list(CUDA_DLLS)

DL_DIR = Path(os.environ.get("LLAMA_DL_DIR", str(Path.home() / "Downloads")))
TARGET = Path(os.environ.get("LLAMA_TARGET", r"D:\llama.cpp\bin-new"))
DUMP = Path(os.environ.get("LLAMA_DUMP", r"D:\ZLia\llama-flags-nuevo.txt"))

RESULTS = []  # (critico, ok, etiqueta, detalle)


def ok(critical, label, detail=""):
    RESULTS.append((critical, True, label, detail))
    print("  [OK]    {:38s} {}".format(label, detail))


def fail(critical, label, detail=""):
    RESULTS.append((critical, False, label, detail))
    print("  [FALLO] {:38s} {}".format(label, detail))


def skip(label, detail=""):
    RESULTS.append((False, True, label, detail))
    print("  [OMIT]  {:38s} {}".format(label, detail))


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest, expected_size):
    if dest.exists() and expected_size and dest.stat().st_size == expected_size:
        print("    ya existe con tamano exacto ({:,} B) -> descarga omitida".format(expected_size))
        return
    print("    descargando {:,} bytes ...".format(expected_size))
    req = urllib.request.Request(url, headers={"User-Agent": "laia-updater/1.0"})
    done = 0
    last_pct = -1
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length", expected_size or 0))
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if total:
                pct = int(done * 100 / total) // 10 * 10
                if pct > last_pct:
                    last_pct = pct
                    print("    {:3d}%  ({:,} / {:,} bytes)".format(pct, done, total))
    if done != expected_size:
        raise RuntimeError(
            "tamano descargado {} != esperado {}".format(done, expected_size)
        )
    print("    descarga completa ({:,} bytes)".format(done))


def safe_extract(zip_path, target):
    """Extrae con proteccion zip-slip; devuelve cantidad de archivos."""
    target = target.resolve()
    tstr = str(target) + os.sep
    count = 0
    with zipfile.ZipFile(zip_path) as z:
        for m in z.infolist():
            dest = (target / m.filename).resolve()
            if not (str(dest) == str(target) or str(dest).startswith(tstr)):
                raise RuntimeError("zip-slip detectado: {}".format(m.filename))
            z.extract(m, target)
            count += 1
    return count


def run_capture(exe, args, timeout=180):
    p = subprocess.run([exe] + args, capture_output=True, timeout=timeout)
    out = p.stdout.decode("utf-8", errors="replace")
    err = p.stderr.decode("utf-8", errors="replace")
    return p.returncode, out, err


def main():
    print("=" * 66)
    print("LAIA - ACTUALIZACION AUTOMATICA llama.cpp b11856 (CUDA 12.4)")
    print("=" * 66)
    print("  destino : {}".format(TARGET))
    print("  descargas: {}".format(DL_DIR))
    print("  (solo se ejecuta --version y --help; no se carga el modelo)\n")

    DL_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- 1) descarga + 2) hash (fail-fast: ROJO = parar ya) ----------
    print("[1-2] DESCARGA Y VERIFICACION SHA-256")
    for z in ZIPS:
        dest = DL_DIR / z["name"]
        print("  -> {}".format(z["name"]))
        try:
            download(z["url"], dest, z["size"])
        except Exception as ex:
            fail(True, "descarga " + z["name"], str(ex))
            print("\nROJO: problema de descarga. Revisa conexion y vuelve a ejecutar.")
            return 1
        real = sha256_of(dest)
        if real == z["sha256"]:
            ok(True, "SHA-256 " + z["name"], "VERDE")
        else:
            fail(True, "SHA-256 " + z["name"],
                 "ROJO real={} esperado={}".format(real, z["sha256"]))
            print("\nROJO: hash distinto. BORRA {} de {} y vuelve a ejecutar.".format(
                z["name"], DL_DIR))
            return 1

    # ---------- 3) extraccion con anti zip-slip ----------------------------
    print("\n[3] EXTRACCION EN {}".format(TARGET))
    try:
        TARGET.mkdir(parents=True, exist_ok=True)
        for z in ZIPS:
            n = safe_extract(DL_DIR / z["name"], TARGET)
            ok(True, "extraido " + z["name"], "{} archivos".format(n))
    except Exception as ex:
        fail(True, "extraccion", str(ex))
        return 1

    # ---------- 4) archivos criticos + tamaños CUDA ------------------------
    print("\n[4] ARCHIVOS CRITICOS Y TAMAÑOS BYTE-EXACTOS")
    for fn in CRITICAL_FILES:
        p = TARGET / fn
        if p.exists():
            ok(True, "presente " + fn, "{:,} B".format(p.stat().st_size))
        else:
            fail(True, "presente " + fn, "NO EXISTE en bin-new")
    for fn, sz in CUDA_DLLS.items():
        p = TARGET / fn
        if p.exists() and p.stat().st_size != sz:
            fail(False, "tamano " + fn,
                 "{} != {} (serie 12.4 esperada)".format(p.stat().st_size, sz))

    # ---------- 5) sistema ---------------------------------------------------
    print("\n[5] VERIFICACION DEL SISTEMA")
    if os.name == "nt":
        sys32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
        nvcuda = sys32 / "nvcuda.dll"
        if nvcuda.exists():
            ok(True, "driver NVIDIA (nvcuda.dll)", str(nvcuda))
        else:
            fail(True, "driver NVIDIA (nvcuda.dll)", "no esta en System32")
        msvcp = sys32 / "msvcp140.dll"
        if msvcp.exists():
            ok(True, "runtime VC++ (msvcp140.dll)", str(msvcp))
        else:
            fail(False, "runtime VC++ (msvcp140.dll)",
                 "falta: instalar VC++ Redistributable 2015-2022 x64 si da 0xC0000135")
    else:
        skip("driver NVIDIA / runtime VC++", "solo aplica en Windows")

    # ---------- 6-8) version, draft-mtp, dump --------------------------------
    print("\n[6-8] BINARIO: VERSION, SOPORTE MTP Y DUMP")
    exe = TARGET / "llama-server.exe"
    if os.name != "nt":
        skip("--version / draft-mtp / dump", "prueba en Windows (este no es Windows)")
    else:
        try:
            rc, out, err = run_capture(str(exe), ["--version"])
            # v1.1: llama.cpp imprime la version por STDERR (logging), no stdout.
            combined = (out.strip() + "\n" + err.strip()).strip()
            first = combined.splitlines()[0] if combined else ""
            if rc == 0 and combined:
                ok(True, "llama-server.exe --version", first)
                print("        (pega esta linea en el chat: anota el b-number nuevo)")
            else:
                fail(True, "llama-server.exe --version",
                     "rc={} out={} err={}".format(rc, out[:120], err[:120]))

            rc, out, err = run_capture(str(exe), ["--help"], timeout=300)
            combined = out + ("\n" + err if err.strip() else "")
            dump_text = out if len(out.strip()) > 1000 else combined
            if "draft-mtp" in combined.lower():
                ok(True, "soporte draft-mtp (MTP)", "PR #22673 presente")
            else:
                fail(True, "soporte draft-mtp (MTP)",
                     "NO aparece en --help -> NO usar este binario; avisar")

            DUMP.parent.mkdir(parents=True, exist_ok=True)
            with open(DUMP, "w", encoding="utf-16", newline="") as f:
                f.write(dump_text)
            sz = DUMP.stat().st_size
            if sz > 10000:
                ok(True, "dump regenerado (UTF-16)", "{} ({:,} B)".format(DUMP, sz))
            else:
                fail(False, "dump regenerado (UTF-16)",
                     "{} sospechosamente pequeno ({:,} B)".format(DUMP, sz))
        except Exception as ex:
            fail(True, "ejecucion del binario", str(ex))

    # ---------- 9) veredicto global ------------------------------------------
    print("\n" + "=" * 66)
    print("[9] VEREDICTO DE SEGURIDAD")
    crit_fail = [r for r in RESULTS if r[0] and not r[1]]
    warn = [r for r in RESULTS if not r[0] and not r[1]]
    total = len(RESULTS)
    passed = total - len(crit_fail) - len(warn)
    print("  checks: {} OK / {} avisos / {} criticos fallidos (de {})".format(
        passed, len(warn), len(crit_fail), total))
    for _, _, label, detail in crit_fail:
        print("   CRITICO FALLIDO: {} {}".format(label, detail))
    for _, _, label, detail in warn:
        print("   aviso: {} {}".format(label, detail))
    if crit_fail:
        print("\n  VEREDICTO GLOBAL: ROJO — NO usar el binario; pegar esta salida en el chat.")
        return 1
    print("\n  VEREDICTO GLOBAL: VERDE — binario listo en {}".format(TARGET))
    print("  SIGUIENTE PASO: pega TODA esta salida en el chat (LAIA audita y cerramos).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
        sys.exit(130)
