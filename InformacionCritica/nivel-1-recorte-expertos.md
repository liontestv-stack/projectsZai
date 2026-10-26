# NIVEL 1 — RECORTE DE EXPERTOS EN RUNTIME (fase D EXP)

Proyecto APEX-I-MINI / Qwen3.6-35B-A3B | Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB
Fecha: 2026-10-26 | Investigación profesional profunda | Nivel 1 de 3 ("hacer el modelo más ligero sin complicar")

Etiquetas: **[F]** = verificado en fuente externa (URL abajo) · **[M]** = medido en ESTE rig (sweeps/barridos propios) · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy

---

## 0. Veredicto ejecutivo

El recorte de expertos en runtime —bajar `expert_used_count` de 8 a menos vía `--override-kv`— es la vía de aligerado más potente, reversible y de cero descargas que existe para este modelo. La evidencia profesional en modelos hermanos es fuerte: el paper MoE-Spec mide **~95% de calidad retenida incluso a 2.0× de speedup** en Qwen3-30B-A3B [F], y Cerebras REAP retiene 97.6% de coding con la mitad de expertos podados [F].

**PERO hay un hallazgo crítico propio**: el barrido-30 midió la familia EXP **completamente plana** (EXP10=21.43, EXP8=21.54, EXP6=21.32, EXP5=21.41, EXP4=21.52 vs ancla 21.53 t/s) [M]. La explicación ya identificada: el override usó la clave `qwen3moe.expert_used_count`, pero la arquitectura real del 3.6 es `qwen3_5_moe` → **la dosis nunca se aplicó (no-op)** [F: script barrido-qwen-30.py + model card]. La firma es inequívoca: el control EXP10 (MÁS expertos = MÁS bytes/token = debería frenar) tampoco se movió.

Conclusión: **fase D EXP no está refutada — está sin estrenar**. El barrido-total.py v1.0 ya la corrige (parser GGUF propio que lee el nombre real del arch y construye la clave exacta). Esperanza realista en este rig: **+8–17% t/s a k=6..4, +22–28% a k=3..2** [T], con calidad que la evidencia dice que aguanta hasta k=4 sin caída mayor [F].

---

## 1. Qué toca exactamente la dosis: la máquina de expertos del 3.6

Ficha oficial de Qwen3.6-35B-A3B [F, unsloth model card]:

| Parámetro | Valor |
|---|---|
| Capas | 40 (layout 10 × [3×(Gated DeltaNet → MoE) → 1×(Gated Attention → MoE)]) |
| Expertos por capa MoE | 256 routed + 1 shared |
| Activados por token | **8 routed + 1 shared** |
| Dim intermedia del experto | 512 |
| Hidden | 2048 |
| Vocabulario | 248,320 (padded), lm_head **untied** [F, repo REAP] |
| MTP | "trained with multi-steps" (cabeza nativa en la familia) |
| Arquitectura en llama.cpp | `qwen3_5_moe` (QWEN35MOE, híbrido lineal-attention + MoE fusionado) [F] |

Parámetros por experto: 3 × 2048 × 512 = **3.15 M**. Routed totales: 256 × 40 × 3.15 M ≈ 32.2 B (el 92% del modelo). Routed **activos** por token: 8 × 40 × 3.15 M ≈ **1.01 B**.

Detalle fino que importa para el recorte [F, MoE-Spec §2.1]: **Qwen3 NO renormaliza** los pesos de mezcla sobre el top-k seleccionado. Eso significa que cuando el router usa menos expertos, los pesos de los que quedan NO se re-escalan: la salida de la capa queda levemente "atenuada" (estilo *truncation* del paper), no re-mezclada (estilo *substitution*). A dosis moderadas (k≥4) la diferencia entre ambas políticas es pequeña en el paper; a dosis agresivas substitution gana. En llama.cpp el override-kv hace truncation implícita [T].

### Qué cambia y qué NO cambia al bajar k

