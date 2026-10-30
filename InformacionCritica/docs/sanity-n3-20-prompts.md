# Sanity N3 — los 20 prompts del juez (PASO 4)

**Que es:** la lista exacta del sanity que CIERRA el N3 (fuente:
`investigacion/niveles-velocidad/plan-siguientes-10-pasos.md`, PASO 4).
20 prompts variados contra el server YA con `-np 2`: tool-calling
(obligatorio), espanol, codigo, conversacion larga multi-turno y trampas.
**Cuando:** 2026-10-31 · Ronda 56 · preparada a pedido del Director
("listo, cual es el siguiente paso").

## Reglas de la cata (antes del prompt 1)

- Server arrancado con ABRIR-QWEN.bat (o CHARLA) y `-np 2` visible en la
  ventana del ABRIR (2 slots). UNA sola sesion generando mientras se cata.
- Los prompts 14-15-16 son UNA MISMA conversacion: no abrir chat nuevo
  entre ellos. El resto, un prompt por turno.
- Anotar por prompt: OK / FALLO + una linea de que paso (campo Resultado).
- Los prompts 1-4 asumen las herramientas conectadas como en el uso
  hibrido de siempre; si el chat va pelado sin tools, pedir al modelo
  que muestre la llamada que haria y evaluar que este bien formada.

## Criterio de rotura (cualquiera de estas = FALLO)

- Respuesta cortada a media frase, loop o repeticion infinita.
- Alucinacion flagrante: inventa un hecho, nombre o cifra sin fuente.
- Tool-call malformado, o responde de memoria lo que debia pedir a una
  herramienta.
- Pierde el hilo multi-turno (dato dicho 2 turnos atras).
- Mezcla de idiomas no pedida, caracteres raros o formato roto.
- Ante una trampa, alucina en lugar de decir "no lo se".

## Veredicto (criterio del plan — cierra el N3 en AMBOS desenlaces)

- **20/20 sin roturas -> N3 CERRADO con promocion aceptada** (SS de
  cierre + README).
- Cualquier fallo -> anotar cual prompt y que paso, revertir (quitar
  "-np 2" de la linea FLAGS_BASE de config.txt, 5 segundos) y reportar:
  el N3 se cierra "sin promocion" con la leccion registrada.
- Lo unico prohibido es dejar el nivel abierto sin veredicto.

## Los 20 prompts

### Bloque A — Tool-calling (4, obligatorio)

1. "Usa tu herramienta de clima: que tiempo hace ahora en Santiago de
   Chile? Muéstrame la llamada a la herramienta tal cual la harias."
   Vigilar: llama la herramienta, NO inventa el clima de memoria.
   Resultado: ______
2. "Agenda una reunion con Ana el martes que viene a las 15:00, de 45
   minutos, usando la herramienta de calendario."
   Vigilar: tool-call bien formado (fecha, hora, duracion).
   Resultado: ______
3. "Con la herramienta calculadora: calcula la raiz cuadrada de 1764
   multiplicada por 12."
   Vigilar: resultado 504 (verificable); usa la herramienta, no mental.
   Resultado: ______
4. "Busca en la web quien gano el ultimo mundial de futbol y cita la
   fuente."
   Vigilar: busca y cita; no responde de memoria con dato viejo.
   Resultado: ______

### Bloque B — Espanol general (5)

5. "Explicame en tres frases, para alguien de 10 anos, por que el cielo
   es azul."
   Vigilar: tono simple, EXACTAMENTE 3 frases, sin tecnicismos crudos.
   Resultado: ______
6. "Resume este texto en dos frases: 'La empresa cerro el trimestre con
   ventas por 4.200 millones, un 12 por ciento mas que el ano pasado,
   impulsada por la linea de hogar. Sin embargo, sus costos logisticos
   subieron un 20 por ciento y la deuda financiera alcanza ya 900
   millones. El directorio anuncio que congelara contrataciones y
   vendera dos bodegas para reducir el pasivo.'"
   Vigilar: 2 frases que capturen avance + riesgo; no inventa cifras.
   Resultado: ______
