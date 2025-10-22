mul16:
	mv		a2, a0
	li		a0, 0
	li		t0, 16

2:
	slli	a0, a0, 1
	bgez	a1, 1f
	add		a0, a0, a2
1:
	slli	a1, a1, 1
	addi	t0, t0, -1
	bnez	t0, 2b

	ret


div:
	beqz	a1, 3f
	mv		a2, a0
	li		a0, 0
	li		t0, 1

1:
	bltu	a2, a1, 2f
	slli	t0, t0, 1
	slli	a1, a1, 1
	bgez	a1, 1b

1:
	bltu	a2, a1, 2f
	sub		a2, a2, a1
	add		a0, a0, t0
2:
	srli	a1, a1, 1
	srli	t0, t0, 1
	bnez	t0, 1b

	ret

3:
	ebreak

