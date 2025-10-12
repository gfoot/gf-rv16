import sys

import assem

def arg2int(arg):
	if arg.startswith("x"):
		value = int(arg[1:])
	elif arg.startswith("$"):
		value = int(arg[1:],16)
	else:
		value = int(arg)
	return value

if __name__ == "__main__":

	filename = sys.argv[1]
	result, entry = assem.Assembler().assemble(filename)

	done = False
	while not done:
		done = True
		pinstr,pargtypes,pargs = None,None,None
		for i,(instr,argtypes,args) in enumerate(result):
			if pinstr == "auipc" and instr == "addi":
				if pargs[0] == args[0] and args[0] == args[1]:
					nargs = [args[0],pargs[1]+args[2]]
					if nargs[1] >= 0x8000:
						nargs[1] -= 0x10000
					result[i-1:i+1] = [("auipc_addi", "ri", nargs)]
					done = False
					break
			if pinstr == "auipc_addi" and instr == "jalr":
				if pargs[0] == args[0] and args[0] == args[1]:
					assert args[2] == 0
					nargs = [args[0],pargs[1]]
					result[i-1:i+1] = [("jal_l", "ri", nargs)]
					done = False
					break
			if pinstr == "auipc_addi" and instr == "jr":
				if pargs[0] == args[0]:
					assert args[1] == 0
					nargs = [pargs[1]]
					result[i-1:i+1] = [("j_l", "i", nargs)]
					done = False
					break
			if pinstr == "beq" and instr == "j" and pargs[2] == 4:
				result[i-1:i+1] = [("bne_l", "rri", pargs[:2] + args)]
				done = False
				break
			if pinstr == "bne" and instr == "j" and pargs[2] == 4:
				result[i-1:i+1] = [("beq_l", "rri", pargs[:2] + args)]
				done = False
				break
			pinstr,pargtypes,pargs = instr,argtypes,args

		# auipc addi load/store
		# auipc addi jalr
		# auipc addi jr
		# bXXX j

	loranges = {}

	hiranges = {}

	frequencies = {}

	hiinstrs = set(["lui", "auipc"])

	for instr, argtypes, args in result:

		if instr == "none" or instr == "data":
			continue

		if instr in { "beq", "bne", "blt", "bge", "beq_l", "bne_l" }:
			if argtypes == "rri" and args[0] == args[1]:
				instr = instr[:3] + "z" + instr[3:]
				argtypes = "ri"
				args = args[1:]

		if "i" not in argtypes and "o" not in argtypes:
			continue

		imm = args[argtypes.index("i") if "i" in argtypes else argtypes.index("o")]

		hibs = 1
		for i in range(16):
			if ((imm >> i) & 1) ^ (imm < 0):
				hibs = i+2

		if hibs < 4:
			hibs = 4

		instr = f"{instr}_{hibs}"

		if instr not in frequencies.keys():	
			frequencies[instr] = 1
		else:
			frequencies[instr] += 1

		lobs,hibs = 0,0
		for i in range(16):
			if imm & (1<<i):
				hibs = i
				if not lobs:
					lobs = i

		if instr in hiinstrs:
			pass
		else:
			hibs = 1
			for i in range(16):
				if ((imm >> i) & 1) ^ (imm < 0):
					hibs = i+2
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
		print(f"{instr:<15} {freq:4}  {lo:5}  {hi:5}  {hibs:5}")


