#!bin/python
import os
import zmq


MSG = b"\x00"
DONE = b"\x01"

ctx = zmq.Context()
print("Connecting work.")
work = ctx.socket(zmq.PULL)

work_path = os.path.expandvars("ipc://$PWD/work")
print(work_path)

work.connect(work_path)

results = ctx.socket(zmq.PUSH)

# set the max queue size or "high water mark" in terms of sent messages (not
# bytes, etc.) ipc connections block by default.
results.set_hwm(2)

results_path = os.path.expandvars("ipc://$PWD/results")
print(results_path)
print("Connecting results.")
results.connect(results_path)

while True:
    print("Receiving.")
    (cmd, payload) = work.recv_multipart()
    if cmd == DONE:
        break
    print(f"Recv: {len(payload)}")
    results.send(payload)


work.close()
results.close()
