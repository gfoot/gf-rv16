# Test some aspects of CSR handling

MMIO_PUTCHAR = $fffe

resetvector:
	j		entry

ecallvector:
	csrrci	a0, mstatus, 8
	mret	2

irqvector:
	ebreak

entry:
	lui		sp, $ff00

	# mstatus = 0000
	csrrsi	a0, mstatus, 8
	sw		a0, 2(sp)
	# mstatus = 0008
	csrrsi	a0, mstatus, 8
	sw		a0, 4(sp)
	# mstatus = 0008
	csrrci	a0, mstatus, 8
	sw		a0, 6(sp)
	# mstatus = 0000
	csrrci	a0, mstatus, 8
	sw		a0, 8(sp)
	# mstatus = 0000

	ecall                     # 0000 =ecall=> 0000 =csrrci=> 0000 =mret=> 0000
	sw		a0, 10(sp)        #                 ^--- this one is stored at 10(sp)

	csrrsi	a0, mstatus, 8
    # mstatus = 0008

	ecall                     # 0008 =ecall=> 0080 =csrrci=> 0080 =mret=> 0088
	sw		a0, 12(sp)        #                 ^--- this one is stored at 12(sp)

	# mstatus = 0088
	csrrci	a0, mstatus, 8
	sw		a0, 14(sp)
	# mstatus = 0080

	addi	s0, sp, 2
	addi	s1, sp, 16

1:
	lw		a0, (s0)
	call	printhex16
	li		a0, 10
	call	putchar

	addi	s0, s0, 2
	bne		s0, s1, 1b

	ebreak


.include "lib/io.s"

