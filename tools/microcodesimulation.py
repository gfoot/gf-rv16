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


def format16(lo,hi):
	return f"{hi:02X}{lo:02X}"

def formatbus(busval):
	if busval is not None:
		return f"{busval:02X}"
	else:
		return "--"


class MicrocodeSimulation:

	class InstructionDispatcher:

		def dispatch(self, st, instr, argtypes, args):

			if instr == "ecall":
				st.ecall()
				return True

			nextpc = st.getpc() + 2
			st.pcnext = [nextpc & 0xff, nextpc >> 8]

			argtypes = argtypes.replace('o', 'i')

			if instr not in instrs.keys():
				return False

			mcaddr, mcargtypes, mcargnames = instrs[instr]

			if mcargtypes != argtypes:
				return False

			argsdict = {}
			for name,arg in zip(mcargnames, args):
				argsdict[name] = arg

			startaddr = mcaddr

			if st.trace:
				st.env.cycletrace(f"{instr:5} {argtypes:3} {argsdict}")

			traceprefix = ""

			while True:
				if st.trace:
					traceprefix = f"${mcaddr:02X} : {mcaddr-startaddr}"
				if not st.cycle(microcode[mcaddr], argsdict, traceprefix):
					break
				mcaddr += 1

			return True


	class State:

		def __init__(self, env, trace):
			self.env = env
			self.trace = trace

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
			elif mc.bus_b == "zero":
				bus_b = 0
			elif mc.bus_b == "":
				bus_b = None
			else:
				assert False, f"Invalid bus_b: '{mc.bus_b}'"

			bus_c = None
			if   mc.aluop == "ad0": value = bus_a + bus_b              ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "ad1": value = bus_a + bus_b + 1          ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "adc": value = bus_a + bus_b + self.carry ; bus_c = value & 0xff ; self.carry = value > 0xff
			elif mc.aluop == "and": bus_c = bus_a & bus_b
			elif mc.aluop == "or" : bus_c = bus_a | bus_b
			elif mc.aluop == "xor": bus_c = bus_a ^ bus_b
			elif mc.aluop == "sll": value = (bus_b << 8) + bus_a ; bus_c = (value << self.mar[0] >> 8) & 0xff
			elif mc.aluop == "srl": value = (bus_a << 8) + bus_b ;                                  bus_c = (value >> self.mar[0]) & 0xff
			elif mc.aluop == "sra": value = (bus_a << 8) + bus_b ; value -= (value & 0x8000) << 1 ; bus_c = (value >> self.mar[0]) & 0xff
			elif mc.aluop: assert False, f"Invalid aluop: '{mc.aluop}'"

			if mc.mar_w:
				self.mar = [self.mar[1], bus_c]

			if mc.reg_w:
				if mc.reg_w == "ra":
					regnum = 1
				else:
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


			if self.trace:
			    pcstr = format16(self.pc[0], self.pc[1])
			    marstr = format16(self.mar[0], self.mar[1])
			    regsstr = ' '.join([format16(self.regs[0][i], self.regs[1][i]) + (" " if i==3 else "") for i in range(8)])
			    busstr = f"a:{formatbus(bus_a)} b:{formatbus(bus_b)} c:{formatbus(bus_c)}"

			    self.env.cycletrace(tracestr + f"  pc:{pcstr}  mar:{marstr}  regs: {regsstr}   {busstr}  {mc}")


			if mc.endz and bus_c == 0:
				return False

			if mc.endnz and bus_c != 0:
				return False

			return True


if __name__ == "__main__":

	# Print statistics about the microcode - which combinations of signals are required
	#
	# This informs how it could be packed into a ROM
	#
	# I think in conclusion there are about 16 bits worth of entropy:
	#
	#	Group 0 - 4 bits - aluop, mem_w, mar_w, pc_w
	#	Group 1 - 2 bits - rw, ri
	#	Group 2 - 3 bits - bus b sources
	#	Group 3 - 2 bits - end conditions
	#	Group 4 - 3-4 bits - bus a sources, maybe rw on/off
	#	Group 5 - 1 bit - high/low
	#
	# It depends a bit what happens with the constants in group 4, perhaps some can be 
	# done as immediates in the instruction and save a bit
	#
	# But this is the approximate complexity
	#
	# In group 1, ri_zero can also be derived from mar_w and high, hence only 2 bits; or
	# if an "rw on/off" bit is generated in group 4, it also saves the extra state in 
	# group 1 for no-register-write.  ("ri_zero" is also only present to save one cycle 
	# in a few instructions, so could be removed for little loss.)

	frequencies = [{},{},{},{},{},{}]
	for mc in microcode:

		flags = ([],[],[],[],[],[])

		if mc.aluop: flags[0].append("aluop_" + mc.aluop)
		if mc.mar_w: flags[0].append("mar_w")
		if mc.pc_w: flags[0].append("pc_w")
		if mc.mem_w: flags[0].append("mem_w")

		if mc.reg_w: flags[1].append("rw_" + mc.reg_w)
		if mc.reg_win: flags[1].append("ri_" + mc.reg_win)

		flags[2].append("b_" + mc.bus_b)
		if mc.reg_r: flags[2].append("rr_" + mc.reg_r)

		if mc.endz: flags[3].append("endz")
		if mc.endnz: flags[3].append("endnz")

		flags[4].append("a_" + mc.bus_a)
		#if mc.reg_w: flags[4].append("rw")

		if mc.high: flags[5].append("high")


		for group in range(len(frequencies)):
			s = " ".join(flags[group])

			if s not in frequencies[group].keys():
				frequencies[group][s] = 1
			else:
				frequencies[group][s] += 1

	for group in range(len(frequencies)):
		print(f"\nGroup {group}")

		for i,(v,k) in enumerate(sorted([(v,k) for k,v in frequencies[group].items()])):
			print(f"{i:3} {v:3} {k}")

	print(f"\n\nMicrocode length: {len(microcode)}")
	
	addrs = sorted([(v,k) for k,v in instrs.items()])
	sizes = [[],[],[],[],[],[],[],[],[]]
	for i,((v,x,x),k) in enumerate(addrs):
		nv = addrs[i+1][0][0] if i+1<len(addrs) else len(microcode)
		size = nv - v
		sizes[size].append(k)

	for i,instrs in enumerate(sizes):
		if instrs:
		    print(f"size {i}: {len(instrs):3} instrs")

