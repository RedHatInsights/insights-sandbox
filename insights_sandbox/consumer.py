#!/usr/bin/env python3
"""
This script is the entrypoint for starting the sandbox. It connects to the
pipes created by the "outside" process and starts the ``Controller`` and
``RunnerAdapter`` that use them.
"""
import argparse
import os
from contextlib import contextmanager

import zmq

from insights_sandbox.controller import Controller
from insights_sandbox.adapter import RunnerAdapter


@contextmanager
def _make_pipes(work_path, results_path):
    ctx = zmq.Context()

    work = ctx.socket(zmq.PULL)
    work.connect(work_path)

    results = ctx.socket(zmq.PUSH)
    results.set_hwm(1)
    results.connect(results_path)

    yield (work, results)

    work.close()
    results.close()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-c", "--comm", default="$PWD")
    return p.parse_args()


def main():
    args = parse_args()

    base = os.path.expandvars(args.comm)
    work_pipe = "ipc://" + os.path.join(base, "work")
    results_pipe = "ipc://" + os.path.join(base, "results")

    with _make_pipes(work_pipe, results_pipe) as (work, results):
        adapter = RunnerAdapter()
        worker = Controller(
            adapter.setup, adapter.process, results.send_multipart, work.recv_multipart
        )
        worker.run()


if __name__ == "__main__":
    main()
