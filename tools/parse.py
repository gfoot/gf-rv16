import re

import error


def parsenumber(text):
	neg = text.startswith("-")
	if neg:
		text = text[1:]
	if text.startswith("$"):
		value = int(text[1:], 16)
	else:
		value = int(text)

	if neg:
		return -value

	return value


TOK_IDENTIFIER = 'ident'
TOK_NUMBER = 'num'
TOK_BINARYOPERATOR = 'binop'
TOK_UNARYOPERATOR = 'unop'
TOK_ENDEXPR = ','
TOK_PARENOPEN = '('
TOK_PARENCLOSE = ')'
TOK_FUNCCALL = 'func('
TOK_REGISTER = 'reg'
TOK_MEMOFFSET = '(m'

re_numbernosign = re.compile(r"(\$[0-9A-Fa-f]+|[0-9]+)(.*)")
re_identifier = re.compile(r"(\*|[.A-Za-z_][.A-Za-z_0-9]*|[0-9]+[bf])(.*)")
re_funccall = re.compile(r'(%[a-zA-Z_][a-zA-Z0-9_]*)\((.*)')
re_register = re.compile(r"([xsta][0-9]|[xsta][0-9][0-9]|zero|sp|ra)($|[^.A-Za-z_0-9].*)")
re_character = re.compile(r"'(([^\\])|\\(.))'(.*)")

binaryoperators = {
	"<<": lambda x,y: x << y,
	">>": lambda x,y: x >> y,
	"==": lambda x,y: x == y,
	"!=": lambda x,y: x != y,
	"<=": lambda x,y: x <= y,
	">=": lambda x,y: x >= y,
	"+": lambda x,y: x + y,
	"-": lambda x,y: x - y,
	"*": lambda x,y: x * y,
	"/": lambda x,y: x // y,
	"&": lambda x,y: x & y,
	"|": lambda x,y: x | y,
	"^": lambda x,y: x ^ y,
	"%": lambda x,y: x % y,
}

unaryoperators = {
	"+": lambda x: x,
	"-": lambda x: -x,
	"~": lambda x: ~x,
	"!": lambda x: x != 0,
	"<": lambda x: x & 0xff,
	">": lambda x: (x >> 8) & 0xff,
}

binaryprecedence = { 
	"|": 5,

	"^": 6, 

	"&": 7, 

	"==": 8, 
	"!=": 8, 

	"<=": 9, 
	">=": 9, 

	"<<": 10, 
	">>": 10, 

	"+": 11, 
	"-": 11, 

	"*": 12, 
	"/": 12, 
	"%": 12,
}


CONTEXT_PRE = 0
CONTEXT_POST = 1
def gettoken(line, context):
	line = line.strip()
	if not line:
		return TOK_ENDEXPR, "$", None

	if context == CONTEXT_PRE:

		m = re_funccall.match(line)
		if m:
			value,line = m.groups()
			return TOK_FUNCCALL, value, line.strip()

		m = re_register.match(line)
		if m:
			value,line = m.groups()
			return TOK_REGISTER, value, line.strip()

		m = re_identifier.match(line)
		if m:
			value,line = m.groups()
			return TOK_IDENTIFIER, value, line.strip()

		m = re_character.match(line)
		if m:
			junk,val1,val2,line = m.groups()
			return TOK_NUMBER, ord(val1 or val2), line.strip()

		m = re_numbernosign.match(line)
		if m:
			value,line = m.groups()
			return TOK_NUMBER, parsenumber(value), line.strip()

		if line[0] in unaryoperators.keys():
			return TOK_UNARYOPERATOR, line[0], line[1:]

		if line[0] == '(':
			return TOK_PARENOPEN, line[0], line[1:]

	elif context == CONTEXT_POST:

		if line[:2] in binaryoperators.keys():
			return TOK_BINARYOPERATOR, line[:2], line[2:]

		if line[0] in binaryoperators.keys():
			return TOK_BINARYOPERATOR, line[0], line[1:]

		if line[0] == ',':
			return TOK_ENDEXPR, line[0], line[1:]

		if line[0] == ')':
			return TOK_PARENCLOSE, line[0], line[1:]

		if line[0] == '(':
			return TOK_MEMOFFSET, line[0], line[1:]

	raise error.AsmSyntaxError(f"Unexpected '{line[0]}'")


def contractstack(stack, precedence):

	while len(stack) >= 2 and stack[-1][0] == TOK_NUMBER:

		if stack[-2][0] == TOK_UNARYOPERATOR:
			value, op = stack[-1][1], stack[-2][1]
			value = unaryoperators[op](value)
			stack[-2:] = [(TOK_NUMBER, value)]
			continue

		if stack[-2][0] == TOK_BINARYOPERATOR:
			op = stack[-2][1]
			if binaryprecedence[op] >= precedence:
				assert len(stack) >= 3 and stack[-3][0] == TOK_NUMBER
				value1,value2 = stack[-3][1], stack[-1][1]
				value = binaryoperators[op](value1, value2)
				stack[-3:] = [(TOK_NUMBER, value)]
				continue

		break


