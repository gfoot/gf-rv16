.include "lib/os.s"
.include "lib/random.s"
.include "lib/io.s"

_start:
	li		sp, -4

	li		s0, 16
1:
	call	random
	addi	s0, s0, -1
	bnez	s0, 1b

	li		s0, 10000
1:
	call	random
	call	printbin16

	addi	s0, s0, -1
	bnez	s0, 1b

	call	exit



printbin16:
	addi	sp, sp, -6
	sw		ra, (sp)
	sw		s0, 2(sp)
	sw		s1, 4(sp)

	li		s1, 16
	mv		s0, a0

1:
	sltz	a0, s0
	addi	a0, a0, 48
	call	putchar

	slli	s0, s0, 1
	
	addi	s1, s1, -1
	bnez	s1, 1b

	lw		ra, (sp)
	lw		s0, 2(sp)
	lw		s1, 4(sp)
	addi	sp, sp, 6
	ret