- **Cambia**: bytes leídos de RAM por token (banda), que es EL cuello de botella de este rig [T, §2].
- **NO cambia**: RAM ocupada (los 256 expertos siguen cargados), ni VRAM, ni el archivo del modelo, ni el prefill por defecto. Es un recorte "virtual": el modelo íntegro sigue en memoria, solo se lee menos.

---

## 2. Presupuesto de bytes/token en ESTE rig (por qué esto es bandwidth)

Derivación [T] con la ficha del modelo y el ancla medido 21.53 t/s [M, ANCHOR-B]:

| Componente leído por token | Parámetros | Bytes @~3.26 bpw |
|---|---|---|
| Expertos routed activos (8×40×3.15M) | 1.008 B | **0.41 GB** |
| Atención GDN (30 capas) + Attention (10 capas) | ~1.69 B | 0.69 GB |
| LM head untied (248320×2048) | 0.51 B | 0.21 GB |
| Expertos shared (40 capas) | 0.126 B | 0.05 GB |
| Estado recurrente GDN (lectura+escritura, fp32) | — | ~0.12 GB |
| KV cache q8_0 (según contexto 4k–16k) | — | 0.02–0.18 GB |
| **Total ≈** | | **~1.45–1.55 GB/token** |

Banda efectiva implícita: 21.53 t/s × ~1.5 GB ≈ **32 GB/s** [T] — consistente con DDR4-2666 dual-channel (42.6 GB/s teóricos). El rig está clavado en banda de memoria: **todo lo que reduzca bytes/token se convierte casi 1:1 en t/s** [T].

## 3. Evidencia profesional (lo que dice la literatura y la comunidad)

### 3.1 MoE-Spec: Expert Budgeting for Efficient Speculative Decoding (arXiv 2602.16052, Feb-2026) [F]

El paper más directo, en el hermano de 30B con el MISMO patrón de routing (128 exp, top-8, sin renorm):

- **Heavy-tail**: en un árbol de verificación, el top-32 de 64 expertos captura el **93% del peso de routing**; la cola larga son "stragglers" que pagan banda completa y aportan poco.
- **Qwen3-30B-A3B es el modelo MÁS favorable de los 3 evaluados**: mantiene **~95% de calidad a 2.0× de speedup** con barras de error estrechas (Mixtral cae a ~78%, OLMoE es la peor). En GSM8K T=0: 2.4× vs 1.9× de EAGLE-3 a calidad igual.
- **Static ranking** (orden fijo por frecuencia de calibración) rinde comparable al adaptativo en presupuestos B ≥ N/2, y habilita poda permanente; el Oracle dice que un ranking perfecto reduciría requisitos de expertos otro 25%.
- **Truncation vs substitution**: truncation (lo que hace nuestro override) pierde contra substitution solo a presupuestos agresivos; el largo de aceptación media solo baja **−1.4%** con budgets apretados.
- Punto de saturación ~32 expertos cargados por árbol: cargar más allá no paga.

Implicación para nosotros [T]: el 35B-A3B (256 exp, top-8) tiene todavía más cola para recortar que el 30B (128 exp, top-8): bajar a k=4 equivale al presupuesto B=N/2 donde el ranking estático ya bastaba, y el 3.6 es "significantly better" cuantizando y más robusto [F localbench].

### 3.2 No todos los expertos valen igual — familia de papers de poda [F]

- **Not All Experts are Equal** (Lu et al., ACL 2024, arXiv 2402.14800): poda post-training task-agnostic por frecuencia de selección/eliminación; reduce tamaño Y acelera sin perder satisfactoriamente. Código: `Lucky-Lance/Expert_Sparsity`.
- **REAP (Cerebras, arXiv 2510.13999)**: poda one-shot ponderada por contribución de activación (router-weighted), no solo frecuencia. A 50% de poda retiene **97.6% de coding no-agéntico y 96.7% de SWE-Bench agéntico** [F blog Cerebras]; −1.9% accuracy media. Ya existen recortes REAP del propio 3.6-35B en HF (ver §3.4).
- **Advertencia de la cola larga** (arXiv 2604.23036, Apr-2026): quitar GLOBALMENTE expertos raramente activados degrada bastante el rendimiento — esos expertos llevan información única. Nuestro método NO quita expertos del modelo: solo deja de leer, por token, los de menor probabilidad de SU top-8. Es el caso menos dañino posible de recorte [T], y de hecho coincide con lo que el router ya hace con la cola (pesos no renormalizados → los últimos del top-8 pesan poco).

