.include "lib/os.s"
.include "lib/str.s"
.include "lib/mem.s"
.include "lib/io.s"

_start:
	li		a0, $4000
	li		a1, $11b4
	li		a2, $fe
	call	memsetb

	li		a0, $4200
	li		a1, $11b4
	li		a2, $ff
	call	memsetb

	li		a0, $4401
	li		a1, $11b4
	li		a2, $fe
	call	memsetb

	li		a0, $4601
	li		a1, $11b4
	li		a2, $ff
	call	memsetb

	li		a0, $4010
	li		a1, $3342
	li		a2, 0
	call	memsetb

	li		a0, $4021
	li		a1, $3342
	li		a2, 0
	call	memsetb

	li		a0, $4030
	li		a1, $3342
	li		a2, 1
	call	memsetb

	li		a0, $4041
	li		a1, $3342
	li		a2, 1
	call	memsetb

	li		a0, $4050
	li		a1, $3342
	li		a2, 2
	call	memsetb

	li		a0, $4061
	li		a1, $3342
	li		a2, 2
	call	memsetb

	li		a0, $5000
	li		a1, $11b4
	li		a2, $fe
	call	memset

	li		a0, $5200
	li		a1, $11b4
	li		a2, $ff
	call	memset

	li		a0, $5401
	li		a1, $11b4
	li		a2, $fe
	call	memset

	li		a0, $5601
	li		a1, $11b4
	li		a2, $ff
	call	memset

	li		a0, $5010
	li		a1, $3342
	li		a2, 0
	call	memset

	li		a0, $5021
	li		a1, $3342
	li		a2, 0
	call	memset

	li		a0, $5030
	li		a1, $3342
	li		a2, 1
	call	memset

	li		a0, $5041
	li		a1, $3342
	li		a2, 1
	call	memset

	li		a0, $5050
	li		a1, $3342
	li		a2, 2
	call	memset

	li		a0, $5061
	li		a1, $3342
	li		a2, 2
	call	memset

	ebreak

