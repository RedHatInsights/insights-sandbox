#!/usr/bin/python3
import os
import zmq


MSG = b"\x00"
DONE = b"\x01"

ctx = zmq.Context()
work = ctx.socket(zmq.PUSH)

# set the max queue size or "high water mark" in terms of sent messages (not
# bytes, etc.) ipc connections block by default.
work.set_hwm(2)

work_path = os.path.expandvars("ipc://$PWD/work")
print(work_path)
work.bind(work_path)

results = ctx.socket(zmq.PULL)

results_path = os.path.expandvars("ipc://$PWD/results")
print(results_path)
results.bind(results_path)


# fifos have a default buffer size of 64k, but zmq abstracts over that for us.
task = "a" * 12800000
for r in range(10):
    print(f"Send: {len(task)}")
    work.send_multipart([MSG, task.encode("utf-8")])
    payload = results.recv().decode("utf-8")

work.send_multipart([DONE, b""])
work.close()
results.close()
