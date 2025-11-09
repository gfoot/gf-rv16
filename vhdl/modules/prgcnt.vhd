library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

ENTITY prgcnt IS
	PORT(
		reset		: IN	STD_LOGIC;

		endc		: IN	STD_LOGIC;

		ctl_end		: IN	STD_LOGIC;
		ctl_pcr		: IN	STD_LOGIC;
		ctl_pcw		: IN	STD_LOGIC;
		ctl_high	: IN	STD_LOGIC;
		ctl_regw_src: IN	STD_LOGIC_VECTOR(1 downto 0);

		pcn			: OUT	UNSIGNED(15 downto 0);

		bus_b		: OUT	STD_LOGIC_VECTOR(7 downto 0);
		bus_c		: IN	STD_LOGIC_VECTOR(7 downto 0);

		regw_val	: OUT	STD_LOGIC_VECTOR(7 downto 0)
	);
END prgcnt;

ARCHITECTURE RTL OF prgcnt IS

	SIGNAL	pc_h	: STD_LOGIC_VECTOR(7 downto 0);
	SIGNAL	pc_l	: STD_LOGIC_VECTOR(7 downto 0);

	SIGNAL	pc_lh	: STD_LOGIC_VECTOR(7 downto 0);
	SIGNAL	pcn_lh	: STD_LOGIC_VECTOR(7 downto 0);

BEGIN

	PROCESS(endc)
	BEGIN
		if (rising_edge(endc)) then
			if (reset = '1') then
				pcn <= x"0000";
				pc_l <= x"00";
				pc_h <= x"00";
			elsif (ctl_end = '1') then
				pcn <= pcn + x"0002";
				pc_l <= std_logic_vector(pcn(7 downto 0));
				pc_h <= std_logic_vector(pcn(15 downto 8));
			elsif (ctl_pcw = '1' and ctl_high = '1') then
				pcn <= unsigned(bus_c) & pcn(7 downto 0);
			elsif (ctl_pcw = '1') then
				pcn <= pcn(15 downto 8) & unsigned(bus_c);
			end if;
		end if;
	END PROCESS;

	pc_lh <= pc_h when ctl_high='1' else pc_l;
	pcn_lh <= std_logic_vector(pcn(15 downto 8)) when ctl_high='1' else std_logic_vector(pcn(7 downto 0));

	bus_b <= pc_lh when ctl_pcr='1' else (others => 'Z');

	regw_val <= x"00" when ctl_regw_src="00" else bus_c when ctl_regw_src="01" else pc_lh when ctl_regw_src="10" else pcn_lh;

END ARCHITECTURE RTL;

