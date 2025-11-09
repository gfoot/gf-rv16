library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

library gfrv16;

entity tb_prgcnt is
	generic (runner_cfg : string);
end entity;

architecture tb of tb_prgcnt is

	signal reset : std_logic := '0';
	signal endc : std_logic := '0';
	signal ctl_end : std_logic := '0';
	signal ctl_pcr : std_logic := '0';
	signal ctl_pcw : std_logic := '0';
	signal ctl_high : std_logic := '0';
	signal ctl_regw_src : std_logic_vector(1 downto 0) := (others => '0');
	signal pcn : unsigned(15 downto 0);
	signal bus_b : std_logic_vector(7 downto 0);
	signal bus_c : std_logic_vector(7 downto 0);
	signal regw_val : std_logic_vector(7 downto 0);

begin
	main: process is

		procedure cycle is
		begin
			endc <= '0';
			wait for 1 ns;
			endc <= '1';
			wait for 1 ns;
		end cycle;

	begin
		test_runner_setup(runner, runner_cfg);

		-- Send a valid reset pulse to initialise the device under test
		reset <= '1';
		cycle;
		cycle;
		reset <= '0';
		wait for 1 ns;

		while test_suite loop

			if run("Test that PCN is zero after the reset") then
				check_equal(pcn, 0);

			elsif run("Test that a clock cycle without ctl_end asserted has no effect on PCN") then
				cycle;
				check_equal(pcn, 0);
				
			elsif run("Test that clock cycle with ctl_end causes PCN to increment by 2") then
				ctl_end <= '1';
				cycle;
				check_equal(pcn, 2);

			elsif run("Test that bus_b is not driven when ctl_pcr is not asserted") then
				-- Converting to a string feels really clunky but I couldn't find a better way
				check_equal(to_string(bus_b), "ZZZZZZZZ");

			elsif run("Test that when ctl_pcr is asserted bus_b is driven by PC initially zero") then
				-- This is asynchronous, so no need to cycle the clock, but we do need a wait.
				ctl_pcr <= '1';
				wait for 1 ns;
				check_equal(bus_b, 0);
				
			elsif run("Test that PC lags PCN by 2 as PCN advances 2 at a time") then
				ctl_pcr <= '1';
				ctl_end <= '1';
				cycle;
				check_equal(pcn, 2, result("for pcn"));
				check_equal(bus_b, 0, result("for bus_b"));
				cycle;
				check_equal(pcn, 4, result("for pcn"));
				check_equal(bus_b, 2, result("for bus_b"));
				cycle;
				check_equal(pcn, 6, result("for pcn"));
				check_equal(bus_b, 4, result("for bus_b"));

			elsif run("Test that PCN is written from bus_c when ctl_pcw is asserted") then
				ctl_pcw <= '1';
				bus_c <= x"DE";
				cycle;
				check_equal(pcn, 16#de#, result("PCN after low byte written"));
				ctl_high <= '1';
				bus_c <= x"BC";
				cycle;
				check_equal(pcn, 16#bcde#, result("PCN after both bytes written"));

			elsif run("Test ctl_regw_src controlling regw_val") then
				-- Preload PCN and PC with non-zero values
				ctl_pcw <= '1';
				bus_c <= x"DE";    -- PC low
				cycle;
				ctl_high <= '1';
				bus_c <= x"BC";    -- PC high
				cycle;
				ctl_end <= '1';
				cycle;
				ctl_end <= '0';

				bus_c <= x"76";    -- PCN high
				cycle;
				ctl_high <= '0';
				bus_c <= x"54";    -- PCN low
				cycle;

				bus_c <= x"4A";    -- ALU

				ctl_regw_src <= "00";
				wait for 1 ns;
				check_equal(regw_val, 0, result("ctl_regw_src:00 (zero)"));

				ctl_regw_src <= "01";
				wait for 1 ns;
				check_equal(regw_val, 16#4A#, result("ctl_regw_src:01 (alu)"));

				ctl_regw_src <= "10";
				ctl_high <= '0';
				wait for 1 ns;
				check_equal(regw_val, 16#DE#, result("ctl_regw_src:10 (pc), low"));
				ctl_high <= '1';
				wait for 1 ns;
				check_equal(regw_val, 16#BC#, result("ctl_regw_src:10 (pc), high"));

				ctl_regw_src <= "11";
				ctl_high <= '0';
				wait for 1 ns;
				check_equal(regw_val, 16#54#, result("ctl_regw_src:11 (pcn), low"));
				ctl_high <= '1';
				wait for 1 ns;
				check_equal(regw_val, 16#76#, result("ctl_regw_src:11 (pcn), high"));
				
				
			end if;

		end loop;
		
		test_runner_cleanup(runner);
		wait;
	end process;

	test_runner_watchdog(runner, 10 ms);

	dut : entity gfrv16.prgcnt
		port map (
			reset => reset,
			endc => endc,
			ctl_end => ctl_end,
			ctl_pcr => ctl_pcr,
			ctl_pcw => ctl_pcw,
			ctl_high => ctl_high,
			ctl_regw_src => ctl_regw_src,
			pcn => pcn,
			bus_b => bus_b,
			bus_c => bus_c,
			regw_val => regw_val
		);

end architecture;
