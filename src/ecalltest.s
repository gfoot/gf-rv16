MMIO_PUTCHAR = $ffff

_start:
resetvector:
	j		entry

ecallvector:
	j		ecallhandler

irqvector:
	j		irqvector

ecallhandler:
	li		t0, 0
	li		a0, 'e'
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 'c'
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 'a'
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 'l'
	sb		a0, MMIO_PUTCHAR(t0)
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 10
	sb		a0, MMIO_PUTCHAR(t0)
	ebreak

entry:
	li		t0, 0
	li		a0, 'e'
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 'n'
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 't'
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 'r'
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 'y'
	sb		a0, MMIO_PUTCHAR(t0)
	li		a0, 10
	sb		a0, MMIO_PUTCHAR(t0)

	ecall

