#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de CAMPANA-N4-N5.py v1.0 con taller falso (sin GPU, sin red, sin
13 GB). Patron de la casa (test_campana6a10_mock): el modulo se carga por
importlib desde InformacionCritica/scripts, los directorios del rig son
temporales y los objetos pesados son FALSOS PERO REALISTAS.

Es la bateria de su hermana CAMPANA-6A10.py ADAPTADA a la olla real nacida
del boceto (r65; renombrada CAMPANA-N4-N5.py en r67 por orden del
Director "si ahora es n4 cambiale el titulo, no mezcles cosas"), con los
checks nuevos de los deltas documentados:

  - config.txt falso, SERVER FALSO (--version b11901, --help para el diff,
    --die para el cliff, /health + /v1/chat/completions con timings y las
    3 ANCLAS de calidad), MODELO falso y primera olla falsa.
  - Verifica: huella anti-tamper, cirugia de flags por tokens, tablas
    candidatas/escalera derivadas de la receta REAL (v2: NCM primero y
    activo, NGL inactivas al final, --moe-cache-mib nombre real, pilas
    con ';', sin mlock), estado corrupto -> evidencia .corrupto, anclas
    de calidad, PUERTAS, P7 completa (ancla + candidata + sanity),
    P8 con cliff real y regla cliff-1 + hueco para P10 en el informe,
    P9 (version + cudart + diff --help + reuse vivo + re-ancla MED3),
    P10 (duelo A/B + fallback C + receta final con backup y re-lectura),
    informes APPEND-ONLY con linea "- script:" (delta D3) y MODO AUTO
    end-to-end (7..10 verdes).
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import socket
import stat
import sys
import tempfile
import types

RAIZ = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(RAIZ, "..", "InformacionCritica", "scripts",
                      "CAMPANA-N4-N5.py")

