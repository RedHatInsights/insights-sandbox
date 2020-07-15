Sandbox
=======
Run rules in a sandbox with no network access and filesystem access only to
the archive working directory.


Strategy
--------
- Create a sandbox for the rules using [bubblewrap (bwrap)](https://github.com/containers/bubblewrap).
    - Enable only required linux namespaces (see `man namespaces` for more info).
- Communicate with the sandbox using [zeromq](https://zeromq.org/languages/python/) over named pipes.
    - zmq hides underlying buffer details (`man 7 pipe` for fifos).
    - `work` pipe carries a serialized Broker to the inside process.
    - `results` pipe carries analysis results from the inside process to the outside process.


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
