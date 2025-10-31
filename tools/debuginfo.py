# Debugging information for GF-RV16 assembled code
#
# For each address that contains an instruction we will allow looking up:
#
#    The source filename and line number
#    Whether this is the final instruction for that line number (e.g. due to pseudoinstructions it may not be)
#    The most recent global label name and address
#
# Maybe also:
#
#    The stack depth within the current function
#    Where to find the return address (ra, or a location relative to sp)
#    Whether this should be considered a terminal location in backtraces


class DebugInfo:

	class AddrInfo:
		def __init__(self):
			self.sourcelocation = None

		def __str__(self):
			if self.sourcelocation:
				filename,linenumber = self.sourcelocation
				return f"\"{filename}:{linenumber}\""
			else:
				return "(source unknown)"

	def __init__(self, builder):
		self.sortedbyvalue = sorted([(v,k) for k,v in builder.symboldict.items() if '.' not in k], reverse=True)
		self.addrinfo = builder.addrinfo

	def __getitem__(self, addr):
		assert (addr&1) == 0
		i = addr // 2
		if i < len(self.addrinfo):
			return self.addrinfo[i]

		return None


	def sym_from_addr(self, addr):
		for v,k in self.sortedbyvalue:
			if v <= addr:
				return k, addr-v
		return None,None

	def getaddrsforline(self, filename, linenumber):
		addrlo = 0x10000
		addrhi = -2
		for i,info in enumerate(self.addrinfo):
			if info.sourcelocation == (filename,linenumber):
				addr = i * 2
				addrlo = min(addrlo, addr)
				addrhi = max(addrhi, addr)
		
		if addrlo < 0x10000:
			return addrlo, addrhi+2-addrlo
		else:
			return None, None


class DebugInfoBuilder:

	def __init__(self):
		self.symboldict = {}
		self.addrinfo = []

	def add_symbol(self, name, value):
		self.symboldict[name] = value

	def set_source_location(self, addr, filename, linenumber):
		annotation = self.addr_annotation(addr)
		annotation.sourcelocation = (filename, linenumber)

	def addr_annotation(self, addr):
		assert (addr&1) == 0
		i = addr // 2
		while i >= len(self.addrinfo):
			self.addrinfo.append(None)

		if self.addrinfo[i] is None:
			self.addrinfo[i] = DebugInfo.AddrInfo()

		return self.addrinfo[i]

	def build(self):
		return DebugInfo(self)

