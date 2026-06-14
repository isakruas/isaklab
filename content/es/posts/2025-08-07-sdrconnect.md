---
title: sdrconnect — extraer IQ en crudo de un SDR
date: 2025-08-07
tags: radio, sdr, python
summary: Una pequeña biblioteca para conectividad con SDR y captura de IQ en crudo, con análisis para ver qué se recibió realmente.
---

sdrconnect es una pequeña biblioteca Python para conectar a una radio definida por
software y extraer muestras de IQ en crudo — el flujo complejo en banda base sobre el
que se construye todo lo demás en un receptor.

La parte útil más allá de la conexión es ver qué capturaste: el análisis de IQ de la
biblioteca reporta métricas de señal y gráficos, así que una captura puede revisarse —
nivel, espectro, calidad básica — antes de intentar cualquier decodificación. Está
empaquetada y publicada en PyPI.

sdrconnect está en [GitHub](https://github.com/isakruas/sdrconnect).
