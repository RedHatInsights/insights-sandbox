from collections import deque
import dill

from sandbox.controller import Controller
from sandbox.protocol import Setup, Process, Stop


def test_controller_stop():
    io = IO([Stop()])
    controller = Controller(handle_setup, handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopping"
    assert len(io.output) == 2


def test_controller_setup():
    io = IO([Setup({}), Stop()])
    controller = Controller(handle_setup, handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopping"
    assert len(io.output) == 3


def test_controller_process():
    io = IO([Setup({}), Process("some data"), Process("more data"), Stop()])
    controller = Controller(handle_setup, handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopping"
    assert len(io.output) == 5


def test_setup_error():
    io = IO([Setup({}), Process("some data"), Stop()])
    controller = Controller(handle_setup_error, handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopping"
    assert len(io.output) == 2


def test_processing_error():
    io = IO([Setup({}), Process("some data"), Stop()])
    controller = Controller(handle_setup, handle_processing_error, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopping"
    assert len(io.output) == 3


class IO:
    def __init__(self, inbuf):
        self.inbuf = deque(inbuf)
        self.output = []

    def recv(self):
        cmd, payload = self.inbuf.popleft()
        return (cmd, dill.dumps(payload))

    def send(self, payload):
        self.output.append(payload)


def handle_setup(payload):
    return payload


def handle_setup_error(payload):
    raise Exception("setup boom")


def handle_processing(payload):
    return payload


def handle_processing_error(payload):
    raise Exception("process boom")
