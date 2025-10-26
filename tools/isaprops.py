import re


class IsaProps:
	def __init__(self, encoding):
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

		self.regnames = [ "zero", "ra", "sp", "s0", "s1", "a0", "a1", "a2", "t0" ]
		self.csrnames = [ "mepc", "mstatus" ]

		self.immed_constraints = {}

		for instrname, instr in encoding.instrs.items():
			constr = instr.immediateconstraint
			if constr is None:
				continue

			m = re.match(r"imm([0-9]+)(h([0-9]+))?(e)?(z)?(u)?$", constr)
			assert m, f"Unmatchable consrtaint: {constr}"
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

			self.immed_constraints[instrname] = constr

		self.luimultiplier = self.immed_constraints["lui"][3]
		self.auipcmultiplier = self.immed_constraints["auipc"][3]

		self.orimin, self.orimax = self.immed_constraints["ori"][:2]
		self.limin, self.limax = self.immed_constraints["li"][:2]
		self.jalmin, self.jalmax = self.immed_constraints["jal"][:2]
		self.jmin, self.jmax = self.immed_constraints["j"][:2]


	def regnum(self, text):
		if text in self.register_substitutions.keys():
			text = self.register_substitutions[text]
		if not text.startswith("x"):
			return None
		try:
			return int(text[1:])
		except ValueError:
			return None

	def regname(self, value):
		return self.regnames[value]

	def csrnum(self, text):
		return self.csrnames.index(text)

	def csrname(self, value):
		return self.csrnames[value]


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


