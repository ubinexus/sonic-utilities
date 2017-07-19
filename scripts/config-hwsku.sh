#!/bin/bash

# The command line help
display_help() {
    echo "Usage: $0 [-h] [-p] [-s HWSKU]" >&2
    echo
    echo "   -h, --help           print this usage page"
    echo "   -p, --print          print the current HWSKU"
    echo "   -s, --set            set the HWSKU"
    exit 0
}

HWSKU_ROOT='/usr/share/sonic/device/'
platform=`sonic-cfggen -m /etc/sonic/minigraph.xml -y /etc/sonic/sonic_version.yml -v platform`
current_hwsku=`sonic-cfggen -m /etc/sonic/minigraph.xml -y /etc/sonic/sonic_version.yml -v minigraph_hwsku`
RUNNING_PATH='/etc/sonic/'

config_hwsku_exec() {
    config_hwsku=$1
    while true; do
        read -p "This will change the port mode of the box and reboot it. [Y/N] " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) echo "no changes were made"; exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done

    printf -v hwsku_minigraph "%s%s%s%s%s" $HWSKU_ROOT $platform '/' $config_hwsku '/' "minigraph.xml"
    target_minigraph=$RUNNING_PATH
    target_minigraph+="minigraph.xml"

    #echo $hwsku_minigraph " to "  $target_minigraph
    cp $hwsku_minigraph $target_minigraph

    docker stop syncd >/dev/null
    docker stop swss >/dev/null
    docker rm syncd >/dev/null
    docker rm swss >/dev/null
    echo "rebooting the box..."
    reboot
}

config_hwsku_fun() {

    config_hwsku=$1
    # Check root privileges
    if [ "$EUID" -ne 0 ]
    then
      echo "Please run as root"
      exit
    fi

    if [ "$config_hwsku" == "$current_hwsku" ]; then
        echo "The HWSKU configured is current, no changes were made"
        exit
    fi

    # Check the available HWSKUs
    platform_dir=$HWSKU_ROOT$platform
    dirs=`ls -l $platform_dir | egrep '^d' | awk '{print $9}' | grep -v plugins | grep -v led-code`
    
    for dir in $dirs
    do
	if [ $config_hwsku == $dir ]; then
	    config_hwsku_exec "$config_hwsku"
	    exit
	fi
    done

    # Not matching any HWSKU names, print error
    printf "Please use one of the options:\n"
    printf "%s\n" $dirs
    exit 1
}

case "$1" in
-h | --help)
    display_help
    ;;
-p | --print)
    echo $current_hwsku
    ;;
-s | --set)
    config_hwsku=$2
    config_hwsku_fun "$config_hwsku"
    ;;
*)
    echo "Please use options as following:" >&2
    display_help
    ;;
esac
