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
         'en_tick_test',
         'load_test',
         'bangen_tick_test',
         'free_run_test_001']

@pytest.mark.parametrize("width_p,reset_val_p", [(2, 1), (2, 0), (5, 63)])
@pytest.mark.parametrize("test_name", tests)
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(0)
def test_each(test_name, simulator, width_p, reset_val_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['test_name']
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters, testname=test_name)

@pytest.mark.parametrize("width_p,reset_val_p", [(2, 1), (2, 0), (5, 63)])
@pytest.mark.parametrize("simulator", ["verilator", "icarus"])
@max_score(.5)
def test_all(simulator, width_p, reset_val_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    runner(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("width_p,reset_val_p", [(5, 63)])
@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.4)
def test_lint(simulator, width_p, reset_val_p):
    # This line must be first
    parameters = dict(locals())
    del parameters['simulator']
    lint(simulator, timescale, tbpath, parameters)

@pytest.mark.parametrize("width_p,reset_val_p", [(5, 63)])
@pytest.mark.parametrize("simulator", ["verilator"])
@max_score(.1)
def test_style(simulator, width_p, reset_val_p):
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
    enable_i = dut.enable_i
    d_i = dut.d_i
    load_i = dut.load_i
    data_i = dut.data_i
    data_o = dut.data_o

    enable_i.value = LogicArray(['x'])
    data_i.value = LogicArray(['x'] * dut.width_p.value)

    await clock_start_sequence(clk_i)

    model = ShiftModel(dut.width_p, dut.reset_val_p, clk_i, reset_i, enable_i, d_i, data_i, load_i, data_o)
    model.start()

    d_i.value = 0
    enable_i.value = 0
    data_i.value = 0
    load_i.value = 0

    await reset_sequence(clk_i, reset_i, 10)

    assert data_o.value.is_resolvable, f"Unresolvable value (x or z in some or all bits) at Time {get_sim_time(units='ns')}ns."
    assert data_o.value == dut.reset_val_p.value, f"Incorrect Result: data_o should be {dut.reset_val_p.value} after reset. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."

async def wait_for(clk_i, signal, value):
    while(signal.value.is_resolvable and signal.value != value):
        await FallingEdge(clk_i)

@cocotb.test()
async def load_test(dut):
    """Test one clock cycle of the shift register"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    enable_i = dut.enable_i
    d_i = dut.d_i
    load_i = dut.load_i
    data_i = dut.data_i
    data_o = dut.data_o

    enable_i.value = LogicArray(['x'])
    data_i.value = LogicArray(['x'] * dut.width_p.value)

    await clock_start_sequence(clk_i)

    model = ShiftModel(dut.width_p, dut.reset_val_p, clk_i, reset_i, enable_i, d_i, data_i, load_i, data_o)
    model.start()

    d_i.value = 0
    enable_i.value = 0
    data_i.value = 0
    load_i.value = 0

    await reset_sequence(clk_i, reset_i, 10)

    await FallingEdge(clk_i)
    # First, test shifting in a 1
    mask = (1 << dut.width_p.value) -1
    data_i.value = dut.reset_val_p.value ^ mask
    load_i.value = 1

    await RisingEdge(clk_i)

    assert_resolvable(data_o)
    assert data_o.value == model._data_o, f"Incorrect Result: data_o != {model._data_o}. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."


@cocotb.test()
async def en_tick_test(dut):
    """Test one clock cycle of the shift register"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    enable_i = dut.enable_i
    d_i = dut.d_i
    load_i = dut.load_i
    data_i = dut.data_i
    data_o = dut.data_o

    enable_i.value = LogicArray(['x'])
    data_i.value = LogicArray(['x'] * dut.width_p.value)

    await clock_start_sequence(clk_i)

    model = ShiftModel(dut.width_p, dut.reset_val_p, clk_i, reset_i, enable_i, d_i, data_i, load_i, data_o)
    model.start()

    d_i.value = 0
    enable_i.value = 0
    data_i.value = 0
    load_i.value = 0

    await reset_sequence(clk_i, reset_i, 10)

    await FallingEdge(clk_i)
    # First, test shifting in a 1
    d_i.value = 1
    enable_i.value = 1

    await RisingEdge(clk_i)

    assert_resolvable(data_o)
    assert data_o.value == model._data_o, f"Incorrect Result: data_o != {model._data_o}. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."


    # Then do the same test, but shift in a 0

    await reset_sequence(clk_i, reset_i, 10)

    await FallingEdge(clk_i)
    data_i.value = 0
    enable_i.value = 1

    await RisingEdge(clk_i)

    assert_resolvable(data_o)
    assert data_o.value == model._data_o, f"Incorrect Result: data_o != {model._data_o}. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."



@cocotb.test()
async def bangen_tick_test(dut):
    """Test one clock cycle of the shift register, with enable low"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    enable_i = dut.enable_i
    d_i = dut.d_i
    load_i = dut.load_i
    data_i = dut.data_i
    data_o = dut.data_o

    enable_i.value = LogicArray(['x'])
    data_i.value = LogicArray(['x'] * dut.width_p.value)

    await clock_start_sequence(clk_i)

    model = ShiftModel(dut.width_p, dut.reset_val_p, clk_i, reset_i, enable_i, d_i, data_i, load_i, data_o)
    model.start()

    d_i.value = 0
    enable_i.value = 0
    data_i.value = 0
    load_i.value = 0

    await reset_sequence(clk_i, reset_i, 10)

    await FallingEdge(clk_i)
    # First, test shifting in a 1, but no enable
    d_i.value = 1
    enable_i.value = 0

    await RisingEdge(clk_i)
    assert_resolvable(data_o)
    assert data_o.value == model._data_o, f"Incorrect Result: data_o != {model._data_o}. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."

    await RisingEdge(clk_i)
    assert_resolvable(data_o)
    assert data_o.value == model._data_o, f"Incorrect Result: data_o != {model._data_o}. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."

    # Then do the same test, but "shift" in a 0
    await reset_sequence(clk_i, reset_i, 10)


    await FallingEdge(clk_i)
    d_i.value = 0
    enable_i.value = 0

    await RisingEdge(clk_i)
    assert_resolvable(data_o)
    assert data_o.value == model._data_o, f"Incorrect Result: data_o != {model._data_o}. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."

    await RisingEdge(clk_i)
    assert_resolvable(data_o)
    assert data_o.value == model._data_o, f"Incorrect Result: data_o != {model._data_o}. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."

async def free_run_test(dut, l):
    """Test l cycles of the shift register"""

    clk_i = dut.clk_i
    reset_i = dut.reset_i
    enable_i = dut.enable_i
    d_i = dut.d_i
    load_i = dut.load_i
    data_i = dut.data_i
    data_o = dut.data_o

    enable_i.value = LogicArray(['x'])
    data_i.value = LogicArray(['x'] * dut.width_p.value)

    await clock_start_sequence(clk_i)

    model = ShiftModel(dut.width_p, dut.reset_val_p, clk_i, reset_i, enable_i, d_i, data_i, load_i, data_o)
    model.start()

    d_i.value = 0
    enable_i.value = 0
    data_i.value = 0
    load_i.value = 0

    await reset_sequence(clk_i, reset_i, 10)

    await FallingEdge(clk_i)

    ens = [random.randint(0, 1) for i in range(l)]
    ds  = [random.randint(0, 1) for i in range(l)]
    datas  = [random.randint(0, 1) for i in range(l)]
    loads  = [random.randint(0, 10) for i in range(l)]
    seq = zip(ens, ds, datas, loads)
    for (en, d, data, load) in seq:

        await FallingEdge(clk_i)
        enable_i.value = (en == 1)
        d_i.value = d
        data_i.value = data
        load_i.value = (load == 1)

        await RisingEdge(clk_i)
        assert_resolvable(data_o)
        assert data_o.value == model._data_o, f"Incorrect Result: data_o != {model._data_o}. Got: {data_o.value} at Time {get_sim_time(units='ns')}ns."

           
tf = TestFactory(test_function=free_run_test)
tf.add_option(name='l', optionlist=[100])
tf.generate_tests()

class ShiftModel():
    def __init__(self, width_p, reset_val_p, clk_i, reset_i, enable_i, d_i, data_i, load_i, data_o):
                 
        self._width_p = width_p
        self._reset_val_p = reset_val_p
        self._clk_i = clk_i
        self._reset_i = reset_i
        self._enable_i = enable_i
        self._d_i = d_i
        self._load_i = load_i
        self._data_i = data_i
        self._coro_run = None
        self._nstate = 0
        self._data_o = 0

    def start(self):
        """Start model"""
        if self._coro_run is not None:
            raise RuntimeError("Model already started")
        self._coro_run = cocotb.start_soon(self._run())

    async def _run(self):
        mask = (1 << self._width_p.value) -1
        print(mask)

        while True:
            await RisingEdge(self._clk_i)
            if(self._reset_i.value.is_resolvable and (self._reset_i.value == 1)):
                self._nstate = self._reset_val_p.value
            elif(self._load_i.value.is_resolvable and (self._load_i.value == 1)):
                self._nstate = self._data_i.value
            elif(self._enable_i.value.is_resolvable and (self._enable_i.value == 1)):
                self._nstate = ((self._data_o << 1) | self._d_i.value) & mask

            await FallingEdge(self._clk_i)
            self._data_o = self._nstate

    def stop(self) -> None:
        """Stop monitor"""
        if self._coro_run is None:
            raise RuntimeError("Monitor never started")
