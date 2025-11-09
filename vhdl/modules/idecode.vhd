library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity idecode is
	port(
		ir		: IN	STD_LOGIC_VECTOR(15 downto 0);

		reg1	: OUT	STD_LOGIC_VECTOR(2 downto 0);
		reg2	: OUT	STD_LOGIC_VECTOR(2 downto 0);
		reg3	: OUT	STD_LOGIC_VECTOR(2 downto 0);

		mcaddr	: OUT	STD_LOGIC_VECTOR(7 downto 0);
		immtype	: OUT	STD_LOGIC_VECTOR(2 downto 0)
	);
end idecode;

architecture RTL of idecode is

	signal	rs1_eq_rs3 : STD_LOGIC;
	signal	rs1_lt_rs2 : STD_LOGIC;
	signal	rs1_eq_rs2 : STD_LOGIC;

	signal	xir : STD_LOGIC_VECTOR(18 downto 0);

begin

	reg1 <= ir(9 downto 7);
	reg2 <= ir(12 downto 10);
	reg3 <= ir(6 downto 4);

	rs1_eq_rs3 <= '1' when reg1=reg3 else '0';
	rs1_lt_rs2 <= '1' when reg1<reg2 else '0';
	rs1_eq_rs2 <= '1' when reg1=reg2 else '0';

	xir <= (rs1_eq_rs3 & rs1_lt_rs2 & rs1_eq_rs2 & ir);

	process(xir) is
	begin
		   if xir ?= "---------0-1--10001" then mcaddr <= "00000100"; -- jal
		elsif xir ?= "---------0-1--00001" then mcaddr <= "00001000"; -- j
		elsif xir ?= "1---1----------1011" then mcaddr <= "00001100"; -- jalr
		elsif xir ?= "1---1----------1010" then mcaddr <= "00010000"; -- jr
		elsif xir ?= "1--------------1000" then mcaddr <= "00010100"; -- beqz
		elsif xir ?= "1--------------1001" then mcaddr <= "00011010"; -- bnez
		elsif xir ?= "1---0----------1011" then mcaddr <= "00100000"; -- bltz
		elsif xir ?= "1---0----------1010" then mcaddr <= "00100110"; -- bgez
		elsif xir ?= "0--------------1000" then mcaddr <= "00101100"; -- beq
		elsif xir ?= "0--------------1001" then mcaddr <= "00110100"; -- bne
		elsif xir ?= "0---0----------1011" then mcaddr <= "00111111"; -- blt
		elsif xir ?= "0---0----------1010" then mcaddr <= "01001000"; -- bge
		elsif xir ?= "0---1----------1011" then mcaddr <= "01010001"; -- bltu
		elsif xir ?= "0---1----------1010" then mcaddr <= "01011010"; -- bgeu
		elsif xir ?= "---------------0100" then mcaddr <= "01100011"; -- lb
		elsif xir ?= "---------------0110" then mcaddr <= "01100111"; -- lbu
		elsif xir ?= "---------------0010" then mcaddr <= "01101010"; -- lw
		elsif xir ?= "---------------0101" then mcaddr <= "01101110"; -- sb
		elsif xir ?= "---------------0011" then mcaddr <= "01110001"; -- sw
		elsif xir ?= "---------101---0001" then mcaddr <= "01110101"; -- li
		elsif xir ?= "-----------0---0000" then mcaddr <= "01110111"; -- lui
		elsif xir ?= "-----------1---0000" then mcaddr <= "01111001"; -- auipc
		elsif xir ?= "-----------0---0001" then mcaddr <= "01111011"; -- addi8
		elsif xir ?= "-----0---------1100" then mcaddr <= "01111101"; -- addi
		elsif xir ?= "-----1---------1100" then mcaddr <= "01111111"; -- andi
		elsif xir ?= "-----0---------1101" then mcaddr <= "10000001"; -- ori
		elsif xir ?= "-----1---------1101" then mcaddr <= "10000011"; -- xori
		elsif xir ?= "---1-0---------1111" then mcaddr <= "10000101"; -- srli
		elsif xir ?= "---0-1---------1111" then mcaddr <= "10001001"; -- srai
		elsif xir ?= "---0-0---------1111" then mcaddr <= "10001101"; -- slli
		elsif xir ?= "-----0---------1110" then mcaddr <= "10010001"; -- slti
		elsif xir ?= "-----1---------1110" then mcaddr <= "10010100"; -- sltiu
		elsif xir ?= "-1-000---------0111" then mcaddr <= "10010111"; -- add
		elsif xir ?= "--0010---------0111" then mcaddr <= "10011011"; -- sub
		elsif xir ?= "-0-000---------0111" then mcaddr <= "10011111"; -- and
		elsif xir ?= "-1-001---------0111" then mcaddr <= "10100011"; -- or
		elsif xir ?= "-0-001---------0111" then mcaddr <= "10100111"; -- xor
		elsif xir ?= "--0110---------0111" then mcaddr <= "10101011"; -- slt
		elsif xir ?= "--0111---------0111" then mcaddr <= "10110000"; -- sltu
		elsif xir ?= "---101---------0111" then mcaddr <= "10110110"; -- srl
		elsif xir ?= "---100---------0111" then mcaddr <= "10111010"; -- sra
		elsif xir ?= "---011---------0111" then mcaddr <= "10111110"; -- sll
		elsif xir ?= "--1111---------0111" then mcaddr <= "11000010"; -- snez
		elsif xir ?= "--1110---------0111" then mcaddr <= "11000101"; -- sgtz
		elsif xir ?= "--1010---------0111" then mcaddr <= "11001000"; -- neg
		elsif xir ?= "---1-1---110---1111" then mcaddr <= "11001100"; -- mret
		elsif xir ?= "---1-1---000---1111" then mcaddr <= "11010000"; -- ecall
		elsif xir ?= "---1-1---101---1111" then mcaddr <= "11011000"; -- setmie
		elsif xir ?= "---1-1---100---1111" then mcaddr <= "11011011"; -- clrmie
		elsif xir ?= "---1-1---010---1111" then mcaddr <= "11011110"; -- rdmepc
		elsif xir ?= "---1-1---011---1111" then mcaddr <= "11100000"; -- wrmepc
		else mcaddr <= "11111111";
		end if;
	end process;

end architecture RTL;

