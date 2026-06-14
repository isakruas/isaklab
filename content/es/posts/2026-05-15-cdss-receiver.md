---
title: Un receptor coherente para cdss
date: 2026-05-15
tags: radio, dsp, fortran
summary: Construir el lado receptor de un módem DSSS — recuperación de temporización, desvío de frecuencia de portadora y seguimiento de fase a lo largo de la trama.
---

cdss es un módem digital CHIRP-DSSS-Polar. Esta fue la parte del receptor — donde un
canal real (deriva, desvío, ruido) debe deshacerse antes de leer cualquier bit.

**Recuperar la temporización.** El receptor no sabe dónde empieza un símbolo. Usa
recuperación de temporización de segundo orden con interpolación lineal entre
muestras, que sigue no solo un desvío de muestreo fijo, sino uno que cambia
lentamente — el tipo que dos relojes libres, uno en cada extremo, producen
inevitablemente.

**Corregir el desvío de frecuencia de portadora.** Dos radios nunca coinciden
exactamente en frecuencia; el desvío residual gira la señal y, si se deja suelto,
destruye los símbolos. El receptor estima y corrige ese desvío durante la
sincronización de preámbulo, antes de que empiece el payload, y luego mantiene el
seguimiento de fase y frecuencia a lo largo de la trama para que la corrección no se
escape de nuevo.
