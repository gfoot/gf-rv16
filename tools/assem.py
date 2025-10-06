import os
import re
import sys

import error
import parse
import disassem
import isaprops


DEBUG = 0

re_assignment = re.compile(r"(\*|[A-Za-z_0-9]+)\s*=(.*)")
re_labeldef = re.compile(r"([.A-Za-z_0-9]+)\s*:(.*)")
re_label = re.compile(r"([.A-Za-z_0-9]+)$")
re_relativelabel = re.compile(r"(\d+[bf])$")
re_instr = re.compile(r"([.A-Za-z]+)\s*(.*)")
re_number = re.compile(r"-?(\$[0-9A-Fa-f]+|[0-9]+)$")
re_directive = re.compile(r"\.([A-Za-z]+)((\s|$).*)")
re_directivearg = re.compile(r'("[^"]*"|[^,]*[^, ])\s*(,|$)\s*(.*)')
re_hilomacro = re.compile(r'%([a-zA-Z0-9_]*)\((.*)\)')

restr_instr = r"([A-Za-z]+)"
restr_inssep = r"\s+"
restr_argsep = r"\s*,\s*"
restr_reg = r"([xsta][0-9]|x1[0-5]|zero|sp|ra)"
restr_imm = r'([^,]*[^, ])'
restr_mem = restr_imm + r"? *\(" + restr_reg + r"\)"
restr_end = r"\s*$"

def compile_insfor_regex(argtypes):
	restrs = {
		"r": restr_reg,
		"i": restr_imm,
		"m": restr_mem
	}

	if argtypes:
		return re.compile(restr_instr + restr_inssep + restr_argsep.join([restrs[typ] for typ in argtypes]) + restr_end)
	else:
		return re.compile(restr_instr + restr_end)


instruction_formats = [(argtypes, compile_insfor_regex(argtypes)) for argtypes in ["rrr", "rri", "rir", "rr", "rm", "ri", "ir", "r", "i", ""]]


instructions_with_pcrel_immed = set([
	"blt", "ble", "bgt", "bge", 
	"bltu", "bleu", "bgtu", "bgeu",
	"beq", "bne", "beqz", "bnez", 
	"bgez", "bltz", "blez", "bgtz",
	"j", "jal", "call", "tail", "jump", "la",
])


branchswaps = {
	"bgt": "blt",
	"bgtu": "bltu",
	"ble": "bge",
	"bleu": "bgeu",
}

branchopposites = {
	"blt":  "bge", 
	"bgt":  "ble", 
	"bltu": "bgeu",  
	"bgtu": "bleu",  
	"bne":  "beq", 
	"bnez": "beqz", 
	"bge":  "blt", 
	"ble":  "bgt", 
	"bgeu": "bltu", 
	"bleu": "bgtu",  
	"beq":  "bne", 
	"beqz": "bnez",  
}

regwrite_ops = {
	"lui", "auipc", "lw", "lb", "lbu",
	"addi", "andi", "ori", "xori", "slti", "sltiu", "slli", "srli", "srai",
	"add", "and", "or", "xor", "sll", "srl", "sra", "slt", "sltu", "sub", "snez", "sgtz", "neg"
}


def format_arg(arg, typ):
	if typ == "r":
		return f"x{arg}"
	elif arg >= -128 and arg <= 128:
		return f"{arg}"
	elif arg >= 0:
		return f"${arg:04X}"
	else:
		return f"-${abs(arg):04X}"

def format_args(args, argtypes):
	if argtypes == "ror":
		return f"{format_arg(args[0],'r')}, {format_arg(args[1],'i')}({format_arg(args[2],'r')})"

	return ', '.join([format_arg(arg,typ) for arg,typ in zip(args, argtypes)])


