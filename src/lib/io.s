exit:
	ebreak


getchar = os_getchar


gets:
	addi	sp, sp, -6
	sw		ra, (sp)
	sw		s0, 2(sp)
	sw		s1, 4(sp)

	mv		s0, a0
	mv		s1, a0

.again:
	call	getchar

	addi	a0, a0, -127
	beqz	a0, .backspace
	bgez	a0, .again

	addi	a0, a0, 117
	beqz	a0, .enter

	addi	a0, a0, -22
	bltz	a0, .again

	addi	a0, a0, 32

	sb		a0, (s0)
	addi	s0, s0, 1

	call	putchar
	j		.again

.backspace:
	beq		s0, s1, .again
	li		a0, 8
	call	putchar
	li		a0, 32
	call	putchar
	li		a0, 8
	call	putchar
	addi	s0, s0, -1
	j		.again

.enter:
	sb		a0, (s0)
	li		a0, 10
	call	putchar

	mv		a0, s1

	lw		ra, (sp)
	lw		s0, 2(sp)
	lw		s1, 4(sp)
	addi	sp, sp, 6
	ret


putchar:
	li		t0, 0
	sb		a0, MMIO_PUTCHAR(t0)
	ret
	

puts:
	li		t0, 0
1:
	lb		a1, (a0)
	beqz	a1, 1f
	sb		a1, MMIO_PUTCHAR(t0)
	addi	a0, a0, 1
	j		1b
1:
	ret


printimm:
	mv		a0, ra
	call	puts
	jr		a0, 2


printnum:
	mv		a1, a0
	la		t0, printnumtable
1:
	lh		a2, 2(t0)
	bltu	a1, a2, 1f
	addi	t0, t0, 2
	j		1b
1:
	lh		a2, (t0)
3:	
	li		a0, 48
	blt		a1, a2, 1f
2:
	sub		a1, a1, a2
	addi	a0, a0, 1
	bge		a1, a2, 2b
1:
	li		a2, 0
	sb		a0, MMIO_PUTCHAR(a2)

	addi	t0, t0, -2
	lh		a2, (t0)
	bnez 	a2, 3b

	ret

printnumtable:
	.word	0,1,10,100,1000,10000,$ffff


printhexnybble:
	andi	a0, a0, 15
	addi	a0, a0, -10
	bltz	a0, 1f
	addi	a0, a0, 7
1:
	addi	a0, a0, 58
	li		t0, 0
	sb		a0, MMIO_PUTCHAR(t0)
	ret


printhex16:
	addi	sp, sp, -4
	sw		a0, 2(sp)
	sw		ra, (sp)
	srli	a0, a0, 12
	call	printhexnybble
	lw		a0, 2(sp)
	srli	a0, a0, 8
	call	printhexnybble
	lw		a0, 2(sp)
1:
	srli	a0, a0, 4
	call	printhexnybble
	lw		a0, 2(sp)
	call	printhexnybble
	lw		a0, 2(sp)
	lw		ra, (sp)
	addi	sp, sp, 4
	ret


printhex8:
	addi	sp, sp, -4
	sw		s0, 2(sp)
	sw		ra, (sp)
	tail	1b


