# RESUMEN SIMPLE — Nivel 4: Presupuesto de memoria al límite (VRAM útil de la GTX 1650 + RAM sin pageouts)

> **Qué es este archivo:** la misma información que `nivel-4-memoria-vram-ram.md`, punto a punto y sección por sección (los números de § coinciden), pero explicada en términos simples y resumida.
> **La información completa (mapas de memoria, tablas de dosis, issues, auditoría punto a punto) está en el archivo completo.** Este resumen no añade nada nuevo.
>
> Etiquetas simplificadas: **[medido aquí]** = probado en este rig / leído del dump del build · **[verificado afuera]** = confirmado en fuente externa · **[estimación]** = cuenta propia.

---

## 1. Tesis (§1)

- El rig usa DOS memorias (VRAM y RAM) y solo administramos una bien. Ideas clave:
  - Los expertos del modelo viven en la RAM (DDR4), que es el cuello de botella.
  - La GTX 1650 tiene **~1.2-1.7 GB de VRAM libre** con la config actual.
  - La RAM (16 GB) está tan justa que el propio build advierte de pageouts (usar el SSD como memoria de emergencia = lentitud).
- Este nivel explota ambos frentes con flags que ya existen: subir capas de expertos a VRAM y controlar cómo se carga el modelo. **Ganancia esperada: +3-5% por VRAM + 0 a +15% por eliminar pageouts. Sin tocar calidad** (es el mismo modelo, byte a byte).

## 2. Mapa de memoria (§2)

- El **92% del modelo son expertos ruteados** (13.13 GB) y viven en CPU. Cada capa de expertos pesa ~328 MB.
- Con la VRAM libre caben **3-5 capas de expertos** (o un draft de ~0.5 GB + 2-3 capas).
- El contexto es BARATO en esta arquitectura (la KV entera a 16k pesa menos que 1 capa de expertos) → **reducir `-c` para "ahorrar" NO es palanca: NO-GO** (además rompe la cache de prompts del N3).
- Cada capa que sube a VRAM quita ~10 MB/token de tráfico de RAM.

## 3. Front VRAM-A: dosis `-ncmoe` (§3)

- `-ncmoe N` = cuántas capas de MoE se quedan en CPU. Semántica confirmada por el dump del build: "first N layers" (N bajo = más capas en GPU).
- Dosis propuestas: H2 `-ncmoe 38` (+1.6%), H3 `37` (+2.5%), H4 `36` (+3.3%), H5 `34` (+5.2% solo si sobra VRAM), y H6 blindada con `-ot` explícito (independiente de la semántica).
- **El cliff que manda** [verificado afuera]: si desbordas la VRAM, Windows manda los datos a RAM **en silencio** y el rendimiento colapsa ×10 (caso real: 12.70 → 1.28 t/s). Fallar por debajo cuesta 5%; pasarse cuesta 900% → dosis ascendente + `nvidia-smi` tras cada arranque + Sysmem Fallback OFF (N3 §11).

## 4. Front VRAM-B: reparto cuando hay especulación (§4)

- El nextn (MTP) pesa **858 MB**: puede ir a VRAM (draft casi gratis) o a CPU (libera VRAM ≈ 2.6 capas de expertos, penaliza ~1% del gain) → casi neutro, se decide midiendo.
- Un draft sidecar (421-517 MB) cabe junto a 2-3 capas. Regla: el draft tiene prioridad sobre las capas (es obligatorio para su función).

## 5. Front VRAM-C: shootout CUDA vs Vulkan (§5)

- Probar el binario Vulkan es gratis (1 min de arranque). Riesgo: que la arquitectura del 3.6 no esté soportada en Vulkan → NO-GO automático. Ganancia esperada ~0 o negativa; se prueba porque es la única variable sin coste.

## 6. Front RAM-A: pageouts (§6)

