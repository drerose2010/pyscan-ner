import sys

from argParser import parse_ports, argParse
from portScan import scan_port
from collections import Counter


def main(argv=None) -> None:
    # 1. Get the arguments
    # argParse currently takes a string, so join sys.argv (without the script name)
    args = argParse(" ".join(argv if argv is not None else sys.argv[1:]))

    # 2. Validate the target
    # args.ip is None when -ip is omitted, so print a usage error and exit
    ...

    # 3. Convert the port spec
    # parse_ports raises ValueError on bad input, so catch it, print the
    # message, and exit with a non-zero code
    try:
        ports = parse_ports(args.ports)
    except ValueError as e:
        ...

    # 4. Scan (sequential for now)
    results = []                 # list of (port, PortState) tuples
    for port in ports:
        ...                      # call scan_port, append the result

    # 5. Report
    # open ports: loop over results, print only the OPEN ones
    ...
    # summary: Counter of states, e.g. "993 closed, 28 filtered"
    counts = Counter(state for _, state in results)
    ...


if __name__ == "__main__":
    main()