from mock_trace import MockTrace as mt
import importlib

from examples.fibonacci import slow_fib


def test_basic():
    assert slow_fib(-1) == 0
    assert slow_fib(0) == 0
    assert slow_fib(1) == 1
    assert slow_fib(2) == 1
    assert slow_fib(3) == 2
    assert slow_fib(4) == 3
    assert slow_fib(5) == 5
    assert slow_fib(6) == 8
    assert slow_fib(7) == 13
    assert slow_fib(8) == 21
    assert slow_fib(9) == 34
    assert slow_fib(10) == 55


def test_dynamic():
    slow_fib2 = getattr(importlib.import_module(
        'examples.fibonacci'), 'slow_fib')
    assert slow_fib2(-1) == 0
    assert slow_fib2(0) == 0
    assert slow_fib2(1) == 1
    assert slow_fib2(2) == 1
    assert slow_fib2(3) == 2
    assert slow_fib2(4) == 3
    assert slow_fib2(5) == 5
    assert slow_fib2(6) == 8
    assert slow_fib2(7) == 13
    assert slow_fib2(8) == 21
    assert slow_fib2(9) == 34
    assert slow_fib2(10) == 55


def test_trace():
    with mt.patch('examples.fibonacci.slow_fib') as sf2:
        sf2(4)

    assert mt.calls_count() == 9
    assert str(sf2) == "MockTrace(function=examples.fibonacci.slow_fib, mocker=slow_fib) called 9 times"

    with mt.patch('examples.fibonacci.slow_fib') as sf2:
        sf2(4)

    assert mt.calls_count() == 9
    assert str(sf2) == "MockTrace(function=examples.fibonacci.slow_fib, mocker=slow_fib) called 9 times"

    shape = mt.graph_shape()
    print(shape)
    assert shape == [
        (None, ["examples.fibonacci.slow_fib(['4'])"]),
        ("examples.fibonacci.slow_fib(['4'])", ["examples.fibonacci.slow_fib(['3'])", "examples.fibonacci.slow_fib(['2'])"]
         ),
        ("examples.fibonacci.slow_fib(['3'])", ["examples.fibonacci.slow_fib(['2'])", "examples.fibonacci.slow_fib(['1'])"]
         ),
        ("examples.fibonacci.slow_fib(['2'])", ["examples.fibonacci.slow_fib(['1'])", "examples.fibonacci.slow_fib(['0'])"]
         ),
        ("examples.fibonacci.slow_fib(['2'])", ["examples.fibonacci.slow_fib(['1'])", "examples.fibonacci.slow_fib(['0'])"]
         ),
    ]
