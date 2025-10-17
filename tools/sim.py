import assem
import os
import sys

from highlevelsimulation import HighLevelSimulation
from microcodesimulation import MicrocodeSimulation
from encode import Encoding


MMIO_BASE = 0xffff
MMIO_PUTCHAR = MMIO_BASE
MMIO_GETCHAR = MMIO_BASE
MMIO_SIZE = 1


LOGLEVEL_ERROR = 0
LOGLEVEL_INFO = 1
LOGLEVEL_TRACE = 2
cycletrace = False

class Log:

	def __init__(self):
		self.level = LOGLEVEL_ERROR
		self.tracefile = None

	def settracefile(self, tracefile):
		self.tracefile = tracefile

	def error(self, s):
		self.do_log(LOGLEVEL_ERROR, s)

	def info(self, s):
		self.do_log(LOGLEVEL_INFO, s)

	def trace(self, s):
		if self.tracefile:
			self.tracefile.write(s+"\n")
		self.do_log(LOGLEVEL_TRACE, s)

	def do_log(self, level, s):
		if self.level >= level:
			print(s)


class Sim:

	class DebugInfo:
		def __init__(self, debuginfo):
			self.symboldict = debuginfo if debuginfo else dict()
			self.sortedbyvalue = sorted([(v,k) for k,v in self.symboldict.items() if '.' not in k], reverse=True)

		def sym_from_addr(self, addr):
			for v,k in self.sortedbyvalue:
				if v <= addr:
					return k, addr-v
			return None,None


	def __init__(self, simulation, memory, entry, log=None, debuginfo=None):
		self.state = simulation.State(self, cycletrace)
		self.state.setpc(entry)
		self.state.advancepc()

		self.instructiondispatcher = simulation.InstructionDispatcher()

		self.memory = memory
		self.encoding = Encoding()

		self.log = log if log else Log()

		self.debuginfo = Sim.DebugInfo(debuginfo)

		self.stop = False

		self.ecall_dispatch = [
			self.ecall_exit,
			self.ecall_print,
			self.ecall_putchar,
			self.ecall_gets,
		]


	def unimp(self):
		self.exception(2, self.pc, f"Illegal instruction (unimp)")

	def memreadw(self, addr, noexcept=False):
		addr &= 0xffff

		if addr & 1:
			if not noexcept:
				self.exception(4, addr, f"Unaligned address during word read")
			return None

		return 0xffff & self.memory[addr // 2]

	def memreadb(self, addr):
		addr &= 0xffff

		if addr >= MMIO_BASE and addr < MMIO_BASE + MMIO_SIZE:
			return self.mmio_read(addr)

		value = self.memory[addr // 2]
		return 0xff & (value >> (8*(addr & 1)))

	def memwritew(self, addr, value):
		addr &= 0xffff
		value &= 0xffff

		if addr & 1:
			self.exception(4, addr, f"Unaligned address during word write")

		self.memory[addr // 2] = value

	def memwriteb(self, addr, value):
		addr &= 0xffff
		value &= 0xff

		if addr >= MMIO_BASE and addr < MMIO_BASE + MMIO_SIZE:
			self.mmio_write(addr, value)
			return

		oldvalue = self.memory[addr // 2]

		if addr & 1:
			value = value << 8 | oldvalue & 0xff
		else:
			value = value | oldvalue & 0xff00

		self.memory[addr // 2] = value


	def mmio_read(self, addr):
		if addr == MMIO_PUTCHAR:
			sys.stdout.flush()
			c = sys.stdin.read(1)
			return ord(c) & 0xff

	def mmio_write(self, addr, value):
		if addr == MMIO_PUTCHAR:
			sys.stdout.write(chr(value))
			sys.stdout.flush()


	def cycletrace(self, text):
		if cycletrace:
			self.log.trace(f"    {text}")


	def format_arg(self, arg, typ):
		if typ == "r":
			return f"x{arg}"
		elif arg >= -64 and arg <= 64:
			return f"{arg}"
		else:
			return f"${arg:04x}"

	def step(self):
		value = self.memory[self.state.getpc()//2]
		instr,argtypes,args = self.encoding.decode(value)


		argsfmt = ', '.join([f"{self.format_arg(arg,typ)}" for arg,typ in zip(args,argtypes)])
		regsfmt = "  ".join([" ".join([f"{self.state.ureg(n+1):04x}" for n in range(m,m+4)]) for m in range(0,8,4)])
		self.log.trace(f"{self.state.getpc():04x}   {instr:<6}  {argsfmt:<20}   {regsfmt}")


		# Dispatch the instruction
		if not self.instructiondispatcher.dispatch(self.state, instr, argtypes, args):
			self.exception(2, self.state.getpc(), f"Unsupported instruction '{instr}' with argtypes '{argtypes}'")


		self.state.advancepc()

		return not self.stop


	def backtrace(self):
		addr = self.state.getpc()
		sp = self.state.ureg(2)

		stackframes = []

		while addr is not None and len(stackframes) < 100:
			sym,offset = self.debuginfo.sym_from_addr(addr)

			stackframes.append((addr, offset, sym))

			if not sym:
				break

			framesize = 0

			# Look at the instruction at sym - if it's addi sp, sp, -nnn then we know the likely frame size
			symaddr = addr - offset
			
			typ,types,value = self.encoding.decode(self.memory[symaddr // 2])

			if typ == "addi" and types == "rri":
				if value[0] == 2 and value[1] == 2 and value[2] < 0 and value[2] > -128:
					framesize = -value[2]

			if framesize:
				addr = self.memreadw(sp,True)-2
				sp = (sp + framesize) & 0xffff
			elif len(stackframes) == 1:
				# The very first function might be a leaf function that doesn't need a stack frame
				addr = self.state.ureg(1)-2 # ra
			else:
				break

		return stackframes


	def exception(self, index, addr, message):

		pc = self.state.getpc()
		sp = self.state.ureg(2)

		exceptionstring = f"Exception {index:02X} at address {addr:04x}: {message}"

		regsstr = f"  pc = {pc:04X}  "
		regsstr += "  ".join([f"x{i} = {self.state.ureg(i):04X}" for i in range(1, 9)])

		def formatstack(addr, count):
			values = []
			for stackaddr in range(addr, addr+2*count, 2):
				value = self.memreadw(stackaddr & 0xffff, True)
				if value is None:
					break
				values.append(value)

			return "  ".join([f"{value:04X}" for value in values])

		stackstr = "  stack:  " + formatstack(sp, 16)

		sys.stdout.write("\n")
		sys.stdout.write("\n")
		sys.stdout.write(exceptionstring+"\n")
		sys.stdout.write("\n")
		sys.stdout.write(regsstr+"\n")
		sys.stdout.write("\n")
		sys.stdout.write(stackstr+"\n")
		sys.stdout.write("\n")

		stackframes = self.backtrace()

		for i in range(len(stackframes)-1, -1, -1):
			addr, offset, sym = stackframes[i]
			symstr = f"{offset:3} + {sym}" if sym else "?"

			sys.stdout.write(f"  {i:3}   {addr:04X}  {symstr}\n")

		sys.stdout.write("\n")

		self.log.error(exceptionstring)
		sys.exit(1)


	def ecall(self):
		func = self.state.sreg(7)

		if func < 0 or func >= len(self.ecall_dispatch):
			self.exception(50, self.state.getpc(), f"Invalid ecall number {func}")

		self.ecall_dispatch[func]()


	def ecall_print(self):
		i = self.state.ureg(5)
		c = 1
		s = ""
		while c:
			c = self.memreadb(i)
			if c:
				s += chr(c)
			i += 1
		sys.stdout.write(s)

	def ecall_putchar(self):
		i = self.state.ureg(5)
		sys.stdout.write(chr(i & 0xff))

	def ecall_exit(self):
		self.stop = True

	def ecall_gets(self):
		p = self.state.ureg(5)
		size = self.state.ureg(6)
		text = input()
		text = text[:size-1]
		for c in text:
			self.memwriteb(p,ord(c))
			p += 1
		self.memwriteb(p,0)
		self.setreg(6, p - self.ureg(5))


if __name__ == "__main__":

	filename = None
	trace = False
	highlevel = False

	for arg in sys.argv[1:]:
		if arg == "--debug":
			assem.DEBUG = 1
			trace = True
		elif arg == "--trace":
			trace = True
		elif arg == "--hl":
			highlevel = True
		elif arg == "--cycletrace":
			cycletrace = True
			trace = True
		elif filename is None:
			filename = arg
		else:
			print("Bad args")
			sys.exit(1)

	if not filename:
		print("Bad args")
		sys.exit(1)

	base,ext = os.path.splitext(filename)
	directory,base = os.path.split(base)
	tracefilename = os.path.join("out", base + ".trace")
	listingfilename = os.path.join("out", base + ".lst")

	print(f"Assembling {filename}...")
	with open(listingfilename, "w") as listingfile:
		assembler = assem.Assembler()
		mem, entry = assembler.assemble(filename, listingfile)
		listingfile.close()

		debuginfo = assembler.builddebuginfo()

	print("Simulating...")

	log = Log()
	if trace:
		tracefile = open(tracefilename, "w")
		log.settracefile(tracefile)

	if highlevel:
		simulation = HighLevelSimulation
	else:
		simulation = MicrocodeSimulation

	sim = Sim(simulation, mem, entry, log, debuginfo)
		
	while sim.step():
		pass

	if trace:
		tracefile.close()

