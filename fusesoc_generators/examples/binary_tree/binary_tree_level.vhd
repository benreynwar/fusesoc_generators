library ieee;
use ieee.std_logiC_1164.all;

entity binary_tree_level_{{level}} is
  generic (
    OPERATION: string;
    N_INPUTS: positive;
    PIPELINE: natural;
    WIDTH: positive;
    META_WIDTH: natural
    );
  port (
    clk: in std_logic;
    reset: in std_logic;
    i_valid: in std_logic;
    i_ready: out std_logic;
    i_data: in std_logic_vector(WIDTH*N_INPUTS-1 downto 0);
    i_meta: in std_logic_vector(META_WIDTH-1 downto 0);
    o_valid: out std_logic;
    o_ready: in std_logic;
    o_data: out std_logic_vector(WIDTH-1 downto 0);
    o_meta: out std_logic_vector(META_WIDTH-1 downto 0)
    );
end entity;

architecture arch of binary_tree_level_{{level}} is
  constant N_PAIRS: natural := N_INPUTS/2;
  constant HAS_SINGLE: natural := N_INPUTS - N_PAIRS * 2;
  signal ic_valid: std_logic;
  signal ic_ready: std_logic;
  signal i_reduceddata: std_logic_vector(WIDTH*(N_PAIRS+HAS_SINGLE)-1 downto 0);
  signal a_valid: std_logic;
  signal a_ready: std_logic;
  signal a_data: std_logic_vector(WIDTH*(N_PAIRS+HAS_SINGLE)-1 downto 0);
  signal a_meta: std_logic_vector(META_WIDTH-1 downto 0);
begin

  ic_valid <= i_valid;
  i_ready <= ic_ready;

  loop_pairs: for pair_index in 0 to N_PAIRS-1 generate
    op: entity work.binary_tree_operation
      generic map (
        OPERATION => OPERATION,
        WIDTH => WIDTH
        )
      port map (
        i_data => i_data(WIDTH*2*(pair_index+1)-1 downto WIDTH*2*pair_index),
        o_data => i_reduceddata(WIDTH*(pair_index+1)-1 downto WIDTH*pair_index)
        );
  end generate;
  odd_n_inputs: if HAS_SINGLE = 1 generate
    i_reduceddata(WIDTH*(N_PAIRS+1)-1 downto WIDTH*N_PAIRS) <=
      i_data(WIDTH*N_INPUTS-1 downto WIDTH*(N_INPUTS-1));
  end generate;

  has_buffer: if (PIPELINE mod 2) = 1 generate
    process(clk)
    begin
      if rising_edge(clk) then
        if reset = '1' then
          a_valid <= '0';
        elsif (ic_valid = '1') and (ic_ready = '1') then
          a_data <= i_reduceddata;
          a_meta <= a_meta;
        elsif a_ready = '1' then
          a_valid <= '0';
        end if;
      end if;
    end process;
    ic_ready <= a_ready or (not a_valid);
  end generate;

  no_buffer: if PIPELINE mod 2 = 0 generate
    a_valid <= ic_valid;
    ic_ready <= a_ready;
    a_meta <= i_meta;
    a_data <= i_reduceddata;
  end generate;

  {% if not last_level %}
  another_level: if N_PAIRS > 0 generate
  next_level: entity work.binary_tree_level_{{level+1}} 
    generic map (
      OPERATION => OPERATION,
      N_INPUTS => N_PAIRS + HAS_SINGLE,
      PIPELINE => PIPELINE/2,
      WIDTH => WIDTH,
      META_WIDTH => META_WIDTH
    )
    port map (
      clk => clk,
      reset => reset,
      i_valid => a_valid,
      i_ready => a_ready,
      i_data => a_data,
      i_meta => a_meta,
      o_valid => o_valid,
      o_ready => o_ready,
      o_data => o_data,
      o_meta => o_meta
      );
  end generate;
  {% endif %}
  
  not_another_level: if N_PAIRS = 0 generate
    o_valid <= a_valid;
    a_ready <= o_ready;
    o_data <= a_data;
    o_meta <= a_meta;
  end generate;

end architecture;