Paisaje adicional [F]: Shapley-MoE (NeurIPS 2025, importancia por valor de Shapley), C-PRUNE (2026, clustering por dominio), DiEP. Todos confirman la misma tesis: hay redundancia funcional entre expertos y sensibilidad por capa.

### 3.3 Evidencia de comunidad en llama.cpp (override real, medido) [F]

- **Discusión #30155 (Oct-2026)**: usuario overridea `expert_used_count` 10→7 en un MoE grande: **35 → 45 t/s (+29%)**, hit-rate de la cache de expertos sube 50%→80%, "no se observó una gran degradación". Compara con modelos REAP que podaron 30% de 512 expertos.
- **Issue #19528 (Feb-2026)**: petición de un flag `--expert-override` / `--moe-topk` dedicado — confirma que el override-kv es la vía actual y que es quisquilloso con la clave exacta.

### 3.4 Recortes YA hechos sobre el 3.6-35B, descargables [F]

| Repo HF | Qué es | Estado para nosotros |
|---|---|---|
| `DJLougen/Qwen3.6-35B-A3B-REAP-90pct-GGUF` | REAP keep-26 (−90% expertos), 6.15B params, 3.4 GB Q4_K_M | **NO-GO**: el propio autor lo llama "MEME", "tokens mostly incoherent" [F] |
| `anik-jha/Qwen3.6-35B-A3B-coding-reap50-GGUF` | REAP-50 coding, imatrix | Experimento opcional con sanity gates (el REAP-50 canónico retiene 97.6% coding [F Cerebras]) |
| `Elsephire/Qwen3.6-35B-A3B-vocabulary-trimming-GGUF` | vocab −41.3%, lenguas latinas preservadas | Descarga segura: +6–7% t/s [T] (ver Nivel 2, §6) |
| `t1pe/MoE384-pruned` Q4_K_M | 17.8 GB | NO cabe en el rig, descartado |

---

## 4. Análisis del no-op medido: qué pasó en el barrido-30 [M+F]

Datos [M, barrido-30-resultados.csv]:

| Config | Override | decode t/s (media 4 pases) |
|---|---|---|
| ANCHOR-B | — | 21.53 |
| EXP10 (control, debería FRENAR) | 10 | 21.43 |
| EXP8 (sanity, = default) | 8 | 21.54 |
| EXP6 | 6 | 21.32 |
| EXP5 | 5 | 21.41 |
| EXP4 (agresivo) | 4 | 21.52 |

Tres lecturas posibles y su veredicto:

