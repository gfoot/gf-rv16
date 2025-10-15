# Instruction encoder

encodings = """
  0  0  0   0  0  0   0  0  0   0  0  0   0 0 0 0  	   1          	unimp

  iF iD iC  iB iA i9  i8 iE 0   d  d  d   0 0 0 0  	2048 (8,3)    	lui	rd, imm8hz
  iF iD iC  iB iA i9  i8 iE 1   d  d  d   0 0 0 0  	2048 (8,3)    	auipc	rd, imm8hz
                                                    
  i7 i5 i4  i3 i2 i1  i0 i6 0   d  d  d   0 0 0 1  	2048 (8,3)    	addi8	rd, imm8
  i9 i5 i4  i3 i2 i1  0  i6 1   i7 i8 0   0 0 0 1  	 512 (9,)      	j	imm9ez
  i9 i5 i4  i3 i2 i1  0  i6 1   i7 i8 1   0 0 0 1  	 512 (9,)      	jal	ra, imm9ez
  i5 i0 i4  i3 i2 i1  1  0  1   d  d  d   0 0 0 1  	 512 (6,3)    	li	rd, imm6z
  .  .  .   .  .  .   1  1  1   .  .  .   0 0 0 1  	 512 (6,3)    	.	
                                                   
  i6 i5 i4  i3 i2 i1  s1 s1 s1  d  d  d   0 0 1 0  	4096 (6,3,3) 	lw	rd, rs1, imm6ez
  i6 i5 i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  0 0 1 1  	4096 (6,3,3) 	sw	rs3, rs1, imm6ez
  i5 i0 i4  i3 i2 i1  s1 s1 s1  d  d  d   0 1 0 0  	4096 (6,3,3) 	lb	rd, rs1, imm6z
  i5 i0 i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  0 1 0 1  	4096 (6,3,3) 	sb	rs3, rs1, imm6z
  i5 i0 i4  i3 i2 i1  s1 s1 s1  d  d  d   0 1 1 0  	4096 (6,3,3) 	lbu	rd, rs1, imm6z

  0  0  0   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  <	 224 (3,3,3) 	add	rd, rs1, rs2
  0  0  0   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  >	 224 (3,3,3) 	and	rd, rs1, rs2
  0  0  1   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  <	 224 (3,3,3) 	or	rd, rs1, rs2
  0  0  1   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  >	 224 (3,3,3) 	xor	rd, rs1, rs2
  0  1  0   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  !	 448 (3,3,3) 	sub	rd, rs1, rs2
  0  1  0   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  =	  64 (3,3,3) 	neg	rd, rs1, rs2
  0  1  1   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  	 512 (3,3,3) 	sll	rd, rs1, rs2
  1  0  0   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  	 512 (3,3,3) 	sra	rd, rs1, rs2
  1  0  1   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  	 512 (3,3,3) 	srl	rd, rs1, rs2
  1  1  0   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  !	 448 (3,3,3) 	slt	rd, rs1, rs2
  1  1  0   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  =	  64 (3,3,3) 	sgtz	rd, rs1, rs2
  1  1  1   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  !	 448 (3,3,3) 	sltu	rd, rs1, rs2
  1  1  1   s2 s2 s2  s1 s1 s1  d  d  d   0 1 1 1  =	  64 (3,3,3) 	snez	rd, rs1, rs2

  i6 i5 i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 0 0  !	3584 (6,3,3) 	beq	rs1, rs3, imm6ez
  i6 i5 i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 0 0  =	 512 (6,3) 	beqz	rs1, rs3, imm6ez
           
  i6 i5 i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 0 1  !	3584 (6,3,3) 	bne	rs1, rs3, imm6ez
  i6 i5 i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 0 1  =	 512 (6,3) 	bnez	rs1, rs3, imm6ez
           
  i5 0  i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 1 0  !	1792 (5,3,3) 	bge	rs1, rs3, imm5ez
  i5 0  i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 1 0  =	 256 (5,3) 	bgez	rs1, rs3, imm5ez
  i5 1  i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 1 0  !	1792 (5,3,3) 	bgeu	rs1, rs3, imm5ez
  i5 1  i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 1 0  =	 256 (5,3) 	jr	rs1, rs3, imm5ez
                                                   
  i5 0  i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 1 1  !	1792 (5,3,3) 	blt	rs1, rs3, imm5ez
  i5 0  i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 1 1  =	 256 (5,3) 	bltz	rs1, rs3, imm5ez
  i5 1  i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 1 1  !	1792 (5,3,3) 	bltu	rs1, rs3, imm5ez
  i5 1  i4  i3 i2 i1  s1 s1 s1  s3 s3 s3  1 0 1 1  =	 256 (5,3) 	jalr	rs1, rs3, imm5ez
                                                   
  i4 i0 0   i3 i2 i1  s1 s1 s1  d  d  d   1 1 0 0  	2048 (5,3,3) 	addi	rd, rs1, imm5
  i4 i0 1   i3 i2 i1  s1 s1 s1  d  d  d   1 1 0 0  	2048 (5,3,3) 	andi	rd, rs1, imm5
                                                   
  i4 i0 0   i3 i2 i1  s1 s1 s1  d  d  d   1 1 0 1  	2048 (5,3,3) 	ori	rd, rs1, imm5
  i4 i0 1   i3 i2 i1  s1 s1 s1  d  d  d   1 1 0 1  	2048 (5,3,3) 	xori	rd, rs1, imm5
                                                   
  i4 i0 0   i3 i2 i1  s1 s1 s1  d  d  d   1 1 1 0  	2048 (5,3,3) 	slti	rd, rs1, imm5z
  i4 i0 1   i3 i2 i1  s1 s1 s1  d  d  d   1 1 1 0  	2048 (5,3,3) 	sltiu	rd, rs1, imm5u
                                                   
  0  i0 0   i3 i2 i1  s1 s1 s1  d  d  d   1 1 1 1  	1024 (4,3,3) 	slli	rd, rs1, imm4zu
  0  i0 1   i3 i2 i1  s1 s1 s1  d  d  d   1 1 1 1  	1024 (4,3,3) 	srai	rd, rs1, imm4zu
  1  i0 0   i3 i2 i1  s1 s1 s1  d  d  d   1 1 1 1  	1024 (4,3,3) 	srli	rd, rs1, imm4u

  1  0  1   .  .  .   .  .  .   .  0  0   1 1 1 1  	   1           	ecall
  1  0  1   .  .  .   .  .  .   .  1  0   1 1 1 1  	   1           	ebreak
  1  0  1   .  .  .   .  .  .   .  .  1   1 1 1 1  	   1           	mret

"""
# 1  1  1   .  .  .   .  .  .   .  .  .   1 1 1 1  	   1           	*irq


