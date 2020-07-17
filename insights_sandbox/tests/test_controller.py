from insights_sandbox.controller import Controller
from insights_sandbox.protocol import Setup, Process, Stop
from insights_sandbox.tests import IO


def handle_setup(payload):
    return payload


def error_handle_setup(payload):
    raise Exception("setup boom")


def handle_processing(payload):
    return payload


def error_handle_processing(payload):
    raise Exception("process boom")


def test_controller_stop():
    io = IO([Stop()])
    controller = Controller(handle_setup, handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopped"
    assert len(io.output) == 2


def test_controller_setup():
    io = IO([Setup({}), Stop()])
    controller = Controller(handle_setup, handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopped"
    assert len(io.output) == 3


def test_controller_process():
    io = IO([Setup({}), Process("some data"), Process("more data"), Stop()])
    controller = Controller(handle_setup, handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopped"
    assert len(io.output) == 5


def test_setup_error():
    io = IO([Setup({}), Process("some data"), Stop()])
    controller = Controller(error_handle_setup, handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopped"
    assert len(io.output) == 2


def test_processing_error():
    io = IO([Setup({}), Process("some data"), Stop()])
    controller = Controller(handle_setup, error_handle_processing, io.send, io.recv)
    assert controller._state == "starting"
    controller.run()
    assert controller._state == "stopped"
    assert len(io.output) == 3
