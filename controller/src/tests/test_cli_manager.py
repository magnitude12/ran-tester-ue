import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest
from unittest.mock import MagicMock

from cli_manager import CLIManager, HELP_STR
from globals import Globals


@pytest.fixture
def mock_thread_manager(mocker):
    tm = mocker.Mock()
    tm.process_metadata = []
    tm.start = mocker.Mock()
    tm.start_external = mocker.Mock()
    tm.stop = mocker.Mock()
    Globals.thread_manager = tm
    return tm

@pytest.fixture
def yaml_config():
    return {
        "build_spec": [
            {"component": "cueltschey/rt-env-test", "pull": False},
        ],
        "run_spec": [
            {"component": "cueltschey/rt-env-test", "config_file": "test.conf", "rf": { "type": "none"}},
            {"component": "cueltschey/rt-env-test", "target": "dummy", "config_file": "test.conf", "rf": { "type": "none"}}
        ],
    }


@pytest.fixture
def cli(yaml_config):
    return CLIManager(yaml_config)


# -------------------------
# handle_shutdown
# -------------------------

def test_handle_shutdown_stops_all_and_exits(cli, mock_thread_manager, mocker):
    mock_thread_manager.process_metadata = [
        {"id": 1},
        {"id": 2},
    ]
    mock_exit = mocker.patch.object(sys, "exit")

    cli.handle_shutdown()

    assert mock_thread_manager.stop.call_count == 2
    mock_exit.assert_called_once_with(0)
    assert Globals.thread_manager.process_metadata == []


# -------------------------
# list_components
# -------------------------

def test_list_components_logs_all(cli, mock_thread_manager, mocker):
    mock_log = mocker.patch("logging.info")
    mock_thread_manager.process_metadata = [{"id": 1}, {"id": 2}]

    cli.list_components()

    assert mock_log.call_count == 2


# -------------------------
# list_specifications
# -------------------------

def test_list_specifications(cli, mocker):
    mock_log = mocker.patch("logging.info")

    cli.list_specifications()

    # build_spec header + item + run_spec header + 2 items
    assert mock_log.call_count == 5


# -------------------------
# start_all_components
# -------------------------

def test_start_all_components(cli, mock_thread_manager):
    cli.start_all_components()

    mock_thread_manager.start.assert_called_once_with({"component": "cueltschey/rt-env-test", "config_file": "test.conf", "rf": { "type": "none"}})
    mock_thread_manager.start_external.assert_called_once_with({"component": "cueltschey/rt-env-test", "target": "dummy", "config_file": "test.conf", "rf": { "type": "none"}})


# -------------------------
# start_component
# -------------------------

def test_start_component_valid_index(cli, mock_thread_manager):
    cli.start_component(0)
    mock_thread_manager.start.assert_called_once()


def test_start_component_target(cli, mock_thread_manager):
    cli.start_component(1)
    mock_thread_manager.start_external.assert_called_once()


def test_start_component_out_of_bounds(cli, mock_thread_manager, capsys):
    cli.start_component(99)
    captured = capsys.readouterr()
    assert "out of bounds" in captured.out
    mock_thread_manager.start.assert_not_called()


# -------------------------
# stop_all_components
# -------------------------

def test_stop_all_components(cli, mock_thread_manager):
    mock_thread_manager.process_metadata = [{"id": 1}, {"id": 2}]

    cli.stop_all_components()

    assert mock_thread_manager.stop.call_count == 2
    assert Globals.thread_manager.process_metadata == []


# -------------------------
# stop_component
# -------------------------

def test_stop_component(cli, mock_thread_manager):
    mock_thread_manager.process_metadata = [{"id": 1}, {"id": 2}]

    cli.stop_component(0)

    mock_thread_manager.stop.assert_called_once_with({"id": 1})
    assert len(mock_thread_manager.process_metadata) == 1


# -------------------------
# process_cmd
# -------------------------

def test_process_cmd_help(cli, capsys):
    cli.process_cmd("help")
    captured = capsys.readouterr()
    assert HELP_STR.strip() in captured.out


def test_process_cmd_unknown(cli, capsys):
    cli.process_cmd("nonsense")
    captured = capsys.readouterr()
    assert "Unknown command" in captured.out


def test_process_cmd_exit(cli, mocker):
    mock_shutdown = mocker.patch.object(cli, "handle_shutdown")

    cli.process_cmd("exit")

    mock_shutdown.assert_called_once()


def test_process_cmd_start_all(cli, mocker):
    mock_start_all = mocker.patch.object(cli, "start_all_components")

    cli.process_cmd("start all")

    mock_start_all.assert_called_once()


def test_process_cmd_stop_all(cli, mocker):
    mock_stop_all = mocker.patch.object(cli, "stop_all_components")

    cli.process_cmd("stop all")

    mock_stop_all.assert_called_once()


def test_process_cmd_stop_invalid_index(cli, mock_thread_manager, capsys):
    mock_thread_manager.process_metadata = [{"id": 1}]
    cli.process_cmd("stop 5")

    captured = capsys.readouterr()
    assert "out of bounds" in captured.out


def test_process_cmd_restart_all(cli, mocker):
    mock_stop_all = mocker.patch.object(cli, "stop_all_components")
    mock_start_all = mocker.patch.object(cli, "start_all_components")

    cli.process_cmd("restart all")

    mock_stop_all.assert_called_once()
    mock_start_all.assert_called_once()


# -------------------------
# Main entry
# -------------------------

if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__]))

