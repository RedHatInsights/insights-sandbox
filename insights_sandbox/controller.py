import traceback

import dill
from insights_sandbox.protocol import Commands, Error, Okay, Results


class Controller:
    """
    Drives a state machine that controls a ``Runner`` via the
    setup and process methods of a ``RunnerAdapter``.

    Arguments:
        setup (function): Function that handles the SETUP command's payload.
        process (function): Function that handles archive processing.
        send (function): Used to send Responses.
        recv (function): Used to get commands with their payloads.

    """

    def __init__(self, setup, process, send, recv):
        self.handlers = {
            "starting": Starting(self, setup),
            "processing": Processing(self, process),
        }
        self._send = send
        self._recv = recv
        self._state = "starting"

    def run(self):
        # Let the sender know we're ready.
        self.send(Okay())
        while self._state != "stopping":
            cmd, payload = self.recv()
            result = self.handlers[self._state].run(cmd, payload)
            self.send(result)
        self._state = "stopped"

    def send(self, msg):
        if msg is not None:
            code, payload = msg
            self._send([code, dill.dumps(payload)])

    def recv(self):
        cmd, payload = self._recv()
        return cmd, dill.loads(payload)

    def transition_to(self, state):
        self._state = state


class State:
    def __init__(self, controller, action):
        self._controller = controller
        self._action = action

    def run(self, cmd, payload):
        if cmd == Commands.STOP:
            self.transition_to("stopping")
            return Okay()

        try:
            return self.handle(cmd, payload)
        except Exception:
            self.transition_to("stopping")
            return Error(traceback.format_exc())

    def handle(self, cmd, payload):
        raise NotImplementedError()

    def transition_to(self, state):
        self._controller.transition_to(state)


class Starting(State):
    def handle(self, cmd, payload):
        if cmd == Commands.SETUP:
            self._action(payload)
            self.transition_to("processing")
            return Okay()

        raise Exception(f"Invalid Command.")


class Processing(State):
    def handle(self, cmd, payload):
        if cmd == Commands.PROCESS:
            return Results(self._action(payload))

        raise Exception(f"Invalid Command")
