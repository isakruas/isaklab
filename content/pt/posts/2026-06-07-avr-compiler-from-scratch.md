---
title: Começando um compilador AVR do zero
date: 2026-06-07
tags: avr, ik8b, compiladores
summary: As primeiras decisões do ik8b — armazenamento explícito, alocação de registradores e uma biblioteca padrão sem runtime de C.
---

Comecei o ik8b: um compilador de uma linguagem pequena, `ik`, direto para firmware
AVR, sem assembler, linker ou runtime de C externos. A semana foi sobre as decisões
que precisam vir antes de qualquer coisa disso funcionar.

**Onde um valor mora faz parte do tipo.** O `ik` exige que toda declaração diga seu
armazenamento — RAM, EEPROM ou flash — e separa primitivos escalares (`i8`, `i16`,
`bool`, `char`) dos tipos mapeados em registrador (`r8`, `r16`). Numa peça de 8 bits
com algumas centenas de bytes de RAM, deixar o armazenamento explícito mantém o
código gerado previsível.

**Alocação de registradores.** Num chip de 32 registradores, o backend ganhou um
alocador por coloração de grafo sobre análise de liveness do CFG, e em seguida a
correção que isso força: preservar registradores de operando e de argumento através
de chamadas aninhadas, para que uma chamada dentro de uma expressão não sobrescreva
os valores ao redor.

**Sem runtime de C, é preciso entregar uma biblioteca padrão.** Sem a libc não há a
que recorrer, então a linguagem carrega a sua: uma fonte ASCII 5×7 em flash,
literais de string em flash com escapes `\x`, e drivers para ADC, PWM, timers,
sleep, watchdog e um ring buffer — cada um lendo e escrevendo os registradores de
hardware diretamente.

No meio da semana o backend foi reorganizado em torno de um pipeline SSA. É o que
tornou tratáveis os recursos mais difíceis — tabelas de vetores de interrupção
cientes do dispositivo e dobramento de funções constantes.
