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
    - TODO: Investigate user and cgroups settings.
- Communicate with the sandbox using [zeromq](https://zeromq.org/languages/python/) over named pipes.
    - zmq hides underlying buffer details (`man 7 pipe` for fifos).
    - `work` pipe carries local paths to archives from the outside process to
      the inside process.
    - `results` pipe carries analysis results from the inside process to the
      outside process.


Installation
------------
```
sudo dnf install bwrap
python3 -m venv .
. bin/activate
pip install pyzmq
mkfifo work results
```


Run the test
------------
```
./producer.py &
./bubblewrap.sh
```
