library ieee;
use ieee.std_logiC_1164.all;

entity binary_tree is
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

architecture arch of binary_tree is
begin

  match: if (false{% for operation, n_inputs in operation_and_n_inputs %}
             or ((OPERATION="{{operation}}") and (N_INPUTS={{n_inputs}})){% endfor %}) generate
  tree: entity work.binary_tree_level_0
    generic map (
      OPERATION => OPERATION,
      N_INPUTS => N_INPUTS,
      PIPELINE => PIPELINE,
      WIDTH => WIDTH,
      META_WIDTH => META_WIDTH
      )
    port map (
      clk => clk,
      reset => reset,
      i_valid => i_valid,
      i_ready => i_ready,
      i_data => i_data,
      i_meta => i_meta,
      o_valid => o_valid,
      o_ready => o_ready,
      o_data => o_data,
      o_meta => o_meta
      );
  end generate;

  nomatch: if not (false{% for operation, n_inputs in operation_and_n_inputs %}
                   or ((OPERATION="{{operation}}") and (N_INPUTS={{n_inputs}})){% endfor %}) generate
    assert false report "Generator name=binary_tree operation=" & OPERATION & " n_inputs=" & integer'image(N_INPUTS);
  end generate;

end architecture;