def parseargs(line, identifiervaluelookup, builtinfuncs):

	line = line.strip()
	if not line:
		return []

	args = []
	debug = 0

	context = CONTEXT_PRE
	stack = []
	parendepth = 0
	while True:
		if debug:
			print(stack)

		# Check we don't have some weird contradiction with operators and types at the top of the stack
		if len(stack) >= 2 and stack[-2][0] == TOK_UNARYOPERATOR:
			if stack[-1][0] == TOK_REGISTER:
				raise AsmError(f"Unary operator unsupported for '{stack[-1][0]}'-type argument")

		# Similar for binary operators
		if len(stack) >= 2 and stack[-2][0] == TOK_BINARYOPERATOR:
			if stack[-1][0] == TOK_REGISTER:
				raise AsmError(f"Binary operator unsupported for '{stack[-1][0]}'-type argument")


		toktype, content, line = gettoken(line, context)

		if debug:
			print(f"{toktype} : {content}")

		if toktype == TOK_PARENCLOSE:
			if parendepth < 1:
				raise error.AsmSyntaxError(f"Unmatched ')'")

			contractstack(stack, 0)

			assert len(stack) >= 2

			if stack[-2][0] == TOK_PARENOPEN:
				stack[-2:] = stack[-1:]
				if debug:
					print(stack)
				parendepth -= 1
				continue

			elif stack[-2][0] == TOK_FUNCCALL:
				func,value = stack[-2][1], stack[-1][1]
				stack[-2:] = [(TOK_NUMBER, builtinfuncs[func](value))]
				if debug:
					print(stack)
				parendepth -= 1
				continue

			elif stack[-2][0] == TOK_MEMOFFSET:
				# Remember the register
				regtyp,reg = stack.pop()
				if regtyp != TOK_REGISTER:
					raise AsmError(f"Unsupported type {reg[0]} used as base in register-offset addressing")
				
				# Pop the open parenthesis and contract the stack again
				stack.pop()
				contractstack(stack, 0)

				# This should be the end of the expression so tidy that up
				assert len(stack) == 1

				# Add the numeric argument but with a different token type so the assembler sees the difference
				numtyp,value = stack.pop()
				assert numtyp == TOK_NUMBER
				args.append((TOK_MEMOFFSET,value))

				# Put the register back on the stack so that the usual end-of-expression code can run next
				stack.append((regtyp, reg))

				parendepth -= 1
				continue

			assert False

		elif toktype == TOK_ENDEXPR:

			if parendepth > 0:
				raise error.AsmSyntaxError(f"Unmatched '('")

			contractstack(stack, 0)

			if debug:
				print(stack)

			assert len(stack) == 1
			assert stack[-1][0] == TOK_NUMBER or stack[-1][0] == TOK_REGISTER
			args.append(stack.pop())

			if debug:
				print(f"arg: {args[-1]}")

			context = CONTEXT_PRE

			if content == ',':
				continue
			else:
				break

		elif toktype == TOK_REGISTER:
			stack.append((toktype, content))
			context = CONTEXT_POST
			continue

		elif toktype == TOK_IDENTIFIER:
			stack.append((TOK_NUMBER, identifiervaluelookup(content)))
			context = CONTEXT_POST
			continue

		elif toktype == TOK_NUMBER:
			stack.append((TOK_NUMBER, content))
			context = CONTEXT_POST
			continue

		if toktype == TOK_BINARYOPERATOR:
			contractstack(stack, binaryprecedence[content])

			if stack[-1][0] == TOK_REGISTER:
				raise AsmError(f"Binary operator unsupported for '{stack[-1][0]}'-type argument")

		if toktype == TOK_PARENOPEN or toktype == TOK_FUNCCALL or toktype == TOK_MEMOFFSET:
			parendepth += 1

		stack.append((toktype, content))
		context = CONTEXT_PRE


	return args



if __name__ == "__main__":

	identifiervalue = {
		"a": 12,
		"b": 34,
		"c": 45,
		"r1": 101,
		"label": 17,
		"baseaddr": 4096,
		"*": 8192,
		"reference": 8000,
		"shiftamount": 7,
		"2b": 8188,
		"ofs_stack3": 6,
		"ofs_field2": 4,
	}
	def identlookup(s):
		return identifiervalue[s]


	funcs = {
		"%hi": lambda x: (x>>8) & 0xff,
		"%lo": lambda x: x & 0xff,
		"%pcrel_hi": lambda x: ((x-identifiervalue["*"]) >> 8) & 0xff,
		"%pcrel_lo": lambda x: (x-identifiervalue["*"]) & 0xff,
	}


	for s in [
		"",
		"   ",
		"   a, b , c  ",
		" a1, %pcrel_hi(label+12)",
		"$1234",
		"-$1234",
		"baseaddr + $123",
		"baseaddr + ((*-reference) & ~(1 << shiftamount)) + 2b/2",
		"a1, 12(sp)",
		"a1, ofs_stack3(sp)",
		"a2, ofs_field2(a0)",
	#	"a,,b",
	#	" ( a , b ) , c ",
	#	" a, ( b",
	#	" a), b",
	#	" a, b )",
	#	"!a1",
	#	"a2+5",
	#	"5+a2",
	]:
		print(s)
		print("   ",parseargs(s, identlookup, funcs))

