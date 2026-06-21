---
title: ikOS — a cooperative kernel running on a real AVR
date: 2026-06-21
tags: ikos, avr, ik8b, ikide
summary: This week I got ikOS, a small cooperative kernel for 8-bit AVR, running stably on a real board. The bugs that only showed up on hardware, and how I tracked each one down.
---

This week I finally got ikOS running stably on a real ATmega32, not just in the
simulator. ikOS is a small cooperative kernel I wrote in the ik language, for 8-bit
AVR microcontrollers. For me it's a milestone: it's the missing piece on top of
everything I've been building for a good while, the virtual machine, the language,
the
compiler and the IDE. In the video below I tell that whole story; here I want to talk
about what gave me trouble this week.

<video controls preload="none" style="width:100%;height:auto" src="https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_en_sub.mp4"></video>

*Also dubbed in [Portuguese](https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_pt_sub.mp4) and [Spanish](https://s3.us-east-1.amazonaws.com/isaklab.com/media/videos/2026/06/21/ikos_es_sub.mp4).*

First, what ikOS actually is: a kernel that fits in 32 KB. Each process has its own
stack and runs until it decides to give up the CPU, with `yield`, `sleep` or `exit`;
the scheduler keeps rotating through the ready processes, saving and restoring each
one's context. On top of that there's a shell you reach over the serial port, a
filesystem on the EEPROM, and a small scripting language. The mascot is an ant, Iki.
Ants are small, and only get things done by working together, which is more or less
the idea behind cooperative scheduling.

![ikOS shell responding over the UART in ikide's serial monitor.](/media/images/2026/06/21/ikide-ikos-shell.png)

*The ikOS shell answering over serial, in ikide's monitor.*

What really gave me grief was getting it to run on hardware. In the simulator it
worked perfectly, but on the real board it reset in an endless loop, reprinting the
boot banner forever. Instead of poking around in the dark, I decided to fix the
simulator itself until it behaved exactly like the real chip, and then chase the bug
there, which is far faster than reflashing the board every time.

In the end there were three bugs, and all three only showed up on hardware. The worst
was in the context switch. The simulator treated the program counter in bytes, so the
code built the return address in bytes too; but the real AVR's `RET` expects a word
address, so the switch jumped to double the address and landed in the middle of
nowhere. There was also the byte order: the AVR stores the high byte at the lower
stack address, the opposite of what the simulator was doing. The second bug was the
watchdog, which I just hadn't dealt with. On boards that boot via a watchdog reset, a
bit stays set, `WDRF`, that forces the watchdog to stay on, so the normal "disable"
did nothing; I had to clear that bit first. The third was kind of silly: some 8-bit
registers were declared as 16-bit in the library, and the 16-bit write ended up
zeroing the neighboring register, `SPL`, which corrupted the stack and reset the chip.

For this kernel to exist, the compiler had to pitch in. The main thing was a new
instruction, `@swtch`, that saves the registers and the stack pointer and switches
from one stack to another, something you can't write in ik alone. I also had to trim
the code size, because the kernel was bumping against the 32 KB ceiling; with some
compiler optimizations I got almost 900 bytes back without dropping any features. And
the tests now run inside the IDE itself, automatically.

![ikide editor with the ikOS source and the AVR simulator alongside.](/media/images/2026/06/21/ikide-ikos-editor-sim.png)

*ikOS in the ikide editor, with the simulator running on the right.*

What makes me happy in the end is simple: ikOS runs the same on the board and in the
simulator. And it only runs the same because the simulator became faithful to the real
chip. It's tagged v0.1.0, codename "Sauva".
