#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
barrido-n1-expertos.py v1.0 — FASE D del NIVEL 1 (recorte de expertos + MEC)
=============================================================================
Encargo del Director (27-oct-2026), siguiendo la Ronda 12 (orden de ejecucion
N1 -> N3 -> N2 -> N4): "vamos nivel por nivel... crea todas las pruebas que
necesites... verifica mis flags nuevas permitidas... crea un archivo .py que
haga todas las pruebas y genere un log para pasar y analizar".

Analiza punto a punto investigacion/nivel-1-recorte-expertos.md (SS0-SS19) y
traduce SUS dosis a configs ejecutables. SOLO mide: no inventa nada ([M]).

  BLOQUE EXP   (base campeona del barrido-30, -cmoe + -ngl 99 + -lm none):
    D-ANCLA (21.53 [M]) · D-EXP10-CTRL (control: deberia FRENAR ~-6.5%) ·
    D-EXP8 (sanity = default) · D-EXP6/5/4/3/2 (escalera SS5: +8..+28% [T])
  BLOQUE UB1K  D-EXP4-UB1K (apilado con ORO-UB1K, SS6.4: sin conflicto [M])
  BLOQUE MEC   D-NCM37C4-MEC0 (control 22.49 [M]) · D-MEC-512/1024/768
               (--moe-cache-mib, SS14-16; orden de dosis final SS15:
                0 -> 512 -> 1024 -> 768, control en la MISMA sesion)
  BLOQUE COMBO D-EXP4-NCM37C4 (stack EXP x NCM, SS8)