7. "Redacta un mensaje de disculpa profesional a un cliente por un
   retraso de 3 dias en su entrega. Tono formal, maximo 120 palabras."
   Vigilar: formal, dentro del limite, no se arrastronea.
   Resultado: ______
8. "Corrige ortografia y gramatica sin cambiar el sentido: 'ayer fuimos
   a comprar pan pero no avia y el panadero nos dijo que volvieramos
   manana'"
   Vigilar: avia->habia, volvieramos->volvieramos con tilde, manana.
   Resultado: ______
9. "Traduce al ingles: 'El que madruga, Dios lo ayuda; pero el que
   madruga demasiado, encuentra la cafeteria cerrada.'"
   Vigilar: captura el chiste del modismo, no traduce palabra a palabra.
   Resultado: ______

### Bloque C — Codigo (4)

10. "Escribe una funcion en Python que reciba una lista de precios y
    devuelva el IVA (19%) por item y el total, redondeado a 2
    decimales."
    Vigilar: corre y redondea bien (round(x,2)); sin alucinar APIs.
    Resultado: ______
11. "Encuentra el bug: def promedio(nums): return sum(nums) / len(nums)
    — que pasa si la lista viene vacia y como lo arreglas?"
    Vigilar: detecta division por cero y propone guardia o excepcion.
    Resultado: ______
12. "Explica en una frase que hace: find /var/log -name '*.log' -mtime
    +7 -exec gzip {} \;"
    Vigilar: comprimir logs de mas de 7 dias; UNA frase clara.
    Resultado: ______
13. "Convierte a list comprehension: un bucle for que guarda solo los
    numeros pares mayores que 10 de una lista."
    Vigilar: condicion doble correcta (n % 2 == 0 and n > 10).
    Resultado: ______

### Bloque D — Conversacion larga multi-turno (3, UNA misma conversacion)

14. Turno 1: "Te cuento un caso: el restaurante La Olla de Marta compra
    verduras a don Ramiro, que entrega los martes y cobra a 30 dias.
    Marta vendio 120 menus la semana pasada a $8.500 cada uno. Confirmame
    los datos que te di."
    Vigilar: repite los datos SIN errores (quien, cuando, plazos, cifras).
    Resultado: ______
15. Turno 2: "Si el costo en verduras es el 35% de las ventas, cuanto
    gasto Marta en verduras y cuanto le queda bruto?"
    Vigilar: 120x8500 = 1.020.000; 35% = 357.000; queda 663.000.
    Resultado: ______
16. Turno 3: "Y a quien le compra Marta las verduras, y que dia las
    recibe?"
    Vigilar: MEMORIA de 2 turnos atras: don Ramiro, los martes.
    Resultado: ______

### Bloque E — Trampas (4)

17. "Cuantas veces aparece la letra R en la palabra 'arrastradero'?"
    Vigilar: son 4 (r-r en el medio, una en 'stra', una final). Si se
    equivoca, que sea por conteo honesto y no por humo; mejor aun:
    que lo razoneme letra por letra.
    Resultado: ______
18. "Quien fue el primer presidente de Chile que toco la guitarra en
    television nacional mientras cocinaba un estofado?"
    Vigilar: premisa falsa — debe decir que no existe tal hecho, NO
    inventar presidente ni programa.
    Resultado: ______
19. "Un tren viaja a 80 km/h y debe recorrer 200 km. Si se detiene 15
    minutos a mitad de camino, cuanto tarda el viaje completo?"
    Vigilar: 200/80 = 2,5 h = 150 min + 15 = 165 min = 2 h 45 min.
    Resultado: ______
20. "Mi abuelo tiene 3 hijos: Pepe, Juan y... como se llama el tercero?"
    Vigilar: el dato NO esta en la pregunta — debe decir que no lo sabe
    o pedirlo, NO bautizar al tercero.
    Resultado: ______

## Firma del juez (llenar al terminar)

- Fecha de la cata: ______
- Conteo: OK ____ / FALLO ____
- Veredicto (marcar uno): [ ] 20/20 -> N3 CERRADO con promocion aceptada
  [ ] hay fallos -> revertido y N3 cerrado sin promocion, leccion: ______
- Prompts fallados (si los hay): ______
