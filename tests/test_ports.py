import argparse
import errno
import socket

import pytest

from main.argParser import parse_ports, argParse
from main.portScan import scan_port, PortState

# --- Valid specs -----------------------------------------------------------

@pytest.mark.parametrize("spec, expected", [
    ("80", [80]),                                   # single port
    ("22,80,443", [22, 80, 443]),                   # list
    ("443,22,80", [22, 80, 443]),                   # output is sorted
    ("1-5", [1, 2, 3, 4, 5]),                       # range, end is inclusive
    ("22,80,100-103", [22, 80, 100, 101, 102, 103]),  # mixed
    ("1-5,10-12", [1, 2, 3, 4, 5, 10, 11, 12]),     # multiple ranges
    ("80,80", [80]),                                # duplicates removed
    ("1-10,5-15", list(range(1, 16))),              # overlapping ranges merged
    ("22, 80", [22, 80]),                           # whitespace tolerated
    ("1", [1]),                                     # lower boundary
    ("65535", [65535]),                             # upper boundary
    ("5-5", [5]),                                   # single-port range
])
def test_valid_specs(spec, expected):
    assert parse_ports(spec) == expected


def test_default_range_size():
    ports = parse_ports("1-1024")
    assert len(ports) == 1024
    assert ports[0] == 1
    assert ports[-1] == 1024


def test_full_range():
    ports = parse_ports("1-65535")
    assert len(ports) == 65535


# --- Invalid specs ---------------------------------------------------------

@pytest.mark.parametrize("spec", [
    "",            # empty
    "abc",         # not a number
    "80,,443",     # empty chunk
    "80,",         # trailing comma
    "0",           # below range
    "65536",       # above range
    "-1",          # negative
    "1-",          # missing end
    "-5",          # missing start
    "1-2-3",       # too many parts
    "100-50",      # reversed range
    "0-100",       # range starts below 1
    "1-65536",     # range ends above 65535
    "0-70000",     # both ends out of range
    "80-abc",      # non-numeric range end
])
def test_invalid_specs(spec):
    with pytest.raises(ValueError):
        parse_ports(spec)

# --- argParse: valid input -------------------------------------------------

def test_returns_namespace():
    assert isinstance(argParse("-ip 10.0.0.1"), argparse.Namespace)


def test_all_arguments():
    args = argParse("-ip 192.168.1.10 -p 80,443 --timeout 0.5")
    assert args.ip == "192.168.1.10"
    assert args.ports == "80,443"
    assert args.timeout == 0.5


def test_defaults():
    args = argParse("-ip 10.0.0.1")
    assert args.ports == "1-1024"
    assert args.timeout == 1.0


def test_empty_string_gives_defaults():
    args = argParse("")
    assert args.ip is None          # -ip is not required yet
    assert args.ports == "1-1024"
    assert args.timeout == 1.0


def test_long_option_for_ports():
    assert argParse("-ip 10.0.0.1 --ports 22").ports == "22"


def test_ports_stay_a_string():
    # parse_ports() does the conversion, not argParse
    assert argParse("-ip 10.0.0.1 -p 1-100").ports == "1-100"


def test_timeout_is_converted_to_float():
    args = argParse("-ip 10.0.0.1 --timeout 2")
    assert args.timeout == 2.0
    assert isinstance(args.timeout, float)


def test_argument_order_does_not_matter():
    a = argParse("-ip 10.0.0.1 -p 80 --timeout 3")
    b = argParse("--timeout 3 -p 80 -ip 10.0.0.1")
    assert a == b


@pytest.mark.parametrize("target", [
    "127.0.0.1",
    "0.0.0.0",
    "192.168.1.0/24",
    "scanme.nmap.org",
])
def test_target_formats_are_passed_through(target):
    # argParse does not validate the target, it just stores the string
    assert argParse(f"-ip {target}").ip == target


# --- argParse: invalid input (argparse exits with code 2) ------------------

@pytest.mark.parametrize("cmd", [
    "-ip",                          # option with no value
    "-ip 10.0.0.1 -p",              # -p with no value
    "-ip 10.0.0.1 --timeout",       # --timeout with no value
    "-ip 10.0.0.1 --timeout abc",   # non-numeric timeout
    "-ip 10.0.0.1 --bogus",         # unknown option
    "-ip 10.0.0.1 extra",           # stray positional argument
    '-ip 10.0.0.1 -p "22, 80"',     # cmd.split() breaks on quoted spaces
])
def test_invalid_input_exits(cmd):
    with pytest.raises(SystemExit) as exc:
        argParse(cmd)
    assert exc.value.code == 2


def test_help_exits_cleanly():
    with pytest.raises(SystemExit) as exc:
        argParse("-h")
    assert exc.value.code == 0

    # --- scan_port: real sockets on localhost ----------------------------------

@pytest.fixture
def listening_port():
    """A port with a real listener on it. The OS picks a free one (port 0)."""
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        yield server.getsockname()[1]


@pytest.fixture
def unused_port():
    """A port that was free a moment ago and has nothing listening on it."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    return port


def test_open_port(listening_port):
    assert scan_port("127.0.0.1", listening_port, 0.5) == (listening_port, PortState.OPEN)


def test_closed_port(unused_port):
    assert scan_port("127.0.0.1", unused_port, 0.5) == (unused_port, PortState.CLOSED)


def test_returns_port_and_state(unused_port):
    port, state = scan_port("127.0.0.1", unused_port, 0.5)
    assert port == unused_port
    assert isinstance(state, PortState)


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
    assert scan_port("10.0.0.1", 80, 0.1) == (80, expected)


def test_connect_success_is_open(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", lambda self, address: None)
    assert scan_port("10.0.0.1", 443, 0.1) == (443, PortState.OPEN)


# --- PortState -------------------------------------------------------------

def test_port_state_values():
    assert PortState.OPEN == "open"
    assert PortState.CLOSED == "closed"
    assert PortState.FILTERED == "filtered"
    assert PortState.ERROR == "error"