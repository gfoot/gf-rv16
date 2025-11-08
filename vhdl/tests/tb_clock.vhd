library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

library gfrv16;

entity tb_clock is
	generic (runner_cfg : string);
end entity;

architecture tb of tb_clock is

	signal clk : std_logic := '0';
	signal phi1 : std_logic;
	signal phi2 : std_logic;
	signal endc : std_logic;

begin
	main: process
	begin
		test_runner_setup(runner, runner_cfg);

		-- Let the clock pulse a few times before running a test,
		-- so that the various signals are all valid
		wait for 20 ns;

		check_not_unknown(phi1);
		check_not_unknown(phi2);
		check_not_unknown(endc);

		while test_suite loop

			if run("Test that PHI2 is low whenever PHI1 changes") then
				wait until rising_edge(phi1);
				check_equal(phi2, '0');
				wait until falling_edge(phi1);
				check_equal(phi2, '0');

			elsif run("Test that PHI1 is low whenever PHI2 changes") then
				wait until rising_edge(phi2);
				check_equal(phi1, '0');
				wait until falling_edge(phi2);
				check_equal(phi1, '0');

			elsif run("Test that PHI2 is high when ENDC rises") then
				wait until rising_edge(endc);
				check_equal(phi2, '1');

			end if;

		end loop;
		
		test_runner_cleanup(runner);
		wait;
	end process;

	test_runner_watchdog(runner, 10 ms);

	clk <= not clk after 5 ns;

	dut : entity gfrv16.clock
		port map (
			clk => clk,
			phi1 => phi1,
			phi2 => phi2,
			endc => endc
		);

end architecture;
