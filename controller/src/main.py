#!/usr/bin/python3

import time
import os
import http
import sys
import argparse
import pathlib
import yaml
import logging
import colorlog
import uuid
import threading

from datetime import datetime, timezone


from control_handler import SystemControlHandler
from component_manager import ComponentManager
from cli_manager import CLIManager
from api_interface import ApiInterface

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
    server = http.server.HTTPServer(("0.0.0.0", 1343), SystemControlHandler)
    logging.info("Starting control server at: http://controller:1343")

    server.serve_forever()



if __name__ == '__main__':
    if os.geteuid() != 0:
        logging.critical("User must be root")
        sys.exit(1) 

    Globals.controller_init_time = f"{datetime.now().astimezone(timezone.utc)
        .isoformat().replace("+00:00", "Z")}"

    yaml_config = configure()

    for target_config in yaml_config.get("external_targets", []):
        target_name = target_config.get("name", None)
        target_host = target_config.get("host", None)
        target_token = target_config.get("token", None)
        target_port = target_config.get("port", None)
        if target_name is None or target_host is None or target_token is None or not isinstance(target_port, int):
            logging.warning("Skipping external target due to insufficient configuration")
            continue
        Globals.target_managers[target_name] = ApiInterface(target_host, target_port, target_token)

    Globals.api_auth = yaml_config.get("api_auth", [])
    for i in range(len(Globals.api_auth)):
        if Globals.api_auth[i].get("token") is None:
            Globals.api_auth[i]["token"] = uuid.uuid4()

    external_influx_config = yaml_config.get("external_influx", None)
    Globals.thread_manager = ComponentManager(external_influx_config)

    build_config = yaml_config.get("build_spec", [])
    threads_config = yaml_config.get("run_spec", [])

    for b in build_config:
        if b.get("force_rebuild", False):
            Globals.thread_manager.build(b)
        else:
            Globals.thread_manager.build_if_not_exists(b)

    if yaml_config.get("autorun", True):
        for t in threads_config:
            if t.get("target", False):
                Globals.thread_manager.start_external(t)
                continue
            Globals.thread_manager.start(t)

    if yaml_config.get("enable_cli", False):
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        time.sleep(1)
        cli_manager = CLIManager(yaml_config)
        cli_manager.cli_loop()
    else:
        start_server()
