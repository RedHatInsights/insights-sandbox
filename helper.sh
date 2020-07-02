#!/usr/bin/bash

. bin/activate
echo `which python3`
echo $PYTHONHOME
python3 consumer.py $@
deactivate
