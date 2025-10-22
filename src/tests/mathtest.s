.include "lib/os.s"
.include "lib/io.s"
.include "lib/math.s"
.include "lib/random.s"


_start:

	li		a0, 13
	li		a1, 24
	call	multest

	li		a0, 1
	li		a1, 4
	call	multest

	li		a0, 0
	li		a1, 7
	call	multest

	li		a0, 7
	li		a1, 0
	call	multest

	li		a0, 0
	li		a1, 0
	call	multest


	li		s0, $ff

1:
	call	random
	and		s1, a0, s0
	
	call	random
	and		a0, a0, s0

	mv		a1, s1
	call	multest

	j		1b


	ebreak


multest:
	addi	sp, sp, -8
	sw		ra, (sp)
	sw		a0, 2(sp)
	sw		a1, 4(sp)

	call	printnum

	call	printimm
	.asciz " * "

	lw		a0, 4(sp)
	call	printnum

	call	printimm
	.asciz " = "

	lw		a0, 2(sp)
	lw		a1, 4(sp)
	call	mul16
	sw		a0, 6(sp)
	call	printnum

	li		a0, 10
	call	putchar

	lw		a0, 4(sp)
	beqz	a0, 2f

	lw		a0, 6(sp)
	call	printnum

	call	printimm
	.asciz " / "

	lw		a0, 4(sp)
	call	printnum

	call	printimm
	.asciz " = "

	lw		a0, 6(sp)
	lw		a1, 4(sp)
	call	div
	sw		a0, 6(sp)

	call	printnum

	lw		a0, 6(sp)
	lw		a1, 2(sp)
	beq		a0, a1, 1f

	call	printimm
	.asciz " (mismatch)"
1:

	li		a0, 10
	call	putchar

2:
	lw		ra, (sp)
	addi	sp, sp, 8
	ret

