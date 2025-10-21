# Experimenting with what IRQ-handling code might look like
#
# I'm considering whether an ARM-style separate stack pointer may be
# beneficial for IRQ handling, but I am not sure yet, nor whether it
# would then make sense to also fork some other registers.  One
# important question is whether the IRQ handler ever needs to be able
# to see what the values of those other registers were before the
# interrupt.
#
# It is possible that the missing "bit 0" of the program counter could
# be used as an IRQ-disable flag and/or a state flag to drive the
# register swap.  This bit won't exist in the actual program counter
# but will exist in cases where it is transferred to a register, i.e.
# jal, jalr, and auipc.  Theoretically the way to leave IRQ mode is
# just to jump to an "even" address.
#
# Immediate offsets in jump/branch instructions are encoded without
# bit 0, so they are always even and can't be used for this
# transition, but a jump relative to a register that has an odd value
# could be used here, with "ret" being a particularly important
# example.


irqhandler:
	addi	sp, sp, -16        # Reserve stack space for preserving registers
	sw		ra, 14(sp)
	sw		a0, 12(sp)
	sw		a1, 10(sp)
	sw		a2, 8(sp)
	# ... etc ... we probably don't really need to save all of them, it depends on the IRQ handler complexity

	# Handle the hardware interrupt

	lw		ra, 14(sp)
	lw		a0, 12(sp)
	lw		a1, 10(sp)
	lw		a2, 8(sp)
	# ... etc ...
	addi	sp, sp, 16

	# As the interrupt disable flag is built into ra, ret will return from the interrupt correctly
	# However this relies on ra here map to a different register to what it maps to in userspace
	ret


# As the regular calling convention may benefit from being able to store 
# values at negative offsets from sp, on occasion, it may be useful 
# to move the stack somewhere else during interrupt handling.  Here
# is one possible way - we require that user code never store 
# important data at -2(sp), so that we can use it in this fashion.
# This is an acceptable compromise for user code as the use cases
# for storing data below sp will always be at greater offsets than
# this.

irqhandler:
	sw		s1, -2(sp)          # store s1 so we can restore it before returning
	mv		s1, sp              # stash the old stack pointer there
	lui		sp, irqstack        # set up a new stack, where irqstack is appropriately aligned
	# ... save registers etc

	# ... restore registers
	mv		sp, s1
	lw		s1, -2(sp)
	ret


# Another benefit of swapping out the stack is that it the stack pointer
# could then double up as a base pointer for accessing OS global variables
# - e.g. sp points at the OS global variable base, and negative offsets 
# from there are used for saving/restoring registers.


# Before going too far down the ARM-like path, I ought to find out more about
# how these things are meant to be done in RISC-V...

# Notes on standard RISC-V interrupt handling
#
#	CSRs
#		mstatus		machine status register
#						MIE = interrupt enable bit
#						MDT = double-trap bit
#						MPIE = prev MIE bit value
#						MPP = prev priv level (2 bits, 0=user, 3=machine)
#
#		mtvec		machine trap vector, bottom two bits are flags
#						bit 0 = 0: direct mode, all traps go to given address
#						bit 0 = 1: vectored mode, interrupt number times 4 is added to hardware-generated traps
#					reset and nmi vectors defined elsewhere
#
#		mip 		machine interrupt pending register
#					one bit per interrupt cause, numbered according to mcause values
#
#		mie			machine interrupt enable register
#					one bit per interrupt cause, numbered according to mcause values
#
#		mscratch	machine scratch register - e.g. use to store a user register on entry to ISR,
#					and then use the user register to point to global storage for the ISR's use
#
#		mepc		machine exception program counter - address of instruction that was interrupted/caused exception
#
#		mcause		cause of trap
#						top bit = set if caused by interrupt
#						remaining bits = exception code
#
#						interrupts:
#							11 = machine external interrupt
#						traps:
#							2 = illegal instruction
#							3 = breakpoint (including ebreak)
#							8 = ecall from U mode
#							11 = ecall from M mode
#
#						mcause is also set to zero on hard reset, but that may go through a different vector address
#
#		mtval		trap value - information about the trap

# Relevant SYSTEM instructions
#
#	ecall
#	ebreak
#	mret
#	csrrw	rd, csrname, rs1

