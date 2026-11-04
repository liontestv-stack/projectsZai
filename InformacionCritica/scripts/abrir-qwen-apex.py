#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
abrir-qwen-apex.py v3.2 — apertura + cambio administrado K=4..8
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

v3.2 (04-nov-2026): NUEVO --expertos K, usado por /expertos K en el chat.
El cambio solo procede con /health sano, /slots verificable y todos libres.
Identifica el proceso por exe + modelo + puerto, cierra sin taskkill /F,
reinicia con K=4..8 y autentica el comando vivo. Si el nuevo perfil falla,
intenta restaurar el K anterior. No modifica config.txt. El server reiniciado
se abre en una consola nueva; el historial permanece en el cliente, la KV se
reconstruye. Los perfiles .bat TRABAJO/CHARLA siguen funcionando sin cambios.

v3.1 (30-oct-2026): PROMOCION NP2 (R53, aprobacion del Director) — config.txt
FLAGS_BASE lleva -np 2 (campeon del N3: mediana de 3 = 21.45 t/s, +19.8% vs
ancla propia; con 4 sesiones 21.43 / +21.3%). Matices: contexto 8192 por
sesion (con -c 16384); MTP/speculative exige -np 1 y se decide en el duelo
N5. El comando generado YA NO es identico al v2.1 (suma -np 2): el T06 del
test fija la receta promovida. LOGICA INTACTA (la receta vive en config.txt).
"""
import json
import ntpath
import os
import re
import shlex
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


def construir_comando_expertos(cfg, k):
    """Construye la receta con K=4..8. El resto de flags no cambia."""
    k = int(k)
    if not 4 <= k <= 8:
        raise ValueError("expertos fuera del rango seguro habilitado: 4..8")
    cmd = [cfg["RUTA_SERVER"], "-m", cfg["RUTA_MODELO"], "-a", ALIAS]
    cmd += cfg.get("FLAGS_BASE", "").split()
    if k != 8:
        cmd += ["--override-kv", "qwen35moe.expert_used_count=int:%d" % k]
    cmd += cfg.get("SAMPLING", "").split()
    cmd += cfg.get("FLAGS_GANADORAS", "").split()
    cmd += ["--host", "127.0.0.1", "--port", cfg.get("PUERTO", "9931")]
    return cmd, k


def construir_comando(cfg, perfil):
    """Compatibilidad con los dos perfiles históricos TRABAJO/CHARLA."""
    k = int(cfg.get("EXPERTOS_CHARLA", "4") if perfil == "charla"
            else cfg.get("EXPERTOS_TRABAJO", "8"))
    return construir_comando_expertos(cfg, k)


def _norm_ruta_windows(ruta):
    return ntpath.normcase(ntpath.normpath(str(ruta or ""))).lower()


def _tokens_cmdline(linea):
    """Tokeniza CommandLine de WMI respetando rutas entre comillas."""
    try:
        return [t.strip('"') for t in shlex.split(linea, posix=False)]
    except ValueError as exc:
        raise RuntimeError("no pude interpretar la linea de comando WMI: %s" % exc)


def _valor_despues(tokens, flag):
    for i, token in enumerate(tokens):
        if token == flag and i + 1 < len(tokens):
            return tokens[i + 1]
    return None


def _k_desde_tokens(tokens):
    valor = _valor_despues(tokens, "--override-kv")
    if not valor:
        return 8  # default documentado del modelo: 8 expertos usados
    m = re.search(r"qwen35moe\.expert_used_count=int:(\d+)", valor)
    if not m:
        raise RuntimeError("override-kv presente pero no contiene expert_used_count reconocible")
    k = int(m.group(1))
    if not 4 <= k <= 8:
        raise RuntimeError("el server vivo usa K=%d, fuera del rango administrado 4..8" % k)
    return k


def _lista_procesos_server(cfg):
    """Enumera SOLO el nombre del ejecutable configurado; nunca mata por puerto a ciegas."""
    if os.name != "nt":
        raise RuntimeError("el cambio administrado de expertos requiere Windows")
    nombre = ntpath.basename(cfg["RUTA_SERVER"]).replace("'", "''")
    ps = (
        "$items = @(Get-CimInstance Win32_Process -Filter \"Name='%s'\" | "
        "Select-Object @{Name='pid';Expression={$_.ProcessId}},"
        "@{Name='exe';Expression={$_.ExecutablePath}},"
        "@{Name='cmd';Expression={$_.CommandLine}}); "
        "ConvertTo-Json -InputObject $items -Compress"
    ) % nombre
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=25)
    except Exception as exc:
        raise RuntimeError("no pude consultar procesos con PowerShell: %s" % exc)
    if r.returncode != 0:
        raise RuntimeError("PowerShell no pudo enumerar llama-server: %s" %
                           (r.stderr or r.stdout or "error sin detalle")[:500])
    try:
        data = json.loads((r.stdout or "[]").strip() or "[]")
    except ValueError:
        raise RuntimeError("PowerShell devolvio un inventario de procesos no valido")
    if isinstance(data, dict):
        data = [data]
    return data if isinstance(data, list) else []


def _identificar_server(cfg):
    """Identifica por EXE + modelo + puerto. Exige una sola coincidencia exacta."""
    objetivo_exe = _norm_ruta_windows(cfg["RUTA_SERVER"])
    objetivo_modelo = _norm_ruta_windows(cfg["RUTA_MODELO"])
    objetivo_puerto = str(cfg.get("PUERTO", "9931"))
    coincidencias = []
    for item in _lista_procesos_server(cfg):
        if not isinstance(item, dict) or not item.get("cmd") or not item.get("pid"):
            continue
        tokens = _tokens_cmdline(item["cmd"])
        if not tokens:
            continue
        exe = item.get("exe") or tokens[0]
        modelo = _valor_despues(tokens, "-m")
        puerto = _valor_despues(tokens, "--port")
        if (_norm_ruta_windows(exe) == objetivo_exe and
                _norm_ruta_windows(modelo) == objetivo_modelo and
                str(puerto) == objetivo_puerto):
            coincidencias.append({
                "pid": int(item["pid"]),
                "k": _k_desde_tokens(tokens),
                "cmd": item["cmd"],
            })
    if len(coincidencias) != 1:
        raise RuntimeError(
            "esperaba exactamente 1 llama-server de este modelo/puerto; encontre %d. "
            "No detuve ningun proceso." % len(coincidencias))
    return coincidencias[0]


def _health_ok(cfg):
    url = "http://127.0.0.1:%s/health" % cfg.get("PUERTO", "9931")
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def _slots_libres(cfg):
    """Failsafe: solo cambia de perfil si /slots existe y TODOS estan libres."""
    url = "http://127.0.0.1:%s/slots" % cfg.get("PUERTO", "9931")
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as exc:
        raise RuntimeError("no pude verificar /slots; no se reinicia: %s" % exc)
    if not isinstance(data, list) or not data:
        raise RuntimeError("/slots no devolvio una lista valida; no se reinicia")
    for slot in data:
        if not isinstance(slot, dict) or not isinstance(slot.get("is_processing"), bool):
            raise RuntimeError("/slots no expone is_processing verificable; no se reinicia")
        if slot["is_processing"]:
            raise RuntimeError("hay una generacion activa en un slot; termina los turnos primero")
    return len(data)


def _pid_existe(pid):
    ps = "Get-CimInstance Win32_Process -Filter \"ProcessId=%d\" | Select-Object -ExpandProperty ProcessId" % int(pid)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        raise RuntimeError("no pude verificar el cierre del PID %s" % pid)
    return str(pid) in (r.stdout or "").split()


def _detener_server(pid, cfg):
    """Cierre no forzado; sin /F. Si no se confirma el cierre, aborta."""
    try:
        r = subprocess.run(["taskkill", "/PID", str(pid), "/T"],
                           capture_output=True, text=True, timeout=25)
    except Exception as exc:
        raise RuntimeError("no pude solicitar el cierre del PID %s: %s" % (pid, exc))
    if r.returncode != 0 and _pid_existe(pid):
        raise RuntimeError("taskkill no pudo detener el PID %s: %s" %
                           (pid, (r.stderr or r.stdout or "").strip()[:300]))
    limite = time.time() + 45
    while time.time() < limite:
        if not _pid_existe(pid) and not _health_ok(cfg):
            return
        time.sleep(1)
    raise RuntimeError("el servidor no termino en 45 s; no intentare abrir otra instancia")


def _arrancar_k(cfg, k, timeout=600):
    cmd, _ = construir_comando_expertos(cfg, k)
    flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=(os.path.dirname(cfg["RUTA_SERVER"]) or "."),
            creationflags=flags
        )
    except Exception as exc:
        raise RuntimeError("no pude iniciar llama-server: %s" % exc)
    limite = time.time() + timeout
    while time.time() < limite:
        if proc.poll() is not None:
            raise RuntimeError("llama-server termino durante el arranque (codigo %s)" %
                               proc.returncode)
        if _health_ok(cfg):
            try:
                vivo = _identificar_server(cfg)
                if vivo["k"] == k:
                    return
            except Exception:
                pass  # la enumeracion WMI puede tardar un instante en reflejar el PID
        time.sleep(2)
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except Exception:
        pass
    raise RuntimeError("el server no quedo saludable y autenticado en %d s" % timeout)


def cambiar_expertos(cfg, k):
    """Reinicio administrado y reversible. No edita config.txt ni fuerza cierres."""
    try:
        k = int(k)
        if not 4 <= k <= 8:
            raise RuntimeError("usa un numero entre 4 y 8")
        if not _health_ok(cfg):
            raise RuntimeError("no hay un server saludable en el puerto configurado")
        slots = _slots_libres(cfg)
        vivo = _identificar_server(cfg)
        anterior = vivo["k"]
        if anterior == k:
            print("EXPERTOS_YA_ACTIVOS: %d" % k)
            return 0
        print("Cambio solicitado: K=%d -> K=%d; %d slots verificados libres." %
              (anterior, k, slots), flush=True)
        print("Deteniendo de forma no forzada el PID %d..." % vivo["pid"], flush=True)
        _detener_server(vivo["pid"], cfg)
        try:
            print("Iniciando Qwen con K=%d..." % k, flush=True)
            _arrancar_k(cfg, k)
        except Exception as nuevo_error:
            print("[AVISO] El perfil nuevo no arranco: %s" % nuevo_error, flush=True)
            print("Intentando restaurar el perfil anterior K=%d..." % anterior, flush=True)
            try:
                _arrancar_k(cfg, anterior)
                print("[RESTAURADO] Qwen volvio a K=%d. La conversacion local sigue intacta." %
                      anterior, flush=True)
                return 2
            except Exception as rollback_error:
                print("[ERROR CRITICO] No pude restaurar K=%d: %s" %
                      (anterior, rollback_error), flush=True)
                return 3
        print("EXPERTOS_CAMBIADOS: %d" % k, flush=True)
        print("El historial del chat sigue en memoria; la cache KV del server se reconstruyo.", flush=True)
        return 0
    except Exception as exc:
        print("[CAMBIO CANCELADO] %s" % exc, flush=True)
        return 1


def estado_expertos(cfg):
    try:
        vivo = _identificar_server(cfg)
        print("EXPERTOS_ACTUALES: %d" % vivo["k"])
        return 0
    except Exception as exc:
        print("[NO VERIFICABLE] %s" % exc)
        return 1


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    operacion = args[0].lower() if args else ""
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

    if operacion == "--estado-expertos":
        return estado_expertos(cfg)
    if operacion == "--expertos":
        if len(args) != 2 or not args[1].isdigit():
            print("[ERROR] Uso interno: abrir-qwen-apex.py --expertos 4..8")
            return 1
        return cambiar_expertos(cfg, int(args[1]))

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
