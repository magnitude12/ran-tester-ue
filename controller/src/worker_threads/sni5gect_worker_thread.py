from worker_thread import WorkerThread

class sni5gect(WorkerThread):
    def start(self):
        self.config.image_name = "ghcr.io/oran-testing/sni5gect"
        self.cleanup_old_containers()
        self.setup_env()
        self.setup_networks()
        self.config.container_volumes[self.config.config_file] = {"bind": "/sni5gect.yaml", "mode": "ro"}
        self.setup_volumes()

        self.start_container()