# An interrupt i will trap to M-mode (priv=3) if all of:
#
#	priv<3 or priv==3 and mstatus.MIE
#	mie & mip & (1<<i)
#	~mdeleg & (1<<i)

# i=11 is external interrupts, i=7 is some sort of timer interrupts that I probably won't use


# Tiny machine RISC-V interrupt handling
#
#	For a system which only supports M-mode, and reset, hardware interrupt, ecall and ebreak
#		-	we can probably do without mip/mie, mscratch, mtval
#		-	mtvec = 0 always because that's easy
#		-	mstatus only has MIE
#		-	mepc is an extra hidden register
#		-	do we need mcause?
#		-	none of these things really exist per se as csrs - but we could implement dedicated
#			instructions for the things we need, and still use the standard syntax for accessing
#			them, just with heavy restrictions like only supporting one register and specific
#			immediate values that we need
#
#	On reset:
#		Set mcause to 0 maybe because it's easy (not interrupt; trap 0 = unaligned instruction)
#		Set pc to 0 (easy) or some other simple value
#		Clear MIE (however that's stored) to disable interrupts
#
#	On hardware interrupt if MIE is set, or on ecall, or on ebreak:
#		Set mepc = pc
#		Set mcause = $800b, $000b, $0003 (int, ecall, ebreak)
#		Set pc = mtvec = 0
#		Clear MIE
#
#	On mret:
#		Set pc = mepc
#		Set MIE
#
#	Before setting MIE, code must first read and save mepc otherwise its value will be lost
#
#	Required operations to support:
#		- mret
#		- read mcause        csrrsi  t0, mcause, 0
#		- read mepc          csrrsi  t0, mepc, 0
#		- write mepc         csrrw   x0, mepc, t0
#		- write MIE          csrrsi  x0, mstatus, 8  &  csrrci  x0, mstatus, 8
#	plus RESET and IRQ of course

traphandler:
	addi	sp, sp, -8          # reserve some space
	sw		t0, 6(sp)           # save t0
	csrrsi	t0, mcause, 0       # read mcause
	bltz	t0, irqhandler      # is it IRQ?
	beqz	t0, resethandler    # hard reset sets to zero
	addi	t0, t0, -11         # 11 = ecall
	beqz	t0, ecallhandler    # is it ecall?
	j		ebreakhandler       # assume ebreak for anything else


irqhandler:
	# save any additional registers we need

	# service the interrupt

	# restore additional registers

	lw		t0, 6(sp)           # restore old t0 value
	addi	sp, sp, 8           # restore sp
	mret                        # return to mepc with interrupts enabled

ecallhandler:
	csrrsi	t0, mepc, 0         # get mepc
	addi	t0, t0, 2           # add 2 to skip the ecall instruction when we return
	sw		t0, 4(sp)           # store this value for later
	csrrsi	t0, mstatus, 8      # set MIE to allow interrupts

	# ecall handling code here

	csrrci	t0, mstatus, 8      # clear MIE to disable interrupts
	lw		t0, 4(sp)           # restore the target mepc value
	csrrw	t0, mepc, t0		# write the mepc value to the register
	lw		t0, 6(sp)           # restore old t0 value
	addi	sp, sp, 8           # restore sp
	mret                        # return to mepc with interrupts enabled


# Or maybe the hardware can call through different vectors for ebreak, ecall, reset, and irq
#
# RISC-V allows reset to be different, and the trap can add 4*cause to the vector for interrupts.
# This would mean that ebreak and ecall would go to mtvec+0 and irq would go to mtvec+11*4=44 (or 
# maybe we'd use 11*2=22 because that's the instruction width)
#
# We don't have to stick to what RISC-V specifies here but let's see how it could look:

		traphandler:
			# ebreak and ecall go to here
$0000		addi	sp, sp, -8
$0002		sw		t0, 6(sp)		# save t0
$0004		csrrsi	t0, mcause, 0
$0006		addi	t0, t0, -3
$0008		beqz	t0, $000c
$000a		j		ecallhandler
$000c		j		ebreakhandler
$000e		nop
		resethandler:
$0010		j		resethandlerimpl
$0012		nop
$0014		nop
		irqhandler:
$0016		...

