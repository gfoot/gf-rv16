# Enter source code here
_start:
	li	a0, 1230
	li	a1, 48
	call	gcd
	ebreak

gcd:
	sub	a2, a0, a1
	bnez	a2, 1f
	ret
1:
	bltz	a2, 1f
	mv	a0, a2
	j	gcd
1:
	neg	a1, a2
	j	gcd

