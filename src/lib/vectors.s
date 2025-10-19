MMIO_PUTCHAR = $fffe
MMIO_GETCHAR = $fffe
MMIO_INPUTSTATE = $ffff


resetvector:
	ebreak
ecallvector:
	j		ecallhandler
irqvector:
	ebreak

ecallhandler:
	bnez	a2, 1f

	# ecall 0 = exit
	j		ecall_exit

1:
	addi	a2, a2, -1
	bnez	a2, 1f

2:  # ecall 1 = puts
	lb		a1, 0(a0)
	beqz	a1, 2f
	sb		a1, MMIO_PUTCHAR(a2)
	addi	a0, a0, 1
	j 2b
2:
	mret	2

1:
	addi	a2, a2, -1
	bnez	a2, 1f
	
	# ecall 2 = putchar
	sb		a0, MMIO_PUTCHAR(a2)
	mret	2

1:
	addi	a2, a2, -1
	bnez	a2, 1f

	# ecall 3 = gets
	j		ecall_gets

1:
	addi	a2, a2, -1
	bnez	a2, 1f

	# ecall 4 = getchar
2:
	lb		a0, MMIO_INPUTSTATE(a2)
	beqz	a0, 2b
	lb		a0, MMIO_GETCHAR(a2)
	mret	2

1:
	j		ecall_invalid


ecall_exit:
	ebreak

ecall_invalid:
	ebreak

ecall_gets:
	mv		t0, a0
.again:
	lb		a1, MMIO_INPUTSTATE(a2)
	beqz	a1, .again
	lb		a1, MMIO_GETCHAR(a2)

	addi	a1, a1, -127
	beqz	a1, .backspace
	bgez	a1, .again

	addi	a1, a1, 117
	beqz	a1, .enter

	addi	a1, a1, -22
	bltz	a1, .again

	addi	a1, a1, 32

	sb		a1, MMIO_PUTCHAR(a2)
	sb		a1, (a0)
	addi	a0, a0, 1
	j		.again

.backspace:
	beq		a0, t0, .again
	li		a1, 8
	sb		a1, MMIO_PUTCHAR(a2)
	li		a1, 32
	sb		a1, MMIO_PUTCHAR(a2)
	li		a1, 8
	sb		a1, MMIO_PUTCHAR(a2)
	addi	a0, a0, -1
	j		.again

.enter:
	sb		a1, (a0)
	li		a1, 10
	sb		a1, MMIO_PUTCHAR(a2)
	mv		a0, t0
	mret	2


