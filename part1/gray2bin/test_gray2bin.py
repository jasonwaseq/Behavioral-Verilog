import git
import os
import sys
import git
from functools import reduce 

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

import random

timescale = "1ps/1ps"

tests = ['init_test',
         'width_in',
         'width_out',
         'all_test'
         ]
   
@pytest.mark.parametrize("width_p", [2, 7])
@pytest.mark.parametrize("test_name", tests)
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(0)
def test_each(test_name, simulator, width_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['test_name']
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters, testname=test_name)

# Opposite above, run all the tests in one simulation but reset
# between tests to ensure that reset is clearing all state.
@pytest.mark.parametrize("width_p", [2, 7])
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(2)
def test_all(simulator, width_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("width_p", [7])
@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.4)
def test_lint(simulator, width_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("width_p", [7])
@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.1)
def test_style(simulator, width_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters, compile_args=["--lint-only", "-Wwarn-style", "-Wno-lint"])

@cocotb.test()
async def width_out(dut):
    """The width of gray_i should be equal to width_p"""
    assert len(dut.gray_i) == (dut.width_p.value)

@cocotb.test()
async def width_in(dut):
    """The width of bin_o should be equal to width_p"""
    assert len(dut.bin_o) == (dut.width_p.value)

@cocotb.test()
async def init_test(dut):
    """Test for Basic Connectivity"""

    gray_i = dut.gray_i
    gray_i.value = 0

    await Timer(1, units="ns")

    assert_resolvable(dut.bin_o)

def gray2bin(val):
   b = BinaryValue(0,len(val), False)
   for i in range(len(val)):
      rval = BinaryValue(val>>i, len(val), False)
      b[i] = reduce(lambda x, y: x ^ y, rval, 0)
   return b

@cocotb.test()
async def all_test(dut):
    """Test for converting numbers from graycode to binary"""

    gray_i = dut.gray_i
    gray_i.value = 0

    await Timer(1, units="ns")

    assert_resolvable(dut.bin_o)
    
    for i in range(0, (1 << len(gray_i)) - 1):
       gray_i.value = i

       await Timer(1, units="ns")
       assert_resolvable(dut.bin_o)

       expected = gray2bin(gray_i.value)
       assert dut.bin_o.value == (expected) , f"Incorrect Result: gray_i == {gray_i.value}. Got: bin_o == {dut.bin_o.value} at Time {get_sim_time(units='ns')}ns."
