.include "os/os.s"

_start:
	rdmepc	t0
	wrmepc	t0

	csrrci	t0, mepc, 0
	csrrsi	t0, mepc, 0

	lui		t0, os_globals

	lw		a0, os_g_serial_in_tail(t0)

1:
	lw		a1, os_g_serial_in_head(t0)
	beq		a0, a1, 1b

	addi	a0, a0, -15
	ori		a0, a0, 16
	sw		a0, os_g_serial_in_tail(t0)

	lb		a1, (a0)
	li		t0, 0
	sb		a1, MMIO_PUTCHAR(t0)

1:
	addi	t0, t0, 8
	bgez	t0, 1b

	j		_start

