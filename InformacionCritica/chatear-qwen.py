#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chatear-qwen.py — Cliente de chat TOKEN A TOKEN con metricas para el rig
=========================================================================
Habla con Qwen APEX-I-MINI servido por llama-server b11856 (9931).
Companero del lanzador: ABRIR-QWEN.bat abre el server en una ventana;
este cliente corre en OTRA ventana (doble click en CHATEAR-QWEN.bat).

QUE HACE:
  · Streaming token a token: el thinking se muestra en gris (canal propio)
    y la respuesta en blanco. Compatible con los dos formatos del server:
    reasoning separado (delta.reasoning_content) y tags <think> inline.
  · Metricas POR TURNO: tokens, tok/s de generacion, TTFT (tiempo al 1er
    token), prefill ~aprox, y CTX usada del server vs el -c del rig.
  · t/s EN VIVO (v1.1): mientras genera, el titulo de la ventana muestra
    el tok/s del momento; al cerrar el turno queda el del turno completo.
  · /modo N (v1.1): etiqueta los turnos con los expertos del server abierto
    (8 trabajo / 4 charla). /stats y /guardar comparan tok/s POR MODO.
  · Metricas acumuladas de sesion: /stats (turnos, tokens, tok/s medio).

METRICAS — de donde salen (nada inventado):
  · Cliente mide SIEMPRE: reloj + conteo de chunks (1 chunk ~ 1 token,
    llama.cpp stream) -> tok/s y TTFT son reales aunque el server no
    reporte usage. Marcadas con ~ cuando son aproximadas.
  · Server: si responde usage (se pide stream_options include_usage;
    si tu build lo ignora, no pasa nada) -> ctx real (prompt_tokens),
    completion_tokens y prefill ~prompt/TTFT. El cross-check sale al final.
  · Aceptacion del draft MTP: solo vive en el LOG del server (ventana
    donde corre ABRIR-QWEN.bat); este cliente no puede verla.

SAMPLING POR REQUEST (doc config-sampling-qwen36.md §3.2, verificado):
  /preset think|coding|fast  cambia temperature/top_p/top_k/min_p/presence
  /temp N                    override ad-hoc. NO greedy: /temp 0 se rechaza
                             (card oficial Qwen3.6: nunca temperature 0).

HISTORIAL: multi-turno en memoria; la respuesta se guarda SIN thinking
(limpio) — el server b11856 gestiona el preserve del trace (--reasoning-
preserve ya ON en el build, dump verbatim). /reset borra la conversacion.

