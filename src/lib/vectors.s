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
2:
	lb		a1, MMIO_GETCHAR(a2)
	sb		a1, (a0)
	addi	a0, a0, 1
	addi	a1, a1, -10
	bnez	a1, 2b
	sb		a1, -1(a0)
	mret	2

1:
	addi	a2, a2, -1
	bnez	a2, 1f

	# ecall 4 = getchar
	lb		a0, MMIO_GETCHAR(a2)
	mret	2

1:
	j		ecall_invalid


ecall_exit:
	ebreak

ecall_invalid:
	ebreak


MMIO_PUTCHAR = $ffff
MMIO_GETCHAR = $ffff