SERVER_FALSO = r'''#!/usr/bin/env python3
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
ARGS = sys.argv[1:]
ES_B11901 = "b11901" in sys.argv[0]   # el build nuevo se comporta como nuevo
if "--version" in ARGS or "-v" in ARGS:
    print("version: %s (c7adfabe)" % ("b11901" if ES_B11901 else "b11856"))
    sys.exit(0)
if "--help" in ARGS or "-h" in ARGS:
    print("usage: llama-server [options]")
    print("  -ngl, --n-gpu-layers N   number of layers to store in VRAM")
    print("  -c, --ctx-size N         size of the prompt context")
    print("  -np, --parallel N        number of parallel sequences")
    print("  -ub, --ubatch-size N     physical maximum batch size")
    if ES_B11901:
        print("  --expert-used-count N    family expert_used_count (fake)")
    sys.exit(0)
if "--die" in ARGS:
    sys.stderr.write("killswitch: el peldano rasga\n")
    sys.exit(1)
PORT = 0
for i, a in enumerate(ARGS):
    if a == "--port":
        PORT = int(ARGS[i + 1])
REUSE = "--cache-reuse" in ARGS
CONTADOR = [0]

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path == "/health":
            if REUSE:
                CONTADOR[0] += 1
                if CONTADOR[0] >= 2:
                    sys.stdout.write("restore: restored context checkpoint (fake)\n")
                    sys.stdout.flush()
            return self._json(200, {"status": "ok"})
        return self._json(404, {"error": "no"})
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        req = json.loads(self.rfile.read(n) or b"{}")
        texto = req.get("messages", [{}])[0].get("content", "")
        low = texto.lower()
        resp = None
        # el sondeo de reuse (p9): con --cache-reuse el log del server
        # anuncia el checkpoint restaurado desde la 2a peticion
        if REUSE and CONTADOR[0] >= 1:
            sys.stdout.write("restore: restored context checkpoint (fake)\n")
            sys.stdout.flush()
        if "17 * 23" in texto or "17*23" in low:
            resp = "391"
        elif "verde" in low and "color" in low:
            resp = "Tu color favorito es el verde."
        elif "valpara" in low:
            resp = "Trabajas en Valparaiso."
        elif "2030" in low:
            resp = "No lo se: no tengo datos del mundial de 2030."
        elif "fizzbuzz" in low:
            resp = "for i in range(1, 16): print(...)"
        else:
            resp = "Lista en marcha: la olla hierve con calma."
        tps = 20.0 + (CONTADOR[0] % 3) * 0.5
        CONTADOR[0] += 1
        self._json(200, {"choices": [{"message": {"content": resp}}],
                         "timings": {"predicted_per_second": tps}})

HTTPServer(("127.0.0.1", PORT), H).serve_forever()
'''


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def carga_modulo():
    spec = importlib.util.spec_from_file_location("campanan4n5_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CHECKS = []


def check(nombre, cond):
    CHECKS.append((nombre, bool(cond)))
    print("%s %s" % ("[OK]  " if cond else "[FALLO]", nombre))


def args_falsos(mod, base, puerto, **kw):
    d = dict(dir=base, config=None, puerto=puerto, corridas=1, m_prompts=3,
             archivo=None, previa=False, sin_sanity=False, build_dir=None,
             fuerza=False)
    d.update(kw)
    return types.SimpleNamespace(**d)


def main():
    m = carga_modulo()
    tmp = tempfile.mkdtemp(prefix="cn4n5-")
    try:
        # ---------- taller falso ----------
        base = os.path.join(tmp, "rig")
        os.makedirs(base)
        srv = os.path.join(tmp, "llama-server-falso.py")
        with open(srv, "w", encoding="utf-8") as f:
            f.write(SERVER_FALSO)
        os.chmod(srv, os.stat(srv).st_mode | stat.S_IEXEC)
        modelo = os.path.join(base, "models", "falso.gguf")
        os.makedirs(os.path.dirname(modelo))
        with open(modelo, "wb") as f:
            f.write(b"GGUFfalso" * 100)
        with open(os.path.join(base, "config.txt"), "w", encoding="utf-8") as f:
            f.write("RUTA_SERVER = %s\n" % srv)
            f.write("RUTA_MODELO = %s\n" % modelo)
            f.write("EXPERTOS_TRABAJO = 8\n")
            f.write("EXPERTOS_CHARLA = 4\n")
            f.write("FLAGS_BASE = -ngl 99 -c 16384 -b 2048 -ub 256 -lm none\n")
            f.write("SAMPLING = --temp 1.0 --top-k 20\n")
            f.write("FLAGS_GANADORAS = -ub 1024 -b 4096\n")
        with open(os.path.join(base, "campana-estado.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"n3": {"cerrado": True},
                       "pasos": {"3": {"estado": "OK"},
                                 "6": {"estado": "EJECUTADO"}}}, f)

        # ---------- unidad: huella ----------
        ok, causa = m._autoverifica_huella()
        check("U01 huella anti-tamper del archivo en disco", ok)
        check("U02 mediana basica", m.mediana([2.0, 4.0, 9.0]) == 4.0)
        check("U03 mediana sin datos -> None", m.mediana([]) is None)
        check("U04 sin_tildes normaliza", m.sin_tildes("Valparaíso") == "Valparaiso")

        # ---------- unidad: cirugia de flags ----------
        tok = ["-ngl", "99", "-b", "2048"]
        check("U05 add anade tokens", m._acciona(tok, "add:--ctxcp,4")
              == ["-ngl", "99", "-b", "2048", "--ctxcp", "4"])
        check("U06 del borra el token", m._acciona(tok, "del:99")
              == ["-ngl", "-b", "2048"])
        check("U07 delpair borra flag+valor", m._acciona(tok, "delpair:-b")
              == ["-ngl", "99"])
        check("U08 sub sustituye TODAS las apariciones (T4)",
              m._acciona(["-ctk", "q8_0", "-ctv", "q8_0"], "sub:q8_0>f16")
              == ["-ctk", "f16", "-ctv", "f16"])
        check("U09 delpair con flag sin valor", m._acciona(["-cmoe", "-b", "2048"],
                                                           "delpair:-cmoe")
              == ["-b", "2048"])
        check("U10 _quita_modelo saca -m y su ruta",
              m._quita_modelo(["-m", "X.gguf", "-ngl", "99"]) == ["-ngl", "99"])
        check("U11 _acciona con acciones vacias = receta intacta",
              m._acciona(tok, "") == tok)

        # ---------- unidad: tablas ----------
        tab = os.path.join(tmp, "tabla.txt")
        with open(tab, "w", encoding="utf-8") as f:
            f.write("# comentario\n\nA | add:--x | activa | nota a\n"
                    "B | | inactiva | nota b\n")
        filas = m._leer_tabla(tab)
        check("U12 tabla: ignora # y parsea activa/inactiva",
              len(filas) == 2 and filas[0]["activa"] and not filas[1]["activa"])

        # ---------- unidad: derivas (P7 igual a la hermana; P8 CORREGIDA) ----
        cfg = m.leer_config(os.path.join(base, "config.txt"))
        lineas, avisos = m._deriva_candidatas(cfg)
        texto = "\n".join(lineas)
        check("U13 deriva K-N1-PIN8 desde EXPERTOS_TRABAJO (dos ramas, F9)",
              "K-N1-PIN8 | add:--override-kv,qwen35moe.expert_used_count=8 | activa"
              in texto)
        check("U14 deriva SIN-UB1K (hay -ub) y CTXCP4",
              "SIN-UB1K" in texto and "CTXCP4" in texto)
        lineas8, avisos8 = m._deriva_escalera(cfg)
        t8 = "\n".join(lineas8)
        # delta D1: la escalera nace CORREGIDA (trampas T1/T2/T3 del boceto)
        check("U15a NCM primero y ACTIVO (T1)",
              "NCM38 | add:-ncmoe,38 | activa" in t8
              and t8.index("NCM38") < t8.index("NGL-"))
        check("U15b los 5 peldanos NCM activos 38..34",
              all(("NCM%d | add:-ncmoe,%d | activa" % (n, n)) in t8
                  for n in (38, 37, 36, 35, 34)))
        check("U15c NGL-87/93 INACTIVAS (T1)",
              "NGL-87 | sub:99>87 | inactiva" in t8
              and "NGL-93 | sub:99>93 | inactiva" in t8)
        check("U16a MEC con el nombre REAL --moe-cache-mib (T2)",
              "add:--moe-cache-mib,512" in t8)
        check("U16b el placeholder muerto --cmoe-cache NO aparece (T2)",
              "--cmoe-cache," not in t8.replace("--moe-cache-mib,", ""))
        check("U16c sin peldano mlock (plan R3) y BLIND-OT37 presente",
              "PAGINA-ON" not in t8 and "BLIND-OT37" in t8)
        check("U16d pilas de vuelta 2 con ';' e inactivas (T3)",
              "WIN+MEC512 | add:-ncmoe,37;add:--moe-cache-mib,512 | inactiva" in t8
              and "WIN+CHARLA4" in t8)
        check("U16e avisos de derivacion no vacios (delta D2)", len(avisos8) >= 1)

        # ---------- unidad: anclas ----------
        ok_a, _ = m._anclas_chequeo([("ancla-aritmetica", "391"),
                                     ("ancla-memoria", "el verde"),
                                     ("ancla-seguimiento", "Valparaíso")])
        check("U17 anclas OK con tildes", ok_a)
        ok_b, motivos = m._anclas_chequeo([("ancla-aritmetica", "392"),
                                           ("ancla-memoria", ""),
                                           ("ancla-seguimiento", "Santiago")])
        # 4 motivos: la respuesta vacia anade el suyo (sin carne) a los 3 anclas
        check("U18 anclas FALLA senala motivos", (not ok_b) and len(motivos) == 4)

        # ---------- unidad: estado corrupto -> evidencia ----------
        podrido = os.path.join(base, "campana-n4-n5-estado.json")
        with open(podrido, "w", encoding="utf-8") as f:
            f.write("{esto no es json")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            est = m.leer_estado(podrido)
        check("U19 estado corrupto -> dict fresco", est.get("pasos") == {})
        restos = [x for x in os.listdir(base) if ".corrupto-" in x]
        check("U20 estado corrupto deja evidencia .corrupto", len(restos) == 1)

        # ---------- puertas y P7 ----------
        rutas = m._rutas(args_falsos(m, base, 0))
        estado = m.leer_estado(rutas["estado"])
        cerrada, det = m._primera_olla(rutas)
        check("U21 primera olla falsa cerrada (formula exacta F3)", cerrada)

        pu = puerto_libre()
        a = args_falsos(m, base, pu)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = m.paso7(a, rutas, m.leer_estado(rutas["estado"]))
        est7 = m.leer_estado(rutas["estado"])["pasos"]["7"]
        check("P01 p7 corre con taller falso (rc 0)", rc == 0)
        check("P02 p7 queda verde (GO o REGISTRADO)",
              est7["estado"] in ("GO", "REGISTRADO"))
        check("P03 p7 midio ancla", est7.get("ancla_tps", 0) > 0)
        check("P04 sanity con anclas OK",
              est7.get("sanity", {}).get("ok") is True)
        check("P05 CSV de p7 existe",
              os.path.exists(os.path.join(base, "campana-n4-n5-p7",
                                          "resultados.csv")))
        candidatas_txt = open(os.path.join(base, "campana-n4-n5-p7-candidatas.txt"),
                              encoding="utf-8").read()
        check("P06 candidatas generadas con K-N1-PIN8 activa",
              "K-N1-PIN8" in candidatas_txt and "ANCLA" in candidatas_txt)
        inf7 = open(rutas["informe"], encoding="utf-8").read()
        check("P07 informe append-only con seccion P7", "P7 N2 dosis" in inf7)
        check("P07b informe lleva la linea - script: (delta D3)",
              "- script: CAMPANA-N4-N5.py" in inf7)

        # p7 --previa: rc 0 y NINGUN server (rapido)
        a_prev = args_falsos(m, base, puerto_libre(), previa=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_prev = m.paso7(a_prev, rutas, m.leer_estado(rutas["estado"]))
        check("P08 p7 --previa rc 0 sin tocar servers", rc_prev == 0)

        # ---------- P8: cliff real con --die ----------
        tabla_die = os.path.join(base, "escala-die.txt")
        with open(tabla_die, "w", encoding="utf-8") as f:
            f.write("ANCLA | | ancla | receta\n"
                    "BUENO | sub:2048>2048 | activa | peldano sano (no-op)\n"
                    "RASGADO | add:--die | activa | muere a proposito\n")
        a_die = args_falsos(m, base, puerto_libre(), archivo=tabla_die)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc8 = m.paso8(a_die, rutas, m.leer_estado(rutas["estado"]))
        est8 = m.leer_estado(rutas["estado"])["pasos"]["8"]
        check("P09 p8 con cliff real corre (rc 0)", rc8 == 0)
        check("P10 cliff detectado en RASGADO", est8.get("cliff") == "RASGADO")
        check("P11 regla cliff-1: frontera = BUENO",
              (est8.get("frontera") or {}).get("nombre") == "BUENO")
        check("P12 p8 verde", est8["estado"] in ("GO", "REGISTRADO"))
        inf8 = open(rutas["informe"], encoding="utf-8").read()
        check("P13 informe p8 con CLIFF y HUECO para P10 (deltas)",
              "P8 escalera VRAM" in inf8 and "CLIFF" in inf8
              and "HUECO" in inf8)

        # ---------- P9: b11901 falso ----------
        build = os.path.join(tmp, "llama.cpp", "b11901")
        os.makedirs(build)
        srv2 = os.path.join(build, "llama-server")
        with open(srv2, "w", encoding="utf-8") as f:
            f.write(SERVER_FALSO)
        os.chmod(srv2, os.stat(srv2).st_mode | stat.S_IEXEC)
        with open(os.path.join(build, "cudart64_12.dll"), "wb") as f:
            f.write(b"dll de mentira")
        a9 = args_falsos(m, base, puerto_libre(), build_dir=build)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc9 = m.paso9(a9, rutas, m.leer_estado(rutas["estado"]))
        est9 = m.leer_estado(rutas["estado"])["pasos"]["9"]
        check("P14 p9 corre con build falso (rc 0)", rc9 == 0)
        check("P15 p9 verde (reuse vivo -> MOTIVO-CERRADO o GO)",
              est9["estado"] in ("GO", "MOTIVO-CERRADO"))
        check("P16 reuse VIVO detectado en el log", est9.get("reuse_vivo") is True)
        check("P17 diff de defaults queda en el estado",
              isinstance(est9.get("flags_nacidas"), list)
              and "--expert-used-count" in est9["flags_nacidas"])
        check("P18 dumps de --help escritos",
              os.path.exists(os.path.join(base, "campana-n4-n5-p9",
                                          "help-b11901.txt")))

        # ---------- P10: duelo + receta final (AUTO auto-acepta) ----------
        m.AUTO["on"] = True
        m.AUTO["aceptadas"] = []
        a10 = args_falsos(m, base, puerto_libre())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc10 = m.paso10(a10, rutas, m.leer_estado(rutas["estado"]))
        est10 = m.leer_estado(rutas["estado"])["pasos"]["10"]
        check("P19 p10 corre (rc 0)", rc10 == 0)
        check("P20 duelo con ganador y CERRADO",
              est10["estado"] == "CERRADO" and est10.get("ganador"))
        d = m.leer_estado(rutas["estado"])["duelo"]
        check("P21 duelo registro con brazos A y B",
              {f["nombre"] for f in d["brazos"]} >= {"A-NP2", "B-SPEC"})
        check("P22 DUELO.md escrito",
              os.path.exists(os.path.join(base, "campana-n4-n5-p10", "DUELO.md")))
        backups = [x for x in os.listdir(base)
                   if x.startswith("config.txt.bak-antes-receta-final")]
        check("P23 receta final con backup", len(backups) == 1)
        cfg_post = m.leer_config(rutas["config"])
        check("P24 config re-leible y SAMPLING intacto (T8)",
              cfg_post.get("SAMPLING") == "--temp 1.0 --top-k 20")
        check("P25 informe con CIERRE DE CAMPAÑA",
              "CIERRE DE CAMPAÑA" in open(rutas["informe"],
                                          encoding="utf-8").read())
        m.AUTO["on"] = False

        # ---------- estado / plan / main ----------
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.mostrar_estado(rutas, m.leer_estado(rutas["estado"]))
        out = buf.getvalue()
        check("M01 estado muestra la puerta y los 4 pasos",
              "CAMPANA-N4-N5" in out and "P7" in out and "P10" in out)

        # ---------- AUTO end-to-end con todo verde: retoma y salta ----------
        m.AUTO["on"] = True
        m.AUTO["aceptadas"] = []
        a_auto = args_falsos(m, base, puerto_libre())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_auto = m.modo_auto(a_auto, rutas, m.leer_estado(rutas["estado"]))
        check("M02 AUTO con todo verde -> FIN DE TURNO (rc 0)", rc_auto == 0)
        est_final = m.leer_estado(rutas["estado"])
        verdes = [n for n in ("7", "8", "9", "10")
                  if est_final["pasos"].get(n, {}).get("estado") in m.VERDES]
        check("M03 los 4 pasos quedaron verdes", len(verdes) == 4)
        m.AUTO["on"] = False

        # ---------- AUTO con primera olla abierta -> detenido limpio ----------
        base2 = os.path.join(tmp, "rig2")
        os.makedirs(base2)
        shutil.copy(os.path.join(base, "config.txt"), base2)
        with open(os.path.join(base2, "models2.gguf"), "wb") as f:
            f.write(b"x")  # no: RUTA_MODELO apunta fuera; el prevuelo FATALea
        rutas2 = m._rutas(args_falsos(m, base2, puerto_libre()))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_det = m.modo_auto(args_falsos(m, base2, puerto_libre()),
                                 rutas2, m.leer_estado(rutas2["estado"]))
        check("M04 AUTO sin primera olla -> detenido limpio (rc 2)",
              rc_det == 2)
        check("M05 detencion queda en el informe",
              "DETENIDO" in open(rutas2["informe"], encoding="utf-8").read())

        # ---------- veredicto ----------
        n_ok = sum(1 for _, ok in CHECKS if ok)
        print("\n%d/%d checks" % (n_ok, len(CHECKS)))
        return 0 if n_ok == len(CHECKS) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
