.include "lib/os.s"
.include "lib/str.s"
.include "lib/io.s"
.include "lib/mem.s"

value1 = 18
value2 = $15

message:
	.asciz "Hello world!\r\n","Goodbye "  , "this, ÞteÞst" 

buffer:
	.word 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
buffersize = * - buffer

buffer2:
	.word 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0

_start:
	lui		sp, $ff00

	la		s0, message
1:
	lb		a0, 0(s0)
	beqz	a0, 1f
	li		t0, 0
	sb		a0, MMIO_PUTCHAR(t0)
	
	addi	s0, s0, 1
	j		1b
1:
	li		a0, 10
	sb		a0, MMIO_PUTCHAR(t0)

	call	printimm
	.asciz "Inline string-printing test"

	li		t0, 0
	li		a0, 10
	sb		a0, MMIO_PUTCHAR(t0)
	sb		a0, MMIO_PUTCHAR(t0)

	li		a0, 31856
	call	printnum

	li		t0, 0
	li		a0, 10
	sb		a0, MMIO_PUTCHAR(t0)

	la		a0, message
	call	strlen

	call	printnum

	li		t0, 0
	li		a0, 10
	sb		a0, MMIO_PUTCHAR(t0)
	sb		a0, MMIO_PUTCHAR(t0)

	li		x4, value1
	li		x5, value2

	blt		x5,x4,.x4bigger
	beq		x5,x4,.done
.x5bigger:
	sub		x5,x5,x4
	blt		x4,x5,.x5bigger
	blt		x5,x4,.x4bigger
	j		.done
.x4bigger:
	sub		x4,x4,x5
	blt		x5,x4,.x4bigger
	blt		x4,x5,.x5bigger
.done:


	li		a0,		10
	call	putchar
	call	putchar

	call	printimm
	.asciz "What is your name? "

	la		a0, buffer
	li		a1, buffersize
	call	gets

	call	printimm
	.asciz "Hello "

	la		a0, buffer
	call	puts

	call	printimm
	.asciz ", how are you today?\r\n"

	la		a0, buffer
	call	strrev

	call	printimm
	.asciz "Your name backwards is "

	la		a0, buffer
	call	puts

	call	printimm
	.asciz "\r\nBack to normal it's "

	la		a0, buffer
	call	strrev

	la		a0, buffer
	call	puts

	call	printimm
	.word $0d0a,0

	# Use strcpy to copy it to the other buffer
	la		a0, buffer2
	la		a1, buffer
	call	strcpy

	call	printimm
	.asciz "In the new buffer: "

	la		a0, buffer2
	call	puts
	call	printimm
	.word $0d0a,0

	# Use strncpy to copy just some of it
	la		a0, buffer2
	la		a1, buffer+1
	li		a2, 3
	call	strncpy

	call	printimm
	.asciz "After strncpy(buffer2, buffer+1, 3): "

	la		a0, buffer2
	call	puts
	call	printimm
	.word $0d0a,0

	# Do it again with a perfect length value
	la		a0, buffer+1
	call	strlen
	addi	a2, a0, 1
	la		a0, buffer2
	la		a1, buffer+1
	call	strncpy

	call	printimm
	.asciz "After strncpy(buffer2, buffer+1, strlen(buffer+1)+1): "

	la		a0, buffer2
	call	puts
	call	printimm
	.word $0d0a,0

	# And now with a length value that's larger than needed
	la		a0, buffer+3
	call	strlen
	addi	a2, a0, 10
	la		a0, buffer2
	la		a1, buffer+3
	call	strncpy

	call	printimm
	.asciz "After strncpy(buffer2, buffer+3, strlen(buffer+3)+10): "

	la		a0, buffer2
	call	puts
	call	printimm
	.word $0d0a,0


	call exit


arraysum:
    # a0 = int a[]
    # a1 = int size
    # t0 = ret
    # a2 = a1*4
    li    t0, 0        # ret = 0
1:  # For loop
	addi  a1, a1, -1
    bltz  a1, 1f       # if i < 0, break
    slli  a2, a1, 2    # Multiply i by 4 (1 << 2 = 4)
    add   a2, a0, a2   # Update memory address
    lw    a2, 0(a2)    # Dereference address to get integer
    add   t0, t0, a2   # Add integer value to ret
    j     1b           # Jump back to start of loop (1 backwards)
1:
    mv    a0, t0       # Move t0 (ret) into a0
    ret                # Return via return address register


