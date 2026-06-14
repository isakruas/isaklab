---
title: sdrconnect — extrair IQ bruto de um SDR
date: 2025-08-07
tags: radio, sdr, python
summary: Uma pequena biblioteca para conectividade com SDR e captura de IQ bruto, com análise para ver o que de fato foi recebido.
---

O sdrconnect é uma pequena biblioteca Python para conectar a um rádio definido por
software e puxar amostras de IQ brutas — o fluxo complexo em banda base sobre o qual
todo o resto de um receptor é construído.

A parte útil além da conexão é ver o que você capturou: a análise de IQ da biblioteca
reporta métricas de sinal e gráficos, então uma captura pode ser conferida — nível,
espectro, qualidade básica — antes de qualquer tentativa de decodificação. Ela é
empacotada e publicada no PyPI.

O sdrconnect está no [GitHub](https://github.com/isakruas/sdrconnect).
