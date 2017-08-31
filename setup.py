from setuptools import setup

setup(
    name="fusesoc_generators",
    packages=['fusesoc_generators'],
    author="Ben Reynwar",
    author_email="ben@reynwar.net",
    description=(""),
    license="MIT",
    keywords=["VHDL", "hdl", "rtl", "FPGA", "ASIC", "Xilinx", "Altera", "fusesoc"],
    url="https://github.com/benreynwar/fusesoc_generators",
    install_requires=[
        'jinja2',
        'fusesoc>=1.7.0',
    ],
)
