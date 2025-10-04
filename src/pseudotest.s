* = $8000
global_thing = $ffee
global_aligned = $ff00
global_nearzero = $0004

local_distant_thing = $9000

_start:

	# %hi, %lo
	lui		t0, %hi(global_thing)                     # EXPECT: srli x8, x8, 16
	addi	t0, t0, %lo(global_thing)                 # EXPECT: addi x8, x8, -18

	# %pcrel_hi, %pcrel_lo
1:	auipc	t0, %pcrel_hi(local_distant_thing)        # EXPECT: auipc x8, $1000	
	addi	t0, t0, %pcrel_lo(1b)                     # EXPECT: addi x8, x8, -4

	# unimp
	unimp                                  # EXPECT: lui x8, 0

	# nop
	nop                                    # EXPECT: slli x8, x8, 0

	# mv rd, rs => maybe ori rd, rs, rs, andi -1, or shift-0
	mv		t0, ra                         # EXPECT: slli x8, x1, 0

	# li
	li		t0, 0                          # EXPECT: srli x8, x8, 16
	li		t0, -16                        # EXPECT: ori x8, x2, -16
	li		t0, 16                         # EXPECT: ori x8, x2, 16
	li		t0, global_thing               # EXPECT: srli x8, x8, 16 : addi x8, x8, -18
	li		t0, global_aligned             # EXPECT: lui x8, $ff00

	# la
	#	medium -8k <= x <= 8k - auipc : addi
	la		t0, local_distant_thing        # EXPECT: auipc x8, $1000 : addi x8, x8, -26

	# lw a0, var1 => auipc a0, %hi(var1) : lw a0, %lo(var1)(a0)
	lw		t0, local_distant_thing        # EXPECT: auipc x8, $1000 : lw x8, -30(x8)
	lb		t0, local_distant_thing        # EXPECT: auipc x8, $0fc0 : lb x8, 30(x8)
	lbu		t0, local_distant_thing        # EXPECT: auipc x8, $0fc0 : lbu x8, 26(x8)

	# sw a0, var1, t0 => auipc t0, ... : sw a0, ...(t0)
	sw		a0, local_distant_thing, t0    # EXPECT: auipc x8, $0fc0 : sw x5, 22(x8)
	sb		a0, local_distant_thing, t0    # EXPECT: auipc x8, $0fc0 : sb x5, 18(x8)

	# call label => auipc ra, ... : jalr ra, ra, ...
1:
	call	local_distant_thing       # EXPECT: auipc x1, $0fc0 : jalr x1, x1, 14
	call	1b                        # EXPECT: jal x1, -4

	# tail label		=> jump label, t1
	tail	local_distant_thing       # EXPECT: auipc x8, $0fc0 : jr x8, 8

	# jump label, rd	=> auipc rd, ... : jr rd, ...
	jump	local_distant_thing, a2   # EXPECT: auipc x7, $0fc0 : jr x7, 4

	# ret => jr ra, 0
	ret                               # EXPECT: jr x1, 0

	# jal offset => jal ra, offset
