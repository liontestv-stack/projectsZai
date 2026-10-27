#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test E2E de chatear-qwen.py contra un mock SSE del llama-server.

Ejercita: /health 503->ok, thinking separado (reasoning_content), thinking
inline <think> PARTIDO entre chunks (retencion de prefijos), usage final
(ctx real), metricas cliente, /temp 0 rechazado (NO greedy), /modo N
(etiqueta turnos, /modo 0 rechazado), /stats agrupa tok/s por modo,
/guardar con linea "Por modo" y /salir. Verifica ademas que en pipe NO
hay codigos ANSI.
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

CLIENTE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "InformacionCritica", "scripts", "chatear-qwen.py")
PORT = 19931
HITOS = {"reqs": 0, "cuerpos": []}


def sse(data):
    return "data: {}\n\n".format(json.dumps(data)).encode("utf-8")


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):          # silenciar log del mock
        pass

    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        n = HITOS["reqs"]
        HITOS["reqs"] += 1
        largo = int(self.headers.get("Content-Length", 0))
        HITOS["cuerpos"].append(json.loads(self.rfile.read(largo)))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()                # HTTP/1.0: el cierre delimita el body

        def ev(d, pausa=0.01):
            self.wfile.write(sse(d))
            self.wfile.flush()
            time.sleep(pausa)

        if n == 0:
            # turno 1: thinking SEPARADO + respuesta + usage final
            ev({"choices": [{"delta": {"reasoning_content": "Pienso "}}]})
            ev({"choices": [{"delta": {"reasoning_content": "paso a paso."}}]})
            ev({"choices": [{"delta": {"content": "La respuesta es 4."}}]})
            ev({"choices": [], "usage": {"prompt_tokens": 1234,
                                         "completion_tokens": 42}})
            self.wfile.write(b"data: [DONE]\n\n")
        else:
            # turno 2: <think> inline PARTIDO entre chunks
            for trozo in ["Veamos", "<thi", "nk>2+2=4", "</", "think>",
                          "Son 4.", " ¡Correcto!"]:
                ev({"choices": [{"delta": {"content": trozo}}]})
            ev({"choices": [], "usage": {"prompt_tokens": 1500,
                                         "completion_tokens": 25}})
            self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def main():
    srv = HTTPServer(("127.0.0.1", PORT), Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    cwd = "/tmp/laia-test-chat"
    os.makedirs(cwd, exist_ok=True)
    for f in os.listdir(cwd):             # limpiar restos de corridas previas
        os.remove(os.path.join(cwd, f))
    entrada = ("hola\n/modo 4\notra\n/temp 0\n/modo 0\n"
               "/stats\n/guardar\n/salir\n")
    p = subprocess.run(
        [sys.executable, CLIENTE, "--port", str(PORT)],
        input=entrada.encode(), capture_output=True, timeout=60, cwd=cwd)
    out = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")

    fallos = []

    def check(nombre, cond, detalle=""):
        print("  [{}] {} {}".format("OK" if cond else "FALLO", nombre,
                                    detalle if not cond else ""))
        if not cond:
            fallos.append(nombre)

    check("rc=0", p.returncode == 0, "rc={} err={}".format(p.returncode, err[:400]))
    check("sin ANSI en pipe", "\x1b[" not in out)
    check("banner", "CHAT QWEN APEX-I-MINI" in out)
    check("thinking separado mostrado", "(pensando)" in out and "paso a paso." in out)
    check("respuesta turno 1", "La respuesta es 4." in out)
    check("ctx real server", "ctx 1,234/16,384" in out)
    check("completion_tokens server", "42 tok" in out)
    check("prefill aprox", re.search(r"~[\d,]+ tok/s prefill", out) is not None)
    check("think inline gris", "2+2=4" in out)
    check("respuesta tras tag partido", "Son 4. ¡Correcto!" in out)
    check("NO greedy rechazado", "NO greedy" in out)
    check("/modo 4 aceptado", "modo: 4 expertos" in out)
    check("/modo 0 rechazado", "numero de expertos" in out)
    check("metricas etiquetadas modo 4", "modo 4  ·" in out)
    check("stats agrupa modo 4", "modo 4: 1 turno ·" in out)
    check("stats agrupa sin modo", "(sin modo): 1 turno ·" in out)
    check("stats 2 turnos", "turnos 2" in out)
    check("historial SIN thinking",
          HITOS["cuerpos"][1]["messages"][-2]["content"] == "La respuesta es 4.")
    check("cuerpo 1: preset think",
          HITOS["cuerpos"][0]["temperature"] == 1.0 and
          HITOS["cuerpos"][0]["top_k"] == 20)
    check("stream_options pedido",
          HITOS["cuerpos"][0].get("stream_options", {}).get("include_usage") is True)

    md = [f for f in os.listdir(cwd) if f.startswith("chat-qwen-") and f.endswith(".md")]
    check("transcript creado", len(md) == 1)
    if md:
        texto = open(os.path.join(cwd, md[0]), encoding="utf-8").read()
        check("transcript sin thinking", "<think>" not in texto and
              "2+2=4" not in texto)
        check("transcript con respuesta", "La respuesta es 4." in texto)
        check("transcript con modo", "modo 4" in texto and "Por modo:" in texto)

    print()
    if fallos:
        print("ROJO: {} fallos: {}".format(len(fallos), fallos))
        print("---- STDOUT ----")
        print(out)
        return 1
    print("VERDE: test E2E completo OK ({} requests al mock)".format(
        HITOS["reqs"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
