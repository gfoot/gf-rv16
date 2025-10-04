# Experimenting with impacts of different immediate widths in various instructions
#
# The table lists the instructions along with the widths of any immediate constants
#
# The program then calculates the total number of bit patterns used up by the 
# instruction, and shows the total
#
# In this way you can check at the ballpark level that the instructions can fit within
# the target instruction width, and see how much room to manoeuvre there is


instrs = [
	( (8,3), "lui rd, imm8hz" ),
	( (8,3), "auipc rd, imm8hz" ),

	( (9,), "j imm9e" ),
	( (9,), "jal ra, imm9e" ),

	( (6,3,3), "lw rd, imm6ez(rs1)" ),
	( (6,3,3), "lb rd, imm6z(rs1)" ),
	( (6,3,3), "lbu rd, imm6z(rs1)" ),

	( (6,3,3), "sb rs3, imm6z(rs1)" ),
	( (6,3,3), "sw rs3, imm6ez(rs1)" ),

	( (8,3), "addi rd, rd, imm8" ),
	( (5,3,3), "addi rd, rs1, imm5" ),
	( (5,3,3), "andi rd, rs1, imm5" ),
	( (5,3,3), "ori rd, rs1, imm5" ),
	( (5,3,3), "xori rd, rs1, imm5" ),
	( (5,3,3), "slti rd, rs1, imm5z" ),
	( (5,3,3), "sltiu rd, rs1, imm5u" ),

	( (6,3,3), "beq rs1, rs3, imm6ez" ),
	( (6,3,3), "bne rs1, rs3, imm6ez" ),
	( (5,3,3), "blt rs1, rs3, imm5ez" ),
	( (5,3,3), "bge rs1, rs3, imm5ez" ),
	( (5,3,3), "bltu rs1, rs3, imm5ez" ),
	( (5,3,3), "bgeu rs1, rs3, imm5ez" ),

	( (5,3), "jalr ra, imm5ez(rs1)" ),
	( (5,3), "jr imm5ez(rs1)" ),

	( (4,3,3), "slli rd, rs1, imm4zu" ),
	( (4,3,3), "srli rd, rs1, imm4u" ),
	( (4,3,3), "srai rd, rs1, imm4zu" ),
	
	( (3,3,3), "add/and rd, rs1, rs2" ),
	( (3,3,3), "or/xor rd, rs1, rs2" ),
	( (3,3,3), "sll rd, rs1, rs2" ),
	( (3,3,3), "srl rd, rs1, rs2" ),
	( (3,3,3), "sra rd, rs1, rs2" ),
	( (3,3,3), "slt rd, rs1z, rs2" ),
	( (3,3,3), "sltu rd, rs1z, rs2" ),
	( (3,3,3), "sub rd, rs1z, rs2" ),
]

footprints = []
for counts, ins in instrs:
	footprints.append((2**sum(counts), counts, ins))

for footprint,counts,ins in sorted(footprints):
	print(f"{footprint:>6}  {'%s'%(counts,):<10}  {ins}")

print(sum([footprint for footprint,counts,ins in footprints]))



# For comparison, a sample of instruction frequencies in real world code:
#
#     $ objdump -d -Mno-aliases /bin/bash | awk '/[a-f0-9]+:/ {print $3}' | sort | uniq -c | sort -rnk1 | head -20
#     17902 c.mv
#     17707 jal
#     15808 c.ldsp
#     13567 c.li
#     12219 c.sdsp
#     10774 auipc
#     10584 addi
#     9357 ld
#     7438 c.j
#     7055 beq
#     5522 c.beqz
#     5458 c.ld
#     4339 c.lw
#     4299 bne
#     3641 lw
#     3567 lbu
#     3535 c.addi
#     3212 c.bnez
#     2728 sw                                                                                                                 
#     2618 c.jr

# Combining some together:
#
#     17902 c.mv
#     17707 jal
#     15808 c.ldsp
#     14815 ld + c.ld
#     14119 addi + c.addi
#     13567 c.li
#     12577 beq + c.beqz
#     12219 c.sdsp
#     10774 auipc
#     7511 bne + c.bnez
#     7438 c.j
#     4339 c.lw
#     3641 lw
#     3567 lbu
#     2728 sw                                                                                                                 
#     2618 c.jr

# Insights:
#
#  *  jal is really common - PC-relative function call, outside range of c.jal (12 bits, 11:1, +/-2K I guess)
#           - or maybe the C compiler just can't use c.jal due to not knowing final code location until link time
#  *  simply moving between registers is common too - maybe arguments, or s vs t?
#  *  at least half of memory loads are from the stack; w and b loads are uncommon; signed byte even more uncommon
#  *  addi (12 bit) much more common than c.addi (6 bit)
#           - but probably most of them were after auipc
#           - so most add operands in practice fit in 6 bits
#  *  beq/bne are common, slightly more often comparing against other registers rather than zero

