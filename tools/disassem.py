import isaprops

props = isaprops.IsaProps()

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


def disassemble(mem):
	on = False

	for i,(instr,argtypes,args) in enumerate(mem):
		if instr == "none":
			if on:
				print("...")
				on = False
			continue

		on = True

		if instr == "data":
			print(f"{2*i:04x}   data    {format_arg(args, 'i')}")
			continue
	
		if instr == "slli" and argtypes == "rri" and args[2] == 0:
			if args[0] == args[1]:
				instr = "nop"
				argtypes = ""
				args = tuple()
			else:
				instr = "mv"
				argtypes = "rr"
				args = (args[0], args[1])
		elif instr == "j" or instr == "jal" and argtypes.endswith("i"):
			args = args[:]
			args[-1] += 2*i
			if instr == "jal" and argtypes == "ri" and args[0] == props.regnum("ra"):
				instr = "call"
				argtypes = "i"
				args = (args[1],)
		elif instr == "lui" and argtypes == "ri" and (args[0]&7) == 0 and args[1] == 0:
			instr = "unimp"
			argtypes = ""
			args = tuple()
		elif (instr == "jr" or instr == "jalr") and argtypes.endswith("i") and args[-1] == 0:
			argtypes = argtypes[:-1]
			args = args[:-1]

		if instr == "jr" and argtypes == "r" and args[0] == props.regnum("ra"):
			instr = "ret"
			argtypes = ""
			args = tuple()

		if instr == "xori" and argtypes == "rri" and args[2] == -1:
			instr = "not"
			argtypes = "rr"
			args = args[:-1]

		if instr == "addi8" and argtypes == "ri":
			instr = "addi"
			argtypes = "rri"
			args = args[:1] + args

		print(f"{2*i:04x}   {instr:<6}  {format_args(args, argtypes)}")