1:
	jal		1b                         # EXPECT: jal x1, 0

	# jalr rs => jalr ra, rs, 0
	jalr	a0                         # EXPECT: jalr x1, x5, 0
	jalr	ra, a0                     # EXPECT: jalr x1, x5, 0
	jalr	a0, 4                      # EXPECT: jalr x1, x5, 4

	# not rd, rs => xori rd, rs, -1
	not		a0, a1                        # EXPECT: xori x5, x6, -1
	not		zero, a1                      # EXPECT: slli x8, x8, 0

	# seqz rd, rs => sltiu rd, rs, 1
	seqz	a0, a1                        # EXPECT: sltiu x5, x6, 1
	seqz	a0, zero                      # EXPECT: ori x5, x2, 1
	seqz	zero, a1                      # EXPECT: slli x8, x8, 0

	# sltz rd, rs => slt rd, rs, x0
	sltz	a0, a1                        # EXPECT: slti x5, x6, 0
	sltz	a0, zero                      # EXPECT: srli x5, x5, 16
	sltz	zero, a1                      # EXPECT: slli x8, x8, 0

	# Not pseudo in this arch as x0 doesn't exist
	# snez rd, rs => sltu rd, x0, rs
	snez	a0, a1                        # EXPECT: sltu x5, x6, x6
	snez	a0, zero                      # EXPECT: srli x5, x5, 16
	snez	zero, a1                      # EXPECT: slli x8, x8, 0

	# Not pseudo in this arch as x0 doesn't exist
	# sgtz rd, rs => slt rd, x0, rs
	sgtz	a0, a1                        # EXPECT: slt x5, x6, x6
	sgtz	a0, zero                      # EXPECT: srli x5, x5, 16
	sgtz	zero, a1                      # EXPECT: slli x8, x8, 0

	# Not pseudo in this arch as x0 doesn't exist
	# neg rd, rs => sub rd, x0, rs
	neg		a0, a1                        # EXPECT: sub x5, x6, x6
	neg		a0, zero                      # EXPECT: srli x5, x5, 16
	neg		zero, a1                      # EXPECT: slli x8, x8, 0


	# This architecture doesn't have x0, so we need to do certain substitutions
	# when it is used in instructions

	addi	a0, a1, 0          # EXPECT: slli x5, x6, 0
	addi	a0, zero, 4        # EXPECT: ori x5, x2, 4
	addi	zero, a1, 4        # EXPECT: slli x8, x8, 0

	andi	a0, a1, 0          # EXPECT: srli x5, x5, 16
	andi	a0, zero, 4        # EXPECT: srli x5, x5, 16
	andi	zero, a1, 4        # EXPECT: slli x8, x8, 0

	ori		a0, a1, 0          # EXPECT: slli x5, x6, 0
	ori		a0, zero, 4        # EXPECT: ori x5, x2, 4
	ori		zero, a1, 4        # EXPECT: slli x8, x8, 0

	xori	a0, a1, 0          # EXPECT: slli x5, x6, 0
	xori	a0, zero, 4        # EXPECT: ori x5, x2, 4
	xori	zero, a1, 4        # EXPECT: slli x8, x8, 0

	slti	a0, a1, 0          # EXPECT: slti x5, x6, 0
	slti	a0, zero, 4        # EXPECT: ori x5, x2, 1
	slti	a0, zero, -4       # EXPECT: srli x5, x5, 16
	slti	zero, a1, 4        # EXPECT: slli x8, x8, 0

	sltiu	a0, a1, 0          # EXPECT: srli x5, x5, 16
	sltiu	a0, zero, 4        # EXPECT: ori x5, x2, 1
	sltiu	a0, zero, -4       # EXPECT: ori x5, x2, 1
	sltiu	zero, a1, 4        # EXPECT: slli x8, x8, 0

	slli	a0, a1, 0          # EXPECT: slli x5, x6, 0
	srli	a0, a1, 0          # EXPECT: slli x5, x6, 0
	srai	a0, a1, 0          # EXPECT: slli x5, x6, 0

	slli	a0, zero, 4        # EXPECT: srli x5, x5, 16
	srli	a0, zero, 4        # EXPECT: srli x5, x5, 16
	srai	a0, zero, 4        # EXPECT: srli x5, x5, 16

	add		a0, a1, zero       # EXPECT: slli x5, x6, 0
	add		a0, zero, a1       # EXPECT: slli x5, x6, 0
	add		a0, zero, zero     # EXPECT: srli x5, x5, 16
	add		zero, a0, a1       # EXPECT: slli x8, x8, 0

	and		a0, a1, zero       # EXPECT: srli x5, x5, 16
	and		a0, zero, a1       # EXPECT: srli x5, x5, 16
	and		a0, zero, zero     # EXPECT: srli x5, x5, 16
	and		zero, a0, a1       # EXPECT: slli x8, x8, 0

	or		a0, a1, zero       # EXPECT: slli x5, x6, 0
	or		a0, zero, a1       # EXPECT: slli x5, x6, 0
	or		a0, zero, zero     # EXPECT: srli x5, x5, 16
	or		zero, a0, a1       # EXPECT: slli x8, x8, 0

	xor		a0, a1, zero       # EXPECT: slli x5, x6, 0
	xor		a0, zero, a1       # EXPECT: slli x5, x6, 0
	xor		a0, zero, zero     # EXPECT: srli x5, x5, 16
	xor		zero, a0, a1       # EXPECT: slli x8, x8, 0

	sub		a0, a1, zero       # EXPECT: slli x5, x6, 0
	sub		a0, zero, a1       # EXPECT: sub x5, x6, x6
	sub		a0, zero, zero     # EXPECT: srli x5, x5, 16
	sub		zero, a0, a1       # EXPECT: slli x8, x8, 0

	sll		a0, a1, zero       # EXPECT: slli x5, x6, 0
	srl		a0, a1, zero       # EXPECT: slli x5, x6, 0
	sra		a0, a1, zero       # EXPECT: slli x5, x6, 0

	sll		a0, zero, a1       # EXPECT: srli x5, x5, 16
	srl		a0, zero, a1       # EXPECT: srli x5, x5, 16
	sra		a0, zero, a1       # EXPECT: srli x5, x5, 16

	slt		a0, a1, zero       # EXPECT: slti x5, x6, 0
	slt		a0, zero, a1       # EXPECT: slt x5, x6, x6
	slt		zero, a1, a2       # EXPECT: slli x8, x8, 0

	sltu	a0, a1, zero       # EXPECT: srli x5, x5, 16
	sltu	a0, zero, a1       # EXPECT: sltu x5, x6, x6
	sltu	zero, a1, a2       # EXPECT: slli x8, x8, 0


	# Some operations have restrictions on the order or equality of their arguments

	add		a0, a1, a2         # EXPECT: add x5, x6, x7
	add		a0, a2, a1         # EXPECT: add x5, x6, x7
	add		a0, a1, a1         # EXPECT: slli x5, x6, 1

	and		a0, a1, a2         # EXPECT: and x5, x7, x6
	and		a0, a2, a1         # EXPECT: and x5, x7, x6
	and		a0, a1, a1         # EXPECT: slli x5, x6, 0

	or		a0, a1, a2         # EXPECT: or x5, x6, x7
	or		a0, a2, a1         # EXPECT: or x5, x6, x7
	or		a0, a1, a1         # EXPECT: slli x5, x6, 0

	xor		a0, a1, a2         # EXPECT: xor x5, x7, x6
	xor		a0, a2, a1         # EXPECT: xor x5, x7, x6
	xor		a0, a1, a1         # EXPECT: srli x5, x5, 16

	sub		a0, a1, a1         # EXPECT: srli x5, x5, 16

	slt		a0, a1, a1         # EXPECT: srli x5, x5, 16

	sltu	a0, a1, a1         # EXPECT: srli x5, x5, 16


	# These are not supported in any form, so generate an error
	#lw		a0, 4(zero)
	#jalr	ra, zero, 4
	#jr		zero, 4


	# beq mid => bne +4 : j mid     mid out of range of beq but not out of range of j
	blt		a0, a1, _start        # EXPECT: bge x5, x6, 4 : j -$0100
	bgt		a0, a1, _start        # EXPECT: bge x6, x5, 4 : j -$0104
	bltu	a0, a1, _start        # EXPECT: bgeu x5, x6, 4 : j -$0108
	bgtu	a0, a1, _start        # EXPECT: bgeu x6, x5, 4 : j -$010c
	bne		a0, a1, _start        # EXPECT: beq x5, x6, 4 : j -$0110
	bge		a0, a1, _start        # EXPECT: blt x5, x6, 4 : j -$0114
	ble		a0, a1, _start        # EXPECT: blt x6, x5, 4 : j -$0118
	bgeu	a0, a1, _start        # EXPECT: bltu x5, x6, 4 : j -$011c
	bleu	a0, a1, _start        # EXPECT: bltu x6, x5, 4 : j -$0120
	beq		a0, a1, _start        # EXPECT: bne x5, x6, 4 : j -$0124

	bnez	a0, _start            # EXPECT: beq x5, x5, 4 : j -$0128
	beqz	a0, _start            # EXPECT: bne x5, x5, 4 : j -$012c
	bgez	a0, _start            # EXPECT: blt x5, x5, 4 : j -$0130
	bltz	a0, _start            # EXPECT: bge x5, x5, 4 : j -$0134

	# For comparisons against 0, encode as comparison against self
