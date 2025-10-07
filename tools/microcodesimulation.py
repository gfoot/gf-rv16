import sys

class MicrocodeEntry:
	def __init__(self, fields):
		assert len(fields) == 11
		self.endz = fields[0] in ("1","z")
		self.endnz = fields[0] in ("1","nz")
		self.high = fields[1] == "high"
		self.bus_a = fields[2] # FIXME: should be individual output control signals
		self.bus_b = fields[3] # FIXME: should be individual output control signals
		self.reg_r = fields[4]
		self.aluop = fields[5]
		self.mar_w = fields[6] == "mar_w"
		self.reg_w = fields[7]
		self.reg_win = fields[8] # Multiplexer
		self.pc_w = fields[9] == "pc_w"
		self.mem_w = fields[10] == "mem_w"

		self.flags = []
		if self.endz: self.flags.append("endz")
		if self.endnz: self.flags.append("endnz")
		if self.high: self.flags.append("high")
		self.flags.append("a_" + self.bus_a)
		self.flags.append("b_" + self.bus_b)
		if self.reg_r: self.flags.append("rr_" + self.reg_r)
		if self.aluop: self.flags.append("aluop_" + self.aluop)
		if self.mar_w: self.flags.append("mar_w")
		if self.reg_w: self.flags.append("rw_" + self.reg_w)
		if self.reg_win: self.flags.append("ri_" + self.reg_win)
		if self.pc_w: self.flags.append("pc_w")
		if self.mem_w: self.flags.append("mem_w")
		

	def __str__(self):
		return ' '.join(self.flags)


with open("doc/microcode.txt") as fp:
	line = fp.readline().strip().split('\t')
	assert line[0].startswith("mnemonic")
	assert line[1] == "cycle"
	columnnames = ["last","high","bus_a","bus_b","reg_r","aluop","mar_w","reg_w","reg_win","pc_w","mem_w"]
	assert line[2:] == columnnames
	
	microcode = []
	instrs = {}
	instr = None

	for line in fp.readlines():
		line = line.strip().split('\t')

		if len(line) < 2 or line[1] == "":
			if instr:
				instr = None
			continue

		if line[0][0] != '.':
			instr,args = line[0].strip().lower().split(" ",1)
			if args.endswith("."):
				args = args[:-1].strip()
			argtypes = ""
			if args:
				args = [arg.strip() for arg in args.split(",")]
				if len(args) == 2 and args[1].endswith(')'):
					args[1:] = args[1][:-1].split('(')

				argtypes = ''.join([arg[0] for arg in args])
				argtypes = argtypes.replace('u','i')

			assert instr not in instrs.keys()
			instrstart = len(microcode)
			instrs[instr] = (instrstart, argtypes, args)

		assert instr
		assert int(line[1]) == len(microcode) - instrstart

		fields = line[2:]
		while len(fields) < len(columnnames):
			fields.append("")

		microcode.append(MicrocodeEntry(fields))


if False:

	print("Microcode instructions:")
	for instr,(mcaddr,argtypes,argnames) in instrs.items():
		print(f"{instr:7} {argtypes:4} {argnames}")


	print()
	print("Microcode:")
	for i,mc in enumerate(microcode):
		instr = ""
		for k,v in instrs.items():
			if v[0] == i:
				instr = k
		print(f"{i:3X}{chr(9)}{instr}{chr(9)}{mc}")

	print()


