import git
import os
import sys
import git

# I don't like this, but it's convenient.
_REPO_ROOT = git.Repo(search_parent_directories=True).working_tree_dir
assert (os.path.exists(_REPO_ROOT)), "REPO_ROOT path must exist"
sys.path.append(os.path.join(_REPO_ROOT, "util"))
from utilities import runner, lint, assert_resolvable
tbpath = os.path.dirname(os.path.realpath(__file__))

import pytest

import cocotb

from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.utils import get_sim_time
from cocotb.triggers import Timer, ClockCycles, RisingEdge, FallingEdge, with_timeout
from cocotb.types import LogicArray, Range
from cocotb.binary import BinaryValue

from cocotb_test.simulator import run

from cocotbext.axi import AxiLiteBus, AxiLiteMaster, AxiStreamSink, AxiStreamMonitor, AxiStreamBus

from pytest_utils.decorators import max_score, visibility, tags
   
timescale = "1ps/1ps"

tests = ['init_test',
         'all_test'
         ]
   
@pytest.mark.parametrize("test_name", tests)
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(0)
def test_each(test_name, simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['test_name']
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters, testname=test_name)

@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.4)
def test_lint(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.1)
def test_style(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters, compile_args=["--lint-only", "-Wwarn-style", "-Wno-lint"])

@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(2)
def test_all(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters)

@cocotb.test()
async def init_test(dut):
    """Test for Basic Connectivity"""

    hex_i = dut.hex_i
    hex_i.value = 0

    await Timer(1, units="ns")

    assert dut.ssd_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."


@cocotb.test()
async def all_test(dut):
    """Test for converting numbers from graycode to binary"""

    hex_i = dut.hex_i
    hex_i.value = 0

    values = {0:BinaryValue(0x40, 7, False),
              1:BinaryValue(0x79, 7, False),
              2:BinaryValue(0x24, 7, False),
              3:BinaryValue(0x30, 7, False),
              4:BinaryValue(0x19, 7, False),
              5:BinaryValue(0x12, 7, False),
              6:BinaryValue(0x02, 7, False),
              7:BinaryValue(0x78, 7, False),
              8:BinaryValue(0x00, 7, False),
              9:BinaryValue(0x18, 7, False),
              10:BinaryValue(0x08, 7, False),
              11:BinaryValue(0x03, 7, False),
              12:BinaryValue(0x46, 7, False),
              13:BinaryValue(0x21, 7, False),
              14:BinaryValue(0x06, 7, False),
              15:BinaryValue(0x0e, 7, False)}

    await Timer(1, units="ns")

    assert_resolvable(dut.ssd_o)

    for i in range(0, (1 << len(hex_i)) - 1):
       hex_i.value = i

       await Timer(1, units="ns")
       assert_resolvable(dut.ssd_o)

       expected = values[hex_i.value.integer]
       assert dut.ssd_o.value == (expected) , f"Incorrect Result: hex_i == {hex_i.value}. Got: ssd_o == {dut.ssd_o.value} at Time {get_sim_time(units='ns')}ns."
