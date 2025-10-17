resetvector:
	j	_start
ecallvector:
	ebreak
irqvector:
	ebreak

_start:
	li	t0, 0

	li	a0, $48
	sb	a0, -1(t0)
	li	a0, $65
	sb	a0, -1(t0)
	li	a0, $6c
	sb	a0, -1(t0)
	sb	a0, -1(t0)
	li	a0, $6f
	sb	a0, -1(t0)

	li	a0, $20
	sb	a0, -1(t0)

	li	a0, $77
	sb	a0, -1(t0)
	li	a0, $6f
	sb	a0, -1(t0)
	li	a0, $72
	sb	a0, -1(t0)
	li	a0, $6c
	sb	a0, -1(t0)
	li	a0, $64
	sb	a0, -1(t0)
	li	a0, $21
	sb	a0, -1(t0)

stop:
	li	x7, 0
	ecall

