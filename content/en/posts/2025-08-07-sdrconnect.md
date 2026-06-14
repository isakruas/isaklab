---
title: sdrconnect — getting raw IQ out of an SDR
date: 2025-08-07
tags: radio, sdr, python
summary: A small library for SDR connectivity and raw IQ capture, with analysis to see what was actually received.
---

sdrconnect is a small Python library for connecting to a software-defined radio and
pulling raw IQ samples — the complex baseband stream everything else in a receiver
is built on.

The useful part beyond the connection is seeing what you captured: the library's IQ
analysis reports signal metrics and plots, so a capture can be checked — level,
spectrum, basic quality — before any decoding is attempted. It is packaged and
published to PyPI.

sdrconnect is on [GitHub](https://github.com/isakruas/sdrconnect).
