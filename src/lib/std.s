# Some functions from C's stdlib

atoi:
	addi	sp, sp, -6
	sw		ra, (sp)
	sw		s0, 2(sp)

	addi	a1, a0, -1
	li		a0, 0
	li		s0, 0

1:	# Skip leading whitespace
	addi	a1, a1, 1
	lb		a2, (a1)
	beqz	a2, 5f          # End of string?
	addi	a2, a2, -33
	bltz	a2, 1b          # Skip until non-whitespace

	# Handle a possible + or - sign
	addi	a2, a2, 33-'+'
	beqz	a2, 1f          # Positive - no change to s0, but do skip the character
	addi	a2, a2, '+'-'-'
	bnez	a2, 2f          # Not a sign, so don't skip the character

	li		s0, -1          # Mark that the result should be made negative
1:
	addi	a1, a1, 1       # Skip the sign character

2:
	# Read the number a digit at a time
	lb		a2, (a1)
	addi	a1, a1, 1

	beqz	a2, 1f          # End of string?

	addi	a2, a2, -('0'+10)
	bgez	a2, 1f          # ASCII >= 58, not a digit

	addi	a2, a2, 10
	bltz	a2, 1f          # ASCII < 48, not a digit

	slli	t0, a0, 2       # t0 = a0 * 4
	add		t0, t0, a0      # t0 = a0 * 5
	add		t0, t0, t0      # t0 = a0 * 10

	add		a0, t0, a2      # a2 is between 0 and 9 by this point

	j		2b

1:
5:
	xor		a0, a0, s0      # Flip all bits if the result should be negative
	sub		a0, a0, s0      # Add 1 if the result should be negative

	lw		ra, (sp)
	lw		s0, 2(sp)
	addi	sp, sp, 6
	ret