class RegDef:
	def __init__(self, name, lobit, constraint = None):
		self.type = "r"
		self.name = name
		self.lobit = lobit
		self.constraint = constraint

	def encode(self, value):
		if self.constraint:
			assert value == self.constraint
			return 0
		assert value >= 1 and value <= 8
		return (value & 7) << self.lobit

	def decode(self, encodedvalue):
		if self.constraint:
			return self.constraint
		return (encodedvalue >> self.lobit) & 7 or 8

	def describe(self):
		if self.constraint:
			return f"reg x{self.constraint}"
		return f"reg x1-x8 shift={self.lobit}"

	def test(self):
		if self.constraint:
			assert self.encode(self.constraint) == 0
			assert self.decode(0) == self.constraint
		else:
			for i in range(1,9):
				assert self.decode(self.encode(i)) == i

	def checkandremovebits(self, bits):
		if self.constraint:
			return True

		for i in range(self.lobit):
			assert bits[i] != self.name[1:]
		for i in range(self.lobit, self.lobit+3):
			assert bits[i] == self.name[1:]
			bits[i] = ""
		for i in range(self.lobit+3,len(bits)):
			assert bits[i] != self.name[1:]

		return True


class ImmDef:
	def __init__(self, name, bits, signed, allowzero):
		self.type = "i"
		self.name = name
		self.bits = bits
		topbit = max(bits)
		bottombit = min([bit for bit in bits if bit >= 0])

		self.multiple = 1 << bottombit

		if signed:
			self.maxvalue = (1<<topbit)-1
			self.minvalue = 0xffff & ~self.maxvalue
			self.signextension = self.minvalue
		else:
			self.maxvalue = (2<<topbit)-1
			self.minvalue = 0
			self.signextension = 0

		self.zerovalue = 0
		if not allowzero:
			self.maxvalue += 1
			self.zerovalue = self.maxvalue
			if self.minvalue == 0:
				self.minvalue += 1

		self.maxvalue &= ~(self.multiple-1)

	def describe(self):
		return f"{self.minvalue:04X}-{self.maxvalue:04X}|{self.multiple:X}, 0={self.zerovalue:04X}, -={self.signextension:04X}  {self.bits}"

	def encode(self, value):
		if value == self.zerovalue:
			value = 0
		result = 0
		for i,j in enumerate(self.bits):
			if j >= 0 and value & (1<<j):
				result |= 1<<i
		return result

	def decode(self, encodedvalue):
		result = 0
		for i,j in enumerate(self.bits):
			if j >= 0 and encodedvalue & (1<<i):
				result |= 1<<j
		if result == 0:
			return self.zerovalue
		if result & self.signextension:
			result |= self.signextension
		return result

	def test(self):
		minvalue = self.minvalue
		if self.signextension:
			minvalue -= 0x10000

		for num in range(minvalue, self.maxvalue+1, self.multiple):
			if num == 0 and self.zerovalue:
				continue

			value = num & 0xffff
			print(f"\r{value:04x} => ", end="")
			encodedvalue = self.encode(value)
			print(f"{encodedvalue:04x} => ", end="")
			decodedvalue = self.decode(encodedvalue)
			print(f"{decodedvalue:04x}", end="")
			
			assert decodedvalue == value
		print()

	def checkandremovebits(self, bits):
		for i in range(len(bits)):
			if self.bits[i] >= 0:
				assert bits[i] == f"i{self.bits[i]:X}"
				bits[i] = ""
			else:
				assert not bits[i].startswith("i")


