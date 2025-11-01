class AsmError(Exception):
	pass

class AsmSyntaxError(AsmError):
	pass

class SimulatorError(Exception):
	pass

class SimulatedException(SimulatorError):
	pass

