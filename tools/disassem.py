import isaprops
from encode import Encoding

encoding = Encoding()
props = isaprops.IsaProps(encoding)

def format_arg(arg, typ):
	if typ == "r":
		return props.regname(arg)
	if typ == "c":
		return props.csrname(arg)
	elif arg >= -128 and arg <= 128:
		return f"{arg}"
	elif arg >= 0:
		arg &= 0xffff
		return f"${arg:04X}"
	else:
		arg = (-arg) & 0xffff
		return f"-${arg:04X}"


def format_args(args, argtypes):
	if argtypes == "ror":
		return f"{format_arg(args[0],'r')}, {format_arg(args[1],'i')}({format_arg(args[2],'r')})"

	return ', '.join([format_arg(arg,typ) for arg,typ in zip(args, argtypes)])


def printline(addr, value, text):
	print(f"{2*addr:04x}: {value:04x}      {text}")


def disassemble(mem):
	zerocount = 0
	for i,value in enumerate(mem):
		instr,argtypes,args = encoding.decode(value)
		if value == 0:
			zerocount += 1
			continue

		if zerocount > 4:
			print(f"... zeros x{zerocount} ...")
		else:
			for z in range(zerocount):
				printline(i-zerocount+z, value, ".word   0x0000")

		zerocount = 0

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
			args = args[:-1] + tuple([args[-1] + 2*i])
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

		if instr == "setmie" and argtypes == "r":
			instr = "csrrsi"
			argtypes = "rci"
			args = [args[0], 1, 8]

		if instr == "clrmie" and argtypes == "r":
			instr = "csrrci"
			argtypes = "rci"
			args = [args[0], 1, 8]

		if instr == "rdmepc" and argtypes == "r":
			instr = "csrr"
			argtypes = "rc"
			args = [args[0], 0]

		if instr == "wrmepc" and argtypes == "r":
			instr = "csrw"
			argtypes = "cr"
			args = [0, args[0]]

		printline(i, value, f"{instr:<6}  {format_args(args, argtypes)}")

