library ieee;
use ieee.std_logic_1164.all;


entity binary_tree_operation is
  generic (
    OPERATION: string;
    WIDTH: positive
    );
  port (
    i_data: in std_logic_vector(WIDTH*2-1 downto 0);
    o_data: out std_logic_vector(WIDTH-1 downto 0)
    );
end entity;

architecture arch of binary_tree_operation is
begin
  {% for operation in operations %}op_{{operation}}: if OPERATION = "{{operation}}" generate
    op_{{operation}}_inst: entity work.{{operation}}
      generic map (
        WIDTH => WIDTH
      )
      port map (
        i_data => i_data,
        o_data => o_data
        );
    end generate;
  {% endfor %}
   
end architecture;