class Instr:
	def __init__(self, line, argdefs):
		split = line.split("\t")
		while len(split) < 4:
			split.append("")
		bits,sizes,instr,args = split[:4]

		self.name = instr

		self.constraint = ""
		bits = [bit.strip() for bit in reversed(bits.split())]
		if len(bits) == 17:
			self.constraint = bits[0]
			bits = bits[1:]
		assert len(bits) == 16

		args = [arg.strip() for arg in args.split(',')]

		self.argtypes = ""

		self.constraintarg2idx = None
		self.constraintarg1idx = None

		self.args = []
		for arg in args:
			if not arg:
				continue

			assert arg in argdefs.keys()
			argdef = argdefs[arg]

			argdef.checkandremovebits(bits)

			if arg.startswith("r"):
				self.argtypes += "r"
				self.constraintarg1idx = self.constraintarg2idx
				self.constraintarg2idx = len(self.args)
			else:
				self.argtypes += "i"

			self.args.append(argdef)

		self.mask = 0
		self.opcode = 0
		for i,bit in enumerate(bits):
			if not bit or bit == ".":
				continue
			assert bit in "01", f"unexpected bit {bit}"
			self.mask |= 1<<i
			if bit == '1':
				self.opcode |= 1<<i

	def encode(self, argtypes, args):

		orig_argtypes = argtypes
		orig_unsigned_args = tuple([arg & 0xffff for arg in args])
		args = tuple(args)

		if self.constraint == "=":
			assert len(args) == len(self.args) - 1, f"{self.name} expected {len(self.args)-1} args but got {len(args)} args"
			assert len(argtypes) == len(self.args) - 1 and argtypes[self.constraintarg1idx] == "r", f"{self.name} expected {len(self.args)-1} args but got {len(argtypes)} argtypes"
			# Special case for encodings where two register fields are required to be equal - if the assembler emits
			# the instruction with only one of the registers specified, insert the other register before encoding,
			# rather than throwing an error
			regarg = args[self.constraintarg1idx]
			argtypes = argtypes[:self.constraintarg2idx] + "r" + argtypes[self.constraintarg2idx:]
			args = args[:self.constraintarg2idx] + (regarg,) + args[self.constraintarg2idx:]

		assert len(args) == len(self.args), f"{self.name} expected {len(self.args)} args but got {len(args)} args"
		assert len(argtypes) == len(self.args), f"{self.name} expected {len(self.args)} args but got {len(argtypes)} argtypes"
		
		result = self.opcode

		if self.constraint:
			if argtypes[self.constraintarg1idx] != "r" or argtypes[self.constraintarg2idx] != "r":
				# The argtypes must be wrong but that will get picked up in the next loop anyway
				pass
			prevregnum = args[self.constraintarg1idx]
			lastregnum = args[self.constraintarg2idx]
			
			if self.constraint == "!":
				assert prevregnum != lastregnum, f"'{self.name}' argument constraint violated: {prevregnum} != {lastregnum}"
			if self.constraint == "=":
				assert prevregnum == lastregnum, f"'{self.name}' argument constraint violated: {prevregnum} == {lastregnum}"
			if self.constraint == "<":
				assert prevregnum < lastregnum, f"'{self.name}' argument constraint violated: {prevregnum} < {lastregnum}"
			if self.constraint == ">":
				assert prevregnum > lastregnum, f"'{self.name}' argument constraint violated: {prevregnum} > {lastregnum}"

		for i,(argtype,arg,argdef) in enumerate(zip(argtypes, args, self.args)):
			assert argdef.type == argtype, f"{self.name} argument {i} should be type {argdef.type} but got type {argtype}"
			result |= argdef.encode(arg)

		# Check the decoding
		decoded = self.decode(result)
		assert decoded, f"'{self.name}' ({args}): decoding '{result:04X}' failed"
		decodedname,decodedargtypes,decodedargs = decoded
		assert (decodedname,decodedargtypes,decodedargs) == (self.name, orig_argtypes, orig_unsigned_args), f"'{self.name}' ({args}): decode mismatch: {decoded} vs {(self.name,argtypes,unsignedargs)}"

		return result


	def decode(self, encodedvalue):
		if encodedvalue & self.mask != self.opcode:
			return False
		args = tuple(argdef.decode(encodedvalue) for argdef in self.args)
		
		if self.constraint:
		    prevregnum = args[self.constraintarg1idx]
		    lastregnum = args[self.constraintarg2idx]

		    if self.constraint == "!" and not prevregnum != lastregnum:
			    return False
		    if self.constraint == "=" and not prevregnum == lastregnum:
			    return False
		    if self.constraint == "<" and not prevregnum < lastregnum:
			    return False
		    if self.constraint == ">" and not prevregnum > lastregnum:
			    return False

		argtypes = self.argtypes

		if self.constraint == "=":
			# Remove the extra copy of the constrained register from the argument list
			argtypes = argtypes[:self.constraintarg2idx] + argtypes[self.constraintarg2idx+1:]
			args = args[:self.constraintarg2idx] + args[self.constraintarg2idx+1:]

		return self.name, argtypes, args


	def __str__(self):
		argstring = ', '.join([arg.name for arg in self.args])
		return f"{self.opcode:04X}/{self.mask:04X} {self.constraint or ' '}  {self.name:5}  {argstring}"


