from worker_thread import WorkerThread
import os

class oai_ue(WorkerThread):
    def __init__(self, influxdb_client, docker_client, process_config):
        # OAI UE doesn't require a conf file so optional
        if "config_file" not in process_config:
            process_config["config_file"] = ""
        super().__init__(influxdb_client, docker_client, process_config)
    
    def start(self):
        self.config.image_name = "ghcr.io/oran-testing/oai_ue"
        self.cleanup_old_containers()
        
        # First populate default env (sets ARGS to joined cli flags)
        self.setup_env()

        # Ensure ARGS begins with the binary, not a dash option
        # so the entrypoint executes the full command correctly.
        oai_command = "/opt/openairinterface5g/cmake_targets/ran_build/build/nr-uesoftmodem"
        if self.config.cli_args:
            args_str = " ".join(self.config.cli_args)
            self.config.container_env["ARGS"] = f"{oai_command} {args_str}"
        else:
            self.config.container_env["ARGS"] = oai_command
        self.config.host_network = True
        
        # Volumes for B200 RF are handled in base setup_volumes()
        # (adds /dev/bus/usb and images_dir). No extra mounts here to
        # avoid duplicate mount points.
        
        self.setup_volumes()
        self.start_container()
