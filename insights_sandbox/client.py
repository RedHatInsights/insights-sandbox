"""
A ``Client`` creates a sandboxed process using bubblewrap and
communicates with it to evaluate insights components against archives.
This approach allows execution of standard python in a controlled
environment.
"""
import logging
import os
import subprocess
import tempfile

import zmq

from insights.core.archives import extract
from insights_sandbox.adapter import RunnerAdapterProxy

log = logging.getLogger(__name__)


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
                --ro-bind $VIRTUAL_ENV $VIRTUAL_ENV \\
                --ro-bind ${INSIGHTS_COMM_PATH:-/tmp} ${INSIGHTS_COMM_PATH:-/tmp} \\
                --ro-bind $PWD $PWD \\
                --ro-bind ${INSIGHTS_TMP_PATH:-/tmp} /tmp \\
                --chdir $PWD \\
                --unshare-ipc \\
                --unshare-net \\
                --unshare-uts \\
                --unshare-user \\
                --die-with-parent \\
                python3 -m insights_sandbox.consumer -c ${INSIGHTS_COMM_PATH:-/tmp})
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
        """
        Sets up communication channels and the sandbox process to use for
        evaluation. If a ``Client`` is created as a context manager,
        resources are cleaned up automatically. Otherwise, you must call
        ``Client.close()``.

        Arguments:
            packages (List str): A list of package names to load.
            component_config (dict): A dictionary for configuring insights
                components.
            target_components (list): A list of fully qualified component
                names to execute.
            include_timings (bool): whether results should include component
                timings.
            include_tracebacks (bool): whether results should include all
                tracebacks encountered.
            tmp_dir (str): The temporary directory to use for extracting
                archives.
            comm_dir (str): The directory to use for creating named pipes
                used for communication with the sandbox.
            format (str): The fully qualified name of the Format class to use
                when formatting results.
        """

        comm_base = os.path.expandvars(comm_dir) if comm_dir else None
        self._comm_temp_dir = tempfile.TemporaryDirectory(dir=comm_base)
        comm_path = self._comm_temp_dir.name

        work_path = os.path.join(comm_path, "work")
        results_path = os.path.join(comm_path, "results")

        os.mkfifo(work_path)
        os.mkfifo(results_path)

        self._work, self._results = self._make_pipes(
            "ipc://" + work_path, "ipc://" + results_path
        )

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

        self._start()

    def process(self, path, broker=None):
        """
        Use this method to process archives. Pass a path to an archive and an
        optional seed broker to use when evaluating it.

        Archives are extracted outside the sandbox, and the temporary path is
        sent inside for processing.

        Arguments:
            path (str): Path to an archive or directory to analyze.
                Directories must be inside the temporary directory so the
                sandbox can see them.
            broker (insights.core.dr.Broker): Seed broker to use during the
                evaluation. Observers registered with the seed broker won't
                be fired since it is serialized into the sandbox before
                evaluation.
        """
        if os.path.isdir(path):
            return self._runner_adapter_proxy.process(path, broker=broker)
        else:
            with extract(path) as extraction:
                p = extraction.tmp_dir
                return self._runner_adapter_proxy.process(p, broker=broker)

    def close(self):
        """
        Shuts down the sandbox and cleans up the resources used for
        communication and archive work.
        """
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

    def _make_pipes(self, work_path, results_path):
        ctx = zmq.Context()

        results = ctx.socket(zmq.PULL)
        results.bind(results_path)

        work = ctx.socket(zmq.PUSH)
        work.set_hwm(1)
        work.bind(work_path)

        return work, results

    def _start(self):
        self._worker = subprocess.Popen(
            self._worker_command,
            shell=True,
            env=self._env,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        self._runner_adapter_proxy = RunnerAdapterProxy(
            self._work.send_multipart, self._results.recv_multipart
        )
        self._runner_adapter_proxy.setup(self._config)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
