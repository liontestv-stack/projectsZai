#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
barrido-n3-eficiencia.py v1.3 — COSECHA del NIVEL 3 (eficiencia simple)
=======================================================================
Encargo del Director (28-oct-2026): "dejemos de lado el diagnostico, que
hacemos" -> el siguiente paso del orden aprobado (Ronda 12: N1 -> N3 -> N2
-> N4) es cosechar lo que queda vivo del NIVEL 3 con el metodo de la casa
(ESCALERA + CONTROL + CERTIFICADO + GUARDARRAILS + INFORME).

Lo que falta por medir en el rig (nivel-3-eficiencia-simple.md, "estado de
cosecha" SS13 + plan de pruebas ronda 19):
  (1) COMBO GANADORES juntos: ORO-UB1K (ya en la base) x NCM37C4 x
      cache-reuse/ram/cms/ctxcp/context-shift (SS8.1/SS11.7).
  (2) LA JOYA: cache de prompts en el HIBRIDO (SS3): --cache-reuse 256 +
      validacion OBLIGATORIA con el repro de turnos crecientes (lineas
      "restored context checkpoint" vs "forcing full prompt re-processing",
      issues #21831/#24055; #24055 puede AUTO-DESHABILITAR la cache: el
      warning del arranque es certificado, no opcion).
  (3) dosis de RAM: --cache-ram 512 (ORO-CRAM512 midio decode intacto y
      libera ~7.7 GB del default 8192), -ctxcp 4 (checkpoints 32->4:
      ~63 MB/checkpoint GDN = ~2 GB potenciales -> libera ~1.5-1.8 GB) y
      -cms 1024 (cadencia de checkpoints para chat continuo).
  (4) -np 2 (throughput agregado +14% [M SS4]; ctx 16384 se reparte:
      8192 por slot; SOLO sin spec - SS11.4 MTP exige -np 1, aqui no hay).
  (5) A/B cache OFF (--no-cache-prompt): control del protocolo (SS14: si
      el decode gana pero el TTFT del chat empeora, separar los dos efectos).

La BASE de esta fase es la RECETA DIARIA (config.txt FLAGS_BASE +
FLAGS_GANADORAS = ORO-UB1K, auditoria R24) + -lv 4 para que el log deje
los certificados de cache. Por eso el ancla de esta sesion ES la receta
que ABRIR-QWEN.bat lanza hoy: los deltas se leen directo sobre la vida
real del Director (no sobre un ancla de laboratorio).

v1.3 (hotfix de campo 28-oct, primera corrida completa del rig): la
COLOCACION va POR CONFIG (leccion barrido-qwen-30: en b11856 -cmoe y
-ncmoe juntos = gana el general y anula al -ncmoe). La v1.2 salio sin
colocacion en 11 de 13 configs: el comando pedia los 14.27 GB del modelo
EN la GPU de 4 GB y 11 configs murieron en ~2.5 s (exit 1, "fit abortado:
VRAM insuficiente"); solo sobrevivieron las 2 que llevaban -ncmoe 37.
Ahora: (a) cada config trae su colocacion (ANCLA/CTRL/RAM/CACHE/SLOTS/
COMBO-R = -cmoe; NCM37C4 y COMBO-T = -ncmoe 37 verbatim barrido-30);
(b) CERTIFICADO DE RECETA: el ancla DEBE contener la receta diaria
exacta (config.txt FLAGS_BASE + FLAGS_GANADORAS) o FATAL antes de medir
— la auditoria de flags ve que cada token EXISTE en el dump, pero no que
el comando contenga LA RECETA COMPLETA: por eso paso VERDE y murio;
(c) regla barrido-30 materializada: TODA config necesita -cmoe/-ncmoe o
FATAL; (d) ancla muerta = FATAL inmediato (sin baseline no hay sesion)
y la nota del CSV guarda el forense del log; (e) el resume solo cuenta
filas validas (ya era asi): re-copiar y repetir el comando re-mide solas
las configs muertas.

CERTIFICADOS de este barrido (un knob sin certificado = no-op sospechoso):
  - CACHE: lineas de log (SS3.3/SS10.3): warning "cache_reuse is not
    supported" = NO-SOPORTADO; "restored context checkpoint" = SANO;
    "forcing full prompt re-processing" = ROTO (hibrido #21831).
  - TTFT: repro de 6 turnos crecientes con stream:true (proxy de
    time_starttransfer, SS3.3/SS13): PLANO = el cache trabaja; CRECE =
    cada turno re-paga el prompt. N3-NOCACHE es el control que DEBE crecer.
  - RAM: RAM libre del sistema (GlobalMemoryStatusEx) + WorkingSet del
    proceso (Get-CimInstance) antes/despues: el certificado de CRAM512
    (-7.7 GB esperado) y de CTXCP4 (-1.5-1.8 GB esperado).
  - AGREGADO: probe concurrente de 2 pedidos simultaneos (el +14% de -np 2
    solo aparece con concurrencia real).
  - system_info del arranque: USE_GRAPHS = 1 | REPACK = 1 (SS11.6, gratis).

Reglas de la casa respetadas (aprendido.md + protocolo SS8/SS13):
  - Auditoria de flags ANTES de arrancar: cada token verbatim contra el
    dump b11856 (fuente de verdad #1). Falta uno -> FATAL, nada se toca.
  - PROHIBIDAS abortan: --mlock, -nkvo, -ub 512, --spec-* (aqui NO hay
    spec), flags muertas (--no-mmap/-dio/--jinja/-dt).
  - Protocolo SS8: 4 pasadas x 256 tokens, prompts distintos misma familia,
    temp 0, seed fija, cache_prompt, se descarta la 1a (prefill = pasada 1
    fria, decode = media 2-4), pausas termicas 60 s cada 8 configs, CSV
    reanudable, ruido declarado +/-0.3-0.5 t/s.
  - Estudio thc1006 v4 (SS13): el mismo config abarca 9.4 pp entre corridas
    -> mediana de 3 corridas para las celdas clave ANTES de proclamar una
    ganancia; nunca comparar contra el ancla de OTRA sesion; deltas <5pp no
    se persiguen.
  - Sanity automatica de 3 pares (temp 0): humo-detector. La puerta de
    calidad COMPLETA sigue siendo la sanity manual de 20 prompts.
  - Guardarrail: ABORTA si /health ya responde (--si lo mata). VRAM >3700
    MiB = aviso (sysmem fallback).
  - El libro de muertos del N3 NO se re-mide: ngram spec (acceptance 0.00),
    afinidad (-9..-38%), FIT-C (-38%), repack off (-5%), KV q5_1 (0%),
    POLL (ruido), TB8 (muerto).

Salidas (carpeta de logs, default D:\\ZLia\\faseD-logs):
  faseN3-INFORME.md     <- informe para pasar al Director/LAIA
  faseN3-resultados.csv <- CSV crash-safe reanudable
  faseN3-datos.json     <- datos crudos completos
  faseN3-consola.log    <- copia de toda la consola
  logs-config\\NN-NOMBRE.log <- stdout+stderr del server por config

Uso:
  py barrido-n3-eficiencia.py            -> 13 configs (~35-45 min)
  py barrido-n3-eficiencia.py --quick    -> 5 configs criticas (~18 min)
  py barrido-n3-eficiencia.py --solo ram        (CRAM512/CTXCP4/CMS1024)
  py barrido-n3-eficiencia.py --solo cache      (REUSE/SHIFT)
  py barrido-n3-eficiencia.py --solo combo      (COMBO-R/COMBO-T/NP2-C)
  py barrido-n3-eficiencia.py --solo ancla,cache,combo,anclafin
  py barrido-n3-eficiencia.py --sin-ttft  -> salta el repro de turnos
  py barrido-n3-eficiencia.py --si        -> mata un server vivo y sigue
  py barrido-n3-eficiencia.py --sin-prevuelo  -> omite el dossier PC/modelo/nivel
  py barrido-n3-eficiencia.py --sin-sha256    -> prevuelo sin el hash del modelo

PREVUELO COMPLETO (v1.1, pedido Director 'todo lo que haya que saber sobre mi
PC, el modelo y el nivel antes de comenzar'): antes de medir ANY config, el
barrido escribe en el informe la seccion 0 con (0.1) el hardware del dia (SO,
CPU, RAM por modulo, pagefile, discos, GPU + driver, plan de energia, uptime,
top procesos de RAM), (0.2) la identidad certificada del modelo (bytes, SHA256,
metadatos GGUF: arch, expertos de fabrica, contexto, blocks, nextn/MTP) y la
version/pin del server, (0.3) la receta viva + auditoria de flags, (0.4) el
estado del nivel N3 (referencias [M], libro de muertos, pendientes que cosecha,
protocolo de decision) y la campana completa, (0.5) el dia (recordatorio R28:
RAM al 97%). Todo NO-FATAL (piezas Windows ausentes -> nota, nunca crash).

PROMOCION: el informe emite "candidatas a config.txt" con su certificado;
la promocion formal la aprueba el Director editando UNA linea de config.txt
(pago del config central, ronda 20). Si la cache sale ROTO o NO-SOPORTADO
en b11856, el motivo de RUTA 0 (build nuevo) queda registrado con el dato.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

# ------------------------- constantes del rig (RutasArchivos.md) ------------
VERSION = "barrido-n3-eficiencia v1.3 (2026-10-28, hotfix de campo 2: colocacion por config + certificado de receta + ancla-muerta=FATAL; 11 configs murieron sin -cmoe en la 1a corrida completa)"
PROTO = "faseN3-v1"

RUTA_SERVER_DEF = r"D:\llama.cpp\llama-server.exe"
RUTA_MODELO_DEF = (r"D:\ZLia\models"
                   r"\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf")
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DUMP_DEF = os.path.join(_SCRIPT_DIR, "llama-flags-nuevo.txt")
if not os.path.exists(RUTA_DUMP_DEF):   # Ronda 21: layout del repo
    _dump_repo = os.path.join(_SCRIPT_DIR, "..", "configs",
                              "llama-flags-nuevo.txt")
    if os.path.exists(_dump_repo):
        RUTA_DUMP_DEF = _dump_repo
LOGS_DIR_DEF = r"D:\ZLia\faseD-logs"

ALIAS = "apex35b"
HOST_DEF = "127.0.0.1"
PUERTO_DEF = 9931
BYTES_MODELO_ESPERADOS = 14273277376  # RutasArchivos.md / flags-verificadas
BUILD_PIN_ESPERADO = "11856"          # 0.7.0-dev (build 11856, commit 3642238cc)

# Referencias historicas [M] (barrido-30, 25/26-oct-2026)
ANCLA_UB1K = 21.53     # id 32 ORO-UB1K (decode) = receta diaria
NCM37C4_REF = 22.49    # id 14 NCM37C4 (decode, +4.4%) — SIN UB1K encima
CRAM512_REF = 21.57    # ORO-CRAM512: decode intacto, -7.7 GB RAM de cache
SHIFT_REF = 21.39      # ORO-SHIFT: --context-shift --cache-reuse 256 sin coste
TECHO_RUIDO = 0.5      # aprendido SS8: +/-0.3-0.5 t/s -> zona muerta

# BASE_FLAGS = la RECETA DIARIA materializada (config.txt FLAGS_BASE con
# -b/-ub pisados por FLAGS_GANADORAS = ORO-UB1K, last-wins) + -lv 4 para los
# certificados de cache en el log. Auditoria R24: comando identico al que
# lanzan los .bat (salvo -lv 4, solo log; NO toca la medicion).
BASE_FLAGS_FIJAS = [
    "-ngl", "99",
    "-c", "16384",
    "-ub", "1024", "-b", "4096",            # FLAGS_GANADORAS (ORO-UB1K)
    "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
    "-t", "4", "--prio", "2", "--no-mmproj",
    "-lm", "none",
    "-lv", "4",
    "--host", HOST_DEF, "--port", str(PUERTO_DEF),
]

# COLOCACION POR CONFIG (leccion barrido-qwen-30, materializada en v1.3):
# en b11856 -cmoe y -ncmoe juntos = gana el GENERAL (-cmoe) y anula al
# -ncmoe; por eso la base NO lleva colocacion y CADA config trae la suya:
# la ANCLA y todo el resto llevan -cmoe (= la receta diaria: expertos en
# RAM); NCM37C4 y COMBO-T llevan -ncmoe 37. HOTFIX de campo (28-oct, 1a
# corrida completa): la v1.2 salio SIN colocacion en 11 de 13 configs ->
# el comando pedia los 14.27 GB del modelo EN la GPU de 4 GB y el server
# moria en ~2.5 s (exit 1); solo sobrevivieron las 2 con -ncmoe 37.
CM = ["-cmoe"]

# CERTIFICADO DE RECETA del ANCLA: tokens EXACTOS de la receta diaria
# (config.txt FLAGS_BASE + FLAGS_GANADORAS, ultimo valor gana). El ANCLA
# (id 1) DEBE contenerlos todos ANTES de medir nada: sin receta diaria no
# hay baseline y el protocolo de decision entero queda sin pata. Leccion
# del campo 28-oct: la auditoria de flags verifica que cada token del
# comando EXISTE en el dump, no que el comando traiga LA RECETA COMPLETA
# (faltaba -cmoe y todo paso VERDE igual).
CERTIFICADO_RECETA = [
    ("-ngl", "99"), ("-cmoe", None), ("-c", "16384"),
    ("-ub", "1024"), ("-b", "4096"),
    ("-fa", "on"), ("-ctk", "q8_0"), ("-ctv", "q8_0"),
    ("-t", "4"), ("--prio", "2"), ("--no-mmproj", None),
    ("-lm", "none"),
]

# dosis N3 (verbatim del dump b11856, auditadas 28-oct-2026)
CRAM512 = ["--cache-ram", "512"]
CTXCP4 = ["-ctxcp", "4"]
CTXCP8 = ["-ctxcp", "8"]
CMS1024 = ["-cms", "1024"]
REUSE256 = ["--cache-reuse", "256"]
SHIFT = ["--context-shift"]
NCM37C4 = ["-ncmoe", "37", "-c", "4096",
           "-ctk", "q4_0", "-ctv", "q4_0"]   # id 14 verbatim barrido-30

# ---- valores legales (verbatim del dump b11856) ----------------------------
LM_MODOS = {"auto", "none", "mmap", "mlock", "mmap+mlock", "dio"}
KV_TIPOS = {"f32", "f16", "bf16", "q8_0", "q4_0", "q4_1", "iq4_nl", "q5_0", "q5_1"}
FA_VALORES = {"on", "off", "auto"}

# ---- prohibidas (aprendido.md SS2/SS7 + flags-verificadas seccion C) -------
PROHIBIDAS_EXACTAS = {
    "--mlock", "-nkvo", "--no-kv-offload", "--draft-max", "-draft",
    "--draft-min", "-dt", "--defrag-thold", "--no-mmap", "--direct-io",
    "-dio", "--jinja",
}
PROHIBIDAS_PREFIJO = ("--spec-", "-turbo", "turbo")  # N3 no usa spec

# Tokens que el dump DEBE contener para que este script arranque
DUMP_REQUERIDOS = [
    "-m,", "--model", "-a,", "--alias", "-ngl,", "--gpu-layers",
    "-cmoe,", "--cpu-moe", "-ncmoe,", "--n-cpu-moe",
    "-lm,", "--load-mode", "-fa,", "--flash-attn", "-ctk,",
    "--cache-type-k", "-ctv,", "--cache-type-v", "-c,", "--ctx-size",
    "-b,", "--batch-size", "-ub,", "--ubatch-size", "-t,", "--threads",
    "--prio", "--no-mmproj", "--host", "--port", "q8_0", "q4_0",
    "on|off|auto", "-lv,", "--log-verbosity",
    # ---- N3: cache / checkpoints / slots (dump b11856 verificado 28-oct) ----
    "--cache-reuse", "-cram,", "--cache-ram",
    "-ctxcp,", "--ctx-checkpoints", "-cms,", "--checkpoint-min-step",
    "--context-shift", "-np,", "--parallel", "--cache-prompt",
    "--no-cache-prompt", "-kvu,", "--kv-unified",
]

# pausa termica (SS8): 60 s cada PAUSA_CADA configs; env para tests
PAUSA_TERMICA_S = int(os.environ.get("BARRIDO_PAUSA_S", "60") or 0)
PAUSA_CADA = 8

# ------------------------------- utilidades ---------------------------------
USE_COLOR = False
try:
    USE_COLOR = sys.stdout.isatty()
except Exception:
    USE_COLOR = False


def _c(txt, code):
    if not USE_COLOR:
        return str(txt)
    return "\x1b[%sm%s\x1b" % (code, txt)


def bold(t):
    return _c(t, "1m")


def red(t):
    return _c(t, "31m")


def green(t):
    return _c(t, "32m")


def yellow(t):
    return _c(t, "33m")


def cyan(t):
    return _c(t, "36m")


def gray(t):
    return _c(t, "90m")


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


class Tee:
    """Copia todo lo que sale por stdout/stderr a un archivo de log (sin
    codigos ANSI, siempre utf-8) — v1.1 del barrido N1: stderr TAMBIEN."""

    def __init__(self, ruta):
        self.arch = open(ruta, "ab")
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def write(self, txt):
        try:
            self.arch.write(_ANSI_RE.sub("", txt).encode("utf-8", "replace"))
        except Exception:
            pass
        try:
            self.stdout.write(txt)
        except Exception:
            pass
        return len(txt)

    def flush(self):
        try:
            self.arch.flush()
        except Exception:
            pass
        try:
            self.stdout.flush()
        except Exception:
            pass

    def isatty(self):
        return False

    def reconfigure(self, *a, **k):
        pass

    def close(self):
        try:
            self.arch.close()
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
    diff) esten verbatim en el dump del build (fuente de verdad #1). Aborta
    si falta uno. Tambien revisa prohibidas y valores legales. Devuelve
    lista de problemas (vacia = verde)."""
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
                if tok not in ("--no-mmproj", "--no-cache-prompt"):
                    problemas.append("config %s usa prefijo prohibido %s"
                                     % (cfg["id"], tok))
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
                problemas.append("config %s usa -lm ilegal %r"
                                 % (cfg["id"], fl[i + 1]))
            if tok == "-fa" and i + 1 < len(fl) and fl[i + 1] not in FA_VALORES:
                problemas.append("config %s usa -fa ilegal %r"
                                 % (cfg["id"], fl[i + 1]))
            if tok == "-ctxcp" and i + 1 < len(fl) and not fl[i + 1].isdigit():
                problemas.append("config %s usa -ctxcp ilegal %r"
                                 % (cfg["id"], fl[i + 1]))
            if tok in ("-cms", "--cache-ram", "--cache-reuse", "-np") \
                    and i + 1 < len(fl) and not fl[i + 1].lstrip("-").isdigit():
                problemas.append("config %s usa %s con valor ilegal %r"
                                 % (cfg["id"], tok, fl[i + 1]))

    for tok in sorted(tokens_usados):
        patron = re.escape(tok) + r"(?=[\s,]|$)"
        if not re.search(patron, txt):
            problemas.append("token %r NO aparece verbatim en el dump" % tok)
    return problemas

# ------------------------- prompts del protocolo ----------------------------
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

# REPRO DE TURNOS CRECIENTES (SS3.3): prefijo estable + parrafo nuevo por
# turno. Lo inmutable ARRIBA, lo volatil al final (regla SS3.2: si la
# plantilla muta el inicio, el prefijo compartido se rompe y la cache no
# acierta). TTFT = time-to-first-chunk con stream:true (proxy de
# time_starttransfer del curl del repro original).
PROMPT_REPRO_BASE = (
    "Eres un asistente que responde corto. Conversacion con historial:\n\n"
    "Tema: el faro de un puerto. Un faro es una torre con una luz potente "
    "que gira y avisa a los barcos donde esta la costa y donde estan los "
    "peligros. Antes lo vigilaba una persona que encendia la lampara al "
    "anochecer; hoy la luz es electrica y automatica. La luz se agrupa en "
    "destellos con un ritmo propio, y cada faro del mundo tiene un ritmo "
    "distinto para que el marinero sepa cual esta viendo.\n\n"
)
TURNOS_REPRO_EXTRA = [
    "Turno 1: Cuenta en una frase como se llamaba la persona que cuidaba "
    "el faro y que hacía al atardecer.",
    "Turno 2: Explica brevemente por que cada faro tiene un ritmo de "
    "destellos distinto y para que le sirve eso al marinero.",
    "Turno 3: Resume en una frase que cambio cuando la lampara paso de "
    "aceite a electricidad, y que ventaja trajo de noche.",
    "Turno 4: Menciona en una frase dos peligros tipicos que un faro "
    "ayuda a evitar cerca de la costa.",
    "Turno 5: Explica en una frase que es la niebla para un marinero y "
    "que otra senal se usa cuando la luz del faro no se ve.",
    "Turno 6: Cierra con una frase: por que sigue teniendo sentido tener "
    "faros hoy que existen el GPS y los satelites.",
]
PROMPT_REPRO_COLA = ("\n\nResponde SOLO a lo nuevo del historial con UNA "
                     "frase corta en espanol.")
REPRO_TURNOS = 6          # turnos del repro (1 fria + 5 utiles)
REPRO_N_PREDICT = 24      # respuestas cortas: manda el TTFT, no el decode


def construir_configs():
    """Construye las configs de la cosecha N3. Cada config = BASE (receta
    diaria + -lv 4) + flags diff (el ultimo valor gana en llama.cpp).
    La COLOCACION va en el diff POR CONFIG (leccion barrido-30 + hotfix de
    campo v1.3): add() inyecta -cmoe en toda config que no traiga -ncmoe."""
    configs = []

    def add(cid, familia, nombre, flags, hipotesis):
        fl = list(flags)
        if "-ncmoe" not in fl:
            fl += list(CM)   # receta diaria: expertos en RAM (-cmoe)
        configs.append({"id": cid, "familia": familia, "nombre": nombre,
                        "flags": fl, "hipotesis": hipotesis})

    add(1, "ANCLA", "N3-ANCLA", [],
        "control de sesion = LA RECETA DIARIA (FLAGS_BASE + FLAGS_GANADORAS "
        "de config.txt, auditoria R24): baseline de todos los deltas; sin "
        "cache-reuse el hibrido puede mostrar 'forcing full re-processing' "
        "(#21831): ese es el comportamiento de HOY, no un fallo del barrido")
    add(2, "RAM", "N3-CRAM512", list(CRAM512),
        "--cache-ram 8192 (default) -> 512: la cache de prompts del host "
        "deja de pelear con el modelo de 14.27 GB en 16 GB; ORO-CRAM512 "
        "midio decode intacto (%.2f) y -7.7 GB [M]; certificado = RAM "
        "libre/proceso sube" % CRAM512_REF)
    add(3, "RAM", "N3-CTXCP4", list(CTXCP4),
        "-ctxcp 32 (default) -> 4: cada checkpoint GDN pesa ~63 MB -> el "
        "default puede pedir ~2 GB de RAM; dosis mas defendible del N3 "
        "(SS12/SS13); certificado = WorkingSet del proceso baja ~1.5-1.8 GB")
    add(4, "RAM", "N3-CMS1024", list(CMS1024),
        "-cms 8192 (default) -> 1024: checkpoints mas seguidos en chat "
        "continuo (sin chats de 16K caben <=2; SS10.1); va de la mano con "
        "-ctxcp y -cram")
    add(5, "CACHE", "N3-REUSE", list(REUSE256),
        "LA JOYA (SS3): --cache-reuse 256 recicla el prefijo por chunks "
        "(default 0 = OFF en b11856); en comunidad TTFT -93% en prompts "
        "repetidos (#20574); ORO-SHIFT ya midio reuse sin coste de decode; "
        "OJO #24055: el arranque puede auto-deshabilitarla (warning = "
        "certificado NO-SOPORTADO -> RUTA 0 gana motivo)")
    add(6, "CACHE", "N3-SHIFT", list(SHIFT) + list(REUSE256),
        "familia ORO-SHIFT verbatim (%.2f [M], sin coste): --context-shift "
        "para conversaciones largas + reuse 256; certificado doble: lineas "
        "de log + TTFT plano en el repro" % SHIFT_REF)
    add(7, "SLOTS", "N3-NP2", ["-np", "2"],
        "2 slots: throughput agregado +14%% [M SS4] con concurrencia real; "
        "-c 16384 se reparte (8192 por slot, sobra para chat); SOLO sin "
        "spec (SS11.4: MTP exige -np 1, aqui no hay spec); certificado = "
        "probe concurrente de 2 pedidos")
    add(8, "NCM", "N3-NCM37C4-UB", list(NCM37C4),
        "colocacion campeona (%.2f [M]) APILADA con la receta diaria "
        "(UB1K ya en la base): PRIMER dato del stack ORO-UB1K x NCM37C4 "
        "(pendiente SS13-1); paga con ctx 4096 y KV q4_0" % NCM37C4_REF)
    add(9, "COMBO", "N3-COMBO-R",
        list(CRAM512) + list(CTXCP4) + list(CMS1024) + list(REUSE256)
        + list(SHIFT),
        "combo RAM seguro sobre la receta diaria SIN tocar colocacion: "
        "cram 512 + ctxcp 4 + cms 1024 + reuse 256 + shift; expectativa: "
        "decode ~= ancla, RAM liberada, TTFT plano; la candidata natural "
        "a config.txt si certifica")
    add(10, "COMBO", "N3-COMBO-T",
        list(NCM37C4) + list(CRAM512) + list(CTXCP8) + list(CMS1024)
        + list(REUSE256) + list(SHIFT),
        "combo ganadores SS8.1/SS11.7: NCM37C4 x cram/ctxcp/cms/reuse/"
        "shift (sin -np); expectativa decode ~22.5-23.5 [T]; ctx 4096 de "
        "NCM37C4 manda (single slot); control de sesion = id 8")
    add(11, "COMBO", "N3-NP2-C",
        ["-np", "2"] + list(CRAM512) + list(CTXCP8) + list(CMS1024)
        + list(REUSE256) + list(SHIFT),
        "combo slots SS11.7 sin NCM: -np 2 (8192 ctx por slot) x cache "
        "completa; para el caso de 2 sesiones a la vez; certificado = "
        "probe concurrente")
    add(12, "CTRL", "N3-NOCACHE", ["--no-cache-prompt"],
        "control del A/B cache (SS14): sin cache de prompts TODO turno "
        "re-procesa -> el repro DEBE crecer lineal; separa el efecto "
        "cache del efecto decode; tambien calibra el %real del cache")
    add(13, "ANCLA-FIN", "N3-ANCLA-FIN", [],
        "bookend (leccion v1.2.1): re-ancla al cierre; |fin-inicio| > 5% = "
        "la sesion derivo y los deltas se leen con cuidado")
    return configs


def verificar_receta(ancla_flags, cert=None):
    """CERTIFICADO DE RECETA (v1.3): devuelve los items del certificado que
    FALTAN en los flags finales del ANCLA (base + diff). [] = la receta
    diaria vive completa. Pares (flag, valor): deben aparecer adyacentes;
    (flag, None): el token debe existir."""
    faltan = []
    tokens = list(ancla_flags or [])
    for flag, valor in (cert if cert is not None else CERTIFICADO_RECETA):
        if valor is None:
            if flag not in tokens:
                faltan.append(flag)
        else:
            ok = False
            for i, t in enumerate(tokens):
                if t == flag and i + 1 < len(tokens) and tokens[i + 1] == valor:
                    ok = True
                    break
            if not ok:
                faltan.append("%s %s" % (flag, valor))
    return faltan


def verificar_colocacion(configs, base_flags=()):
    """Regla del barrido-30 materializada (v1.3): TODO comando final debe
    traer su colocacion (-cmoe o -ncmoe). Sin ella el modelo de 14.27 GB
    no cabe en la GPU de 4 GB (11 configs muertas en el campo 28-oct).
    Devuelve los nombres de las configs que no la llevan."""
    malas = []
    for c in configs:
        full = list(base_flags or []) + list(c["flags"])
        if "-cmoe" not in full and "-ncmoe" not in full:
            malas.append("#%d %s" % (c["id"], c["nombre"]))
    return malas


BLOQUES_DE = {"ancla": [1], "ram": [2, 3, 4], "cache": [5, 6], "slots": [7],
              "ncm": [8], "combo": [9, 10, 11], "ctrl": [12],
              "anclafin": [13]}
QUICK_IDS = [1, 5, 9, 10, 13]
TTFT_IDS = {1, 5, 6, 9, 10, 11, 12}   # configs donde el TTFT ES el certificado
TIENE_REUSE = ("--cache-reuse",)


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
    """Lee el log del server y extrae la identidad + los CERTIFICADOS del
    N3: warning de cache_reuse (#24055), lineas restored/forcing (#21831),
    system_info (USE_GRAPHS/REPACK), fit abortado vs declinado, sysmem."""
    try:
        txt = open(log_path, "rb").read().decode("utf-8", errors="replace")
    except Exception:
        return {}
    low = txt.lower()
    datos = {}
    # ---- identidad: nunca medir un fantasma ----
    if modelo_basename is not None:
        datos["modelo_en_log"] = modelo_basename.lower() in txt.lower()
    if puerto is not None:
        datos["puerto_en_log"] = ("listening on" in low
                                  and (":%d" % puerto) in low)
    # ---- certificados de cache (N3 SS3.3/SS10.3/SS14) ----
    datos["cache_reuse_warn"] = ("cache_reuse is not supported" in low)
    datos["cache_restored_n"] = len(
        re.findall(r"restored context checkpoint", low))
    datos["cache_forcing_n"] = len(
        re.findall(r"forcing full prompt re-processing", low))
    m = re.search(r"system_info:[^\r\n]*", txt)
    si = m.group(0) if m else ""
    datos["graphs_ok"] = ("USE_GRAPHS = 1" in si)
    datos["repack_ok"] = ("REPACK = 1" in si)
    # ---- fit abortado vs declinado (leccion v1.2.1 del N1) ----
    datos["fit_abort"] = False
    datos["fit_info"] = ""
    mfit = re.search(r"failed to fit params[^\r\n]*", txt)
    if mfit:
        if "already set by user" in mfit.group(0):
            datos["fit_info"] = ("auto-fit declino (ngl ya fijado por "
                                 "usuario; esperado, benigno)")
        else:
            datos["fit_abort"] = True
    if "failed to allocate" in low:
        datos["fit_abort"] = True
    datos["sysmem_warn"] = ("sysmem fallback" in low
                            or "shared memory" in low)
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


def ram_sistema():
    """(libre_mib, total_mib) del sistema. Windows: GlobalMemoryStatusEx
    (ctypes, sin dependencias); Linux: /proc/meminfo; otro: None. Nunca
    es fatal."""
    try:
        if os.name == "nt":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            st = MEMORYSTATUSEX()
            st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
            return (int(st.ullAvailPhys // (1024 * 1024)),
                    int(st.ullTotalPhys // (1024 * 1024)))
        if os.name == "posix":
            d = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        d[parts[0].rstrip(":")] = int(parts[1])  # kB
            libre = d.get("MemAvailable", d.get("MemFree"))
            if libre is not None and "MemTotal" in d:
                return (libre // 1024, d["MemTotal"] // 1024)
    except Exception:
        pass
    return None


def ram_proceso_mib(pid):
    """WorkingSet del proceso server en MiB (Windows via Get-CimInstance),
    o None fuera de Windows / si la consulta falla. Nunca es fatal."""
    if os.name != "nt" or not pid:
        return None
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Process -Filter 'ProcessId=%d')"
             ".WorkingSetSize" % int(pid)],
            capture_output=True, timeout=30)
        txt = (out.stdout or b"").decode("utf-8", errors="replace").strip()
        return round(int(txt) / (1024 * 1024), 1) if txt.isdigit() else None
    except Exception:
        return None


# ------------- prevuelo completo: PC + modelo + nivel (Ronda 29) -------------
# Pedido Director: "hazlo completo con todo lo que va a necesitar saber sobre
# mi pc, el modelo y todo sobre el nivel en el que estamos antes de comenzar".
# TODO no-fatal: si una pieza no existe (fuera de Windows, sin nvidia-smi),
# queda la nota "(no disponible)" y el barrido sigue.

_CLAVES_GGUF = (   # filtro post-parseo (substring/fin): lo que va al informe
    "general.architecture", "general.name", "general.size_label",
    "general.file_type", "general.quantization_imatrix",
    ".expert_count", ".expert_used_count", ".expert_feed_forward_length",
    ".context_length", ".block_count", ".embedding_length",
    ".attention.head_count", ".attention.key_length",
    "nextn", "shared_expert", "tokenizer.ggml.model",
)
_TAM_GGUF = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1,
             10: 8, 11: 8, 12: 8}
_FMT_GGUF = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i",
             6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}


class _Lector:
    """Lector con buffer de 1 MiB (leccion del parser N1 ronda 14): evita un
    syscall por campo en cabeceras grandes (tokenizer = decenas de miles de
    strings) y salta sin materializar con seek relativo."""

    def __init__(self, f, tam=1 << 20):
        self.f, self.tam = f, tam
        self.buf = b""
        self.pos = 0

    def _llenar(self, n):
        while len(self.buf) - self.pos < n:
            chunk = self.f.read(max(self.tam, n))
            if not chunk:
                raise EOFError("GGUF truncado")
            resto = self.buf[self.pos:] + chunk
            self.buf, self.pos = resto, 0

    def leer(self, n):
        self._llenar(n)
        d = self.buf[self.pos:self.pos + n]
        self.pos += n
        return d

    def u32(self):
        return struct.unpack("<I", self.leer(4))[0]

    def u64(self):
        return struct.unpack("<Q", self.leer(8))[0]

    def cadena(self):
        n = self.u64()
        return self.leer(n).decode("utf-8", errors="replace")

    def saltar(self, n):
        disp = len(self.buf) - self.pos
        if n <= disp:
            self.pos += n
            return
        n -= disp
        self.buf, self.pos = b"", 0
        self.f.seek(n, 1)


def gguf_metadatos(ruta):
    """Lee SOLO la cabecera GGUF (kvs; cero tensores) y devuelve
    (metadatos_filtrados, None) o (None, error). Las claves de interes
    (_CLAVES_GGUF) incluyen nextn (MTP preserved) y expert_used_count de
    fabrica. Nunca es fatal."""
    try:
        with open(ruta, "rb") as f:
            le = _Lector(f)
            if le.leer(4) != b"GGUF":
                return None, "no es GGUF (magic distinto)"
            version = le.u32()
            le.u64()                       # tensor_count (no lo recorremos)
            n_kv = le.u64()
            crudos = {}
            for _ in range(n_kv):
                clave = le.cadena()
                tipo = le.u32()
                if tipo == 8:              # string
                    n = le.u64()
                    if n <= 65536:
                        crudos[clave] = le.leer(n).decode(
                            "utf-8", errors="replace")
                    else:
                        le.saltar(n)
                elif tipo == 9:            # array: se salta entero
                    etipo = le.u32()
                    n = le.u64()
                    if etipo == 8:
                        for _ in range(n):
                            le.saltar(le.u64())
                    elif etipo in _TAM_GGUF:
                        le.saltar(n * _TAM_GGUF[etipo])
                    else:
                        return None, ("array con tipo de elemento "
                                      "desconocido %d" % etipo)
                elif tipo in _TAM_GGUF:
                    v = struct.unpack(_FMT_GGUF[tipo], le.leer(_TAM_GGUF[tipo]))[0]
                    crudos[clave] = bool(v) if tipo == 7 else v
                else:
                    return None, "tipo GGUF desconocido %d" % tipo
        metadatos = {"gguf_version": version}
        for k, v in sorted(crudos.items()):
            if any(k == c or k.endswith(c) or c in k for c in _CLAVES_GGUF):
                metadatos[k] = v
        return metadatos, None
    except Exception as e:
        return None, repr(e)


def sha256_archivo(ruta, notificador=None):
    """SHA256 en streaming (1 MiB por paso); avanza cada ~2 GB si hay
    notificador. Certifica EL archivo exacto (cuant correcto, N2)."""
    h = hashlib.sha256()
    tam = os.path.getsize(ruta)
    hecho, prox = 0, 2 << 30
    with open(ruta, "rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
            hecho += len(chunk)
            if notificador and hecho >= prox and tam > (1 << 30):
                notificador("  sha256... %d/%d GB" % (hecho >> 30, tam >> 30))
                prox += 2 << 30
    return h.hexdigest()


def _ps_json(comando_ps, timeout=60):
    """Ejecuta una consulta PowerShell (Get-CimInstance ... ConvertTo-Json) y
    devuelve lista/dict, o None fuera de Windows / si falla. Nunca es fatal."""
    if os.name != "nt":
        return None
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              comando_ps], capture_output=True, timeout=timeout)
        txt = (out.stdout or b"").decode("utf-8", errors="replace").strip()
        if not txt:
            return None
        d = json.loads(txt)
        if isinstance(d, dict):
            d = [d]
        return d
    except Exception:
        return None


def dossier_pc(con_nvidia=True):
    """Estacion 0.1 del prevuelo: el hardware y el estado del dia."""
    d = {}
    sos = _ps_json("Get-CimInstance Win32_OperatingSystem | Select-Object "
                   "Caption,Version,BuildNumber,OSArchitecture,LastBootUpTime"
                   " | ConvertTo-Json -Compress")
    if sos:
        s = sos[0]
        d["so"] = "%s · %s · build %s (version %s)" % (
            s.get("Caption") or "?", s.get("OSArchitecture") or "?",
            s.get("BuildNumber") or "?", s.get("Version") or "?")
        m = re.match(r"(\d{14})", str(s.get("LastBootUpTime") or ""))
        if m:
            try:
                arranco = datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M%S")
                d["encendido_horas"] = round(
                    (datetime.datetime.now() - arranco).total_seconds() / 3600, 1)
            except Exception:
                pass
    cpus = _ps_json("Get-CimInstance Win32_Processor | Select-Object Name,"
                    "NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed"
                    " | ConvertTo-Json -Compress")
    if cpus:
        c = cpus[0]
        d["cpu"] = "%s (%d nucleos / %d hilos, %s MHz max)" % (
            str(c.get("Name") or "?").strip(), c.get("NumberOfCores") or 0,
            c.get("NumberOfLogicalProcessors") or 0,
            c.get("MaxClockSpeed") or "?")
    palos = _ps_json("Get-CimInstance Win32_PhysicalMemory | Select-Object "
                     "Capacity,Speed,ConfiguredClockSpeed | ConvertTo-Json "
                     "-Compress")
    if palos:
        caps = [int(x.get("Capacity") or 0) for x in palos]
        vels = sorted({str(x.get("ConfiguredClockSpeed")
                           or x.get("Speed") or "?") for x in palos})
        # HOTFIX campo 28-oct: el literal iba partido en dos statements sin
        # parentesis -> "son 2)" % (3 args) = TypeError en el rig (2 palos).
        # Los parentesis restauran la concatenacion y el % sobre el literal
        # COMPLETO (cazado en la primera corrida real del prevuelo).
        d["ram_hardware"] = (
            "%d modulos, %s GB en total a %s MT/s (dual channel si son 2)"
            % (len(palos), fmt(sum(caps) / (1024 ** 3), 1),
               "/".join(vels)))
    pf = _ps_json("Get-CimInstance Win32_PageFileUsage | Select-Object Name,"
                  "AllocatedBaseSize,CurrentUsage,PeakUsage | ConvertTo-Json "
                  "-Compress")
    if pf:
        p = pf[0]
        d["pagefile"] = "%s reservado %s MB · en uso %s MB · pico %s MB" % (
            p.get("Name") or "?", p.get("AllocatedBaseSize") or "?",
            p.get("CurrentUsage") or "?", p.get("PeakUsage") or "?")
    dk = _ps_json("Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | "
                  "Select-Object DeviceID,Size,FreeSpace | ConvertTo-Json "
                  "-Compress")
    if dk:
        partes = []
        for x in dk:
            tot = int(x.get("Size") or 0)
            lib = int(x.get("FreeSpace") or 0)
            if tot:
                partes.append("%s libre %s/%s GB" % (
                    x.get("DeviceID") or "?", fmt(lib / (1024 ** 3), 0),
                    fmt(tot / (1024 ** 3), 0)))
        d["discos"] = " | ".join(partes)
    if con_nvidia:
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,"
                 "temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, timeout=15)
            linea = out.stdout.decode("utf-8", errors="replace").strip()
            if linea:
                p = [q.strip() for q in linea.splitlines()[0].split(",")]
                if len(p) >= 4:
                    d["gpu"] = "%s · driver %s · %s MiB · %s C" % tuple(p[:4])
        except Exception:
            pass
    try:
        out = subprocess.run(["powercfg", "/getactivescheme"],
                             capture_output=True, timeout=15)
        m = re.search(r"\(([^)]+)\)", out.stdout.decode(
            "utf-8", errors="replace"))
        if m:
            d["plan_energia"] = m.group(1)
    except Exception:
        pass
    r = ram_sistema()
    if r:
        d["ram_ahora"] = "libre %s MiB de %s MiB (%.0f%% en uso)" % (
            fmt(r[0], 0), fmt(r[1], 0), (1 - r[0] / r[1]) * 100)
    top = _ps_json("Get-Process | Sort-Object WS -Descending | "
                   "Select-Object -First 4 Name,@{n='MB';e={[math]::Round("
                   "$_.WS/1MB)}} | ConvertTo-Json -Compress", timeout=45)
    if top:
        d["ram_comepanes"] = ", ".join(
            "%s %s MB" % (x.get("Name") or "?", x.get("MB") or "?")
            for x in top[:4])
    return d


def dossier_modelo(ruta, bytes_modelo, pin, con_sha=True, notificador=None):
    """Estacion 0.2: identidad certificada del modelo (bytes, SHA256, GGUF)
    + version/pin del server."""
    d = {"ruta": ruta, "bytes": bytes_modelo,
         "bytes_esperados": BYTES_MODELO_ESPERADOS,
         "bytes_ok": bytes_modelo == BYTES_MODELO_ESPERADOS,
         "server_version": pin or "N/D",
         "build_esperado": BUILD_PIN_ESPERADO,
         "build_ok": bool(pin) and BUILD_PIN_ESPERADO in pin}
    if con_sha:
        d["sha256"] = sha256_archivo(ruta, notificador)
    meta, err = gguf_metadatos(ruta)
    if err:
        d["gguf_error"] = err
    elif meta:
        d["gguf"] = meta
    return d


def dossier_nivel(configs):
    """Estacion 0.4: el estado del nivel N3 y de la campana, incrustado como
    constantes (el rig corre SIN el repo). Fuentes: nivel-3 SS0-SS19,
    nivel-1 SS14-SS30, README rondas 12/24/28."""
    return {
        "campana": ("Orden aprobado (ronda 12): N1 -> N3 -> N2 -> N4 -> "
                    "RUTA 0 + N5. Estado hoy: N1 medido (k=8 techo 21.53 / "
                    "k=4 +41% = 28.85-29.13 / k=3 falla aritmetica / k=2 "
                    "colapso; falta barrido formal v1.2.1 + sanity 20 "
                    "prompts) - N3 EN CURSO (esta corrida) - N2, N4 y "
                    "RUTA 0 + N5 pendientes."),
        "refs": [
            ("ORO-UB1K (receta diaria, ancla del barrido-30 id 32)",
             "21.53 t/s [M]"),
            ("NCM37C4 (colocacion campeona, id 14, SIN UB1K encima)",
             "22.49 t/s [M]"),
            ("ORO-CRAM512 (decode intacto, -7.7 GB RAM)", "21.57 t/s [M]"),
            ("ORO-SHIFT (shift + reuse 256, sin coste)", "21.39 t/s [M]"),
            ("k=4 CHARLA (D-EXP4 / D-EXP4-UB1K, +41%)",
             "28.85 / 29.13 t/s [M]"),
            ("Suelo k=8 con la MISMA receta otro dia", "17.36 / 17.80 [M]"),
            ("Techo de la familia flags k=8 (sweep LMNONE)", "21.50 [M]"),
            ("Ruido declarado / dispersion entre corridas",
             "+/-0.3-0.5 t/s · 9.4 pp (thc1006 v4)"),
        ],
        "muertos": [
            "ngram spec: acceptance 0.00-0.16 [M] - muerto",
            "afinidad CPU-GPU (-ot): -9..-38% [M] - muerto",
            "FIT-C (cuant cache f16->q): -38% [M] - muerto",
            "repack off: -5% [M] - muerto",
            "KV q5_1: 0% de cambio [M] - muerto",
            "POLL: ruido · TB8: muerto",
        ],
        "pendientes": [
            "Stack UB1K x NCM37C4 (SS13-1): PRIMER dato = id 8 de esta "
            "corrida (el 22.49 historico fue SIN UB1K)",
            "Combo ganadores juntos (SS8.1/SS11.7): ids 9 (COMBO-R, seguro), "
            "10 (COMBO-T, expectativa 22.5-23.5 [T]) y 11 (NP2-C, slots)",
            "Cache del hibrido con certificados (SS3.3/SS13): ids 5/6 con "
            "lineas de log + repro TTFT de 6 turnos; NOCACHE (id 12) es el "
            "control que DEBE crecer",
        ],
        "protocolo": [
            "Bookend (id 13): |fin-inicio| > 5% = la sesion derivo -> leer "
            "los deltas con cuidado (leccion v1.2.1)",
            "Mediana de 3 antes de proclamar ganancias (thc1006 v4); deltas "
            "<5pp no se persiguen",
            "Un knob sin certificado = no-op sospechoso (barrido-30)",
            "PROMOCION: candidatas -> UNA linea de FLAGS_BASE en config.txt "
            "(la aprueba el Director, config central ronda 20)",
            "Cache NO-SOPORTADO/ROTO en b11856 = MOTIVO DE RUTA 0 (build "
            "nuevo), no un fracaso",
            "El sanity manual de 20 prompts sigue siendo el juez de calidad",
        ],
        "dia": ("Ronda 28: el diagnostico midio 17.29 t/s (dia lento dentro "
                "del lab) con RAM al 97% (0.40 GB libres) = CULPABLE del dia "
                "confirmado. Antes de medir: cerrar apps; si no, el barrido "
                "mide el pagefile, no la receta."),
        "configs_hoy": [{"id": c["id"], "nombre": c["nombre"],
                         "familia": c["familia"]} for c in configs],
    }


def _nd(v, suf=""):
    return (str(v) + suf) if v not in (None, "", 0) else "no disponible"


def imprimir_prevuelo(pc, mod, niv):
    """Resumen de consola (~8 lineas); el detalle completo va al informe."""
    print(cyan("[0.5] PREVUELO COMPLETO (detalle total en el informe, seccion 0)"))
    print("  PC     : %s" % _nd(pc.get("cpu")))
    print("           %s · %s" % (_nd(pc.get("ram_hardware")),
                                  _nd(pc.get("so"))))
    print("           %s · plan: %s" % (_nd(pc.get("ram_ahora")),
                                        _nd(pc.get("plan_energia"))))
    if pc.get("ram_comepanes"):
        print("           comepanes de RAM: %s" % pc["ram_comepanes"])
    g = mod.get("gguf") or {}
    nombre = g.get("general.name") or os.path.basename(mod["ruta"])
    print("  MODELO : %s · %s bytes (%s) · server %s" % (
        nombre, fmt(mod["bytes"], 0),
        "bytes OK" if mod["bytes_ok"] else "BYTES NO COINCIDEN",
        "build OK" if mod["build_ok"] else "verificar pin"))
    if mod.get("sha256"):
        print("           sha256: %s..." % mod["sha256"][:24])
    if mod.get("gguf_error"):
        print(gray("           (cabecera GGUF: %s)" % mod["gguf_error"]))
    print("  NIVEL  : %s" % niv["campana"][:110] + "...")
    print("           refs [M]: 21.53 ancla · 22.49 NCM · 21.57 CRAM · "
          "21.39 SHIFT · k=4 28.85-29.13")


def md_prevuelo(pc, mod, niv, contexto, problemas_flags):
    """Seccion 0 completa del informe (reemplaza al pre-vuelo minimal v1.0)."""
    md = []
    md.append("## 0. PREVUELO COMPLETO — PC, modelo y nivel "
              "(lo que hay que saber antes de leer resultados)")
    md.append("")
    md.append("### 0.1 El PC (hardware y estado del dia)")
    md.append("")
    md.append("- SO: %s" % _nd(pc.get("so")))
    if pc.get("encendido_horas") is not None:
        nota = ("  **OJO: maquina encendida %.0f h — dia largo**"
                % pc["encendido_horas"] if pc["encendido_horas"] >= 12 else "")
        md.append("- Encendido desde hace: %s h%s"
                  % (fmt(pc["encendido_horas"], 1), nota))
    md.append("- CPU: %s" % _nd(pc.get("cpu")))
    md.append("- RAM hardware: %s" % _nd(pc.get("ram_hardware")))
    md.append("- RAM ahora: %s" % _nd(pc.get("ram_ahora")))
    if pc.get("ram_comepanes"):
        md.append("- Los 4 comepanes de RAM (procesos que mas comen): %s"
                  % pc["ram_comepanes"])
    md.append("- Pagefile: %s" % _nd(pc.get("pagefile")))
    md.append("- Discos: %s" % _nd(pc.get("discos")))
    md.append("- GPU: %s" % _nd(pc.get("gpu")))
    md.append("- Plan de energia: %s (el correcto es 'Maximo rendimiento'; "
              "el 'Equilibrado' frenaba — R24)" % _nd(pc.get("plan_energia")))
    md.append("")
    md.append("### 0.2 El modelo (identidad certificada)")
    md.append("")
    md.append("- Archivo: `%s`" % mod["ruta"])
    md.append("- Bytes: %s (esperados %s)%s" % (
        fmt(mod["bytes"], 0), fmt(mod["bytes_esperados"], 0),
        "" if mod["bytes_ok"] else "  **NO COINCIDEN — verificar cuant**"))
    if mod.get("sha256"):
        md.append("- SHA256: `%s` (certifica EL archivo exacto; la cadena de "
                  "descarga se cierra aqui)" % mod["sha256"])
    else:
        md.append("- SHA256: omitido (--sin-sha256)")
    if mod.get("gguf_error"):
        md.append("- Cabecera GGUF: NO leible (%s)" % mod["gguf_error"])
    elif mod.get("gguf"):
        md.append("- Metadatos GGUF (fabrica):")
        for k in sorted(mod["gguf"]):
            md.append("  - `%s` = %s" % (k, mod["gguf"][k]))
        k_exp = [k for k in mod["gguf"] if k.endswith(".expert_used_count")]
        if k_exp:
            md.append("  - OJO: expert_used_count de FABRICA (el barrido "
                      "mide k=8 de fabrica; CHARLA usa override a 4 en el "
                      "arranque diario, no aqui)")
    md.append("- Server: `%s` · version: %s · build esperado %s: %s"
              % (contexto["ruta_server"], mod.get("server_version"),
                 mod.get("build_esperado"),
                 "OK" if mod.get("build_ok") else "**OJO: verificar**"))
    md.append("")
    md.append("### 0.3 La receta viva y la auditoria de flags")
    md.append("")
    md.append("- Auditoria de flags: %s"
              % ("VERDE - todos los tokens verbatim en el dump b11856"
                 if not problemas_flags else "FALLOS: %s" % problemas_flags))
    md.append("- Comando base por config (LA RECETA DIARIA + -lv 4): `%s` "
              "(+ diff de la config; el ultimo valor gana)"
              % (contexto.get("base_flags_str") or "N/D"))
    md.append("")
    md.append("### 0.4 El nivel N3 — donde estamos y que cosecha esta corrida")
    md.append("")
    md.append("- **Campana:** %s" % niv["campana"])
    md.append("- Referencias del laboratorio [M] (el ancla de HOY manda sobre "
              "todas):")
    for nom, val in niv["refs"]:
        md.append("  - %s: **%s**" % (nom, val))
    md.append("- Libro de muertos (NO se re-mide): %s."
              % "; ".join(niv["muertos"]))
    md.append("- Lo que esta corrida cosecha (pendientes del nivel):")
    for p in niv["pendientes"]:
        md.append("  - %s" % p)
    md.append("- Protocolo de decision:")
    for p in niv["protocolo"]:
        md.append("  - %s" % p)
    md.append("- Las %d configs de hoy: %s"
              % (len(niv["configs_hoy"]),
                 ", ".join("%d %s (%s)" % (c["id"], c["nombre"], c["familia"])
                           for c in niv["configs_hoy"])))
    md.append("")
    md.append("### 0.5 El dia (recordatorio de la ronda 28)")
    md.append("")
    md.append("- %s" % niv["dia"])
    md.append("")
    return md


# ------------------------------ medicion ------------------------------------
class MeasError(RuntimeError):
    """Fallo de medicion con diagnostico (HTTP 4xx/5xx, server muerto...)."""


def _post_json(url, cuerpo, timeout, proc=None, reintentos=2):
    """POST application/json; captura el CUERPO de cualquier error HTTP y
    reintenta SOLO fallos transitorios (5xx/429/conexion) — leccion v1.1
    del barrido N1. proc se vigila: si el server muere a mitad, MeasError."""
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


def _post_stream(url, cuerpo, timeout, proc=None):
    """POST con stream:true; devuelve (ttft_s, n_chunks, texto). TTFT =
    tiempo hasta el PRIMER chunk de datos (proxy del time_starttransfer
    del curl, SS3.3/SS13). Es el instrumento del repro de turnos."""
    datos = cuerpo if isinstance(cuerpo, bytes) else \
        json.dumps(cuerpo).encode("utf-8")
    if proc is not None and proc.poll() is not None:
        raise MeasError("el server murio antes del stream (exit %s)"
                        % proc.returncode)
    req = urllib.request.Request(url, data=datos, method="POST",
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    ttft = None
    n_chunks = 0
    texto = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for linea in r:
                s = linea.decode("utf-8", errors="replace").strip()
                if not s.startswith("data:"):
                    continue
                carga = s[5:].strip()
                if carga == "[DONE]":
                    break
                try:
                    obj = json.loads(carga)
                except Exception:
                    continue
                if ttft is None:
                    ttft = time.time() - t0
                n_chunks += 1
                c = obj.get("content")
                if c:
                    texto.append(c)
                if obj.get("stop"):
                    break
    except urllib.error.HTTPError as e:
        detalle = ""
        try:
            detalle = e.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        raise MeasError("HTTP %d en stream %s -> %s"
                        % (e.code, url, detalle or "(sin cuerpo)"))
    except MeasError:
        raise
    except Exception as e:
        if proc is not None and proc.poll() is not None:
            raise MeasError("el server murio durante el stream (exit %s)"
                            % proc.returncode)
        raise MeasError("stream fallo en %s: %r" % (url, e))
    if ttft is None:
        raise MeasError("stream sin chunks de datos: %s" % url)
    return ttft, n_chunks, "".join(texto)


def pasadas_medicion(puerto, prompts, n_predict=256, seed=424242, timeout=600,
                     proc=None):
    """4 pasadas x n_predict tokens. Devuelve (prefill_ts, [dec r1..r4],
    detalles). Prefill = pasada 1 fria (prompt_per_second); decode = media
    2-4 de predicted_per_second (protocolo aprendido SS8)."""
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


def sanity_chat(puerto, n_predict=128, seed=424242, timeout=180):
    """3 pares temp 0 (humo-detector). Estados: OK (palabra esperada) /
    TRUNCADO (quedo dentro de un <think>: artefacto del probe) / FALLO
    real. Devuelve (ok_n, trunc_n, total, detalle)."""
    url = "http://%s:%d/completion" % (HOST_DEF, puerto)
    ok_n = 0
    trunc_n = 0
    detalle = []
    for pregunta, esperados in SANITY_PARES:
        cuerpo = {
            "prompt": pregunta, "n_predict": n_predict, "temperature": 0.0,
            "seed": seed, "cache_prompt": False, "stream": False,
        }
        try:
            d = _post_json(url, cuerpo, timeout=timeout, reintentos=0)
            txt = (d.get("content") or "")
        except MeasError as e:
            txt = "ERROR: %s" % e
        low = txt.lower()
        hit = any(e.lower() in low for e in esperados)
        trunc = (not hit and "<think>" in low
                 and "</think>" not in low and not low.startswith("error:"))
        if hit:
            ok_n += 1
        elif trunc:
            trunc_n += 1
        detalle.append({"pregunta": pregunta, "esperado": esperados,
                        "ok": hit, "truncado": trunc, "respuesta": txt[:160]})
        if txt.startswith("ERROR:"):
            break  # server caido: las restantes fallaran igual
    return ok_n, trunc_n, len(SANITY_PARES), detalle


def repro_ttft(puerto, proc=None, turnos=REPRO_TURNOS,
               n_predict=REPRO_N_PREDICT, timeout=300, seed=424242):
    """REPRO DE TURNOS CRECIENTES (SS3.3): conversacion que crece turno a
    turno con prefijo estable. Devuelve dict con ttfts por turno (el
    turno 1 es FRIA: se descarta del criterio), t2 (referencia) y tfin.
    Sano: TTFT plano (cada turno solo digiere el parrafo nuevo).
    Roto (#21831): TTFT crece lineal (cada turno re-paga TODO)."""
    url = "http://%s:%d/completion" % (HOST_DEF, puerto)
    ttfts = []
    detalle = []
    for i in range(turnos):
        texto = PROMPT_REPRO_BASE + "\n\n".join(
            TURNOS_REPRO_EXTRA[:i + 1]) + PROMPT_REPRO_COLA
        cuerpo = {
            "prompt": texto, "n_predict": n_predict, "temperature": 0.0,
            "seed": seed, "cache_prompt": True, "stream": True,
        }
        t0 = time.time()
        ttft, nch, resp = _post_stream(url, cuerpo, timeout=timeout,
                                       proc=proc)
        ttfts.append(ttft)
        detalle.append({"turno": i + 1, "ttft_s": round(ttft, 3),
                        "chunks": nch, "s_wall": round(time.time() - t0, 1),
                        "respuesta": resp[:120]})
    datos = {"turnos": turnos, "ttfts": ttfts, "t1_fria": ttfts[0],
             "t2": ttfts[1] if turnos > 1 else None,
             "tfin": ttfts[-1] if turnos > 1 else None,
             "detalle": detalle}
    return datos


def probe_concurrente(puerto, n_hilos=2, n_predict=96, timeout=300,
                      proc=None):
    """Probe de CONCURRENCIA: n_hilos pedidos simultaneos; devuelve
    (tokens_agregados_por_segundo, tokens_totales). Con 1 slot los pedidos
    se encolan (agg ~ decode individual); con -np 2 llenan los 2 slots
    (el +14% [M SS4] SOLO aparece aqui). None si algo fallo."""
    url = "http://%s:%d/completion" % (HOST_DEF, puerto)
    prompts = PROMPTS_MEDICION[:n_hilos]
    total = {"tok": 0}
    lock = threading.Lock()
    errores = []

    def _hilo(p):
        try:
            d = _post_json(url, {"prompt": p, "n_predict": n_predict,
                                 "temperature": 0.0, "seed": 424242,
                                 "cache_prompt": True, "ignore_eos": True,
                                 "stream": False}, timeout=timeout, proc=proc)
            n = (d.get("timings", {}) or {}).get("predicted_n") or 0
            with lock:
                total["tok"] += int(n or 0)
        except Exception as e:
            errores.append(e)

    t0 = time.time()
    hs = [threading.Thread(target=_hilo, args=(p,)) for p in prompts]
    for h in hs:
        h.start()
    for h in hs:
        h.join()
    wall = time.time() - t0
    if errores or total["tok"] <= 0 or wall <= 0:
        return None, 0
    return (total["tok"] / wall, total["tok"])


# ------------------------- criterios (funciones puras) ----------------------
def criterio_cache(tiene_reuse, warn, restored, forcing):
    """Certificado de cache por lineas de log (SS3.3/SS10.3/SS14):
    NO-APLICA (la config no lleva --cache-reuse) / NO-SOPORTADO (warning
    del arranque: #24055, la via queda condicionada a build/colocacion) /
    SANO (restored y cero forcing) / ROTO (forcing sin restored: el
    re-procesado completo del hibrido #21831) / MIXTO (hay de los dos:
    leer el repro y las pasadas) / SIN-DATOS (el build no imprimio nada)."""
    if not tiene_reuse:
        return "NO-APLICA"
    if warn:
        return "NO-SOPORTADO"
    if restored and not forcing:
        return "SANO"
    if forcing and not restored:
        return "ROTO"
    if forcing and restored:
        return "MIXTO"
    return "SIN-DATOS"


def criterio_ttft(t2, tfin):
    """PLANO = el cache trabaja (TTFT no crece con la conversacion);
    CRECE = cada turno re-paga el prompt (hibrido sin cache util);
    GRIS = zona intermedia. Umbral honesto: crecimiento t2->tfin <= +50%
    = PLANO; >= +100% = CRECE; entre medias GRIS. N/D si faltan datos."""
    try:
        t2 = float(t2)
        tfin = float(tfin)
    except (TypeError, ValueError):
        return "N/D"
    if t2 <= 0 or tfin <= 0:
        return "N/D"
    crec = (tfin - t2) / t2
    if crec <= 0.50:
        return "PLANO"
    if crec >= 1.00:
        return "CRECE"
    return "GRIS"


# ------------------------------- CSV / resume -------------------------------
COLUMNAS = ["proto", "id", "nombre", "familia", "fecha_hora", "flags",
            "load_s", "valido", "nota", "prefill_ts",
            "dec_r2", "dec_r3", "dec_r4", "decode_ts",
            "cache_estado", "cache_reuse_warn", "cache_restored_n",
            "cache_forcing_n",
            "ttft_t1", "ttft_t2", "ttft_tfin", "ttft_crecimiento_pct",
            "ttft_veredicto", "agg_ts",
            "ram_free0_mib", "ram_free1_mib", "ram_proc_mib",
            "graphs_ok", "repack_ok",
            "vram_usada_mib", "vram_total_mib",
            "sanity_ok_n", "sanity_trunc_n", "sanity_total",
            "dispers_max_min", "delta_vs_ancla_pct"]


def csv_ruta(dir_logs):
    return os.path.join(dir_logs, "faseN3-resultados.csv")


def csv_proto_de(ruta_csv):
    """Proto de la primera fila de datos de un CSV existente ('' si no hay)."""
    try:
        with open(ruta_csv, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                return row.get("proto") or ""
    except Exception:
        pass
    return ""


def csv_cargar_hechos(ruta_csv):
    """Dict id->fila de corridas previas validas (mismo proto). Solo las
    filas SI cuentan como hechas; una config que fallo se re-mide."""
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
    """Corre UNA config completa: RAM inicial -> server up -> 4 pasadas ->
    sanity -> repro TTFT (si aplica) -> probe concurrente -> RAM final ->
    certificados del log -> down. Devuelve (fila CSV, datos completos)."""
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

    # el comando lanzado es SIEMPRE base + diff (el ultimo valor gana)
    flags_full = list(contexto.get("base_flags") or []) + list(cfg["flags"])
    fila["flags"] = " ".join(flags_full)
    completo["flags"] = flags_full

    ram0 = ram_sistema()
    if ram0:
        fila["ram_free0_mib"] = str(ram0[0])
        completo["ram0"] = ram0

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
        # forense en el CSV (v1.3): el campo 28-oct necesito el log en la
        # mano para diagnosticar sin abrir logs-config a mano
        fila["nota"] += " | log: %s" % cola_log(log_path, n=3)[:220]
        print(red("    FAIL carga (%s)" % fila["nota"]))
        print(red("    cola del log: %s" % cola_log(log_path)))
        completo.update({"valido": False, "nota": fila["nota"],
                         "log_datos": log_txt, "log_cola": cola_log(log_path)})
        return fila, completo

    try:
        modelo_basename = os.path.basename(contexto.get("ruta_modelo") or "")
        puerto = contexto.get("puerto", PUERTO_DEF)
        log_txt = leer_log_server(log_path, modelo_basename=modelo_basename,
                                  puerto=puerto)
        # ---- identidad del server: nunca medir un fantasma ----
        if log_txt.get("modelo_en_log") is False:
            fila["valido"] = "NO"
            fila["nota"] = ("el log del server NO menciona el modelo esperado "
                            "(%s): otro proceso ocupa el puerto %s o el "
                            "arranque fue reemplazado"
                            % (contexto.get("ruta_modelo"), puerto))
            print(red("    FAIL identidad: %s" % fila["nota"]))
            print(red("    cola del log: %s" % cola_log(log_path)))
            completo.update({"valido": False, "nota": fila["nota"],
                             "log_datos": log_txt,
                             "log_cola": cola_log(log_path)})
            return fila, completo
        if log_txt.get("puerto_en_log") is False:
            print(yellow("    AVISO: el log no confirma 'listening on' en el "
                         "puerto %s (se continua, pero revisar)" % puerto))

        valido = True
        notas = []
        if log_txt.get("fit_info"):
            notas.append(log_txt.get("fit_info"))
        if log_txt.get("fit_abort"):
            valido = False
            notas.append("fit abortado en el log (causa real, no el auto-fit)")
        if log_txt.get("sysmem_warn"):
            notas.append("aviso sysmem/shared en el log (posible spill)")

        vram = None if contexto["sin_nvidia"] else vram_nvidia()
        if vram:
            fila["vram_usada_mib"], fila["vram_total_mib"] = str(vram[0]), str(vram[1])
            if vram[0] > 3700:
                print(yellow("    AVISO VRAM: %d MiB usados (>3700, riesgo de "
                             "sysmem fallback)" % vram[0]))

        # ---- medicion estilo laboratorio (SS8 verbatim) ----
        med_ok = False
        print(cyan("    midiendo: 4 pasadas x 256 tokens (temp 0, prompts "
                   "distintos)..."))
        try:
            prefill, decs, detalle = pasadas_medicion(puerto,
                                                      PROMPTS_MEDICION,
                                                      proc=proc)
            med_ok = True
        except MeasError as e:
            valido = False  # una medicion que fallo JAMAS es valida
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
                             "decode_ts": dec, "pasadas": detalle})
            # dispersion entre pasadas (leccion v1.2.1: outlier visible)
            if len(decs) >= 2 and min(decs) > 0:
                disp = max(decs) / min(decs)
                fila["dispers_max_min"] = "%.3f" % disp
                if disp > 1.08:
                    notas.append("dispersion alta en pasadas (max/min=%.2f): "
                                 "confirmar con mediana de 3 (SS13)" % disp)

            # ---- sanity auto (humo-detector) ----
            if contexto["con_sanity"]:
                ok_n, trunc_n, tot, sdet = sanity_chat(puerto)
                fila["sanity_ok_n"] = str(ok_n)
                fila["sanity_trunc_n"] = str(trunc_n)
                fila["sanity_total"] = str(tot)
                completo["sanity"] = sdet
                if ok_n == tot:
                    marca = green("%d/%d" % (ok_n, tot))
                elif trunc_n and (ok_n + trunc_n == tot):
                    marca = yellow("%d OK + %dT/%d" % (ok_n, trunc_n, tot))
                else:
                    marca = red("%d/%d (%dT)" % (ok_n, tot, trunc_n))
                print("    sanity auto: %s" % marca)
                if ok_n < tot:
                    if trunc_n and (ok_n + trunc_n == tot):
                        notas.append("sanity %d OK + %d truncadas (probe "
                                     "corto dentro de <think>, no es fallo "
                                     "de calidad)" % (ok_n, trunc_n))
                    else:
                        notas.append("sanity con fallos reales (%d/3 OK, "
                                     "%d truncadas)" % (ok_n, trunc_n))

            # ---- repro de turnos crecientes (TTFT / certificado cache) ----
            if cfg["id"] in TTFT_IDS and not contexto.get("sin_ttft"):
                print(cyan("    repro TTFT: %d turnos crecientes (stream)..."
                           % REPRO_TURNOS))
                try:
                    rep = repro_ttft(puerto, proc=proc)
                    completo["repro_ttft"] = rep
                    fila["ttft_t1"] = fmt(rep.get("t1_fria"), 2)
                    fila["ttft_t2"] = fmt(rep.get("t2"), 2)
                    fila["ttft_tfin"] = fmt(rep.get("tfin"), 2)
                    if rep.get("t2") and rep.get("tfin"):
                        crec = (rep["tfin"] / rep["t2"] - 1.0) * 100
                        fila["ttft_crecimiento_pct"] = "%.0f" % crec
                    fila["ttft_veredicto"] = criterio_ttft(rep.get("t2"),
                                                           rep.get("tfin"))
                    print("    TTFT t2=%s s -> tfin=%s s (%s)"
                          % (fmt(rep.get("t2"), 2), fmt(rep.get("tfin"), 2),
                             fila["ttft_veredicto"]))
                except MeasError as e:
                    notas.append("repro TTFT fallo: %s" % e)
                    print(red("    FAIL repro: %s" % e))

            # ---- probe de concurrencia (certificado de -np) ----
            if not contexto.get("sin_probe"):
                agg, tok = probe_concurrente(puerto, proc=proc)
                if agg:
                    fila["agg_ts"] = fmt(agg, 2)
                    completo["agg"] = {"tokens_s": agg, "tokens": tok}

            # ---- RAM final + certificados del log (ya con el repro dentro) ----
            ram1 = ram_sistema()
            if ram1:
                fila["ram_free1_mib"] = str(ram1[0])
                completo["ram1"] = ram1
            rproc = ram_proceso_mib(proc.pid)
            if rproc:
                fila["ram_proc_mib"] = fmt(rproc, 1)
                completo["ram_proc_mib"] = rproc
            log_txt2 = leer_log_server(log_path, modelo_basename=modelo_basename,
                                       puerto=puerto)
            log_txt.update({k: v for k, v in log_txt2.items()
                            if k in ("cache_reuse_warn", "cache_restored_n",
                                     "cache_forcing_n", "graphs_ok",
                                     "repack_ok")})
            tiene_reuse = any(tok == "--cache-reuse" for tok in cfg["flags"])
            fila["cache_reuse_warn"] = "SI" if log_txt.get("cache_reuse_warn") else ""
            fila["cache_restored_n"] = str(log_txt.get("cache_restored_n") or "0")
            fila["cache_forcing_n"] = str(log_txt.get("cache_forcing_n") or "0")
            fila["graphs_ok"] = "SI" if log_txt.get("graphs_ok") else ""
            fila["repack_ok"] = "SI" if log_txt.get("repack_ok") else ""
            cestado = criterio_cache(tiene_reuse,
                                     log_txt.get("cache_reuse_warn"),
                                     log_txt.get("cache_restored_n") or 0,
                                     log_txt.get("cache_forcing_n") or 0)
            fila["cache_estado"] = cestado
            completo["cache_estado"] = cestado
            if cestado == "NO-SOPORTADO":
                notas.append("cache_reuse NO SOPORTADA en este contexto "
                             "(#24055): la via queda condicionada a build/"
                             "colocacion -> RUTA 0 gana un motivo")
            elif cestado == "ROTO":
                notas.append("cache ROTO en el repro (#21831): 'forcing full "
                             "prompt re-processing' sin checkpoints utiles")
            elif cestado == "MIXTO":
                notas.append("cache MIXTA: hay restored Y forcing; leer el "
                             "repro turno a turno (JSON)")
        else:
            completo.update({"errores": list(notas)})

        fila["valido"] = "SI" if valido else "NO"
        fila["nota"] = "; ".join(notas)
        estado_run = green("VALIDO") if valido else red("INVALIDO")
        print("    decode %s t/s | prefill %s tok/s | agg %s tok/s | %s %s"
              % (bold(fmt(fila.get("decode_ts") or None)),
                 fmt(fila.get("prefill_ts") or None, 0),
                 fmt(fila.get("agg_ts") or None, 0), estado_run,
                 gray(("; " + "; ".join(notas)) if notas else "")))
    finally:
        apagar_server(proc)
    return fila, completo


# ------------------------------ informe -------------------------------------
def _dif_veredicto(dec, ancla_dec):
    """GANA/EMPATA/PIERDE vs ancla con el ruido declarado +/-0.5 (SS8)."""
    if not dec or not ancla_dec:
        return "N/D", 0.0
    dif = dec - ancla_dec
    if dif > TECHO_RUIDO:
        return "GANA", dif
    if dif >= -TECHO_RUIDO:
        return "EMPATA", dif
    return "PIERDE", dif


def protocolo_decision(resultados, ancla_dec):
    """Evalua automaticamente el arbol del N3: bookend, familia RAM, familia
    cache (certificado + TTFT), slots (probe agregado), NCM apilada, combos
    y el control NOCACHE. Devuelve lineas md."""
    lineas = []

    def dec_de(cid):
        r = resultados.get(cid) or {}
        try:
            return float(r.get("decode_ts")) if r.get("decode_ts") else None
        except (TypeError, ValueError):
            return None

    def agg_de(cid):
        r = resultados.get(cid) or {}
        try:
            return float(r.get("agg_ts")) if r.get("agg_ts") else None
        except (TypeError, ValueError):
            return None

    # ---- bookend ----
    fin = dec_de(13)
    if ancla_dec and fin:
        drift = (fin / ancla_dec - 1.0) * 100
        if abs(drift) <= 5.0:
            lineas.append("- BOOKEND ESTABLE: ancla fin %.2f vs inicio %.2f "
                          "(%+.1f%%, dentro del +/-5%%): los deltas de la "
                          "sesion se leen limpios." % (fin, ancla_dec, drift))
        else:
            lineas.append("- DERIVA DE SESION %+.1f%% (ancla %.2f -> fin "
                          "%.2f): leer los deltas con cuidado (leccion "
                          "v1.2.1: la 1a config sale lenta y el dia se "
                          "mueve)." % (drift, ancla_dec, fin))

    # ---- familia RAM (2,3,4): decode + RAM ----
    rproc_ancla = None
    try:
        rproc_ancla = float((resultados.get(1) or {}).get("ram_proc_mib") or "") or None
    except (TypeError, ValueError):
        pass
    for cid in (2, 3, 4):
        r = resultados.get(cid) or {}
        dec = dec_de(cid)
        v, dif = _dif_veredicto(dec, ancla_dec)
        if not dec:
            continue
        extra = ""
        rproc = None
        try:
            rproc = float(r.get("ram_proc_mib") or "") or None
        except (TypeError, ValueError):
            pass
        if rproc and rproc_ancla:
            delta = rproc_ancla - rproc
            if delta >= 300:
                extra = ("; RAM proceso -%.0f MiB (certificado de la dosis)"
                         % delta)
            elif delta <= -300:
                extra = ("; OJO: RAM proceso +%.0f MiB (la dosis NO libero)"
                         % (-delta))
            else:
                extra = "; RAM proceso ~plana (%+.0f MiB)" % delta
        if v == "PIERDE":
            ver = ("PIERDE (%.2f): SE DESCARTA (no se promociona una dosis "
                   "que frena)" % dif)
        elif v == "GANA":
            ver = "GANA vs ancla (+%.2f): candidata fuerte a config.txt" % dif
        else:
            ver = ("EMPATA (%+.2f, dentro del ruido): decode intacto -> "
                   "candidata a config.txt POR LA RAM, no por decode" % dif)
        lineas.append("- %s: decode %s vs ancla %s -> %s%s"
                      % (r.get("nombre"), fmt(dec), fmt(ancla_dec), ver, extra))

    # ---- familia cache (5,6): certificado + TTFT + decode ----
    for cid in (5, 6):
        r = resultados.get(cid) or {}
        dec = dec_de(cid)
        if not dec:
            continue
        v, dif = _dif_veredicto(dec, ancla_dec)
        estado = r.get("cache_estado") or "N/D"
        tver = r.get("ttft_veredicto") or "N/D"
        if estado == "NO-SOPORTADO":
            lineas.append("- %s: cache NO SOPORTADA (#24055) -> la via "
                          "cache-reuse queda condicionada a build/colocacion; "
                          "RUTA 0 gana un motivo (decode de esta sesion: %s "
                          "t/s, %s vs ancla)."
                          % (r.get("nombre"), fmt(dec), v))
        elif estado == "SANO" and tver == "PLANO":
            lineas.append("- %s: cache SANO + TTFT PLANO + decode %s vs "
                          "ancla (%s, %+.2f) -> LA JOYA CERTIFICADA: "
                          "candidata a config.txt." % (r.get("nombre"),
                                                       fmt(dec), v, dif))
        elif estado == "ROTO" or tver == "CRECE":
            lineas.append("- %s: cache %s / TTFT %s (decode %s, %s) -> el "
                          "hibrido re-procesa; mitigaciones: RUTA 0 (cpent "
                          "no existe en b11856), parche, o aceptar el coste "
                          "medido." % (r.get("nombre"), estado, tver,
                                       fmt(dec), v))
        else:
            lineas.append("- %s: cache %s / TTFT %s (decode %s, %s %+.2f) "
                          "-> revisar el JSON turno a turno antes de "
                          "decidir." % (r.get("nombre"), estado, tver,
                                        fmt(dec), v, dif))

    # ---- slots (7): probe agregado ----
    dec7 = dec_de(7)
    if dec7:
        agg7 = agg_de(7)
        agg1 = agg_de(1)
        extra = ""
        if agg7 and agg1:
            g = (agg7 / agg1 - 1.0) * 100
            extra = ("; probe agregado %.1f vs ancla %.1f tok/s (%+.1f%%)"
                     % (agg7, agg1, g))
            if g >= 5.0:
                extra += " -> concurrencia certificada."
            else:
                extra += " -> SIN ganancia de concurrencia medible."
        lineas.append("- N3-NP2: decode por slot %s vs ancla (%s %+.2f); "
                      "el +14%% [M SS4] solo aparece con 2 sesiones a la "
                      "vez.%s" % (fmt(dec7),
                                  _dif_veredicto(dec7, ancla_dec)[0],
                                  _dif_veredicto(dec7, ancla_dec)[1], extra))

    # ---- NCM apilada (8) vs historico y vs combo (10) ----
    dec8 = dec_de(8)
    if dec8:
        v, dif = _dif_veredicto(dec8, ancla_dec)
        ref = ""
        if NCM37C4_REF:
            d8 = (dec8 / NCM37C4_REF - 1.0) * 100
            ref = (" (historico NCM37C4 sin UB1K: %.2f; el stack UB1K x NCM "
                   "sale %+.1f%%)" % (NCM37C4_REF, d8))
        lineas.append("- N3-NCM37C4-UB: %s t/s vs ancla (%s, %+.2f)%s."
                      % (fmt(dec8), v, dif, ref))
    dec10 = dec_de(10)
    if dec10 and dec8:
        dif108 = dec10 - dec8
        if dif108 > TECHO_RUIDO:
            ver = ("GANA %+.2f sobre NCM37C4 sola: el combo de la SS8.1 "
                   "certifica -> candidato a config.txt con -c 4096" % dif108)
        elif dif108 >= -TECHO_RUIDO:
            ver = ("EMPATA con NCM37C4 sola (%+.2f): el cache no suma decode "
                   "ahi, pero suma RAM/TTFT; decidir con el certificado "
                   "cache de esta fila" % dif108)
        else:
            ver = ("PIERDE %+.2f vs NCM37C4 sola: revisar la VRAM de la "
                   "columna buffer/VRAM antes de descartar" % dif108)
        lineas.append("- N3-COMBO-T: %s t/s vs NCM37C4-UB de esta sesion "
                      "(%s): %s" % (fmt(dec10), fmt(dec8), ver))

    # ---- combos RAM (9): la promocion natural ----
    dec9 = dec_de(9)
    if dec9:
        v, dif = _dif_veredicto(dec9, ancla_dec)
        est9 = (resultados.get(9) or {}).get("cache_estado") or "N/D"
        tv9 = (resultados.get(9) or {}).get("ttft_veredicto") or "N/D"
        if v != "PIERDE" and est9 in ("SANO", "NO-APLICA") and tv9 != "CRECE":
            lineas.append("- N3-COMBO-R: decode %s (%s %+.2f) con RAM "
                          "liberada y cache %s/TTFT %s -> COMBO SEGURO "
                          "certificado: candidata #1 a config.txt."
                          % (fmt(dec9), v, dif, est9, tv9))
        else:
            lineas.append("- N3-COMBO-R: decode %s (%s %+.2f), cache %s, "
                          "TTFT %s -> NO se promociona tal cual; separar "
                          "dosis con --solo ram / --solo cache."
                          % (fmt(dec9), v, dif, est9, tv9))

    # ---- control NOCACHE (12): DEBE crecer ----
    r12 = resultados.get(12) or {}
    if r12.get("decode_ts"):
        tv12 = r12.get("ttft_veredicto") or "N/D"
        v12, dif12 = _dif_veredicto(dec_de(12), ancla_dec)
        if tv12 == "CRECE":
            lineas.append("- N3-NOCACHE (control): TTFT %s como se esperaba "
                          "(sin cache TODO turno re-paga); decode %s (%s "
                          "%+.2f): el cache no paga decode, paga TTFT."
                          % (tv12, fmt(dec_de(12)), v12, dif12))
        else:
            lineas.append("- N3-NOCACHE (control): TTFT %s INESPERADO "
                          "(deberia CREcer sin cache) -> revisar el log "
                          "(el cache quizas no se apago de verdad)."
                          % tv12)
    return lineas


def generar_informe(dir_logs, contexto, resultados, completos, problemas_flags):
    md = []
    md.append("# INFORME FASE N3 — NIVEL 3: eficiencia simple (cosecha)")
    md.append("")
    md.append("Generado: %s · %s · proto %s" % (ahora(), VERSION, PROTO))
    md.append("")
    prev = contexto.get("prevuelo")
    if prev:
        # v1.1: la seccion 0 es el dossier completo PC + modelo + nivel
        md.extend(md_prevuelo(prev["pc"], prev["modelo"], prev["nivel"],
                              contexto, problemas_flags))
    else:
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
        md.append("- Auditoria de flags: %s"
                  % ("VERDE - todos los tokens verbatim en el dump b11856"
                     if not problemas_flags else "FALLOS: %s" % problemas_flags))
        md.append("- Comando base por config (LA RECETA DIARIA + -lv 4): `%s` "
                  "(+ diff de la config; el ultimo valor gana)"
                  % (contexto.get("base_flags_str") or "N/D"))
        md.append("")
    md.append("## 1. Resultados")
    md.append("")
    ancla_dec = None
    a1 = resultados.get(1) or {}
    try:
        ancla_dec = float(a1.get("decode_ts")) if a1.get("decode_ts") else None
    except (TypeError, ValueError):
        ancla_dec = None
    md.append("Ancla de sesion (N3-ANCLA = receta diaria): %s t/s "
              "(referencia barrido-30 ORO-UB1K: %.2f; la de HOY manda)"
              % (fmt(ancla_dec), ANCLA_UB1K))
    md.append("")
    md.append("| id | config | flags diff | decode t/s | vs ancla | prefill | "
              "cache | TTFT (t2->tfin) | RAM proc MiB | agg tok/s | VRAM MiB | "
              "sanity | valido |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for cid in sorted(resultados):
        r = resultados[cid]
        d = None
        try:
            d = float(r.get("decode_ts")) if r.get("decode_ts") else None
        except (TypeError, ValueError):
            d = None
        delta = ("+%0.1f%%" % ((d / ancla_dec - 1) * 100)
                 if (d and ancla_dec) else "N/D")
        flags_cortos = (r.get("flags") or "").replace(
            contexto.get("base_flags_str", ""), "").strip()
        ttft = "-"
        if r.get("ttft_t2") or r.get("ttft_tfin"):
            ttft = "%s -> %s s (%s)" % (fmt(r.get("ttft_t2"), 2),
                                        fmt(r.get("ttft_tfin"), 2),
                                        r.get("ttft_veredicto") or "N/D")
        okn = r.get("sanity_ok_n") or "-"
        trn = r.get("sanity_trunc_n") or ""
        san_txt = ("%s+%sT/%s" % (okn, trn, r.get("sanity_total") or "-")
                   if trn not in ("", "0") else
                   "%s/%s" % (okn, r.get("sanity_total") or "-"))
        md.append("| %s | %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s/%s | "
                  "%s | %s |"
                  % (cid, r.get("nombre"), flags_cortos or "BASE",
                     fmt(d), delta, fmt(r.get("prefill_ts"), 0),
                     r.get("cache_estado") or "-", ttft,
                     r.get("ram_proc_mib") or "N/D",
                     r.get("agg_ts") or "N/D",
                     r.get("vram_usada_mib") or "N/D",
                     r.get("vram_total_mib") or "N/D",
                     san_txt, r.get("valido") or ""))
    md.append("")
    md.append("Referencias historicas del barrido-30 [M]: ORO-UB1K (ancla de "
              "la receta diaria) = %.2f t/s - NCM37C4 (sin UB1K) = %.2f - "
              "ORO-CRAM512 = %.2f (decode intacto, -7.7 GB) - ORO-SHIFT "
              "(shift+reuse) = %.2f. Ruido declarado +/-0.3-0.5 t/s; el "
              "mismo config abarca 9.4pp entre corridas (thc1006 v4): "
              "mediana de 3 antes de proclamar ganancias."
              % (ANCLA_UB1K, NCM37C4_REF, CRAM512_REF, SHIFT_REF))
    md.append("")
    md.append("## 2. Certificados de cache (lineas de log + repro)")
    md.append("")
    md.append("| id | config | warning #24055 | restored | forcing #21831 | "
              "estado |")
    md.append("|---|---|---|---|---|---|")
    for cid in sorted(resultados):
        r = resultados[cid]
        md.append("| %s | %s | %s | %s | %s | %s |"
                  % (cid, r.get("nombre"),
                     r.get("cache_reuse_warn") or "-",
                     r.get("cache_restored_n") or "-",
                     r.get("cache_forcing_n") or "-",
                     r.get("cache_estado") or "-"))
    md.append("")
    md.append("Lectura: NO-APLICA = la config no lleva --cache-reuse · "
              "NO-SOPORTADO = el build declino la cache en el arranque "
              "(#24055) · SANO = checkpoints restaurados y cero re-procesado "
              "· ROTO = 'forcing full prompt re-processing' (#21831, el "
              "hibrido re-paga el prompt) · MIXTO/SIN-DATOS = leer el JSON.")
    md.append("")
    md.append("## 3. Protocolo de decision N3 (evaluacion automatica)")
    md.append("")
    md.extend(protocolo_decision(resultados, ancla_dec) or
              ["- (sin datos suficientes)"])
    md.append("")
    md.append("## 4. Recuerdos de la casa aplicados")
    md.append("")
    md.append("- Protocolo SS8 verbatim: 4 pasadas x 256 tokens, se descarta "
              "la 1a, temp 0, prompts distintos, seed fija; ruido declarado "
              "+/-0.3-0.5 t/s.")
    md.append("- Estudio thc1006 v4 (SS13): el mismo config abarca 9.4 pp "
              "entre corridas -> las celdas que GANEN aqui se confirman con "
              "mediana de 3 corridas (o --quick en otro bloque horario) "
              "ANTES de proclamar la ganancia; nunca comparar contra el "
              "ancla de OTRA sesion.")
    md.append("- El libro de muertos del N3 NO se re-mide: ngram spec "
              "(acceptance 0.00-0.16), afinidad (-9..-38%), FIT-C (-38%), "
              "repack off (-5%), KV q5_1 (0%), POLL/TB8 (ruido/muerto).")
    md.append("- Sanity manual de 20 prompts del Director: sigue siendo la "
              "puerta de calidad completa (la auto de 3 pares solo es "
              "humo-detector).")
    md.append("- PROMOCION: las candidatas a config.txt que salgan aqui se "
              "promueven editando UNA linea de FLAGS_BASE (pago del config "
              "central, ronda 20); la aprobacion formal es del Director.")
    md.append("- Si la cache sale NO-SOPORTADO o ROTO en b11856: queda "
              "registrado como MOTIVO DE RUTA 0 (build nuevo con cpent / "
              "fix del checkpoint), no como fracaso de la idea.")
    md.append("")
    md.append("## 5. Archivos de esta corrida")
    md.append("")
    md.append("- CSV: `faseN3-resultados.csv` (reanudable)")
    md.append("- Datos: `faseN3-datos.json` (repro TTFT turno a turno, "
              "sanity, probe agregado, RAM)")
    md.append("- Consola: `faseN3-consola.log`")
    md.append("- Logs del server: `logs-config/NN-nombre.log`")
    md.append("")
    ruta_md = os.path.join(dir_logs, "faseN3-INFORME.md")
    open(ruta_md, "w", encoding="utf-8").write("\n".join(md) + "\n")

    datos_json = {"version": VERSION, "proto": PROTO, "fecha": ahora(),
                  "contexto": {k: v for k, v in contexto.items()
                               if k not in ("tee",)},
                  "runs": list(completos.values())}
    open(os.path.join(dir_logs, "faseN3-datos.json"), "w",
         encoding="utf-8").write(json.dumps(datos_json, ensure_ascii=False,
                                            indent=1, default=str))
    return ruta_md


# ------------------------------- main ---------------------------------------
def main(argv=None):
    global PUERTO_DEF
    ap = argparse.ArgumentParser(
        description=VERSION + " — cosecha del nivel 3 (eficiencia simple)")
    ap.add_argument("--quick", action="store_true",
                    help="solo 5 configs criticas (~18 min)")
    ap.add_argument("--solo", type=str, default="",
                    help="bloques separados por coma: "
                         "ancla,ram,cache,slots,ncm,combo,ctrl,anclafin")
    ap.add_argument("--server", type=str, default=RUTA_SERVER_DEF)
    ap.add_argument("--modelo", type=str, default=RUTA_MODELO_DEF)
    ap.add_argument("--logs", type=str, default=LOGS_DIR_DEF)
    ap.add_argument("--puerto", type=int, default=PUERTO_DEF)
    ap.add_argument("--carga-timeout", type=int, default=600)
    ap.add_argument("--si", action="store_true",
                    help="matar un server vivo antes de empezar")
    ap.add_argument("--sin-ttft", action="store_true",
                    help="saltar el repro de turnos crecientes")
    ap.add_argument("--sin-probe", action="store_true",
                    help="saltar el probe de concurrencia")
    ap.add_argument("--sin-sanity", action="store_true")
    ap.add_argument("--sin-nvidia", action="store_true")
    ap.add_argument("--sin-pausas", action="store_true")
    ap.add_argument("--sin-prevuelo", action="store_true",
                    help="omitir el dossier completo PC/modelo/nivel (v1.0)")
    ap.add_argument("--sin-sha256", action="store_true",
                    help="prevuelo sin el hash del modelo (~1 min ahorro)")
    args = ap.parse_args(argv)

    PUERTO_DEF = args.puerto
    # el comando lanzado es SIEMPRE base + diff (el ultimo valor gana);
    # la base = LA RECETA DIARIA (config.txt FLAGS_BASE + FLAGS_GANADORAS,
    # auditoria R24) + -lv 4 para los certificados del log.
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
    tee = Tee(os.path.join(args.logs, "faseN3-consola.log"))
    sys.stdout = tee
    sys.stderr = tee

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

    configs = filtrar_configs(construir_configs(), solo=args.solo,
                              quick=args.quick)

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

    # ---- certificado de receta + colocacion (v1.3, hotfix de campo) -------
    # el campo 28-oct paso la auditoria VERDE y aun asi murio 11 configs: la
    # auditoria ve TOKENS en el dump, no la RECETA COMPLETA del comando.
    ancla_ref = next((c for c in construir_configs() if c["id"] == 1), None)
    if ancla_ref is not None:
        faltan = verificar_receta(list(base_flags) + list(ancla_ref["flags"]))
        if faltan:
            raise SystemExit(red(
                "FATAL: la receta base NO es la diaria certificada: faltan "
                "%s (config.txt FLAGS_BASE + FLAGS_GANADORAS). Sin la receta "
                "diaria el ancla no es el ancla: nada se mide."
                % ", ".join(faltan)))
        print(green("  VERDE: receta diaria certificada en el ancla "
                    "(incluida la colocacion -cmoe)"))
    sin_coloc = verificar_colocacion(configs, base_flags)
    if sin_coloc:
        raise SystemExit(red(
            "FATAL: configs SIN colocacion (-cmoe/-ncmoe): %s (leccion "
            "barrido-30: sin colocacion el modelo de 14.27 GB no cabe en la "
            "GPU de 4 GB y el server muere en la carga)"
            % ", ".join(sin_coloc)))
    print(green("  VERDE: colocacion por config en %d/%d configs"
                % (len(configs) - len(sin_coloc), len(configs))))

    if args.si:
        matar_server_vivo(args.puerto)
    elif health_ok(args.puerto):
        raise SystemExit(red("FATAL: /health ya responde en el puerto %d. Hay "
                             "un server vivo (medir con el falsea todo). "
                             "Cerrarlo o relanzar con --si." % args.puerto))

    # ---- 0.5 prevuelo completo (PC + modelo + nivel) -----------------------
    prevuelo = None
    if not args.sin_prevuelo:
        print(cyan("[0.5] PREVUELO COMPLETO: PC + modelo + nivel "
                   "(~1-2 min por el sha256 del modelo; --sin-sha256 lo salta)"))
        pc_d = dossier_pc(con_nvidia=not args.sin_nvidia)
        mod_d = dossier_modelo(args.modelo, bytes_modelo, pin,
                               con_sha=not args.sin_sha256, notificador=print)
        niv_d = dossier_nivel(configs)
        prevuelo = {"pc": pc_d, "modelo": mod_d, "nivel": niv_d}
        imprimir_prevuelo(pc_d, mod_d, niv_d)
    else:
        print(gray("  --sin-prevuelo: dossier omitido (comportamiento v1.0)"))

    contexto = {"ruta_server": args.server, "ruta_modelo": args.modelo,
                "dir_logs": args.logs, "pin": pin,
                "bytes_modelo": bytes_modelo,
                "carga_timeout": args.carga_timeout,
                "con_sanity": not args.sin_sanity,
                "sin_nvidia": args.sin_nvidia,
                "sin_ttft": args.sin_ttft,
                "sin_probe": args.sin_probe,
                "puerto": args.puerto,
                "base_flags_str": " ".join(base_flags),
                "base_flags": base_flags,
                "prevuelo": prevuelo}

    # ---- 1. corrida --------------------------------------------------------
    print(cyan("[1] CORRIDA: %d configs (pausa termica %d s cada %d)"
               % (len(configs), PAUSA_TERMICA_S, PAUSA_CADA)))
    ruta_csv = csv_ruta(args.logs)
    proto_viejo = csv_proto_de(ruta_csv)
    if proto_viejo and proto_viejo != PROTO:
        destino = os.path.join(args.logs,
                               "faseN3-resultados-%s.csv" % proto_viejo)
        try:
            os.replace(ruta_csv, destino)
            print(yellow("  proto nuevo (%s): el CSV '%s' se ARCHIVA como %s "
                         "(nada se borra); la corrida es completa"
                         % (PROTO, proto_viejo, os.path.basename(destino))))
        except Exception as e:
            print(yellow("  AVISO: no pude archivar el CSV de %s (%r)"
                         % (proto_viejo, e)))
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
            if (hechas_sesion and hechas_sesion % PAUSA_CADA == 0
                    and not args.sin_pausas and PAUSA_TERMICA_S > 0):
                print(yellow("  pausa termica %d s (protege la medicion)..."
                             % PAUSA_TERMICA_S))
                time.sleep(PAUSA_TERMICA_S)
            try:
                fila, completo = medir_config(cfg, contexto)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                # una config JAMAS tumba el barrido (leccion v1.1 del N1)
                fila = {c: "" for c in COLUMNAS}
                fila.update({"proto": PROTO, "id": cfg["id"],
                             "nombre": cfg["nombre"], "familia": cfg["familia"],
                             "fecha_hora": ahora(), "valido": "NO",
                             "nota": "excepcion no capturada: %r" % e})
                completo = {"id": cfg["id"], "nombre": cfg["nombre"],
                            "familia": cfg["familia"], "valido": False,
                            "nota": fila["nota"], "excepcion": repr(e)}
                print(red("  [%02d] EXCEPCION no capturada: %r" % (cfg["id"], e)))
            if (cfg["id"] != 1 and fila.get("decode_ts")
                    and (resultados.get(1) or {}).get("decode_ts")):
                try:
                    fila["delta_vs_ancla_pct"] = "%.1f" % (
                        (float(fila["decode_ts"])
                         / resultados[1]["decode_ts"] - 1.0) * 100)
                except (TypeError, ValueError, ZeroDivisionError):
                    pass
            csv_append(ruta_csv, fila)
            try:
                dec = float(fila.get("decode_ts") or "") or None
            except Exception:
                dec = None
            resultados[cfg["id"]] = dict(fila)
            resultados[cfg["id"]]["decode_ts"] = dec
            completos[cfg["id"]] = completo
            hechas_sesion += 1
            # ---- ancla muerta = FATAL (v1.3, campo 28-oct) -----------------
            # sin baseline de sesion el protocolo entero queda sin pata
            # (bookend imposible, deltas N/D): seguir midiendo es tirar el
            # dia. La fila queda en el CSV y el resume re-mide sola.
            if cfg["id"] == 1 and fila.get("valido") != "SI":
                print(red("  cola del log del ancla: %s"
                          % (completos.get(1, {}).get("log_cola") or "N/D")))
                raise SystemExit(red(
                    "FATAL: el ANCLA (id 1 = la receta diaria) no cargo (%s). "
                    "Sin ancla no hay baseline: bookend imposible y deltas "
                    "N/D -> nada mas se mide en esta sesion. Causa tipica: la "
                    "receta base no coincide con config.txt (colocacion -cmoe "
                    "ausente = el modelo no cabe en la GPU). Revisar "
                    "logs-config/01-N3-ANCLA.log; el resume re-mide sola esta "
                    "config al repetir el comando." % fila.get("nota", "")))
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
    print(green("  %s" % os.path.join(args.logs, "faseN3-datos.json")))
    print(green("  %s" % os.path.join(args.logs, "faseN3-consola.log")))
    print("")
    print(bold("Para pasar al analisis: faseN3-INFORME.md + "
               "faseN3-resultados.csv (+ carpeta logs-config si se pide)."))
    return 130 if interrumpido else 0


if __name__ == "__main__":
    sys.exit(main())
