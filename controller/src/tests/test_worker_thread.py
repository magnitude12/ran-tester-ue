import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest
import types
import threading
import itertools
from datetime import datetime

import docker
from influxdb_client.client.write_api import SYNCHRONOUS

from worker_thread import WorkerThread, RfType
from globals import Globals


# -------------------------
# Fixtures
# -------------------------

@pytest.fixture
def docker_client(mocker):
    client = mocker.Mock()

    # Images
    image = mocker.Mock()
    image.tags = ["test_image:latest"]
    client.images.list.return_value = [image]

    # Containers
    container = mocker.Mock()
    container.logs.return_value = iter([])
    container.attrs = {
        "State": {"Running": True},
        "Image": "test_image",
    }
    client.containers.get.side_effect = docker.errors.NotFound("not found")
    client.containers.run.return_value = container

    # Networks
    net = mocker.Mock()
    client.networks.get.return_value = net

    return client


@pytest.fixture
def influx_client(mocker):
    write_api = mocker.Mock()
    write_api.write = mocker.Mock()

    write_api_cm = mocker.Mock()
    write_api_cm.__enter__ = mocker.Mock(return_value=write_api)
    write_api_cm.__exit__ = mocker.Mock(return_value=False)

    influx = mocker.Mock()
    influx.write_api.return_value = write_api_cm

    return influx


@pytest.fixture
def process_config_base():
    return {
        "name": "proc1",
        "component": "WorkerThread",
        "rf": {"type": "none"},
        "args": ["--foo", "bar"],
    }


@pytest.fixture
def worker(influx_client, docker_client, process_config_base):
    return WorkerThread(influx_client, docker_client, process_config_base)


# -------------------------
# __init__
# -------------------------

def test_init_rf_none(worker):
    assert worker.config.rf_type == RfType.NONE
    assert worker.config.container_id == "proc1"


def test_init_rf_zmq_missing_fields(influx_client, docker_client):
    with pytest.raises(RuntimeError):
        WorkerThread(
            influx_client,
            docker_client,
            {
                "name": "proc1",
                "rf": {"type": "zmq"},
            },
        )


def test_init_rf_unsupported(influx_client, docker_client):
    with pytest.raises(RuntimeError):
        WorkerThread(
            influx_client,
            docker_client,
            {
                "name": "proc1",
                "rf": {"type": "invalid"},
            },
        )


# -------------------------
# cleanup_old_containers
# -------------------------

def test_cleanup_old_containers_image_missing(worker, docker_client):
    worker.config.image_name = "missing_image"
    docker_client.images.list.return_value = []

    with pytest.raises(RuntimeError):
        worker.cleanup_old_containers()


def test_cleanup_old_containers_existing_removed(worker, docker_client):
    worker.config.image_name = "test_image"
    container = docker_client.containers.get.return_value = docker_client.containers.run.return_value

    worker.cleanup_old_containers()

# -------------------------
# setup_volumes
# -------------------------

def test_setup_volumes_none(worker):
    worker.setup_volumes()
    assert "/tmp" in worker.config.container_volumes


# -------------------------
# setup_env
# -------------------------

def test_setup_env(worker):
    worker.setup_env()
    assert "ARGS" in worker.config.container_env


def test_setup_env_b200(worker):
    worker.config.rf_type = RfType.B200
    worker.setup_env()
    assert "UHD_IMAGES_DIR" in worker.config.container_env


# -------------------------
# setup_networks
# -------------------------

def test_setup_networks_basic(worker, docker_client):
    Globals.api_auth = []

    worker.setup_networks()

    docker_client.networks.get.assert_called_with("rt_metrics")
    assert len(worker.config.container_networks) == 1


def test_setup_networks_with_api_auth(worker, docker_client):
    Globals.api_auth = [
        {
            "name": "api1",
            "token": "tok",
            "scopes": ["start"],
            "allowed_components": ["proc1"],
            "pass_to": ["proc1"],
        }
    ]

    worker.setup_networks()

    assert "CONTROL_TOKEN" in worker.config.container_env


# -------------------------
# start_container
# -------------------------

def test_start_container_non_host(worker, docker_client, mocker):
    worker.config.image_name = "test_image"
    worker.setup_env()
    worker.setup_volumes()
    worker.setup_networks()

    mocker.patch.object(threading.Thread, "start")

    worker.start_container()

    docker_client.containers.run.assert_called_once()
    assert worker.log_thread is not None


def test_start_container_host_network(worker, docker_client, mocker):
    worker.config.image_name = "test_image"
    worker.config.host_network = True
    worker.setup_env()
    worker.setup_volumes()

    mocker.patch.object(threading.Thread, "start")

    worker.start_container()

    docker_client.containers.run.assert_called_once()
    assert worker.docker_container is not None


# -------------------------
# stop
# -------------------------

def test_stop_container(worker):
    container = worker.config.docker_client.containers.run.return_value
    worker.docker_container = container
    worker.stop_thread = threading.Event()

    worker.stop()

    container.stop.assert_called_once()
    container.remove.assert_called_once()
    assert worker.stop_thread.is_set()


# -------------------------
# get_status
# -------------------------

def test_get_status_running(worker):
    container = worker.config.docker_client.containers.run.return_value
    worker.docker_container = container

    status = worker.get_status()

    assert status["healthy"] is True


def test_get_status_exited(worker):
    container = worker.config.docker_client.containers.run.return_value
    container.attrs["State"]["Running"] = False
    container.attrs["State"]["ExitCode"] = 1
    worker.docker_container = container

    status = worker.get_status()

    assert status["healthy"] is False
    assert status["exit_code"] == 1


# -------------------------
# send_message / influx_push
# -------------------------

def test_send_message_success(worker, influx_client, mocker):
    mocker.patch("uuid.uuid4", return_value="uuid")
    mocker.patch("hashlib.md5")

    worker.send_message("hello")

    influx_client.write_api.assert_called_once_with(write_options=SYNCHRONOUS)


def test_influx_push_retry(worker, mocker):
    write_api = mocker.Mock()
    write_api.write.side_effect = [ConnectionError("fail"), None]

    worker.influx_push(write_api, "bucket", "time", {})

    assert write_api.write.call_count == 2


# -------------------------
# log_report_thread
# -------------------------

def test_log_report_thread(worker, mocker):
    worker.stop_thread = threading.Event()

    # Fake logs
    worker.docker_logs = iter([b"line1\n", b"line2\n"])

    mock_send = mocker.patch.object(worker, "send_message")

    # Run only one loop iteration
    mocker.patch.object(worker.stop_thread, "is_set", side_effect=[False, True])

    worker.log_report_thread()

    mock_send.assert_called()


# -------------------------
# Main entry
# -------------------------

if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__]))

