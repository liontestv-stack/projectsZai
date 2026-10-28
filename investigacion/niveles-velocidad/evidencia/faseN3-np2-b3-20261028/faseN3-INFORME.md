# INFORME FASE N3 — NIVEL 3: eficiencia simple (cosecha)

Generado: 2026-10-28 17:24:53 · barrido-n3-eficiencia v1.3 (2026-10-28, hotfix de campo 2: colocacion por config + certificado de receta + ancla-muerta=FATAL; 11 configs murieron sin -cmoe en la 1a corrida completa) · proto faseN3-v1

## 0. PREVUELO COMPLETO — PC, modelo y nivel (lo que hay que saber antes de leer resultados)

### 0.1 El PC (hardware y estado del dia)

- SO: Microsoft Windows 11 Home Single Language · 64 bits · build 26200 (version 10.0.26200)
- CPU: Intel(R) Core(TM) i3-10100F CPU @ 3.60GHz (4 nucleos / 8 hilos, 3600 MHz max)
- RAM hardware: 2 modulos, 16.0 GB en total a 2666 MT/s (dual channel si son 2)
- RAM ahora: libre 13388 MiB de 16317 MiB (18% en uso)
- Los 4 comepanes de RAM (procesos que mas comen): explorer 138 MB, MsMpEng 117 MB, powershell 77 MB, Secure System 62 MB
- Pagefile: C:\pagefile.sys reservado 3840 MB · en uso 1039 MB · pico 3389 MB
- Discos: C: libre 15/223 GB | D: libre 200/931 GB
- GPU: NVIDIA GeForce GTX 1650 · driver 610.88 · 4096 MiB · 37 C
- Plan de energia: Máximo rendimiento (el correcto es 'Maximo rendimiento'; el 'Equilibrado' frenaba — R24)

### 0.2 El modelo (identidad certificada)

- Archivo: `D:\ZLia\models\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf`
- Bytes: 14273277376 (esperados 14273277376)
- SHA256: `e4eae0e289b36039faa26f955ca021025754e0c56130a16746749bb1491118d4` (certifica EL archivo exacto; la cadena de descarga se cierra aqui)
- Metadatos GGUF (fabrica):
  - `general.architecture` = qwen35moe
  - `general.file_type` = 12
  - `general.name` = Qwen3.6 35B A3B Uncensored Heretic Native MTP Preserved
  - `general.size_label` = 35B-A3B
  - `gguf_version` = 3
  - `qwen35moe.attention.head_count` = 16
  - `qwen35moe.attention.head_count_kv` = 2
  - `qwen35moe.attention.key_length` = 256
  - `qwen35moe.block_count` = 41
  - `qwen35moe.context_length` = 262144
  - `qwen35moe.embedding_length` = 2048
  - `qwen35moe.expert_count` = 256
  - `qwen35moe.expert_feed_forward_length` = 512
  - `qwen35moe.expert_used_count` = 8
  - `qwen35moe.nextn_predict_layers` = 1
  - `tokenizer.ggml.model` = gpt2
  - OJO: expert_used_count de FABRICA (el barrido mide k=8 de fabrica; CHARLA usa override a 4 en el arranque diario, no aqui)
- Server: `D:\llama.cpp\llama-server.exe` · version: version: 0.7.0-dev (build 11856, commit 3642238cc) built with Clang 20.1.8 for Windows x86_64 · build esperado 11856: OK

### 0.3 La receta viva y la auditoria de flags

- Auditoria de flags: VERDE - todos los tokens verbatim en el dump b11856
- Comando base por config (LA RECETA DIARIA + -lv 4): `-m D:\ZLia\models\Qwen3.6-35B-A3B-uncensored-heretic-Native-MTP-Preserved-APEX-I-MINI.gguf -ngl 99 -c 16384 -ub 1024 -b 4096 -fa on -ctk q8_0 -ctv q8_0 -t 4 --prio 2 --no-mmproj -lm none -lv 4 --host 127.0.0.1 --port 9931` (+ diff de la config; el ultimo valor gana)

