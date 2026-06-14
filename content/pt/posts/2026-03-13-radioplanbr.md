---
title: radioplanbr — planejamento de cobertura de RF no navegador
date: 2026-03-13
tags: radio, propagacao, web
summary: Uma ferramenta de navegador para planejamento de RF amador — modelos de propagação, dados ionosféricos em tempo real e padrões de antena no mapa.
---

O radioplanbr é uma ferramenta de navegador para planejar cobertura de radioamadorismo:
até onde um sinal chega, dados o terreno, a antena e a banda. Roda inteiramente no
cliente, sem servidor próprio.

**Propagação como modelos.** A cobertura é estimada com modelos de perda de percurso
estabelecidos — Okumura-Hata, COST-231, ECC-33, Friis, Ericsson — escolhidos por
banda e ambiente, com terreno e linha de visada levados em conta em vez de assumir
espaço livre.

**HF é um problema diferente.** Acima de VHF, a cobertura é quase só geometria; em HF
ela depende da ionosfera, que muda a cada hora. O radioplanbr adiciona um modelo de
onda celeste para HF alimentado por dados ionosféricos em tempo real da NOAA, para que
a previsão reflita as condições atuais em vez de uma suposição estática.

**O mapa carrega o detalhe.** Sobre a estimativa de cobertura, o mapa mostra o
diagrama de irradiação da antena girado por azimute, a polarização, os localizadores
de grade Maidenhead e as zonas de rádio CQ/ITU do ponto de transmissão. Repetidoras
podem ser cadastradas e persistidas localmente, importadas e exportadas em JSON.

O radioplanbr está no [GitHub](https://github.com/isakruas/radioplanbr).
