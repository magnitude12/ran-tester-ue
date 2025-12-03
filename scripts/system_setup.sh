#!/bin/bash

SCRIPT_PATH=$(realpath $0)
SCRIPT_DIR=$(dirname $SCRIPT_PATH)
PROJECT_ROOT_DIR=$(realpath $SCRIPT_DIR)

if [ $(basename $SCRIPT_DIR) == "scripts" ]; then
	PROJECT_ROOT_DIR=$(realpath $SCRIPT_DIR/..)
fi

echo "Configuring with project root: $PROJECT_ROOT_DIR"

read -p "Are you sure you want to proceed? (y/N): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborting setup"
  exit 0
fi

echo "Updating DOCKER_SYSTEM_DIRECTORY to ${PROJECT_ROOT_DIR}"
sed -i "s|DOCKER_SYSTEM_DIRECTORY=.*|DOCKER_SYSTEM_DIRECTORY=${PROJECT_ROOT_DIR}|g" $PROJECT_ROOT_DIR/.env

if ! command -v docker &>/dev/null; then
  echo "Docker is not installed!"
	exit 1
else
  echo "Docker is already installed!"
  docker --version
fi

if ! command -v uhd_images_downloader &>/dev/null; then
	echo "UHD is not installed!"
	exit 1
else
	echo "UHD utils are installed"
	uhd_config_info --version
fi

uhd_images_downloader -i $PROJECT_ROOT_DIR/.uhd_images
