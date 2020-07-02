#!/usr/bin/env python3
import argparse
import os

from contextlib import contextmanager

import dill
import zmq

from insights import dr
from insights.core.archives import extract
from insights.core.hydration import create_context

from protocol import DONE, MSG


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("archive")
    return p.parse_args()


@contextmanager
def make_pipes():
    ctx = zmq.Context()
    # set the max queue size or "high water mark" in terms of sent messages
    # (not bytes, etc.) ipc connections block by default.
    work_path = os.path.expandvars("ipc://$PWD/work")
    work = ctx.socket(zmq.PUSH)
    work.set_hwm(2)
    work.bind(work_path)

    results_path = os.path.expandvars("ipc://$PWD/results")
    results = ctx.socket(zmq.PULL)
    results.bind(results_path)

    yield (work, results)

    work.close()
    results.close()


# fifos have a default buffer size of 64k, but zmq abstracts over that for us.
def main():
    args = parse_args()

    with make_pipes() as (work, results):
        with extract(args.archive) as extraction:
            broker = dr.Broker()
            ctx = create_context(extraction.tmp_dir)
            broker[ctx.__class__] = ctx

            work.send_multipart([MSG, dill.dumps(broker)])
            payload = results.recv().decode("utf-8")
            print(payload)

            # work.send_multipart([DONE, b""])


if __name__ == "__main__":
    main()
