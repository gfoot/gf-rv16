library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

ENTITY prgcnt IS
	PORT(
		reset	: IN	STD_LOGIC;

		endc	: IN	STD_LOGIC;

		ctl_end	: IN	STD_LOGIC;
		ctl_pcr	: IN	STD_LOGIC;
		ctl_pcw	: IN	STD_LOGIC;
		ctl_high	: IN	STD_LOGIC;

		pcn		: OUT	UNSIGNED(15 downto 0);

		bus_b	: OUT	STD_LOGIC_VECTOR(7 downto 0);
		bus_c	: OUT	STD_LOGIC_VECTOR(7 downto 0)
	);
END prgcnt;

ARCHITECTURE RTL OF prgcnt IS

	SIGNAL	pc		: UNSIGNED(15 downto 0);

BEGIN

	PROCESS(endc)
	BEGIN
		if (rising_edge(endc)) then
			if (reset = '1') then
				pcn <= x"0000";
			elsif (ctl_end = '1') then
				pcn <= pcn + x"0002";
			elsif (ctl_pcw = '1' and ctl_high = '1') then
				pcn <= unsigned(bus_c) & pcn(7 downto 0);
			elsif (ctl_pcw = '1') then
				pcn <= pcn(15 downto 8) & unsigned(bus_c);
			end if;
			pc <= pcn;
		end if;
	END PROCESS;

	bus_b <= std_logic_vector(pc(15 downto 8)) when ctl_pcr='1' and ctl_high='1' else std_logic_vector(pc(7 downto 0)) when ctl_pcr='1' else (others => 'Z');

END ARCHITECTURE RTL;

