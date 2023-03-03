import os
import subprocess

from nmigen.build import *
from nmigen.vendor.lattice_ecp5 import *
from nmigen_boards.resources import *


__all__ = ["HadBadge2019"]


class HadBadge2019(LatticeECP5Platform):
    device      = "LFE5U-45F"
    package     = "BG381"
    speed       = 8

    default_clk = "clk8"
    resources   = [
        Resource("clk8", 0, Pins("U18", dir="i"),
                 Clock(8e6), Attrs(GLOBAL=True, IO_TYPE="LVCMOS33")),

        *LEDResources(pins="E3 D3 C3 C4 C2 B1 B20 B19 A18 K20 K19", invert=False, attrs=Attrs(IO_TYPE="LVCMOS33")),

        *ButtonResources(pins="G2 F2 F1 C1 E1 D2 D1 E2", invert=False, attrs=Attrs(IO_TYPE="LVCMOS33", PULLUP=1)),

        UARTResource(0,
            rx="U2", tx="U1",
            attrs=Attrs(IO_TYPE="LVCMOS33", PULLUP=1)
        ),
        Resource("pmod", 0, Pins("A15 C16 A14 D16      B15 C15 A13 B13")) # PMOD
    ]


        # FIXME: add PSRAM
    """
    # PSRAM #1
    *SPIFlashResources(0, #TODO: check pins!
        cs_n="D20", clk="E20", copi="E19", cipo="D19", wp_n="A11", hold_n="B8",
        attrs=Attrs(IO_TYPE="LVCMOS33", SLEWRATE="SLOW")
    ),

    # PSRAM #2
    *SPIFlashResources(1, #TODO: check pins!
        cs_n="A2", clk="A4", copi="A5", cipo="B3", wp_n="B4", hold_n="A3",
        attrs=Attrs(IO_TYPE="LVCMOS33")
    ),
    """

    connectors = [
        Connector("pmod", 0, "A15 C16 A14 D16      B15 C15 A13 B13"), # PMOD
    ]

    def toolchain_program(self, products, name):
        #interface = os.environ.get("INTERFACE", "/dev/ttyACM0")
        bitstrem_name = "{}.bit".format(name)
        print("PROGRAM BITSTREAM COMMAND:");
        print("dfu-util -d 1d50:614a,1d50:614b -a 0 -R -D build/" + bitstrem_name)
        # Grab our generated bitstream, and upload it to the FPGA.
        # bitstream_data =  products.get(bitstream_name) #get contents

