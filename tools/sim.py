import assem
import error
import os
import sys

from highlevelsimulation import HighLevelSimulation
from microcodesimulation import MicrocodeSimulation
from encode import Encoding
from isaprops import IsaProps


MMIO_BASE = 0xfffe
MMIO_PUTCHAR = MMIO_BASE
MMIO_GETCHAR = MMIO_BASE
MMIO_INPUTSTATE = MMIO_BASE+1
MMIO_SIZE = 2


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

	def __init__(self, simulation, memory, entry=0, log=None, debuginfo=None, inp=None, memcallback=None, enablecoredump=True):
		self.state = simulation.State(self, cycletrace)
		#self.state.setpc(entry)
		#self.state.advancepc()

		self.memory = memory
		self.encoding = Encoding()
		self.isaprops = IsaProps(self.encoding)

		self.log = log if log else Log()

		self.debuginfo = debuginfo

		self.stop = False

		self.inp = inp
		self.pendinginput = None

		self.memcallback = memcallback
		self.enablecoredump = enablecoredump


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

		if addr == MMIO_GETCHAR:
			value = self.pendinginput or 0
			self.pendinginput = None
			return value

		elif addr == MMIO_INPUTSTATE:
			return 1 if self.pendinginput is not None else 0


	def mmio_write(self, addr, value):

		if addr == MMIO_PUTCHAR:
			sys.stdout.write(chr(value))
			sys.stdout.flush()


	def memtrace(self, addr, value, readnotwrite):
		self.log.trace(f"{'R' if readnotwrite else 'W'}:${addr:04x} {'=>' if readnotwrite else '<='} ${value:02x}")
		if self.memcallback:
			self.memcallback(addr, value, readnotwrite)


	def cycletrace(self, text):
		if cycletrace:
			self.log.trace(" "*27 + text)


	def format_arg(self, arg, typ):
		if typ == "r":
			return f"x{arg}"
		elif arg >= -64 and arg <= 64:
			return f"{arg}"
		else:
			return f"${arg:04x}"

	def stepcycle(self):
		if self.stop:
			return True

		if self.inp:
			if (ch := self.inp.getchar()) is not None:
				self.pendinginput = ch & 0xff

		self.state.setirq(self.pendinginput is not None)

		endofinstruction = not self.state.cycle()

		if endofinstruction:
			# Instruction ended
			value = self.memory[self.state.getpc()//2]
			instr,argtypes,args = self.encoding.decode(value)
			argsfmt = ', '.join([f"{self.format_arg(arg,typ)}" for arg,typ in zip(args,argtypes)])
			regsfmt = "  ".join([" ".join([f"{self.state.ureg(n+1):04x}" for n in range(m,m+4)]) for m in range(0,8,4)])
			self.log.trace(f"                {self.state.getpc():04x}  ${value:04x} = {instr:<6}  {argsfmt:<20}   {regsfmt}")

		return endofinstruction

	def step(self):
		try:
			while not self.stepcycle():
				if self.stop:
					break
		except error.SimulatedException as e:
			self.log.error(e)
			self.stop = True

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

			if typ == "addi8" and types == "ri":
				regnum,imm = value
				if regnum == 2 and imm > 65536-128:
					framesize = 65536-imm

			if framesize:
				addr = self.memreadw(sp,True)-2
				sp = (sp + framesize) & 0xffff
			elif len(stackframes) == 1 and self.state.ureg(1) != 0:
				# The very first function might be a leaf function that doesn't need a stack frame
				addr = self.state.ureg(1)-2 # ra
			else:
				break

		return stackframes


	def coredump(self):
		if not self.enablecoredump:
			return

		if False:
			step = 16
			for base in range(0,len(self.memory),step):
				words = self.memory[base:base+step]
				if words == [0] * 16:
					continue
				sys.stdout.write(f"{base*2:04X}:  ")
				sys.stdout.write(" ".join([f"{w:04X}" for w in words]))
				sys.stdout.write("\n")

		with open("core", "wb") as fp:
			for word in self.memory:
				fp.write(bytes((word & 0xff, word >> 8)))
			fp.close()
		sys.stdout.write("core dumped\n")

	def exception(self, index, addr, message):

		self.stop = True

		pc = self.state.getpc()
		sp = self.state.ureg(2)

		exceptionstring = f"Exception {index:02X} at address {addr:04x}: {message}"

		regsstr = f"  pc={pc:04X}  "
		regsstr += "  ".join([f"{self.isaprops.regname(i)}={self.state.ureg(i):04X}" for i in range(1, 9)])

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

		longestsym = max([len(sym) for addr,offset,sym in stackframes if sym])
		if longestsym > 20:
			longestsym = 20

		for i in range(len(stackframes)):
			addr, offset, sym = stackframes[-1-i]
			length = max(longestsym, len(sym) if sym else 0)
			symstr = f"{offset:3} + {sym:{length}}" if sym else "?"

			info = self.debuginfo[addr]
			if info and info.sourcelocation:
				filename, linenumber = info.sourcelocation
				sourcelocation = f"{filename}:{linenumber}"
			else:
				sourcelocation = ""

			sys.stdout.write(f"  {i:3}   {addr:04X}  {symstr}  {sourcelocation}\n")

		sys.stdout.write("\n")

		self.coredump()

		raise error.SimulatedException(exceptionstring)


if __name__ == "__main__":

	from nbio import NonBlockingInput

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
		mem = assembler.assemble(filename, listingfile)
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

	with NonBlockingInput() as inp:
		sim = Sim(simulation, mem, log=log, debuginfo=debuginfo, inp=inp);
		while not sim.stop:
			sim.step()

	if trace:
		tracefile.close()

