exit:
	ebreak


getchar = os_getchar

gets:
	addi	sp, sp, -2
	sw		ra, (sp)

	li		a2, 3
	ecall

	lw		ra, (sp)
	addi	sp, sp, 2
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

	ret


printimm:
	addi	a0, ra, 2
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


