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

---

## 12. ANEXO — Segunda ronda: inventario exacto de HF vía API (2026-10-26) [F]

### 12.1 Tamaños exactos del repo unsloth (texto, sin mmproj)

Leído por API de HF (`/tree/main`), bytes exactos:

| Cuant | GB | Comentario |
|---|---|---|
| UD-IQ1_M | 10.05 | NO-GO agéntico [F unsloth] |
| UD-IQ2_XXS | 10.76 | NO-GO (cliff) |
| UD-IQ2_M | 11.52 | NO-GO (cliff) |
| UD-Q2_K_XL | 12.29 | solo test con mitigaciones |
| **UD-IQ3_XXS** | **13.21** | **el peldaño GO (+8% t/s [T])** |
| **UD-IQ3_S** | **13.68** | **REVELACIÓN: 0.59 GB MENOR que el APEX-I-MINI (14.27) a la MISMA densidad** |
| UD-Q3_K_S | 15.36 | no aporta (más grande que hoy) |
| UD-Q3_K_M / UD-Q3_K_XL | 16.60 / 16.85 | no caben cómodos |
| UD-IQ4_XS | 17.73 | fuera |
| MXFP4_MOE | 21.71 | fuera |
| Q8_0 | 36.90 | referencia |

mmproj (visión) van aparte: F16 0.90 GB — no se necesita para uso de texto.

### 12.2 REVELACIÓN 1: el cambio "sin bajar peldaño"

UD-IQ3_S (13.68 GB) es IQ3_S como el APEX-I-MINI (14.27 GB): **−0.59 GB (−4%) a calidad superior por la frontera localbench [F]** (mudler/APEX nunca en frontera). Cambio de marca "gratis": +4% t/s [T] y sanea RAM sin tocar la escalera. Opción conservadora si IQ3_XXS asustara.

### 12.3 REVELACIÓN 2: el repo MTP de unsloth con UD quants (para fase E en una descarga)

`unsloth/Qwen3.6-35B-A3B-MTP-GGUF` EXISTE (API verificada) y trae la cabeza nextn DENTRO de los UD quants:

| Cuant con MTP | GB | vs sin MTP |
|---|---|---|
| **UD-IQ3_XXS-MTP** | **14.07** | +0.86 GB (módulo nextn) |
| UD-IQ3_S-MTP | 15.35 | +1.67 |
| UD-Q2_K_XL-MTP | 12.57 | +0.28 |
| UD-IQ2_XXS-MTP | 11.82 | +1.06 |

**La descarga única soñada**: UD-IQ3_XXS-MTP = 14.07 GB ≈ el footprint RAM del APEX-I-MINI actual (14.27), con cuant mejor (frontera [F]) y MTP incluido → habilita `--spec-type draft-mtp` (×1.28–1.4+ [F]) sin segunda descarga. La tabla de requisitos MTP de unsloth [F]: 35B-A3B 3-bit = **18 GB combinados** (rig: 16 RAM + 4 VRAM = 20 ✓ cabe).
El repo oficial ggml-org MTP solo trae BF16 (66.21) y Q8_0 (35.21 GB) [F] — confirmado: la vía 3-bit MTP es la de unsloth.
Verificación al descargar: el parser del barrido (fase E) debe ver los tensores `nextn.*` en el GGUF.

### 12.4 Guía MTP de unsloth para el 3.6 [F]

- "llama.cpp has merged MTP support" (ya no experimental).
- `--spec-draft-n-max 2` funciona mejor "en la mayoría de setups", PERO "no asumir: probar 1 a 6" — coincide con el protocolo T2 del tester-mtp.
- MTP usa ~1 GB extra de RAM/VRAM de margen.
- Referencia: 35B-A3B a 240 t/s en RTX 6000 (techo de hardware muy superior; aquí esperamos 27–36 [T]).

### 12.5 Aviso de hardware/software: CUDA 13.2 roto [F]

Reddit oficial de unsloth (danielhanchen): **CUDA 13.2 genera gibberish en cuants low-bit de todos los modelos** (NVIDIA lo confirmó; fix en 13.3; workaround: usar CUDA 13.1). Acción del rig: comprobar qué CUDA lleva el build b11856 (log de arranque del server / DLLs); si es 13.2, juzgar un IQ3 con cuidado y considerar toolkit 13.1 antes de descartar calidad.

### 12.6 Decisión sugerida actualizada

