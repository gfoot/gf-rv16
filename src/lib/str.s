
strlen:
	# a0 = pointer to first char

	addi	t0, a0, -1		# Point t0 before the first char
1:
	addi	t0, t0, 1		# Advance t0
	lb		a1, (t0)		# until it reaches
	bnez	a1, 1b			# the null terminator

	sub		a0, t0, a0		# Subtract the original pointer and return the result
	ret


strcpy:
    # a0 = destination
    # a1 = source
1:
    lb      t0, 0(a1)    # Copy a character from a1...
    sb      t0, 0(a0)    # ... to a0

    addi    a0, a0, 1    # Advance both pointers
    addi    a1, a1, 1

    bnez    t0, 1b       # Loop back if the character was not zero

    ret


strncpy:
    # a0 = destination
    # a1 = source
    # a2 = size of destination buffer

	add		a2, a2, a0		# Now a2 points one character beyond the end of the destination buffer

1:
	lb		t0, (a1)		# Copy a character
	sb		t0, (a0)
	beqz	t0, 1f			# Skip if reached end of string

	addi	a0, a0, 1		# Advance pointers
	addi	a1, a1, 1

	blt		a0, a2, 1b		# Loop back so long as we haven't got to a2 yet

	li		t0, 0			# If we reached a2, replace the last character copied with a null terminator
	sb		t0, -1(a0)

1:
	ret


strrev:
	# a0 = instr, forward pointer
	# a1 = backward pointer

	# Handle empty string first
	lb		t0, 0(a0)
	beqz	t0, 2f

	# Iterate a1 through string to find last char
	addi	a1, a0, -1
1:
	addi	a1, a1, 1
	lb		t0, 1(a1)
	bnez	t0, 1b

	# Now a0 points to first char and a1 points to last char
1:
	# Swap characters
	lb		t0, (a0)
	lb		a2, (a1)
	sb		t0, (a1)
	sb		a2, (a0)

	# Adjust pointers
	addi	a0, a0, 1
	addi	a1, a1, -1

	# Loop until they meet
	blt		a0, a1, 1b

2:
	ret



