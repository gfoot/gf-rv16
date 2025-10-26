# GF-RV16

An experimental 16-bit RISC-V ISA which I hope to build hardware to 
support one day

The tools, documents, and source code here are to validate that the 
ISA is reasonable - i.e. that it is both useful (easy enough to 
write code with) and implementable (i.e. instructions can be 
encoded reasonably in a 16-bit encoding space, and can execute on a 
relatively simple back end core)

See the wiki on github for more information: https://github.com/gfoot/gf-rv16/wiki

# Python tools

## Assembling some code, running the simulator

  $ python tools/assem.py src/testcode.s

  $ python tools/sim.py src/testcode.s --trace


## Library tests

  $ python tools/sim.py src/randtest.s

Outputs a lot of random bits that can be fed into a randomness checker.

  $ python tools/sim.py src/malloctest.s

Tests basic allocation and freeing behaviour, including coallescing adjacent free regions

  $ python tools/sim.py src/malloctest2.s

Stress-tests allocation and freeing randomly, small and large blocks, to try to fragment the
heap and make life hard for the allocator


## Analysing some code

  $ python tools/stats.py src/malloctest2.s

This gathers statistics about instruction usage and immediate ranges used by the assembled code.


## ISA metrics

  $ python tools/isatest.py

Prints information about how much of the 16-bit encoding space is used for each instruction, 
so you can experiment a bit with immediate constant bit widths and see if everything is likely
to fit.

Note that tools/isaprops.py has - along with its own definitions about how immediate constants
are encoded - some code to determine the actual immediate values that each instruction supports,
so that it can check the assembled code didn't violate them, as well as explain what the 
restrictions are.  Maybe it should be combined somehow with isatest.py.


# Source code

src contains various test programs, many of which are runnable through the simulator.

pseudotest.s is a bit different - originally intended to check generation of real instructions
to support pseudoinstructions, it evolved into a more general test suite for the assembler.  So
it is not intended to be executed - but when it is assembled, the assembler will check that the
generated code matches the expectations listed in comments in pseudotest, and report errors for
any differences.

src/lib contains library code used by many of the programs, including basic I/O, string handling,
and malloc/free, using approximately the same interfaces as C's standard library does.


# Documentation

See the wiki on github for more information: https://github.com/gfoot/gf-rv16/wiki