1. Descargar **UD-IQ3_XXS-MTP (14.07 GB)** → A/B contra APEX-I-MINI (fase B + sanity tool-calling).
2. Si el MTP aprieta la RAM en el arranque real: plan B = UD-IQ3_XXS (13.21) + draft MTP separado más adelante.
3. Cambio mínimo sin riesgo: UD-IQ3_S (13.68) si se quiere solo "misma IQ, menos bytes".

---

## 13. ANEXO — Tercera ronda: bytes exactos, SHA256, correcciones y restricciones MTP (2026-10-26)

### 13.1 Bytes exactos y hash de los candidatos (API de HF, verificado hoy) [F]

Repo `unsloth/Qwen3.6-35B-A3B-GGUF` (sin MTP):

| Archivo | Bytes exactos |
|---|---|
| **UD-IQ3_XXS** | **13,211,155,424** |
| UD-IQ3_S | 13,676,723,168 |
| UD-Q2_K_XL | 12,290,628,576 |
| UD-IQ1_M / UD-IQ2_XXS / UD-IQ2_M | 10,047,749,088 / 10,756,586,464 / 11,522,702,304 |
| UD-Q3_K_S | 15,359,196,128 |

Repo `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` (nextn DENTRO de cada cuant, 21 cuants):

| Archivo | Bytes exactos | SHA256 (lfs.oid) |
|---|---|---|
| **UD-IQ3_XXS** | **14,069,266,720** | `36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012e3d9e2495a90e7a7150` |
| UD-IQ3_S | 15,346,432,288 | `ab639a7f...f27f9` (primeros: ab639a7f330f) |
| UD-Q2_K_XL | 12,574,128,416 | `ed7cda7e...0ca9e` |
| UD-IQ2_XXS | 11,819,399,456 | `627e2b05...c0013` |
| UD-IQ1_M | 11,366,414,624 | `223db8b3...ddc14` |

- **Tamaño del módulo nextn, medido por diferencia de bytes** [T sobre datos F]: UD-IQ3_XXS: 14,069,266,720 − 13,211,155,424 = **858,111,296 B (0.86 GB)**; UD-IQ3_S: **1,669,709,120 B (1.67 GB)**. El módulo MTP se cuantiza al mismo nivel que el resto — por eso crece en cuants mejores.
- `imatrix_unsloth.gguf_file` (192,223,904 B): es la matriz de calibración, SOLO para quien re-cuantiza — **no descargar**.
- mmproj (visión): F16 = 899,283,584 B — aparte, innecesario para uso de texto.

### 13.2 Protocolo de descarga con verificación de integridad [F método]

```
hf download unsloth/Qwen3.6-35B-A3B-MTP-GGUF Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf --local-dir D:\ZLia\models
certutil -hashfile D:\ZLia\models\Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf SHA256
```
→ El hash debe salir `36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012e3d9e2495a90e7a7150`. Si la descarga se corta, `hf download` retoma (re-ejecutar el mismo comando); verificar hash SIEMPRE antes de borrar el APEX original.

### 13.3 CORRECCIÓN: el vocab-trim NO es viable en este rig [F nuevo — deroga §6]

Verificado por API: el repo `Elsephire/Qwen3.6-35B-A3B-vocabulary-trimming-GGUF` contiene UN SOLO GGUF:

- `qwen3.6-35B-vocabulary-trimming-MTP-Q4_K_S.gguf` = **20,070,193,920 B (20.07 GB)**.

Es decir: el vocab-trim publicado NO es 3-bit sino **Q4_K_S (con MTP dentro)** → 20.07 GB > 16 GB de RAM → **NO-GO por RAM en este rig**. El "+6–7% t/s" de §6 quedaba condicionado a un vocab-trim a ~3 bits: **no existe hoy** [N/D]. La opción se retira de la escalera hasta que alguien publique un vocab-trim 3-bit. (La matemática §6 sigue siendo válida como concepto; lo que falla es el artefacto disponible.)

### 13.4 REAP-50 aterrizado en bytes: NO es upgrade de t/s en este rig [F bytes + T lectura]

