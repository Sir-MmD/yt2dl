#!/bin/bash
while true
do
    if ! pgrep -f "python3 p.py" > /dev/null
    then
        cd /root/
        exec python3 p.py &
    fi
    sleep 1
done
