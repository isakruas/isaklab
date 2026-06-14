---
title: Ejecutar firmware AVR sin el hardware
date: 2026-06-14
tags: avr, ik8b, ikide
summary: Dos problemas en el toolchain AVR — simular periféricos para desarrollar sin placa y emitir código correcto por núcleo.
---

Dos problemas ocuparon la semana en el toolchain AVR: simular hardware con fidelidad
suficiente para desarrollar sin placa, y emitir código correcto para los distintos
núcleos AVR.

**Ejecutar sin hardware.** Para que el IDE ejecute e inspeccione un programa, la VM
(ik8bvm) tiene que comportarse como los periféricos, no solo como la CPU. Esta
semana pasó a capturar todo el I/O del programa y a modelar ambos sentidos de un
intercambio SPI, un maestro TWI, la recepción UART y lecturas de ADC. Sobre eso
funciona la protoboard virtual de ikide — LEDs, botones, pantallas, un joystick:
cada pieza es un dispositivo conectado a pines que reacciona, en tiempo real, a lo
que el programa simulado escribe. Es lo que permite escribir y probar firmware sin
grabar nada.

**Código correcto por núcleo.** Los AVR no son un solo objetivo. El núcleo reducido
(AVRrc) de los más pequeños usa vectores de interrupción de una palabra en vez de
dos y hace wraparound del contador de programa en piezas de hasta 8 KB; los núcleos
nuevos (XT/XM) tienen acceso directo a I/O y un TWI distinto. El compilador venía
emitiendo código en el modelo clásico, que se rompe en silencio en esos casos. La
corrección fue hacer el codegen consciente del núcleo y de la pieza, emitiendo los
vectores y el direccionamiento correctos para cada objetivo.

El cambio de fondo en ambos frentes es el mismo: dejar de asumir un objetivo único y
pasar a describir cada pieza — espacios de datos, periféricos, núcleo — en tablas
que el compilador y la VM consultan.
