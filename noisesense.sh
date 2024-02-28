#!/bin/sh

# make : /etc/systemd/system/noisesense.service
# exec : sudo systemctl enable noisesense.service

python3 /home/pi/doc/private/python/noise/noisesense.py 2
