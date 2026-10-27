#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
abrir-qwen-apex.py v3.0 — abrir el modelo, nada mas (todo sale de config.txt)
=============================================================================
Doble click en ABRIR-QWEN.bat        -> perfil TRABAJO (8 expertos, fabrica)
Doble click en ABRIR-QWEN-CHARLA.bat -> perfil CHARLA  (4 expertos, +41% t/s)

TODA la configuracion (rutas, puerto, expertos, flags) vive en:
    D:\ZLia\config.txt     (o config.txt junto a este script)
Aqui abajo ya NO hay nada que editar. Si falta config.txt, avisa y sale.

  - Para HABLAR: abre CHATEAR-QWEN.bat (otra ventana, token a token)
  - Para CERRAR el modelo: cierra esta ventana (o Ctrl+C)
  - Para MEDIR: BARRIDO-N1.bat (la dosis ganadora se anota en config.txt)

v3.0 (27-oct-2026): la config se muda a config.txt (pedido del Director:
"toda configuracion debe ir en un solo archivo"). El comando generado es
IDENTICO al v2.1 (mismos flags, verificado por test de regresion). NUEVO:
modo dual SS25 Opcion A — el perfil charla anade
--override-kv qwen35moe.expert_used_count=int:K SOLO si K != 8
(8 es el default del modelo: el perfil trabajo no toca nada).
Cambiar de perfil = cerrar esta ventana y abrir el otro .bat (~1 min).
"""
import os
import subprocess
import sys
import time
import urllib.request

CONFIG_OFICIAL = r"D:\ZLia\config.txt"
ALIAS = "apex35b"   # etiqueta fija del server en el rig (no es config diaria)
KEYS = ("RUTA_SERVER", "RUTA_MODELO", "RUTA_LOGS", "PUERTO",
        "EXPERTOS_TRABAJO", "EXPERTOS_CHARLA",
        "FLAGS_BASE", "SAMPLING", "FLAGS_GANADORAS")


def encontrar_config():
    """Orden de busqueda: variable de entorno CONFIG_TXT (tests/avanzado)
    -> ruta oficial D:\\ZLia\\config.txt -> config.txt junto a este script -> configs/ del repo (Ronda 21)."""
    candidatas = []
    if os.environ.get("CONFIG_TXT"):
        candidatas.append(os.environ["CONFIG_TXT"])
    candidatas.append(CONFIG_OFICIAL)
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    candidatas.append(os.path.join(_script_dir, "config.txt"))
    candidatas.append(os.path.join(_script_dir, "..", "configs",
                                   "config.txt"))  # Ronda 21: layout repo
    for c in candidatas:
        if c and os.path.exists(c):
            return c
    return None


def parsear_config(ruta):
    """clave = valor -> dict. Ignora comentarios (#) y lineas vacias."""
    cfg = {}
    with open(ruta, "r", encoding="utf-8", errors="replace") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            cfg[clave.strip()] = valor.strip()
    return cfg


def construir_comando(cfg, perfil):
    """Arma el comando del server. FLAGS_GANADORAS van AL FINAL (last-wins).
    El override de expertos SOLO se anade si k != 8 (8 = default del modelo)."""
    k = int(cfg.get("EXPERTOS_CHARLA", "4") if perfil == "charla"
            else cfg.get("EXPERTOS_TRABAJO", "8"))
    cmd = [cfg["RUTA_SERVER"], "-m", cfg["RUTA_MODELO"], "-a", ALIAS]
    cmd += cfg.get("FLAGS_BASE", "").split()
    if k != 8:
        cmd += ["--override-kv", "qwen35moe.expert_used_count=int:%d" % k]
    cmd += cfg.get("SAMPLING", "").split()
    cmd += cfg.get("FLAGS_GANADORAS", "").split()
    cmd += ["--host", "127.0.0.1", "--port", cfg.get("PUERTO", "9931")]
    return cmd, k


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    perfil = "charla" if args and args[0].lower().startswith("char") else "trabajo"

    ruta_cfg = encontrar_config()
    if not ruta_cfg:
        print("[ERROR] No encontre config.txt.")
        print("        Debe estar en: %s" % CONFIG_OFICIAL)
        print("        (o junto a este script, en la misma carpeta)")
        return 1
    cfg = parsear_config(ruta_cfg)
    faltan = [k for k in KEYS if k not in cfg]
    if faltan:
        print("[ERROR] A config.txt le faltan claves: %s" % ", ".join(faltan))
        print("        (%s)" % ruta_cfg)
        return 1

    url = "http://127.0.0.1:%s/health" % cfg["PUERTO"]
    try:
        urllib.request.urlopen(url, timeout=2)
        print("[AVISO] El modelo YA esta abierto en %s" % url.replace("/health", ""))
        print("        Usa CHATEAR-QWEN.bat para hablar, o cierra ese server primero.")
        return 0
    except Exception:
        pass

    cmd, k = construir_comando(cfg, perfil)
    try:
        print("Abriendo Qwen APEX-I-MINI — perfil %s (%d expertos) — config: %s"
              % (perfil.upper(), k, ruta_cfg))
        print("(la carga tarda ~1-2 min)...")
        proc = subprocess.Popen(cmd,
                                cwd=(os.path.dirname(cfg["RUTA_SERVER"]) or "."))
    except Exception as e:
        print("[ERROR] No pude lanzar el server: %s" % e)
        print("        Revisa RUTA_SERVER en config.txt.")
        return 1

    t0 = time.time()
    while time.time() - t0 < 600:
        try:
            urllib.request.urlopen(url, timeout=2)
            break
        except Exception:
            if proc.poll() is not None:
                print("[ERROR] El server se cerro solo (codigo %s)." % proc.returncode)
                print("        Revisa RUTA_MODELO y la VRAM libre en config.txt.")
                return 1
            time.sleep(2)
    else:
        print("[ERROR] 10 min sin responder. Cierra esta ventana y revisa VRAM/RAM.")
        proc.terminate()
        return 1

    print("")
    print("  ==============================================")
    print("   MODELO LISTO:  http://127.0.0.1:%s" % cfg["PUERTO"])
    print("   Perfil:        %s (%d expertos)" % (perfil.upper(), k))
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
