
# Just a simple LFSR random number generator

random1_seed:
	.word $1234

random1:
	li		a0, 1

	la		t0, random1_seed
	lw		a1, (t0)
2:
	slli	a0, a0, 1
	bltz	a1, 1f
	addi	a0, a0, 1
1:
	slli	a2, a1, 3
	xor		a2, a2, a1
	slli	t0, a2, 2
	xor		a2, a2, t0
	slli	a1, a1, 1
	sltz	a2, a2
	add		a1, a1, a2
	
	bgtz	a0, 2b

	slli	a0, a0, 1
	bltz	a1, 1f
	addi	a0, a0, 1
1:
	slli	a2, a1, 3
	xor		a2, a2, a1
	slli	t0, a2, 2
	xor		a2, a2, t0
	slli	a1, a1, 1
	sltz	a2, a2
	add		a1, a1, a2
	
	la		t0, random1_seed
	sw		a1, (t0)

	ret



random2_seed:
	.word $1234
	.word $5678

random2:

	addi	sp, sp, -4
	sw		s0, (sp)
	sw		s1, 2(sp)

	la		t0, random2_seed  # a1,a2 = state vector
	lw		a1, (t0)
	lw		a2, 2(t0)

	mv		t0, a0            # loop counter
	li		a0, 0             # output register

2:
	sltz	s0, a1            # output and feedback bit
	sltz	s1, a2            # carry from upcoming shift
	slli	a1, a1, 1
	add		a1, a1, s1        # add the carry

	slli	a0, a0, 1         # shift output register
	beqz	s0, 1f
	addi	a0, a0, 1         # add output bit
	xori	a2, a2, 9         # apply feedback
1:
	slli	a2, a2, 1

	addi	t0, t0, -1
	bnez	t0, 2b
	
	la		t0, random2_seed
	sw		a1, (t0)
	sw		a2, 2(t0)

	lw		s0, (sp)
	lw		s1, 2(sp)
	addi	sp, sp, 4
	ret



# random3 is inspired by some things Arlet did on the 6502 (posted on 6502.org) using just chained adds
# to get good randomness.  I didn't try very hard to get good results but this does fairly well at
# https://mzsoltmolnar.github.io/random-bitstream-tester/
#
# And it's much cheaper than the LFSRs above

random3_state:
	.word $1234
	.word $4567
	.word $3003
	.word $beef
	.word $0778
	.word $6502
	.word $8080
	.word $6850

random3:
	addi	sp, sp, -8
	sw		ra, (sp)
	sw		s0, 2(sp)
	sw		s1, 4(sp)
	
	la		a0, random3_state
	
	lw		t0, (a0)
	lw		a1, 2(a0)
	lw		a2, 4(a0)
	lw		s0, 6(a0)
	lw		s1, 8(a0)
	lw		ra, 10(a0)
	lw		a0, 12(a0)
	
	addi	a0, a0, 27
	add		a1, a1, a0
	add		a2, a2, a1
	xor		s0, s0, a2
	add		s1, s1, s0
	add		ra, ra, s1
	add		t0, t0, s0
	xor		a0, a0, t0

	sw		a0, 6(sp)
	
	la		a0, random3_state
	sw		t0, (a0)
	sw		a1, 2(a0)
	sw		a2, 4(a0)
	sw		s0, 6(a0)
	sw		s1, 8(a0)
	sw		ra, 10(a0)

	mv		t0, a0
	lw		a0, 6(sp)
	sw		a0, 12(t0)

	lw		ra, (sp)
	lw		s0, 2(sp)
	lw		s1, 4(sp)
	addi	sp, sp, 8
	ret


# This one scores very well at PractRand testing.  However it requires
# add-with carry which this architecture doesn't provide, so it costs
# a bit more to implement here than it does on other architectures.

random4_state:
	.word 0
	.word 0
	.word 0
	.word 0
random4:
	la	t0, random4_state

	li	a0, $0081       # LDA #$0081
	lw	a1, 6(t0)
	add	a1, a1, a0      # ADD state+6
	sw	a1, 6(t0)       # STA state+6
	sltu	a0, a1, a0	
	add	a0, a1, a0      # ADC #0

	lw	a1, 4(t0)
	add	a2, a1, a0      # ADD state+4
	sw	a2, 4(t0)       # STA state+4  = a2
	sltu	a0, a2, a0
	add	a0, a2, a0      # ADC #0

	lw	a1, 2(t0)
	add	a1, a1, a0      # ADD state+2
	sw	a1, 2(t0)       # STA state+2  = a1
	sltu	a0, a1, a0
	add	a0, a1, a0      # ADC #0

	# We want to load state+3 but it's misaligned.  But its low
	# byte is in the high byte of a1 and its high byte is in the
	# low byte of a2.
	slli	a2, a2, 8
	srli	a1, a1, 8
	or	a1, a1, a2
	add	a1, a1, a0      # ADD state+3
	sltu	a0, a1, a0
	add	a0, a1, a0      # ADC #0

	lw	a1, 0(t0)
	add	a1, a1, a0      # ADD state+0
	sw	a1, 0(t0)       # STA state+0
	sltu	a0, a1, a0
	add	a0, a1, a0      # ADC #0

	lw	a1, 2(t0)
	add	a0, a1, a0      # ADD state+2
	sw	a0, 2(t0)       # STA state+2

	ret

random = random4

