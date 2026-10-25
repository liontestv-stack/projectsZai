#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
abrir-qwen-apex.py v2.1-minimal — abrir el modelo, nada mas
============================================================
Doble click (o ABRIR-QWEN.bat) -> el modelo queda corriendo en
http://127.0.0.1:9931 y esta ventana lo mantiene vivo.

  - Para HABLAR: abre CHATEAR-QWEN.bat (otra ventana, token a token)
  - Para CERRAR el modelo: cierra esta ventana (o Ctrl+C)
  - Para MEDIR y mejorar t/s: BARRIDO-QWEN.bat (barrido de 37 configs)

Sampling: preset oficial "think" de Qwen3.6 FIJO aqui abajo (card +
generation_config; los defaults del server NO son optimos). Para cambiarlo
al vuelo usa /preset en chatear-qwen.py.

MEJORA DE VELOCIDAD: corre BARRIDO-QWEN.bat; al terminar imprime una linea
FLAGS_GANADORAS = [...] -> pegala aqui abajo y listo. Si queda vacia, abre
con la base verificada.

v2.1 (26-oct-2026): entra el ORO-UB1K del barrido-30 (config 32), el mas
INSTANTANEO del barrido por coste total: prefill 57.56 tok/s (+26.5% vs
ancla 45.50, pasada fria de 293 tok) con decode intacto 21.55 (~21.53).
FIT-A/NCM37C4 (22.40/22.49 decode) NO se aplican todavia: son ganadores de
COLOCACION que quedaron sin medir combinados con UB1K (los combos 28-30
mostraron que las colocaciones se pelean entre si). Mini-sweep pendiente:
FIT-A + UB1K antes de tocar -ngl/-ncmoe aqui.

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

# Ganador barrido-25: LMNONE = 21.50 t/s vs BASE 20.85 (+3.1%).
# + Ganador barrido-30 (26-oct-2026): ORO-UB1K (config 32) = -ub 1024 -b 4096
#   sobre esta MISMA base (con -lm none): prefill 57.56 tok/s (+26.5% vs
#   45.50) con decode 21.55 intacto. Es el que empieza a hablar antes:
#   300 tok nuevos en ~5.2 s vs ~6.6 s de la base; a 8k+ tok gana ~19 s.
#   Medido con 4 pasadas x 256 sin errores; el -ub/-b de BASE_FLAGS queda
#   overrides por estos (mismo mecanismo que en el barrido: van despues).
#   Revertir: borra esta lista y vuelve la base sola.
FLAGS_GANADORAS = ["-lm", "none", "-ub", "1024", "-b", "4096"]

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
