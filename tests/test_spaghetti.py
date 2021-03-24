import pytest

from mock_trace import MockTrace as mt

from examples.spaghetti import good


def test_swapin():
    with pytest.raises(TypeError):
        good(42, name="Eastwood")

    with (
        mt.patch('examples.spaghetti.good') as mgood,
        mt.patch('examples.spaghetti.bad') as mbad,
        mt.patch('examples.spaghetti.ugly', mocker=lambda _: "NOOP") as mugly,
    ):
        g = mgood(42, name="Eastwood")

    shape = mt.graph_shape()
    print(shape)
    assert shape == [
        (None, ["examples.spaghetti.good(['42', 'name'])"]),
        ("examples.spaghetti.good(['42', 'name', 'name'])", [
         "examples.spaghetti.bad(['42'])", "examples.spaghetti.ugly(['Eastwood'])"]),
        ("examples.spaghetti.bad(['42'])", [
         "examples.spaghetti.ugly(['42'])"]),
    ]

    with mt.patch('examples.spaghetti.ugly', mocker=lambda _: "NOOP") as mugly:
        g = good(42, name="Eastwood")
    shape = mt.graph_shape()
    print(shape)
    assert shape == [
        (None, ["examples.spaghetti.ugly(['42'])",
         "examples.spaghetti.ugly(['Eastwood'])"]),
    ]