class Encoding:

	def __init__(self):
		self.argdefs = {}
		for name, *args in [
			( "ra", 0, 1 ),
			( "rd", 4 ),
			( "rs1", 7 ),
			( "rs2", 10 ),
			( "rs3", 4 )
		]:
			self.argdefs[name] = RegDef(name, *args)

		for name, *args in [
			( "imm8hz",  [ -1,-1,-1,-1,-1,-1,-1,-1,14, 8, 9,10,11,12,13,15 ], True,  True  ),
			( "imm8",    [ -1,-1,-1,-1,-1,-1,-1,-1, 6, 0, 1, 2, 3, 4, 5, 7 ], True,  False ),
			( "imm9ez",  [ -1,-1,-1,-1,-1, 8, 7,-1, 6,-1, 1, 2, 3, 4, 5, 9 ], True,  True  ),
			( "imm6ez",  [ -1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 2, 3, 4, 5, 6 ], True,  True  ),
			( "imm6z",   [ -1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 2, 3, 4, 0, 5 ], True,  True  ),
			( "imm5",    [ -1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 2, 3,-1, 0, 4 ], True,  False ),
			( "imm5z",   [ -1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 2, 3,-1, 0, 4 ], True,  True  ),
			( "imm5u",   [ -1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 2, 3,-1, 0, 4 ], False, False ),
			( "imm4zu",  [ -1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 2, 3,-1, 0,-1 ], False, True  ),
			( "imm4u",   [ -1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 2, 3,-1, 0,-1 ], False, False ),
			( "imm5ez",  [ -1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 1, 2, 3, 4,-1, 5 ], True,  True  ),
		]:
			self.argdefs[name] = ImmDef(name, *args)

		self.instrs = {}

		for line in encodings.splitlines():
			line = line.strip()
			if not line:
				continue

			instr = Instr(line, self.argdefs)

			if instr.name == ".":
				continue

			assert instr.name not in self.instrs.keys()
			self.instrs[instr.name] = instr

	def encode(self, instr, argtypes, args):
		if instr == "data" or instr == "none":
			assert argtypes == ""
			return args

		assert instr in self.instrs, f"Unknown instruction {instr} {repr((argtypes,args))}"

		if "o" in argtypes:
			assert argtypes == "ror"
			argtypes = "rri"
			args = [args[0], args[2], args[1]]

		encodedvalue = self.instrs[instr].encode(argtypes, args)
		
		decoding = self.decode(encodedvalue)
		unsignedargs = tuple([arg & 0xffff for arg in args])
		assert decoding == (instr, argtypes, unsignedargs), f"Encode-decode mismatch: {repr((instr, argtypes, unsignedargs))} => {encodedvalue:04X} => {repr(decoding)}"

		return encodedvalue
		

	def decode(self, encodedvalue):
		if encodedvalue == 0 or encodedvalue == 0xffff:
			return ("unimp", "", tuple())

		matches = []
		for instr in self.instrs.values():
			decoding = instr.decode(encodedvalue)
			if decoding:
				matches.append((instr,decoding))

		# Use the most specific match (most mask bits set)
		bestmask = 0
		bestdecoding = ("unimp", "", tuple())
		for instr,decoding in matches:
			if instr.mask & bestmask != instr.mask:
				bestmask = instr.mask
				bestdecoding = decoding

		return bestdecoding


	def test(self):
		for name,argdef in self.argdefs.items():
			print(f"{name:6}: {argdef.describe()}")
			argdef.test()

		descs = []
		for k,instr in sorted(self.instrs.items()):
			descs.append(str(instr))
		maxlen = max([len(s) for s in descs]) + 4
		columns = 120 // maxlen
		rows = (len(descs) + columns - 1) // columns
		for i in range(rows):
			print("".join([f"{desc:{maxlen}}" for desc in descs[i::rows]]))


