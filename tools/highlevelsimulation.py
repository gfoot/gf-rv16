
class HighLevelSimulation:

	class InstructionDispatcher:

		def add_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) + st.sreg(rs2))
		def sub_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) - st.sreg(rs2))
		def and_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) & st.sreg(rs2))
		def or_rrr  (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) | st.sreg(rs2))
		def xor_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) ^ st.sreg(rs2))
		def sll_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) << st.sreg(rs2))
		def srl_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) >> st.sreg(rs2))
		def sra_rrr (st, rd, rs1, rs2): st.setreg(rd, st.ureg(rs1) >> st.sreg(rs2))
		def slt_rrr (st, rd, rs1, rs2): st.setreg(rd, st.sreg(rs1) < st.sreg(rs2))
		def sltu_rrr(st, rd, rs1, rs2): st.setreg(rd, st.ureg(rs1) < st.ureg(rs2))

		def addi_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) + imm)
		def andi_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) & imm)
		def ori_rri  (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) | imm)
		def xori_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) ^ imm)
		def slli_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) << imm)
		def srli_rri (st, rd, rs1, imm): st.setreg(rd, st.ureg(rs1) >> imm)
		def srai_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) >> imm)
		def slti_rri (st, rd, rs1, imm): st.setreg(rd, st.sreg(rs1) < imm)
		def sltiu_rri(st, rd, rs1, imm): st.setreg(rd, st.ureg(rs1) < imm)

		def beq_rri (st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) == st.sreg(rs2))
		def bne_rri (st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) != st.sreg(rs2))
		def blt_rri (st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) <  st.sreg(rs2))
		def bltu_rri(st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.ureg(rs1) <  st.ureg(rs2))
		def bge_rri (st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) >= st.sreg(rs2))
		def bgeu_rri(st, rs1, rs2, imm): st.setpc(st.getpc() + imm - 2, st.ureg(rs1) >= st.ureg(rs2))

		def lui_ri  (st, rd, imm): st.unimp() if imm == 0 else st.setreg(rd, imm)
		def auipc_ri(st, rd, imm): st.setreg(rd, imm + st.getpc())

		def j_i     (st,          imm):                                                     st.setpc(st.getpc() + imm - 2)
		def jal_ri  (st, rd,      imm):                     st.setreg(rd, st.getpc() + 2) ; st.setpc(st.getpc() + imm - 2)
		def jalr_rri(st, rd, rs1, imm): dest=st.sreg(rs1) ; st.setreg(rd, st.getpc() + 2) ; st.setpc(dest       + imm - 2)
		def jr_ri   (st,     rs1, imm): dest=st.sreg(rs1) ;                                 st.setpc(dest       + imm - 2)

		def lb_ror (st,  rd, imm, rs1): st.setreg(rd, st.memreadb(imm + st.sreg(rs1)))
		def lbu_ror(st,  rd, imm, rs1): st.setreg(rd, st.memreadb(imm + st.sreg(rs1)) & 0xff)
		def lw_ror (st,  rd, imm, rs1): st.setreg(rd, st.memreadw(imm + st.sreg(rs1)))
		def sb_ror (st, rs1, imm, rs2): st.memwriteb(imm + st.sreg(rs2), st.sreg(rs1))
		def sw_ror (st, rs1, imm, rs2): st.memwritew(imm + st.sreg(rs2), st.sreg(rs1))

		def ecall_(st): st.ecall()

		# Special cases for certain argument values
		def li_ri(st, rd, imm): st.setreg(rd, imm)
		def beqz_ri(st, rs1, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) == 0)
		def bnez_ri(st, rs1, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) != 0)
		def bltz_ri(st, rs1, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) <  0)
		def bgez_ri(st, rs1, imm): st.setpc(st.getpc() + imm - 2, st.sreg(rs1) >= 0)


		def dispatch(self, st, instr, argtypes, args):
			handler = getattr(self.__class__, instr+"_"+argtypes, None)
			if not handler:
				return False
			handler(st, *args)
			return True


	class State:

		def __init__(self, env, cycletrace):
			self.env = env

			self.regs = [0] * 9
			self.pc = 0

		def setreg(self, num, value):
			assert num > 0 and num < len(self.regs)
			self.regs[num] = value & 0xffff

		def sreg(self, num):
			v = self.regs[num]
			return v if v < 0x8000 else v-0x10000

		def ureg(self, num):
			return self.regs[num]

		def getpc(self):
			return self.pc

		def setpc(self, value, cond=True):
			if cond:
				self.pc = value

		def memreadw(self, addr): return self.env.memreadw(addr)
		def memreadb(self, addr): return self.env.memreadb(addr)
		def memwritew(self, addr, value): self.env.memwritew(addr, value)
		def memwriteb(self, addr, value): self.env.memwriteb(addr, value)
		def unimp(self): self.env.unimp()
		def ecall(self): self.env.ecall()


