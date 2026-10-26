# NIVEL 2 — CUANT MÁS LIGERO YA HECHO (descarga, sin requant local)

Proyecto APEX-I-MINI / Qwen3.6-35B-A3B | Rig: i3-10100F (4C/8T) + 16 GB DDR4 dual + GTX 1650 4GB
Fecha: 2026-10-26 | Investigación profesional profunda | Nivel 2 de 3 ("hacer el modelo más ligero sin complicar")

Etiquetas: **[F]** = verificado en fuente externa (URL abajo) · **[M]** = medido en ESTE rig · **[T]** = derivado/matemática propia · **[N/D]** = sin datos hoy

Regla del proyecto respetada: **no requantizamos nada en este rig** (decisión del Director). Todo este nivel son descargas de cuants ya hechos por terceros — permitido explícitamente.

---

## 0. Veredicto ejecutivo

1. **El peldaño inferior del APEX-I-MINI ya existe y está disponible HOY**: `unsloth/Qwen3.6-35B-A3B-GGUF` → **`Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf`, 13.2 GB** [F]. Es un −7.5% de tamaño → **~+8% t/s** [T] y libera ~1.05 GB de RAM.
2. **Sorpresa del benchmark independiente**: oobabooga (localbench) midió 64 cuants del 3.6 de 6 uploaders contra BF16 y **mudler/APEX (nuestro uploader actual) nunca aparece en la frontera Pareto** [F]. Unsloth domina (14/26 posiciones de frontera). Es decir: bajar de APEX-I-MINI a UD-IQ3_XXS probablemente no solo acelera — **probablemente también MEJORA la calidad por byte**.
3. **Abajo de IQ3_XXS el suelo se rompe rápido**: Q2_K_XL es territorio de test con mitigaciones; IQ2_XXS y 1-bit son NO-GO para uso agéntico (cliff KLD ×2–3 medido en el gemelo 3.5 [F]; breaking de tool-calling/loops documentado por Unsloth [F]).

---

## 1. Teoría mínima profesional: qué es exactamente lo que bajamos

**bpw y familias.** Un GGUF guarda los pesos en bloques con escalas. Las familias [F, dwarez/kaitchup]:
- *K-quants* (Q2_K…Q8_0): escalas jerárquicas por super-bloque; los sufijos S/M/L mezclan precisión por tipo de tensor.
- *I-quants* (IQ1…IQ4): por debajo de ~3 bits ya no bastan escalas — entra un **codebook** (tabla de niveles no uniformes). IQ3_XXS = 2.0625-ish×(3bit family) con codebook, ~3.3 bpw efectivo en la práctica.
- **imatrix**: matriz de importancia calculada con datos de calibración; pondera el error donde el modelo más lo siente. Sin imatrix, un IQ3 de baja calidad es peor que un Q3_K_M [F].

**UD (Unsloth Dynamic) 2.0/3.0** [F]: asignación dinámica de bits por capa/tensor (capas críticas a más bpw, cola a menos), con imatrix de alta calidad curada (300K–1.5M tokens, chat/agéntico/multilingüe, sin entrenar sobre el dataset, sin QAT). Dynamic 3.0 (Qwen3.8) reporta >10% top-1 extra a igual tamaño vs otros proveedores.

**Cómo se mide la pérdida: KL-divergence (KLD)** [F, unsloth docs]: divergencia entre la distribución de logits del cuant y la del BF16 sobre tokens reales. Referencias útiles: KLD < 0.1 imperceptible; 1–2 = ligero; 3–4 = notable; y ojo — Wikipedia como test infla scores (overfitting de calibración); los benchmarks serios usan tareas reales (oobabooga: 250K tokens de coding/chat/tool-calling/ciencia/no-latin/long-docs).

**Por qué un MoE colapsa a 2 bits** [T+F]: cada experto tiene solo 3.15 M de parámetros y dim intermedia 512 — poco margen para promediar el error de cuant; además el router amplifica errores pequeños de logits. Unsloth documenta que bajo UD-Q2_K_XL el comportamiento agéntico se rompe (loops; mitigación `presence_penalty=1.5`) y que quitan el módulo MTP de los cuants pequeños para ahorrar ~500 MB [F].

---

## 2. La escalera completa de este modelo (datos medidos por terceros)

Escalera Unsloth del gemelo **Qwen3.5-35B-A3B** (misma arch `qwen3_5_moe`) [F, unsloth docs "Qwen3.5 GGUF Benchmarks"]:

| Cuant | GB | Perplejidad | KLD 99.9 | Lectura |
|---|---|---|---|---|
| IQ2_XXS | 9.09 | 7.716 | 4.2221 | **cliff ×3** — NO-GO |
| Q2_K_XL | 12.04 | 7.0438 | 2.9092 | cliff ×2 — solo test con mitigaciones |
| **IQ3_XXS** | **13.12** | **6.7829** | **1.5296** | **el peldaño objetivo (+0.11 KLD vs actual)** |
| IQ3_S | 14.13 | 6.7715 | 1.4193 | ≈ densidad del APEX-I-MINI actual (14.27 GB [M]) |
| Q3_K_XL | 16.06 | 6.7245 | 0.9539 | más grande que hoy: no aporta |
| Q4_K_XL | 19.17 | 6.5918 | 0.4097 | no cabe cómodo en 16 GB RAM |