if __name__ == "__main__":

	encoding = Encoding()
	encoding.test()

	for expected, instr, argtypes, args in [
		( 0xf150, "lui", "ri",  (5, 0xf800) ),
		( 0x0d17, "add", "rrr", (1, 2, 3) ),
		( None  , "add", "rrr", (1, 3, 2) ),
		( None  , "and", "rrr", (1, 2, 3) ),
		( 0x0997, "and", "rrr", (1, 3, 2) ),
		( 0x5ad1, "li",  "ri",  (5, 13) ),
		( 0x595d, "ori", "rri", (5, 2, 13) ),
		( 0x59dd, "ori", "rri", (5, 3, 13) ),
		( None  , "bnez","rri", (5, 5, 12) ),
		( 0x1ad9, "bnez","ri",  (5, 12) ),
	]:
		expectedstr = f"{expected:04X}" if expected is not None else "----"
		print(f"{expectedstr} {repr((instr,argtypes,args))}  =>  ", end="")
		try:
			value = encoding.encode(instr, argtypes, args)
		except AssertionError as e:
			assert expected is None, f"Expected {expected:04X} but got exception while encoding {repr((instr,argtypes,args))}"
		else:
			assert expected is not None, f"Expected exception but got {value:04X} while encoding {repr((instr,argtypes,args))}"
			assert value == expected, f"Expected {expected:04X} but got {value:04X} while encoding {repr((instr,argtypes,args))}"

		if expected:
			decoding = encoding.decode(value)
			print(f"{value:04X} {decoding}")
			assert decoding == (instr, argtypes, args)
		else:
			print(f"exception")

	# RISC-V specifies that all-bits-clear and all-bits-set are not valid instruction encodings
	for value in [ 0, 0xffff ]:
		instr, argtypes, args = encoding.decode(value)
		assert instr == "unimp", f"Expected encoding {value:04X} to decode to 'unimp' but got '{instr}' instead"

