#!/usr/bin/python3

import os
import http
import sys
import argparse
import pathlib
import yaml
import logging
import colorlog

from datetime import datetime, timezone


from control_handler import SystemControlHandler
from component_manager import ComponentManager

from globals import Globals

def configure():
    """
    Reads in CLI arguments
    Configures log level with colored output
    Returns YAML config
    """
    script_dir = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="RAN tester UE process controller")
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        required=True,
        help="Path of YAML config for the controller")
    parser.add_argument("--log-level",
                        default="DEBUG",
                        help="Set the logging level. Options: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    args = parser.parse_args()
    log_level = getattr(logging, args.log_level.upper(), 1)

    if not isinstance(log_level, int):
        raise ValueError(f"Invalid log level: {args.log_level}")

    console_handler = logging.StreamHandler()

    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)-8s%(reset)s - %(message)s', 
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    console_handler.setFormatter(color_formatter)

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(console_handler)

    yaml_options = None
    with open(str(args.config), 'r') as file:
        yaml_options = yaml.safe_load(file)

    if yaml_options is None:
        logging.critical("YAML parsing failed")
        sys.exit(1)

    return yaml_options

def start_server():
    if os.geteuid() != 0:
        logging.critical("User must be root")
        sys.exit(1) 

    control_ip = os.getenv("DOCKER_CONTROLLER_API_IP", None)
    if not control_ip:
        logging.critical("environment variable DOCKER_CONTROLLER_API_IP not set")
        sys.exit(1)

    control_port = os.getenv("DOCKER_CONTROLLER_API_PORT", None)
    if not control_port:
        logging.critical("environment variable DOCKER_CONTROLLER_API_PORT not set")
        sys.exit(1)
    try:
        control_port = int(control_port)
    except RuntimeError:
        logging.critical("DOCKER_CONTROLLER_API_PORT is not a valid integer")
        sys.exit(1)

    logging.info(f"Starting control server at: http://{control_ip}:{control_port}")
    server = http.server.HTTPServer((control_ip, control_port), SystemControlHandler)

    server.serve_forever()


if __name__ == '__main__':
    Globals.controller_init_time = f"{datetime.now().astimezone(timezone.utc)
        .isoformat().replace("+00:00", "Z")}"

    yaml_config = configure()

    force_build = yaml_config.get("force_build", False)

    build_config = yaml_config.get("build_spec", None)
    if build_config is None:
        logging.critical("No components supplied in YAML config")
        sys.exit(1)

    threads_config = yaml_config.get("run_spec", None)
    if threads_config is None:
        logging.critical("No processes supplied in YAML config")
        sys.exit(1)

    Globals.thread_manager = ComponentManager()

    for b in build_config:
        if force_build:
            Globals.thread_manager.build(b)
        else:
            Globals.thread_manager.build_if_not_exists(b)

    for t in threads_config:
        Globals.thread_manager.start(t)

    start_server()

