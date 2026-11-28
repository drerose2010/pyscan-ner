import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from main import pyscan_ner as app
from main.argParser import argParse
from main.portScan import PortState

# --- Helper ----------------------------------------------------------------

def install_fake_scan(monkeypatch, states=None, default=PortState.CLOSED, delay=None):
    """Replace scan_port in main with a fake that never touches the network.

    states maps port -> PortState, anything else gets `default`.
    delay is an optional function port -> seconds to sleep, used to make
    scans finish out of order. Every call is recorded in fake.calls.
    """
    states = states or {}
    calls = []

    def fake(ip, port, timeout):
        if delay:
            time.sleep(delay(port))
        calls.append((ip, port, timeout))
        return port, states.get(port, default), "fake"

    fake.calls = calls
    monkeypatch.setattr(app, "scan_port", fake)
    return fake


# --- argParse: --threads ---------------------------------------------------

def test_threads_default():
    args = argParse(["-ip", "10.0.0.1"])
    assert args.threads == 50
    assert isinstance(args.threads, int)


@pytest.mark.parametrize("value, expected", [
    ("1", 1),          # lowest allowed
    ("8", 8),
    ("100", 100),
    ("500", 500),
])
def test_threads_accepts_positive_integers(value, expected):
    assert argParse(["-ip", "10.0.0.1", "--threads", value]).threads == expected


@pytest.mark.parametrize("value", ["0", "-1", "abc", "2.5", ""])
def test_threads_rejects_bad_values(value):
    with pytest.raises(SystemExit) as exc:
        argParse(["-ip", "10.0.0.1", "--threads", value])
    assert exc.value.code == 2


def test_threads_missing_value_exits():
    with pytest.raises(SystemExit) as exc:
        argParse(["-ip", "10.0.0.1", "--threads"])
    assert exc.value.code == 2


# --- main: threaded scanning (fake scanner, no network) --------------------

def test_thread_count_reaches_the_pool(monkeypatch):
    install_fake_scan(monkeypatch)
    seen = []

    class SpyPool(ThreadPoolExecutor):
        def __init__(self, *args, **kwargs):
            seen.append(kwargs.get("max_workers"))
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(app, "ThreadPoolExecutor", SpyPool)
    app.main(["-ip", "10.0.0.1", "-p", "1-3", "--threads", "7"])
    assert seen == [7]


def test_every_port_scanned_exactly_once(monkeypatch):
    fake = install_fake_scan(monkeypatch)
    app.main(["-ip", "10.0.0.1", "-p", "1-200", "--threads", "50"])
    # sorted() because threads call the scanner in no fixed order
    assert sorted(port for _, port, _ in fake.calls) == list(range(1, 201))


def test_single_thread_scans_everything(monkeypatch):
    fake = install_fake_scan(monkeypatch)
    app.main(["-ip", "10.0.0.1", "-p", "1-20", "--threads", "1"])
    assert sorted(port for _, port, _ in fake.calls) == list(range(1, 21))


def test_more_threads_than_ports(monkeypatch):
    fake = install_fake_scan(monkeypatch)
    app.main(["-ip", "10.0.0.1", "-p", "1-3", "--threads", "100"])
    assert sorted(port for _, port, _ in fake.calls) == [1, 2, 3]


@pytest.mark.parametrize("threads", ["2", "4", "32"])
def test_output_is_identical_for_any_thread_count(monkeypatch, capsys, threads):
    install_fake_scan(monkeypatch, {2: PortState.OPEN, 5: PortState.FILTERED,
                                    7: PortState.OPEN})
    app.main(["-ip", "10.0.0.1", "-p", "1-10", "--threads", "1"])
    baseline = capsys.readouterr().out

    app.main(["-ip", "10.0.0.1", "-p", "1-10", "--threads", threads])
    assert capsys.readouterr().out == baseline


def test_open_ports_listed_in_order_when_scans_finish_out_of_order(monkeypatch, capsys):
    # Port 1 is the slowest, so it finishes last. The report must still list 1 first.
    install_fake_scan(
        monkeypatch,
        {port: PortState.OPEN for port in range(1, 5)},
        delay=lambda port: 0.05 if port == 1 else 0,
    )
    app.main(["-ip", "10.0.0.1", "-p", "1-4", "--threads", "4"])
    listed = re.findall(r"Port (\d+): Open", capsys.readouterr().out)
    assert listed == ["1", "2", "3", "4"]


def test_error_in_a_worker_exits_with_error(monkeypatch, capsys):
    def flaky(ip, port, timeout):
        if port == 3:
            raise RuntimeError("boom")
        return port, PortState.CLOSED, "fake"

    monkeypatch.setattr(app, "scan_port", flaky)
    with pytest.raises(SystemExit) as exc:
        app.main(["-ip", "10.0.0.1", "-p", "1-5", "--threads", "4"])
    assert exc.value.code == 1
    assert "Error scanning ports" in capsys.readouterr().out


def test_invalid_threads_value_does_not_scan(monkeypatch):
    fake = install_fake_scan(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        app.main(["-ip", "10.0.0.1", "--threads", "0"])
    assert exc.value.code == 2
    assert fake.calls == []


# --- End to end on localhost (no mocks) ------------------------------------

def test_real_threaded_scan_finds_all_listeners(capsys):
    servers = []
    try:
        for _ in range(3):
            s = socket.socket()
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            servers.append(s)

        ports = sorted(s.getsockname()[1] for s in servers)
        spec = ",".join(str(p) for p in ports)

        app.main(["-ip", "127.0.0.1", "-p", spec, "--threads", "8", "--timeout", "0.5"])
        out = capsys.readouterr().out

        for port in ports:
            assert f"Port {port}: Open" in out
        assert "State Summary: 3 open" in out
    finally:
        for s in servers:
            s.close()
