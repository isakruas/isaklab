---
title: Rodar firmware AVR sem o hardware
date: 2026-06-14
tags: avr, ik8b, ikide
summary: Dois problemas no toolchain AVR — simular periféricos para desenvolver sem placa e gerar código correto por núcleo.
---

Dois problemas ocuparam a semana no toolchain AVR: simular hardware com fidelidade
suficiente para desenvolver sem placa, e gerar código correto para os diferentes
núcleos AVR.

**Rodar sem hardware.** Para a IDE executar e inspecionar um programa, a VM
(ik8bvm) precisa se comportar como os periféricos, não só como a CPU. Nesta semana
ela passou a capturar todo o I/O do programa e a modelar os dois sentidos de uma
troca SPI, um mestre TWI, a recepção UART e leituras de ADC. Sobre isso a protoboard
virtual da ikide — LEDs, botões, displays, um joystick — funciona: cada peça é um
dispositivo ligado a pinos que reage, em tempo real, ao que o programa simulado
escreve. É o que permite escrever e testar firmware sem gravar nada.

**Código correto por núcleo.** Os AVR não são um alvo só. O núcleo reduzido (AVRrc)
dos menores usa vetores de interrupção de uma palavra em vez de duas e faz
wraparound no contador de programa em peças de até 8 KB; os núcleos novos (XT/XM)
têm acesso direto a I/O e um TWI diferente. O compilador vinha emitindo código num
modelo clássico que quebra silenciosamente nesses casos. A correção foi tornar o
codegen ciente do núcleo e da peça, emitindo os vetores e o endereçamento certos
para cada alvo.

A mudança de fundo nas duas frentes é a mesma: parar de assumir um alvo único e
passar a descrever cada peça — espaços de dados, periféricos, núcleo — em tabelas
que o compilador e a VM consultam.
