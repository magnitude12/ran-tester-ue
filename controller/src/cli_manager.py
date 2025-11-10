from globals import Globals
import logging
import sys


HELP_STR="""
Available commands:
  help - show this message
  exit - quit program
  list - list running components
  stop <idx | all> - stop a component
  start <idx | all> - start a component
  restart <idx | all> - stop, then start a component
"""


class CLIManager:
    def __init__(self, yaml_config):
        logging.info("CLI commands are enabled, starting CLI thread...")
        self.yaml_config = yaml_config

    def handle_shutdown(self):
        logging.info("Shutting down controller...")
        for i in range(len(Globals.thread_manager.process_metadata)):
            logging.info(f"Stopping {Globals.thread_manager.process_metadata[i]}")
            Globals.thread_manager.stop(Globals.thread_manager.process_metadata[i])
        Globals.thread_manager.process_metadata = []
        logging.info("Controller exited with code: 0")
        sys.exit(0)

    def list_components(self):
        for i in range(len(Globals.thread_manager.process_metadata)):
            logging.info(f"Process {i}: {Globals.thread_manager.process_metadata[i]}")

    def start_all_components(self):
        threads_config = self.yaml_config.get("run_spec", [])
        for t in threads_config:
            if t.get("target", False):
                Globals.thread_manager.start_external(t)
                continue
            Globals.thread_manager.start(t)

    def start_component(self):
        threads_config = self.yaml_config.get("run_spec", [])
        if idx < 0 or idx >= len(threads_config):
            print("Index to start out of bounds")
            return

        if threads_config[i].get("target", False):
            Globals.thread_manager.start_external(threads_config[i])
            return
        Globals.thread_manager.start(threads_config[i])

    def stop_all_components(self):
        for i in range(len(Globals.thread_manager.process_metadata)):
            logging.info(f"Stopping {Globals.thread_manager.process_metadata[i]}")
            Globals.thread_manager.stop(Globals.thread_manager.process_metadata[i])
        Globals.thread_manager.process_metadata = []

    def stop_component(self, idx):
        Globals.thread_manager.stop(Globals.thread_manager.process_metadata[idx])
        del Globals.thread_manager.process_metadata[idx]

    def cli_loop(self):
        while True:
            try:
                self.process_cmd(input("> ").strip().lower())
            except (EOFError, KeyboardInterrupt):
                self.handle_shutdown()

    def process_cmd(self, cmd):
        if cmd in ("exit", "quit"):
            self.handle_shutdown()

        elif cmd == "help":
            print(HELP_STR)

        elif cmd in ("list", "ls"):
            self.list_components()

        elif cmd.startswith("stop"):
            args = cmd.split(" ")
            if len(args) > 1:
                print("Usage: stop <process index or 'all'>")
                return
            process_idx = args[1]
            if process_idx == "all":
                self.stop_all_components()
                return

            try:
                process_idx = int(process_idx)
            except:
                print("must supply valid integer index")

            self.stop_component(process_idx)

        elif cmd.startswith("restart"):
            args = cmd.split(" ")
            if len(args) > 1:
                print("Usage: stop <process index or 'all'>")
                return
            process_idx = args[1]
            if process_idx == "all":
                self.stop_all_components()
                self.start_all_components()
                return

            try:
                process_idx = int(process_idx)
            except:
                print("must supply valid integer index")

            self.stop_component(process_idx)
            self.start_component(process_idx)


        elif cmd.startswith("start"):
            args = cmd.split(" ")
            if len(args) > 1:
                print("Usage: stop <process index or 'all'>")
                return
            process_idx = args[1]
            if process_idx == "all":
                self.start_all_components()
                return

            try:
                process_idx = int(process_idx)
            except:
                print("must supply valid integer index")

            self.start_component(process_idx)
            pass
        else:
            print(f"Unknown command: {cmd}")
