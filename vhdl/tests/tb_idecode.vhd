library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

library gfrv16;

entity tb_idecode is
	generic (runner_cfg : string);
end entity;

architecture tb of tb_idecode is

	signal ir : std_logic_vector(15 downto 0) := (Others => '0');

	signal reg1 : std_logic_vector(2 downto 0);
	signal reg2 : std_logic_vector(2 downto 0);
	signal reg3 : std_logic_vector(2 downto 0);

	signal mcaddr : std_logic_vector(7 downto 0);
	signal immtype : std_logic_vector(2 downto 0);

begin
	main: process is

	begin
		test_runner_setup(runner, runner_cfg);

		while test_suite loop

			if run("Test reg1") then
				for reg in 0 to 7 loop
					ir <= "------" & std_logic_vector(to_unsigned(reg,3)) & "-------";
					wait for 1 ns;
					check_equal(reg1, reg);
				end loop;

			elsif run("Test reg2") then
				for reg in 0 to 7 loop
					ir <= "---" & std_logic_vector(to_unsigned(reg,3)) & "----------";
					wait for 1 ns;
					check_equal(reg2, reg);
				end loop;

			elsif run("Test reg3") then
				for reg in 0 to 7 loop
					ir <= "---------" & std_logic_vector(to_unsigned(reg,3)) & "----";
					wait for 1 ns;
					check_equal(reg3, reg);
				end loop;

			elsif run("Test JAL") then
				ir <= "0000000010010001";
				wait for 1 ns;
				check_equal(mcaddr, 16#04#);

			elsif run("Test ADD") then
				ir <= "000" & "010" & "001" & "111" & "0111";
				wait for 1 ns;
				check_equal(mcaddr, 16#97#);

			elsif run("Test AND") then
				ir <= "000" & "001" & "010" & "111" & "0111";
				wait for 1 ns;
				check_equal(mcaddr, 16#9f#);

			elsif run("Test OR") then
				ir <= "001" & "010" & "001" & "111" & "0111";
				wait for 1 ns;
				check_equal(mcaddr, 16#a3#);

			elsif run("Test XOR") then
				ir <= "001" & "001" & "010" & "111" & "0111";
				wait for 1 ns;
				check_equal(mcaddr, 16#a7#);

			elsif run("Test SUB") then
				ir <= "010" & "010" & "001" & "111" & "0111";
				wait for 1 ns;
				check_equal(mcaddr, 16#9b#);

			elsif run("Test NEG") then
				ir <= "010" & "001" & "001" & "111" & "0111";
				wait for 1 ns;
				check_equal(mcaddr, 16#c8#);

			elsif run("Test BEQ") then
				ir <= "000000" & "001" & "111" & "1000";
				wait for 1 ns;
				check_equal(mcaddr, 16#2c#);

			elsif run("Test BEQZ") then
				ir <= "000000" & "001" & "001" & "1000";
				wait for 1 ns;
				check_equal(mcaddr, 16#14#);

			end if;

		end loop;
		
		test_runner_cleanup(runner);
		wait;
	end process;

	test_runner_watchdog(runner, 10 ms);

	dut : entity gfrv16.idecode
		port map (
			ir => ir,
			reg1 => reg1,
			reg2 => reg2,
			reg3 => reg3,
			mcaddr => mcaddr,
			immtype => immtype
		);

end architecture;
