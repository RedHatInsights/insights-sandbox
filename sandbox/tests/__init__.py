import dill
from collections import deque


class IO:
    def __init__(self, inbuf):
        self.inbuf = deque(inbuf)
        self.output = []

    def recv(self):
        cmd, payload = self.inbuf.popleft()
        return (cmd, dill.dumps(payload))

    def send(self, payload):
        self.output.append(payload)
