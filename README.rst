fusesoc_generators
==================

fusesoc_generators extends fusesoc to provide support for generating
files using python functions.
It is currently limited to VHDL source files.

A new kind of section is added to the core file in the form

.. code:: text

    [generator]
    module = somepythonpackage.somepythonmodule
    function = somepythonfunction
    type = python

This specifys a python function to be called that will return a list
of filenames, and include directories that the core depends upon.

The function takes the following arguments:

directory
  The directory where generated files should be placed.
generics
  A list of dictionaries of the generic parameters of the module.
top_params
  A dictionary of top level parameters for the entire design.

Use Cases
---------
1) It's fairly common to define a VHDL package containing constants
   to be used throughout the design.  It's convenient to be able to
   easily generate this file from a python dictionary.

.. code:: vhdl

    package mydesign_constants is
      constant BUS_WIDTH: {bus_width};
      constant N_BLOCKS: {n_blocks};
    end package;

.. code:: python

    def generate(directory, generics, top_params):
        '''
        Generate the mydesign_constants package using values from the
        top_params dictionary.
        '''
        template_filename = 'mydesign_constants.vhd'
        with open(template_filename, 'r') as template_file:
            template_contents = template_file.read()
        package_contents = template_contents.format(**top_params)
        package_filename = os.path.join(directory, 'mydesign_constants.vhd')
        with open(package_filename, 'w') as package_file:
            package_file.write(package_contents)
        filenames = [package_filename]
        incdirs = []
        return filenames, incdirs

2) If you're making an ASIC design, then there's a good chance you'll
   be using compiled memories.


.. code:: python

    def generate(directory, generics, top_params):
        '''
        Generate compiled memories and wrappers that gather all compiled
        memories into a single interface that other VHDL entities can use.
        '''
        generated_filenames = []
        width_depth_pairs = []
        for generic_params in generics:
          width = generic_params['width']
          depth = generic_params['depth']
          generated_filenames.append(
              generate_a_compiled_memory(width=width, depth=depth))
          width_depth_pairs.append((width, depth))
        generated_filenames.append(generate_memory_wrapper(width_depth_pairs))
        incdirs = []
        return generated_filenames, incdirs

3)  Sometimes there just no easy way to easily create the parameterized design
    required without generation.  Binary trees can be difficult, and tool
    support for recursive instantiation is poor so it is often easiest simply
    to generate the VHDL source files.

Super Elaboration
-----------------
To be able to detect which generic parameters a given module uses,
fusesoc_generators runs all the files through ghdl and requires that
generators that need to know their generics must add logging into their
source that outputs the generics used.  In this way the generics can be
extracted by parsing the output of ghdl.

Below is an example ``jinja2`` template of a VHDL file that collects RAM
definitions for various RAM instantiations and creates a single RAM entity
with generic ``width`` and ``depth`` properties that the rest of the design
can use.

When ``fusesoc_generators`` processes the design, the generate function for
the RAM will initially be passed an empty list of ``generics`` so that this
template will be formatted with an empty list of ``width_depth_pairs``.
The resulting VHDL will display an assertion for each time it is instantiated
in the design listing the required ``width`` and ``depth``.  The ghdl logs
are parsed and so the parameters of all the required RAM are determined.

The generate function is now called with a full list of ``generics``.
Compiled memories can be generated, and when the ``jinja2`` template is
formatted it will contain instantiations of the compiled memories.

.. code:: vhdl

    entity RAM is
      generic (
        WIDTH: natural;
        DEPTH: positive
        );
      port (
        clk: in std_logic;
        w_valid: in std_logic;
        w_data: in std_logic_vector(WIDTH-1 downto 0);
        w_address: in std_logic_vector(logceil(DEPTH)-1 downto 0);
        ir_valid: in std_logic;
        ir_address: in std_logic_vector(logceil(DEPTH)-1 downto 0);
        or_valid: out std_logic;
        or_data: out std_logic_vector(WIDTH-1 downto 0)
        );
    end entity;
    
    architecture arch of RAM is
    begin
      {% for width, depth in width_depth_pairs %}check_{{width}}_{{depth}}: if ((WIDTH = {{width}}) and (DEPTH = {{depth}})) generate
        ram_for_{{width}}_{{depth}}: entity work.RAM_{{width}}_{{depth}}
          port map (
            clk => clk,
            reset => reset,
            w_valid => i_valid,
            w_data => w_data,
            w_address => w_address,
            ir_valid => ir_valid,
            ir_address => ir_address,
            or_valid => or_valid,
            or_data => or_data
            );
      end generate;
      {% endfor %}
      nomatch: if not (false{% for width, depth in width_depth_pairs %}
                       or ((WIDTH={{width}}) and (DEPTH={{depth}})){% endfor %}) generate
        assert false report "Generator name=RAM width=" & integer'image(WIDTH) & " depth=" & integer'image(DEPTH);
      end generate;
    end arch;

Utilities
---------

Besides adding the 'generator' section to the core description,
fusesoc_generators provides a function to return a list of files required
by a core, ``get_filenames_from_core``.

It has the arguments:

work_root
  The directory where generated files are placed
top_core_nae
  The top level core we will generate.
top_entity_name
  The entity in the top level core to be generated.
generic_sets
  An iterable of dictionaries of the generic parameters for the top level entity.
top_params
  The top level parameters that will be passed to all generator functions.
additional_generator
  An optional function that takes a directory and list of files, and returns
  a new list of files.  This is useful for adding utility packages.
