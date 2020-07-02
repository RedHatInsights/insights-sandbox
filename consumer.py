import argparse
import os
from contextlib import contextmanager
from io import StringIO

import dill
import zmq

from insights import dr, load_default_plugins, parse_plugins, load_packages
from insights.formats._json import JsonFormat

from protocol import DONE


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--plugins", default="")
    return p.parse_args()


@contextmanager
def make_pipes():
    ctx = zmq.Context()

    work = ctx.socket(zmq.PULL)
    work_path = os.path.expandvars("ipc://$PWD/work")
    work.connect(work_path)

    # set the max queue size or "high water mark" in terms of sent messages
    # (not bytes, etc.) ipc connections block by default.
    results_path = os.path.expandvars("ipc://$PWD/results")
    results = ctx.socket(zmq.PUSH)
    results.set_hwm(2)
    results.connect(results_path)

    yield (work, results)

    work.close()
    results.close()


def process(work, results):
    while True:
        (cmd, payload) = work.recv_multipart()
        if cmd == DONE:
            break
        broker = dill.loads(payload)
        output = StringIO()
        with JsonFormat(broker, stream=output):
            dr.run(broker=broker)
        output.seek(0)
        payload = output.read().encode("utf-8")
        results.send(payload)


def main():
    args = parse_args()
    load_default_plugins()
    load_packages(parse_plugins(args.plugins))

    with make_pipes() as (work, results):
        process(work, results)


if __name__ == "__main__":
    main()
