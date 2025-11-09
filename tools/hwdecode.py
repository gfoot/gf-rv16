from encode import Encoding
import microcodesimulation


if __name__ == "__main__":

	# Crossover between microcode and encoding - we need to map encoded instructions to microcode addresses and other things
	#
	# The hardware decoder will look at specific bits from the instruction and compare against "opcodes" - in which some bits
	# may be "don't care".  Based on that it needs to output a microcode address and instruction-wide control signals that 
	# determine things like immediate widths.
	#
	# Some instructions in encode.py have identical masks and opcodes, due to the consrtaint system.  First of all we will 
	# add some extra bits to the instruction that depend upon the register bit comparisons - the hardware will do these up
	# front and feed the results into the encoder.

	# Bit 16 will be set if bits 7-9 are equal to bits 10-12 (used by a lot of the reg-reg-reg arithmetic instructions)
	# Bit 17 will be set if bits 7-9 are less than bits 10-12 (also used by reg-reg-reg arithmetic instructions)
	# Bit 18 will be set if bits 7-9 are equal to bits 4-6 (used by branch instructions)

	encoding = Encoding()

	ext_instrs = []
	for instr in encoding.instrs.values():
		mask = instr.mask
		opcode = instr.opcode

		if instr.opcode & 0xf == 7:
			# arithmetic instructions
			if instr.constraint == '=':
				mask |= 0x10000
				opcode |= 0x10000
			elif instr.constraint == '!':
				mask |= 0x10000
			elif instr.constraint == '<':
				mask |= 0x20000
				opcode |= 0x20000
			elif instr.constraint == '>': # we actually do >= here
				mask |= 0x20000
		else:
			# branch instructions
			if instr.constraint == '=':
				mask |= 0x40000
				opcode |= 0x40000
			elif instr.constraint == '!':
				mask |= 0x40000
		
		mcaddr = -1
		if instr.name in microcodesimulation.instrs.keys():
			mcaddr = microcodesimulation.instrs[instr.name][0]
		else:
			print(f"no microcode for {instr.name}")
			continue

		ext_instrs.append((mask,opcode,mcaddr,instr))
	
	mask_all = 0
	for mask,opcode,mcaddr,instr in ext_instrs:
		mask_all |= mask
	print(f"Overall mask: {mask_all:05X}")
	
	print()

	#masks = {}
	#for mask,opcode,mcaddr,instr in ext_instrs:
	#	if not mask in masks.keys():
	#		masks[mask] = []
	#	masks[mask].append((opcode,instr))
	#
	#for k,v in sorted(masks.items()):
	#	print(f"{k:04x}: {len(v)}  [" + ','.join(sorted([f"{opc:04x}" for opc,instr in v])) + "]")

	if False:
		print("case? xir is")
		for mask,opcode,mcaddr,instr in ext_instrs:
			opcstr = ''.join(['-' if not mask & (1<<b) else '1' if opcode & (1<<b) else '0' for b in range(18,-1,-1)])
			print(f"    when \"{opcstr}\" => mcaddr <= \"{mcaddr:08b}\"; -- {instr.name}")
		print("end case?;")
		print()

	if True:
		ifword = "   if"
		for mask,opcode,mcaddr,instr in ext_instrs:
			opcstr = ''.join(['-' if not mask & (1<<b) else '1' if opcode & (1<<b) else '0' for b in range(18,-1,-1)])
			print(f"{ifword} xir ?= \"{opcstr}\" then mcaddr <= \"{mcaddr:08b}\"; -- {instr.name}")
			ifword = "elsif"
		print("else mcaddr <= \"11111111\";")
		print("end if;")
		print()


	# See how bad this would look as a set of sums of products
	#
	# For each of the eight output bits, we write a sum-of-products for when it should be set
	outputs = [[] for bitnum in range(8)]
	for mask,opcode,mcaddr,instr in ext_instrs:
		product = [b if opcode & (1<<b) else -b-1 for b in range(18) if mask & (1<<b)]
		for i,outputterms in enumerate(outputs):
			if mcaddr & (1<<i):
				outputterms.append(product[:])

	def format_productterm(term):
		return " & ".join([f" IR{b:<2}" if b >= 0 else f"!IR{-b-1:<2}" for b in term])

	# Reduce the product terms where two terms differ only in one bit
	for i,outputterms in enumerate(outputs):

		dirty = True
		while dirty:
			dirty = False

			for first in range(len(outputterms)-1):
				if first >= len(outputterms)-1:
					break

				for second in range(first+1, len(outputterms)):
					if second >= len(outputterms):
						break

					if len(outputterms[first]) != len(outputterms[second]):
						continue

					if outputterms[first] == outputterms[second]:
						del outputterms[second]
						dirty = True

					match = True
					differences = []
					for i,(f,s) in enumerate(zip(outputterms[first],outputterms[second])):
						if f == s:
							continue
						if f == -s-1:
							differences.append(i)
							continue
						match = False
						break

					if match and len(differences) == 1:
						del outputterms[first][differences[0]]
						del outputterms[second]
						dirty = True

	if True:
		for i,outputterms in enumerate(outputs):
			print(f"MCADDR{i} =    ({len(outputterms)} terms)")
			for term in outputterms:
				print("    " + format_productterm(term))
			print()