Correcciones que este script materializa respecto al barrido-30 (no-op):
  1. La clave del override se construye desde el GGUF REAL: parser propio
     (stdlib) lee general.architecture del archivo y arma UNA clave
     <arch>.expert_used_count=int:K. Nunca qwen3moe.* a ciegas (SS4/SS11.1).
  2. Autenticador OBLIGATORIO por run: el log del server debe mostrar
     "n_expert_used = K" (SS12.2, datapoint #5114). Sin eso: run INVALIDO.
  3. Segundo autenticador: "CUDA0 compute buffer size" debe BAJAR con k
     (SS12.6). Se registra por run.

Reglas de la casa respetadas (aprendido.md + flags-verificadas-LAIA.txt):
  - Auditoria de flags ANTES de arrancar: cada token verificado verbatim
    contra InformacionCritica/llama-flags-nuevo.txt (dump UTF-16 b11856).
    Si falta uno, ABORTA sin tocar el server.
  - PROHIBIDAS abortan el arranque: --mlock, -nkvo, -ub 512, turbo*,
    --spec-* (fase D no usa spec), flags muertas (--no-mmap/-dio/--jinja/-dt).
  - MEC: aprendido SS2 midio veneno en la base vieja (-cmoe, ctx 16k, KV q8_0,
    256/512 MiB -> 13.51/17.22). La investigacion SS14-16 (posterior, auditada
    en ronda 10) mantiene las dosis SOLO sobre NCM37C4 (fit + KV q4_0 + ctx 4k
    liberan VRAM) y SOLO con control D-MEC-0 en la misma sesion: si pierde,
    se descarta. Este script ejecuta exactamente eso.
  - Protocolo de medicion del barrido (aprendido SS8): 4 pasadas x 256 tokens,
    prompts DISTINTOS misma familia, temp 0, seed fija, cache_prompt, se
    descarta la 1a, decode = media 2-4, prefill = pasada 1 fria, pausas
    termicas 60 s cada 8 configs, CSV reanudable, ruido declarado +/-0.3-0.5.
  - Sanity automatica de 3 pares en dosis de calidad (temp 0). La puerta de
    calidad COMPLETA es la sanity manual de 20 prompts del Director (SS5).
  - Guardarrail: ABORTA si /health ya responde (medir con un server vivo
    falsea todo). --si lo mata antes de arrancar.

Salidas (carpeta de logs, default D:\\ZLia\\faseD-logs):
  faseD-N1-INFORME.md     <- informe para pasar al Director/LAIA
  faseD-N1-resultados.csv <- CSV crash-safe reanudable
  faseD-N1-datos.json     <- datos crudos completos
  faseD-N1-consola.log    <- copia de toda la consola
  logs-config\\NN-NOMBRE.log <- stdout+stderr del server por config

Uso:
  py barrido-n1-expertos.py              -> 14 configs (~40-55 min)
  py barrido-n1-expertos.py --quick      -> 7 configs criticas (~25 min)
  py barrido-n1-expertos.py --solo exp   -> solo bloque EXP
  py barrido-n1-expertos.py --solo exp,mec,combo
  py barrido-n1-expertos.py --extra-k 9,7 -> dosis k extra en el bloque EXP
  py barrido-n1-expertos.py --si         -> mata un server vivo y sigue

AUDITORIA v1.1 (28-oct-2026, tras el HTTP 400 de la primera corrida real):
  La v1.0 lanzaba el server con SOLO los flags diff de cada config (p.ej.
  D-ANCLA quedaba como `llama-server.exe -cmoe`): SIN -m, SIN --port 9931,
  SIN contexto, SIN -fa, SIN KV cuantizada. El server que respondia en el
  puerto no era el nuestro y POST /completion devolvio HTTP 400; ademas el
  CUERPO del error se descartaba y una excepcion mataba TODO el barrido.
  Correcciones materializadas:
  1. CRITICO: el comando lanzado ahora es SIEMPRE
     `server -m <modelo> <BASE_FLAGS_FIJAS> <flags diff de la config>`
     (el diff va detras y gana: llama.cpp deja ganar al ultimo valor).
  2. El cuerpo de CUALQUIER error HTTP se captura y se imprime en consola,
     nota del CSV y JSON: un 400 ya no es un misterio.
  3. Un fallo HTTP/conexion marca la config NO-VALIDA y el barrido SIGUE
     con la siguiente (antes: traceback y muerte total, CSV vacio).
  4. Identidad del server verificada por su log: si no menciona el modelo
     esperado, esa config se invalida (nunca medir un server fantasma o
     watchdog que se cuelgue del puerto).
  5. Muerte del server a mitad de medicion -> detectada por exit code.
  6. Resume v2: solo las filas SI cuentan como hechas; las NO se re-miden.
  7. La auditoria de flags cubre TAMBIEN la base (v1.0 solo miraba el diff).
  8. consola.log SIEMPRE sin colores ANSI; consola Windows con VT habilitado.
  9. stderr tambien va al log; Ctrl+C guarda informe parcial (rc 130).
 10. Parser GGUF con buffer de 1 MiB (arrays gigantes saltan mucho mas
     rapido). Retries solo para fallos transitorios (5xx/429/conexion).
"""
import argparse
import csv
import datetime
import json
import os
import re
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request

# ------------------------- constantes del rig (RutasArchivos.md) ------------
VERSION = "barrido-n1-expertos v1.1 (2026-10-27)"
PROTO = "faseD-N1-v2"

RUTA_SERVER_DEF = r"D:\llama.cpp\llama-server.exe"
RUTA_MODELO_DEF = (r"D:\ZLia\models"
                   r"\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf")
RUTA_DUMP_DEF = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "llama-flags-nuevo.txt")
LOGS_DIR_DEF = r"D:\ZLia\faseD-logs"

ALIAS = "apex35b"
HOST_DEF = "127.0.0.1"
PUERTO_DEF = 9931
BYTES_MODELO_ESPERADOS = 14273277376  # RutasArchivos.md / flags-verificadas
BUILD_PIN_ESPERADO = "11856"          # 0.7.0-dev (build 11856, commit 3642238cc)

# Anclas historicas [M] (barrido-30, 26-oct-2026)
ANCLA_UB1K = 21.53    # id 32 ORO-UB1K / ANCHOR-B (decode)
NCM37C4_REF = 22.49   # id 14 NCM37C4 (decode, +4.4%)
TECHO_RUIDO = 0.5     # aprendido SS8: +/-0.3-0.5 t/s -> zona muerta

# BASE_FLAGS = verbatim barrido-qwen-30.py (campeon -lm none SIN colocacion;
# la colocacion va POR CONFIG: -cmoe para EXP, -ncmoe 37 para MEC/NCM).
# Mantiene -ngl 99 y -c 16384 para que los numeros sean comparables 1:1 con
# el barrido-30 (ANCHOR-B 21.53, NCM37C4 22.49).
BASE_FLAGS_FIJAS = [
    "-ngl", "99",
    "-c", "16384", "-b", "2048", "-ub", "256",
    "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
    "-t", "4", "--prio", "2", "--no-mmproj",
    "-lm", "none",
    "--host", HOST_DEF, "--port", str(PUERTO_DEF),
]
CM = ["-cmoe"]
UB1K = ["-ub", "1024", "-b", "4096"]            # id 32 verbatim barrido-30
NCM37C4 = ["-ncmoe", "37", "-c", "4096",
           "-ctk", "q4_0", "-ctv", "q4_0"]      # id 14 verbatim barrido-30

# ---- valores legales (verbatim del dump b11856, auditados 27-oct-2026) -----
LM_MODOS = {"auto", "none", "mmap", "mlock", "mmap+mlock", "dio"}
KV_TIPOS = {"f32", "f16", "bf16", "q8_0", "q4_0", "q4_1", "iq4_nl", "q5_0", "q5_1"}
FA_VALORES = {"on", "off", "auto"}

# ---- prohibidas (aprendido.md SS2/SS7 + flags-verificadas seccion C) -------
PROHIBIDAS_EXACTAS = {
    "--mlock", "-nkvo", "--no-kv-offload", "--draft-max", "-draft",
    "--draft-min", "-dt", "--defrag-thold", "--no-mmap", "--direct-io",
    "-dio", "--jinja",
}
PROHIBIDAS_PREFIJO = ("--spec-", "-turbo", "turbo")  # fase D no usa spec

# Tokens que el dump DEBE contener para que este script arranque
DUMP_REQUERIDOS = [
    "-m,", "--model", "-a,", "--alias", "-ngl,", "--gpu-layers",
    "-cmoe,", "--cpu-moe", "-ncmoe,", "--n-cpu-moe",
    "--override-kv", "--moe-cache-mib", "-lm,", "--load-mode",
    "-fa,", "--flash-attn", "-ctk,", "--cache-type-k", "-ctv,",
    "--cache-type-v", "-c,", "--ctx-size", "-b,", "--batch-size",
    "-ub,", "--ubatch-size", "-t,", "--threads", "--prio",
    "--no-mmproj", "--host", "--port", "q8_0", "q4_0",
    "on|off|auto",
]

# ------------------------------- utilidades ---------------------------------
USE_COLOR = False
try:
    USE_COLOR = sys.stdout.isatty()
except Exception:
    USE_COLOR = False


def _c(txt, code):
    if not USE_COLOR:
        return str(txt)
    return "\x1b[%sm%s\x1b[0m" % (code, txt)


def bold(t):
    return _c(t, "1")


def red(t):
    return _c(t, "91")


def green(t):
    return _c(t, "92")


def yellow(t):
    return _c(t, "93")


def cyan(t):
    return _c(t, "96")


def gray(t):
    return _c(t, "90")


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


class Tee:
    """Copia la consola a un archivo. En el ARCHIVO se eliminan los codigos
    de color ANSI (el log se lee/parsea despues); en pantalla se conservan
    si la consola los soporta."""

    def __init__(self, ruta):
        self.ruta = ruta
        self.f = open(ruta, "w", encoding="utf-8", errors="replace")

    def write(self, s):
        try:
            sys.__stdout__.write(s)
        except Exception:
            pass
        try:
            self.f.write(_ANSI_RE.sub("", s))
            self.f.flush()
        except Exception:
            pass
        return len(s)

    def flush(self):
        try:
            sys.__stdout__.flush()
        except Exception:
            pass
        try:
            self.f.flush()
        except Exception:
            pass


def ahora():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def media(xs):
    xs = [x for x in xs if x is not None and x == x]
    return sum(xs) / len(xs) if xs else None


def fmt(x, nd=2, suf=""):
    if x is None:
        return "N/D"
    try:
        x = float(x)
    except Exception:
        return str(x)
    return ("%." + str(nd) + "f%s") % (x, suf)


# --------------------- auditoria de flags contra el dump --------------------
def decodificar_dump(ruta_dump):
    raw = open(ruta_dump, "rb").read()
    candidatos = []
    for enc in ("utf-16-le", "utf-16", "utf-8"):
        try:
            candidatos.append(raw.decode(enc))
        except Exception:
            continue
    if not candidatos:
        raise SystemExit(red("FATAL: no pude decodificar el dump %s" % ruta_dump))
    for txt in candidatos:
        if "--model" in txt or "--override-kv" in txt:
            return txt
    return max(candidatos, key=len)


def auditar_flags(ruta_dump, lista_configs, base_flags=()):
    """Verifica que TODOS los tokens de flag de TODAS las configs (base +
    diff; v1.1 la BASE tambien se audita, antes se le pasaba por alto)
    esten verbatim en el dump del build (fuente de verdad #1). Aborta si
    falta uno. Tambien revisa prohibidas y valores legales. Devuelve lista
    de problemas (vacia = verde)."""
    problemas = []
    txt = decodificar_dump(ruta_dump)
    faltan = [t for t in DUMP_REQUERIDOS if t not in txt]
    if faltan:
        problemas.append("el dump no contiene (requeridos): %s" % faltan)

    tokens_usados = set()
    for cfg in lista_configs:
        fl = list(base_flags) + list(cfg["flags"])
        for tok in fl:
            if tok.startswith("-"):
                tokens_usados.add(tok)
        for par in PROHIBIDAS_EXACTAS:
            if par in fl:
                problemas.append("config %s usa PROHIBIDA %s" % (cfg["id"], par))
        for tok in fl:
            if any(tok.startswith(p) or tok == p for p in PROHIBIDAS_PREFIJO):
                if tok not in ("--no-mmproj",):
                    problemas.append("config %s usa prefijo prohibido %s"
                                     % (cfg["id"], tok))
    # -ub 512 prohibido (aprendido: 20.77, ruido; el validador rechaza)
    for cfg in lista_configs:
        fl = list(base_flags) + list(cfg["flags"])
        for i, tok in enumerate(fl):
            if tok == "-ub" and i + 1 < len(fl) and fl[i + 1] == "512":
                problemas.append("config %s usa -ub 512 (PROHIBIDO)" % cfg["id"])
            if tok in ("-ctk", "-ctv") and i + 1 < len(fl):
                v = fl[i + 1]
                if v not in KV_TIPOS or v.startswith("turbo"):
                    problemas.append("config %s usa KV ilegal %r" % (cfg["id"], v))
            if tok == "-lm" and i + 1 < len(fl) and fl[i + 1] not in LM_MODOS:
                problemas.append("config %s usa -lm ilegal %r" % (cfg["id"], fl[i + 1]))
            if tok == "-fa" and i + 1 < len(fl) and fl[i + 1] not in FA_VALORES:
                problemas.append("config %s usa -fa ilegal %r" % (cfg["id"], fl[i + 1]))

    for tok in sorted(tokens_usados):
        if tok in ("--override-kv", "--moe-cache-mib"):
            continue  # ya verificados en DUMP_REQUERIDOS
        patron = re.escape(tok) + r"(?=[\s,]|$)"
        if not re.search(patron, txt):
            problemas.append("token %r NO aparece verbatim en el dump" % tok)
    return problemas


# ------------------------- parser GGUF (stdlib) -----------------------------
_GGUF_TAM = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}
_GGUF_FMT = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i",
             6: "<f", 10: "<Q", 11: "<q", 12: "<d"}


def _gguf_string(f):
    (n,) = struct.unpack("<Q", f.read(8))
    if n > 100 * 1024 * 1024:
        raise ValueError("string GGUF demasiado largo: %d" % n)
    b = f.read(n)
    return b.decode("utf-8", errors="replace")


def _gguf_valor(f, vtype, profundidad=0):
    if profundidad > 4:
        raise ValueError("anidamiento GGUF demasidado profundo")
    if vtype == 8:
        return _gguf_string(f)
    if vtype in _GGUF_FMT:
        (v,) = struct.unpack(_GGUF_FMT[vtype], f.read(_GGUF_TAM[vtype]))
        return v
    if vtype == 7:
        return bool(f.read(1)[0])
    if vtype == 9:  # array: elem_type u32 + count u64 + elems
        (etype,) = struct.unpack("<I", f.read(4))
        (n,) = struct.unpack("<Q", f.read(8))
        if n > 5_000_000:
            raise ValueError("array GGUF demasiado largo: %d" % n)
        out = []
        for _ in range(n):
            if len(out) >= 8:  # basta una muestra; salta el resto rapido
                _gguf_salta(f, etype, profundidad + 1)
                continue
            out.append(_gguf_valor(f, etype, profundidad + 1))
        return out
    raise ValueError("tipo GGUF desconocido: %d" % vtype)


def _gguf_salta(f, vtype, profundidad=0):
    if vtype == 8:
        (n,) = struct.unpack("<Q", f.read(8))
        f.seek(n, 1)
        return
    if vtype in _GGUF_FMT:
        f.seek(_GGUF_TAM[vtype], 1)
        return
    if vtype == 7:
        f.seek(1, 1)
        return
    if vtype == 9:
        (etype,) = struct.unpack("<I", f.read(4))
        (n,) = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            _gguf_salta(f, etype, profundidad + 1)
        return
    raise ValueError("tipo GGUF desconocido: %d" % vtype)


def gguf_leer_hparams(ruta_modelo):
    """Lee SOLO la region de metadata del GGUF (v2/v3): general.architecture,
    expert_count y expert_used_count del arch. No lee tensores ni tokenizer
    completo. Devuelve dict con arch, n_expert, n_expert_used."""
    f = open(ruta_modelo, "rb", buffering=1 << 20)
    try:
        magic = f.read(4)
        if magic != b"GGUF":
            raise ValueError("no es GGUF (magic=%r)" % magic)
        (version,) = struct.unpack("<I", f.read(4))
        if version < 2:
            raise ValueError("GGUF v%d no soportado por este parser" % version)
        (tensor_count,) = struct.unpack("<Q", f.read(8))
        (kv_count,) = struct.unpack("<Q", f.read(8))

        # pasadas: 1) general.architecture, 2) claves del arch concreto
        primero = {}
        for _ in range(kv_count):
            key = _gguf_string(f)
            (vtype,) = struct.unpack("<I", f.read(4))
            val = _gguf_valor(f, vtype)
            primero[key] = val
            if key == "general.architecture":
                break
        arch = primero.get("general.architecture")
        if not arch:
            raise ValueError("el GGUF no trae general.architecture")

        buscadas = {arch + ".expert_count", arch + ".expert_used_count"}
        encontrado = {}
        if set(buscadas).issubset(primero.keys()):
            encontrado = {k: primero[k] for k in buscadas}
        else:
            f.seek(0)
            f.read(4 + 4 + 8 + 8)
            for _ in range(kv_count):
                key = _gguf_string(f)
                (vtype,) = struct.unpack("<I", f.read(4))
                val = _gguf_valor(f, vtype)
                if key in buscadas:
                    encontrado[key] = val
                if len(encontrado) == len(buscadas):
                    break
        return {
            "arch": arch,
            "gguf_version": version,
            "tensor_count": tensor_count,
            "n_expert": encontrado.get(arch + ".expert_count"),
            "n_expert_used": encontrado.get(arch + ".expert_used_count"),
        }
    finally:
        f.close()


# --------------------- prompts y configs de la fase D -----------------------
# 4 prompts DISTINTOS de la misma familia (~misma longitud). Con cache_prompt
# la pasada 1 es prefill frio real; las pasadas 2-4 no reutilizan KV entre si
# (prefijos distintos). Anti-inflado spec heredado del barrido-25/30.
PROMPTS_MEDICION = [
    "Describe en un parrafo como funciona una bicicleta: pedales, cadena y "
    "ruedas. Incluye un consejo basico de mantenimiento.",
    "Explica en un parrafo por que el cielo es azul durante el dia y rojo al "
    "atardecer, con palabras simples.",
    "Resume en un parrafo la historia de la imprenta de Gutenberg y por que "
    "cambio el mundo.",
    "Explica en un parrafo que es la fotosintesis: que entra en la hoja, que "
    "sale y por que importa, en palabras simples.",
]

SANITY_PARES = [
    ("Cuanto es 17 x 23? Responde solo el numero.", ["391"]),
    ("Quien escribio Don Quijote? Responde muy corto.", ["cervantes"]),
    ("Que planeta es conocido como el planeta rojo? Responde muy corto.",
     ["marte"]),
]

# Expectativas [T] del SS5 del nivel-1 (banda ~32 GB/s) para el informe
EXPECT_EXP = {
    10: ("CONTROL: deberia FRENAR ~-6.5%", 21.53 * 0.935),
    8: ("sanity = default", 21.53),
    6: ("+8% esperado", 23.3),
    5: ("+12.5% esperado", 24.2),
    4: ("+17% esperado", 25.1),
    3: ("+22% esperado; sacrificio real", 26.4),
    2: ("+28% esperado; cliff de calidad", 27.5),
}


def _ovexp(arch, n):
    """Override runtime con la clave EXACTA leida del GGUF (correccion del
    no-op del barrido-30: aquella vez se uso qwen3moe.* a ciegas)."""
    clave = "%s.expert_used_count=int:%d" % (arch, n)
    return ["--override-kv", clave], clave


def construir_configs(arch, bloque="", extra_k=()):
    """Construye las configs de la fase D. Cada config = BASE + flags diff
    (mismo patron del barrido-30). Devuelve lista de dicts."""
    configs = []

    def add(cid, familia, nombre, flags, hipotesis):
        configs.append({"id": cid, "familia": familia, "nombre": nombre,
                        "flags": flags, "hipotesis": hipotesis})

    if bloque in ("", "exp"):
        add(1, "ANCLA", "D-ANCLA", list(CM),
            "re-ancla de sesion (barrido-30: 21.53 [M]); baseline de todos los deltas")
        add(2, "EXP", "D-EXP10-CTRL", CM + _ovexp(arch, 10)[0],
            "CONTROL autenticador: +25% bytes routed -> deberia medir MENOS "
            "(~20.1). Si no frena, override sospechoso (SS4)")
        add(3, "EXP", "D-EXP8", CM + _ovexp(arch, 8)[0],
            "sanity: = default (8). Debe clavarse con el ancla y logear "
            "n_expert_used = 8 (SS12.2)")
        add(4, "EXP", "D-EXP6", CM + _ovexp(arch, 6)[0],
            "escalera SS6: ~+8% [T], calidad despreciable en chat [F]")
        add(5, "EXP", "D-EXP5", CM + _ovexp(arch, 5)[0],
            "escalera SS5: ~+12.5% [T], punto medio")
        add(6, "EXP", "D-EXP4", CM + _ovexp(arch, 4)[0],
            "escalera SS6: ~+17% [T], ~95-98% calidad [F MoE-Spec]; test de "
            "coherencia SS11.4: debe subir 15-17%")
        add(7, "EXP", "D-EXP3", CM + _ovexp(arch, 3)[0],
            "escalera SS6: ~+22% [T]; sacrificio real (math/codigo)")
        add(8, "EXP", "D-EXP2", CM + _ovexp(arch, 2)[0],
            "curiosidad SS6: ~+28% [T]; cliff esperado, solo con calidad "
            "sacrificable")
        for k in extra_k:
            try:
                kk = int(k)
            except Exception:
                continue
            if kk in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16):
                add(90 + kk, "EXP", "D-EXP%d-EXT" % kk, CM + _ovexp(arch, kk)[0],
                    "dosis extra pedida por CLI (--extra-k)")

    if bloque in ("", "ub1k"):
        add(9, "UB1K", "D-EXP4-UB1K", CM + UB1K + _ovexp(arch, 4)[0],
            "stack SS6.4: ganador candidato EXP4 apilado con ORO-UB1K "
            "(prefill +26.5% ya medido); sin conflicto de flags [M]")

    if bloque in ("", "mec"):
        add(10, "MEC", "D-NCM37C4-MEC0", list(NCM37C4) + ["--moe-cache-mib", "0"],
            "CONTROL MEC (= NCM37C4 del barrido-30, 22.49 [M]) con cache "
            "explicitamente a 0; obligatorio para cada A/B de MEC (SS15)")
        add(11, "MEC", "D-MEC-512", list(NCM37C4) + ["--moe-cache-mib", "512"],
            "cache de expertos calientes en VRAM (SS14): +34..60% en GPUs ajenas; "
            "en este rig GO/NO-GO vs control; aprendido SS2 ya veto 256/512 en la "
            "base vieja -> aqui se mide sobre NCM37C4 con control en sesion (SS15)")
        add(12, "MEC", "D-MEC-1024", list(NCM37C4) + ["--moe-cache-mib", "1024"],
            "dosis fina SS15 (orden final: 0 -> 512 -> 1024 -> 768); si pierde "
            "vs control, se descarta")
        add(13, "MEC", "D-MEC-768", list(NCM37C4) + ["--moe-cache-mib", "768"],
            "dosis fina SS15 (tercera en orden); si pierde vs control, se descarta")

    if bloque in ("", "combo"):
        add(14, "COMBO", "D-EXP4-NCM37C4", list(NCM37C4) + _ovexp(arch, 4)[0],
            "stack SS8: EXP4 x NCM37C4 (el compuesto del objetivo +50%)")

    return configs


BLOQUES_DE = {"exp": [1, 2, 3, 4, 5, 6, 7, 8],
              "ub1k": [9], "mec": [10, 11, 12, 13], "combo": [14]}
QUICK_IDS = [1, 2, 3, 4, 6, 10, 11]


def filtrar_configs(configs, solo=None, quick=False):
    if quick:
        return [c for c in configs if c["id"] in QUICK_IDS]
    if solo:
        pedidos = [s.strip() for s in solo.split(",") if s.strip()]
        ids = []
        for p in pedidos:
            if p not in BLOQUES_DE:
                raise SystemExit(red("--solo bloque desconocido: %s (validos: %s)"
                                     % (p, ",".join(sorted(BLOQUES_DE)))))
            ids.extend(BLOQUES_DE[p])
        return [c for c in configs if c["id"] in ids]
    return configs


# --------------------------- control del server -----------------------------
def health_ok(puerto, timeout=2):
    try:
        r = urllib.request.urlopen(
            "http://%s:%d/health" % (HOST_DEF, puerto), timeout=timeout)
        return r.getcode() == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


def version_server(ruta_server):
    try:
        out = subprocess.run([ruta_server, "--version"], capture_output=True,
                             timeout=30)
        txt = ((out.stdout or b"") + (out.stderr or b"")).decode(
            "utf-8", errors="replace")
        return " ".join(txt.split())
    except Exception as e:
        return "N/D (%s)" % e


def matar_server_vivo(puerto):
    if health_ok(puerto):
        print(yellow("  server vivo en el puerto %d -> taskkill llama-server.exe" % puerto))
        try:
            subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"],
                           capture_output=True)
        except Exception as e:
            print(yellow("  taskkill no disponible aqui (%s); cerrar a mano" % e))
        time.sleep(3)
        if health_ok(puerto):
            raise SystemExit(red("FATAL: el puerto %d sigue respondiendo tras "
                                 "taskkill. Cerrar a mano y reintentar." % puerto))


def lanzar_server(ruta_server, flags, log_path, carga_timeout):
    """Lanza llama-server con los flags EXACTOS; stdout+stderr al log."""
    logf = open(log_path, "wb")
    proc = subprocess.Popen([ruta_server] + flags, stdout=logf,
                            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < carga_timeout:
        if proc.poll() is not None:
            logf.close()
            return None, time.time() - t0, ("el server murio durante la "
                                            "carga (exit %s)" % proc.returncode)
        if health_ok(PUERTO_DEF, timeout=1.5):
            logf.close()
            return proc, time.time() - t0, "ok"
        time.sleep(1.0)
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    logf.close()
    return None, time.time() - t0, "timeout de carga (%d s)" % carga_timeout


def apagar_server(proc):
    try:
        proc.terminate()
        proc.wait(timeout=15)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    time.sleep(2)


def cola_log(log_path, n=12):
    """Ultimas lineas del log del server (diagnostico rapido de fallos)."""
    try:
        lineas = open(log_path, "rb").read().decode(
            "utf-8", errors="replace").splitlines()
        vivas = [l.strip() for l in lineas if l.strip()]
        return " | ".join(vivas[-n:])[:700]
    except Exception:
        return "(log no disponible)"


def leer_log_server(log_path, modelo_basename=None, puerto=None):
    try:
        txt = open(log_path, "rb").read().decode("utf-8", errors="replace")
    except Exception:
        return {}
    datos = {}
    m = re.search(r"(?:llm_load_print_meta|print_info):\s*general\.architecture"
                  r"\s*=\s*(\S+)", txt)
    if not m:
        m = re.search(r"arch\s*=\s*(qwen\w*)", txt)
    datos["arch_log"] = m.group(1) if m else None
    m = re.search(r"(?:llm_load_print_meta|print_info):\s*n_expert\s*=\s*(\d+)", txt)
    datos["n_expert_log"] = int(m.group(1)) if m else None
    m = re.search(r"(?:llm_load_print_meta|print_info):\s*n_expert_used\s*=\s*(\d+)",
                  txt)
    datos["n_expert_used_log"] = int(m.group(1)) if m else None
    m = re.search(r"CUDA0 compute buffer size\s*:\s*([\d.]+)\s*([MKG])iB", txt)
    if m:
        factor = {"M": 1.0, "K": 1.0 / 1024.0, "G": 1024.0}[m.group(2)]
        datos["buffer_mib"] = round(float(m.group(1)) * factor, 1)
    else:
        datos["buffer_mib"] = None
    datos["fit_abort"] = ("failed to fit params" in txt
                          or "failed to allocate" in txt)
    datos["sysmem_warn"] = ("sysmem fallback" in txt.lower()
                            or "shared memory" in txt.lower())
    if datos.get("n_expert_used_log") is not None and "n_expert_used" in txt:
        datos["override_aplicado"] = True
    else:
        datos["override_aplicado"] = False
    # identidad (v1.1): el log debe PROBAR que este server carga NUESTRO
    # modelo; si no, otro proceso (watchdog/proxy/server viejo) ocupa el
    # puerto y medirlo falsearia todo sin ruido ninguno.
    if modelo_basename is not None:
        datos["modelo_en_log"] = modelo_basename.lower() in txt.lower()
    if puerto is not None:
        datos["puerto_en_log"] = ("listening on" in txt
                                  and (":%d" % puerto) in txt)
    return datos


def vram_nvidia():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, timeout=15)
        linea = out.stdout.decode("utf-8", errors="replace").strip().splitlines()
        if not linea:
            return None
        usada, total = linea[0].split(",")[:2]
        return int(usada.strip()), int(total.strip())
    except Exception:
        return None


# ------------------------------ medicion ------------------------------------
class MeasError(RuntimeError):
    """Fallo de medicion con diagnostico (HTTP 4xx/5xx, server muerto...)."""


def _post_json(url, cuerpo, timeout, proc=None, reintentos=2):
    """POST application/json. v1.1: captura el CUERPO de cualquier error
    HTTP (el 400 de la v1.0 quedo sin diagnostico porque se descartaba) y
    reintenta SOLO fallos transitorios (5xx/429/conexion). Los 4xx son
    rechazos del pedido: fallan de inmediato CON el mensaje del server."""
    datos = cuerpo if isinstance(cuerpo, bytes) else \
        json.dumps(cuerpo).encode("utf-8")
    ultimo = None
    for intento in range(reintentos + 1):
        if proc is not None and proc.poll() is not None:
            raise MeasError("el server murio a mitad de la medicion "
                            "(exit code %s)" % proc.returncode)
        req = urllib.request.Request(url, data=datos, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            detalle = ""
            try:
                detalle = e.read().decode("utf-8", errors="replace")[:400]
            except Exception:
                pass
            ultimo = MeasError("HTTP %d en %s -> %s"
                               % (e.code, url, detalle or "(sin cuerpo)"))
            if 400 <= e.code < 500 and e.code != 429:
                raise ultimo
        except Exception as e:
            ultimo = MeasError("conexion fallo en %s: %r" % (url, e))
        if intento < reintentos:
            time.sleep(8)
    raise ultimo


def pasadas_medicion(puerto, prompts, n_predict=256, seed=424242, timeout=600,
                     proc=None):
    """4 pasadas x n_predict tokens. Devuelve (prefill_ts, [dec r1..r4],
    detalles). Prefill = pasada 1 fria (prompt_per_second); decode = media
    2-4 de predicted_per_second (protocolo aprendido SS8). proc se vigila:
    si el server muere a mitad, MeasError (no un timeout ciego)."""
    url = "http://%s:%d/completion" % (HOST_DEF, puerto)
    prefill = None
    decs = []
    detalle = []
    for i, p in enumerate(prompts):
        cuerpo = {
            "prompt": p, "n_predict": n_predict, "temperature": 0.0,
            "seed": seed, "cache_prompt": True, "ignore_eos": True,
            "stream": False,
        }
        t0 = time.time()
        d = _post_json(url, cuerpo, timeout=timeout, proc=proc)
        t = d.get("timings", {}) or {}
        pf = t.get("prompt_per_second")
        dec = t.get("predicted_per_second")
        pn = t.get("predicted_n")
        detalle.append({"pasada": i + 1, "prompt_per_second": pf,
                        "predicted_per_second": dec, "predicted_n": pn,
                        "s_wall": round(time.time() - t0, 1)})
        if i == 0:
            prefill = pf
        else:
            decs.append(dec)
    return prefill, decs, detalle


def sanity_chat(puerto, n_predict=48, seed=424242, timeout=120):
    url = "http://%s:%d/completion" % (HOST_DEF, puerto)
    ok_n = 0
    detalle = []
    for pregunta, esperados in SANITY_PARES:
        cuerpo = {
            "prompt": pregunta, "n_predict": n_predict, "temperature": 0.0,
            "seed": seed, "cache_prompt": False, "stream": False,
        }
        try:
            d = _post_json(url, cuerpo, timeout=timeout, reintentos=0)
            txt = (d.get("content") or "").lower()
        except MeasError as e:
            txt = "ERROR: %s" % e
        hit = any(e.lower() in txt for e in esperados)
        ok_n += 1 if hit else 0
        detalle.append({"pregunta": pregunta, "esperado": esperados,
                        "ok": hit, "respuesta": txt[:160]})
        if txt.startswith("ERROR:"):
            break  # server caido: las restantes fallaran igual (v1.1)
    return ok_n, len(SANITY_PARES), detalle


# ------------------------------- CSV / resume -------------------------------
COLUMNAS = ["proto", "id", "nombre", "familia", "fecha_hora", "flags",
            "load_s", "valido", "nota", "prefill_ts",
            "dec_r2", "dec_r3", "dec_r4", "decode_ts",
            "override_pedida", "n_expert_used_log", "override_aplicado",
            "arch_gguf", "arch_log", "n_expert_log", "buffer_mib",
            "vram_usada_mib", "vram_total_mib",
            "sanity_ok_n", "sanity_total", "delta_vs_ancla_pct"]


def csv_ruta(dir_logs):
    return os.path.join(dir_logs, "faseD-N1-resultados.csv")


def csv_cargar_hechos(ruta_csv):
    """Dict id->fila de corridas previas validas (mismo proto). v1.1: solo
    las filas SI cuentan como hechas; una config que fallo se re-mide."""
    hechos = {}
    if not os.path.exists(ruta_csv):
        return hechos
    try:
        with open(ruta_csv, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("proto") == PROTO and row.get("valido") == "SI":
                    try:
                        hechos[int(row["id"])] = row
                    except Exception:
                        pass
    except Exception:
        pass
    return hechos


def csv_append(ruta_csv, fila):
    nuevo = not os.path.exists(ruta_csv)
    with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nuevo:
            w.writeheader()
        w.writerow(fila)


# --------------------------- ejecucion de una config ------------------------
def medir_config(cfg, contexto):
    """Corre UNA config completa: server up -> 4 pasadas -> sanity -> down.
    Devuelve dict fila CSV + datos completos."""
    dir_logs = contexto["dir_logs"]
    log_path = os.path.join(dir_logs, "logs-config",
                            "%02d-%s.log" % (cfg["id"], cfg["nombre"]))
    fila = {c: "" for c in COLUMNAS}
    fila.update({"proto": PROTO, "id": cfg["id"], "nombre": cfg["nombre"],
                 "familia": cfg["familia"], "fecha_hora": ahora(),
                 "flags": " ".join(cfg["flags"])})
    completo = {"id": cfg["id"], "nombre": cfg["nombre"],
                "familia": cfg["familia"], "flags": cfg["flags"],
                "hipotesis": cfg["hipotesis"], "log": log_path}

    # v1.1: el comando lanzado es SIEMPRE base + diff (el ultimo valor gana
    # en llama.cpp). La v1.0 lanzaba SOLO el diff: D-ANCLA quedaba como
    # `llama-server.exe -cmoe` (sin -m, sin --port, sin -c...): ahi nacio
    # el HTTP 400 de la primera corrida real.
    flags_full = list(contexto.get("base_flags") or []) + list(cfg["flags"])
    fila["flags"] = " ".join(flags_full)
    completo["flags"] = flags_full

    print(cyan("  [%02d] %s: lanzando server..." % (cfg["id"], cfg["nombre"])))
    proc, load_s, estado = lanzar_server(contexto["ruta_server"], flags_full,
                                         log_path, contexto["carga_timeout"])
    fila["load_s"] = "%.1f" % load_s if load_s else ""
    completo["load_s"] = round(load_s, 1) if load_s else None
    if proc is None:
        fila["valido"] = "NO"
        fila["nota"] = "carga fallida: %s" % estado
        log_txt = leer_log_server(log_path)
        if log_txt.get("fit_abort"):
            fila["nota"] += " (fit abortado: VRAM insuficiente para esta config)"
        print(red("    FAIL carga (%s)" % fila["nota"]))
        print(red("    cola del log: %s" % cola_log(log_path)))
        completo.update({"valido": False, "nota": fila["nota"],
                         "log_datos": log_txt, "log_cola": cola_log(log_path)})
        return fila, completo

    try:
        log_txt = leer_log_server(log_path,
                                  modelo_basename=os.path.basename(
                                      contexto.get("ruta_modelo") or ""),
                                  puerto=contexto.get("puerto", PUERTO_DEF))
        # ---- identidad del server (v1.1): nunca medir un fantasma ----
        if log_txt.get("modelo_en_log") is False:
            fila["valido"] = "NO"
            fila["nota"] = ("el log del server NO menciona el modelo esperado "
                            "(%s): otro proceso ocupa el puerto %s o el "
                            "arranque fue reemplazado"
                            % (contexto.get("ruta_modelo"),
                               contexto.get("puerto", PUERTO_DEF)))
            print(red("    FAIL identidad: %s" % fila["nota"]))
            print(red("    cola del log: %s" % cola_log(log_path)))
            completo.update({"valido": False, "nota": fila["nota"],
                             "log_datos": log_txt,
                             "log_cola": cola_log(log_path)})
            return fila, completo
        if log_txt.get("puerto_en_log") is False:
            print(yellow("    AVISO: el log no confirma 'listening on' en el "
                         "puerto %s (se continua, pero revisar)"
                         % contexto.get("puerto", PUERTO_DEF)))
        override_pedida = None
        fl = cfg["flags"]
        for i, tok in enumerate(fl):
            if tok == "--override-kv" and i + 1 < len(fl):
                m = re.search(r"expert_used_count=int:(\d+)", fl[i + 1])
                if m:
                    override_pedida = int(m.group(1))
        fila["override_pedida"] = str(override_pedida) if override_pedida else ""
        aplicado = None
        if override_pedida is not None:
            aplicado = (log_txt.get("n_expert_used_log") == override_pedida)
            fila["override_aplicado"] = "SI" if aplicado else "NO"
        fila["n_expert_used_log"] = str(log_txt.get("n_expert_used_log") or "")
        fila["arch_gguf"] = contexto.get("arch_gguf") or ""
        fila["arch_log"] = log_txt.get("arch_log") or ""
        fila["n_expert_log"] = str(log_txt.get("n_expert_log") or "")
        fila["buffer_mib"] = str(log_txt.get("buffer_mib") or "")
        vram = None if contexto["sin_nvidia"] else vram_nvidia()
        if vram:
            fila["vram_usada_mib"], fila["vram_total_mib"] = str(vram[0]), str(vram[1])
            if vram[0] > 3700:
                print(yellow("    AVISO VRAM: %d MiB usados (>3700, riesgo de "
                             "sysmem fallback)" % vram[0]))

        valido = True
        notas = []
        if override_pedida is not None and not aplicado:
            valido = False
            notas.append("OVERRIDE NO APLICADO (log n_expert_used=%s != %d): "
                         "run INVALIDO por regla SS12.2"
                         % (log_txt.get("n_expert_used_log"), override_pedida))
        if log_txt.get("fit_abort"):
            valido = False
            notas.append("fit abortado en el log")
        if log_txt.get("sysmem_warn"):
            notas.append("aviso sysmem/shared en el log (posible spill)")

        med_ok = False
        print(cyan("    midiendo: 4 pasadas x 256 tokens (temp 0, prompts "
                   "distintos)..."))
        try:
            prefill, decs, detalle = pasadas_medicion(PUERTO_DEF,
                                                      PROMPTS_MEDICION,
                                                      proc=proc)
            med_ok = True
        except MeasError as e:
            valido = False  # v1.1: una medicion que fallo JAMAS es valida
            notas.append("medicion fallo: %s" % e)
            print(red("    FAIL medicion: %s" % e))
        except Exception as e:
            valido = False
            notas.append("medicion fallo (inesperado): %r" % e)
            print(red("    FAIL medicion: %r" % e))
        if med_ok:
            dec = media(decs)
            fila["prefill_ts"] = fmt(prefill, 1)
            for j, v in enumerate(decs):
                fila["dec_r%d" % (j + 2)] = fmt(v, 2)
            fila["decode_ts"] = fmt(dec, 2)
            completo.update({"prefill_ts": prefill, "dec_r2_a_r4": decs,
                             "decode_ts": dec, "pasadas": detalle,
                             "log_datos": log_txt, "vram": vram})

            if contexto["con_sanity"]:
                ok_n, tot, sdet = sanity_chat(PUERTO_DEF)
                fila["sanity_ok_n"], fila["sanity_total"] = str(ok_n), str(tot)
                completo["sanity"] = sdet
                marca = green("%d/%d" % (ok_n, tot)) if ok_n == tot else \
                    yellow("%d/%d" % (ok_n, tot))
                print("    sanity auto: %s" % marca)
                if ok_n < tot:
                    notas.append("sanity auto incompleta (%d/%d)" % (ok_n, tot))
        else:
            completo.update({"log_datos": log_txt, "errores": list(notas)})
        fila["valido"] = "SI" if valido else "NO"
        fila["nota"] = "; ".join(notas)
        estado_run = green("VALIDO") if valido else red("INVALIDO")
        print("    decode %s t/s | prefill %s tok/s | %s %s"
              % (bold(fmt(fila.get("decode_ts") or None)),
                 fmt(fila.get("prefill_ts") or None, 0), estado_run,
                 gray(("; " + "; ".join(notas)) if notas else "")))
    finally:
        apagar_server(proc)
    return fila, completo


# ------------------------------ informe -------------------------------------
def protocolo_decision(resultados, ancla_dec):
    """Evalua automaticamente el arbol de decision SS11.4 del nivel-1."""
    lineas = []
    ancla = resultados.get(1)
    exp4 = resultados.get(6)
    exp10 = resultados.get(2)
    exp8 = resultados.get(3)
    if not ancla or not ancla.get("decode_ts"):
        lineas.append("- ANCLA sin dato: no se puede evaluar el arbol (run invalido?)")
        return lineas
    if exp10 and exp10.get("decode_ts") and ancla.get("decode_ts"):
        if exp10["decode_ts"] >= ancla["decode_ts"] - TECHO_RUIDO:
            lineas.append("- CONTROL EXP10 NO freno (%s >= ancla %s - ruido): "
                          "override SOSPECHOSO aunque el log diga lo contrario "
                          "-> tratar como sospecha de no-op (SS4)"
                          % (fmt(exp10["decode_ts"]), fmt(ancla["decode_ts"])))
        else:
            lineas.append("- CONTROL EXP10 freno como debia (%s < %s): el "
                          "mecanismo override RESPONDE [M]" % (
                              fmt(exp10["decode_ts"]), fmt(ancla["decode_ts"])))
    if exp8 and exp8.get("decode_ts") and ancla.get("decode_ts"):
        d = abs(exp8["decode_ts"] - ancla["decode_ts"])
        if d <= max(TECHO_RUIDO, 0.02 * ancla["decode_ts"]):
            lineas.append("- EXP8 clava el ancla (|delta| = %.2f): medicion "
                          "sana" % d)
        else:
            lineas.append("- EXP8 se desvia del ancla (%.2f t/s): revisar "
                          "estabilidad de la sesion" % d)
    if exp4 and exp4.get("decode_ts") and ancla.get("decode_ts"):
        delta = exp4["decode_ts"] / ancla["decode_ts"] - 1.0
        if exp4.get("valido") != "SI":
            lineas.append("- EXP4 invalido (%s): resolver la autenticacion "
                          "ANTES de seguir la escalera" % exp4.get("nota", ""))
        elif delta >= 0.10:
            lineas.append("- DOSIS VIVA: EXP4 +%.1f%% (esperado 15-17%%): "
                          "escalera k=6->4->3 CONFIRMADA; seguir con EXP3 y "
                          "sanity manual de 20 prompts (SS5) antes de fijar k "
                          "operativo (SS11.4 caso 1)" % (delta * 100))
        elif delta > 0:
            lineas.append("- EXP4 sube solo +%.1f%% (<10%%) con n_expert_used "
                          "correcto: la banda ya no domina -> revisar "
                          "colocacion NCM37C4/FIT-A antes de bajar k (SS11.4 "
                          "caso 2)" % (delta * 100))
        else:
            lineas.append("- EXP4 PLANO o negativo CON override aplicado: el "
                          "build ignora la dosis -> PLAN B: RUTA 0 (build "
                          "b11901, 2 zips) (SS11.4 caso 3)" % ())
    return lineas


def generar_informe(dir_logs, contexto, resultados, completos, problemas_flags):
    md = []
    md.append("# INFORME FASE D — NIVEL 1: recorte de expertos + MEC")
    md.append("")
    md.append("Generado: %s · %s · proto %s" % (ahora(), VERSION, PROTO))
    md.append("")
    md.append("## 0. Pre-vuelo")
    md.append("")
    md.append("- Server: `%s`" % contexto["ruta_server"])
    md.append("- Pin del server: %s" % (contexto.get("pin") or "N/D")
              + ("" if BUILD_PIN_ESPERADO in (contexto.get("pin") or "")
                 else "  **OJO: se esperaba build %s**" % BUILD_PIN_ESPERADO))
    md.append("- Modelo: `%s`" % contexto["ruta_modelo"])
    if contexto.get("bytes_modelo") is not None:
        ok_bytes = contexto["bytes_modelo"] == BYTES_MODELO_ESPERADOS
        md.append("- Bytes del modelo: %s (esperados %s)%s"
                  % (contexto["bytes_modelo"], BYTES_MODELO_ESPERADOS,
                     "" if ok_bytes else "  **NO COINCIDEN**"))
    hp = contexto.get("hparams") or {}
    md.append("- GGUF: arch = `%s` · n_expert = %s · n_expert_used = %s "
              "(parser propio, GGUF v%s)"
              % (hp.get("arch"), hp.get("n_expert"), hp.get("n_expert_used"),
                 hp.get("gguf_version")))
    md.append("- Auditoria de flags: %s"
              % ("VERDE - todos los tokens verbatim en el dump b11856"
                 if not problemas_flags else "FALLOS: %s" % problemas_flags))
    md.append("- Clave override usada: `%s`" % (contexto.get("clave") or "N/D"))
    md.append("- Comando base por config: `%s` (+ diff de la config; el "
              "ultimo valor gana)" % (contexto.get("base_flags_str") or "N/D"))
    md.append("")
    md.append("## 1. Resultados")
    md.append("")
    ancla = resultados.get(1) or {}
    ancla_dec = ancla.get("decode_ts")
    md.append("Ancla de sesion (D-ANCLA): %s t/s (referencia barrido-30: 21.53)"
              % fmt(ancla_dec))
    md.append("")
    md.append("| id | config | flags | decode t/s | vs ancla | esperado | "
              "prefill | override | buffer MiB | VRAM MiB | sanity | valido |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for cid in sorted(resultados):
        r = resultados[cid]
        d = r.get("decode_ts")
        delta = ("+%0.1f%%" % ((d / ancla_dec - 1) * 100)
                 if (d and ancla_dec) else "N/D")
        esperado = ""
        m = re.search(r"int:(\d+)", r.get("override_pedida") or "")
        if m and int(m.group(1)) in EXPECT_EXP:
            esperado = EXPECT_EXP[int(m.group(1))][0]
        flags_cortos = (r.get("flags") or "").replace(
            contexto.get("base_flags_str", ""), "").strip()
        md.append("| %s | %s | `%s` | %s | %s | %s | %s | %s%s | %s | %s/%s | "
                  "%s/%s | %s |"
                  % (cid, r.get("nombre"), flags_cortos or "BASE",
                     fmt(d), delta, esperado, fmt(r.get("prefill_ts"), 0),
                     r.get("override_pedida") or "-",
                     ("-> " + str(r.get("override_aplicado") or "-")),
                     r.get("buffer_mib") or "N/D",
                     r.get("vram_usada_mib") or "N/D",
                     r.get("vram_total_mib") or "N/D",
                     r.get("sanity_ok_n") or "-", r.get("sanity_total") or "-",
                     r.get("valido") or ""))
    md.append("")
    md.append("## 2. Protocolo de decision SS11.4 (evaluacion automatica)")
    md.append("")
    md.extend(protocolo_decision(resultados, ancla_dec) or
              ["- (sin datos suficientes)"])
    md.append("")
    mec_ctrl = resultados.get(10)
    if mec_ctrl and mec_ctrl.get("decode_ts"):
        md.append("## 3. Veredicto MEC (control en la misma sesion)")
        md.append("")
        for cid in (11, 12, 13):
            r = resultados.get(cid)
            if not r or not r.get("decode_ts"):
                continue
            dif = r["decode_ts"] - mec_ctrl["decode_ts"]
            veredicto = ("GANA vs control (+%.2f): proponer como dosis"
                         % dif) if dif > TECHO_RUIDO else (
                "pierde vs control (%.2f): SE DESCARTA (regla SS15)" % dif)
            md.append("- %s: %s t/s vs control %s -> %s"
                      % (r["nombre"], fmt(r["decode_ts"]),
                         fmt(mec_ctrl["decode_ts"]), veredicto))
        md.append("")
    md.append("## 4. Recuerdos de la casa aplicados")
    md.append("")
    md.append("- aprendido SS2 (MEC veneno en la base vieja): aqui MEC corre "
              "SOLO sobre NCM37C4 con control D-MEC-0 en la MISMA sesion; si "
              "pierde, se descarta. La dosis 256 MiB ni se prueba (ya medida).")
    md.append("- aprendido SS8: 4 pasadas x 256 tokens, se descarta la 1a, "
              "temp 0, prompts distintos; ruido declarado +/-0.3-0.5 t/s; "
              "deltas <5pp no se persiguen sin mediana de 3 corridas.")
    md.append("- Sanity manual de 20 prompts (10 chat ES, 5 codigo, "
              "5 tool-calling) PENDIENTE del Director para fijar k operativo "
              "(la auto de 3 pares solo es humo-detector).")
    md.append("")
    md.append("## 5. Archivos de esta corrida")
    md.append("")
    md.append("- CSV: `faseD-N1-resultados.csv` (reanudable)")
    md.append("- Datos: `faseD-N1-datos.json`")
    md.append("- Consola: `faseD-N1-consola.log`")
    md.append("- Logs del server: `logs-config/NN-nombre.log`")
    md.append("")
    ruta_md = os.path.join(dir_logs, "faseD-N1-INFORME.md")
    open(ruta_md, "w", encoding="utf-8").write("\n".join(md) + "\n")

    datos_json = {"version": VERSION, "proto": PROTO, "fecha": ahora(),
                  "contexto": {k: v for k, v in contexto.items()
                               if k not in ("tee",)},
                  "runs": list(completos.values())}
    open(os.path.join(dir_logs, "faseD-N1-datos.json"), "w",
         encoding="utf-8").write(json.dumps(datos_json, ensure_ascii=False,
                                            indent=1, default=str))
    return ruta_md


# --------------------------------- main -------------------------------------
def main(argv=None):
    global PUERTO_DEF
    ap = argparse.ArgumentParser(
        description=VERSION + " — fase D del nivel 1 (expertos + MEC)")
    ap.add_argument("--quick", action="store_true",
                    help="solo 7 configs criticas (~25 min)")
    ap.add_argument("--solo", type=str, default="",
                    help="bloques separados por coma: exp,ub1k,mec,combo")
    ap.add_argument("--extra-k", type=str, default="",
                    help="dosis k extra para el bloque EXP, p.ej. 9,7")
    ap.add_argument("--server", type=str, default=RUTA_SERVER_DEF)
    ap.add_argument("--modelo", type=str, default=RUTA_MODELO_DEF)
    ap.add_argument("--logs", type=str, default=LOGS_DIR_DEF)
    ap.add_argument("--puerto", type=int, default=PUERTO_DEF)
    ap.add_argument("--carga-timeout", type=int, default=600)
    ap.add_argument("--si", action="store_true",
                    help="matar un server vivo antes de empezar")
    ap.add_argument("--sin-sanity", action="store_true")
    ap.add_argument("--sin-nvidia", action="store_true")
    ap.add_argument("--sin-pausas", action="store_true")
    args = ap.parse_args(argv)

    PUERTO_DEF = args.puerto
    # v1.1 CAUSA RAIZ del HTTP 400: antes el server se lanzaba con el diff de
    # la config a secas (sin -m, sin --port, sin -c, sin -fa). Ahora la base
    # SIEMPRE lleva el modelo y todos los flags fijos del protocolo.
    base_flags = ["-m", args.modelo] + list(BASE_FLAGS_FIJAS)
    for i, tok in enumerate(base_flags):
        if tok == "--port" and i + 1 < len(base_flags):
            base_flags[i + 1] = str(args.puerto)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if os.name == "nt":
        try:
            os.system("")  # habilita codigos VT/ANSI en la consola Windows
        except Exception:
            pass

    os.makedirs(args.logs, exist_ok=True)
    os.makedirs(os.path.join(args.logs, "logs-config"), exist_ok=True)
    tee = Tee(os.path.join(args.logs, "faseD-N1-consola.log"))
    sys.stdout = tee  # toda la consola queda copiada al log
    sys.stderr = tee  # v1.1: los tracebacks TAMBIEN van al log

    print(gray("=" * 78))
    print(bold(VERSION))
    print(gray("=" * 78))
    print("  server : %s" % args.server)
    print("  modelo : %s" % args.modelo)
    print("  logs   : %s" % args.logs)
    print("  puerto : %d" % args.puerto)

    # ---- 0. pre-vuelo ------------------------------------------------------
    if not os.path.exists(args.server):
        raise SystemExit(red("FATAL: no existe el server: %s" % args.server))
    if not os.path.exists(args.modelo):
        raise SystemExit(red("FATAL: no existe el modelo: %s" % args.modelo))
    if not os.path.exists(RUTA_DUMP_DEF):
        raise SystemExit(red("FATAL: no existe el dump de flags: %s (el script "
                             "NO arranca sin su fuente de verdad)" % RUTA_DUMP_DEF))

    bytes_modelo = os.path.getsize(args.modelo)
    if bytes_modelo != BYTES_MODELO_ESPERADOS:
        print(yellow("  AVISO: el modelo mide %d B y RutasArchivos dice %d B "
                     "-> verificar que es el APEX-I-MINI correcto"
                     % (bytes_modelo, BYTES_MODELO_ESPERADOS)))

    pin = version_server(args.server)
    if BUILD_PIN_ESPERADO not in pin:
        print(yellow("  AVISO: el pin del server no menciona build %s: %s"
                     % (BUILD_PIN_ESPERADO, pin[:120])))

    print(cyan("[0] PARSER GGUF (correccion del no-op del barrido-30)..."))
    try:
        hp = gguf_leer_hparams(args.modelo)
    except Exception as e:
        raise SystemExit(red("FATAL: parser GGUF fallo: %s" % e))
    arch = hp["arch"]
    clave, _ = _ovexp(arch, 8)
    print("  arch = %s (GGUF v%s) · n_expert = %s · n_expert_used = %s"
          % (bold(arch), hp["gguf_version"], hp["n_expert"],
             hp["n_expert_used"]))
    if hp["n_expert"] != 256 or hp["n_expert_used"] != 8:
        print(yellow("  AVISO: se esperaban 256 expertos / 8 usados (ficha "
                     "N1 SS1). Revisar que este es el GGUF correcto."))

    extra_k = [x for x in args.extra_k.split(",") if x.strip()]
    configs = construir_configs(arch, extra_k=extra_k)
    configs = filtrar_configs(configs, solo=args.solo, quick=args.quick)

    print(cyan("[0] AUDITORIA DE FLAGS contra el dump b11856..."))
    problemas = auditar_flags(RUTA_DUMP_DEF, configs, base_flags)
    if problemas:
        for p in problemas:
            print(red("  FALLO: %s" % p))
        raise SystemExit(red("FATAL: la auditoria de flags fallo (%d). Nada se "
                             "ejecuta: revisar configs o regenerar el dump."
                             % len(problemas)))
    print(green("  VERDE: %d configs, todos los tokens verbatim en el dump, "
                "cero prohibidas" % len(configs)))

    if args.si:
        matar_server_vivo(args.puerto)
    elif health_ok(args.puerto):
        raise SystemExit(red("FATAL: /health ya responde en el puerto %d. Hay "
                             "un server vivo (medir con el falsea todo). "
                             "Cerrarlo o relanzar con --si." % args.puerto))

    contexto = {"ruta_server": args.server, "ruta_modelo": args.modelo,
                "dir_logs": args.logs, "pin": pin,
                "bytes_modelo": bytes_modelo, "hparams": hp,
                "arch_gguf": arch, "clave": clave,
                "carga_timeout": args.carga_timeout,
                "con_sanity": not args.sin_sanity,
                "sin_nvidia": args.sin_nvidia,
                "puerto": args.puerto,
                "base_flags_str": " ".join(base_flags),
                "base_flags": base_flags}

    # ---- 1. corrida --------------------------------------------------------
    print(cyan("[1] CORRIDA: %d configs (pausa termica 60 s cada 8)"
               % len(configs)))
    ruta_csv = csv_ruta(args.logs)
    hechos = csv_cargar_hechos(ruta_csv)
    pendientes = [c for c in configs if c["id"] not in hechos]
    if len(pendientes) < len(configs):
        print(gray("  resume: %d ya medidas, %d pendientes"
                   % (len(configs) - len(pendientes), len(pendientes))))

    resultados, completos = {}, {}
    for cid, row in hechos.items():
        try:
            dec = float(row.get("decode_ts") or "") or None
        except Exception:
            dec = None
        resultados[cid] = dict(row)
        resultados[cid]["decode_ts"] = dec
        completos[cid] = dict(row)

    hechas_sesion = 0
    interrumpido = False
    try:
        for cfg in configs:
            if cfg["id"] in hechos:
                print(gray("  [%02d] %s: ya medida (valida), salto"
                           % (cfg["id"], cfg["nombre"])))
                continue
            if hechas_sesion and hechas_sesion % 8 == 0 and not args.sin_pausas:
                print(yellow("  pausa termica 60 s (protege la medicion)..."))
                time.sleep(60)
            try:
                fila, completo = medir_config(cfg, contexto)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                # v1.1: una config JAMAS tumba el barrido (la v1.0 murio con
                # traceback en la config 01 y el resto se perdio entero)
                fila = {c: "" for c in COLUMNAS}
                fila.update({"proto": PROTO, "id": cfg["id"],
                             "nombre": cfg["nombre"], "familia": cfg["familia"],
                             "fecha_hora": ahora(), "valido": "NO",
                             "nota": "excepcion no capturada: %r" % e})
                completo = {"id": cfg["id"], "nombre": cfg["nombre"],
                            "familia": cfg["familia"], "valido": False,
                            "nota": fila["nota"], "excepcion": repr(e)}
                print(red("  [%02d] EXCEPCION no capturada: %r" % (cfg["id"], e)))
            csv_append(ruta_csv, fila)
            try:
                dec = float(fila.get("decode_ts") or "") or None
            except Exception:
                dec = None
            resultados[cfg["id"]] = dict(fila)
            resultados[cfg["id"]]["decode_ts"] = dec
            completos[cfg["id"]] = completo
            hechas_sesion += 1
    except KeyboardInterrupt:
        interrumpido = True
        print(yellow("\n  INTERRUMPIDO (Ctrl+C): guardando informe parcial; "
                     "lo ya medido queda en el CSV y se reanuda despues..."))

    # ---- 2. informe --------------------------------------------------------
    print(cyan("[2] INFORME..."))
    ruta_md = generar_informe(args.logs, contexto, resultados, completos,
                              problemas)
    print(green("  %s" % ruta_md))
    print(green("  %s" % ruta_csv))
    print(green("  %s" % os.path.join(args.logs, "faseD-N1-datos.json")))
    print(green("  %s" % os.path.join(args.logs, "faseD-N1-consola.log")))
    print("")
    print(bold("Para pasar al analisis: faseD-N1-INFORME.md + "
               "faseD-N1-resultados.csv (+ carpeta logs-config si se pide)."))
    return 130 if interrumpido else 0


if __name__ == "__main__":
    sys.exit(main())
