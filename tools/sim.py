import assem
import os
import sys


LOGLEVEL_ERROR = 0
LOGLEVEL_INFO = 1
LOGLEVEL_TRACE = 2

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

	class InstructionSet:

		def add_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) + st.sreg(rs2))
		def sub_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) - st.sreg(rs2))
		def and_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) & st.sreg(rs2))
		def or_rrr  (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) | st.sreg(rs2))
		def xor_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) ^ st.sreg(rs2))
		def sll_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) << st.sreg(rs2))
		def srl_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) >> st.sreg(rs2))
		def sra_rrr (st, rd, rs1, rs2): st.setreg(rd, st.ureg(rs1) >> st.sreg(rs2))
		def slt_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) < st.sreg(rs2))
		def sltu_rrr(st, rd, rs1, rs2): st.setreg(rd, st.ureg(rs1) < st.ureg(rs2))

		def addi_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) + imm)
		def andi_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) & imm)
		def ori_rri  (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) | imm)
		def xori_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) ^ imm)
		def slli_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) << imm)
		def srli_rri (st, rd, rs1, imm): st.setreg(rd, st.ureg(rs1) >> imm)
		def srai_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) >> imm)
		def slti_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) < imm)
		def sltiu_rri(st, rd, rs1, imm): st.setreg(rd, st.ureg(rs1) < imm)

		def beq_rri (st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) == st.sreg(rs2))
		def bne_rri (st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) != st.sreg(rs2))
		def blt_rri (st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) < st.sreg(rs2))
		def bltu_rri(st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.ureg(rs1) < st.ureg(rs2))
		def bge_rri (st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) >= st.sreg(rs2))
		def bgeu_rri(st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.ureg(rs1) >= st.ureg(rs2))

		def li_ri   (st, rd, imm): st.setreg(rd, imm)
		def lui_ri  (st, rd, imm): st.setreg(rd, imm)
		def auipc_ri(st, rd, imm): st.setreg(rd, imm + st.getpc())
		def jal_ri  (st, rd, imm): st.setreg(rd, st.getpc() + 2) ; st.setpc(st.getpc() + imm - 2)
		def jr_ri   (st, rs1, imm): st.setpc(st.sreg(rs1) + imm - 2)

		def j_i(st, imm): st.setpc(st.getpc() + imm - 2)

		def lb_ror(st, rd, imm, rs1): st.setreg(rd, st.memreadb(imm + st.sreg(rs1)))
		def lbu_ror(st, rd, imm, rs1): st.setreg(rd, st.memreadb(imm + st.sreg(rs1)) & 0xff)
		def lw_ror(st, rd, imm, rs1): st.setreg(rd, st.memreadw(imm + st.sreg(rs1)))
		def sb_ror(st, rs1, imm, rs2): st.memwriteb(imm + st.sreg(rs2), st.sreg(rs1))
		def sw_ror(st, rs1, imm, rs2): st.memwritew(imm + st.sreg(rs2), st.sreg(rs1))

		def jalr_rri(st, rd, rs1, imm): dest=st.sreg(rs1) + imm ; st.setreg(rd, st.getpc() + 2) ; st.setpc(dest - 2)


		def ecall_(st): st.ecall()


	def __init__(self, memory, entry, log):

		self.memory = memory
		self.pc = entry
		self.log = log

		self.regs = [0] * 9

		self.stop = False

		self.ecall_dispatch = [
			self.ecall_exit,
			self.ecall_print,
			self.ecall_putchar,
			self.ecall_gets,
		]


	def setreg(self, num, value):
		assert num > 0 and num < len(self.regs)
		self.regs[num] = value & 0xffff

	def sreg(self, num):
		v = self.regs[num]
		return v if v < 0x8000 else v-0x10000

	def ureg(self, num):
		return self.regs[num]

	def getpc(self):
		return self.pc

	def setpc(self, value, cond=True):
		if cond:
			self.pc = value


	def memreadw(self, addr):

		if addr & 1:
			self.exception(4, addr, f"Unaligned address during word read")

		typ,types,value = self.memory[addr // 2]

		if typ != "data":
			self.exception(5, addr, f"Read from non-data memory ({typ} {value})")

		return value

	def memreadb(self, addr):

		typ,types,value = self.memory[addr // 2]

		if typ != "data":
			self.exception(5, addr, f"Read from non-data memory ({typ} {value})")

		return 0xff & (value >> (8*(addr & 1)))


	def memwritew(self, addr, value):

		typ,types,oldvalue = self.memory[addr // 2]

		if typ == "none":
			typ,oldvalue = "data",0

		if typ != "data":
			self.exception(5, addr, f"Write to non-data memory ({typ} {types} {oldvalue})")

		if addr & 1:
			self.exception(4, addr, f"Unaligned address during word write")

		self.memory[addr // 2] = ("data", None, value & 0xffff)

	def memwriteb(self, addr, value):
		value &= 0xff

		typ,types,oldvalue = self.memory[addr // 2]

		if typ == "none":
			typ,oldvalue = "data",0

		if typ != "data":
			self.exception(5, addr, f"Write to non-data memory ({typ} {types} {oldvalue})")

		if addr & 1:
			value = value << 8 | oldvalue & 0xff
		else:
			value = value | oldvalue & 0xff00

		self.memory[addr // 2] = ("data", None, value & 0xffff)


	def format_arg(self, arg, typ):
		if typ == "r":
			return f"x{arg}"
		else:
			return f"{arg}"

	def step(self):
		instr,argtypes,args = self.memory[self.pc//2]

		if instr == "none" or instr == "data":
			self.exception(1, self.pc, f"Executing non-code ({instr}, {args})")

		argsfmt = ', '.join([f"{self.format_arg(arg,typ)}" for arg,typ in zip(args,argtypes)])
		regsfmt = "  ".join([" ".join([f"{self.regs[n+1]:04x}" for n in range(m,m+4)]) for m in range(0,len(self.regs)-1,4)])
		self.log.trace(f"{self.pc:04x}   {instr:<6}  {argsfmt:<20}   {regsfmt}")


		# Apply decoding fixups
		if instr == "ori" and args[1] == 2:
			args[1] = 0

		if instr in { "beq", "bne", "bge", "blt" } and args[1] == args[0]:
			args[1] = 0

		handler = getattr(self.InstructionSet, instr+"_"+argtypes, None)
		if handler:
			handler(self, *args)
		else:
			self.exception(2, self.pc, f"Unsupported instruction '{instr}' with argtypes '{argtypes}'")

		self.pc += 2

		return not self.stop


	def exception(self, index, addr, message):
		self.log.error(f"Exception {index:02X} at address {addr:04x}: {message}")
		sys.exit(1)


	def ecall(self):
		func = self.sreg(7)

		if func < 0 or func >= len(self.ecall_dispatch):
			self.exception(50, self.pc-2, f"Invalid ecall number {func}")

		self.ecall_dispatch[func]()


	def ecall_print(self):
		i = self.regs[5]
		c = 1
		s = ""
		while c:
			c = self.memreadb(i)
			if c:
				s += chr(c)
			i += 1
		sys.stdout.write(s)

	def ecall_putchar(self):
		i = self.regs[5]
		sys.stdout.write(chr(i & 0xff))

	def ecall_exit(self):
		self.stop = True

	def ecall_gets(self):
		p = self.regs[5]
		size = self.regs[6]
		text = input()
		text = text[:size-1]
		for c in text:
			self.memwriteb(p,ord(c))
			p += 1
		self.memwriteb(p,0)
		self.regs[6] = p - self.regs[5]


if __name__ == "__main__":

	filename = None
	trace = False

	for arg in sys.argv[1:]:
		if arg == "--debug":
			assem.DEBUG = 1
			trace = True
		elif arg == "--trace":
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
		code, entry = assem.Assembler().assemble(filename, listingfile)
		listingfile.close()

	print("Simulating...")

	log = Log()
	if trace:
		tracefile = open(tracefilename, "w")
		log.settracefile(tracefile)

	sim = Sim(code, entry, log)
		
	while sim.step():
		pass

	if trace:
		tracefile.close()

