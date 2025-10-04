.include "lib/random.s"
.include "lib/io.s"

_start:
	li		s0, 10000

1:
	li		a0, 16
	call	random3
	call	printbin16

	addi	s0, s0, -1
	bnez	s0, 1b

	call	exit



printbin16:
	addi	sp, sp, -2
	sw		ra, (sp)

	li		a1, 16
	mv		t0, a0

1:
	sltz	a0, t0
	addi	a0, a0, 48
	call	putchar

	slli	t0, t0, 1
	
	addi	a1, a1, -1
	bnez	a1, 1b

	lw		ra, (sp)
	addi	sp, sp, 2
	ret

