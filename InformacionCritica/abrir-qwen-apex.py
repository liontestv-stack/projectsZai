#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
abrir-qwen-apex.py v2.0-minimal — abrir el modelo, nada mas
============================================================
Doble click (o ABRIR-QWEN.bat) -> el modelo queda corriendo en
http://127.0.0.1:9931 y esta ventana lo mantiene vivo.

  - Para HABLAR: abre CHATEAR-QWEN.bat (otra ventana, token a token)
  - Para CERRAR el modelo: cierra esta ventana (o Ctrl+C)
  - Para MEDIR y mejorar t/s: BARRIDO-QWEN.bat (barrido de 25 configs)

Sampling: preset oficial "think" de Qwen3.6 FIJO aqui abajo (card +
generation_config; los defaults del server NO son optimos). Para cambiarlo
al vuelo usa /preset en chatear-qwen.py.

MEJORA DE VELOCIDAD: corre BARRIDO-QWEN.bat; al terminar imprime una linea
FLAGS_GANADORAS = [...] -> pegala aqui abajo y listo. Si queda vacia, abre
con la base verificada.

Historia: la version completa con menu (V1/V2/sweep/MTP/presets) quedo
conservada como abrir-qwen-apex-v13-avanzado.py.
"""
import os
import subprocess
import sys
import time
import urllib.request

# ============================ CONFIG (editar aqui) ============================
RUTA_SERVER = r"D:\llama.cpp\llama-server.exe"
RUTA_MODELO = (r"D:\ZLia\models"
               r"\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf")
HOST = "127.0.0.1"
PORT = 9931

# Pega aqui el ganador del BARRIDO-QWEN.bat (empieza vacio):
FLAGS_GANADORAS = []

# Base verificada (V1 del build b11856, preset think oficial fijo):
BASE_FLAGS = [
    "-m", RUTA_MODELO, "-a", "apex35b",
    "-ngl", "99", "-cmoe",
    "-c", "16384", "-b", "2048", "-ub", "256",
    "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
    "-t", "4", "--prio", "2", "--no-mmproj",
    "--temp", "1.0", "--top-k", "20", "--top-p", "0.95",
    "--min-p", "0.0", "--presence-penalty", "0.0",
    "--host", HOST, "--port", str(PORT),
]
# ==============================================================================


def main():
    url = "http://%s:%d/health" % (HOST, PORT)
    try:
        urllib.request.urlopen(url, timeout=2)
        print("[AVISO] El modelo YA esta abierto en %s" % url.replace("/health", ""))
        print("        Usa CHATEAR-QWEN.bat para hablar, o cierra ese server primero.")
        return 0
    except Exception:
        pass
    try:
        print("Abriendo Qwen APEX-I-MINI (la carga tarda ~1-2 min)...")
        proc = subprocess.Popen([RUTA_SERVER] + BASE_FLAGS + FLAGS_GANADORAS,
                                cwd=(os.path.dirname(RUTA_SERVER) or "."))
    except Exception as e:
        print("[ERROR] No pude lanzar el server: %s" % e)
        print("        Revisa RUTA_SERVER en este archivo.")
        return 1
    t0 = time.time()
    while time.time() - t0 < 600:
        try:
            urllib.request.urlopen(url, timeout=2)
            break
        except Exception:
            if proc.poll() is not None:
                print("[ERROR] El server se cerro solo (codigo %s)." % proc.returncode)
                print("        Revisa que la ruta del modelo y la VRAM libre sean correctas.")
                return 1
            time.sleep(2)
    else:
        print("[ERROR] 10 min sin responder. Cierra esta ventana y revisa VRAM/RAM.")
        proc.terminate()
        return 1
    print("")
    print("  ==============================================")
    print("   MODELO LISTO:  http://127.0.0.1:9931")
    print("   Para hablar:   abre CHATEAR-QWEN.bat")
    print("   Para cerrar:   cierra esta ventana (o Ctrl+C)")
    print("  ==============================================")
    print("")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("Cerrando el modelo...")
        proc.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