### 0.4 El nivel N3 — donde estamos y que cosecha esta corrida

- **Campana:** Orden aprobado (ronda 12): N1 -> N3 -> N2 -> N4 -> RUTA 0 + N5. Estado hoy: N1 medido (k=8 techo 21.53 / k=4 +41% = 28.85-29.13 / k=3 falla aritmetica / k=2 colapso; falta barrido formal v1.2.1 + sanity 20 prompts) - N3 EN CURSO (esta corrida) - N2, N4 y RUTA 0 + N5 pendientes.
- Referencias del laboratorio [M] (el ancla de HOY manda sobre todas):
  - ORO-UB1K (receta diaria, ancla del barrido-30 id 32): **21.53 t/s [M]**
  - NCM37C4 (colocacion campeona, id 14, SIN UB1K encima): **22.49 t/s [M]**
  - ORO-CRAM512 (decode intacto, -7.7 GB RAM): **21.57 t/s [M]**
  - ORO-SHIFT (shift + reuse 256, sin coste): **21.39 t/s [M]**
  - k=4 CHARLA (D-EXP4 / D-EXP4-UB1K, +41%): **28.85 / 29.13 t/s [M]**
  - Suelo k=8 con la MISMA receta otro dia: **17.36 / 17.80 [M]**
  - Techo de la familia flags k=8 (sweep LMNONE): **21.50 [M]**
  - Ruido declarado / dispersion entre corridas: **+/-0.3-0.5 t/s · 9.4 pp (thc1006 v4)**
- Libro de muertos (NO se re-mide): ngram spec: acceptance 0.00-0.16 [M] - muerto; afinidad CPU-GPU (-ot): -9..-38% [M] - muerto; FIT-C (cuant cache f16->q): -38% [M] - muerto; repack off: -5% [M] - muerto; KV q5_1: 0% de cambio [M] - muerto; POLL: ruido · TB8: muerto.
- Lo que esta corrida cosecha (pendientes del nivel):
  - Stack UB1K x NCM37C4 (SS13-1): PRIMER dato = id 8 de esta corrida (el 22.49 historico fue SIN UB1K)
  - Combo ganadores juntos (SS8.1/SS11.7): ids 9 (COMBO-R, seguro), 10 (COMBO-T, expectativa 22.5-23.5 [T]) y 11 (NP2-C, slots)
  - Cache del hibrido con certificados (SS3.3/SS13): ids 5/6 con lineas de log + repro TTFT de 6 turnos; NOCACHE (id 12) es el control que DEBE crecer
- Protocolo de decision:
  - Bookend (id 13): |fin-inicio| > 5% = la sesion derivo -> leer los deltas con cuidado (leccion v1.2.1)
  - Mediana de 3 antes de proclamar ganancias (thc1006 v4); deltas <5pp no se persiguen
  - Un knob sin certificado = no-op sospechoso (barrido-30)
  - PROMOCION: candidatas -> UNA linea de FLAGS_BASE en config.txt (la aprueba el Director, config central ronda 20)
  - Cache NO-SOPORTADO/ROTO en b11856 = MOTIVO DE RUTA 0 (build nuevo), no un fracaso
  - El sanity manual de 20 prompts sigue siendo el juez de calidad
- Las 3 configs de hoy: 1 N3-ANCLA (ANCLA), 7 N3-NP2 (SLOTS), 13 N3-ANCLA-FIN (ANCLA-FIN)

### 0.5 El dia (recordatorio de la ronda 28)

- Ronda 28: el diagnostico midio 17.29 t/s (dia lento dentro del lab) con RAM al 97% (0.40 GB libres) = CULPABLE del dia confirmado. Antes de medir: cerrar apps; si no, el barrido mide el pagefile, no la receta.

## 1. Resultados

Ancla de sesion (N3-ANCLA = receta diaria): 17.32 t/s (referencia barrido-30 ORO-UB1K: 21.53; la de HOY manda)

