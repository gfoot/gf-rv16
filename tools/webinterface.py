import sys

from browser import document, html, alert
from browser.timer import request_animation_frame, cancel_animation_frame

import assem
import disassem
import sim


class StdoutToDocument:
	def __init__(self):
		self.element = document["outputwindow"]

	def write(self, characters):
		self.element <= characters
		self.element.scrollTop = self.element.scrollHeight

sys.stdout = StdoutToDocument()


class Interface:
	def __init__(self):
		document["assemblebutton"].bind("click", self.assemble)
		document["disassemblebutton"].bind("click", self.disassemble)
		document["startbutton"].bind("click", self.startsimulation)
		document["stepbutton"].bind("click", self.stepsimulation)
		document["runbutton"].bind("click", self.runsimulation)
		document["stopbutton"].bind("click", self.stopsimulation)

		self.sim = None
		self.assembled = None
		self.debuginfo = None

		self.raf_id = None

		self.memelements = []

	def assemble(self, ev):
		self.sim = None
		self.assembled = None
		self.debuginfo = None

		document["outputwindow"].clear()

		try:
			sourceelement = document["sourcecode"]
			sourcelines = sourceelement.value.splitlines()

			assembler = assem.Assembler()
			self.assembled = assembler.assemble("test.s", sys.stdout, sourcelines)
			self.debuginfo = assembler.builddebuginfo()
		except Exception as e:
			document["outputwindow"] <= str(e)
			document["outputwindow"].scrollTop = document["outputwindow"].scrollHeight

	def disassemble(self, ev):
		if not self.assembled:
			return

		document["outputwindow"].clear()
		disassem.disassemble(self.assembled)

	def startsimulation(self, ev):
		if not self.assembled or not self.debuginfo:
			self.assemble(ev)
			if not self.assembled or not self.debuginfo:
				return

		log = sim.Log()
		self.mem = self.assembled[:]
		self.sim = sim.Sim(sim.MicrocodeSimulation, self.mem, log=log, debuginfo=self.debuginfo, memcallback=self.memcallback)
		self.update_ui()
		self.reset_memory_pane()

	def stepsimulation(self, ev):
		if self.raf_id is not None:
			cancel_animation_frame(self.raf_id)
		if not self.sim:
			self.startsimulation(ev)
			if not self.sim:
				return

		self.do_stepsimulation()

	def runsimulation(self, ev):
		if not self.sim:
			self.startsimulation(ev)
			if not self.sim:
				return

		if self.sim.stop:
			return

		self.raf_id = request_animation_frame(self.runsimulation)

		self.do_stepsimulation()

	def stopsimulation(self, ev):
		if self.raf_id is not None:
			cancel_animation_frame(self.raf_id)

	def do_stepsimulation(self):
		self.mem_clearhighlights()
		self.sim.step()
		self.update_ui()

	def update_ui(self):
		if not self.sim:
			return

		st = self.sim.state

		document["registers"].clear()
		document["registers"] <= "\n".join([
			f"     pc = ${     st.getpc():04X}    x1: ra = ${st.ureg(1):04X}    x5: a0 = ${st.ureg(5):04X}",
			f"                   x2: sp = ${st.ureg(2):04X}    x6: a1 = ${st.ureg(6):04X}",
			f"   mepc = ${   st.getmepc():04X}    x3: s0 = ${st.ureg(3):04X}    x7: a2 = ${st.ureg(7):04X}",
			f"mstatus = ${st.getmstatus():04X}    x4: s1 = ${st.ureg(4):04X}    x8: t0 = ${st.ureg(8):04X}",
		])


		document["callstack"].clear()

		stackframes = self.sim.backtrace()
		for i in range(len(stackframes)):
			addr, offset, sym = stackframes[i]
			symstr = f"{offset:3} + {sym}" if sym else "?"
			
			document["callstack"] <= f"  {i:3}   {addr:04X}  {symstr}\n"

	def reset_memory_pane(self):
		docelt = document["memory"]

		docelt.clear()
		self.memelts = []

		fc = lambda v: chr(v&0xff) if v >= 32 and v < 127 else "."

		try:
			self.memlo = int(document["memlo"].value,16)
		except ValueError:
			self.memlo = 0

		try:
			self.memhi = int(document["memhi"].value,16)
		except ValueError:
			self.memhi = 0x200

		if self.memhi < (self.memlo + 0x20):
			self.memhi = self.memlo + 0x20

		step = 8
		mask = (step*2)-1

		self.memlo &= 0xffff & ~mask
		self.memhi = (self.memhi + mask) & 0xffff & ~mask

		for i in range(self.memlo//2,self.memhi//2,step):
			addr = 2*i
			data = self.mem[i:i+step]
			datastr = " ".join([f"{v:04X}" for v in data])
			datachars = "".join([f"{fc(v&0xff)}{fc(v>>8)}" for v in data])
			document["memory"] <= f"{addr:04X}:  "

			for addr in range(2*i, 2*(i+step), 2):
				v = self.mem[addr//2]
				eltlo = html.SPAN(f"{v & 0xff:02X}")
				elthi = html.SPAN(f"{v >> 8:02X}")
				self.memelts.append(eltlo)
				self.memelts.append(elthi)
				docelt <= elthi
				docelt <= eltlo
				docelt <= " "

			docelt <= f" {datachars}\n"

		self.memhighlights = set()

	def memcallback(self, addr, value, readnotwrite):
		if addr < self.memlo or addr >= self.memhi:
			return

		elt = self.memelts[addr-self.memlo]
		self.memhighlights.add(elt)

		if readnotwrite:
			elt.style["backgroundColor"] = "#88ff88"
		else:
			elt.style["backgroundColor"] = "#ffcc88"
			elt.text = f"{value:02X}"

	def mem_clearhighlights(self):
		for elt in self.memhighlights:
			elt.style["backgroundColor"] = ""
		self.memhighlights = set()


interface = Interface()


document["sourcecode"].value = "\n".join([
	"# Enter source code here",
	"    sievebase = $0050",
	"    sievetop = $0150",
    "    results = $0050",
	"",
	"_start:",
	"    li   sp, $f000",
	"    li   a2, results",
	"",
	"    li   s0, sievebase",
	"    li   s1, sievetop",
	"",
	"    li   a0, -1",
	"    mv   a1, s1",
	"",
	"1:",
	"    sw   a0, -2(a1)",
	"    addi a1, a1, -2",
	"    bne  a1, s0, 1b",
	"",
	"    li   a0, 2",
	"",
	".sieveloop:",
	"    add  a1, a0, s0",
	"    beq  a1, s1, .finished",
	"",
	"    lb   t0, (a1)",
	"    bnez t0, .updatesieve",
	"",
	"    addi a0, a0, 1",
	"    j    .sieveloop",
	"",
	".updatesieve:",
	"    sw   a0, (a2)",
    "    addi a2, a2, 2",
	"    li   t0, 0",
	"1:",
	"    add  a1, a1, a0",
	"    bge  a1, s1, 1f",
	"    sb   t0, (a1)",
	"    j    1b",
	"1:",
	"    addi a0, a0, 1",
	"    j    .sieveloop",
	"",
	".finished:",
	"    nop",
	"    ebreak",
])


#	"# Enter source code here",
#	"_start:",
#	"	li	a0, 1230",
#	"	li	a1, 48",
#	"	call	gcd",
#	"	ebreak",
#	"",
#	"gcd:",
#	"	sub	a2, a0, a1",
#	"	bnez	a2, 1f",
#	"	ret",
#	"1:",
#	"	bltz	a2, 1f",
#	"	mv	a0, a2",
#	"	j	gcd",
#	"1:",
#	"	neg	a1, a2",
#	"	j	gcd",

