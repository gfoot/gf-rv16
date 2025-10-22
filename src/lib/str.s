
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
	mv		a2, a0
1:
    lb      t0, 0(a1)    # Copy a character from a1...
    sb      t0, 0(a2)    # ... to a2

    addi    a2, a2, 1    # Advance both pointers
    addi    a1, a1, 1

    bnez    t0, 1b       # Loop back if the character was not zero

    ret


strncpy:
	addi	sp, sp, -4
	sw		ra, (sp)
	sw		a0, 2(sp)

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
	lw		a0, 2(sp)
	addi	sp, sp, 4
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


strdup:
	.oldstringptr = 2
	.newstringptr = 4

	addi	sp, sp, -6
	sw		ra, (sp)
	sw		a0, .oldstringptr(sp)

	call	strlen

	addi	a0, a0, 1

	call	malloc

	sw		a0, .newstringptr(sp)

	lw		a1, .oldstringptr(sp)
	call	strcpy

	lw		a0, .newstringptr(sp)
	lw		ra, (sp)
	addi	sp, sp, 6
	ret


strchr:
	lbu		a2, (a0)
	beqz	a2, 2f
	beq		a1, a2, 1f
	addi	a0, a0, 1
	j		strchr
2:
	li		a0, 0
1:
	ret


strcat:
	mv		a2, a0
1:
	lb		t0, (a2)
	addi	a2, a2, 1
	bnez	t0, 1b

1:	
	lb		t0, (a1)
	sb		t0, -1(a2)
	addi	a1, a1, 1
	addi	a2, a2, 1
	bnez	t0, 1b

	ret


memset:
	addi	sp, sp, -2
	sw		ra, (sp)

	mv		ra, a0

	andi	t0, ra, 1
	beqz	t0, 1f
	beqz	a2, 1f
	sb		a1, (ra)
	addi	ra, ra, 1
	addi	a2, a2, -1

1:
	andi	t0, a2, 1
	beqz	t0, 1f
	add		t0, ra, a2
	sb		a1, -1(t0)
	addi	a2, a2, -1

1:
	beqz	a2, 2f
	slli	t0, a1, 8
	srli	a1, t0, 8
	or		a1, a1, t0

1:
	sw		a1, (ra)
	addi	ra, ra, 2
	addi	a2, a2, -2
	bnez	a2, 1b

2:
	lw		ra, (sp)
	addi	sp, sp, 2
	ret


memsetb:
	beqz	a2, 2f
	mv		t0, a0
1:
	sb		a1, (t0)
	addi	t0, t0, 1
	addi	a2, a2, -1
	bnez	a2, 1b
2:
	ret


memcpy:
	addi	sp, sp, -2
	sw		ra, (sp)

	beqz	a2, 2f
	mv		ra, a0
1:
	lb		t0, (a1)
	sb		t0, (ra)
	addi	a1, a1, 1
	addi	ra, ra, 1
	addi	a2, a2, -1
	bnez	a2, 1b

2:
	lw		ra, (sp)
	addi	sp, sp, 2
	ret


memcmp:
	addi	sp, sp, -2
	sw		ra, (sp)

	li		ra, 0

	beqz	a2, 2f

1:
	lb		ra, (a0)
	lb		t0, (a1)
	sub		ra, ra, t0
	bnez	ra, 2f

	addi	a0, a0, 1
	addi	a1, a1, 1
	addi	a2, a2, -1
	bnez	a2, 1b

2:
	mv		a0, ra

	lw		ra, (sp)
	addi	sp, sp, 2
	ret