- **Por qué amenaza**: modelo 14-14.3 GB + todo lo demás ≈ 15.3-16 GB de huella en 16 GB físicos → cualquier presión (navegador, índice de búsqueda) manda páginas del modelo al SSD y el decode se traba.
- **Detección en 10 min** (PowerShell `Get-Counter` de Page Reads/sec durante decode): ≈0 → RAM limpia, este frente rinde 0; >0 sostenido → hay velocidad regalada.
- **Dosis `-lm`**: `dio` (salta la cache de Windows, libera 1-2 GB de standby) o `mmap+mlock` (cero pageouts garantizados PERO solo con margen de RAM — dosis última).
- `-lzm` (lazy) no aplica a este GGUF: no hay tensores >4 GiB.

## 7. Vigilancia — no accionar hoy (§7)

- **Expert streaming desde disco**: ~5 implementaciones comunitarias sin fusionar; si upstream la fusiona, el límite de 16 GB de RAM deja de ser techo (revisar mensualmente).
- #29964 (pipeline parallelism): solo multi-GPU, no aplica.

## 8. Integración con el barrido (fase H) (§8)

Plan de corridas H1-H8 (ancla → ncmoe 38/37/36 → -ot blindado → -lm → nextn GPU vs CPU), cada una con sus autenticadores (delta de buffer en el log, pageouts ≈ 0, nvidia-smi ≤ 3.7 GB, t/s estándar).

## 9. Riesgos y NO-GO predeclarados (§9)

- Overshoot VRAM = cliff ×10 → jamás saltar dosis sin medir la anterior.
- mlock con RAM justa = peligro → revertir si degrada.
- Vulkan sin soporte GDN → NO-GO automático.
- Nada de BIOS ni Defender; reducir `-c` para ahorrar RAM = NO-GO.

## 10. Líneas finales por escenario (§10)

Comandos concretos con rutas reales del rig (H4, H4+RAM limpia, H4+MTP) — texto completo en el archivo.

## 12. Anexo ronda 4: corrección KV y semillas ya medidas (§12)

- **Corrección**: la KV se almacena chica pero se LEE completa en cada token → en chats largos, reducir ctx es una palanca PEQUEÑA de decode (no de RAM).
- **Las semillas ya están medidas** [medido aquí]: NCM37C4 22.49 t/s (+4.4%, el mejor) y FIT-A 22.40 (+4.0%) → la fase H no parte de cero. Dosis nueva para separar el efecto de capas-GPU del efecto ctx-4k.
- La semántica de `--fit` confirmada: solo ajusta argumentos NO fijados → en la fase H fijar SIEMPRE `-c` y `-ngl` explícitos.

## 13. Anexo ronda 5: MEC entra al presupuesto (§13)

- El cache de expertos MEC (`--moe-cache-mib`) consume la MISMA VRAM libre que administra este nivel → ahora hay **3 competidores** por los 1.2-1.7 GB: (1) más capas en GPU, (2) pool MEC, (3) KV f16. Los datos favorecen al MEC (un MiB de cache rinde más que un MiB de expertos permanentes, porque el routing se repite entre tokens).
- Regla definitiva: **KV cuantizada es feature de MEMORIA, no de velocidad** (f16 es más rápido cuando cabe) → solo usarla si libera VRAM para algo mejor.
- `-lm none` con número externo: RAM del 98% → 71% a la misma velocidad → palanca #1 de pageouts junto a `-ctxcp 4`.
- mmproj/imatrix: NO entrar al disco (ahorra hasta 1.8 GB y evita accidentes).
- El cliff silencioso tiene dato de forma (5090: 69.4 → 27.5 t/s por un paso de más) → regla: "el paso óptimo es cliff menos uno"; subir dosis de a 256 MiB con nvidia-smi abierto.
- Orden de dosis v5: 1) `-ctxcp 4` + Sysmem Fallback OFF + Alto rendimiento → 2) `-lm` según pageouts → 3) MEC 512 sobre NCM37C4 → 4) escalar si sobra VRAM → 5) KV f16 solo como diagnóstico.

## 14. Anexo ronda 6: producción ajena y el cache chico como riesgo (§14)

