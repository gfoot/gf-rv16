os_init:

	lui		sp, $ff00

	lui		s0, os_globals

	# Set up buffers ready for interrupt-driven I/O
	mv		a0, s0
	addi	a0, a0, os_g_serial_in_buffer
	sw		a0, os_g_serial_in_head(s0)
	sw		a0, os_g_serial_in_tail(s0)

	mv		a0, s0
	addi	a0, a0, os_g_serial_out_buffer
	sw		a0, os_g_serial_out_head(s0)
	sw		a0, os_g_serial_out_tail(s0)


	csrrsi	ra, mstatus, 8      # Enable interrupts
	
	j		_start              # Chain to application code


