Sandbox
=======
Run rules in a sandbox with no network access and filesystem access only to
the archive working directory.


Strategy
--------
- Use an outside process to interact with rabbitmq and s3 and an inside process
  to run the rules.
- Create a sandbox for the rules using [bubblewrap (bwrap)](https://github.com/containers/bubblewrap).
    - Enable only required linux namespaces (see `man namespaces` for more info).
    - TODO: Investigate cgroups settings.
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

mkfifo work results
```


Test an archive
------------
```
# this runs forever or until it gets a protocol.DONE message from the producer.
./consumer.sh -p examples.rules

# Run this in a separate terminal.
./producer.py <path to archive> | jq .
```
