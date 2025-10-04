import sys

import assem


if __name__ == "__main__":

	filename = sys.argv[1]
	result, entry = assem.Assembler().assemble(filename)

	loranges = {}

	hiranges = {}

	frequencies = {}

	hiinstrs = set(["lui", "auipc"])

	for instr, argtypes, args in result:
		if instr == "none" or instr == "data":
			continue

		if "i" not in argtypes and "o" not in argtypes:
			continue

		if instr not in frequencies.keys():	
			frequencies[instr] = 1
		else:
			frequencies[instr] += 1

		imm = args[argtypes.index("i") if "i" in argtypes else argtypes.index("o")]

		lobs,hibs = 0,0
		for i in range(16):
			if imm & (1<<i):
				hibs = i
				if not lobs:
					lobs = i

		if instr in hiinstrs:
			pass
		else:
			hibs = 0
			for i in range(16):
				if ((imm >> i) & 1) ^ (imm < 0):
					hibs = i
			if instr not in hiranges.keys():
				hiranges[instr] = [imm, imm, hibs]
			else:
				instrstats = hiranges[instr]
				if imm < instrstats[0]:
					instrstats[0] = imm
				elif imm > instrstats[1]:
					instrstats[1] = imm
				if hibs > instrstats[2]:
					instrstats[2] = hibs

	for instr in sorted(hiranges.keys()):
		lo,hi,hibs = hiranges[instr]
		freq = frequencies[instr]
		print(f"{instr:<6}   {freq:5} {lo:5}  {hi:5}  {hibs:5}")