- `anik-jha/Qwen3.6-35B-A3B-coding-reap50-GGUF`: **Q4_K_M-imat = 11,373,058,080 B (11.37 GB)**; Q5_K_M-imat = 13,257,709,600 B (13.26 GB). (Llena el [N/D] de §7.)
- Lectura de banda [T]: REAP-50 deja los expertos en 128 pero los cuantiza a Q4_K_M (~4.85 bpw) — los componentes densos suben de 3.26 → 4.85 bpw. Presupuesto aproximado: routed activos ~0.31 GB + densos ~1.02 GB + lm_head 0.21 + shared 0.05 ≈ **1.6 GB/token > 1.45 del APEX actual** → en este rig bandwidth-bound, REAP-50-Q4_K_M sería MÁS LENTO que el cuant actual a pesar de pesar 3 GB menos. Es un recorte de RAM/calidad, NO de velocidad. Posición en la escalera (§7) queda aún más rezagada.

### 13.5 Restricciones oficiales del MTP, del README del repo [F]

El README de `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` da el comando de referencia:

```
llama-server -hf unsloth/Qwen3.6-35B-A3B-MTP-GGUF:UD-Q4_K_XL \
  -ngl 99 -c 8192 -fa on -np 1 \
  --spec-type draft-mtp --spec-draft-n-max 2
```

Y declara dos límites DUROS:

1. **`-np > 1` no está soportado aún con MTP** → con fase E activa, `-np 1` obligatorio (impacto directo en el combo del Nivel 3: el +14% de slots solo aplica sin MTP).
2. **`--mmproj` no soportado con MTP** → irrelevante para nosotros (sin visión).

Claim del uploader [F]: "MTP enables ~1.5–2× faster inference with no accuracy loss". Nuestro techo conservador sigue siendo ×1.28–1.4 [T] hasta medir en el rig.