# I guess it's not too bad but jumping to addresses like $0016 might be harder for the hardware.
#
# mtvec=2 would require ebreak/ecall to set bit 1 while irqhandler would be at $18, setting bits 3 and 4
# and then reset could be at 0 perhaps - this seems a bit easier in hardware

# An alternative is to break from RISC-V and do it more like ARM - say that $0000, $0002, $0004, 
# $0006 are the jump vectors, with the last being for irq for fastest handling:

$0000	ebreakvec:	j	ebreakhandler
$0002	ecallvec:	j	ecallhandler
$0004	resetvec:	j	resethandler
		irqhandler:
$0006		...


# With this approach ecallhandler has a lot more latitude and we can define a calling convention
# that removes a lot of the boilerplate - e.g. use the regular function call convention, so
# there's no need to save t0 or ra and we can just copy mepc into ra and return using 'ret'.
# (This is only possible in an M-mode-only system as otherwise we'd need to return to U-mode.)
#
# This removes the need to support setting a CSR to a particular value as we were only using that
# to write to mepc.  We may also be able to get away with not supporting explicit disabling of
# interrupts, so the only CSR operations would be reading mepc and setting MIE.
ecallhandler:
	csrrsi	ra, mepc, 0         # get mepc into ra
	addi	ra, ra, 2           # add 2 to skip the ecall instruction when we return

	csrrsi	t0, mstatus, 8      # set MIE to allow interrupts

	# ecall handling code here

	ret                         # normal ret, nothing fancy needed


# I still like the ARM-like idea that some registers are shadowed when servicing an interrupt.  A
# low cost approach there could be to shadow just ra - so that when the interrupt-disable bit is
# set, ra refers to a different register (i.e. mepc).  On interrupt/ebreak/ecall that register is 
# set to the current program counter.  The trap handler can't see the true ra value any more, but 
# it doesn't need it.
#
# On top of that, if the MIE state is set/cleared by writing to the non-existent low bit of the
# program counter, then any "jr", "jalr", or "ret" can manipulate it - there's no need for any
# specialist instructions like mret or csrrsi.
ecallhandler:
	mv		t0, ra                     # copy the shadow ra register to t0
	la		a2, .interruptsenabled-1   # form a pointer to .interruptsenabled with the bottom bit cleared
	jr		a2                         # jump through the pointer to enable interrupts
.interruptsenabled:
	# now interrupts are enabled
	addi	ra, t0, 2                  # copy the shadow ra value into the normal ra register, plus 2 to skip the ecall instruction

	# ecall handling code here

	ret                                # normal ret, nothing fancy needed


# ebreak would be handled similarly, but would suffer a bit through not being able to capture 
# and report the full state of the machine (as it can't see true ra)




# Here's a more specific irqhandler based on some 6502 code, focusing on the mechanics of the
# I/O rather than the calling convention which - aside from the need to save registers - 
# doesn't otherwise affect it much:

irqhandler:
	# Save any registers we need before modifying them
	#
	# We seem to benefit from:
	#	t0 - base for OS global memory access
	#	s0 - base for ACIA registers
	#	s1 - base for VIA registers
	#	a0, a1, a2 - general purpose
	addi	sp, sp, -12
	sw		t0, 10(sp)
	sw		s0, 8(sp)
	sw		s1, 6(sp)
	sw		a0, 4(sp)
	sw		a1, 2(sp)
	sw		a2, 0(sp)

	lui		t0, os_globals
	lui		s0, ACIA_BASE
	lui		s1, VIA_BASE

	lb		a0, acia_stat(s0)
	bgez	a0, afterserialreceive

	# ; and #7           ; check for errors
	# ; bne ...          ; TODO: better error handling
	# 
	# ; Check for buffer space and advance the pointer
	lw		a0, g_serial_in_head(t0)
	lw		a1, g_serial_in_tail(t0)
	addi	a0, a0, 1
	beq		a0, a1, bufferfull
	sw		a0, g_serial_in_head(t0)

	# ; Read and store the character
	lb		a1, acia_data(s0)
	sb		a1, 0(a0)

	j		afterserialreceive

bufferfull:
	# ; Read and discard the character
	lb		a1, acia_data(s0)

	# ; Log a "buffer full" error
	lw		a1, g_serial_error(t0)
	ori		a1, a1, SERIAL_ERROR_BUFFERFULL
	sw		a1, g_serial_error(t0)

