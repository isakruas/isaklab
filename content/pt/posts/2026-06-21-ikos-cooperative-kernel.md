---
title: ikOS — um kernel cooperativo rodando num AVR de verdade
date: 2026-06-21
tags: ikos, avr, ik8b, ikide
summary: Essa semana coloquei o ikOS, um kernel cooperativo pequeno pra AVR de 8 bits, pra rodar estável numa placa de verdade. Os bugs que só apareciam no hardware e como achei cada um.
---

Essa semana eu finalmente coloquei o ikOS pra rodar estável numa ATmega32 de
verdade, não só no simulador. O ikOS é um kernel cooperativo bem pequeno que eu
escrevi na linguagem ik, pra microcontrolador AVR de 8 bits. Pra mim é um marco: é a
peça que faltava em cima de tudo que venho construindo há um bom tempo, a máquina
virtual, a
linguagem, o compilador e a IDE. No vídeo aqui embaixo eu conto essa história toda;
neste texto eu queria falar do que deu trabalho nesta semana.

<video controls preload="none" style="width:100%;height:auto" src="https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_pt_sub.mp4"></video>

*Também dublado em [inglês](https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_en_sub.mp4) e [espanhol](https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_es_sub.mp4).*

Primeiro, o que é o ikOS: um kernel que cabe em 32 KB. Cada processo tem a sua
própria pilha e roda até resolver ceder a CPU, com `yield`, `sleep` ou `exit`; o
escalonador fica alternando entre os processos prontos, salvando e restaurando o
contexto de cada um. Em cima disso tem um shell que você acessa pela serial, um
sistema de arquivos na EEPROM e uma pequena linguagem de script. O mascote é uma
formiga, a Iki. Formiga é pequena e só dá conta das coisas trabalhando junto, que é
mais ou menos a ideia do escalonamento cooperativo.

![Shell do ikOS respondendo por UART no monitor serial da ikide.](/media/images/2026/06/21/ikide-ikos-shell.png)

*O shell do ikOS respondendo pela serial, no monitor da ikide.*

O que mais me penou foi fazer ele rodar no hardware. No simulador funcionava redondo,
mas na placa de verdade ele resetava num loop sem fim, reimprimindo o banner de boot
pra sempre. Em vez de ficar tentando no escuro, resolvi melhorar o próprio simulador
até ele se comportar igual ao chip real, e aí caçar o bug ali dentro, que é bem
mais rápido do que regravar a placa toda hora.

No fim eram três bugs, e os três só apareciam no hardware. O pior estava na troca de
contexto. O simulador tratava o contador de programa em bytes, então o código montava
o endereço de retorno em bytes também; só que o `RET` do AVR de verdade espera um
endereço em palavras, então a troca pulava pro dobro do endereço e ia parar no meio do
nada. Tinha também a ordem dos bytes: o AVR guarda o byte mais alto no endereço mais
baixo da pilha, o contrário do que o simulador fazia. O segundo bug era o watchdog,
que eu simplesmente não tinha tratado. Em placas que dão boot por reset de watchdog
fica um bit ligado, o `WDRF`, que força o watchdog a continuar ativo, então o
"desliga" normal não fazia nada; tive que limpar esse bit antes. O terceiro era meio
bobo: uns registradores de 8 bits estavam declarados como 16 bits na biblioteca, e a
escrita de 16 bits acabava zerando o registrador vizinho, o `SPL`, o que corrompia a
pilha e reiniciava o chip.

Pra esse kernel existir, o compilador precisou dar uma ajuda. A principal foi
uma instrução nova, a `@swtch`, que salva os registradores e o ponteiro de pilha e
troca de uma pilha pra outra, uma coisa que não dá pra escrever só em ik. Também tive
que enxugar o tamanho do código, porque o kernel estava encostando no teto dos 32 KB;
com algumas otimizações no compilador deu pra recuperar quase 900 bytes sem cortar
nenhuma funcionalidade. E os testes passaram a rodar dentro da própria IDE,
automaticamente.

![Editor da ikide com o código do ikOS e o simulador AVR ao lado.](/media/images/2026/06/21/ikide-ikos-editor-sim.png)

*O ikOS no editor da ikide, com o simulador rodando à direita.*

O que me deixa contente no fim é simples: o ikOS roda igual na placa e no simulador. E
ele só roda igual porque o simulador ficou fiel ao chip de verdade. Tá marcado como
v0.1.0, com o codinome "Sauva".
