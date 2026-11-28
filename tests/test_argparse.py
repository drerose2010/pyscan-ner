import argparse
import sys

import pytest

from main.argParser import argParse


def test_returns_namespace():
    assert isinstance(argParse(["-ip", "10.0.0.1"]), argparse.Namespace)


def test_all_arguments():
    args = argParse(["-ip", "192.168.1.10", "-p", "80,443", "--timeout", "0.5"])
    assert args.ip == "192.168.1.10"
    assert args.ports == "80,443"
    assert args.timeout == 0.5


def test_defaults():
    args = argParse(["-ip", "10.0.0.1"])
    assert args.ports == "1-1024"
    assert args.timeout == 1.0


def test_empty_list_gives_defaults():
    args = argParse([])
    assert args.ip is None          # -ip is not required yet
    assert args.ports == "1-1024"
    assert args.timeout == 1.0


def test_long_option_for_ports():
    assert argParse(["-ip", "10.0.0.1", "--ports", "22"]).ports == "22"


def test_ports_stay_a_string():
    # parse_ports() does the conversion, not argParse
    assert argParse(["-ip", "10.0.0.1", "-p", "1-100"]).ports == "1-100"


def test_timeout_is_converted_to_float():
    args = argParse(["-ip", "10.0.0.1", "--timeout", "2"])
    assert args.timeout == 2.0
    assert isinstance(args.timeout, float)


def test_argument_order_does_not_matter():
    a = argParse(["-ip", "10.0.0.1", "-p", "80", "--timeout", "3"])
    b = argParse(["--timeout", "3", "-p", "80", "-ip", "10.0.0.1"])
    assert a == b


def test_value_with_spaces_stays_one_argument():
    # A list keeps "22, 80" as a single value. The old string version split it.
    args = argParse(["-ip", "10.0.0.1", "-p", "22, 80"])
    assert args.ports == "22, 80"


@pytest.mark.parametrize("target", [
    "127.0.0.1",
    "0.0.0.0",
    "192.168.1.0/24",
    "scanme.nmap.org",
])
def test_target_formats_are_passed_through(target):
    # argParse does not validate the target, it just stores the string
    assert argParse(["-ip", target]).ip == target


# --- argParse: reading the real command line -------------------------------

def test_none_reads_sys_argv(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pyscan", "-ip", "10.0.0.1", "-p", "80"])
    args = argParse()
    assert args.ip == "10.0.0.1"
    assert args.ports == "80"


def test_explicit_list_ignores_sys_argv(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pyscan", "-ip", "1.1.1.1"])
    assert argParse(["-ip", "10.0.0.1"]).ip == "10.0.0.1"


# --- argParse: invalid input (argparse exits with code 2) ------------------

@pytest.mark.parametrize("argv", [
    ["-ip"],                                        # option with no value
    ["-ip", "10.0.0.1", "-p"],                      # -p with no value
    ["-ip", "10.0.0.1", "--timeout"],               # --timeout with no value
    ["-ip", "10.0.0.1", "--timeout", "abc"],        # non-numeric timeout
    ["-ip", "10.0.0.1", "--bogus"],                 # unknown option
    ["-ip", "10.0.0.1", "extra"],                   # stray positional argument
])
def test_invalid_input_exits(argv):
    with pytest.raises(SystemExit) as exc:
        argParse(argv)
    assert exc.value.code == 2


def test_help_exits_cleanly():
    with pytest.raises(SystemExit) as exc:
        argParse(["-h"])
    assert exc.value.code == 0