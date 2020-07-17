Insights Sandbox
================
Run rules with access only to necessary binaries and the archive working
directory.


Strategy
--------
- Create a sandbox using [bubblewrap (bwrap)](https://github.com/containers/bubblewrap).
    - Enable only required linux namespaces (see `man namespaces` for more info).
- Communicate with the sandbox using [zeromq](https://zeromq.org/languages/python/) over named pipes.
    - zmq hides underlying buffer details (`man 7 pipe` for fifos).


Architecture
------------
```
Client <-> runner adapter proxy <-> named pipes <-> [controller <-> runner adapter <-> runner]
```

The `Client` creates named pipes and a child process that uses `bwrap` to
invoke `insights_sandbox.consumer`.

The client creates a `RunnerAdapterProxy` and configures it with `zmq`
functions for sending and recieving messages over the pipes. The proxy is
used to setup the `Runner` via the `Controller` and `RunnerAdapter`.


Installation
------------
```
CentOS 7:
yum install epel-release
yum install bubblewrap

Fedora:
dnf install epel-release
dnf install bubblewrap

Both:
python3 -m venv .
. bin/activate
pip install -e .[develop]

```


Test an archive
------------
```
./driver.py -p examples.rules <archive>
```

Example Code
------------
```python
#!/usr/bin/env python3
"""
This script is only for testing the sandbox.
"""
import argparse

from insights import dr, parse_plugins
from insights_sandbox.client import Client


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--plugins", "-p", help="plugins to load", default="")
    p.add_argument("archive", help="pass an archive to analyze.")
    return p.parse_args()


def main():
    args = parse_args()
    broker = dr.Broker()
    packages = parse_plugins(args.plugins)
    with Client(packages=packages) as client:
        doc = client.process(args.archive, broker=broker)
        print(doc["results"].decode("utf-8"))


if __name__ == "__main__":
    main()
```