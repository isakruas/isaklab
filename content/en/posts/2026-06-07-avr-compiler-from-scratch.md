---
title: Starting an AVR compiler from scratch
date: 2026-06-07
tags: avr, ik8b, compilers
summary: The first decisions in ik8b — explicit storage, register allocation, and a standard library with no C runtime.
---

I started ik8b: a compiler from a small language, `ik`, straight to AVR firmware,
with no external assembler, linker, or C runtime. The week was about the decisions
that have to come before any of that works.

**Where a value lives is part of the type.** `ik` requires every declaration to
name its storage — RAM, EEPROM, or flash — and separates scalar primitives (`i8`,
`i16`, `bool`, `char`) from register-mapped types (`r8`, `r16`). On an 8-bit part
with a few hundred bytes of RAM, making storage explicit keeps the generated code
predictable.

**Register allocation.** On a chip with 32 registers, the backend got a
graph-coloring allocator over CFG liveness analysis, and then the fix it forces:
preserving operand and argument registers across nested calls, so a call inside an
expression does not clobber the values around it.

**No C runtime means shipping a standard library.** Without libc there is nothing
to fall back on, so the language carries its own: a flash-backed 5×7 ASCII font,
flash string literals with `\x` escapes, and drivers for ADC, PWM, timers, sleep,
the watchdog, and a ring buffer — each reading and writing the hardware registers
directly.

Midweek the backend was reorganized around an SSA pipeline. That is what made the
harder features tractable — device-aware interrupt vector tables and
constant-function folding.