afterserialreceive:

	# ; If there's no pending VIA interrupt then skip to the end
	lb		a0, via_ifr(s1)
	bgez	a0, aftervia

	# ; Apply the current mask before processing VIA interrupt sources
	lw		a1, g_via_ier(t0)
	and		a0, a0, a1

	# ; Check for timer 1 interrupt
	slli	a0, a0, 9
	bgez	a0, aftertimer1

	# ; xba
	# ;
	# ; Deal with timer 1...
	# ; 
	# ; xba

aftertimer1:

	# ; Check far timer 2 (serial transmit interrupt)
	slli	a0, a0, 1
	bgez	a0, afterserialtransmit

	# ; xba   ; only necessary if other VIA interrupts need to be tested afterwards

	# ; Transfer the next data byte to the serial port and restart the timer to 
	# ; monitor its progress
	lw		a1, g_serial_out_tail(t0)
	lb		a2, 0(a1)
	sb		a2, acia_data(s0)

	# ; Advance the pointer
	addi	a1, a1, 1
	sw		a1, g_serial_out_tail(t0)
	lw		a2, g_serial_out_head(t0)
	bne		a1, a2, buffernotempty

	# ; If the buffer is empty, disable this interrupt source so that next time 
	# ; a character is printed we can reenable it and have the interrupt fire 
	# ; immediately
	li		a1, $20
	sb		a1, via_ier(s1)
	lw		a2, g_via_ier(t0)
	eor		a2, a2, a1
	sw		a2, g_via_ier(t0)

buffernotempty:

	# ; xba   ; only necessary if other VIA interrupts need to be tested afterwards

afterserialtransmit:

	# ; Check other bits as necessary
	# ;
	# ; If any are added here, ensure the "xba" instructions in the previous block 
	# ; are uncommented

aftervia:
	lw		t0, 10(sp)
	lw		s0, 8(sp)
	lw		s1, 6(sp)
	lw		a0, 4(sp)
	lw		a1, 2(sp)
	lw		a2, 0(sp)
	addi	sp, sp, 12
	mret

# That's 52 instructions = 104 bytes
#
# The original 65C816 code was 93 bytes, so this is comparable code density
#
# However the circular buffers abused the 8-bit wrapping behaviour on the 65C816
# and would need more specific wrap handling here.  One simple way to do this 
# would be "ori a1, a1, 16" to force bit 4 set and or:xor to force it clear.
#
# It would be possible to skip the sp adjustments to save two instructions, given 
# that this code cannot be interrupted.
#
# It may also be possible for the VIA and ACIA MMIO registers to be accessed 
# relative to a common base, e.g. by using negative offsets for one of them



# Another option for system calls is to just use jumps and not bother with
# ecall.  Since the system doesn't have privilege modes, and never will
# (will it?), ecall is just a way to call an operating system routine.  It
# disables interrupts at the start of the call, but probably just enables
# them again really soon afterwards.
#
# It is convenient not to have to create an absolute address to call
# through, as that normally requires a register.  We do not have x0 to use
# as a base, either.  However ecall still requires the caller to select a
# function using a register, so we can leverage that to also perform the
# actual call:

	li		a0, SYSCALL_PUTCHAR
	jalr	syscall_entry - SYSCALL_PUTCHAR(a0)     # call to syscall_entry

# The range of offsets supported by jalr is a constraint here - currently
# it's an imm5ez, i.e. -32..30 even numbers only.  li's constant is imm6z so
# it spans numbers from -32 to 31, odd and even.  So if the entry point was
# at $0020 (32) then there's room to support 16 syscall numbers, from 0 to
# 30 in even steps.  If more are required then that could be done through
# additional entry points nearby, using the same underlying even numbers but
# with a different entry point.  The entry points themselves could use the
# value in the register to further indirect through a lookup table.
#
# It's also simple for a macro to wrap up this combination.
#
# There's also this idea:

	li		ra, SYSCALL_PUTCHAR
	lw		ra, syscall_table(ra)
	jalr	(ra)

# This avoids double-jumping as it can jump straight to the correct entry
# point for the requested syscall.  It doesn't pass a syscall number through
# to the called routine, which frees up a register for parameter passing -
# though if the syscall number was useful anyway it could still be passed in
# a0 instead of being loaded into ra.

