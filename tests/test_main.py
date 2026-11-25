import importlib
import socket
import sys

import pytest

from main.portScan import PortState

# The module file is named "pyscan-ner.py". A hyphen is not valid in an
# import statement, so load it by name with importlib instead.
app = importlib.import_module("main.pyscan_ner")


# --- Helpers ---------------------------------------------------------------

def install_fake_scan(monkeypatch, states=None, default=PortState.CLOSED):
    """Replace scan_port in main with a fake that never touches the network.

    states maps port -> PortState. Any other port gets `default`.
    The returned function records every call in fake.calls.
    """
    states = states or {}
    calls = []

    def fake(ip, port, timeout):
        calls.append((ip, port, timeout))
        return port, states.get(port, default), "fake"

    fake.calls = calls
    monkeypatch.setattr(app, "scan_port", fake)
    return fake


@pytest.fixture
def listening_port():
    """A real listener on a free port chosen by the OS."""
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        yield server.getsockname()[1]


# --- Argument handling -----------------------------------------------------

def test_missing_ip_exits_with_error(monkeypatch, capsys):
    fake = install_fake_scan(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        app.main([])
    assert exc.value.code == 1
    assert "-ip" in capsys.readouterr().out
    assert fake.calls == []                       # nothing scanned


def test_invalid_port_spec_exits_without_scanning(monkeypatch, capsys):
    fake = install_fake_scan(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        app.main(["-ip", "10.0.0.1", "-p", "abc"])
    assert exc.value.code != 0
    assert "Error" in capsys.readouterr().out
    assert fake.calls == []


def test_invalid_port_spec_gives_clear_message(monkeypatch, capsys):
    # Fails until the `except ValueError` in main() exits straight away.
    # Without that, `ports` is undefined and a NameError is caught and
    # reported as "Error scanning ports", which is a misleading message.
    install_fake_scan(monkeypatch)
    with pytest.raises(SystemExit):
        app.main(["-ip", "10.0.0.1", "-p", "abc"])
    assert "Error scanning ports" not in capsys.readouterr().out


def test_reads_real_command_line_when_no_argv(monkeypatch):
    fake = install_fake_scan(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["pyscan", "-ip", "10.0.0.1", "-p", "80"])
    app.main()
    assert fake.calls == [("10.0.0.1", 80, 1.0)]


# --- Scanning --------------------------------------------------------------

def test_scans_every_requested_port(monkeypatch):
    fake = install_fake_scan(monkeypatch)
    app.main(["-ip", "10.0.0.1", "-p", "22,80,100-102"])
    assert [port for _, port, _ in fake.calls] == [22, 80, 100, 101, 102]


def test_default_ports_are_1_to_1024(monkeypatch):
    fake = install_fake_scan(monkeypatch)
    app.main(["-ip", "10.0.0.1"])
    ports = [port for _, port, _ in fake.calls]
    assert len(ports) == 1024
    assert ports[0] == 1
    assert ports[-1] == 1024


def test_target_and_timeout_are_passed_through(monkeypatch):
    fake = install_fake_scan(monkeypatch)
    app.main(["-ip", "192.168.1.10", "-p", "80", "--timeout", "0.25"])
    assert fake.calls == [("192.168.1.10", 80, 0.25)]


def test_scan_failure_exits_with_error(monkeypatch, capsys):
    def boom(ip, port, timeout):
        raise RuntimeError("boom")

    monkeypatch.setattr(app, "scan_port", boom)
    with pytest.raises(SystemExit) as exc:
        app.main(["-ip", "10.0.0.1", "-p", "80"])
    assert exc.value.code == 1
    assert "Error scanning ports" in capsys.readouterr().out


# --- Reporting -------------------------------------------------------------

def test_open_port_is_reported(monkeypatch, capsys):
    install_fake_scan(monkeypatch, {80: PortState.OPEN})
    app.main(["-ip", "10.0.0.1", "-p", "79-81"])
    out = capsys.readouterr().out
    assert "Port 80: Open" in out


def test_only_open_ports_are_listed(monkeypatch, capsys):
    install_fake_scan(monkeypatch, {22: PortState.OPEN, 80: PortState.OPEN,
                                    81: PortState.FILTERED})
    app.main(["-ip", "10.0.0.1", "-p", "22,80,81,443"])
    out = capsys.readouterr().out
    assert "Port 22: Open" in out
    assert "Port 80: Open" in out
    assert "Port 81:" not in out                  # filtered, not listed
    assert "Port 443:" not in out                 # closed, not listed
    assert out.count("Port ") == 2


def test_no_open_ports_lists_none(monkeypatch, capsys):
    install_fake_scan(monkeypatch)                # everything closed
    app.main(["-ip", "10.0.0.1", "-p", "1-5"])
    assert "Port " not in capsys.readouterr().out.replace("State Summary", "")


def test_summary_counts_each_state(monkeypatch, capsys):
    install_fake_scan(monkeypatch, {1: PortState.OPEN, 2: PortState.CLOSED,
                                    3: PortState.CLOSED, 4: PortState.FILTERED})
    app.main(["-ip", "10.0.0.1", "-p", "1-4"])
    out = capsys.readouterr().out
    assert "State Summary: 1 open" in out
    assert "State Summary: 2 closed" in out
    assert "State Summary: 1 filtered" in out


def test_summary_counts_add_up_to_ports_scanned(monkeypatch, capsys):
    install_fake_scan(monkeypatch, {1: PortState.OPEN, 2: PortState.FILTERED,
                                    3: PortState.ERROR})
    app.main(["-ip", "10.0.0.1", "-p", "1-10"])
    lines = [line for line in capsys.readouterr().out.splitlines()
             if line.startswith("State Summary:")]
    total = sum(int(line.split(": ")[1].split()[0]) for line in lines)
    assert total == 10


# --- End to end on localhost (no mocks) ------------------------------------

def test_real_scan_finds_listening_port(listening_port, capsys):
    app.main(["-ip", "127.0.0.1", "-p", str(listening_port), "--timeout", "0.5"])
    out = capsys.readouterr().out
    assert f"Port {listening_port}: Open" in out
    assert "State Summary: 1 open" in out
