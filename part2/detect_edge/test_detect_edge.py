import git
import os
import sys
import git

# I don't like this, but it's convenient.
_REPO_ROOT = git.Repo(search_parent_directories=True).working_tree_dir
assert (os.path.exists(_REPO_ROOT)), "REPO_ROOT path must exist"
sys.path.append(os.path.join(_REPO_ROOT, "util"))
from utilities import runner, lint, assert_resolvable, clock_start_sequence, reset_sequence
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
   
import random
random.seed(42)

timescale = "1ps/1ps"
tests = ['reset_test',
         'posedge_test',
         'negedge_test'
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

# Opposite above, run all the tests in one simulation but reset
# between tests to ensure that reset is clearing all state.
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(.5)
def test_all(simulator):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters)

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

         
    
@cocotb.test()
async def reset_test(dut):
    """Test for Initialization"""

    reset_i = dut.reset_i
    button_i = dut.button_i
    button_o = dut.button_o
    unbutton_o = dut.unbutton_o
    clk_i = dut.clk_i

    await clock_start_sequence(clk_i)

    button_i.value = LogicArray(['x'])

    await RisingEdge(clk_i)

    await reset_sequence(clk_i, reset_i, 10)

    # Set the initial inputs
    button_i.value = 0

    await RisingEdge(dut.clk_i)

    assert_resolvable(button_o)
    assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    assert_resolvable(unbutton_o)
    assert unbutton_o.value == 0 , f"Incorrect Result: unbutton_o != {0}. Got: {unbutton_o.value} at Time {get_sim_time(units='ns')}ns."


@cocotb.test()
async def posedge_test(dut):
    """Test for Positive Edge"""

    reset_i = dut.reset_i
    button_i = dut.button_i
    button_o = dut.button_o
    unbutton_o = dut.unbutton_o
    clk_i = dut.clk_i

    await clock_start_sequence(clk_i)

    button_i.value = LogicArray(['x'])

    await RisingEdge(clk_i)

    await reset_sequence(clk_i, reset_i, 10)

    button_i.value = LogicArray(['0'])
    await FallingEdge(dut.clk_i)

    for i in range(0, 10):
        await RisingEdge(dut.clk_i)
        assert_resolvable(button_o)
        assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    await FallingEdge(dut.clk_i)
    button_i.value = LogicArray(['1'])

    await RisingEdge(dut.clk_i)

    assert_resolvable(button_o)
    assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns. Is your solution a *mealy* machine?"

    await RisingEdge(dut.clk_i)
    assert_resolvable(button_o)
    assert button_o.value == 1 , f"Incorrect Result: button_o != {1}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    for i in range(0, 10):
        await RisingEdge(dut.clk_i)
        assert_resolvable(button_o)
        assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."


@cocotb.test()
async def negedge_test(dut):
    """Test for Negative Edge"""

    reset_i = dut.reset_i
    button_i = dut.button_i
    button_o = dut.button_o
    unbutton_o = dut.unbutton_o
    clk_i = dut.clk_i

    await clock_start_sequence(clk_i)

    button_i.value = LogicArray(['x'])

    await RisingEdge(clk_i)

    await reset_sequence(clk_i, reset_i, 10)

    button_i.value = LogicArray(['0'])

    await FallingEdge(dut.clk_i)
        
    button_i.value = LogicArray(['1'])

    await RisingEdge(dut.clk_i)

    assert_resolvable(button_o)
    assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns. Is your solution a *mealy* machine?"

    await RisingEdge(dut.clk_i)
    assert_resolvable(button_o)
    assert button_o.value == 1 , f"Incorrect Result: button_o != {1}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    for i in range(0, 10):
        await RisingEdge(dut.clk_i)
        assert_resolvable(unbutton_o)
        assert unbutton_o.value == 0 , f"Incorrect Result: unbutton_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    await FallingEdge(dut.clk_i)
    button_i.value = LogicArray(['0'])

    await RisingEdge(dut.clk_i)
    assert_resolvable(unbutton_o)
    assert unbutton_o.value == 0 , f"Incorrect Result: unbutton_o != {1}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns. Is your solution a *mealy* machine?"

    await RisingEdge(dut.clk_i)
    assert_resolvable(unbutton_o)
    assert unbutton_o.value == 1 , f"Incorrect Result: unbutton_o != {1}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    for i in range(0, 10):
        await RisingEdge(dut.clk_i)
        assert_resolvable(unbutton_o)
        assert unbutton_o.value == 0 , f"Incorrect Result: unbutton_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."
