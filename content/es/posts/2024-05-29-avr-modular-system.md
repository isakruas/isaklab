---
title: avr-modular-system — una biblioteca modular de drivers AVR
date: 2024-05-29
tags: avr, embebido, c
summary: Una biblioteca C de drivers de periférico AVR — I2C, SPI y pantallas, con módulos y protocolos separados.
---

avr-modular-system reúne drivers de periférico AVR en C, con los módulos y los
protocolos organizados en directorios separados.

Los módulos cubren I2C (con la EEPROM AT24C256), SPI, las pantallas ST7735S y ST7789,
el expansor de I/O PCF8574 y el puente USB-serial CP2102. También hay rutinas para
dibujar formas geométricas y un proyecto de comunicación serial con interfaz gráfica,
además de configuración de reloj (F_CPU) y del prescaler del SPI.

avr-modular-system está en
[GitHub](https://github.com/isakruas/avr-modular-system).
