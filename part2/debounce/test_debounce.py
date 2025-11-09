import git
import os
import sys
import git

from math import log, ceil

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
from cocotb.result import SimTimeoutError
from cocotb_test.simulator import run

from cocotbext.axi import AxiLiteBus, AxiLiteMaster, AxiStreamSink, AxiStreamMonitor, AxiStreamBus

from pytest_utils.decorators import max_score, visibility, tags
   
import random
random.seed(42)
timescale = "1ps/1ps"
tests = ['reset_test',
         'min_delay_test',
         'max_delay_test',
         'noise_test'
         ]

@pytest.mark.parametrize("min_delay_p", [10, 500, 1000])
@pytest.mark.parametrize("test_name", tests)
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(0)
def test_each(test_name, simulator, min_delay_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['test_name']
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters, testname=test_name)

# Opposite above, run all the tests in one simulation but reset
# between tests to ensure that reset is clearing all state.
@pytest.mark.parametrize("min_delay_p", [10, 500, 1000])
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(.5)
def test_all(simulator, min_delay_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("min_delay_p", [10])
@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.4)
def test_lint(simulator, min_delay_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("min_delay_p", [10])
@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.1)
def test_style(simulator,min_delay_p):
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
    clk_i = dut.clk_i
    min_delay_p = dut.min_delay_p.value

    await clock_start_sequence(clk_i)

    button_i.value = LogicArray(['x'])

    await RisingEdge(clk_i)

    await reset_sequence(clk_i, reset_i, 10)

    button_i.value = LogicArray(['0'])

    await RisingEdge(dut.clk_i)

    assert_resolvable(button_o)
    assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

async def wait_for(dut, value):
    while(dut.button_o.value.is_resolvable and dut.button_o.value != value):
        await FallingEdge(dut.clk_i)

async def wait_cycles(dut, value, cycles):
    for i in range(cycles):
        if(dut.button_o.value.is_resolvable and dut.button_o.value == value):
            break;
        await FallingEdge(dut.clk_i)

@cocotb.test()
async def min_delay_test(dut):
    """Test mininimum delay parameter"""

    reset_i = dut.reset_i
    button_i = dut.button_i
    button_o = dut.button_o
    clk_i = dut.clk_i
    min_delay_p = dut.min_delay_p.value

    await clock_start_sequence(clk_i)

    button_i.value = LogicArray(['x'])

    await RisingEdge(clk_i)

    await reset_sequence(clk_i, reset_i, 10)

    button_i.value = LogicArray(['0'])

    await RisingEdge(dut.clk_i)

    assert_resolvable(button_o)
    assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    button_i.value = LogicArray(['1'])

    try:
        await with_timeout(wait_for(dut, value=1), min_delay_p, 'ns')
    except:
        assert_resolvable(button_o)
        assert button_o.value == 0 , f"Too early! button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

@cocotb.test()
async def max_delay_test(dut):
    """Test mininimum delay parameter"""

    reset_i = dut.reset_i
    button_i = dut.button_i
    button_o = dut.button_o
    clk_i = dut.clk_i
    min_delay_p = dut.min_delay_p.value

    await clock_start_sequence(clk_i)

    button_i.value = LogicArray(['x'])

    await RisingEdge(clk_i)

    await reset_sequence(clk_i, reset_i, 10)

    button_i.value = LogicArray(['0'])

    await RisingEdge(dut.clk_i)

    assert_resolvable(button_o)
    assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    button_i.value = LogicArray(['1'])

    await with_timeout(wait_for(dut, value=1), (1 << ceil(log(min_delay_p, 2))) + 1, 'ns')

@cocotb.test()
async def noise_test(dut):
    """Test for min_delay_p in the presence of noise"""

    reset_i = dut.reset_i
    button_i = dut.button_i
    button_o = dut.button_o
    clk_i = dut.clk_i
    min_delay_p = dut.min_delay_p.value

    await clock_start_sequence(clk_i)

    button_i.value = LogicArray(['x'])

    await RisingEdge(clk_i)

    await reset_sequence(clk_i, reset_i, 10)

    button_i.value = LogicArray(['0'])

    await RisingEdge(dut.clk_i)

    assert_resolvable(button_o)
    assert button_o.value == 0 , f"Incorrect Result: button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

    button_i.value = LogicArray(['1'])

    seq = [random.randint(0, 1) for i in range(min_delay_p)]
    for i in seq:
        await FallingEdge(dut.clk_i)
        button_i.value = i

    await RisingEdge(dut.clk_i)
    if(seq[-1] == 0):
        button_i.value = 1
        mindelay = cocotb.start_soon(with_timeout(wait_for(dut, value=1), min_delay_p - 1, 'ns'))
        maxdelay = cocotb.start_soon(with_timeout(wait_for(dut, value=1), (1 << ceil(log(min_delay_p, 2))) + 1, 'ns'))
    else:
        mindelay = cocotb.start_soon(with_timeout(wait_for(dut, value=1), min_delay_p - seq[::-1].index(0) - 1, 'ns'))
        maxdelay = cocotb.start_soon(with_timeout(wait_for(dut, value=1), (1 << ceil(log(min_delay_p, 2))) - seq[::-1].index(0) +1, 'ns'))

    try:
        await mindelay
    except SimTimeoutError:
        assert_resolvable(button_o)
        assert button_o.value == 0 , f"Too early! button_o != {0}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."
   
    try:
        await maxdelay
    except SimTimeoutError:
        assert_resolvable(button_o)
        assert button_o.value == 1 , f"Too Late! button_o != {1}. Got: {button_o.value} at Time {get_sim_time(units='ns')}ns."

