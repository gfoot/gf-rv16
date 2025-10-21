# Test for stack trace dumping
#
# Some mutually-recursive functions that will run for a while and then trigger a fault
# causing the execution environment to print a stack trace
#
# For now all the functions have the same standard stack frame, with no frameless leaf
# functions, tail calls, local variables, or shorter frames that don't save s0 and s1


.include "lib/os.s"
.include "lib/io.s"


_start:
	li		sp, 0

	li		a0, 74
	call	torquay

	call	exit


printnumspace:
	addi	sp, sp, -6
	sw		s1, 4(sp)
	sw		s0, 2(sp)
	sw		ra, 0(sp)

	mv		s0, a0

	call	printnum

	li		a0, ' '
	call	putchar

	mv		a0, s0

	lw		s1, 4(sp)
	lw		s0, 2(sp)
	lw		ra, 0(sp)
	addi	sp, sp, 6
	ret

torquay:
	addi	sp, sp, -6
	sw		s1, 4(sp)
	sw		s0, 2(sp)
	sw		ra, 0(sp)

	andi	a1, a0, 1
	bnez	a1, 1f

	call	nebraska
	j		2f

1:
	call	barcelona

2:
	lw		s1, 4(sp)
	lw		s0, 2(sp)
	lw		ra, 0(sp)
	addi	sp, sp, 6
	ret


nebraska:
	addi	sp, sp, -14
	sw		s1, 4(sp)
	sw		s0, 2(sp)
	sw		ra, 0(sp)

	call	printnumspace

	srli	a0, a0, 1
	call	alexandria

	lw		s1, 4(sp)
	lw		s0, 2(sp)
	lw		ra, 0(sp)
	addi	sp, sp, 14
	ret


barcelona:
	addi	sp, sp, -10
	sw		s1, 4(sp)
	sw		s0, 2(sp)
	sw		ra, 0(sp)

	call	printnumspace

	slli	a1, a0, 1
	add		a0, a0, a1
	addi	a0, a0, 1
	call	nebraska

	lw		s1, 4(sp)
	lw		s0, 2(sp)
	lw		ra, 0(sp)
	addi	sp, sp, 10
	ret


alexandria:
	addi	sp, sp, -2
	sw		ra, 0(sp)

	call	nairobi

	call	torquay

	lw		ra, 0(sp)
	addi	sp, sp, 2
	ret


nairobi:	
	addi	a1, a0, -1
	bnez	a1, 1f

	ebreak

1:
	ret

