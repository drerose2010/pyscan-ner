import pytest

from main.argParser import parse_ports

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
