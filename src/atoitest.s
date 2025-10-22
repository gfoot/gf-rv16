.include "lib/os.s"
.include "lib/io.s"
.include "lib/math.s"
.include "lib/random.s"
.include "lib/std.s"
.include "lib/str.s"
.include "lib/mem.s"


_start:
	addi	sp, sp, -4
	sw		ra, (sp)

	la		a0, testcases

1:
	mv		s0, a0

	li		a0, '"'
	call	putchar

	mv		a0, s0
	call	puts

	call	printimm
	.asciz "\" => "

	mv		a0, s0
	call	atoi

	mv		s1, a0

	call	printnum

	li		a0, 10
	call	putchar

	mv		a0, s0
	call	strlen
	add		a0, s0, a0    # a0 points to null terminator
	addi	a0, a0, 4     # skip null terminator, and next word, plus one for rounding
	andi	a0, a0, -2    # round back down

	lw		a1, -2(a0)
	bne		s1, a1, 1f    # check result matches expectation

	la		s0, testcases_end
	bne		s0, a0, 1b

	j		2f

1:
	sw		a1, 2(sp)

	call	printimm
	.asciz "Test failed"
	li		a0, 10
	call	putchar

	mv		a0, s0
	call	puts

	li		a0, 32
	call	putchar

	mv		a0, s1
	call	printhex16

	li		a0, 32
	call	putchar

	lw		a0, 2(sp)
	call	printhex16

	li		a0, 10
	call	putchar

	ebreak

2:
	call	printimm
	.asciz "Tests passed"

	ebreak


testcases:
	.asciz " -123junk"
	.word -123

	.asciz " +321dust"
	.word 321

	.asciz "0"
	.word 0

	.asciz "0042"
	.word 42

	.asciz "0x2A"
	.word 0

	.asciz "junk"
	.word 0

	.asciz "2147483648"
	.word -2147483648

testcases_end:

