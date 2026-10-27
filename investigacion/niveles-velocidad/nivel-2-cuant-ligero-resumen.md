# RESUMEN SIMPLE — Nivel 2: Cuant más ligero ya hecho (descarga, sin requant local)

> **Qué es este archivo:** la misma información que `nivel-2-cuant-ligero.md`, punto a punto y sección por sección (los números de § coinciden), pero explicada en términos simples y resumida.
> **La información completa (bytes exactos, SHA256 completos, tablas, auditoría punto a punto) está en el archivo completo.** Este resumen no añade nada nuevo.
>
> Etiquetas simplificadas: **[medido aquí]** = probado en este rig · **[verificado afuera]** = confirmado en fuente externa · **[estimación]** = cuenta propia.
> Regla del proyecto respetada: **aquí no se re-quantiza nada** — todo son descargas de cuants ya hechos por terceros.

---

## 0. Veredicto (§0 del completo)

1. El peldaño inferior ya existe hoy: **UD-IQ3_XXS de unsloth, ~13.2 GB** → ~+8% t/s [estimación] y libera ~1 GB de RAM.
2. Sorpresa del benchmark independiente (localbench): de 64 cuants medidos contra el original, **unsloth domina la tabla y mudler/APEX (nuestro cuant actual) nunca aparece en la frontera** → bajar de APEX a UD-IQ3_XXS probablemente también MEJORA la calidad por byte.
3. Debajo de IQ3 la calidad se rompe rápido: Q2 = solo test; IQ2_XXS e IQ1 = NO-GO para uso serio (los errores se multiplican).

## 1. Teoría mínima (§1)

- Un GGUF guarda los pesos "comprimidos". Menos bits por peso = archivo más chico = menos lectura de RAM.
- **imatrix**: matriz de calibración que decide dónde importa más no equivocarse. Un IQ3 sin imatrix es peor que un Q3 normal.
- **UD (Unsloth Dynamic)**: asigna más bits a las capas críticas y menos a la cola, con calibración curada. Es la marca que mejor rinde en este modelo.
- **KLD**: la métrica que mide cuánto se desvían las respuestas del cuant respecto al original. Referencia: <0.1 imperceptible; 3–4 = notable. El KLD se mide con tareas reales (no Wikipedia, que infla los resultados).
- Por qué un MoE sufre a 2 bits: cada experto es chiquito y el router amplifica errores pequeños. Unsloth documenta que a 2 bits el comportamiento agéntico se rompe (loops).

## 2. La escalera del modelo (§2)

- Escalera medida en el gemelo 3.5: **IQ3_XXS es el último peldaño con pérdida casi gratis** (KLD 1.53 vs 1.42 del peldaño superior). Q2_K_XL ya duplica el error; IQ2_XXS lo triplica.
- La marca importa tanto como el nivel: el IQ3_XXS de bartowski tiene mucho peor KLD que el de unsloth.
- En el 3.6 (localbench, 64 cuants de 6 marcas): el 3.6 cuantiza MEJOR que el 3.5; unsloth gana 14/26 posiciones de frontera; **tool-calling es la categoría que peor cuantiza** (se rompe primero); hasta el IQ1_M retiene 86.9% del top-1 (pero no sirve para agéntico).

## 3. El candidato concreto (§3)

- `unsloth/Qwen3.6-35B-A3B-GGUF` → `UD-IQ3_XXS.gguf`, 13.2 GB [verificado afuera].
- KLD exacto del 3.6 no publicado, pero el análogo 3.5 y el ranking localbench dicen pérdida despreciable esperada.
- El módulo MTP probablemente viene incluido — verificar al descargar (el parser busca los tensores `nextn.*`). Si está, habilita la fase E sin descarga extra.

## 4. Qué gana exactamente el rig (§4) [estimación]

- ~+8% t/s (menos bytes por token, misma física del N1).
- **+1.05 GB de RAM libres** — el margen para el cache de prompts, el draft y un contexto estable.
- Colocación y flags funcionan igual; carga ~2–3 s más rápida.

## 5. ¿Y si bajamos más? (§5)

