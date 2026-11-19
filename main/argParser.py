# ---------------------------------------------------------------------------
# Argument parser
#
# Defines the command-line interface for pyscan-ner:
#
#   target          (positional) IP address, CIDR range, or hostname to scan
#   -p, --ports     Ports to scan, e.g. "80", "1-1024", "22,80,443"
#                   (default: 1-1024)
#   --timeout       Per-connection timeout in seconds (default: 1.0)
#   --discover      Host discovery only, skip the port scan
#   --os            Attempt basic OS detection
#
# Usage:
#   python pyscan.py 192.168.1.10 -p 1-1024
#   python pyscan.py 192.168.1.0/24 --discover
#
# Port specs are validated by parse_ports(), which raises ValueError on bad
# input. main() catches it and reports it via parser.error() so the user sees
# a clean usage message instead of a traceback.
# ---------------------------------------------------------------------------

import argparse
from argparse import Namespace


def argParse(cmd: str) -> list:
    """
    Parse a command-line style string into pyscan arguments.

    Parameters:
        cmd (str): The arguments as a single string, without the program
            name, e.g. '-ip 192.168.1.10 -p 80,443 --timeout 0.5'.
            It is split on whitespace before parsing.

    Arguments recognised:
        -ip (str): IP address, CIDR range, or hostname to scan.
        -p, --ports (str): Port spec, e.g. '80', '1-1024', '22,80,443'.
            Defaults to '1-1024'. Kept as a string; convert it with
            parse_ports().
        --timeout (float): Per-connection timeout in seconds.
            Defaults to 1.0.

    Returns:
        argparse.Namespace: The parsed values as attributes, e.g.
        args.ip, args.ports, args.timeout. An omitted -ip is None.
    """
    parser = argparse.ArgumentParser(
        prog = "pyscan",
        description = "reads argumements from command line and returns them as a list"
    )
    parser.add_argument("-ip", type=str, help="IP address, CIDR range, or hostname to scan")
    parser.add_argument("-p", "--ports", type=str, default="1-1024", help="Ports to scan, e.g. '80', '1-1024', '22,80,443'")
    parser.add_argument("--timeout", type=float, default=1.0, help="Per-connection timeout in seconds (default: 1.0)")

    return parser.parse_args(cmd.split())


def parse_ports(port_str: str) -> list:
    """
    Convert a port specification string into a list of port numbers.

    Parameters:
        port_str (str): Comma-separated ports and/or ranges, e.g. '80',
            '22,80,443', '1-1024', or '22,80,100-103'. Whitespace is
            ignored, and range ends are inclusive.

    Returns:
        list[int]: The unique port numbers in ascending order, e.g.
        '22,80,100-103' returns [22, 80, 100, 101, 102, 103].

    Raises:
        ValueError: If a port is not a number, is outside 1-65535, or is
            part of a malformed range (more than one dash, reversed
            such as '100-50', or a missing start or end such as '1-').
    """
    portSet = set()

    for port in port_str.split(","):
        port = "".join(port.split())

        if port.count("-") > 1:
            raise ValueError(f"Invalid port range: {port}")

        if "-" in port:
            port_range = port.split("-")
            start_port = int(port_range[0])
            end_port = int(port_range[1])
            if start_port > end_port:
                raise ValueError(f"Invalid port range: {start_port}-{end_port}")
            elif start_port < 1 or end_port > 65535:
                raise ValueError(f"Port range out of range: {start_port}-{end_port}")

            portSet.update(list(range(start_port, end_port + 1)))
        else:
            if not port.isdigit():
                raise ValueError(f"Invalid port: {port}")
            if int(port) < 1 or int(port) > 65535:
                raise ValueError(f"Port out of range: {port}")
            portSet.add(int(port))

    return sorted(portSet)