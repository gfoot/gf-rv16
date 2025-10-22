.include "lib/os.s"
.include "lib/str.s"
.include "lib/io.s"
.include "lib/mem.s"

string_world:
	.asciz "world"

string_hello:
	.asciz "Hello"

string_exclam:
	.asciz "!"

string_space:
	.asciz " "

string_universe:
	.asciz "universe"


_start:
	lui		sp, $ff00

	lui		a0, $1000
#	la		a1, _top
#	sub		a0, a0, a1
#	addi	a0, a0, -64

	call	alloc_init

	call	heapdump

	call	main

	ebreak


main:
	addi	sp, sp, -6
	sw		ra, (sp)
	sw		s0, 2(sp)

	.bufferptr = 4

	li		a0, 128
	call	malloc
	sw		a0, .bufferptr(sp)

	call	heapdump

	lw		a0, .bufferptr(sp)

	la		a1, string_hello
	call	strcpy

	la		a1, string_space
	call	strcat

	la		a1, string_world
	call	strcat

	la		a1, string_exclam
	call	strcat

	call	puts
	call	newline


	lw		a0, .bufferptr(sp)
	call	strdup

	mv		s0, a0

	call	puts
	call	newline

	call	heapdump

	mv		a0, s0
	call	free

	call	heapdump


	lw		a0, .bufferptr(sp)
	li		a1, 'w'
	call	strchr

	la		a1, string_universe
	call	strcpy

	lw		a0, .bufferptr(sp)
	call	puts
	call	newline


	lw		a0, .bufferptr(sp)
	call	free

	call	heapdump

	lw		ra, (sp)
	lw		s0, 2(sp)
	addi	sp, sp, 6
	ret


newline:
	li		a0, 10
	tail	putchar


