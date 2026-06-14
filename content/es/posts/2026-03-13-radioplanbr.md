---
title: radioplanbr — planificación de cobertura de RF en el navegador
date: 2026-03-13
tags: radio, propagacion, web
summary: Una herramienta de navegador para planificación de RF amateur — modelos de propagación, datos ionosféricos en tiempo real y patrones de antena en el mapa.
---

radioplanbr es una herramienta de navegador para planificar cobertura de
radioafición: hasta dónde llega una señal, dados el terreno, la antena y la banda.
Corre enteramente en el cliente, sin servidor propio.

**Propagación como modelos.** La cobertura se estima con modelos de pérdida de
trayecto establecidos — Okumura-Hata, COST-231, ECC-33, Friis, Ericsson —
seleccionados por banda y entorno, con terreno y línea de vista tenidos en cuenta en
vez de asumir espacio libre.

**HF es un problema distinto.** Por encima de VHF, la cobertura es casi solo
geometría; en HF depende de la ionosfera, que cambia cada hora. radioplanbr agrega un
modelo de onda celeste para HF alimentado por datos ionosféricos en tiempo real de la
NOAA, para que una predicción refleje las condiciones actuales en vez de una
suposición estática.

**El mapa lleva el detalle.** Sobre la estimación de cobertura, el mapa muestra el
diagrama de irradiación de la antena girado por azimut, la polarización, los
localizadores de cuadrícula Maidenhead y las zonas de radio CQ/ITU del punto de
transmisión. Las repetidoras pueden registrarse y persistirse localmente, importarse
y exportarse en JSON.

radioplanbr está en [GitHub](https://github.com/isakruas/radioplanbr).
