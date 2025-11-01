import sys

from browser import document, html, alert, window
from browser.timer import request_animation_frame, cancel_animation_frame, set_timeout, clear_timeout

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
		document["startbutton"].bind("click", self.startsimulation)
		document["stepbutton"].bind("click", self.stepsimulation)
		document["runbutton"].bind("click", self.runsimulation)

		self.sim = None
		self.assembled = None
		self.debuginfo = None

		self.raf_id = None
		self.timeout_id = None

		self.memelements = []
		self.instrelements = []
		self.breakpoints = set()

		self.stepmode = "source"
		document["stepmode"].bind("change", self.stepmodechanged)

		self.runspeed = int(document["runspeed"].value)
		document["runspeed"].bind("change", self.runspeedchanged)

		document["memlo"].bind("change", self.memrangechanged)
		document["memhi"].bind("change", self.memrangechanged)

	def stepmodechanged(self, ev):
		for option in ev.currentTarget:
			if option.selected:
				assert option.id.startswith("stepmode_")
				self.stepmode = option.id.replace("stepmode_", "")

	def runspeedchanged(self, ev):
		self.runspeed = int(ev.currentTarget.value)

	def assemble(self, ev):
		if self.sim:
			self.stopsimulation()

		self.sim = None
		self.assembled = None
		self.debuginfo = None

		document["outputwindow"].clear()
		document["machinecode"].clear()

		self.reset_memory_pane()

		try:
			sourceelement = document["sourcecode"]
			sourcelines = sourceelement.value.splitlines()

			assembler = assem.Assembler()
			self.assembled = assembler.assemble("test.s", sys.stdout, sourcelines)
			self.debuginfo = assembler.builddebuginfo()

		except Exception as e:
			document["outputwindow"] <= str(e)
			document["outputwindow"].scrollTop = document["outputwindow"].scrollHeight

		else:
			self.update_machinecode_pane()
			self.startsimulation(ev)

	def startsimulation(self, ev):
		if self.sim:
			self.stopsimulation()

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
		if not self.sim:
			self.startsimulation(ev)
			if not self.sim:
				return

		self.clear_memhighlights()

		self.do_stepsimulation(self.stepmode)

	def runsimulation(self, ev):
		if not self.sim:
			self.startsimulation(ev)
			if not self.sim:
				return

		if self.sim.stop:
			return

		self.clear_memhighlights()

		if self.runspeed >= 0:
			bp = False
			for i in range(1 << self.runspeed):
				self.do_stepsimulation("source")

				if self.sim.state.getpc() in self.breakpoints:
					bp = True
					break

			if not bp:
				self.raf_id = request_animation_frame(self.runsimulation)

		else:
			self.do_stepsimulation(self.stepmode)

			if not self.sim.state.getpc() in self.breakpoints:
				self.timeout_id = set_timeout(self.runsimulationslow, 20 << (-self.runspeed))

	def runsimulationslow(self):
		self.runsimulation(None)

	def stopsimulation(self):
		if self.raf_id is not None:
			cancel_animation_frame(self.raf_id)
			self.raf_id = None
		if self.timeout_id is not None:
			clear_timeout(self.timeout_id)
			self.timeout_id = None

	def do_stepsimulation(self, stepmode):
		self.stopsimulation()

		if stepmode == "source":
			originfo = self.debuginfo[self.sim.state.getpc()]
			while True:
				self.sim.step()
				info = self.debuginfo[self.sim.state.getpc()]
				if originfo is None or info is None or originfo.sourcelocation is None or info.sourcelocation is None:
					break
				if originfo.sourcelocation != info.sourcelocation:
					break
		elif stepmode == "mc":
			self.sim.step()
		elif stepmode == "cycle":
			self.sim.stepcycle()

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

		self.clear_instrhighlights()
		instrelement = self.instrelements[st.getpc()//2]
		if instrelement:
			instrelement.style["backgroundColor"] = "#ffff88"
			self.instrhighlights.add(instrelement)
			self.scroll_machinecode(st.getpc())

	def scroll_machinecode(self, addr):
		info = self.debuginfo[addr]
		if not info or not info.sourcelocation:
			return

		filename,linenumber = info.sourcelocation

		if filename != "test.s":
			return
		
		elt = document["machinecode"]
		targetscroll = elt.scrollHeight * (linenumber-1) / (self.num_mclines-1)
		if targetscroll < elt.scrollTop:
			elt.scrollTop = targetscroll - 8
		elif targetscroll - elt.height + 16 > elt.scrollTop:
			elt.scrollTop = targetscroll - elt.height + 16

	def memrangechanged(self, ev):
		self.reset_memory_pane()

	def reset_memory_pane(self):
		docelt = document["memory"]
		docelt.clear()

		if not self.sim:
			docelt <= "----------------------------------------------------------------"
			return

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

	def clear_memhighlights(self):
		for elt in self.memhighlights:
			elt.style["backgroundColor"] = ""
		self.memhighlights = set()

	def update_machinecode_pane(self):
		sourceelt = document["sourcecode"]
		mcelt = document["machinecode"]

		self.instrelements = [None]*32768
		
		oldbreakpoints = self.breakpoints
		self.breakpoints = set()

		sourcelines = sourceelt.value.splitlines()
		for i,line in enumerate(sourcelines):
			linenum = i+1

			text = ""

			addr,size = self.debuginfo.getaddrsforline("test.s", linenum)
			if addr is not None:
				text = f"{addr:04X}: "
				if size > 6:
					text += f"({size//2} words)"
				else:
					for i in range(size//2):
						text += f"{self.assembled[addr//2 + i]:04X} "

			text = f"{text:22}  {line}\n"

			checkbox = self.make_breakpoint_checkbox(addr)

			element = html.DIV(checkbox + text, Class="machinecodeline")

			if addr is not None:
				element.bind("mouseover", Interface.machinecodeline_showbpcheckbox)
				element.bind("mouseout", Interface.machinecodeline_hidebpcheckbox)
				if addr in oldbreakpoints:
					self.breakpoints.add(addr)
					checkbox.checked = True
					checkbox.style["visibility"] = "visible"

			mcelt <= element

			if addr is not None:
				for i in range(size//2):
					self.instrelements[addr//2 + i] = element

		self.instrhighlights = set()
		self.num_mclines = len(sourcelines)

	def make_breakpoint_checkbox(self, addr):
		element = html.INPUT(type="checkbox", style="visibility:hidden")

		if addr is not None:
			element.attrs["breakpointaddr"] = addr
			element.bind("change", self.breakpoint_checkbox_changed)

		return element

	def breakpoint_checkbox_changed(self, ev):
		elt = ev.currentTarget
		addr = int(elt.attrs["breakpointaddr"])
		if elt.checked:
			self.breakpoints.add(addr)
			elt.style["visibility"] = "visible"
		else:
			self.breakpoints.remove(addr)

	def machinecodeline_showbpcheckbox(ev):
		elt = ev.currentTarget.select_one("input")
		elt.style["visibility"] = "visible"

	def machinecodeline_hidebpcheckbox(ev):
		elt = ev.currentTarget.select_one("input")
		if not elt.checked:
			elt.style["visibility"] = "hidden"

	def clear_instrhighlights(self):
		for elt in self.instrhighlights:
			elt.style["backgroundColor"] = ""
		self.instrhighlights = set()

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

