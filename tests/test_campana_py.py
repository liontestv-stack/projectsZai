#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ronda 45 - pruebas de CAMPANA.py (adios al bat: "todo sera .py").
U26: existe, tiene el bloque R45, cuerpo byte-idéntico al v1.6 y el viejo
     bloque main no sobrevive.
U27: arranque REAL por subproceso en lab (con barrido+config): rc=0 y sin
     FATAL de auto-verificacion (el guardian deja pasar solo al integro).
U28: tamper con sintaxis valida (un digito del SHA incrustado) -> el
     guardian PARADA LIMPIA con "auto-verificacion de huella" y rc!=0.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(RAIZ, "InformacionCritica", "scripts")
CAMPANA = os.path.join(SCRIPTS, "CAMPANA.py")
FUENTE = os.path.join(SCRIPTS, "campana-10-pasos.py")
BARRIDO = os.path.join(SCRIPTS, "barrido-n3-eficiencia.py")
CONFIG = os.path.join(RAIZ, "InformacionCritica", "configs", "config.txt")
BLOQUE_VIEJO = 'if __name__ == "__main__":\n    sys.exit(main())\n'
HUELLA_FUENTE = "77A7AF69777EA3FEB2A848CA5F9B3C6C42252865A92AB4ED0FD0088EC959F901"

resultado = []


def check(nombre, condicion):
    resultado.append(condicion)
    print("[OK  ] %s" % nombre if condicion else "[FALLA] %s" % nombre)


def main():
    datos = open(CAMPANA, "rb").read()
    texto = datos.decode("utf-8")
    fuente = open(FUENTE, "rb").read()

    check("U26a CAMPANA.py existe y lleva el bloque R45",
          "ARRANQUE REFORZADO (CAMPANA.py" in texto)
    check("U26b cuerpo byte-idéntico al v1.6 certificado (SHA %s...)"
          % HUELLA_FUENTE[:8],
          hashlib.sha256(fuente).hexdigest().upper() == HUELLA_FUENTE
          and texto.startswith(fuente.decode("utf-8")[:-len(BLOQUE_VIEJO)]))
    check("U26c el viejo bloque main no sobrevive",
          BLOQUE_VIEJO not in texto)

    lab = tempfile.mkdtemp(prefix="lab-u27-")
    try:
        shutil.copy(CAMPANA, os.path.join(lab, "CAMPANA.py"))
        shutil.copy(BARRIDO, lab)
        shutil.copy(CONFIG, lab)
        r1 = subprocess.run([sys.executable, "CAMPANA.py", "estado"],
                            capture_output=True, cwd=lab, timeout=120)
        salida1 = (r1.stdout + r1.stderr).decode("utf-8", errors="replace")
        check("U27a arranque REAL del integro: rc=0", r1.returncode == 0)
        check("U27b el guardian no freno al integro",
              "auto-verificacion de huella" not in salida1)

        bytes_final = bytearray(datos)
        idx = bytes_final.find(b'SHA_AUTOCHEQUEO = "')
        pos = idx + len(b'SHA_AUTOCHEQUEO = "')
        bytes_final[pos] ^= 0x01
        ruta_roja = os.path.join(lab, "CAMPANA-TAMPERED.py")
        with open(ruta_roja, "wb") as f:
            f.write(bytes(bytes_final))
        r2 = subprocess.run([sys.executable, "CAMPANA-TAMPERED.py", "estado"],
                            capture_output=True, cwd=lab, timeout=120)
        salida2 = (r2.stdout + r2.stderr).decode("utf-8", errors="replace")
        check("U28 tamper (sintaxis valida) -> PARADA LIMPIA del guardian",
              r2.returncode != 0 and "auto-verificacion de huella" in salida2)
    finally:
        shutil.rmtree(lab, ignore_errors=True)

    print()
    if all(resultado):
        print("BATERIA campana-py: TODO VERDE (%d checks: U26-U28)" %
              len(resultado))
        return 0
    print("BATERIA campana-py: HAY FALLAS (%d/%d)" %
          (resultado.count(False), len(resultado)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
