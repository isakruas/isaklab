---
title: Empezando un compilador AVR desde cero
date: 2026-06-07
tags: avr, ik8b, compiladores
summary: Las primeras decisiones de ik8b — almacenamiento explícito, asignación de registros y una biblioteca estándar sin runtime de C.
---

Empecé ik8b: un compilador de un lenguaje pequeño, `ik`, directo a firmware AVR, sin
ensamblador, enlazador ni runtime de C externos. La semana fue sobre las decisiones
que deben venir antes de que nada de eso funcione.

**Dónde vive un valor es parte del tipo.** `ik` exige que cada declaración indique
su almacenamiento — RAM, EEPROM o flash — y separa los primitivos escalares (`i8`,
`i16`, `bool`, `char`) de los tipos mapeados a registro (`r8`, `r16`). En una pieza
de 8 bits con unos pocos cientos de bytes de RAM, hacer explícito el almacenamiento
mantiene predecible el código generado.

**Asignación de registros.** En un chip de 32 registros, el backend recibió un
asignador por coloreo de grafo sobre análisis de liveness del CFG, y luego la
corrección que eso obliga: preservar los registros de operando y de argumento a
través de llamadas anidadas, para que una llamada dentro de una expresión no
sobrescriba los valores alrededor.

**Sin runtime de C, hay que entregar una biblioteca estándar.** Sin libc no hay a
qué recurrir, así que el lenguaje lleva la suya: una fuente ASCII 5×7 en flash,
literales de cadena en flash con escapes `\x`, y drivers para ADC, PWM,
temporizadores, sleep, watchdog y un buffer circular — cada uno leyendo y
escribiendo los registros de hardware directamente.

A mitad de semana el backend se reorganizó en torno a un pipeline SSA. Es lo que
hizo tratables las funciones más difíciles — tablas de vectores de interrupción
conscientes del dispositivo y plegado de funciones constantes.
