---
title: Um receptor coerente para o cdss
date: 2026-05-15
tags: radio, dsp, fortran
summary: Construir o lado receptor de um modem DSSS — recuperação de temporização, desvio de frequência de portadora e rastreio de fase ao longo do quadro.
---

O cdss é um modem digital CHIRP-DSSS-Polar. Esta foi a parte do receptor — onde um
canal real (deriva, desvio, ruído) precisa ser desfeito antes de qualquer bit ser
lido.

**Recuperar a temporização.** O receptor não sabe onde um símbolo começa. Ele usa
recuperação de temporização de segunda ordem com interpolação linear entre amostras,
que rastreia não só um desvio de amostragem fixo, mas um que muda lentamente — o tipo
que dois clocks livres, um em cada ponta, inevitavelmente produzem.

**Corrigir o desvio de frequência de portadora.** Dois rádios nunca concordam
exatamente na frequência; o desvio residual gira o sinal e, deixado solto, destrói os
símbolos. O receptor estima e corrige esse desvio durante a sincronização de
preâmbulo, antes de o payload começar, e então mantém o rastreio de fase e frequência
ao longo do quadro para que a correção não escorregue de volta.
