import time
import sys
import docker
import os
import importlib.util
import inspect
import logging
import subprocess

from influxdb_client import InfluxDBClient, WriteApi


class ComponentManager:
    def __init__(self):

        for worker_thread_file in [f for f in os.listdir("worker_threads") if f.endswith('.py') and f != '__init__.py']:
            module_name = worker_thread_file[:-3]

            file_path = os.path.join("worker_threads", worker_thread_file)

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, obj in vars(module).items():
                if isinstance(obj, type):
                    globals()[name] = obj
                    if name == "WorkerThread":
                        continue
                    logging.info(f"Loaded worker thread module: {name}")

        influxdb_host = os.getenv("DOCKER_INFLUXDB_INIT_HOST")
        influxdb_port = os.getenv("DOCKER_INFLUXDB_INIT_PORT")
        influxdb_org = os.getenv("DOCKER_INFLUXDB_INIT_ORG")
        influxdb_token = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN")

        if not influxdb_host or not influxdb_port or not influxdb_org or not influxdb_token:
            logging.critical("Influxdb environment is not complete! Ensure .env is configured and passed properly")
            sys.exit(1)

        self.influxdb_client = InfluxDBClient(
            f"http://{influxdb_host}:{influxdb_port}",
            org=influxdb_org,
            token=influxdb_token
        )

        self.docker_client = docker.from_env()

        self.process_metadata = []

    def build(self, component):
        docker_image = component.get("docker_image")
        if docker_image is None:
            logging.critical("docker_image required in build_spec")
            sys.exit(1)

        component_name = component.get("component")
        if component_name is None:
            logging.critical("component required in build_spec")
            sys.exit(1)

        try:
            enable_pull = component.get("enable_pull", False)
            if enable_pull:
                logging.info(f"Pulling Docker image: {docker_image}")
                self.docker_client.images.pull(docker_image)
            else:
                logging.info(f"Building Docker image: {docker_image}")
                dockerfile_path = os.path.join("/host/dockerfiles", f"Dockerfile.{component_name}")

                # Check if the Dockerfile exists
                if not os.path.exists(dockerfile_path):
                    raise RuntimeError(f"Dockerfile {dockerfile_path} does not exist")

                # Build the Docker image from the Dockerfile
                logging.info(f"Building Docker image from: {dockerfile_path}")

                # The context for building the image (the parent directory of the Dockerfile)
                build_context = os.path.dirname(dockerfile_path)

                self._run_buildx_build(docker_image, dockerfile_path, build_context)

        except Exception as e:
            raise RuntimeError(f"Error while building component {component['component']}: {str(e)}")

    def build_if_not_exists(self, component):
        docker_image = component.get("docker_image")
        if docker_images is None:
            logging.critical("docker_image required in build_spec")
            sys.exit(1)

        try:
            images = self.docker_client.images.list()
            image_names = [image.tags[0] for image in images if image.tags]
            if docker_image in image_names:
                logging.debug(f"Component {component['component']} already exists. Skipping build.")
            else:
                logging.debug(f"Component {component['component']} does not exist. Building now.")
                self.build(component)

        except Exception as e:
            raise RuntimeError(f"Error while checking/existing component {component['component']}: {str(e)}")

    
    def start(self, process_config):
        if "name" not in process_config.keys():
            logging.critical("name field required for each process")
            sys.exit(1)

        if "component" not in process_config.keys():
            logging.critical("component field required for each process")
            sys.exit(1)

        # config_file is optional for some process types (e.g., oai_ue which uses CLI args only)
        if "config_file" in process_config.keys():
            process_config["config_file"] = os.path.join("/host",process_config["config_file"])
            if not os.path.exists(process_config["config_file"]):
                logging.warning(f"File {process_config['config_file']} not found searching root")
                config_basename = process_config["config_file"].split("/")[-1]
                found = False
                for root, _, files in os.walk("/host"):
                    if config_basename in files:
                        process_config["config_file"] = os.path.join(root, config_basename)
                        logging.info(f"Found config file {process_config['config_file']}")
                        found = True
                        break
                if not found:
                    raise RuntimeError(f"config file {process_config['config_file']} not found")
            process_config["config_file"] = process_config["config_file"].replace("/host", os.getenv("DOCKER_SYSTEM_DIRECTORY"))
            logging.debug(f"Filename on host {process_config['config_file']}")
        else:
            logging.debug(f"Process {process_config['name']} does not require a config file")
            process_config["config_file"] = ""



        if "depends_on" in process_config.keys():
            depends_on_list = list(process_config["depends_on"])
            for dependency in depends_on_list:
                found_dep = False
                for process_data in self.process_metadata:
                    if process_data["name"] == dependency:
                        found_dep = True
                if not found_dep:
                    raise RuntimeError(f"Did not find dependent process '{dependency}' for '{process_config['name']}'")

        if "sleep_ms" in process_config.keys():
            logging.warning(f"Sleeping for {process_config['sleep_ms']/1000.0} seconds")
            sleep_time = float(process_config["sleep_ms"])/1000.0
            time.sleep(sleep_time)

        permissions = []
        if "permissions" in process_config.keys():
            permissions = process_config["permissions"]
        process_config["permissions"] = permissions

        process_class = None
        try:
            process_class = globals()[process_config["component"]]
        except KeyError:
            raise RuntimeError(f"Invalid component {process_config['component']}")

        process_handle = process_class(self.influxdb_client, self.docker_client, process_config)
        process_token = None
        if hasattr(process_handle, "get_token"):
            process_token = process_handle.get_token()

        self.process_metadata.append({
            'id': process_config['name'],
            'type': process_config['component'],
            'config': process_config,
            'handle': process_handle,
            'token': {process_token: permissions}
        })

        process_handle.start()

    def _run_buildx_build(self, docker_image, dockerfile_path, build_context):
        buildx_command = [
            "docker", "buildx", "build",
            "--file", dockerfile_path,
            "--tag", docker_image,
            "--progress", "plain",
            build_context
        ]

        logging.info(f"Running command: {' '.join(buildx_command)}")

        try:
            process = subprocess.Popen(buildx_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            for stdout_line in iter(process.stdout.readline, ""):
                logging.debug(stdout_line.strip())
            for stderr_line in iter(process.stderr.readline, ""):
                logging.debug(stderr_line.strip())

            process.stdout.close()
            process.stderr.close()

            return_code = process.wait()

            if return_code != 0:
                raise RuntimeError(f"Buildx build failed with exit code {return_code}")

            logging.info("Buildx build completed successfully.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Buildx build failed: {e.stderr}")
