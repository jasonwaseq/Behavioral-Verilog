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
from functools import reduce
   
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
         "sequence_single_test_008",
         "sequence_single_test_009",
         "sequence_single_test_010",
         "sequence_single_test_011",
         "sequence_single_test_012",
         "sequence_single_test_013",
         "sequence_single_test_014",
         "sequence_single_test_015",
         "sequence_single_test_016",
         "sequence_single_test_017",
         "sequence_single_test_018",
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

@cocotb.test()
async def reset_test(dut):
    """Test for Initialization"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    direction_i = dut.direction_i
    valid_i = dut.valid_i
    sequence_o = dut.sequence_detected_o
    await clock_start_sequence(clk_i)
    
    await reset_sequence(clk_i, reset_i, 10)

    valid_i.value = 0
    direction_i.value = 0

    await FallingEdge(clk_i)

    assert sequence_o.value.is_resolvable, f"Unresolvable value in sequence_detected_o (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert sequence_o.value == 0 , f"Error! Sequence detected after reset!. Got: {unlocked_o.value} at Time {get_sim_time(units='ns')}ns."
    

# Valid sequences: NSN (001100), NSE (001101), EW (0110), WSN (101100), WSE (101101)
# dirs = {"N": 00, "E": 01, "S": 3, "W": 2}
goals = ["NSN", "NSE", "EW", "WSN", "WSE"]

async def sequence_single_test(dut, sequence):
    """Test for a single sequence of inputs"""
    clk_i = dut.clk_i
    reset_i = dut.reset_i
    sequence_o = dut.sequence_detected_o
    direction_i = dut.direction_i
    valid_i = dut.valid_i

    model = MealyModel(clk_i, reset_i, direction_i, valid_i, sequence_o, goals)
    print(f"Binary Sequence: {model.apply(sequence)}")


    await clock_start_sequence(clk_i)    
    await reset_sequence(clk_i, reset_i, 10)

    valid_i.value = 0
    direction_i.value = 0

    model.start()

    await FallingEdge(clk_i)

    for i in sequence:
        # Provide some random, invalid, inputs.
        while(random.randint(0, 10) != 5):
            dut.valid_i.value = 0
            dut.direction_i.value = model._dirs[random.choice(["N", "E", "S", "W"])]
            await FallingEdge(clk_i)
            
        # Provide a valid input
        dut.direction_i.value = model._dirs[i]
        dut.valid_i.value = 1
        print(i)
        await FallingEdge(clk_i)

tf = TestFactory(test_function=sequence_single_test)

sequences = ["N", "E", "S", "W",
             *goals,
             *[g[::-1] for g in goals], # Reverse goals
             "EWNSN", "WSEW", "NSNSE", # Two goals back to back.
             reduce(lambda x, y: x + y, goals) # All goals
             ]
tf.add_option(name='sequence', optionlist=sequences)
tf.generate_tests()


class MealyModel():
    def __init__(self, clk_i, reset_i, direction_i, valid_i, sequence_o, goals):
        self._clk_i = clk_i
        self._reset_i = reset_i
        self._direction_i = direction_i
        self._valid_i = valid_i
        self._sequence_o = sequence_o
        self._coro_run = None
        self._coro_win = None
        self._history = ""
        self._goals = goals
        self._dirs = {"N": 0, "E": 1, "S": 3, "W": 2}
        self._invdirs = {0: "N", 1:"E", 3:"S", 2:"W"}
        self._state_win = False
        self._next_win = False

    def start(self):
        """Start model"""
        if self._coro_run is not None:
            raise RuntimeError("Model already started")
        self._coro_run = cocotb.start_soon(self._run())

        self._coro_win = cocotb.start_soon(self._win())

    def apply(self, sequence):
        return reduce(lambda x, y: x + y, map(lambda x: f"{self._dirs[x]:02b}", sequence))

    async def _win(self):
        while True:
            await RisingEdge(self._clk_i)
            assert_resolvable(self._sequence_o)
            assert self._sequence_o.value == self._state_win, f"Error! sequence_o does not match expected! History: {self._history}. Got: {self._sequence_o.value} at Time {get_sim_time(units='ns')}ns."

    async def _run(self):
        while True:
            await RisingEdge(self._clk_i)
            if(not(self._reset_i.value.is_resolvable)):
                pass
            elif(self._reset_i.value == 1):
                self._history = ""
            elif(self._valid_i.value == 1):
                self._history += self._invdirs[int(self._direction_i.value)]
                ms = [self._history.endswith(w) for w in self._goals]
                self._state_win = reduce(lambda x, y: x or y, ms)
            else:
                # If not a valid button press...
                self._state_win = False
                      
    def stop(self) -> None:
        """Stop monitor"""
        if self._coro_run is None:
            raise RuntimeError("Monitor never started")
        
