import re

class IsaProps:
	def __init__(self):
		self.luishift = 8
		self.auipcshift = 8
		self.orimin = -16
		self.orimax = 16
		self.limin = -32
		self.limax = 31
		self.jalmin = -512
		self.jalmax = 510
		self.jmin = -512
		self.jmax = 510
		self.branchmin = -64
		self.branchmax = 62

		self.immed_constraints = {}

		self.register_substitutions = {
			"zero": "x0",
		
			"ra": "x1",
			"sp": "x2",
			"s0": "x3",
			"s1": "x4",
			"a0": "x5",
			"a1": "x6",
			"a2": "x7",
			"t0": "x8",
		}

		for instrs,constr in [
			("lui", "imm8h8z"), # broken
			("auipc", "imm8h8z"),
			("j jal", "imm9ez"),
			("lw lb lbu sb sw li", "imm6z"),
			("addi8", "imm8"),
			("addi andi ori xori", "imm5"),
			("slti", "imm5z"),
			("sltiu", "imm5u"),
			("beq bne beqz bnez", "imm6ez"),
			("blt bge bltu bgeu bltz bgez", "imm5ez"),
			("jr jalr", "imm5ez"),
			("slli srai", "imm4zu"),
			("srli", "imm4u"),
		]:
			if constr == "2":
				constr = (2,2,None,None)
			else:
				m = re.match(r"imm([0-9]+)(h([0-9]+))?(e)?(z)?(u)?$", constr)
				assert m
				bits, hgrp, shift, even, zero, uns = m.groups()

				unsmax = 1 << int(bits)
				if uns:
					lo = 0
					hi = unsmax
				else:
					lo = -(unsmax // 2)
					hi = unsmax // 2
				if zero:
					hi -= 1
				elif lo == 0:
					lo += 1

				mult = 2 if even else None
				if hgrp:
					mult = 1 << int(shift)
				if mult:
					lo *= mult
					hi *= mult

				constr = (lo,hi,zero,mult)

			for instr in instrs.split(" "):
				self.immed_constraints[instr] = constr


	def regnum(self, text):
		if text in self.register_substitutions.keys():
			text = self.register_substitutions[text]
		if not text.startswith("x"):
			return None
		try:
			return int(text[1:])
		except ValueError:
			return None


	def checkimmed(self, immed, instr):
		if instr not in self.immed_constraints.keys():
			return False

		immed = immed & 0xffff

		lo,hi,zero,mult = self.immed_constraints[instr]
		if lo < 0 and immed > hi:
			immed -= 65536
		if immed < lo or immed > hi:
			return False

		if immed == 0 and not zero:
			return False

		if mult and immed % mult:
			return False

		return True
		

	def immedconstraints(self, instr):
		if instr not in self.immed_constraints.keys():
			return "no immediate arguments"
		lo,hi,zero,mult = self.immed_constraints[instr]
		if lo == hi:
			return f"must equal {lo}"
		s = f"{lo}..{hi}"
		if not zero:
			s = s + ", non-zero"
		if mult:
			s = s + f", multiple of {mult}"

		return s


