---
title: avr-modular-system — a modular AVR driver library
date: 2024-05-29
tags: avr, embedded, c
summary: A C library of AVR peripheral drivers — I2C, SPI, and displays, with modules and protocols kept separate.
---

avr-modular-system collects AVR peripheral drivers in C, with the modules and the
protocols organized into separate directories.

The modules cover I2C (with the AT24C256 EEPROM), SPI, the ST7735S and ST7789
displays, the PCF8574 I/O expander, and the CP2102 USB-to-serial bridge. There are
also routines for drawing geometric shapes and a serial-communication project with a
GUI, plus clock (F_CPU) and SPI prescaler configuration.

avr-modular-system is on
[GitHub](https://github.com/isakruas/avr-modular-system).
