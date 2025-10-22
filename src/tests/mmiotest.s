# Test of MMIO functionality alone, without the operating system

.include "lib/defs.s"

resetvector:
	j	_start
ecallvector:
	ebreak
irqvector:
	ebreak

_start:
	li	t0, 0

	li	a0, $48
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, $65
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, $6c
	sb	a0, MMIO_PUTCHAR(t0)
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, $6f
	sb	a0, MMIO_PUTCHAR(t0)

	li	a0, $20
	sb	a0, MMIO_PUTCHAR(t0)

	li	a0, $77
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, $6f
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, $72
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, $6c
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, $64
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, $21
	sb	a0, MMIO_PUTCHAR(t0)


	li	a1, '.'
.loop:
	lb	a0, MMIO_INPUTSTATE(t0)
	bnez	a0, 1f
	sb	a1, MMIO_PUTCHAR(t0)
	j	.loop

1:
	lb	a0, MMIO_GETCHAR(t0)
	sb	a0, MMIO_PUTCHAR(t0)
	li	a0, 10
	sb	a0, MMIO_PUTCHAR(t0)
	j	.loop

stop:
	li	x7, 0
	ecall

