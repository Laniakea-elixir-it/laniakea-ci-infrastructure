#!/bin/bash

# Log file
LOGFILE='/var/log/recas-netconfig.log'

#________________________________
# Check for private IP
function find_private_nic(){

  # If the private interface is on use this command to determine its name
  PRIVATE_IFACE_NAME=$(ip a | grep -E '172.30.[0-9]{1,3}' -B 2 | head -1 | awk -F\: '{print $2}' | sed "s/^ //")

  # Exit if the variable is unset or empty
  if [ -z "$PRIVATE_IFACE_NAME" ]
  then
    echo "The private network is not set" >> $LOGFILE
    return 1
  fi

  PRIVATE_IFCFG_FILE=/etc/sysconfig/network-scripts/ifcfg-$PRIVATE_IFACE_NAME
  echo 'METRIC=300' >> $PRIVATE_IFCFG_FILE

  true

}

#________________________________
# Check for public IP
function find_public_nic(){

  # If the public interface is on use this command to determine its name
  PUBLIC_IFACE_NAME=$(ip a | grep -E '90.147.[0-9]{1,3}|212.189.[0-9]{1,3}' -B 2 | head -1 | awk -F\: '{print $2}' | sed "s/^ //")

  # Exit if the variable is unset or empty
  if [ -z "$PUBLIC_IFACE_NAME" ]
  then
    echo "The public network is not set" >> $LOGFILE
    return 1
  fi

  # Set public network configuration file
  PUBLIC_IFCFG_FILE=/etc/sysconfig/network-scripts/ifcfg-$PUBLIC_IFACE_NAME

  true

}


#________________________________
#________________________________
# Main script

# Check if the number of network interfaces is not two and decide how to behave
if [[ $(ls -A /sys/class/net | wc -l)  == 3 ]]
then

  if find_private_nic; then
    systemctl restart network
    exit 0
  fi

  if find_public_nic
  then
    echo $PUBLIC_IFACE_NAME

    # Check if eth1 is present
    if [ $PUBLIC_IFACE_NAME == "eth0" ]; then
      # trova l'altra rete che sara eth + qualcosa
      # controlla se il file di configurazione esiste
      # se esiste aggiungi metrica e riavvia
      PRIVATE_IFACE_NAME="eth1"
    elif [ $PUBLIC_IFACE_NAME == "eth1" ]; then
      PRIVATE_IFACE_NAME="eth0"
    fi

    PRIVATE_IFCFG_FILE=/etc/sysconfig/network-scripts/ifcfg-$PRIVATE_IFACE_NAME
    echo 'METRIC=300' >> $PRIVATE_IFCFG_FILE
    systemctl restart network
    exit 0

  fi

fi
