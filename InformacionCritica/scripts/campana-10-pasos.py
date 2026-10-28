#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
campana-10-pasos.py v1.0 — PILOTO DE LA CAMPANA: los 10 pasos en un solo script
===============================================================================
Encargo del Director (28-oct-2026): "tengo mas espacio en D:, ahora planea
esos 10 pasos solidificarlos bien en un .py que haga todo".

Este script NO reemplaza a los instrumentos de cada nivel (regla de la casa:
"los instrumentos N3/N2/N4/N5 se generan con el mismo esqueleto del barrido
N1 conforme se llegue a cada nivel, sin adelantar trabajo"). Es el PILOTO que
los maneja en orden, con puertas (gates), pre-vuelos, certificados y memoria:

  estado        foto de la campana (que paso, que falta, que decidio el Director)
  p1            higiene (C:/D:/RAM) + log NOCACHE + mediana de 3 de NP2 (b2/b3
                via barrido-n3) + veredicto GO / NO-GO / DUDOSO
  p2            promocion de -np 2 en config.txt (con confirmacion escrita,
                backup con marca de tiempo y --revert)
  p3            sanity de 20 prompts contra el server vivo + veredicto OK/FALLA
                que CIERRA el N3 (FALLA -> instruye revert)
  p4            descarga UD-IQ3_XXS (14,069,266,720 B) con HF_HOME en D:
                (nunca en paralelo con mediciones; resumable; --dry-run)
  p5            verificacion + humo del cuant nuevo: SHA256 certificado
                36f9ec0e...7150 + parser GGUF (nextn.* = MTP dentro) + primer
                arranque con la receta promovida y 1 prompt (fail-fast)
  p6            N1 formal: lanza BARRIDO-N1.bat v1.2.1 (con confirmacion)
  p7..p10       GUIADOS: checklist del nivel + registro de resultados
                (los instrumentos finos de N2/N4/RUTA0/N5 se generan cuando
                se llegue; aqui queda la ruta y la decision por escrito)

REGLAS que el script hace cumplir:
  - PUERTAS: p2 exige p1=GO; p3 exige p2; p4 exige N3 cerrado; p5 exige p4.
    --fuerza las salta APROPOSITO y lo deja escrito en el informe (la
    autoridad es del Director; la pista tambien).
  - config.txt SOLO se edita en p2, con confirmacion escrita y backup
    previo; --revert restaura el backup. Ningun otro paso toca la receta.
  - el informe (campana-INFORME.md) es APPEND-ONLY: cada accion anade una
    seccion con fecha; nada se borra ni reescribe.
  - las descargas corren cuando el rig NO mide; si hay que medir, se pausa.
  - FATAL nominado con forense: si algo muere, se imprime por que y donde
    mirar, y el estado queda guardado.

Todo vive junto al script (en el rig: D:\ZLia): campana-estado.json,
campana-INFORME.md, campana-sanity-<tag>/, models/. --dir cambia la base.
Importa barrido-n3-eficiencia.py (mismo directorio) para reutilizar el
parser GGUF, el SHA256 streaming, el chequeo de RAM y el cliente HTTP:
si no esta al lado, FATAL (son el mismo paquete del rig).

CHANGELOG v1.1 (2026-10-28, ronda 36 — revision "ni un solo bug" pedida por
el Director: "yo hago doble click y hace todo automaticamente... hazle una
revision para que no tenga ni un solo bug"). 13 hallazgos corregidos, todos
verificados contra los compañeros reales (barrido-n3 v1.3, config.txt de la
casa, abrir-qwen-apex.py, tests de la casa):
  1. p3: la puerta moria si p2 se re-ejecutaba (YA-PROMOVIDA no contaba
     como promovida) — el Director quedaba bloqueado por un re-run inofensivo.
  2. p1: disco D: por debajo del minimo salia VERDE (higiene que no avisaba);
     ahora avisan AMBOS discos con su motivo.
  3. p2: el chequeo "-np 2" era por substring ("-np 20" engañaba) y la
     promocion se APILABA si ya habia un -np → ahora por tokens; si ya hay
     un -np distinto de 2, no se toca nada y queda escrito.
  4. p5: campana-humo.log se SOBREESCRIBIA en cada intento (se perdia el
     forense del intento anterior) → acumulativo con cabecera por intento.
  5. p5: el humo NO replicaba la receta de la casa (faltaba el override de
     expertos si EXPERTOS_TRABAJO != 8), moria feo sin RUTA_SERVER, y un
     -m pegado dentro de las flags habria cargado OTRO modelo → receta
     espejo del lanzador + limpieza de -m/--model + FATAL nominado.
  6. p1/p6: Ctrl+C mostraba traceback crudo → pausa limpia (rc 130).
  7. DOBLE CLICK: la ventana se cerraba sola antes de poder leerse → si el
     script se arranca SIN argumentos, espera un Enter al mostrar estado.
  8. estado: YA-PROMOVIDA / VERIFICADO-SIN-HUMO / NO-GO / REVERTIDA /
     INCOMPLETO pintados de rojo (alarma falsa) → paleta correcta.
  9. estado json viejo o roto (sin pasos/n3, o no-dict) reventaba después
     → lectura defensiva con setdefault.
 10. p4: un hf instalado como .bat/.cmd (shim de pip) no arrancaba en
     Windows (CreateProcess no corre shells) → envuelto en cmd /c.
 11. p3: el veredicto OK/FALLA no actualizaba pasos["3"] (quedaba
     "EN-ESPERA-DEL-JUEZ" para siempre en el estado) → actualizado; y una
     re-corrida del mismo tag PISABA el RESUMEN.md → el anterior se archiva.
 12. p2/p4/p6 cancelados por el Director no dejaban rastro en el informe →
     la memoria append-only ahora registra tambien las cancelaciones.
 13. REPO_ALT (repo alternativo con el mismo archivo y SHA) estaba muerto
     → documentado en la ayuda de --repo.
Bateria ampliada: test_campana_mock.py pasa de 46 a 65 checks ejecutados
TODO VERDE (N01-N14 nuevos; nota: r35 anunciaba "38 checks" y era un conteo
a la baja — papereria tambien corregida).

CHANGELOG v1.2 (2026-10-29, ronda 37 — verificacion de seguridad EN VIVO del
objetivo N2, pedida por el Director: "realiza una verificacion de seguridad
del archivo"). Verificacion contra la API publica de HuggingFace:
  1. OBJETIVO CONFIRMADO AUTENTICO: la API publica HOY UD-IQ3_XXS.gguf con
     EXACTAMENTE 14,069,266,720 bytes y SHA256 36f9ec0e...7150 — identicos
     a los pinados aqui desde la ronda 35 (comparados al caracter). El repo
     es de la org oficial unsloth, no gated, sin banner de seguridad.
  2. HALLAZGO (el unico ROJO): REPO_ALT estaba MAL DOCUMENTADO — la nota
     "mismo archivo, mismo SHA" (heredada de r35/r36) es FALSA. La API
     publica en unsloth/Qwen3.6-35B-A3B-GGUF el mismo NOMBRE de archivo
     pero SIN el modulo MTP (13,211,155,424 B, SHA256 9c964e65...88fbe) y
     sin ninguna variante -MTP (23 GGUF, 0 con MTP). Haberlo usado habria
     costado una descarga nocturna de 13 GB que p5 rechazaria por SHA.
  3. FIX: p4 rechaza --repo REPO_ALT con FATAL nominado ANTES de descargar
     (--fuerza lo salta dejandolo escrito en el informe); comentario de la
     constante y ayuda de --repo corregidos con la evidencia; el fallback
     real sigue siendo re-ejecutar p4 contra REPO_DEFAULT (hf RETOMA la
     descarga cortada, no empieza de cero).
Bateria: 67 checks (E13b/E13c nuevos).
"""
import argparse
import csv
import datetime
import importlib.util
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
VERSION = "campana-10-pasos v1.2 (2026-10-29, verificacion de seguridad EN VIVO del objetivo N2: objetivo autentico confirmado al byte y al SHA; REPO_ALT desautenticado y bloqueado con FATAL nominado; pedido del Director 'realiza una verificacion de seguridad del archivo')"


def _pausa_doble_click(es_tty=None):
    """Doble click en Windows: la consola se cierra sola al terminar y el
    Director no alcanza a leer nada. Si el script se arranco SIN argumentos
    (doble click puro) se espera un Enter antes de cerrar; con argumentos
    (uso real desde consola/bat) no molesta."""
    if len(sys.argv) <= 1:
        if es_tty is None:
            try:
                es_tty = sys.stdin.isatty()
            except Exception:
                es_tty = False
        if es_tty:
            try:
                input("\n(Enter para cerrar)")
            except Exception:
                pass


# ---------------- importacion del companero de taller (barrido N3) ----------
_BARRIDO = os.path.join(AQUI, "barrido-n3-eficiencia.py")
if not os.path.exists(_BARRIDO):
    print("[FATAL] no encuentro barrido-n3-eficiencia.py junto a mi (%s)." % AQUI)
    print("        El piloto y el barrido viajan JUNTOS en D:\\ZLia.")
    _pausa_doble_click()
    sys.exit(2)
_spec = importlib.util.spec_from_file_location("barrido_n3", _BARRIDO)
bn3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bn3)

c, bold, red = bn3._c, bn3.bold, bn3.red
green, yellow, cyan, gray = bn3.green, bn3.yellow, bn3.cyan, bn3.gray
health_ok, ram_sistema = bn3.health_ok, bn3.ram_sistema
sha256_archivo, gguf_metadatos = bn3.sha256_archivo, bn3.gguf_metadatos

# ---------------- constantes del hito N2 (autenticadores cerrados) ----------
MODELO_NUEVO_NOMBRE = "Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf"
MODELO_NUEVO_BYTES = 14069266720
MODELO_NUEVO_SHA = ("36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012e3d9e249"
                    "5a90e7a7150")
REPO_DEFAULT = "unsloth/Qwen3.6-35B-A3B-MTP-GGUF"  # RUTAS.md L738: MTP preserved
# REPO_ALT DESAUTENTICADO en vivo (API HF 2026-10-29, verificacion r37):
# sirve el MISMO NOMBRE de archivo pero SIN modulo MTP (13,211,155,424 B,
# SHA256 9c964e65...88fbe) y sin variante -MTP. La nota vieja "mismo
# archivo, mismo SHA" era FALSA. p4 lo rechaza antes de descargar.
REPO_ALT = "unsloth/Qwen3.6-35B-A3B-GGUF"
REPO_ALT_MOTIVO = ("la API de HF (29-oct) publica en este repo el UD-IQ3_XXS "
                   "SIN modulo MTP (13,211,155,424 B, SHA256 9c964e65...88fbe) "
                   "y sin ninguna variante -MTP: NO es el archivo del hito N2 "
                   "y p5 lo rechazaria por SHA despues de horas de descarga")
GO_PCT, NOGO_PCT = 15.0, 5.0
DISCO_MIN_GB = 16.0      # para la descarga en D:
DISCO_HIGIENE_GB = 25.0  # aviso de higiene en C: (pagefile vive en C:)
SANITY_TOTAL = 20

# ---------------- los 20 prompts del juez (p3) ------------------------------
# Mezcla obligatoria: espanol, codigo, tool-calling, memoria corta, trampa.
SANITY_PROMPTS = [
    ("casual", "Hola! Que tal? Responde en una frase amable."),
    ("explica-simple", "Explica en dos frases que es la RAM de un computador, como para un nino."),
    ("codigo-fizzbuzz", "Escribe una funcion Python que imprima FizzBuzz del 1 al 15. Solo codigo."),
    ("matematica", "Cuanto es 17 * 23? Responde solo el numero."),
    ("traduccion", "Traduce al ingles: 'El perro corre por la playa al atardecer.'"),
    ("resumen", "Resume en una frase: 'El server de llama.cpp carga el modelo en la GPU, atiende peticiones HTTP y devuelve tokens generados uno a uno hasta completar la respuesta.'"),
    ("logica", "Todos los gatos son mamiferos. Algunos mamiferos nadan. Se puede concluir que todos los gatos nadan? Responde si o no y explica en una frase."),
    ("memoria-corta", "Mi color favorito es el verde. Sin pensar en nada mas, de que color te dije que era mi favorito?"),
    ("formato-lista", "Dame 3 consejos para dormir mejor, en lista con vinetas, uno por linea."),
    ("trampa-futuro", "Quien gano la final del mundial de futbol de 2030? Si no lo sabes, di que no lo sabes."),
    ("tool-clima", "Tienes la herramienta get_weather(ciudad). Usandola en formato JSON, como consultarias el clima de Santiago? Muestra solo la llamada."),
    ("tool-buscar", "Tienes la herramienta buscar_productos(termino, max). Muestra la llamada JSON para buscar 'teclado mecanico' con maximo 5 resultados."),
    ("redaccion", "Escribe un parrafo corto (3 frases) sobre el mar de Chile."),
    ("codigo-bug", "Este codigo tiene un bug: def suma(a,b): return a-b. Dime cual es y corrigelo en una linea."),
    ("clasificacion", "Clasifica el sentimiento como positivo/negativo/neutral: 'El servicio fue lento pero la comida estaba excelente.'"),
    ("creativo", "Escribe un haiku (3 versos) sobre el desierto de Atacama."),
    ("multilingue", "Traduce 'buenos dias' al ingles, frances y aleman, en una linea."),
    ("seguimiento", "Me llamo Ana y trabajo en Valparaiso. En que ciudad dije que trabajo?"),
    ("dominio", "Para que sirve la flag -ngl 99 en llama.cpp? Una frase."),
    ("despedida", "Despidete en una frase corta y amable."),
]

# ---------------- memoria de la campana -------------------------------------

def _rutas(args):
    base = os.path.abspath(args.dir) if args.dir else AQUI
    return {
        "base": base,
        "estado": os.path.join(base, "campana-estado.json"),
        "informe": os.path.join(base, "campana-INFORME.md"),
        "config": args.config or os.path.join(base, "config.txt"),
        "models": os.path.join(base, "models"),
    }


def leer_estado(ruta_estado):
    if os.path.exists(ruta_estado):
        try:
            with open(ruta_estado, encoding="utf-8") as f:
                datos = json.load(f)
            if isinstance(datos, dict):
                # defensa: un json viejo o a medio escribir no revienta despues
                datos.setdefault("pasos", {})
                datos.setdefault("n3", {})
                return datos
        except Exception:
            pass
    return {"version": VERSION, "actualizado": "", "pasos": {}, "n3": {}}


def guardar_estado(ruta_estado, estado):
    estado["version"] = VERSION
    estado["actualizado"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tmp = ruta_estado + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ruta_estado)


def informe(ruta_informe, titulo, lineas):
    """APPEND-ONLY: cada accion anade su seccion; nunca se reescribe."""
    sello = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ruta_informe, "a", encoding="utf-8") as f:
        f.write("\n\n## %s — %s\n\n" % (sello, titulo))
        for ln in lineas:
            f.write("%s\n" % ln)
        f.flush()
    return ruta_informe


def fatal(msg, pistas=()):
    print(red("\n[FATAL] %s" % msg))
    for p in pistas:
        print(yellow("  pista: %s" % p))
    sys.exit(2)


def confirmar(palabra, pregunta):
    print(yellow("\n%s" % pregunta))
    try:
        resp = input(yellow("  escribe %s para confirmar (otra cosa cancela): " % bold(palabra)))
    except EOFError:
        resp = ""
    if resp.strip().upper() != palabra:
        print(gray("  cancelado (no se toco nada)."))
        return False
    return True


def gb_libres(ruta):
    try:
        u = shutil.disk_usage(ruta)
        return u.free / (1024.0 ** 3), u.total / (1024.0 ** 3)
    except Exception:
        return None, None


def leer_config(ruta_config):
    """CLAVE = valor -> dict (lineas con # se ignoran). Igual que la casa."""
    if not os.path.exists(ruta_config):
        fatal("no encuentro config.txt en %s" % ruta_config,
              ["pasa --config D:\\ZLia\\config.txt"])
    cfg = {}
    with open(ruta_config, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


# ---------------- CSV del barrido: clasificacion de filas -------------------

def cosechar_carpeta(carpeta):
    """Lee faseN3-resultados.csv de una carpeta y devuelve las filas
    validas que importan para la mediana: ANCLA, NP2 (SLOTS) y ANCLA-FIN.
    (csv_cargar_hechos de la casa: solo valido=SI.)"""
    ruta = os.path.join(carpeta, "faseN3-resultados.csv")
    if not os.path.exists(ruta):
        return None
    filas = {"ancla": [], "np2": [], "anclafin": [], "total_validas": 0}
    try:
        with open(ruta, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("valido") or "").strip().upper() != "SI":
                    continue
                filas["total_validas"] += 1
                nom = (row.get("nombre") or "").upper()
                ts = row.get("decode_ts") or ""
                try:
                    ts = float(ts)
                except Exception:
                    continue
                if nom.startswith("N3-ANCLA") and "FIN" in nom:
                    filas["anclafin"].append(ts)
                elif nom.startswith("N3-ANCLA"):
                    filas["ancla"].append(ts)
                elif nom == "N3-NP2":
                    filas["np2"].append(ts)
    except Exception as e:
        return {"error": repr(e)}
    return filas


def mediana_np2(datos_carpetas):
    """Por carpeta: delta NP2 vs SU ancla. Veredicto con la mediana de los
    deltas (regla de la casa: mediana de 3, ancla por corrida)."""
    deltas, absolutos, detalle = [], [], []
    for nombre, filas in datos_carpetas:
        if not filas or filas.get("error") or not filas.get("np2") or not filas.get("ancla"):
            detalle.append("%s: N/D (ancla o NP2 no validas)" % nombre)
            continue
        ancla = statistics.median(filas["ancla"])
        np2 = statistics.median(filas["np2"])
        delta = (np2 / ancla - 1.0) * 100.0
        drift = ""
        if filas.get("anclafin"):
            fin = statistics.median(filas["anclafin"])
            d = abs(fin / ancla - 1.0) * 100.0
            drift = " (bookend %+.1f%%%s)" % ((fin / ancla - 1.0) * 100.0,
                                              ", sesion ESTABLE" if d < 5 else ", ATENCION >5%")
        deltas.append(delta)
        absolutos.append(np2)
        detalle.append("%s: ancla %.2f -> NP2 %.2f = %+.1f%%%s"
                       % (nombre, ancla, np2, delta, drift))
    if len(deltas) < 3:
        veredicto = "INCOMPLETO"
    else:
        m = statistics.median(deltas)
        veredicto = "GO" if m >= GO_PCT else ("NO-GO" if m < NOGO_PCT else "DUDOSO")
        detalle.append("mediana de los deltas: %+.1f%% -> %s" % (m, veredicto))
        if absolutos:
            detalle.append("t/s absolutos NP2: %s (mediana %.2f)"
                           % (", ".join("%.2f" % a for a in absolutos),
                              statistics.median(absolutos)))
    return veredicto, detalle


# ---------------- P1: higiene + mediana + NOCACHE ---------------------------

def paso1(args, rutas, estado):
    b1 = args.b1 or os.path.join(rutas["base"], "faseN3")
    b2 = args.b2 or os.path.join(rutas["base"], "faseN3-np2-b2")
    b3 = args.b3 or os.path.join(rutas["base"], "faseN3-np2-b3")
    lineas = []
    print(bold(cyan("\n=== P1 - higiene + mediana de 3 de NP2 ===")))

    # -- higiene (nunca fatal; advierte) --
    for etiqueta, ruta, minimo in (("C: (pagefile)", "C:\\" if os.name == "nt" else "/", DISCO_HIGIENE_GB),
                                   ("D: (trabajo)", "D:\\" if os.name == "nt" else "/", DISCO_MIN_GB)):
        libre, total = gb_libres(ruta)
        if libre is None:
            print(gray("  disco %s: (no disponible)" % etiqueta))
            continue
        msg = "  disco %s: %.1f GB libres de %.1f" % (etiqueta, libre, total)
        if libre < minimo:
            # AMBOS discos avisan (v1.0 solo miraba C: y D: bajo salia VERDE)
            detalle = ("higiene: pagefile en C:" if etiqueta.startswith("C:")
                       else "minimo para la descarga del cuant")
            print(yellow(msg + yellow("  <- por DEBAJO de %.0f GB (%s)" % (minimo, detalle))))
            lineas.append("- disco %s: %.1f GB libres (< %.0f GB: %s)"
                          % (etiqueta, libre, minimo, detalle))
        else:
            print(green(msg))
            lineas.append("- disco %s: %.1f GB libres de %.1f" % (etiqueta, libre, total))
    ram = ram_sistema()
    if ram:
        libre_mib, total_mib = ram
        pct = 100.0 * (total_mib - libre_mib) / max(total_mib, 1)
        estilo = green if pct < 70 else yellow
        print(estilo("  RAM: %.0f%% usada (%.1f GB libres de %.1f) — regla R28: apps cerradas antes de medir"
                     % (pct, libre_mib / 1024.0, total_mib / 1024.0)))
        lineas.append("- RAM: %.0f%% usada al iniciar" % pct)

    # -- log NOCACHE (2 min que cierran la anomalia) --
    for raiz in (b1, os.path.dirname(b1)):
        if not raiz:
            continue
        cand = os.path.join(raiz, "logs-config", "12-NOCACHE.log")
        if os.path.exists(cand):
            print(cyan("  log NOCACHE: %s" % cand))
            try:
                with open(cand, encoding="utf-8", errors="replace") as f:
                    utiles = [ln.rstrip() for ln in f
                              if any(s in ln for s in ("cache_reuse", "restored", "forcing", "not supported"))]
                for ln in utiles[:12]:
                    print("    %s" % gray(ln[:160]))
                lineas.append("- NOCACHE log: %d lineas utiles (%s)" % (len(utiles), os.path.basename(cand)))
            except Exception as e:
                print(yellow("    (no pude leerlo: %r)" % e))
            break
    else:
        print(gray("  log NOCACHE: no encontrado (no fatal; anotado)"))
        lineas.append("- NOCACHE log: no encontrado en b1")

    # -- las 2 corridas de mediana (barrido v1.3; reanudable) --
    if not args.sin_corridas:
        try:
            for carpeta in (b2, b3):
                if not confirmar("EJECUTAR", "Se lanzara el barrido (~6-8 min) en carpeta '%s' con --solo ancla,slots,anclafin. El rig debe estar QUIETO (sin descargas, apps cerradas)." % carpeta):
                    fatal("mediana incompleta: el Director cancelo la corrida de %s" % carpeta,
                          ["re-lanza p1 cuando puedas dejar el rig quieto",
                           "o usa p1 --sin-corridas para cosechar lo ya medido"])
                cmd = [sys.executable, _BARRIDO, "--logs", carpeta,
                       "--solo", "ancla,slots,anclafin"]
                print(cyan("  $ %s" % " ".join(cmd)))
                rc = subprocess.call(cmd)
                if rc != 0:
                    fatal("el barrido salio con rc=%d en %s" % (rc, carpeta),
                          ["mira el final de la salida de arriba (forense)",
                           "el resume de la casa re-mide solo lo muerto: repite p1"])
        except KeyboardInterrupt:
            print(yellow("\n  INTERRUMPIDO (Ctrl+C): corrida pausada. El resume "
                         "de la casa re-mide solo lo muerto: repite p1."))
            return 130
    else:
        print(gray("  (--sin-corridas: cosechando lo que ya hay en las carpetas)"))

    # -- cosecha y veredicto --
    carpetas = [("b1=%s" % b1, cosechar_carpeta(b1)),
                ("b2=%s" % b2, cosechar_carpeta(b2)),
                ("b3=%s" % b3, cosechar_carpeta(b3))]
    print(bold("\n  cosecha de la mediana:"))
    for nombre, filas in carpetas:
        if filas is None:
            print(yellow("    %s: SIN CSV (¿carpeta correcta?)" % nombre))
        elif filas.get("error"):
            print(yellow("    %s: CSV ilegible (%s)" % (nombre, filas["error"])))
        else:
            print("    %s: validas=%d ancla=%d np2=%d anclafin=%d"
                  % (nombre, filas["total_validas"], len(filas["ancla"]),
                     len(filas["np2"]), len(filas["anclafin"])))
    veredicto, detalle = mediana_np2(carpetas)
    for d in detalle:
        print("    %s" % d)
    color = {"GO": green, "NO-GO": red, "DUDOSO": yellow}.get(veredicto, yellow)
    print(color(bold("  VEREDICTO P1: %s" % veredicto)))
    if veredicto == "GO":
        print("  -> pasa a p2: promocion de -np 2 en config.txt")
    elif veredicto == "NO-GO":
        print("  -> NP2 no aguanta: CMS1024 (plan B) o se queda como esta")
    elif veredicto == "DUDOSO":
        print("  -> zona de decision del Director (entre %.0f%% y %.0f%%)" % (NOGO_PCT, GO_PCT))

    estado["pasos"]["1"] = {"estado": veredicto, "carpetas": [n for n, _ in carpetas],
                            "detalle": detalle}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P1 mediana de 3 de NP2 -> %s" % veredicto, lineas + detalle)
    return 0


# ---------------- P2: promocion de -np 2 (la UNICA cirugia) -----------------

def _linea_flags_base(ruta_config):
    with open(ruta_config, encoding="utf-8") as f:
        for i, ln in enumerate(f):
            if ln.strip().startswith("FLAGS_BASE ="):
                return i, ln.rstrip("\n")
    return None, None


def paso2(args, rutas, estado):
    print(bold(cyan("\n=== P2 - promocion de -np 2 en config.txt ===")))
    if args.revert:
        return _p2_revert(rutas, estado)
    p1 = estado["pasos"].get("1", {})
    if p1.get("estado") != "GO" and not args.fuerza:
        fatal("la puerta p1 no esta en GO (estado actual: %s)" % (p1.get("estado") or "SIN P1"),
              ["corre p1 primero (mediana de 3 de NP2)",
               "si el Director decide saltarse la puerta: p2 --fuerza (queda escrito)"])
    ruta = rutas["config"]
    i, linea = _linea_flags_base(ruta)
    if i is None:
        fatal("no encuentro la linea FLAGS_BASE en %s" % ruta)
    # -np se busca por TOKENS, no por substring: "-np 20" no es "-np 2",
    # y si ya hay un -np distinto, la promocion NO se apila encima
    tokens = linea.split()
    ya_np = None
    for bandera in ("-np", "--parallel"):
        if bandera in tokens:
            i = tokens.index(bandera)
            ya_np = tokens[i + 1] if i + 1 < len(tokens) else "?"
            break
    if ya_np == "2":
        print(yellow("  FLAGS_BASE ya contiene -np 2: nada que hacer (idempotente)."))
        previo = estado["pasos"].get("2", {})
        estado["pasos"]["2"] = {"estado": "YA-PROMOVIDA",
                                "backup": previo.get("backup"),
                                "linea": previo.get("linea", linea)}
        guardar_estado(rutas["estado"], estado)
        return 0
    if ya_np is not None:
        print(yellow("  FLAGS_BASE ya trae -np %s (no 2): NO se toca nada." % ya_np))
        print(yellow("  El numero de slots ya lo decidio otra mano: revisa y decide tu."))
        informe(rutas["informe"], "P2 promocion ABORTADA: FLAGS_BASE ya trae -np %s" % ya_np,
                ["- linea: `%s`" % linea, "- config.txt intacto (nada editado)"])
        return 1
    nueva = linea + " -np 2"
    print("  linea actual : %s" % gray(linea))
    print("  linea nueva  : %s" % green(nueva))
    print(yellow("  matices aceptados: contexto 8192 por sesion (con -c 16384), "
                "WorkingSet +965 MiB, SS11.4 (MTP exige -np 1, se decide en p10)."))
    if not confirmar("PROMOVER", "Se editara %s (backup automatico antes)." % ruta):
        print(gray("  cancelado: config.txt intacto."))
        informe(rutas["informe"], "P2 promocion CANCELADA por el Director",
                ["- config.txt intacto (nada editado)"])
        return 1
    backup = "%s.bak-campana-p2-%s" % (ruta, datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(ruta, backup)
    with open(ruta, encoding="utf-8") as f:
        contenido = f.readlines()
    contenido[i] = nueva + "\n"
    with open(ruta, "w", encoding="utf-8") as f:
        f.writelines(contenido)
    _, verifica = _linea_flags_base(ruta)
    if not verifica or "-np 2" not in verifica:
        fatal("la edicion no quedo aplicada; restaura el backup: %s" % backup)
    print(green("  promovida. backup: %s" % backup))
    estado["pasos"]["2"] = {"estado": "PROMOVIDA", "backup": backup, "linea": nueva}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P2 promocion -np 2 -> PROMOVIDA",
            ["- config: %s" % ruta, "- backup: %s" % backup,
             "- linea nueva: `%s`" % nueva,
             "- siguiente: p3 (sanity 20 prompts como juez)"])
    print(cyan("  siguiente: arranca el server como siempre y corre p3."))
    return 0


def _p2_revert(rutas, estado):
    ruta = rutas["config"]
    info = estado["pasos"].get("2", {})
    backup = info.get("backup")
    if not backup or not os.path.exists(backup):
        # fallback: el backup mas reciente junto a config.txt
        candidatos = sorted(
            f for f in os.listdir(os.path.dirname(ruta) or ".")
            if f.startswith(os.path.basename(ruta) + ".bak-campana-p2-"))
        if not candidatos:
            fatal("no hay backup registrado para revertir",
                  ["busca config.txt.bak-campana-p2-* a mano junto a config.txt"])
        backup = os.path.join(os.path.dirname(ruta), candidatos[-1])
    shutil.copy2(backup, ruta)
    print(green("  config.txt restaurado desde %s" % backup))
    estado["pasos"]["2"] = {"estado": "REVERTIDA", "backup": backup}
    estado["n3"]["cerrado"] = False
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P2 revert: config.txt restaurada",
            ["- backup usado: %s" % backup])
    return 0


# ---------------- P3: sanity de 20 prompts (el juez) ------------------------

def _chat_uno(puerto, texto, timeout=180):
    cuerpo = json.dumps({
        "messages": [{"role": "user", "content": texto}],
        "max_tokens": 220, "temperature": 1.0, "top_k": 20, "top_p": 0.95,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d/v1/chat/completions" % puerto, data=cuerpo,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        js = json.loads(r.read().decode("utf-8", errors="replace"))
    contenido = ""
    try:
        contenido = js["choices"][0]["message"]["content"] or ""
    except Exception:
        contenido = json.dumps(js)[:400]
    tps = None
    try:
        tps = float(js["timings"]["predicted_per_second"])
    except Exception:
        pass
    return contenido, tps


def paso3(args, rutas, estado):
    print(bold(cyan("\n=== P3 - sanity de 20 prompts (el juez) ===")))
    if args.veredicto:
        v = args.veredicto.strip().upper()
        if v not in ("OK", "FALLA"):
            fatal("veredicto debe ser OK o FALLA")
        estado["n3"]["veredicto_sanity"] = v
        estado.setdefault("pasos", {}).setdefault("3", {})
        if v == "OK":
            estado["n3"]["cerrado"] = True
            estado["pasos"]["3"]["estado"] = "OK"
            print(green(bold("  N3 CERRADO con promocion aceptada. Campana desbloqueada hasta p10.")))
            lineas = ["- veredicto del Director: OK", "- N3 CERRADO con -np 2 promovida"]
        else:
            estado["n3"]["cerrado"] = False
            estado["pasos"]["3"]["estado"] = "FALLA"
            print(red("  FALLA registrada. La casa instruye: p2 --revert (5 segundos) y reportar que fallo."))
            lineas = ["- veredicto del Director: FALLA", "- accion: p2 --revert + registrar que fallo"]
        estado["n3"]["cerrado_en"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        guardar_estado(rutas["estado"], estado)
        informe(rutas["informe"], "P3 veredicto del juez -> %s" % v, lineas)
        return 0
    p2 = estado["pasos"].get("2", {})
    if p2.get("estado") not in ("PROMOVIDA", "YA-PROMOVIDA") and not args.fuerza:
        fatal("la puerta p2 no esta PROMOVIDA (estado: %s)" % (p2.get("estado") or "SIN P2"),
              ["promueve con p2 primero (el sanity juzga la receta NUEVA)",
               "o --fuerza si sabes lo que haces (queda escrito)"])
    puerto = args.puerto
    if not health_ok(puerto):
        fatal("no hay server vivo en el puerto %d" % puerto,
              ["arranca el server como siempre (ABRIR-QWEN.bat) y reintenta",
               "o pasa --puerto si usa otro"])
    tag = args.tag or ("np2" if p2.get("estado") in ("PROMOVIDA", "YA-PROMOVIDA") else "libre")
    carpeta = os.path.join(rutas["base"], "campana-sanity-%s" % tag)
    os.makedirs(carpeta, exist_ok=True)
    print(cyan("  server vivo en %d. %d prompts, 1 por uno..." % (puerto, SANITY_TOTAL)))
    resumen, fallas = [], 0
    for i, (nombre, texto) in enumerate(SANITY_PROMPTS, 1):
        try:
            contenido, tps = _chat_uno(puerto, texto)
        except Exception as e:
            contenido, tps, fallas = "[ERROR HTTP] %r" % e, None, fallas + 1
        with open(os.path.join(carpeta, "prompt-%02d-%s.txt" % (i, nombre)),
                  "w", encoding="utf-8") as f:
            f.write("PROMPT: %s\n\nRESPUESTA:\n%s\n" % (texto, contenido))
        primera = contenido.strip().splitlines()[0][:70] if contenido.strip() else "(vacia)"
        tps_s = "%.1f t/s" % tps if tps else "-"
        estilo = green if "[ERROR" not in contenido and contenido.strip() else red
        print(estilo("  %02d/%02d %-18s %-12s %s" % (i, SANITY_TOTAL, nombre, tps_s, primera)))
        resumen.append("| %02d | %s | %s | %s |" % (i, nombre, tps_s, primera.replace("|", "/")))
    if fallas:
        print(red("  %d/%d prompts con error HTTP: revisa el log del server." % (fallas, SANITY_TOTAL)))
    ruta_res = os.path.join(carpeta, "RESUMEN.md")
    if os.path.exists(ruta_res):
        # re-corrida del mismo tag: el resumen ANTERIOR se archiva (la
        # evidencia de la casa nunca se pisa; el informe guarda todas)
        viejo = os.path.join(carpeta, "RESUMEN-%s.md"
                             % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.replace(ruta_res, viejo)
        print(gray("  resumen anterior archivado: %s" % os.path.basename(viejo)))
    with open(ruta_res, "w", encoding="utf-8") as f:
        f.write("# Sanity %s — %d prompts (juez: Director)\n\n"
                "(respuestas completas en prompt-NN-*.txt junto a este archivo)\n\n"
                "| # | tipo | velocidad | primera linea |\n|---|------|-----------|---------------|\n"
                % (tag, SANITY_TOTAL))
        f.write("\n".join(resumen) + "\n")
    print(green("  resumen: %s" % ruta_res))
    print(yellow("  LEE las 20 respuestas (tu eres el catador) y cierra con:"))
    print("    py campana-10-pasos.py p3 --veredicto OK      (20/20 -> N3 CERRADO)")
    print("    py campana-10-pasos.py p3 --veredicto FALLA   (algo se rompio -> revert)")
    estado["pasos"]["3"] = {"estado": "EN-ESPERA-DEL-JUEZ", "carpeta": carpeta,
                            "errores_http": fallas}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P3 sanity %d prompts ejecutado (%s)" % (SANITY_TOTAL, tag),
            ["- carpeta: %s" % carpeta, "- errores http: %d" % fallas,
             "- esperando veredicto: p3 --veredicto OK|FALLA"])
    return 0


# ---------------- P4: descarga del cuant nuevo (fuera de la ruta critica) ----

def _binario_hf():
    for binario in ("hf", "huggingface-cli"):
        ruta = shutil.which(binario)
        if ruta:
            return [ruta]
    return None


def _envuelve_gui(cmd, es_windows=None):
    """En Windows, un ejecutable instalado como .bat/.cmd (shim de pip) no
    arranca con exec directo: CreateProcess no corre shells. Se envuelve en
    cmd /c. En Linux/macOS (o un .exe) pasa igual."""
    if es_windows is None:
        es_windows = (os.name == "nt")
    if cmd and es_windows and os.path.splitext(cmd[0])[1].lower() in (".bat", ".cmd"):
        return ["cmd", "/c"] + cmd
    return cmd


def _quita_modelo_de_flags(flags):
    """Quita un -m/--model <ruta> pegado dentro de las flags: el modelo del
    humo va a parte y SIEMPRE es el nuevo (un -m colado cargaria otro cuant
    y el humo mentiria)."""
    while "-m" in flags or "--model" in flags:
        i = flags.index("-m") if "-m" in flags else flags.index("--model")
        del flags[i:i + 2]
    return flags


def paso4(args, rutas, estado):
    print(bold(cyan("\n=== P4 - descarga UD-IQ3_XXS (corre cuando el rig NO mide) ===")))
    if args.repo == REPO_ALT and not args.fuerza:
        fatal("el repo alternativo esta DESAUTENTICADO: %s" % REPO_ALT_MOTIVO,
              ["usa el repo por defecto (%s)" % REPO_DEFAULT,
               "si la descarga se corto, re-ejecuta p4 igual: hf RETOMA donde iba",
               "si de verdad quieres el repo ALT: --fuerza (queda escrito, y p5 "
               "rechazara el archivo por SHA salvo que unsloth lo arregle)"])
    if args.repo == REPO_ALT and args.fuerza:
        informe(rutas["informe"], "P4 repo ALT usado con --fuerza",
                ["- %s" % REPO_ALT_MOTIVO,
                 "- el archivo bajado NO pasara el SHA256 de p5 salvo que "
                 "unsloth lo haya cambiado de vuelta"])
    if not estado["n3"].get("cerrado") and not args.fuerza:
        fatal("la puerta p3 no cerro el N3 (veredicto: %s)"
              % (estado["n3"].get("veredicto_sanity") or "SIN P3"),
              ["cierra el N3 con p3 --veredicto OK (o FALLA + revert)",
               "o --fuerza si el Director decide adelantarla (queda escrito)"])
    os.makedirs(rutas["models"], exist_ok=True)
    destino = os.path.join(rutas["models"], MODELO_NUEVO_NOMBRE)
    if os.path.exists(destino):
        tam = os.path.getsize(destino)
        print(yellow("  el archivo YA existe (%.2f GB). Si venia de una descarga cortada, "
                     "el propio hf retoma; para verificarlo directo: p5." % (tam / 1024.0 ** 3)))
    cache_hf = os.path.join(rutas["base"], "hf-cache")
    os.makedirs(cache_hf, exist_ok=True)
    binario = _binario_hf()
    cmd = (binario or ["hf"]) + ["download", args.repo, MODELO_NUEVO_NOMBRE,
                                 "--local-dir", rutas["models"]]
    libre, total = gb_libres(rutas["models"])
    print("  destino    : %s" % destino)
    print("  tamano     : %.2f GB exactos (%d B)" % (MODELO_NUEVO_BYTES / 1024.0 ** 3, MODELO_NUEVO_BYTES))
    print("  cache HF   : %s (EN D:, fuera de C:)" % cache_hf)
    print("  comando    : %s" % " ".join(cmd))
    if libre is not None:
        estilo = green if libre >= DISCO_MIN_GB else red
        print(estilo("  disco D:   : %.1f GB libres (minimo %.0f)" % (libre, DISCO_MIN_GB)))
        if libre < DISCO_MIN_GB:
            if args.dry_run:
                print(red("  (dry-run: no frena aqui, pero en descarga real esto es FATAL)"))
            else:
                fatal("D: sin espacio suficiente para la descarga",
                      ["libera espacio o pasa --dir a otro disco con sitio"])
    if not binario:
        if args.dry_run:
            print(red("  (dry-run: sin cliente hf instalado; en real esto es FATAL "
                      "-> pip install -U \"huggingface_hub[cli]\")"))
        else:
            fatal("no encuentro el cliente de HuggingFace (hf / huggingface-cli)",
                  ["instalalo con: pip install -U \"huggingface_hub[cli]\""])
    if args.dry_run:
        print(yellow("  (--dry-run: nada se descargo)"))
        return 0
    if not confirmar("DESCARGAR", "Arranca la descarga (%.2f GB). Puede correr sola de noche; "
                                  "Ctrl+C la PAUSA y p4 la retoma." % (MODELO_NUEVO_BYTES / 1024.0 ** 3)):
        print(gray("  cancelado."))
        informe(rutas["informe"], "P4 descarga CANCELADA por el Director",
                ["- nada se descargo en este intento"])
        return 1
    env = dict(os.environ)
    env["HF_HOME"] = cache_hf
    try:
        rc = subprocess.call(_envuelve_gui(cmd), env=env)
    except KeyboardInterrupt:
        print(yellow("\n  INTERRUMPIDO (Ctrl+C): pausada. p4 la retoma mas tarde."))
        return 130
    if rc != 0:
        fatal("el cliente de HF salio con rc=%d" % rc,
              ["repite p4: la descarga retoma donde quedo"])
    tam = os.path.getsize(destino) if os.path.exists(destino) else 0
    if tam != MODELO_NUEVO_BYTES:
        fatal("bytes en disco (%d) != certificados (%d)" % (tam, MODELO_NUEVO_BYTES),
              ["puede ser descarga incompleta: repite p4 (retoma)",
               "el autenticador de bytes es cerrado [F RUTAS.md L738]"])
    print(green("  bytes exactos en disco: %d [OK] (certificado [F])" % tam))
    estado["pasos"]["4"] = {"estado": "DESCARGADA", "ruta": destino, "bytes": tam}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P4 descarga UD-IQ3_XXS -> DESCARGADA",
            ["- ruta: %s" % destino, "- bytes: %d (certificado)" % tam,
             "- cache HF en: %s" % cache_hf, "- siguiente: p5 (SHA256 + parser + humo)"])
    print(cyan("  siguiente: p5 (fail-fast: SHA256 + parser nextn + humo)."))
    return 0


# ---------------- P5: verificacion + humo del cuant nuevo -------------------

def verificar_descarga(ruta, sha_esperado, bytes_esperados):
    """(ok, lineas). Bytes exactos + SHA256 streaming con el certificado [F]."""
    lineas, ok = [], True
    tam = os.path.getsize(ruta)
    if tam != bytes_esperados:
        lineas.append("bytes en disco %d != certificados %d" % (tam, bytes_esperados))
        return False, lineas
    lineas.append("bytes exactos: %d [OK]" % tam)
    print(cyan("  SHA256 en streaming (13 GB, ~1-2 min)..."))
    sha = sha256_archivo(ruta, notificador=lambda s: print(gray(s)))
    if sha != sha_esperado:
        lineas.append("SHA256 %s != certificado %s" % (sha, sha_esperado))
        return False, lineas
    lineas.append("SHA256 [OK] certificado %s...%s" % (sha[:8], sha[-4:]))
    return ok, lineas


def verificar_gguf(ruta):
    """(metadatos, nextn_ok, lineas): parser GGUF de la casa (cero tensores)."""
    meta, err = gguf_metadatos(ruta)
    lineas = []
    if meta is None:
        return None, False, ["parser GGUF fallo: %s" % err]
    nextn = [k for k in meta if "nextn" in k]
    for clave in ("general.architecture",):
        if clave in meta:
            lineas.append("%s = %s" % (clave, meta[clave]))
    for k in sorted(meta):
        if k.endswith(".block_count") or k.endswith(".expert_count") or k.endswith(".expert_used_count"):
            lineas.append("%s = %s" % (k, meta[k]))
    lineas.append("tensores nextn (MTP dentro): %s" % (sorted(nextn) if nextn else "NINGUNO"))
    return meta, nextn, lineas  # nextn = LISTA de claves ([] = ausente)


def paso5(args, rutas, estado):
    print(bold(cyan("\n=== P5 - verificacion + humo del cuant nuevo (fail-fast) ===")))
    p4 = estado["pasos"].get("4", {})
    ruta = p4.get("ruta") or os.path.join(rutas["models"], MODELO_NUEVO_NOMBRE)
    if not os.path.exists(ruta):
        fatal("no esta el modelo nuevo en %s" % ruta,
              ["descarga primero: p4", "o pasa --dir si cambio de carpeta"])
    lineas = []
    ok_sha, lineas_sha = verificar_descarga(ruta, MODELO_NUEVO_SHA, MODELO_NUEVO_BYTES)
    for ln in lineas_sha:
        print("  %s" % (green(ln) if "[OK]" in ln else red(ln)))
    if not ok_sha:
        estado["pasos"]["5"] = {"estado": "FALLO-CERTIFICADO", "detalle": lineas_sha}
        guardar_estado(rutas["estado"], estado)
        informe(rutas["informe"], "P5 certificacion -> FALLO", ["- %s" % l for l in lineas_sha])
        fatal("el archivo NO es el certificado: NO se usa. Repite p4 (retoma) o re-descarga.",
              lineas_sha)
    meta, nextn, lineas_gguf = verificar_gguf(ruta)
    for ln in lineas_gguf:
        print("  %s" % (green(ln) if "nextn" in ln and "NINGUNO" not in ln else gray(ln)))
    if meta is None:
        fatal("la cabecera GGUF no se pudo leer", lineas_gguf)
    if not nextn:
        print(yellow("  SIN tensores nextn: el MTP NO viene dentro -> plan B draft separado "
                     "(doc N5); la descarga sigue siendo valida como cuant base."))
        lineas.append("- nextn: AUSENTE (plan B draft separado)")
    else:
        lineas.append("- nextn: PRESENTE (%d claves)" % len(nextn))
    lineas += ["- %s" % l for l in lineas_sha + lineas_gguf]

    if args.sin_humo:
        print(yellow("  (--sin-humo: verificacion lista; humo saltado a proposito)"))
        estado["pasos"]["5"] = {"estado": "VERIFICADO-SIN-HUMO", "nextn": nextn, "detalle": lineas}
        guardar_estado(rutas["estado"], estado)
        informe(rutas["informe"], "P5 verificacion (sin humo)", ["- %s" % l for l in lineas])
        return 0

    # -- humo: receta promovida + modelo nuevo, 1 prompt, y se apaga --
    cfg = leer_config(rutas["config"])
    puerto = args.puerto
    if health_ok(puerto):
        fatal("ya hay un server vivo en el puerto %d (guardarrail de la casa)" % puerto,
              ["apaga el server diario antes del humo", "o usa --puerto 9932"])
    servidor = cfg.get("RUTA_SERVER", "")
    if not servidor:
        fatal("config.txt no trae RUTA_SERVER (el humo no sabe QUE server arrancar)",
              ["revisa config.txt: RUTA_SERVER = ruta del llama-server.exe"])
    if not os.path.exists(servidor):
        fatal("el server no esta donde dice config.txt: %s" % servidor,
              ["revisa RUTA_SERVER en config.txt"])
    flags = (cfg.get("FLAGS_BASE", "") + " " + cfg.get("FLAGS_GANADORAS", "")).split()
    # el modelo va A PARTE y SIEMPRE es el nuevo (ver _quita_modelo_de_flags)
    flags = _quita_modelo_de_flags(flags)
    # MISMA regla del lanzador de la casa (abrir-qwen-apex.py): el override
    # de expertos SOLO se anade si EXPERTOS_TRABAJO != 8 (8 = de fabrica);
    # sin esto el humo corria una receta DIFERENTE a la diaria
    try:
        k = int(cfg.get("EXPERTOS_TRABAJO", "8"))
    except Exception:
        k = 8
    if k != 8:
        flags += ["--override-kv", "qwen35moe.expert_used_count=int:%d" % k]
    cmd = [servidor, "-m", ruta] + flags + [
        "--host", "127.0.0.1", "--port", str(puerto)]
    log_humo = os.path.join(rutas["base"], "campana-humo.log")
    print(cyan("  humo: arrancando server con el modelo NUEVO (puerto %d)..." % puerto))
    print(gray("  $ %s" % " ".join(cmd)))
    # forense ACUMULATIVO: cada intento anade su cabecera; nada se pisa
    with open(log_humo, "a", encoding="utf-8") as flog:
        flog.write("===== intento de humo %s (puerto %d) =====\n"
                   % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), puerto))
        flog.flush()
        proc = subprocess.Popen(cmd, stdout=flog, stderr=subprocess.STDOUT)
        try:
            fin = time.time() + 420
            while time.time() < fin:
                if proc.poll() is not None:
                    fatal("el server murio durante la carga del modelo nuevo (rc=%s)" % proc.returncode,
                          ["forense en %s" % log_humo,
                           "si dice VRAM insuficiente, el cuant nuevo necesito otra colocacion"])
                if health_ok(puerto):
                    break
                time.sleep(2)
            else:
                fatal("el server no levanto en 7 min", ["forense en %s" % log_humo])
            try:
                contenido, tps = _chat_uno(puerto, "Responde solo: HUMO OK")
            except Exception as e:
                fatal("el humo no pudo hablar con el server: %r" % e,
                      ["forense en %s" % log_humo])
            print(green("  respuesta del humo: %s" % contenido.strip()[:80]))
            if tps:
                print(green("  velocidad: %.1f t/s" % tps))
                lineas.append("- humo: %.1f t/s" % tps)
            lineas.append("- humo: respuesta OK con la receta promovida + modelo nuevo")
        finally:
            # el humo lanzo SU PROPIO hijo: lo termina directo (multiplataforma,
            # sin taskkill y sin riesgo de matar un server ajeno)
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
    print(green("  HUMO SANO: el cuant nuevo carga y responde con la receta de la casa."))
    estado["pasos"]["5"] = {"estado": "VERIFICADO-HUMO-OK", "nextn": nextn, "detalle": lineas}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P5 verificacion + humo -> OK", ["- %s" % l for l in lineas])
    print(cyan("  siguiente: p6 (N1 formal) o directo a p7 cuando puedas."))
    return 0


# ---------------- P6: N1 formal (BARRIDO-N1.bat) ----------------------------

def paso6(args, rutas, estado):
    print(bold(cyan("\n=== P6 - N1 formal (BARRIDO-N1.bat v1.2.1, ~50-65 min) ===")))
    candidatos = ([args.bat] if args.bat else
                  [os.path.join(rutas["base"], "BARRIDO-N1.bat"),
                   os.path.join(rutas["base"], "scripts", "BARRIDO-N1.bat")])
    bat = next((b for b in candidatos if b and os.path.exists(b)), None)
    if not bat:
        fatal("no encuentro BARRIDO-N1.bat",
              ["pasalo con --bat D:\\ZLia\\BARRIDO-N1.bat"])
    print("  bat: %s" % bat)
    print(yellow("  corre CON la receta ya promovida (-np 2): sus numeros viven en el mundo final."))
    if not confirmar("LANZAR", "Ocupara el rig ~50-65 min. Sin descargas ni apps en paralelo."):
        print(gray("  cancelado."))
        informe(rutas["informe"], "P6 N1 formal CANCELADO por el Director",
                ["- el bat no se lanzo"])
        return 1
    cmd = ["cmd", "/c", bat] if os.name == "nt" else [bat]
    try:
        rc = subprocess.call(cmd)
    except KeyboardInterrupt:
        print(yellow("\n  INTERRUMPIDO (Ctrl+C): N1 formal pausado. El resume de "
                     "la casa permite repetirlo."))
        return 130
    if rc != 0:
        fatal("BARRIDO-N1.bat salio con rc=%d" % rc,
              ["revisa su salida/informe; el resume de la casa permite repetirlo"])
    estado["pasos"]["6"] = {"estado": "EJECUTADO", "bat": bat}
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P6 N1 formal -> EJECUTADO",
            ["- bat: %s" % bat, "- rc: %d" % rc,
             "- recuerda: sanity tras N1 (p3 --tag n1 con el server del cuant actual)"])
    print(cyan("  siguiente: sanity del N1 (p3 --tag n1) y luego p7 (N2 dosis)."))
    return 0


# ---------------- P7..P10: guiados (el instrumento fino se genera al llegar) -

CHECKLISTS = {
    "7": ("N2 - dosis re-aplicadas sobre el cuant nuevo",
          ["re-ancla con el modelo nuevo (misma receta promovida)",
           "re-aplicar: escalera k de N1 (transfiere: es arquitectura)",
           "re-aplicar: cache de prompts y -ctxcp 4 (ahora con ~1 GB mas de margen)",
           "UB1K SOLO donde no estorbe (R32: UB1K x NCM = -16.5%)",
           "re-check rapido de NCM37C4 (dosis de capas: no transfiere limpia)",
           "sanity con tool-calling OBLIGATORIO (p3 --tag n2 con el modelo nuevo en config)"],
          "criterio: >= +8% t/s con calidad intacta y ~+1 GB RAM libre [N2 s5]"),
    "8": ("N4 - escalera de VRAM sobre el cuant nuevo",
          ["escalera ascendente de ngl/limites (una dosis por corrida, ancla por sesion)",
           "MEC dosis fina en MiB; regla cliff-1 (para UNO antes del cliff)",
           "certificados: nvidia-smi <= 3.7 GB, delta de buffer en log, pageouts ~ 0"],
          "criterio: frontera VRAM estable sin cliff; modo dual ratificado"),
    "9": ("RUTA 0 - build b11901 (2 zips, sin compilar)",
          ["descargar (cuando el rig NO mide): llama-b11901-bin-win-cuda-12.4-x64.zip",
           "+ el zip de cudart DLLs del mismo release (sin el cudart la GPU queda dormida)",
           "re-auditoria de defaults del build nuevo (dump vs llama-flags)",
           "re-certificar overrides: la clave qwen35moe.expert_used_count puede cambiar",
           "probar si cache-reuse revive (busca 'restored context checkpoint' en el log)",
           "re-ancla completa: el build nuevo es un mundo nuevo"],
          "criterio: reuse vivo o motivo cerrado con certificado; overrides aplicados"),
    "10": ("N5 - duelo spec vs NP2 + receta final",
           ["fase E: MTP-n2 (el draft puede venir dentro del GGUF nuevo: revisa p5 nextn)",
            "fase S: DSpark Q4_K_M n2/n3 (A/B conf-min 0.5-0.7) -> DFlash-n2 -> EAGLE3",
            "fijar SIEMPRE --spec-draft-n-max y --spec-draft-p-min explicitos",
            "DUELO: receta con NP2 sin spec vs receta con spec sin NP2 (mediana de 3)",
            "ojo #25345 kv-unified: si el draft calla, --kv-unified off",
            "spot-check ES por config; gana el mejor t/s x calidad"],
           "criterio: >= +25% [M] con spot-check limpio; luego receta final con backup"),
}


def paso_guiado(n, args, rutas, estado):
    titulo, items, criterio = CHECKLISTS[n]
    print(bold(cyan("\n=== P%s - %s (guiado) ===" % (n, titulo))))
    print(yellow("  (el instrumento fino de este nivel se genera con el esqueleto de "
                 "la casa cuando se llega: aqui la ruta y la decision por escrito)"))
    for it in items:
        print("    [ ] %s" % it)
    print("  %s" % gray(criterio))
    try:
        nota = input(yellow("  resultado/decision de este paso (linea libre, Enter para dejar pendiente): ")).strip()
    except EOFError:
        nota = ""
    registro = {"estado": "REGISTRADO" if nota else "PENDIENTE"}
    if nota:
        registro["nota"] = nota
    estado["pasos"][n] = registro
    guardar_estado(rutas["estado"], estado)
    informe(rutas["informe"], "P%s %s -> %s" % (n, titulo.split(" ·")[0], registro["estado"]),
            (["- nota del Director: %s" % nota] if nota else ["- pendiente"]) +
            ["- checklist aplicada (%d items)" % len(items)])
    print(cyan("  registrado en campana-estado.json y campana-INFORME.md"))
    return 0


# ---------------- estado / plan / main --------------------------------------

VERDES_ESTADO = ("GO", "PROMOVIDA", "YA-PROMOVIDA", "OK", "DESCARGADA",
                 "VERIFICADO-HUMO-OK", "EJECUTADO", "REGISTRADO")
AMARILLOS_ESTADO = ("DUDOSO", "PENDIENTE", "EN-ESPERA-DEL-JUEZ", "INCOMPLETO",
                    "VERIFICADO-SIN-HUMO", "REVERTIDA", "NO-GO")


def mostrar_estado(rutas, estado):
    print(bold(cyan("\n=== CAMPANA - %s ===" % estado.get("actualizado", "sin empezar"))))
    print("  informe append-only: %s" % rutas["informe"])
    tabla = [("1", "mediana NP2 (higiene + NOCACHE)"), ("2", "promocion -np 2"),
             ("3", "sanity 20 prompts -> cierra N3"), ("4", "descarga UD-IQ3_XXS"),
             ("5", "verificacion + humo del cuant"), ("6", "N1 formal (bat)"),
             ("7", "N2 dosis re-aplicadas"), ("8", "N4 escalera VRAM"),
             ("9", "RUTA 0 build b11901"), ("10", "N5 duelo spec vs NP2 + receta final")]
    for n, titulo in tabla:
        paso = estado["pasos"].get(n, {})
        et = paso.get("estado", "PENDIENTE")
        estilo = green if et in VERDES_ESTADO else (yellow if et in AMARILLOS_ESTADO else red)
        print("   P%-3s %-38s %s" % (n, titulo, estilo(et)))
    n3 = estado.get("n3", {})
    print("  N3: cerrado=%s veredicto_sanity=%s" % (n3.get("cerrado", False),
                                                    n3.get("veredicto_sanity", "-")))
    print(gray("  regla: descargas cuando el rig NO mide; mediana de 3; --fuerza salta "
               "puertas y lo deja escrito."))
    return 0


def main():
    ap = argparse.ArgumentParser(description=VERSION)
    ap.add_argument("paso", nargs="?", default="estado",
                    help="estado | plan | p1..p10")
    ap.add_argument("--dir", help="carpeta base de la campana (def: junto al script)")
    ap.add_argument("--config", help="ruta de config.txt (def: base/config.txt)")
    ap.add_argument("--puerto", type=int, default=9931)
    ap.add_argument("--b1", help="p1: carpeta de la corrida 1 (def: base/faseN3)")
    ap.add_argument("--b2", help="p1: carpeta de la corrida 2 (def: base/faseN3-np2-b2)")
    ap.add_argument("--b3", help="p1: carpeta de la corrida 3 (def: base/faseN3-np2-b3)")
    ap.add_argument("--sin-corridas", action="store_true",
                    help="p1: cosechar sin lanzar corridas nuevas")
    ap.add_argument("--revert", action="store_true", help="p2: restaurar backup")
    ap.add_argument("--veredicto", help="p3: OK | FALLA (cierra el N3)")
    ap.add_argument("--tag", help="p3: etiqueta de la carpeta de sanity")
    ap.add_argument("--repo", default=REPO_DEFAULT,
                    help="p4: repo HF (def: %s). El ALT (%s) esta "
                         "DESAUTENTICADO en vivo 29-oct: sirve la variante "
                         "SIN MTP y p4 lo rechaza"
                         % (REPO_DEFAULT, REPO_ALT))
    ap.add_argument("--dry-run", action="store_true", help="p4: mostrar sin descargar")
    ap.add_argument("--sin-humo", action="store_true", help="p5: solo certificar, sin server")
    ap.add_argument("--bat", help="p6: ruta de BARRIDO-N1.bat")
    ap.add_argument("--fuerza", action="store_true",
                    help="saltar puertas A PROPOSITO (queda escrito en el informe)")
    args = ap.parse_args()
    rutas = _rutas(args)
    estado = leer_estado(rutas["estado"])

    bruto = args.paso.lower()
    paso = bruto[1:] if (bruto.startswith("p") and bruto[1:].isdigit()) else bruto
    if paso == "estado":
        rc = mostrar_estado(rutas, estado)
        _pausa_doble_click()
        return rc
    if paso == "plan":
        mostrar_estado(rutas, estado)
        print(gray("  detalle completo: plan-siguientes-10-pasos.md en el repo"))
        return 0
    if paso == "1":
        return paso1(args, rutas, estado)
    if paso == "2":
        return paso2(args, rutas, estado)
    if paso == "3":
        return paso3(args, rutas, estado)
    if paso == "4":
        return paso4(args, rutas, estado)
    if paso == "5":
        return paso5(args, rutas, estado)
    if paso == "6":
        return paso6(args, rutas, estado)
    if paso in CHECKLISTS:
        return paso_guiado(paso, args, rutas, estado)
    print(red("paso desconocido: %s (usa estado | plan | p1..p10)" % args.paso))
    return 1


if __name__ == "__main__":
    sys.exit(main())