COMANDOS: /ayuda /reset /sistema /preset /temp /modo /stats /guardar /salir
REQUISITOS: Python 3.8+ solo stdlib. Server abierto en otra ventana.
Rutas y puerto sobreescribibles: CLI --host/--port (default 127.0.0.1:9931).
"""

import argparse
import ctypes
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

if sys.version_info < (3, 8):
    raise SystemExit("Se requiere Python 3.8 o superior.")

# ------------------------------------------------------------------ constantes
PORT_DEFAULT = 9931      # dump verbatim: default del server b11856 (v0.7.0)
CTX_RIG = 16384          # -c del lanzador; ahora se hereda de config.txt

CONFIG_OFICIAL = r"D:\ZLia\config.txt"   # misma fuente que abrir-qwen-apex.py


def _config_central():
    """Lee config.txt (ruta oficial D:\\ZLia\\config.txt o junto a este
    script). Devuelve {} si no existe — el cliente usa sus defaults y
    los --host/--port de la linea de comandos SIEMPRE ganan."""
    candidatas = [CONFIG_OFICIAL,
                  os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "config.txt")]
    for ruta in candidatas:
        try:
            if not os.path.exists(ruta):
                continue
            cfg = {}
            with open(ruta, "r", encoding="utf-8", errors="replace") as f:
                for linea in f:
                    linea = linea.strip()
                    if linea and not linea.startswith("#") and "=" in linea:
                        k, _, v = linea.partition("=")
                        cfg[k.strip()] = v.strip()
            if cfg:
                return cfg
        except Exception:
            pass
    return {}

# Sampling oficial Qwen3.6 (card + generation_config, fetch 2026-10-25;
# doc config-sampling-qwen36.md §1) — mismo set que inyecta el lanzador,
# aqui en formato API por-request (§3.2: overwrites al vuelo verificados).
SAMPLING_API = {
    "think":  {"temperature": 1.0, "top_k": 20, "top_p": 0.95,
               "min_p": 0.0, "presence_penalty": 0.0},
    "coding": {"temperature": 0.6, "top_k": 20, "top_p": 0.95,
               "min_p": 0.0, "presence_penalty": 0.0},
    "fast":   {"temperature": 0.7, "top_k": 20, "top_p": 0.80,
               "min_p": 0.0, "presence_penalty": 1.5},
}

TAG_A = "<think>"
TAG_C = "</think>"

ESTADO = {
    "messages": [],       # [{role, content}] SIN thinking del assistant
    "system": None,       # system prompt opcional (/sistema)
    "preset": "think",
    "modo": None,         # expertos del server abierto (/modo 8|4) — etiqueta
    "temp_override": None,
    "turnos": [],         # resumenes de metricas por turno (para /guardar)
    "acum": {"turnos": 0, "tokens": 0, "t_gen": 0.0, "mejor": 0.0},
}

# ------------------------------------------------------------------ color
class C:
    on = False            # ANSI habilitado?

GRA = "90"   # thinking
AMA = "33"   # metricas
ROJ = "91"   # errores
VER = "92"   # ok
CIA = "96"   # banner / prompt


def pintar(cod, s):
    return "\x1b[{}m{}\x1b[0m".format(cod, s) if C.on else s


def activar_color():
    if not sys.stdout.isatty():
        return                        # piped: sin codigos de color
    if os.name != "nt":
        C.on = True
        return
    try:                              # habilitar VT en consola de Windows
        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-11)
        modo = ctypes.c_uint32()
        if k32.GetConsoleMode(h, ctypes.byref(modo)):
            if k32.SetConsoleMode(h, modo.value | 0x0004):
                C.on = True
    except Exception:
        pass                          # consola sin VT: sin color, sin fallo


def titulo(s):
    """Titulo de la ventana de consola (Windows nativo / OSC en POSIX).
    Silencioso fuera de TTY: en tests y pipes no toca nada."""
    if not sys.stdout.isatty():
        return
    try:
        if os.name == "nt":
            ctypes.windll.kernel32.SetConsoleTitleW(s)
        else:
            sys.stdout.write("\x1b]2;{}\x07".format(s))
            sys.stdout.flush()
    except Exception:
        pass                          # sin titulo: nunca un fallo


# ------------------------------------------------------------------ servidor
def url_base(host, port):
    return "http://{}:{}".format(host, port)


def comprobar_salud(host, port):
    """GET /health (endpoint ya usado por el lanzador). True/False/cargando."""
    try:
        with urllib.request.urlopen(
                url_base(host, port) + "/health", timeout=4) as r:
            return ("ok", r.status == 200)
    except urllib.error.HTTPError as e:
        if e.code == 503:
            return ("cargando", False)
        return ("error", False)
    except Exception:
        return ("apagado", False)


def stream_chat(host, port, cuerpo, timeout=600):
    """POST /v1/chat/completions stream=True -> generador de eventos SSE."""
    req = urllib.request.Request(
        url_base(host, port) + "/v1/chat/completions",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for linea in r:                       # bytes, una linea SSE por vez
            linea = linea.strip()
            if not linea.startswith(b"data:"):
                continue
            payload = linea[5:].strip()
            if payload == b"[DONE]":
                return
            try:
                yield json.loads(payload.decode("utf-8", "replace"))
            except ValueError:
                continue                      # linea malformada: saltar


# ------------------------------------------------------------------ <think>
def _retener_cola(buf, tag):
    """Cuantos chars del final de buf son prefijo PROPIO de tag (tag partido
    entre chunks). No emite nada que pueda formar parte del tag."""
    maximo = min(len(buf), len(tag) - 1)
    for k in range(maximo, 0, -1):
        if tag.startswith(buf[-k:]):
            return k
    return 0


class CanalThinking:
    """Divide el stream content en partes (canal, texto): 'think' | 'out'.
    Estado: dentro/fuera de <think>. Sobrevive a tags partidos en chunks."""

    def __init__(self):
        self.modo = "out"
        self.buf = ""
        self.out_acumulado = ""        # respuesta final SIN thinking

    def alimentar(self, texto):
        self.buf += texto
        partes = []
        while self.buf:
            tag = TAG_C if self.modo == "think" else TAG_A
            nuevo = "out" if self.modo == "think" else "think"
            i = self.buf.find(tag)
            if i >= 0:
                if i:
                    partes.append((self.modo, self.buf[:i]))
                self.buf = self.buf[i + len(tag):]
                self.modo = nuevo
            else:
                k = _retener_cola(self.buf, tag)
                if k < len(self.buf):
                    partes.append((self.modo, self.buf[:len(self.buf) - k]))
                    self.buf = self.buf[len(self.buf) - k:]
                break
        for c, t in partes:
            if c == "out":
                self.out_acumulado += t
        return partes

    def vaciar(self):
        partes = []
        if self.buf:                          # tag sin cerrar (corte, etc.)
            partes.append((self.modo, self.buf))
            self.buf = ""
        for c, t in partes:
            if c == "out":
                self.out_acumulado += t
        return partes


# ------------------------------------------------------------------ turno
def impresor_turno():
    """Devuelve (emitir, cerrar): imprime token a token con canal color."""
    estado_canal = {"actual": None}

    def emitir(canal, texto):
        if not texto:
            return
        if estado_canal["actual"] != canal:
            if estado_canal["actual"] in ("think", "out"):
                print()                       # nueva linea al cambiar de canal
            if canal == "think" and estado_canal["actual"] != "think":
                print(pintar(GRA, "(pensando) "), end="", flush=True)
            estado_canal["actual"] = canal
        print(pintar(GRA, texto) if canal == "think" else texto,
              end="", flush=True)

    def cerrar():
        if estado_canal["actual"] is not None:
            print()
        return estado_canal["actual"]

    return emitir, cerrar


def responder_turno(host, port):
    """Un turno completo: envia historial, imprime stream, devuelve metricas."""
    msgs = []
    if ESTADO["system"]:
        msgs.append({"role": "system", "content": ESTADO["system"]})
    msgs += ESTADO["messages"]
    cuerpo = {"messages": msgs, "stream": True,
              "stream_options": {"include_usage": True}}
    cuerpo.update(SAMPLING_API[ESTADO["preset"]])
    if ESTADO["temp_override"] is not None:
        cuerpo["temperature"] = ESTADO["temp_override"]

    canal = CanalThinking()
    emitir, cerrar = impresor_turno()
    m = {"n_tok": 0, "ttft": None, "t_gen": 0.0, "total": 0.0,
         "prompt_tokens": None, "completion_tokens": None, "cortado": False,
         "modo": ESTADO["modo"]}
    t0 = time.perf_counter()
    vivo = {"t_1er": None, "t_ult": t0}   # tok/s en vivo para el titulo
    sufijo = " · modo {}".format(ESTADO["modo"]) if ESTADO["modo"] else ""

    def titulo_vivo():
        """Contador de tok/s en el titulo (cada 0.5s, con >=4 tokens)."""
        ahora = time.perf_counter()
        if (vivo["t_1er"] is None or m["n_tok"] < 4
                or ahora - vivo["t_ult"] < 0.5):
            return
        vivo["t_ult"] = ahora
        gen = ahora - vivo["t_1er"]
        if gen > 0:
            titulo("Qwen · {:.1f} tok/s{}".format(
                m["n_tok"] / gen, sufijo))

    try:
        for ev in stream_chat(host, port, cuerpo):
            titulo_vivo()
            if ev.get("usage"):
                u = ev["usage"]
                m["prompt_tokens"] = u.get("prompt_tokens")
                m["completion_tokens"] = u.get("completion_tokens")
                continue
            choices = ev.get("choices") or []
            if not choices:
                continue
            d = choices[0].get("delta") or {}
            if d.get("reasoning_content"):    # thinking separado (server)
                if vivo["t_1er"] is None:
                    vivo["t_1er"] = time.perf_counter()
                m["n_tok"] += 1
                emitir("think", d["reasoning_content"])
            texto = d.get("content")
            if texto:
                if vivo["t_1er"] is None:
                    vivo["t_1er"] = time.perf_counter()
                m["n_tok"] += 1
                for c, t in canal.alimentar(texto):
                    emitir(c, t)
    except KeyboardInterrupt:
        m["cortado"] = True
    except urllib.error.URLError as e:
        cerrar()
        print(pintar(ROJ, "  [FALLO] el server no responde: {}".format(
            getattr(e, "reason", e))))
        return None
    finally:
        if not m["cortado"]:
            for c, t in canal.vaciar():
                emitir(c, t)
        cerrar()

    m["total"] = time.perf_counter() - t0
    if vivo["t_1er"] is not None:
        m["ttft"] = vivo["t_1er"] - t0
        m["t_gen"] = m["total"] - m["ttft"]
    ts_fin = tok_s(m)
    titulo("Qwen · {} tok/s{}".format(
        "{:.1f}".format(ts_fin) if ts_fin else "n/d", sufijo))
    # respuesta SIN thinking (historial limpio; el server gestiona preserve)
    m["respuesta"] = canal.out_acumulado if not m["cortado"] else None
    return m


# ------------------------------------------------------------------ metricas
def tok_s(m):
    return m["n_tok"] / m["t_gen"] if m["t_gen"] > 0 and m["n_tok"] else None


def linea_metricas(m):
    partes = []
    if m.get("modo") is not None:
        partes.append("modo {}".format(m["modo"]))
    if m["completion_tokens"] is not None:
        partes.append("{:,} tok".format(m["completion_tokens"]))
    else:
        partes.append("~{} tok".format(m["n_tok"]))
    ts = tok_s(m)
    if ts:
        partes.append("{:.1f} tok/s".format(ts))
    if m["ttft"] is not None:
        partes.append("1er tok {:.1f}s".format(m["ttft"]))
    if m["prompt_tokens"] is not None and m["ttft"] is not None and m["ttft"] > 0:
        partes.append("~{:.0f} tok/s prefill".format(
            m["prompt_tokens"] / m["ttft"]))
    if m["prompt_tokens"] is not None:
        pct = 100.0 * m["prompt_tokens"] / CTX_RIG
        partes.append("ctx {:,}/{:,} ({:.1f}%)".format(
            m["prompt_tokens"], CTX_RIG, pct))
    else:
        partes.append("ctx n/d")
    partes.append("{:.1f}s total".format(m["total"]))
    return "  ·  ".join(partes)


def imprimir_metricas(m):
    print(pintar(AMA, "  " + "-" * 68))
    print(pintar(AMA, "  " + linea_metricas(m)))
    if m["cortado"]:
        print(pintar(AMA, "  turno INTERRUMPIDO (Ctrl+C) — no entra al historial"))


def registrar_turno(m):
    ts = tok_s(m) or 0.0
    ESTADO["acum"]["turnos"] += 1
    ESTADO["acum"]["tokens"] += m["n_tok"]
    ESTADO["acum"]["t_gen"] += m["t_gen"]
    ESTADO["acum"]["mejor"] = max(ESTADO["acum"]["mejor"], ts)
    ESTADO["turnos"].append({
        "hora": datetime.now().strftime("%H:%M:%S"),
        "ts": ts,
        "modo": m.get("modo"),
        "metricas": linea_metricas(m),
    })


# ------------------------------------------------------------------ comandos
AYUDA = """  /ayuda                    esta ayuda
  /reset                    borra la conversacion (mantiene system/preset)
  /sistema <texto>          fija el system prompt (/sistema solo: lo limpia)
  /preset think|coding|fast sampling oficial Qwen3.6 por request (§3.2)
  /temp N                   temperature ad-hoc (/temp solo: volver al preset;
                            NO greedy: temp 0 rechazado — card Qwen3.6)
  /modo N                   etiqueta los turnos con los expertos del server
                            abierto (/modo 4 tras abrir CHARLA; /modo solo: quita)
  /stats                    metricas acumuladas (agrupa tok/s por /modo)
  /guardar                  transcript a chat-qwen-FECHA.md
  /salir                    cerrar"""


def muestrear_descripcion(preset, override=None):
    s = SAMPLING_API[preset]
    t = override if override is not None else s["temperature"]
    return "{} (T {}/top-k {}/top-p {}/min-p {}/presencia {})".format(
        preset, t, s["top_k"], s["top_p"], s["min_p"], s["presence_penalty"])


def ejecutar_comando(linea, host, port):
    trozos = linea.split(maxsplit=1)
    cmd = trozos[0].lower()
    resto = trozos[1].strip() if len(trozos) > 1 else ""

    if cmd in ("/salir", "/quit", "/exit"):
        return False
    if cmd in ("/ayuda", "/help", "/?"):
        print(pintar(CIA, AYUDA))
    elif cmd == "/reset":
        ESTADO["messages"] = []
        print(pintar(VER, "  conversacion borrada (historial limpio)."))
    elif cmd == "/sistema":
        ESTADO["system"] = resto or None
        print(pintar(VER, "  system: " + (ESTADO["system"] or "(limpio)")))
    elif cmd == "/preset":
        if resto in SAMPLING_API:
            ESTADO["preset"] = resto
            ESTADO["temp_override"] = None
            print(pintar(VER, "  sampling: " +
                         muestrear_descripcion(resto)))
        else:
            print(pintar(ROJ, "  preset invalido. Opciones: " +
                         ", ".join(SAMPLING_API)))
    elif cmd == "/temp":
        if not resto:
            ESTADO["temp_override"] = None
            print(pintar(VER, "  temperature: vuelve al preset (" +
                         muestrear_descripcion(ESTADO["preset"]) + ")"))
            return True
        try:
            v = float(resto.replace(",", "."))
        except ValueError:
            print(pintar(ROJ, "  /temp N — numero, no '{}'".format(resto)))
            return True
        if v <= 0:
            print(pintar(ROJ, "  NO greedy: la card de Qwen3.6 prohíbe "
                         "temperature 0 (repite en bucle). Usa /temp 0.05 "
                         "o menor si quieres casi-determinismo."))
            return True
        ESTADO["temp_override"] = min(v, 2.0)
        print(pintar(VER, "  temperature {} (por request)".format(
            ESTADO["temp_override"])))
    elif cmd == "/modo":
        if not resto:
            ESTADO["modo"] = None
            print(pintar(VER, "  modo: sin etiqueta (los turnos dejan "
                         "de agruparse)."))
        elif resto.isdigit() and int(resto) > 0:
            ESTADO["modo"] = int(resto)
            print(pintar(VER, "  modo: {} expertos — etiqueta los turnos "
                         "siguientes (para /stats y /guardar).".format(
                             ESTADO["modo"])))
        else:
            print(pintar(ROJ, "  /modo N — numero de expertos del server "
                         "abierto (ej: /modo 8, /modo 4)."))
    elif cmd == "/stats":
        a = ESTADO["acum"]
        medio = a["tokens"] / a["t_gen"] if a["t_gen"] > 0 else 0.0
        print(pintar(AMA, "  turnos {} · ~{} tok · tok/s medio {:.1f} · "
                     "mejor turno {:.1f} tok/s · tiempo gen {:.1f}s".format(
                         a["turnos"], a["tokens"], medio,
                         a["mejor"], a["t_gen"])))
        grupos = {}
        for t in ESTADO["turnos"]:
            grupos.setdefault(t.get("modo"), []).append(t["ts"])
        for modo, lista in sorted(grupos.items(),
                                  key=lambda kv: (kv[0] is None, kv[0] or 0)):
            et = "modo {}".format(modo) if modo is not None else "(sin modo)"
            print(pintar(AMA, "  {}: {} turno{} · {:.1f} tok/s medio "
                         "(max {:.1f})".format(
                             et, len(lista), "" if len(lista) == 1 else "s",
                             sum(lista) / len(lista), max(lista))))
    elif cmd == "/guardar":
        guardar_transcript()
    else:
        print(pintar(ROJ, "  comando desconocido: {} (/ayuda)".format(cmd)))
    return True


def guardar_transcript():
    nombre = "chat-qwen-{}.md".format(
        datetime.now().strftime("%Y%m%d-%H%M%S"))
    a = ESTADO["acum"]
    with open(nombre, "w", encoding="utf-8") as f:
        f.write("# Chat Qwen APEX-I-MINI ({})\n\n".format(
            datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write("- preset: {}\n".format(muestrear_descripcion(
            ESTADO["preset"], ESTADO["temp_override"])))
        f.write("- server: llama.cpp b11856, puerto 9931, ctx {}\n\n".format(
            CTX_RIG))
        if ESTADO["system"]:
            f.write("**System:** {}\n\n".format(ESTADO["system"]))
        for turno in ESTADO["turnos"]:
            f.write("- turno {}: {}\n".format(turno["hora"],
                                              turno["metricas"]))
        f.write("\n---\n\n")
        for msg in ESTADO["messages"]:
            quien = "**Tú**" if msg["role"] == "user" else "**Qwen**"
            f.write("{}:\n\n{}\n\n".format(quien, msg["content"]))
        medio = a["tokens"] / a["t_gen"] if a["t_gen"] > 0 else 0.0
        f.write("---\n\nSesion: {} turnos · ~{} tok · {:.1f} tok/s medio\n"
                .format(a["turnos"], a["tokens"], medio))
        modos = {}
        for turno in ESTADO["turnos"]:
            modos.setdefault(turno.get("modo"), []).append(turno["ts"])
        por_modo = ["modo {} {:.1f} tok/s (n={})".format(
                        k, sum(v) / len(v), len(v))
                    for k, v in sorted(modos.items(),
                                       key=lambda kv: (kv[0] is None,
                                                       kv[0] or 0))
                    if k is not None]
        if por_modo:
            f.write("Por modo: {}\n".format(" | ".join(por_modo)))
    print(pintar(VER, "  transcript guardado: {}".format(nombre)))


# ------------------------------------------------------------------ main
def main():
    global PORT_DEFAULT, CTX_RIG
    _cfg = _config_central()          # config central (si existe); la CLI gana
    if _cfg.get("PUERTO", "").isdigit():
        PORT_DEFAULT = int(_cfg["PUERTO"])
    _fb = _cfg.get("FLAGS_BASE", "").split()
    if "-c" in _fb:
        _i = _fb.index("-c")
        if _i + 1 < len(_fb) and _fb[_i + 1].isdigit():
            CTX_RIG = int(_fb[_i + 1])

    ap = argparse.ArgumentParser(
        description="Chat token a token con Qwen APEX-I-MINI (llama-server b11856)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=PORT_DEFAULT)
    ap.add_argument("--preset", default="think", choices=sorted(SAMPLING_API),
                    help="sampling inicial (default think; /preset cambia al vuelo)")
    args = ap.parse_args()

    try:                                  # consola con acentos/garantizado
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    activar_color()

    estado, ok = comprobar_salud(args.host, args.port)
    if not ok:
        if estado == "cargando":
            print(pintar(AMA, "El server esta CARGANDO el modelo (503). "
                         "Espera a que termine y relanza."))
        else:
            print(pintar(ROJ, "No hay server en http://{}:{}".format(
                args.host, args.port)))
            print("  Abre primero el modelo: doble click en ABRIR-QWEN.bat")
            print("  -> [1] ABRIR (o [5] CHAT RAPIDO) y espera el banner.")
        return 1

    ESTADO["preset"] = args.preset
    print("=" * 70)
    print(pintar(CIA, "  CHAT QWEN APEX-I-MINI  ·  server b11856 en {}".format(
        url_base(args.host, args.port))))
    print(pintar(CIA, "  sampling: " + muestrear_descripcion(ESTADO["preset"])))
    print("=" * 70)
    print(pintar(GRA, "  (thinking en gris; tok/s bajo cada respuesta y en el "
                     "titulo; /modo 8|4 etiqueta que .bat abriste; Ctrl+C corta)"))
    print()

    while True:
        try:
            linea = input(pintar(CIA, "Tú> ")).strip()
        except KeyboardInterrupt:
            print("\n(Ctrl+C — usa /salir para cerrar)")
            continue
        except EOFError:
            print()
            return 0
        if not linea:
            continue
        if linea.startswith("/"):
            if not ejecutar_comando(linea, args.host, args.port):
                return 0
            continue

        print()
        ESTADO["messages"].append({"role": "user", "content": linea})
        m = responder_turno(args.host, args.port)
        if m is None:
            ESTADO["messages"].pop()      # server caido: no contaminar
            continue
        if m["cortado"]:
            ESTADO["messages"].pop()      # turno interrumpido: descartado
        else:
            if m["respuesta"]:
                ESTADO["messages"].append(
                    {"role": "assistant", "content": m["respuesta"]})
            registrar_turno(m)
        imprimir_metricas(m)
        print()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
        sys.exit(130)
