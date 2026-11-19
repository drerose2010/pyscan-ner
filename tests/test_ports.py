import argparse
import pytest

from main.argParser import parse_ports, argParse

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