1. ~~"La dosis aplicó pero no hay ganancia"~~ → **DESCARTADA por la matemática** [T]: k=10 añade +25% de bytes routed (+0.10 GB/token); a 32 GB/s de banda efectiva debería caer a ~20.1 t/s. No cayó. k=4 quita −0.20 GB/token y debería subir a ~24.9. No subió. Un rig bandwidth-bound no puede ser insensible a ±15% de banda.
2. ~~"El modelo no es bandwidth-bound"~~ → **DESCARTADA**: todo lo demás medido en este rig (ubatch, colocación, cuant) se comporta exactamente como predice el modelo de banda [M].
3. **"El override nunca se aplicó (no-op)"** → **CONFIRMADA por evidencia convergente**: (a) el script usó la clave `qwen3moe.expert_used_count` [F, barrido-qwen-30.py] pero el arch del GGUF es `qwen3_5_moe` [F, model card y repo REAP]; (b) el control EXP10 plano es LA firma de un override ignorado — el propio docstring del script lo anticipó: *"El control EXP10 y la lectura de n_expert_used en el log del server dicen si el override se aplico de verdad (nada se asume)"* [F]; (c) la comunidad reporta que el override-kv es sensible a la clave exacta (#19528) [F].

**Lección operativa**: en los 3 niveles de aligerado, toda dosis debe autenticarse. El barrido-total v1.0 fase D ya lo hace: parsea los metadatos del GGUF con un parser propio, saca el arch real y el valor actual, y construye `--override-kv <arch_real>.expert_used_count=int:N`. Además el log de carga de llama-server imprime los hparams (línea `n_expert_used = N`): **un run de fase D solo es válido si esa línea muestra el valor dosificado** [M: criterio ya cableado].

---

## 5. Dosis, tabla esperada y puerta de calidad

Tabla de rendimiento esperado en este rig [T] (banda efectiva ~32 GB/s, resto de tráfico ~1.05–1.10 GB/token):

| Dosis (k routed) | Ahorro bytes/token | decode esperado | vs ancla | Calidad esperada (evidencia) |
|---|---|---|---|---|
| 10 (control) | −0.10 GB | ~20.1 | −6.5% | >default [T] — solo como autenticador |
| 8 (ancla) | — | 21.5 | = | 100% |
| 6 | −0.10 GB | ~23.3 | **+8%** | Pérdida ≈ despreciable en chat [F análogo] |
| 5 | −0.15 GB | ~24.2 | **+12.5%** | Pequeña [F análogo] |
| 4 | −0.20 GB | ~25.1 | **+17%** | ~95–98% de calidad (B=N/2 donde static ranking bastaba) [F MoE-Spec] |
| 3 | −0.26 GB | ~26.4 | **+22%** | Sacrificio real; math/código se notan primero [T] |
| 2 | −0.31 GB | ~27.5 | **+28%** | Cliff esperado; solo si la calidad es sacrificable (el Director la permite) [T] |

La calidad NO se mide con t/s: la puerta de calidad es doble — (1) fase B del barrido (re-ancla + consistencia de salida), (2) sanity manual de 20 prompts (10 chat ES, 5 código, 5 tool-calling; categoría **tool-calling es la que más sufre en cuants de este modelo** [F localbench], presumiblemente también en recortes [T]).

---

## 6. Protocolo de ejecución (con lo que ya existe)

1. **Correr** `python barrido-total.py` (o `--quick`) → fase D EXP con dosis dinámicas ya cableadas (parser GGUF → arch real → override). El informe MD trae por run: `n_expert_used` leído del log (autenticación), decode/prefill, y flags exactos.
2. **Gate de autenticación**: si `n_expert_used` del log ≠ dosis pedida → run inválido, no computa. (Esto es lo que faltaba en el barrido-30 y ya está.)
3. **Escalera recomendada**: EXP6 → EXP4 → EXP3 (solo si EXP4 pasa sanity) → EXP2 (solo curiosity con calidad sacrificada).
4. **Combinación**: el ganador EXP se apila con ORO-UB1K (launcher actual) sin conflicto de flags (override-kv es ortogonal a -ub/-b) [M].
5. Si el override con la clave correcta TAMPOCO se aplicara (0 casos conocidos en builds recientes), plan B: build nuevo upstream que traiga el flag dedicado `--moe-topk` (#19528) cuando exista [N/D fecha].

---

## 7. Riesgos, límites y mitigaciones

- **Degradación no uniforme** [T]: math/código/tool-calling primero, chat casual al final. Mitigación: sanity gates por categoría; k≥4 como default operativo.
- **Truncation sin renormalización** [F MoE-Spec + T]: a k agresivo la salida se atenúa. No hay substitution en llama.cpp runtime [N/D]. Mitigación práctica: quedarse en k=4–6 donde el paper muestra que la política importa poco.
- **Interacción con MTP (fase E)**: es SINERGIA, no conflicto — MoE-Spec es exactamente "drafting con presupuesto de expertos + verificación completa". Con n-max 2, la verificación carga la unión de expertos de 2 tokens; con k reducido el coste de esa unión baja también [T].
- **La RAM no baja** [T]: si el objetivo fuese también liberar RAM para el draft MTP, eso lo aporta el Nivel 2 (cuant más ligero), no este.
- **Reversibilidad total** [M]: es un flag de línea de comandos; el modelo no se toca.

## 8. Stack con los otros niveles (multiplicativo [T])

| Ruta | decode esperado |
|---|---|
| Ancla (hoy) | 21.5 t/s |
| + UD-IQ3_XXS (Nivel 2) | ~23.2 (+8%) |
| + EXP k=4 autenticado (Nivel 1) | ~27.1 |
| + NCM37C4 o FIT-A (Nivel 3) | ~28.2 |
| + MTP n-max 2 (fase E, ×1.28 [F hermano]) | **~36 t/s** |
| Variante sacrificio: k=2 en vez de k=4 | **~40 t/s** |

El objetivo +50% (32.3–33.6) queda dentro del compuesto EXP+IQ3_XXS+MTP; el ×2 (43–45) exige todo el stack y algo de suerte [T].

## 9. Pendientes / N/D

- KLD exacto de la dosis EXP: no existe métrica KLD para recorte (es inferencia distinta, no cuant). La puerta es sanity + benchmarks de uso.
- Confirmar en T2 si la salida con k<8 muestra renormalización implícita en el build b11856 (leer log/evals) [N/D].
- Flag dedicado `--moe-topk` upstream (#19528): vigilar merge.

## 10. Referencias

- MoE-Spec (arXiv 2602.16052): https://arxiv.org/html/2602.16052v1 · OpenReview: https://openreview.net/pdf/a1cf120339f2acbb45379fcb501da39bb90e6464.pdf
- Not All Experts are Equal (ACL 2024): https://arxiv.org/abs/2402.14800 · https://aclanthology.org/2024.acl-long.334/
- REAP (Cerebras): https://arxiv.org/pdf/2510.13999 · https://github.com/CerebrasResearch/reap · https://www.cerebras.ai/blog/reap
- Cola larga de expertos: https://arxiv.org/html/2604.23036v1
- Shapley-MoE (NeurIPS 2025): https://neurips.cc/virtual/2025/poster/119676 · C-PRUNE: https://proceedings.mlr.press/v317/yao26a.html
- llama.cpp discusión override (k10→7, +29%): https://github.com/ggml-org/llama.cpp/discussions/30155 · issue flag dedicado: https://github.com/ggml-org/llama.cpp/issues/19528
- REAP-90pct GGUF del 3.6 ("meme"): https://huggingface.co/DJLougen/Qwen3.6-35B-A3B-REAP-90pct-GGUF
- Model card Qwen3.6-35B-A3B (arch): https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF
- Datos propios: `barrido-30-resultados.csv`, `barrido-qwen-30.py` (familia EXP y control), `barrido-total.py` fase D [M]

---

## 11. ANEXO — Segunda ronda de investigación (2026-10-26)

### 11.1 La clave exacta del override, confirmada en el código fuente [F]

Del código maestro de llama.cpp (`src/llama-arch.cpp`):

- Línea 219: `{ LLM_KV_EXPERT_USED_COUNT, "%s.expert_used_count" }` — el formato de la clave es `<arch>.expert_used_count`.
- Línea 141: `{ LLM_ARCH_QWEN35MOE, "qwen35moe" }` — el string del arch en el código upstream es **`qwen35moe`**.
- Matiz que importa: el TAG del repo HF de unsloth usa `qwen3_5_moe` y el repo REAP citó ambos ("qwen3_5_moe / QWEN35MOE"). El prefijo correcto es **el `general.architecture` que lleva el GGUF concreto y que imprime el log de carga** — no el tag de HF ni el nombre del enum. El parser de fase D lee ese campo del archivo: por eso es la fuente autoridad.

Regla operativa final: `--override-kv <arch_del_log>.expert_used_count=int:N`. El run solo es válido si el log muestra `n_expert_used = N` tras la carga.

### 11.2 Confirmación de comunidad: el override SÍ funciona cuando la clave es correcta [F]

- Reddit (Qwen3-235B, arch `qwen3moe`): `--override-kv qwen3moe.expert_used_count=int:5` descrito como "el balance entre velocidad y masa", k=4 para más velocidad. Técnica validada en producción por terceros cuando la clave coincide.
- Discusión #30155 (Oct-2026, k 10→7): +29% t/s y, detalle nuevo, el **hit-rate de la cache de expertos** sube de 50% a 80% — relevante si en el futuro se usa moe-cache; con todo en RAM como en este rig es efecto secundario [T].

### 11.3 Refuerzo de la puerta de calidad [F]

- MoE-Spec eligió el presupuesto que "maximiza throughput manteniendo calidad dentro de 1σ de EAGLE" (los valores exactos por modelo van en apéndice, no accesible [N/D]).
- REAP-50 (poda global −50%, MÁS agresiva que nuestro k=4 que no borra nada) retiene 96.7% en SWE-Bench agéntico [F Cerebras]: el margen de seguridad a k=4 es amplio.
- La cola-larga (2604.23036) castiga BORRAR expertos raros; nuestro método no borra — refuerza que k≥4 es territorio seguro y k=2 es el que requiere sanity estricto.

### 11.4 Test de coherencia del rig (validación cruzada) [T]

Si la dosis k=4 se aplica de verdad: bytes/token −0.20 GB sobre ~1.5 → **el t/s DEBE subir ~15–17%** a banda constante. Protocolo de decisión:
1. t/s sube ~15% → dosis viva, escalera k=6→4→3 en marcha.
2. t/s sube <10% con `n_expert_used` correcto → la banda ya no domina (revisar colocación NCM37C4/FIT-A antes de seguir bajando k).
3. `n_expert_used` no cambia o t/s plano → build ignora el override: escalar a build upstream nuevo (flag dedicado `--moe-topk` del issue #19528 cuando se fusione).

### 11.5 Impacto en el roadmap [T]

Con el descubrimiento del repo MTP de unsloth (ver anexo del Nivel 2), la escalera compuesta se simplifica: **UD-IQ3_XXS-MTP (14.07 GB) ya trae la cabeza nextn** → EXP (este nivel) + cuant + MTP caben en UNA sola descarga y UNA sesión de barrido. El objetivo 32–36 t/s pasa por: autenticar EXP k=4 → apilar MTP n-max 2 → rematar con NCM37C4/FIT-A.

---

## 12. ANEXO — Tercera ronda: mecánica interna del override hasta el último detalle (2026-10-26)

### 12.1 Sintaxis y mecánica de `--override-kv`, confirmadas al carácter [F]

Del dump del build b11856 (líneas 162–166) [F]:

- Sintaxis: `--override-kv KEY=TYPE:VALUE,...` — "advanced option to override model metadata by key".
- Tipos soportados: **`int`, `float`, `bool`, `str`** (ejemplo oficial del help: `--override-kv tokenizer.ggml.add_bos_token=bool:false,tokenizer.ggml.add_eos_token=bool:false`).
- Múltiples overrides: separados por comas en un solo flag (el dump corrige el texto antiguo de 2024 que decía "may be specified multiple times" — ambas formas funcionan, la coma es la moderna).
- La dosis correcta para este modelo queda entonces: `--override-kv qwen3_5_moe.expert_used_count=int:4` (con el arch REAL del GGUF, que el parser de fase D lee — ver §11.1).

### 12.2 La firma de autenticación en el log, literal [F]

Datapoint fundacional (discusión #5114, Mixtral 8x7B, en producción desde Ene-2024): `--override-kv llama.expert_used_count=int:3` produce en el log:

```
llm_load_print_meta: n_expert = 8
llm_load_print_meta: n_expert_used = 3
```

→ La línea exacta a grep en cada run de fase D es **`llm_load_print_meta: n_expert_used = N`**. Si muestra la dosis pedida, el override VIVIÓ; cualquier otra cosa = run inválido (criterio ya cableado en barrido-total fase D).

### 12.3 Issue #19528 CERRADO como "not planned": no esperen flag dedicado [F]

Estado verificado (Mar-2026): el issue pidiendo `--expert-override`/`--moe-topk` fue cerrado por inactividad tras la respuesta del mantenedor CISC: *"There already is such an option; `--override-kv <arch>.expert_used_count=int:8`"*, con confirmación de un tercero en `nemotron_h_moe` (`--override-kv nemotron_h_moe.expert_used_count=int:8` "works").

**Consecuencia operativa**: el "plan B" de §6.5 y §9 (esperar un flag dedicado upstream) está **MUERTO — el issue está cerrado como not planned**. `--override-kv` es LA vía oficial, soportada y permanente. Si la clave correcta fallara en el build b11856 (0 casos conocidos), el único plan B real es actualizar build, no esperar flag nuevo.

### 12.4 Claves MoE emparentadas: lista de NO-TOCAR [T]

El GGUF lleva más claves `<arch>.expert_*` que el loader consulta. Solo `expert_used_count` es seguro porque no cambia la FORMA de ningún tensor — solo cuántos del top-k se leen:

| Clave | Valor del 3.6 | Por qué NO tocarla |
|---|---|---|
| `expert_count` | 256 | Cambiarla desincroniza con los tensores ffn_*_exps cargados → crash o corrupción |
| `expert_feed_forward_length` | 512 | Idem: define la dim de los tensores de expertos |
| `expert_shared_count` | 1 | El shared expert tiene tensor PROPIO (`ffn_*_shexp`); poner 0 rompe el grafo |
| `expert_weights_scale` / `expert_weights_norm` | 1.0 / — | Alteran la matemática del router en silencio |
| `expert_gating_func` | silu | Cambiar la activación = otra red |

### 12.5 Per-layer NO es posible; dosis global k es lo que hay [T]

MoE-Spec calcula presupuesto por capa/árbol; el override-kv es **global para todo el modelo** (una clave, un valor). Ningún build conocido acepta `<arch>.block.N.expert_used_count`. El recorte runtime en llama.cpp = truncation global del top-k, punto. Todo refinamiento por capa exige poda offline (REAP y familia, Nivel 2/§7).

### 12.6 Bonus inesperado: bajar k libera VRAM del buffer de cómputo [T]

Los intermedios de la MoE (`ggml_mul_mat_id`) escalan con el número de expertos usados por token: son por `n_tok × k × n_embd`. Bajar k=8→4 reduce ese buffer ~a la mitad → **margen VRAM extra en la GTX 1650** exactamente cuando el Nivel 3 lo necesita (subir `-ncmoe` o ctx). Verificable gratis en el log de cada run: comparar la línea `CUDA0 compute buffer size` del run EXP4 vs ancla.

### 12.7 El draft MTP hereda la dosis; y tiene flags de colocación PROPIOS [F dump]

- El draft MTP se construye del MISMO GGUF (tensores `nextn.*` dentro): un solo load, un solo override → **la dosis k aplica al trunk y al draft por igual** [T: mecánica del loader]. Sin conflicto; sinergia ya documentada en §7.
- La cabeza del draft sale de `nextn.shared_head_head` a vocab completo (248,320) — hardcoded en `qwen35moe.cpp` según el análisis del issue #25187 [F]: el draft NO se beneficia del recorte de expertos en su cabeza, solo en su capa MoE.
- b11856 trae flags de colocación EXCLUSIVOS del draft [F dump L344–350]: `-cmoed/--cpu-moe-draft` y `-ncmoed N` (MoE del draft a CPU), además de `-ngld`, `-tbd`, `--prio-draft` (default **0**, ver Nivel 3 §11.4), `-otd`. Si el nextn trae capa MoE propia y la VRAM aprieta con MTP activo, `-ncmoed` es la válvula.

### 12.8 DFlash/DSpark existen en el build y están descartados con evidencia [F]

El enum completo de `--spec-type` en b11856 [F dump L390]: `none, draft-simple, draft-eagle3, draft-mtp, draft-dflash, draft-dspark, ngram-simple, ngram-map-k, ngram-map-k4v, ngram-mod, ngram-cache`.

- **DFlash (PR #22105)**: reporte directo de comunidad con el 3.6-35B: *"with dflash, there is not enough vram"* en una 6 GB → en nuestra 1650 de 4 GB, **NO-GO** [F]. Es spec "wide" que necesita VRAM extra para la cabeza del draft.
- DSpark: sin datos de calidad/VRAM [N/D] — prioridad cero mientras MTP nativo esté disponible.

### 12.9 Resumen de cambios operativos de esta ronda

1. Plan B del §6.5 reemplazado: no hay flag futuro; el override-kv es definitivo (#19528 cerrado not planned).
2. Autenticación literal: grep `llm_load_print_meta: n_expert_used = N`.
3. Prohibido tocar las otras claves `expert_*` (§12.4).
4. Bonus a medir en fase D: `CUDA0 compute buffer size` debe bajar con k (confirma la dosis por segunda vía independiente del t/s).
5. Con fase E: la dosis cubre también el draft; `--prio-draft 2` recomendado; `-ncmoed` disponible si aprieta VRAM.

**Referencias nuevas de esta ronda**: discusión #5114 (override validado 2024): https://github.com/ggml-org/llama.cpp/discussions/5114 · issue #19528 CERRADO not planned: https://github.com/ggml-org/llama.cpp/issues/19528 · FR-Spec MTP + `nextn.shared_head_head` en qwen35moe.cpp: https://github.com/ggml-org/llama.cpp/issues/25187 · DFlash: https://github.com/ggml-org/llama.cpp/pull/22105 · dump local del build b11856 (líneas 162–166, 344–352, 390) [M].

## 13. ANEXO — Cuarta ronda: granularidad 256, sinergia con especulación y gates de calidad (2026-10-26)

- **Granularidad del router 3.6 [F ficha oficial]:** 256 expertos / 8 activos (vs 128/8 del Qwen3-30B-A3B [F su ficha]) → el doble de candidatos por slot: mayor redundancia por token → los recortes k=6/k=4 deberían costar MENOS calidad que en el hermano de 128 [T, argumento estadístico; sin evidencia directa del 3.6 → lo da el gate].
- **El draft MTP también es MoE [F bytes]:** el/los layer(s) nextn del repo -MTP (858,111,296 B medidos) contienen expertos ruteados → `expert_used_count` los afecta también → dosis k baja abarata TAMBIÉN el draft (doble ahorro DDR4) y puede bajar su aceptación [N/D → medir accept en el combo D×E].
- **Evidencia indirecta de recortes agresivos [F anécdota]:** "Qwen3-30B-A6B-16-Extreme" (variante comunitaria con 16 expertos, bien recibida en r/LocalLLaMA May-2025) → los MoE Qwen toleran recortes fuertes; NO sustituye al gate propio del 3.6.
- **Gate de calidad barato para dosis EXP (propuesto):** (1) llama-perplexity sobre snippet ES fijo (compatibilidad con qwen3_5_moe N/D → 2 min en el rig; si la tool falla, gate = solo spot-check), (2) sanity prompt del barrido con temp 0 y semillas fijas, (3) comparar k=8 vs 6 vs 4 en la MISMA sesión.
- **Interacción con N5:** los drafts sidecar (EAGLE3/DFlash) se entrenaron contra el modelo COMPLETO: recortar k del target no cambia el draft pero sí su distribución de aceptación [T] → anotar accept por dosis k.
- **Validez:** el gate n_expert_used del log (firma literal "llm_load_print_meta: n_expert_used = N" [F #5114]) sigue siendo condición de validez de cada config EXP (el NO-OP del barrido-30 por clave equivocada no se repite: parser GGUF propio).