Comparativa entre uploaders (misma escalera 3.5) [F]: el IQ3_XXS de **bartowski** tiene KLD 2.1563 (¡vs 1.5296 de Unsloth!) — la marca importa tanto como el nivel. Para el **3.6** oobabooga midió 64 cuants/6 uploaders contra BF16 [F, localbench]: Qwen3.6 cuantiza MEJOR que 3.5 (Q8_0: KLD 0.069 vs 0.121), unsloth domina la frontera, **mudler/APEX nunca en frontera**, tool-calling es la categoría que peor cuantiza (KLD 0.177 incluso a Q8_0), y hasta UD-IQ1_M (10 GB) retiene 86.9% top-1 (pero no sirve para agéntico [F unsloth]).

---

## 3. El candidato concreto: UD-IQ3_XXS del 3.6 (disponible hoy)

- Repo: `unsloth/Qwen3.6-35B-A3B-GGUF` — archivo `Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf`, **13.2 GB** [F, file listing]. Release de cuants 3.6: Abr-2026.
- Descarga (un archivo, HF CLI o curl):
  ```
  hf download unsloth/Qwen3.6-35B-A3B-GGUF Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf --local-dir D:\ZLia\models
  ```
- KLD específico del 3.6 para IQ3_XXS: **[N/D]** en la tabla pública (la tabla fina de oobabooga está tras suscripción) — pero su titular es que unsloth tiene el mejor KLD-vs-disco del 3.6 y el análogo 3.5 marca KLD 1.53 (+0.11 sobre el IQ3_S actual): **pérdida esperada despreciable** [T].
- **Módulo MTP dentro del GGUF**: para Qwen3.8, Unsloth solo lo quita en quants ≤ UD-Q2_K_XL [F]; en UD-IQ3_XXS del 3.6 lo esperable es que VENGA incluido [T] — **verificar al descargar con el parser del barrido** (fase E busca `nextn.*`): si está, el GGUF del Nivel 2 habilita de paso el draft-mtp de la fase E sin descarga extra. Si no: plan B draft separado (ya documentado en el worklog).

---

## 4. Matemática del rig: qué gana exactamente [T]

- Bytes/token: todos los pesos bajan ~7.5% proporcionalmente (routed y no-routed) → tráfico ~1.5 → ~1.39 GB/token → **21.5 → ~23.2 t/s (+8%)**.
- **RAM: 14.27 → 13.2 GB = ~1.05 GB liberados**. En un rig con 16 GB y Windows encima, ese gigabyte es el margen que faltaba para: (a) `--cache-ram` de 512–1024 MiB sin pelear con el modelo, (b) el draft MTP (+~2 GB seguiría sin caber cómodo — para eso el Nivel 1 no basta solo, ver stack), (c) mayor contexto estable.
- Colocación intacta: `-cmoe`/`-ncmoe` y `-ngl` funcionan igual; el fit de VRAM tiene MÁS margen (el bloque no-routed también adelgaza).
- Carga: −1 GB menos de disco→RAM ≈ −2–3 s de load_s [T].

## 5. ¿Y si bajamos más? (Q2_K_XL e IQ2 — mapa honesto)

| Peldaño | GB | t/s esperado [T] | Riesgo | Veredicto |
|---|---|---|---|---|
| UD-IQ3_XXS | 13.2 | ~23.2 (+8%) | KLD +0.11 [proxy 3.5] | **GO** |
| UD-Q2_K_XL | ~11.9 | ~24.8 (+15%) | KLD ×2; tool-calling ya es la categoría más frágil del 3.6 [F]; loops agénticos [F unsloth] | TEST opcional con sanity de tool-calling |
| UD-IQ2_XXS | ~9.0 | ~27.5 (+28%) | cliff ×3 [F]; incoherencia esperada | NO-GO |
| IQ1_M | ~10.0 | ~25.8 | 86.9% top-1 pero agéntico roto [F] | NO-GO |

La física manda: el escalón IQ3_S→IQ3_XXS es el último con "gratis" real; debajo, cada punto de t/s se paga con multiples de KLD [F/T].

## 6. La otra descarga que compite: vocab-trimming (frontera N1/N2)

