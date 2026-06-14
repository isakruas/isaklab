---
title: Running AVR firmware without the hardware
date: 2026-06-14
tags: avr, ik8b, ikide
summary: Two problems on the AVR toolchain — simulating peripherals to develop without a board, and emitting correct code per core.
---

Two problems took the week on the AVR toolchain: simulating hardware faithfully
enough to develop without a board, and emitting correct code for the different AVR
cores.

**Running without hardware.** For the IDE to run and inspect a program, the VM
(ik8bvm) has to behave like the peripherals, not just the CPU. This week it gained
capture of all program I/O and modeling of both directions of an SPI exchange, a
TWI master, UART receive, and ADC reads. The ikide virtual breadboard — LEDs,
buttons, displays, a joystick — rests on that: each part is a device wired to pins
that reacts, in real time, to what the simulated program writes. That is what makes
it possible to write and test firmware without flashing anything.

**Correct code per core.** The AVRs are not a single target. The reduced core
(AVRrc) on the smaller parts uses one-word interrupt vectors instead of two and
wraps the program counter on parts of 8 KB or less; the newer cores (XT/XM) have
direct I/O access and a different TWI. The compiler had been emitting code in the
classic model, which breaks silently on those parts. The fix was to make codegen
aware of the core and the part, emitting the right vectors and addressing for each
target.

The underlying shift on both fronts is the same: stop assuming a single target and
describe each part — data spaces, peripherals, core — in tables the compiler and
the VM consult.
