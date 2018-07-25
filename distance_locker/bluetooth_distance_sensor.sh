#!/usr/bin/env bash

#Global VARS:
device=$1
btconnected=0
btcurrent=-1
counter=0
notconnected="0"
connected="1"
rssi=-1

#Command loop:
while [ 1 ]; do
    cmdout=$(hcitool rssi $device)
    btcurrent=$(echo $cmdout | grep -c "RSSI return value") 2> /dev/null
    rssi=$(echo $cmdout | sed -e 's/RSSI return value: //g')
    if [ $btcurrent = $notconnected ]; then
        echo "Attempting connection..."
        rfcomm connect 0 $device 1 2> /dev/null >/dev/null &
        sleep 1
    fi
    if [ $btcurrent = $connected ]; then
        echo "Device connected. RSSI: "$rssi
    fi
    if [ $btconnected -ne $btcurrent ]; then
        if [ $btcurrent -eq 0 ]; then
            echo "GONE!"
        fi
        if [ $btcurrent -eq 1 ]; then
            echo "HERE!"
        fi
        btconnected=$btcurrent
    fi
    sleep 1
done
