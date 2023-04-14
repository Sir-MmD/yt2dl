#!/bin/bash
while true
do
    if ! pgrep -f "python3 yt2dl_en.py" > /dev/null
    then
        cd /root/yt2dl
        exec python3 yt2dl_en.py &
    fi
    sleep 1
done