`Elsephire/Qwen3.6-35B-A3B-vocabulary-trimming-GGUF`: vocabulario recortado −41.3% manteniendo lenguas latinas (EN/FR/DE/**ES**/IT/PT/NL/PL) [F]. Mecánica [T]: el LM head es 248320×2048 ≈ 0.21 GB leídos POR token (~15% del presupuesto de banda). Recortar 41% del vocab → **+6–7% t/s**, y de paso abarata un futuro draft (FR-Spec: el coste del draft es proporcional al vocab [F issue #25187]). El tamaño del archivo casi no cambia (los embeddings dominan). Cuidado: cualquier carácter fuera de las lenguas preservadas degrada [F implícito]; para uso ES/PT del Director es ideal por diseño.

## 7. REAP-50 (si se quiere "más ligero" de verdad, sacrificando)

REAP-50 canónico retiene 97.6% coding / 96.7% SWE-Bench [F Cerebras]; hay build del 3.6 (`anik-jha/...-coding-reap50-GGUF`, tamaño [N/D]) [F]. Al podar expertos GLOBALMENTE sí baja el archivo y la RAM (a diferencia de N1). Requiere sanity gates estrictos y es un salto de riesgo frente a IQ3_XXS; REAP-90 está auto-etiquetado "meme" incoherente [F]. Posición en la escalera personal: solo después de cosechar N1+N2+E.

## 8. Protocolo de validación en este rig

1. **Descargar** UD-IQ3_XXS (§3) y vocab-trim (§6) si se quiere probar ambos.
2. **Autenticar el GGUF**: correr el parser del barrido-total (fase E lo usa) para confirmar arch `qwen3_5_moe`, `expert_used_count=8`, y presencia de tensores `nextn.*` (MTP) en el archivo nuevo.
3. **Medir**: fase B (re-ancla) + fase C del barrido-total con el GGUF nuevo (mismos prompts; comparar decode/prefill/load contra el ancla del APEX-I-MINI).
4. **Sanity de calidad 20-prompt**: 10 chat ES, 5 código, **5 tool-calling** (la categoría más frágil [F]). Comparar salidas vs APEX-I-MINI lado a lado. Aceptar si no hay regresión visible.
5. **A/B de marca**: si algún día se duda, repetir el sanity contra `UD-IQ3_S` de unsloth (14.13 GB): si UD-IQ3_S gana el sanity y queda a ~0 t/s del APEX, la marca sola justifica el cambio [T].

## 9. Riesgos y límites

- KLD del IQ3_XXS **del 3.6** no publicado en abierto [N/D] — mitigado por el benchmark 3.5-análogo y el ranking localbench [F].
- Tool-calling cuantiza peor que todo lo demás en este modelo [F localbench] → el sanity debe incluirlo sí o sí.
- Espacio en disco D: ~13.2 GB + modelo actual; limpiar si no cabe.
- Vision/mmproj: si se usa la parte multimodal, verificar que el repo incluya mmproj compatible [N/D — no lo usamos hoy].
- **No existe** (a fecha de hoy) un cuant 3-bit de APEX/mudler mejor posicionado que unsloth según la frontera medida [F].

## 10. Vigilancia (cosas que pueden mejorar esta escalera pronto)

- **MoQ ("Mixture of Quants")** [F kaitchup Jun-2026]: mixed-precision por "elasticidad de tensor", ya produce GGUFs que baten a Unsloth a igual tamaño; soporte de 2-bit/3-bit aún limitado en engines. Cuando haya MoQ del 3.6 a 3-bit: candidato directo.
- **GSQ (ISTA-DASLab)** [F]: refinamiento de low-bit con Gumbel-Softmax; pipeline futuro MoQ+GSQ.
- **OpenDynamicGGUF** [F]: variante abierta/reproducible del concepto UD.
- UD-IQ3_XXS/Q2_K_XL con MTP separado tipo "Q4_0 MTP module" (patrón Qwen3.8) [F] — vigilar repo unsloth del 3.6.

## 11. Referencias

- Repo y UD-IQ3_XXS 13.2 GB: https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF (file: Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf)
- Escalera KLD 3.5: https://unsloth.ai/docs/models/qwen3.5/gguf-benchmarks
- localbench 3.6 (64 cuants, 6 uploaders, APEX fuera de frontera): https://localbench.substack.com/p/qwen-36-35b-a3b-gguf-quality-benchmark · hilo: https://www.reddit.com/r/LocalLLaMA/comments/1so5nrl/
- Unsloth Dynamic 3.0 (mitigaciones 2-bit, MTP aparte): https://unsloth.ai/docs/basics/dynamic-3.0-ggufs · Dynamic 2.0: https://unsloth.ai/blog/dynamic-v2
- Anatomía GGUF bit a bit: https://dwarez.dev/blog/gguf-quantization-bit-by-bit · guía nombres: https://scalastic.io/en/ai-model-formats-gguf-quantization-explained
- MoQ/GSQ: https://kaitchup.substack.com/p/moq-ggufs-and-gsq-low-bit-ggufs-are
- Vocab-trim del 3.6: https://huggingface.co/Elsephire/Qwen3.6-35B-A3B-vocabulary-trimming-GGUF · REAP-50: https://huggingface.co/anik-jha/Qwen3.6-35B-A3B-coding-reap50-GGUF
- FR-Spec (coste draft ∝ vocab): issue https://github.com/ggml-org/llama.cpp/issues/25187
- Datos propios: ancla 21.53 t/s, APEX-I-MINI 14.27 GB [M]
