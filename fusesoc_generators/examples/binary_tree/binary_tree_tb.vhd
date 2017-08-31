library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library OSVVM;
use OSVVM.RandomPkg.all;

library vunit_lib;
use vunit_lib.check_pkg.all;
use vunit_lib.run_pkg.all;
use vunit_lib.queue_pkg.all;
use vunit_lib.logger_pkg.all;

entity binary_tree_tb is
  generic (
    runner_cfg : string
    );
end entity;

architecture arch of binary_tree_tb is
  constant WIDTH: positive := 3;
  constant N_INPUTS: positive := 7;
  constant META_WIDTH: positive := 4;
  constant OPERATION: string := "binary_minimum";
  constant PIPELINE: natural := 0;
  constant clk_period : integer := 8; -- ns

  signal clk: std_logic := '0';
  signal stimulus_clk: std_logic := '0';
  signal monitor_clk: std_logic := '0';
  signal reset: std_logic := '0';

  type i_t is record
    valid: std_logic;
    ready: std_logic;
    data: std_logic_vector(WIDTH*N_INPUTS-1 downto 0);
    meta: std_logic_vector(META_WIDTH-1 downto 0);
  end record;
  type o_t is record
    valid: std_logic;
    ready: std_logic;
    data: std_logic_vector(WIDTH-1 downto 0);
    meta: std_logic_vector(META_WIDTH-1 downto 0);
  end record;

  signal i: i_t;
  signal o: o_t;

  procedure monitor_i(i: i_t; queue: queue_t; meta_queue: queue_t) is
  begin
    if (i.valid and i.ready) = '1' then
      push(queue, i.data);
      push(meta_queue, i.meta);
    end if;
  end procedure;
  
  procedure monitor_o(o: o_t; queue: queue_t; meta_queue: queue_t) is
  begin
    if (o.valid and o.ready) = '1' then
      push(queue, o.data);
      push(meta_queue, o.meta);
    end if;
  end procedure;
  
  impure function check(i_queue: queue_t; o_queue: queue_t; i_meta_queue: queue_t; o_meta_queue: queue_t) return boolean is
    variable tested: boolean;
    variable i_data: std_logic_vector(WIDTH*N_INPUTS-1 downto 0);
    variable o_data: std_logic_vector(WIDTH-1 downto 0);
    variable piece: unsigned(WIDTH-1 downto 0);
    variable minimum_piece: unsigned(WIDTH-1 downto 0) := (others => '1');
    variable i_meta: std_logic_vector(META_WIDTH-1 downto 0);
  begin
    tested := false;
    if (length(i_queue) > 0) and (length(o_queue) > 0) then
      i_data := pop(i_queue);
      for ii in 0 to N_INPUTS-1 loop
        piece := unsigned(i_data((ii+1)*WIDTH-1 downto ii*WIDTH));
        if piece < minimum_piece then
          minimum_piece := piece;
        end if;
      end loop;
      o_data := pop(o_queue);
      check(unsigned(o_data) = minimum_piece, "o.data must be minimum in i.data");
      tested := true;
    end if;
    if (length(i_meta_queue) > 0) and (length(o_meta_queue) > 0) then
      i_meta := pop(i_meta_queue);
      check(i_meta = pop(o_meta_queue), "i_meta must pass unchanged to o_meta");
    end if;
    return tested;
  end function;

begin

  input_stimulus: process
    variable RV: RandomPType;
    variable random_bit: std_logic_vector(0 downto 0);
  begin
    RV.InitSeed(RV'instance_name);
    while true loop
      wait until rising_edge(stimulus_clk);
      random_bit := RV.RandSlv(1);
      i.valid <= random_bit(0);
      i.data <= RV.RandSlv(WIDTH*N_INPUTS);
      random_bit := RV.RandSlv(1);
      o.ready <= random_bit(0);
    end loop;
  end process;

  duv: entity work.binary_tree
    generic map (
      WIDTH => WIDTH,
      N_INPUTS => N_INPUTS,
      PIPELINE => PIPELINE,
      META_WIDTH => META_WIDTH,
      OPERATION => OPERATION
      )
    port map (
      clk => clk,
      reset => reset,
      i_valid => i.valid,
      i_ready => i.ready,
      i_data => i.data,
      i_meta => i.meta,
      o_valid => o.valid,
      o_ready => o.ready,
      o_data => o.data,
      o_meta => o.meta
      );

  main : process
    variable n_tested: integer := 0;
    variable i_queue: queue_t;
    variable o_queue: queue_t;
    variable i_meta_queue: queue_t;
    variable o_meta_queue: queue_t;
  begin
    test_runner_setup(runner, runner_cfg);
    i_queue := allocate;
    o_queue := allocate;
    i_meta_queue := allocate;
    o_meta_queue := allocate;
    while n_tested < 100 loop
      wait until rising_edge(monitor_clk);
      monitor_i(i, i_queue, i_meta_queue);
      monitor_o(o, o_queue, o_meta_queue);
      if check(i_queue, o_queue, i_meta_queue, o_meta_queue) then
        n_tested := n_tested + 1;
      end if;
    end loop;
    test_runner_cleanup(runner);
    wait;
  end process;
  test_runner_watchdog(runner, 10 us);

  clks: process
  begin
    while true loop
      wait for (1*clk_period/8) * 1 ns;
      stimulus_clk <= not stimulus_clk;
      wait for (2*clk_period/8) * 1 ns;
      clk <= not clk;
      wait for (1*clk_period/8) * 1 ns;
      monitor_clk <= not monitor_clk;
    end loop;
  end process;

end architecture;
