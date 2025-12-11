#!/bin/bash

docker run -it --privileged -v /dev/bus/usb:/dev/bus/usb -v ./.uhd_images/:/usr/local/share/uhd/images --env UHD_IMAGES_DIR=/usr/local/share/uhd/images -v ./configs/srsran/gnb_uhd.yaml:/gnb.yaml --net host ghcr.io/cueltschey/srsgnb bash -c "gnb -c /gnb.yaml"
