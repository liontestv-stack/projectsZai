# BOCETO — PSEUDOCÓDIGO DE LA RONDA COMPLETA + EXPERIMENTOS DENSIFICADOS (ronda 62, 2026-10-31)

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
> **Convención del pseudocódigo:** `FUN` = función/paso; `PUERTA ROJA` = frena el turno
> con causa escrita (nunca se salta sola); `MED3` = mediana de 3 corridas; `→` = escribe
> en estado/informe/CSV; los comentarios `#` son las reglas de la casa que evitan bugs.

---

## 0. CONSTANTES DE LA CASA (leídas del código, no de memoria)

```
PUERTO_DEF           = 9932     # hornilla propia de la segunda olla (la 1ª usa 9931)
CORRIDAS_DEF         = 3        # mediana de 3 ANTES de proclamar (regla)
M_PROMPTS_DEF        = 8        # prompts de medida por corrida (fijos y deterministas)
MAX_TOKENS           = 220      # mismo corte que el sanity de la casa
TIMEOUT_PROMPT       = 180      # por prompt
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

FUN DETENER_LIMPIO(causa):  todo_lo_hecho→informe (append-only) + causa + rc=2

REGLA DE ORO DE LA OLLA: lo ya medido se SUMA al CSV; "edita la tabla y vuelve a
correr pN" es el flujo oficial; ANCLA SIEMPRE primero y no se edita.
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
        chequeo anclas: 17×23=391 · color "verde" · "Valparaíso" · TODO con carne
  4) VEREDICTO N2:
        sanity FALLA                → FALLA (rc=2)
        mejor delta >= +8 pp y OK   → GO   ("%s transfiere +x pp con sanity OK")
        si no                       → REGISTRADO (se registra y se decide con datos [N2 s5])
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
        cae_cliff = (sin datos) O (server muerto) O (m < ANCLA × 0.70)
        SI cae_cliff: CLIFF en peldaño → stop  (jamás se compra el traje que rasga [F cliff×10: 12.70→1.28])
        SI NO: frontera = peldaño; avisar si VRAM > 3712 MB
  3) VEREDICTO: sin peldaños → REGISTRADO (solo ancla) · con cliff → GO si hay frontera · sin cliff → GO
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

AVULSOS (manual, fuera de la olla, cualquier sesión):
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
  VEREDICTO: receta viva + reuse muerto → MOTIVO-CERRADO | receta viva → GO | sin datos → DUDOSO
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

  1) PARA cada brazo ACTIVO: MED3 × 8 prompts = mediana de medianas + SPOT ES (5 prompts:
       anclas 391/verde/Valparaíso + tool + trampa "no lo sé") → fila (mediana, spot, errores, muertos)
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
