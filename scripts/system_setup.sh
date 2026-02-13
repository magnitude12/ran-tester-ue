#!/bin/bash
set -e

<<<<<<< HEAD
NO_CONFIRM=false

# --- Argument parsing ---
for arg in "$@"; do
  case "$arg" in
    --no-confirm)
      NO_CONFIRM=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--no-confirm]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      exit 1
      ;;
  esac
done

SCRIPT_PATH=$(realpath "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
PROJECT_ROOT_DIR=$(realpath "$SCRIPT_DIR")

if [ "$(basename "$SCRIPT_DIR")" == "scripts" ]; then
  PROJECT_ROOT_DIR=$(realpath "$SCRIPT_DIR/..")
fi
=======
if [ $EUID -ne 0 ]; then
	echo "This script must be run as root"
	exit 1
fi

SCRIPT_PATH=$(realpath $0)
SCRIPT_DIR=$(dirname $SCRIPT_PATH)
PROJECT_ROOT_DIR=$(realpath $SCRIPT_DIR/..)
>>>>>>> fa77f9d6 (Fix issue with URSP images)

echo "Configuring with project root: $PROJECT_ROOT_DIR"

# --- Confirmation ---
if [ "$NO_CONFIRM" = false ]; then
  read -p "Are you sure you want to proceed? (y/N): " confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborting setup"
    exit 0
  fi
else
  echo "Skipping confirmation (--no-confirm)"
fi

echo "Updating DOCKER_SYSTEM_DIRECTORY to ${PROJECT_ROOT_DIR}"
sed -i "s|DOCKER_SYSTEM_DIRECTORY=.*|DOCKER_SYSTEM_DIRECTORY=${PROJECT_ROOT_DIR}|g" "$PROJECT_ROOT_DIR/.env"

# --- Docker check ---
if ! command -v docker &>/dev/null; then
<<<<<<< HEAD
  echo "Docker is not installed!"
  exit 1
=======
  echo "Docker is not installed. Installing now..."

  # Update package list
  apt update

  # Install Docker (Debian/Ubuntu)
  apt install -y docker.io

  # Enable Docker service
  systemctl start docker
  systemctl enable docker

  echo "Docker installation completed."
>>>>>>> fa77f9d6 (Fix issue with URSP images)
else
  echo "Docker is already installed!"
  docker --version
fi

<<<<<<< HEAD
# --- UHD check ---
if ! command -v uhd_images_downloader &>/dev/null; then
  echo "UHD is not installed!"
  exit 1
else
  echo "UHD utils are installed"
  uhd_config_info --version
fi

uhd_images_downloader -i "$PROJECT_ROOT_DIR/.uhd_images"

=======
if ! command -v uhd_images_downloader &>/dev/null; then
	echo "UHD is not installed. Installing now..."
	apt update
	apt install -y uhd-host

	echo "UHD utils are installed."
fi

uhd_images_downloader -i $PROJECT_ROOT_DIR/.uhd_images
>>>>>>> fa77f9d6 (Fix issue with URSP images)
