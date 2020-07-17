#!/usr/bin/env python3
import argparse
import os

from contextlib import contextmanager

import zmq

from sandbox.controller import Controller
from sandbox.engine import EngineAdapter


@contextmanager
def make_pipes(work_path, results_path):
    ctx = zmq.Context()

    work = ctx.socket(zmq.PULL)
    work_path = "ipc://" + os.path.expandvars(work_path)
    work.connect(work_path)

    # set the max queue size or "high water mark" in terms of sent messages
    # (not bytes, etc.) ipc connections block by default.
    results_path = "ipc://" + os.path.expandvars(results_path)
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
    work_pipe = os.path.join(base, "work")
    results_pipe = os.path.join(base, "results")

    with make_pipes(work_pipe, results_pipe) as (work, results):
        adapter = EngineAdapter()
        worker = Controller(
            adapter.setup, adapter.process, results.send_multipart, work.recv_multipart
        )
        worker.run()


if __name__ == "__main__":
    main()