- Cómo estira el presupuesto una producción real (L4 24 GB): `-ub 64 -b 512` (micro-batch chico = buffers chicos = más VRAM libre), ctx máx 56,320, KV ~22 KiB/token.
- La escala del MEC cuando hay VRAM: caches de **7-9 GiB** en una 5070Ti (+36-40%) → nuestro techo con 512-1024 MiB es fracción de eso.
- **El cache chico puede ser NETO NEGATIVO** (600 MiB → −48%) → el control D-MEC-0 es paso obligatorio.
- Fix upstream del sampler DRY (agotaba RAM): el rig NO está expuesto (DRY desactivado por default).

## 15. Anexo ronda 7: el draft abre un SEGUNDO presupuesto (§15)

- Al activar MTP/draft aparecen gastos propios: el draft context sobre-reserva buffers (~800 MiB de sobreestimación, #26038) y hubo un caso de crash porque el fit ignoraba la VRAM del MTP (#23472) → **el presupuesto del draft se mide con el log, no se asume**.
- Dosis defensivas (existen en b11856 [medido en el dump]): ctx del draft chico (`-cd`) + KV del draft cuantizada (`-ctkd/-ctvd` q8_0) ANTES de tocar el ctx principal.
- Fallback silencioso upstream (#26432): el draft puede empujar el total pasado la VRAM sin error; único síntoma = t/s desplomado → **señal de alarma: aceptación normal pero t/s desplomado = fallback del driver, no culpa del draft**.
- Referencia de coste MTP: +1,296 MiB a ctx 131k (escalar por ctx, no copiar).

## 16. Anexo ronda 8: referencia de producción de la pila completa (§16)

- Una guía de producción con nuestra familia exacta corre la pila completa (KV cuantizada + ctx acotado + draft con budget + MoE parcial en CPU) sin conflicto → prueba de viabilidad. La dosis exacta para 4 GB sigue siendo dato propio del barrido post-RUTA-0.

## 17. Anexo ronda 9: suelo del backbone y regla del desborde (§17)

- **Suelo VRAM del backbone validado por terceros**: ~2.4 GB con visión / ~1.5 GB sin (1060 6GB) → consistente con nuestra estimación.
- **Regla del desborde permanente**: en la 1650 el modelo NUNCA cabe entero → el offload no se "gradúa", solo se re-optimiza si cambia cuant, ctx o entra MEC/draft.
- La KV del 3.6 es modesta **por diseño** (solo las 10 capas de atención llevan KV; las 30 recurrentes llevan un estado compacto) → el ctx grande es viable en 4 GB: **el KV no es el enemigo, los expertos sí**.

## 18. Anexo ronda 10: auditoría de respaldo riguroso (§18)

- Re-verificación punto a punto: **0 puntos refutados**; el mapa de memoria y el régimen bandwidth-bound quedaron cross-validados por 3 fuentes nuevas; el spill silencioso de Windows quedó triple-fuente.
- **Novedad de estado**: #26038 (sobre-reserva del draft) quedó **cerrado como "not planned"** → no esperar fix: al llegar a RUTA 0, el buffer del draft se mide con el log desde el primer run.
- Orden de dosis v5 SIN cambios.

---

## Cheatsheet operativa del nivel 4

- **Orden de dosis v5**: `-ctxcp 4` + Sysmem Fallback OFF + Alto rendimiento → `-lm` según pageouts medidos → MEC 512 sobre NCM37C4 (con control D-MEC-0) → escalar de a 256 MiB si sobra VRAM → KV f16 solo diagnóstico.
- **Autenticadores**: delta de buffer-size en el log, Pages Input/sec ≈ 0, nvidia-smi ≤ 3.7 GB.
- **Reglas de oro**: cliff −1 (nunca un paso de más); draft en GPU siempre; ctx del draft y su KV antes que el ctx principal; reducir `-c` = NO-GO.
- 📄 Detalle completo, fuentes y auditoría: [`nivel-4-memoria-vram-ram.md`](nivel-4-memoria-vram-ram.md)
