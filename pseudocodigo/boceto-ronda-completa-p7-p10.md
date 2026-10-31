# BOCETO — PSEUDOCÓDIGO DE LA RONDA COMPLETA + EXPERIMENTOS DENSIFICADOS (ronda 62, auditado en r63 y RE-AUDITADO en r64, 2026-10-31)

> **Qué es este archivo:** el boceto que pidió el Director ("en una nueva carpeta realiza
> pseudocodigo... tratara sobre toda la ronda y los experimentos densificados, en un solo
> archivo estará todo, dejando un log final que te proporcionaré, este pseudocodigo
> disminuirá futuros bugs, será casi un boceto"). UN solo archivo, carpeta nueva
> (`pseudocodigo/`), con TODA la ronda de la segunda olla (P7 → P10) y TODOS los
> experimentos posibles densificados (§6). Es un plano para leer antes de tocar nada:
> si el código real y este boceto se pelean, **manda el byte-intacto** — este boceto no
> se ejecuta, se consulta.
> **Fuentes citadas (nada inventado):** `InformacionCritica/scripts/CAMPANA-6A10.py`
> v1.0 (SHA256 crudo certutil `CFEADBEA...D1947`, byte-intacta), `plan-p8-n4-experimentos.md`
> (APÉNDICE R61), `plan-siguientes-10-pasos.md` (PASOS 7-10 + R60/R61),
> `InformacionCritica/configs/config.txt` (receta real leída esta ronda),
> `para-el-log-final.md`. Ollas hermanas re-verificadas: CAMPANA.py `65D33CBA...DA4B1`,
> CAMPANA-v2.py `52996E67...B1E86`.
> **Auditoría r63:** todas las ramas de veredicto, puertas, rc y cirugía del boceto fueron
> contrastadas función por función contra el código fuente (hallazgos F1-F12 en §9 BITÁCORA;
> trampas nuevas T11-T14). El boceto describe la CONDUCTA real, incluido un cosmético de la
> olla anotado (P9 dice "1 corrida" y corre MED3) — la olla sigue byte-intacta.
> **Re-auditoría r64:** segunda pasada por lo que quedó sin contrastar — hornilla fina
> (_arranca_server/_chat_uno/_auto_apaga/_cuenta_en_log), utilidades (mediana, health_ok,
> sin_tildes, gb_libres) y docstring de cabecera: hallazgos F13-F24 y trampas T15-T18.
> **Convención del pseudocódigo:** `FUN` = función/paso; `PUERTA ROJA` = frena el turno
> con causa escrita (nunca se salta sola); `MED3` = mediana de MEDIANAS (3 corridas y cada
> corrida = mediana de los t/s de sus prompts, reportados por el server); `→` = escribe
> en estado/informe/CSV; los comentarios `#` son las reglas de la casa que evitan bugs.

---

## 0. CONSTANTES DE LA CASA (leídas del código, no de memoria)

```
PUERTO_DEF           = 9932     # hornilla propia de la segunda olla (la 1ª usa 9931)
CORRIDAS_DEF         = 3        # mediana de 3 ANTES de proclamar (regla); mediana()
                                #   filtra no-numéricos: 2 vivas → promedio, 0 → sin datos
M_PROMPTS_DEF        = 8        # prompts de medida por corrida (fijos y deterministas;
                                #   --m-prompts corta los PRIMEROS N de la lista, no mezcla)
MAX_TOKENS           = 220      # mismo corte que el sanity de la casa
TEMP/TOP_K/TOP_P     = 1.0/20/0.95  # sampling FIJO del medidor [M _chat_uno]: IGUAL para
                                #   todas las dosis → es lo que hace comparables las corridas
TIMEOUT_PROMPT       = 180      # por prompt (1 reintento de 3 s SOLO si red/timeout/5xx)
TIMEOUT_CARGA        = 420      # carga del modelo (7 min)
KEEP_MIN_PP          = 5.0      # no perseguir deltas < 5 pp (regla transversal)
N2_META_PP           = 8.0      # salida del N2: >= +8% t/s [N2 s5]
CLIFF_FRACCION       = 0.70     # t/s < 70% del ancla (o server muerto) = CLIFF
VRAM_CERTIFICADO_MB  = 3712     # certificado: nvidia-smi <= 3.7 GB

VERDES     = GO | REGISTRADO | OK | CERRADO | RATIFICADA | EJECUTADO
           | MOTIVO-CERRADO | DUELO-HECHO
AMARILLOS  = PENDIENTE | DUDOSO | REVISAR | INCOMPLETO
ROJOS      = FALLA | MUERTO | FALLO-CERTIFICADO

RECETA real de HOY (config.txt: FLAGS_BASE + FLAGS_GANADORAS, el último valor gana):
  -ngl 99 -cmoe -c 16384 -fa on -ctk q8_0 -ctv q8_0 -t 4 --prio 2 --no-mmproj
  -lm none -np 2 -ub 1024 -b 4096
VRAM medida con NP2: 2211/4096 MB [M R52] → libre ANCLA ≈ 1885 MB
capa de expertos = 328.2 MB [F] · KV @16k q8_0 ≈ 171 MB [F] · nextn (MTP) = 858 MB [F]
```

---

## 1. EL CICLO DE LA RONDA (main + MODO AUTO)

```
MAPA GRANDE (los 5 niveles, orden aprobado r12: N1 → N3 → N2 → N4 → RUTA 0 + N5):
  1ª olla CAMPANA.py/CAMPANA-v2.py: P1..P6 → N1 y N3 CERRADAS (puerta de entrada)
  2ª olla CAMPANA-6A10.py (ESTE BOCETO): P7=N2 · P8=N4 · P9=RUTA 0 · P10=N5+cierre

ORDEN DE CORRIDA (runbook — una lectura y sabes dónde estás):
  DOOR(1ª olla cerrada) → P7[ancla → candidatas → sanity] → DOOR(p7 verde) →
  P8[vuelta 1 subida NCM → vuelta 2 pila sobre el ganador + bookend ‖ avulsos
  A0/R0/V1 aparte] → DOOR(p8 verde) → P9[6 checks b11901] → DOOR(p9 verde) →
  P10[A/B(/C) → duelo → receta final → cierre] → CAMPAÑA CERRADA

PUERTA DE ENTRADA (EXACTA, _primera_olla [M]): cerrada = (olla1.n3.cerrado == True
  O olla1.pasos["3"] in VERDES_OLLA1) **Y** olla1.pasos["6"] in VERDES_OLLA1 —
  leído del campana-estado.json de la 1ª olla en la MISMA base.

FUN arranque():                                  # herencia del guardián (R51)
    huella_ok, causa = autoverifica_sha_propio() # excluye la línea del SHA del cálculo
    SI NOT huella_ok: PAUSA + rc=3 + PARADA LIMPIA (no se ejecuta NADA)

FUN main(paso):
    SI paso == NINGUNO: return modo_auto()       # doble click = P7..P10 en orden
    SI paso == "estado": foto del estado; SI paso == "plan": foto + guía
    SI paso in {p7,p8,p9,p10}: return paso_N(args, rutas, estado)   # sin pausa extra
    SI paso desconocido: rc=1

FUN modo_auto():
    AUTO.on = True; SI args.fuerza: se IGNORA (las puertas rojas mandan, queda escrito)
    mostrar_estado()
    fatales, avisos = prevuelo():                # muere a los 5 s, no a las 2 h
        FATAL si: 1ª olla abierta · sin config.txt · RUTA_SERVER/RUTA_MODELO no existen
                  · server vivo en el puerto (apagar el charlatán primero)
        aviso si: nvidia-smi no responde (certificados VRAM vacíos) · disco < 4 GB
    PARA n en (7,8,9,10):                        # re-lee estado en CADA vuelta
        SI estado[n] in VERDES: "ya estaba hecho: se salta"; continue
        rc = paso_n(args, rutas, estado); informar_trail()
        SI rc != 0: return DETENER_LIMPIO("P%s rc=%s" ...)   # re-doble-click retoma
    excepciones: SystemExit→causa visible+rc; Ctrl+C→rc=130, lo hecho queda escrito;
                 Exception→traceback+rc=1. NUNCA una ventana sin causa visible.
    estado corrupto: NUNCA se descarta en silencio (herencia r50) → queda
                 .corrupto-<sello> como evidencia y arranca limpio [M leer_estado].

FUN DETENER_LIMPIO(causa):  todo_lo_hecho→informe (append-only) + causa + rc=2

REGLA DE ORO DE LA OLLA: lo ya medido se SUMA al CSV; "edita la tabla y vuelve a
correr pN" es el flujo oficial; ANCLA SIEMPRE primero y no se edita.

MUNDO PROPIO (rutas, _rutas [M]): base = junto al script (o --dir) · estado
campana-6a10-estado.json · informe campana-6a10-INFORME.md (APPEND-ONLY) · config:
base/config.txt, con fallback ../configs/config.txt si en la base no está · lee
campana-estado.json (1ª olla) para la puerta · carpetas campana-6a10-p7/ p8/ p9/ p10/
con resultados.csv — UNA fila POR CORRIDA, 9 columnas (dosis,corrida,viva,mediana_tps,
errores,vram_mb,pageouts,spot_ok,acciones), nunca se pisa: se suma — y logs
server-<ETIQUETA>-c<k>.log · tablas editables: campana-6a10-p7-candidatas.txt ·
campana-6a10-p8-escalera.txt · campana-6a10-p10/brazos.txt

HORNILLA (convivencia) [M _arranca_server/_auto_apaga]: NUNCA levanta ni apaga servers
ajenos — solo los hijos que ella misma arranca (el charlatán diario se respeta) · logs
de server en APPEND (acumulan sesiones, cabecera "===== server de campana-6a10") ·
health poll cada 2 s, tope 7 min; si muere en la carga o no hay health → auto-apaga y
el peldaño queda como DATO (viva=False), no como accidente.

TABLA DE RC (los 5 del guardián): 0 = verde · 2 = puerta roja/FATAL/DUDOSO/FALLA
(fatal() SIEMPRE sale rc=2) · 1 = excepción inesperada o sys.exit("texto") ·
130 = Ctrl+C (lo hecho queda escrito) · 3 = huella manipulada (PARADA LIMPIA).

CLI (argparse, main): estado | plan | p7..p10 | (sin argumento = MODO AUTO) ·
--dir --config --puerto(9932) --corridas(3) --m-prompts(8) · p7/p8: --archivo
--previa · p7: --sin-sanity · p9: --build-dir · --fuerza (queda escrito; en AUTO
NO existe). Uso manual de un paso NO pausa la ventana (solo AUTO/estado pausan).
```

---

## 2. P7 — N2 DOSIS (re-ancla + candidatas + sanity)

```
FUN paso7():
  # PUERTA ROJA de entrada de la olla entera:
  SI NOT primera_olla_cerrada(): FATAL("corre CAMPANA.py 1..6 antes")   # --fuerza lo deja escrito
  cfg = leer_config(); carpeta = campana-6a10-p7/
  tabla = campana-6a10-p7-candidatas.txt
  SI NOT existe(tabla): tabla ← DERIVAR_CANDIDATAS(receta real):   # sin inventar flags
        ANCLA | (receta tal cual)
        K-N1-PIN8  | add:--override-kv,qwen35moe.expert_used_count=8 | activa
        K-N1-7/9   | vecinos de la escalera k | inactiva
        SIN-UB1K   | delpair:-ub;delpair:-b   | inactiva (activar solo si el cuant se porta como NCM)
        CTXCP4     | add:--ctxcp,4            | inactiva (verificar flag en el dump)
        # DOS ramas [M _deriva_candidatas]: receta SIN pin de k (HOY, sin --override-kv)
        #   → PIN desde EXPERTOS_TRABAJO=8 ACTIVA + vecinos 7 y 9 inactivos;
        #   receta CON pin → re-aplica el pin ACTIVA + solo el vecino pin-1 inactivo.
  SI --previa: listar y rc=0 (ni un server arranca)

  1) ANCLA = MED3(receta tal cual)               # "el cuant nuevo es un mundo nuevo"
     SI sin datos → estado DUDOSO + informe + rc=2
  2) PARA cada candidata ACTIVA (una dosis por corrida, NO acumulativas):
        m = MED3(acciones(c)); delta = (m - ANCLA)/ANCLA×100
        veredicto: delta >= +5 pp → GANA | 0..+5 → NEUTRA (no se persigue) | < 0 → PIERDE
        → CSV + estado
  3) SANITY cambio de cuant (tool-calling OBLIGATORIO, 12 prompts; --sin-sanity queda escrito):
        server vivo → se USA, no se toca; si no → arrancar PROPIO y auto-apagar al final
        calentar plancha → 12 prompts → guardar respuestas → RESUMEN.md
        (el RESUMEN.md de una vuelta anterior se ROTA a RESUMEN-<sello>.md, no se borra)
        chequeo anclas: 17×23=391 · color "verde" · "Valparaíso" · TODO con carne
  4) VEREDICTO N2:
        sanity FALLA                → FALLA (rc=2)
        mejor delta >= +8 pp y OK   → GO   ("%s transfiere +x pp con sanity OK")
        si no                       → REGISTRADO (se registra y se decide con datos [N2 s5])
        # ⚠ T11 [M código]: con --sin-sanity el GO es IMPOSIBLE (la rama GO exige
        #   sanity_ok en True; None corta) → techo REGISTRADO. P8 abre igual (REGISTRADO
        #   es verde), pero el N2 no cierra como GO sin su juez de calidad.
  → estado["7"], informe, rc = 0 si GO/REGISTRADO; 2 si no
```

---

## 3. P8 — N4 ESCALERA DE VRAM (la despensa)

```
FUN paso8():
  # PUERTA ROJA: p8 exige p7 verde (GO o REGISTRADO). --fuerza lo deja escrito.
  # El lado RAM de dosis fina del N4 (CTXCP4) vive en P7: saltarla con --fuerza
  # deja ese lado SIN medir (queda registrado como pendiente de P7).
  cfg = leer_config(); carpeta = campana-6a10-p8/
  tabla = campana-6a10-p8-escalera.txt
  SI NOT existe(tabla): tabla ← DERIVAR_ESCALERA(receta)   # NGL descendente + MEC + PÁGINA
        # ⚠ TRAMPA R61 (a): la derivación deja NGL-87/93 ACTIVAS ANTES de la subida NCM.
        #   Bajar -ngl manda atención+GDN a CPU (castigo mayor que mover expertos) y un
        #   cliff temprano DETENDRÍA la escalera sin subirla. Tabla correcta: NCM PRIMERO,
        #   NGL INACTIVAS (van al final y aparte).
        # ⚠ TRAMPA R61 (b): el placeholder "--cmoe-cache" NO existe en el dump; la flag
        #   real es --moe-cache-mib [dump línea 128]. En la tabla editable va el nombre real.
        # ⚠ TRAMPA R61 (c): los peldaños NO son acumulativos; las pilas del ganador se
        #   escriben combinadas con ';' (NCM+MEC, NCM+CHARLA4...).
  SI --previa: listar y rc=0

  1) ANCLA = MED3(receta tal cual)                # también es el ancla de sesión: la GPU fría miente ~−15%
     SI sin datos → DUDOSO + rc=2
  2) PARA cada peldaño ACTIVO EN ORDEN DE ARCHIVO:
        SI ya hubo cliff: break                   # REGLA CLIFF-1: la escalera SE DETIENE
                                                  # y la frontera queda UN peldaño antes
        m = MED3(acciones); por cada corrida capturar:
            t/s del medidor · VRAM usada (nvidia-smi) · contador "pageout" del log · errores
        cae_cliff = (sin datos) O (≥1 corrida muerta, muertos>0) O (m < ANCLA × 0.70)
        # [M] basta UNA corrida muerta de las 3 para declarar el cliff; la mediana se
        #   calcula con las vivas (2 → promedio de ambas), pero muertos>0 manda
        SI cae_cliff: CLIFF en peldaño → stop  (jamás se compra el traje que rasga [F cliff×10: 12.70→1.28])
        SI NO: frontera = peldaño; avisar si VRAM > 3712 MB
        # VRAM = certificado BLANDO [M _vram_usada_mb]: nvidia-smi ausente → None →
        #   solo aviso, NUNCA frena. Lo que SÍ frena es el cliff (t/s < 70% o muerto).
  3) VEREDICTO [M código — TRES ramas exactas]:
       sin peldaños activos          → REGISTRADO (solo ancla)
       con cliff Y hay frontera      → GO (frontera = un peldaño antes del rasgón)
       con cliff Y SIN frontera      → DUDOSO, rc=2 (el PRIMER peldaño activo fue el que rasgó)
       sin cliff (escalera completa) → GO
  → estado["8"] (peldaños, cliff, frontera), informe por peldaño, CSV, rc

PREFLIGHT de higiene ANTES de subir (manual, cada sesión, ~10 min — plan R61 §1):
  H1 apps cerradas/RAM libre · H2 Sysmem Fallback OFF · H3 Alto rendimiento + pagefile SSD
  H4 mmproj/imatrix fuera del disco de trabajo · H5 toda flag existe en el dump vigente
  H6 sin MTP/spec en P8 (exige -np 1 → rompería NP2; se PLANEA aquí, se CORRE en P10)

VUELTA 1 — subida pura NCM (buscar la frontera; tabla lista en plan R61 §5):
  ANCLA · NCM38(+656 MiB) · NCM37(+985) · NCM36(+1313) · NCM35(+1641, zona cliff) ·
  NCM34(+1969, CLIFF esperado >4096) · NGL-87/93 INACTIVAS · BLIND-OT37 inactivo
  A0 (avulso, 30 s, PRIMER peldaño real): correr NCM38 y autenticar semántica:
      buffer del log "CUDA0 model buffer size" debe crecer ~+656 MiB; si no crece,
      la semántica es la inversa → vía -ot blindada y se anota
VUELTA 2 — la pila sobre el GANADOR (sustituir NCM37 por el ganador real) + bookend:
  ANCLA · WIN · WIN+MEC512 (activa) · WIN+MEC768 (inactiva; escalar de a 256 MiB) ·
  WIN+DIO (solo si R0 detecta pageouts) · WIN+UBCHICO (intercambio, nunca promoción) ·
  WIN+KVF16 (diagnóstico; un solo sub:q8_0>f16 pisa AMBOS -ctk y -ctv) ·
  WIN+CHARLA4 (activa; ratificación dual k=4) → al cerrar, BOOKEND: re-corrida del ANCLA ≈ ancla

AVULSOS + BOOKEND (MANUAL, FUERA de la olla — el código NO los ejecuta; cualquier sesión).
  Dentro de la olla, en cambio, SÍ es automático: CADA corrida descarta un calentamiento
  ("Calienta la plancha") antes de medir — la GPU fría miente [M _corrida]. Lo manual:
  R0 (10 min): Get-Counter '\Memory\Page Reads/sec','\Memory\Pages Input/sec' durante decode
               ≈0 → frente RAM CERRADO con certificado; >0 sostenido → WIN+DIO
  V1 (1-10 min): Vulkan con el binario del release; arch GDN no carga → NO-GO automático;
               si carga: UNA mediana de 3 en el ganador, todo lo demás idéntico

ARITMÉTICA del presupuesto [M-arit, base 2211/4096 R52; la escalera decide por peldaño]:
  NCM38 2867 · NCM37 3196 · NCM36 3524 (bajo certificado 3712) · NCM35 3852 (cliff zone) ·
  NCM34 4180 = CLIFF · NCM37+MEC512 = 3708 (al borde exacto) · NCM36+MEC512 = 4036 (sobre)

CRITERIOS DE P8: promoción de dosis >= +5 pp sostenido (MED3; no perseguir < 5 pp);
  con < +5 pp la receta diaria NO se toca y P8 cierra con frontera = ANCLA (resultado válido).
SALIDA DEL PASO 8 (intacta): frontera VRAM estable sin cliff + dual ratificado (D1) +
  hueco real del draft registrado como dato + pageouts certificados (R0). La VRAM queda CERRADA.
HUECO para P10: hueco = 4096 − VRAM(ganador)  → si frontera NCM37: ~901 MB (nextn 858 cabe sin margen)
                                              → si NCM36: ~572 MB (no cabe → -cmoed o bajar una capa)
```

---

## 4. P9 — RUTA 0 (build b11901, el mundo nuevo)

```
FUN paso9():
  # PUERTA ROJA: p9 exige p8 verde. --fuerza lo deja escrito.
  servidor_viejo = cfg.RUTA_SERVER (b11856, debe existir)
  build_dir = --build-dir O junto-al-viejo/b11901
  SI NOT existe(build_dir/llama-server.exe):
      estado PENDIENTE + FATAL con receta: EL DIRECTOR descarga cuando el rig NO mide:
        llama-b11901-bin-win-cuda-12.4-x64.zip + zip de cudart DLLs del MISMO release
        (sin cudart la GPU duerme); descomprimir LOS DOS en esa carpeta y volver a correr

  1) --version del binario nuevo DEBE contener "b11901"; si no → FALLO-CERTIFICADO (rc=2)
  2) cudart*.dll presentes en build_dir; si no → PENDIENTE + FATAL (motivo certificado N3 s16)
  3) RE-AUDITORÍA de defaults: --help b11856 vs b11901 → help-viejo/nuevo.txt + diff
       flags que MUEREN (aliases) → AVISO: traducirlas en config.txt ANTES de seguir midiendo (PR #28334)
       flags que NACEN → dato
  4) override de expertos: familia expert_used_count sigue en --help nuevo?
       si NO aparece → AVISO: revisar el nombre nuevo de la clave antes de fiarse del pin
  5) SONDEO cache-reuse (#24055: MUERTO en b11856 en ambas colocaciones):
       server nuevo + add:--cache-reuse,256 → 2 prompts con el MISMO prefijo →
       contar "restored context checkpoint" en el log
       VIVO → la familia ORO-SHIFT vuelve a la mesa · MUERTO → motivo cerrado con certificado
  6) RE-ANCLA del mundo nuevo: MED3 con la receta vigente (build nuevo = mundo nuevo)
       # (cosmético cazado r63: el print de la olla dice "1 corrida" pero _lanza_corridas
       #  corre --corridas=3; el boceto describe la CONDUCTA: MED3. Olla byte-intacta.)
  VEREDICTO [M — el sondeo tiene TRES salidas, no dos]:
       receta viva + reuse MUERTO (0 líneas)    → MOTIVO-CERRADO
       receta viva + reuse VIVO                 → GO (la familia ORO-SHIFT vuelve a la mesa)
       receta viva + reuse INDETERMINADO (el server del sondeo no levantó) → GO con reuse "?"
       receta sin datos (re-ancla vacía)        → DUDOSO, rc=2
  → estado["9"], informe, dumps de help, rc
```

---

## 5. P10 — N5 DUELO SPEC vs NP2 + RECETA FINAL + CIERRE

```
FUN paso10():
  # PUERTA ROJA: p10 exige p9 verde. --fuerza lo deja escrito.
  # P10 ya cerrado → no se re-corre salvo pedido explícito (la receta final ya está escrita).
  escribir brazos.txt (tabla fija):
    A-NP2   | (receta tal cual)                  | activa   | NP2 sin spec (+22.8% [N3])
    B-SPEC  | delpair:-np; add:--spec-draft-n-max,2; add:--spec-draft-p-min,0.75
            |                                    | activa   | MTP-n2 sin NP2 (SS11.4: MTP exige -np 1);
            |                                    |          | n-max y p-min SIEMPRE explícitos
    C-KVOFF | B + add:--kv-unified,off           | inactiva | fallback #25345: se activa SOLA si B < 90% de A

  1) PARA cada brazo ACTIVO: MED3 (misma mecánica de TODA la olla [M]: mediana de 3 medianas
       de corrida; cada corrida = mediana de los t/s de los prompts que reporta el server)
       + SPOT ES POR CORRIDA (5 prompts: anclas 391/verde/Valparaíso + tool + trampa "no lo
       sé"; el brazo queda elegible solo con spot limpio en TODAS sus corridas) [M _corrida]
       → fila (mediana, spot, errores, muertos)
  2) FALLBACK: SI B < 0.90 × A → el draft CALLA → C-KVOFF se corre sola (#25345)
  3) VEREDICTO: ganador = max(mediana) entre brazos con spot limpio (OK o sin spot)
       ninguno elegible → DUDOSO + rc=2
       → DUELO.md + estado DUELO-HECHO + informe
  4) CIERRE (confirmación SI del Director; en AUTO se auto-acepta y queda escrita):
       SI A-NP2 gana: ratificar receta vigente (backup igualmente)
       SI NO: cirugía del brazo ganador: del/delpair/sub cambian FLAGS_BASE; add → FLAGS_GANADORAS
       ESCRITURA SEGURA (el ÚNICO sitio de la olla que toca config.txt):
           backup config.txt.bak-antes-receta-final-<sello> → tmp + os.replace →
           RE-LECTURA de verificación; si NO coincide → FATAL + restaurar backup
       SI el Director cancela → DUELO-HECHO "(receta final cancelada)", config intacto, rc=0
       SI la re-lectura NO coincide → FATAL + restaurar backup (no debería pasar NUNCA)
       SAMPLING, RUTA_* y el cuant NUNCA se tocan (RUTA_MODELO manda)
  CIERRE DE CAMPAÑA: tabla de los 5 niveles (N1=primera olla, N2=P7, N3=CERRADO si olla1.n3,
       N4=P8, RUTA 0+N5=P9/P10) → informe "CIERRE DE CAMPAÑA — receta final certificada"
       estado["10"] = CERRADO. CAMPAÑA CERRADA.

ESPECULACIÓN (planeada en P8, corrida AQUÍ — F4 R61): el hueco real de VRAM (dato de P8)
  alimenta el presupuesto del draft: nextn 858 MB; defensas: -ctkd/-ctvd q8_0, ctx del draft
  chico; alarma #26432 (aceptación normal + t/s desplomado = driver, no draft);
  #26038 not-planned → el buffer del draft se mide con el log desde el primer run.
  Duelo nextn-GPU vs nextn-CPU+2capas (-cmoed) dentro del duelo spec vs NP2 (criterio >= +25%).
```

---

## 6. EXPERIMENTOS DENSIFICADOS — TODOS, NADA FUERA (matriz compacta)

```
P7 (N2 dosis, sobre cuant vigente):                    [criterio]
  E01 ANCLA receta tal cual (re-ancla, MED3)           obligatoria, no editable
  E02 K-N1-PIN8  expert_used_count=8                   k transfiere (arquitectura)
  E03 K-N1-7 / K-N1-9  vecinos de la escalera k        opcional (activar a mano)
  E04 SIN-UB1K  delpair:-ub;-b                         solo si el cuant se porta como NCM
  E05 CTXCP4  add:--ctxcp,4                            verificar flag en dump; liberará 1.5-1.8 GB RAM [T]
  E06 SANITY 12 prompts tool-calling                   OBLIGATORIO en cambio de cuant; anclas 391/verde/Valp.
                                                       GO N2 = mejor delta >= +8 pp + sanity OK [N2 s5]

P8 (N4 VRAM — 8 frentes, ~20 peldaños; MED3, cliff-1, cert 3712 MB):   [autenticador]
  F1 escalera -ncmoe ascendente (jamás saltar peldaño):
    E07 A0  semántica NCM38: buffer +656 MiB           delta de buffer en log (30 s, primero)
    E08 A1  NCM38 (+2 capas) est 2867 MB               buffer +656; nvidia-smi
    E09 A2  NCM37 (+3)       est 3196 MB               buffer +985 (semilla 22.49 t/s mundo viejo)
    E10 A3  NCM36 (+4)       est 3524 MB               buffer +1313 (máx conservadora)
    E11 A4  NCM35 (+5)       est 3852 MB               zona cliff: cliff-1 decide
    E12 A5  NCM34 (+6)       est 4180 MB               CLIFF esperado (>4096)
    E13 A6  BLIND-OT37: NCM37 + -ot blk\.(3[7-9])\.ffn_.*_exps\.weight=CUDA0
                                                       control de semántica independiente; comma-list, sin | ni ,
    E14 A7  ctx confound: NCM37 con -c 16384 vs 8192 vs 4096
                                                       SOLO diagnóstico: reducir -c = NO-GO (mata cache-reuse N3)
  F2 MEC (--moe-cache-mib, flag REAL del dump):
    E15 M0  D-MEC-0: ganador SIN MEC vs con MEC        OBLIGATORIO: cache chico = riesgo −48% [F #29887]
    E16 M1  WIN+MEC512   est 3708 MB (borde exacto)    buffer +512
    E17 M2  WIN+MEC768/1024 (inactivas)                escalar de a 256 MiB solo sin cliff
    E18 M3  techo ajeno 7-9 GiB (+36-40%)              dato para el día que el rig suba de VRAM
  F3 RAM/pageouts:
    E19 R0  Get-Counter 10 min: Pages Input/sec ≈ 0    certificado literal del Director; >0 → DIO
    E20 R1  -lm none YA vive en la receta              certificar, no repetir
    E21 R2  WIN+DIO  sub:none>dio                      solo si R0 detecta pageouts
    E22 R3  mmap+mlock                                 PROHIBIDO salvo headroom demostrado (14.27/16 GB)
    E23 R4  -lzm lazy                                  NO se corre: mayor tensor 328 MB < 4 GiB (documentado)
    E24 R5  CTXCP4                                     vive en P7 (E05); si --fuerza, queda pendiente de P7
  F4 VRAM-B especulación: se PLANEA en P8, se CORRE en P10
    E25 hueco real = 4096 − VRAM(ganador) como DATO    NCM37→~901 (nextn 858 cabe sin margen) · NCM36→~572 (no cabe)
  F5 Vulkan:
    E26 V1  shootout 1-10 min, mismo comando           GDN no carga → NO-GO automático; esperada ~0 o negativa
  F6 buffers:
    E27 U1  WIN+UBCHICO (-ub 64 -b 512)                intercambio presupuestario; ORO-UB1K manda en velocidad
  F7 KV f16:
    E28 K1  WIN+KVF16  sub:q8_0>f16 (pisa -ctk y -ctv) SOLO diagnóstico (KVQ = memoria, no velocidad; KVQ51 = 0%)
  F8 ratificación dual:
    E29 D1  WIN+CHARLA4 (--override-kv expert_used_count=4)
                                                       salida del PASO 8 exige modo dual ratificado
  extra (diagnóstico aparte, al final):
    E30 NGL-87 / NGL-93 descendente (inactivas)        suelo del backbone; NUNCA antes de la subida NCM

P9 (RUTA 0 b11901):
  E31 versión honesta del binario ("b11901" en --version)   si no → FALLO-CERTIFICADO
  E32 cudart DLLs presentes                                si no → GPU dormida (N3 s16)
  E33 diff --help b11856 vs b11901 (muertas/nacidas)       alias muertos → traducir en config.txt antes de medir
  E34 familia expert_used_count viva en --help             si no → revisar clave antes de fiarse del pin
  E35 sondeo cache-reuse 256 (#24055)                      VIVO → ORO-SHIFT vuelve a la mesa; MUERTO → certificado
  E36 re-ancla MED3 en el mundo nuevo                      build nuevo = mundo nuevo

P10 (N5 duelo):
  E37 A-NP2  receta tal cual                    NP2 sin spec
  E38 B-SPEC  delpair:-np + spec-draft-n-max 2 + p-min 0.75    MTP exige -np 1; parámetros SIEMPRE explícitos
  E39 C-KVOFF  B + --kv-unified off             se activa SOLA si B < 90% de A (#25345)
  E40 spot ES por brazo (391/verde/Valparaíso/tool/trampa)     ganador exige spot limpio
  E41 receta final con backup + re-lectura      el único toque a config.txt; confirmación del Director
  E42 cierre de campaña: tabla de los 5 niveles               estado CERRADO

PREDECLARADOS (nada nuevo se improvisa):
  overshoot VRAM = cliff ×10 [12.70→1.28] · mlock prohibido sin headroom · reducir -c = NO-GO ·
  Vulkan sin GDN = NO-GO · MEC chico sin control = riesgo −48% · nada de BIOS/Defender/requant ·
  ninguna flag fuera del dump · NP2+CMS1024 sin medir juntas (CMS1024 aparcada) ·
  sanity tool-calling NO obligatorio en P8 (mismo modelo byte a byte).
```

---

## 7. ANTI-BUGS DEL BOCETO (las trampas ya cazadas, para no repetirlas)

```
T1 NGL antes que NCM detendría la escalera → NCM primero, NGL inactivas (R61-a)
T2 --cmoe-cache no existe → --moe-cache-mib (R61-b, dump línea 128)
T3 peldaños NO acumulativos → pilas con ';' (R61-c)
T4 sub:q8_0>f16 pisa AMBOS -ctk y -ctv (la cirugía sustituye TODAS las apariciones)
T5 -ot va en comma-list en UN solo flag (repetirlo está deprecado [F #13154]); patrón sin | ni ,
T6 la GPU fría miente ~−15% → ANCLA en cada arranque + bookend al cerrar
T7 no comparar t/s entre sesiones (regla anti-cruce R40)
T8 config.txt solo se toca en P10 con confirmación + backup + re-lectura
T9 en AUTO, --fuerza NO existe; puerta roja = turno detenido limpio con causa
T10 el MEC y las capas compiten por los mismos ~1885 MB libres; draft con prioridad cuando entre
T11 --sin-sanity en P7 ⇒ techo REGISTRADO (la rama GO exige sanity; P8 abre igual, el N2 no cierra GO)
T12 tabla editable: fila con <3 celdas " | " se IGNORA EN SILENCIO (¡peldaño que creías activo
    y no corre!); ninguna celda puede llevar "|"; activa/inactiva se lee por PREFIJO "activa" [M _leer_tabla]
T13 VRAM (nvidia-smi) = certificado BLANDO: ausente → aviso, nunca frena; el cliff SÍ frena [M]
T14 cirugía exacta [M _acciona]: add → al final (último valor gana) · del → borra TODAS las
    apariciones del token · delpair → flag+valor (si lo que sigue no es flag) · sub:viejo>nuevo
    → sustituye TODAS las apariciones · acción desconocida → se ignora y queda en el informe
T15 el sampling del medidor es FIJO (temp 1.0 / top_k 20 / top_p 0.95 / max_tokens 220):
    jamás cambiarlo entre dosis — es lo que hace comparables las corridas [M _chat_uno]
T16 el reintento (1, con 3 s de espera) es SOLO para red/timeout/5xx; un 4xx NO se repite
    (herencia r50) [M _chat_uno]
T17 mediana() filtra los no-numéricos: 2 corridas vivas → promedio de ambas; 0 vivas → sin
    datos; pero en P8 basta 1 muerta para el cliff (muertos>0 manda) [M mediana + paso8]
T18 la hornilla jamás toca servers ajenos (solo sus hijos) y los logs de server acumulan en
    APPEND — no esperar logs "limpios" por sesión [M _auto_apaga/_arranca_server]
```

---

## 8. LOG FINAL (HUECO RESERVADO — lo proporciona el Director)

> Este hueco queda RESERVADO. Cuando el Director entregue el log final (corridas,
> informes de la olla, salidas de rig), se pega AQUÍ sin reescribir nada de arriba.
> Sugerencia de formato para cuando llegue: fecha/sesión → pasos corridos → medianas
> y deltas → certificados (nvidia-smi, pageouts, buffers) → veredictos → archivo
> del log crudo citado por ruta.

```
(reservado — vacío a la espera del log final del Director)
```

---

## 9. BITÁCORA DEL BOCETO (append-only — cada ronda anuda aquí qué cambió y por qué)

**R62 (2026-10-31) — creación** (pedido del Director: pseudocódigo de toda la ronda + experimentos densificados en UN archivo, con hueco reservado para el log final).

**R63 (2026-10-31) — AUDITORÍA + FORTALEZA** (pedido del Director: "encuentra inconsistencias incoherencias en el pseudocodigo, fortificalo hazlo mas eficiente"). Método: contraste función por función del boceto contra `CAMPANA-6A10.py` (P7-P10, hornilla, rutas, cirugía de flags y bloque final leídos en fuente). HALLAZGOS CORREGIDOS:

| # | Inconsistencia/incoherencia encontrada (antes) | Fortaleza (ahora) | Fuente verificada [M] |
|---|---|---|---|
| F1 | Veredicto P8 INCOMPLETO: "con cliff → GO si hay frontera" sin cubrir cliff-en-el-primer-peldaño | TRES ramas exactas; cliff sin frontera → DUDOSO rc=2 | paso8 (ramas del veredicto) |
| F2 | P7 no documentaba que --sin-sanity hace el GO IMPOSIBLE | T11: techo REGISTRADO (rama GO exige sanity_ok True); P8 abre igual | paso7 (rama del veredicto) |
| F3 | Puerta de entrada genérica ("primera_olla_cerrada()") | Definición EXACTA: (n3.cerrado O P3 verde_olla1) **Y** P6 verde_olla1 | _primera_olla |
| F4 | Faltaban rutas del mundo propio y el detalle del CSV | Bloque MUNDO PROPIO + 9 columnas del CSV, una fila POR CORRIDA | _rutas + _guarda_csv |
| F5 | Faltaba la tabla de rc del guardián | TABLA DE RC: 0/1/2/3/130 con su causa | bloque final + fatal() |
| F6 | Faltaba el mapa CLI completo | Bloque CLI: estado|plan|pN|AUTO + flags por paso + quién pausa | main() |
| F7 | Spot de P10 parecía UNO por brazo | Spot POR CORRIDA; elegible solo con spot limpio en TODAS sus corridas | _corrida(con_spot) |
| F8 | Bookend/avulsos sonaban a automáticos; calentamiento sin citar | Avulsos+bookend = MANUAL fuera de la olla; calentamiento descartado POR CORRIDA = automático | plan §4 vuelta 2 + _corrida |
| F9 | Derivación de candidatas mostraba UNA sola rama | DOS ramas: sin pin → PIN EXPERTOS_TRABAJO+vecinos 7/9; con pin → re-aplica+pin-1 | _deriva_candidatas |
| F10 | Estado corrupto sin cobertura en el ciclo de la ronda | Nunca se descarta en silencio → .corrupto-<sello> como evidencia | leer_estado |
| F11 | (DE LA OLLA, no del boceto) print de P9 dice "1 corrida" pero _lanza_corridas corre --corridas=3 | Anotado en §4 y aquí; el boceto describe la CONDUCTA (MED3); olla BYTE-INTACTA, no se toca | paso9 paso 6 |
| F12 | Faltaba la semántica exacta de la cirugía de flags | T14: add/del/delpair/sub — sub y del pisan TODAS las apariciones; desconocida → informe | _acciona |

EFICIENCIA añadida (misma información, menos lectura para operar): runbook de una lectura (§1), MUNDO PROPIO, TABLA DE RC y CLI como bloques de consulta rápida — preparar una sesión ya no exige re-derivar nada del código. NINGÚN criterio del plan cambió: cliff-1, MED3, ≥ +5 pp, ≥ +8 pp, 3712 MB, fallback 90%, spot limpio — todo INTACTO (el boceto sigue espejando R61).

**R64 (2026-10-31) — SEGUNDA RONDA DE REVISIÓN** (pedido del Director: "segunda ronda de revision del pseudocodigo"). Esta pasada cubrió lo que la r63 NO había contrastado: hornilla fina (_arranca_server/_chat_uno/_auto_apaga/_cuenta_en_log), utilidades (mediana/health_ok/sin_tildes/gb_libres/sha256_archivo) y el docstring de cabecera. HALLAZGOS CORREGIDOS:

| # | Inconsistencia/omisión encontrada (antes) | Fortaleza (ahora) | Fuente verificada [M] |
|---|---|---|---|
| F13 | "Mediana de medianas" aparecía SOLO en P10 | Es la mecánica de TODA la olla: corrida = mediana de los t/s de sus prompts; total = mediana de las 3 medianas (el docstring lo dice palabra por palabra) | _corrida + _lanza_corridas + docstring |
| F14 | Cliff descrito como "server muerto" a secas | Basta ≥1 corrida muerta (muertos>0) de las 3 para declarar cliff; la mediana se calcula con las vivas | paso8 (cae_cliff) |
| F15 | Sondeo reuse de P9 con DOS salidas | TRES: VIVO / MUERTO (0 líneas) / INDETERMINADO (server del sondeo no levantó → GO con reuse "?") | _sondea_reuse + veredicto paso9 |
| F16 | mediana() sin semántica exacta | Filtra no-numéricos; 3 → central; 2 vivas → promedio; 0 → None (sin datos) | mediana() |
| F17 | El sampling del medidor NO estaba en constantes | FIJO: temp 1.0 / top_k 20 / top_p 0.95 / max_tokens 220 — igual para toda dosis (comparabilidad) | _chat_uno |
| F18 | Reintentos sin especificar | 1 reintento de 3 s SOLO red/timeout/5xx; un 4xx NO se repite (herencia r50) | _chat_uno |
| F19 | Logs de server sin política dicha | APPEND: acumulan sesiones con cabecera "===== server de campana-6a10" | _arranca_server |
| F20 | Regla de convivencia de servers sin escribir | La hornilla NUNCA levanta/apaga servers ajenos: solo sus hijos | _auto_apaga + docstring |
| F21 | Arranque del server sin detalle | Health poll cada 2 s, tope 7 min; muere en carga o sin health → auto-apaga + peldaño DATO (viva=False) | _arranca_server |
| F22 | --m-prompts sin semántica | Corta los PRIMEROS N de la lista fija de 8 (no mezcla) | _corrida (PROMPTS_MEDIDA[:N]) |
| F23 | Rotación del RESUMEN.md del sanity sin citar | El RESUMEN viejo se ROTA a RESUMEN-<sello>.md (no se borra: evidencia) | _p7_sanity |
| F24 | Warm-up del sondeo reuse de P9 sin citar | El sondeo también calienta plancha antes de sus 2 prompts | _sondea_reuse |

Trampas nuevas T15-T18 (sampling fijo, reintento solo 5xx, mediana de vivas + muertos>0 manda, hornilla/servers ajenos + logs append). La re-auditoría confirma que el "MED3" del boceto era correcto en espíritu pero incompleto en mecánica (F13) — ahora la convención del encabezado lo define exacto. NINGÚN criterio cambió (cliff-1, ≥ +5 pp, ≥ +8 pp, 3712 MB, fallback 90%: INTACTOS); las tres ollas siguen byte-intactas.

**R65 (2026-10-31) — EL BOCETO SE MATERIALIZA: CAMPANA-6A10-v2.py v1.0** (pedido del Director: "bien, ahora si, crea el archivo python puro real, siguiendo la guia del pseudocodigo"). Este boceto DEJO DE SER SOLO PLANO: su transcripcion ejecutable vive en `InformacionCritica/scripts/CAMPANA-6A10-v2.py` (cuarta olla, hermana de las tres BYTE-INTACTAS; mundo compartido con CAMPANA-6A10.py: mismo estado, informe, carpetas y puerto 9932). Conducta identica a la que este boceto describe (verificada con bateria mock 58/58 + baterias de la casa verdes) salvo TRES deltas documentados en su cabecera: (D1) la derivacion de la escalera P8 ya nace corregida segun §3 y las trampas T1/T2/T3 de este boceto (NCM primero y activo, NGL inactivas al final, --moe-cache-mib nombre real, pilas con ';', sin mlock); (D2) impresiones honestas (P9 anuncia la mediana real — cosmético F11; avisos de derivacion visibles; hueco para P10 anotado en el informe de P8); (D3) linea "- script:" en el informe compartido. La regla de la cabecera sigue mandando: si el codigo y este boceto se pelean, manda el byte-intacto. Huellas de las tres ollas re-verificadas antes y despues. Worklog: Task 65.

**R66 (2026-10-31) — REENCUADRE: LA RUTA SE GOBIERNA POR NIVELES (N4 -> N5); el mapa de pasos queda como bitacora** (palabras del Director: "ibamos en n4, los 10 pasos del 1 al 6 y 7 a 10, eran n3, ya no nos sirve, ahora vamos con n4 y luego n 5"). Este boceto SIGUE VIVO como portador del contenido: su §3 ES el N4 (escalera de VRAM con cliff-1, certificados, auto-ancla MED3 que no depende de P7) y sus §4+§5 SON el N5 (RUTA 0 b11901 + duelo spec vs NP2 + receta final + cierre de los 5 niveles); lo que se retira es el ANDAMIAJE de pasos como mapa gobernante — P7 sale de la ruta critica (solo aplicaba a cambio de cuant, y el cuant ya esta cerrado desde R59). Las etiquetas p8/p9/p10 del Python siguen siendo los comandos del rig: la puerta p7->p8 se cruza UNA vez con --fuerza (queda ESCRITA en el informe, conducta exacta del codigo, linea de la puerta en paso8) y de ahi en adelante el estado sigue solo (p9 tras p8, p10 tras p9). El HUECO §8 para el log final del Director permanece reservado. Huellas de las tres ollas re-verificadas antes y despues. Worklog: Task 66.

**R67 (2026-10-31) — RENOMBRE POR ORDEN DEL DIRECTOR: CAMPANA-6A10-v2.py -> CAMPANA-N4-N5.py** ("si a hora es n4 cambiale el titulo, no mescles cosas"). El portador ejecutable de este boceto (§3 = N4, §4+§5 = N5) cambia de nombre e identidad completa: titulo de cabecera ("campana-n4-n5.py v1.0 — VIA ACTIVA N4 -> N5"), VERSION interna ("campana-n4-n5 v1.0"), banner del `estado`, linea "- script:" del informe, mundo nuevo campana-n4-n5-* (el mundo compartido con CAMPANA-6A10.py muere: esa olla queda byte-intacta con el SUYO, virgen) y variables PASOS_N4N5/TITULOS_N4N5. Huella re-sellada E3E0F08A...0965 -> F6BD479D...3D041 (mecanismo de auto-verificacion intacto, rc=3 probado pasando). Los comandos del rig siguen siendo p8 (N4) y p9/p10 (N5) — mecanismo, no mapa (R66). Bateria renombrada test_campana_n4n5_mock.py 58/58 VERDE; las tres ollas byte-intactas re-verificadas por huella. Worklog: Task 67.
