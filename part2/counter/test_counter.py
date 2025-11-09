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
         'up_test',
         'down_test',
         'updown_test',
         'overflow_test',
         'underflow_test',
         'fuzz_test_001',
         'fuzz_test_002',
         'fuzz_test_003']


@pytest.mark.parametrize("width_p", [2, 7, 5, 4])
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
@pytest.mark.parametrize("width_p", [2, 7, 5, 4])
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(1)
def test_all(simulator, width_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("width_p", [5])
@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.4)
def test_lint(simulator, width_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("width_p", [5])
@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.1)
def test_style(simulator, width_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters, compile_args=["--lint-only", "-Wwarn-style", "-Wno-lint"])


### Begin Tests ###

@cocotb.test()
async def reset_test(dut):
    """Test for Initialization"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    up_i = dut.up_i
    down_i = dut.down_i
    count_o = dut.count_o

    up_i.value = LogicArray(['x'])
    down_i.value = LogicArray(['x'])

    await clock_start_sequence(clk_i)
    await reset_sequence(clk_i, reset_i, 10)

    # Set the initial inputs
    up_i.value = 0
    down_i.value = 0

    # Always check outputs on the rising edge
    await RisingEdge(dut.clk_i)

    ex_val = 0

    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."


@cocotb.test()
async def up_test(dut):
    """Test up_i"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    up_i = dut.up_i
    down_i = dut.down_i
    count_o = dut.count_o

    up_i.value = LogicArray(['x'])
    down_i.value = LogicArray(['x'])

    await clock_start_sequence(clk_i)
    await reset_sequence(clk_i, reset_i, 10)

    # Always Set Inputs on the falling edge
    up_i.value = 0
    down_i.value = 0

    # Always check outputs on the rising edge
    await RisingEdge(dut.clk_i)
    
    await FallingEdge(dut.clk_i)
    up_i.value = 1
    
    # Increment once.
    await RisingEdge(dut.clk_i)

    ex_val = 1
    if(ex_val == (1 << len(dut.count_o))):
       ex_val = 0

    await FallingEdge(dut.clk_i)
    up_i.value = 0

    # Check after one cycle of up
    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

    await RisingEdge(dut.clk_i)

    # Value should remain constant.
    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

@cocotb.test()
async def down_test(dut):
    """Test down_i"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    up_i = dut.up_i
    down_i = dut.down_i
    count_o = dut.count_o

    up_i.value = LogicArray(['x'])
    down_i.value = LogicArray(['x'])

    await clock_start_sequence(clk_i)
    await reset_sequence(clk_i, reset_i, 10)

    # Always Set Inputs on the falling edge
    up_i.value = 0
    down_i.value = 0

    # Always check outputs on the rising edge
    await RisingEdge(dut.clk_i)
    
    await FallingEdge(dut.clk_i)
    down_i.value = 1
    
    # Increment once.
    await RisingEdge(dut.clk_i)

    ex_val = -1

    if(ex_val == -1):
       ex_val = (1 << len(dut.count_o)) -1

    await FallingEdge(dut.clk_i)
    down_i.value = 0

    # Check after one cycle of down
    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

    await RisingEdge(dut.clk_i)

    # Value should remain constant.
    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

@cocotb.test()
async def updown_test(dut):
    """Test for up_i and down_i (Simultaneously)"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    up_i = dut.up_i
    down_i = dut.down_i
    count_o = dut.count_o

    up_i.value = LogicArray(['x'])
    down_i.value = LogicArray(['x'])

    await clock_start_sequence(clk_i)
    await reset_sequence(clk_i, reset_i, 10)

    # Always Set Inputs on the falling edge
    up_i.value = 0
    down_i.value = 0

    # Always check outputs on the rising edge
    await RisingEdge(dut.clk_i)
    
    await FallingEdge(dut.clk_i)
    up_i.value = 1
    down_i.value = 1
    
    # Increment once.
    await RisingEdge(dut.clk_i)

    ex_val = 0

    await FallingEdge(dut.clk_i)
    up_i.value = 0
    down_i.value = 0

    # Check after one cycle of down
    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

    await RisingEdge(dut.clk_i)

    # Value should remain constant.
    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

async def wait_for(dut, value):
    while(dut.count_o.value.is_resolvable and dut.count_o.value != value):
        await FallingEdge(dut.clk_i)

@cocotb.test()
async def overflow_test(dut):
    """Test for Overflow"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    up_i = dut.up_i
    down_i = dut.down_i
    count_o = dut.count_o

    up_i.value = LogicArray(['x'])
    down_i.value = LogicArray(['x'])

    await clock_start_sequence(clk_i)
    await reset_sequence(clk_i, reset_i, 10)

    # Always Set Inputs on the falling edge
    up_i.value = 0
    down_i.value = 0
    
    await FallingEdge(dut.clk_i)
    up_i.value = 1
    
    count_to = (1<<dut.width_p.value)-1
    ex_val = count_to
    await with_timeout(wait_for(dut, value=count_to), count_to + 1, 'ns')

    # Increment once more.
    await FallingEdge(dut.clk_i)

    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == 0 , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

@cocotb.test()
async def underflow_test(dut):
    """Test for Underflow"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    up_i = dut.up_i
    down_i = dut.down_i
    count_o = dut.count_o

    up_i.value = LogicArray(['x'])
    down_i.value = LogicArray(['x'])

    await clock_start_sequence(clk_i)
    await reset_sequence(clk_i, reset_i, 10)

    # Always Set Inputs on the falling edge
    up_i.value = 0
    down_i.value = 0
    
    await FallingEdge(dut.clk_i)
    down_i.value = 1
    
    count_to = 0
    ex_val = (1<<dut.width_p.value)-1
    await with_timeout(wait_for(dut, value=0), 1, 'ns')

    # Decrement once more to underflow
    await FallingEdge(dut.clk_i)

    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val, f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

async def fuzz_test(dut, l):
    """Test for Random Input"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    up_i = dut.up_i
    down_i = dut.down_i
    count_o = dut.count_o

    up_i.value = LogicArray(['x'])
    down_i.value = LogicArray(['x'])

    await clock_start_sequence(clk_i)
    await reset_sequence(clk_i, reset_i, 10)

    # set the initial inputs
    up_i.value = 0
    down_i.value = 0

    await FallingEdge(dut.clk_i)

    seq = [random.randint(0, 4) for i in range(l)]
    for i in seq:
        await FallingEdge(dut.clk_i)
        up_i.value = (i == 1 or i == 3)
        down_i.value = (i == 2 or i == 3)

    await FallingEdge(dut.clk_i)

    ctrseq = list(range((1<<dut.width_p.value)))
    idx = seq.count(1) - seq.count(2)
    idx = idx % len(ctrseq)
    ex_val = ctrseq[idx]
    
    assert count_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert count_o.value == ex_val , f"Incorrect Result: count_o != {ex_val}. Got: {count_o.value} at Time {get_sim_time(units='ns')}ns."

tf = TestFactory(test_function=fuzz_test)
tf.add_option(name='l', optionlist=[10, 100, 1000])
tf.generate_tests()
