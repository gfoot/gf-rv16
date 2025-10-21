irqhandler:
	sw		s0, -2(sp)
	sw		s1, -4(sp)
	sw		a0, -6(sp)
	sw		a1, -8(sp)
	
	li		s1, 0

	# Check for pending input
	lb		a0, MMIO_INPUTSTATE(s1)
	beqz	a0, .no_input_pending

	# Check for buffer space
	lui		s0, os_globals
	lw		a0, os_g_serial_in_head(s0)
	lw		a1, os_g_serial_in_tail(s0)
	addi	a0, a0, -15                   # Increment the head pointer while wrapping...
	ori		a0, a0, 16                    # ... within the buffer's range
	beq		a0, a1, .input_buffer_full    # If the incremented head collides with the tail 
			                              # ... then the buffer was full

	sw		a0, os_g_serial_in_head(s0)   # Write back the updated head pointer

	lb		a1, MMIO_GETCHAR(s1)          # Read the character...
	sb		a1, (a0)                      # ... and store it at the head

.no_input_pending:
	lw		s0, -2(sp)
	lw		s1, -4(sp)
	lw		a0, -6(sp)
	lw		a1, -8(sp)
	mret

.input_buffer_full:
	lb		a0, MMIO_GETCHAR(s1)    # Read and discard the character
	j		.no_input_pending

