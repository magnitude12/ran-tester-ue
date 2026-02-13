#!/bin/bash
set -e

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

# --- UHD check ---
if ! command -v uhd_images_downloader &>/dev/null; then
  echo "UHD is not installed!"
  exit 1
else
  echo "UHD utils are installed"
  uhd_config_info --version
fi

uhd_images_downloader -i "$PROJECT_ROOT_DIR/.uhd_images"
