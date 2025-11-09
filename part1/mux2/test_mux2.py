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

from cocotb_test.simulator import run

from cocotbext.axi import AxiLiteBus, AxiLiteMaster, AxiStreamSink, AxiStreamMonitor, AxiStreamBus

from pytest_utils.decorators import max_score, visibility, tags
   
timescale = "1ps/1ps"

tests = ['init_test',
         'three_input_test_001',
         'three_input_test_002',
         'three_input_test_003',
         'three_input_test_004',
         'three_input_test_005',
         'three_input_test_006',
         'three_input_test_007',
         'three_input_test_008',
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
@max_score(.5)
def test_all(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters)

### Begin Tests ###

@cocotb.test()
async def init_test(dut):
    """Test for Basic Connectivity"""

    dut.a_i.value = 0
    dut.b_i.value = 0
    dut.select_i.value = 0

    await Timer(1, units="ns")

    assert_resolvable(dut.c_o)

    
async def three_input_test(dut, a, b, s):
    """Test for three inputs"""

    # I would like to test numbers that depend on the parameters to
    # the DUT (e.g. width_p), but the parameters are not available
    # until test runtime, so we occasionally have to pass in strings
    # that reference the DUT. Hence, these if/else statements (until I
    # find a better way).
    
    if(isinstance(a, int)):
        A = a
    else:
        A = eval(a)

    if(isinstance(b, int)):
        B = b
    else:
        B = eval(b)

    if(isinstance(s, int)):
        S = s
    else:
        S = eval(s)
    
    dut.a_i.value = A
    dut.b_i.value = B
    dut.select_i.value = S

    await Timer(1, units="ns")

    # Isn't python nice!
    c_o = dut.a_i.value if not dut.select_i.value else dut.b_i.value

    assert_resolvable(dut.c_o)
    assert dut.c_o.value == (c_o) , f"Incorrect Result: c_o for a_i == {dut.a_i.value}, b_i == {dut.b_i.value}, and select_i == {dut.select_i.value}). Got: {dut.c_o.value} at Time {get_sim_time(units='ns')}ns."

tf = TestFactory(test_function=three_input_test)

tf.add_option(name='a', optionlist=[0, 1])
tf.add_option(name='b', optionlist=[0, 1])
tf.add_option(name='s', optionlist=[0, 1])
tf.generate_tests()
