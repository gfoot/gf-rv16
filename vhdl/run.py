from pathlib import Path
from vunit import VUnit

VU = VUnit.from_argv(compile_builtins=False)
VU.add_vhdl_builtins()
VU.add_osvvm()
VU.add_verification_components()

SRC_PATH = Path(__file__).parent

VU.add_library("gfrv16").add_source_files(SRC_PATH / "modules" / "*.vhd")
VU.add_library("tb_gfrv16").add_source_files(SRC_PATH / "tests" / "tb_*.vhd")

VU.main()

