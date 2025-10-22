# Test of ecall functionality on its own, without the operating system

MMIO_PUTCHAR = $fffe

_start:
resetvector:
	j		entry

ecallvector:
	j		ecallhandler

irqvector:
	j		irqvector

ecallhandler:
	li		t0, 0
	sb		a0, MMIO_PUTCHAR(t0)

	csrr	t0, mepc
	addi	t0, t0, 2
	csrrw	zero, mepc, t0
	mret

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

	li		a0, 'e'
	ecall
	li		a0, 'c'
	ecall
	li		a0, 'a'
	ecall
	li		a0, 'l'
	ecall
	li		a0, 'l'
	ecall
	li		a0, 10
	ecall

	ebreak

