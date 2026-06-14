---
title: avr-modular-system — uma biblioteca modular de drivers AVR
date: 2024-05-29
tags: avr, embarcado, c
summary: Uma biblioteca de drivers de periférico para AVR em C — I2C, SPI e displays, com módulos e protocolos separados.
---

O avr-modular-system reúne drivers de periférico para AVR em C, com os módulos e os
protocolos organizados em diretórios separados.

Os módulos cobrem I2C (com a EEPROM AT24C256), SPI, os displays ST7735S e ST7789, o
expansor de I/O PCF8574 e o conversor USB-serial CP2102. Há ainda rotinas para
desenhar formas geométricas e um projeto de comunicação serial com interface
gráfica, além de configuração de clock (F_CPU) e do prescaler do SPI.

O avr-modular-system está no
[GitHub](https://github.com/isakruas/avr-modular-system).
