library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

ENTITY ifetch IS
	PORT(
		reset	: IN	STD_LOGIC;

		phi1	: IN	STD_LOGIC;
		phi2	: IN	STD_LOGIC;
		endc	: IN	STD_LOGIC;

		ctl_ifl	: IN	STD_LOGIC;
		ctl_ifh	: IN	STD_LOGIC;

		pcn		: IN	UNSIGNED(15 downto 0);

		ir		: OUT	UNSIGNED(15 downto 0)
	);
END ifetch;

ARCHITECTURE RTL OF ifetch IS

BEGIN

	PROCESS(endc)
	BEGIN
		if (rising_edge(endc)) then
			if (reset = '1') then
				ir <= x"0000";
			else
				if (ctl_ifl = '1') then
					ir(7 downto 0) <= pcn(7 downto 0);
				end if;
				if (ctl_ifh = '1') then
					ir(15 downto 8) <= pcn(7 downto 0);
				end if;
			end if;
		end if;
	END PROCESS;

END ARCHITECTURE RTL;

