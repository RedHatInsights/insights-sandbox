import logging
import os
import subprocess
import tempfile

import dill
import zmq

from insights import dr
from insights.core.archives import extract

from sandbox.protocol import Setup, Process, Responses

log = logging.getLogger(__name__)


def _make_pipes(work_path, results_path, hwm=2):
    ctx = zmq.Context()
    # set the max queue size or "high water mark" in terms of sent messages
    # (not bytes, etc.) ipc connections block by default.
    work = ctx.socket(zmq.PUSH)
    work.set_hwm(hwm)
    work_path = "ipc://" + work_path
    work.bind(work_path)

    results_path = "ipc://" + results_path
    results_path = os.path.expandvars(results_path)
    results = ctx.socket(zmq.PULL)
    results.bind(results_path)

    return work, results


class Client:

    _worker_command = """
    #!/usr/bin/env bash
    set -euo pipefail
    (exec bwrap --ro-bind /usr /usr \\
                --symlink usr/lib /lib \\
                --symlink usr/lib64 /lib64 \\
                --symlink usr/bin /bin \\
                --symlink usr/sbin /sbin \\
                --dev /dev \\
                --bind $VIRTUAL_ENV $VIRTUAL_ENV \\
                --bind ${INSIGHTS_TMP_PATH:-/tmp} /tmp \\
                --bind ${INSIGHTS_COMM_PATH:-/tmp} ${INSIGHTS_COMM_PATH:-/tmp} \\
                --bind $PWD $PWD \\
                --chdir $PWD \\
                --unshare-ipc \\
                --unshare-net \\
                --unshare-uts \\
                --unshare-user \\
                --die-with-parent \\
                python3 -m sandbox.consumer -c ${INSIGHTS_COMM_PATH:-/tmp})
    """.strip()

    def __init__(
        self,
        packages=None,
        component_config=None,
        target_components=None,
        include_timings=False,
        include_tracebacks=False,
        tmp_dir=None,
        comm_dir=None,
        format=None,
    ):
        comm_base = os.path.expandvars(comm_dir) if comm_dir else None
        self._comm_temp_dir = tempfile.TemporaryDirectory(dir=comm_base)
        comm_path = self._comm_temp_dir.name

        work_path = os.path.join(comm_path, "work")
        results_path = os.path.join(comm_path, "results")

        os.mkfifo(work_path)
        os.mkfifo(results_path)

        self._work, self._results = _make_pipes(work_path, results_path)

        self._config = {
            "packages": packages or [],
            "format": format or "insights.formats._json.JsonFormat",
            "include_timings": include_timings,
            "include_tracebacks": include_tracebacks,
            "target_components": target_components or [],
            "component_config": component_config or {},
        }

        self._env = {
            "PATH": os.environ.get("PATH"),
            "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
            "INSIGHTS_TMP_PATH": tmp_dir or tempfile.gettempdir(),
            "INSIGHTS_COMM_PATH": comm_path,
        }

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def start(self):
        # start the remote process
        self._worker = subprocess.Popen(
            self._worker_command,
            shell=True,
            env=self._env,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        # wait for acknowledgement
        self._get_okay()

        self.send(Setup(self._config))
        self._get_okay()

    def send(self, payload):
        cmd, payload = payload
        return self._work.send_multipart([cmd, dill.dumps(payload)])

    def recv(self):
        cmd, payload = self._results.recv_multipart()
        return (cmd, dill.loads(payload))

    def _get_okay(self):
        code, result = self.recv()
        if code != Responses.OKAY:
            raise Exception(result)

    def process(self, path, broker=None):
        broker = broker if broker is None else dr.Broker()

        def do_work(p):
            payload = {"broker": broker, "path": p}
            self.send(Process(payload))
            (code, result) = self.recv()

            if code == Responses.ERROR:
                raise Exception(result)
            return result

        if os.path.isdir(path):
            return do_work(path)
        else:
            with extract(path) as extraction:
                return do_work(extraction.tmp_dir)

    def close(self):
        for f in [
            self._worker.terminate,
            self._worker.wait,
            self._work.close,
            self._results.close,
            self._comm_temp_dir.cleanup,
        ]:
            try:
                f()
            except Exception as ex:
                log.exception(ex)
