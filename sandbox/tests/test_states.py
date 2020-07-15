from sandbox.controller import Processing, Starting
from sandbox import protocol


class MockController:
    def __init__(self, initial_state):
        self.state = initial_state

    def transition_to(self, state):
        self.state = state


def null_action(payload):
    pass


def error_action(payload):
    raise Exception("boom")


def process_action(payload):
    return payload


def test_starting_stop():
    controller = MockController("starting")
    starting = Starting(controller, null_action)
    result = starting.run(protocol.Commands.STOP, None)
    assert result
    code, payload = result
    assert code == protocol.Responses.OKAY
    assert controller.state == "stopping"


def test_starting_setup():
    controller = MockController("starting")
    starting = Starting(controller, null_action)
    result = starting.run(protocol.Commands.SETUP, {})
    assert result
    code, payload = result
    assert code == protocol.Responses.OKAY
    assert controller.state == "processing"


def test_starting_error():
    controller = MockController("starting")
    starting = Starting(controller, error_action)
    result = starting.run(protocol.Commands.SETUP, None)
    assert result
    code, payload = result
    assert code == protocol.Responses.ERROR, payload
    assert controller.state == "stopping"


def test_starting_invalid_command():
    controller = MockController("starting")
    starting = Starting(controller, error_action)
    result = starting.run(protocol.Commands.PROCESS, None)
    assert result
    code, payload = result
    assert code == protocol.Responses.ERROR, payload
    assert controller.state == "stopping"


def test_processing_stop():
    controller = MockController("processing")
    starting = Starting(controller, null_action)
    result = starting.run(protocol.Commands.STOP, None)
    assert result
    code, payload = result
    assert code == protocol.Responses.OKAY
    assert controller.state == "stopping"


def test_processing():
    controller = MockController("processing")
    starting = Processing(controller, process_action)
    task = object()
    result = starting.run(protocol.Commands.PROCESS, task)
    assert result
    code, payload = result
    assert code == protocol.Responses.RESULTS, payload
    assert payload is task, payload
    assert controller.state == "processing"


def test_processing_error():
    controller = MockController("processing")
    starting = Processing(controller, error_action)
    result = starting.run(protocol.Commands.PROCESS, None)
    assert result
    code, payload = result
    assert code == protocol.Responses.ERROR, payload


def test_processing_invalid_command():
    controller = MockController("processing")
    starting = Processing(controller, null_action)
    result = starting.run(protocol.Commands.SETUP, None)
    assert result
    code, payload = result
    assert code == protocol.Responses.ERROR
    assert controller.state == "stopping"
