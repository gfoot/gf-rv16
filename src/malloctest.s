.include "lib/vectors.s"
.include "lib/str.s"
.include "lib/mem.s"
.include "lib/io.s"

_start:

	li		sp, 0

	li		a0, $8000
	li		a1, _top
	sub		a0, a0, a1
	call	alloc_init


	la		s0, sizelist
	
1:
	lw		s1, (s0)
	beqz	s1, 1f

	mv		a0, s1
	call	logged_malloc

	addi	sp, sp, -2
	sw		a0, (sp)

	call	printhex16

	li		a0, 10
	call	putchar
	li		a0, 13
	call	putchar

	addi	s0, s0, 2
	j		1b

1:

	call	heapdump

	lw		a0, 4(sp)
	call	logged_free
	call	heapdump

	lw		a0, 6(sp)
	call	logged_free
	call	heapdump

	lw		a0, 2(sp)
	call	logged_free
	call	heapdump


	li		a0, 8
	call	logged_malloc
	call	heapdump


	lw		a0, (sp)
	call	logged_free
	call	heapdump


	call exit

sizelist:
	.word 8,32,256,16,2048,64,0

logged_free:
	addi	sp, sp, -4
	sw		ra, (sp)
	sw		s0, 2(sp)

	mv		s0, a0

	call	printimm
	.asciz "Freeing block "

	mv		a0, s0
	call	printhex16

	call	printimm
	.asciz "\r\n"

	mv		a0, s0
	call	free

	call	printimm
	.asciz "\r\n"

	lw		s0, 2(sp)
	lw		ra, (sp)
	addi	sp, sp, 4
	ret

logged_malloc:
	addi	sp, sp, -4
	sw		ra, (sp)
	sw		s0, 2(sp)

	mv		s0, a0

	call	printimm
	.asciz "Allocating "

	mv		a0, s0
	call	printnum

	call	printimm
	.asciz " bytes: "

	mv		a0, s0
	call	malloc

	mv		s0, a0
	call	printhex16

	call	printimm
	.asciz "\r\n"

	mv		a0, s0

	lw		s0, 2(sp)
	lw		ra, (sp)
	addi	sp, sp, 4
	ret

