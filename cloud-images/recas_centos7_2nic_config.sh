#!/bin/bash

# Log file
LOGFILE='/var/log/recas-netconfig.log'

touch $LOGFILE

echo 'Test cloud init' > $LOGFILE


cat /etc/sysconfig/network-scripts/ifcfg-eth0 >> $LOGFILE
cat /etc/sysconfig/network-scripts/ifcfg-eth1 >> $LOGFILE
