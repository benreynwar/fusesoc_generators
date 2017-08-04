from setuptools import setup

setup(
    name="fusesoc_generators",
    packages=['fusesoc_generators'],
    use_scm_version={
        "relative_to": __file__,
        "write_to": "fusesoc_generators/version.py",
    },
    author="Ben Reynwar",
    author_email="ben@reynwar.net",
    description=(""),
    license="MIT",
    keywords=["VHDL", "hdl", "rtl", "FPGA", "ASIC", "Xilinx", "Altera", "fusesoc"],
    url="https://github.com/benreynwar/fusesoc_generators",
    install_requires=[
        'fusesoc>=1.6.0',
    ],
)
