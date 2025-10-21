SYSCALL_EXIT = 0
SYSCALL_PUTS = 2
SYSCALL_PUTCHAR = 4
SYSCALL_GETS = 6
SYSCALL_GETCHAR = 8
SYSCALL_MAX = 10

MMIO_PUTCHAR = $fffe
MMIO_GETCHAR = $fffe
MMIO_INPUTSTATE = $ffff


# Method 1 - example syscall:
#
#   la    a1, buffer
#   li    a0, SYSCALL_PUTS
#   jalr  ra, syscall_entry-SYSCALL_PUTS(a0)

syscall_table:
	.word syscall_exit
	.word syscall_puts
	.word syscall_putchar
	.word syscall_gets
	.word syscall_getchar
syscall_entry:   # = 32
	bltz	a0, .invalid
	addi	a0, a0, -SYSCALL_MAX
	bgez	a0, .invalid

	lw		a0, syscall_entry(a0)	
	jr		(a0)

.invalid:
	ebreak


# Method 2  example syscall:
#
#   li    ra, SYSCALL_PUTS           # or lui   ra, %hi(syscall_gets)
#   lw    ra, syscall_table(ra)      # or addi  ra, ra, %lo(syscall_gets)
#   jalr  ra, (ra)

syscall_table:    # < 64
	.word syscall_exit
	.word syscall_puts
	.word syscall_putchar
	.word syscall_gets
	.word syscall_getchar

# Another similar way - causes double-jumps but saves an instruction for the
# caller:
#
#   lui     ra, syscall_table       # the table must be page-aligned...
#   jalr    ra, SYSCALL_PUTS(ra)    # ... as jalr's range is only -32..30
#
#
# syscall_table:
#   j       syscall_exit
#   j       syscall_puts
#   j       syscall_putchar
#   j       syscall_gets
#   j       syscall_getchar
#
#
# Another way that's aligned differently:
#
#   li      ra, -32                 # $ffe0 - just under the I/O region
#   jalr    ra, SYSCALL_PUTS(ra)    # SYSCALL constants would be negative
#
# 


syscall_exit:
	ebreak

syscall_puts:
	li		a0, 0
2:
	lb		a2, 0(a1)
	beqz	a2, 2f
	sb		a2, MMIO_PUTCHAR(a0)
	addi	a1, a1, 1
	j		2b
2:
	ret

syscall_putchar:
	li		a0, 0
	sb		a1, MMIO_PUTCHAR(a0)
	ret

syscall_getchar:
	li		a0, 0
2:
	lb		a1, MMIO_INPUTSTATE(a0)
	beqz	a1, 2b
	lb		a0, MMIO_GETCHAR(a0)
	ret


syscall_gets:
	li		a2, 0
	mv		t0, a1
.again:
	lb		a0, MMIO_INPUTSTATE(a2)
	beqz	a0, .again
	lb		a0, MMIO_GETCHAR(a2)

	addi	a0, a0, -127
	beqz	a0, .backspace
	bgez	a0, .again

	addi	a0, a0, 117
	beqz	a0, .enter

	addi	a0, a0, -22
	bltz	a0, .again

	addi	a0, a0, 32

	sb		a0, MMIO_PUTCHAR(a2)
	sb		a0, (a1)
	addi	a1, a1, 1
	j		.again

.backspace:
	beq		a1, t0, .again
	li		a0, 8
	sb		a0, MMIO_PUTCHAR(a2)
	li		a0, 32
	sb		a0, MMIO_PUTCHAR(a2)
	li		a0, 8
	sb		a0, MMIO_PUTCHAR(a2)
	addi	a1, a1, -1
	j		.again

.enter:
	sb		a0, (a1)
	li		a0, 10
	sb		a0, MMIO_PUTCHAR(a2)
	mv		a0, t0
	ret