| Peldaño | Tamaño | Veredicto simple |
|---|---|---|
| UD-IQ3_XXS | 13.2 GB | **GO** (el objetivo) |
| UD-Q2_K_XL | ~12 GB | TEST opcional con sanity de tool-calling |
| UD-IQ2_XXS | ~9-11 GB | NO-GO (calidad rota) |
| IQ1_M | ~10-11 GB | NO-GO (agéntico roto) |

La física manda: debajo de IQ3_XXS cada punto de velocidad se paga con múltiples de error.

## 6. Vocab-trimming (§6, corregido luego en §13)

- Concepto: recortar el vocabulario (−41%) aceleraría +6–7% [estimación]. **PERO verificado después por API: el único archivo publicado es Q4_K_S de 20.07 GB → no cabe en 16 GB de RAM → NO-GO**. La idea queda aparcada hasta que alguien publique uno a 3 bits.

## 7. REAP-50 (§7)

- Poda global de la mitad de expertos, ya hecha por terceros para el 3.6. Baja RAM y archivo de verdad (a diferencia del N1). Pero es un salto de riesgo y su única gracia es RAM/calidad — ver §13.4: no acelera.

## 8. Protocolo de validación en el rig (§8)

1. Descargar el candidato.
2. **Autenticar** el GGUF con el parser (arquitectura, k=8, presencia de `nextn.*`).
3. Medir con las fases B/C del barrido contra el ancla actual.
4. Sanity de 20 prompts (con tool-calling sí o sí).
5. A/B de marca si hay dudas (contra UD-IQ3_S).

## 9. Riesgos (§9)

- KLD del 3.6 no publicado (mitigado con los análogos).
- Tool-calling: siempre en el sanity.
- Espacio en disco; mmproj no necesario.
- No existe un cuant 3-bit de la marca APEX mejor posicionado que unsloth [verificado afuera].

## 10. Vigilancia (§10)

- **MoQ** ("Mixture of Quants") y **GSQ**: familias nuevas que prometen mejor calidad por byte. Cuando salga una del 3.6 a 3 bits, comparar contra UD-IQ3_XXS antes de cualquier descarga.

## 11–12. Anexos rondas 2-3: bytes exactos y la revelación MTP (§11-§13)

- Inventario leído por API de HF con bytes al byte. **UD-IQ3_S (13.68 GB) es 0.59 GB MENOR que nuestro APEX actual a la misma densidad** → cambio de marca "gratis" (+4% t/s) si IQ3_XXS asustara.
- **REVELACIÓN principal**: existe `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` — cuants UD que **ya traen la cabeza nextn (MTP) dentro**. El objetivo pasa a ser **UD-IQ3_XXS-MTP: 14.07 GB** ≈ el mismo footprint RAM que hoy, con cuant mejor Y MTP incluido → la "descarga única soñada".
- El módulo nextn pesa **858 MB** (medido por diferencia de bytes).
- Bytes y SHA256 de la descarga principal: **14,069,266,720 B; SHA256 `36f9ec0e…7150`** (protocolo certutil; no borrar el APEX antes de verificar).
- **Restricciones oficiales del MTP** (README del repo): `-np > 1` no soportado (con fase E va `-np 1`) y `--mmproj` no soportado (irrelevante: no usamos visión).
- Presupuesto RAM por escenario: IQ3_XXS solo = cómodo; IQ3_XXS+MTP = apretado (`-c 8192`, cache-ram 256–512); IQ3_S+MTP = no cabe.
- Cómo saber qué CUDA lleva el build (por el bug 13.2): mirar el nombre del zip descargado o las DLLs.

## 14. Anexo ronda 4: rehabilitación parcial del 2-bit (§14)

- Evidencia: el 2-bit de unsloth completó un flujo agéntico real (30+ tool calls) con 13 GB de RAM → el 2-bit "funciona" para agéntico básico, aunque la calidad de texto largo es una incógnita.
- Escalera de descarga por prioridad RAM: IQ3_XXS-MTP (plan principal) → IQ2_XXS-MTP (plan RAM) → IQ1_M (emergencia).

