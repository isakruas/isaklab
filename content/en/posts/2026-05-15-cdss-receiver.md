---
title: A coherent receiver for cdss
date: 2026-05-15
tags: radio, dsp, fortran
summary: Building the receiver side of a DSSS modem — timing recovery, carrier-frequency offset, and phase tracking that holds across a frame.
---

cdss is a CHIRP-DSSS-Polar digital modem. This was the receiver — where a real
channel (drift, offset, noise) has to be undone before any bit is read.

**Recovering timing.** The receiver doesn't know where a symbol begins. It uses
second-order timing recovery with linear interpolation between samples, which
tracks not just a fixed sampling offset but a slowly changing one — the kind two
free-running clocks, one on each end, inevitably produce.

**Correcting carrier-frequency offset.** Two radios never agree exactly on
frequency; the residual offset rotates the signal and, left alone, destroys the
symbols. The receiver estimates and corrects this offset during preamble
synchronization, before the payload starts, then keeps phase and frequency tracking
running through the frame so the correction doesn't drift back out.