Nota del comando oficial: usa `-c 8192` — con 14.07 GB en 16 GB de RAM, es la señal correcta: el contexto grande es el primer gasto a recortar. La familia entrena a 262,144 de ctx [F log issue #24055] — nuestro -c es presupuesto nuestro, no límite del modelo.

### 13.6 Presupuesto RAM exacto con UD-IQ3_XXS (con y sin MTP) [T]

| Escenario | Modelo | Libre en 16 GB (antes de SO ~2.5–3 GB) | Lectura |
|---|---|---|---|
| HOY (APEX-I-MINI) | 14.27 GB | ~1.7 GB | apretado (es el statu quo) |
| UD-IQ3_XXS | 13.21 GB | ~2.8 GB | cómodo: cache-ram 512–1024 OK |
| UD-IQ3_XXS + MTP | 14.07 GB | ~1.9 GB | apretado: `-c 8192`, `--cache-ram 256–512`, sin mlock, sin mmproj |
| UD-IQ3_S + MTP | 15.35 GB | ~0.6 GB | NO cabe con MTP activo → solo sin MTP |

Si el escenario MTP aprieta en el arranque real (pagina el SO): bajar `-c` a 4096, o volver al plan B (13.21 sin MTP + draft después).

### 13.7 Cómo saber qué CUDA lleva el build b11856 (para el aviso 12.5) [T método]

El log del server imprime `system_info: ... | CUDA : ARCHS = ... | USE_GRAPHS = 1 | ... | REPACK = 1` pero NO la versión del toolkit [F formato de log issue #24055]. Métodos prácticos en orden de fiabilidad:

1. **El nombre del ZIP de release** que se descargó: los assets de llama.cpp se publican como `llama-bXXXX-bin-win-cuda-cu13.2-x64.zip` (la versión va en el nombre) [T patrón de naming; buscar el zip en la carpeta de descargas del Director].
2. DLLs del bin: `cudart64_13.dll` (CUDA 13.x) vs `cudart64_12.dll` [T].
3. `nvidia-smi` (máxima versión de CUDA soportada por el driver) + `echo %CUDA_PATH%` / `nvcc --version` si hay toolkit instalado.

Si resulta ser cu13.2: el gibberish low-bit documentado (§12.5) aconseja re-descargar release cu13.1 antes de juzgar la calidad del IQ3_XXS.

### 13.8 Estado de la vigilancia (§10) tras esta ronda

- FR-Spec para MTP nativo: la infraestructura `d2t` ya existe en EAGLE-3 del propio llama.cpp; la propuesta (issue #25187) con rama `avifenesh/llama.cpp/tree/frspec-mtp-vocab-trim` (commit 047bfa508, ~30 líneas) NO está fusionada [F]. Cuando se fusione Y exista un GGUF-MTP con `output.weight` recortado + tensor `d2t`, el coste del draft baja ~75% en su cabeza — para nuestro vocab de 248K es el multiplicador MTP más grande en el horizonte. Vigilar.
- `nextn.shared_head_head` confirmado como la tensor-cabeza que usa `qwen35moe.cpp` [F #25187] — es lo que el parser de fase E debe ver en el GGUF descargado (junto a `nextn.eh_proj/hnorm/enorm`).

**Referencias nuevas de esta ronda**: API tree repo MTP (bytes + sha256): https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/tree/main · API tree repo principal: https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main · README oficial MTP (comando y restricciones -np/mmproj): https://huggingface.co/unsloth/Qwen3.6-35B-A3B-MTP-GGUF · vocab-trim real (Q4_K_S 20.07 GB): https://huggingface.co/api/models/Elsephire/Qwen3.6-35B-A3B-vocabulary-trimming-GGUF/tree/main · REAP-50 bytes: https://huggingface.co/api/models/anik-jha/Qwen3.6-35B-A3B-coding-reap50-GGUF/tree/main · FR-Spec rama no fusionada: https://github.com/avifenesh/llama.cpp/tree/frspec-mtp-vocab-trim (issue https://github.com/ggml-org/llama.cpp/issues/25187).

## 14. ANEXO — Cuarta ronda: rehabilitación parcial del 2-bit y sinergia RAM (2026-10-26)

- **[F] Evidencia agéntica del 2-bit:** post oficial r/unsloth ("2-bit Qwen3.6-35B-A3B GGUF is amazing"): el UD 2-bit completó 30+ tool calls, búsqueda en 20 sitios y ejecución de Python con solo 13 GB de RAM. → El cliff KLD ×2-3 del proxy NO impide uso agéntico funcional; no dice nada de calidad de texto largo ni de ES.
- **Dosis nueva propuesta (regla "calidad sacrificable" del Director):** descargar unsloth UD-IQ2_XXS-MTP (11.82 GB [F API ronda 2]) → −2.25 GB de RAM vs APEX + MTP incluido en el mismo archivo → mata pageouts (N4) Y habilita la fase E con una sola descarga. Gates obligatorios: spot-check ES + sanity prompt + 1 tool-call real; y chequear CUDA toolkit del build ANTES (bug 13.2 roto para low-bit [F ronda 3] — IQ2 es el caso extremo).
- **Escalera de descarga por prioridad RAM:** UD-IQ3_XXS-MTP 14.07 GB (óptimo calidad, plan principal) → UD-IQ2_XXS-MTP 11.82 GB (sósia funcional, plan RAM) → UD-IQ1_M 86.9% top-1 [F ronda 2] solo emergencia.
- **Chequeo al momento de descargar:** revisar revisiones nuevas del repo unsloth (updates de imatrix) y si apareció un sidecar DSpark para 3.6 [N/D].
- **Coherencia:** REAP-50 Q4_K_M (11.37 GB) sigue descartado como vía de velocidad (≈1.6 GB/token a 4.85 bpw [F ronda 3] = más DDR4, no menos); su único valor sería calidad/byte, no t/s.

## 15. ANEXO — Quinta ronda: inventario MTP al byte completo (IQ2_M e IQ1_M nuevos), GSQ-RCO avanza (2026-10-26)

- **Inventario EXACTO del repo MTP vía tree API [F huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/tree/main]:** la lista completa de archivos con bytes (no redondeos). Los relevantes para el rig, ordenados por tamaño: **UD-IQ1_M 11.366.414.624 B** (11.37 GB — NUEVO, no estaba en el inventario de la ronda 3), UD-IQ2_XXS 11.819.399.456 B (11.82 ✓), **UD-IQ2_M 11.882.969.376 B** (11.88 GB — NUEVO, se sitúa entre IQ2_XXS y Q2_K_XL: +63 MB que IQ2_XXS), UD-Q2_K_XL 12.574.128.416 B (12.57 ✓), UD-IQ3_XXS 14.069.266.720 B (14.07 ✓ con **SHA256 re-confirmado 36f9ec0e…7150, idéntico a la ronda 3**), **UD-IQ3_S 15.346.432.288 B** (15.35 GB — NUEVO en inventario, ver riesgo abajo). Grandes: UD-Q3_K_M 17.10, UD-Q3_K_XL 17.23, UD-IQ4_NL 18.54, UD-IQ4_XS 18.21, UD-Q4_K_S 21.39, UD-Q4_K_M 22.66, UD-Q4_K_XL 22.85, MXFP4_MOE 22.18, Q5s 25.5-27.2, Q6s 30.0-32.6, Q8_0 37.80, UD-Q8_K_XL 39.10 GB.
- **Dosis de emergencia más barata que se creía:** UD-IQ1_M-MTP = **11.37 GB CON el nextn dentro** — y su ancla de calidad ya existe: localbench midió UD-IQ1_M al **86.9% top-1 vs BF16** [F ronda 2]. La ronda 4 lo describía como "solo emergencia" SIN MTP; ahora la misma calidad cabe en 11.37 GB con MTP incluido → sustituye a UD-IQ2_XXS-MTP (11.82) como peldaño mínimo si el frente RAM aprieta de verdad. UD-IQ2_M (11.88) es el peldaño intermedio formal entre IQ2_XXS y Q2_K_XL: +0.06 GB sobre IQ2_XXS por una densidad algo mejor de los tensores importantes [T según patrones UD; KLD propio N/D].
- **UD-IQ3_S-MTP = NO como primer paso [T sobre bytes F]:** 15.35 GB de archivo ⇒ ~11.4 GB en RAM con -ncmoe 37 (igual que hoy) pero si el plan A falla y todo va a CPU, la huella RAM sube ~1.3 GB sobre IQ3_XXS en un rig que ya opera a ~15.5/16 GB → pageouts probables. Queda inventariado para el caso "RAM ampliada a 20 GB".
- **mmproj e imatrix del repo [F tree]:** `mmproj-BF16.gguf` 902.822.528 B, `mmproj-F16.gguf` 899.283.584 B, `mmproj-F32.gguf` 1.786.305.152 B, `imatrix_unsloth.gguf_file` 192.223.904 B → **NO descargar ninguno**: el uso del rig es texto-only, `--mmproj` además NO está soportado con spec [F README MTP, ronda 3] → ahorrar 0.9-1.8 GB de disco y eliminar el riesgo de carga accidental.
- **La familia GSQ-RCO crece [F]:** ISTA-DASLab publicó `DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF` (creado 2026-10-23), y existen `Qwen3.8-27B-GSQ-RCO-GGUF` y `Qwen3.8-Flash-Next-GSQ-RCO-GGUF` + variante abliterated de SC117 (tags: gsq, rco, tensor-transplant; papers arXiv 2604.18556 y 2605.00649). La familia GSQ (la que marcamos como vigilancia en §10) ya cubre MoE grandes y el hermano 3.8-27B — **aún no hay GSQ del 3.6-35B-A3B**. Regla de vigilancia: si aparece `ISTA-DASLab/Qwen3.6-35B-A3B-GSQ-*-GGUF`, comparar contra UD-IQ3_XXS por byte antes de cualquier descarga (la marca importa [F ronda 2: bartowski peor que unsloth a misma marca]).
- **Protocolo de comparación de cuants ACTUALIZADO por la varianza [F estudio thc1006 v4]:** el mismo config medido 12 veces en un día abarca **9.4 puntos porcentuales** (DFlash-n2 osciló +17.3% a +26.7%, clusterizado por corrida) → para validar UD-IQ3_XXS-MTP vs APEX-I-MINI: **mediana de 3 corridas del ancla por sesión**, misma franja horaria, misma plantilla; descartar conclusiones de deltas <5pp en una sola corrida. Esto se aplica igual a cualquier A/B de cuants del rig (el CSV barrido-30 de una corrida por celda tiene ese ruido).
- **Recordatorio de estado:** el plan sigue siendo UD-IQ3_XXS-MTP 14.07 GB (SHA256 36f9ec0e…) como descarga principal; IQ2_XXS-MTP 11.82 e IQ1_M-MTP 11.37 como escalera RAM; el chequeo del CUDA toolkit del build ANTES de juzgar low-bit sigue vigente [F ronda 3: CUDA 13.2 roto para low-bit].

## 16. ANEXO — Sexta ronda: el repo MTP renombra sus archivos (mismo byte exacto), la escalera completa al byte y GSQ-RCO probado en la familia (2026-10-26)

Cambio de inventario que afecta DIRECTAMENTE al plan de descarga del proyecto: el repo `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` **renombró todos sus GGUF eliminando el sufijo "-MTP"**. Verificado por API de HF (tree/main) contra el snapshot de las rondas 2-5.

- **El archivo objetivo AHORA SE LLAMA DISTINTO [F API HF]:** el que era `Qwen3.6-35B-A3B-UD-IQ3_XXS-MTP.gguf` (14,069,266,720 B, SHA256 36f9ec0e… [F ronda 3]) hoy es **`Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf` con EXACTAMENTE los mismos 14,069,266,720 bytes**. Mismo tamaño al byte = mismo archivo renombrado [T; la verificación SHA256 36f9ec0e… al descargar confirma y cierra]. **El comando de descarga del proyecto se actualiza al nombre nuevo**; quien ya descargó con nombre viejo NO necesita re-descargar si el SHA256 coincide.
- **Interpretación [T]:** al eliminar los GGUF sin-nextn de este repo (o al hacerlos minoritarios), unsloth convirtió la variante MTP en el DEFAULT del repo: hoy TODOS los cuants del inventario llevan la cabeza nextn dentro. Eso es lo mejor para nosotros: cualquier peldaño de la escalera RAM habilita la fase E sin descarga extra (condición que ya exigíamos al descargar [F ronda 2]).
- **Escalera completa del repo al byte (F API, 2026-10-26; todos con nextn):** UD-Q8_K_XL 39,099,447,584 · Q8_0 37,801,097,504 · Q6_K_XL 32,611,711,264 · Q6_K 30,011,242,784 · Q5_K_XL 27,159,116,064 · Q5_K_M 27,087,812,896 · Q5_K_S 25,538,017,568 · Q4_K_XL 22,853,663,008 · Q4_K_M 22,663,387,424 · MXFP4_MOE 22,182,574,368 · Q4_K_S 21,388,319,008 · IQ4_NL 18,536,192,288 · IQ4_XS 18,209,036,576 · Q3_K_XL 17,227,569,440 · Q3_K_M 17,104,402,720 · **UD-IQ3_S 15,346,432,288** (el "riesgo" de §15 confirmado al byte) · **UD-IQ3_XXS 14,069,266,720 (OBJETIVO)** · UD-Q2_K_XL 12,574,128,416 · UD-IQ2_M 11,882,969,376 · UD-IQ2_XXS 11,819,399,456 · UD-IQ1_M 11,366,414,624.
- **mmproj ahora en 3 sabores [F API]:** `mmproj-BF16.gguf` 902,822,528 B · `mmproj-F16.gguf` 899,283,584 B · `mmproj-F32.gguf` 1,786,305,152 B. La regla de la ronda 5 sigue: el rig es texto-only → **ninguno se descarga** (ahorra 0.9-1.8 GB de disco y de confusión en la carga).
- **GSQ-RCO pasa de "vigilancia" a "método probado en la familia Qwen" [F]:** ISTA-DASLab publicó `Qwen3.8-27B-GSQ-RCO-GGUF` (el hermano denso de 27B **a 11.8 GB** con asignación de precisión por tensor vía búsqueda con gradiente) y `Qwen3.8-Flash-Next-GSQ-RCO-GGUF` (MoE de **512 expertos**, 4 tamaños, corte de ~80-95 GB a 68-76 GB) + variante **Coder** que conserva solo 256/512 expertos a 1.89 bpw efectivo (58.4 GB). Los GGUF "run unmodified in llama.cpp, Ollama and LM Studio" [F card]. **Sigue sin existir GSQ del 3.6-35B-A3B** → la regla de vigilancia de §15 se mantiene y se afinan los términos de búsqueda: repos de ISTA-DASLab con tag `gsq` + nombre `Qwen3.6-35B-A3B`. Si aparece: comparar por byte contra UD-IQ3_XXS con el gate de §15 (perplexity ES + spot-check) antes de reemplazar el objetivo de descarga, porque la asignación por sensibilidad promete mejor calidad/byte que UD [T hipótesis del método, no medida en nuestro modelo].
- **Dato colateral útil [F blog MindStudio]:** el 27B denso GSQ-RCO a 11.8 GB se posiciona como calidad de Q8 a un tercio del tamaño — coherente con la promesa del método y con lo que convendría exigirle a un futuro GSQ del 35B (no un UD-IQ3 con otra marca, sino "IQ3 con menos pérdida a igual bytes").
- **Ningún otro cambio del inventario:** ni `APEX-I-MINI` (nuestro actual) ni los repos de bartowski/mudler mostraron movimientos relevantes en esta ronda; el A/B de marca de la ronda 2 (unsloth domina la frontera Pareto, mudler nunca en frontera) no tiene razón para cambiar.

*Referencias nuevas: huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/tree/main (snapshot 2026-10-26); cards ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF y ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF (+ variante Coder); reddit r/LocalLLaMA "[Release] SOTA GGUFs for Qwen3.8-Flash-Next"; github IST-DASLab/GSQ issue #9 (reproducibilidad); mindstudio.ai blog GSQ-RCO.*


## 17. ANEXO — Séptima ronda: verificación byte a byte del árbol del repo MTP y encuadre del UD-IQ3_S (2026-10-26)

- **Árbol completo verificado hoy vía API de HF [F]** (snapshot 2026-10-26, `huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/tree/main`): `UD-IQ3_XXS.gguf` = **14,069,266,720 B exactos** — coincide con la ronda 6; el autenticador de descarga sigue siendo SHA256 36f9ec0e… Escalera relevante al byte: UD-IQ1_M 11,366,414,624 · UD-IQ2_XXS 11,819,399,456 · UD-IQ2_M 11,882,969,376 · UD-Q2_K_XL 12,574,128,416 · **UD-IQ3_XXS 14,069,266,720 (objetivo)** · UD-IQ3_S 15,346,432,288 · UD-IQ4_XS 18,209,036,576 · UD-Q4_K_M 22,663,387,424 · UD-Q4_K_XL 22,853,663,008 · MXFP4_MOE 22,182,574,368 · Q8_0 37,801,097,504. mmproj en 3 sabores — BF16 902,822,528 / F16 899,283,584 / F32 1,786,305,152 — (no descargar, decisión de rondas previas se mantiene).
- **Encuadre para no confundir densidades entre repos [F]:** el `UD-IQ3_S` de ESTE repo (15.35 GB) lleva la cabeza nextn dentro; el 13.68 GB documentado en la ronda 5 era el del repo 3.5 SIN nextn. Comparaciones de densidad entre repos solo válidas si ambos lados llevan (o no) nextn.
- **GSQ-RCO [F]:** sigue SIN 3.6-35B-A3B a fecha de hoy — la familia probada sigue siendo 3.8-27B / Flash-Next (+ variante Coder). La vigilancia de rondas 5-6 se mantiene sin cambios.
- **Repo principal unsloth (sin -MTP) [F]:** única novedad visible es de tool-calling ("Developer Role Support" para Codex/OpenCode y parsing de objetos anidados mejorado); sin cuants nuevos. Irrelevante para el objetivo t/s, relevante solo si el Director usa el modelo como agente de código.

*Referencias nuevas: huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/tree/main (snapshot 2026-10-26, verificación byte a byte de esta ronda); card unsloth/Qwen3.6-35B-A3B-GGUF (repo principal, notas de tool-calling).*


## 18. ANEXO — Octava ronda: SHA256 de descarga AUTORITATIVO y cerrado (2026-10-26)

- **SHA256 LFS oficial verificado HOY contra la API de HF [F]:** `UD-IQ3_XXS.gguf` = 14,069,266,720 B, **SHA256 = `36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012e3d9e2495a90e7a7150`** — coincide con el 36f9ec0e… de las rondas 6-7. La descarga del hito queda con autenticador completo y cerrado. Protocolo de verificación en el rig: `certutil -hashfile D:\ZLia\models\Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf SHA256` y comparar contra la cadena completa.
- **Artefacto de la API documentado (para no repetir la confusión) [M]:** el endpoint `/revision/main?blobs=true` devuelve `blobId` de 40 hex = SHA-1 de git (del puntero LFS), NO el sha256 del contenido; el sha256 real vive en `lfs.oid` del endpoint `/tree/main`. Regla: autenticar SIEMPRE con `lfs.oid`.
- **mmproj-F16.gguf archivado con autenticador [F]:** 899,283,584 B, SHA256 `71f3cbc1f7cc0f30d09d41cfa924c0060827ebc33bf15ace7e86661e856f0160` — por si la visión vuelve al plan; hoy sigue fuera del disco de trabajo.
- **Sin más cambios de inventario:** escalera al byte de la ronda 7 se mantiene; GSQ-RCO sigue sin 3.6-35B-A3B.

*Referencias nuevas: huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/tree/main (lfs.oid de UD-IQ3_XXS y mmproj-F16, snapshot 2026-10-26).*
