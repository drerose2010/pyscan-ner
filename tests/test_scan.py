import errno
import socket

import pytest

from main.portScan import PortState, scan_port

# scan_port returns (port, state, message).
# The listening_port and unused_port fixtures live in conftest.py.


# --- scan_port: real sockets on localhost ----------------------------------

def test_open_port(listening_port):
    port, state, message = scan_port("127.0.0.1", listening_port, 0.5)
    assert (port, state) == (listening_port, PortState.OPEN)
    assert message == "Connection successful"


def test_closed_port(unused_port):
    port, state, message = scan_port("127.0.0.1", unused_port, 0.5)
    assert (port, state) == (unused_port, PortState.CLOSED)
    assert message == "Connection refused"


def test_returns_port_state_and_message(unused_port):
    result = scan_port("127.0.0.1", unused_port, 0.5)
    assert len(result) == 3
    port, state, message = result
    assert port == unused_port
    assert isinstance(state, PortState)
    assert isinstance(message, str)


def test_timeout_is_applied(monkeypatch, unused_port):
    seen = []
    original = socket.socket.settimeout

    def spy(self, value):
        seen.append(value)
        original(self, value)

    monkeypatch.setattr(socket.socket, "settimeout", spy)
    scan_port("127.0.0.1", unused_port, 0.25)
    assert seen == [0.25]


# --- scan_port: exception-to-state mapping (mocked, no network) ------------

def _raising_connect(exc):
    def fake_connect(self, address):
        raise exc
    return fake_connect


@pytest.mark.parametrize("exc, expected", [
    (ConnectionRefusedError(), PortState.CLOSED),
    (TimeoutError(), PortState.FILTERED),
    (OSError(errno.EHOSTUNREACH, "No route to host"), PortState.FILTERED),
    (OSError(errno.ENETUNREACH, "Network is unreachable"), PortState.FILTERED),
    (OSError(errno.EPERM, "Operation not permitted"), PortState.FILTERED),
    (OSError(errno.EMFILE, "Too many open files"), PortState.ERROR),
    (OSError("something unexpected"), PortState.ERROR),   # no errno at all
], ids=["refused", "timeout", "host-unreachable", "net-unreachable",
        "eperm", "too-many-files", "unknown-oserror"])
def test_exception_mapping(monkeypatch, exc, expected):
    monkeypatch.setattr(socket.socket, "connect", _raising_connect(exc))
    port, state, message = scan_port("10.0.0.1", 80, 0.1)
    assert (port, state) == (80, expected)
    assert isinstance(message, str)


def test_os_error_message_is_included(monkeypatch):
    exc = OSError(errno.EHOSTUNREACH, "No route to host")
    monkeypatch.setattr(socket.socket, "connect", _raising_connect(exc))
    _, _, message = scan_port("10.0.0.1", 80, 0.1)
    assert "No route to host" in message


def test_connect_success_is_open(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", lambda self, address: None)
    port, state, _ = scan_port("10.0.0.1", 443, 0.1)
    assert (port, state) == (443, PortState.OPEN)


# --- PortState -------------------------------------------------------------

def test_port_state_values():
    assert PortState.OPEN == "open"
    assert PortState.CLOSED == "closed"
    assert PortState.FILTERED == "filtered"
    assert PortState.ERROR == "error"