## 15. Anexo ronda 5: inventario completo y varianza (§15)

- Inventario exacto completo del repo MTP: IQ1_M-MTP 11.37 GB (más barato de lo creído, con MTP dentro), IQ2_M 11.88 (peldaño intermedio nuevo), IQ3_S-MTP 15.35 (NO como primer paso: aprieta RAM), además de todos los Q4/Q5/Q6/Q8.
- mmproj e imatrix: NO descargar ninguno (uso texto-only).
- GSQ-RCO crece en la familia (3.8-27B y Flash-Next) pero **aún sin 3.6** — vigilancia.
- **Lección de medición**: el mismo config medido 12 veces varía hasta 9.4 puntos porcentuales → validar con **mediana de 3 corridas** y desconfiar de deltas <5pp.

## 16–17. Anexos rondas 6-7: renombrado del repo y verificación byte a byte (§16-§17)

- El repo MTP **renombró todos sus archivos quitando el sufijo "-MTP"**: el archivo objetivo ahora se llama `UD-IQ3_XXS.gguf` con EXACTAMENTE los mismos 14,069,266,720 bytes. Mismo tamaño = mismo archivo; quien descargó con nombre viejo no necesita re-descargar (el SHA256 confirma).
- Interpretación: la variante MTP es ahora el DEFAULT del repo — todos los cuants llevan nextn dentro. Cualquier peldaño habilita la fase E sin descarga extra.
- Comparación de densidades entre repos solo válida si ambos lados llevan (o no) nextn.

## 18. Anexo ronda 8: SHA256 autoritativo cerrado (§18)

- El hash completo de la descarga del hito queda cerrado: **UD-IQ3_XXS.gguf = 14,069,266,720 B, SHA256 `36f9ec0e4c775f6efd3a61c1ea76f0875128469c3d012e3d9e2495a90e7a7150`**.
- Gotcha de la API de HF documentado: autenticar SIEMPRE con `lfs.oid` del endpoint `/tree` (el `blobId` de `/revision` es un SHA-1 de git, NO el hash del contenido).
- mmproj-F16 archivado con su hash por si la visión vuelve.

## 19. Anexo ronda 9: el piso físico del formato (§19)

- **IQ1_S 1.66 GB es el mínimo GGUF posible del 3.6** (embedding de 248k + lm_head untied no bajan de ~2 bits). Nuestro plan (11-14 GB) está 7× por encima del piso → sin riesgo de territorio roto por formato.
- REAP-90 (keep-26 de 256): el propio autor re-confirma que es un "meme" incoherente → NO-GO definitivo de la poda extrema.
- Repo alternativo 0xSero: sin SHA256 ni nextn documentados → no adoptado, vigilancia pasiva.

## 20. Anexo ronda 10: auditoría de respaldo riguroso (§20)

- Re-verificación punto a punto: **0 puntos refutados**; la frontera localbench, las restricciones MTP, el aviso CUDA 13.2 y la guía MTP quedaron confirmados verbatim.
- Matiz resuelto a favor del registro: el headroom del MTP es **~1 GB** según la guía ESPECÍFICA del 3.6 (una página general dice ~2 GB).
- Dosis de descarga SIN cambios: UD-IQ3_XXS (14.07 GB, SHA256 cerrado) sigue siendo la principal.

---

## Cheatsheet operativa del nivel 2

- **Descarga principal**: `unsloth/Qwen3.6-35B-A3B-MTP-GGUF` → `UD-IQ3_XXS.gguf` (14,069,266,720 B, SHA256 `36f9ec0e…7150`).
- **Verificar**: `certutil -hashfile … SHA256` antes de borrar el APEX; parser confirma `nextn.*`.
- **Escalera RAM**: IQ3_XXS (14.07) → IQ2_XXS (11.82) → IQ1_M (11.37), todos con MTP dentro.
- **Reglas**: sanity con tool-calling siempre; mediana de 3 corridas; nada de mmproj/imatrix al disco.
- 📄 Detalle completo, fuentes y auditoría: [`nivel-2-cuant-ligero.md`](nivel-2-cuant-ligero.md)