class MicrocodeSimulation:

	class InstructionDispatcher:

		def dispatch(self, st, instr, argtypes, args):

			if instr == "ecall":
				st.ecall()
				return True

			nextpc = st.getpc() + 2
			st.pcnext = [nextpc & 0xff, nextpc >> 8]

			argtypes = argtypes.replace('o', 'i')

			assert instr in instrs.keys(), f"Instruction not in microcode: '{instr}'"
			#return False

			mcaddr, mcargtypes, mcargnames = instrs[instr]

			assert mcargtypes == argtypes, f"Arg type mismatch with microcode for '{instr}': '{argtypes}' should be '{mcargtypes}'"
			#return False

			argsdict = {}
			for name,arg in zip(mcargnames, args):
				argsdict[name] = arg

			startaddr = mcaddr

			st.env.cycletrace(f"{instr:5} {argtypes:3} {argsdict}")
			while st.cycle(microcode[mcaddr], argsdict, f"${mcaddr:02X} : {mcaddr-startaddr}"):
				mcaddr += 1

			return True


	class State:

		def __init__(self, env):
			self.env = env

			self.regs = [ [0] * 8, [0] * 8 ]
			self.pc = [ 0, 0 ]
			self.pcnext = [ 0, 0 ]
			self.mar = [ 0, 0 ]

		def setreg(self, num, value):
			assert num >= 1 and num <= len(self.regs[0])
			self.regs[0][num-1] = value & 0xff
			self.regs[1][num-1] = (value >> 8) & 0xff

		def sreg(self, num):
			v = self.ureg(num)
			return v if v < 0x8000 else v-0x10000

		def ureg(self, num):
			assert num >= 1 and num <= len(self.regs[0])
			return self.regs[0][num-1] + (self.regs[1][num-1] << 8)

		def getpc(self):
			return self.pc[0] + (self.pc[1] << 8)

		def setpc(self, value, cond=True):
			if cond:
				self.pc = [ value & 0xff, (value >> 8) & 0xff ]

		def memreadw(self, addr): return self.env.memreadw(addr)
		def memreadb(self, addr): return self.env.memreadb(addr)
		def memwritew(self, addr, value): self.env.memwritew(addr, value)
		def memwriteb(self, addr, value): self.env.memwriteb(addr, value)
		def unimp(self): self.env.unimp()
		def ecall(self): self.env.ecall()

		def cycle(self, mc, argsdict, tracestr):

			#print(mc, argsdict)
			hilo = 1 if mc.high else 0			

			if "imm" in mc.bus_a:
				value = argsdict[mc.bus_a]
				if mc.bus_a.startswith("u") and value < 0:
					value += 0x10000
				if mc.bus_a == "immj":
					value -= 2
				bus_a = (value >> 8*hilo) & 0xff
			elif mc.bus_a.startswith("0x"):
				bus_a = int(mc.bus_a[2:],16)
			elif mc.bus_a == "mar":
				bus_a = self.mar[1]
			elif mc.bus_a == "marsx":
				bus_a = 0xff * (self.mar[1] < 0)
			else:
				bus_a = None

			if mc.bus_b == "mem":
				addr = (self.mar[1] << 8) + self.mar[0] + hilo
				bus_b = self.memreadb(addr)
			elif mc.bus_b == "regs":
				regnum = argsdict[mc.reg_r]
				assert regnum >= 1 and regnum <= 8
				bus_b = self.regs[hilo][regnum-1]
			elif mc.bus_b == "pc":
				bus_b = self.pc[hilo]
			elif mc.bus_b == "marn":
				bus_b = self.mar[1] >> 7
			elif mc.bus_b == "":
				bus_b = None
			else:
				assert False, f"Invalid bus_b: '{mc.bus_b}'"

			bus_c = None
			if   mc.aluop == "ad0": value = bus_a + bus_b              ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "ad1": value = bus_a + bus_b + 1          ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "adc": value = bus_a + bus_b + self.carry ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "a+0": value = bus_a                      ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "a+1": value = bus_a + 1                  ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "a+c": value = bus_a + self.carry         ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "and": bus_c = bus_a & bus_b
			elif mc.aluop == "or" : bus_c = bus_a | bus_b
			elif mc.aluop == "xor": bus_c = bus_a ^ bus_b
			elif mc.aluop == "sll": value = (bus_b << 8) + bus_a ; value <<= self.mar[0] ; bus_c = (value >> 8) & 0xff
			elif mc.aluop == "srl": value = (bus_a << 8) + bus_b ; value >>= self.mar[0] ; bus_c = value & 0xff
			elif mc.aluop == "sra": value = (bus_a << 8) + bus_b ; value -= (value & 0x8000) << 1 ; value >>= self.mar[0] ; bus_c = value & 0xff
			elif mc.aluop: assert False, f"Invalid aluop: '{mc.aluop}'"

			if mc.mar_w:
				self.mar = [self.mar[1], bus_c]

			if mc.reg_w:
				regnum = argsdict[mc.reg_w]
				assert regnum >= 1 and regnum <= 8

				if mc.reg_win == "alu":
					value = bus_c
				elif mc.reg_win == "pc":
					value = self.pc[hilo]
				elif mc.reg_win == "pcnext":
					value = self.pcnext[hilo]
				elif mc.reg_win == "zero":
					value = 0
				else:
					assert False, f"Invalid reg_win: '{mc.reg_win}'"

				self.regs[hilo][regnum-1] = value

			if mc.pc_w:
				self.pc[hilo] = bus_c

			if mc.mem_w:
				addr = (self.mar[1] << 8) + self.mar[0] + hilo
				self.memwriteb(addr, bus_b) # Note - not bus_c

			def format16(lo,hi): return f"{hi:02X}{lo:02X}"

			pcstr = format16(self.pc[0], self.pc[1])
			marstr = format16(self.mar[0], self.mar[1])
			regsstr = ' '.join([format16(self.regs[0][i], self.regs[1][i]) + (" " if i==3 else "") for i in range(8)])

			def formatbus(busval): return f"{busval:02X}" if busval is not None else "--"

			busstr = f"a:{formatbus(bus_a)} b:{formatbus(bus_b)} c:{formatbus(bus_c)}"

			self.env.cycletrace(tracestr + f"  pc:{pcstr}  mar:{marstr}  regs: {regsstr}   {busstr}  {mc}")

			if mc.endz and bus_c == 0:
				return False

			if mc.endnz and bus_c != 0:
				return False

			return True

