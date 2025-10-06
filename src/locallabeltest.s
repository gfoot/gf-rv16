# Quick test that local labels are properly local to the containing global symbol

_start:
	li		sp, 0    # EXPECT: srli x2, x2, 16

	j	.target      # EXPECT: j 4

	nop              # EXPECT: slli x8, x8, 0
.target:
	nop              # EXPECT: slli x8, x8, 0

otherfunc:
	unimp            # EXPECT: lui x8, 0
	j	.target      # EXPECT: j 2

.target:
	nop              # EXPECT: slli x8, x8, 0

