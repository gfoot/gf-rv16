.include "../lib/os.s"
.include "../lib/str.s"
.include "../lib/mem.s"
.include "../lib/io.s"
.include "../lib/random.s"


_start:
	li		s0, $4000
	li		s1, $100

1:
	call	random
	sw		a0, (s0)
	addi	s0, s0, 2
	addi	s1, s1, -2
	bnez	s1, 1b


	li		a0, $4100
	li		a1, $4000
	li		a2, $100
	call	memcpy

	li		a1, $4000
	li		a2, $100
	li		s1, $4200
1:
	lw		t0, (a0)
	lw		s0, (a1)
	xor		s0, s0, t0
	addi	s0, s0, 1
	sw		s0, (s1)

	addi	a0, a0, 2
	addi	a1, a1, 2
	addi	s1, s1, 2
	addi	a2, a2, -2
	bnez	a2, 1b

	ebreak

