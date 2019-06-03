#!/usr/bin/env bash

#Global VARS:
device=$1  # Bluetooth mac address
btconnected=0
btcurrent=-1
counter=0
notconnected="0"
connected="1"
rssi=-1

#Linux applications
#1. hcitool - Bluetooth linux driver cli app
#             For getting RSSI readings
#2. rfcomm  - RF communication linux cli app
#             For connecting with mac address
#Command loop:
while [ 1 ]; do
    # Trying to get RSSI signal from Bluetooth
    cmdout=$(hcitool rssi $device)
    btcurrent=$(echo $cmdout | grep -c "RSSI return value") 2> /dev/null
    rssi=$(echo $cmdout | sed -e 's/RSSI return value: //g')

    if [ $btcurrent = $notconnected ]; then
        # Trying to connect to the Bluetooth mac address
        echo "Attempting connection..."
        rfcomm connect 0 $device 1 2> /dev/null >/dev/null &
        sleep 1
    fi

    if [ $btcurrent = $connected ]; then
        # print to STDOUT RSSI signal
        echo "Device connected. RSSI: "$rssi
    fi

    if [ $btconnected -ne $btcurrent ]; then
        if [ $btcurrent -eq 0 ]; then
            # print to STDOUT No Connection
            echo "GONE!"
        fi
        if [ $btcurrent -eq 1 ]; then
            # print to STDOUT have Connection
            echo "HERE!"
        fi
        btconnected=$btcurrent
    fi
    sleep 1
done
