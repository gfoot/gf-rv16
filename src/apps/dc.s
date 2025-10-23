# dc-like stack-based calculator program
#
# Type numbers in decimal, terminated by non-numeric characters like spaces or operators.
#
# Operators operate on the top elements of the stack, which are popped and replaced with the result.
#
# Operators are +, -, *, /, %
#
# Other commands:
#
#    d = duplicate top stack entry
#    p = print top stack entry
#    q = quit

.include "lib/os.s"
.include "lib/math.s"
.include "lib/io.s"


globals = $3000
g_gotdigit = 0

stack = $4000
inputbuffer = $5000


_start:
	addi	sp, sp, -2
	sw		ra, (sp)

	li		s0, stack
	mv		s1, s0

2:
	li		a0, inputbuffer
	call	gets

	mv		s1, a0

1:
	lbu		a0, (s1)
	beqz	a0, 2b
	call	character
	bnez	a0, 2b
	addi	s1, s1, 1
	j		1b


digit:
	addi	a0, a0, -48

	lw		a1, (s0)
	slli	a2, a1, 2
	add		a1, a1, a2
	slli	a1, a1, 1
	add		a1, a1, a0
	sw		a1, (s0)

	lui		t0, globals
	li		a1, 1
	sb		a1, g_gotdigit(t0)

	ret


character:
	addi	sp, sp, -2
	sw		ra, (sp)

	mv		a1, a0
	addi	a1, a1, -48
	bltz	a1, 1f
	addi	a1, a1, -10
	bgez	a1, 1f

	call	digit

	li		a0, 0
	j		.return

1:
	call	command

.return:
	lw		ra, (sp)
	addi	sp, sp, 2
	ret


command:
	addi	sp, sp, -2
	sw		ra, (sp)

	lui		t0, globals
	lb		a1, g_gotdigit(t0)
	beqz	a1, 1f

	li		a1, 0
	sb		a1, g_gotdigit(t0)

	addi	s0, s0, 2
	sw		a1, (s0)

1:
	li		a1, .commandtable

1:
	lbu		a2, (a1)
	sub		t0, a2, a0
	beqz	t0, 1f
	addi	a1, a1, 4
	bnez	a2, 1b
	j		.badcommand

1:
	lw		a2, 2(a1)
	jalr	a2
	li		a0, 0

.return:
	lw		ra, (sp)
	addi	sp, sp, 2
	ret

.badcommand:
	mv		s1, a0

	call	printimm
	.asciz "Bad command '"

	mv		a0, s1
	call	putchar

	call	printimm
	.asciz "'\n"

	li		a0, 1
	j		.return
	

.commandtable:
	.word	'+', cmd_add
	.word	'-', cmd_sub
	.word	'*', cmd_mul
	.word	'/', cmd_div
	.word	'%', cmd_rem
	.word	' ', cmd_space
	.word	'd', cmd_dup
	.word	'p', cmd_print
	.word	'q', cmd_quit
	.word	0


cmd_add:
	lw		a0, -2(s0)
	lw		a1, -4(s0)
	add		a0, a0, a1
	sw		a0, -4(s0)
	addi	s0, s0, -2
	li		a0, 0
	sw		a0, (s0)
	ret

cmd_sub:
	lw		a1, -2(s0)
	lw		a0, -4(s0)
	sub		a0, a0, a1
	sw		a0, -4(s0)
	addi	s0, s0, -2
	li		a0, 0
	sw		a0, (s0)
	ret

cmd_mul:
	addi	sp, sp, -2
	sw		ra, (sp)

	lw		a0, -2(s0)
	lw		a1, -4(s0)
	call	mul16
	sw		a0, -4(s0)
	addi	s0, s0, -2
	li		a0, 0
	sw		a0, (s0)

	lw		ra, (sp)
	addi	sp, sp, 2
	ret

cmd_div:
	addi	sp, sp, -2
	sw		ra, (sp)

	lw		a1, -2(s0)
	lw		a0, -4(s0)
	call	div
	sw		a0, -4(s0)
	addi	s0, s0, -2
	li		a0, 0
	sw		a0, (s0)

	lw		ra, (sp)
	addi	sp, sp, 2
	ret

cmd_rem:
	addi	sp, sp, -2
	sw		ra, (sp)

	lw		a1, -2(s0)
	lw		a0, -4(s0)
	call	div
	sw		a2, -4(s0)
	addi	s0, s0, -2
	li		a0, 0
	sw		a0, (s0)

	lw		ra, (sp)
	addi	sp, sp, 2
	ret

cmd_space:
	ret

cmd_dup:
	lw		a0, -2(s0)
	addi	s0, s0, 2
	sw		a0, -2(s0)
	ret

cmd_print:
	addi	sp, sp, -2
	sw		ra, (sp)

	lw		a0, -2(s0)
	call	printnum
	call	printnl

	lw		ra, (sp)
	addi	sp, sp, 2
	ret

cmd_quit:
	ebreak
