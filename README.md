Sandbox
=======
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

The client creates an `RunnerAdapterProxy` and configures it with `zmq`
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
pip install insights-core dill pyzmq

```


Test an archive
------------
```
./driver.py -p examples.rules <archive>
```
