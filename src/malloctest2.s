.include "lib/os.s"
.include "lib/str.s"
.include "lib/mem.s"
.include "lib/io.s"
.include "lib/random.s"

_start:

	li		sp, 0
	addi	sp, sp, -8

	li		a0, $f800
	li		a1, _top
	sub		a0, a0, a1
	call	alloc_init


	# We allocate a table of pointers, initially all null, then each loop pick one at random and 
	# either allocate it or free it, depending on its current state.  Allocation sizes are also
	# chosen at random.

	numentries = 1024

	li		a0, numentries*2
	call	malloc
	mv		s0, a0

	li		t0, numentries*2-2
	add		t0, t0, s0
	li		a0, 0
1:
	sw		a0, (t0)
	addi	t0, t0, -2
	bgeu	t0, s0, 1b

	li		s1, 100
	sw		s1, (sp)

.loop:
	call	random3
	li		t0, numentries-1
	and		a0, a0, t0
	slli	a0, a0, 1

	add		s1, a0, s0
	lw		a1, (s1)

	beqz	a1, .allocate

	li		a0, 'F'
	call	putchar

	mv		a0, a1
	call	free

	li		a0, 0
	sw		a0, (s1)

	j		.loopend

.allocate:
	li		a0, 'M'
	call	putchar

	call	random3
	li		t0, 127
	and		a0, a0, t0
	bnez	a0, 1f

	call	random3
	li		t0, 1023
	and		a0, a0, t0
	li		t0, 1024
	add		a0, a0, t0
	j		2f

1:
	call	random3
	li		t0, 127
	and		a0, a0, t0

2:

	addi	a0, a0, 1

	call	malloc
	sw		a0, (s1)

.loopend:
	lw		s1, (sp)
	addi	s1, s1, -1
	bnez	s1, .nodump

#	call	heapdump
	addi	sp, sp, -memstats__size
	mv		a0, sp
	call	memstats

	call	printimm
	.asciz "    memstats: "

	lw		a0, memstats_total_allocated(sp)
	call	printhex16
	li		a0, ' '
	call	putchar
	lw		a0, memstats_total_free(sp)
	call	printhex16
	li		a0, ' '
	call	putchar
	lw		a0, memstats_num_allocated(sp)
	call	printhex16
	li		a0, ' '
	call	putchar
	lw		a0, memstats_num_free(sp)
	call	printhex16
	li		a0, ' '
	call	putchar
	lw		a0, memstats_largest_free(sp)
	call	printhex16

	call	printimm
	.asciz "\r\n"

	addi	sp, sp, memstats__size

	li		s1, 100

	call	visualiseheap
	call	printimm
	.asciz "\r\n\n"

.nodump:
	sw		s1, (sp)
	j		.loop


