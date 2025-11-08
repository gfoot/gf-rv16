library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

ENTITY clock IS
	PORT(
		clk		: IN	STD_LOGIC;
		phi1	: OUT	STD_LOGIC := '0';
		phi2	: OUT	STD_LOGIC := '1';
		endc	: OUT	STD_LOGIC := '0'
	);
END clock;

ARCHITECTURE RTL OF clock IS

BEGIN

	phi1 <= not clk and not phi2 after 1 ns;
	endc <= not clk after 1 ns;
	phi2 <= not endc after 1 ns;

END ARCHITECTURE RTL;