| id | config | flags diff | decode t/s | vs ancla | prefill | cache | TTFT (t2->tfin) | RAM proc MiB | agg tok/s | VRAM MiB | sanity | valido |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | N3-ANCLA | `-cmoe` | 17.32 | +0.0% | 16 | NO-APLICA | 4.26 -> 5.06 s (PLANO) | 12259.9 | 17.57 | 2353/4096 | 3/3 | SI |
| 7 | N3-NP2 | `-np 2 -cmoe` | 21.37 | +23.4% | 20 | NO-APLICA | - | 13176.2 | 20.73 | 2211/4096 | 3/3 | SI |
| 13 | N3-ANCLA-FIN | `-cmoe` | 17.60 | +1.6% | 16 | NO-APLICA | - | 13241.2 | 17.76 | 2353/4096 | 3/3 | SI |

Referencias historicas del barrido-30 [M]: ORO-UB1K (ancla de la receta diaria) = 21.53 t/s - NCM37C4 (sin UB1K) = 22.49 - ORO-CRAM512 = 21.57 (decode intacto, -7.7 GB) - ORO-SHIFT (shift+reuse) = 21.39. Ruido declarado +/-0.3-0.5 t/s; el mismo config abarca 9.4pp entre corridas (thc1006 v4): mediana de 3 antes de proclamar ganancias.

## 2. Certificados de cache (lineas de log + repro)

| id | config | warning #24055 | restored | forcing #21831 | estado |
|---|---|---|---|---|---|
| 1 | N3-ANCLA | - | 0 | 5 | NO-APLICA |
| 7 | N3-NP2 | - | 0 | 1 | NO-APLICA |
| 13 | N3-ANCLA-FIN | - | 0 | 0 | NO-APLICA |

Lectura: NO-APLICA = la config no lleva --cache-reuse · NO-SOPORTADO = el build declino la cache en el arranque (#24055) · SANO = checkpoints restaurados y cero re-procesado · ROTO = 'forcing full prompt re-processing' (#21831, el hibrido re-paga el prompt) · MIXTO/SIN-DATOS = leer el JSON.

## 3. Protocolo de decision N3 (evaluacion automatica)

- BOOKEND ESTABLE: ancla fin 17.60 vs inicio 17.32 (+1.6%, dentro del +/-5%): los deltas de la sesion se leen limpios.
- N3-NP2: decode por slot 21.37 vs ancla (GANA +4.05); el +14% [M SS4] solo aparece con 2 sesiones a la vez.; probe agregado 20.7 vs ancla 17.6 tok/s (+18.0%) -> concurrencia certificada.

## 4. Recuerdos de la casa aplicados

- Protocolo SS8 verbatim: 4 pasadas x 256 tokens, se descarta la 1a, temp 0, prompts distintos, seed fija; ruido declarado +/-0.3-0.5 t/s.
- Estudio thc1006 v4 (SS13): el mismo config abarca 9.4 pp entre corridas -> las celdas que GANEN aqui se confirman con mediana de 3 corridas (o --quick en otro bloque horario) ANTES de proclamar la ganancia; nunca comparar contra el ancla de OTRA sesion.
- El libro de muertos del N3 NO se re-mide: ngram spec (acceptance 0.00-0.16), afinidad (-9..-38%), FIT-C (-38%), repack off (-5%), KV q5_1 (0%), POLL/TB8 (ruido/muerto).
- Sanity manual de 20 prompts del Director: sigue siendo la puerta de calidad completa (la auto de 3 pares solo es humo-detector).
- PROMOCION: las candidatas a config.txt que salgan aqui se promueven editando UNA linea de FLAGS_BASE (pago del config central, ronda 20); la aprobacion formal es del Director.
- Si la cache sale NO-SOPORTADO o ROTO en b11856: queda registrado como MOTIVO DE RUTA 0 (build nuevo con cpent / fix del checkpoint), no como fracaso de la idea.

## 5. Archivos de esta corrida

- CSV: `faseN3-resultados.csv` (reanudable)
- Datos: `faseN3-datos.json` (repro TTFT turno a turno, sanity, probe agregado, RAM)
- Consola: `faseN3-consola.log`
- Logs del server: `logs-config/NN-nombre.log`

