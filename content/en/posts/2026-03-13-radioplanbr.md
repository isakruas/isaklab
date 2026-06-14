---
title: radioplanbr — RF coverage planning in the browser
date: 2026-03-13
tags: radio, propagation, web
summary: A browser tool for amateur RF planning — propagation models, real-time ionospheric data, and antenna patterns on a map.
---

radioplanbr is a browser tool for planning amateur-radio coverage: where a signal
reaches, given terrain, antenna, and band. It runs entirely client-side, with no
server of its own.

**Propagation as models.** Coverage is estimated with established path-loss models
— Okumura-Hata, COST-231, ECC-33, Friis, Ericsson — selected by band and
environment, with terrain and line-of-sight taken into account rather than assuming
free space.

**HF is a different problem.** Above VHF, coverage is mostly geometry; on HF it
depends on the ionosphere, which changes by the hour. radioplanbr adds an HF skywave
model fed by real-time ionospheric data from NOAA, so a prediction reflects current
conditions instead of a static assumption.

**The map carries the detail.** On top of the coverage estimate, the map shows the
antenna radiation diagram rotated by azimuth, polarization, Maidenhead grid
locators, and the CQ/ITU radio zones for the transmit site. Repeaters can be
registered and persisted locally, imported and exported as JSON.

radioplanbr is on [GitHub](https://github.com/isakruas/radioplanbr).
