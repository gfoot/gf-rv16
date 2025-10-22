.include "lib/os.s"
.include "lib/io.s"

_start:

2:
	call	getchar
	call	putchar

1:
	addi	t0, t0, 8
	bgez	t0, 1b

	j		2b

