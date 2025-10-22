.include "lib/os.s"
.include "lib/io.s"

_start:

	call	printnl

	call	printimm
	.asciz "This is a test of interrupt-driven buffered I/O."

	call	printnl
	call	printnl

	call	printimm
	.asciz "Characters you type will be echoed at a low rate, "
	call	printimm
	.asciz "requiring subsequent characters to be buffered by the interrupt handler."

	call	printnl
	call	printnl

	call	printimm
	.asciz "Note that the simulator itself does not perform any buffering - typed characters cause an immediate"
	call	printimm
	.asciz "interrupt and the MMIO only allows reading of the most recent pending character."

	call	printnl
	call	printnl

	call	printimm
	.asciz "The machine's OS itself also has a limited buffer capacity of 16 characters."

	call	printnl
	call	printnl

2:
	call	getchar
	call	putchar

1:
	addi	t0, t0, 8
	bgez	t0, 1b

	j		2b

