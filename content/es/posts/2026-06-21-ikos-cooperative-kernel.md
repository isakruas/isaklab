---
title: ikOS — un kernel cooperativo corriendo en un AVR de verdad
date: 2026-06-21
tags: ikos, avr, ik8b, ikide
summary: Esta semana puse ikOS, un kernel cooperativo pequeño para AVR de 8 bits, a correr estable en una placa de verdad. Los bugs que solo aparecían en el hardware y cómo encontré cada uno.
---

Esta semana por fin puse ikOS a correr estable en un ATmega32 de verdad, no solo en
el simulador. ikOS es un kernel cooperativo bien pequeño que escribí en el lenguaje
ik, para microcontroladores AVR de 8 bits. Para mí es un hito: es la pieza que faltaba
encima de todo lo que vengo construyendo desde hace un buen tiempo, la máquina
virtual, el
lenguaje, el compilador y el IDE. En el video de abajo cuento toda esa historia; en
este texto quería hablar de lo que me dio trabajo esta semana.

<video controls preload="none" style="width:100%;height:auto" src="https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_es_sub.mp4"></video>

*También doblado en [portugués](https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_pt_sub.mp4) e [inglés](https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_en_sub.mp4).*

Primero, qué es ikOS: un kernel que cabe en 32 KB. Cada proceso tiene su propia pila y
corre hasta que decide ceder la CPU, con `yield`, `sleep` o `exit`; el planificador va
alternando entre los procesos listos, guardando y restaurando el contexto de cada uno.
Encima de eso hay un shell al que entras por el puerto serial, un sistema de archivos
en la EEPROM y un pequeño lenguaje de script. La mascota es una hormiga, Iki. Las
hormigas son pequeñas y solo logran las cosas trabajando en conjunto, que es más o
menos la idea de la planificación cooperativa.

![Shell de ikOS respondiendo por la UART en el monitor serial de ikide.](/media/images/2026/06/21/ikide-ikos-shell.png)

*El shell de ikOS respondiendo por serial, en el monitor de ikide.*

Lo que de verdad me costó fue hacerlo correr en el hardware. En el simulador
funcionaba perfecto, pero en la placa real se reiniciaba en un bucle sin fin,
reimprimiendo el banner de arranque para siempre. En vez de andar probando a ciegas,
decidí mejorar el propio simulador hasta que se comportara igual al chip real, y
ahí cazar el bug, mucho más rápido que regrabar la placa a cada rato.

Al final eran tres bugs, y los tres solo aparecían en el hardware. El peor estaba en
el cambio de contexto. El simulador trataba el contador de programa en bytes, así que
el código armaba la dirección de retorno en bytes también; pero el `RET` del AVR de
verdad espera una dirección en palabras, entonces el cambio saltaba al doble de la
dirección y caía en cualquier lado. También estaba el orden de los bytes: el AVR
guarda el byte más alto en la dirección más baja de la pila, al revés de lo que hacía
el simulador. El segundo bug era el watchdog, que simplemente no había tratado. En
placas que arrancan por un reset de watchdog queda un bit activo, el `WDRF`, que fuerza
al watchdog a seguir encendido, así que el "apagar" normal no hacía nada; tuve que
limpiar ese bit antes. El tercero era medio tonto: unos registros de 8 bits estaban
declarados como 16 bits en la biblioteca, y la escritura de 16 bits terminaba poniendo
en cero el registro vecino, el `SPL`, lo que corrompía la pila y reiniciaba el chip.

Para que este kernel existiera, el compilador tuvo que dar una mano. Lo principal
fue una instrucción nueva, `@swtch`, que guarda los registros y el puntero de pila y
cambia de una pila a otra, algo que no se puede escribir solo en ik. También tuve que
reducir el tamaño del código, porque el kernel estaba rozando el techo de los 32 KB;
con algunas optimizaciones en el compilador recuperé casi 900 bytes sin sacar ninguna
funcionalidad. Y las pruebas ahora corren dentro del propio IDE, de forma automática.

![Editor de ikide con el código de ikOS y el simulador AVR al lado.](/media/images/2026/06/21/ikide-ikos-editor-sim.png)

*ikOS en el editor de ikide, con el simulador corriendo a la derecha.*

Lo que me deja contento al final es simple: ikOS corre igual en la placa y en el
simulador. Y corre igual solo porque el simulador se volvió fiel al chip de verdad.
Está etiquetado como v0.1.0, con el nombre clave "Sauva".
