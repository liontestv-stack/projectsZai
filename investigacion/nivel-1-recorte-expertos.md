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

## 14. ANEXO — Quinta ronda: el cache de expertos calientes YA está en b11856 (2026-10-26)

Esta ronda cambia el nivel 1 más que cualquiera de las anteriores: el concepto "pool persistente de expertos calientes en VRAM" que la comunidad llevaba meses pidiendo en RFCs y PoCs **ya viene fusionado en el build b11856 del rig**, apagado por defecto. Nadie lo había conectado antes en este archivo porque el flag no se llaman como en los RFCs y está a 0.

- **DESCUBRIMIENTO [M dump b11856] el flag existe y está APAGADO:** `--moe-cache-mib N` — texto literal del dump: *"GPU cache size in MiB for the MoE experts kept in the CPU. with multiple GPUs, it is split among them like the layers (--tensor-split) (default: 0, disabled)"* (env: `LLAMA_ARG_MOE_CACHE_MIB`). **Default 0 = desactivado** → por eso el barrido-30 nunca lo benefició y por eso ningún default auditado lo mostraba. El dump VIEJO (build anterior del Director) tiene 0 ocurrencias → la feature entró entre ese build y b11856. También aparece `-ncffn/--n-cpu-ffn` (offload de FFN densa; no aplica al 3.6, todo-MoE, pero es un flag nuevo del inventario).
- **OJO colisión de nombre [M dump vs F reddit]:** en builds posteriores la comunidad reporta el par `-cmoe/--moe-cache-mib` [F reddit PR #29887]; en **b11856 `-cmoe` sigue siendo `--cpu-moe`** (todos los expertos a CPU) y el cache SOLO se controla por `--moe-cache-mib N`. No confundir: en este build `-cmoe` NO activa el cache.
- **Números comunitarios del cache [F reddit PR #29887 "llama : add a GPU cache for MoE experts kept in host memory", follow-up #30112 MERGED]:** **33 → 52 t/s (+60%) con Qwen3.6-35B-A3B en RTX 4050 de 6 GB** (¡exactamente nuestro modelo y nuestro régimen híbrido!); 35 → 47 t/s (+34%) en RTX 3080 10 GB; prefill 350 → 500 t/s. La mecánica: los expertos elegidos por el router que residen en CPU se copian a un pool en VRAM; los hits se sirven sin tráfico PCIe; los misses copian y expulsan el slot LRU menos usado.
- **La línea evolutiva [F]:** (1) issue #20757 PoC Vulkan de martinalderson: overlap de expertos entre tokens consecutivos = **44%**, skew de routing Gini ≈ 0.76, hit-rate del cache sube de 47% (100 tokens) a 67% (500+ tokens), perplexity idéntica dentro de barras de error; además descubrió que el `set_tensor_async` sobre datos mmap'd es síncrono y que el bypass SAM/ReBAR solo ya da +55% de prefill — pero sin SAM, forzar MoE a GPU EMPEORA decode (9 vs 28 t/s). (2) RFC/discussion #28248 (`--moe-expert-cache N/-mec`, rama `moe-expert-pool`, NO fusionada a la fecha): +84% decode (21.21 vs 11.55) y +34% code-gen en RTX 4090 con Qwen3.8-Flash-Next, pool limitado a la mitad de la VRAM libre. (3) **b11856 YA trae la versión fusionada** con nombre `--moe-cache-mib` [M].
- **Por qué es PALANCA #1 del nivel 1 ahora:** las dosis EXP (`-ncmoe N`) ahorran VRAM sacando expertos, y `--moe-cache-mib` recupera velocidad sobre lo que queda en CPU SIN sacar nada. Son ortogonales y combinables: `-ncmoe 37 --moe-cache-mib 512` usa 512 MiB de la VRAM libre como cache LRU de los expertos CPU. En el 3090-full-GPU esto no existía (nada en CPU); en nuestro híbrido es donde más rinde [T apoyada en los +60% del 4050].
- **Dosis fase D actualizada (sobre NCM37C4 22.49):** D-MEC-512 = `-ncmoe 37 -c 4096 --moe-cache-mib 512`; D-MEC-768 y D-MEC-1024 como subida progresiva vigilando el cliff (la VRAM del cache sale del mismo presupuesto que KV/buffers — ver N4 §13). Presupuesto: VRAM libre estimada tras carga 1.2-1.7 GB [T §8] → 512 MiB es la dosis segura inicial; si el buffer de cómputo MoE ya consume el margen, el cache se nota en fallo de carga, no en silencio.
- **Reglas de colocación confirmadas por fuentes externas [F blog openclawdc 2026 + Doctor-Shotgun HF]:** mantener `-ngl` al máximo y ajustar la memoria con `-ncmoe` (la atención SIEMPRE en GPU); **`--n-cpu-moe` cuenta las capas desde la MÁS ALTA** → en el 3.6 (40 capas todas MoE) `-ncmoe 37` deja en GPU las capas 0-2; la regla de oro del sweep: *encuentra el cliff y retrocede un paso* (dato 5090: 20→54, 16→64.5, 12→69.4 t/s y un paso menos → 27.5 por spill silencioso a RAM). `-b/-ub` chicos liberan VRAM para expertos a costa de solo prefill.
- **KV cuantizada NO es palanca de velocidad [F openclawdc, consistente con nuestro barrido]:** "f16 KV es más rápido que q8_0 cuando cabe" (la cuantía añade conversión por token); nuestro KVQ51 midió 0% [F CSV] → la KV cuant en el rig es SOLO para memoria (N4), nunca se esperaba velocidad de ahí.
- **Integración barrido-total:** añadir 3 dosis MEC a la fase D (512/768/1024 con `-ncmoe 37 -c 4096`) + autenticadores existentes (n_expert_used del log + buffer-size) + NO-GO predeclarado: si la carga falla por VRAM con MEC ≥ 768, dosis se reduce y se anota. Interacción con fase E (MTP): el draft nextn también es MoE [F §13]; si su experto queda en CPU con `-ncmoed`, el cache podría cubrirlo también [N/D → leer log].

*Referencias nuevas: reddit r/LocalLLaMA "llama : add a GPU cache for MoE experts kept in host memory" (PR #29887, #30112); github ggml-org/llama.cpp discussions/28248 y issues/20757; openclawdc.com/blog/llama-cpp-moe-offload-flags-explained (2026); huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide.*

## 15. ANEXO — Sexta ronda: MEC con números de producción sobre nuestro modelo exacto, el riesgo de thrash del cache chico y la sinergia MEC×MTP (2026-10-26)

La sexta ronda trae la primera batería de números de PRODUCCIÓN del `--moe-cache-mib` sobre **Qwen3.6-35B-A3B exactamente** (no un hermano): confirman la palanca, calibran expectativas y añaden un riesgo nuevo que cambia el protocolo de dosis.

- **Números de producción en 5070Ti 16GB con UD-Q4_K_XL del repo MTP [F note.com/high_u "MoE cache added to llama.cpp v0.7.0"]:** misma tarjeta, mismo modelo, única variable = MEC y contexto. **Q3:** `-ncmoe 26`, ctx 262144, SIN MEC → **83.27 t/s**. **Q1:** `-ncmoe 99` (TODO el MoE en CPU) + `--moe-cache-mib 7168`, ctx 262144 → **116.64 t/s (+40%)**. **Q2:** `-ncmoe 99` + MEC **9216** MiB, ctx 131072 → **143.43 t/s** (vs 105.37 de Q4 = -ncmoe 22 sin MEC en el mismo ctx: **+36%**). Lectura doble: (1) el cache en régimen GiB NO solo compensa el `-ncmoe 99` completo sino que lo SUPERA (116.64 vs 83.27 con menos expertos residentes); (2) el autor usó `--spec-type draft-mtp --spec-draft-n-max 3 -np 1 -fa on -ctk q8_0 -ctv q8_0` — MEC + MTP + KV cuantizada convivieron sin conflicto en esa escala.
- **CALIBRACIÓN de expectativa para el rig [T sobre F]:** esos caches son de 7-9 GiB (una 16GB se los puede pagar; nuestra 1650 de 4GB NO: presupuesto libre 1.2-1.7 GB [T §8]). La ganancia del cache escala con el hit-rate, y el hit-rate con el tamaño relativo al working set de expertos → **nuestros 512-1024 MiB NO reproducirán +40%; el rango honesto es desconocido [N/D] y lo mide la fase D con el control D-MEC-0**. El dato de los 6950 XT (ronda 5: 8.2→18.9 t/s subiendo slots hasta saturar) muestra que la curva tamaño→ganancia es empinada recién cerca de cubrir el hot set (~85-93% hit).
- **RIESGO NUEVO — el cache CHICO puede REGRESAR [F reddit PR #29887]:** un usuario reportó **28 → 14.5 t/s (−48%) con 600 MiB de cache**. Mecánica [T]: si el cache es mucho menor que el working set de expertos activos (nuestro routed activo = 8 expertos × 40 capas × ~8 MB ≈ 1.0 GB por token de conjunto [T §7]), cada token expulsa lo que el siguiente necesita → churn PCIe constante PEOR que sin cache (el LRU nunca calienta). → **Protocolo de dosis actualizado: toda dosis MEC se mide A/B contra D-MEC-0 (= NCM37C4 puro, `--moe-cache-mib 0`) en la MISMA sesión con mediana de 3; si la dosis es más lenta que el control, se descarta y se anota el número.** El thrash explica de paso por qué el dato del 4050 (+60%) usó un pool proporcionalmente grande.
- **Sinergia MEC×MTP es SUPER-ADITIVA [F RFC/discussion #24528, fork Lidenburg — NO fusionado]:** en GLM (MoE híbrido hermano de situación), MTP solo = **+28%**; MTP **con** el cache de expertos = **+51%**. Cita literal del RFC: *"verification batches are what multi-token fusion accelerates"* — el verify de un bloque de k tokens relee el mismo conjunto de expertos k+1 veces seguidas; con cache, la 2ª..(k+1)ª lectura sale de VRAM en vez de DDR4. Es la respuesta cuantitativa al [N/D] de la ronda 5 sobre si el cache cubre al draft: SÍ, y el bonus de fase E podría casi duplicarse con MEC activo [T, pendiente de medir en el rig con el combo D-MEC + E].
- **Advertencia de build para el combo [F reporte Vulkan + M dump]:** en la línea de código del cache existe un **gate de batch único** que EXCLUYE del cache a los batches chicos de verificación especulativa (los reportes dicen que "convertía el multi-token drafting en pérdida en un host débil" hasta que un build posterior añadió un límite opt-in de tokens que restaura el cache sin cambiar el default). **En el dump b11856 NO hay ninguna flag CLI de ese gate** (grep verbatim: solo `--moe-cache-mib` y su env; cero ocurrencias de min-batch/token-limit) → si el combo D-MEC + fase E no muestra la sinergia esperada, la hipótesis #1 es este gate; mitigación = RUTA 0 (build nuevo) o aceptar MEC solo en fases sin spec. Anotar en el barrido: correr E con MEC 0 y MEC 512 para aislar el efecto.
- **Fix menor upstream [F release b11888, 25-Oct]:** límite de profundidad recursiva en grammar (tokens de 256+ caracteres siempre rechazados bajo GBNF; mejora sampling con gramática en Qwen3.6 entre otros). Sin efecto en nuestras dosis (no usamos GBNF en el barrido), se anota por completitud del inventario b11856-vs-upstream.
- **Dosis fase D FINAL (sustituye §14, añade control):** D-MEC-0 (control = NCM37C4) → D-MEC-512 → D-MEC-1024 → D-MEC-768 (si 512 gana y 1024 no cabe/regresa). Autenticadores: n_expert_used del log + buffer-size + A/B mismo-session. NO-GO de dosis individual: más lenta que D-MEC-0 con mediana de 3 → descartada (el caso 600 MiB ya ocurrió en la naturaleza).

*Referencias nuevas: note.com/high_u/n/nf64f0b62a91f (bench v0.7.0 5070Ti); github ggml-org/llama.cpp discussion #24528 (fork Lidenburg, sinergia MEC×MTP en GLM); reddit PR #29887 comentarios (regresión 600 MiB, 3080 35→47 t/s, PRO 4500 22→35 t/s); reporte Vulkan dual-6950XT (freenode.net, Sept-2026); release b11888.*


## 16. ANEXO — Séptima ronda: MEC oficializada en v0.7.0, el coste MoE de la verificación especulativa y la enumeración real de spec-types en b11856 (2026-10-26)

- **MEC ya es feature de release estable [F]:** las notas de v0.7.0 (15-Oct-2026) oficializan el GPU cache para expertos MoE en memoria host: `--moe-cache-mib`, "up to ~2.2x decode speedup when experts are offloaded" (#29887), el cache de expertos ahora se COMPARTE entre múltiples GPUs (#30112) y existe un parámetro API nuevo `moe_cache_size` en `include/llama.h`. Para la 1650 (single GPU) el multi-GPU no aplica, pero confirma la dirección upstream y estabiliza la flag que ya usamos en dosis.
- **Coste MoE de la verificación especulativa [F→T]:** la guía de Jetson AI Lab sobre DFlash advierte que "un valor menor puede ganar cuando... la verificación paralela activa expertos extra en un MoE" — verificar un bloque de K tokens en un paso puede activar MÁS expertos que decodificar 1 a 1. Con k-bajo (este nivel) + MEC, el coste marginal de esa activación extra baja → hipótesis de sinergia dosis k-bajo × dosis spec, direccional, a medir en el cruce fase D × fase E tras RUTA 0.
- **Enumeración real de spec-types en b11856 [M dump]:** la entrada `--spec-type` del dump lista SOLO tipos sin draft — `[none|ngram-cache|ngram-simple|ngram-map-k|ngram-map-k4v|ngram-mod]` — con la nota "type of speculative decoding to use when no draft model is provided"; cero ocurrencias de eagle3/dflash/dspark/mtp en el dump completo. Con `-md` el build va por el camino clásico (draft-simple implícito). Implicación presupuestaria para este nivel: HOY el spec no compite por los 1.2-1.7 GB libres de VRAM con nada; tras RUTA 0 el draft (nextn o sidecar) entra al mismo presupuesto → orden de operaciones: fijar dosis E/S primero, reordenar dosis D después, no al revés.

*Referencias nuevas: release v0.7.0 de llama.cpp (15-Oct-2026, notas oficiales con #29887, #30112, #30506); jetson-ai-lab.com/tutorials/speculative-decoding (guía MTP/DFlash/DSpark con la advertencia MoE); dump b11856 del Director (enumeración --spec-type, re-verificación [M] de esta ronda).*


## 17. ANEXO — Octava ronda: punto de datos de producción de terceros para ncmoe en nuestra familia exacta (2026-10-26)

- **`--n-cpu-moe 31` de terceros [F]:** una guía de setup en producción con NUESTRA familia de modelo exacta (Qwen3.6-35B-A3B, cuant UD-Q4_K_S) usa `-ngl 99` + `--n-cpu-moe 31` — 31 capas de expertos en CPU, resto en GPU — junto a draft-mtp n-max 4, ctx 64,000 y KV q4_0/q4_0. Para las dosis ncmoe de este nivel: la escalera propia 26/99 (ronda 6) ahora tiene un punto de referencia externo intermedio (31); la GPU de esa guía NO es una 1650 4GB (su VRAM no se especifica en la fuente [N/D]) así que el número NO es transferible directo — es señal de que el knob `--n-cpu-moe` convive en producción con draft-mtp + KV cuantizada sin conflicto, que era la pieza que faltaba validar.
- **Sin novedad adicional de MEC esta ronda:** lo de la ronda 7 (oficialización en v0.7.0, multi-GPU) se mantiene como última palabra; el control D-MEC-0 sigue siendo el paso obligatorio del barrido.

*Referencias nuevas: lautenbacher.io/en/general/setting-up-llama-cpp-on-windows-with-cuda-13 (setup 8-Jul-2026 con Qwen3.6-35B-A3B UD-Q4_K_S, tabla completa de parámetros).*


## 18. ANEXO — Novena ronda: `-ot/--override-tensor` al detalle, la regla de clasificación del offload (cuándo `-cmoe` mata y cuándo salva), el fork ik descartado con números y el piso de formato del 3.6 (2026-10-26)

- **`-ot/--override-tensor` EXISTE en b11856 [M dump L108]:** `-ot, --override-tensor <tensor name pattern>=<buffer type>,...` — "override tensor buffer type" (env `LLAMA_ARG_OVERRIDE_TENSOR`); y su variante de draft `-otd/--spec-draft-override-tensor/--override-tensor-draft` [M dump L323]. Es el hermano de baja granularidad de `-ncmoe`: mismo efecto (expertos fuera de VRAM), control por regex.
- **Mecánica completa de `-ot` [F guía Doctor-Shotgun + PR #11397 + manpage Debian]:** (1) regex por substring sobre el nombre del tensor → `-ot "exps=CPU"` manda TODOS los expertos routed a CPU; el patrón "exps" NO matchea "shexp" (falta la s final en `ffn_*_shexp`) → **el experto shared, la atención, la KV y el compute buffer quedan en GPU automáticamente** — la configuración base de la guía es exactamente nuestro régimen. (2) La primera regla que matchea gana: `-ot "blk\.([0-9]|[1-2][0-9]|30)\.=CUDA0,exps=CPU"` pone capas 0-30 completas en CUDA0 y el resto de expertos en CPU. (3) Forma oficial para múltiples overrides: **una sola flag con lista separada por comas** (pasar `-ot` varias veces está deprecado según la guía; la manpage Debian solo documenta comas). (4) En modelos con capas densas al inicio (DeepSeek: 3 primeras), el conteo es desplazado — irrelevante para el 3.6 (40/40 MoE).
- **Resolución de la contradicción first-vs-highest [M+F]:** el dump b11856 dice literalmente *"keep the Mixture of Experts (MoE) weights of the **first** N layers in the CPU"* (L113-114), igual que openclawdc y la discusión #22183; la guía Doctor-Shotgun afirma "highest numbered layers". Para el 3.6 (todas las capas son MoE) la diferencia es SOLO el orden de qué capas, no la cantidad offloadeda → **las dosis no cambian**. Run autenticador cruzado barato (1 run, fase D): `-ot "blk\.(3[7-9])\.ffn_(gate|up|down)_exps=CPU"` debe dar ≈ NCM37C4 (22.49 [M]) dentro de varianza → si coincide, la comprensión del knob queda validada por segunda vía; si difiere, bug de comprensión antes de seguir barriendo. Ojo: si el GGUF lleva nextn como capa extra, ese patrón no la toca (la colocación del draft sigue siendo territorio de `-ncmoed/-otd`).
- **La regla de clasificación del offload [F llmkube 18-Abr-2026]:** `--cpu-moe` NO intercambia "banda por banda": intercambia **VRAM ahorrada ↔ coste de CPU por token** (con -cmoe el 3.6 paga ~360 matmuls de experto en CPU por token). Dato duro: dual 16GB donde el 3.6 Q4_K_M CABE entero con su KV (solo las 10 capas Gated Attention llevan KV): **sin -cmoe 107.8 t/s vs con -cmoe 21.7 t/s = 5x de PÉRDIDA**. Contraste en el mismo box: Qwen3-Coder-30B (48 capas GQA, TODAS con KV) no cabe sin -cmoe y ahí el flag es el que lo hace posible (31 t/s). Lección operativa: el flag solo paga cuando modelo+ctx DESBORDA; en la 1650 el desborde es permanente → offload sí, pero **el mínimo necesario** (sweep del cliff, nunca `-cmoe` global salvo emergencia de ctx máximo).
- **Convergencia 3090 [F reddit 1v4gzc4]:** Qwen3.6-35B-A3B-MTP-MXFP4 en 3090 + i5-12600K: `-cmoe` ON = 31.6/30.1/27.8 t/s (3 turns) vs default/auto = 55.4/51.1/47.8 → **~1.7x a favor de offload parcial/auto**. Recomendación comunitaria resultante: dejar fit auto O `-ngl 999` + sweep `-ncmoe`; reservar `-cmoe` para ctx máximo/OOM. Nuestro NCM37C4 (explicito, no confiar en -fit) va en la dirección de los ganadores.
- **El auto-fit es conservador y cuesta [F hanxiao/Qwen3.6-35B-A3B-MTP-L4]:** en L4 24GB donde el modelo cabe (21.3 GiB de 22.5), el auto-fit "parks several MoE expert layers on the CPU to be safe" → 63.3 t/s; la escalera explícita: `-ncmoe 4`→67.3, `2`→73.5, `1`→76.9, **`0`→80.9 (+28%)**. Tercera fuente que valida nuestra regla de dosis explícitas (ronda 3: `-fit` solo toca args no fijados): nunca dejar que el fit decida la colocación de expertos.
- **ik_llama.cpp = NO-GO cerrado con números [F issue #1699, 27-Abr-2026]:** mismo 3.6-35B (IQ4_XS, ctx 131k, `-cmoe -ngl 999`), GTX 1660 Super 6GB + Ryzen 5800X: mainline PP 239.8 / TG **15.69** t/s vs ik PP 118.8 / TG **10.4** → **−2x PP y −1.5x TG del fork vs mainline** en el arch híbrido; el propio mantenedor termina sugiriendo usar mainline. La ventaja histórica del fork (kernels MoE-CPU fusionados) NO aparece en `qwen3_5_moe` → la vía "fork más rápido" muere; **RUTA 0 a mainline b11901 sigue siendo el único camino de build** (coherente con N5 §14).
- **Cross-check 6GB del backbone [F discusión #30426, 12-Oct-2026]:** Qwen3-Omni-30B-A3B-Thinker Q4_K_M con `-cmoe -ngl 99` en GTX 1060 6GB + 32GB DDR4: backbone denso + proyección de visión en **~2.4 GB de VRAM**, 18.5 GB de RAM, ~16.2 t/s decode, PP ~270. Dos lecturas: (a) el suelo VRAM del backbone es real (~2.4 GB con mmproj; ~1.5 GB sin él [T]) — consistente con nuestro presupuesto de §8; (b) full-offload de terceros = 16.2 t/s vs nuestro 21.5 [M] con offload parcial → refuerza que **parcial > full** en régimen DDR4-bound.
- **Piso de formato GGUF del 3.6 [F card DJLougen]:** `IQ1_S 1.66 GB` es el mínimo GGUF posible: llama.cpp mantiene el embedding 248k y la lm_head untied a ≥2-bit (forzar 1-bit **aborta** la conversión). El REAP-90pct (keep-26 de 256, 6.15B params): Q4_K_M 3.4 GB — pero el propio autor: "THIS MODEL IS MEANT TO BE A MEME... mostly incoherent". Cierra la cola de poda extrema (coherente con el NO-GO de la ronda 1) y fija el suelo físico de cualquier cuant extremo futuro (ver N2 §19).
- **Dato hermano 8GB [F reddit Poor GPU Club, snippet]:** Qwen3-30B-A3B en 4060 Laptop 8GB + 32GB RAM: ~17.6-29.2 t/s según fase/muestra [N/D detalle completo por bloqueo de reddit] — nuestro 21.5 t/s con el 35B en 4GB [M] queda dentro del rango del régimen bandwidth-bound (sanidad cruzada externa).
- **Dosis de fase D: SIN cambios** — NCM37C4 + D-MEC-0/512/1024 + escalera EXP6→4→3 se mantienen íntegras. Único añadido opcional: el run autenticador cruzado `-ot` del punto 3.

*Referencias nuevas: llmkube.com/blog/hybrid-moe-offloading-qwen-36-deltanet (18-Abr-2026, el 5x de -cmoe y la clasificación); huggingface.co/blog/Doctor-Shotgun/llamacpp-moe-offload-guide (mecánica -ot, prioridad de reglas, op-offload); github ggml-org/llama.cpp PR #11397 (origen de -ot), discussions #13154, #22183; manpages.debian.org/unstable/llama.cpp-tools/llama-server.1 (sintaxis comas); reddit r/LocalLLaMA 1v4gzc4 (3090 A/B), 1tany5t (PP 5.5x), 1nyxmci (8GB, snippet); github ikawrakow/ik_llama.cpp issue #1699 (fork vs mainline con el 3.6); github discussion #30426 (Omni en 1060 6GB); huggingface.co/DJLougen/Qwen3.6-35B-A3B-REAP-90pct-GGUF (card completa, piso IQ1_S); github hanxiao/Qwen3.6-35B-A3B-MTP-L4 (escalera -ncmoe); dump b11856 del Director (L108-118: -ot, -cmoe, -ncmoe "first N", -ngl auto; L323: -otd) [M].*


---

## 19. ANEXO — Décima ronda: AUDITORÍA DE RESPALDO RIGUROSO punto a punto (2026-10-26)

Orden del Director: "respalda cada punto de los 4 archivos, de forma rigurosa". Método: re-verificación independiente de los puntos [F] contra fuente primaria (40+ búsquedas frescas y lectura directa de las páginas citadas), re-chequeo de los [M] del dump contra la manpage Debian de llama-server (segunda fuente del mismo texto, independiente del dump), y consistencia interna de los [M] CSV y las [T]. **Resultado global del nivel 1: 0 puntos refutados; ~20 confirmados verbatim; 2 matices de precisión; dosis de fase D SIN cambios.**

Veredictos usados abajo: **✔ VERBATIM** = re-encontrado hoy con las mismas cifras/texto en la fuente; **✔ EXISTE** = fuente confirmada viva hoy (detalle fino no visible en el snippet pero registrado en rondas previas con URL); **⚠ MATIZ** = confirmado con precisión a añadir; **◻** = no re-buscado hoy (respaldo original en pie).

### 19.1 Evidencia académica y de poda

| Punto (§) | Veredicto | Respaldo re-verificado hoy |
|---|---|---|
| MoE-Spec ~95% calidad @2.0× en Qwen3-30B-A3B, el más favorable de los evaluados (§0, §3.1) | ✔ VERBATIM | arXiv 2602.16052v1 (17-Feb-2026): *"Qwen3-30B-A3B shows the most favorable tradeoff, maintaining approximately 95% quality even at 2.0× speedup with tight error bars"* |
| REAP retiene 97.6% coding / 96.7% SWE-Bench a 50% de poda (§3.2, §11.3) | ✔ VERBATIM + ⚠ | Blog Cerebras (16-Oct-2025): *"with the Qwen3-480B-Coder-FP8 model, REAP at 50% pruning retains 97.6% of its baseline non-agentic coding ability and 96.7% on the agentic SWE-Bench benchmark"* — MATIZ de precisión: las cifras son del **480B-Coder**, no del 30B; nuestro texto no especificaba modelo |
| Not All Experts are Equal (ACL 2024), REAP arXiv 2510.13999, repo CerebrasResearch/reap (§3.2) | ✔ EXISTE | arXiv y GitHub del repo confirmados vivos hoy; paper evalúa EvalPlus/LiveCodeBench/SWE-Bench Verified con mini-SWE-agent (método leído hoy) |
| Cola larga 2604.23036, Shapley-MoE, C-PRUNE (§3.2) | ◻ | No re-buscados individualmente hoy; la tesis "routing skew" la re-confirma por otro camino el dato Gini 0.76 de #20757 (abajo) |
| El override NO renormaliza pesos → truncation implícita (§1, §7) | ◻ (apoyado hoy) | El mecanismo sigue sin contradicción en ninguna fuente re-visita; la guía oficial de unsloth de expert_override no lo desmiente |

### 19.2 El override-kv: clave, autenticación y estado del flag dedicado

| Punto (§) | Veredicto | Respaldo re-verificado hoy |
|---|---|---|
| `--override-kv llama.expert_used_count=int:3` imprime `n_expert = 8` / `n_expert_used = 3` en el log (§12.2) | ✔ VERBATIM | Discusión #5114 (Ene-2024, marcada como respuesta): las DOS líneas de log literales, idénticas a las registradas; además hilo reddit de Mixtral y tutos japoneses (DeepSeek-V3 k8→2-4 sube 18→22-25 t/s; k=1 rompe la generación) = la escalera EXP tiene 2 validaciones externas más |
| Issue #19528 (`--expert-override`/`--moe-topk`) cerrado not-planned; override-kv es LA vía (§12.3) | ✔ EXISTE | El issue está vivo en GitHub (11-Feb-2026, "Add a command-line flag --expert-override or --moe-topk..."); estado not-planned registrado en ronda 3 |
| Discusión #30155: override k10→7 da +29% t/s y hit-rate de cache 50→80% (§3.3, §11.2) | ✔ EXISTE + ⚠ | La discusión está viva hoy; MATIZ de precisión: el título real es *"Is it reasonable to override **qwen4exp**.expert_used_count"* — el arch de esa discusión es `qwen4exp` (MoE de la familia 4), no un genérico; las cifras 35→45 t/s quedan de la lectura de ronda 1 |
| Clave correcta = `<arch del GGUF>.expert_used_count` con comas en un flag (§11.1, §12.1) | ✔ VERBATIM | Manpage Debian llama-server (re-chequeada hoy): `--override-kv KEY=TYPE:VALUE,...` con tipos int/float/bool/str — mismo texto que el dump b11856 [M]: el dump queda respaldado por segunda fuente |

### 19.3 MEC (`--moe-cache-mib`) y la línea evolutiva del cache

| Punto (§) | Veredicto | Respaldo re-verificado hoy |
|---|---|---|
| PR #29887 "GPU cache for MoE experts kept in host memory" + #30112 multi-GPU MERGED (§14, §16) | ✔ VERBATIM | Reddit del PR vivo hoy: anuncio de am17an, *"update #30112 MERGED"*, benchmark del hilo: 3080 10GB Qwen3.6-35B-A3B ~35→40 t/s; con `-cmoe` + `--moe-cache-mib`: **47 t/s gen y prefill 500 (desde 350)** = exactamente las cifras 35→47/350→500 registradas en §14 |
| v0.7.0 oficializa MEC: ~2.2x decode, `moe_cache_size` en llama.h (§16) | ✔ VERBATIM | Notas de release v0.7.0 (15-Oct-2026, espejo SourceForge leído hoy): *"a new GPU cache for MoE experts kept in host memory (--moe-cache-mib, up to ~2.2x decode speedup when experts are offloaded)"* + *"The expert cache is now shared across multiple GPUs [#30112]"* + API `moe_cache_size` |
| Gate de batch que excluía verificación especulativa del cache + opt-in posterior (§15) | ✔ VERBATIM | Reporte dual-6950XT (freenode, 04-Sep-2026): *"a single-token gate blocked the cache on small speculative-verification batches, turning multi-token drafting into a loss on a weak host. An opt-in token limit restores cache use"*; escalera 8.2 → 12-13 (85%) → 17.4-17.8 (92%) → 18.9-19.1 t/s (93%) = verbatim a §15/§14 |
| PoC #20757 martinalderson: overlap 44%, Gini 0.76, hit-rate 47→67%, SAM bypass +55% prefill, sin SAM el MoE-GPU EMPEORA (9 vs 28) (§14) | ✔ VERBATIM | Issue leído hoy: todos los números y hasta la tabla (27.9 → 35.1 t/s) y la perplexity "identical within error bars" coinciden al carácter |
| RFC #28248 pool persistente NO fusionado (§14) | ✔ EXISTE | Vivo hoy (06-Sep-2026); menciona la copia selectiva de expertos de #15346 como base |
| Sinergia MEC×MTP GLM +28%→+51% (§15, RFC #24528 fork Lidenburg) | ✔ EXISTE | RFC vivo hoy (12-Jun-2026) con el fork Lidenburg enlazado; cifras GLM de la lectura de ronda 6 |
| Thrash del cache chico: 600 MiB = −48% (28→14.5 t/s) (§15) | ◻ | Registrado ronda 6 desde el hilo de #29887; el hilo sigue vivo; el dato CUvinny del mismo hilo (9070XT: cache 8000 MiB = 76.9 t/s, 12000 = 42.6, pp se degrada antes) AÑADE hoy otra muestra de que el tamaño y el prefill importan |
| 5070Ti UD-Q4_K_XL: 83.27 / 116.64 / 143.43 t/s con MEC 7-9 GiB (§15) | ✔ EXISTE | note.com/high_u citado y leído en ronda 6; no re-abierto hoy — el punto crítico (escala 7-9 GiB >> nuestros 512-1024 MiB) es matemática propia [T] |
| b11888: fix de profundidad recursiva en grammar (§15) | ◻ | De release notes de ronda 6; irrelevante para dosis (sin GBNF) |

### 19.4 Offload, -ot, fork ik y cross-checks de producción

| Punto (§) | Veredicto | Respaldo re-verificado hoy |
|---|---|---|
| `-ot "exps=CPU"` NO matchea `shexp` → shared/atención/KV quedan en GPU (§18) | ✔ VERBATIM | Guía Doctor-Shotgun leída hoy: *"Attention + Dense FFN + Shared expert FFN on the GPU along with the model's k/v cache and compute buffer. The remaining Routed expert FFN are all assigned to the CPU"* |
| Primera regla que matchea gana; comas oficiales; repetir `-ot` deprecado (§18) | ✔ VERBATIM | Misma guía: *"The first statement takes priority"* + *"Multiple -ot expressions are officially recommended to be provided as a comma-separated list, rather than specifying the -ot argument multiple times, which is deprecated"*; manpage Debian solo documenta comas |
| `-ncmoe` = "first N layers" (dump L113) vs "highest numbered" (Doctor-Shotgun) (§18) | ✔ VERBATIM (ambas fuentes) | Manpage Debian: *"keep the MoE (MoE) weights of the first N layers in the CPU"* = dump; la guía mantiene su nota *"starts counting layers starting from the highest numbered layers"* → la contradicción es real y nuestra resolución (irrelevante en 40/40 MoE, run autenticador cruzado) queda la vía correcta |
| `-cmoe` REGRESA 5x cuando el modelo cabe (107.8 vs 21.7) (§18) | ✔ EXISTE (tesis VERBATIM) | Blog llmkube vivo hoy (18-Abr-2026) con título tautológico del punto: *"Why Qwen 3.6 Doesn't Need --cpu-moe"*: *"Because the model fits in VRAM without any offloading, the 'VRAM savings' that --cpu-moe normally trades for is not needed. Enabling it anyway..."*; cifras del box dual-16GB de la lectura de ronda 9 |
| 3090: -cmoe 27.8-31.6 vs auto/parcial 47.8-55.4 (~1.7x) (§18) | ✔ EXISTE | Reddit 1v4gzc4 registrado ronda 9 |
| ik_llama.cpp −2x PP / −1.5x TG con el 3.6 (§18) | ✔ VERBATIM | Issue #1699 vivo hoy (27-Abr-2026): *"ik_llama.cpp is ~2x slower on prompt processing (PP) and ~1.5x slower on token generation (TG) compared to mainline llama.cpp. Model Qwen3_6-35..."*; hilos hermanos (reddit Qwen3.5, discusión 1737) confirman el patrón |
| #30426 Omni-30B en 1060 6GB: ~2.4 GB VRAM backbone+visión, 18.5 GB RAM, 16.2 t/s, PP 270 (§18) | ✔ VERBATIM | Discusión leída hoy (MIThriade, 12-Oct-2026): tabla de hardware y todos los números coinciden; comando `-cmoe -ngl 99 -c 4096 -t 8` |
| Piso GGUF IQ1_S 1.66 GB; REAP-90 "meme, mostly incoherent" (§18) | ✔ VERBATIM | Card DJLougen leída hoy: *"This is a 90%-expert-pruned model. It loads, it streams tokens, and the tokens are mostly incoherent — more so at IQ1_S than Q4_K_M"* |
| Dato hermano 8GB (17.6-29.2 t/s) (§18) | ✔ EXISTE + refuerzo | Encontrado hoy además: mdda.net (11-May-2026) corre el 3.6 en GTX 1080 8GB con `--n-cpu-moe` y concluye *"PCIe maxed out + GPU half-idle = bandwidth-limited"*; reddit 4060 8GB+96GB RAM con el 3.6 en marcha — el régimen bandwidth-bound queda corroborado por 2 fuentes más |
| KV del 3.6 modesta por diseño (solo 10 capas GA) (§18, coherencia) | ✔ VERBATIM (corroboración) | Reddit dual-5060Ti: *"Qwen 3.6's DeltaNet hybrid attention keeps the KV cache small enough that offloading solves a problem that doesn't actually exist here"* |

### 19.5 Estado [M] y [T] del nivel

- **[M dump b11856]** (`-ot` L108, `-otd` L323, `-ncmoe` "first N" L113, `-ngl` auto L116, `--moe-cache-mib` default 0, `-lm` modos, `-lzm` >4GiB): **TODOS los textos del dump coinciden palabra por palabra con la manpage Debian de llama-server re-leída hoy** — el dump deja de ser fuente única y pasa a estar respaldado 1:1 por segunda fuente independiente.
- **[M CSV barrido-30]** (familia EXP plana, NCM37C4 22.49, FIT-A 22.40): datos propios; la auditoría no los toca. El test de coherencia §11.4 (k=4 debe subir ~15-17% si la dosis vive) sigue siendo el árbitro.
- **[T] modelo de banda** (~32 GB/s efectivos): reforzado hoy por mdda.net (mismo régimen bandwidth-bound en PCIe 3.0) y por la clasificación openclawdc "f16 KV más rápido que q8_0 cuando cabe" (consistente con KVQ51=0%).
- **Dosis fase D: SIN CAMBIOS** — NCM37C4 + D-MEC-0/512/1024 + escalera EXP6→4→3 + run autenticador cruzado `-ot` se mantienen íntegras.

*Referencias de esta auditoría: arXiv 2602.16052v1; blog Cerebras REAP y repo CerebrasResearch/reap; discusiones #5114, #30155, #20757, #28248, #24528, #30426; issue #19528 e ik_llama.cpp #1699; reddit PR #29887 (con #30112 MERGED), 1v4gzc4, dual-5060Ti, 4060-8GB; freenode dual-6950XT; notas oficiales v0.7.0; manpages.debian.org llama-server.1; Doctor-Shotgun HF blog; openclawdc flags-2026; llmkube deltanet; mdda.net GTX-1080; DJLougen card; note.com high_u y aisatoshi.*

## 20. ANEXO — Ronda 13: instrumento dedicado de la fase D, creado y validado (2026-10-27)

La ronda 12 fijó el orden de campaña N1→N3→N2→N4 y el Director encargó ejecutar **nivel por nivel**: "analiza todo el documento no resumido y crea todas las pruebas que necesites... verifica mis flags nuevas permitidas... crea un archivo .py que haga todas las pruebas y genere un log". Este anexo registra el instrumento creado (NADA cambia en las dosis ni en las conclusiones de §0-§19; el instrumento LAS EJECUTA).

### 20.1 `InformacionCritica/barrido-n1-expertos.py` v1.0 (+ `BARRIDO-N1.bat`)

- **14 configs en 4 bloques**, todas traducidas de ESTE documento: bloque EXP sobre la base campeona del barrido-30 (`-cmoe` + `-ngl 99` + `-lm none`, comparable 1:1 con 21.53 [M]): D-ANCLA, D-EXP10-CTRL, D-EXP8, D-EXP6, D-EXP5, D-EXP4, D-EXP3, D-EXP2 (§5/§6); bloque UB1K: D-EXP4-UB1K (§6.4, tokens id 32 verbatim del barrido-30); bloque MEC sobre NCM37C4 (tokens id 14 verbatim, 22.49 [M]): D-NCM37C4-MEC0 (control), D-MEC-512, D-MEC-1024, D-MEC-768 (§15, orden final); bloque COMBO: D-EXP4-NCM37C4 (§8). CLI: `--quick` (7 críticas), `--solo exp,ub1k,mec,combo`, `--extra-k`, `--si`.
- **Corrección del no-op materializada (§4/§11.1)**: parser GGUF propio (stdlib, sin pip) lee `general.architecture` del archivo REAL y arma UNA clave `<arch>.expert_used_count=int:K`. Nunca más `qwen3moe.*` a ciegas. Si el parser falla, el script ABORTA (nada se asume).
- **Autenticador obligatorio (§12.2)**: grep `n_expert_used = N` del log del server por run; si ≠ dosis pedida → run INVALIDO (`override_aplicado=NO`, `valido=NO`), no computa.
- **Segundo autenticador (§12.6)**: `CUDA0 compute buffer size` registrado por run (debe bajar con k; confirma la dosis por vía independiente del t/s).
- **Auditoría de flags integrada (encargo explícito del Director)**: antes de arrancar, decodifica `llama-flags-nuevo.txt` (dump UTF-16 b11856, fuente de verdad #1) y verifica CADA token de CADA config verbatim; valida valores legales (modos `-lm`, tipos KV sin turbo*, `-fa on|off|auto`), prohibidas (`--mlock`, `-nkvo`, `-ub 512`, `--spec-*`, flags muertas) y requeridos (`--override-kv`, `--moe-cache-mib`, `-ncmoe`...). Cualquier fallo → ABORTA sin tocar el server.
- **Protocolo de medición de la casa (aprendido §8)**: 4 pasadas × 256 tokens, 4 prompts DISTINTOS misma familia, temp 0, seed fija, `cache_prompt`, se descarta la 1ª, decode = media 2-4, prefill = pasada 1 fría, pausas térmicas 60 s cada 8, CSV reanudable (resume por proto), guardarrail `/health` (aborta si hay server vivo).
- **MEC reconciliado con aprendido §2**: el veneno medido (256/512 MiB sobre la base vieja) NO se repite; MEC corre SOLO sobre NCM37C4 (fit + KV q4_0 + ctx 4k liberan VRAM) y SOLO con control D-MEC-0 en la MISMA sesión; la dosis 256 ni se prueba; si una dosis pierde vs control → el informe la descarta (regla §15).
- **Sanity automática de 3 pares** (17×23 / Don Quijote / planeta rojo) por config + VRAM por `nvidia-smi` (aviso >3700 MiB) + detección de fit-abort y avisos sysmem. La puerta de calidad COMPLETA (20 prompts manuales del Director, §5) sigue siendo paso humano posterior.
- **Informe autónomo**: `faseD-N1-INFORME.md` evalúa SOLO el árbol de decisión §11.4 (dosis viva / banda no domina / build ignora → plan B RUTA 0), veredicto MEC vs control y recuerdos de casa. Salidas en `D:\ZLia\faseD-logs\`: INFORME + `faseD-N1-resultados.csv` + `faseD-N1-datos.json` + `faseD-N1-consola.log` + `logs-config/NN-nombre.log`. Pre-vuelo: pin del server (build 11856), bytes del modelo (14,273,277,376 B), hparams del GGUF (256/8).
- **Validación**: `scripts/test_faseD_n1.py` — 30/30 VERDE con server falso (parser GGUF sintético v3 con salto de arrays de 5.000 tokens, dump sintético UTF-16, E2E de 8 configs, control EXP10 frena, override ignorado → runs inválidos + plan B, resume, MEC vs control, informe sin códigos ANSI).

### 20.2 Qué NO cambia

Dosis de fase D SIN CAMBIOS (NCM37C4 + D-MEC-0/512/1024/768 + escalera EXP6→4→3, con EXP5 y EXP2 informativas y el run autenticador cruzado `-ot` de §18 disponible). Expectativas [T] de §5 intactas. El instrumento añade como medidas explícitas D-EXP4-UB1K (§6.4) y D-EXP4-NCM37C4 (combo del stack §8); nada más.

## 21. ANEXO — Ronda 14: auditoría total del instrumento v1.1 tras el HTTP 400 real (2026-10-27)

Contexto: el Director ejecutó la v1.0 en su rig real (`D:\ZLia\barrido-n1-expertos.py`, 14 configs, puerto 9931). El parser GGUF y la auditoría de flags pasaron (arch leído del GGUF real, VERDE 14 configs), pero la PRIMERA pasada de medición de D-ANCLA murió con `urllib.error.HTTPError: HTTP Error 400: Bad Request` y traceback crudo: sin CSV, sin informe, sin diagnóstico. Encargo del Director: "hazle una auditoría total cazando todos los bugs posibles y súbelo a git". Este anexo registra la auditoría (NADA cambia en las dosis ni en las conclusiones de §0-§20).

### 21.1 Causa raíz (lectura línea a línea + prueba T13)

La v1.0 lanzaba el server con SOLO los flags diff de cada config: `medir_config` llamaba a `lanzar_server(ruta_server, cfg["flags"])` SIN fusionar `BASE_FLAGS_FIJAS`, y esa base además NO incluía `-m`. D-ANCLA quedaba como `llama-server.exe -cmoe`: sin modelo, sin `--port 9931`, sin `-c 16384`, sin `-fa`, sin KV q8_0, sin `-lm none`. El server que respondía en el puerto no podía ser el nuestro; su `/completion` rechazó el POST con 400 — y la v1.0 DESCARTABA el cuerpo del error (`HTTPError.read()` nunca se llamaba), así que el 400 quedó sin diagnóstico y la excepción mató el barrido entero. Dos bugs encadenados: lanzamiento incompleto + diagnóstico tragado. Lección de instrumentación: **el cuerpo de un error HTTP es oro; descartarlo convierte un bug de 1 línea en un misterio de 1 día**.

### 21.2 Las 10 correcciones de la v1.1 (proto `faseD-N1-v2`)

1. **CRÍTICO (causa raíz)**: comando lanzado = SIEMPRE `server -m <modelo> <BASE_FLAGS_FIJAS> <diff de la config>` — el diff va al final y gana (llama.cpp deja ganar al último valor). El CSV registra ahora el comando COMPLETO por fila (reproducibilidad 1:1).
2. **Cuerpo de error HTTP capturado** (`_post_json`): cualquier 4xx/5xx llega con el mensaje del server en consola + nota del CSV + JSON. Un 400 ya no es un misterio.
3. **Una config nunca tumba el barrido**: fallo HTTP/conexión → fila NO-VALIDA al CSV, se sigue con la siguiente; el informe se genera igualmente. Reintentos SOLO para transitorios (5xx/429/conexión, 2 intentos con espera); los 4xx fallan de inmediato (reintentar un pedido mal hecho no ayuda).
4. **Identidad del server verificada por su log**: si el log del server no menciona el basename del modelo esperado → config invalidada sin medir (nunca medir un server fantasma/watchdog que se cuelgue del puerto). Aviso suave si el log no confirma `listening on` en el puerto pedido.
5. **Muerte del server a mitad de medición** detectada por exit code (`proc.poll()` en cada pasada) — antes era un timeout ciego de 600 s.
6. **Resume v2**: solo las filas SI cuentan como hechas; las NO se re-miden (la v1.0 habría saltado PARA SIEMPRE una config fallida).
7. **La auditoría de flags cubre TAMBIÉN la base**: la v1.0 solo miraba el diff — el "VERDE" de la corrida real nunca había auditado `-ngl/-fa/-ctk/-ctv/-lm/--port`.
8. **consola.log SIEMPRE sin ANSI** (el Tee elimina códigos de color en el archivo); consola Windows con VT habilitado (`os.system("")`) — la v1.0 pintaba basura `[96m` en cmd.
9. **stderr también al log** (los tracebacks entran en consola.log); **Ctrl+C** guarda informe parcial y permite reanudar (rc 130); excepción no capturada en una config → fila de fallo, no crash.
10. **Parser GGUF con buffer de 1 MiB** (los arrays de ~248k tokens del vocab real se saltan mucho más rápido) + `sanity_chat` con timeout 240→120 s que corta al primer fallo de conexión + `taskkill` protegido fuera de Windows.

### 21.3 Validación: 42/42 VERDE (`scripts/test_faseD_n1.py` ampliado)

Nuevos checks de regresión: **T13** el comando lanzado trae `-m <modelo> -ngl 99 -c 16384 ... --port ... -cmoe` con el diff al final (prueba directa de la causa raíz, vía log RECIBIDO del server falso); **T14** server sin línea de modelo en su log → 8 filas NO con nota de identidad, sin medir nada; **T15** regresión EXACTA del desastre: server que responde 400 → el barrido sobrevive con rc 0, 8 filas NO con el cuerpo `{"error":...}` capturado en la nota, informe generado; **T16** server que muere en la carga → filas NO con exit code; **T17** resume re-mide las 8 fallidas (CSV 16 filas, las nuevas SI); **T18** consola.log sin ANSI aunque USE_COLOR esté activo. Los 30 checks originales siguen verdes (T02 parser ahora en 0.00 s). Durante la propia batería los tests cazaron un bug más de la v1.1-intermedia: una medición que fallaba aún se marcaba VALIDO → corregido (`valido = False` en los dos ramos de excepción) y cubierto por T17.

### 21.4 Qué NO cambia y cómo relanzar

- **Dosis de fase D SIN CAMBIOS** (§20.2 en pie). El fallo era del LANZAMIENTO, no de las dosis, ni de las claves, ni del parser: el parser leyó el arch del GGUF real (`qwen35moe`, sin guiones bajos — NÓTESE: la lección del barrido-30 anticipaba `qwen3_5_moe`; la forma exacta la dicta el archivo y los autenticadores deciden) y la auditoría de flags ya era verde.
- **Los autenticadores cubren cualquier duda sobre el arch**: si el build normalizara el arch internamente o el override no aplicara, `n_expert_used = N` no aparecería en el log → run INVALIDO por §12.2, y el control EXP10 que debe frenar (~-6.5%) expondría un no-op aunque el log dijera lo contrario (§11.4). El instrumento es autocorrector en la misma corrida.
- **Relanzamiento**: copiar el `barrido-n1-expertos.py` v1.1 actualizado a `D:\ZLia\` y ejecutar `BARRIDO-N1.bat`. El proto nuevo (`faseD-N1-v2`) ignora CSVs viejos → re-corrida completa (la v1.0 no llegó a escribir ninguna fila, no se pierde nada).
- Si reaparece un 400, la nota dirá QUÉ respondió el server (contexto, endpoint, slot...): diagnóstico en la primera línea en vez de un misterio.
