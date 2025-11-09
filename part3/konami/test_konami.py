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
timescale = "1ps/1ps"
tests = ['reset_test',
         "sequence_single_test_001",
         "sequence_single_test_002",
         "sequence_single_test_003",
         "sequence_single_test_004",
         "sequence_single_test_005",
         "sequence_single_test_006",
         "sequence_single_test_007",
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

@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(8)
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
         
async def reset(dut, reset_i, cycles, FinishFalling=True):
    # Wait for the next rising edge
    await RisingEdge(dut.clk_i)

    # Always assign inputs on the falling edge
    await FallingEdge(dut.clk_i)
    reset_i.value = 1

    await ClockCycles(dut.clk_i, cycles)

    # Always assign inputs on the falling edge
    await FallingEdge(dut.clk_i)
    reset_i.value = 0

    reset_i._log.debug("Reset complete")

    # Always assign inputs on the falling edge
    if (not FinishFalling):
        await RisingEdge(dut.clk_i)
   
async def wait_for_signal(dut, signal, value):
    signal = getattr(dut, signal)
    while(signal.value.is_resolvable and signal.value != value):
        await FallingEdge(dut.clk_i)

async def pretest_sequence(dut):
    # Set the clock to Z for 10 ns. This helps separate tests.
    dut.clk_i.value = LogicArray(['z'])
    await Timer(10, 'ns')

    # Unrealistically fast clock, but nice for mental math (1 GHz)
    c = Clock(dut.clk_i, 1, 'ns')

    # Start the clock (soon). Start it low to avoid issues on the first RisingEdge
    cocotb.start_soon(c.start(start_high=False))

async def reset_sequence(dut):
    buttons = {
        "U":dut.up_i,
        "u":dut.unup_i,
        "R":dut.right_i,
        "r":dut.unright_i,
        "D":dut.down_i,
        "d":dut.undown_i,
        "l":dut.left_i,
        "L":dut.unleft_i,
        "a":dut.a_i,
        "A":dut.una_i,
        "b":dut.b_i,
        "B":dut.unb_i,
        "S":dut.start_i,
        "s":dut.unstart_i
    }
               
    clk_i = dut.clk_i
    reset_i = dut.reset_i
    unlocked_o = dut.cheat_code_unlocked_o
    
    for _,v in buttons.items():
        v.value = LogicArray(['x'])

    await reset(dut, reset_i, cycles=10, FinishFalling=True)

    for _,v in buttons.items():
        v.value = 0

    await FallingEdge(clk_i)

    assert unlocked_o.value.is_resolvable, f"Unresolvable value in cheat_code_unlocked_o (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert unlocked_o.value == 0 , f"Error! Cheat code unlocked after reset!. Got: {unlocked_o.value} at Time {get_sim_time(units='ns')}ns."

    
@cocotb.test()
async def reset_test(dut):
    """Test for Initialization"""

    await pretest_sequence(dut)
    await reset_sequence(dut)
    

async def sequence_single_test(dut, sequence):
    """Test for a single sequence of inputs"""

    await pretest_sequence(dut)
    await reset_sequence(dut)

    clk_i = dut.clk_i
    unlocked_o = dut.cheat_code_unlocked_o
    buttons = {
        "U":dut.up_i,
        "u":dut.unup_i,
        "R":dut.right_i,
        "r":dut.unright_i,
        "D":dut.down_i,
        "d":dut.undown_i,
        "L":dut.left_i,
        "l":dut.unleft_i,
        "A":dut.a_i,
        "a":dut.una_i,
        "B":dut.b_i,
        "b":dut.unb_i,
        "S":dut.start_i,
        "s":dut.unstart_i
    }


    history = ""
    goal = "UuUuDdDdLlRrLlRrBbAaSs"
    #goal = "SsAaBbRrLlRrLlDdDdUuUu"
    last = "u"
    unlocked = False
    for i in sequence:
        await FallingEdge(clk_i)
        # Check from posedge
        assert_resolvable(unlocked_o)
        assert unlocked_o.value == unlocked, f"Error! Cheat code unlocked does not match expected!. Got: {unlocked_o.value} at Time {get_sim_time(units='ns')}ns."

        # Set values
        buttons[last].value = 0
        buttons[i].value = 1
        last = i
        history = history + i
        unlocked = history.endswith(goal)
        await RisingEdge(clk_i)        

    await FallingEdge(clk_i)
    assert_resolvable(unlocked_o)
    assert unlocked_o.value == unlocked, f"Error! Cheat code unlocked does not match expected!. Got: {unlocked_o.value} at Time {get_sim_time(units='ns')}ns."

tf = TestFactory(test_function=sequence_single_test)

sequences = ["UUDDLRLRBAS",
             "uuddlrlrbas",
             "UUDDLRLRBASuuddlrlrbas",
             "SsAaBbRrLlRrLlDdDdUuUu",
             "UuUuDdDdLlRrLlRrBbAaSs",
             "UuUuUuUuDdDdLlRrLlRrBbAaSs",
             "SsAaBbRrLlRrLlDdDdUuUuUu",
             "UuUuUuUuDdDdLlRrLlRrBbAaSsSs",
             "SsSsAaBbRrLlRrLlDdDdUuUuUu",
             "UuUuDdDdLlRrLlRrBbAaSsUuUuDdDdLlRrLlRrBbAaSs",
             "SsAaBbRrLlRrLlDdDdUuUuSsAaBbRrLlRrLlDdDdUuUu"
             ]
tf.add_option(name='sequence', optionlist=sequences)
tf.generate_tests()
