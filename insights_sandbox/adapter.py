import dill

from insights import dr
from insights.formats._json import JsonFormat

from insights_sandbox.runner import Runner
from insights_sandbox.protocol import Setup, Process, Responses


class RunnerAdapter:
    """
    Provides the setup and process methods used by the ``Controller`` inside
    the sandbox. Extracts options and data out of the raw dictionaries sent
    over the wire and delegates to the underlying ``Runner``.
    """

    def __init__(self):
        self._runner = None

    def setup(self, config):
        self._runner = Runner(
            packages=config.get("packages", []),
            Format=dr.get_component(config["format"])
            if "format" in config
            else JsonFormat,
            include_timings=config.get("include_timings", False),
            include_tracebacks=config.get("include_tracebacks", False),
            target_components=config.get("target_components", []),
            component_config=config.get("component_config", {}),
        )

    def process(self, payload):
        broker = payload["broker"]
        path = payload["path"]
        return self._runner.process(path, broker=broker)


class RunnerAdapterProxy:
    """
    ``RunnerAdapterProxy`` is used by the ``Client`` outside the sandbox to communicate
    with the ``RunnerAdapter`` via the ``Controller`` inside the sandbox.
    """

    def __init__(self, send, recv):
        self.__send = send
        self.__recv = recv

    def setup(self, config):
        self._await_okay()
        self._send(Setup(config))
        self._await_okay()

    def process(self, path, broker=None):
        broker = broker if broker is None else dr.Broker()

        payload = {"broker": broker, "path": path}
        self._send(Process(payload))
        (code, result) = self._recv()

        if code == Responses.ERROR:
            raise Exception(result)
        return result

    def _send(self, payload):
        cmd, payload = payload
        return self.__send([cmd, dill.dumps(payload)])

    def _recv(self):
        cmd, payload = self.__recv()
        return (cmd, dill.loads(payload))

    def _await_okay(self):
        code, result = self._recv()
        if code != Responses.OKAY:
            raise Exception(result)