class Assembler:

	def __init__(self):
		self.filename = None
		self.linenumber = 0

		self.listingfile = None
		self.printlisting = False

		self.isaprops = isaprops.IsaProps()

		self.builtinfuncs = {
			"%lo": lambda value: self.calc_lo_hi(value, self.isaprops.luishift)[0],
			"%hi": lambda value: self.calc_lo_hi(value, self.isaprops.luishift)[1],
			"%pcrel_lo": self.calc_pcrel_lo,
			"%pcrel_hi": self.calc_pcrel_hi,
		}


	def emit(self, instr, argtypes, args, comment=""):

		if self.assemblypass == self.lastpass or DEBUG:
			if instr != "data":
				argsstr = format_args(args, argtypes)
				self.log_listing(f"{self.pos:04x}      {instr:<6} {argsstr:<20}   {'#' if comment else ''} {comment}")

		if self.assemblypass == self.lastpass:
			if instr != "data":
				argsstr = format_args(args, argtypes)
				if self.expectations:
					if self.expectations[0] != f"{instr} {argsstr}".lower():
						self.error(f"Expected {self.expectations[0]}")
					self.expectations = self.expectations[1:]

				for immed,typ in zip(args, argtypes):
					if typ == "i" or typ == "o":
						if not self.isaprops.checkimmed(immed, instr):
							self.error(f"Immediate argument {immed} to instruction {instr} violates constraints: {self.isaprops.immedconstraints(instr)}")

		self.output[self.pos//2] = (instr, argtypes, args)
		self.pos += 2


	def log_listing(self, s):
		if self.listingfile:
			self.listingfile.write(s+"\n")
		if self.printlisting:
			print(s)


	def error(self, s):
		print(f"{self.filename}:{self.linenumber+1}: {s}")
		sys.exit(1)


	def setlabel(self, name, value, allowpadding=False):

		if name in self.labels.keys():

			if self.labels[name] is not None and self.labels[name] != value:

				if self.convergelabels and allowpadding and self.labels[name] > value and self.labels[name] - value <= 2:
					while value < self.labels[name]:
						self.filtered_emit("nop", "", [], "nop (padding)")
						value += 2
					return

				self.converged = False
				self.log_listing(f"non-convergence: label {name}: {self.labels[name]:4x} => {value:4x}")

				if self.assemblypass == self.lastpass:
					self.error(f"Label redefinition: {name}")

		self.labels[name] = value


	def nextrelativelabel(self):
		self.numrelativelabels += 1
		return f".L{self.numrelativelabels}"

	
	def lookuplabel(self, arg):
		if arg == "*":
			return self.pos

		if re_relativelabel.match(arg):
			direction = arg[-1]
			number = arg[:-1]
			
			if direction == 'b':
				if number not in self.backrelativelabels.keys():
					self.error(f"Backward label reference not found: {arg}")
				target = self.backrelativelabels[number]
			elif number in self.forwardrelativelabels.keys():
				target = self.forwardrelativelabels[number]
			else:
				target = self.nextrelativelabel()
				self.forwardrelativelabels[number] = target

			arg = target

		if re_label.match(arg):
			if arg not in self.labels.keys():
				if self.assemblypass > 0:
					self.error(f"Label not defined: {arg}")
				return self.pos
			else:
				value = self.labels[arg]
				if value is not None:
					return value

				return self.pos

		assert False


	def calc_lo_hi(self, value, shift):
		value = value & 0xffff
		lo = value & ((1 << shift) - 1)
		if lo >= (1 << (shift - 1)):
			lo -= 1 << shift
		hi = value - lo
		return lo, hi & 0xffff


	def calc_pcrel_lo(self, value):
		if value in self.relocs.keys():
			value = self.relocs[value]
		elif self.assemblypass == self.lastpass:
			self.error(f"Incorrect usage of %pcrel_lo - no relocation tag found at address {value:X}")
		else:
			value = 0
		value,hi = self.calc_lo_hi(value, self.isaprops.auipcshift)
		return value


	def calc_pcrel_hi(self, value):
		self.relocs[self.pos] = value - self.pos
		lo,value = self.calc_lo_hi(value - self.pos, self.isaprops.auipcshift)
		return value


	def addexpectations(self, expectationstring):
		if self.assemblypass == self.lastpass:
			for fragment in expectationstring.split(":"):
				fragment = fragment.strip()
				self.expectations.append(fragment.lower())


	def assembleline(self, line):

		if line.endswith("\n"):
			line = line[:-1]

		if DEBUG:
			print(f"{self.filename}:{self.linenumber+1}: {line}")


		commentpos = len(line)
		for commentchar in '#;':
			if commentchar in line:
				if line.index(commentchar) < commentpos:
					commentpos = line.index(commentchar)

		comment = line[commentpos+1:]
		line = line[:commentpos]

		if 'EXPECT:' in comment:
			self.addexpectations(comment[comment.index('EXPECT:')+7:].strip())

		line = line.strip()

		m = re_assignment.match(line)
		if m:
			name, argsstring = m.groups()

			values = parse.parseargs(argsstring, self.lookuplabel, self.builtinfuncs)
			if len(values) != 1:
				self.error(f"Assignment has multiple values")

			typ,value = values[0]
			if typ != parse.TOK_NUMBER:
				self.error(f"Assignment rvalue is not a number")

			if name == "*":
				self.pos = value
				return

			self.setlabel(name, value)

			if self.assemblypass == self.lastpass:
				self.log_listing(f"{self.pos:04x}  {name} = ${value:x}")

			return

		m = re_labeldef.match(line)
		if m:
			name = m.group(1)
			line = m.group(2).strip()

			if re_number.match(name):
				if name in self.forwardrelativelabels.keys():
					newname = self.forwardrelativelabels[name]
					del self.forwardrelativelabels[name]
				else:
					newname = self.nextrelativelabel()
				self.backrelativelabels[name] = newname

				self.setlabel(newname, self.pos, True)

				if self.assemblypass == self.lastpass:
					self.log_listing(f"{self.pos:04x}  {name}:    # {newname}")

			else:

				self.setlabel(name, self.pos, True)

				if self.assemblypass == self.lastpass:
					self.log_listing(f"{self.pos:04x}  {name}:")

		m = re_directive.match(line)
		if m:
			directive = m.group(1)
			line = m.group(2).strip()

			args = []
			while line:
				m = re_directivearg.match(line)
				assert m
				args.append(m.group(1))
				line = m.group(3)

			if directive == "asciz" or directive == "string":
				bytestowrite = []
				for arg in args:
					if not arg.startswith('"') or not arg.endswith('"'):
						self.error(f"Invalid string: {arg}")

					s = eval(arg) # Let Python parse the string
					bytestowrite.extend([ord(c) for c in s] + [0])

				if len(bytestowrite) & 1:
					bytestowrite.append(0)

				wordstowrite = [a | (b<<8) for a,b in zip(bytestowrite[::2], bytestowrite[1::2])]

				if self.assemblypass == self.lastpass:
					for i in range(0,len(bytestowrite),16):
						datastr = ','.join([f"{d:02X}" for d in bytestowrite[i:i+16]])
						textstr = ''.join([chr(d) if d >= 32 and d < 128 else '.' for d in bytestowrite[i:i+16]])
						self.log_listing(f"{self.pos+i:04x}      .byt   {datastr:<48}  # {textstr}")


				for word in wordstowrite:
					self.emit("data", "", word)

			elif directive == "word":

				wordstowrite = []

				for arg in args:
					parsed = parse.parseargs(arg, self.lookuplabel, self.builtinfuncs)
					assert len(parsed) == 1
					t,v = parsed[0]
					if t != parse.TOK_NUMBER:
						self.error(f".{directive} argument {arg} is not a number")

					wordstowrite.append(v)

				if self.assemblypass == self.lastpass:
					datastr = ','.join([f"{d:04X}" for d in wordstowrite])
					self.log_listing(f"{self.pos:04X}      .word  {datastr}")

				for word in wordstowrite:
					self.emit("data", "", word)

			elif directive == "include":

				for arg in args:
					if not arg.startswith('"') or not arg.endswith('"'):
						self.error(f"Invalid string: {arg}")
					filename = arg[1:-1]

					searchpath = [ os.path.dirname(self.filename) or "." ]

					found = False
					for path in searchpath:
						if os.path.exists(os.path.join(path, filename)):
							found = True
							break
					
					if not found:
						self.error(f"{filename}: File not found")

					self.assemblefile(os.path.join(path,filename))

			else:
				print(f"Unknown directive {directive}")

			return	

		m = re_instr.match(line)
		if m:
			instr,argsstring = m.groups()

			parsed_args = parse.parseargs(argsstring, self.lookuplabel, self.builtinfuncs)

			args = []
			value_args = []
			argtypes = ""
			for typ,v in parsed_args:

				if typ == parse.TOK_REGISTER:
					argtypes += "r"
					args.append(v)
					value = self.isaprops.regnum(v)
					if value == None:
						self.error(f"Invalid register {v}")

				elif typ == parse.TOK_NUMBER:
					argtypes += "i"
					args.append(format_arg(v, "i"))
					value = v
					if instr in instructions_with_pcrel_immed:
						value -= self.pos

				elif typ == parse.TOK_MEMOFFSET:
					argtypes += "o"
					args.append(format_arg(v, "i"))
					value = v

				value_args.append(value)

			comment = (f"{instr} {', '.join(args)}")

			self.filtered_emit(instr, argtypes, value_args, comment)

			return

		if not line:
			return

		self.error(f"Bad line: [{line}]")
		

	def assemblefile(self, filename):
		oldfilename,oldlinenumber = self.filename,self.linenumber

		self.filename = filename
		with open(filename, "r") as fp:
			lines = fp.readlines()
			fp.close()

		for self.linenumber,line in enumerate(lines):
			try:
				self.assembleline(line)
			except error.AsmError as e:
				self.error(f"{e}")

		self.filename,self.linenumber = oldfilename,oldlinenumber


	def assemble(self, filename, listingfile=None):
		self.listingfile = listingfile

		# Labels persist between passes
		self.labels = {}

		self.lastpass = 8

		for self.assemblypass in range(self.lastpass+1):

			self.pos = 0

			self.output = [("none", "", 0)] * 32768

			self.numrelativelabels = 0

			self.backrelativelabels = {}
			self.forwardrelativelabels = {}

			# We don't really do relocations, but some support is required for correct handling of the 
			# canonical syntax for %pcrel_lo
			self.relocs = {}

			self.expectations = []

			self.convergelabels = self.assemblypass >= 4
			self.converged = self.convergelabels

			if self.assemblypass == self.lastpass and DEBUG:
				print(f"\n\nLAST PASS ({self.lastpass})\n\n")

			self.setlabel("_bottom", self.pos)

			self.assemblefile(filename)

			self.setlabel("_top", self.pos, True)

			if self.forwardrelativelabels:
				self.error(f"Undefined forward label references: {' '.join(sorted(self.forwardrelativelabels.keys()))}")

			if self.converged:
				if self.assemblypass == self.lastpass:
					break

				self.lastpass = self.assemblypass + 1


		if self.expectations:
			self.error(f"Unresolved expectations: {' : '.join(self.expectations)}")

		return self.output, self.labels["_start"]


	def builddebuginfo(self):
		debuginfo = {}
		for k,v in self.labels.items():
			if k.startswith("."):
				continue
			if k == "_bottom" or k == "_top":
				continue
			debuginfo[k] = v
		return debuginfo


	def filtered_emit(self, instr, argtypes, value_args, comment, changed = False):
		if instr == "unimp":
			self.emit("lui", "ri", (8, 0), comment)
			return

		if instr == "nop":
			self.filtered_emit("mv", "rr", (8,8), comment, True)
			return

		if instr in regwrite_ops and argtypes.startswith("r") and value_args[0] == 0:
			self.filtered_emit("nop", "", [], comment, True)
			return

		if instr == "ld" or instr == "lhu" or instr == "lh":
			self.filtered_emit("lw", argtypes, value_args, comment, True)
			return

		if instr == "mv":
			assert argtypes == "rr"
			rd,rs1 = value_args
			if rd == 0:
				self.filtered_emit("nop", "", [], comment, True)
			elif rs1 == 0:
				self.filtered_emit("li", "ri", [rd, 0], comment, True)
			else:
				self.filtered_emit("slli", "rri", [rd, rs1, 0], comment, True)
			return

		if instr == "not":
			assert argtypes == "rr"
			rd,rs1 = value_args
			self.filtered_emit("xori", "rri", [rd, rs1, -1], comment, True)
			return

		if instr == "neg":
			assert argtypes == "rr"
			rd,rs1 = value_args
			if rs1 == 0:
				self.filtered_emit("li", "ri", [rd, 0], comment, True)
			else:
				self.emit("sub", "rrr", [rd, rs1, rs1], comment)
			return

		if instr == "snez":
			assert argtypes == "rr"
			rd,rs1 = value_args
			if rs1 == 0:
				self.filtered_emit("li", "ri", [rd, 0], comment, True)
			else:
				self.emit("sltu", "rrr", [rd, rs1, rs1], comment)
			return

		if instr == "sgtz":
			assert argtypes == "rr"
			rd,rs1 = value_args
			if rs1 == 0:
				self.filtered_emit("li", "ri", [rd, 0], comment, True)
			else:
				self.emit("slt", "rrr", [rd, rs1, rs1], comment)
			return

		if instr == "seqz":
			assert argtypes == "rr"
			self.filtered_emit("sltiu", "rri", value_args + [1], comment, True)
			return

		if instr == "sltz":
			assert argtypes == "rr"
			self.filtered_emit("slti", "rri", value_args + [0], comment, True)
			return

		# Load/store with missing immediate
		if argtypes == "rr" and instr in { "lb", "lbu", "lw", "sb", "sw" }:
			r1,r2 = value_args
			self.filtered_emit(instr, "ror", [r1,0,r2], comment, True)
			return

		# Deal with rrr ops with register zero as an argument
		if argtypes == "rrr":
			rd,rs1,rs2 = value_args

			if rs1 == 0:
				if instr in { "and", "sll", "srl", "sra" }:
					self.filtered_emit("li", "ri", [rd, 0], comment, True)
					return
				if instr in { "add", "or", "xor" }:
					self.filtered_emit("mv", "rr", [rd, rs2], comment, True)
					return
				if instr == "sub":
					self.filtered_emit("neg", "rr", [rd, rs2], comment, True)
					return
				if instr == "slt":
					self.filtered_emit("sgtz", "rr", [rd, rs2], comment, True)
					return
				if instr == "sltu":
					self.filtered_emit("snez", "rr", [rd, rs2], comment, True)
					return
				self.error(f"Unsupported rrr operation with rs1=0: {instr} {value_args} # {comment}")

			if rs2 == 0:
				if instr in { "add", "sub", "or", "xor", "sll", "srl", "sra" }:
					self.filtered_emit("mv", "rr", [rd, rs1], comment, True)
					return
				if instr == "and" or instr == "sltu":
					self.filtered_emit("li", "ri", [rd, 0], comment, True)
					return
				if instr == "slt":
					self.filtered_emit("slti", "rri", [rd, rs1, 0], comment, True)
					return
				self.error(f"Unsupported rrr operation with rs1=0: {instr} {value_args} # {comment}")

			# rs1==rs2 needs special handling for several cases
			if rs1 == rs2:
				if instr in { "xor", "slt", "sltu", "sub" }:
					self.filtered_emit("li", "ri", [rd, 0], comment, True)
					return
				if instr == "add":	
					self.filtered_emit("slli", "rri", [rd, rs1, 1], comment, True)
					return
				if instr == "and" or instr == "or":
					self.filtered_emit("mv", "rr", [rd, rs1], comment, True)
					return
				# Other cases are fine so fall through
			
			# and/add/or/xor have order-of-argument requirements
			if rs1 < rs2 and (instr == "and" or instr == "xor") or rs2 < rs1 and (instr == "add" or instr == "or"):
				# Swap the arguments
				self.filtered_emit(instr, argtypes, [ rd, rs2, rs1 ], comment, True)
				return

		# Deal with rri ops with zero as an argument
		if argtypes == "rri":
			rd,rs1,imm = value_args
			if imm == 0:
				if instr in { "addi", "ori", "xori" }:
					self.filtered_emit("mv", "rr", [rd, rs1], comment, True)
					return
				if instr == "andi" or instr == "sltiu":
					self.filtered_emit("li", "ri", [rd, 0], comment, True)
					return
				if instr == "srli" or instr == "srai":
					self.filtered_emit("slli", "rri", [rd, rs1, 0], comment, True)
					return
			if rs1 == 0:
				if instr in { "lw", "lb", "lbu", "sb", "sw" }:
					self.error(f"Load/store operations with register zero as base are not supported")
				if instr in { "addi", "ori", "xori" }:
					self.filtered_emit("li", "ri", [rd, imm], comment, True)
					return
				if instr == "sltiu" or instr == "slti" and imm > 0:
					self.filtered_emit("li", "ri", [rd, 1], comment, True)
					return
				if instr in { "slti", "andi", "slli", "srli", "srai" }:
					self.filtered_emit("li", "ri", [rd, 0], comment, True)
					return
			if rd == 0 and instr in { "sw", "sb" }:
				self.error(f"Store operations with source register zero are not supported")

		if instr == "li":
			assert argtypes == "ri"
			reg, value = value_args

			if value & 0xffff == 0:
				self.filtered_emit("srli", "rri", [reg, reg, 16], comment, True)
				return

			if value >= self.isaprops.orimin and value <= self.isaprops.orimax:
				self.filtered_emit("ori", "rri", [reg, self.isaprops.regnum("sp"), value], comment, True)
				return

			lo,hi = self.calc_lo_hi(value, self.isaprops.luishift)

			self.filtered_emit("lui", "ri", [reg, hi], comment, True)
			if lo:
				self.filtered_emit("addi", "rri", [reg, reg, lo], comment, True)
			return

		if instr == "la":
			assert argtypes == "ri"
			reg, value = value_args

			lo,hi = self.calc_lo_hi(value, self.isaprops.auipcshift)

			self.filtered_emit("auipc", "ri", [reg, hi], comment, True)
			self.filtered_emit("addi", "rri", [reg, reg, lo], comment, True)
			return

		if instr == "lui":
			assert argtypes == "ri"
			reg, value = value_args
			if value & 0xffff == 0:
				self.filtered_emit("li", "ri", [reg, 0], comment, True)
				return
			if value < 0 or value > 0xffff:
				self.filtered_emit("lui", "ri", [reg, value & 0xffff], comment, True)
				return
			# else fall through

		if argtypes == "ri" and instr in {"lw", "lb", "lbu"}:
			# e.g. "lw t0, somelabel"
			reg, value = value_args

			lo,hi = self.calc_lo_hi(value - self.pos, self.isaprops.auipcshift)

			self.filtered_emit("auipc", "ri", [reg, hi], comment, True)
			self.filtered_emit("addi", "rri", [reg, reg, lo], comment, True)
			self.filtered_emit(instr, "ror", [reg, 0, reg], comment, True)
			return

		if argtypes == "rir" and instr in {"sw", "sb"}:
			# e.g. "sw a0, somelabel, t0"
			rs1, value, rs2 = value_args

			lo,hi = self.calc_lo_hi(value - self.pos, self.isaprops.auipcshift)

			self.filtered_emit("auipc", "ri", [rs2, hi], comment, True)
			self.filtered_emit("addi", "rri", [rs2, rs2, lo], comment, True)
			self.filtered_emit(instr, "ror", [rs1, 0, rs2], comment, True)
			return

		if instr == "call" or (instr == "jal" and argtypes == "i"):
			assert argtypes == "i"
			(addr,) = value_args

			reg = self.isaprops.regnum("ra")

			if addr <= self.isaprops.jalmax and addr >= self.isaprops.jalmin:
				self.filtered_emit("jal", "ri", [reg, addr], comment, True)
				return

			lo,hi = self.calc_lo_hi(addr, self.isaprops.auipcshift)

			self.filtered_emit("auipc", "ri", [reg, hi], comment, True)
			self.filtered_emit("addi", "rri", [reg, reg, lo], comment, True)
			self.filtered_emit("jalr", "rri", [reg, reg, 0], comment, True)
			return

		if instr == "jump":
			assert argtypes == "ir"
			(addr,rt) = value_args

			if addr <= self.isaprops.jmax and addr >= self.isaprops.jmin:
				self.filtered_emit("j", "i", [addr], comment, True)
				return

			lo,hi = self.calc_lo_hi(addr, self.isaprops.auipcshift)

			self.filtered_emit("auipc", "ri", [rt, hi], comment, True)
			self.filtered_emit("addi", "rri", [rt, rt, lo], comment, True)
			self.filtered_emit("jr", "ri", [rt, 0], comment, True)
			return

		if instr == "tail":
			assert argtypes == "i"
			self.filtered_emit("jump", "ir", value_args + [self.isaprops.regnum("t0")], comment, True)
			return

		if instr == "jalr":
			if argtypes == "r":
				self.filtered_emit("jalr", "rri", [self.isaprops.regnum("ra"), value_args[0], 0], comment, True)
				return
			elif argtypes == "ri":
				self.filtered_emit("jalr", "rri", [self.isaprops.regnum("ra"), value_args[0], value_args[1]], comment, True)
				return
			elif argtypes == "rr":
				self.filtered_emit("jalr", "rri", value_args + [0], comment, True)
				return
			elif argtypes == "rri" and value_args[1] == 0:
				self.error(f"jr/jalr operations with register zero as base are not supported")

		if instr == "jr" and argtypes == "ri" and value_args[0] == 0:
			self.error(f"jr/jalr operations with register zero as base are not supported")

		if instr == "jr" and argtypes == "r":
			self.filtered_emit("jr", "ri", value_args + [0], comment, True)
			return

		if instr == "ret":
			assert argtypes == ""
			self.filtered_emit("jr", "ri", [self.isaprops.regnum("ra"), 0], comment, True)
			return

		if instr == "beqz":
			assert argtypes == "ri"
			reg, value = value_args
			self.filtered_emit("beq", "rri", [reg, 0, value], comment, True)
			return

		if instr == "bnez":
			assert argtypes == "ri"
			reg, value = value_args
			self.filtered_emit("bne", "rri", [reg, 0, value], comment, True)
			return

		if instr == "bgez":
			assert argtypes == "ri"
			reg, value = value_args
			self.filtered_emit("bge", "rri", [reg, 0, value], comment, True)
			return

		if instr == "bltz":
			assert argtypes == "ri"
			reg, value = value_args
			self.filtered_emit("blt", "rri", [reg, 0, value], comment, True)
			return

		if instr == "blez":
			assert argtypes == "ri"
			reg, value = value_args
			self.filtered_emit("bltz", "ri", [reg, value], comment, True)
			self.filtered_emit("beqz", "ri", [reg, value-2], comment, True)
			return

		if instr == "bgtz":
			assert argtypes == "ri"
			reg, value = value_args
			self.filtered_emit("bltz", "ri", [reg, 4], comment, True)
			self.filtered_emit("bnez", "ri", [reg, value-2], comment, True)
			return

		if instr in { "beq", "bne", "bge", "blt" }:
			assert argtypes == "rri"
			rs1, rs2, value = value_args
			if rs2 == 0:
				self.filtered_emit(instr, "rri", [rs1, rs1, value], comment, True)
				return

		if instr in branchswaps.keys():
			assert argtypes == "rri"
			rs1, rs2, imm = value_args
			self.filtered_emit(branchswaps[instr], "rri", [rs2, rs1, imm], comment, True)
			return

		if instr in branchopposites.keys():
			assert argtypes.endswith("i")
			imm = value_args[-1]
			if imm > self.isaprops.branchmax or imm < self.isaprops.branchmin:
				self.filtered_emit(branchopposites[instr], argtypes, value_args[:-1] + [4], comment, True)
				self.filtered_emit("j", "i", [value_args[-1]-2], comment, True)
				return

		self.emit(instr, argtypes, value_args, comment if changed else "")


if __name__ == "__main__":

	print("Assembling...")
	result, entry = Assembler().assemble(sys.argv[1], sys.stdout)

	print()
	print("Disassembling...")
	disassem.disassemble(result)

