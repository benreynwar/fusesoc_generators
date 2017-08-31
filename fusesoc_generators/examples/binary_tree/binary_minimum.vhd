library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity binary_minimum is
  generic (
    WIDTH: positive
    );
  port (
    i_data: in std_logic_vector(WIDTH*2-1 downto 0);
    o_data: out std_logic_vector(WIDTH-1 downto 0)
    );
end entity;

architecture arch of binary_minimum is
begin

  o_data <= i_data(WIDTH-1 downto 0)
            when unsigned(i_data(WIDTH-1 downto 0)) < unsigned(i_data(2*WIDTH-1 downto WIDTH)) else
            i_data(2*WIDTH-1 downto WIDTH);
   
end architecture;
