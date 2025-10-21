.include "defs.s"


resetvector:
	j		os_init

ecallvector:
	ebreak

irqvector:

.include "irq.s"


.include "init.s"

