#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ronda 48-49 - pruebas de CAMPANA.py v1.7.2 LA MALETA (archivo unico).
U26: existe, tiene el bloque R45/R46, cuerpo byte-idéntico al v1.7.2 y el viejo
     bloque main no sobrevive.
U27: arranque REAL por subproceso en lab (con barrido+config): rc=0 y sin
     FATAL de auto-verificacion (el guardian deja pasar solo al integro).
U28: tamper con sintaxis valida (un digito del SHA incrustado) -> el
     guardian PARADA LIMPIA con "auto-verificacion de huella" y rc!=0.
U29: LA MALETA (r47): en lab SOLO despliega los cuatro companeros (SHA
     verificado) y NUNCA pisa un config.txt pre-existente (P2 es su dueno).
U30: (r48, auditoria antibugs) payload corrupto -> la ruta protegida del
     despliegue da causa visible + PARADA LIMPIA + rc=3 (antes: SystemExit
     crudo rc=1 que cerraba la ventana del doble click sin causa).
U31: (r48) self-heal del dump sin rama ciega: dump viejo -> REEMPLAZADO por
     el certificado; dump solo en ../configs -> nota honesta sin copia local.
U32: (r49, repaso antibugs) el import del companero tiene RED (chmod 000 ->
     causa visible + rc=1, no ventana callada); el guard imprime SIEMPRE el
     texto de un sys.exit("texto") (antes se perdia); higiene del tmp.
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
HUELLA_FUENTE = "12DA5AE150AC7F302DBB56B653FB3D6EBF5E49F50070332DA41C3F354563E127"

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
    check("U26b cuerpo byte-idéntico al v1.7.2 certificado (SHA %s...)"
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

    # U29: LA MALETA — lab SOLO (solo CAMPANA.py) + config pre-existente
    lab_m = tempfile.mkdtemp(prefix="lab-maleta-")
    try:
        shutil.copy(CAMPANA, os.path.join(lab_m, "CAMPANA.py"))
        # U29b primero: un config tuyo NUNCA se pisa (P2 es su dueno)
        config_tuyo = os.path.join(lab_m, "config.txt")
        with open(config_tuyo, "w", encoding="utf-8") as f:
            f.write("RUTA_SERVER = D:\\el_de_mi_casa\\llama-server.exe\n")
        r3 = subprocess.run([sys.executable, "CAMPANA.py", "estado"],
                            capture_output=True, cwd=lab_m, timeout=180)
        salida3 = (r3.stdout + r3.stderr).decode("utf-8", errors="replace")
        desplegados = [n for n in ("barrido-n3-eficiencia.py",
                                   "barrido-n1-expertos.py",
                                   "llama-flags-nuevo.txt")
                       if os.path.exists(os.path.join(lab_m, n))]
        config_respetado = (open(config_tuyo, encoding="utf-8").read()
                            == "RUTA_SERVER = D:\\el_de_mi_casa\\llama-server.exe\n")
        check("U29a maleta en lab SOLO: despliega companeros y rc=0",
              r3.returncode == 0 and len(desplegados) == 3
              and "MALETA (R47)" in salida3)
        check("U29b config.txt pre-existente NUNCA se pisa (semilla solo si falta)",
              config_respetado)
    finally:
        shutil.rmtree(lab_m, ignore_errors=True)

    # U30 (r48): payload corrupto -> ruta protegida del despliegue: causa
    # visible + PARADA LIMPIA + rc=3 (la r47 salia con SystemExit crudo rc=1
    # y la ventana del doble click se cerraba sin causa legible).
    lab_c = tempfile.mkdtemp(prefix="lab-payload-roto-")
    try:
        shutil.copy(CAMPANA, os.path.join(lab_c, "CAMPANA.py"))
        ruta_rota = os.path.join(lab_c, "CAMPANA.py")
        texto_roto = open(ruta_rota, encoding="utf-8").read()
        ancla = "'barrido-n1-expertos.py': ('"
        i0 = texto_roto.index(ancla)
        pos = i0 + len(ancla) + 1  # un digito hex del SHA incrustado
        digito = texto_roto[pos]
        sust = "0" if digito != "0" else "1"
        texto_roto = texto_roto[:pos] + sust + texto_roto[pos + 1:]
        with open(ruta_rota, "w", encoding="utf-8") as f:
            f.write(texto_roto)
        r6 = subprocess.run([sys.executable, "CAMPANA.py", "estado"],
                            capture_output=True, cwd=lab_c, timeout=180)
        salida6 = (r6.stdout + r6.stderr).decode("utf-8", errors="replace")
        check("U30 payload corrupto -> PARADA LIMPIA con causa y rc=3 "
              "(ruta protegida r48)",
              r6.returncode == 3 and "NO clava" in salida6
              and "PARADA LIMPIA" in salida6 and "barrido-n1-expertos.py" in salida6)
    finally:
        shutil.rmtree(lab_c, ignore_errors=True)

    # U31 (r48): self-heal del dump sin rama ciega.
    lab_d = tempfile.mkdtemp(prefix="lab-dump-viejo-")
    outer = tempfile.mkdtemp(prefix="lab-repo-layout-")
    try:
        shutil.copy(CAMPANA, os.path.join(lab_d, "CAMPANA.py"))
        dump_repo = os.path.join(RAIZ, "InformacionCritica", "configs",
                                 "llama-flags-nuevo.txt")
        with open(os.path.join(lab_d, "llama-flags-nuevo.txt"), "w",
                  encoding="utf-8") as f:
            f.write("# dump viejo del taller (NO certificado)\n")
        r7 = subprocess.run([sys.executable, "CAMPANA.py", "estado"],
                            capture_output=True, cwd=lab_d, timeout=180)
        salida7 = (r7.stdout + r7.stderr).decode("utf-8", errors="replace")
        check("U31a dump viejo en disco -> self-heal al certificado (nota "
              "visible, bytes clavados)",
              r7.returncode == 0 and "REEMPLAZADO" in salida7
              and open(os.path.join(lab_d, "llama-flags-nuevo.txt"), "rb").read()
              == open(dump_repo, "rb").read())

        # U31b: layout de repo — dump SOLO en ../configs: nota honesta y
        # NINGUNA copia local (ademas config.txt de ../configs no se planta).
        lab_e = os.path.join(outer, "scripts")
        cfgs = os.path.join(outer, "configs")
        os.makedirs(lab_e)
        os.makedirs(cfgs)
        shutil.copy(CAMPANA, os.path.join(lab_e, "CAMPANA.py"))
        shutil.copy(dump_repo, os.path.join(cfgs, "llama-flags-nuevo.txt"))
        with open(os.path.join(cfgs, "config.txt"), "w", encoding="utf-8") as f:
            f.write("RUTA_SERVER = D:\\rig\\llama-server.exe\n")
        r8 = subprocess.run([sys.executable, "CAMPANA.py", "estado"],
                            capture_output=True, cwd=lab_e, timeout=180)
        salida8 = (r8.stdout + r8.stderr).decode("utf-8", errors="replace")
        check("U31b dump solo en ../configs: nota honesta, sin copia local",
              r8.returncode == 0 and "../configs" in salida8
              and not os.path.exists(os.path.join(lab_e, "llama-flags-nuevo.txt")))
    finally:
        shutil.rmtree(lab_d, ignore_errors=True)
        shutil.rmtree(outer, ignore_errors=True)

    # U32 (r49, repaso antibugs): el import del companero con RED.
    # U32a REAL: companero ilegible (chmod 000) -> la red del despliegue da
    # causa visible + rc=1 (la maleta no puede verificar su SHA). U32b/U32c:
    # estructura de las redes en el archivo vivo.
    lab_f = tempfile.mkdtemp(prefix="lab-import-net-")
    try:
        shutil.copy(CAMPANA, os.path.join(lab_f, "CAMPANA.py"))
        r9 = subprocess.run([sys.executable, "CAMPANA.py", "estado"],
                            capture_output=True, cwd=lab_f, timeout=180)
        assert r9.returncode == 0, "lab base rc=%d" % r9.returncode
        os.chmod(os.path.join(lab_f, "barrido-n3-eficiencia.py"), 0o000)
        r10 = subprocess.run([sys.executable, "CAMPANA.py", "estado"],
                             capture_output=True, cwd=lab_f, timeout=180)
        salida10 = (r10.stdout + r10.stderr).decode("utf-8", errors="replace")
        check("U32a companero ilegible (chmod 000) -> causa visible + rc=1 "
              "(nada muere callado)",
              r10.returncode == 1 and "despliegue imposible" in salida10
              and "Traceback" in salida10)
        os.chmod(os.path.join(lab_f, "barrido-n3-eficiencia.py"), 0o644)
    finally:
        shutil.rmtree(lab_f, ignore_errors=True)

    check("U32b el import del companero queda DENTRO de la red (try con las "
          "3 ramas + pausa)",
          "\n    _spec.loader.exec_module(bn3)" in texto
          and texto.count("except SystemExit as _import_exc:") == 1
          and texto.count("Ctrl+C durante la importacion del companero") == 1
          and texto.count("importacion de barrido-n3-eficiencia.py imposible") == 1)
    check("U32c el guard imprime SIEMPRE el texto de sys.exit (causa no se "
          "pierde, r49)",
          texto.count("isinstance(exc.code, str) and exc.code.strip()") == 1
          and texto.count('print("[FATAL] %s" % exc.code)') == 1)

    print()
    if all(resultado):
        print("BATERIA campana-py: TODO VERDE (%d checks: U26-U32)" %
              len(resultado))
        return 0
    print("BATERIA campana-py: HAY FALLAS (%d/%d)" %
          (resultado.count(False), len(resultado)))
    return 1

if __name__ == "__main__":
    sys.exit(main())
