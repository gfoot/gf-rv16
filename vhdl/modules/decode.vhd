library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

ENTITY decode IS
	PORT(
		reset	: IN	STD_LOGIC;

		phi1	: IN	STD_LOGIC;
		phi2	: IN	STD_LOGIC;
		endc	: IN	STD_LOGIC;

		ctl_end	: OUT	STD_LOGIC;
		ctl_ifl	: OUT	STD_LOGIC;
		ctl_ifh	: OUT	STD_LOGIC
	);
END decode;

ARCHITECTURE RTL OF decode IS

	SIGNAL	mcaddr	: UNSIGNED(7 downto 0);

BEGIN

	PROCESS(phi1)
	BEGIN
		if (rising_edge(phi1)) then
			if ((reset = '1') or (ctl_end = '1')) then
				mcaddr <= x"00";
			else
				mcaddr <= mcaddr + x"01";
			end if;
		end if;
	END PROCESS;

	PROCESS(mcaddr)
	BEGIN
		ctl_end <= '0';
		if (mcaddr = x"03") then
			ctl_end <= '1';
		end if;

		ctl_ifl <= '0';
		if (mcaddr = x"02") then
			ctl_ifl <= '1';
		end if;

		ctl_ifh <= '0';
		if (mcaddr = x"03") then
			ctl_ifh <= '1';
		end if;
	END PROCESS;

END ARCHITECTURE RTL;

