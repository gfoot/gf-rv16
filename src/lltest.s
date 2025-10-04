* = $2000

_start:
	li x7, 0
	ecall

123:
	j 123b

456:
	j 123b
	j 456b
	j 456f
456:
	j 456f
456:
	j 123b
	j 456b
