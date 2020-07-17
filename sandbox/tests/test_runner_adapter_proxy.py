import pytest

from sandbox.tests import IO
from sandbox.adapter import RunnerAdapterProxy
from sandbox.protocol import Error, Okay, Results


def test_setup():
    io = IO([Okay(), Okay()])
    proxy = RunnerAdapterProxy(io.send, io.recv)
    proxy.setup({})
    assert len(io.output) == 1


def test_process_success():
    res = 0
    io = IO([Okay(), Okay(), Results(res)])
    proxy = RunnerAdapterProxy(io.send, io.recv)
    proxy.setup({})
    result = proxy.process("")
    assert result == res
    assert len(io.output) == 2


def test_process_error():
    res = r"boom"
    io = IO([Okay(), Okay(), Error(res)])
    proxy = RunnerAdapterProxy(io.send, io.recv)
    proxy.setup({})
    with pytest.raises(Exception, match=res):
        proxy.process("")