1:	beqz	a0, 1b                # EXPECT beq x5, x5, 0
1:	bnez	a0, 1b                # EXPECT bne x5, x5, 0
1:	bgez	a0, 1b                # EXPECT bge x5, x5, 0
1:	bltz	a0, 1b                # EXPECT blt x5, x5, 0


	# These are special though as ble and bgt are also pseudo-ops
1:	blez	a0, 1b                # EXPECT: blt x5, x5, 0 : beq x5, x5, -2
1:	bgtz	a0, 1b                # EXPECT: blt x5, x5, 4 : bne x5, x5, -2

	# Branch pseudo-ops - swap args and direction of test
1:	bgt		a0, a1, 1b            # EXPECT: blt x6, x5, 0
1:	ble		a0, a1, 1b            # EXPECT: bge x6, x5, 0
1:	bgtu	a0, a1, 1b            # EXPECT: bltu x6, x5, 0
1:	bleu	a0, a1, 1b            # EXPECT: bgeu x6, x5, 0


	# These are just regular syntax-support checks
	lb		a0, 12(a1)            # EXPECT: lb x5, 12(x6)
	lbu		a0, 12(a1)            # EXPECT: lbu x5, 12(x6)
	lw		a0, 12(a1)            # EXPECT: lw x5, 12(x6)
	sb		a0, 12(a1)            # EXPECT: sb x5, 12(x6)
	sw		a0, 12(a1)            # EXPECT: sw x5, 12(x6)

	lb		a0, (a1)              # EXPECT: lb x5, 0(x6)
	lb		a0, -4(a1)            # EXPECT: lb x5, -4(x6)

	# Testing arithmetic inside branch arguments
	beq		a0, a1, *             # EXPECT: beq x5, x6, 0
	beq		a0, a1, *-2           # EXPECT: beq x5, x6, -2
	beq		a0, a1, *+2           # EXPECT: beq x5, x6, 2


	# n/a due to architecture:

	# j offset => jal x0, offset
	# jr rs => jalr x0, rs, 0
	# call rt, label => auipc rt, ... : jalr rt, rt, ...

	# negb?

	# sext.b?
	# zext.b?

	# la >8k


size = *-_start

data:
	.word _start, size, (size+15)/16
	.asciz "That's all"

